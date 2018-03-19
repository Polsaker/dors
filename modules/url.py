from dors import stuffHook
import config
import re
import urllib.request, urllib.error, urllib.parse
import time
from bs4 import BeautifulSoup
import requests


url_finder = re.compile('(?iu)(\!?(http|https|ftp)(://\S+\.?\S+/?\S+?))')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }


def remove_nonprint(text):
    new = str()
    for char in text:
        x = ord(char)
        if x > 32 and x <= 126:
            new += char
    return new


def find_title(url, irc):
    """
    This finds the title when provided with a string of a URL.
    """

    for item in config.urlblacklist:
        if item in url:
            return False, 'ignored'

    if not re.search('^((https?)|(ftp))://', url):
        url = 'http://' + url

    if '/#!' in url:
        url = url.replace('/#!', '/?_escaped_fragment_=')

    if 'i.imgur' in url: # blacklist?
        return

    if 'zerobin.net' in url:
        return True, 'ZeroBin'

    if 'store.steampowered.com/app' in url and 'steam' in irc.plugins:
        appid = re.search('.*store.steampowered.com/app/(\d+).*', url)
        return True, irc.plugins['steam'].getAppInfo(appid.group(1), False)

    if 'twitter.com' in url:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        title = str(soup.title.string)
        title = title.replace('\n', ' ').replace('\r', '')
        title = title.replace('"', '')
        return True, "{0}".format(title)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    title = str(soup.title.string)
    title = title.replace('\n', '').replace('\r', '')

    def remove_spaces(x):
        if '  ' in x:
            x = x.replace('  ', '')
            return remove_spaces(x)
        else:
            return x

    title = remove_spaces(title)

    if len(title) > 200:
        title = title[:200] + '...'
    return True, "{0}".format(title)


def getTLD(url):
    url = url.strip()
    url = remove_nonprint(url)
    idx = 7
    if url.startswith('https://'):
        idx = 8
    elif url.startswith('ftp://'):
        idx = 6
    u = url[idx:]
    f = u.find('/')
    if f != -1:
        u = u[0:f]
    return remove_nonprint(u)


def get_results(text, irc, manual=False):
    if not text:
        return False, list()
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    display = list()
    passs = False
    channel = str()
    if hasattr(text, 'sender'):
        channel = text.sender
    while i < k:
        url = a[i][0].encode()
        url = url.decode()
        url = remove_nonprint(url)
        domain = getTLD(url)
        if '//' in domain:
            domain = domain.split('//')[1]

        bitly = url

        if not url.startswith("!"):
            passs, page_title = find_title(url, irc)
            display.append([page_title, url, bitly, passs])
        else:
            ## has exclusion character
            if manual:
                ## only process excluded URLs if .title is used
                url = url[1:]
                passs, page_title = find_title(url, irc)
                display.append([page_title, url, bitly, passs])
        i += 1

    ## check to make sure at least 1 URL worked correctly
    overall_pass = False
    for x in display:
        if x[-1] == True:
            overall_pass = True

    return overall_pass, display


@stuffHook('(?iu).*(\!?(http|https)(://\S+)).*')
def show_title_auto(irc, ev):
    '''No command - Automatically displays titles for URLs'''
    if len(re.findall('\([\d]+\sfiles\sin\s[\d]+\sdirs\)', ev.message)) == 1:
        ## Directory Listing of files
        return

    try:
        status, results = get_results(ev.message, irc)
    except Exception as e:
        print('[%s]' % e, ev.message)
        return

    k = 1

    output_shorts = str()
    results_len = len(results)

    for r in results:
        ## loop through link, shorten pairs, and titles
        returned_title = r[0]
        orig = r[1]
        bitly_link = r[2]
        link_pass = r[3]

        if returned_title == 'imgur: the simple image sharer':
            ## because of the i.imgur hack above this is done
            ## to prevent from showing useless titles on image
            ## files
            return

        if k > 3:
            ## more than 3 titles to show from one line of text?
            ## let's just show only the first 3.
            break
        k += 1


        reg_format = '[ %s ] - %s'
        special_format = '[ %s ]'
        response = str()

        if status and link_pass:
            response = reg_format % (returned_title, getTLD(orig))

        if response:
            irc.message(ev.replyto, response)

    if output_shorts:
        jenni.say((output_shorts).strip())
