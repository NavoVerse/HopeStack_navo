import io
import os
import base64
import logging
import threading
import tempfile
from datetime import timedelta

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import librosa
import numpy as np
from sqlalchemy.orm import Session

import model as ml_model
import auth
import models
from database import engine, get_db

# --- Database Initialization ---
models.Base.metadata.create_all(bind=engine)

# --- Logging setup ---
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Emotion AI with Auth")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Label Mappings ---
LABEL_MAP = {
    "ang": "Angry", "hap": "Happy", "neu": "Neutral", "sad": "Sad",
    "anger": "Angry", "happy": "Happy", "neutral": "Neutral", "sad": "Sad",
    "surprise": "Surprised", "fear": "Fearful", "disgust": "Disgusted",
}

EMOJI_MAP = {
    "Angry": "😠", "Happy": "😊", "Sad": "😢", "Neutral": "😐",
    "Surprised": "😲", "Fearful": "😨", "Disgusted": "🤢",
}

COLOR_MAP = {
    "Angry": "#FF4757", "Happy": "#FFD700", "Sad": "#4B9FFF", "Neutral": "#A0AEC0",
    "Surprised": "#38BDF8", "Fearful": "#C084FC", "Disgusted": "#34D399",
}

# Startup logic
@app.on_event("startup")
async def startup():
    threading.Thread(target=ml_model.load_models, daemon=True).start()
    logger.info("Model loading started in background.")

# --- Models ---
class ImageRequest(BaseModel):
    image: str

# --- Auth Routes ---
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    path = os.path.join(os.path.dirname(__file__), "login.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(password)
    new_user = models.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    
    # Auto-login after signup
    access_token = auth.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token = auth.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# --- Core Routes (Protected) ---
@app.get("/", response_class=HTMLResponse)
async def index(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login")
    
    path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/status")
async def status():
    return JSONResponse(ml_model.get_status())

@app.post("/analyze/face")
async def analyze_face(req: ImageRequest, current_user: models.User = Depends(auth.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    st = ml_model.get_status()["face"]
    if st["status"] == "loading":
        raise HTTPException(status_code=503, detail="Face model loading...")
    
    try:
        header, encoded = req.image.split(",", 1) if "," in req.image else ("", req.image)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        raw = ml_model.predict_face(image)
        if "error" in raw:
            return JSONResponse(content={"error": raw["error"], "emotions": []})
        
        formatted = []
        for r in raw["emotions"]:
            label = LABEL_MAP.get(r["label"].lower(), r["label"].capitalize())
            formatted.append({
                "label": label,
                "emoji": EMOJI_MAP.get(label, "👤"),
                "color": COLOR_MAP.get(label, "#94A3B8"),
                "score": round(r["score"] * 100, 1),
            })
        
        return {
            "emotions": sorted(formatted, key=lambda x: x["score"], reverse=True),
            "coords": raw["coords"]
        }
    except Exception as e:
        logger.error(f"Face error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/voice")
async def analyze_voice(audio: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    st = ml_model.get_status()["voice"]
    if st["status"] == "loading":
        raise HTTPException(status_code=503, detail="Voice model loading...")
    
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        audio_array, _ = librosa.load(tmp_path, sr=16000, mono=True)
        raw = ml_model.predict_voice(audio_array)
        
        formatted = []
        for r in raw:
            label = LABEL_MAP.get(r["label"].lower(), r["label"].capitalize())
            formatted.append({
                "label": label,
                "emoji": EMOJI_MAP.get(label, "🎙️"),
                "color": COLOR_MAP.get(label, "#94A3B8"),
                "score": round(r["score"] * 100, 1),
            })
        
        return {
            "emotions": sorted(formatted, key=lambda x: x["score"], reverse=True)
        }
    except Exception as e:
        logger.error(f"Voice error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
