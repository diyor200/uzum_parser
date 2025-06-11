import requests
from fastapi import FastAPI
from pydantic import BaseModel

from parser.helpers import remove_query
from soup import parse_info

app = FastAPI()

class ProductURL(BaseModel):
    url: str


@app.post("/parse_product")
def parse_product(product: ProductURL):
    res = main(product.url)

    return {"success": True, "data": res}


def main(url: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    # url = "https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109825"
    # url = "https://uzum.uz/uz/product/erkaklar-tapochkasi-ekocharmdan-toq-yashil---275-1706132?skuId=5833754"

    print("sending request...")
    response = requests.get(url, headers=headers)
    res = parse_info(response.text, remove_query(url))

    return res

if __name__ == "__main__":
    print(main(url="https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187"))