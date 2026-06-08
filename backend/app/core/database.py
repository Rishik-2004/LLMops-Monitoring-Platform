"""
Async SQLAlchemy database setup
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
from typing import AsyncGenerator
import structlog

logger = structlog.get_logger()


class Base(DeclarativeBase):
    pass


import ssl as ssl_module
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

def _build_engine_kwargs(db_url: str):
    """
    asyncpg doesn't accept ?sslmode=require in the URL.
    Strip it out and pass ssl=True via connect_args instead.
    """
    parsed = urlparse(db_url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    
    needs_ssl = query_params.pop("sslmode", None) is not None
    
    # Rebuild the URL without sslmode
    new_query = urlencode({k: v[0] for k, v in query_params.items()})
    clean_url = urlunparse(parsed._replace(query=new_query))
    
    connect_args = {}
    if needs_ssl:
        ssl_ctx = ssl_module.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl_module.CERT_NONE
        connect_args["ssl"] = ssl_ctx
    
    return clean_url, connect_args

_db_url, _connect_args = _build_engine_kwargs(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
