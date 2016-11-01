from dors import startupHook, commandHook
import ircmatch
import sqlite3 

oldOn_message = None
gbot = None
def checkdb(c):
    c.execute("CREATE TABLE IF NOT EXISTS ignore ( hostmask text)")
            
def load_db():
    conn = sqlite3.connect('ignore.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    c.execute("SELECT * FROM ignore")
    
    ignores = []
    
    for i in c:
        ignores.append(i[0])
    
    return ignores

def our_on_message(target, source, message):
    global gbot
    global oldOn_message
    for ignore in gbot.ignores:
        if gbot.isadmin(source):
            break
        hostmask = "{0}!{1}@{2}".format(gbot.users[source]['nickname'],
                                        gbot.users[source]['username'],
                                        gbot.users[source]['hostname'])
        if ircmatch.match(0, ignore, hostmask):
            return
    oldOn_message(target, source, message)


@startupHook()
def setupIgnore(bot):
    global gbot
    global oldOn_message
    if gbot is None
        oldOn_message = bot.on_message
        
        bot.on_message = our_on_message

    gbot = bot
    bot.ignores = load_db()


@commandHook('ignore', help="ignore <add|del|list> [ignore]")
def ignore(irc, event):
    if not irc.isadmin(event.source):
        return irc.message(event.replyto, "Not authorized")
    
    if not event.args:
        return irc.reply("Usage: ignore <add|del|list> [ignore]")
    
    if event.args[0] == "list":
        return irc.reply(" ".join(irc.ignores))
    if not len(event.args) > 1:
        return irc.reply("Usage: ignore <add|del|list> [ignore]")
    
    conn = sqlite3.connect('ignore.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()

    if event.args[0] == "add":
        irc.ignores.append(event.args[1])
        c.execute("INSERT INTO ignore VALUES (?)", (event.args[1], ))
        conn.commit()
        irc.reply("Ignore added.")
    elif event.args[0] == "del":
        try:
            irc.ignores.remove(event.args[1])
        except ValueError:
            return irc.reply("Ignore not found.")
        c.execute("DELETE FROM ignore WHERE hostmask = ?", (event.args[1], ))
        conn.commit()
        irc.reply("Ignore removed.")
    else:
        irc.reply("Usage: ignore <add|del|list> [ignore]")
