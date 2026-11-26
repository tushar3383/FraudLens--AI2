# FraudLens AI — 5-minute demonstration guide

## Before the demonstration
1. Start the app with `python run.py`.
2. Open `http://127.0.0.1:5000`.
3. Ensure the AI model has downloaded once before class.
4. Prepare one real photo, one AI-generated image, a short MP4 video, and a PDF that contains image content.
5. Use media that you have permission to analyze.

## Demonstration

### 1. Dashboard (30 seconds)
Explain that the dashboard opens directly without login or registration, as this is the local college-demo version.

### 2. Image analysis (90 seconds)
Upload an image. Explain:
- Flask receives the upload.
- File extension and size are checked.
- The image is preprocessed.
- The ONNX model estimates AI-generation likelihood.
- The system shows the assessment and metadata.
- SHA-256 generates a file fingerprint.

### 3. Video analysis (90 seconds)
Upload a short MP4. Explain:
- OpenCV reads the video properties.
- The app samples up to 12 frames.
- The same image detector analyzes each selected frame.
- The median sampled-frame score is shown.
- This is a demonstration workflow, not a dedicated video deepfake model.

### 4. PDF analysis (45 seconds)
Upload an unlocked PDF. Explain that PyMuPDF renders up to 8 selected pages and the image detector analyzes the rendered pages. Point out that text-heavy pages can make this estimate unreliable.

### 5. Database and report (60 seconds)
Open Analysis History. Show saved records. Open a result and download its PDF report. Explain the `analyses` and `frame_analyses` tables.

### 6. System design and security (30 seconds)
Explain the modular layers, local SQLite storage, file validation, random filenames, and future Azure architecture.

## Honest limitations to mention
- AI detection is probabilistic, not proof.
- Model performance can vary on new generators and compressed images.
- Video analysis samples frames only.
- No login is included in this version.
- Azure deployment is an architectural extension, not an active cloud integration.
