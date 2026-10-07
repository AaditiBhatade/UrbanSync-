import os
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.database import get_db
from backend.models.models import (
    Complaint, Department, User, UserRole, ComplaintStatus, 
    ComplaintStatusHistory, Worker
)
from backend.middleware.auth_middleware import get_current_user, require_role, log_audit_action
from backend.services.clustering_service import clustering_service
from backend.services.complaint_service import (
    update_complaint_status, validate_status_transition
)

router = APIRouter(prefix="/api/worker", tags=["Field Worker"])

def get_current_worker(
    current_user: User = Depends(require_role([UserRole.FIELD_WORKER.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
) -> tuple[User, Worker]:
    """
    Resolves the Worker entity associated with the current user.
    """
    worker = db.query(Worker).filter(
        (Worker.user_id == current_user.id) | (Worker.email == current_user.email)
    ).first()

    if not worker:
        # If Super Admin is accessing for testing purposes, fallback to first available worker
        if current_user.role == UserRole.SUPER_ADMIN.value:
            worker = db.query(Worker).first()
            
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Field Worker record found associated with this account."
        )

    return current_user, worker

def get_allowed_worker_transitions(current_status: str) -> List[str]:
    """
    Returns valid status transitions permitted for a field worker.
    """
    if current_status in [ComplaintStatus.ASSIGNED.value, ComplaintStatus.REOPENED.value]:
        return [ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value]
    elif current_status == ComplaintStatus.ACKNOWLEDGED.value:
        return [ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value]
    elif current_status == ComplaintStatus.IN_PROGRESS.value:
        return [ComplaintStatus.RESOLVED.value]
    return []

@router.get("/me")
def get_worker_dashboard_profile(
    user_worker: tuple[User, Worker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Returns field worker profile and workload analytics.
    """
    user, worker = user_worker

    # Aggregate complaints assigned to this worker
    assigned_query = db.query(Complaint).filter(Complaint.assigned_worker_id == worker.id)
    total_assigned = assigned_query.count()

    active_statuses = [
        ComplaintStatus.ASSIGNED.value,
        ComplaintStatus.ACKNOWLEDGED.value,
        ComplaintStatus.IN_PROGRESS.value,
        ComplaintStatus.REOPENED.value
    ]
    active_count = assigned_query.filter(Complaint.status.in_(active_statuses)).count()
    acknowledged_count = assigned_query.filter(Complaint.status == ComplaintStatus.ACKNOWLEDGED.value).count()
    in_progress_count = assigned_query.filter(Complaint.status == ComplaintStatus.IN_PROGRESS.value).count()
    resolved_count = assigned_query.filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value])
    ).count()

    return {
        "success": True,
        "worker": {
            "id": worker.id,
            "worker_code": worker.worker_code,
            "name": worker.name,
            "designation": worker.designation,
            "phone": worker.phone,
            "email": worker.email,
            "department_code": worker.department_code,
            "department_name": worker.department.name if worker.department else worker.department_code,
            "worker_status": worker.worker_status,  # True = Free, False = Busy
            "status_label": "Free (Available)" if worker.worker_status else "Busy (On Task)",
            "skills": worker.skills
        },
        "stats": {
            "total_assigned": total_assigned,
            "active_tasks": active_count,
            "acknowledged_tasks": acknowledged_count,
            "in_progress_tasks": in_progress_count,
            "resolved_tasks": resolved_count
        }
    }

@router.get("/complaints")
def get_worker_assigned_complaints(
    status_filter: Optional[str] = "ALL",
    user_worker: tuple[User, Worker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Returns list of complaints assigned specifically to this field worker.
    Supports filtering by ALL, ACTIVE, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED.
    """
    user, worker = user_worker

    query = db.query(Complaint).filter(Complaint.assigned_worker_id == worker.id)

    if status_filter and status_filter.upper() != "ALL":
        filter_upper = status_filter.upper()
        if filter_upper == "ACTIVE":
            query = query.filter(Complaint.status.in_([
                ComplaintStatus.ASSIGNED.value,
                ComplaintStatus.ACKNOWLEDGED.value,
                ComplaintStatus.IN_PROGRESS.value,
                ComplaintStatus.REOPENED.value
            ]))
        elif filter_upper in ["RESOLVED", "CLOSED", "IN_PROGRESS", "ACKNOWLEDGED", "ASSIGNED"]:
            query = query.filter(Complaint.status == filter_upper)

    complaints = query.order_by(desc(Complaint.updated_at)).all()

    results = []
    for c in complaints:
        c_name = f"Cluster {c.cluster_id}" if c.cluster_id is not None else "Unassigned"
        for h in clustering_service.cluster_metadata:
            if h.get("cluster_id") == c.cluster_id:
                c_name = h.get("zone_name", c_name)
                break

        results.append({
            "id": c.id,
            "complaint_id": c.complaint_id,
            "title": c.title,
            "description": c.description,
            "category": c.ai_predicted_category,
            "predicted_category": c.ai_predicted_category,
            "department": c.department.name if c.department else "General Civic",
            "department_code": c.department.code if c.department else "GENERAL",
            "status": c.status,
            "priority": c.priority,
            "impact_level": c.impact_level,
            "location": c.address or c.area or "Mumbai",
            "address": c.address,
            "area": c.area,
            "city": c.city or "Mumbai",
            "latitude": c.latitude,
            "longitude": c.longitude,
            "cluster_id": c.cluster_id,
            "cluster_name": c_name,
            "citizen_name": c.citizen.full_name if c.citizen else "Citizen",
            "citizen_phone": c.citizen.mobile if c.citizen else None,
            "image": c.images,
            "images": [c.images] if c.images else [],
            "resolution_description": c.resolution_description,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "assigned_at": c.assigned_at.isoformat() if c.assigned_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "allowed_transitions": get_allowed_worker_transitions(c.status)
        })

    return {
        "success": True,
        "worker_code": worker.worker_code,
        "worker_name": worker.name,
        "total": len(results),
        "status_filter": status_filter,
        "complaints": results
    }

@router.get("/complaints/{complaint_ref}")
def get_worker_complaint_detail(
    complaint_ref: str,
    user_worker: tuple[User, Worker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Returns full details of an assigned complaint for the field worker.
    Enforces worker ownership isolation (worker can only view their own tasks).
    """
    user, worker = user_worker

    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_ref).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if user.role != UserRole.SUPER_ADMIN.value and complaint.assigned_worker_id != worker.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: This complaint is not assigned to you."
        )

    c_name = f"Cluster {complaint.cluster_id}" if complaint.cluster_id is not None else "Unassigned"
    for h in clustering_service.cluster_metadata:
        if h.get("cluster_id") == complaint.cluster_id:
            c_name = h.get("zone_name", c_name)
            break

    return {
        "success": True,
        "complaint": {
            "id": complaint.id,
            "complaint_id": complaint.complaint_id,
            "title": complaint.title,
            "description": complaint.description,
            "category": complaint.ai_predicted_category,
            "predicted_category": complaint.ai_predicted_category,
            "department": complaint.department.name if complaint.department else "General Civic",
            "department_code": complaint.department.code if complaint.department else "GENERAL",
            "status": complaint.status,
            "priority": complaint.priority,
            "impact_level": complaint.impact_level,
            "location": complaint.address or complaint.area or "Mumbai",
            "address": complaint.address,
            "area": complaint.area,
            "city": complaint.city or "Mumbai",
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "cluster_id": complaint.cluster_id,
            "cluster_name": c_name,
            "citizen_name": complaint.citizen.full_name if complaint.citizen else "Citizen",
            "citizen_phone": complaint.citizen.mobile if complaint.citizen else None,
            "image": complaint.images,
            "images": [complaint.images] if complaint.images else [],
            "resolution_description": complaint.resolution_description,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "assigned_at": complaint.assigned_at.isoformat() if complaint.assigned_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "allowed_transitions": get_allowed_worker_transitions(complaint.status),
            "history": [
                {
                    "status": h.status,
                    "old_status": h.old_status,
                    "comment": h.comment,
                    "actor_role": h.actor_role,
                    "timestamp": h.created_at.isoformat()
                }
                for h in complaint.status_history
            ]
        }
    }

@router.post("/complaints/{complaint_ref}/status")
async def update_worker_complaint_status(
    complaint_ref: str,
    request: Request,
    user_worker: tuple[User, Worker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Field worker changes status: ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED.
    Automatically frees the worker upon RESOLUTION.
    """
    user, worker = user_worker

    # Support JSON or Form body
    form_data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            form_data = await request.json()
        except Exception:
            form_data = {}
    else:
        try:
            form = await request.form()
            form_data = dict(form)
        except Exception:
            form_data = {}

    new_status = form_data.get("status")
    comment = form_data.get("comment")
    resolution_description = form_data.get("resolution_description")

    if not new_status:
        raise HTTPException(status_code=400, detail="Missing required field: status")

    new_status = new_status.upper().strip()

    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_ref).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Verify worker ownership
    if user.role != UserRole.SUPER_ADMIN.value and complaint.assigned_worker_id != worker.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only update complaints assigned to you."
        )

    # Validate state transition
    if not validate_status_transition(complaint.status, new_status, user):
        allowed = get_allowed_worker_transitions(complaint.status)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {complaint.status} to {new_status}. Allowed next steps: {', '.join(allowed) if allowed else 'None'}"
        )

    # Auto-generate or populate resolution description if marking RESOLVED
    if new_status == ComplaintStatus.RESOLVED.value:
        if not resolution_description:
            resolution_description = comment or f"Issue addressed and resolved on-ground by {worker.name} ({worker.designation})."

    updated = update_complaint_status(
        db=db,
        complaint=complaint,
        new_status=new_status,
        actor=user,
        comment=comment or f"Field Worker updated status to {new_status}",
        resolution_description=resolution_description
    )

    db.refresh(worker)

    return {
        "success": True,
        "message": f"Complaint {complaint_ref} status updated to {new_status}.",
        "complaint_id": updated.complaint_id,
        "status": updated.status,
        "resolution_description": updated.resolution_description,
        "worker_status": worker.worker_status,
        "worker_status_label": "Free (Available)" if worker.worker_status else "Busy (On Task)"
    }

@router.post("/toggle-status")
def toggle_own_worker_status(
    user_worker: tuple[User, Worker] = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """
    Field worker manually toggles their own availability (Free <-> Busy).
    """
    user, worker = user_worker

    old_status = worker.worker_status
    worker.worker_status = not worker.worker_status
    worker.updated_at = datetime.datetime.utcnow()

    log_audit_action(
        db=db,
        actor=user,
        action="WORKER_SELF_TOGGLE_STATUS",
        entity_type="WORKER",
        entity_id=worker.worker_code,
        old_value="Free" if old_status else "Busy",
        new_value="Free" if worker.worker_status else "Busy"
    )

    db.commit()
    db.refresh(worker)

    return {
        "success": True,
        "message": f"Your availability has been set to {'Free (Available)' if worker.worker_status else 'Busy (On Task)'}.",
        "worker_status": worker.worker_status,
        "status_label": "Free (Available)" if worker.worker_status else "Busy (On Task)"
    }
