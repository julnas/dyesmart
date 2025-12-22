from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from image_analysis import analyze_hair_image_simple

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dyesmart.netlify.app",
    ],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_bytes = await file.read()
    return analyze_hair_image_simple(image_bytes)
