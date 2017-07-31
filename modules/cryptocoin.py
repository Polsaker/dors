from dors import commandHook
import requests
import math

@commandHook(['fees'])
def bitfee(irc, ev):
    bitfee = requests.get("https://bitcoinfees.21.co/api/v1/fees/recommended").json()
    irc.message(ev.replyto, ev.source + ": Recommended fees (in satoshi/byte): \002Fastest\002: " + str(bitfee['fastestFee']) + ", \002half hour\002: " + str(bitfee['halfHourFee']) + ", \002hour\002: " + str(bitfee['hourFee']))


@commandHook(['bit', 'bits'])
def bit(irc, ev):
    try:
        bits = float(ev.args[0].replace('k', ''))
        if 'k' in ev.args[0]:
            bits *= 1000
        bits = int(bits)
    except (IndexError, ValueError):
        return irc.message(ev.replyto, "Usage: .bit <bits>")
    
    bitcoin = bits /1000000
    bitprice = requests.get("https://blockchain.info/es/ticker").json()
    
    message = "\002{0}\002 bits => ฿\002{1}\002 => $\002{2}\002, €\002{3}\002, £\002{4}\002.".format(
                bits, bitcoin, round(bitprice['USD']['last']*bitcoin,2), round(bitprice['EUR']['last']*bitcoin,2),
                round(bitprice['GBP']['last']*bitcoin,2))
    irc.message(ev.replyto, ev.source + ": " + message)    


@commandHook(['bitcoin', 'btc'])
def btc(irc, ev):
    tick = True
    try:
        bitcoin = float(ev.args[0])
    except (IndexError, ValueError):
        if len(ev.args) > 0 and len(ev.args[0]) <= 34 and len(ev.args[0]) >= 26 and ev.args[0][0] in ("1", "3"):
            data = requests.get("http://btc.blockr.io/api/v1/address/info/" + ev.args[0]).json()
            if not data['data']['is_valid']:
                return irc.reply('Invalid address')
            bitcoin = data['data']['balance']
            tick = False
        else:
            bitcoin = 1.0
    
    coinPrice(irc, 'bitcoin', bitcoin, tick)

@commandHook(['litecoin', 'ltc'])
def ltc(irc, ev):
    tick = True
    try:
        bitcoin = float(ev.args[0])
    except (IndexError, ValueError):
        if len(ev.args) > 0 and len(ev.args[0]) <= 34 and len(ev.args[0]) >= 26 and ev.args[0][0] in ("L", "M", "3"):
            data = requests.get("http://ltc.blockr.io/api/v1/address/info/" + ev.args[0]).json()
            if not data['data']['is_valid']:
                return irc.reply('Invalid address')
            bitcoin = data['data']['balance']
            tick = False
        else:
            bitcoin = 1.0
    
    coinPrice(irc, 'litecoin', bitcoin, tick)

@commandHook(['dogecoin', 'doge'])
def doge(irc, ev):
    tick = True
    try:
        dogecoin = float(ev.args[0])
    except (IndexError, ValueError):
        if len(ev.args) > 0 and len(ev.args[0]) <= 34 and len(ev.args[0]) >= 26 and ev.args[0][0] in ("D", "9", "A"):
            data = requests.get("https://dogechain.info/api/v1/address/balance/" + ev.args[0]).json()
            if data['success'] == 0:
                return irc.reply(data['error'])
            dogecoin = float(data['balance'])
            tick = False
        else:
            dogecoin = 1000.0

    coinPrice(irc, 'dogecoin', dogecoin, tick)

@commandHook(['ethereum', 'eth'])
def eth(irc, ev):
    try:
        ethereum = float(ev.args[0])
    except (IndexError, ValueError):
        ethereum = 1.0
    
    coinPrice(irc, 'ethereum', ethereum)

@commandHook(['mysterium', 'myst'])
def myst(irc, ev):
    try:
        mysterium = float(ev.args[0])
    except (IndexError, ValueError):
        mysterium = 1.0
    
    coinPrice(irc, 'mysterium', mysterium)

def prettify(thing):
    if thing > 0:
        return "\00303+" + str(thing) + "\003"
    elif thing < 0:
        return "\00304" + str(thing) + "\003"

@commandHook(['coin'])
def coin(irc, ev):
    try:
        coin = ev.args[0]
    except (IndexError, ValueError):
        coin = 'bitcoin'
    try:
        amount = float(ev.args[1])
    except (IndexError, ValueError):
        amount = 1.0

    coinPrice(irc, coin, amount)

def coinPrice(irc, coin, amount, tick=True):
    try:
        info = requests.get("https://api.coinmarketcap.com/v1/ticker/" + coin + "/").json()[0]
    except:
        return irc.reply("Coint not found")
    message = "\002{0}\002 \002{1}\002 => $\002{2}\002".format(
                amount, info['symbol'], round(float(info['price_usd'])*amount,2))
    if coin != 'bitcoin':
        message += ", ฿\002{0}\002".format(round(float(info['price_btc'])*amount,8))
    
    if tick:
        message += "  [hour: \002{0}\002%, day: \002{1}\002%, week: \002{2}\002%]".format(
                   prettify(float(info['percent_change_1h'])),
                   prettify(float(info['percent_change_24h'])),
                   prettify(float(info['percent_change_7d'])))
    irc.reply(message + '.') 
