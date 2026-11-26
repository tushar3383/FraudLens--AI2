"""
FraudLens AI image detector.
Model: TensorFold/detectra-v1 (MIT-licensed model card).
The model is downloaded on first use and cached by Hugging Face Hub.
No scores are fabricated: if the model cannot load, analysis is marked unavailable.
"""
import os
import numpy as np
from PIL import Image, ImageOps
from huggingface_hub import hf_hub_download
import onnxruntime as ort

MODEL_ID = "TensorFold/detectra-v1"
MODEL_FILE = "model.onnx"
_session = None
_model_error = None

def _load_session():
    global _session, _model_error
    if _session is not None:
        return _session
    if _model_error:
        raise RuntimeError(_model_error)
    try:
        model_path = hf_hub_download(repo_id=MODEL_ID, filename=MODEL_FILE)
        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _session = ort.InferenceSession(model_path, sess_options=options,
                                        providers=["CPUExecutionProvider"])
        return _session
    except Exception as exc:
        _model_error = (
            "The AI model could not be downloaded or loaded. Check your internet connection "
            "and try again. Technical detail: " + str(exc)
        )
        raise RuntimeError(_model_error)

def _preprocess(image):
    image = ImageOps.exif_transpose(image).convert("RGB")
    w, h = image.size
    scale = 440 / min(w, h)
    new_size = (max(384, int(round(w * scale))), max(384, int(round(h * scale))))
    image = image.resize(new_size, Image.Resampling.BILINEAR)
    left = (image.width - 384) // 2
    top = (image.height - 384) // 2
    image = image.crop((left, top, left + 384, top + 384))
    arr = np.asarray(image).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    return np.transpose(arr, (2, 0, 1))[None, ...]

def analyze_pil(image):
    session = _load_session()
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()[0]
    tensor = _preprocess(image)
    output = session.run([output_meta.name], {input_meta.name: tensor})[0]
    logit = float(np.asarray(output).reshape(-1)[0])
    # Detectra model card defines sigmoid(logit) as AI-generated probability.
    probability = 1.0 / (1.0 + np.exp(-np.clip(logit, -60, 60)))
    ai = float(np.clip(probability, 0, 1))
    return {
        "ai_likelihood": round(ai * 100, 1),
        "camera_likelihood": round((1 - ai) * 100, 1),
        "classification": ("Likely AI-generated" if ai >= 0.65 else
                           "Likely camera-originated" if ai <= 0.35 else "Inconclusive"),
        "model_name": MODEL_ID,
        "confidence_note": (
            "Model score is an estimated AI-generation likelihood, not proof. "
            "The 0.35–0.65 interval is treated as inconclusive."
        )
    }

def model_status():
    if _session is not None:
        return {"ready": True, "message": "AI model is loaded and ready."}
    if _model_error:
        return {"ready": False, "message": _model_error}
    return {"ready": False, "message": "Model will download automatically when you run your first analysis. Internet is required for the initial download."}
