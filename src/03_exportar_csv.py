"""Deja TODAS las tablas originales de siniestros en CSV, listas para abrir y revisar.

Salida: siniestros/datos_csv/<tabla>.csv  (UTF-8 con BOM para que Excel muestre bien las tildes)
- Mismo contenido que entrega el servicio de la Secretaría de Movilidad, sin limpiar.
- Único cambio de formato: las fechas, que vienen en milisegundos desde 1970, se escriben como fecha legible.
- Privacidad: sin PLACA (vehículos) ni FECHA_NACIMIENTO (actor vial).
"""
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "datos_csv"
OUT.mkdir(exist_ok=True)
URL = "https://sig.simur.gov.co/arcgis/rest/services/Accidentalidad/AccidentalidadAnalisis/FeatureServer"
S = requests.Session()

# La tabla de actores viales (capa 3) no se había descargado: se baja ahora sin FECHA_NACIMIENTO
destino_actor = RAW / "actor_vial.parquet"
if not destino_actor.exists():
    campos = ("OBJECTID,FORMULARIO,CODIGO_ACCIDENTADO,FECHA_OCURRENCIA,CODIGO_VICTIMA,CODIGO_VEHICULO,CONDICION,"
              "ESTADO,MUERTE_POSTERIOR,FECHA_POSTERIOR_MUERTE,GENERO,EDAD,CODIGO,CONDICION_A")

    def get(params):
        for i in range(5):
            try:
                j = S.get(f"{URL}/3/query", params=params, timeout=180).json()
                if "error" not in j:
                    return j
            except Exception:
                pass
            time.sleep(2 * (i + 1))
        raise RuntimeError(f"Falló la consulta {params}")

    ids = sorted(get({"where": "1=1", "returnIdsOnly": "true", "f": "json"})["objectIds"])
    bloques = [ids[i:i + 2000] for i in range(0, len(ids), 2000)]
    with ThreadPoolExecutor(8) as ex:
        filas = [f["attributes"] for parte in ex.map(
            lambda b: get({"where": f"OBJECTID>={b[0]} AND OBJECTID<={b[-1]}", "outFields": campos,
                           "returnGeometry": "false", "f": "json"})["features"], bloques) for f in parte]
    pd.DataFrame(filas).to_parquet(destino_actor, index=False)
    print(f"actor_vial descargado: {len(filas):,} filas")

NOMBRES = {"accidente": "1_siniestros", "muerto": "2_fallecidos", "lesionado": "3_lesionados",
           "actor_vial": "4_actores_viales", "vehiculo": "5_vehiculos", "causa": "6_causas", "via": "7_via"}
resumen = []
for raw, nombre in NOMBRES.items():
    df = pd.read_parquet(RAW / f"{raw}.parquet").drop(columns=["PLACA", "FECHA_NACIMIENTO"], errors="ignore")
    for c in [c for c in df.columns if c.startswith("FECHA")]:
        con_hora = c in ("FECHA_HORA_ACC", "FECHA_OCURRENCIA")
        f = pd.to_datetime(df[c], unit="ms", utc=True, errors="coerce")
        f = f.dt.tz_convert("America/Bogota") if con_hora else f
        df[c] = f.dt.strftime("%Y-%m-%d %H:%M" if con_hora else "%Y-%m-%d")
    df.to_csv(OUT / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    mb = (OUT / f"{nombre}.csv").stat().st_size / 1e6
    resumen.append((nombre, len(df), df.shape[1], round(mb, 1)))
    print(f"{nombre}.csv: {len(df):,} filas, {df.shape[1]} columnas, {mb:,.0f} MB")

pd.DataFrame(resumen, columns=["archivo", "filas", "columnas", "MB"]).to_csv(OUT / "0_resumen.csv", index=False,
                                                                            encoding="utf-8-sig")
