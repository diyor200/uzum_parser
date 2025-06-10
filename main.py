import requests
from soup import parse_info


def main():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # url = "https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109825"
    url = "https://uzum.uz/uz/product/erkaklar-tapochkasi-ekocharmdan-toq-yashil---275-1706132?skuId=5833754"

    print("sending request...")
    response = requests.get(url, headers=headers)
    res = parse_info(response.text)
    print(res)

if __name__ == "__main__":
    main()
