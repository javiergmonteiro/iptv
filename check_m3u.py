#!/usr/bin/env python3
"""
Revisa una lista M3U y genera una version limpia solo con los canales vivos.

  lista_maestra.m3u  -> la que editas vos (todos los canales, vivos o no)
  lista.m3u          -> la que carga Kodi (solo los que funcionan)
  estado.json        -> cuantas veces seguidas fallo cada canal
  informe.txt        -> resumen legible

Un canal sale de lista.m3u recien despues de FALLOS_PARA_OCULTAR fallos
seguidos (evita sacar canales por un corte momentaneo) y vuelve solo
apenas responde de nuevo.

Canales de YouTube: si el grupo (group-title) contiene "YouTube", en la
maestra va el link del canal (https://www.youtube.com/@canal) o de un
directo (watch?v=...). En cada revision se busca el directo que esta al
aire y en lista.m3u se escribe el link del addon de YouTube de Kodi con
el ID actual, asi sigue andando aunque el canal reinicie la transmision.

Uso:  python check_m3u.py [maestra] [salida]
Solo usa la libreria estandar de Python.
"""
import json
import re
import ssl
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

FALLOS_PARA_OCULTAR = 2
TIMEOUT = 12
# Muchos de estos servidores tienen certificados vencidos y Kodi los
# reproduce igual, asi que no exigimos certificado valido.
SSL_CTX = ssl._create_unverified_context()
UA = "Kodi/21.0 (Windows NT 10.0; Win64; x64) App_Bitness/64 Version/21.0"

base = Path(__file__).resolve().parent
maestra = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "lista_maestra.m3u"
salida = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "lista.m3u"
estado_path = base / "estado.json"
informe_path = base / "informe.txt"


def parsear(texto):
    """Devuelve (cabecera, [(lineas_extinf, url)])."""
    cabecera, canales, pendientes = "#EXTM3U", [], []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("#EXTM3U"):
            cabecera = linea
        elif linea.startswith("#"):
            pendientes.append(linea)
        else:
            canales.append((pendientes, linea))
            pendientes = []
    return cabecera, canales


def nombre(extinf, url):
    for l in extinf:
        if l.startswith("#EXTINF") and "," in l:
            return l.rsplit(",", 1)[1].strip()
    return url


