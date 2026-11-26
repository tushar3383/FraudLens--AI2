# FraudLens AI

**AI-Powered Image & Video Authenticity Detection and Digital Forensics Platform**

FraudLens AI is a local-first Flask application. It starts directly on the dashboard: **there is no login or registration page**.

## Features

- AI-generated image likelihood estimation using `TensorFold/detectra-v1` (ONNX).
- Video analysis by extracting and analyzing a limited set of frames with the same image detector.
- PDF upload with metadata extraction and limited page rendering/analysis.
- Frame-level results and a median sampled-frame estimate.
- Image/video metadata inspection.
- SHA-256 file fingerprint.
- SQLite analysis history.
- PDF forensic report generation.
- Dashboard analytics.
- Dark/light theme.
- Upload size and extension checks.

## Important model and interpretation notes

The image detector model is downloaded from Hugging Face on first analysis and cached locally. Internet access is needed for that first download. Model repository: https://huggingface.co/TensorFold/detectra-v1

The model card describes a ViT-S/16 binary detector and specifies that sigmoid(logit) is the estimated AI-generated probability. The model is MIT-licensed according to its model card. Read the model card and its evaluation caveats before presenting results.

This project does **not** contain a dedicated video deepfake model. Video analysis samples up to 12 frames and applies the image detector to those frames. The displayed video estimate is the median sampled-frame score; it is not a validated whole-video authenticity probability. This is clearly stated in the UI and report.

A score is not proof. Detectors can produce false positives and false negatives, especially for unseen generators, edited/compressed files, and media outside their training distribution. Camera-origin likelihood is the complement of the detector's AI score, not independent proof that a camera captured the media.

If model download or inference fails, the app stores the analysis record as **Analysis unavailable** rather than generating fake scores.

## Requirements

- Windows 10/11
- Python 3.10 or 3.11 recommended
- Internet for initial model download
- Approximately 1 GB free disk space recommended for Python packages, model cache, and temporary files
- CPU inference is supported; an NVIDIA GPU is not required

## Run on Windows 11 (VS Code)

1. Extract the ZIP file.
2. Open the extracted `FraudLens_AI` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:

```powershell
py -3.11 -m venv .venv
```

5. Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

6. Upgrade pip and install requirements:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

7. Start the application:

```powershell
python run.py
```

8. Open this address in Chrome:

http://127.0.0.1:5000

The dashboard opens directly. No account is required.

## First model run

The first image/video analysis downloads the ONNX model from Hugging Face. Keep the terminal open and wait for the download to finish. Subsequent runs use the cached model.

## Supported uploads

Images: JPG, JPEG, PNG, WEBP, BMP  
Videos: MP4, MOV, AVI, MKV, WEBM  
Documents: PDF (unlocked PDFs only; up to 8 pages are sampled)  
Maximum upload size: 100 MB

Video codecs vary. MP4/H.264 is the recommended demonstration format.

## Project structure

```text
FraudLens_AI/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── detector.py
│   ├── forensics.py
│   ├── reports.py
│   ├── routes.py
│   ├── templates/
│   └── static/
├── docs/
├── instance/
├── reports/
├── uploads/
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Database

SQLite database is created automatically at `instance/fraudlens.db`. It stores analysis metadata, scores, model identifiers, SHA-256 hashes, and sampled-frame results. The uploaded media itself is stored in `uploads/`.

Delete an analysis from the History page to remove its database record and corresponding uploaded file.

## Security and privacy notes

- No user authentication is included, as requested. Anyone with access to the local app can view its dashboard and history.
- The development server binds to `127.0.0.1`, so it is intended for local demonstration only.
- Do not expose the debug server to the public internet.
- Uploaded files remain on the local machine until deleted.
- For production, add authentication, CSRF protection, HTTPS, rate limiting, malware scanning, isolated media processing, secret management, and private cloud storage.
- PDFs are rendered page-by-page using PyMuPDF. Up to 8 pages are sampled. The image detector evaluates rendered page appearance; it does not assess PDF text authorship, signatures, or complete document integrity. Text-heavy pages may produce unreliable scores. Password-protected PDFs are not supported. The current extension checks are a first filter, not a complete malware defense.

## System design and cloud computing

See `docs/SYSTEM_DESIGN.md` for architecture, data flow, ER diagram, API routes, security considerations, and an Azure-ready deployment proposal. Cloud services are documented as a design extension and are not configured in this local version.

## Troubleshooting

**`py` is not recognized**  
Install Python 3.11 from https://www.python.org/downloads/ and enable “Add Python to PATH”.

**Model download fails**  
Check internet access, then restart the app and retry. No detection score is fabricated when the model is unavailable.

**OpenCV cannot read a video**  
Convert the video to MP4 with H.264 encoding and try again.

**PDF upload is rejected or unreadable**  
Ensure the file is a valid, unlocked PDF and that PyMuPDF installed successfully (`pip install PyMuPDF`). Up to 8 pages are sampled in this version.

**Port 5000 is already in use**  
Change `port=5000` to `port=5001` in `run.py`, then open http://127.0.0.1:5001.

**PowerShell activation is blocked**  
Use the process-scoped execution policy command in the setup section.

## Academic use and attribution

This is an educational project. Attribute the detector to the authors of `TensorFold/detectra-v1` and cite its model card: https://huggingface.co/TensorFold/detectra-v1. Confirm model terms and evaluation claims directly from the model repository before redistribution or formal publication.
