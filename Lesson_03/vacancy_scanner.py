from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
from pymongo import MongoClient

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
client = MongoClient('127.0.0.1', 27017)
db = client['vacancies']

def calc_salary(vacancy, tag, param, value):
    """
    Возвращает минимальную и максимальную границы зарплаты по вакансии
    :param vacancy:
    :param tag:
    :param param:
    :param value:
    :return:
    """
    try:
        vacancy_salary = vacancy.find(tag, {param: value}).text
        salary = [el.replace('\xa0', '') for el in re.findall(r'\d+\s\d+', vacancy_salary)]
        currency = vacancy_salary.split()[-1]
        if vacancy_salary != 'По договорённости':
            if vacancy_salary.startswith('от'):
                salary_min = int(salary[0])
                salary_max = 'None'
            elif vacancy_salary.startswith('до'):
                salary_min = 'None'
                salary_max = int(salary[0])
            elif len(salary) == 2:
                salary_min = int(salary[0])
                salary_max = int(salary[1])
            else:
                salary_min = salary_max = int(salary[0])
        else:
            salary_min = 'None'
            salary_max = 'None'
    except:
        salary_min = 'None'
        salary_max = 'None'
        currency = 'None'
    return salary_min, salary_max, currency


def scan_hh(user_request):
    """
    Возвращает список с вакансиями hh.ru
    :param user_request: строка пользовательского запроса
    :return: список вакансий
    """
    page = 0
    vacancies = []
    while True:
        print(f'Сканируем hh.ru - стр. {page}', end='')
        main_link = 'https://hh.ru'
        params = {'L_is_autosearch': 'false',
                  'area': '1',
                  'clusters': 'true',
                  'enable_snippets': 'true',
                  'search_field': 'name',
                  'text': user_request,
                  'page': str(page)}

        html = requests.get(main_link + '/search/vacancy', params=params, headers=HEADERS)

        soup = bs(html.text, 'html.parser')

        vacancies_block = soup.find('div', {'class': 'vacancy-serp'})
        vacancies_list = vacancies_block.find_all('div', {'class': 'vacancy-serp-item'})

        for vacancy in vacancies_list:
            vacancy_data = {}
            vacancy_name = vacancy.find('a').text      # Наименование вакансии
            vacancy_link = vacancy.find('a')['href']   # Ссылка на вакансию
            # Зарплата
            salary_min, salary_max, currency = calc_salary(vacancy, 'span', 'data-qa', 'vacancy-serp__vacancy-compensation')

            # Работодатель
            try:
                vacancy_employer = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).text.strip()
            except:
                vacancy_employer = ''
            # Запихиваем значения в словарь
            vacancy_data['name'] = vacancy_name
            vacancy_data['link'] = vacancy_link
            vacancy_data['min_salary'] = salary_min
            vacancy_data['max_salary'] = salary_max
            vacancy_data['currency'] = currency
            vacancy_data['employer'] = vacancy_employer
            vacancy_data['source'] = 'hh.ru'
            # Добавляем в список вакансий
            vacancies.append(vacancy_data)
        if soup.find('a', {'data-qa': 'pager-next'}):
            page += 1
            print('', end='\r')
        else:
            break
    print(f'\nНайдено {len(vacancies)} вакансий.')
    return vacancies


def scan_superjob(user_request):
    """
        Возвращает список с вакансиями superjob.ru
        :param user_request: строка пользовательского запроса
        :return: список вакансий
    """
    vacancies = []
    page = 1
    while True:
        print(f'Сканируем superjob.ru - стр. {page}', end='')
        main_link = 'https://www.superjob.ru'
        params = {'keywords': user_request,
                  'geo[t][0]': '4',
                  'page': f'{page}'
                  }

        html = requests.get(main_link + '/vacancy/search/', params=params, headers=HEADERS)
        soup = bs(html.text, 'html.parser')
        try:
            vacancies_block = soup.find_all('div', {'class': '_3zucV undefined _3SGgo'})[2]
            vacancies_list = vacancies_block.find_all('div', {'class': '_3zucV _1fMKr undefined _3tcTB _3SGgo'})
            for vacancy in vacancies_list:
                vacancy_data = {}
                if vacancy.find('div', {'class': 'iJCa5 f-test-vacancy-item _1fma_ undefined _2nteL'}):
                    vacancy_name = vacancy.find('a').text                   # Наименование вакансии
                    vacancy_link = main_link + vacancy.find('a')['href']    # Ссылка на вакансию
                    # Зарплата
                    salary_min, salary_max, currency = calc_salary(vacancy, 'span', 'class',
                                                         '_1OuF_ _1qw9T f-test-text-company-item-salary')
                    # Работодатель
                    vacancy_employer = vacancy.find('span', {'class': '_3mfro _3Fsn4 f-test-text-vacancy-item-company-name _9fXTd _2JVkc _2VHxz _15msI'}).text
                    # Запихиваем значения в словарь
                    vacancy_data['name'] = vacancy_name
                    vacancy_data['link'] = vacancy_link
                    vacancy_data['min_salary'] = salary_min
                    vacancy_data['max_salary'] = salary_max
                    vacancy_data['currency'] = currency
                    vacancy_data['employer'] = vacancy_employer
                    vacancy_data['source'] = 'superjob.ru'
                    # Добавляем в список вакансий
                    vacancies.append(vacancy_data)
            if soup.find('a', {'class': 'icMQ_ _1_Cht _3ze9n f-test-button-dalshe f-test-link-Dalshe'}):
                page += 1
                print('', end='\r')
            else:
                break
        except:
            print('\nВакансий не найдено.')
            return
    print(f'\n Найдено {len(vacancies)} вакансий.')
    return vacancies


def scan_all(user_request):
    """
    Сканирует все сервисы сразу
    :param user_request: строка пользовательского запроса
    :return: список вакансий
    """
    vacancies = scan_hh(user_request)
    vacancies.extend(scan_superjob(user_request))
    print(f'\nИтого найдено {len(vacancies)} вакансий.')
    return vacancies


def to_csv(vacancies, filename):
    """
    Сохраняет вакансии в файл csv
    :param vacancies: список вакансий
    :param filename: имя файла
    :return:
    """
    try:
        pd.DataFrame(vacancies).to_csv(filename, index=False, encoding='utf-8')
        print(f'Результаты сохранены в файл {filename}')
    except:
        print('Что-то пошло не так...')


def to_db(vacancies):
    """
    Добавляет вакании в базу, если таких еще нет.
    :param vacancies:
    :return:
    """
    counter = 0
    for vacancy in vacancies:
        if len([elem for elem in db.vacancies.find({'link': vacancy['link']})]) == 0:
            db.vacancies.insert_one(vacancy)
            counter += 1
    print(f'\nВ базу добавлено {counter} вакансий.')

