import re, urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
out=[]
for u in ["https://www.youtube.com/@LofiGirl/live","https://www.youtube.com/@aljazeeraenglish/live"]:
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Cookie":"CONSENT=YES+1; SOCS=CAI","Accept-Language":"es"})
    with urllib.request.urlopen(req,timeout=15) as r:
        final=r.geturl(); h=r.read(3_000_000).decode("utf-8","ignore")
    out.append(f"== {u}\nfinal={final} len={len(h)}")
    out += ["canonical: "+m for m in re.findall(r'<link rel="canonical"[^>]*>',h)[:3]]
    for k in ['"isLive":true','"isLiveNow":true','isLiveContent','consent.youtube','Sign in to confirm','"videoId":"','og:url','watch?v=']:
        i=h.find(k); out.append(f"{k}: {'NO' if i<0 else h[max(0,i-60):i+80]!r}")
open("diag_yt.txt","w").write("\n".join(out)+"\n")
