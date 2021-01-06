import psycopg2
import requests
from bs4 import BeautifulSoup
import re


def make_soup(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def extract_sex():
    url = "https://wearmedicine.com"
    soup = make_soup(url)
    ul_her = soup.find("a", href="/k/ona/odziez").next_sibling.next_sibling
    ul_him = soup.find("a", href="/k/on/odziez").next_sibling.next_sibling
    extract_category(ul_her, "ona")
    extract_category(ul_him, "on")


def extract_category(ul, sex):
    for i in ul.find_all("a"):
        category_url = "https://wearmedicine.com" + i.get("href")
        category_name = str(i.find("span")).replace("<span>", "").replace("</span>", "")
        # category_name = str(i.string).lstrip('\n')
        if category_url != "https://wearmedicine.com" and category_name is not None:
            extract_products(category_url, sex, category_name)
            # insert_category(category_name)


def extract_products(category_url, sex, category_name):
    soup = make_soup(category_url)
    for i in soup.find_all("div", class_="product-item__thumb"):
        product = i.find("a").get("href").strip("/p")
        product_url = "https://wearmedicine.com/p/" + product
        extract_product(product_url, sex, category_name)


def extract_product(product_url, sex, category_name):
    soup = make_soup(product_url)
    title = str(soup.title.string)
    images = []
    desc = []

    div = soup.find_all("div", class_="product__gallery-main")
    for i in div:
        for j in i.find_all("img"):
            images.append(str(j.get("src")))
            # images.append(str(j.get("src")))

    images = list(dict.fromkeys(images))

    for k in soup.find_all("p", class_="product__price"):
        price = re.findall("\d+\.\d+", k.text.replace(",", "."))
        id_price = insert_price(price[0])

    for l in soup.find_all("div", class_="product__info"):
        for m in l.find_all("div", class_="row"):
            for n in m.find_all("p"):
                desc.append(n.text)
            for n in m.find_all("li"):
                desc.append(n.text)

    description = "\n".join(desc)

    id_category = find_category(category_name)
    id_product = insert_product(title, sex, description, product_url, 5, id_price, id_category)
    for o in images:
        insert_picture(o, id_product)


conn = psycopg2.connect(host="localhost", port="5432", user="postgres", database="postgres",  password="postgres")


def insert_price(price):
    sql = """INSERT INTO price(price)
             VALUES(%s) RETURNING id_price;"""
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
             VALUES(%s) RETURNING id_category;"""
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


def insert_product(product, sex, desc, link, id_store, id_price, id_category):
    sql = """INSERT INTO product(name, sex, descr, link, id_store, id_price, id_category)
             VALUES(%s, %s, %s, %s, %s, %s, %s) RETURNING id_product;"""
    cur = conn.cursor()
    cur.execute(sql, (product, sex, desc, link, id_store, id_price, id_category,))
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