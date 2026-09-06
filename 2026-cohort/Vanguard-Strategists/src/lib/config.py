import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DATABASE_PATH = DB_DIR / "pollinator_plants.db"
STATIC_DIR = BASE_DIR / "statics"

DB_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    SQLALCHEMY_DATABASE_URI= os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    UPLOAD_FOLDER = STATIC_DIR/ "uploads"