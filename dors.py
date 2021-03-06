#!/usr/bin/env python3

import pydle
import config
import os
import importlib
import re
import traceback
import threading
import copy
import time

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
        
        self.match = None # regex match for stuffHooks
        
        self.pm = False if target.startswith('#') else True
        self.replyto = source if self.pm else target
        
        self.command = message.split(" ")[0][1:] if message[0] == "." else None
        self.args = list(filter(None, message.split(" ")[1:]))
        
        self.text = " ".join(self.args)
        


class Dors(Waifu):
    def __init__(self, nick, *args, **kwargs):
        super().__init__(nick, *args, **kwargs)

        self.config = config

        self.stuffHandlers = []
        self.startupHooks = []
        self.commandHooks = []
        
        self.plugins = {}
        
        
        self.lastheardfrom = {}
        self.sourcehistory = []

        modules = []
        whitelistonly = False
        for module in os.listdir(os.path.dirname("modules/")):
            if module == '__init__.py' or module[-3:] != '.py':
                continue
            module = module[:-3]
            modules.append(module)
            if module in config.whitelistonly_modules:
                whitelistonly = True

        if whitelistonly == True:
            for module in config.whitelistonly_modules:
                self.loadModule(module)
        else:
            for module in modules:
                if module in config.disabled_modules:
                    continue
                self.loadModule(module)
            
    
    def loadModule(self, module):
        themodule = __import__("modules." + module, locals(), globals())
        themodule = getattr(themodule, module)

        self.plugins[module] = themodule
        # Iterate over all the methods in the module to find handlers
        funcs = [f for _, f in themodule.__dict__.items() if callable(f)]
        for func in funcs:
            try:
                func._handler
            except:
                continue # nothing to do here.
            if func._handler == 1: # Stuff handler.
                self.stuffHandlers.append({'regex': func._regex, 'func': func, 'module': module})
            elif func._handler == 2: # startup
                self.startupHooks.append({'func': func, 'module': module})
            elif func._handler == 3: # command
                self.commandHooks.append({'commands': func._commands, 'help': func._help, 'func': func, 'module': module})

                        
    @pydle.coroutine
    def on_message(self, target, source, message):
        event = Event(source, target, message)
        # Commands
        if message.strip().startswith(config.prefix):
            try:
                if ((time.time() - self.lastheardfrom[source] < 6) and # if it's been six seconds since this person has made a command...
                    (source == self.sourcehistory[-2] and source == self.sourcehistory[-1]) and # And they made the last two commands...
                    not self.isadmin(source)): # And the person is not an administrator...
                    return # Ignore it
            except (KeyError, IndexError):
                pass
            finally:
                self.lastheardfrom[source] = time.time()
                self.sourcehistory.append(source)

            command = message.strip().split()[0].replace(config.prefix, '', 1)
            args = message.strip().split()[1:]
            
            try:
                pot = next((item for item in self.commandHooks if command in item['commands']))
            except StopIteration:
                pot = False

            if pot:
                try:
                    pot['func'](self.wrapper(event), event)
                except Exception as e:
                    print(traceback.format_exc())
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(pot['module'], tb))


        # Hooks
        # Iterate over all the stuff handlers.
        for stuff in self.stuffHandlers:
            # try to find a match
            if stuff['regex'].match(message):
                event.match = stuff['regex'].match(message)
                # Got a match. Call the function
                try:
                    stuff['func'](self.wrapper(event), event)
                except Exception as e:
                    print(traceback.format_exc())

                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(stuff['module'], tb))

    # Remove this if pydle is fixed
    def _rename_user(self, user, new):
        if user in self.users:
            self.users[new] = copy.copy(self.users[user])
            self.users[new]['nickname'] = new
            del self.users[user]
        else:
            self._create_user(new)
            if new not in self.users:
                return

        for ch in self.channels.values():
            # Rename user in channel list.
            if user in ch['users']:
                ch['users'].discard(user)
                ch['users'].add(new)


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
                print(traceback.format_exc())

                tb = repr(e) + traceback.format_exc().splitlines()[-3]
                print("Error in {0} module: {1}".format(hook['module'], tb))

    def isadmin(self, user):
        if self.users[user]['account'] not in config.admins:
            return False
        return True
    
    def getPlugin(self, plugin):
        try:
            return self.plugins[plugin]
        except KeyError:
            return False
            
    def wrapper(self, event):
        """ we wrap ourselves before passing to modules """
        class BotWrapper(object):
            def __init__(self, bot):
                self._bot = bot

            def __getattr__(self, attr):
                if attr == 'say' or attr == 'msg':
                    return (lambda msg: self._bot.message(event.replyto, msg))
                elif attr == 'reply':
                    return (lambda msg: self._bot.message(event.replyto, event.source + ': ' + msg))
                
                return getattr(self._bot, attr)

            def __setattr__(self, attr, value):
                if attr == '_bot':
                    return super(BotWrapper, self).__setattr__(attr, value)
                else:
                    return setattr(self._bot, attr, value)

        return BotWrapper(self)
    
if __name__ == '__main__':
    client = Dors(config.nick, sasl_username=config.user, sasl_password=config.password)
    client.throttling = True
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
    
def startupHook(dummy=None):
    def wrap(func):
        func._handler = 2 # 2: function called when bot connects.
        return func
    return wrap
