import os
import os.path
import shutil
import requests
import itertools
from time import sleep
from selenium import webdriver
from difflib import SequenceMatcher
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService

import KemonoConstants


class KemonoSpider():

    def __init__(self, artist, config=None):
        options = Options()
        # options.add_argument('--headless')
        options.page_load_strategy = 'eager'

        driver = webdriver.Chrome(service=ChromeService(
            executable_path=ChromeDriverManager().install()), options=options)
        driver.get(KemonoConstants.BASE_URL_ARTIST)

    def get_artist_links(self, webpage, handles):

        WebDriverWait(webpage, timeout=10).until(
            lambda d: d.find_element(By.TAG_NAME, 'input'))

        WebDriverWait(webpage, timeout=10).until_not(
            lambda d: d.find_element(By.XPATH, "//*[contains(text(), 'Loading creator index')]"))

        links = []
        textbox = webpage.find_element(By.TAG_NAME, 'input')
        for handle in handles:

            if handle.isnumeric():
                if requests.get(KemonoConstants.BASE_URL+'/fanbox/user/'+handle).status_code < 300:
                    links.append(KemonoConstants.BASE_URL +
                                 '/fanbox/user/'+handle)
                continue

            textbox.send_keys(handle)
            sleep(3)  # Change into explicit wait later...
            cards = webpage.find_elements(By.CLASS_NAME, 'user-card ')

            for card in cards:
                card_name = card.find_element(By.CLASS_NAME, 'user-card__name')
                link = card_name.find_elements(By.CLASS_NAME, 'fancy-link ')

                if not link:
                    continue

                match_ratio = SequenceMatcher(
                    None, handle.lower(), card_name.text.lower()).ratio()
                if match_ratio < KemonoConstants.SIMILAR_ARTIST_NAME_RATIO:
                    print(u"Current artist '{0}' is not close enough to '{1}' ({2:.2f}%)".format(
                        card_name.text, handle, match_ratio*100))
                    continue
                links.append(link[0].get_attribute('href'))

            textbox.clear()

        return links

    def scrape_card(self, webpage):

        scrapped_info = {'Card_url': None, 'Card_number': None, 'Title': None, 'Date': None, 'Download_link': [],
                         'Content': None, 'Content_link': [], 'Content_image': [], 'Image': []}

        body = webpage.find_element(By.CLASS_NAME, 'post__body')
        header = webpage.find_element(By.CLASS_NAME, 'post__header')

        scrapped_info['Card_url'] = webpage.current_url
        scrapped_info['Card_number'] = webpage.current_url.rpartition('/')[-1]
        scrapped_info['Date'] = header.find_element(
            By.CLASS_NAME, 'post__published').text
        scrapped_info['Title'] = header.find_element(
            By.CLASS_NAME, 'post__title').text

        sections = body.find_elements(By.TAG_NAME, 'h2')
        if not sections:
            return scrapped_info

        for sec in sections:
            match sec.text:
                case 'Downloads':
                    downloads = body.find_elements(
                        By.CLASS_NAME, 'post__attachments')
                    if not downloads:
                        continue
                    lis = downloads[0].find_elements(By.TAG_NAME, 'li')
                    if not lis:
                        continue
                    for li in lis:
                        scrapped_info['Download_link'].append(
                            li.find_element(By.TAG_NAME, 'a').get_attribute('href'))

                case 'Content':
                    content = body.find_elements(
                        By.CLASS_NAME, 'post__content')
                    if not content:
                        continue
                    if content[0].text != None:
                        scrapped_info['Content'] = content[0].text
                    links = content[0].find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        scrapped_info['Content_link'].append(
                            link.get_attribute('href'))
                    images = content[0].find_elements(By.TAG_NAME, 'img')
                    for image in images:
                        scrapped_info['Content_image'].append(
                            image.get_attribute('src'))

                case 'Files':
                    files = body.find_elements(By.CLASS_NAME, 'post__files')
                    if not files:
                        continue
                    links = files[0].find_elements(By.TAG_NAME, 'img')
                    for link in links:
                        scrapped_info['Image'].append(
                            link.get_attribute('src').replace('/thumbnail', ''))

        return scrapped_info

    def download_artist(self, webpage, link):

        webpage.get(link)

        # Checks if there are cards to get
        try:
            WebDriverWait(webpage, timeout=10).until(
                lambda d: d.find_element(By.CLASS_NAME, 'card-list__items'))
        except TimeoutError:
            print("Couldn't find any cards for link {0}".format(link))
            return

        # Gets number of cards
        number_of_cards = webpage.find_element(By.CLASS_NAME, 'paginator').find_element(
            By.TAG_NAME, 'small').text.rpartition(' ')[-1]
        if(_config.confirm_download):
            while True:
                proceed = input(
                    'Download files from {0} cards? [Y/N]'.format(number_of_cards)).lower()
                if proceed[0] == 'y':
                    break
                elif proceed[0] == 'n':
                    return

        cards_url = []
        current_page = webpage
        # Loops for every artist's page and retrieves its url
        while True:
            sleep(0.5)  # Change into explicit wait later...

            cards = current_page.find_element(
                By.CLASS_NAME, 'card-list__items').find_elements(By.TAG_NAME, 'article')
            for card in cards:
                cards_url.append(card.find_element(By.TAG_NAME, 'header').find_element(
                    By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'a').get_attribute('href'))

            next_page = current_page.find_element(By.ID, 'paginator-top').find_element(
                By.TAG_NAME, 'menu').find_elements(By.TAG_NAME, 'li')[-1].find_elements(By.TAG_NAME, 'a')
            if not next_page:
                break

            current_page.get(next_page[0].get_attribute('href'))

        scrapped_cards = []
        for url in cards_url:
            webpage.get(url)
            scrapped_cards.append(scrape_card(webpage))

        try:
            os.makedirs(_config.path)
        except FileExistsError:
            pass

        for card in scrapped_cards:
            mod = ''
            path = ''
            while True:
                c = -1
                try:
                    path = os.path.join(
                        _config.path, (card['Card_number']+mod))
                    print(path)
                    os.mkdir(path)
                    break
                except FileExistsError:
                    mod = str(c)
                    c += -1
            os.chdir(path)

            all_links = list(itertools.chain(
                card['Image'], card['Content_image'], card['Download_link']))
            mod = -1
            for file in all_links:
                file_name = card['Card_number'] + \
                    str(mod)+'.'+file.rpartition('.')[-1]
                if os.access(file_name, os.F_OK) == True:
                    continue

                response = requests.get(file, stream=True)
                print(file)
                if response.status_code == 200:
                    with open(file_name, 'wb') as outfile:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, outfile)
                    mod += -1

        with open('tst.txt', 'w', encoding='utf-8') as f:
            for info in scrapped_cards:
                for k, v in info.items():
                    try:
                        f.write(u"'{0}': {1:.150}\n".format(k, v))
                    except TypeError:
                        if v == None:
                            f.write(u"'{0}': None\n".format(k))
                            continue
                        for vv in v:
                            f.write(u"'{0}[{1}]': {2:.150}\n".format(
                                k, v.index(vv), vv))
                f.write('\n\n')
