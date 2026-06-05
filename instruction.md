# Real-Time Auction Engine — AI Build Specification
### Full Project Blueprint | 10 Chunks | FastAPI · Redis · WebSockets · PostgreSQL

---

> **HOW TO USE THIS DOCUMENT**
> Each chunk is a self-contained prompt you hand to an AI model.
> Always share Chunk 1 as context alongside any subsequent chunk.
> Build and verify each chunk before starting the next.

---

## CHUNK 1 — Project Foundation & Architecture Setup

### Goal
Bootstrap the complete project skeleton: directory structure, all dependencies,
environment configuration, and the FastAPI application factory. Nothing functional
is built yet — this chunk is purely scaffolding.

---

### Tech Stack
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
| Testing | Pytest + httpx + pytest-asyncio |
| Containerization | Docker + Docker Compose |

---

### Project Directory Structure to Create

```
auction-engine/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory & lifespan
│   ├── config.py                # Settings via Pydantic BaseSettings
│   ├── dependencies.py          # Shared FastAPI dependencies (DB session, current user)
│   ├── database.py              # Async SQLAlchemy engine & session factory
│   ├── redis_client.py          # Redis connection pool
│   │
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auction.py
│   │   ├── bid.py
│   │   ├── transaction.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auction.py
│   │   ├── bid.py
│   │   └── transaction.py
│   │
│   ├── routers/                 # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── auctions.py
│   │   ├── bids.py
│   │   └── websocket.py
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── auction_service.py
│   │   ├── bid_service.py
│   │   ├── cache_service.py
│   │   └── notification_service.py
│   │
│   ├── workers/                 # Background job handlers
│   │   ├── __init__.py
│   │   └── auction_worker.py
│   │
│   └── websocket_manager.py     # WebSocket connection registry
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                # Migration files go here
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_auctions.py
│   ├── test_bids.py
│   └── test_websocket.py
│
├── .env                         # Local dev secrets (never commit)
├── .env.example                 # Template for team
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

### requirements.txt (exact packages)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
redis[hiredis]==5.0.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.7.1
pydantic-settings==2.2.1
apscheduler==3.10.4
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
python-multipart==0.0.9
email-validator==2.1.1
```

---

### .env.example to Create

```env
# Application
APP_NAME="Real-Time Auction Engine"
APP_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://auction_user:auction_pass@localhost:5432/auction_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300

# Auction Settings
BID_LOCK_BUFFER_SECONDS=5
WINNER_NOTIFICATION_DELAY_SECONDS=10
```

---

### app/config.py — Settings Class

Use `pydantic_settings.BaseSettings` to load all env vars with type validation.
Include a `@property` that returns `is_production: bool`.
Make it a singleton via `@lru_cache`.

```python
# Pattern to implement:
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Auction Engine"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str
    redis_url: str
    redis_cache_ttl: int = 300
    bid_lock_buffer_seconds: int = 5

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

### app/main.py — Application Factory

Implement using FastAPI `lifespan` context manager (NOT deprecated `on_event`):
- On startup: initialize DB engine, Redis pool, start APScheduler
- On shutdown: close DB connections, close Redis pool, stop APScheduler
- Register all routers with `/api/v1` prefix
- Add CORS middleware allowing all origins in dev
- Add a health check endpoint at `GET /health` returning `{"status": "ok", "version": "1.0.0"}`
- Add global exception handler for `HTTPException` and unhandled `Exception`

---

### app/database.py

```python
# Pattern to implement:
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create async engine with pool_size=10, max_overflow=20
# Create async_sessionmaker with expire_on_commit=False
# Provide get_db() async generator for dependency injection
```

---

### app/redis_client.py

Use `redis.asyncio` with connection pool.
Provide `get_redis()` async dependency.
Include helper functions: `set_json`, `get_json`, `delete_key`, `publish_message`.

---

### AI Model Instructions for Chunk 1

1. Create every file listed in the directory tree — even empty `__init__.py` files.
2. Do NOT implement any route logic yet — only the wiring (app factory, config, db setup).
3. Verify the app starts with `uvicorn app.main:app --reload` without errors.
4. The health check endpoint must return HTTP 200.
5. Write the README.md with setup instructions (clone, create venv, copy .env.example, run migrations, start app).

---
---

## CHUNK 2 — Database Layer: PostgreSQL Models & Alembic Migrations

### Goal
Define all SQLAlchemy ORM models with proper relationships, constraints, and indexes.
Set up Alembic for migration management. The database schema must support
financial-grade data integrity.

---

### Models to Implement

#### 1. `app/models/user.py` — User Model

```
Table: users
Columns:
  - id: UUID (primary key, server_default=uuid_generate_v4())
  - username: VARCHAR(50), unique, not null, indexed
  - email: VARCHAR(255), unique, not null, indexed
  - hashed_password: VARCHAR(255), not null
  - is_active: BOOLEAN, default=True
  - is_verified: BOOLEAN, default=False
  - created_at: TIMESTAMPTZ, server_default=now()
  - updated_at: TIMESTAMPTZ, onupdate=now()

Relationships:
  - auctions: one-to-many (auctions created by user)
  - bids: one-to-many (bids placed by user)
```

#### 2. `app/models/auction.py` — Auction Model

```
Table: auctions
Columns:
  - id: UUID (primary key)
  - title: VARCHAR(200), not null
  - description: TEXT
  - seller_id: UUID, FK → users.id, not null
  - starting_price: NUMERIC(12,2), not null, check > 0
  - reserve_price: NUMERIC(12,2), nullable (hidden reserve)
  - current_price: NUMERIC(12,2), not null (updated on each bid)
  - bid_increment: NUMERIC(10,2), default=1.00
  - status: ENUM('pending','active','locked','completed','cancelled'), default='pending'
  - starts_at: TIMESTAMPTZ, not null
  - ends_at: TIMESTAMPTZ, not null
  - winner_id: UUID, FK → users.id, nullable
  - total_bids: INTEGER, default=0
  - created_at: TIMESTAMPTZ, server_default=now()
  - updated_at: TIMESTAMPTZ, onupdate=now()

Constraints:
  - CHECK (ends_at > starts_at)
  - CHECK (current_price >= starting_price)
  - INDEX on (status, ends_at) for worker queries
  - INDEX on seller_id

Relationships:
  - seller: many-to-one → users
  - winner: many-to-one → users
  - bids: one-to-many → bids
  - transactions: one-to-many → transactions
```

#### 3. `app/models/bid.py` — Bid Model

```
Table: bids
Columns:
  - id: UUID (primary key)
  - auction_id: UUID, FK → auctions.id, not null
  - bidder_id: UUID, FK → users.id, not null
  - amount: NUMERIC(12,2), not null, check > 0
  - is_winning: BOOLEAN, default=False
  - ip_address: INET, nullable (for fraud detection)
  - created_at: TIMESTAMPTZ, server_default=now()

Constraints:
  - INDEX on (auction_id, amount DESC) — critical for winner lookup
  - INDEX on bidder_id
  - This table is APPEND-ONLY — no updates or deletes ever

