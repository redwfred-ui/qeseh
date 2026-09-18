import json
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# إعداد CORS لضمان قبول Stremio للطلبات
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MANIFEST = {
    "id": "org.qeseh.stremio.arabic",
    "version": "1.0.0",
    "name": "Qeseh Arabic",
    "description": "مشاهدة المسلسلات والأفلام التركية المترجمة من موقع قصة",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "idPrefixes": ["tt"],
    "catalogs": []
}

# ترويسات الاستجابة المباشرة لبرنامج Stremio
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Content-Type": "application/json"
}

@app.get("/")
async def root():
    return Response(content=json.dumps({"status": "Qeseh Addon Active"}), headers=CORS_HEADERS)

@app.get("/manifest.json")
async def get_manifest():
    return Response(content=json.dumps(MANIFEST), headers=CORS_HEADERS)

@app.get("/stream/{type}/{id}.json")
async def get_streams(type: str, id: str):
    return Response(content=json.dumps({"streams": []}), headers=CORS_HEADERS)
