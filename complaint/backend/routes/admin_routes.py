import json
import os
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.models.database import get_db
from backend.models.models import (
    Complaint, Department, User, UserRole, ComplaintStatus, 
    ComplaintStatusHistory, AuditLog, Worker
)
from backend.middleware.auth_middleware import get_current_user, require_role, log_audit_action, create_notification
from backend.services.clustering_service import clustering_service
from backend.services.complaint_service import update_complaint_status

router = APIRouter(prefix="/api/admin", tags=["Department Admin"])

# Resolve dataset EDA summary for ML telemetry
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
EDA_SUMMARY_PATH = os.path.join(PROJECT_ROOT, "ml", "eda_summary.json")

def load_eda_summary():
    if os.path.exists(EDA_SUMMARY_PATH):
        try:
            with open(EDA_SUMMARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

@router.get("/complaints")
def get_department_complaints(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Department Admin views complaints queue.
    Strictly isolated to their assigned department unless SUPER_ADMIN.
    """
    query = db.query(Complaint)

    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        # Resolve admin's department
        admin_dept = db.query(Department).filter(Department.code == current_user.department_code).first()
        if admin_dept:
            query = query.filter(Complaint.department_id == admin_dept.id)
        else:
            query = query.filter(False) # No department linked

    if status_filter and status_filter != "ALL":
        query = query.filter(Complaint.status == status_filter)

    complaints = query.order_by(desc(Complaint.created_at)).all()

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
            "citizen_name": c.citizen.full_name if c.citizen else "Citizen",
            "citizen_mobile": c.citizen.mobile if c.citizen else None,
            "predicted_category": c.ai_predicted_category,
            "category": c.ai_predicted_category,
            "department": c.department.name if c.department else "General Civic",
            "department_code": c.department.code if c.department else "GENERAL",
            "status": c.status,
            "priority": c.priority,
            "impact_level": c.impact_level,
            "location": c.address or c.area or "Mumbai",
            "latitude": c.latitude,
            "longitude": c.longitude,
            "cluster_id": c.cluster_id,
            "cluster_name": c_name,
            "assigned_department_head": c.assigned_department_head,
            "assigned_worker": {
                "id": c.assigned_worker.id,
                "worker_code": c.assigned_worker.worker_code,
                "name": c.assigned_worker.name,
                "phone": c.assigned_worker.phone,
                "designation": c.assigned_worker.designation,
                "worker_status": c.assigned_worker.worker_status
            } if c.assigned_worker else None,
            "assigned_worker_name": c.assigned_worker.name if c.assigned_worker else None,
            "assigned_worker_code": c.assigned_worker.worker_code if c.assigned_worker else None,
            "is_duplicate": c.is_duplicate,
            "duplicate_of_id": c.duplicate_of_id,
            "image": c.images,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return {
        "success": True,
        "total": len(results),
        "department": current_user.department_code,
        "complaints": results
    }

@router.get("/complaints/{complaint_ref}")
def get_admin_complaint_detail(
    complaint_ref: str,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Department Admin views complaint details.
    Enforces STRICT DEPARTMENT ISOLATION: 403 Forbidden if viewing outside own department.
    """
    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        admin_dept = db.query(Department).filter(Department.code == current_user.department_code).first()
        if not admin_dept or complaint.department_id != admin_dept.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Complaint belongs to a different municipal department."
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
            "citizen_name": complaint.citizen.full_name if complaint.citizen else "Citizen",
            "citizen_phone": complaint.citizen.mobile if complaint.citizen else None,
            "title": complaint.title,
            "description": complaint.description,
            "predicted_category": complaint.ai_predicted_category,
            "category": complaint.ai_predicted_category,
            "department": complaint.department.name if complaint.department else "General Civic",
            "department_code": complaint.department.code if complaint.department else "GENERAL",
            "department_id": complaint.department_id,
            "status": complaint.status,
            "priority": complaint.priority,
            "impact_level": complaint.impact_level,
            "location": complaint.address or complaint.area or "Mumbai",
            "address": complaint.address,
            "area": complaint.area,
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "cluster_id": complaint.cluster_id,
            "cluster_name": c_name,
            "image": complaint.images,
            "images": [complaint.images] if complaint.images else [],
            "assigned_department_head": complaint.assigned_department_head,
            "assigned_worker": {
                "id": complaint.assigned_worker.id,
                "worker_code": complaint.assigned_worker.worker_code,
                "name": complaint.assigned_worker.name,
                "email": complaint.assigned_worker.email,
                "phone": complaint.assigned_worker.phone,
                "designation": complaint.assigned_worker.designation,
                "worker_status": complaint.assigned_worker.worker_status,
                "skills": complaint.assigned_worker.skills
            } if complaint.assigned_worker else None,
            "assigned_worker_name": complaint.assigned_worker.name if complaint.assigned_worker else None,
            "assigned_worker_code": complaint.assigned_worker.worker_code if complaint.assigned_worker else None,
            "resolution_description": complaint.resolution_description,
            "rejection_reason": complaint.rejection_reason,
            "is_duplicate": complaint.is_duplicate,
            "duplicate_of_id": complaint.duplicate_of_id,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
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
async def update_status_endpoint(
    complaint_ref: str,
    request: Request,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Department Admin updates status: ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED.
    Accepts both Form data and JSON.
    """
    # Parse incoming body (form or json)
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
    rejection_reason = form_data.get("rejection_reason")

    if not new_status:
        raise HTTPException(status_code=400, detail="Missing required field: status")

    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Enforce department isolation
    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        admin_dept = db.query(Department).filter(Department.code == current_user.department_code).first()
        if not admin_dept or complaint.department_id != admin_dept.id:
            raise HTTPException(status_code=403, detail="Access denied: Complaint belongs to a different department.")

    if new_status == ComplaintStatus.RESOLVED.value and not resolution_description:
        # Mandatory resolution description
        resolution_description = comment or "Issue addressed and resolved by field team."

    updated = update_complaint_status(
        db=db,
        complaint=complaint,
        new_status=new_status,
        actor=current_user,
        comment=comment,
        resolution_description=resolution_description,
        rejection_reason=rejection_reason
    )

    return {
        "success": True,
        "message": f"Complaint status updated to {new_status}",
        "complaint_id": updated.complaint_id,
        "status": updated.status,
        "resolution_description": updated.resolution_description
    }

@router.post("/complaints/{complaint_ref}/assign")
async def manual_assign_complaint(
    complaint_ref: str,
    request: Request,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Section 9 & 10: Manual Municipal Assignment.
    Admin manually assigns the complaint to the responsible BMC department and department head.
    """
    form_data = {}
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            form_data = await request.json()
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            form_data = dict(form)
        except Exception:
            pass

    dept_head = form_data.get("department_head")
    dept_id = form_data.get("department_id")

    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    dept_head = form_data.get("department_head")
    dept_id = form_data.get("department_id")
    worker_id = form_data.get("worker_id")

    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Enforce department isolation
    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        admin_dept = db.query(Department).filter(Department.code == current_user.department_code).first()
        if not admin_dept or complaint.department_id != admin_dept.id:
            raise HTTPException(status_code=403, detail="Access denied: Complaint belongs to a different department.")

    audit_items = []
    comment_items = []
    if dept_head:
        complaint.assigned_department_head = str(dept_head).strip()
        audit_items.append(f"Dept Head: {complaint.assigned_department_head}")
        comment_items.append(f"Assigned department head: {complaint.assigned_department_head}")

    if worker_id:
        try:
            target_worker = db.query(Worker).filter(Worker.id == int(worker_id)).first()
            if target_worker:
                # Free previous worker if changing
                if complaint.assigned_worker and complaint.assigned_worker.id != target_worker.id:
                    complaint.assigned_worker.worker_status = True
                complaint.assigned_worker_id = target_worker.id
                target_worker.worker_status = False # New worker becomes occupied
                audit_items.append(f"Worker: {target_worker.name} ({target_worker.worker_code})")
                comment_items.append(f"Assigned field worker: {target_worker.name} ({target_worker.worker_code})")
        except ValueError:
            pass

    if dept_id:
        try:
            # Super admin can transfer complaint across departments; dept admin assigns department head
            if current_user.role == UserRole.SUPER_ADMIN.value:
                complaint.department_id = int(dept_id)
                audit_items.append(f"Department ID: {complaint.department_id}")
        except ValueError:
            pass

    complaint.updated_at = func.now()

    # Log assignment
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=complaint.status,
        old_status=complaint.status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        comment="; ".join(comment_items) if comment_items else "Manual assignment updated"
    )
    db.add(history)

    log_audit_action(
        db=db,
        actor=current_user,
        action="MANUAL_ASSIGNMENT",
        entity_type="COMPLAINT",
        entity_id=complaint.complaint_id,
        new_value="; ".join(audit_items) if audit_items else "Manual assignment updated"
    )

    db.commit()
    db.refresh(complaint)

    return {
        "success": True,
        "message": f"Successfully updated assignment for {complaint.complaint_id}",
        "assigned_department_head": complaint.assigned_department_head,
        "assigned_worker": {
            "id": complaint.assigned_worker.id,
            "worker_code": complaint.assigned_worker.worker_code,
            "name": complaint.assigned_worker.name,
            "designation": complaint.assigned_worker.designation,
            "phone": complaint.assigned_worker.phone,
            "worker_status": complaint.assigned_worker.worker_status
        } if complaint.assigned_worker else None,
        "department_id": complaint.department_id
    }

@router.get("/workers")
def get_department_workers(
    department_code: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Returns list of 5 dummy workers for the department admin's department.
    Includes their worker_status (True/False) and currently active assigned complaints.
    """
    target_dept_code = current_user.department_code
    if current_user.role == UserRole.SUPER_ADMIN.value and department_code:
        target_dept_code = department_code

    query = db.query(Worker)
    if target_dept_code:
        query = query.filter(Worker.department_code == target_dept_code)
    
    workers = query.order_by(Worker.id.asc()).all()

    worker_list = []
    free_count = 0
    busy_count = 0

    for w in workers:
        if w.worker_status:
            free_count += 1
        else:
            busy_count += 1

        active_complaints = (
            db.query(Complaint)
            .filter(
                Complaint.assigned_worker_id == w.id,
                Complaint.status.in_([
                    ComplaintStatus.PENDING.value,
                    ComplaintStatus.SUBMITTED.value,
                    ComplaintStatus.ASSIGNED.value,
                    ComplaintStatus.ACKNOWLEDGED.value,
                    ComplaintStatus.IN_PROGRESS.value
                ])
            )
            .order_by(desc(Complaint.created_at))
            .all()
        )

        active_comp_data = [
            {
                "complaint_id": c.complaint_id,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in active_complaints
        ]

        worker_list.append({
            "id": w.id,
            "worker_code": w.worker_code,
            "name": w.name,
            "designation": w.designation,
            "phone": w.phone,
            "email": w.email,
            "department_code": w.department_code,
            "department_name": w.department.name if w.department else w.department_code,
            "worker_status": w.worker_status,  # True = Free/Available, False = Busy/Assigned
            "status_label": "Free (Available)" if w.worker_status else "Busy (On Task)",
            "skills": w.skills,
            "active_complaints_count": len(active_complaints),
            "active_complaints": active_comp_data
        })

    return {
        "success": True,
        "department_code": target_dept_code,
        "total_workers": len(worker_list),
        "free_workers": free_count,
        "busy_workers": busy_count,
        "workers": worker_list
    }

@router.post("/workers/{worker_id}/toggle-status")
def toggle_worker_status(
    worker_id: int,
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Allows Department Admin to toggle a field worker's status (Free <-> Busy).
    Strict department isolation enforced.
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        if worker.department_code != current_user.department_code:
            raise HTTPException(status_code=403, detail="Access denied: Worker belongs to another department.")

    # Toggle status
    old_status = worker.worker_status
    worker.worker_status = not worker.worker_status
    worker.updated_at = datetime.datetime.utcnow()

    log_audit_action(
        db=db,
        actor=current_user,
        action="TOGGLE_WORKER_STATUS",
        entity_type="WORKER",
        entity_id=worker.worker_code,
        old_value="Free" if old_status else "Busy",
        new_value="Free" if worker.worker_status else "Busy"
    )
    db.commit()
    db.refresh(worker)

    return {
        "success": True,
        "message": f"Worker {worker.name} status updated to {'Free (Available)' if worker.worker_status else 'Busy (On Task)'}",
        "worker_id": worker.id,
        "worker_code": worker.worker_code,
        "name": worker.name,
        "worker_status": worker.worker_status,
        "status_label": "Free (Available)" if worker.worker_status else "Busy (On Task)"
    }


@router.get("/city-analytics")
@router.get("/ml-analytics")
def get_ml_analytics(
    current_user: User = Depends(require_role([UserRole.DEPARTMENT_ADMIN.value, UserRole.SUPER_ADMIN.value])),
    db: Session = Depends(get_db)
):
    """
    Section 2, 3, 19:
    ML Analytics combining:
    1. 15 BMC Classification Categories with exact dataset counts
    2. 6 K-Means Complaint Hotspot Clusters with coordinates & complaint counts
    """
    eda = load_eda_summary()
    
    category_counts = {}
    total_complaints = 16006
    if eda and "category_counts" in eda:
        category_counts = eda["category_counts"]
        total_complaints = eda.get("total_records", 16006)
    else:
        category_counts = {
            "Roads & Footpaths": 3969,
            "Solid Waste Management": 3764,
            "Traffic & Road Safety": 1509,
            "Street Lighting": 1330,
            "Trees & Gardens": 1076,
            "Drainage & Sewerage": 1001,
            "Animal Management": 865,
            "Pollution": 485,
            "Public Toilets & Sanitation": 429,
            "Water Supply": 398,
            "Electricity": 322,
            "Other Civic Services": 312,
            "Stormwater & Flooding": 275,
            "Public Transport": 162,
            "Public Safety & Security": 109
        }

    categories_list = [
        {"category": cat, "count": cnt}
        for cat, cnt in category_counts.items()
    ]

    hotspots_list = clustering_service.get_all_hotspots()

    return {
        "success": True,
        "total_dataset_complaints": total_complaints,
        "categories": categories_list,
        "hotspots": hotspots_list
    }