IMPORTANT: Never add UPDATE or DELETE operations on this table anywhere in the codebase.
```

#### 4. `app/models/transaction.py` — Transaction Model

```
Table: transactions
Columns:
  - id: UUID (primary key)
  - auction_id: UUID, FK → auctions.id, not null
  - buyer_id: UUID, FK → users.id, not null
  - seller_id: UUID, FK → users.id, not null
  - amount: NUMERIC(12,2), not null
  - status: ENUM('pending','processing','completed','failed','refunded')
  - reference_number: VARCHAR(64), unique, not null (format: TXN-{uuid4 short})
  - created_at: TIMESTAMPTZ, server_default=now()
  - completed_at: TIMESTAMPTZ, nullable

INDEX on reference_number (unique lookup)
INDEX on (buyer_id, status)
INDEX on (seller_id, status)
```

#### 5. `app/models/audit_log.py` — Immutable Audit Log

```
Table: audit_logs
Columns:
  - id: BIGSERIAL (primary key, sequential for ordering)
  - entity_type: VARCHAR(50), not null (e.g. 'auction', 'bid', 'transaction')
  - entity_id: UUID, not null
  - action: VARCHAR(100), not null (e.g. 'bid_placed', 'auction_locked', 'winner_notified')
  - actor_id: UUID, nullable (null for system actions)
  - old_value: JSONB, nullable
  - new_value: JSONB, nullable
  - metadata: JSONB, nullable (IP, user agent, etc.)
  - created_at: TIMESTAMPTZ, server_default=now()

CRITICAL CONSTRAINTS:
  - NO updated_at column (records must never be updated)
  - Apply PostgreSQL row-level security: GRANT INSERT only (no UPDATE/DELETE)
  - INDEX on (entity_type, entity_id) for fast history lookup
  - INDEX on created_at for time-range queries
  - INDEX on actor_id

APPEND-ONLY RULE: Never import this model in any UPDATE or DELETE context.
```

---

### Alembic Setup Instructions

1. Run `alembic init alembic` and configure `alembic/env.py`:
   - Import `Base` from `app.database`
   - Set `target_metadata = Base.metadata`
   - Use async engine via `run_async_migrations()` function
   - Load `DATABASE_URL` from settings

2. Create initial migration: `alembic revision --autogenerate -m "initial_schema"`

3. In the migration file, manually add after the table creation:
```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Audit log protection (append-only)
REVOKE UPDATE, DELETE ON audit_logs FROM PUBLIC;
```

4. Apply migrations: `alembic upgrade head`

---

### Shared Base Model Mixin

Create `app/models/base.py` with a `TimestampMixin`:
```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMPTZ, onupdate=func.now(), nullable=True
    )
```

---

### AI Model Instructions for Chunk 2

1. Use SQLAlchemy 2.x `Mapped` and `mapped_column` syntax — NOT the old Column() syntax.
2. All primary keys must be UUID type with `server_default=text("uuid_generate_v4()")`.
3. All monetary fields use `Numeric(12, 2)` — never `Float`.
4. Create the AuctionStatus and TransactionStatus enums as Python `enum.Enum` classes
   AND as PostgreSQL native ENUM types in the migration.
5. Export all models from `app/models/__init__.py` so Alembic can discover them.
6. Test by running `alembic upgrade head` — it must complete with zero errors.
7. Verify table creation in psql: `\dt` should show all 5 tables.

---
---

## CHUNK 3 — Authentication & Security System

### Goal
Build a complete JWT-based authentication system: user registration, login,
token refresh, password hashing, and protected route dependencies.
All password operations use bcrypt via Passlib.

---

### Pydantic Schemas — `app/schemas/user.py`

```python
# Schemas to create:

class UserCreate(BaseModel):
    username: str  # min 3, max 50 chars, regex: ^[a-zA-Z0-9_]+$
    email: EmailStr
    password: str  # min 8 chars, must contain letter + digit

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user ID
    exp: datetime
    type: str  # "access" or "refresh"

class PasswordChange(BaseModel):
    current_password: str
    new_password: str  # same validation as UserCreate.password
```

---

### `app/services/auth_service.py` — Core Auth Logic

Implement these functions:

```python
# 1. Password hashing
def hash_password(password: str) -> str:
    # Use passlib CryptContext with bcrypt scheme
    # rounds=12 for production security

# 2. Password verification
def verify_password(plain: str, hashed: str) -> bool:
    # Use same CryptContext

# 3. Create access token
def create_access_token(user_id: UUID) -> str:
    # Payload: {"sub": str(user_id), "type": "access", "exp": now + ACCESS_TOKEN_EXPIRE_MINUTES}
    # Sign with SECRET_KEY + ALGORITHM

# 4. Create refresh token
def create_refresh_token(user_id: UUID) -> str:
    # Payload: {"sub": str(user_id), "type": "refresh", "exp": now + REFRESH_TOKEN_EXPIRE_DAYS}
    # Longer expiry, different type claim

# 5. Decode and validate token
def decode_token(token: str) -> TokenPayload:
    # Raises HTTPException 401 on expired or invalid token
    # Validates "type" claim matches expected type

# 6. Register user
async def register_user(db: AsyncSession, data: UserCreate) -> User:
    # Check username uniqueness → 409 if taken
    # Check email uniqueness → 409 if taken
    # Hash password
    # Insert user
    # Write to audit_log: action="user_registered", entity_type="user"
    # Return user

# 7. Authenticate user
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    # Lookup by email
    # verify_password
    # Raise 401 "Invalid credentials" (never specify which field is wrong)
    # Write to audit_log: action="user_login"
    # Return user
```

---

### `app/dependencies.py` — FastAPI Dependencies

```python
# Dependency 1: Database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Dependency 2: Get current user from Bearer token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)
    if payload.type != "access":
        raise HTTPException(401, "Invalid token type")
    user = await db.get(User, UUID(payload.sub))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user

# Dependency 3: Optional current user (for public endpoints)
async def get_optional_user(...) -> Optional[User]:
    # Same as get_current_user but returns None instead of raising
```

---

### `app/routers/auth.py` — Auth Endpoints

```
POST /api/v1/auth/register
  Body: UserCreate
  Response 201: UserResponse
  Errors: 409 (username/email taken), 422 (validation)

POST /api/v1/auth/login
  Body: OAuth2PasswordRequestForm (username=email, password=password)
  Response 200: Token
  Errors: 401 (invalid credentials)

POST /api/v1/auth/refresh
  Body: {"refresh_token": "..."}
  Response 200: Token (new access + refresh tokens)
  Errors: 401 (invalid/expired refresh token)

GET /api/v1/auth/me
  Header: Authorization: Bearer <token>
  Response 200: UserResponse
  Errors: 401

PUT /api/v1/auth/me/password
  Header: Authorization: Bearer <token>
  Body: PasswordChange
  Response 200: {"message": "Password updated successfully"}
  Errors: 400 (wrong current password), 401
