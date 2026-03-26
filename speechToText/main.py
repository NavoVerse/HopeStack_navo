import os
import shutil
import whisper
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Load Whisper model globally
print("Loading Whisper model (base)...")
model = whisper.load_model("base")
print("Model loaded.")

# Ensure temp directory exists
TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(exist_ok=True)

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Check if file is provided
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Check file extension (basic check)
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_ext}")

    # Generate temporary path
    temp_file_path = TEMP_DIR / f"{file.filename}"
    
    try:
        # Save uploaded file
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Perform transcription
        print(f"Transcribing {file.filename}...")
        result = model.transcribe(str(temp_file_path))
        print("Transcription complete.")
        
        return JSONResponse(content={
            "text": result["text"],
            "language": result["language"]
        })
        
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Cleanup: Remove temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()

@app.get("/")
async def read_index():
    return FileResponse("index.html")

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
