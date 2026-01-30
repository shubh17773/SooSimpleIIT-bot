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