```

---

### Security Requirements

- NEVER log passwords, tokens, or hashed passwords anywhere
- NEVER return hashed_password in any response schema — exclude it explicitly
- Rate limit login endpoint: max 5 attempts per IP per 15 minutes
  (implement using Redis: key `rate_limit:login:{ip}`, TTL=900)
- All token errors must return 401 with message "Could not validate credentials"
  and `WWW-Authenticate: Bearer` header
- bcrypt rounds must be configurable via settings (default 12)
- Store the OAuth2 scheme as: `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`

---

### AI Model Instructions for Chunk 3

1. Use `python-jose` for JWT operations, NOT PyJWT.
2. The login form must use `OAuth2PasswordRequestForm` (FastAPI standard) so Swagger UI works.
3. Password validation must happen in Pydantic validators using `@field_validator`.
4. Test all endpoints manually via Swagger UI at `/docs` before finishing.
5. Verify: registering twice with the same email returns 409, not 500.
6. Verify: accessing `/api/v1/auth/me` with no token returns 401, not 422.
7. Write at least 5 test cases in `tests/test_auth.py` covering happy path + error cases.

---
---

## CHUNK 4 — Core Auction REST API

### Goal
Build the complete REST API for auction lifecycle management: creating auctions,
listing/filtering them, placing bids, retrieving bid history.
All business logic goes in the service layer, not the router.

---

### Pydantic Schemas — `app/schemas/auction.py`

```python
class AuctionCreate(BaseModel):
    title: str  # min 5, max 200 chars
    description: Optional[str] = None
    starting_price: Decimal  # > 0, max 2 decimal places
    reserve_price: Optional[Decimal] = None  # must be > starting_price if set
    bid_increment: Decimal = Decimal("1.00")  # > 0
    starts_at: datetime  # must be in the future
    ends_at: datetime  # must be > starts_at, max 30 days from now

class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    # Only allowed when status == 'pending'

class AuctionResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    seller_id: UUID
    starting_price: Decimal
    current_price: Decimal
    bid_increment: Decimal
    status: str
    starts_at: datetime
    ends_at: datetime
    winner_id: Optional[UUID]
    total_bids: int
    created_at: datetime
    # NOTE: reserve_price is NEVER included in the response (hidden reserve)
    model_config = ConfigDict(from_attributes=True)

