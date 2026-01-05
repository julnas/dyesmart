from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from image_analysis import analyze_hair_image_simple

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dyesmart.netlify.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*--dyesmart\.netlify\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "data": {"status": "healthy"}}


@app.post("/analyze")
async def analyze(
    # Frontends nutzen oft "file" ODER "image" als Feldname -> wir unterstützen beides
    file: UploadFile | None = File(default=None),
    image: UploadFile | None = File(default=None),
):
    upload = file or image
    if upload is None:
        return {"ok": False, "error": {"code": "NO_FILE", "message": "No file uploaded. Use form-data field 'file' or 'image'."}}

    image_bytes = await upload.read()
    result = analyze_hair_image_simple(image_bytes)

    # Wenn dein Analyzer Fehler als {"error": "..."} zurückgibt, sauber wrappen:
    if isinstance(result, dict) and "error" in result:
        return {"ok": False, "error": {"code": "ANALYZE_FAILED", "message": result["error"]}}

    # Frontend-freundlich: konsistente Keys
    # (du kannst hier auch die alten Keys zusätzlich drin lassen, falls du willst)
    data = {
        "depth": result.get("source_depth"),
        "nuance": result.get("source_nuance"),
        "avgColor": result.get("avg_color"),  # [r,g,b]
        "depthName": result.get("depth_name"),
        "nuanceName": result.get("nuance_name"),
        "info": result.get("info"),
        "raw": result,  # optional: kompletten Raw-Output mitschicken
    }
    return {"ok": True, "data": data}


@app.post("/recipe")
def recipe(
    source_depth: int = Form(...),
    source_nuance: float = Form(...),
    target_depth: int = Form(...),
    target_nuance: float = Form(...),
):
    """
    Minimaler Rezept-Endpoint passend zu deiner UI.
    Logik ist erstmal Placeholder – du kannst hier später die echte Farbrezept-Berechnung ergänzen.
    """
    # super simple heuristik:
    lift = max(0, target_depth - source_depth)

    if lift >= 3:
        oxidant = "9%"
    elif lift == 2:
        oxidant = "6%"
    elif lift == 1:
        oxidant = "3%"
    else:
        oxidant = "3%"

    recipe_text = (
        f"Quelle: Tiefe {source_depth}, Nuance {source_nuance}\n"
        f"Ziel:   Tiefe {target_depth}, Nuance {target_nuance}\n\n"
        f"Oxidant: {oxidant}\n"
        f"Beispiel: 1:1 Farbe : Oxidant\n"
        f"Hinweis: Rezept-Logik ist aktuell vereinfacht."
    )

    return {
        "ok": True,
        "data": {
            "source": {"depth": source_depth, "nuance": source_nuance},
            "target": {"depth": target_depth, "nuance": target_nuance},
            "oxidant": oxidant,
            "recipe": recipe_text,
        }
    }
