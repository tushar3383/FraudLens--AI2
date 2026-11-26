from PIL import Image, ExifTags
import hashlib
import json
import mimetypes
import os

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def image_metadata(path):
    info = {}
    with Image.open(path) as im:
        info["format"] = im.format
        info["width"] = im.width
        info["height"] = im.height
        info["mode"] = im.mode
        info["file_size_bytes"] = os.path.getsize(path)
        try:
            exif = im.getexif()
            for tag_id, value in exif.items():
                name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    value = f"<binary data: {len(value)} bytes>"
                info[str(name)] = str(value)[:300]
        except Exception:
            info["exif_status"] = "No readable EXIF metadata"
    info["mime_type_guess"] = mimetypes.guess_type(path)[0]
    info["metadata_note"] = "Metadata can be missing, stripped, or edited; it does not prove authenticity."
    return info

def video_metadata(path, cv2):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return {
        "width": width, "height": height, "fps": round(fps, 3),
        "frame_count": int(frames),
        "duration_seconds": round(frames / fps, 2) if fps > 0 else None,
        "metadata_note": "Container metadata may be incomplete or altered."
    }

def pretty_metadata(raw):
    try:
        return json.dumps(json.loads(raw or "{}"), indent=2, ensure_ascii=False)
    except Exception:
        return raw or "{}"


def pdf_metadata(path, document):
    """Return safe, concise document metadata for a PyMuPDF document."""
    info = document.metadata or {}
    metadata = {
        "format": "PDF",
        "page_count": document.page_count,
        "title": info.get("title") or "Not provided",
        "author": info.get("author") or "Not provided",
        "creator": info.get("creator") or "Not provided",
        "producer": info.get("producer") or "Not provided",
        "creation_date": info.get("creationDate") or "Not provided",
        "modification_date": info.get("modDate") or "Not provided",
        "file_size_bytes": os.path.getsize(path),
        "metadata_note": "PDF metadata can be missing or edited and does not prove authenticity."
    }
    return metadata
