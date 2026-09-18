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
    "version": "2.1.0",
    "name": "Tom & Jerry Classic (Complete)",
    "description": "جميع الحلقات الـ 161 مع الصور وأسماء الحلقات بوضوح - متوافق مع Nuvio و Stremio",
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

# صور الكرتون الرئيسية (البوستر، الخلفية، الشعار)
SERIES_POSTER = "https://upload.wikimedia.org/wikipedia/en/5/5f/Tom_and_Jerry_title_card.png"
SERIES_BACKGROUND = "https://images.wallpapersden.com/image/download/tom-and-jerry-art_bGdpZm2UmZqaraWkpJRmZmdlrWZnZWU.jpg"
SERIES_LOGO = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Tom_and_Jerry_logo.svg/1200px-Tom_and_Jerry_logo.svg.png"

ARCHIVE_ITEM = "tom_and_jerry_1940_1958"

# أسماء جميع الحلقات الـ 161 الكلاسيكية مرتبة
EPISODE_TITLES = [
    "Puss Gets the Boot", "The Midnight Snack", "The Night Before Christmas", "Fraidy Cat",
    "Dog Trouble", "Puss n' Toots", "The Bowling Alley-Cat", "Fine Feathered Friend",
    "Sufferin' Cats!", "Lonesome Mouse", "The Yankee Doodle Mouse", "Baby Puss",
    "The Zoot Cat", "The Million Dollar Cat", "The Bodyguard", "Puttin' on the Dog",
    "Mouse Trouble", "The Mouse Comes to Dinner", "Mouse in Manhattan", "Tee for Two",
    "Flirty Birdy", "Quiet Please!", "Springtime for Thomas", "The Milky Waif",
    "Trap Happy", "Solid Serenade", "Cat Fishin'", "Part Time Pal",
    "The Cat Concert", "Dr. Jekyll and Mr. Mouse", "Salt Water Tabby", "A Mouse in the House",
    "The Invisible Mouse", "Kitty Foiled", "The Truce Hurts", "Old Rockin' Chair Tom",
    "Professor Tom", "Mouse Cleaning", "Polka-Dot Puss", "The Little Orphan",
    "Hatch Up Your Troubles", "Heavenly Puss", "The Cat and the Mermouse", "Love That Puppy",
    "Jerry's Diary", "Tennis Chumps", "Little Quacker", "Saturday Evening Puss",
    "Texas Tom", "Jerry and the Lion", "Safety Second", "Tom and Cherie",
    "Cue Ball Cat", "Casanova Cat", "Jerry and the Goldfish", "Jerry's Cousin",
    "Sleepy-Time Tom", "His Mouse Friday", "Slicked-up Pup", "Nit-witty Kitty",
    "Cat Napping", "The Flying Cat", "The Duck Doctor", "The Two Mouseketeers",
    "Smitten Kitten", "Triple Trouble", "Little Runaway", "Fit to Be Tied",
    "Push-Button Kitty", "Cruise Cat", "The Dog House", "Missing Mouse",
    "Jerry and Jumbo", "Johann Mouse", "That's My Pup!", "Just Ducky",
    "Two Little Indians", "Life with Tom", "Puppy Tale", "Posse Cat",
    "Hic-cup Pup", "Little School Mouse", "Baby Butch", "Mice Follies",
    "Neapolitan Mouse", "Downheart Duckling", "Pet Snack", "Touche, Pussy Cat!",
    "Southbound Duckling", "Pup on a Leash", "Designing Mice", "Puppy's Birthday",
    "Smarty Cat", "Pecos Pest", "That's My Mommy", "The Flying Sorceress",
    "The Egg and Jerry", "Busy Buddies", "Muscle Beach Tom", "Down Beat Bear",
    "Blue Cat Blues", "Barbecue Brawl", "Tops with Pops", "Timid Tabby",
    "Feedin' the Kiddie", "Mucho Mouse", "Tom's Photo Finish", "Happy Go Ducky",
    "Royal Cat Nap", "The Vanishing Duck", "Robin Hoodwinked", "Tot Watchers",
    "Switchin' Kitten", "Down and Outing", "High Steaks", "Mouse Into Space",
    "Landing Stripling", "Calypso Cat", "Dicky Moe", "The Tom and Jerry Cartoon Kit",
    "Tall in the Trap", "Sorry Safari", "Buddies Thicker Than Water", "Carmen Get It!",
    "Pent-House Mouse", "The Cat Above and the Mouse Below", "Is There a Doctor in the Mouse?", "Much Ado About Mousing",
    "Snowbody Loves Me", "The Unshrinkable Jerry Mouse", "Ah, Sweet Mouse-Story of Life", "Tom-ic Energy",
    "Bad Day at Cat Rock", "The Brothers Carry-Mouse-Off", "Haunted Mouse", "I'm Just Wild About Jerry",
    "Of Feline Bondage", "Year of the Mouse", "The Cat's Me-Ouch!", "Duel Personality",
    "Jerry, Jerry, Quite Contrary", "Jerry-Go-Round", "Love Me, Love My Mouse", "Puss 'n' Boats",
    "Filet Meow", "Matinee Mouse", "The Oicker-Upper", "Advance and Be Mechanized",
    "Guided Mouse-ille", "Rock 'n' Rodent", "Cannery Rodent", "The Mouse from H.U.N.G.E.R.",
    "Surf-Bored Cat", "Shutter Bugged Cat", "Advance and Be Mechanized", "Purr-Chance to Dream"
]

