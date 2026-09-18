from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import re
import uvicorn

app = FastAPI(title="Qeseh Stremio Addon")

# 1. إعدادات الإضافة (Manifest)
MANIFEST = {
    "id": "com.qeseh.arabic.addon",
    "version": "1.0.0",
    "name": "Qeseh - موقع قصة",
    "description": "إضافة لمشاهدة المسلسلات والأفلام العربية والتركية من موقع قصة",
    "resources": ["stream"],
    "types": ["series", "movie"],
    "idPrefixes": ["qeseh"]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://wwv.qeseh.com/"
}

DOMAIN = "https://wwv.qeseh.com"

@app.get("/")
def home():
    return {"status": "Qeseh Addon is Running!"}

@app.get("/manifest.json")
def get_manifest():
    return MANIFEST

# 2. جلب روابط البث من موقع قصة
@app.get("/stream/{type}/{id}.json")
def get_stream(type: str, id: str):
    streams = []
    
    try:
        # تحويل اسم المحتوى في Stremio إلى كلمة بحث
        query = id.replace("qeseh-", "").replace("-", " ")
        search_url = f"{DOMAIN}/?s={query}"
        
        # البحث في موقع قصة
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # استخراج أول نتيجة بحث
            link_tag = soup.find("a", href=re.compile(r"qeseh\.com/"))
            if link_tag and link_tag.get("href"):
                page_url = link_tag["href"]
                
                # دخول صفحة الحلقة أو الفيلم
                page_res = requests.get(page_url, headers=HEADERS, timeout=10)
                if page_res.status_code == 200:
                    page_soup = BeautifulSoup(page_res.text, "html.parser")
                    
                    # البحث عن سيرفرات المشاهدة المضمنة (iframes)
                    iframes = page_soup.find_all("iframe")
                    for idx, iframe in enumerate(iframes):
                        src = iframe.get("src") or iframe.get("data-src", "")
                        if src:
                            if src.startswith("//"):
                                src = "https:" + src
                            
                            streams.append({
                                "name": "Qeseh",
                                "title": f"سيرفر قصة #{idx+1}",
                                "url": src
                            })
                            
    except Exception as e:
        print(f"Error fetching from Qeseh: {e}")

    # رابط احتياطي في حال كان سيرفر قصة يحتاج فك تشفير خاص
    if not streams:
        streams.append({
            "name": "Qeseh",
            "title": "سيرفر تجريبي / تعذر جلب الرابط المباشر تلقائياً",
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        })

    return {"streams": streams}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
