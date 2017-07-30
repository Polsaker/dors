""" return a current balance for crytpo """
from dors import commandHook


@commandHook(['btcbalance'])
def getbtcbalance(irc, ev):
    addr = ev.args[0]
    data = requests.get("http://btc.blockr.io/api/v1/address/info/" + addr).json()
    irc.message(ev.replyto, ev.source + ": ฿" + data['data']['balance'])


@commandHook(['ltcbalance'])
def getltcbalance(irc, ev):
    addr = ev.args[0]
    data = requests.get("http://ltc.blockr.io/api/v1/address/info/" + addr).json()
    irc.message(ev.replyto, ev.source + ": " + data['data']['balance'] + "LTC")


@commandHook(['dogebalance'])
def getdogebalance(irc, ev):
    addr = ev.args[0]
    data = requests.get("https://dogechain.info/api/v1/address/balance/" + addr).json()
    irc.message(ev.replyto, ev.source + ": " + data['balance'] + "Doge")
