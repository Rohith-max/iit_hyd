"""Authentication routes — Google OAuth2 + JWT."""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72

# In-memory user store
_users: dict[str, dict] = {}  # user_id -> user dict


class GoogleTokenRequest(BaseModel):
    credential: str  # Google ID token from frontend


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


def _create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def _verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")


async def get_current_user(authorization: str = Header(None)) -> dict:
    """Dependency to extract current user from JWT Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization header")
    token = authorization.split(" ", 1)[1]
    payload = _verify_jwt(token)
    user = _users.get(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found")
    return user


@router.post("/google", response_model=AuthResponse)
async def google_login(req: GoogleTokenRequest):
    """Verify a Google ID token and return a JWT."""
    try:
        idinfo = id_token.verify_oauth2_token(
            req.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(401, "Invalid Google token")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(401, "Email not provided by Google")

    # Find or create user
    existing = next((u for u in _users.values() if u["email"] == email), None)
    if existing:
        user = existing
        user["name"] = idinfo.get("name", user["name"])
        user["picture"] = idinfo.get("picture", user.get("picture"))
    else:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": email,
            "name": idinfo.get("name", email.split("@")[0]),
            "picture": idinfo.get("picture"),
            "created_at": datetime.utcnow(),
        }
        _users[user_id] = user

    token = _create_jwt(user["id"], email)
    return AuthResponse(
        token=token,
        user=UserResponse(**user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserResponse(**user)
