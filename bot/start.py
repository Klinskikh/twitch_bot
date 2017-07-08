import requests
import subprocess
import json
import sys
import multiprocessing
import time
import random
from bs4 import BeautifulSoup
import urllib2

headers = {'User-Agent': 'Mozilla 5.10'}
url = 'https://free-proxy-list.net'
request = urllib2.Request(url, None, headers)
page = urllib2.urlopen(request)
soup = BeautifulSoup(page, "html.parser")
table = soup.findAll('tbody')[0]('tr')

i = 0
data = []
for row in table:
    cols = row.find_all('td')
    cols = [elem.text for elem in cols]
    data.append([elem for elem in cols if elem])
    i += 1

k = 0
proxies = []
while k < 40:
    proxies.append([data[k][0] + ":" + data[k][1]])
    k = k + 1

channel_url = "www.twitch.tv/"
processes = []
CUR_FILE = 'current_viewers'

def get_channel():
    # Reading the channel name - passed as an argument to this script
    if len(sys.argv) >= 2:
        global channel_url
        channel_url += sys.argv[1]
    else:
        print "An error has occurred while trying to read arguments. Did you specify the channel?"
        sys.exit(1)


def get_proxies():
    # Reading the list of proxies
    try:
        with open(u'proxylist') as f:
            lines = ['http://{0}'.format(line.rstrip("\n")) for line in f]
    except IOError as e:
        print "An error has occurred while trying to read the list of proxies: %s" % e.strerror
        sys.exit(1)

    return lines


def get_url():
    # Getting the json with all data regarding the stream
    try:
        response = subprocess.Popen(
            ["livestreamer", "--http-header", "Client-ID=ewvlchtxgqq88ru9gmfp1gmyt6h2b93",
             channel_url, "-j"], stdout=subprocess.PIPE).communicate()[0]
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


def open_url(url, proxy):
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
                response = s.head(url, proxies=proxy)
            print "Sent HEAD request with %s" % proxy["http"]
            time.sleep(10)
        except requests.exceptions.Timeout:
            print "  Timeout error for %s" % proxy["http"]
            break
        except requests.exceptions.ConnectionError:
            print "  Connection error for %s" % proxy["http"]
            errors += 1
            if errors > 10:
                break


def prepare_processes():
    global processes
    #    proxies = get_proxies()
    if len(proxies) < 1:
        print "An error has occurred while preparing the process: Not enough proxy servers. Need at least 1 to function."
        sys.exit(1)

    for proxy in proxies:
        # Preparing the process and giving it its own proxy
        processes.append(
            multiprocessing.Process(
                target=open_url, kwargs={
                    "url": get_url(), "proxy": {
                        "http": proxy[0]}}))
        print '.',
    print ''


if __name__ == "__main__":
    print "Obtaining the channel..."
    get_channel()
    print "Obtained the channel"
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
