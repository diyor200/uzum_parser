import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0"
}
url = "https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109825"
response = requests.get(url, headers=headers)


soup = BeautifulSoup(response.text, 'html.parser')
with open("index.html", "w") as file:
    file.write(soup.prettify())