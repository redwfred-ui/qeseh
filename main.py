import json
import urllib.parse
import urllib3
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MANIFEST = {
    "id": "org.qeseh.stremio.dynamic",
    "version": "2.0.0",
    "name": "Qeseh Eshq - قصة عشق الشامل",
    "description": "تصفح وبحث في كامل مكتبة مسلسلات وأفلام قصة عشق مباشرة",
    "resources": ["catalog", "meta", "stream"],
    "types": ["series", "movie"],
    "catalogs": [
        {
            "type": "series",
            "id": "qeseh_all_series",
            "name": "جميع مسلسلات قصة عشق",
            "extra": [{"name": "search", "isRequired": False}, {"name": "skip", "isRequired": False}]
        },
        {
            "type": "movie",
            "id": "qeseh_all_movies",
            "name": "جميع أفلام قصة عشق",
            "extra": [{"name": "search", "isRequired": False}, {"name": "skip", "isRequired": False}]
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

def scrape_qeseh_catalog(search_query=None, page=1, is_movie=False):
    metas = []
    if search_query:
        url = f"https://wwv.qeseh.com/?s={urllib.parse.quote(search_query)}"
    else:
        cat = "افلام-تركية" if is_movie else "مسلسلات-تركية"
        url = f"https://wwv.qeseh.com/category/{cat}/page/{page}/" if page > 1 else f"https://wwv.qeseh.com/category/{cat}/"

    try:
        res = requests.get(url, headers=HEADERS, timeout=6, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.select("article, .post-item, .box, .item")
            for art in articles:
                a_tag = art.find("a")
                img_tag = art.find("img")
                title_tag = art.find(["h2", "h3", "span"]) or a_tag

                if a_tag and a_tag.get("href"):
                    title = title_tag.get_text(strip=True) if title_tag else "عرض تركي"
                    link = a_tag["href"]
                    img_url = img_tag.get("src") or img_tag.get("data-src") if img_tag else ""
                    
                    # تشفير رابط الصفحة ليكون ID خاص بـ Stremio
                    item_id = "qeseh_" + urllib.parse.quote_plus(link)
                    
                    metas.append({
                        "id": item_id,
                        "type": "movie" if is_movie else "series",
                        "name": title,
                        "poster": img_url,
                        "description": f"شاهد {title} على قصة عشق"
                    })
    except Exception as e:
        print(f"Catalog Error: {e}")

    return metas

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    return Response(content=json.dumps({"status": "Qeseh Dynamic Active"}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/manifest.json")
def get_manifest():
    return Response(content=json.dumps(MANIFEST, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/catalog/{type}/{id}.json")
@app.get("/catalog/{type}/{id}/{extra}.json")
def get_catalog(type: str, id: str, extra: str = None):
    search_q = None
    skip = 0
    
    if extra:
        for param in extra.split("&"):
            if param.startswith("search="):
                search_q = urllib.parse.unquote(param.split("=")[1])
            elif param.startswith("skip="):
                try:
                    skip = int(param.split("=")[1])
                except:
                    skip = 0

    page = (skip // 20) + 1
    is_movie = (type == "movie")
    
    metas = scrape_qeseh_catalog(search_query=search_q, page=page, is_movie=is_movie)
    return Response(content=json.dumps({"metas": metas}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/{type}/{id}.json")
def get_meta(type: str, id: str):
    clean_id = id.replace(".json", "")
    return Response(content=json.dumps({
        "meta": {
            "id": clean_id,
            "type": type,
            "name": "مشاهدة عبر قصة عشق",
            "poster": "",
            "description": "انقر لعرض السيرفرات المتاحة"
        }
    }, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/stream/{type}/{id}.json")
def get_streams(type: str, id: str):
    clean_id = id.replace(".json", "")
    streams = []
    
    if clean_id.startswith("qeseh_"):
        target_url = urllib.parse.unquote_plus(clean_id.replace("qeseh_", ""))
        try:
            page_res = requests.get(target_url, headers=HEADERS, timeout=6, verify=False)
            if page_res.status_code == 200:
                page_soup = BeautifulSoup(page_res.text, "html.parser")
                iframes = page_soup.find_all("iframe")
                
                idx = 1
                for iframe in iframes:
                    src = iframe.get("src") or iframe.get("data-src")
                    if src:
                        if src.startswith("//"): src = "https:" + src
                        streams.append({
                            "name": "Qeseh Web",
                            "title": f"سيرفر قصة #{idx} (فتح خارجي)",
                            "externalUrl": src
                        })
                        idx += 1
        except Exception as e:
            print(f"Stream error: {e}")

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
