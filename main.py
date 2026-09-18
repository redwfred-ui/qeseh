import json
import requests
from fastapi import FastAPI, Response, Request
from fastapi.responses import RedirectResponse
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
    "id": "org.tomandjerry.classic.nuvio",
    "version": "2.0.0",
    "name": "Tom & Jerry Classic (Complete)",
    "description": "جميع حلقات توم وجيري الـ 161 الكلاسيكية - مشغل مباشر متوافق مع Nuvio و Stremio",
    "resources": ["catalog", "meta", "stream"],
    "types": ["series", "movie"],
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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

ARCHIVE_ITEM = "tom_and_jerry_1940_1958"
EPISODES_CACHE = {}

def get_archive_episodes():
    global EPISODES_CACHE
    if EPISODES_CACHE:
        return EPISODES_CACHE
    
    try:
        url = f"https://archive.org/metadata/{ARCHIVE_ITEM}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            files = data.get("files", [])
            mp4_files = [f for f in files if f.get("name", "").lower().endswith(".mp4")]
            mp4_files.sort(key=lambda x: x.get("name", ""))
            
            for idx, file_info in enumerate(mp4_files, start=1):
                file_name = file_info["name"]
                clean_title = file_name.rsplit(".", 1)[0].replace("_", " ")
                download_url = f"https://archive.org/download/{ARCHIVE_ITEM}/{file_name}"
                
                EPISODES_CACHE[idx] = {
                    "ep": idx,
                    "title": clean_title,
                    "url": download_url
                }
    except Exception as e:
        print(f"Error loading archive metadata: {e}")
        
    return EPISODES_CACHE

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    episodes = get_archive_episodes()
    total = len(episodes) if episodes else 161
    return Response(content=json.dumps({"status": "Active", "total_episodes_found": total}), headers=CORS_HEADERS)

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
        "description": "جميع الحلقات الأصلية الكلاسيكية الـ 161 مباشرة بدون تقطيع."
    }
    return Response(content=json.dumps({"metas": [meta]}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/series/{id}.json")
def get_meta(id: str):
    episodes = get_archive_episodes()
    videos = []
    
    total_count = max(len(episodes), 161)
    for ep in range(1, total_count + 1):
        ep_title = episodes[ep]["title"] if ep in episodes else f"Tom & Jerry Episode {ep}"
        videos.append({
            "id": f"tj_classic_1940:1:{ep}",
            "title": f"الحلقة {ep} - {ep_title}",
            "season": 1,
            "episode": ep
        })

    meta_data = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": "https://upload.wikimedia.org/wikipedia/en/5/5f/Tom_and_Jerry_title_card.png",
        "description": f"مجموعة توم وجيري الكاملة ({total_count} حلقة جاهزة للتشغيل).",
        "videos": videos
    }
    return Response(content=json.dumps({"meta": meta_data}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/play/{ep_num}")
def play_stream(request: Request, ep_num: int):
    episodes = get_archive_episodes()
    
    if ep_num in episodes:
        raw_url = episodes[ep_num]["url"]
    else:
        formatted = f"{ep_num:03d}"
        raw_url = f"https://archive.org/download/{ARCHIVE_ITEM}/Tom_and_Jerry_{formatted}.mp4"

    try:
        res = requests.head(raw_url, headers=HEADERS, allow_redirects=True, timeout=5)
        target_url = res.url if res.status_code in [200, 301, 302] else raw_url
    except Exception:
        target_url = raw_url

    return RedirectResponse(url=target_url, status_code=307)

@app.get("/stream/series/{id}.json")
def get_streams(request: Request, id: str):
    clean_id = id.replace(".json", "")
    parts = clean_id.split(":")
    streams = []
    
    if len(parts) >= 3:
        try:
            ep_num = int(parts[2])
            base_host = str(request.base_url).rstrip("/")
            play_url = f"{base_host}/play/{ep_num}"
            
            episodes = get_archive_episodes()
            ep_title = episodes[ep_num]["title"] if ep_num in episodes else f"الحلقة {ep_num}"
            
            streams.append({
                "name": "Nuvio Direct Player",
                "title": f"تشغيل مباشر - {ep_title}",
                "url": play_url
            })
            
            if ep_num in episodes:
                streams.append({
                    "name": "Archive Direct Link",
                    "title": f"سيرفر الأرشيف - {ep_title}",
                    "url": episodes[ep_num]["url"]
                })
        except Exception as e:
            print(f"Stream error: {e}")

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
