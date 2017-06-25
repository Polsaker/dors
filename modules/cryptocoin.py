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
    except IndexError or ValueError:
        return irc.message(ev.replyto, "Usage: .bit <bits>")
    
    bitcoin = bits /1000000
    bitprice = requests.get("https://blockchain.info/es/ticker").json()
    
    message = "\002{0}\002 bits => ฿\002{1}\002 => $\002{2}\002, €\002{3}\002, £\002{4}\002.".format(
                bits, bitcoin, round(bitprice['USD']['last']*bitcoin,2), round(bitprice['EUR']['last']*bitcoin,2),
                round(bitprice['GBP']['last']*bitcoin,2))
    irc.message(ev.replyto, ev.source + ": " + message)    


@commandHook(['bitcoin', 'btc'])
def btc(irc, ev):
    try:
        bitcoin = float(ev.args[0])
    except IndexError or ValueError:
        bitcoin = 1.0
    
    coinPrice(irc, 'bitcoin', bitcoin)

@commandHook(['litecoin', 'ltc'])
def ltc(irc, ev):
    try:
        bitcoin = float(ev.args[0])
    except IndexError or ValueError:
        bitcoin = 1.0
    
    coinPrice(irc, 'litecoin', bitcoin)

@commandHook(['dogecoin', 'doge'])
def doge(irc, ev):
    try:
        dogecoin = float(ev.args[0])
    except IndexError or ValueError:
        dogecoin = 1000.0

    coinPrice(irc, 'dogecoin', dogecoin)

def prettify(thing):
    if thing > 0:
        return "\00303+" + str(thing) + "\003"
    elif thing < 0:
        return "\00304" + str(thing) + "\003"

@commandHook(['coin'])
def coin(irc, ev):
    try:
        coin = ev.args[0]
    except IndexError or ValueError:
        coin = 'bitcoin'
    try:
        amount = float(ev.args[1])
    except IndexError or ValueError:
        amount = 1.0

    coinPrice(irc, coin, amount)

def coinPrice(irc, coin, amount):
    try:
        info = requests.get("https://api.coinmarketcap.com/v1/ticker/" + coin + "/").json()[0]
    except:
        return irc.reply("Coint not found")
    message = "\002{0}\002 \002{1}\002 => $\002{2}\002".format(
                amount, info['symbol'], round(float(info['price_usd'])*amount,2))
    if coin != 'bitcoin':
        message += ", ฿\002{0}\002".format(round(float(info['price_btc'])*amount,8))
    message += "  [hour: \002{0}\002%, day: \002{1}\002%, week: \002{2}\002%]".format(
               prettify(float(info['percent_change_1h'])),
               prettify(float(info['percent_change_24h'])),
               prettify(float(info['percent_change_7d'])))
    irc.reply(message + '.') 
