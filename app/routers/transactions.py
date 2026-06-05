"""Transaction and Audit Log REST endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.auction import Auction
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog
from app.schemas.transaction import TransactionResponse, AuditLogResponse
from app.routers.auctions import check_and_update_auction_statuses

router = APIRouter(prefix="/api/v1", tags=["transactions"])


@router.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    role: str = Query("buyer", regex="^(buyer|seller)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get transactions for the current user (as buyer or seller)."""
    await check_and_update_auction_statuses(db)

    if role == "seller":
        condition = Transaction.seller_id == current_user.id
    else:
        condition = Transaction.buyer_id == current_user.id

    result = await db.execute(
        select(Transaction).where(condition).order_by(Transaction.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/transactions/{reference_number}", response_model=TransactionResponse)
async def get_transaction(
    reference_number: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a transaction by reference number."""
    result = await db.execute(
        select(Transaction).where(Transaction.reference_number == reference_number)
    )
    txn = result.scalar_one_or_none()

    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    # Only buyer or seller can view
    if txn.buyer_id != current_user.id and txn.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this transaction",
        )
    return txn


@router.get("/auctions/{auction_id}/audit-log", response_model=List[AuditLogResponse])
async def get_auction_audit_log(
    auction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full event history for an auction. Only accessible by the seller."""
    auction = await db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found",
        )
    if auction.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the auction seller can view the audit log",
        )

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type == "auction", AuditLog.entity_id == auction_id)
        .order_by(AuditLog.id.asc())
    )
    logs = list(result.scalars().all())

    # Also include bid and transaction logs related to this auction
    bid_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type.in_(["bid", "transaction"]))
        .order_by(AuditLog.id.asc())
    )
    related_logs = [
        log for log in bid_result.scalars().all()
        if log.new_value and str(auction_id) in str(log.new_value)
    ]

    all_logs = sorted(logs + related_logs, key=lambda x: x.id)
    return all_logs
