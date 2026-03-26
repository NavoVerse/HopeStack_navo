import base64
import io
import numpy as np
import cv2
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from transformers import pipeline

app = FastAPI(title="FaceEmotion API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the facial emotion recognition pipeline
# This will download the model on the first run
print("Loading model: dima806/facial_emotions_image_detection...")
classifier = pipeline("image-classification", model="dima806/facial_emotions_image_detection")

# Load OpenCV's face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

class ImageRequest(BaseModel):
    image: str  # Base64 encoded image string

@app.post("/analyze")
async def analyze_emotions(request: ImageRequest):
    try:
        # Decode base64 image
        header, encoded = request.image.split(",", 1) if "," in request.image else ("", request.image)
        image_data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Convert PIL to OpenCV for face detection
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
        
        if len(faces) == 0:
            return JSONResponse(content={"error": "No face detected", "emotions": []})

        # Process the largest face found
        (x, y, w, h) = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
        face_crop = image.crop((x, y, x + w, y + h))
        
        # Run emotion classification
        results = classifier(face_crop)
        
        # Sort results by score
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        return {
            "emotions": results,
            "face_coords": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
        }
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "FaceEmotion API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
