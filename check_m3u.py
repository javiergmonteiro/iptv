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

Uso:  python check_m3u.py [maestra] [salida]
Solo usa la libreria estandar de Python.
"""
import json
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


def main():
    cabecera, canales = parsear(maestra.read_text(encoding="utf-8-sig"))
    try:
        estado = json.loads(estado_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        estado = {}

    with ThreadPoolExecutor(max_workers=10) as ex:
        resultados = list(ex.map(lambda c: probar(c[1]), canales))

    vivos, ocultos, avisos, dudosos = [], [], [], []
    nuevo_estado = {}
    for (extinf, url), (ok, detalle) in zip(canales, resultados):
        if ok is None:
            dudosos.append(f"  [~] {nombre(extinf, url)}  ({detalle})")
            ok = True
        fallos = 0 if ok else estado.get(url, {}).get("fallos", 0) + 1
        nuevo_estado[url] = {"fallos": fallos, "ultimo": detalle}
        n = nombre(extinf, url)
        if fallos >= FALLOS_PARA_OCULTAR:
            ocultos.append(f"  [X] {n}  ({detalle}, {fallos} fallos seguidos)")
        else:
            vivos.append("\n".join(extinf + [url]))
            if not ok:
                avisos.append(f"  [?] {n}  ({detalle}, fallo {fallos}/{FALLOS_PARA_OCULTAR})")

    salida.write_text(cabecera + "\n" + "\n".join(vivos) + "\n", encoding="utf-8")
    estado_path.write_text(json.dumps(nuevo_estado, indent=1, ensure_ascii=False), encoding="utf-8")

    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    informe = [f"Revision {ahora}: {len(vivos)} en la lista, {len(ocultos)} ocultos, {len(canales)} total"]
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
