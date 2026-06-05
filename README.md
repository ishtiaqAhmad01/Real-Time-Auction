# Real-Time Auction Engine

High-performance live bidding API with WebSocket support, built with FastAPI.

## Architecture Overview

```
┌──────────┐     ┌──────────────────┐     ┌────────────┐
│  Client   │────▶│  FastAPI (REST    │────▶│ PostgreSQL │
│  Browser  │◀────│  + WebSocket)    │◀────│    15+     │
└──────────┘     │                  │     └────────────┘
                 │  APScheduler     │
                 │  (Background     │     ┌────────────┐
                 │   Workers)       │────▶│  Redis 7+  │
                 └──────────────────┘     └────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI (latest stable) |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 15+ |
| Cache | Redis 7+ |
| Real-Time | WebSockets (via FastAPI / Starlette) |
| Auth | JWT (python-jose) + bcrypt (Passlib) |
| Background Tasks | APScheduler (AsyncIOScheduler) |
| Migrations | Alembic |
| Server | Uvicorn |
| Validation | Pydantic v2 |

## Quick Start (Docker)

```bash
# Clone the repository
git clone <repository-url>
cd Real-Time-Auction

# Start all services
docker compose up --build

# Apply database migrations (in a separate terminal)
docker compose exec app alembic upgrade head

# App is now running at http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Development Setup (Local)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your local PostgreSQL and Redis connection details

# Start PostgreSQL and Redis (if not using Docker)
# Ensure PostgreSQL has the uuid-ossp extension:
# CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: GET http://localhost:8000/health

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login (get tokens) |
| POST | /api/v1/auth/refresh | Refresh access token |
| GET | /api/v1/auth/me | Get current user profile |
| GET | /api/v1/auctions | List auctions (with filters) |
| POST | /api/v1/auctions | Create new auction |
| GET | /api/v1/auctions/{id} | Get auction details |
| POST | /api/v1/auctions/{id}/bids | Place a bid |
| GET | /api/v1/auctions/{id}/bids | Get bid history |
| GET | /api/v1/transactions | List user transactions |

## WebSocket Protocol

Connect to live auction feed:
```
ws://localhost:8000/ws/auctions/{auction_id}?token=<optional_jwt>
```

Connect for real-time bidding:
```
ws://localhost:8000/ws/auctions/{auction_id}/bid?token=<required_jwt>
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| INIT | Server → Client | Initial auction state on connect |
| NEW_BID | Server → Client | Broadcast when bid is placed |
| BID_ACCEPTED | Server → Client | Confirmation to bidder |
| BID_REJECTED | Server → Client | Rejection with reason |
| AUCTION_LOCKED | Server → Client | Auction bidding ended |
| WINNER_ANNOUNCED | Server → Client | Winner determined |
| VIEWER_UPDATE | Server → Client | Updated viewer count |
| PLACE_BID | Client → Server | Place a bid |
| PING/PONG | Both | Keepalive |

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| APP_NAME | Application name | Auction Engine |
| APP_ENV | Environment (development/production) | development |
| SECRET_KEY | JWT signing key (**MUST change in prod**) | — |
| DATABASE_URL | PostgreSQL connection string | — |
| REDIS_URL | Redis connection string | — |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT access token TTL | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | JWT refresh token TTL | 7 |
| REDIS_CACHE_TTL | Default cache TTL in seconds | 300 |
| BID_LOCK_BUFFER_SECONDS | Distributed bid lock duration | 5 |

## Project Structure

```
Real-Time-Auction/
├── app/
│   ├── main.py                  # FastAPI app factory & lifespan
│   ├── config.py                # Settings via Pydantic BaseSettings
│   ├── dependencies.py          # Shared FastAPI dependencies
│   ├── database.py              # Async SQLAlchemy engine & session
│   ├── redis_client.py          # Redis connection pool
│   ├── websocket_manager.py     # WebSocket connection registry
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── routers/                 # FastAPI route handlers
│   ├── services/                # Business logic layer
│   └── workers/                 # Background job handlers
├── alembic/                     # Database migrations
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container image
└── requirements.txt             # Python dependencies
```
