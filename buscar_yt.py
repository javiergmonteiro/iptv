import re, json, urllib.request, urllib.parse
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
def get(u):
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Cookie":"CONSENT=YES+1; SOCS=CAI","Accept-Language":"es-419,es"})
    return urllib.request.urlopen(req,timeout=20).read(4_000_000).decode("utf-8","ignore")
def data(h):
    m=re.search(r'var ytInitialData = (\{.*?\});</script>',h,re.S)
    return json.loads(m.group(1)) if m else {}
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
def txt(x):
    if not x: return ""
    if "simpleText" in x: return x["simpleText"]
    return "".join(r.get("text","") for r in x.get("runs",[]))
def vivos(d):
    out=[]
    for o in walk(d):
        r=o.get("videoRenderer")
        if r:
            s=json.dumps(r,ensure_ascii=False)
            if '"style": "LIVE"' in s or "viéndolo" in s or '"BADGE_STYLE_TYPE_LIVE_NOW"' in s:
                out.append((r["videoId"],txt(r.get("title")),txt(r.get("ownerText") or r.get("longBylineText")),txt(r.get("viewCountText"))))
    seen=set();res=[]
    for x in out:
        if x[0] not in seen: seen.add(x[0]);res.append(x)
    return res
lines=[]
for vid in ["cb12KmMMDJA","rZtTUCxpPuI","FEWZjXJ7M0c","iaooxPL8G_I","hw4uHyct4vg","XhAYcYpPzTc","zcWXboTnous","w78Zr0J-dIs","ArKbAx1K-2U"]:
    try:
        h=get("https://www.youtube.com/watch?v="+vid)
        m=re.search(r'"videoOwnerRenderer".{0,3000}?"canonicalBaseUrl":"(/@[^"]+)"',h,re.S)
        handle=m.group(1) if m else "NO"
        lv=get("https://www.youtube.com"+handle+"/live") if m else ""
        m2=re.search(r'"currentVideoEndpoint":\{.{0,600}?"videoId":"([\w-]{11})"',lv,re.S)
        lines.append(f"{vid} -> {handle} -> /live da {m2.group(1) if m2 else 'NO'}")
    except Exception as e: lines.append(f"{vid} ERROR {e!r}")
open("busqueda_yt.txt","w").write("\n".join(lines)+"\n")
