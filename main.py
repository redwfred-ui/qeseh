import json
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# تفعيل CORS لضمان قبول جميع طلبات Stremio
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

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Content-Type": "application/json; charset=utf-8"
}

def get_title_from_imdb(imdb_id: str, item_type: str):
    """جلب اسم العمل من Cinemeta باستخدام ID الخاص بـ IMDB"""
    try:
        url = f"https://v3-cinemeta.stremio.com/meta/{item_type}/{imdb_id}.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("meta", {}).get("name")
    except Exception as e:
        print(f"Error fetching Cinemeta: {e}")
    return None

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """معالجة طلبات OPTIONS لضمان استقرار الاتصال"""
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
async def root():
    body = json.dumps({"status": "Qeseh Active"}, ensure_ascii=False)
    return Response(content=body, headers=CORS_HEADERS)

@app.get("/manifest.json")
async def get_manifest():
    body = json.dumps(MANIFEST, ensure_ascii=False)
    return Response(content=body, headers=CORS_HEADERS)

@app.get("/stream/{type}/{id}.json")
async def get_streams(type: str, id: str):
    parts = id.split(":")
    imdb_id = parts[0]
    season = parts[1] if len(parts) > 1 else None
    episode = parts[2] if len(parts) > 2 else None

    title = get_title_from_imdb(imdb_id, type)
    streams = []

    if title:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            # البحث في موقع قصة عبر التمرير المباشر الآمن
            search_url = "https://wwv.qeseh.com/"
            res = requests.get(search_url, params={"s": title}, headers=headers, timeout=5)
            
            if res.status_code == 200:
                streams.append({
                    "name": "Qeseh",
                    "title": f"سيرفر قصة - {title}",
                    "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
                })
        except Exception as e:
            print(f"Error fetching Qeseh: {e}")

    body = json.dumps({"streams": streams}, ensure_ascii=False)
    return Response(content=body, headers=CORS_HEADERS)
