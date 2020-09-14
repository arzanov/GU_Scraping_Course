from pprint import pprint
from lxml import html
import requests
import re
from datetime import datetime, timedelta
from pymongo import MongoClient

header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
client = MongoClient('127.0.0.1', 27017)
db = client['news']


def mail_news_page_parse(link):
    """
    Сканирует страницу с новостью
    :param link: URL страницы
    :return: новость в виде словаря
    """
    new = {}
    response = requests.get(link, headers=header)
    dom_child = html.fromstring(response.text)
    source = dom_child.xpath("//a[@class='link color_gray breadcrumbs__link']//text()")[0]
    date = dom_child.xpath("//span[@class='note__text breadcrumbs__text js-ago']/@datetime")[0]
    subject = dom_child.xpath("//h1[@class='hdr__inner']/text()")[0]
    new['source'] = source
    new['subject'] = subject
    new['link'] = link
    new['date'] = '/'.join(date[:10].split('-')[::-1])
    return new

def mail_scan():
    """
    Собирает новости с сайта news.mail.ru
    :return:
    """
    main_link = 'https://news.mail.ru'
    response = requests.get(main_link, headers=header)
    dom_parent = html.fromstring(response.text)

    print('\nСканируем mail.ru')

    news_block = dom_parent.xpath("//div[@name='clb20268335']")
    news_list = []
    # Главная новость
    new_link = main_link + dom_parent.xpath("//a[@class='photo photo_full photo_scale js-topnews__item']/@href")[0]
    news_list.append(mail_news_page_parse(new_link))

    # Новости дня
    day_news = dom_parent.xpath("//td[@class='daynews__items']//@href")
    for item in day_news:
        if item.startswith('http'):
            new_link = item
        else:
            new_link = main_link + item
        news_list.append(mail_news_page_parse(new_link))

    # Прочие новости
    other_news = dom_parent.xpath("//ul[@class='list list_type_square list_half js-module']/li[@class='list__item']/a/@href")
    for item in other_news:
        if item.startswith('http'):
            new_link = item
        else:
            new_link = main_link + item
        news_list.append(mail_news_page_parse(new_link))

    print(f'\nСобрано {len(news_list)} новостей')
    return news_list


def lenta_scan():
    """
    Собирает новости с сайта lenta.ru
    :return:
    """
    main_link = 'https://lenta.ru'
    response = requests.get(main_link, headers=header)
    dom = html.fromstring(response.text)
    print('\nСканируем lenta.ru')
    news_list = []
    news_block = dom.xpath("//section[@class='row b-top7-for-main js-top-seven']//div[contains(@class, 'item')]")
    for item in news_block:
        news = {}
        subject = item.xpath(".//a/text()")[0]
        link = item.xpath(".//a/@href")[0]
        if not link.startswith('http'):
            date = '/'.join(re.findall(r'\d\d\d\d\D\d\d\D\d\d', link)[0].split('/')[::-1])
            news['source'] = 'lenta.ru'
            news['link'] = main_link + link
        else:
            date = re.findall(r'\d\d\D\d\d\D\d\d\d\d', link)[0]
            news['source'] = 'moslenta.ru'
            news['link'] = link
        news['subject'] = subject

        news['date'] = date
        news_list.append(news)

    print(f'\nСобрано {len(news_list)} новостей')

    return news_list


def yandex_scan():
    """
    Собирает новости с сайта yandex.ru
    :return:
    """
    main_link = 'https://yandex.ru/news'
    response = requests.get(main_link, headers=header)
    dom = html.fromstring(response.text)

    print('\nСканируем yandex.ru')
    news_list = []
    news_block = dom.xpath("//div[@class='mg-grid__row mg-grid__row_gap_8 news-top-stories news-app__top']/div")
    for item in news_block:
        news = {}
        subject = item.xpath(".//h2[@class='news-card__title']/text()")[0]
        link = item.xpath(".//a[@class='news-card__link']/@href")[0]
        source = item.xpath(".//span[@class='mg-card-source__source']/a/text()")[0]
        date = datetime.today()
        if item.xpath(".//span[@class='mg-card-source__time']/text()")[0].startswith('вчера'):
            date -= timedelta(days=1)
        date = date.strftime('%d/%m/%Y')
        news['subject'] = subject
        news['link'] = link
        news['date'] = date
        news['source'] = source
        news_list.append(news)

    print(f'\nСобрано {len(news_list)} новостей')
    
    return news_list


def add_to_db(source, news_list):
    """
    Добавляет новости в базу, если таких еще нет.
    :param source: сканируемый ресурс, используется в качестве имени коллекции
    :param news_list: список новостей
    :return:
    """
    counter = 0
    for news in news_list:
        if db[source].count_documents({'subject': news['subject']}) == 0:
            db[source].insert_one(news)
            counter += 1
    print(f'\nВ базу добавлено {counter} новостей.')


add_to_db('yandex', yandex_scan())
add_to_db('mail', mail_scan())
add_to_db('lenta', lenta_scan())
