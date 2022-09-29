import os
import os.path
import shutil
import argparse
import requests
import itertools
import configparser
from time import sleep
from selenium import webdriver
from difflib import SequenceMatcher
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService

args = {}
BASE_URL = 'https://kemono.party'
BASE_URL_ARTIST = 'https://kemono.party/artists/'

SIMILAR_ARTIST_NAME_RATIO = 0.90
EXTENSIONS_VIDEO = ['.mp4', '.avi', '.mkv', '.webm']
EXTENSIONS_IMAGE = ['.jpg', '.jpeg', '.png', '.jpe', '.webp', '.gif']


def main():

    global args
    args.update(get_arguments())
    args['path'] = os.path.abspath(args['path'])

    options = Options()
    # options.add_argument('--headless')
    options.page_load_strategy = 'eager'

    driver = webdriver.Chrome(service=ChromeService(
        executable_path=ChromeDriverManager().install()), options=options)
    driver.get(BASE_URL_ARTIST)

    if args['find_more_handles'] == True:
        args['handles'].append(get_more_handles(driver, args['handles']))

    artist_links = get_artist_links(driver, args['handles'])

    for link in artist_links:
        download_artist(driver, link)

    driver.quit()


def get_arguments():

    unit = 'KBYTES_SIZE'
    argparser = argparse.ArgumentParser()
    def positive_parser(str): return abs(int(str))

    argparser.add_argument('path', help='local path to retrive stuff to')
    argparser.add_argument('handles', nargs='+',
                           help='string handles to search for the artist, like their Pixiv ID or name')
    argparser.add_argument('-f', '--find-more-handles', action='store_true',
                           help='best effort to find other handles based on the given ones')
    argparser.add_argument('-n', '--number-of-posts', nargs=1, type=positive_parser,
                           default=-1, help='number of posts to look for stuff to download')
    argparser.add_argument('-c', '--confirm-download', action='store_true',
                           help='prompts user if they really want to download the amount of files found')
    argparser.add_argument('-i', '--ignore-first-image',
                           action='store_true', help='ignores the first image in a post')
    argparser.add_argument('--img-max-size', type=positive_parser, default=-1,
                           help='max size limit for images, in kilo bytes (default: any)', metavar=unit)
    argparser.add_argument('--video-max-size', type=positive_parser,
                           default=-1, help='max size limit for videos, in kilo bytes (default: any)', metavar=unit)
    argparser.add_argument('--other-file-max-size', type=positive_parser, default=-1,
                           help='max size limit for files that are not image nor video, in kilo bytes (default: any)', metavar=unit)
    argparser.add_argument('-w', '--extensions-whitelist', nargs='+',
                           help='extensions whitelist: the script will only look for those', metavar=('extension1', 'extension2'))
    argparser.add_argument('-b', '--extensions-blacklist', nargs='+',
                           help='extensions blacklist', metavar=('extension1', 'extension2'))
    argparser.add_argument('-B', '--titles-blacklist', nargs='+',
                           help='posts with these words in their title will be skipped', metavar=('word1', 'word2'))
    argparser.add_argument(
        '--name-mask', help='string mask to name downloaded files')
    argparser.add_argument('-d', '--get-description', action='store_true',
                           help='also saves post\'s description in a text file with file\'s name')
    argparser.add_argument(
        '-l', '--LOG', action='store_true', help='enables log on console')

    return vars(argparser.parse_args())


def get_more_handles(webpage, base_handles):
    """
    pipeline *for artist's ID handle*:  1 - go to artist's pixiv;
                                        2 - get 3 images;
                                        3 - dump them into saucenao;
                                        4 - if saucenao '1xx% founded', get Pixiv artist name as handle;
                                        5 - look for danbooru or gelbooru for that image;
                                        6 - get artist romaji name as handle from there too

    pipeline for generic handle: 1 - ?
    """
    return base_handles


def get_artist_links(webpage, handles):

    WebDriverWait(webpage, timeout=10).until(
        lambda d: d.find_element(By.TAG_NAME, 'input'))

    WebDriverWait(webpage, timeout=10).until_not(
        lambda d: d.find_element(By.XPATH, "//*[contains(text(), 'Loading creator index')]"))

    links = []
    textbox = webpage.find_element(By.TAG_NAME, 'input')
    for handle in handles:

        if handle.isnumeric():
            if requests.get(BASE_URL+'/fanbox/user/'+handle).status_code < 300:
                links.append(BASE_URL+'/fanbox/user/'+handle)
            continue

        textbox.send_keys(handle)
        sleep(3)  # Change into explicit wait later...
        cards = webpage.find_elements(By.CLASS_NAME, 'user-card ')

        for card in cards:
            card_name = card.find_element(By.CLASS_NAME, 'user-card__name')
            link = card_name.find_elements(By.CLASS_NAME, 'fancy-link ')

            if link:
                if (SequenceMatcher(None, handle.lower(), card_name.text.lower()).ratio()) < SIMILAR_ARTIST_NAME_RATIO:
                    print(u"Current artist '{0}' is not close enough to '{1}' ({2:.2f}%)".format(
                        card_name.text, handle, SequenceMatcher(None, handle, card_name.text).ratio()*100))
                    continue
                links.append(link[0].get_attribute('href'))

        textbox.clear()

    return links


def download_artist(webpage, link):

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
    if(args['confirm_download']):
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
        os.makedirs(args['path'])
    except FileExistsError:
        pass

    for card in scrapped_cards:
        mod = ''
        path = ''
        while True:
            c = -1
            try:
                path = os.path.join(args['path'], (card['Card_number']+mod))
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


def scrape_card(webpage):

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
                content = body.find_elements(By.CLASS_NAME, 'post__content')
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


if __name__ == "__main__":
    main()

"""
TODO:   - Argparse configfile;
        - implement most important optional arguments (-f, -i, -b & -B);
        - implement log (& debug?);
        - refactor and modulate code.

        - V2:   - database for artists' files and cards;
                - kemonoparty artists monitor;
                - interface between PixivUtils2 & Kemono (skip images if same as downloaded by PU2, etc);
                - unify PU2 and Kemono.
        
        - V3:   - Multithreading (+multiple drivers) [refactor 2.0];
                - Finetuning of -f, -b, -B & cards' content/links
                - implement remaining optional arguments
"""
