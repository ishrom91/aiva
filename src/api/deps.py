"""Dependency functions for API endpoints in Aiva AI Bot."""

import asyncio
import hashlib
from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import HTTPException, Request
from sqlalchemy import select

from ..config import settings
from ..database import get_session
from ..models.api_key import APIKey
from ..models.api_request_log import APIRequestLog


async def get_api_key(request: Request) -> APIKey:
    """Get API key from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    raw_key = auth_header.removeprefix("Bearer ").strip()
    if not raw_key:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async with get_session() as session:
        result = await session.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active.is_(True),
            )
        )
        api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key.expires_at is not None:
        expires_at = api_key.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API key expired")

    return api_key


async def check_rate_limit(api_key: APIKey) -> None:
    """Check rate limit for the given API key."""
    limit = api_key.rate_limit or settings.DATA_API_RATE_LIMIT_DEFAULT

    if not settings.REDIS_URL:
        return

    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_key = f"api_rate:{api_key.id}"
        count = await redis_client.incr(redis_key)
        if count == 1:
            await redis_client.expire(redis_key, 3600)
        await redis_client.aclose()

        if count > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        return


async def _write_api_request_log(
    api_key_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
) -> None:
    async with get_session() as session:
        log_entry = APIRequestLog(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
        session.add(log_entry)
        await session.commit()


async def log_api_request(
    api_key: APIKey,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
) -> None:
    """Log API request in the background."""
    asyncio.create_task(
        _write_api_request_log(
            api_key_id=api_key.id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
    )
