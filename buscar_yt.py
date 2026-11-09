import json, urllib.request
def get(u,h=None):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=h or {"User-Agent":"Mozilla/5.0","accept":"application/dns-json"}),timeout=20).read(200000).decode("utf-8","ignore")
    except Exception as e: return f"ERROR {e!r}"
out=[]
for d in ["bozztv.com","lbgo.bozztv.com","live20.bozztv.com","web13.bozztv.com"]:
    out.append(f"google {d}: {get('https://dns.google/resolve?name='+d+'&type=A')[:300]}")
    out.append(f"cloudflare {d}: {get('https://cloudflare-dns.com/dns-query?name='+d+'&type=A')[:300]}")
r=get("https://rdap.verisign.com/com/v1/domain/bozztv.com",{"User-Agent":"Mozilla/5.0"})
try:
    j=json.loads(r); out.append("RDAP status: "+str(j.get("status"))); out.append("RDAP events: "+str([(e['eventAction'],e['eventDate']) for e in j.get('events',[])])); out.append("RDAP ns: "+str([n['ldhName'] for n in j.get('nameservers',[])]))
except Exception: out.append("RDAP raw: "+r[:500])
open("busqueda_yt.txt","w").write("\n".join(out)+"\n")
