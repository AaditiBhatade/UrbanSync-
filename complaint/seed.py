"""
UrbanSync Database Seeder
Populates initial municipal departments, superadmin, department admins, and test citizen accounts.
"""

import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.database import engine, Base, SessionLocal
from backend.models.models import User, Department, UserRole
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

def seed_database():
    print("[*] Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[*] Seeding municipal departments...")
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
        db.commit()

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
        print("[SUCCESS] Database seeding completed successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