EPISODES_CACHE = {}

def get_archive_episodes():
    global EPISODES_CACHE
    if EPISODES_CACHE:
        return EPISODES_CACHE
    try:
        url = f"https://archive.org/metadata/{ARCHIVE_ITEM}"
        res = requests.get(url, headers=HEADERS, timeout=5)
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
        print(f"Archive metadata fetch bypassed: {e}")
        
    return EPISODES_CACHE

@app.options("/{full_path:path}")
def options_handler(full_path: str):
    return Response(status_code=200, headers=CORS_HEADERS)

@app.get("/")
def root():
    return Response(content=json.dumps({"status": "Active", "total_episodes": 161}), headers=CORS_HEADERS)

@app.get("/manifest.json")
def get_manifest():
    return Response(content=json.dumps(MANIFEST, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/catalog/series/tj_catalog.json")
def get_catalog():
    meta = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": SERIES_POSTER,
        "background": SERIES_BACKGROUND,
        "logo": SERIES_LOGO,
        "description": "جميع الحلقات الأصلية الكلاسيكية الـ 161 كاملة مع الصور وأسماء الحلقات."
    }
    return Response(content=json.dumps({"metas": [meta]}, ensure_ascii=False), headers=CORS_HEADERS)

@app.get("/meta/series/{id}.json")
def get_meta(id: str):
    episodes_data = get_archive_episodes()
    videos = []
    
    for i in range(1, 162):
        if i <= len(EPISODE_TITLES):
            title_str = f"الحلقة {i}: {EPISODE_TITLES[i-1]}"
        elif i in episodes_data:
            title_str = f"الحلقة {i}: {episodes_data[i]['title']}"
        else:
            title_str = f"الحلقة {i}: Tom & Jerry Classic"

        # صورة مصغرة خاصة بكل حلقة من الأرشيف
        thumb_url = f"https://ia800200.us.archive.org/zipview.php?zip=/30/items/tom_and_jerry_1940_1958/tom_and_jerry_1940_1958_thumbs.zip&file={i:03d}.jpg"

        videos.append({
            "id": f"tj_classic_1940:1:{i}",
            "title": title_str,
            "season": 1,
            "episode": i,
            "thumbnail": thumb_url,
            "overview": f"الحلقة الكلاسيكية رقم {i} من سلسلة توم وجيري (1940-1958)."
        })

    meta_data = {
        "id": "tj_classic_1940",
        "type": "series",
        "name": "Tom and Jerry: The Classic Collection",
        "poster": SERIES_POSTER,
        "background": SERIES_BACKGROUND,
        "logo": SERIES_LOGO,
        "description": "المجموعة الكلاسيكية الكاملة (161 حلقة مع الصور والأسماء جاهزة للتشغيل المباشر).",
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
            
            ep_name = EPISODE_TITLES[ep_num - 1] if 1 <= ep_num <= len(EPISODE_TITLES) else f"الحلقة {ep_num}"
            
            streams.append({
                "name": "Nuvio / Stremio Direct",
                "title": f"تشغيل مباشر - {ep_name}",
                "url": play_url
            })
        except Exception as e:
            print(f"Stream error: {e}")

    return Response(content=json.dumps({"streams": streams}, ensure_ascii=False), headers=CORS_HEADERS)
