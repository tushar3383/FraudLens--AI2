# FraudLens AI — Viva Questions and Answers

**1. What is FraudLens AI?**  
It is a web-based AI-assisted digital media authenticity assessment platform. It estimates whether images may be AI-generated and offers sampled-frame analysis for videos.

**2. What problem does it solve?**  
Realistic synthetic media can be difficult to distinguish from camera-captured content. The project gives users a model-based assessment and supporting forensic metadata.

**3. Which technologies are used?**  
Python, Flask, ONNX Runtime, OpenCV, Pillow, SQLite, HTML, CSS, JavaScript, Chart.js, and ReportLab.

**4. How does image detection work?**  
The image is validated, resized and normalized using the model's documented preprocessing. ONNX Runtime executes the detector. The model output logit is passed through a sigmoid to estimate AI-generation likelihood.

**5. What is ONNX Runtime?**  
It is a cross-platform inference engine for executing machine-learning models in ONNX format.

**6. Why is OpenCV used?**  
OpenCV reads video properties, seeks to selected timestamps, and extracts frames for image-model inference.

**7. Is this a dedicated video deepfake detector?**  
No. This version samples up to 12 video frames and applies an image detector to them. A dedicated temporal video model is future work.

**8. What does AI likelihood mean?**  
It is the detector's estimated AI-generation score, not a guarantee or proof.

**9. Why show inconclusive?**  
A middle score indicates the model is not sufficiently decisive under the chosen thresholds. It is safer than forcing a binary verdict.

**10. Why is camera-origin likelihood complementary?**  
The model outputs AI likelihood. The UI displays its complement as a simple counterpart, not as an independently verified camera-origin probability.

**11. What is SHA-256?**  
A cryptographic hash function that produces a 256-bit digest. It can help identify whether the file bytes have changed, but it does not prove origin.

**12. Which database is used?**  
SQLite. It stores analysis records and sampled-frame results. SQLite is easy to run locally and requires no separate database server.

**13. What are primary and foreign keys?**  
A primary key uniquely identifies a row. A foreign key links a row in one table to a related row in another table.

**14. How is System Design used?**  
The application is divided into presentation, application routes, media processing, AI inference, database, and report-generation modules.

**15. How is DBMS used?**  
The system stores analysis history, media properties, scores, timestamps, and video frame records in relational tables.

**16. How is Cloud Computing used?**  
The architecture proposes Azure App Service, Blob Storage, Azure Database for PostgreSQL, Azure Monitor, and Key Vault. These are future deployment components, not provisioned in the local demo.

**17. What security features are included?**  
Upload extension allow-listing, size limits, randomized storage names, localhost-only binding, and no direct public route to uploaded files.

**18. Why did you omit login and registration?**  
The current version is designed for a direct college demonstration. Authentication can be added in a future version. It should not be deployed publicly without access control.

**19. What are the limitations?**  
Detector errors, new image generators, compression, manipulated metadata, and the limited sampled-frame video workflow.

**20. What is the future scope?**  
Dedicated video detection, temporal analysis, audio deepfake detection, C2PA provenance, explainable heatmaps, user authentication, and full Azure deployment.


**21. Can FraudLens AI accept PDF files?**  
Yes. It validates the PDF, extracts document metadata, renders up to eight selected pages using PyMuPDF, and runs the image detector on each rendered page.

**22. Does PDF analysis prove that the document or its text was AI-generated?**  
No. The detector assesses the visual appearance of rendered pages. It does not determine who wrote the text, verify signatures, or prove document authenticity. Text-heavy pages may produce unreliable scores.

**23. Why are only selected PDF pages analyzed?**  
To keep processing time and memory use manageable for the college demo. The report records which page numbers were sampled.
