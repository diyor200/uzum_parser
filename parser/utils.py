import re

from typing import Optional
from urllib.parse import urlparse

import requests


def extract_num(text: str) -> Optional[int]:
    if isinstance(text, (int, float)):
        return int(text)
    if not isinstance(text, str):
        return None
    return int(re.sub(r"[^\d]", "", text)) or None

def to_safe_url(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.split("/")
    if "product" in parts:
        product_id = parts[-1].split("-")[-1]
        return f"https://uzum.uz/uz/product/{product_id}" + (f"?{parsed.query}" if parsed.query else "")
    return url


def send_to_telegram():
    bot_token = "7595418811:AAGd0EDnO-yQ7JnTPO3JBeWv_c96U_-2bZo"
    chat_ids = [5697570359, 1626359242]
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open("products.json", "rb") as file:
        response = requests.post(url, data={"chat_id":chat_ids}, files={"document": file})

    print(response.json())

    # send notification
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_ids[0],
        "text": "file has been sent!"
    }

    response = requests.post(url, data=payload)
    print(response.json())