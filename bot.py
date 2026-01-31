import os
import time
import requests
from openai import OpenAI
from openai import APIConnectionError, APITimeoutError

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # e.g. "@SooSimpleIIT"

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

def make_quote():
    def _do():
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input="Write ONE original motivational quote for exam students. Max 16 words. No emojis. No author."
        )
        return resp.output_text.strip()
    return retry_call(_do)

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()

if __name__ == "__main__":
    try:
        quote = make_quote()
    except Exception as e:
        print("OpenAI failed, using fallback:", repr(e))
        quote = "Small daily effort beats rare intensity. Study today; thank yourself tomorrow."

    send_telegram_message(quote)
    print("Posted to Telegram.")
