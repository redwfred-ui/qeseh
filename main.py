from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# السماح لـ Stremio بالوصول للإضافة بدون حجب (CORS)
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

@app.get("/")
def root():
    return {"status": "Qeseh Addon is Running!"}

@app.get("/manifest.json")
def get_manifest():
    return MANIFEST

@app.get("/stream/{type}/{id}.json")
def get_streams(type: str, id: str):
    # هنا يتم وضع منطق الجلب من موقع قصة
    streams = []
    return {"streams": streams}

# Handler الخاص بـ Vercel Serverless
handler = Mangum(app)
