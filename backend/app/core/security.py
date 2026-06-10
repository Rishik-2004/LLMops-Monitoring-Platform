"""
Security utilities: JWT tokens, password hashing, API key management
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt
import bcrypt
import secrets
import hashlib
import re
import structlog

from app.core.config import settings

logger = structlog.get_logger()



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        return None


def get_password_hash(password: str) -> str:
    """Hash password with bcrypt"""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash. Returns (plain_key, hashed_key)"""
    key = f"llm_{secrets.token_urlsafe(32)}"
    hashed = hashlib.sha256(key.encode()).hexdigest()
    return key, hashed


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against stored hash"""
    return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key


def mask_sensitive_data(data: str, mask_type: str = "email") -> str:
    """Mask sensitive data for logging"""
    if mask_type == "email":
        parts = data.split("@")
        if len(parts) == 2:
            return f"{parts[0][:2]}***@{parts[1]}"
    elif mask_type == "api_key":
        return f"{data[:8]}...{data[-4:]}"
    elif mask_type == "token":
        return f"{data[:6]}...{data[-4:]}"
    return "***"


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"


def generate_verification_token() -> str:
    """Generate email verification token"""
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """Generate password reset token"""
    return secrets.token_urlsafe(32)
