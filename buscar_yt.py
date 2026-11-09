import socket, ssl, urllib.request, time
out=[]
urls=["https://lbgo.bozztv.com/ssh101/ssh101/myevent2025/playlist.m3u8","https://live20.bozztv.com/akamaissh101/ssh101/cartoonclasico/playlist.m3u8","https://183.bozztv.com/giatv/giatv-magicplus/magicplus/playlist.m3u8","https://bozztv.com/","https://ssh101.com/"]
for h in ["lbgo.bozztv.com","live20.bozztv.com","183.bozztv.com","bozztv.com","ssh101.com"]:
    try: out.append(f"DNS {h}: {sorted({a[4][0] for a in socket.getaddrinfo(h,443)})}")
    except Exception as e: out.append(f"DNS {h}: ERROR {e!r}")
for u in urls:
    t=time.time()
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20)
        out.append(f"{u} -> {r.status} {r.read(200)[:120]!r} ({time.time()-t:.1f}s)")
    except urllib.error.HTTPError as e: out.append(f"{u} -> HTTP {e.code}")
    except Exception as e: out.append(f"{u} -> {type(e).__name__}: {getattr(e,'reason',e)!r} ({time.time()-t:.1f}s)")
for u in urls[:2]:
    try:
        ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=20,context=ctx)
        out.append(f"SIN VERIFICAR CERT {u} -> {r.status}")
    except Exception as e: out.append(f"SIN VERIFICAR CERT {u} -> {type(e).__name__}: {getattr(e,'reason',e)!r}")
open("busqueda_yt.txt","w").write("\n".join(out)+"\n")
