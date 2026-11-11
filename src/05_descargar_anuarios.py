"""Descarga los Anuarios de Siniestralidad Vial de Bogotá (PDF + base Excel), 2017-2025.

Fuente: Observatorio de Movilidad de Bogotá — https://observatorio.movilidadbogota.gov.co/publicaciones/anuarios
Salida: data/raw/anuarios/ + _fuentes.csv
"""
import csv
import re
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests

PAG = "https://observatorio.movilidadbogota.gov.co/publicaciones/anuarios"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "anuarios"
OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (proyecto academico)"}

urls = set()
for p in range(0, 3):
    html = requests.get(PAG, params={"page": p}, headers=H, timeout=60).text
    urls |= {urljoin(PAG, u) for u in re.findall(r'href="([^"]+\.(?:pdf|xlsx))"', html)}

# Bases Excel enlazadas en la página (algunas no aparecen en el HTML inicial, se cargan después)
BASE = "https://observatorio.movilidadbogota.gov.co/sites/default/files/"
urls |= {BASE + p for p in [
    "2025-09/SIGAT_ANUARIO_2017_0.xlsx", "2025-09/SIGAT_ANUARIO_2018_0.xlsx", "2025-09/SIGAT_ANUARIO_2019.xlsx",
    "2025-09/SIGAT_ANUARIO_2020.xlsx", "2025-09/SIGAT_ANUARIO_2021.xlsx", "2025-09/SIGAT_ANUARIO_2022.xlsx",
    "2025-09/SIGAT_ANUARIO_2023.xlsx", "2025-09/Base_Anuario_de_Siniestralidad_2024.xlsx"]}

filas = []
for u in sorted(urls):
    nombre = unquote(u.rsplit("/", 1)[1]).replace(" ", "_")
    anio = re.search(r"20\d\d", nombre).group(0)
    destino = OUT / nombre
    if not destino.exists():
        r = requests.get(u, headers=H, timeout=300)
        r.raise_for_status()
        destino.write_bytes(r.content)
    filas.append({"anio": anio, "archivo": nombre, "url": u, "MB": round(destino.stat().st_size / 1e6, 1)})
    print(anio, nombre, filas[-1]["MB"], "MB")

with open(OUT / "_fuentes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["anio", "archivo", "url", "MB"])
    w.writeheader()
    w.writerows(sorted(filas, key=lambda r: r["anio"]))
