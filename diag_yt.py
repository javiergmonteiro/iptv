import re, urllib.request
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
out=[]
for v in ["434nAi7ibV4","zpfvKzuCB-k"]:
    req=urllib.request.Request("https://www.youtube.com/watch?v="+v,headers={"User-Agent":UA,"Cookie":"CONSENT=YES+1; SOCS=CAI","Accept-Language":"es"})
    h=urllib.request.urlopen(req,timeout=15).read(3_000_000).decode("utf-8","ignore")
    out.append(f"== {v} len={len(h)}")
    i=h.find('"videoDetails"'); out.append("videoDetails: "+(repr(h[i:i+500]) if i>=0 else "NO"))
    for k in ['"isLiveNow"','"isLive":true','"isLiveContent"','"liveBroadcastDetails"','"playabilityStatus"','"isUpcoming"']:
        j=h.find(k); out.append(f"{k}: "+(repr(h[max(0,j-80):j+160]) if j>=0 else "NO"))
    m=re.search(r'<meta name="title" content="([^"]*)"',h); out.append("meta title: "+(m.group(1) if m else "NO"))
    m=re.search(r'<link itemprop="name" content="([^"]*)"',h); out.append("autor: "+(m.group(1) if m else "NO"))
open("diag_yt.txt","w").write("\n".join(out)+"\n")
