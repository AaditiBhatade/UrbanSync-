import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db_schema():
    """Ensures all tables and schema changes exist in the database."""
    Base.metadata.create_all(bind=engine)
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA table_info(complaints);")
                columns = [col[1] for col in cursor.fetchall()]
                if columns and "assigned_worker_id" not in columns:
                    cursor.execute("ALTER TABLE complaints ADD COLUMN assigned_worker_id INTEGER REFERENCES workers(id);")
                    conn.commit()

                cursor.execute("PRAGMA table_info(workers);")
                worker_columns = [col[1] for col in cursor.fetchall()]
                if worker_columns and "user_id" not in worker_columns:
                    cursor.execute("ALTER TABLE workers ADD COLUMN user_id INTEGER REFERENCES users(id);")
                    conn.commit()
            except Exception as e:
                print(f"[DB MIGRATION ERROR] {e}")
            finally:
                conn.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

