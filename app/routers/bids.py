"""Bid router — bid placement endpoint."""

from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.models.audit_log import AuditLog
from app.schemas.bid import BidCreate, BidResponse
from app.routers.auctions import check_and_update_auction_statuses
from app.websocket_manager import manager, MSG_NEW_BID

router = APIRouter(prefix="/api/v1/auctions", tags=["bids"])


@router.post("/{auction_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def create_bid(
    auction_id: UUID,
    data: BidCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a bid on an auction."""
    ip_address = request.client.host if request.client else None

    # 1. Update statuses based on current time first
    await check_and_update_auction_statuses(db)

    # 2. Get the auction with pessimistic lock (for postgres)
    query = select(Auction).where(Auction.id == auction_id)
    if db.bind and db.bind.dialect.name == "postgresql":
        query = query.with_for_update()

    result = await db.execute(query)
    auction = result.scalar_one_or_none()

    # Validate existence
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )

    # Validate status
    if auction.status != AuctionStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Auction is not active",
        )

    # Validate expiration
    now = datetime.now(timezone.utc)
    ends_at = auction.ends_at.replace(tzinfo=timezone.utc) if auction.ends_at.tzinfo is None else auction.ends_at
    if ends_at <= now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Auction has ended",
        )

    # Validate bidder
    if auction.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sellers cannot bid on own auction",
        )

    # Validate amount
    min_amount = auction.current_price + auction.bid_increment
    if data.amount < min_amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bid too low. Minimum: {min_amount}",
        )

    # Mark previous winning bid as not winning
    prev_winning = await db.execute(
        select(Bid).where(
            and_(Bid.auction_id == auction_id, Bid.is_winning == True)
        )
    )
    prev_bid = prev_winning.scalar_one_or_none()
    if prev_bid:
        prev_bid.is_winning = False
        db.add(prev_bid)

    # Create new bid
    bid = Bid(
        auction_id=auction_id,
        bidder_id=current_user.id,
        amount=data.amount,
        is_winning=True,
        ip_address=ip_address,
    )
    db.add(bid)

    # Update auction price & bids count
    auction.current_price = data.amount
    auction.total_bids = (auction.total_bids or 0) + 1
    db.add(auction)
    await db.flush()

    # Create audit log
    audit = AuditLog(
        entity_type="bid",
        entity_id=bid.id,
        action="bid_placed",
        actor_id=current_user.id,
        new_value={
            "amount": str(data.amount),
            "auction_id": str(auction_id),
            "previous_price": str(auction.current_price),
        },
    )
    db.add(audit)
    await db.flush()

    # Broadcast new bid info to WebSocket viewers
    await manager.broadcast_to_auction(str(auction_id), {
        "type": MSG_NEW_BID,
        "data": {
            "bid_id": str(bid.id),
            "amount": str(bid.amount),
            "bidder_username": current_user.username,
            "auction_id": str(auction_id),
            "total_bids": auction.total_bids,
            "timestamp": bid.created_at.isoformat(),
        },
    })

    return bid
