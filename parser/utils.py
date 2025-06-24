import re

from typing import Optional
from urllib.parse import urlparse


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
