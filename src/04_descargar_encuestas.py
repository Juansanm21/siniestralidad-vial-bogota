"""Descarga los archivos de la Encuesta de Percepción de Riesgo Vial (EPRV) 2019 y 2022 del portal de Movilidad.

Fuente: https://datos.movilidadbogota.gov.co (catálogo ArcGIS Hub de la Secretaría Distrital de Movilidad)
Salida: data/raw/encuestas/<archivo original> + _fuentes.csv (título, id del ítem y URL)
"""
import csv
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "encuestas"
OUT.mkdir(parents=True, exist_ok=True)
HUB = "https://datos.movilidadbogota.gov.co/api/search/v1/collections/all/items"

items = {}
for q in ["Encuesta Percepción Riesgo Vial", "EPRV", "Riesgo Vial en Bogota"]:
    for f in requests.get(HUB, params={"q": q, "limit": 50}, timeout=60).json().get("features", []):
        p = f["properties"]
        if "Riesgo Vial" in (p.get("title") or ""):
            items[f["id"]] = p["title"]

filas = []
for iid, titulo in sorted(items.items(), key=lambda x: x[1]):
    meta = requests.get(f"https://www.arcgis.com/sharing/rest/content/items/{iid}", params={"f": "json"}, timeout=60).json()
    nombre = meta.get("name") or f"{iid}.bin"
    url = f"https://www.arcgis.com/sharing/rest/content/items/{iid}/data"
    destino = OUT / nombre
    if not destino.exists():
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        destino.write_bytes(r.content)
    filas.append({"titulo": titulo, "item_id": iid, "archivo": nombre, "url": url, "bytes": destino.stat().st_size})
    print(f"{titulo} -> {nombre} ({destino.stat().st_size / 1e6:.1f} MB)")

with open(OUT / "_fuentes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
