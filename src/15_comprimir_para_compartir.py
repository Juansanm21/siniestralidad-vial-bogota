"""Comprime las 3 tablas consolidadas del Anuario (.csv → .csv.gz) para subirlas a GitHub (límite: 100 MB por archivo).

Power BI las lee comprimidas (Binary.Decompress con GZip), desde la carpeta local o desde GitHub.
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\15_comprimir_para_compartir.py
"""
import gzip
import shutil
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data" / "anuario_consolidado"
for n in ["siniestros", "actor_vial", "vehiculos"]:
    origen, destino = D / f"{n}.csv", D / f"{n}.csv.gz"
    with open(origen, "rb") as fi, gzip.open(destino, "wb", compresslevel=9) as fo:
        shutil.copyfileobj(fi, fo)
    print(f"{n}: {origen.stat().st_size / 1e6:.1f} MB -> {destino.stat().st_size / 1e6:.1f} MB")
