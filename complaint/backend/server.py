import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.routes.auth_routes import router as auth_router
from backend.routes.complaint_routes import router as complaint_router
from backend.routes.admin_routes import router as admin_router
from backend.routes.super_admin_routes import router as super_admin_router
from backend.routes.notification_routes import router as notification_router
from backend.routes.worker_routes import router as worker_router

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

from backend.models.database import init_db_schema
init_db_schema()

app = FastAPI(
    title="UrbanSync Civic Complaints Platform",
    description="Smart City Civic Infrastructure Management & AI Intelligence Platform",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include Routers
app.include_router(auth_router)
app.include_router(complaint_router)
app.include_router(admin_router)
app.include_router(super_admin_router)
app.include_router(notification_router)
app.include_router(worker_router)

# Mount Static Assets
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "UrbanSync",
        "version": "2.0.0",
        "ml_classification": "TF-IDF + Logistic Regression",
        "ml_clustering": "K-Means Hotspots"
    }

# SPA Fallback Routes for Frontend
INDEX_HTML = os.path.join(FRONTEND_DIR, "index.html")

@app.get("/")
def serve_index():
    return FileResponse(INDEX_HTML)

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    # Ignore API and static/uploads calls
    if full_path.startswith("api/") or full_path.startswith("static/") or full_path.startswith("uploads/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return FileResponse(INDEX_HTML)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
