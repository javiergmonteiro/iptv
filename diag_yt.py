import re, urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
req=urllib.request.Request("https://www.youtube.com/watch?v=434nAi7ibV4",headers={"User-Agent":UA,"Cookie":"CONSENT=YES+1; SOCS=CAI","Accept-Language":"es"})
h=urllib.request.urlopen(req,timeout=15).read(3_000_000).decode("utf-8","ignore")
out=[]
for k in [r'"author":"([^"]*)"', r'"channelId":"([^"]*)"', r'"ownerProfileUrl":"([^"]*)"', r'"canonicalBaseUrl":"(/@[^"]*)"', r'"isLiveNow":(\w+)', r'"title":"([^"]*)"']:
    m=re.search(k,h); out.append(f"{k} -> {m.group(1) if m else 'NO'}")
open("diag_yt.txt","w").write("\n".join(out)+"\n")
