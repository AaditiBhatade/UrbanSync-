import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

from backend.models.database import get_db
from backend.models.models import (
    Complaint, Department, User, UserRole, ComplaintStatus, 
    AuditLog, ComplaintStatusHistory
)
from backend.middleware.auth_middleware import (
    get_current_user, require_role, log_audit_action, create_notification
)
from backend.utils.auth import get_password_hash

router = APIRouter(prefix="/api/super-admin", tags=["Super Admin"])

class CreateAdminRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    department_code: str
    mobile: Optional[str] = None

class CreateDepartmentRequest(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None

class OverrideCategoryRequest(BaseModel):
    category: str
    department_code: str
    reason: str = Field(..., min_length=5)

@router.get("/dashboard")
def get_superadmin_dashboard(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    total_citizens = db.query(User).filter(User.role == UserRole.CITIZEN.value).count()
    total_admins = db.query(User).filter(User.role == UserRole.DEPARTMENT_ADMIN.value).count()
    total_departments = db.query(Department).filter(Department.is_active == True).count()
    total_complaints = db.query(Complaint).count()

    pending = db.query(Complaint).filter(Complaint.status.in_([
        ComplaintStatus.SUBMITTED.value, ComplaintStatus.ASSIGNED.value, ComplaintStatus.ACKNOWLEDGED.value
    ])).count()
    in_progress = db.query(Complaint).filter(Complaint.status == ComplaintStatus.IN_PROGRESS.value).count()
    resolved = db.query(Complaint).filter(Complaint.status.in_([
        ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value
    ])).count()
    needs_review = db.query(Complaint).filter(Complaint.status.in_([
        ComplaintStatus.NEEDS_REVIEW.value, ComplaintStatus.UNCLASSIFIED.value
    ])).count()
    duplicates_flagged = db.query(Complaint).filter(Complaint.is_duplicate == True).count()

    # Breakdown by Department
    dept_counts = (
        db.query(Department.name, Department.code, func.count(Complaint.id))
        .join(Complaint, Complaint.department_id == Department.id, isouter=True)
        .group_by(Department.id)
        .all()
    )
    by_department = [{"department": d[0], "code": d[1], "count": d[2]} for d in dept_counts]

    # Breakdown by AI predicted Category
    cat_counts = (
        db.query(Complaint.ai_predicted_category, func.count(Complaint.id))
        .filter(Complaint.ai_predicted_category.isnot(None))
        .group_by(Complaint.ai_predicted_category)
        .all()
    )
    by_category = [{"category": c[0], "count": c[1]} for c in cat_counts]

    # Breakdown by Status
    status_counts = (
        db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .all()
    )
    by_status = [{"status": s[0], "count": s[1]} for s in status_counts]

    return {
        "success": True,
        "metrics": {
            "total_citizens": total_citizens,
            "total_admins": total_admins,
            "total_departments": total_departments,
            "total_complaints": total_complaints,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,
            "needs_review": needs_review,
            "duplicates_flagged": duplicates_flagged
        },
        "by_department": by_department,
        "by_category": by_category,
        "by_status": by_status
    }

@router.get("/triage-review")
@router.get("/review-queue")
@router.get("/ai-review")
def get_ai_review_queue(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Queue of complaints needing human/super-admin review:
    low confidence, unclassified, needs review, or flagged duplicates
    """
    complaints = (
        db.query(Complaint)
        .filter(
            (Complaint.status.in_([ComplaintStatus.NEEDS_REVIEW.value, ComplaintStatus.UNCLASSIFIED.value])) |
            (Complaint.is_duplicate == True) |
            (Complaint.ai_confidence < 0.75)
        )
        .order_by(desc(Complaint.created_at))
        .all()
    )

    items = []
    for c in complaints:
        items.append({
            "id": c.id,
            "complaint_id": c.complaint_id,
            "title": c.title,
            "description": c.description,
            "citizen_name": c.citizen.full_name if c.citizen else "Citizen",
            "citizen_selected_category": c.citizen_selected_category,
            "ai_predicted_category": c.ai_predicted_category,
            "ai_confidence": round(c.ai_confidence * 100, 1) if c.ai_confidence else 0.0,
            "current_department": c.department.name if c.department else "Unassigned",
            "current_department_code": c.department.code if c.department else "NONE",
            "status": c.status,
            "priority": c.priority,
            "is_duplicate": c.is_duplicate,
            "duplicate_of_id": c.duplicate_of_id,
            "original_prediction": c.original_prediction,
            "override_category": c.override_category,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return {"success": True, "count": len(items), "queue": items}

@router.post("/triage-review/{complaint_ref}/override")
@router.post("/review-queue/{complaint_ref}/override")
@router.post("/ai-review/{complaint_ref}/override")
def override_ai_prediction(
    complaint_ref: str,
    payload: OverrideCategoryRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Super Admin overrides AI classification without losing the original prediction.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_ref).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    target_dept = db.query(Department).filter(Department.code == payload.department_code).first()
    if not target_dept:
        raise HTTPException(status_code=400, detail=f"Department '{payload.department_code}' does not exist.")

    # Preserve original prediction if not already set
    if not complaint.original_prediction:
        complaint.original_prediction = complaint.ai_predicted_category
        complaint.original_confidence = complaint.ai_confidence

    # Set override records
    complaint.override_category = payload.category
    complaint.override_department_id = target_dept.id
    complaint.override_reason = payload.reason
    complaint.overridden_by_id = current_user.id
    complaint.overridden_at = datetime.datetime.utcnow()

    # Route and assign
    complaint.department_id = target_dept.id
    complaint.ai_predicted_category = payload.category
    old_status = complaint.status
    complaint.status = ComplaintStatus.ASSIGNED.value
    complaint.assigned_at = datetime.datetime.utcnow()
    complaint.updated_at = datetime.datetime.utcnow()

    # Add history
    hist = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=ComplaintStatus.ASSIGNED.value,
        old_status=old_status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        comment=f"Super Admin override: Categorized as '{payload.category}', assigned to {target_dept.name}. Reason: {payload.reason}"
    )
    db.add(hist)
    db.commit()

    # Log audit
    log_audit_action(
        db=db,
        actor=current_user,
        action="AI_OVERRIDE",
        entity_type="COMPLAINT",
        entity_id=complaint.complaint_id,
        old_value=f"{complaint.original_prediction} ({round((complaint.original_confidence or 0)*100, 1)}%)",
        new_value=f"{payload.category} -> {target_dept.name} [Reason: {payload.reason}]"
    )

    # Notify Citizen
    create_notification(
        db=db,
        user_id=complaint.citizen_id,
        title=f"Complaint Reviewed ({complaint.complaint_id})",
        message=f"Your complaint was reviewed by city coordinators and assigned to {target_dept.name}.",
        link=f"/citizen/complaints/{complaint.complaint_id}"
    )

    return {
        "success": True,
        "message": f"Complaint {complaint.complaint_id} successfully reclassified and routed to {target_dept.name}."
    }

@router.get("/users")
def list_users(
    role: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role and role != "ALL":
        query = query.filter(User.role == role)
    users = query.order_by(desc(User.created_at)).all()

    items = []
    for u in users:
        items.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "department_code": u.department_code,
            "mobile": u.mobile,
            "city": u.city,
            "is_active": u.is_active,
            "provider": u.provider,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })

    return {"success": True, "users": items}

@router.post("/users/department-admin")
def create_department_admin(
    payload: CreateAdminRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(Department.code == payload.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail=f"Department '{payload.department_code}' does not exist.")

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email address already exists.")

    new_admin = User(
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        mobile=payload.mobile,
        role=UserRole.DEPARTMENT_ADMIN.value,
        department_code=dept.code,
        is_active=True
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    log_audit_action(
        db=db,
        actor=current_user,
        action="CREATE_DEPARTMENT_ADMIN",
        entity_type="USER",
        entity_id=str(new_admin.id),
        new_value=f"Created {dept.code} Admin ({new_admin.email})"
    )

    return {
        "success": True,
        "message": f"Department Admin created for {dept.name} ({new_admin.email}).",
        "user_id": new_admin.id
    }

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool = Form(...),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own super-admin account.")

    old_status = user.is_active
    user.is_active = is_active
    db.commit()

    log_audit_action(
        db=db,
        actor=current_user,
        action="USER_STATUS_CHANGE",
        entity_type="USER",
        entity_id=str(user.id),
        old_value=str(old_status),
        new_value=str(is_active)
    )

    return {"success": True, "message": f"User status updated to {'Active' if is_active else 'Inactive'}."}

@router.get("/departments")
def list_departments(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    departments = db.query(Department).all()
    items = []
    for d in departments:
        complaint_count = db.query(Complaint).filter(Complaint.department_id == d.id).count()
        admin_count = db.query(User).filter(User.department_code == d.code).count()
        items.append({
            "id": d.id,
            "code": d.code,
            "name": d.name,
            "description": d.description,
            "contact_email": d.contact_email,
            "is_active": d.is_active,
            "complaints_count": complaint_count,
            "admins_count": admin_count
        })
    return {"success": True, "departments": items}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    items = []
    for l in logs:
        items.append({
            "id": l.id,
            "actor": l.actor.full_name if l.actor else "System",
            "actor_role": l.actor_role,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None
        })
    return {"success": True, "audit_logs": items}
