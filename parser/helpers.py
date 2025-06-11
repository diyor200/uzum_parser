from urllib.parse import urlparse, urlunparse

def remove_query(url: str) -> str:
    parsed = urlparse(url)
    cleaned = parsed._replace(query="")
    return str(urlunparse(cleaned))

def extract_num(text: str) -> str:
    result = ""
    for t in text:
        if t.isdigit():
            result += t

    return result