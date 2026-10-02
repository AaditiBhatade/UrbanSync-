import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# App configurations
APP_NAME = "UrbanSync"
APP_TAGLINE = "Connecting Citizens. Coordinating Cities."
APP_VERSION = "1.0.0"

# Secret & Auth
SECRET_KEY = os.getenv("JWT_SECRET", "urbansync-super-secret-development-key-2026-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/urbansync.db")

# Google OAuth (configured or gracefully handled if keys not provided)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# File Uploads
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Confidence Thresholds
CONFIDENCE_AUTO_ASSIGN = 0.75
CONFIDENCE_REVIEW_QUEUE = 0.50
