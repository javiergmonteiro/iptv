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
        r=o.get("lockupViewModel")
        if r and r.get("contentType","").endswith("VIDEO"):
            s=json.dumps(r,ensure_ascii=False)
            if '"LIVE"' in s or "EN VIVO" in s or "viéndolo" in s or "espectadores" in s:
                md=r.get("metadata",{}).get("lockupMetadataViewModel",{})
                tit=md.get("title",{}).get("content","")
                filas=[p.get("text",{}).get("content","") for row in md.get("metadata",{}).get("contentMetadataViewModel",{}).get("metadataRows",[]) for p in row.get("metadataParts",[])]
                out.append((r.get("contentId"),tit," · ".join(filas),""))
    seen=set();res=[]
    for x in out:
        if x[0] not in seen: seen.add(x[0]);res.append(x)
    return res
lines=[]
lines.append("## CONtv /streams")
try:
    for v in vivos(data(get("https://www.youtube.com/@CONtv/streams"))): lines.append(" | ".join(map(str,v)))
except Exception as e: lines.append("ERROR "+repr(e))
for q in ["CONtv en vivo","pokemon en vivo español","pokemon serie 24/7","digimon en vivo","digimon latino 24/7","anime clasico en vivo latino","anime 24/7 español latino","anime en vivo sub español","anime retro 24/7","dragon ball latino en vivo","sailor moon en vivo","caballeros del zodiaco en vivo","naruto en vivo latino","dibujos animados clasicos en vivo","yu-gi-oh en vivo"]:
    u="https://www.youtube.com/results?search_query="+urllib.parse.quote(q)+"&sp=EgJAAQ%253D%253D"
    lines.append("## "+q)
    try:
        for v in vivos(data(get(u)))[:10]: lines.append(" | ".join(map(str,v)))
    except Exception as e: lines.append("ERROR "+repr(e))
open("busqueda_yt.txt","w").write("\n".join(lines)+"\n")
