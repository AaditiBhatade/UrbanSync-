"""
UrbanSync Database Seeder
Populates initial municipal departments, superadmin, department admins, and test citizen accounts.
"""

import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.database import engine, Base, SessionLocal, init_db_schema
from backend.models.models import User, Department, UserRole, Worker
from backend.utils.auth import get_password_hash

DEPARTMENTS_SEED = [
    {"code": "WATER", "name": "Water Department", "description": "Hydraulic engineering, clean water supply, and pipeline network operations.", "contact_email": "water@urbansync.city"},
    {"code": "ELECTRICITY", "name": "Electricity Department", "description": "Power grid, transformers, electrical substations, and street illumination.", "contact_email": "power@urbansync.city"},
    {"code": "ROADS", "name": "Roads & Infrastructure Department", "description": "Pavement surfacing, potholes, footpaths, bridges, and arboriculture.", "contact_email": "roads@urbansync.city"},
    {"code": "WASTE", "name": "Waste Management Department", "description": "Solid waste collection, dump cleanups, recycling, and public sanitation.", "contact_email": "waste@urbansync.city"},
    {"code": "DRAINAGE", "name": "Drainage Department", "description": "Stormwater drains, sewage pipelines, nullahs, and monsoon flood abatement.", "contact_email": "drainage@urbansync.city"},
    {"code": "TRAFFIC", "name": "Traffic Department", "description": "Traffic signals, road signage, public transit coordination, and junction safety.", "contact_email": "traffic@urbansync.city"},
    {"code": "PUBLIC_SAFETY", "name": "Public Safety Department", "description": "Civil defense, stray animal control, hazardous structure monitoring.", "contact_email": "safety@urbansync.city"},
    {"code": "HEALTHCARE", "name": "Healthcare & Environment Department", "description": "Vector control, air and noise pollution monitoring, environmental health.", "contact_email": "health@urbansync.city"},
    {"code": "TELECOM", "name": "Telecommunications Department", "description": "Municipal optic cables, utility digging coordination, citizen connectivity.", "contact_email": "telecom@urbansync.city"},
    {"code": "GENERAL", "name": "General Civic Department", "description": "Administrative triage, cross-department coordination, miscellaneous grievances.", "contact_email": "civic@urbansync.city"},
]

