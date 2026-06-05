"""Auction router — CRUD endpoints for auctions and dynamic lifecycle state manager."""

import math
import string
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.models.transaction import Transaction, TransactionStatus
from app.models.audit_log import AuditLog
from app.websocket_manager import manager, MSG_AUCTION_ACTIVATED, MSG_AUCTION_LOCKED
from app.schemas.auction import (
    AuctionCreate, AuctionUpdate, AuctionResponse, AuctionListResponse,
)
from app.schemas.bid import BidListResponse

router = APIRouter(prefix="/api/v1/auctions", tags=["auctions"])


def generate_reference_number() -> str:
    """Generate TXN-XXXXXXXXXXXXXXXX (16 uppercase alphanumeric chars)."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(16))
    return f"TXN-{suffix}"


async def check_and_update_auction_statuses(db: AsyncSession) -> None:
    """
    Dynamically checks and transitions auction statuses based on current time.
    Replaces background workers.
    """
    now = datetime.now(timezone.utc)

    # 1. Transition PENDING -> ACTIVE if starts_at <= now
    pending_query = select(Auction).where(
        and_(
            Auction.status == AuctionStatus.PENDING.value,
            Auction.starts_at <= now
        )
    )
    result = await db.execute(pending_query)
    pending_auctions = result.scalars().all()
    for auction in pending_auctions:
        auction.status = AuctionStatus.ACTIVE.value
        db.add(auction)
        
        # Log audit log
        audit = AuditLog(
            entity_type="auction",
            entity_id=auction.id,
            action="auction_activated",
            new_value={"status": auction.status}
        )
        db.add(audit)

        # Broadcast via websocket
        await manager.broadcast_to_auction(str(auction.id), {
            "type": MSG_AUCTION_ACTIVATED,
            "data": {
                "auction_id": str(auction.id),
                "title": auction.title,
            },
        })

    # 2. Transition ACTIVE -> COMPLETED if ends_at <= now
    active_query = select(Auction).where(
        and_(
            Auction.status == AuctionStatus.ACTIVE.value,
            Auction.ends_at <= now
        )
    )
    result = await db.execute(active_query)
    expired_auctions = result.scalars().all()
    for auction in expired_auctions:
        # Determine winner by finding the highest bid
        bid_query = select(Bid).where(Bid.auction_id == auction.id).order_by(Bid.amount.desc()).limit(1)
        bid_result = await db.execute(bid_query)
        winning_bid = bid_result.scalar_one_or_none()

        if winning_bid:
            auction.winner_id = winning_bid.bidder_id
            auction.status = AuctionStatus.COMPLETED.value
            db.add(auction)

            # Create Transaction
            txn = Transaction(
                auction_id=auction.id,
                buyer_id=winning_bid.bidder_id,
                seller_id=auction.seller_id,
                amount=auction.current_price,
                status=TransactionStatus.PENDING.value,
                reference_number=generate_reference_number(),
            )
            db.add(txn)
            await db.flush()

            # Log audit logs
            audit_auction = AuditLog(
                entity_type="auction",
                entity_id=auction.id,
                action="winner_determined",
                new_value={"winner_id": str(winning_bid.bidder_id), "amount": str(winning_bid.amount)}
            )
            db.add(audit_auction)

            audit_txn = AuditLog(
                entity_type="transaction",
                entity_id=txn.id,
                action="transaction_created",
                new_value={"reference_number": txn.reference_number, "amount": str(txn.amount)}
            )
            db.add(audit_txn)
        else:
            # No bids
            auction.status = AuctionStatus.COMPLETED.value
            db.add(auction)

            audit_auction = AuditLog(
                entity_type="auction",
                entity_id=auction.id,
                action="auction_completed_no_bids",
                new_value={"status": auction.status}
            )
            db.add(audit_auction)

        # Broadcast via websocket
        await manager.broadcast_to_auction(str(auction.id), {
            "type": MSG_AUCTION_LOCKED,
            "data": {
                "auction_id": str(auction.id),
                "final_price": str(auction.current_price),
            },
        })

    if pending_auctions or expired_auctions:
        await db.flush()


@router.get("/my/created", response_model=AuctionListResponse)
async def my_created_auctions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get auctions created by the current user."""
    await check_and_update_auction_statuses(db)
    
    page_size = min(page_size, 100)
    query = select(Auction).where(Auction.seller_id == current_user.id)
    count_query = select(func.count()).select_from(Auction).where(Auction.seller_id == current_user.id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Auction.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    auctions = list(result.scalars().all())

    return AuctionListResponse(
        items=auctions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/my/participated", response_model=AuctionListResponse)
async def my_participated_auctions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get auctions the current user has bid on."""
    await check_and_update_auction_statuses(db)

    page_size = min(page_size, 100)
    
    # Subquery to find auctions the user has bid on
    bid_auction_ids = (
        select(Bid.auction_id)
        .where(Bid.bidder_id == current_user.id)
        .distinct()
        .subquery()
    )

    query = select(Auction).where(Auction.id.in_(select(bid_auction_ids.c.auction_id)))
    count_query = select(func.count()).select_from(Auction).where(
        Auction.id.in_(select(bid_auction_ids.c.auction_id))
    )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Auction.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    auctions = list(result.scalars().all())

    return AuctionListResponse(
        items=auctions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("", response_model=AuctionListResponse)
async def list_all_auctions(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    seller_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List auctions with optional filtering and pagination."""
    await check_and_update_auction_statuses(db)

    page_size = min(page_size, 100)
    query = select(Auction)
    count_query = select(func.count()).select_from(Auction)

    conditions = []
    if status:
        conditions.append(Auction.status == status)
    if search:
        conditions.append(Auction.title.ilike(f"%{search}%"))
    if seller_id:
        conditions.append(Auction.seller_id == seller_id)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(Auction.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    auctions = list(result.scalars().all())

    return AuctionListResponse(
        items=auctions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.post("", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_auction(
    data: AuctionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new auction."""
    now = datetime.now(timezone.utc)
    if data.starts_at.tzinfo is None:
        data.starts_at = data.starts_at.replace(tzinfo=timezone.utc)
    if data.ends_at.tzinfo is None:
        data.ends_at = data.ends_at.replace(tzinfo=timezone.utc)

    if data.starts_at <= now:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Start time must be in the future",
        )
    if data.ends_at <= data.starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="End time must be after start time",
        )
    if data.reserve_price is not None and data.reserve_price <= data.starting_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reserve price must be greater than starting price",
        )

    auction = Auction(
        title=data.title,
        description=data.description,
        seller_id=current_user.id,
        starting_price=data.starting_price,
        reserve_price=data.reserve_price,
        current_price=data.starting_price,
        bid_increment=data.bid_increment,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        status=AuctionStatus.PENDING.value,
        total_bids=0,
    )
    db.add(auction)
    await db.flush()

    # Audit log
    audit = AuditLog(
        entity_type="auction",
        entity_id=auction.id,
        action="auction_created",
        actor_id=current_user.id,
        new_value={"title": auction.title, "starting_price": str(auction.starting_price)},
    )
    db.add(audit)
    await db.flush()

    return auction


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(
    auction_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single auction by ID."""
    await check_and_update_auction_statuses(db)
    auction = await db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )
    return auction


@router.put("/{auction_id}", response_model=AuctionResponse)
async def update_existing_auction(
    auction_id: UUID,
    data: AuctionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an auction (only when status is 'pending')."""
    auction = await db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )

    if auction.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can update this auction",
        )

    if auction.status != AuctionStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only edit auctions in 'pending' status",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(auction, key, value)

    db.add(auction)
    await db.flush()
    return auction


@router.delete("/{auction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_auction(
    auction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an auction (only when status is 'pending')."""
    auction = await db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )

    if auction.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can delete this auction",
        )

    if auction.status != AuctionStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only delete auctions in 'pending' status",
        )

    await db.delete(auction)
    await db.flush()


@router.get("/{auction_id}/bids", response_model=BidListResponse)
async def get_auction_bids(
    auction_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get bid history for an auction."""
    page_size = min(page_size, 100)

    count_result = await db.execute(
        select(func.count()).select_from(Bid).where(Bid.auction_id == auction_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.amount.desc(), Bid.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    bids = list(result.scalars().all())

    return BidListResponse(
        items=bids,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )
