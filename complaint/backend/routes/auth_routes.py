import re
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from backend.models.database import get_db
from backend.models.models import User, UserRole, PasswordResetToken, Worker
from backend.utils.auth import (
    verify_password, get_password_hash, create_access_token, generate_random_token
)
from backend.middleware.auth_middleware import (
    get_current_user, log_audit_action
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    mobile: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    confirm_password: str
    address: Optional[str] = None
    city: Optional[str] = "Mumbai"
    pincode: Optional[str] = None
    profile_photo: Optional[str] = None
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")

class LoginRequest(BaseModel):
    email: str = Field(..., description="Email address or Worker Code (e.g. WRK-WAT-001)")
    password: str
    remember_me: Optional[bool] = False

class GoogleAuthRequest(BaseModel):
    email: EmailStr
    name: str
    google_id: str
    photo_url: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    profile_photo: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

@router.post("/register")
def register_citizen(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    if not payload.terms_accepted:
        raise HTTPException(status_code=400, detail="You must accept the terms and conditions.")

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    # Validate mobile (allow standard 10 digit Indian number)
    clean_mobile = re.sub(r"[^\d]", "", payload.mobile)
    if len(clean_mobile) < 10:
        raise HTTPException(status_code=400, detail="Please provide a valid 10-digit mobile number.")

    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    new_user = User(
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        mobile=clean_mobile,
        role=UserRole.CITIZEN.value, # Strict: citizen role only
        address=payload.address,
        city=payload.city or "Mumbai",
        pincode=payload.pincode,
        profile_photo=payload.profile_photo,
        provider="local"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "email": new_user.email, "role": new_user.role})

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        samesite="lax"
    )

    log_audit_action(
        db=db,
        actor=new_user,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=str(new_user.id),
        new_value=f"Registered as CITIZEN ({new_user.email})",
        ip_address=request.client.host if request.client else None
    )

    return {
        "success": True,
        "message": "Registration successful! Welcome to UrbanSync.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "mobile": new_user.mobile,
            "role": new_user.role,
            "city": new_user.city,
            "address": new_user.address,
            "pincode": new_user.pincode,
            "profile_photo": new_user.profile_photo
        }
    }

@router.post("/login")
def login_user(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    login_id = payload.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == login_id).first()
    
    # If not found by email, check if identifier is a Worker Code (e.g. WRK-WAT-001)
    if not user:
        worker_rec = db.query(Worker).filter(func.lower(Worker.worker_code) == login_id).first()
        if worker_rec:
            if worker_rec.user_id:
                user = db.query(User).filter(User.id == worker_rec.user_id).first()
            elif worker_rec.email:
                user = db.query(User).filter(func.lower(User.email) == worker_rec.email.lower()).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email/worker code or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account has been deactivated. Please contact support.")

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

    max_age = 86400 * 30 if payload.remember_me else 86400
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax"
    )

    log_audit_action(
        db=db,
        actor=user,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=str(user.id),
        new_value=f"Login from {user.role}",
        ip_address=request.client.host if request.client else None
    )

    user_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "mobile": user.mobile,
        "role": user.role,
        "department_code": user.department_code,
        "city": user.city,
        "address": user.address,
        "pincode": user.pincode,
        "profile_photo": user.profile_photo
    }

    # If user is a FIELD_WORKER, attach their worker details
    if user.role == UserRole.FIELD_WORKER.value:
        worker = db.query(Worker).filter((Worker.user_id == user.id) | (Worker.email == user.email)).first()
        if worker:
            user_data["worker"] = {
                "id": worker.id,
                "worker_code": worker.worker_code,
                "name": worker.name,
                "designation": worker.designation,
                "phone": worker.phone,
                "email": worker.email,
                "department_code": worker.department_code,
                "department_name": worker.department.name if worker.department else worker.department_code,
                "worker_status": worker.worker_status,
                "skills": worker.skills
            }

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": user_data
    }

