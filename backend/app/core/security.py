import hashlib
import hmac
import json
import logging
import secrets
from typing import Any

import redis.exceptions
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

logger = logging.getLogger(__name__)

# Argon2id password hashing engine
_password_hash = PasswordHash((Argon2Hasher(),))

SESSION_COOKIE_NAME = "session_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SESSION_DURATION_SECONDS = 7 * 24 * 60 * 60  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2id hash."""
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except (PwdlibError, ValueError, TypeError):
        return False


def generate_session_token() -> str:
    """Generate a high-entropy random session token."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Compute SHA-256 hash of a session token for secure database lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """Constant-time verification of CSRF tokens."""
    if not token or not expected_token:
        return False
    return hmac.compare_digest(token, expected_token)


# Redis session caching with PostgreSQL fallback
_redis_client = None
_redis_available = True


def get_redis_client():
    """Lazily initialize and return Redis client if available."""
    global _redis_client, _redis_available
    if not _redis_available:
        return None

    if _redis_client is None:
        try:
            import redis.asyncio as aioredis

            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2,
                socket_timeout=0.2,
            )
        except (redis.exceptions.RedisError, OSError, TimeoutError) as e:
            logger.debug(f"Redis not available, continuing with database fallback: {e}")
            _redis_available = False
            _redis_client = None
    return _redis_client


async def cache_session_in_redis(
    token_hash: str,
    session_data: dict[str, Any],
    ttl_seconds: int = SESSION_DURATION_SECONDS,
) -> bool:
    """Attempt to cache session in Redis. Returns False if Redis is unavailable."""
    global _redis_available
    client = get_redis_client()
    if client is None:
        return False
    try:
        key = f"session:{token_hash}"
        await client.set(key, json.dumps(session_data), ex=ttl_seconds)
        return True
    except (redis.exceptions.RedisError, OSError, TimeoutError) as e:
        logger.debug(f"Failed to cache session in Redis, switching to database fallback: {e}")
        _redis_available = False
        return False


async def get_cached_session_from_redis(token_hash: str) -> dict[str, Any] | None:
    """Fetch session from Redis cache if available."""
    global _redis_available
    client = get_redis_client()
    if client is None:
        return None
    try:
        key = f"session:{token_hash}"
        raw = await client.get(key)
        if raw:
            return json.loads(raw)
        return None
    except (redis.exceptions.RedisError, OSError, TimeoutError) as e:
        logger.debug(f"Failed to get session from Redis, switching to database fallback: {e}")
        _redis_available = False
        return None


async def invalidate_cached_session_in_redis(token_hash: str) -> bool:
    """Invalidate session in Redis cache."""
    global _redis_available
    client = get_redis_client()
    if client is None:
        return False
    try:
        key = f"session:{token_hash}"
        await client.delete(key)
        return True
    except (redis.exceptions.RedisError, OSError, TimeoutError) as e:
        logger.debug(f"Failed to delete session from Redis: {e}")
        _redis_available = False
        return False
