# UrbanSync — AI-Powered Smart City Civic Complaint Platform

> **"Connecting Citizens. Coordinating Cities."**

UrbanSync is an enterprise-grade cyber-physical civic operations and infrastructure management platform built for modern municipal corporations. Citizens can report infrastructure anomalies (water leaks, power disruptions, potholes, uncollected waste, sewage overflows), while our machine learning classification pipeline diagnoses the issue in real time and automatically routes tasks to the responsible department.

---

## Architecture Diagram

```
                                  +---------------------------------------+
                                  |         UrbanSync Citizen Portal       |
                                  | (Web Geolocation + Leaflet + Photos)  |
                                  +-------------------+-------------------+
                                                      |
                                         POST /api/complaints
                                                      |
                                                      v
+---------------------------------------------------------------------------------------------------+
|                                  FastAPI Full-Stack Gateway                                       |
|  * JWT Auth & Role Access Control (CITIZEN, DEPARTMENT_ADMIN, SUPER_ADMIN)                        |
|  * Haversine Spatial Proximity & Textual Duplicate Detection                                      |
|  * Audit Logging & Real-time Notification Engine                                                  |
+---------------------------------------------+-----------------------------------------------------+
                                              |
                                              v
                              +-------------------------------+
                              |    UrbanSync ML Classifier    |
                              |  (TF-IDF + LogisticRegression)|
                              +---------------+---------------+
                                              |
                                              | Output: Category, Confidence, Dept
                                              v
                      +-----------------------------------------------+
                      |          Automated Municipal Routing          |
                      +-------+-------------------+---------------+---+
                              |                   |               |
                              v                   v               v
                     [Water Department]   [Roads Dept]    [Waste Dept] ...
                              |                   |               |
                              +-------------------+---------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               | Department Admin Isolation Console  |
                               | (Acknowledge -> Work -> Resolution) |
                               +------------------+------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |       Super Admin Command Center    |
                               |  * City Telemetry & Load Balancer   |
                               |  * AI Review & Override Queue       |
                               |  * Immutable System Audit Logs      |
                               +-------------------------------------+
```

---

## Key Features

1. **Role-Based Authentication & Authorization**
   - **Citizen**: Register with mobile verification, report complaints, view live timeline tracking, confirm resolution, reopen complaints.
   - **Department Admin**: Strictly isolated department console (e.g. Water Admin only accesses Water complaints). Full workflow state actions: Acknowledge, Start Work, Resolve, Reject.
   - **Super Admin**: Universal overview, city telemetry, user directory management, department capacity monitoring, and immutable audit logs.
2. **AI-Powered Complaint Categorization**
   - Pre-trained and locally fitted Scikit-learn TF-IDF vectorizer + Logistic Regression classifier.
   - 15 municipal classes covering Water Supply, Street Lighting, Drainage & Sewerage, Roads & Footpaths, Solid Waste Management, Traffic, Pollution, etc.
   - Confidence thresholding:
     - Confidence $\ge 75\%$: Automated immediate department assignment.
     - Confidence $50\% - 75\%$: Routed to `NEEDS_REVIEW` queue.
     - Confidence $< 50\%$: Marked `UNCLASSIFIED` for Super Admin manual triage.
3. **AI Classification Override Architecture**
   - Super Admins can manually correct routing with recorded rationale.
   - Original predictions and confidence scores are never overwritten, preserving ground-truth data for future model retraining.
4. **Duplicate Complaint Detection**
   - Automatically compares incoming complaints against active incidents using Haversine geographic distance ($\le 600\text{m}$) and TF-IDF textual cosine similarity.
   - Flags possible duplicates (`POSSIBLE_DUPLICATE`) while preserving reports for municipal review.
5. **Interactive City Mapping**
   - Geolocation API integration for 1-click current GPS location.
   - Interactive draggable Leaflet map with OpenStreetMap tiles.
6. **Multi-Step Complaint Form with Offline Drafts**
   - 5-step intuitive wizard: Basic Info $\rightarrow$ Impact Level $\rightarrow$ Map Location $\rightarrow$ Multiple Photos $\rightarrow$ Review & Submit.
   - Automatically saves progress to `localStorage` to prevent loss on network failure.
   - Double-submission debounce protection.
7. **Controlled State Machine**
   - `SUBMITTED` $\rightarrow$ `PROCESSING` $\rightarrow$ `CLASSIFIED` $\rightarrow$ `ASSIGNED` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `RESOLVED` $\rightarrow$ `CLOSED`.
   - Reopen workflows for dissatisfied citizens (`REOPENED`).
