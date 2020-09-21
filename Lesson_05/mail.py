from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time
import re
from datetime import datetime, timedelta
from pymongo import MongoClient
from pprint import pprint

MONTHS = {'января': '1',
          'февраля': '2',
          'марта': '3',
          'апреля': '4',
          'мая': '5',
          'июня': '6',
          'июля': '7',
          'августа': '8',
          'сентября': '9',
          'октября': '10',
          'ноября': '11',
          'декабря': '12'
          }


def scan_mailbox():
    """
    Сканирует почтовый ящик, собирая ссылки на письма
    :return: Список ссылок
    """
    links_set = set()
    while len(links_set) < letters_count:
        try:
            letters = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,
                                                '//a[@class="llc js-tooltip-direction_letter-bottom js-letter-list-item llc_normal"]')))
        except:
            print('Писем нет')
            break
        for item in letters:
            links_set.add(item.get_attribute('href'))
        action = ActionChains(driver)
        action.move_to_element(letters[-1])
        action.perform()
    return links_set


def read_letters(links):
    """
    Парсит письма, переходя по ссылкам на них.
    :param links: Список ссылок
    :return: Список словарей с письмами
    """
    letters = []
    for item in links:
        letter = {}
        driver.get(item)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'thread__subject'))
        )
        letter['subject'] = driver.find_element_by_class_name('thread__subject').text
        letter['from'] = driver.find_element_by_class_name('letter-contact').get_attribute('title')
        if driver.find_element_by_class_name('letter__date').text.startswith('Сегодня'):
            date = datetime.today()
            letter['date'] = date.strftime('%d/%m/%Y')
        elif driver.find_element_by_class_name('letter__date').text.startswith('Вчера'):
            date = datetime.today() - timedelta(days=1)
            letter['date'] = date.strftime('%d/%m/%Y')
        else:
            date = re.split(r'\W+', driver.find_element_by_class_name('letter__date').text)
            if len(date) == 5:
                letter['date'] = '/'.join((date[0], MONTHS[date[1]], date[2]))
            else:
                letter['date'] = '/'.join((date[0], MONTHS[date[1]], '2020'))
        letter['body'] = driver.find_element_by_class_name('letter-body__body-content').text
        letters.append(letter)
    return letters


def add_to_db(letters_list):
    """
    Добавляет письма в базу, если таких еще нет.
    :param letters_list: список писем
    :return:
    """
    counter = 0
    for letter in letters_list:
        if db['letters'].count_documents({'subject': letter['subject']}) == 0:
            db['letters'].insert_one(letter)
            counter += 1
    print(f'\nВ базу добавлено {counter} писем.')


client = MongoClient('127.0.0.1', 27017)
db = client['letters']

username, domain = input('Укажите почтовый ящик: ').split('@')
password = input('Укажите пароль: ')

driver = webdriver.Chrome(executable_path='/Users/artur/PycharmProjects/GU_Scraping_Course/Lesson_05/chromedriver')

driver.get('https://mail.ru/')
# Вводим имя пользователя
elem = driver.find_element_by_id('mailbox:login-input')
elem.send_keys(username)
# Указываем домен
mailbox = driver.find_element_by_id('mailbox:domain')
select = Select(mailbox)
select.select_by_visible_text('@' + domain)
elem.send_keys(Keys.ENTER)
# Вводим пароль
time.sleep(2)
elem = driver.find_element_by_id('mailbox:password-input')
elem.send_keys(password)
elem.send_keys(Keys.ENTER)
# Пауза чтобы прогрузилось приложение
time.sleep(20)
# Выделяем все письма
button = driver.find_element_by_class_name('button2__wrapper')
button.click()
# Считываем количество
letters_count = int(driver.find_element_by_class_name('button2__txt').text)
# Снимаем выделение
button.click()

# Собираем письма в базу
add_to_db(read_letters(scan_mailbox()))

driver.close()
