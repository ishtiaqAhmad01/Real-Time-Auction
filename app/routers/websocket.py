"""WebSocket router — live auction feeds and real-time bidding."""

import asyncio
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.models.user import User
from app.models.audit_log import AuditLog
from app.dependencies import decode_token
from app.routers.auctions import check_and_update_auction_statuses
from app.websocket_manager import (
    manager,
    MSG_PLACE_BID, MSG_PING, MSG_BID_ACCEPTED, MSG_BID_REJECTED,
    MSG_NEW_BID, MSG_INIT, MSG_VIEWER_UPDATE, MSG_ERROR, MSG_PONG,
)



router = APIRouter(tags=["websocket"])


async def _get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Validate JWT token and return user, or None."""
    try:
        payload = decode_token(token)
        if payload.type != "access":
            return None
        user = await db.get(User, UUID(payload.sub))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None


async def heartbeat(websocket: WebSocket, interval: int = 30):
    """Send PING every 30 seconds to keep connection alive."""
    while True:
        await asyncio.sleep(interval)
        try:
            await websocket.send_json({"type": MSG_PING})
        except Exception:
            break


@router.websocket("/ws/auctions/{auction_id}")
async def auction_live_feed(
    websocket: WebSocket,
    auction_id: UUID,
    token: Optional[str] = None,
):
    """Broadcast-only feed. Clients connect to receive live bid updates."""
    auction_id_str = str(auction_id)

    # Validate auction exists and update statuses dynamically
    async with async_session_factory() as db:
        await check_and_update_auction_statuses(db)
        await db.commit()

        auction = await db.get(Auction, auction_id)
        if not auction:
            await websocket.close(code=4004, reason="Auction not found")
            return
        if auction.status not in (AuctionStatus.ACTIVE, AuctionStatus.PENDING):
            await websocket.close(code=4009, reason="Auction is not active")
            return

        auction_data = {
            "id": str(auction.id),
            "title": auction.title,
            "current_price": str(auction.current_price),
            "status": auction.status if isinstance(auction.status, str) else auction.status.value,
            "total_bids": auction.total_bids,
            "ends_at": auction.ends_at.isoformat(),
        }

    # Connect to manager room
    await manager.connect(websocket, auction_id_str)

    try:
        # Send initial state
        viewer_count = manager.get_viewer_count(auction_id_str)
        await websocket.send_json({
            "type": MSG_INIT,
            "data": {
                **auction_data,
                "viewer_count": viewer_count,
            },
        })

        # Send viewer count update to ALL clients
        await manager.broadcast_to_auction(auction_id_str, {
            "type": MSG_VIEWER_UPDATE,
            "data": {"viewer_count": viewer_count},
        })

        # Start heartbeat
        heartbeat_task = asyncio.create_task(heartbeat(websocket))

        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == MSG_PING:
                    await websocket.send_json({"type": MSG_PONG})
        except (WebSocketDisconnect, json.JSONDecodeError):
            pass
        finally:
            heartbeat_task.cancel()
    finally:
        await manager.disconnect(websocket, auction_id_str)
        # Send updated viewer count to remaining clients
        viewer_count = manager.get_viewer_count(auction_id_str)
        await manager.broadcast_to_auction(auction_id_str, {
            "type": MSG_VIEWER_UPDATE,
            "data": {"viewer_count": viewer_count},
        })


@router.websocket("/ws/auctions/{auction_id}/bid")
async def realtime_bidding(
    websocket: WebSocket,
    auction_id: UUID,
    token: Optional[str] = None,
):
    """Authenticated real-time bidding via WebSocket."""
    auction_id_str = str(auction_id)

    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    # Authenticate user
    async with async_session_factory() as db:
        user = await _get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return

        # Validate auction
        await check_and_update_auction_statuses(db)
        await db.commit()

        auction = await db.get(Auction, auction_id)
        if not auction:
            await websocket.close(code=4004, reason="Auction not found")
            return
        if auction.status != AuctionStatus.ACTIVE:
            await websocket.close(code=4009, reason="Auction is not active")
            return

        user_id = user.id
        username = user.username

    # Accept connection
    await manager.connect(websocket, auction_id_str)

    try:
        heartbeat_task = asyncio.create_task(heartbeat(websocket))

        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == MSG_PLACE_BID:
                    try:
                        amount = Decimal(str(data.get("amount", "0")))
                    except (InvalidOperation, TypeError):
                        await websocket.send_json({
                            "type": MSG_BID_REJECTED,
                            "reason": "Invalid bid amount",
                            "code": "INVALID_AMOUNT",
                        })
                        continue

                    # Process bid
                    async with async_session_factory() as db:
                        try:
                            # 1. Update statuses based on current time first
                            await check_and_update_auction_statuses(db)

                            # 2. Get the auction with lock
                            query = select(Auction).where(Auction.id == auction_id)
                            if db.bind and db.bind.dialect.name == "postgresql":
                                query = query.with_for_update()

                            result = await db.execute(query)
                            auction = result.scalar_one_or_none()

                            if not auction:
                                raise ValueError("Auction not found")

                            if auction.status != AuctionStatus.ACTIVE.value:
                                raise ValueError("Auction is not active")

                            now = datetime.now(timezone.utc)
                            ends_at = auction.ends_at.replace(tzinfo=timezone.utc) if auction.ends_at.tzinfo is None else auction.ends_at
                            if ends_at <= now:
                                raise ValueError("Auction has ended")

                            if auction.seller_id == user_id:
                                raise ValueError("Sellers cannot bid on own auction")

                            min_amount = auction.current_price + auction.bid_increment
                            if amount < min_amount:
                                raise ValueError(f"Bid too low. Minimum: {min_amount}")

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
                                bidder_id=user_id,
                                amount=amount,
                                is_winning=True,
                            )
                            db.add(bid)

                            # Update auction
                            auction.current_price = amount
                            auction.total_bids = (auction.total_bids or 0) + 1
                            db.add(auction)
                            await db.flush()

                            # Create audit log
                            audit = AuditLog(
                                entity_type="bid",
                                entity_id=bid.id,
                                action="bid_placed",
                                actor_id=user_id,
                                new_value={
                                    "amount": str(amount),
                                    "auction_id": str(auction_id),
                                    "previous_price": str(auction.current_price),
                                },
                            )
                            db.add(audit)
                            await db.flush()
                            await db.commit()

                            next_minimum = str(auction.current_price + auction.bid_increment)

                            # Send BID_ACCEPTED to bidder
                            await websocket.send_json({
                                "type": MSG_BID_ACCEPTED,
                                "data": {
                                    "bid_id": str(bid.id),
                                    "amount": str(bid.amount),
                                    "is_winning": bid.is_winning,
                                    "next_minimum": next_minimum,
                                },
                            })

                            # Broadcast NEW_BID to all viewers
                            await manager.broadcast_to_auction(auction_id_str, {
                                "type": MSG_NEW_BID,
                                "data": {
                                    "bid_id": str(bid.id),
                                    "amount": str(bid.amount),
                                    "bidder_username": username,
                                    "auction_id": str(auction_id),
                                    "total_bids": auction.total_bids,
                                    "timestamp": bid.created_at.isoformat(),
                                },
                            })

                        except Exception as e:
                            await db.rollback()
                            error_detail = str(e.detail) if hasattr(e, "detail") else str(e)
                            await websocket.send_json({
                                "type": MSG_BID_REJECTED,
                                "reason": error_detail,
                                "code": "BID_FAILED",
                            })

                elif msg_type == MSG_PING:
                    await websocket.send_json({"type": MSG_PONG})

        except (WebSocketDisconnect, json.JSONDecodeError):
            pass
        except Exception as e:
            print(f"WebSocket bidding error: {e}")
            try:
                await websocket.send_json({
                    "type": MSG_ERROR,
                    "reason": "Internal server error",
                })
            except Exception:
                pass
        finally:
            heartbeat_task.cancel()
    finally:
        await manager.disconnect(websocket, auction_id_str)
