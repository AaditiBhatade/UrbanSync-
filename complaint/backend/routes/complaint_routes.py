import os
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.database import get_db
from backend.models.models import (
    Complaint, Department, User, UserRole, ComplaintStatus, 
    ComplaintStatusHistory, Notification, AuditLog
)
from backend.middleware.auth_middleware import get_current_user, log_audit_action, create_notification
from backend.services.classification_service import classification_service
from backend.services.clustering_service import clustering_service
from backend.services.complaint_service import generate_complaint_id, detect_duplicate, update_complaint_status

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

# Upload directory
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def create_complaint(
    title: Optional[str] = Form(None),
    description: str = Form(...),
    citizen_selected_category: Optional[str] = Form(None),
    impact_level: Optional[str] = Form("MEDIUM"),
    address: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    city: Optional[str] = Form("Mumbai"),
    pincode: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Citizen submits a civic complaint.
    1. ML Component 1: Text classification (TF-IDF + Logistic Regression) -> Predicted Category
    2. ML Component 2: Coordinate clustering (K-Means) -> Hotspot Cluster ID
    3. Image: Stored in uploads/, associated with complaint record
    4. Duplicate detection via TF-IDF cosine similarity + Haversine distance
    """
    if current_user.role not in [UserRole.CITIZEN.value, UserRole.SUPER_ADMIN.value]:
        # Citizens submit complaints
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complaints must be submitted by registered citizens."
        )

    # Use first few words of description if title not provided
    if not title:
        title = (description[:60] + "...") if len(description) > 60 else description

    # Handle image upload if provided
    saved_image_path = None
    if image and image.filename:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            ext = ".jpg"
        file_name = f"comp_{uuid.uuid4().hex[:12]}{ext}"
        target_path = os.path.join(UPLOAD_DIR, file_name)
        with open(target_path, "wb") as f:
            content = await image.read()
            f.write(content)
        saved_image_path = f"/uploads/{file_name}"

    # ML COMPONENT 1: COMPLAINT CLASSIFICATION
    classification_res = classification_service.classify_complaint(
        f"{title}. {description}",
        citizen_impact=impact_level or "MEDIUM"
    )
    predicted_category = classification_res["category"]
    dept_code = classification_res["department_code"]
    dept_name = classification_res["department_name"]
    priority = classification_res["priority"]

    # Resolve department in DB
    dept = db.query(Department).filter(Department.code == dept_code).first()
    department_id = dept.id if dept else None

    # ML COMPONENT 2: HOTSPOT CLUSTERING
    cluster_id, cluster_name = clustering_service.predict_cluster(latitude, longitude)

    # Check for duplicate reports nearby
    is_dup, dup_of_id, sim = detect_duplicate(
        db=db,
        title=title,
        description=description,
        category=predicted_category,
        latitude=latitude,
        longitude=longitude
    )

    complaint_ref = generate_complaint_id(db)

    # Citizen workflow sets initial status: PENDING / ASSIGNED
    initial_status = ComplaintStatus.PENDING.value

    new_complaint = Complaint(
        complaint_id=complaint_ref,
        citizen_id=current_user.id,
        title=title,
        description=description,
        citizen_selected_category=citizen_selected_category or predicted_category,
        ai_predicted_category=predicted_category,
        ai_subcategory=classification_res.get("subcategory"),
        ai_confidence=classification_res.get("confidence"), # internal only
        department_id=department_id,
        priority=priority,
        impact_level=impact_level or "MEDIUM",
        status=initial_status,
        address=address or area or "Mumbai",
        area=area,
        city=city or "Mumbai",
        pincode=pincode,
        latitude=latitude,
        longitude=longitude,
        images=saved_image_path,
        cluster_id=cluster_id,
        is_duplicate=is_dup,
        duplicate_of_id=dup_of_id,
        original_prediction=predicted_category,
        original_confidence=classification_res.get("confidence")
    )

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    # Add initial status history
    history = ComplaintStatusHistory(
        complaint_id=new_complaint.id,
        status=initial_status,
        actor_id=current_user.id,
        actor_role=current_user.role,
        comment="Complaint submitted and categorized."
    )
    db.add(history)

    # Create citizen confirmation notification
    create_notification(
        db=db,
        user_id=current_user.id,
        title="Complaint Registered Successfully",
        message=f"Your complaint {complaint_ref} has been received. Category: {predicted_category}",
        link=f"/citizen/complaints/{complaint_ref}"
    )

    # Audit log
    log_audit_action(
        db=db,
        actor=current_user,
        action="CREATE_COMPLAINT",
        entity_type="COMPLAINT",
        entity_id=complaint_ref,
        new_value=f"Category: {predicted_category}, Cluster: {cluster_id}"
    )

    db.commit()

    return {
        "success": True,
        "message": "Complaint Registered Successfully",
        "complaint_id": complaint_ref,
        "title": title,
        "description": description,
        "category": predicted_category,
        "predicted_category": predicted_category,
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "department": dept_name,
        "department_code": dept_code,
        "status": initial_status,
        "priority": priority,
        "is_duplicate": is_dup,
        "duplicate_of_id": dup_of_id,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "image": saved_image_path,
        "created_at": new_complaint.created_at.isoformat()
    }

@router.get("/my")
def get_citizen_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists complaints registered by current citizen"""
    complaints = (
        db.query(Complaint)
        .filter(Complaint.citizen_id == current_user.id)
        .order_by(desc(Complaint.created_at))
        .all()
    )

    results = []
    for c in complaints:
        # Resolve cluster name
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
            "predicted_category": c.ai_predicted_category,
            "category": c.ai_predicted_category,
            "department": c.department.name if c.department else "General Civic Department",
            "department_code": c.department.code if c.department else "GENERAL",
            "status": c.status,
            "priority": c.priority,
            "impact_level": c.impact_level,
            "location": c.address or c.area or "Mumbai",
            "latitude": c.latitude,
            "longitude": c.longitude,
            "cluster_id": c.cluster_id,
            "cluster_name": c_name,
            "image": c.images,
            "assigned_department_head": c.assigned_department_head,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None
        })

    return {"success": True, "complaints": results, "total": len(results)}

