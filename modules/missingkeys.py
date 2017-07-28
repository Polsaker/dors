""" return a chracter that is broken on your keyboard """
from dors import commandHook


@commandHook(['zero'])
def zerokey(irc, ev):
    irc.message(ev.replyto, "0")


@commandHook(['one'])
def onekey(irc, ev):
    irc.message(ev.replyto, "1")


@commandHook(['nine'])
def ninekey(irc, ev):
    irc.message(ev.replyto, "9")
