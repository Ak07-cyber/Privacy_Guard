"""
Security utilities for PassiveGuard
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets
import hashlib

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_verification_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT verification token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),  # Unique token ID
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_data(data: str) -> str:
    """Hash sensitive data"""
    return hashlib.sha256(data.encode()).hexdigest()


def generate_challenge_id() -> str:
    """Generate unique challenge ID"""
    return secrets.token_urlsafe(32)


def verify_site_key(site_key: str) -> bool:
    """Verify site key is valid (placeholder - implement your own logic)"""
    # In production, validate against registered site keys
    return len(site_key) > 0