@router.get("/{complaint_ref}")
def get_complaint_detail(
    complaint_ref: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Citizen views complaint detail"""
    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Access check: Citizens can only see their own complaints
    if current_user.role == UserRole.CITIZEN.value and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this complaint")

    # Cluster name resolution
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
            "predicted_category": complaint.ai_predicted_category,
            "category": complaint.ai_predicted_category,
            "department": complaint.department.name if complaint.department else "General Civic Department",
            "department_code": complaint.department.code if complaint.department else "GENERAL",
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
            "resolution_description": complaint.resolution_description,
            "assigned_department_head": complaint.assigned_department_head,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "closed_at": complaint.closed_at.isoformat() if complaint.closed_at else None,
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

@router.post("/{complaint_ref}/resolve")
def citizen_confirm_resolution(
    complaint_ref: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Citizen confirms resolution, moving complaint status from RESOLVED -> CLOSED
    """
    complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id == complaint_ref)
        .first()
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if current_user.role == UserRole.CITIZEN.value and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    complaint.status = ComplaintStatus.CLOSED.value
    complaint.closed_at = datetime.datetime.utcnow()
    complaint.updated_at = datetime.datetime.utcnow()

    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=ComplaintStatus.CLOSED.value,
        old_status=ComplaintStatus.RESOLVED.value,
        actor_id=current_user.id,
        actor_role=current_user.role,
        comment="Citizen confirmed satisfactory resolution."
    )
    db.add(history)

    log_audit_action(
        db=db,
        actor=current_user,
        action="CITIZEN_CONFIRM_CLOSE",
        entity_type="COMPLAINT",
        entity_id=complaint.complaint_id,
        old_value=ComplaintStatus.RESOLVED.value,
        new_value=ComplaintStatus.CLOSED.value
    )

    db.commit()
    return {"success": True, "message": "Complaint closed successfully.", "status": ComplaintStatus.CLOSED.value}
