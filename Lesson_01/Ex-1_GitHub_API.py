""" Скрипт выводит список репозиториев пользователя и сохраняет их в файл {nickname}_repos.json """

import requests

nickname = input('User Nickname: ')

main_link = f'https://api.github.com/users/{nickname}'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
           'Accept': '*/*'}

response = requests.get(main_link, headers=headers)
user_data = response.json()

repos_link = user_data['repos_url']
response = requests.get(repos_link, headers=headers)
repos_data = response.text

file_name = f'{nickname}_repos.json'

with open(file_name, 'w') as f:
    f.write(repos_data)
