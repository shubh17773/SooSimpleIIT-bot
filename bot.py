import os
import time
import random
import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def get_quote():
    """
    Fetch a random motivational quote from multiple public sources.
    No OpenAI needed.
    """
    # 1) ZenQuotes
    try:
        r = requests.get("https://zenquotes.io/api/random", timeout=20)
        r.raise_for_status()
        data = r.json()
        q = data[0]["q"]
        a = data[0].get("a", "")
        quote = f"{q} — {a}".strip(" —")
        return quote[:200]
    except Exception as e:
        print("ZenQuotes failed:", repr(e))

    # 2) Quotable
    try:
        r = requests.get("https://api.quotable.io/random?tags=motivational|inspirational", timeout=20)
        r.raise_for_status()
        data = r.json()
        q = data["content"]
        a = data.get("author", "")
        quote = f"{q} — {a}".strip(" —")
        return quote[:200]
    except Exception as e:
        print("Quotable failed:", repr(e))

    # 3) Final fallback list (always works)
    fallback_quotes = [
        "Consistency beats intensity. One focused hour daily changes everything.",
        "Today’s revision is tomorrow’s confidence.",
        "Small steps daily create massive results. Start now.",
        "Focus on the next question, not the whole syllabus.",
        "No zero days. Even 20 minutes counts.",
        "Calm mind, clear plan, ruthless execution.",
        "Discipline is doing it even when motivation is missing.",
        "Win the morning: study first, excuses later.",
        "Your future score depends on today’s effort.",
        "Practice today so exam day feels familiar."
    ]
    return random.choice(fallback_quotes)

def download_random_nature_image():
    cache_buster = int(time.time())
    sources = [
        f"https://source.unsplash.com/1920x1080/?nature,landscape,mountains,forest&sig={cache_buster}",
        f"https://picsum.photos/seed/{cache_buster}/1920/1080",
        f"https://picsum.photos/1920/1080?random={cache_buster}",
    ]

    last_err = None
    for url in sources:
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=60, allow_redirects=True)
                r.raise_for_status()
                return r.content
            except Exception as e:
                last_err = e
                time.sleep(2 ** attempt)
    raise last_err

def send_telegram_photo(image_bytes: bytes, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("motivation.jpg", image_bytes)}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]}
    r = requests.post(url, data=data, files=files, timeout=60)
    if r.status_code != 200:
        print("Telegram status:", r.status_code)
        print("Telegram response:", r.text)
    r.raise_for_status()

if __name__ == "__main__":
    quote = get_quote()
    print("Quote used:", quote)

    img = download_random_nature_image()
    caption = f"{quote}\n\n#motivation #study #jee #boards"
    send_telegram_photo(img, caption)

    print("Posted photo + quote.")
