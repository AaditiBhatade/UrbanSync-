import math
import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.models import Complaint, ComplaintStatusHistory, User, UserRole, ComplaintStatus
from backend.middleware.auth_middleware import log_audit_action, create_notification
from ml.classifier import classifier_instance

def generate_complaint_id(db: Session) -> str:
    """
    Generates human-readable ID like US-2026-000001
    """
    year = datetime.datetime.utcnow().year
    prefix = f"US-{year}-"
    
    # Find last complaint created this year
    last_complaint = (
        db.query(Complaint)
        .filter(Complaint.complaint_id.like(f"{prefix}%"))
        .order_by(Complaint.id.desc())
        .first()
    )
    
    if last_complaint:
        try:
            seq_part = last_complaint.complaint_id.replace(prefix, "")
            seq_num = int(seq_part) + 1
        except ValueError:
            seq_num = 1
    else:
        seq_num = 1
        
    return f"{prefix}{seq_num:06d}"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns distance in meters between two coordinates
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    
    R = 6371000 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def detect_duplicate(
    db: Session,
    title: str,
    description: str,
    category: str,
    latitude: Optional[float],
    longitude: Optional[float]
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Checks if a similar complaint exists recently (within 30 days) nearby (<= 500 meters)
    with high textual similarity (>= 0.60)
    """
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    
    candidates = (
        db.query(Complaint)
        .filter(
            Complaint.created_at >= thirty_days_ago,
            Complaint.status.notin_([ComplaintStatus.CLOSED.value, ComplaintStatus.REJECTED.value])
        )
        .order_by(Complaint.id.desc())
        .limit(50)
        .all()
    )
    
    full_new_text = f"{title}. {description}"

    for c in candidates:
        # Check text similarity
        c_text = f"{c.title}. {c.description}"
        sim = classifier_instance.compute_similarity(full_new_text, c_text)
        
        # Check spatial distance
        dist = haversine_distance(latitude, longitude, c.latitude, c.longitude)
        
        # If very close spatially and similar text, or nearly identical text
        if (dist <= 600 and sim >= 0.50) or sim >= 0.85:
            return True, c.complaint_id, sim
            
    return False, None, 0.0

VALID_TRANSITIONS = {
    ComplaintStatus.SUBMITTED.value: [ComplaintStatus.PROCESSING.value, ComplaintStatus.ASSIGNED.value, ComplaintStatus.NEEDS_REVIEW.value, ComplaintStatus.UNCLASSIFIED.value],
    ComplaintStatus.PROCESSING.value: [ComplaintStatus.ASSIGNED.value, ComplaintStatus.NEEDS_REVIEW.value, ComplaintStatus.UNCLASSIFIED.value],
    ComplaintStatus.NEEDS_REVIEW.value: [ComplaintStatus.ASSIGNED.value, ComplaintStatus.REJECTED.value],
    ComplaintStatus.UNCLASSIFIED.value: [ComplaintStatus.ASSIGNED.value, ComplaintStatus.REJECTED.value],
    ComplaintStatus.ASSIGNED.value: [ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.REJECTED.value, ComplaintStatus.NEEDS_REVIEW.value],
    ComplaintStatus.ACKNOWLEDGED.value: [ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.REJECTED.value],
    ComplaintStatus.IN_PROGRESS.value: [ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value],
    ComplaintStatus.RESOLVED.value: [ComplaintStatus.CLOSED.value, ComplaintStatus.REOPENED.value],
    ComplaintStatus.REOPENED.value: [ComplaintStatus.ACKNOWLEDGED.value, ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.RESOLVED.value],
    ComplaintStatus.CLOSED.value: [],
    ComplaintStatus.REJECTED.value: [ComplaintStatus.REOPENED.value]
}

def validate_status_transition(current_status: str, new_status: str, user: User) -> bool:
    """
    Enforces state machine and role permissions
    """
    if user.role == UserRole.SUPER_ADMIN.value:
        return True # Super admin can force transition
    
    if user.role == UserRole.CITIZEN.value:
        # Citizen can only transition RESOLVED -> CLOSED or RESOLVED -> REOPENED
        if current_status == ComplaintStatus.RESOLVED.value and new_status in [ComplaintStatus.CLOSED.value, ComplaintStatus.REOPENED.value]:
            return True
        return False
    
    if user.role == UserRole.DEPARTMENT_ADMIN.value:
        # Dept Admin can transition within standard workflow
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    return False

def update_complaint_status(
    db: Session,
    complaint: Complaint,
    new_status: str,
    actor: User,
    comment: Optional[str] = None,
    resolution_description: Optional[str] = None,
    rejection_reason: Optional[str] = None
) -> Complaint:
    """
    Safely transitions complaint status, records history, logs audit, and creates notifications
    """
    old_status = complaint.status
    complaint.status = new_status
    complaint.updated_at = datetime.datetime.utcnow()
    
    if new_status == ComplaintStatus.ASSIGNED.value and not complaint.assigned_at:
        complaint.assigned_at = datetime.datetime.utcnow()
    elif new_status == ComplaintStatus.RESOLVED.value:
        complaint.resolved_at = datetime.datetime.utcnow()
        if resolution_description:
            complaint.resolution_description = resolution_description
    elif new_status == ComplaintStatus.CLOSED.value:
        complaint.closed_at = datetime.datetime.utcnow()
    elif new_status == ComplaintStatus.REJECTED.value and rejection_reason:
        complaint.rejection_reason = rejection_reason

    # Add History record
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=new_status,
        old_status=old_status,
        actor_id=actor.id if actor else None,
        actor_role=actor.role if actor else "SYSTEM",
        comment=comment or f"Status changed from {old_status} to {new_status}"
    )
    db.add(history)
    db.commit()
    db.refresh(complaint)

    # Audit log
    log_audit_action(
        db=db,
        actor=actor,
        action="STATUS_CHANGE",
        entity_type="COMPLAINT",
        entity_id=complaint.complaint_id,
        old_value=old_status,
        new_value=new_status
    )

    # Notify Citizen
    status_messages = {
        ComplaintStatus.ASSIGNED.value: f"Your complaint {complaint.complaint_id} has been routed and assigned to {complaint.department.name if complaint.department else 'the department'}.",
        ComplaintStatus.ACKNOWLEDGED.value: f"The department has acknowledged your complaint {complaint.complaint_id}.",
        ComplaintStatus.IN_PROGRESS.value: f"Action is now underway for your complaint {complaint.complaint_id}.",
        ComplaintStatus.RESOLVED.value: f"Your complaint {complaint.complaint_id} has been marked as RESOLVED by the department. Please verify.",
        ComplaintStatus.CLOSED.value: f"Complaint {complaint.complaint_id} has been successfully closed. Thank you!",
        ComplaintStatus.REJECTED.value: f"Your complaint {complaint.complaint_id} was reviewed and rejected. Reason: {rejection_reason or 'Not civic jurisdiction'}",
        ComplaintStatus.REOPENED.value: f"Complaint {complaint.complaint_id} has been reopened for further action."
    }

    if new_status in status_messages and complaint.citizen_id:
        create_notification(
            db=db,
            user_id=complaint.citizen_id,
            title=f"Complaint Update: {new_status}",
            message=status_messages[new_status],
            link=f"/citizen/complaints/{complaint.complaint_id}"
        )

    return complaint