8. **In-App Notification Center & Audit Trail**
   - Real-time updates delivered to citizens and department staff on status changes.
   - Full audit logging of user logins, complaint actions, and administrative overrides.

---

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2
- **Database**: SQLite (Production-ready relational schema, upgradeable to PostgreSQL/MySQL via `DATABASE_URL`)
- **Machine Learning**: Scikit-learn (TF-IDF Vectorizer + Logistic Regression, 57,000+ features, 85% accuracy on municipal dataset)
- **Security**: Passlib (Bcrypt), Python-Jose / PyJWT, HTTPOnly cookies, CORS headers
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (Custom UrbanSync Design System, no bloated CSS frameworks), Modern ES6+ JavaScript
- **Mapping**: Leaflet.js with OpenStreetMap

---

## Folder Structure

```
UrbanSync/
│
├── frontend/                     # Modern Web Client
│   ├── css/
│   │   └── style.css             # UrbanSync smart city design tokens & CSS system
│   ├── js/
│   │   ├── app.js                # Core router, state, notifications, & API fetch
│   │   ├── auth.js               # Login, registration, forgot-pw, & demo accounts
│   │   ├── citizen.js            # Citizen dashboard, 5-step wizard, & tracking
│   │   ├── admin.js              # Department admin isolated queue & actions
│   │   └── superadmin.js         # City command center, AI review queue, & audit trail
│   └── index.html                # Single-page application entry point
│
├── backend/                      # Backend API Services
│   ├── config/
│   │   └── config.py             # Central environment configurations
│   ├── models/
│   │   ├── database.py           # SQLAlchemy engine & session maker
│   │   └── models.py             # User, Department, Complaint, History, Audit, Notif
│   ├── routes/
│   │   ├── auth_routes.py        # Authentication & profile endpoints
│   │   ├── complaint_routes.py   # Citizen complaint submission & tracking
│   │   ├── admin_routes.py       # Department admin queue & status actions
│   │   ├── super_admin_routes.py # Telemetry, AI review queue, overrides, audit logs
│   │   └── notification_routes.py# In-app user notifications
│   ├── middleware/
│   │   └── auth_middleware.py    # JWT decoder, role guards, & audit logger
│   ├── services/
│   │   └── complaint_service.py  # ID generation, duplicate detection, state machine
│   └── server.py                 # Main FastAPI application & static server
│
├── ml/                           # Machine Learning Pipeline
│   ├── model/
│   │   ├── complaint_classifier.pkl # Trained classification model
│   │   └── tfidf_vectorizer.pkl     # Fitted TF-IDF feature extractor
│   ├── classifier.py             # ComplaintClassifier class with confidence logic
│   ├── api.py                    # Standalone /ml/predict endpoint
│   └── requirements.txt          # ML dependencies
│
├── dataset/                      # Training Data
│   └── mumbai_bmc_complaint_categorization_dataset_v2.csv
│
├── uploads/                      # Secure file storage for uploaded images
├── seed.py                       # Database seed script for test accounts & complaints
├── test_system.py                # Automated 15-point end-to-end test suite
├── .env                          # Local environment settings
├── .env.example                  # Environment configuration template
└── README.md                     # Platform documentation
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 1. Clone & Enter Directory
```bash
cd c:/Users/User/Downloads/complaint
```

### 2. Install Dependencies
```bash
pip install -r ml/requirements.txt
pip install fastapi uvicorn sqlalchemy python-dotenv python-multipart python-jose passlib bcrypt
```

### 3. Initialize Database & Seed Data
```bash
python seed.py
```

### 4. Run the Verification Test Suite
```bash
python test_system.py
```

---

## Running the Application

### Start the Server
```bash
python -m uvicorn backend.server:app --host 127.0.0.1 --port 8080 --reload
```

The application will be accessible at:
- **Frontend Portal**: [http://127.0.0.1:8080/](http://127.0.0.1:8080/)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8080/redoc](http://127.0.0.1:8080/redoc)

---

## Pre-Configured Test Accounts

All demo accounts use the standard password: `Password@123`

| Role | Name | Email | Password | Department |
| :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | Chief Administrator | `superadmin@urbansync.city` | `Password@123` | *All Departments* |
| **Dept Admin** | Vikram Seth | `admin.water@urbansync.city` | `Password@123` | **Water Department** |
| **Dept Admin** | Sunita Rao | `admin.electricity@urbansync.city` | `Password@123` | **Electricity Department** |
| **Dept Admin** | Rajesh Deshmukh | `admin.roads@urbansync.city` | `Password@123` | **Roads & Infrastructure** |
| **Dept Admin** | Meera Joshi | `admin.waste@urbansync.city` | `Password@123` | **Waste Management** |
| **Dept Admin** | Anil Patil | `admin.drainage@urbansync.city` | `Password@123` | **Drainage Department** |
| **Dept Admin** | Kavita Shah | `admin.traffic@urbansync.city` | `Password@123` | **Traffic Department** |
| **Citizen** | Rahul Sharma | `rahul.sharma@example.com` | `Password@123` | Citizen (Andheri West) |
| **Citizen** | Priya Patel | `priya.patel@example.com` | `Password@123` | Citizen (Bandra West) |

> **Quick Access**: The login page (`/login`) includes 1-click test login buttons for Citizen, Water Admin, Roads Admin, and Super Admin.

---

## Core API Endpoints

### Authentication
- `POST /api/auth/register` — Citizen registration
- `POST /api/auth/login` — Account login (returns JWT token)
- `POST /api/auth/google` — Google OAuth handler (with development fallback)
- `POST /api/auth/forgot-password` — Password reset link request
- `POST /api/auth/reset-password` — Password reset with security token
- `GET /api/auth/me` — Current user profile
- `PUT /api/auth/me` — Update profile information
- `POST /api/auth/change-password` — Change password
- `POST /api/auth/logout` — Invalidate session

### Complaints
- `POST /api/complaints` — Submit new complaint with images & AI routing
- `GET /api/complaints` — List citizen complaints with filters
- `GET /api/complaints/{id}` — Complaint details with timeline and photos
- `POST /api/complaints/{id}/resolve` — Citizen confirms resolution (`CLOSED`)
- `POST /api/complaints/{id}/reopen` — Citizen reopens unresolved complaint

### Department Admin
- `GET /api/admin/complaints` — Isolated department complaints queue
- `GET /api/admin/complaints/{id}` — Isolated complaint detail
- `POST /api/admin/complaints/{id}/status` — Status transitions (Acknowledge, Start Work, Resolve, Reject)
- `POST /api/admin/complaints/{id}/assign` — Assign to officer within department
- `GET /api/admin/analytics` — Department metrics & KPIs

### Super Admin
- `GET /api/super-admin/dashboard` — City-wide telemetry & breakdowns
- `GET /api/super-admin/ai-review` — Low confidence & duplicate review queue
- `POST /api/super-admin/ai-review/{id}/override` — Manual classification override
- `GET /api/super-admin/users` — User directory
- `POST /api/super-admin/users/department-admin` — Provision new department admin
- `PUT /api/super-admin/users/{id}/status` — Enable / disable user accounts
- `GET /api/super-admin/departments` — List departments & load capacity
- `GET /api/super-admin/audit-logs` — Immutable system audit trail

---

## Automated Verification Suite

The included test suite (`test_system.py`) validates the entire operational lifecycle:
1. System Health Check
2. Citizen Registration & JWT generation
3. Duplicate Email Prevention
4. Auth Profile Verification
5. Complaint Submission with AI Categorization
6. Spatial & Textual Duplicate Detection
7. Department Admin Authentication & Isolation
8. Department Admin Complaint Detail Retrieval
9. Strict Department Isolation (Cross-department access blocked with 403 Forbidden)
10. Department Admin Workflow (Acknowledge $\rightarrow$ In Progress $\rightarrow$ Resolved)
11. Citizen Resolution Confirmation (Resolved $\rightarrow$ Closed)
12. Super Admin Telemetry & Department Load
13. Super Admin AI Override with Audit Reason Preservation
14. System Audit Trail Logging
15. In-App Notifications Delivery

Run the suite anytime:
```bash
python test_system.py
```

---

## Future Roadmap

- **IoT Sensor Telemetry**: Automated alerts from pressure sensors on water mains and vibration sensors on flyovers.
- **Multimodal Vision Model**: Fine-tuned computer vision model to verify severity from uploaded photos.
- **GIS Heatmap Layers**: Real-time municipal map overlays showing cluster density of potholes and water leaks.
- **Multilingual Support**: Hindi, Marathi, and regional voice-to-text input for citizens.
- **SMS/WhatsApp Gateway**: Twilio / Meta WhatsApp Business API integration for offline complaint tracking.
