import re, urllib.request, collections
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"}
def get(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read(3_000_000).decode("utf-8","ignore")
    except Exception as e: return f"ERROR {e!r}"
out=[]
for u in ["https://ssh101.com/","https://ssh101.com/live/myevent2025","https://v2.ssh101.com/home.php","https://ssh101.com/live/magicplus"]:
    h=get(u)
    out.append(f"== {u} len={len(h)} {h[:80]!r}" if h.startswith("ERROR") else f"== {u} len={len(h)}")
    urls=re.findall(r'https?://[^\s"\'<>\\]+',h)
    dom=collections.Counter(re.sub(r'^https?://([^/]+).*',r'\1',x) for x in urls)
    out.append("dominios: "+", ".join(f"{d}({n})" for d,n in dom.most_common(25)))
    for x in sorted({x for x in urls if '.m3u8' in x or 'hls' in x.lower() or 'stream' in x.lower()})[:15]: out.append("  "+x)
    for m in re.finditer(r'(myevent2025|locomotion)',h,re.I): out.append("  ctx: "+h[max(0,m.start()-150):m.end()+150].replace("\n"," "))
for u in ["https://lbgo.ssh101.com/ssh101/ssh101/myevent2025/playlist.m3u8"]:
    out.append(f"{u} -> {get(u)[:120]!r}")
open("busqueda_yt.txt","w").write("\n".join(out)+"\n")