def pedir(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
        return r.status, r.read(65536)


def probar(url_kodi):
    """Acepta la sintaxis de Kodi 'url|Referer=...&User-Agent=...'."""
    url, _, extra = url_kodi.partition("|")
    headers = {"User-Agent": UA}
    for par in filter(None, extra.split("&")):
        k, _, v = par.partition("=")
        headers[k] = urllib.parse.unquote(v)
    try:
        status, cuerpo = pedir(url, headers)
        texto = cuerpo.decode("utf-8", "ignore")
        if ".m3u8" in url.lower() or texto.lstrip().startswith("#EXTM3U"):
            if "#EXTM3U" not in texto:
                return False, f"HTTP {status} pero no es un m3u8"
            # Si es una lista maestra, probar la primera variante tambien
            hijas = [l.strip() for l in texto.splitlines() if l.strip() and not l.startswith("#")]
            if "#EXT-X-STREAM-INF" in texto and hijas:
                s2, c2 = pedir(urljoin(url, hijas[0]), headers)
                if "#EXTM3U" not in c2.decode("utf-8", "ignore"):
                    return False, "variante sin contenido"
        return True, f"HTTP {status}"
    except urllib.error.HTTPError as e:
        if e.code == 403:
            # Suele ser bloqueo por pais (GitHub revisa desde EE.UU.),
            # no que el canal este caido: no lo ocultamos.
            return None, "HTTP 403, posible bloqueo por pais"
        return False, f"HTTP {e.code}"
    except Exception as e:  # timeout, DNS, SSL...
        return False, type(e).__name__


YT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
# Evita la pantalla de "aceptar cookies" que YouTube muestra en Europa.
YT_COOKIE = "CONSENT=YES+1; SOCS=CAI"
YT_PLUGIN = "plugin://plugin.video.youtube/play/?video_id="


def es_youtube(extinf):
    for l in extinf:
        m = re.search(r'group-title="([^"]*)"', l)
        if m and "youtube" in m.group(1).lower():
            return True
    return False


def directo_youtube(url, id_anterior):
    """Devuelve (ok, detalle, video_id) del directo que esta al aire."""
    m = re.search(r"(?:v=|youtu\.be/|/live/)([\w-]{11})(?:[&?/]|$)", url)
    if m and ("watch" in url or "youtu.be" in url or "/live/" in url):
        pagina = f"https://www.youtube.com/watch?v={m.group(1)}"
    else:
        pagina = url.split("?")[0].rstrip("/")
        if not pagina.endswith("/live"):
            pagina += "/live"
    try:
        req = urllib.request.Request(pagina, headers={
            "User-Agent": YT_UA, "Cookie": YT_COOKIE, "Accept-Language": "es"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            html = r.read(3_000_000).decode("utf-8", "ignore")
    except Exception as e:
        # No pudimos preguntar: seguimos con el ultimo ID conocido.
        if id_anterior:
            return None, f"YouTube no respondio ({type(e).__name__}), uso el ultimo ID", id_anterior
        return False, f"YouTube no respondio ({type(e).__name__})", None
    m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([\w-]{11})"', html)
    if not m:
        if "consent.youtube.com" in html or "Sign in to confirm" in html:
            if id_anterior:
                return None, "YouTube pidio verificacion, uso el ultimo ID", id_anterior
            return False, "YouTube pidio verificacion", None
        return False, "no esta transmitiendo en vivo", None
    if '"isLive":true' not in html and '"isLiveNow":true' not in html:
        return False, "el directo termino o todavia no empezo", None
    vid = m.group(1)
    cambio = " (ID nuevo)" if id_anterior and vid != id_anterior else ""
    return True, f"en vivo {vid}{cambio}", vid


def revisar(canal, estado):
    """Devuelve (ok, detalle, url_para_kodi, video_id)."""
    extinf, url = canal
    if es_youtube(extinf) and not url.startswith("plugin://"):
        ok, detalle, vid = directo_youtube(url, estado.get(url, {}).get("video_id"))
        return ok, detalle, (YT_PLUGIN + vid) if vid else url, vid
    if url.startswith("plugin://"):
        return None, "link de addon de Kodi, no se puede revisar", url, None
    ok, detalle = probar(url)
    return ok, detalle, url, None


def main():
    cabecera, canales = parsear(maestra.read_text(encoding="utf-8-sig"))
    try:
        estado = json.loads(estado_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        estado = {}

    with ThreadPoolExecutor(max_workers=10) as ex:
        resultados = list(ex.map(lambda c: revisar(c, estado), canales))

    vivos, ocultos, avisos, dudosos, youtube = [], [], [], [], []
    nuevo_estado = {}
    for (extinf, url), (ok, detalle, url_kodi, vid) in zip(canales, resultados):
        n = nombre(extinf, url)
        if ok is None:
            dudosos.append(f"  [~] {n}  ({detalle})")
            ok = True
        elif vid:
            youtube.append(f"  [YT] {n}  ({detalle})")
        fallos = 0 if ok else estado.get(url, {}).get("fallos", 0) + 1
        nuevo_estado[url] = {"fallos": fallos, "ultimo": detalle}
        if vid:
            nuevo_estado[url]["video_id"] = vid
        elif url in estado and "video_id" in estado[url]:
            nuevo_estado[url]["video_id"] = estado[url]["video_id"]
        if fallos >= FALLOS_PARA_OCULTAR or (not ok and url_kodi == url and es_youtube(extinf)):
            ocultos.append(f"  [X] {n}  ({detalle}, {fallos} fallos seguidos)")
        else:
            vivos.append("\n".join(extinf + [url_kodi]))
            if not ok:
                avisos.append(f"  [?] {n}  ({detalle}, fallo {fallos}/{FALLOS_PARA_OCULTAR})")

    salida.write_text(cabecera + "\n" + "\n".join(vivos) + "\n", encoding="utf-8")
    estado_path.write_text(json.dumps(nuevo_estado, indent=1, ensure_ascii=False), encoding="utf-8")

    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    informe = [f"Revision {ahora}: {len(vivos)} en la lista, {len(ocultos)} ocultos, {len(canales)} total"]
    if youtube:
        informe += ["", "Directos de YouTube:"] + youtube
    if avisos:
        informe += ["", "Fallaron esta vez (siguen en la lista):"] + avisos
    if dudosos:
        informe += ["", "No se pudieron verificar (siguen en la lista):"] + dudosos
    if ocultos:
        informe += ["", "Ocultos (caidos):"] + ocultos
    informe_path.write_text("\n".join(informe) + "\n", encoding="utf-8")
    print("\n".join(informe))


if __name__ == "__main__":
    main()
