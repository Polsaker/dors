from jenni import stuffHook
import config
import re
import urllib.request, urllib.error, urllib.parse
import time

url_finder = re.compile('(?iu)(\!?(http|https|ftp)(://\S+\.?\S+/?\S+?))')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }


def get_page_backup(url):
    # fix url
    k = urllib.parse.urlparse(url)
    url = k.geturl()
    
    req = urllib.request.Request(url, headers={'Accept':'*/*'})
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0')
    u = urllib.request.urlopen(req)
    contents = u.read()
    out = dict()
    try:
        con = (contents).decode('utf-8')
    except:
        con = (contents).decode('iso-8859-1')
    out['code'] = u.code
    out['read'] = con
    out['geturl'] = u.geturl()
    out['headers'] = dict(u.headers)
    out['url'] = u.url
    return out['code'], out


def remove_nonprint(text):
    new = str()
    for char in text:
        x = ord(char)
        if x > 32 and x <= 126:
            new += char
    return new


def find_title(url):
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

    if 'i.imgur' in url:
        a = url.split('.')
        url = a[0][:-1] + '.'.join(a[1:-1])

    if 'zerobin.net' in url:
        return True, 'ZeroBin'

    #url = url.decode()
    msg = str()
    k = 0
    status = False

    while not status:
        k += 1
        if k > 3:
            break

        msg = dict()
        status, msg = get_page_backup(url)

        if type(msg) == type(dict()) and 'code' in msg:
            status = msg['code']
        else:
            continue
        time.sleep(0.5)


    if not status:
        return False, msg

    useful = msg

    info = useful['headers']
    page = useful['read']

    try:
        mtype = info['Content-Type']
    except:
        print('failed mtype:', str(info))
        return False, 'mtype failed'
    if not (('/html' in mtype) or ('/xhtml' in mtype)):
        return False, str(mtype)

    content = page
    regex = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
    content = regex.sub(r'<\1title>', content)
    regex = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)
    content = regex.sub('', content)
    start = content.find('<title>')
    if start == -1:
        return False, 'NO <title> found'
    end = content.find('</title>', start)
    if end == -1:
        return False, 'NO </title> found'
    content = content[start + 7:end]
    content = content.strip('\n').rstrip().lstrip()
    title = content

    if len(title) > 200:
        title = title[:200] + '[...]'

    def e(m):
        entity = m.group()
        if entity.startswith('&#x'):
            cp = int(entity[3:-1], 16)
            meep = chr(cp)
        elif entity.startswith('&#'):
            cp = int(entity[2:-1])
            meep = chr(cp)
        else:
            entity_stripped = entity[1:-1]
            try:
                char = name2codepoint[entity_stripped]
                meep = chr(char)
            except:
                if entity_stripped in HTML_ENTITIES:
                    meep = HTML_ENTITIES[entity_stripped]
                else:
                    meep = str()
        try:
            return meep.decode()
        except:
            return meep.encode().decode()

    title = r_entity.sub(e, title)

    title = title.replace('\n', '')
    title = title.replace('\r', '')

    def remove_spaces(x):
        if '  ' in x:
            x = x.replace('  ', ' ')
            return remove_spaces(x)
        else:
            return x

    title = remove_spaces(title)

    new_title = str()
    for char in title:
        if len(list(char.encode())) <= 3:
            new_title += char
    title = new_title

    title = re.sub(r'(?i)dcc\ssend', '', title)

    title += '\x0F'
    if title:
        return True, title
    else:
        return False, 'No Title'


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
    if f == -1:
        u = url
    else:
        u = url[0:idx] + u[0:f]
    return remove_nonprint(u)


def get_results(text, manual=False):
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
        if 'i.imgur.com' in url and url.startswith('http://'):
            url = url.replace('http:', 'https:')

        bitly = url

        if not url.startswith("!"):
            passs, page_title = find_title(url)
            display.append([page_title, url, bitly, passs])
        else:
            ## has exclusion character
            if manual:
                ## only process excluded URLs if .title is used
                url = url[1:]
                passs, page_title = find_title(url)
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
        status, results = get_results(ev.message)
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
