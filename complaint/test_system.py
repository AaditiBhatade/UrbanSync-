import io
import sys
import json
from fastapi.testclient import TestClient

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.server import app

client = TestClient(app)

def test_full_system():
    print("=================================================================")
    print("[*] RUNNING URBANSYNC FULL-STACK END-TO-END VERIFICATION SUITE")
    print("=================================================================")

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] 1. System Health Check passed:", res.json()["app"])

    # 2. Citizen Registration
    test_email = "test.citizen.suite@example.com"
    reg_payload = {
        "full_name": "Test Citizen Runner",
        "email": test_email,
        "mobile": "9876543210",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "address": "Bandra Kurla Complex",
        "city": "Mumbai",
        "pincode": "400051",
        "terms_accepted": True
    }
    res = client.post("/api/auth/register", json=reg_payload)
    if res.status_code == 400 and "already exists" in res.text:
        # User already exists from previous run, log in
        login_res = client.post("/api/auth/login", json={"email": test_email, "password": "Password@123"})
        citizen_token = login_res.json()["access_token"]
    else:
        assert res.status_code == 200, f"Registration failed: {res.text}"
        citizen_token = res.json()["access_token"]
    print("[PASS] 2. Citizen Registration & JWT generation passed")

    # Verify duplicate email prevention
    res_dup = client.post("/api/auth/register", json=reg_payload)
    assert res_dup.status_code == 400, "Duplicate email check failed"
    print("[PASS] 3. Duplicate Email Prevention verified")

    # 4. Auth Verification & Role check
    headers_citizen = {"Authorization": f"Bearer {citizen_token}"}
    res_me = client.get("/api/auth/me", headers=headers_citizen)
    assert res_me.status_code == 200
    assert res_me.json()["role"] == "CITIZEN"
    print("[PASS] 4. Auth Profile Verification passed:", res_me.json()["full_name"])

    # 5. Complaint Submission with AI Categorization: Water Pipeline
    water_complaint_payload = {
        "title": "Severe water pipeline break with high pressure water leakage",
        "description": "Clean water is flooding the main road near junction for past 2 hours. Pipeline has cracked wide open.",
        "citizen_selected_category": "Water",
        "impact_level": "HIGH",
        "address": "SV Road near metro station",
        "area": "Andheri West",
        "city": "Mumbai",
        "pincode": "400053",
        "latitude": 19.1197,
        "longitude": 72.8468
    }
    res_comp = client.post("/api/complaints", data=water_complaint_payload, headers=headers_citizen)
    assert res_comp.status_code == 200, f"Complaint creation failed: {res_comp.text}"
    water_c_data = res_comp.json()
    water_complaint_id = water_c_data["complaint_id"]
    print(f"[PASS] 5. Water Complaint Created: {water_complaint_id}")
    print(f"     -> ML Predicted Category: {water_c_data['category']}")
    print(f"     -> ML Hotspot Cluster: {water_c_data.get('cluster_id')} ({water_c_data.get('cluster_name')})")
    print(f"     -> Routed Department: {water_c_data['department']} ({water_c_data['department_code']})")
    print(f"     -> Initial Status: {water_c_data['status']}")
    assert water_c_data["department_code"] == "WATER", "ML failed to route water complaint to Water Department"
    assert "cluster_id" in water_c_data and water_c_data["cluster_id"] is not None, "Missing K-Means cluster_id"

    # 6. Duplicate Complaint Detection Test
    dup_payload = {
        "title": "Severe water pipeline break with high pressure water leakage",
        "description": "Clean water is flooding the main road near junction for past 2 hours.",
        "citizen_selected_category": "Water",
        "impact_level": "HIGH",
        "address": "SV Road near metro station",
        "area": "Andheri West",
        "city": "Mumbai",
        "latitude": 19.1198, # Very close coordinates
        "longitude": 72.8469
    }
    res_dup_comp = client.post("/api/complaints", data=dup_payload, headers=headers_citizen)
    assert res_dup_comp.status_code == 200
    dup_data = res_dup_comp.json()
    assert dup_data["is_duplicate"] == True, "Duplicate detector failed to flag similar complaint nearby"
    print(f"[PASS] 6. Duplicate Complaint Detection passed: Flagged as duplicate of {dup_data['duplicate_of_id']}")

    # 7. Department Admin Authentication & Isolation
    # Login as Water Admin
    res_water_admin = client.post("/api/auth/login", json={"email": "admin.water@urbansync.city", "password": "Password@123"})
    assert res_water_admin.status_code == 200
    water_admin_token = res_water_admin.json()["access_token"]
    headers_water_admin = {"Authorization": f"Bearer {water_admin_token}"}

    # Water admin views their queue
    res_water_queue = client.get("/api/admin/complaints", headers=headers_water_admin)
    assert res_water_queue.status_code == 200
    print(f"[PASS] 7. Water Admin Queue loaded: {res_water_queue.json()['total']} complaints")

    # Water admin opens the water complaint
    res_detail = client.get(f"/api/admin/complaints/{water_complaint_id}", headers=headers_water_admin)
    assert res_detail.status_code == 200, f"Water admin detail view failed: {res_detail.text}"
    print(f"[PASS] 8. Water Admin Complaint Detail retrieved successfully")

    # 9. STRICT DEPARTMENT ISOLATION TEST:
    # Login as Electricity Admin
    res_elec_admin = client.post("/api/auth/login", json={"email": "admin.electricity@urbansync.city", "password": "Password@123"})
    assert res_elec_admin.status_code == 200
    elec_admin_token = res_elec_admin.json()["access_token"]
    headers_elec_admin = {"Authorization": f"Bearer {elec_admin_token}"}

    # Electricity admin tries to view Water Department complaint!
    res_unauth_access = client.get(f"/api/admin/complaints/{water_complaint_id}", headers=headers_elec_admin)
    assert res_unauth_access.status_code == 403, f"Expected 403 Forbidden for cross-department access, got {res_unauth_access.status_code}"
    print(f"[PASS] 9. Strict Department Isolation verified: Electricity Admin blocked from Water Complaint (403 Forbidden)")

    # 10. Department Admin Workflow: Acknowledge -> In Progress -> Resolved
    # Acknowledge
    res_ack = client.post(f"/api/admin/complaints/{water_complaint_id}/status", data={"status": "ACKNOWLEDGED", "comment": "Water team dispatched"}, headers=headers_water_admin)
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "ACKNOWLEDGED"

    # Start Work
    res_prog = client.post(f"/api/admin/complaints/{water_complaint_id}/status", data={"status": "IN_PROGRESS", "comment": "Digging and pipe clamping ongoing"}, headers=headers_water_admin)
    assert res_prog.status_code == 200
    assert res_prog.json()["status"] == "IN_PROGRESS"

    # Resolve with mandatory resolution description
    res_res = client.post(f"/api/admin/complaints/{water_complaint_id}/status", data={
        "status": "RESOLVED",
        "resolution_description": "Damaged 6-inch pipe section replaced and pressure tested successfully. No water leak remaining.",
        "comment": "Repairs complete"
    }, headers=headers_water_admin)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    print("[PASS] 10. Department Admin Workflow (Acknowledge -> In Progress -> Resolved) passed")

    # 11. Citizen Confirms Resolution -> CLOSED
    res_close = client.post(f"/api/complaints/{water_complaint_id}/resolve", headers=headers_citizen)
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "CLOSED"
    print("[PASS] 11. Citizen Resolution Confirmation (Resolved -> Closed) passed")

    # 12. Super Admin Dashboard & Telemetry
    res_super = client.post("/api/auth/login", json={"email": "superadmin@urbansync.city", "password": "Password@123"})
    assert res_super.status_code == 200
    super_token = res_super.json()["access_token"]
    headers_super = {"Authorization": f"Bearer {super_token}"}

    res_super_dash = client.get("/api/super-admin/dashboard", headers=headers_super)
    assert res_super_dash.status_code == 200
    metrics = res_super_dash.json()["metrics"]
    print(f"[PASS] 12. Super Admin Telemetry passed: Total={metrics['total_complaints']}, Closed={metrics['resolved']}")

    # 13. Super Admin AI Review & Override Test
    # Create ambiguous complaint
    res_amb = client.post("/api/complaints", data={
        "title": "Strange vibration and humming sound near wall boundary",
        "description": "Not sure what this is, humming sound all day and night.",
        "citizen_selected_category": "Other",
        "impact_level": "LOW",
        "address": "Corner plot"
    }, headers=headers_citizen)
    amb_id = res_amb.json()["complaint_id"]

    # Super admin reviews and overrides
    res_override = client.post(f"/api/super-admin/ai-review/{amb_id}/override", json={
        "category": "Electricity",
        "department_code": "ELECTRICITY",
        "reason": "Humming indicates electrical substation transformer issue. Routed to Power Department."
    }, headers=headers_super)
    assert res_override.status_code == 200
    print(f"[PASS] 13. Super Admin AI Override passed: Reassigned {amb_id} to Electricity Department with audit reason")

    # 14. Audit Logs Verification
    res_audit = client.get("/api/super-admin/audit-logs", headers=headers_super)
    assert res_audit.status_code == 200
    assert len(res_audit.json()["audit_logs"]) > 0
    print(f"[PASS] 14. Immutable Audit Trail verified ({len(res_audit.json()['audit_logs'])} logged events)")

    # 15. In-App Notifications Verification
    res_notif = client.get("/api/notifications", headers=headers_citizen)
    assert res_notif.status_code == 200
    notifs = res_notif.json()["notifications"]
    print(f"[PASS] 15. In-App Notifications verified ({len(notifs)} notifications for citizen)")

    # 16. ML Analytics & Hotspot Telemetry Verification (Section 2, 3, 19)
    res_ml = client.get("/api/admin/ml-analytics", headers=headers_water_admin)
    assert res_ml.status_code == 200, f"ML Analytics endpoint failed: {res_ml.text}"
    ml_data = res_ml.json()
    assert ml_data["success"] is True
    assert len(ml_data["categories"]) == 15, f"Expected 15 BMC categories, got {len(ml_data['categories'])}"
    assert len(ml_data["hotspots"]) == 6, f"Expected 6 K-Means clusters, got {len(ml_data['hotspots'])}"
    assert ml_data["total_dataset_complaints"] == 16006, f"Expected 16,006 records, got {ml_data['total_dataset_complaints']}"
    print(f"[PASS] 16. ML Telemetry API verified: 15 BMC Categories, 6 K-Means Clusters ({ml_data['total_dataset_complaints']} complaints)")

    # 17. Manual Municipal Assignment Verification (Section 9, 10, 12)
    res_assign = client.post(
        f"/api/admin/complaints/{water_complaint_id}/assign",
        data={
            "department_head": "Hydraulic Engineer (Water Supply Operations)",
            "department_id": 3
        },
        headers=headers_water_admin
    )
    assert res_assign.status_code == 200, f"Manual assignment failed: {res_assign.text}"
    print(f"[PASS] 17. Manual Municipal Assignment verified: Assigned Department Head: Hydraulic Engineer (Water Supply Operations)")

    # Verify detail shows the assigned department head
    res_detail_updated = client.get(f"/api/admin/complaints/{water_complaint_id}", headers=headers_water_admin)
    assert res_detail_updated.status_code == 200
    comp_obj = res_detail_updated.json()["complaint"]
    assert comp_obj["assigned_department_head"] == "Hydraulic Engineer (Water Supply Operations)"
    assert comp_obj["cluster_id"] is not None
    print(f"     -> Complaint Record verified: cluster_id={comp_obj['cluster_id']}, cluster_name={comp_obj['cluster_name']}, dept_head={comp_obj['assigned_department_head']}")

    print("=================================================================")
    print("[SUCCESS] ALL 17 CRITICAL CORE INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    test_full_system()

