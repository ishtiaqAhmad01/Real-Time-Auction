"""FastAPI application factory with lifespan, routers, and exception handlers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, async_session_factory
from app.routers import auth, users, auctions, bids, websocket, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    print("Starting Real-Time Auction Engine (Simplified)...")
    yield
    # Shutdown
    await engine.dispose()
    print("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Real-Time Auction Engine",
    description="Simplified High-performance live bidding API with WebSocket support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(auctions.router)
app.include_router(bids.router)
app.include_router(websocket.router)
app.include_router(transactions.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Check health of app and database."""
    health = {
        "status": "ok",
        "version": "1.0.0",
    }

    # Check database
    try:
        from sqlalchemy import text
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        print(f"CRITICAL DB ERROR: {e}")
        health["database"] = "disconnected"
        health["error_detail"] = str(e)
        health["status"] = "degraded"

    status_code = 200 if health["status"] == "ok" else 503
    return JSONResponse(content=health, status_code=status_code)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