WORKERS_SEED = [
    # 1. WATER DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "WATER", "worker_code": "WRK-WAT-001", "name": "Ramesh Pawar", "designation": "Senior Pipe Fitter", "phone": "9820110001", "email": "ramesh.pawar@water.urbansync.city", "worker_status": True, "skills": "Main Pipeline Welding, Valve Calibration, Emergency Pipe Clamping"},
    {"department_code": "WATER", "worker_code": "WRK-WAT-002", "name": "Suresh Kadam", "designation": "Leakage Detection Specialist", "phone": "9820110002", "email": "suresh.kadam@water.urbansync.city", "worker_status": False, "skills": "Acoustic Leak Detection, Pressure Testing, Subsurface Scanning"},
    {"department_code": "WATER", "worker_code": "WRK-WAT-003", "name": "Ganesh Shinde", "designation": "Hydraulic Valve Technician", "phone": "9820110003", "email": "ganesh.shinde@water.urbansync.city", "worker_status": True, "skills": "Sluice Gate Repairs, Flow Regulation, Reservoir Inflow Control"},
    {"department_code": "WATER", "worker_code": "WRK-WAT-004", "name": "Deepak Sawant", "designation": "Main Line Welder", "phone": "9820110004", "email": "deepak.sawant@water.urbansync.city", "worker_status": False, "skills": "Cast Iron Joining, High Pressure Joint Sealing, Trench Excavation"},
    {"department_code": "WATER", "worker_code": "WRK-WAT-005", "name": "Vijay Chavan", "designation": "Water Pumping Station Operator", "phone": "9820110005", "email": "vijay.chavan@water.urbansync.city", "worker_status": True, "skills": "Booster Pump Overhaul, Chlorination Checks, Distribution Grid Routing"},

    # 2. ELECTRICITY DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "ELECTRICITY", "worker_code": "WRK-ELE-001", "name": "Mahesh Patil", "designation": "Senior High-Tension Linesman", "phone": "9820110006", "email": "mahesh.patil@elec.urbansync.city", "worker_status": True, "skills": "11kV Line Repair, Insulator Replacement, Grid Re-routing"},
    {"department_code": "ELECTRICITY", "worker_code": "WRK-ELE-002", "name": "Kiran Deshmukh", "designation": "Streetlight Circuit Technician", "phone": "9820110007", "email": "kiran.deshmukh@elec.urbansync.city", "worker_status": False, "skills": "LED Luminaire Diagnostics, Timer Switching, Feeder Pillar Repairs"},
    {"department_code": "ELECTRICITY", "worker_code": "WRK-ELE-003", "name": "Rajesh More", "designation": "Substation Maintenance Lead", "phone": "9820110008", "email": "rajesh.more@elec.urbansync.city", "worker_status": True, "skills": "Switchgear Servicing, Busbar Inspection, Emergency Trip Clearance"},
    {"department_code": "ELECTRICITY", "worker_code": "WRK-ELE-004", "name": "Sunil Bhosle", "designation": "Transformer Overhaul Specialist", "phone": "9820110009", "email": "sunil.bhosle@elec.urbansync.city", "worker_status": False, "skills": "Dielectric Oil Testing, Core Winding Repair, Overload Protection"},
    {"department_code": "ELECTRICITY", "worker_code": "WRK-ELE-005", "name": "Nitin Jadhav", "designation": "Underground Cable Jointer", "phone": "9820110010", "email": "nitin.jadhav@elec.urbansync.city", "worker_status": True, "skills": "Fault Thumping, Cable Splicing, Heat Shrink Terminations"},

    # 3. ROADS & INFRASTRUCTURE (5 workers: 3 True, 2 False)
    {"department_code": "ROADS", "worker_code": "WRK-ROA-001", "name": "Anand Gaikwad", "designation": "Asphalt Surfacing Supervisor", "phone": "9820110011", "email": "anand.gaikwad@roads.urbansync.city", "worker_status": True, "skills": "Hot-Mix Asphalt Laying, Bitumen Grading, Road Leveling"},
    {"department_code": "ROADS", "worker_code": "WRK-ROA-002", "name": "Pravin Kamble", "designation": "Pothole Jet-Patcher Lead", "phone": "9820110012", "email": "pravin.kamble@roads.urbansync.city", "worker_status": False, "skills": "High-Velocity Emulsion Injection, Cold Mix Patching, Quick-Set Curing"},
    {"department_code": "ROADS", "worker_code": "WRK-ROA-003", "name": "Santosh Naik", "designation": "Footpath & Kerb Paver", "phone": "9820110013", "email": "santosh.naik@roads.urbansync.city", "worker_status": True, "skills": "Paver Block Alignment, Tactile Paving, Kerb Stone Bedding"},
    {"department_code": "ROADS", "worker_code": "WRK-ROA-004", "name": "Sachin Salvi", "designation": "Road Compactor Heavy Operator", "phone": "9820110014", "email": "sachin.salvi@roads.urbansync.city", "worker_status": False, "skills": "Vibratory Roller Operation, Sub-Base Compaction, Road Profiling"},
    {"department_code": "ROADS", "worker_code": "WRK-ROA-005", "name": "Pradeep Mane", "designation": "Bridge & Flyover Structural Technician", "phone": "9820110015", "email": "pradeep.mane@roads.urbansync.city", "worker_status": True, "skills": "Expansion Joint Repairs, Deck Slab Sealing, Structural Railing Anchoring"},

    # 4. WASTE MANAGEMENT (5 workers: 3 True, 2 False)
    {"department_code": "WASTE", "worker_code": "WRK-WAS-001", "name": "Babu Solanki", "designation": "Solid Waste Field Supervisor", "phone": "9820110016", "email": "babu.solanki@waste.urbansync.city", "worker_status": True, "skills": "Ward Waste Sweeping Schedules, Route Logistics, Dustbin Deployment"},
    {"department_code": "WASTE", "worker_code": "WRK-WAS-002", "name": "Jagdish Rathod", "designation": "Garbage Compactor Truck Lead", "phone": "9820110017", "email": "jagdish.rathod@waste.urbansync.city", "worker_status": False, "skills": "Hydraulic Bin Lifting, Compactor Operation, Transfer Station Dispatch"},
    {"department_code": "WASTE", "worker_code": "WRK-WAS-003", "name": "Ashok Valmiki", "designation": "Black Spot Dump Clearance Lead", "phone": "9820110018", "email": "ashok.valmiki@waste.urbansync.city", "worker_status": True, "skills": "Illegal Dump Remediation, Heavy Shovel Operation, Disinfection Spraying"},
    {"department_code": "WASTE", "worker_code": "WRK-WAS-004", "name": "Dinesh Waghela", "designation": "Recycling Station Coordinator", "phone": "9820110019", "email": "dinesh.waghela@waste.urbansync.city", "worker_status": False, "skills": "Wet/Dry Segregation Audit, Plastic Baler Operation, Composting Triage"},
    {"department_code": "WASTE", "worker_code": "WRK-WAS-005", "name": "Kailash Solanki", "designation": "Bio-Medical & Hazardous Waste Handler", "phone": "9820110020", "email": "kailash.solanki@waste.urbansync.city", "worker_status": True, "skills": "Hazardous Material Containment, Sanitary Bin Protocols, PPE Compliance"},

    # 5. DRAINAGE DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "DRAINAGE", "worker_code": "WRK-DRA-001", "name": "Chandrakant Tambe", "designation": "Stormwater Drain De-silting Lead", "phone": "9820110021", "email": "c.tambe@drainage.urbansync.city", "worker_status": True, "skills": "Heavy Silt Grabbing, Trench Excavation, Flood Barrier Positioning"},
    {"department_code": "DRAINAGE", "worker_code": "WRK-DRA-002", "name": "Arun Mhaske", "designation": "Sewage Suction Machine Operator", "phone": "9820110022", "email": "arun.mhaske@drainage.urbansync.city", "worker_status": False, "skills": "High-Pressure Jetting, Vacuum Tanker Extraction, Obstruction Clearance"},
    {"department_code": "DRAINAGE", "worker_code": "WRK-DRA-003", "name": "Vilas Ghadge", "designation": "Nullah & Culvert Maintenance Technician", "phone": "9820110023", "email": "vilas.ghadge@drainage.urbansync.city", "worker_status": True, "skills": "Culvert Slab Restoration, Retaining Wall Sealing, Outfall Gate Clearing"},
    {"department_code": "DRAINAGE", "worker_code": "WRK-DRA-004", "name": "Sanjay Shirke", "designation": "Manhole Safety & Sealing Lead", "phone": "9820110024", "email": "sanjay.shirke@drainage.urbansync.city", "worker_status": False, "skills": "Ductile Iron Cover Fitting, Frame Leveling, Safety Grating Installation"},
    {"department_code": "DRAINAGE", "worker_code": "WRK-DRA-005", "name": "Pandurang Bhole", "designation": "Monsoon Flood Abatement Specialist", "phone": "9820110025", "email": "p.bhole@drainage.urbansync.city", "worker_status": True, "skills": "Submersible Pump Deployment, Waterlogging Triage, Flap Valve Operation"},

    # 6. TRAFFIC DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "TRAFFIC", "worker_code": "WRK-TRA-001", "name": "Hemant Rane", "designation": "Traffic Signal Automation Lead", "phone": "9820110026", "email": "hemant.rane@traffic.urbansync.city", "worker_status": True, "skills": "Microprocessor Signal Timing, Loop Detector Sync, LED Aspect Replacement"},
    {"department_code": "TRAFFIC", "worker_code": "WRK-TRA-002", "name": "Tushar Sutar", "designation": "Road Signage & Marking Specialist", "phone": "9820110027", "email": "tushar.sutar@traffic.urbansync.city", "worker_status": False, "skills": "Thermoplastic Road Marking, Retro-Reflective Board Erection, Gantry Inspection"},
    {"department_code": "TRAFFIC", "worker_code": "WRK-TRA-003", "name": "Ajay Koli", "designation": "Traffic Bollard & Barrier Technician", "phone": "9820110028", "email": "ajay.koli@traffic.urbansync.city", "worker_status": True, "skills": "Median Crash Barrier Anchoring, Spring Post Fixing, Lane Divider Alignment"},
    {"department_code": "TRAFFIC", "worker_code": "WRK-TRA-004", "name": "Manoj Parab", "designation": "Junction Sensor & Loop Wire Lead", "phone": "9820110029", "email": "manoj.parab@traffic.urbansync.city", "worker_status": False, "skills": "Inductive Sensor Slotting, Conduit Routing, Junction Controller Wiring"},
    {"department_code": "TRAFFIC", "worker_code": "WRK-TRA-005", "name": "Rahul Vichare", "designation": "Pedestrian Crossing & Speed Table Lead", "phone": "9820110030", "email": "rahul.vichare@traffic.urbansync.city", "worker_status": True, "skills": "Zebra Striping, Rubber Speed Bump Installation, Pelican Signal Integration"},

    # 7. PUBLIC SAFETY DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "PUBLIC_SAFETY", "worker_code": "WRK-SAF-001", "name": "Vikas Shelar", "designation": "Civil Defense & Rescue Specialist", "phone": "9820110031", "email": "vikas.shelar@safety.urbansync.city", "worker_status": True, "skills": "Emergency Search & Evacuation, Structural Shoring, Hazard Perimeter Cordoning"},
    {"department_code": "PUBLIC_SAFETY", "worker_code": "WRK-SAF-002", "name": "Datta Kasar", "designation": "Stray Animal Rescue & Care Specialist", "phone": "9820110032", "email": "datta.kasar@safety.urbansync.city", "worker_status": False, "skills": "Humane Netting, Rabies Quarantine Logistics, Cattle Impounding"},
    {"department_code": "PUBLIC_SAFETY", "worker_code": "WRK-SAF-003", "name": "Shrikant Mohite", "designation": "Hazardous Tree Trimming Lead", "phone": "9820110033", "email": "shrikant.m@safety.urbansync.city", "worker_status": True, "skills": "Hydraulic Crane Chainsaw Pruning, Overhanging Branch Clearance, Deadwood Removal"},
    {"department_code": "PUBLIC_SAFETY", "worker_code": "WRK-SAF-004", "name": "Amol Kudale", "designation": "Dilapidated Structure Shoring Lead", "phone": "9820110034", "email": "amol.kudale@safety.urbansync.city", "worker_status": False, "skills": "Scaffolding Bracing, Masonry Crack Monitoring, Demolition Hazard Containment"},
    {"department_code": "PUBLIC_SAFETY", "worker_code": "WRK-SAF-005", "name": "Gautam Kamble", "designation": "Emergency Fire & Safety Support Worker", "phone": "9820110035", "email": "gautam.k@safety.urbansync.city", "worker_status": True, "skills": "Hydrant Flushing, Chemical Extinguisher Testing, Smoke Evacuation Clearance"},

    # 8. HEALTHCARE & ENVIRONMENT (5 workers: 3 True, 2 False)
    {"department_code": "HEALTHCARE", "worker_code": "WRK-HEA-001", "name": "Dr. Ravindra Dalvi", "designation": "Vector Control & Fumigation Lead", "phone": "9820110036", "email": "r.dalvi@health.urbansync.city", "worker_status": True, "skills": "Thermal Fogging, Anti-Larval Abate Treatment, Dengue/Malaria Hotspot Spraying"},
    {"department_code": "HEALTHCARE", "worker_code": "WRK-HEA-002", "name": "Sameer Sawant", "designation": "Air & Noise Pollution Field Analyst", "phone": "9820110037", "email": "sameer.s@health.urbansync.city", "worker_status": False, "skills": "Decibel Level Metering, PM2.5/PM10 Sensor Deployment, Industrial Emission Verification"},
    {"department_code": "HEALTHCARE", "worker_code": "WRK-HEA-003", "name": "Vinod Ghosalkar", "designation": "Municipal Pest Control Lead", "phone": "9820110038", "email": "vinod.g@health.urbansync.city", "worker_status": True, "skills": "Rodent Baiting, Open Drain Disinfection, Cockroach Abatement in Public Markets"},
    {"department_code": "HEALTHCARE", "worker_code": "WRK-HEA-004", "name": "Shailesh Borkar", "designation": "Drinking Water Sample Inspector", "phone": "9820110039", "email": "shailesh.b@health.urbansync.city", "worker_status": False, "skills": "TDS & Chlorine Titration, Coliform Culture Collection, Bottled Sample Logging"},
    {"department_code": "HEALTHCARE", "worker_code": "WRK-HEA-005", "name": "Tanaji Jadhav", "designation": "Community Sanitation Hygiene Lead", "phone": "9820110040", "email": "tanaji.j@health.urbansync.city", "worker_status": True, "skills": "Public Toilet Inspection, Lime Powder Boundary Scattering, Bio-deodorant Spraying"},

    # 9. TELECOM DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "TELECOM", "worker_code": "WRK-TEL-001", "name": "Siddhesh Narvekar", "designation": "Fiber Optic Splicing Lead", "phone": "9820110041", "email": "siddhesh.n@telecom.urbansync.city", "worker_status": True, "skills": "Fusion Splicing, OTDR Trace Analysis, Optical Fiber Distribution Frame Termination"},
    {"department_code": "TELECOM", "worker_code": "WRK-TEL-002", "name": "Prashant Dhuri", "designation": "Utility Digging & Duct Inspector", "phone": "9820110042", "email": "prashant.d@telecom.urbansync.city", "worker_status": False, "skills": "Horizontal Directional Drilling Monitoring, Micro-trench Duct Sealing, Right-of-Way Audit"},
    {"department_code": "TELECOM", "worker_code": "WRK-TEL-003", "name": "Makarand Joshi", "designation": "Underground Cable Locator Specialist", "phone": "9820110043", "email": "m.joshi@telecom.urbansync.city", "worker_status": True, "skills": "Electromagnetic Pipe & Cable Detection, GPR Radar Scanning, Cable Depth Verification"},
    {"department_code": "TELECOM", "worker_code": "WRK-TEL-004", "name": "Avinash Surve", "designation": "Smart Pole & IoT Sensor Technician", "phone": "9820110044", "email": "avinash.s@telecom.urbansync.city", "worker_status": False, "skills": "Environmental IoT Hubs, Municipal Wi-Fi Access Points, CCTV Power Supply Servicing"},
    {"department_code": "TELECOM", "worker_code": "WRK-TEL-005", "name": "Kishor Bagve", "designation": "Telecom Manhole Chamber Maintenance Lead", "phone": "9820110045", "email": "kishor.b@telecom.urbansync.city", "worker_status": True, "skills": "Sub-duct De-watering, Chamber Collar Elevation, Cable Slack Management"},

    # 10. GENERAL CIVIC DEPARTMENT (5 workers: 3 True, 2 False)
    {"department_code": "GENERAL", "worker_code": "WRK-GEN-001", "name": "Rupesh Pednekar", "designation": "Rapid Civic Response Officer", "phone": "9820110046", "email": "rupesh.p@civic.urbansync.city", "worker_status": True, "skills": "First Response Field Verification, Inter-department Dispatch, Ward Triage"},
    {"department_code": "GENERAL", "worker_code": "WRK-GEN-002", "name": "Balkrishna More", "designation": "Multi-Department Civic Inspector", "phone": "9820110047", "email": "balkrishna.m@civic.urbansync.city", "worker_status": False, "skills": "Encroachment Spot Check, Public Space Verification, Multi-Utility Auditing"},
    {"department_code": "GENERAL", "worker_code": "WRK-GEN-003", "name": "Naresh Koli", "designation": "Ward Action Task Force Lead", "phone": "9820110048", "email": "naresh.koli@civic.urbansync.city", "worker_status": True, "skills": "On-Ground Grievance Resolution, Citizen Field Consultation, Emergency Civic Clearing"},
    {"department_code": "GENERAL", "worker_code": "WRK-GEN-004", "name": "Jagannath Gawde", "designation": "Public Grievance Site Verifier", "phone": "9820110049", "email": "j.gawde@civic.urbansync.city", "worker_status": False, "skills": "Photographic Evidence Collection, GPS Ground Truth Verification, Citizen Feedback Logging"},
    {"department_code": "GENERAL", "worker_code": "WRK-GEN-005", "name": "Sitaram Shingote", "designation": "Emergency Civic Logistics Coordinator", "phone": "9820110050", "email": "sitaram.s@civic.urbansync.city", "worker_status": True, "skills": "Multi-utility Material Supply, Tool Inventory Management, Rapid Equipment Deployment"}
]

