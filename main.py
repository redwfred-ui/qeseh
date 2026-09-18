import json
import requests
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MANIFEST = {
    "id": "org.tomandjerry.classic.complete",
    "version": "1.3.0",
    "name": "Tom & Jerry Classic Complete",
    "description": "جميع حلقات توم وجيري الكلاسيكية الـ 161 كاملة بدون تقطيع",
    "resources": ["catalog", "meta", "stream"],
    "types": ["series"],
    "idPrefixes": ["tj_classic"],
    "catalogs": [
        {
            "type": "series",
            "id": "tj_catalog",
            "name": "توم وجيري الكلاسيكي"
        }
    ]
}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Content-Type": "application/json; charset=utf-8"
}

ARCHIVE_BASE_URL = "https://archive.org/download/tom_and_jerry_1940_1958/Tom_and_Jerry_"
TOTAL_EPISODES = 161
URL_CACHE = {}

def get_direct_stream_url(initial_url: str) -> str:
    """تتبع إعادة التوجيه لـ Archive.org للحصول على رابط السيرفر المباشر لتفادي التعليق في Stremio"""
    if initial_url in URL_CACHE:
        return URL_CACHE[initial_url]
    try:
        res = requests.head(initial_url, allow_redirects=True, timeout=4)
        if res.status_code == 200:
            URL_CACHE[initial_url] = res.url
            return res.url
    except Exception as e:
        print(f"Redirect resolution error: {e}")
    return initial_url

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    return Response(content=json.dumps({"status": "Active", "total_episodes_found": TOTAL_EPISODES}), headers=CORS_HEADERS)

@app.get("/manifest.json")
def get_manifest():
    return Response(content=json.dumps(MANIFEST, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/catalog/series/tj_catalog.json")
def get_catalog():
    meta = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": "https://upload.wikimedia.org/wikipedia/en/5/5f/Tom_and_Jerry_title_card.png",
        "description": "جميع الحلقات الأصلية الكلاسيكية الـ 161 مباشرة من الأرشيف."
    }
    return Response(content=json.dumps({"metas": [meta]}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/series/{id}.json")
def get_meta(id: str):
    videos = []
    for i in range(1, TOTAL_EPISODES + 1):
        videos.append({
            "id": f"tj_classic_1940:1:{i}",
            "title": f"الحلقة {i} - Tom & Jerry Classic",
            "season": 1,
            "episode": i
        })

    meta_data = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": "https://upload.wikimedia.org/wikipedia/en/5/5f/Tom_and_Jerry_title_card.png",
        "description": "مجموعة توم وجيري الكاملة (161 حلقة جاهزة للتشغيل).",
        "videos": videos
    }
    return Response(content=json.dumps({"meta": meta_data}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/stream/series/{id}.json")
def get_streams(id: str):
    clean_id = id.replace(".json", "")
    parts = clean_id.split(":")
    streams = []
    if len(parts) >= 3:
        try:
            ep_num = int(parts[2])
            if 1 <= ep_num <= TOTAL_EPISODES:
                formatted_num = f"{ep_num:03d}"
                raw_url = f"{ARCHIVE_BASE_URL}{formatted_num}.mp4"
                
                # جلب الرابط المباشر النهائي بدون Redirect
                direct_url = get_direct_stream_url(raw_url)
                
                # سيرفر التشغيل المباشر
                streams.append({
                    "name": "Archive Direct HD",
                    "title": f"تشغيل مباشر - الحلقة {ep_num}",
                    "url": direct_url
                })
                
                # سيرفر الفتح بمشغل خارجي (VLC)
                streams.append({
                    "name": "External Player (VLC)",
                    "title": f"فتح بواسطة مشغل خارجي - الحلقة {ep_num}",
                    "externalUrl": direct_url
                })
        except Exception as e:
            print(f"Stream error: {e}")

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
