import os
import time
import random
import requests
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    timeout=120,
    max_retries=0
)

def retry_call(fn, tries=10):
    delay = 2
    last_err = None
    for _ in range(tries):
        try:
            return fn()
        except (APIConnectionError, APITimeoutError) as e:
            last_err = e
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise last_err

def make_quote():
    themes = ["discipline", "focus", "revision", "confidence", "consistency", "calmness"]
    theme = random.choice(themes)

    def _do():
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                f"Write ONE original motivational quote for exam students. "
                f"Theme: {theme}. Max 18 words. No emojis. No author."
            ),
        )
        return resp.output_text.strip()

    return retry_call(_do, tries=10)

def download_random_nature_image():
    # Multiple sources + retries so it never fails
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
    fallback_quotes = [
        "Consistency beats intensity. One focused hour daily changes everything.",
        "Today’s revision is tomorrow’s confidence.",
        "Discipline is doing it even when motivation is missing.",
        "Small steps daily create massive results. Start now.",
        "Focus on the next question, not the whole syllabus.",
        "No zero days. Even 20 minutes counts.",
        "Calm mind, clear plan, ruthless execution.",
        "Win the morning: study first, excuses later.",
        "Your future score depends on today’s effort.",
        "Practice today so exam day feels familiar.",
    ]

    try:
        quote = make_quote()
        print("OpenAI quote:", quote)
    except Exception as e:
        print("OpenAI error:", repr(e))
        quote = random.choice(fallback_quotes)
        print("Fallback quote:", quote)

    try:
        img = download_random_nature_image()
    except Exception as e:
        print("Image download error:", repr(e))
        # If image download fails, still post text only
        img = None

    caption = f"{quote}\n\n#motivation #study #jee #boards"

    if img:
        send_telegram_photo(img, caption)
        print("Posted photo + quote.")
    else:
        # fallback to text post
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": caption}, timeout=30)
        if r.status_code != 200:
            print("Telegram status:", r.status_code)
            print("Telegram response:", r.text)
        r.raise_for_status()
        print("Posted text only.")
