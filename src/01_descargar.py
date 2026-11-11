"""Descarga la base oficial de siniestros viales de Bogotá (SIGAT, Secretaría Distrital de Movilidad).

Fuente: servicio ArcGIS público de la SDM
  https://sig.simur.gov.co/arcgis/rest/services/Accidentalidad/AccidentalidadAnalisis/FeatureServer
  (publicado en https://datos.movilidadbogota.gov.co como "Siniestralidad_BD")

Privacidad: NO se descargan PLACA (vehículo) ni FECHA_NACIMIENTO; tampoco la tabla de actores viales completa.
Salida: data/raw/<tabla>.parquet  (datos sin transformar, solo como vienen del servicio)
"""
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

URL = "https://sig.simur.gov.co/arcgis/rest/services/Accidentalidad/AccidentalidadAnalisis/FeatureServer"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
PAGINA = 2000
S = requests.Session()

# capa: (nombre, campos a descargar)
TABLAS = {
    2: ("accidente", "*"),
    0: ("muerto", "*"),
    1: ("lesionado", "*"),
    5: ("vehiculo", "OBJECTID,FORMULARIO,CODIGO_VEHICULO,COD_CLASE,CLASE,SERVICIO,MODALIDAD,ENFUGA,CODIGO"),  # sin PLACA
    4: ("causa", "*"),
    6: ("via", "*"),
}


def get(params, capa, intentos=5):
    for i in range(intentos):
        try:
            r = S.get(f"{URL}/{capa}/query", params=params, timeout=180)
            r.raise_for_status()
            j = r.json()
            if "error" in j:
                raise RuntimeError(j["error"])
            return j
        except Exception as e:  # reintento con espera creciente
            if i == intentos - 1:
                raise
            time.sleep(2 * (i + 1))


def rango_ids(capa):
    try:
        j = get({"where": "1=1", "returnIdsOnly": "true", "f": "json"}, capa, intentos=2)
        ids = sorted(j["objectIds"])
        return [ids[i:i + PAGINA] for i in range(0, len(ids), PAGINA)]
    except Exception:
        # Algunas capas no permiten listar IDs: se recorre por rangos de OBJECTID entre el mínimo y el máximo
        import json
        st = [{"statisticType": t, "onStatisticField": "OBJECTID", "outStatisticFieldName": t} for t in ("min", "max")]
        a = get({"where": "1=1", "outStatistics": json.dumps(st), "f": "json"}, capa)["features"][0]["attributes"]
        a = {k.lower(): v for k, v in a.items()}
        return [[i, i + PAGINA - 1] for i in range(int(a["min"]), int(a["max"]) + 1, PAGINA)]


def bajar_bloque(capa, campos, bloque):
    j = get({"where": f"OBJECTID>={bloque[0]} AND OBJECTID<={bloque[-1]}", "outFields": campos,
             "returnGeometry": "false", "f": "json"}, capa)
    return [f["attributes"] for f in j["features"]]


for capa, (nombre, campos) in TABLAS.items():
    destino = OUT / f"{nombre}.parquet"
    if destino.exists():
        print(f"{nombre}: ya existe, se omite")
        continue
    t0 = time.time()
    bloques = rango_ids(capa)
    with ThreadPoolExecutor(8) as ex:
        filas = [f for parte in ex.map(lambda b: bajar_bloque(capa, campos, b), bloques) for f in parte]
    df = pd.DataFrame(filas)
    df.to_parquet(destino, index=False)
    print(f"{nombre}: {len(df):,} filas, {df.shape[1]} columnas, {time.time() - t0:.0f} s")
