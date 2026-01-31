import os, base64, requests
from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # e.g. "@SooSimpleIIT"

client = OpenAI()

def make_quote():
    # SDKs expose resp.output_text for convenience :contentReference[oaicite:3]{index=3}
    resp = client.responses.create(
        model="gpt-5",
        input=(
            "Write ONE original motivational quote for students preparing for exams. "
            "Max 16 words. No emojis. No author name."
        ),
    )
    return resp.output_text.strip()

def make_image(quote: str) -> bytes:
    # GPT Image generation in the Images API :contentReference[oaicite:4]{index=4}
    img = client.images.generate(
        model="gpt-image-1.5",
        prompt=(
            "Create a premium motivational poster for students. "
            "Minimal, clean design, high contrast, readable typography. "
            f'Write this quote clearly as the main text: "{quote}". '
            "No watermark, no logos."
        ),
        n=1,
        size="1024x1024",
    )
    return base64.b64decode(img.data[0].b64_json)

def post_to_telegram(image_bytes: bytes, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("motivation.png", image_bytes)}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    r = requests.post(url, data=data, files=files, timeout=30)
    r.raise_for_status()

if __name__ == "__main__":
    quote = make_quote()
    caption = f"{quote}\n\n#motivation #study #jee #boards"
    image_bytes = make_image(quote)
    post_to_telegram(image_bytes, caption)
    print("Posted to Telegram.")


import os
import time
import requests
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # e.g. "@SooSimpleIIT"

# Longer timeout helps; OpenAI SDK supports a timeout parameter. :contentReference[oaicite:1]{index=1}
client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    timeout=90,        # increase from default
    max_retries=0      # we'll do controlled retries ourselves
)

def retry_call(fn, tries=6):
    delay = 2
    last_err = None
    for i in range(tries):
        try:
            return fn()
        except (APIConnectionError, APITimeoutError) as e:
            last_err = e
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise last_err

def make_quote():
    def _do():
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Write ONE original motivational quote for JEE/Boards students. "
                "Max 16 words. No emojis. No author name."
            ),
        )
        return resp.output_text.strip()
    return retry_call(_do, tries=6)

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()

if __name__ == "__main__":
    try:
        quote = make_quote()
    except Exception:
        # Fallback so GitHub Action doesn't fail if OpenAI connection fails
        quote = "Small daily effort beats rare intensity. Study today; thank yourself tomorrow."

    send_telegram_message(quote)
    print("Posted to Telegram.")
