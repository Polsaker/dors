#!/usr/bin/env python3

import pydle
import config
import os
import importlib
import re
import traceback
import threading

Waifu = pydle.featurize(pydle.features.RFC1459Support, pydle.features.WHOXSupport,
                             pydle.features.ISUPPORTSupport,
                             pydle.features.AccountSupport, pydle.features.TLSSupport, 
                             pydle.features.IRCv3_1Support, pydle.features.CTCPSupport)

# Event object!

class Event(object):
    def __init__(self, source, target, message):
        self.source = source
        self.target = target
        self.message = message
        
        self.command = message.split(" ")[0][1:] if message[0] == "." else None
        self.args = message.split(" ")[1:]


class Jenni(Waifu):
    def __init__(self, nick, *args, **kwargs):
        super().__init__(nick, *args, **kwargs)
                
        self.stuffHandlers = []
        self.startupHooks = []
        self.commandHooks = []
        
        for module in os.listdir(os.path.dirname("modules/")):
            if module == '__init__.py' or module[-3:] != '.py':
                continue
            if module in config.disabled_modules:
                continue
            themodule = __import__("modules." + module[:-3], locals(), globals())
            themodule = getattr(themodule, module[:-3])

            # Iterate over all the methods in the module to find handlers
            funcs = [f for _, f in themodule.__dict__.items() if callable(f)]
            for func in funcs:
                try:
                    func._handler
                except:
                    continue # nothing to do here.
                if func._handler == 1: # Stuff handler.
                    self.stuffHandlers.append({'regex': func._regex, 'func': func, 'module': module[:-3]})
                elif func._handler == 2: # startup
                    self.startupHooks.append({'func': func, 'module': module[:-3]})
                elif func._handler == 3: # command
                    self.commandHooks.append({'commands': func._commands, 'help': func._help, 'func': func, 'module': module[:-3]})
                    
    @pydle.coroutine
    def on_message(self, target, source, message):
        event = Event(source, target, message)
        # Commands
        if message.strip().startswith(config.prefix):
            command = message.strip().split()[0].replace(config.prefix, '', 1)
            args = message.strip().split()[1:]
            
            pot = next((item for item in self.commandHooks if command in item['commands']))

            if pot:
                try:
                    pot['func'](self, event)
                except Exception as e:
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(stuff['module'], tb))


        # Hooks
        # Iterate over all the stuff handlers.
        for stuff in self.stuffHandlers:
            # try to find a match
            if stuff['regex'].match(message):
                # Got a match. Call the function
                try:
                    stuff['func'](self, event)
                except Exception as e:
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(stuff['module'], tb))

    def on_connect(self):
        super().on_connect()
        for channel in config.channels:
            self.join(channel)
        
        for hook in self.startupHooks:
            try:
                t = threading.Thread(target=hook['func'], args=(self,))
                t.daemon=True
                t.start()
            except Exception as e:
                tb = repr(e) + traceback.format_exc().splitlines()[-3]
                print("Error in {0} module: {1}".format(stuff['module'], tb))


if __name__ == '__main__':
    client = Jenni(config.nick, sasl_username=config.user, sasl_password=config.password)

    client.connect(config.server, config.port, tls=config.tls)
    client.handle_forever()

# Decorators and other shit
def stuffHook(regex):
    def wrap(func):
        func._handler = 1 # 1: Stuff handler.
        func._regex = re.compile(regex)
        return func
    return wrap

def commandHook(commands, help=""):
    if type(commands) == str:
        commands = [commands]
    def wrap(func):
        func._handler = 3 # 3: Command.
        func._commands = commands
        func._help = help
        return func
    return wrap
    
def startupHook():
    def wrap(func):
        func._handler = 2 # 2: function called when bot connects.
        return func
    return wrap
