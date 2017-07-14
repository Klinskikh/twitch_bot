# -*- coding: utf-8 -*-
import requests
import subprocess
import json
import sys
import multiprocessing
import time
import random
from bs4 import BeautifulSoup
import urllib2


channel_url = "www.twitch.tv/"
processes = []
CUR_FILE = 'current_viewers'
URLS = 'urls.json'
USED_URLS = 'used_token.json'
BAD_TOKEN = 'bad_token.json'


def get_proxy_list():                                               #функция готова
    # get ip list of proxies
    headers = {'User-Agent': 'Mozilla 5.10'}
    url = 'https://free-proxy-list.net'
    request = urllib2.Request(url, None, headers)
    page = urllib2.urlopen(request)
    soup = BeautifulSoup(page, "html.parser")
    table = soup.findAll('tbody')[0]('tr')                          #выборка в таблице строк
    data = []
    proxies1 = []
    for row in table:                                               #создаем таблицу с данными, полученными супом
        cols = row.find_all('td')
        cols = [elem.text for elem in cols]
        data.append([elem for elem in cols if elem])
    for k in range(0, len(data)):                                   #создание пары прокси и порт
        proxies1.append(data[k][0] + ":" + data[k][1])
    try:
        with open("proxylist.json", 'w+') as f:                     #запись результата в файл в json формате
            f.write(json.dumps(proxies1))
    except IOError as e:
        print "An error has occurred while trying to write the list of proxies: %s" % e.strerror
        sys.exit(1)


def get_channel():                                                  #функция готова
    # Reading the channel name - passed as an argument to this script
    if len(sys.argv) >= 2:
        global channel_url
        channel_url += sys.argv[1]
    else:
        print "An error has occurred while trying to read arguments. Did you specify the channel?"
        sys.exit(1)


def get_proxies():
    # Reading the list of proxies
    proxies1 = get_proxy_list()
    try:
        with open(u'proxylist') as f:
            lines = ['http://{0}'.format(line.rstrip("\n").rstrip("']\\").lstrip("['u\\")) for line in f]
    except IOError as e:
        print "An error has occurred while trying to read the list of proxies: %s" % e.strerror
        sys.exit(1)

    return lines


def get_url():                                                          #кандидат на исключение, аналог создан
    # Getting the json with all data regarding the stream
    try:
        with open("twitch_token") as tn:
            for tn_line in tn:
                tn_line = tn_line.rstrip('\n')
                response = subprocess.Popen(
                    ["livestreamer", "--twitch-oauth-token=" + tn_line, channel_url, "-j"],
                    stdout=subprocess.PIPE).communicate()[0]
    except subprocess.CalledProcessError:
        print "An error has occurred while trying to get the stream data. Is the channel online? Is the channel name correct?"
        sys.exit(1)
    except OSError:
        print "An error has occurred while trying to use livestreamer package. Is it installed? Do you have Python in your PATH variable?"

    # Decoding the url to the worst quality of the stream
    try:
        url = json.loads(response)['streams']['audio_only']['url']
    except:
        try:
            url = json.loads(response)['streams']['worst']['url']
        except (ValueError, KeyError):
            print "An error has occurred while trying to get the stream data. Is the channel online? Is the channel name correct?"
            sys.exit(1)

    return url


def get_urls():                                                     #получаем ссылки для просмотра - на данном этапе готова
    try:
        with open('twitch_token.json', 'r') as tokens:
            urls = []
            bad_token = []
            token_list = json.loads(tokens.read())                  #создаем лист токенов в json
            for token in token_list:                                #проходимся по списку токенов с целью получить варианты воспроизведения в json
                response = subprocess.Popen(
                        ["livestreamer", "--twitch-oauth-token=" + token, channel_url, "-j"],
                        stdout=subprocess.PIPE).communicate()[0]
                try:
                    url = json.loads(response)['streams']['audio_only']['url']          #ищем ссылку на воспроизведение только со звуком
                except:
                    try:
                        url = json.loads(response)['streams']['worst']['url']           #в противном случае худшее качество
                    except (ValueError, KeyError):                                      #возможно канал неактивен или токен протух - проверяем это
                        print "An error has occurred while trying to get the stream data. Is the channel online? Is the channel name correct? Then check token %s" % token
                        # sys.exit(1)
                        url = 'bad_token'
                        bad_token.append(token)
                if url != 'bad_token':
                    urls.append(url)
            with open(URLS, 'w+') as f:                                                 #записываем результаты в файлы
                f.write(json.dumps(urls))
            with open(BAD_TOKEN, 'w+') as f:
                    f.write(json.dumps(bad_token))
    except subprocess.CalledProcessError:
        print "An error has occurred while trying to get the stream data. Is the channel online? Is the channel name correct?"
        sys.exit(1)
    except OSError:
        print "An error has occurred while trying to use livestreamer package. Is it installed? Do you have Python in your PATH variable?"


def open_url(url, proxy_in_use):
    errors = 0
    with open(CUR_FILE, 'r') as f:
        current_viewers = int(f.read())
    current_viewers += 1
    with open(CUR_FILE, 'w+') as f:
        f.write(str(current_viewers))
    print "Now watching {0}".format(current_viewers)
    # Sending HEAD requests
    while True:
        try:
            with requests.Session() as s:
                response = s.head(url, proxies=proxy_in_use)
            print "Sent HEAD request with %s" % proxy_in_use["http"]
            time.sleep(10)
        except requests.exceptions.Timeout:
            print "  Timeout error for %s" % proxy_in_use["http"]
            break
        except requests.exceptions.ConnectionError:
            print "  Connection error for %s" % proxy_in_use["http"]
            errors += 1
            if errors > 10:
                break


def prepare_processes():
    global processes
    proxies = open("proxylist.json", 'r')
    proxy_in_use = list(json.loads(proxies.read()))
    urls = open(URLS, 'r')
    used_urls = []
    if len(proxy_in_use) < 1:
        print "An error has occurred while preparing the process: Not enough proxy servers. Need at least 1 to function."
        sys.exit(1)
    for url in json.loads(urls.read()):
        print proxy_in_use[0]
        processes.append(
            multiprocessing.Process(
                target=open_url, kwargs={
                    "url": url, "proxy_in_use": {
                        "http": proxy_in_use[0]
                    }
                }
            )
        )
        proxy_in_use.remove(proxy_in_use[0])
        used_urls.append(urls)
        with open('proxylist.json', 'w+') as f:
            f.write(json.dumps(proxy_in_use))
    # for proxy in proxies:
    #     # Preparing the process and giving it its own proxy
    #     processes.append(
    #         multiprocessing.Process(
    #             target=open_url, kwargs={
    #                 "url": get_url(), "proxy": {
    #                     "http": proxy}}))
        print '.',
    print ''


if __name__ == "__main__":
    print "Obtaining the channel..."
    get_channel()
    print "Obtained the channel"
    print "Obtain and safe proxy list in file"
    get_proxy_list()
    print "DONE"
    print "Otraining urls list"
    get_urls()
    print "Ontained urls list"
    print "Preparing the processes..."
    prepare_processes()
    with open(CUR_FILE, 'w+') as curf:
        curf.write('0')
    print "Prepared the processes"
    print "Booting up the processes..."

    # Timer multiplier
    n = 2

    # Starting up the processes
    for process in processes:
        time.sleep(random.randint(1, 5) * n)
        process.daemon = True
        process.start()
        if n > 1:
            n -= 1
    print '============================all process have runned'
    # Running infinitely
    while True:
        time.sleep(1)
