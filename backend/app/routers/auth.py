"""Authentication routes: registration, login, and current user profile."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.crud.user import authenticate_user, register_user
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import TokenResponse, UserLoginRequest, UserRead, UserRegisterRequest
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserRead:
    """Create a new CineTrack user account."""
    user = register_user(
        db,
        username=payload.username,
        email=str(payload.email),
        password=payload.password,
        settings=settings,
    )
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Verify credentials and return a signed Bearer JWT access token."""
    user = authenticate_user(
        db,
        username=payload.username,
        email=str(payload.email) if payload.email is not None else None,
        password=payload.password,
        settings=settings,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user.user_id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the currently authenticated user's profile."""
    return UserRead.model_validate(current_user)
