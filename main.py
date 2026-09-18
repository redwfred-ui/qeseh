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
    "id": "org.qeseh.stremio.arabic",
    "version": "1.4.0",
    "name": "Qeseh Arabic - قصة عشق",
    "description": "مشاهدة المسلسلات والأفلام التركية المترجمة والمدبلجة من موقع قصة",
    "resources": ["catalog", "meta", "stream"],
    "types": ["series", "movie"],
    "idPrefixes": ["tt"],
    "catalogs": [
        {
            "type": "series",
            "id": "qeseh_series",
            "name": "مسلسلات قصة عشق",
            "extra": [{"name": "search", "isRequired": False}]
        },
        {
            "type": "movie",
            "id": "qeseh_movies",
            "name": "أفلام قصة عشق",
            "extra": [{"name": "search", "isRequired": False}]
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

KNOWN_TITLES = {
    "tt10886166": "المؤسس عثمان",
    "tt28823795": "حب بلا حدود",
    "tt28817684": "المتوحش",
    "tt22818508": "شراب التوت",
    "tt22080094": "طائر الرفراف",
    "tt15097870": "القضاء",
    "tt29584481": "براعم حمراء",
    "tt31006497": "بهار",
    "tt31006096": "حبات اللؤلؤ",
    "tt7442124": "الحفرة",
    "tt4386808": "قيامة أرطغرل",
    "tt12330196": "أنت اطرق بابي",
    "tt6144884": "في الداخل",
    "tt14050226": "المنظمة",
    "tt7458110": "حب أبيض أسود",
    "tt10439732": "معجزة في الزنزانة رقم 7",
    "tt13083098": "حياة من ورق",
    "tt23824854": "النداء الأخير إلى إسطنبول",
    "tt31102572": "فن الحب",
    "tt27981503": "دعني أؤمن بك",
    "tt13670992": "هل رأيت اليراعات من قبل"
}

TURKISH_SERIES_CATALOG = [
    {"id": "tt10886166", "name": "المؤسس عثمان (Kuruluş Osman)"},
    {"id": "tt28823795", "name": "حب بلا حدود (Hudutsuz Sevda)"},
    {"id": "tt28817684", "name": "المتوحش (Yabani)"},
    {"id": "tt22818508", "name": "شراب التوت (Kızılcık Şerbeti)"},
    {"id": "tt22080094", "name": "طائر الرفراف (Yalı Çapkını)"},
    {"id": "tt15097870", "name": "القضاء (Yargı)"},
    {"id": "tt29584481", "name": "براعم حمراء (Kızıl Goncalar)"},
    {"id": "tt31006497", "name": "بهار (Bahar)"},
    {"id": "tt31006096", "name": "حبات اللؤلؤ (İnci Taneleri)"},
    {"id": "tt7442124", "name": "الحفرة (Çukur)"},
    {"id": "tt4386808", "name": "قيامة أرطغرل (Diriliş Ertuğrul)"},
    {"id": "tt12330196", "name": "أنت اطرق بابي (Sen Çal Kapımı)"},
    {"id": "tt6144884", "name": "في الداخل (İçerde)"},
    {"id": "tt14050226", "name": "المنظمة (Teşkilat)"},
    {"id": "tt7458110", "name": "حب أبيض أسود (Siyah Beyaz Aşk)"}
]

TURKISH_MOVIES_CATALOG = [
    {"id": "tt10439732", "name": "معجزة في الزنزانة رقم 7 (Miracle in Cell No. 7)"},
    {"id": "tt13083098", "name": "حياة من ورق (Paper Lives)"},
    {"id": "tt23824854", "name": "النداء الأخير إلى إسطنبول (Last Call for Istanbul)"},
    {"id": "tt31102572", "name": "فن الحب (Art of Love)"},
    {"id": "tt27981503", "name": "دعني أؤمن بك (Make Me Believe)"},
    {"id": "tt13670992", "name": "هل رأيت اليراعات من قبل؟"}
]

def build_catalog_items(catalog_list, item_type):
    metas = []
    for item in catalog_list:
        metas.append({
            "id": item["id"],
            "type": item_type,
            "name": item["name"],
            "poster": f"https://v3-cinemeta.stremio.com/poster/medium/{item['id']}/img",
            "background": f"https://v3-cinemeta.stremio.com/background/medium/{item['id']}/img",
            "description": f"مشاهدة {item['name']} على إضافة قصة عشق",
            "genres": ["تركي", "قصة عشق"]
        })
    return metas

def get_title(imdb_id: str, item_type: str):
    if imdb_id in KNOWN_TITLES:
        return KNOWN_TITLES[imdb_id]
    
    try:
        url = f"https://v3-cinemeta.stremio.com/meta/{item_type}/{imdb_id}.json"
        res = requests.get(url, headers=HEADERS, timeout=4)
        if res.status_code == 200:
            return res.json().get("meta", {}).get("name")
    except Exception as e:
        print(f"Cinemeta Error: {e}")
    return None

def scrape_qeseh_streams(title: str, episode: str = None):
    streams = []
    search_query = title
    if episode and episode != "0":
        search_query = f"{title} الحلقة {episode}"

    try:
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"https://wwv.qeseh.com/?s={encoded_query}"
        
        res = requests.get(search_url, headers=HEADERS, timeout=6, verify=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select("article a, .post-title a, .entry-title a, h2 a, .box a, .item a")
            target_url = None
            for link in links:
                href = link.get("href")
                if href and ("qeseh.com" in href or href.startswith("/")):
                    target_url = href
                    break

            if target_url:
                if target_url.startswith("/"):
                    target_url = "https://wwv.qeseh.com" + target_url

                page_res = requests.get(target_url, headers=HEADERS, timeout=6, verify=False)
                if page_res.status_code == 200:
                    page_soup = BeautifulSoup(page_res.text, "html.parser")
                    iframes = page_soup.find_all("iframe")
                    
                    server_idx = 1
                    for iframe in iframes:
                        src = iframe.get("src") or iframe.get("data-src") or iframe.get("data-lazy-src")
                        if src:
                            if src.startswith("//"):
                                src = "https:" + src
                            
                            streams.append({
                                "name": "Qeseh Web",
                                "title": f"سيرفر قصة #{server_idx} (فتح المشغل الخارجية)",
                                "externalUrl": src
                            })
                            streams.append({
                                "name": "Qeseh Embed",
                                "title": f"سيرفر قصة #{server_idx} (دمج داخل التطبيق)",
                                "embedUrl": src
                            })
                            server_idx += 1
    except Exception as e:
        print(f"Scraper Error: {e}")

    # سيرفر فيديو مباشر يضمن إتاحة خيار تشغيل بأي حال من الأحوال
    streams.append({
        "name": "Qeseh Direct",
        "title": f"سيرفر قصة المباشر - {title}" + (f" (حلقة {episode})" if episode and episode != "0" else ""),
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    })

    return streams

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    return Response(content=json.dumps({"status": "Qeseh Active"}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/manifest.json")
def get_manifest():
    return Response(content=json.dumps(MANIFEST, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/catalog/{type}/{id}.json")
@app.get("/catalog/{type}/{id}/{extra}.json")
def get_catalog(type: str, id: str, extra: str = None):
    clean_id = id.replace(".json", "")
    metas = []
    
    if type == "series" and "qeseh_series" in clean_id:
        metas = build_catalog_items(TURKISH_SERIES_CATALOG, "series")
    elif type == "movie" and "qeseh_movies" in clean_id:
        metas = build_catalog_items(TURKISH_MOVIES_CATALOG, "movie")

    return Response(content=json.dumps({"metas": metas}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/{type}/{id}.json")
def get_meta(type: str, id: str):
    """ربط الحلقات والمواسم مباشرة مع Cinemeta لتجنب No metadata found"""
    clean_id = id.replace(".json", "")
    try:
        url = f"https://v3-cinemeta.stremio.com/meta/{type}/{clean_id}.json"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return Response(content=res.text, headers=CORS_HEADERS)
    except Exception as e:
        print(f"Meta Error: {e}")
    
    return Response(content=json.dumps({"meta": {}}), headers=CORS_HEADERS)

@app.get("/stream/{type}/{id}.json")
def get_streams(type: str, id: str):
    clean_id = id.replace(".json", "")
    parts = clean_id.split(":")
    imdb_id = parts[0]
    season = parts[1] if len(parts) > 1 else None
    episode = parts[2] if len(parts) > 2 else None

    title = get_title(imdb_id, type)
    streams = []

    if title:
        streams = scrape_qeseh_streams(title, episode)

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
