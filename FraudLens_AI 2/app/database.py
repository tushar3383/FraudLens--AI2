import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def connect(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            media_type TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            ai_likelihood REAL,
            camera_likelihood REAL,
            classification TEXT NOT NULL,
            model_name TEXT,
            confidence_note TEXT,
            metadata_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS frame_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            frame_number INTEGER NOT NULL,
            timestamp_seconds REAL NOT NULL,
            ai_likelihood REAL,
            classification TEXT,
            FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS pdf_page_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            ai_likelihood REAL,
            classification TEXT,
            FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at DESC);
        """)

def save_analysis(db_path, data, frames=None, pages=None):
    frames = frames or []
    pages = pages or []
    with connect(db_path) as con:
        cur = con.execute("""
            INSERT INTO analyses
            (filename, stored_name, media_type, sha256, file_size, ai_likelihood,
             camera_likelihood, classification, model_name, confidence_note,
             metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["filename"], data["stored_name"], data["media_type"], data["sha256"],
            data["file_size"], data.get("ai_likelihood"), data.get("camera_likelihood"),
            data["classification"], data.get("model_name"), data.get("confidence_note"),
            data.get("metadata_json", "{}"),
            datetime.now(timezone.utc).isoformat(timespec="seconds")
        ))
        analysis_id = cur.lastrowid
        for f in frames:
            con.execute("""
                INSERT INTO frame_analyses
                (analysis_id, frame_number, timestamp_seconds, ai_likelihood, classification)
                VALUES (?, ?, ?, ?, ?)
            """, (analysis_id, f["frame_number"], f["timestamp_seconds"],
                  f.get("ai_likelihood"), f.get("classification")))
        for page in pages:
            con.execute("""
                INSERT INTO pdf_page_analyses
                (analysis_id, page_number, ai_likelihood, classification)
                VALUES (?, ?, ?, ?)
            """, (analysis_id, page["page_number"], page.get("ai_likelihood"),
                  page.get("classification")))
        return analysis_id

def list_analyses(db_path, limit=100):
    with connect(db_path) as con:
        return con.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

def get_analysis(db_path, analysis_id):
    with connect(db_path) as con:
        item = con.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        frames = con.execute("SELECT * FROM frame_analyses WHERE analysis_id=? ORDER BY frame_number",
                             (analysis_id,)).fetchall()
        pages = con.execute("SELECT * FROM pdf_page_analyses WHERE analysis_id=? ORDER BY page_number",
                            (analysis_id,)).fetchall()
        return item, frames, pages

def delete_analysis(db_path, analysis_id):
    with connect(db_path) as con:
        row = con.execute("SELECT stored_name FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        con.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
        return row["stored_name"] if row else None

def dashboard_stats(db_path):
    with connect(db_path) as con:
        total = con.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        images = con.execute("SELECT COUNT(*) FROM analyses WHERE media_type='image'").fetchone()[0]
        videos = con.execute("SELECT COUNT(*) FROM analyses WHERE media_type='video'").fetchone()[0]
        pdfs = con.execute("SELECT COUNT(*) FROM analyses WHERE media_type='pdf'").fetchone()[0]
        ai = con.execute("SELECT COUNT(*) FROM analyses WHERE classification='Likely AI-generated'").fetchone()[0]
        real = con.execute("SELECT COUNT(*) FROM analyses WHERE classification='Likely camera-originated'").fetchone()[0]
        inconclusive = con.execute("SELECT COUNT(*) FROM analyses WHERE classification='Inconclusive'").fetchone()[0]
        return {"total": total, "images": images, "videos": videos, "pdfs": pdfs, "ai": ai,
                "real": real, "inconclusive": inconclusive}
