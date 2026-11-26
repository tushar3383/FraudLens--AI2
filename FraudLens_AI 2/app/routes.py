\
import os
import json
import uuid
import statistics
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_file, abort, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from .database import list_analyses, save_analysis, get_analysis, delete_analysis, dashboard_stats
from .detector import analyze_pil, model_status
from .forensics import sha256_file, image_metadata, video_metadata, pdf_metadata
from .reports import create_pdf

bp = Blueprint("main", __name__)

@bp.app_errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 100 MB.", "error")
    return redirect(url_for("main.dashboard"))

@bp.route("/")
def dashboard():
    records = list_analyses(current_app.config["DATABASE"], 8)
    stats = dashboard_stats(current_app.config["DATABASE"])
    status = model_status()
    return render_template("dashboard.html", records=records, stats=stats, model_status=status)

@bp.route("/analyze", methods=["POST"])
def analyze():
    uploaded = request.files.get("media")
    if not uploaded or not uploaded.filename:
        flash("Choose an image, video, or PDF file first.", "error")
        return redirect(url_for("main.dashboard"))
    original = secure_filename(uploaded.filename)
    if not original:
        flash("Invalid filename.", "error")
        return redirect(url_for("main.dashboard"))

    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    image_ext = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    video_ext = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]
    pdf_ext = current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"]
    if ext not in image_ext | video_ext | pdf_ext:
        flash("Unsupported file type. Upload JPG, PNG, WEBP, BMP, MP4, MOV, AVI, MKV, WEBM, or PDF.", "error")
        return redirect(url_for("main.dashboard"))

    stored = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
    uploaded.save(path)
    size = os.path.getsize(path)
    if size == 0:
        os.remove(path)
        flash("The uploaded file is empty.", "error")
        return redirect(url_for("main.dashboard"))

    media_type = "image" if ext in image_ext else ("video" if ext in video_ext else "pdf")
    frames = []
    pages = []
    model_result = None
    metadata = {}
    error = None

    try:
        if media_type == "image":
            try:
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    metadata = image_metadata(path)
                    model_result = analyze_pil(im.copy())
            except (UnidentifiedImageError, OSError) as exc:
                raise ValueError("The uploaded file is not a valid readable image.") from exc

        elif media_type == "video":
            try:
                import cv2
            except ImportError as exc:
                raise RuntimeError("OpenCV is not installed. Run: pip install opencv-python-headless") from exc
            metadata = video_metadata(path, cv2)
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                raise ValueError("Could not open this video. Try MP4 (H.264) format.")
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total <= 0:
                cap.release()
                raise ValueError("No readable frames were found in this video.")
            max_frames = current_app.config["MAX_VIDEO_FRAMES"]
            sample_count = min(max_frames, max(1, int(metadata.get("duration_seconds") or 1)))
            indices = sorted(set(int(i * max(total - 1, 0) / max(sample_count - 1, 1))
                                  for i in range(sample_count)))
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = analyze_pil(Image.fromarray(rgb))
                seconds = round(idx / fps, 2) if fps > 0 else 0.0
                frames.append({
                    "frame_number": idx, "timestamp_seconds": seconds,
                    "ai_likelihood": result["ai_likelihood"],
                    "classification": result["classification"]
                })
            cap.release()
            if not frames:
                raise ValueError("Could not extract analyzable frames from this video.")
            median_ai = statistics.median(f["ai_likelihood"] for f in frames)
            model_result = {
                "ai_likelihood": round(median_ai, 1),
                "camera_likelihood": round(100 - median_ai, 1),
                "classification": ("Likely AI-generated" if median_ai >= 65 else
                                   "Likely camera-originated" if median_ai <= 35 else "Inconclusive"),
                "model_name": "TensorFold/detectra-v1 (sampled video frames)",
                "confidence_note": "Median of sampled-frame AI likelihoods. This is not a validated video deepfake detector."
            }
            metadata["analyzed_frames"] = len(frames)
            metadata["sampling_note"] = "Selected frames only were analyzed; unsampled content may differ."

        else:  # PDF: render selected pages and analyze each rendered page as an image.
            try:
                import fitz  # PyMuPDF
            except ImportError as exc:
                raise RuntimeError("PDF support is missing. Run: pip install PyMuPDF") from exc
            with open(path, "rb") as pdf_file:
                pdf_header = pdf_file.read(5)
            if not pdf_header.startswith(b"%PDF-"):
                raise ValueError("The uploaded file does not have a valid PDF header.")
            document = fitz.open(path)
            try:
                if document.needs_pass:
                    raise ValueError("Password-protected PDFs are not supported. Upload an unlocked PDF.")
                if document.page_count < 1:
                    raise ValueError("The PDF contains no pages.")
                metadata = pdf_metadata(path, document)
                max_pages = current_app.config["MAX_PDF_PAGES"]
                page_count = document.page_count
                if page_count <= max_pages:
                    page_indices = list(range(page_count))
                else:
                    page_indices = sorted(set(round(i * (page_count - 1) / (max_pages - 1))
                                              for i in range(max_pages)))
                for page_index in page_indices:
                    page = document.load_page(page_index)
                    rect = page.rect
                    max_dimension = max(float(rect.width), float(rect.height), 1.0)
                    scale = min(1.5, 1600.0 / max_dimension)
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                                              colorspace=fitz.csRGB, alpha=False)
                    page_image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                    page_result = analyze_pil(page_image)
                    pages.append({
                        "page_number": page_index + 1,
                        "ai_likelihood": page_result["ai_likelihood"],
                        "classification": page_result["classification"]
                    })
                if not pages:
                    raise ValueError("No readable PDF pages could be rendered.")
            finally:
                document.close()
            median_ai = statistics.median(page["ai_likelihood"] for page in pages)
            model_result = {
                "ai_likelihood": round(median_ai, 1),
                "camera_likelihood": round(100 - median_ai, 1),
                "classification": ("Likely AI-generated" if median_ai >= 65 else
                                   "Likely camera-originated" if median_ai <= 35 else "Inconclusive"),
                "model_name": "TensorFold/detectra-v1 (sampled PDF page renders)",
                "confidence_note": "Median of selected rendered-page estimates. The image detector evaluates page appearance, not PDF text authorship or document integrity; text-heavy pages may produce unreliable estimates."
            }
            metadata["analyzed_pages"] = len(pages)
            metadata["sampled_page_numbers"] = [page["page_number"] for page in pages]
            metadata["sampling_note"] = "Up to the configured page limit were rendered and analyzed. Pages not sampled were not inspected."

    except Exception as exc:
        error = str(exc)
        if not metadata:
            metadata = {"analysis_error": error}

    digest = sha256_file(path)
    data = {
        "filename": original, "stored_name": stored, "media_type": media_type,
        "sha256": digest, "file_size": size,
        "ai_likelihood": model_result.get("ai_likelihood") if model_result else None,
        "camera_likelihood": model_result.get("camera_likelihood") if model_result else None,
        "classification": model_result.get("classification", "Analysis unavailable") if model_result else "Analysis unavailable",
        "model_name": model_result.get("model_name") if model_result else None,
        "confidence_note": model_result.get("confidence_note") if model_result else error,
        "metadata_json": json.dumps(metadata, ensure_ascii=False)
    }
    analysis_id = save_analysis(current_app.config["DATABASE"], data, frames, pages)
    if error:
        flash("The file was saved to history, but model analysis was unavailable: " + error, "warning")
    return redirect(url_for("main.result", analysis_id=analysis_id))

