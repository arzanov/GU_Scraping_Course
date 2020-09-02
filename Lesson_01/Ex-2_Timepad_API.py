# access_token=a451e2b7202ff50e7fd1029061aa3ed6c019785b

import requests


main_link = 'https://api.timepad.ru/v1/events.json'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
           'Accept': '*/*',
           'Authorization': 'Bearer a451e2b7202ff50e7fd1029061aa3ed6c019785b'}

response = requests.get(main_link, headers=headers)
events_data = response.text

with open('timepad_request.json', 'w') as f:
    f.write(events_data)
