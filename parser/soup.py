import re
from pprint import pprint as pp
from bs4 import BeautifulSoup

from helpers import extract_num
from brawser import get_info_by_size

def parse_info(content: str, url: str) -> dict:
    print("started parsing data from request...")
    data = {}
    soup = BeautifulSoup(content, "html.parser")

    price = soup.find(class_="sell-price").find("span", class_="HeadlineMBold")
    discount = soup.find("div", class_="badge").find("span", class_="BodyMRegular")

    banner = soup.find_all("div", class_="banner")
    for i in range(0, len(banner)):
        texts = banner[i].find("div", class_="text-wrapper").find("span", {"data-test-id": "text__product-banner"})
        result = extract_num(texts.text.strip())

        if i > 0:
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

    seller = (soup
              .find("div", class_="seller")
              .find("div", class_="info")
              )
    seller_title = seller.find("div", class_="info-container").find("h3").text.strip()
    seller_image = seller.find("img").attrs["src"]
    seller_rating = seller.find("div", class_="rating").find("span", {"data-test-id":"text__shop-rating-value"}).text.strip()

    data["title"] = soup.h1.text.strip()
    data["rating"] = rating.text.strip()[:3]
    data["images"] = img_links
    data["seller"] = {
        "title": seller_title,
        "img": seller_image,
        "rating": seller_rating
    }
    data["price"] = re.sub(r'\s+','', price.text)
    data["discount"] = discount.text.strip()

    print("started playwright to parse data by product size")
    data["products"] = get_info_by_size(url)

    return data

