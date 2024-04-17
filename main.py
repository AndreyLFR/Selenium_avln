import time
import csv
from functools import reduce

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import datetime
import requests
import pprint
import re
import json
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent()

name_file_url_card_auto = f'{datetime.date.today().isoformat()}_url_card_auto.csv'
url = 'https://avilon.ru'
input_brand = input('введите марку автомобиля (введите tank): ')

options = Options()
options.add_argument(f'user-agent={ua.chrome}')
options.add_argument('start-maximized')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
#options.add_argument('--headless')
options.add_argument('--no-sanbox')
options.add_argument('--disable-extensions')
options.add_argument('--dns-prefetch-disable')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

def start_search_auto(driver, url):
    driver.get(f'{url}/search/')
    time.sleep(1)
    search = driver.find_element(By.ID, 'search-page-query')
    search.send_keys(input_brand)
    search.send_keys(Keys.ENTER)
    time.sleep(1)

def save_url_cards(name, input_list):
    with open(name, 'a', newline='') as f:
        url_writer = csv.writer(f, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        url_writer.writerow(input_list)

def collect_cards(driver, name_file):
    while True:
        #можно забрать все карточки, так как динамической прогрузки нет
        cards = driver.find_elements(By.XPATH, "//div[@class='cars-inner__cards wishlist cars-inner__cards--search']//div[@class='cars-cards-list__item cars-card  ']//a")
        links = [card.get_attribute('href') for card in cards]
        #сохраняю ссылки
        print(driver.current_url)
        save_url_cards(name=name_file, input_list=links)
        #проверка следующей страницы
        try:
            next_page = driver.find_element(By.XPATH, "//a[@class='cars-inner__pagination-arrow cars-inner__pagination-arrow--forward']").get_attribute('href')
            driver.get(next_page)
        except Exception as e:
            # условие выхода - отсутствие перехода на следующую страницу
            print(e, 'следующей страницы нет')
            break
        time.sleep(2)


def load_url_cards(name_file):
    with open(name_file, 'r', newline='') as csvfile:
        urls = []
        for list_ in csv.reader(csvfile, delimiter=' ', quotechar='|'):
            urls = urls + list_
    return list(set(urls))


def collecting_data_bs4(name_file):
    urls = load_url_cards(name_file=name_file)
    headers = {'User-Agent': ua.chrome}
    session = requests.session()
    list_dict_auto = []
    for url in urls:
        print(url)
        response = session.get(url=url, headers=headers)
        if not response.ok:
            break
        soup = BeautifulSoup(response.text, features='html.parser')
        auto_dict = {}
        auto_dict['brand'] = soup.find('meta', {'itemprop': 'brand'}).get('content')
        auto_dict['name'] = soup.find('meta', {'itemprop': 'name'}).get('content')
        auto_dict['url'] = url
        try:
            auto_dict['price'] = float(soup.find('div', {'class': 'car-detail__aside-price-full'}).get('data-baseprice'))
        except Exception as e:
            auto_dict['price'] = 0
        print(auto_dict)
        list_dict_auto.append(auto_dict)
        time.sleep(5)
    return auto_dict


start_search_auto(driver=driver, url=url)
collect_cards(driver=driver, name_file=name_file_url_card_auto)
driver.quit()
try:
    auto_dict = collecting_data_bs4(name_file=name_file_url_card_auto)
except Exception as e:
    print(e)
    auto_dict = {'brand': None, 'name': None, 'price': None, 'url': None}

with open(f'{input_brand}.csv', 'w', newline='') as csvfile:
    fieldnames = ['brand', 'name', 'price', 'url']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(auto_dict)