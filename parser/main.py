from fastapi import FastAPI
from pydantic import BaseModel

from brawser import parse

app = FastAPI()

class ProductURL(BaseModel):
    url: str


@app.post("/parse_product")
def parse_product(product: ProductURL):
    res = main(product.url)

    return {"success": True, "data": res}


def main(url: str) -> dict:
    res = parse(url)
    # url = "https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109825"
    # url = "https://uzum.uz/uz/product/erkaklar-tapochkasi-ekocharmdan-toq-yashil---275-1706132?skuId=5833754"

    return res

if __name__ == "__main__":
    print(main(url="https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187"))