import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-this-local-demo-secret")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    REPORT_FOLDER = str(BASE_DIR / "reports")
    INSTANCE_FOLDER = str(BASE_DIR / "instance")
    DATABASE = str(BASE_DIR / "instance" / "fraudlens.db")
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf"}
    MAX_VIDEO_FRAMES = 12
    MAX_PDF_PAGES = 8
    VIDEO_SAMPLE_SECONDS = 2
