from dors import commandHook
import requests
import math


@commandHook(['fees'])
def bitfee(irc, ev):
    coinPrice(irc, 'bitcoin', 1, False, True)


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


@commandHook(['bitcoin-cash', 'bch'])
def bch(irc, ev):
    try:
        bch = float(ev.args[0])
    except (IndexError, ValueError):
        bch = 1.0
    
    coinPrice(irc, 'bitcoin-cash', bch)


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


def coinPrice(irc, coin, amount, tick=True, bitfee=False):
    message = ""
    try:
        info = requests.get("https://api.coinmarketcap.com/v1/ticker/" + coin + "/").json()[0]
    except:
        return irc.reply("Coin not found")
    if bitfee:
        bitfee = requests.get("https://bitcoinfees.21.co/api/v1/fees/recommended").json()
        fee0 = round(bitfee['fastestFee'] * 256 * 0.01,1)
        fee0USD = round(float(info['price_usd']) * (fee0 / 1000000),2)
        fee1 = round(bitfee['halfHourFee'] * 256 * 0.01,1)
        fee1USD = round(float(info['price_usd']) * (fee1 / 1000000),2)
        fee2 = round(bitfee['hourFee'] * 256 * 0.01,1)
        fee2USD = round(float(info['price_usd']) * (fee2 / 1000000),2)
        message += "Recommended fees in bits: \002Fastest\002: {0} (${1}), \002half hour\002: {2} (${3}), \002hour\002: {4} (${5})".format(
                   fee0, fee0USD, fee1, fee1USD, fee2, fee2USD)
    else:
        message += "\002{0}\002 \002{1}\002 => $\002{2}\002".format(
                    amount, info['symbol'], round(float(info['price_usd'])*amount,2))
    if coin != 'bitcoin':
        message += ", ฿\002{0}\002".format(round(float(info['price_btc'])*amount,8))
    if tick:
        message += "  [hour: \002{0}\002%, day: \002{1}\002%, week: \002{2}\002%]".format(
                   prettify(float(info['percent_change_1h'])),
                   prettify(float(info['percent_change_24h'])),
                   prettify(float(info['percent_change_7d'])))
    irc.reply(message + '.') 


@commandHook(['ticker'])
def ticker(irc, ev):
    try:
        coin = ev.args[0]
    except (IndexError, ValueError):
        coin = 'BTC'
    try:
        amount = float(ev.args[1])
    except (IndexError, ValueError):
        amount = 1.0
    if coin.upper() == "DOGE":
        if amount == 1.0:
            amount = 1000.0

    tickerPrice(irc, coin.upper(), amount)


def tickerPrice(irc, coin, amount):
    message = ""
    try:
        info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coin + "&tsyms=BTC,USD,GBP,EUR,AUD,ARS").json()
    except:
        return irc.reply("Coin not found")
    # docs https://www.cryptocompare.com/api
    USD = round(float(info['USD'])*amount,2)
    GBP = round(float(info['GBP'])*amount,2)
    EUR = round(float(info['EUR'])*amount,2)
    AUD = round(float(info['AUD'])*amount,2)
    ARS = round(float(info['ARS'])*amount,2)
    message += "\002{0}\002 \002{1}\002 => $\002{2}\002, £\002{3}\002, €\002{4}\002, $\002{5}\002AUD, $\002{6}\002ARS".format(amount, coin, USD, GBP, EUR, AUD, ARS)
    irc.reply(message + '.')
