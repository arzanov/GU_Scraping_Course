from pymongo import MongoClient
from pprint import pprint
import vacancy_scanner as vs

client = MongoClient('127.0.0.1', 27017)
db = client['vacancies']


def update_db():
    """
    Добавляет в базу данных вакансии по запросу.
    Если такая вакансия в базе уже существует, запись не добавляется.
    :return:
    """
    user_request = input('Укажите название вакансии: ')
    vacancies = vs.scan_all(user_request)
    vs.to_db(vacancies)


def find_in_db():
    """
    Печатает список вакансий по запросу мин зарплаты
    :return:
    """
    min_salary_request = int(input('Укажите нижнюю границу зарплаты: '))
    curr = input('Укажите валюту ("руб.", "USD", "EUR"): ')
    pass
    for vacancy in db.vacancies.find({'$or':
                                          [{'min_salary': {'$gte': min_salary_request}, 'currency': curr},
                                           {'max_salary': {'$gte': min_salary_request}, 'currency': curr}]}):
        pprint(vacancy)


update_db()
find_in_db()
