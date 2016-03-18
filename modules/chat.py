from jenni import stuffHandler
import config

import cleverbot
from html.entities import name2codepoint
import json

import random
import re
import time
import base64

mycb = cleverbot.Cleverbot()

nowords = ['reload', 'help', 'tell', 'ask', 'ping']

r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }
noun = ['ZHVjaw==', 'Y2F0', 'ZG9n', 'aHVtYW4=',]

random.seed()

@stuffHandler("(?i)(" + config.nick + "[:,]?\s)?(.*)")
def chat(irc, event):
    text = event.message

    if len(text) > 1:
        if text.startswith('\x03') or text.startswith('\x01'):
            ## block out /ctcp
            return
    else:
        print(time.time(), 'Something went wrong with chat.py')
        return

    if not text:
        return
    
    if config.nick in text.split(" ")[0]:
        text = " ".join(text.split(" ")[1:])
    
    channel = event.target

    for x in nowords:
        if text.startswith(x):
            return

    msgi = text.strip()
    msgo = str()

    if channel.startswith('+#') or channel.startswith('@#'):
        return
    elif channel.startswith('#'):
        ## in a channel and prepended with jenni's name
        pm = False
        try:
            time.sleep(random.randint(1, 5))
            msgo = mycb.ask(msgi)
        except:
            return
    elif not channel.startswith('#'):
        ## in a PM and not prepended with jenni's name
        pm = True
        if text.startswith('.') or (hasattr(config, 'prefix') and text.startswith(config.prefix)):
            return
        elif text.startswith(config.nick + ':'):
            spt = text.split(':')[1].strip()
            for x in nowords:
                if spt.startswith(x):
                    return
        try:
            time.sleep(random.randint(1, 5))
            msgo = mycb.ask(msgi)
        except:
            return
    else:
        return

    if msgo:
        time.sleep(random.randint(1, 5))

        response = re.sub('(?i)clever(me|script|bot)', 'jenni', msgo)
        response = re.sub('(?i)\S+bot', (base64.b64decode(random.choice(noun))), response)
        response = re.sub('(?i)(bot|human)', (base64.b64decode(random.choice(noun))), response)
        response = re.sub('(?i)computer', (base64.b64decode(random.choice(noun))), response)
        response = r_entity.sub(e, response)

        if random.random() <= 0.5:
            response = response[0].lower() + response[1:]

        if random.random() <= 0.5:
            response = response[:-1]

        def chomp(txt):
            random_int_rm = random.randint(1, len(txt))
            return txt[:random_int_rm-1] + txt[random_int_rm:]

        def switcharoo(txt):
            temp = random.randint(1, len(txt) - 2)
            return txt[:temp] + txt[temp + 1] + txt[temp] + txt[temp + 2:]

        if random.random() <= 0.25:
            l_response = len(response) // 20
            for x in range(1, l_response):
                response = chomp(response)

        if random.random() <= 0.15:
            l_response = len(response) // 30
            for x in range(1, l_response):
                response = switcharoo(response)

        if random.random() <= 0.05:
            response = response.upper()


        if pm:
            if random.random() <= 0.04:
                return
            irc.message(event.source, response)
        else:
            delim = random.choice((',', ':'))
            msg = '%s' % (response)

            if random.random() <= 0.25:
                msg = event.source + delim + ' ' + msg
            if random.random() <= 0.05:
                return

            irc.message(event.target, msg)

    if random.random() <= 0.05:
        chat(jenni, input)

@stuffHandler(".+")
def random_chat(jenni, input):
    bad_chans =  fchannels()
    if bad_chans and (input.sender).lower() in bad_chans:
        return

    if random.random() <= (1 / 2500.0):
        old_input = input
        chat(jenni, old_input)


def e(m):
    entity = m.group()
    if entity.startswith('&#x'):
        cp = int(entity[3:-1], 16)
        meep = unichr(cp)
    elif entity.startswith('&#'):
        cp = int(entity[2:-1])
        meep = unichr(cp)
    else:
        entity_stripped = entity[1:-1]
        try:
            char = name2codepoint[entity_stripped]
            meep = unichr(char)
        except:
            if entity_stripped in HTML_ENTITIES:
                meep = HTML_ENTITIES[entity_stripped]
            else:
                meep = str()
    return meep


def fchannels():
    try:
        f = open('nochannels.txt', 'r')
    except:
        return False
    lines = f.readlines()[0]
    f.close()
    lines = lines.replace('\n', '')
    return lines.split(',')
