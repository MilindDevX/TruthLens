"""
Auth router: registration, login, token refresh, Google OAuth.
Follows router discipline: NEVER calls DB or ML directly — only through service layer.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, RefreshRequest,
)
from app.auth.service import (
    verify_password, create_access_token,
    create_refresh_token_record, rotate_refresh_token,
)
from app.auth.dependencies import get_device_info
from app.auth.oauth import (
    get_google_auth_url, exchange_code_for_tokens, get_google_user_info,
)
from app.users.service import (
    get_user_by_email, create_user, create_oauth_user, get_user_by_id,
)
from app.users.schemas import UserCreate
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with email and password.
    Returns access + refresh token pair.
    """
    try:
        user_data = UserCreate(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
        user = await create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    access_token = create_access_token(str(user.id), user.role.value)
    device_info = get_device_info(request)
    refresh_token = await create_refresh_token_record(db, user.id, device_info)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email and password.
    Returns access + refresh token pair.
    """
    user = await get_user_by_email(db, body.email)
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id), user.role.value)
    device_info = get_device_info(request)
    refresh_token = await create_refresh_token_record(db, user.id, device_info)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate refresh token and issue new access + refresh pair.

    Security:
    - Old refresh token is revoked on use
    - If a previously-revoked token is reused, ALL tokens for
      that user are revoked (compromise detection)
    """
    try:
        device_info = get_device_info(request)
        new_refresh_token, user_id = await rotate_refresh_token(
            db, body.refresh_token, device_info
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(str(user.id), user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/google")
async def google_login():
    """
    Redirect to Google's OAuth consent screen.
    Client should open this URL in browser.
    """
    try:
        auth_url = get_google_auth_url()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return RedirectResponse(url=auth_url)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    Exchanges code for Google tokens → fetches user info → creates/links user → returns JWT pair.
    """
    try:
        google_tokens = await exchange_code_for_tokens(code)
        google_user = await get_google_user_info(google_tokens["access_token"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth failed: {str(e)}",
        )

    user = await create_oauth_user(
        db,
        email=google_user["email"],
        full_name=google_user.get("name", google_user["email"]),
        provider="google",
        oauth_id=google_user["id"],
    )

    access_token = create_access_token(str(user.id), user.role.value)
    device_info = get_device_info(request)
    refresh_token = await create_refresh_token_record(db, user.id, device_info)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
