"""
Comprehensive Verification Test Suite for UrbanSync Field Worker System:
1. Worker Login via Email & Worker Code
2. Worker Dashboard & Analytics API (/api/worker/me)
3. Citizen Complaint Submission -> Auto-Assignment to Field Worker
4. Worker Assigned Complaints Queue (/api/worker/complaints)
5. Worker Complaint Detail (/api/worker/complaints/{id})
6. Worker Status Updates: ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED
7. Automatic Worker Free-Up upon RESOLUTION (worker_status: True)
8. Worker Self-Availability Toggle (/api/worker/toggle-status)
9. Worker Ownership Protection (Cannot update unassigned complaint)
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from backend.server import app
from backend.models.database import SessionLocal
from backend.models.models import User, Worker, Complaint, ComplaintStatus

client = TestClient(app)

def run_worker_system_tests():
    print("=================================================================")
    print("[*] RUNNING FIELD WORKER LOGIN, DASHBOARD & STATUS VERIFICATION")
    print("=================================================================")

    # 1. TEST WORKER LOGIN VIA EMAIL
    print("\n--- TEST 1: Worker Login via Email ---")
    res_login_email = client.post("/api/auth/login", json={
        "email": "ramesh.pawar@water.urbansync.city",
        "password": "Password@123"
    })
    assert res_login_email.status_code == 200, f"Worker login failed: {res_login_email.text}"
    data_email = res_login_email.json()
    assert data_email["success"] is True
    assert data_email["user"]["role"] == "FIELD_WORKER"
    assert data_email["user"]["worker"]["worker_code"] == "WRK-WAT-001"
    assert data_email["user"]["worker"]["name"] == "Ramesh Pawar"
    print(f"[PASS] 1. Ramesh Pawar logged in via Email successfully! Role: {data_email['user']['role']}")

    worker_token = data_email["access_token"]
    worker_headers = {"Authorization": f"Bearer {worker_token}"}

    # 2. TEST WORKER LOGIN VIA WORKER CODE
    print("\n--- TEST 2: Worker Login via Worker Code ---")
    res_login_code = client.post("/api/auth/login", json={
        "email": "WRK-WAT-001",
        "password": "Password@123"
    })
    assert res_login_code.status_code == 200, f"Worker login via code failed: {res_login_code.text}"
    data_code = res_login_code.json()
    assert data_code["success"] is True
    assert data_code["user"]["email"] == "ramesh.pawar@water.urbansync.city"
    print(f"[PASS] 2. Ramesh Pawar logged in via Worker Code 'WRK-WAT-001' successfully!")

    # Login second worker (Electricity worker)
    res_elec_worker = client.post("/api/auth/login", json={
        "email": "WRK-ELE-001",
        "password": "Password@123"
    })
    assert res_elec_worker.status_code == 200
    elec_worker_token = res_elec_worker.json()["access_token"]
    elec_worker_headers = {"Authorization": f"Bearer {elec_worker_token}"}

    # 3. TEST WORKER PROFILE & WORKLOAD API (/api/worker/me)
    print("\n--- TEST 3: Worker Profile & Dashboard Stats API ---")
    res_me = client.get("/api/worker/me", headers=worker_headers)
    assert res_me.status_code == 200, f"Failed to get worker profile: {res_me.text}"
    me_data = res_me.json()
    assert me_data["success"] is True
    assert me_data["worker"]["worker_code"] == "WRK-WAT-001"
    assert "active_tasks" in me_data["stats"]
    assert "total_assigned" in me_data["stats"]
    print(f"[PASS] 3. Worker Dashboard Profile retrieved: {me_data['worker']['name']} ({me_data['worker']['designation']}) - Active Tasks: {me_data['stats']['active_tasks']}")

    # 4. CITIZEN REGISTERS A NEW WATER COMPLAINT
    print("\n--- TEST 4: Citizen Submits Complaint -> Auto-Assigned to Water Worker ---")
    res_citizen_login = client.post("/api/auth/login", json={
        "email": "rahul.sharma@example.com",
        "password": "Password@123"
    })
    assert res_citizen_login.status_code == 200
    citizen_headers = {"Authorization": f"Bearer {res_citizen_login.json()['access_token']}"}

    # Make sure Ramesh is free before test complaint
    db = SessionLocal()
    ramesh = db.query(Worker).filter(Worker.worker_code == "WRK-WAT-001").first()
    ramesh.worker_status = True
    db.commit()
    db.close()

    new_comp_payload = {
        "title": "Severe potable pipeline fracture near Bandra West station",
        "description": "High pressure municipal drinking water fountain gushing into the road from ruptured valve.",
        "citizen_selected_category": "Water",
        "impact_level": "HIGH",
        "address": "Station Road near Platform 1 exit",
        "area": "Bandra West",
        "city": "Mumbai",
        "latitude": 19.0550,
        "longitude": 72.8400
    }
    res_new_comp = client.post("/api/complaints", data=new_comp_payload, headers=citizen_headers)
    assert res_new_comp.status_code == 200, f"Complaint creation failed: {res_new_comp.text}"
    comp_data = res_new_comp.json()
    comp_ref = comp_data["complaint_id"]
    assigned_worker = comp_data.get("assigned_worker")
    print(f"[PASS] 4. Complaint {comp_ref} created, assigned to worker: {assigned_worker['name']} ({assigned_worker['worker_code']})")

    # If assigned to Ramesh or another water worker, grab that worker's token
    assigned_worker_code = assigned_worker["worker_code"]
    res_assigned_worker_login = client.post("/api/auth/login", json={
        "email": assigned_worker_code,
        "password": "Password@123"
    })
    target_worker_headers = {"Authorization": f"Bearer {res_assigned_worker_login.json()['access_token']}"}

    # 5. TEST WORKER ASSIGNED COMPLAINTS QUEUE (/api/worker/complaints)
    print("\n--- TEST 5: Worker Assigned Complaints Queue ---")
    res_queue = client.get("/api/worker/complaints?status_filter=ALL", headers=target_worker_headers)
    assert res_queue.status_code == 200, f"Failed to retrieve worker queue: {res_queue.text}"
    queue_data = res_queue.json()
    assert queue_data["success"] is True
    my_tasks = queue_data["complaints"]
    matched = next((t for t in my_tasks if t["complaint_id"] == comp_ref), None)
    assert matched is not None, f"Complaint {comp_ref} was not found in worker's task queue"
    assert "allowed_transitions" in matched
    assert "ACKNOWLEDGED" in matched["allowed_transitions"]
    print(f"[PASS] 5. Worker queue retrieved ({len(my_tasks)} tasks). Found task {comp_ref} with allowed transitions: {matched['allowed_transitions']}")

    # 6. TEST WORKER COMPLAINT DETAIL (/api/worker/complaints/{id})
    print("\n--- TEST 6: Worker Complaint Detail API ---")
    res_detail = client.get(f"/api/worker/complaints/{comp_ref}", headers=target_worker_headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()["complaint"]
    assert detail_data["complaint_id"] == comp_ref
    assert detail_data["citizen_name"] == "Rahul Sharma"
    assert detail_data["latitude"] == 19.0550
    print(f"[PASS] 6. Worker complaint detail verified with full citizen and geo details.")

    # 7. TEST STATUS TRANSITIONS: ASSIGNED -> ACKNOWLEDGED
    print("\n--- TEST 7: Worker Updates Status to ACKNOWLEDGED ---")
    res_ack = client.post(f"/api/worker/complaints/{comp_ref}/status", json={
        "status": "ACKNOWLEDGED",
        "comment": "Dispatched to site with equipment and tools."
    }, headers=target_worker_headers)
    assert res_ack.status_code == 200, f"Status update to ACKNOWLEDGED failed: {res_ack.text}"
    assert res_ack.json()["status"] == "ACKNOWLEDGED"
    print(f"[PASS] 7. Worker transitioned task {comp_ref} to ACKNOWLEDGED.")

    # 8. TEST STATUS TRANSITIONS: ACKNOWLEDGED -> IN_PROGRESS
    print("\n--- TEST 8: Worker Updates Status to IN_PROGRESS ---")
    res_inp = client.post(f"/api/worker/complaints/{comp_ref}/status", json={
        "status": "IN_PROGRESS",
        "comment": "Excavation completed, welding ruptured pipeline section."
    }, headers=target_worker_headers)
    assert res_inp.status_code == 200, f"Status update to IN_PROGRESS failed: {res_inp.text}"
    assert res_inp.json()["status"] == "IN_PROGRESS"
    print(f"[PASS] 8. Worker transitioned task {comp_ref} to IN_PROGRESS.")

    # 9. TEST WORKER OWNERSHIP ISOLATION (Another worker cannot update this complaint)
    print("\n--- TEST 9: Worker Task Isolation (Forbidden Cross-Worker Updates) ---")
    res_unauth = client.post(f"/api/worker/complaints/{comp_ref}/status", json={
        "status": "RESOLVED",
        "comment": "Unauthorized attempt by different worker"
    }, headers=elec_worker_headers)
    assert res_unauth.status_code == 403, f"Expected 403 Forbidden, got {res_unauth.status_code}"
    print(f"[PASS] 9. Security verified: Electricity Worker blocked from updating Water task (403 Forbidden).")

    # 10. TEST STATUS TRANSITION: IN_PROGRESS -> RESOLVED
    print("\n--- TEST 10: Worker Resolves Complaint & Auto-Frees Worker ---")
    res_res = client.post(f"/api/worker/complaints/{comp_ref}/status", json={
        "status": "RESOLVED",
        "resolution_description": "Water main valve replaced, high-pressure weld completed and pressure tested with zero leakage.",
        "comment": "Repair work completed successfully."
    }, headers=target_worker_headers)
    assert res_res.status_code == 200, f"Status update to RESOLVED failed: {res_res.text}"
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["worker_status"] is True, "Worker should be automatically freed upon RESOLVED"
    print(f"[PASS] 10. Worker marked complaint as RESOLVED! Auto-free worker verified (worker_status: True / Free).")

    # 11. TEST WORKER SELF-TOGGLE AVAILABILITY
    print("\n--- TEST 11: Worker Self-Toggle Duty Availability ---")
    res_toggle = client.post("/api/worker/toggle-status", headers=target_worker_headers)
    assert res_toggle.status_code == 200
    assert res_toggle.json()["worker_status"] is False # toggled to False
    print(f"[PASS] 11. Worker toggled availability to Busy ({res_toggle.json()['status_label']}).")

    # Toggle back to Free
    res_toggle_back = client.post("/api/worker/toggle-status", headers=target_worker_headers)
    assert res_toggle_back.status_code == 200
    assert res_toggle_back.json()["worker_status"] is True
    print(f"[PASS] 11b. Worker toggled availability back to Free ({res_toggle_back.json()['status_label']}).")

    print("\n=================================================================")
    print("[SUCCESS] ALL 11 WORKER LOGIN, DASHBOARD & STATUS TESTS PASSED 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_worker_system_tests()
