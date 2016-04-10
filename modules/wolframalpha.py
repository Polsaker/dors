from jenni import commandHook
import wolframalpha
import config
client = wolframalpha.Client(config.wolframalpha_apikey)

@commandHook(['wolframalpha', 'wa'], help=".wa <input> -- sends input to wolframalpha and returns results")
def wolframalpha(irc, ev):
    try:
        res = client.query(ev.text)
    except:
        return irc.message(ev.replyto, "Error while querying WolframAlpha")
    
    pods = [x for x in res]
    txtpods = [x.text if x.text else "" for x in pods[:3]]
    # prettifying
    txtpods = [": ".join([l.strip() for l in x.split(" | ")]) for x in txtpods]
    txtpods = ["; ".join([l.strip() for l in x.split("\n")]) for x in txtpods]

    txtpods = list(filter(None, txtpods))
    
    resp = " | ".join(txtpods)
    resp = resp.replace("  ", " ")
    if len(resp) > 400:
        resp = resp[:400] + "…"
    
    irc.message(ev.replyto, resp)
