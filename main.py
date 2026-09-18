from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# إعداد CORS الكامل المطلوبة لـ Stremio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MANIFEST = {
    "id": "com.qeseh.stremio.addon",
    "version": "1.0.0",
    "name": "Qeseh Arabic",
    "description": "Stream Arabic content from Qeseh on Stremio",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"],
    "catalogs": []
}

# معالجة طلبات OPTIONS لجميع المسارات (ضروري جداً لبرنامج Stremio Desktop)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.get("/")
def root():
    return {"status": "Qeseh Addon is Running!"}

@app.get("/manifest.json")
def get_manifest():
    return MANIFEST

@app.get("/stream/{type}/{id}.json")
def get_streams(type: str, id: str):
    return {"streams": []}
