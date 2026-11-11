"""Límites oficiales de las localidades de Bogotá → GeoJSON listo para mapas (informe y tablero).

Fuente: Datos Abiertos Bogotá, conjunto «Localidad Bogotá D.C.» (Secretaría Distrital de Planeación),
https://datosabiertos.bogota.gov.co/dataset/localidad-bogota-d-c  (archivo loca.json, formato Esri JSON).
Los nombres del archivo traen caracteres dañados (Ñ, tildes), así que se unen por el código oficial de localidad.
Salida: data/powerbi/localidades.geojson  (propiedad "localidad" = mismo nombre que en fact_victima.csv)
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\14_localidades_geo.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CODIGOS = {"01": "Usaquén", "02": "Chapinero", "03": "Santa Fe", "04": "San Cristóbal", "05": "Usme", "06": "Tunjuelito",
           "07": "Bosa", "08": "Kennedy", "09": "Fontibón", "10": "Engativá", "11": "Suba", "12": "Barrios Unidos",
           "13": "Teusaquillo", "14": "Los Mártires", "15": "Antonio Nariño", "16": "Puente Aranda", "17": "La Candelaria",
           "18": "Rafael Uribe Uribe", "19": "Ciudad Bolívar", "20": "Sumapaz"}


def anillo_area(r):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:])) / 2


esri = json.loads((ROOT / "data" / "raw" / "geo" / "loca.json").read_text(encoding="utf-8"))
nombres = set(pd.read_csv(ROOT / "data" / "powerbi" / "dim_localidad.csv").localidad)
feats = []
for f in esri["features"]:
    cod = str(f["attributes"]["LocCodigo"]).zfill(2)
    nombre = CODIGOS[cod]
    if nombre not in nombres:     # p. ej. «La Candelaria» puede figurar como «Candelaria» en los datos
        alt = [n for n in nombres if n.split()[-1] == nombre.split()[-1]]
        nombre = alt[0] if alt else nombre
    anillos = [[[round(x, 5), round(y, 5)] for x, y in r[::2] + [r[-1]]] for r in f["geometry"]["rings"]]
    # Esri: anillos exteriores en sentido horario (área negativa); los interiores (huecos) en sentido contrario
    poligonos = []
    for r in anillos:
        if anillo_area(r) <= 0 or not poligonos:
            poligonos.append([r])
        else:
            poligonos[-1].append(r)
    feats.append({"type": "Feature", "id": nombre,
                  "properties": {"localidad": nombre, "codigo": cod, "area_km2": round(f["attributes"]["LocArea"] / 1e6, 1)},
                  "geometry": {"type": "MultiPolygon", "coordinates": poligonos}})
out = ROOT / "data" / "powerbi" / "localidades.geojson"
out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")
faltan = nombres - {f["id"] for f in feats} - {"Sin información"}
print(f"{len(feats)} localidades · {out.stat().st_size // 1024} KB · sin geometría: {faltan or 'ninguna'}")
