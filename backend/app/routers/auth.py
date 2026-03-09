from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import logging

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse,
    RefreshTokenRequest, EmailVerifyRequest, UserResponse
)
from app.utils.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    generate_verification_token, verify_token, get_current_user
)
from app.services.email_service import send_verification_email
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/register", response_model=dict, status_code=201)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    token = generate_verification_token()
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        verification_token=token,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    email_sent = send_verification_email(user_data.email, token)

    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    logger.info(f"New registration: {user_data.email} | email_sent={email_sent}")

    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "email": user_data.email,
        "email_sent": email_sent,
        "dev_verify_url": verify_url if not settings.SMTP_USER else None,
    }


@router.post("/verify-email", response_model=dict)
async def verify_email(data: EmailVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == data.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user.is_verified = True
    user.verification_token = None
    db.commit()

    logger.info(f"Email verified for: {user.email}")
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-verification", response_model=dict)
async def resend_verification(data: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    generic_msg = "If that email exists and is unverified, a new link has been sent."

    if not user:
        return {"message": generic_msg}

    if user.is_verified:
        return {"message": "This email is already verified. You can log in."}

    token = generate_verification_token()
    user.verification_token = token
    db.commit()

    email_sent = send_verification_email(data.email, token)
    logger.info(f"Resend verification for {data.email} | sent={email_sent}")

    return {"message": generic_msg}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in. Check your inbox or request a new verification link."
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    user.refresh_token = refresh_token
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = verify_token(data.refresh_token, "refresh")
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.refresh_token != data.refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    user.refresh_token = new_refresh
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.refresh_token = None
    db.commit()
    return {"message": "Logged out successfully"}
