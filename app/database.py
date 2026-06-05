import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv(override=True)

raw_url = os.getenv("DATABASE_URL")


if not raw_url:
    raise ValueError("DATABASE_URL is missing from your environment variables!")

if raw_url.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    SQLALCHEMY_DATABASE_URL = raw_url

SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("&channel_binding=require", "")
SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("sslmode=require", "ssl=require")


Base = declarative_base()
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

async_session_factory = sessionmaker(   
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_session():
    async with async_session_factory() as db:
        try:
            yield db
        finally:
            await db.close()
