from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.models.database import get_db
from backend.models.models import User, UserRole, AuditLog, Notification
from backend.utils.auth import decode_access_token

security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been disabled. Contact support.",
        )
        
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

def log_audit_action(
    db: Session,
    actor: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None
):
    try:
        log = AuditLog(
            actor_id=actor.id if actor else None,
            actor_role=actor.role if actor else "SYSTEM",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Audit Log Error] Failed to log action {action}: {e}")

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None
):
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.add(notif)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Notification Error] Failed to create notification: {e}")
