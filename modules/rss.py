from dors import commandHook, startupHook
import config
import sqlite3
import time
import feedparser
import traceback

_stop = False
_interval = 60 * 5 # 5 minutes
_firstrun = True

archive = {}

def checkdb(c):
    c.execute("CREATE TABLE IF NOT EXISTS rss ( channel text,\
            site_name text, site_url text)")

@commandHook('rss-admin', help="Manages RSS feeds. Usage: .rss-admin add #channel Name url; .rss-admin del #channel [name]")
def rssadmin(irc, event):
    if not irc.isadmin(event.source):
        irc.message(event.replyto, "Not authorized")
        return
    
    if not event.args:
        irc.message(event.replyto, "{0}: {1}".format(event.source, rssadmin._help))
        irc.message(event.replyto, "{0}: No parameters specified".format(event.source))
        return
        
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    if event.args[0] == "add":
        channel = event.args[1]
        site_name = event.args[2]
        site_url = event.args[3]
        
        c.execute("INSERT INTO rss VALUES (?,?,?)", (channel.lower(), site_name,
            site_url))
        conn.commit()
        c.close()
        irc.message(event.replyto, "Successfully added values to database.")
    elif event.args[0] == "del":
        if len(event.args) == 2: # Delete by channel
            c.execute("DELETE FROM rss WHERE channel = ?", (event.args[1].lower(),))
            conn.commit()
            c.close()
            irc.message(event.replyto, "Successfully removed values from database.")
        elif len(event.args) >= 3:
            site_name = ' '.join(event.args[2:])
            c.execute("DELETE FROM rss WHERE channel = ? and site_name = ?",
                        (event.args[1].lower(), site_name))
            conn.commit()
            c.close()
            irc.message(event.replyto, "Successfully removed the site from the given channel.")
    elif event.args[0] == "list":
        c.execute("SELECT * FROM rss")
        k = 0
        for row in c:
            k += 1
            irc.message(event.replyto, "list: " + str(row))
        if k == 0:
            irc.message(event.replyto, "No entries in database")
    else:
        irc.message(event.replyto, "Incorrect parameters specified.")
        c.close()

def announce_rss(irc, channel, name, entry):
    irc.message(channel, "[\002{0}\002] {1} \002{2}\002".format(name, entry.title, entry.link))

def check_rss(irc):
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    c.execute("SELECT * FROM rss")
    if not c.fetchall():
        return
    
    c.execute("SELECT * FROM rss")
    conn_recent = sqlite3.connect('recent_rss.db')
    cursor_recent = conn_recent.cursor()
    cursor_recent.execute("CREATE TABLE IF NOT EXISTS recent ( channel text, site_name text, article_title text, article_url text )")
    conn_recent.commit()
    
    for row in c:
        feed_channel = row[0]
        feed_site_name = row[1]
        feed_url = row[2]
        
        # Giant block of try.. excepts directly ported from jenni!
        try:
            fp = feedparser.parse(feed_url)
        except:
            irc.message(config.logchannel, "Can't parse {0}".format(feed_url))
        
        try:
            entry = fp.entries[0]
        except:
            continue
        
        try:
            article_url = entry.link
        except:
            continue
        
        # only print if new entry
        sql_text = (feed_channel, feed_site_name, entry.title, article_url)
        cursor_recent.execute("SELECT * FROM recent WHERE channel = ? AND site_name = ? and article_title = ? AND article_url = ?", sql_text)
        
        if len(cursor_recent.fetchall()) < 1:
            # Check if this is the first run for this feed
            sql_text = (feed_channel, feed_site_name)
            cursor_recent.execute("SELECT * FROM recent WHERE channel = ? AND site_name = ?", sql_text)
            crfa = cursor_recent.fetchall()
            if len(crfa) < 1: # First run, dump only last entry.
                announce_rss(irc, feed_channel, feed_site_name, entry)
                t = (feed_channel, feed_site_name, i.title, i.link,)
                cursor_recent.execute("INSERT INTO recent VALUES (?, ?, ?, ?)", t)
                conn_recent.commit()
            else: # Not the first entry, find all the entries posted since then and announce em'
                lastposted = []
                for c in crfa:
                    lastposted.append(c[3])
                to_post = []
                for i in fp.entries:
                    if i.link not in lastposted:
                        t = (feed_channel, feed_site_name, i.title, i.link,)
                        cursor_recent.execute("INSERT INTO recent VALUES (?, ?, ?, ?)", t)
                        conn_recent.commit()
                        to_post.append(i)
                        lastposted.append(i.link)
                to_post.reverse()
                for i in to_post:
                    announce_rss(irc, feed_channel, feed_site_name, i)
            
            #cursor_recent.execute("DELETE FROM recent WHERE channel = ? and site_name = ?", sql_text)
            #conn_recent.commit()

            conn_recent.commit()
    
    _firstrun = False
            
            
@startupHook()
def execrss(irc):
    _firstrun = True
    exc = 0
    while True:
        try:
            check_rss(irc)
        except Exception as e:
            tb = repr(e) + traceback.format_exc().splitlines()[-3]
            irc.message(config.logchannel, "Error reading feeds: {0}".format(tb))
            exc += 1
            
        time.sleep(_interval)
        if _stop or exc == 5:
            irc.message(config.logchannel, "RSS stopped.")
            break
