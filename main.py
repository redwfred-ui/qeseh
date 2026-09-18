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
    "version": "1.1.0",
    "name": "Tom & Jerry Classic Complete",
    "description": "جميع حلقات توم وجيري الكلاسيكية المضمونة من أرشيف الإنترنت",
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

ARCHIVE_ITEM = "tom_and_jerry_1940_1958"
EPISODES_CACHE = []

def load_archive_episodes():
    """جلب قائمة جميع ملفات mp4 المتاحة حقيقياً في الأرشيف"""
    global EPISODES_CACHE
    if EPISODES_CACHE:
        return EPISODES_CACHE
    try:
        url = f"https://archive.org/metadata/{ARCHIVE_ITEM}"
        res = requests.get(url, timeout=10).json()
        files = res.get("files", [])
        
        mp4_files = [f for f in files if f.get("name", "").endswith(".mp4")]
        mp4_files.sort(key=lambda x: x["name"])
        
        for idx, file_info in enumerate(mp4_files, start=1):
            clean_name = file_info["name"].replace(".mp4", "").replace("_", " ")
            download_url = f"https://archive.org/download/{ARCHIVE_ITEM}/{file_info['name']}"
            EPISODES_CACHE.append({
                "ep": idx,
                "title": clean_name,
                "url": download_url
            })
    except Exception as e:
        print(f"Error loading archive metadata: {e}")
    return EPISODES_CACHE

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    episodes = load_archive_episodes()
    return Response(content=json.dumps({"status": "Active", "total_episodes_found": len(episodes)}), headers=CORS_HEADERS)

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
        "description": "جميع الحلقات الأصلية الكلاسيكية المضمونة مباشرة من الأرشيف."
    }
    return Response(content=json.dumps({"metas": [meta]}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/series/{id}.json")
def get_meta(id: str):
    episodes = load_archive_episodes()
    videos = []
    for item in episodes:
        videos.append({
            "id": f"tj_classic_1940:1:{item['ep']}",
            "title": f"الحلقة {item['ep']} - {item['title']}",
            "season": 1,
            "episode": item['ep']
        })

    meta_data = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": "https://upload.wikimedia.org/wikipedia/en/5/5f/Tom_and_Jerry_title_card.png",
        "description": f"مجموعة توم وجيري الكاملة (تم العثور على {len(episodes)} حلقة جاهزة للتشغيل).",
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
            episodes = load_archive_episodes()
            target_ep = next((e for e in episodes if e["ep"] == ep_num), None)
            if target_ep:
                streams.append({
                    "name": "Archive Direct HD",
                    "title": f"تشغيل مباشر - {target_ep['title']}",
                    "url": target_ep["url"]
                })
        except Exception as e:
            print(f"Stream error: {e}")

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
