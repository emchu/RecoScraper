import time
import psycopg2
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re

CHROMEDRIVER_PATH = "C:/Users/Aleksandra/PycharmProjects/RecoScraper/venv/Scripts/chromedriver.exe"


def make_soup(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def soup2(url):
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, 0, options=options)
    try:
        driver.get(url)
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource)
        return soup
    except ConnectionResetError as e:
        time.sleep(250)
        driver.get(url)
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource)
        return soup


def extract_sex():
    url = "https://www.housebrand.com/pl/pl/"
    soup = make_soup(url)
    ul_her = soup.find("ul", {"class": "category-tree-wrapper menuOna"}).find("li",
                                                                              {"class": "category-tree"}).find_all("a",
                                                                                                                   href=True)
    ul_him = soup.find("ul", {"class": "category-tree-wrapper menuOn"}).find("li", {"class": "category-tree"}).find_all(
        "a", href=True)

    extract_category(ul_her, "ona")
    extract_category(ul_him, "on")

    links_category_her = []
    for href in ul_her:
        if href.text:
            links_category_her.append(href['href'])
    links_category_him = []
    for href in ul_him:
        if href.text:
            links_category_him.append(href['href'])


def extract_category(ul, sex):
    for i in ul:
        category_url = i['href']
        category_name = i.string
        if category_name is not None:
            extract_products(category_url, sex, category_name)
            # insert_category(category_name)


def extract_products(category_url, sex, category_name):
    soup = make_soup(str(category_url))
    for i in soup.find_all("article"):
        product_url = i.find("a").get("href")
        # print(product_url)
        extract_product(product_url, sex, category_name)


def extract_product(product_url, sex, category_name):
    soup_original = make_soup(product_url)
    soup = soup2(product_url)

    title = soup.find("h1", {"class": "product-name"}).string
    # print(title)

    images = []
    desc = []

    div = soup.find_all("div", class_="swipe gallery-swipe")
    for i in div:
        for j in i.find_all("img"):
            images.append(str(j.get("src")))
            images = [x for x in images if "data" not in x]
            # print(images)

    images = list(dict.fromkeys(images))
    # print(images)

    for k in soup.find_all("section", {"class": "grid-price-wrapper"}):
        price = re.findall("\d+\.\d+", k.text.replace(",", "."))
        id_price = insert_price(price[0])

    for l in soup.find_all("section", class_="product-description"):
        for m in l.find_all("div"):
            desc.append(m.text)
            for n in m.find_all("li"):
                desc.append("- " + n.text)
            for n in m.find_all("p"):
                desc.append(n.text)

    description = "\n".join(desc)

    id_category = find_category(category_name)
    id_product = insert_product(title, sex, description, product_url, 6, id_price, id_category)
    for o in images:
        insert_picture(o, id_product)
    print(title)


conn = psycopg2.connect(host="localhost", port="5432", user="postgres", database="postgres", password="postgres")


def insert_price(price):
    sql = """INSERT INTO price(price)
             VALUES(%s) 
             RETURNING id_price;"""
    id_price = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (price,))
        id_price = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return id_price


def insert_picture(img, id_product):
    sql = """INSERT INTO picture(link, id_product)
             VALUES(%s, %s);"""
    try:
        cur = conn.cursor()
        cur.execute(sql, (img, id_product,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)


def insert_category(category):
    sql = """INSERT INTO category(name)
             VALUES(%s) 
             ON CONFLICT (name) DO NOTHING
             RETURNING id_category;"""
    id_category = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (category,))
        id_category = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return id_category


def find_category(category):
    sql = """SELECT id_category FROM category WHERE name = %s;"""
    id_category = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (category,))
        id_category = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return id_category


def insert_product(product, sex, desc, product_url, id_store, id_price, id_category):
    sql = """INSERT INTO product(name, sex, descr, link, id_store, id_price, id_category)
             VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING id_product;"""
    cur = conn.cursor()
    cur.execute(sql, (product, sex, desc, product_url, id_store, id_price, id_category,))
    id_product = cur.fetchone()[0]
    conn.commit()
    cur.close()
    # except (Exception, psycopg2.DatabaseError) as error:
    #     print(error)

    return id_product


def main():
    extract_sex()
    # category_url = "https://wearmedicine.com/k/on/odziez/t-shirty-i-polo"


#     # extract_products(category_url)
#     product_url = "https://wearmedicine.com/p/medicine-t-shirt-meski-z-nadrukiem-music-wall-szary-16784"
#     extract_product(product_url, "on", "T-shirty i polo")


if __name__ == "__main__":
    main()
