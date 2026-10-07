"""
Verification test suite for UrbanSync Municipal Workers & Automatic Free-Worker Assignment
"""

import sys
from fastapi.testclient import TestClient

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.server import app
from backend.models.database import SessionLocal
from backend.models.models import Worker, Department, Complaint, ComplaintStatus

client = TestClient(app)

def test_workers_and_auto_assignment():
    print("=================================================================")
    print("[*] RUNNING MUNICIPAL WORKERS & AUTO-ASSIGNMENT VERIFICATION SUITE")
    print("=================================================================")

    db = SessionLocal()
    try:
        # 1. Verify 5 dummy workers for each of the 10 departments
        departments = db.query(Department).all()
        assert len(departments) == 10, f"Expected 10 departments, found {len(departments)}"
        print(f"[PASS] 1. Verified 10 Municipal Departments exist.")

        total_workers = 0
        for dept in departments:
            dept_workers = db.query(Worker).filter(Worker.department_id == dept.id).all()
            assert len(dept_workers) == 5, f"Expected 5 workers for {dept.code}, got {len(dept_workers)}"
            
            # Check presence of both worker_status True and False
            statuses = [w.worker_status for w in dept_workers]
            assert True in statuses, f"Department {dept.code} must have worker_status True"
            assert False in statuses, f"Department {dept.code} must have worker_status False"
            
            free_count = sum(1 for s in statuses if s is True)
            busy_count = sum(1 for s in statuses if s is False)
            print(f"     -> {dept.code}: 5 workers verified (Free: {free_count}, Busy: {busy_count})")
            total_workers += len(dept_workers)

        assert total_workers == 50, f"Expected 50 total workers, found {total_workers}"
        print(f"[PASS] 2. Verified 50 total workers (5 per department with True/False worker_status).")

    finally:
        db.close()

    # 2. Login as Citizen
    res_login = client.post("/api/auth/login", json={"email": "rahul.sharma@example.com", "password": "Password@123"})
    assert res_login.status_code == 200, "Citizen login failed"
    citizen_token = res_login.json()["access_token"]
    headers_citizen = {"Authorization": f"Bearer {citizen_token}"}

    # Login as Water Admin
    res_water_admin = client.post("/api/auth/login", json={"email": "admin.water@urbansync.city", "password": "Password@123"})
    assert res_water_admin.status_code == 200, "Water Admin login failed"
    water_admin_token = res_water_admin.json()["access_token"]
    headers_water_admin = {"Authorization": f"Bearer {water_admin_token}"}

    # Login as Electricity Admin
    res_elec_admin = client.post("/api/auth/login", json={"email": "admin.electricity@urbansync.city", "password": "Password@123"})
    assert res_elec_admin.status_code == 200, "Electricity Admin login failed"
    elec_admin_token = res_elec_admin.json()["access_token"]
    headers_elec_admin = {"Authorization": f"Bearer {elec_admin_token}"}

    # 3. Check Water Department workers via Admin API
    res_workers = client.get("/api/admin/workers", headers=headers_water_admin)
    assert res_workers.status_code == 200, f"Get workers failed: {res_workers.text}"
    workers_data = res_workers.json()
    assert workers_data["total_workers"] == 5
    assert workers_data["department_code"] == "WATER"
    print(f"[PASS] 3. Water Admin successfully retrieved department workers: Total=5, Free={workers_data['free_workers']}, Busy={workers_data['busy_workers']}")

    # Find the first free worker before registering complaint
    free_workers_before = [w for w in workers_data["workers"] if w["worker_status"] is True]
    assert len(free_workers_before) > 0, "Expected at least one free worker in Water Department"
    expected_worker = free_workers_before[0]
    print(f"     -> Next available free worker for Water: {expected_worker['name']} ({expected_worker['worker_code']})")

    # 4. Citizen registers a water complaint
    complaint_payload = {
        "title": "Severe potable water main leakage on Link Road",
        "description": "High pressure potable water gushing onto the road from underground main junction.",
        "citizen_selected_category": "Water",
        "impact_level": "HIGH",
        "address": "Link Road near junction",
        "area": "Andheri West",
        "city": "Mumbai",
        "latitude": 19.1350,
        "longitude": 72.8250
    }
    res_comp = client.post("/api/complaints", data=complaint_payload, headers=headers_citizen)
    assert res_comp.status_code == 200, f"Complaint registration failed: {res_comp.text}"
    comp_json = res_comp.json()
    comp_id = comp_json["complaint_id"]
    assigned_worker = comp_json.get("assigned_worker")
    
    assert assigned_worker is not None, "Complaint was not automatically assigned to a worker"
    assert assigned_worker["id"] == expected_worker["id"], f"Expected assigned worker {expected_worker['id']}, got {assigned_worker['id']}"
    assert comp_json["status"] == "ASSIGNED", f"Expected initial status ASSIGNED, got {comp_json['status']}"
    print(f"[PASS] 4. Automatic Assignment Verified: Complaint {comp_id} assigned to free worker {assigned_worker['name']} ({assigned_worker['worker_code']}, {assigned_worker['designation']})")

    # 5. Verify the assigned worker is now occupied (worker_status is False / busy)
    res_workers_after = client.get("/api/admin/workers", headers=headers_water_admin)
    w_after = next(w for w in res_workers_after.json()["workers"] if w["id"] == assigned_worker["id"])
    assert w_after["worker_status"] is False, "Assigned worker should now have worker_status False (Busy)"
    print(f"[PASS] 5. Worker Status State Machine Verified: {assigned_worker['name']} worker_status changed to False (Busy)")

    # 6. Verify visibility to Water Department Admin in Queue
    res_queue = client.get("/api/admin/complaints", headers=headers_water_admin)
    assert res_queue.status_code == 200
    comp_in_queue = next((c for c in res_queue.json()["complaints"] if c["complaint_id"] == comp_id), None)
    assert comp_in_queue is not None, "Complaint not found in Water Admin queue"
    assert comp_in_queue["assigned_worker"] is not None, "Assigned worker missing from admin queue item"
    assert comp_in_queue["assigned_worker"]["name"] == assigned_worker["name"]
    print(f"[PASS] 6. Water Admin Queue Visibility Verified: Admin sees assigned worker '{comp_in_queue['assigned_worker']['name']}' ({comp_in_queue['assigned_worker']['worker_code']})")

    # 7. Verify visibility to Water Department Admin in Complaint Detail
    res_detail = client.get(f"/api/admin/complaints/{comp_id}", headers=headers_water_admin)
    assert res_detail.status_code == 200
    comp_detail = res_detail.json()["complaint"]
    assert comp_detail["assigned_worker"] is not None
    assert comp_detail["assigned_worker"]["id"] == assigned_worker["id"]
    assert comp_detail["assigned_worker"]["phone"] is not None
    assert comp_detail["assigned_worker"]["worker_code"] == assigned_worker["worker_code"]
    print(f"[PASS] 7. Water Admin Complaint Detail Visibility Verified: Complete worker profile {comp_detail['assigned_worker']}")

    # 8. Verify Department Isolation (Electricity Admin cannot access Water workers)
    # Electricity admin tries to toggle Water worker status
    res_forbidden_toggle = client.post(f"/api/admin/workers/{assigned_worker['id']}/toggle-status", headers=headers_elec_admin)
    assert res_forbidden_toggle.status_code == 403, f"Expected 403 Forbidden for cross-department worker toggle, got {res_forbidden_toggle.status_code}"
    print(f"[PASS] 8. Strict Department Worker Isolation Verified: Electricity Admin blocked from Water worker toggle (403 Forbidden)")

    # 9. Verify Water Admin can toggle worker status manually
    res_toggle = client.post(f"/api/admin/workers/{assigned_worker['id']}/toggle-status", headers=headers_water_admin)
    assert res_toggle.status_code == 200
    assert res_toggle.json()["worker_status"] is True, "Worker status toggle failed to toggle to True"
    print(f"[PASS] 9. Water Admin Manual Worker Status Toggle Verified: Worker {assigned_worker['name']} toggled to True (Free)")

    # Toggle back to False
    res_toggle_back = client.post(f"/api/admin/workers/{assigned_worker['id']}/toggle-status", headers=headers_water_admin)
    assert res_toggle_back.status_code == 200
    assert res_toggle_back.json()["worker_status"] is False

    # 10. Verify Complaint Resolution automatically frees up the assigned worker
    res_ack = client.post(f"/api/admin/complaints/{comp_id}/status", data={"status": "ACKNOWLEDGED", "comment": "Worker on site"}, headers=headers_water_admin)
    assert res_ack.status_code == 200

    res_inprog = client.post(f"/api/admin/complaints/{comp_id}/status", data={"status": "IN_PROGRESS", "comment": "Repairing main joint"}, headers=headers_water_admin)
    assert res_inprog.status_code == 200

    res_resolve = client.post(f"/api/admin/complaints/{comp_id}/status", data={
        "status": "RESOLVED",
        "resolution_description": "Potable water line joint repaired, welded and sealed.",
        "comment": "Work complete"
    }, headers=headers_water_admin)
    assert res_resolve.status_code == 200

    # Worker should now be freed up automatically (worker_status == True)!
    res_workers_final = client.get("/api/admin/workers", headers=headers_water_admin)
    w_final = next(w for w in res_workers_final.json()["workers"] if w["id"] == assigned_worker["id"])
    assert w_final["worker_status"] is True, "Worker should be automatically freed upon complaint resolution"
    print(f"[PASS] 10. Auto-Free Worker on Resolution Verified: Worker {assigned_worker['name']} is now Free (worker_status: True)")

    print("=================================================================")
    print("[SUCCESS] ALL 10 MUNICIPAL WORKER SPECIFICATIONS PASSED 100%!")
    print("=================================================================")

if __name__ == "__main__":
    test_workers_and_auto_assignment()
