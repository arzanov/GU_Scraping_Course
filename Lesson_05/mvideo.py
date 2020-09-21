from selenium import webdriver
import json
import time
from pymongo import MongoClient


def add_to_db(my_list):
    """
    Добавляет товары в базу, если таких еще нет.
    :param my_list: список товаров
    :return:
    """
    counter = 0
    for product in my_list:
        if db['sale_hits'].count_documents({'productId': product['productId']}) == 0:
            db['sale_hits'].insert_one(product)
            counter += 1
    print(f'\nВ базу добавлено {counter} товаров.')


client = MongoClient('127.0.0.1', 27017)
db = client['mvideo']

driver = webdriver.Chrome(executable_path='/Users/artur/PycharmProjects/GU_Scraping_Course/Lesson_05/chromedriver')

driver.get('https://www.mvideo.ru/')

# Ожидаем прогрузки страницы
time.sleep(20)

# Загружаем список блоков
page_blocks = driver.find_elements_by_xpath("//div[contains(@class, 'h2')]")

# Вычисляем номер блока "Хиты продаж"
hits_block = 0
for item in page_blocks:
    if item.text == 'Хиты продаж':
        break
    hits_block += 1

# Считаем количество страниц в карусели
pages = driver.find_elements_by_xpath(f"(//div[contains(@class, 'sel-hits-block')])[{hits_block}]"
                                      f"//div[@class='carousel-paging']//a")
# Прокликиваем карусель
for item in pages:
    button = driver.find_element_by_xpath(f"(//div[contains(@class, 'sel-hits-block')])[{hits_block}]"
                                           f"//a[contains(@class,'next-btn')]")
    button.click()
    time.sleep(3)

# Собираем информацию о продуктах в блоке в список
products = driver.find_elements_by_xpath(f"(//div[contains(@class, 'sel-hits-block')])[{hits_block}]"
                                         f"//ul/li//div[@class='c-product-tile-picture__holder']/a")
products_list = []
for item in products:
    product = item.get_attribute("data-product-info")
    product = product.replace('\t', '').replace('\n', '')
    product = json.loads(product)
    products_list.append(product)

# Добавляем продукты в базу
add_to_db(products_list)

driver.close()
