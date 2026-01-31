import os
import time
import random
import requests
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # e.g. "@SooSimpleIIT"

# OpenAI client with bigger timeout; we handle retries ourselves
client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    timeout=90,
    max_retries=0
)

def retry_call(fn, tries=6):
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

def make_quote() -> str:
    # rotate themes so quotes feel different daily
    themes = [
        "discipline", "consistency", "focus", "revision", "confidence",
        "hard work", "smart work", "comeback", "exam day calm", "daily practice"
    ]
    theme = random.choice(themes)

    def _do():
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                f"Write ONE original motivational quote for students preparing for exams. "
                f"Theme: {theme}. "
                f"Max 18 words. No emojis. No author name. No hashtags."
            ),
        )
        return resp.output_text.strip()

    return retry_call(_do, tries=10)

def download_random_nature_image() -> bytes:
    """
    Try multiple HD image sources with retries.
    This prevents job failure if one provider is down (503 etc.).
    """
    cache_buster = int(time.time())
    sources = [
        # Unsplash Source (nice but sometimes 503)
        f"https://source.unsplash.com/1920x1080/?nature,landscape,mountains,forest&sig={cache_buster}",

        # Picsum (always up, random HD photo)
        f"https://picsum.photos/1920/1080?random={cache_buster}",

        # Another picsum endpoint
        f"https://picsum.photos/seed/{cache_buster}/1920/1080",
    ]

    last_err = None
    for url in sources:
        for attempt in range(3):  # retry each source 3 times
            try:
                r = requests.get(url, timeout=60, allow_redirects=True)
                r.raise_for_status()
                return r.content
            except Exception as e:
                last_err = e
                time.sleep(2 ** attempt)  # 1s,2s,4s
                continue

    raise last_err


def send_telegram_photo(image_bytes: bytes, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("motivation.jpg", image_bytes)}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]}  # Telegram caption limit
    r = requests.post(url, data=data, files=files, timeout=60)

    # If it fails, show Telegram's exact reason in GitHub logs
    if r.status_code != 200:
        print("Telegram status:", r.status_code)
        print("Telegram response:", r.text)

    r.raise_for_status()

if __name__ == "__main__":
    # Make quote (fallback if OpenAI fails)
    import random

try:
    quote = make_quote()
except Exception as e:
    print("OpenAI failed, using fallback:", repr(e))

    fallback_quotes = [
        "Win the morning: 45 minutes of deep study before the world wakes up.",
        "Discipline is choosing what you want most over what you want now.",
        "Consistency beats intensity. One solid hour daily changes everything.",
        "Don’t chase motivation—build a routine that works even without it.",
        "Today’s revision is tomorrow’s confidence.",
        "Small steps daily create massive results. Start now.",
        "Focus on the next question, not the whole syllabus.",
        "Your competition is your yesterday. Beat it by 1% today.",
        "No zero days. Even 20 minutes counts.",
        "Calm mind, clear plan, ruthless execution.",
    ]

    quote = random.choice(fallback_quotes)


    # Get a different HD nature image each run
    img = download_random_nature_image()

    caption = f"{quote}\n\n#motivation #study #jee #boards"
    send_telegram_photo(img, caption)

    print("Posted HD nature photo + new quote.")