def seed_database():
    print("[*] Creating database tables and initializing schema if needed...")
    init_db_schema()

    db = SessionLocal()
    try:
        print("[*] Seeding municipal departments...")
        dept_map = {}
        for d_data in DEPARTMENTS_SEED:
            dept = db.query(Department).filter(Department.code == d_data["code"]).first()
            if not dept:
                dept = Department(
                    code=d_data["code"],
                    name=d_data["name"],
                    description=d_data["description"],
                    contact_email=d_data["contact_email"],
                    is_active=True
                )
                db.add(dept)
                db.flush()
            dept_map[d_data["code"]] = dept
        db.commit()

        # Re-fetch dept_map to ensure all IDs are populated
        all_depts = db.query(Department).all()
        for d in all_depts:
            dept_map[d.code] = d

        print("[*] Seeding administrative and test users...")
        pw_hash = get_password_hash("Password@123")

        users_to_seed = [
            {
                "email": "superadmin@urbansync.city",
                "full_name": "Chief Municipal Commissioner",
                "role": UserRole.SUPER_ADMIN.value,
                "department_code": None,
                "mobile": "9999900000"
            },
            {
                "email": "admin.water@urbansync.city",
                "full_name": "Executive Engineer (Water Supply)",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "WATER",
                "mobile": "9819000001"
            },
            {
                "email": "admin.electricity@urbansync.city",
                "full_name": "Superintending Engineer (Power & Lighting)",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "ELECTRICITY",
                "mobile": "9819000002"
            },
            {
                "email": "admin.roads@urbansync.city",
                "full_name": "Chief Engineer (Roads & Traffic)",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "ROADS",
                "mobile": "9819000003"
            },
            {
                "email": "admin.waste@urbansync.city",
                "full_name": "Chief Engineer (Solid Waste Management)",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "WASTE",
                "mobile": "9819000004"
            },
            {
                "email": "admin.drainage@urbansync.city",
                "full_name": "Executive Engineer (Sewerage Operations)",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "DRAINAGE",
                "mobile": "9819000005"
            },
            {
                "email": "admin.traffic@urbansync.city",
                "full_name": "Deputy Commissioner of Traffic",
                "role": UserRole.DEPARTMENT_ADMIN.value,
                "department_code": "TRAFFIC",
                "mobile": "9819000006"
            },
            {
                "email": "rahul.sharma@example.com",
                "full_name": "Rahul Sharma",
                "role": UserRole.CITIZEN.value,
                "department_code": None,
                "mobile": "9876543210"
            },
            {
                "email": "priya.patel@example.com",
                "full_name": "Priya Patel",
                "role": UserRole.CITIZEN.value,
                "department_code": None,
                "mobile": "9876543211"
            }
        ]

        for u_data in users_to_seed:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                user = User(
                    email=u_data["email"],
                    password_hash=pw_hash,
                    full_name=u_data["full_name"],
                    role=u_data["role"],
                    department_code=u_data["department_code"],
                    mobile=u_data["mobile"],
                    city="Mumbai",
                    is_active=True
                )
                db.add(user)
        db.commit()

        print("[*] Seeding 5 dummy workers for each municipal department with dedicated User accounts...")
        workers_created = 0
        workers_updated = 0
        for w_data in WORKERS_SEED:
            dept = dept_map.get(w_data["department_code"])
            if not dept:
                continue

            # Check or create dedicated User account for this worker
            worker_user = db.query(User).filter(User.email == w_data["email"]).first()
            if not worker_user:
                worker_user = User(
                    email=w_data["email"],
                    password_hash=pw_hash,
                    full_name=w_data["name"],
                    role=UserRole.FIELD_WORKER.value,
                    department_code=dept.code,
                    mobile=w_data["phone"],
                    city="Mumbai",
                    is_active=True
                )
                db.add(worker_user)
                db.flush()
            else:
                worker_user.role = UserRole.FIELD_WORKER.value
                worker_user.department_code = dept.code
                worker_user.password_hash = pw_hash
                worker_user.full_name = w_data["name"]
                worker_user.mobile = w_data["phone"]
                db.flush()

            existing_worker = db.query(Worker).filter(Worker.worker_code == w_data["worker_code"]).first()
            if not existing_worker:
                new_worker = Worker(
                    worker_code=w_data["worker_code"],
                    name=w_data["name"],
                    designation=w_data["designation"],
                    phone=w_data["phone"],
                    email=w_data["email"],
                    department_id=dept.id,
                    department_code=dept.code,
                    worker_status=w_data["worker_status"],
                    skills=w_data.get("skills"),
                    user_id=worker_user.id,
                    is_active=True
                )
                db.add(new_worker)
                workers_created += 1
            else:
                # Update attributes to ensure consistency
                existing_worker.name = w_data["name"]
                existing_worker.designation = w_data["designation"]
                existing_worker.phone = w_data["phone"]
                existing_worker.email = w_data["email"]
                existing_worker.department_id = dept.id
                existing_worker.department_code = dept.code
                existing_worker.skills = w_data.get("skills")
                existing_worker.user_id = worker_user.id
                workers_updated += 1

        db.commit()
        print(f"[SUCCESS] Seeded {workers_created} new workers ({workers_updated} already existed) with User accounts across {len(DEPARTMENTS_SEED)} departments.")
        print("[SUCCESS] Database seeding completed successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

