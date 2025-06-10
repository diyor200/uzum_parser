def extract_num(text: str) -> str:
    result = ""
    for t in text:
        if t.isdigit():
            result += t

    return result