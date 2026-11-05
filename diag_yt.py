import re, urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
out=[]
for u in ["https://www.youtube.com/watch?v=434nAi7ibV4","https://www.youtube.com/@CONtv/live","https://www.youtube.com/@LofiGirl/live"]:
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Cookie":"CONSENT=YES+1; SOCS=CAI","Accept-Language":"es"})
    h=urllib.request.urlopen(req,timeout=15).read(3_000_000).decode("utf-8","ignore")
    out.append(f"== {u}")
    for k in [r'"currentVideoEndpoint":\{.{0,400}?"videoId":"([\w-]{11})"', r'shortlinkUrl" href="https://youtu\.be/([\w-]{11})', r'og:url" content="([^"]*)"', r'"videoDetails":\{"videoId":"([\w-]{11})"', r'"liveIndicatorText":\{"simpleText":"([^"]*)"', r'playerOverlayVideoDetailsRenderer":\{"title":\{"simpleText":"([^"]*)"', r'"playabilityStatus":\{"status":"(\w+)"']:
        m=re.search(k,h,re.S); out.append(f"{k[:40]} -> {m.group(1) if m else 'NO'}")
open("diag_yt.txt","w").write("\n".join(out)+"\n")
