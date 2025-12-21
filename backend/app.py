from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2

app = FastAPI()

# Für den Start ok. Später auf deine Netlify-URL einschränken!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    arr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "Bild konnte nicht gelesen werden."}

    # Demo: Durchschnittsfarbe (ersetzen durch deine Haarfarben-Logik)
    b, g, r = [int(x) for x in img.mean(axis=(0, 1))]
    return {
        "hex": f"#{r:02x}{g:02x}{b:02x}",
        "rgb": {"r": r, "g": g, "b": b},
        "note": "Demo. Hier kommt deine Haarfarben-Erkennung rein."
    }
