"""Consolida las 3 tablas de los Anuarios de Siniestralidad Vial (SDM) en una sola serie 2015-2025.

El Excel del Anuario 2024 trae la historia 2015-2024; el del Anuario 2025 trae solo 2025 y renombra
algunas columnas ("Accidente" -> "Siniestro"). Aquí se unen con los nombres del 2024.
Las columnas que 2025 ya no publica (Con_Velocidad, Con_Embriaguez, Con_Huecos...) quedan vacías en 2025.

Entrada : data/raw/anuarios/parquet/{siniestros,vehiculos,actor_vial}_{2024,2025}.parquet (06_cargar_anuario.py)
Salida  : data/anuario_consolidado/{siniestros,vehiculos,actor_vial}.csv
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\12_consolidar_anuario.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "raw" / "anuarios" / "parquet"
OUT = ROOT / "data" / "anuario_consolidado"
OUT.mkdir(parents=True, exist_ok=True)

REN_2025 = {
    "Codigo_Siniestro": "Codigo_Accidente", "Fecha_Siniestro": "Fecha_Acc", "AA_Siniestro": "AA_Acc",
    "MM_Siniestro": "MM_Acc", "DD_Mes_Siniestro": "DD_Mes_Acc", "Dia_Semana_Siniestro": "Dia_Semana_Acc",
    "Hora_Siniestro": "Hora_Acc", "Min_Siniestro": "Min_Acc", "Clase_Siniestro": "Clase_Acc",
    "AnnoSiniestro": "AnnoAcc", "FechaSiniestro": "FechaAcc", "mesSiniestro": "mesAcc",
    "hourSiniestro": "hourAcc", "minuSiniestro": "minuAcc",
}

for nombre in ["siniestros", "vehiculos", "actor_vial"]:
    a = pd.read_parquet(P / f"{nombre}_2024.parquet").assign(anuario_origen="Anuario 2024")
    b = pd.read_parquet(P / f"{nombre}_2025.parquet").rename(columns=REN_2025).assign(anuario_origen="Anuario 2025")
    # El Anuario 2025 escribe los decimales con coma (4,58 en Latitud/Longitud); se pasan a punto como en 2024
    for c in b.columns:
        if not pd.api.types.is_numeric_dtype(b[c]):
            s = b[c].dropna().astype(str)
            if len(s) and s.str.fullmatch(r"-?\d+,\d+").mean() > 0.9:
                b[c] = pd.to_numeric(b[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    t = pd.concat([a, b], ignore_index=True)
    t = t[list(a.columns) + [c for c in b.columns if c not in a.columns]]
    # Llave única del siniestro: 3 códigos aparecen en ambos anuarios (2024 y 2025) con fechas distintas,
    # y las cifras oficiales los cuentan en los dos años; por eso la llave combina código y anuario.
    t.insert(0, "id_siniestro", t.Codigo_Accidente.astype("Int64").astype(str) + "-" + t.anuario_origen.str[-4:])
    t.to_csv(OUT / f"{nombre}.csv", index=False, encoding="utf-8-sig")
    print(f"{nombre}: {len(a):,} (2015-2024) + {len(b):,} (2025) = {len(t):,} filas, {t.shape[1]} columnas")

# validación contra las cifras oficiales publicadas por la SDM
av = pd.read_csv(OUT / "actor_vial.csv", usecols=["AnnoAcc", "Gravedad_Indicador_30d"], low_memory=False)
muertos = av[av.Gravedad_Indicador_30d.str.upper() == "MUERTO"].groupby("AnnoAcc").size()
print("Fallecidos a 30 días por año:", muertos.to_dict())
assert muertos.loc[2015] == 530 and muertos.loc[2025] == 562, "No coincide con las cifras oficiales"
print("Validación OK: 530 en 2015 y 562 en 2025 (cifras oficiales SDM)")