@bp.route("/result/<int:analysis_id>")
def result(analysis_id):
    record, frames, pages = get_analysis(current_app.config["DATABASE"], analysis_id)
    if not record:
        abort(404)
    metadata = json.loads(record["metadata_json"] or "{}")
    return render_template("result.html", record=record, frames=frames, pages=pages, metadata=metadata)

@bp.route("/history")
def history():
    records = list_analyses(current_app.config["DATABASE"], 100)
    return render_template("history.html", records=records)

@bp.route("/report/<int:analysis_id>")
def report(analysis_id):
    record, frames, pages = get_analysis(current_app.config["DATABASE"], analysis_id)
    if not record:
        abort(404)
    metadata = json.loads(record["metadata_json"] or "{}")
    out = os.path.join(current_app.config["REPORT_FOLDER"], f"FraudLens_Report_{analysis_id}.pdf")
    create_pdf(out, record, metadata, frames, pages)
    return send_file(out, as_attachment=True, download_name=f"FraudLens_Report_{analysis_id}.pdf")

@bp.route("/delete/<int:analysis_id>", methods=["POST"])
def delete(analysis_id):
    stored = delete_analysis(current_app.config["DATABASE"], analysis_id)
    if stored:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
        if os.path.isfile(path):
            os.remove(path)
        flash("Analysis record and uploaded file deleted.", "success")
    return redirect(url_for("main.history"))

@bp.route("/api/stats")
def api_stats():
    return jsonify(dashboard_stats(current_app.config["DATABASE"]))

@bp.route("/health")
def health():
    return jsonify({"status": "ok", "application": "FraudLens AI", "authentication": "disabled"})
