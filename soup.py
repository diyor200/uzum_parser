import re
from pprint import pprint as pp
from bs4 import BeautifulSoup

data = {}

with open("index.html", "r") as f:
    soup = BeautifulSoup(f, "html.parser")

price = soup.find(class_="sell-price").find("span", class_="HeadlineMBold")
available_amount = (soup
                    .find("div", class_="banner")
                    .find("div", class_="text-wrapper")
                    .find("span", {"data-test-id": "text__product-banner"})
                    )
aa =  re.sub(r'\s+','', available_amount.text)
aa_res = ""
for i in aa:
    if i.isdigit():
        aa_res = aa_res + i


discount = soup.find("div", class_="badge").find("span", class_="BodyMRegular")
size = (soup
        .find("div", class_="content-right")
        .find("div", class_="sku-selectors")
        .find("div", class_="characteristic-title-and-value")
        .find("span", {"data-test-id": "text__selected-sku-value"})
        )

banner = soup.find_all("div", class_="banner")
for i in range(0, len(banner)):
    texts = banner[i].find("div", class_="text-wrapper").find("span", {"data-test-id": "text__product-banner"})
    result = ""
    for t in texts.text.strip():
        if t.isdigit():
            result += t

    if i == 0:
        data["available_amount"] = result
    else:
        data["sold_count"] = result

rating = (soup
          .find("div", class_="stats")
          .find("div", class_="rating")
          .find("a", class_="rating-value")
          )

images = (soup
          .find("div", class_="content-wrapper")
          .find("div", class_="content-left")
          .find("div", class_="swiper-slider-wrapper")
          .find("swiper-container", class_="u-swiper-pdp")
          .find_all("swiper-slide")
          )
img_links = []
for image in images:
    link = image.find("img").attrs["src"]
    img_links.append(link)

desc = soup.find("div", id="description-tabs-wrapper").find("span", {"data-test-id": "block__tab-content"})
print(desc.text.strip())

data["title"] = soup.h1.text.strip()
data["price"] = re.sub(r'\s+','', price.text)
data["available_amount"] =  aa_res
data["discount"] = discount.text.strip()
data["size"] = size.text.strip()
data["rating"] = rating.text.strip()[:3]
data["images"] = img_links

pp(data)
