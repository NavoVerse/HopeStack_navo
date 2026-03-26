"""
app.py — FastAPI backend for the Voice Emotion Recognizer.

Endpoints:
  GET  /         → Serves index.html
  GET  /status   → Returns model loading status
  POST /predict  → Accepts WAV audio, returns emotion prediction JSON
"""

import io
import logging
import os
import tempfile
import threading

import librosa
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

import model as ml_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Label mappings ─────────────────────────────────────────────────────────────

LABEL_MAP = {
    "ang": "Angry",
    "hap": "Happy",
    "neu": "Neutral",
    "sad": "Sad",
    "angry": "Angry",
    "happy": "Happy",
    "neutral": "Neutral",
    "fearful": "Fearful",
    "fear": "Fearful",
    "dis": "Disgusted",
    "disgust": "Disgusted",
    "exc": "Excited",
    "surprised": "Surprised",
    "surprise": "Surprised",
    "calm": "Calm",
}

EMOJI_MAP = {
    "Angry": "😠",
    "Happy": "😊",
    "Sad": "😢",
    "Neutral": "😐",
    "Fearful": "😨",
    "Disgusted": "🤢",
    "Excited": "🤩",
    "Surprised": "😲",
    "Calm": "😌",
}

COLOR_MAP = {
    "Angry":    "#FF4757",
    "Happy":    "#FFD700",
    "Sad":      "#4B9FFF",
    "Neutral":  "#A0AEC0",
    "Fearful":  "#C084FC",
    "Disgusted":"#34D399",
    "Excited":  "#FF9500",
    "Surprised":"#38BDF8",
    "Calm":     "#6EE7B7",
}

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Voice Emotion Recognizer")


@app.on_event("startup")
async def startup_event():
    """Start model loading in a background thread so the server responds immediately."""
    t = threading.Thread(target=ml_model.load_model, daemon=True)
    t.start()
    logger.info("Model loading started in background thread.")


# ── Routes ─────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/status")
async def status():
    return JSONResponse(ml_model.get_status())


@app.post("/predict")
async def predict(audio: UploadFile = File(...)):
    # ── Read uploaded bytes ───────────────────────────────────────────────
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    # ── Model ready? ──────────────────────────────────────────────────────
    st = ml_model.get_status()
    if st["status"] == "loading":
        raise HTTPException(status_code=503, detail="Model is still loading — please wait a moment and try again.")
    if st["status"] == "error":
        raise HTTPException(status_code=500, detail=st["message"])

    # ── Write to temp file and load with librosa ──────────────────────────
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        audio_array, _ = librosa.load(tmp_path, sr=16000, mono=True)

        if len(audio_array) < 3200:  # < 0.2 s at 16kHz
            raise HTTPException(status_code=400, detail="Recording is too short. Please record at least 1 second of speech.")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Audio loading error: {exc}")
        raise HTTPException(status_code=422, detail=f"Could not decode audio: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # ── Run inference ─────────────────────────────────────────────────────
    try:
        raw_results = ml_model.predict(audio_array, 16000)
    except Exception as exc:
        logger.error(f"Inference error: {exc}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    # ── Format results ────────────────────────────────────────────────────
    formatted = []
    for r in raw_results:
        raw_label = r["label"].lower()
        label = LABEL_MAP.get(raw_label, raw_label.capitalize())
        formatted.append({
            "label": label,
            "emoji": EMOJI_MAP.get(label, "🎙️"),
            "color": COLOR_MAP.get(label, "#94A3B8"),
            "score": round(r["score"] * 100, 1),
        })

    formatted.sort(key=lambda x: x["score"], reverse=True)
    top = formatted[0]

    return JSONResponse({
        "emotion": top["label"],
        "emoji":   top["emoji"],
        "color":   top["color"],
        "confidence": top["score"],
        "all_scores": formatted,
    })
