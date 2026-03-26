"""
model.py — Loads and wraps the HuggingFace Speech Emotion Recognition pipeline.
Model: superb/hubert-large-superb-er (trained on IEMOCAP)
Labels: ang (Angry), hap (Happy), neu (Neutral), sad (Sad)
"""

import logging
import threading
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

_pipe = None
_status = {"status": "loading", "message": "Model is being initialised…"}
_lock = threading.Lock()


def load_model():
    """Download (first run only) and load the SER pipeline. Runs in a background thread."""
    global _pipe, _status
    try:
        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU (CUDA)" if device == 0 else "CPU"
        logger.info(f"Loading model on {device_name}…")
        _status = {
            "status": "loading",
            "message": f"Downloading / loading model on {device_name} — first run may take a few minutes…",
        }

        pipe = pipeline(
            "audio-classification",
            model="superb/hubert-large-superb-er",
            device=device,
        )

        with _lock:
            _pipe = pipe

        _status = {"status": "ready", "message": f"Model ready · running on {device_name}"}
        logger.info("Model loaded successfully.")

    except Exception as exc:
        _status = {"status": "error", "message": f"Failed to load model: {exc}"}
        logger.error(f"Model loading failed: {exc}")


def get_status() -> dict:
    return _status


def predict(audio_array, sample_rate: int = 16000) -> list:
    """Run the classifier pipeline and return a list of {label, score} dicts."""
    with _lock:
        if _pipe is None:
            raise RuntimeError("Model not loaded yet.")
        results = _pipe(
            {"array": audio_array, "sampling_rate": sample_rate},
            top_k=None,
        )
    return results
