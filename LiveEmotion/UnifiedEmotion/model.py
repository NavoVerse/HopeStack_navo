import logging
import threading
import torch
from transformers import pipeline
import cv2
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)

# --- Model Shared State ---
_voice_pipe = None
_face_pipe = None
_face_cascade = None

_status = {
    "voice": {"status": "loading", "message": "Voice model initialising..."},
    "face": {"status": "loading", "message": "Face model initialising..."},
}
_lock = threading.Lock()

# --- Unified Configuration ---
VOICE_MODEL = "superb/hubert-large-superb-er"
FACE_MODEL = "dima806/facial_emotions_image_detection"

def load_models():
    """Load both models in background threads."""
    global _voice_pipe, _face_pipe, _face_cascade, _status
    
    device = 0 if torch.cuda.is_available() else -1
    device_name = "GPU" if device == 0 else "CPU"
    
    # 1. Load Voice Model
    try:
        logger.info(f"Loading voice model on {device_name}...")
        v_pipe = pipeline("audio-classification", model=VOICE_MODEL, device=device)
        with _lock:
            _voice_pipe = v_pipe
            _status["voice"] = {"status": "ready", "message": f"Voice ready ({device_name})"}
        logger.info("Voice model loaded.")
    except Exception as e:
        _status["voice"] = {"status": "error", "message": str(e)}
        logger.error(f"Voice load failed: {e}")

    # 2. Load Face Model
    try:
        logger.info(f"Loading face model on {device_name}...")
        f_pipe = pipeline("image-classification", model=FACE_MODEL, device=device)
        
        # Load OpenCV Face Detector
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        with _lock:
            _face_pipe = f_pipe
            _face_cascade = cascade
            _status["face"] = {"status": "ready", "message": f"Face ready ({device_name})"}
        logger.info("Face model loaded.")
    except Exception as e:
        _status["face"] = {"status": "error", "message": str(e)}
        logger.error(f"Face load failed: {e}")

def get_status():
    with _lock:
        return _status

def predict_voice(audio_array, sample_rate: int = 16000):
    with _lock:
        if _voice_pipe is None:
            raise RuntimeError("Voice model not loaded.")
        return _voice_pipe({"array": audio_array, "sampling_rate": sample_rate}, top_k=None)

def predict_face(image_pil):
    with _lock:
        if _face_pipe is None or _face_cascade is None:
            raise RuntimeError("Face model not loaded.")
            
        # Face Detection
        cv_img = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        faces = _face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(48, 48))
        
        if len(faces) == 0:
            return {"error": "No face detected"}
            
        # Use largest face
        (x, y, w, h) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
        face_crop = image_pil.crop((x, y, x + w, y + h))
        
        results = _face_pipe(face_crop)
        return {
            "emotions": results,
            "coords": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
        }