class AuctionListResponse(BaseModel):
    items: List[AuctionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

---

### Pydantic Schemas — `app/schemas/bid.py`

```python
class BidCreate(BaseModel):
    amount: Decimal  # must be >= current_price + bid_increment

class BidResponse(BaseModel):
    id: UUID
    auction_id: UUID
    bidder_id: UUID
    amount: Decimal
    is_winning: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

---

### `app/routers/auctions.py` — Auction Endpoints

```
GET /api/v1/auctions
  Query params: status (filter), page (default 1), page_size (default 20, max 100),
                search (title contains), seller_id
  Response 200: AuctionListResponse
  Auth: Optional (public endpoint)

POST /api/v1/auctions
  Body: AuctionCreate
  Response 201: AuctionResponse
  Auth: Required
  Rules: seller = current_user

GET /api/v1/auctions/{auction_id}
  Response 200: AuctionResponse
  Errors: 404

PUT /api/v1/auctions/{auction_id}
  Body: AuctionUpdate
  Response 200: AuctionResponse
  Auth: Required (must be seller)
  Rules: only editable when status == 'pending'
  Errors: 403, 404, 409 (wrong status)

DELETE /api/v1/auctions/{auction_id}
  Response 204
  Auth: Required (must be seller)
  Rules: only deletable when status == 'pending'
  Errors: 403, 404, 409

GET /api/v1/auctions/{auction_id}/bids
  Query params: page, page_size
  Response 200: Paginated list of BidResponse
  Auth: Optional

GET /api/v1/auctions/my/created
  Response 200: AuctionListResponse (auctions I created)
  Auth: Required

GET /api/v1/auctions/my/participated
  Response 200: AuctionListResponse (auctions I bid on)
  Auth: Required
```

---

### `app/routers/bids.py` — Bid Placement

```
POST /api/v1/auctions/{auction_id}/bids
  Body: BidCreate
  Response 201: BidResponse
  Auth: Required
  Rules (all must be checked in order):
    1. Auction must exist → 404
    2. Auction status must be 'active' → 409 "Auction is not active"
    3. ends_at must be in the future → 409 "Auction has ended"
    4. Bidder cannot be the seller → 403 "Sellers cannot bid on own auction"
    5. amount >= current_price + bid_increment → 422 "Bid too low. Minimum: {min_amount}"
    6. Insert bid record
    7. Update auction.current_price = amount
    8. Increment auction.total_bids
    9. Mark previous winning bid as is_winning=False
    10. Mark new bid as is_winning=True
    11. Write to audit_log
    12. Invalidate Redis cache for this auction
    13. Return BidResponse
```

---

### `app/services/auction_service.py` — Business Logic

```python
# Functions to implement:

async def create_auction(db, seller_id, data: AuctionCreate) -> Auction:
    # Validate starts_at > now, ends_at > starts_at
    # Set current_price = starting_price
    # Write audit log: action="auction_created"

async def get_auction_or_404(db, auction_id) -> Auction:
    # Raise 404 if not found

async def list_auctions(db, filters, pagination) -> tuple[list[Auction], int]:
    # Build dynamic WHERE clause based on filters
    # Use SELECT COUNT(*) for pagination total (separate query)
    # Use LIMIT/OFFSET for pagination

async def place_bid(db, auction_id, bidder_id, data: BidCreate) -> Bid:
    # Use SELECT ... FOR UPDATE on auction row to prevent race conditions
    # All 13 validation + update steps from router spec above
    # Entire operation wrapped in a single DB transaction

async def get_bid_history(db, auction_id, pagination) -> tuple[list[Bid], int]:
    # Order by amount DESC, created_at DESC
```

---

### Race Condition Prevention

The `place_bid` function MUST use pessimistic locking:

```python
# Inside place_bid, use SELECT FOR UPDATE to lock the auction row
result = await db.execute(
    select(Auction)
    .where(Auction.id == auction_id)
    .with_for_update()  # Locks the row until transaction commits
)
auction = result.scalar_one_or_none()
```

This prevents two simultaneous bids from both passing the minimum price check.

---

### Error Response Format

All API errors must use this consistent format:
```json
{
  "detail": "Human readable error message",
  "code": "MACHINE_READABLE_CODE",
  "field": "field_name_if_applicable"
}
```

Create a custom `AuctionError` exception class and a global handler in `main.py`.

---

### AI Model Instructions for Chunk 4

1. All database operations must be async using `await`.
2. Never put SQL queries or ORM calls directly in router functions — always in services.
3. The bid placement must be wrapped in a DB transaction using `async with db.begin()`.
4. Pagination must never use Python-side slicing — use DB-level LIMIT/OFFSET.
5. The `GET /api/v1/auctions` endpoint must support filtering without SQL injection risk.
6. Test: place two concurrent bids and verify only one wins (use asyncio.gather in tests).
7. Verify: a seller cannot bid on their own auction — returns 403.
8. Write tests in `tests/test_auctions.py` and `tests/test_bids.py`.

---
---

## CHUNK 5 — Redis Caching Layer

### Goal
Implement a caching strategy to eliminate repeated PostgreSQL reads during
active bidding wars. Use Redis as a cache-aside store for hot auction data
and current bid prices.

---

### `app/services/cache_service.py` — Cache Operations

```python
# All functions are async. Redis client injected via dependency.

# KEY SCHEMA (document these as constants at top of file):
AUCTION_KEY = "auction:{auction_id}"              # TTL: 5 min
ACTIVE_AUCTIONS_KEY = "auctions:active"           # TTL: 60 sec
BID_LOCK_KEY = "bid_lock:{auction_id}"            # TTL: bid lock buffer (5 sec)
CURRENT_PRICE_KEY = "auction:{auction_id}:price"  # TTL: no expiry, deleted on update
RATE_LIMIT_KEY = "rate_limit:{action}:{identifier}"

# Functions to implement:

async def cache_auction(redis, auction: Auction) -> None:
    """Serialize auction to JSON and store with TTL."""
    # Use auction.model_dump() equivalent for SQLAlchemy model
    # Handle Decimal serialization (convert to str)
    # Handle datetime serialization (convert to ISO string)
    # TTL = REDIS_CACHE_TTL from settings

async def get_cached_auction(redis, auction_id: UUID) -> Optional[dict]:
    """Return cached auction dict or None if cache miss."""

async def invalidate_auction_cache(redis, auction_id: UUID) -> None:
    """Delete all cached keys for an auction."""
    # Delete: AUCTION_KEY, CURRENT_PRICE_KEY
    # Do NOT delete BID_LOCK_KEY (that's separate)

async def cache_current_price(redis, auction_id: UUID, price: Decimal) -> None:
    """Store only the current price — fastest possible read."""
    # Store as string representation of Decimal

async def get_current_price(redis, auction_id: UUID) -> Optional[Decimal]:
    """Get current price from cache, returns None on miss."""

async def get_active_auctions_cached(redis) -> Optional[List[dict]]:
    """Return list of active auctions from cache."""

async def set_active_auctions_cache(redis, auctions: List[dict]) -> None:
    """Cache list of active auctions with short TTL (60s)."""

async def check_rate_limit(redis, action: str, identifier: str,
                           max_requests: int, window_seconds: int) -> bool:
    """
    Returns True if request is allowed, False if rate limited.
    Use Redis INCR + EXPIRE pattern.
    """
    key = RATE_LIMIT_KEY.format(action=action, identifier=identifier)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    return count <= max_requests

async def acquire_bid_lock(redis, auction_id: UUID) -> bool:
    """
    Distributed lock for bid processing.
    Returns True if lock acquired, False if another bid is processing.
    Use SET NX EX pattern (atomic).
    """
    key = BID_LOCK_KEY.format(auction_id=auction_id)
    result = await redis.set(key, "1", nx=True, ex=5)  # 5 second lock
    return result is not None

async def release_bid_lock(redis, auction_id: UUID) -> None:
    """Release bid processing lock."""
    key = BID_LOCK_KEY.format(auction_id=auction_id)
    await redis.delete(key)
```

---

### Cache Integration in Services

Modify `auction_service.py` to use cache-aside pattern:

```python
# In get_auction_or_404:
async def get_auction_or_404(db, redis, auction_id) -> Auction:
    # 1. Try cache first
    cached = await get_cached_auction(redis, auction_id)
    if cached:
        return deserialize_auction(cached)  # return Pydantic/dict, not ORM object
    # 2. Cache miss → query DB
    auction = await db.get(Auction, auction_id)
    if not auction:
        raise HTTPException(404, "Auction not found")
    # 3. Populate cache
    await cache_auction(redis, auction)
    return auction
```

Cache integration points (modify these service functions):
- `get_auction_or_404` → try cache before DB
- `place_bid` → invalidate cache after successful bid, update price cache
- `list_auctions` (active only) → use active auctions cache
- `auction_worker.lock_auction` → invalidate cache on status change

---

### Distributed Bid Lock Integration

Modify `place_bid` in `auction_service.py` to use the distributed lock:

```python
async def place_bid(db, redis, auction_id, bidder_id, data):
    # Acquire distributed lock BEFORE the DB transaction
    lock_acquired = await acquire_bid_lock(redis, auction_id)
    if not lock_acquired:
        raise HTTPException(429, "Another bid is being processed. Try again.")
    try:
        # ... all existing bid logic with DB FOR UPDATE ...
        await invalidate_auction_cache(redis, auction_id)
        await cache_current_price(redis, auction_id, data.amount)
    finally:
        # ALWAYS release lock, even on error
        await release_bid_lock(redis, auction_id)
```

---

### Cache Serialization Helpers

```python
# In cache_service.py — handle non-JSON-serializable types

def serialize_for_cache(obj: dict) -> str:
    """Convert Decimal→str, datetime→ISO string, UUID→str before JSON dump."""

def deserialize_from_cache(data: str) -> dict:
    """Reverse: parse JSON and convert str→Decimal for price fields."""
```

---

### Redis Health Check

Add to the `GET /health` endpoint:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```
Ping both services on health check. Return 503 if either is down.

---

### AI Model Instructions for Chunk 5

1. Never use `redis.get()` without checking for `None` — always handle cache misses.
2. All cache keys must be defined as module-level string constants — no magic strings.
3. Decimal values must be serialized as strings in Redis (JSON cannot represent Decimal).
4. The bid lock uses Redis SET NX EX — this is atomic and safe for distributed use.
5. Cache should be a performance optimization only — if Redis is down, the app must
   still function by falling back to DB queries (wrap all cache reads in try/except).
6. Test cache hit vs miss by checking Redis keys with `redis-cli KEYS "*"` during tests.
7. Test the rate limiter: call login 6 times in 15 minutes → 6th must return 429.

---
---

## CHUNK 6 — WebSocket Real-Time Bidding Engine

### Goal
Build the WebSocket layer that broadcasts live bid updates to all clients
watching an auction. Implement real-time bid validation and instant push
notifications to every connected viewer.

---

### `app/websocket_manager.py` — Connection Registry

```python
from collections import defaultdict
from fastapi import WebSocket
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        # Room-based: auction_id → set of active WebSocket connections
        self.active_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, auction_id: str) -> None:
        """Accept connection and register in auction room."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[auction_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, auction_id: str) -> None:
        """Remove connection from auction room."""
        async with self._lock:
            self.active_connections[auction_id].discard(websocket)
            if not self.active_connections[auction_id]:
                del self.active_connections[auction_id]

    async def broadcast_to_auction(self, auction_id: str, message: dict) -> None:
        """Send JSON message to ALL clients watching an auction."""
        connections = self.active_connections.get(auction_id, set()).copy()
        dead = set()
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.add(websocket)
        # Clean up dead connections
        async with self._lock:
            self.active_connections[auction_id] -= dead

    def get_viewer_count(self, auction_id: str) -> int:
        return len(self.active_connections.get(auction_id, set()))

# Singleton instance — import this in routers
manager = ConnectionManager()
```

---

### `app/routers/websocket.py` — WebSocket Endpoints

#### Endpoint 1: Auction Live Feed (Public)

```
WS /ws/auctions/{auction_id}
Purpose: Broadcast-only feed. Clients connect to receive live bid updates.
Auth: Optional (JWT token via query param `?token=...`)
```

```python
@router.websocket("/ws/auctions/{auction_id}")
async def auction_live_feed(
    websocket: WebSocket,
    auction_id: UUID,
    token: Optional[str] = None,   # Query param for auth
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    # 1. Validate auction exists and is active
    # 2. Authenticate user if token provided (optional)
    # 3. Connect to manager room
    # 4. Send initial state to the new client:
    #    {"type": "INIT", "data": {auction data, current_price, viewer_count}}
    # 5. Send viewer count update to ALL clients in room
    # 6. Keep connection alive with heartbeat (ping every 30s)
    # 7. On disconnect: clean up, send updated viewer count to remaining clients
```

#### Endpoint 2: Bid Placement via WebSocket

```
WS /ws/auctions/{auction_id}/bid
Purpose: Authenticated real-time bidding
Auth: REQUIRED (JWT token via query param or first message)
```

```python
@router.websocket("/ws/auctions/{auction_id}/bid")
async def realtime_bidding(
    websocket: WebSocket,
    auction_id: UUID,
    token: str,  # Required query param
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    # 1. Validate and decode JWT token → get user
    # 2. Validate auction is active
    # 3. Accept connection
    # 4. Enter receive loop:
    #    while True:
    #      data = await websocket.receive_json()
    #      if data["type"] == "PLACE_BID":
    #          result = await handle_websocket_bid(...)
    #          await websocket.send_json(result)
    #      elif data["type"] == "PING":
    #          await websocket.send_json({"type": "PONG"})
    # 5. On WebSocketDisconnect: clean up gracefully
```

---

### Message Protocol (JSON)

Define ALL message types as constants:

```python
# Client → Server messages
MSG_PLACE_BID = "PLACE_BID"   # {"type": "PLACE_BID", "amount": "150.00"}
MSG_PING = "PING"

# Server → Client messages
MSG_BID_ACCEPTED = "BID_ACCEPTED"    # Sent to bidder
MSG_BID_REJECTED = "BID_REJECTED"    # Sent to bidder with reason
MSG_NEW_BID = "NEW_BID"              # Broadcast to ALL viewers
MSG_AUCTION_LOCKED = "AUCTION_LOCKED"  # Broadcast when auction ends
MSG_WINNER_ANNOUNCED = "WINNER_ANNOUNCED"  # Broadcast winner
MSG_INIT = "INIT"                    # Initial state for new connection
MSG_VIEWER_UPDATE = "VIEWER_UPDATE"  # Updated viewer count
MSG_ERROR = "ERROR"
MSG_PONG = "PONG"
```

Message payload examples:
```json
// MSG_NEW_BID (broadcast to all in room)
{
  "type": "NEW_BID",
  "data": {
    "bid_id": "uuid",
    "amount": "150.00",
    "bidder_username": "john_doe",  // NOT bidder_id for privacy
    "auction_id": "uuid",
    "total_bids": 5,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}

// MSG_BID_ACCEPTED (only to the bidder)
{
  "type": "BID_ACCEPTED",
  "data": {
    "bid_id": "uuid",
    "amount": "150.00",
    "is_winning": true,
    "next_minimum": "151.00"
  }
}

// MSG_BID_REJECTED (only to the bidder)
{
  "type": "BID_REJECTED",
  "reason": "Bid too low. Minimum bid is $151.00",
  "code": "BID_TOO_LOW",
  "minimum_amount": "151.00"
}
```

---

### Bid Flow via WebSocket

When a `PLACE_BID` message arrives on the bidding WebSocket:

```
1. Parse and validate amount (Decimal, > 0)
2. Call bid_service.place_bid() — same service used by REST API
3. If successful:
   a. Send MSG_BID_ACCEPTED to the bidder's WebSocket
   b. Broadcast MSG_NEW_BID to ALL connections in auction room (via manager)
4. If ValidationError / HTTPException:
   a. Send MSG_BID_REJECTED to bidder only
5. If unexpected error:
   a. Send MSG_ERROR to bidder
   b. Log the error server-side
```

This ensures REST and WebSocket bidding use identical validation logic.

---

### Heartbeat / Keepalive

```python
async def heartbeat(websocket: WebSocket, interval: int = 30):
    """Send PING every 30 seconds to keep connection alive."""
    while True:
        await asyncio.sleep(interval)
        try:
            await websocket.send_json({"type": "PING"})
        except Exception:
            break

# Run as background task alongside the main receive loop:
# asyncio.create_task(heartbeat(websocket))
```

---

### AI Model Instructions for Chunk 6

1. Use `asyncio.Lock()` in ConnectionManager to prevent race conditions on
   connection registration — multiple bids can arrive simultaneously.
2. WebSocket token auth must use query params (headers are not accessible in
   standard browser WebSocket API).
3. Always wrap `websocket.receive_json()` in try/except for `WebSocketDisconnect`
   and `json.JSONDecodeError`.
4. The heartbeat must run as `asyncio.create_task()` — not blocking the receive loop.
5. NEVER send raw user IDs in broadcast messages — use usernames only.
6. Test: connect two browser tabs to the same auction WebSocket and verify both
   receive the `MSG_NEW_BID` broadcast when a bid is placed via REST API.
7. Test: disconnecting one tab must not affect the other tab's connection.

---
---

## CHUNK 7 — Financial Transactions & Immutable Audit Trail

### Goal
Implement the transaction creation system and the append-only audit logging
that guarantees complete financial traceability. Every significant system
event must produce an audit record.

---

### `app/schemas/transaction.py`

```python
class TransactionResponse(BaseModel):
    id: UUID
    auction_id: UUID
    buyer_id: UUID
    seller_id: UUID
    amount: Decimal
    status: str
    reference_number: str
    created_at: datetime
    completed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: Optional[UUID]
    new_value: Optional[dict]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # NOTE: old_value and metadata are NOT returned in public API for security
```

---

### `app/services/audit_service.py` — Audit Logging

```python
from decimal import Decimal
from uuid import UUID
import json

async def write_audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: UUID,
    action: str,
    actor_id: Optional[UUID] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    metadata: Optional[dict] = None
) -> AuditLog:
    """
    Append a single immutable record to audit_logs.
    This function NEVER raises — if audit logging fails, it logs the error
    but does NOT roll back the parent transaction.
    All Decimal values must be converted to str before storing as JSONB.
    """

# Convenience wrappers — call these throughout the codebase:

async def log_user_registered(db, user: User, metadata: dict) -> None:
    await write_audit_log(db, "user", user.id, "user_registered",
                          new_value={"username": user.username, "email": user.email},
                          metadata=metadata)

async def log_user_login(db, user: User, metadata: dict) -> None:
    await write_audit_log(db, "user", user.id, "user_login", actor_id=user.id,
                          metadata=metadata)

async def log_auction_created(db, auction: Auction, seller: User) -> None:
    await write_audit_log(db, "auction", auction.id, "auction_created",
                          actor_id=seller.id,
                          new_value={"title": auction.title, "starting_price": str(auction.starting_price)})

async def log_bid_placed(db, bid: Bid, auction: Auction) -> None:
    await write_audit_log(db, "bid", bid.id, "bid_placed",
                          actor_id=bid.bidder_id,
                          new_value={
                              "amount": str(bid.amount),
                              "auction_id": str(auction.id),
                              "previous_price": str(auction.current_price)
                          })

async def log_auction_locked(db, auction: Auction) -> None:
    await write_audit_log(db, "auction", auction.id, "auction_locked",
                          actor_id=None,  # System action
                          old_value={"status": "active"},
                          new_value={"status": "locked", "final_price": str(auction.current_price)})

async def log_winner_determined(db, auction: Auction, winner: User) -> None:
    await write_audit_log(db, "auction", auction.id, "winner_determined",
                          actor_id=None,
                          new_value={"winner_id": str(winner.id),
                                     "winning_amount": str(auction.current_price)})

async def log_transaction_created(db, txn: Transaction) -> None:
    await write_audit_log(db, "transaction", txn.id, "transaction_created",
                          new_value={
                              "reference_number": txn.reference_number,
                              "amount": str(txn.amount),
                              "buyer_id": str(txn.buyer_id),
                              "seller_id": str(txn.seller_id)
                          })
```

---

### `app/services/transaction_service.py` — Transaction Processing

```python
import secrets
import string

def generate_reference_number() -> str:
    """Generate TXN-XXXXXXXXXXXXXXXX (16 uppercase alphanumeric chars)."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(16))
    return f"TXN-{suffix}"

async def create_winner_transaction(
    db: AsyncSession,
    auction: Auction,
    winner_id: UUID
) -> Transaction:
    """
    Called by background worker when auction completes.
    Creates a 'pending' transaction record.
    Writes audit log entry.
    """

async def get_transaction_by_reference(
    db: AsyncSession,
    reference_number: str
) -> Optional[Transaction]:
    """Look up transaction by reference number."""

async def get_transactions_for_user(
    db: AsyncSession,
    user_id: UUID,
    role: str = "buyer"  # or "seller"
) -> List[Transaction]:
    """Get all transactions where user is buyer or seller."""
```

---

### Transaction & Audit Log REST Endpoints

Add to `app/routers/auctions.py` or create `app/routers/transactions.py`:

```
GET /api/v1/transactions
  Query: role=buyer|seller
  Response: List[TransactionResponse]
  Auth: Required
  Returns only transactions belonging to current user

GET /api/v1/transactions/{reference_number}
  Response: TransactionResponse
  Auth: Required (must be buyer or seller of transaction)
  Errors: 403, 404

GET /api/v1/auctions/{auction_id}/audit-log
  Response: List[AuditLogResponse]
  Auth: Required (must be auction seller OR admin)
  Returns full event history for an auction
  Ordered by id ASC (chronological)
  NOTE: old_value and metadata fields are stripped from response
```

---

### Audit Log Invariants (Enforce Everywhere)

These rules must never be violated anywhere in the codebase:

1. Every bid placement must produce an audit log entry in the SAME transaction.
2. Every auction status change must produce an audit log entry.
3. Every transaction creation must produce an audit log entry.
4. Audit log entries are NEVER deleted or updated — no exceptions.
5. If an operation fails and is rolled back, its audit log entry is also rolled back
   (they share the same DB transaction). This is the correct behavior.
6. Financial amounts in audit logs are always stored as strings (never floats).

---

### AI Model Instructions for Chunk 7

1. The audit log table must have NO `updated_at` column — add this check to a test.
2. Write a test that verifies after placing 3 bids, there are exactly 3 `bid_placed`
   audit log entries with correct amounts.
3. `generate_reference_number()` must use `secrets` module (cryptographically random).
4. The audit log response must never include `old_value` or `metadata` in the public
   API (these may contain sensitive data like IP addresses).
5. Write a test that verifies attempting to UPDATE an audit_log row raises a
   database permission error (PostgreSQL REVOKE takes effect).
6. All monetary amounts in JSON (JSONB) fields must be stored as strings.

---
---

## CHUNK 8 — Background Workers & Auction Lifecycle Automation

### Goal
Build async background workers that monitor auction deadlines, automatically
transition auction states, lock sessions, determine winners, create transactions,
and trigger winner notifications — all without manual intervention.

---

### `app/workers/auction_worker.py` — Worker Functions

#### Worker 1: Activate Pending Auctions

```python
async def activate_pending_auctions(db: AsyncSession, redis) -> int:
    """
    Runs every 60 seconds.
    Find all auctions WHERE status='pending' AND starts_at <= NOW().
    Update status → 'active'.
    Invalidate their cache entries.
    Write audit log for each: action="auction_activated"
    Broadcast via WebSocket: MSG_AUCTION_ACTIVATED to room.
    Returns count of activated auctions.
    """
```

#### Worker 2: Lock Expired Active Auctions

```python
async def lock_expired_auctions(db: AsyncSession, redis, ws_manager: ConnectionManager) -> int:
    """
    Runs every 30 seconds (frequent check for accuracy).
    Find all auctions WHERE status='active' AND ends_at <= NOW().
    For each expired auction:
      1. Update status → 'locked' (use UPDATE ... WHERE id=? AND status='active' to prevent double-locking)
      2. Invalidate Redis cache
      3. Broadcast MSG_AUCTION_LOCKED to all WebSocket clients in room
      4. Write audit log: action="auction_locked"
      5. Trigger winner determination (call determine_winner)
    Returns count of locked auctions.
    """
```

#### Worker 3: Determine Winner & Create Transaction

```python
async def determine_winner(db: AsyncSession, auction: Auction) -> Optional[Bid]:
    """
    Called immediately after auction is locked.
    Find the highest bid: SELECT * FROM bids WHERE auction_id=? ORDER BY amount DESC LIMIT 1
    If winning bid found:
      1. Update auction.winner_id = winning_bid.bidder_id
      2. Update auction.status = 'completed'
      3. Create Transaction record via transaction_service.create_winner_transaction()
      4. Write audit log: action="winner_determined"
      5. Trigger winner notification (call notify_winner)
    If no bids exist:
      1. Update auction.status = 'completed' (no winner)
      2. Write audit log: action="auction_completed_no_bids"
    Returns the winning Bid or None.
    """
```

#### Worker 4: Winner Notification

```python
async def notify_winner(
    db: AsyncSession,
    ws_manager: ConnectionManager,
    auction: Auction,
    winner_id: UUID,
    transaction: Transaction
) -> None:
    """
    1. Broadcast MSG_WINNER_ANNOUNCED to all WebSocket clients in auction room:
       {"type": "WINNER_ANNOUNCED", "data": {
           "auction_id": ...,
           "winner_username": ...,  # NOT winner_id
           "winning_amount": ...,
           "reference_number": ...,  # Transaction reference
       }}
    2. Log notification: write audit log action="winner_notified"
    3. (Simulate email) Log to console: "EMAIL: Winner notification sent to {email}"
       (Real email integration is out of scope — just log it)
    """
```

---

### Scheduler Setup in `app/main.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

# In lifespan startup:
scheduler.add_job(
    activate_pending_auctions_job,
    trigger=IntervalTrigger(seconds=60),
    id="activate_auctions",
    replace_existing=True
)
scheduler.add_job(
    lock_expired_auctions_job,
    trigger=IntervalTrigger(seconds=30),
    id="lock_auctions",
    replace_existing=True
)
scheduler.start()

# In lifespan shutdown:
scheduler.shutdown(wait=False)
```

Wrap each scheduled job in a standalone async function that creates its own
DB session and Redis client (do NOT reuse request-scoped sessions in workers):

```python
async def lock_expired_auctions_job():
    """APScheduler job wrapper with its own DB session."""
    async with async_session_factory() as db:
        redis = await get_redis_client()
        try:
            count = await lock_expired_auctions(db, redis, manager)
            if count > 0:
                logger.info(f"Locked {count} expired auctions")
        except Exception as e:
            logger.error(f"Error in lock_expired_auctions_job: {e}")
```

---

### Race Condition Prevention in Workers

The lock step must be atomic to prevent double-processing when multiple
worker instances run (in production with multiple Uvicorn workers):

```python
# Use optimistic locking: UPDATE only if current status matches
result = await db.execute(
    update(Auction)
    .where(
        Auction.id == auction_id,
        Auction.status == AuctionStatus.ACTIVE  # Guard condition
    )
    .values(status=AuctionStatus.LOCKED)
    .returning(Auction)
)
locked_auction = result.scalar_one_or_none()
if locked_auction is None:
    return  # Another worker already locked it — skip
```

---

### Auction Lifecycle State Machine

```
                    [Worker: activate_pending]
    pending ──────────────────────────────────► active
                                                  │
                                     [Worker: lock_expired]
                                                  │
                                                  ▼
                                               locked
                                                  │
                                    [Worker: determine_winner]
                                                  │
                                                  ▼
                                             completed
                                          (with or without winner)

    pending ─── (seller deletes) ──► cancelled
```

Include this diagram as a comment at the top of `auction_worker.py`.

---

### Logging Requirements for Workers

```python
import logging
logger = logging.getLogger(__name__)

# Required log lines:
logger.info(f"[WORKER] Activated auction {auction.id}: '{auction.title}'")
logger.info(f"[WORKER] Locked auction {auction.id}: final price ${auction.current_price}")
logger.info(f"[WORKER] Winner determined for {auction.id}: user {winner_id}, amount ${amount}")
logger.info(f"[WORKER] Transaction created: {txn.reference_number}")
logger.warning(f"[WORKER] Auction {auction.id} ended with no bids")
logger.error(f"[WORKER] Failed to lock auction {auction.id}: {e}")
```

---

### AI Model Instructions for Chunk 8

1. Workers MUST create their own DB sessions — never accept sessions as parameters
   from outside (APScheduler cannot pass request-scoped dependencies).
2. The `UPDATE ... WHERE status='active'` pattern is critical — test that running
   the lock worker twice on the same auction only locks it once.
3. Broadcast the `MSG_AUCTION_LOCKED` message BEFORE `determine_winner` runs,
   so clients know immediately when bidding ends.
4. `determine_winner` must handle the edge case of zero bids gracefully.
5. Add integration test: create an auction with `ends_at = now() + 5 seconds`,
   wait 10 seconds, run the worker function manually, verify auction is `completed`.
6. Never call `asyncio.sleep()` inside worker functions — the scheduler handles timing.

---
---

## CHUNK 9 — Testing Suite

### Goal
Build a comprehensive test suite covering authentication, auction CRUD,
bid validation, WebSocket behavior, caching, and worker logic.
Tests must be repeatable, isolated, and runnable in CI.

---

### `tests/conftest.py` — Test Fixtures

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Test database URL (separate DB from dev)
TEST_DATABASE_URL = "postgresql+asyncpg://auction_user:auction_pass@localhost:5432/auction_test_db"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test DB engine and run migrations."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide a DB session that rolls back after each test."""
    async with test_engine.begin() as conn:
        session = AsyncSession(bind=conn)
        yield session
        await conn.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    """Provide AsyncClient with overridden DB dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """Create a standard test user."""

@pytest_asyncio.fixture
async def test_seller(db_session) -> User:
    """Create a seller test user."""

@pytest_asyncio.fixture
async def auth_headers(client, test_user) -> dict:
    """Return {'Authorization': 'Bearer <token>'} for test_user."""

@pytest_asyncio.fixture
async def active_auction(db_session, test_seller) -> Auction:
    """Create an active auction with status='active' for testing."""
```

---

### `tests/test_auth.py` — Authentication Tests

Write tests for:
```
✓ test_register_success → 201, returns UserResponse with correct fields
✓ test_register_duplicate_username → 409
✓ test_register_duplicate_email → 409
✓ test_register_weak_password → 422 (no digits)
✓ test_login_success → 200, returns Token with access + refresh
✓ test_login_wrong_password → 401
✓ test_login_nonexistent_email → 401
✓ test_get_me_authenticated → 200, returns own user data
✓ test_get_me_no_token → 401
✓ test_get_me_expired_token → 401
✓ test_refresh_token → 200, new access token different from old
✓ test_change_password_success → 200
✓ test_change_password_wrong_current → 400
✓ test_hashed_password_not_in_response → verify response has no 'hashed_password' key
```

---

### `tests/test_auctions.py` — Auction CRUD Tests

```
✓ test_create_auction_success → 201
✓ test_create_auction_unauthenticated → 401
✓ test_create_auction_past_start_date → 422
✓ test_create_auction_end_before_start → 422
✓ test_list_auctions_pagination → correct page/total fields
✓ test_list_auctions_filter_by_status → only returns matching status
✓ test_get_auction → 200 with correct data
✓ test_get_nonexistent_auction → 404
✓ test_update_auction_as_seller → 200
✓ test_update_auction_as_non_seller → 403
✓ test_update_active_auction → 409 (can't edit active auction)
✓ test_delete_pending_auction → 204
✓ test_delete_active_auction → 409
✓ test_reserve_price_not_in_response → verify 'reserve_price' key absent
```

---

### `tests/test_bids.py` — Bid Logic Tests

```
✓ test_place_bid_success → 201, BidResponse returned
✓ test_place_bid_unauthenticated → 401
✓ test_place_bid_on_inactive_auction → 409
✓ test_place_bid_below_minimum → 422 with minimum amount in error
✓ test_seller_cannot_bid_own_auction → 403
✓ test_bid_updates_current_price → auction.current_price == bid amount after bid
✓ test_bid_increments_total_bids → auction.total_bids +1 after bid
✓ test_multiple_bids_only_one_winning → only latest highest bid is_winning=True
✓ test_bid_creates_audit_log_entry → audit_logs has 1 entry after bid
✓ test_concurrent_bids_one_wins → use asyncio.gather, verify only one bid accepted
✓ test_get_bid_history → returns bids in descending amount order
```

---

### `tests/test_websocket.py` — WebSocket Tests

```
✓ test_connect_to_auction_feed → receives INIT message on connect
✓ test_receives_bid_broadcast → after REST bid placed, WebSocket receives NEW_BID
✓ test_viewer_count_increments → viewer count in VIEWER_UPDATE increases on connect
✓ test_viewer_count_decrements → viewer count decreases after disconnect
✓ test_websocket_bid_placement → send PLACE_BID, receive BID_ACCEPTED
✓ test_websocket_bid_rejected → send low PLACE_BID, receive BID_REJECTED
✓ test_unauthenticated_bidding_ws → connect to bid endpoint without token → rejected
✓ test_auction_locked_broadcast → after worker locks auction, all clients get AUCTION_LOCKED
```

---

### `tests/test_workers.py` — Worker Tests

```
✓ test_activate_pending_auction → auction with past starts_at gets activated
✓ test_does_not_activate_future_auction → future starts_at unchanged
✓ test_lock_expired_auction → auction with past ends_at gets locked
✓ test_lock_only_active_auctions → pending/completed not touched by lock worker
✓ test_determine_winner_with_bids → winner_id set, status='completed'
✓ test_determine_winner_no_bids → status='completed', winner_id=None
✓ test_transaction_created_after_winner → transaction record exists after completion
✓ test_double_lock_prevention → running lock worker twice doesn't create two audit entries
```

---

### Test Configuration

`pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
log_cli = true
log_cli_level = INFO
```

`tests/conftest.py` must also:
- Set `TESTING=true` env var to disable rate limiting in tests
- Mock the APScheduler (disable background jobs during tests)
- Provide a fake Redis using `fakeredis[aioredis]` package

---

### AI Model Instructions for Chunk 9

1. Add `fakeredis[aioredis]` to requirements.txt for Redis mocking in tests.
2. Every test must be completely independent — no shared state between tests.
3. The `db_session` fixture must rollback after every test (not commit).
4. Use `pytest.mark.asyncio` on every async test function.
5. Concurrent bid test must use `asyncio.gather` with at least 5 simultaneous requests.
6. Running `pytest tests/ -v` must result in all tests passing with no warnings.
7. Aim for minimum 80% code coverage: `pytest --cov=app tests/`.

---
---

## CHUNK 10 — Docker, Deployment & Final Integration

### Goal
Containerize the full application stack, wire all services together, add
production-ready configuration, and verify the complete system works
end-to-end.

---

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

---

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://auction_user:auction_pass@postgres:5432/auction_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./app:/app/app  # Hot reload in dev

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: auction_user
      POSTGRES_PASSWORD: auction_pass
      POSTGRES_DB: auction_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auction_user -d auction_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

### `init.sql` — PostgreSQL Initialization

```sql
-- Runs once when container first starts
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For LIKE query optimization

-- Audit log protection
DO $$
BEGIN
    EXECUTE 'REVOKE UPDATE, DELETE ON TABLE audit_logs FROM ' || current_user;
EXCEPTION WHEN others THEN
    NULL;  -- Table may not exist yet (Alembic runs after)
END $$;
```

---

### Production Configuration

Add to `app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Production
    app_env: str = "development"
    debug: bool = False
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[str] = ["*"]  # Restrict in production
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
```

---

### Logging Configuration

Add structured logging in `app/main.py`:

```python
import logging
import sys

def setup_logging(settings: Settings):
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

---

### API Documentation Enhancement

Add to `app/main.py` FastAPI constructor:
```python
app = FastAPI(
    title="Real-Time Auction Engine",
    description="High-performance live bidding API with WebSocket support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "User registration and authentication"},
        {"name": "auctions", "description": "Auction management and lifecycle"},
        {"name": "bids", "description": "Bid placement and history"},
        {"name": "transactions", "description": "Financial transaction records"},
        {"name": "websocket", "description": "Real-time WebSocket connections"},
    ]
)
```

Add `tags=["auth"]` etc. to every router's `APIRouter(prefix=..., tags=[...])`.

---

### End-to-End Verification Checklist

After running `docker compose up`, verify each step manually:

```
□ GET /health → {"status": "ok", "database": "connected", "redis": "connected"}
□ POST /api/v1/auth/register → creates user, returns 201
□ POST /api/v1/auth/login → returns access + refresh tokens
□ GET /api/v1/auth/me → returns user profile
□ POST /api/v1/auctions → creates auction (status: pending)
□ GET /api/v1/auctions → lists auctions with pagination
□ [Wait for starts_at] Worker activates auction → status: active
□ POST /api/v1/auctions/{id}/bids → places bid, returns BidResponse
□ GET /api/v1/auctions/{id}/bids → shows bid history
□ Open WS ws://localhost:8000/ws/auctions/{id} → receives INIT message
□ Place REST bid → WebSocket client receives NEW_BID broadcast
□ [Wait for ends_at] Worker locks auction → WS receives AUCTION_LOCKED
□ Worker determines winner → WS receives WINNER_ANNOUNCED
□ GET /api/v1/transactions → returns transaction record
□ GET /api/v1/auctions/{id}/audit-log → shows full event history
```

---

### Final README.md Structure

Include these sections:
```
# Real-Time Auction Engine
## Architecture Overview (brief diagram in ASCII)
## Tech Stack
## Quick Start (Docker)
## Development Setup (local without Docker)
## API Documentation
## WebSocket Protocol
## Environment Variables Reference
## Running Tests
## Project Structure
```

---

### AI Model Instructions for Chunk 10

1. Run `docker compose up --build` and verify all containers start healthy.
2. Run `docker compose exec app alembic upgrade head` to apply migrations inside container.
3. The app must start with 0 errors in logs — warnings are acceptable.
4. Test the full E2E checklist above before considering this chunk complete.
5. In production mode (`APP_ENV=production`), disable `/docs` and `/redoc` endpoints,
   or secure them behind authentication.
6. Ensure `SECRET_KEY` in `.env.example` has a comment: "MUST be changed in production".
7. Final test: run the full test suite inside Docker:
   `docker compose exec app pytest tests/ -v --cov=app`

---
---

## QUICK REFERENCE — Chunk Build Order

| # | Chunk | Depends On | Estimated Complexity |
|---|---|---|---|
| 1 | Foundation & Setup | Nothing | Low |
| 2 | DB Models & Migrations | Chunk 1 | Medium |
| 3 | Auth & Security | Chunks 1–2 | Medium |
| 4 | Core REST API | Chunks 1–3 | High |
| 5 | Redis Caching | Chunks 1–4 | Medium |
| 6 | WebSocket Engine | Chunks 1–5 | High |
| 7 | Transactions & Audit | Chunks 1–4 | Medium |
| 8 | Background Workers | Chunks 1–7 | Medium |
| 9 | Testing Suite | Chunks 1–8 | High |
| 10 | Docker & Deployment | Chunks 1–9 | Low |

---

## CROSS-CHUNK RULES (Apply in Every Chunk)

These apply to every AI prompt, regardless of which chunk you're building:

1. **Async First** — every database call, Redis call, and I/O operation must be `async/await`.
2. **Never Float Money** — all monetary values use `Decimal` in Python and `NUMERIC(12,2)` in PostgreSQL.
3. **Services Layer** — no ORM queries in router functions; all logic belongs in `app/services/`.
4. **Audit Everything** — every state change must produce an audit log entry.
5. **UUID Primary Keys** — all entity IDs are UUID, never integers.
6. **Consistent Errors** — all HTTP errors follow the `{"detail": ..., "code": ...}` format.
7. **No Magic Strings** — Redis keys, status values, and message types are constants.
8. **Append-Only Tables** — never UPDATE or DELETE from `bids` or `audit_logs` tables.
9. **Graceful Failure** — if Redis is unavailable, fall back to DB. Never let a cache failure crash a request.
10. **Test Every Endpoint** — every router endpoint must have at least one passing pytest test.