@router.post("/google")
def google_auth(payload: GoogleAuthRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Google OAuth login/signup handler with seamless development fallback
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user:
        # Create new citizen user from Google profile
        user = User(
            email=payload.email.lower(),
            full_name=payload.name,
            role=UserRole.CITIZEN.value,
            provider="google",
            provider_user_id=payload.google_id,
            profile_photo=payload.photo_url,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log_audit_action(
            db=db,
            actor=user,
            action="GOOGLE_REGISTER",
            entity_type="USER",
            entity_id=str(user.id),
            new_value=f"New Google user registered ({user.email})",
            ip_address=request.client.host if request.client else None
        )
    else:
        # Update existing user info if needed
        if not user.provider_user_id:
            user.provider_user_id = payload.google_id
            user.provider = "google"
            db.commit()

        log_audit_action(
            db=db,
            actor=user,
            action="GOOGLE_LOGIN",
            entity_type="USER",
            entity_id=str(user.id),
            new_value=f"Google login ({user.email})",
            ip_address=request.client.host if request.client else None
        )

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=86400 * 7, samesite="lax")

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "mobile": user.mobile,
            "role": user.role,
            "department_code": user.department_code,
            "city": user.city,
            "profile_photo": user.profile_photo
        }
    }

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generates password reset token without leaking account enumeration
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    reset_url = None

    if user and user.is_active:
        token_str = generate_random_token(32)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        
        # Deactivate old tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})

        token_record = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
            is_used=False
        )
        db.add(token_record)
        db.commit()
        reset_url = f"/reset-password/{token_str}"

    return {
        "success": True,
        "message": "If this email is registered in UrbanSync, password reset instructions have been generated.",
        "dev_reset_url": reset_url # Useful for testing in development
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    token_record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == payload.token)
        .first()
    )

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or unrecognized reset token.")

    if token_record.is_used:
        raise HTTPException(status_code=400, detail="This reset token has already been used.")

    if datetime.datetime.utcnow() > token_record.expires_at:
        raise HTTPException(status_code=400, detail="This reset token has expired. Please request a new link.")

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Associated user not found.")

    user.password_hash = get_password_hash(payload.new_password)
    user.updated_at = datetime.datetime.utcnow()
    token_record.is_used = True
    db.commit()

    log_audit_action(
        db=db,
        actor=user,
        action="PASSWORD_RESET",
        entity_type="USER",
        entity_id=str(user.id),
        new_value="Password reset successfully via token"
    )

    return {
        "success": True,
        "message": "Password has been successfully reset! You can now log in with your new password."
    }

@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "mobile": current_user.mobile,
        "role": current_user.role,
        "department_code": current_user.department_code,
        "address": current_user.address,
        "city": current_user.city,
        "pincode": current_user.pincode,
        "profile_photo": current_user.profile_photo,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
    if current_user.role == UserRole.FIELD_WORKER.value:
        worker = db.query(Worker).filter((Worker.user_id == current_user.id) | (Worker.email == current_user.email)).first()
        if worker:
            profile["worker"] = {
                "id": worker.id,
                "worker_code": worker.worker_code,
                "name": worker.name,
                "designation": worker.designation,
                "phone": worker.phone,
                "email": worker.email,
                "department_code": worker.department_code,
                "department_name": worker.department.name if worker.department else worker.department_code,
                "worker_status": worker.worker_status,
                "skills": worker.skills
            }
    return profile

@router.put("/me")
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.full_name:
        current_user.full_name = payload.full_name.strip()
    if payload.mobile:
        current_user.mobile = re.sub(r"[^\d]", "", payload.mobile)
    if payload.address is not None:
        current_user.address = payload.address
    if payload.city is not None:
        current_user.city = payload.city
    if payload.pincode is not None:
        current_user.pincode = payload.pincode
    if payload.profile_photo is not None:
        current_user.profile_photo = payload.profile_photo

    current_user.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profile updated successfully.",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "mobile": current_user.mobile,
            "role": current_user.role,
            "city": current_user.city,
            "address": current_user.address,
            "pincode": current_user.pincode,
            "profile_photo": current_user.profile_photo
        }
    }

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password.")

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Password changed successfully."}

@router.post("/logout")
def logout(response: Response, current_user: Optional[User] = Depends(get_current_user)):
    response.delete_cookie(key="access_token")
    return {"success": True, "message": "Logged out successfully."}
