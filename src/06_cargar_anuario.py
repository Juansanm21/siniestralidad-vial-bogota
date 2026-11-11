"""Convierte las bases Excel de los anuarios 2024 (histórica) y 2025 a Parquet para analizarlas rápido.

Entrada: data/raw/anuarios/Base_Anuario_de_Siniestralidad_2024.xlsx y Base_Anuario_de_Siniestralidad_Vial_2025_(2).xlsx
Salida : data/raw/anuarios/parquet/{siniestros,vehiculos,actor_vial}_{2024,2025}.parquet
"""
from pathlib import Path

import pandas as pd

A = Path(__file__).resolve().parents[1] / "data" / "raw" / "anuarios"
OUT = A / "parquet"
OUT.mkdir(exist_ok=True)
for archivo, sufijo in [("Base_Anuario_de_Siniestralidad_2024.xlsx", "2024"),
                        ("Base_Anuario_de_Siniestralidad_Vial_2025_(2).xlsx", "2025")]:
    hojas = pd.read_excel(A / archivo, sheet_name=None, engine="openpyxl")
    for nombre, df in hojas.items():
        if nombre.lower().startswith("dicc"):
            df.to_csv(OUT / f"diccionario_{sufijo}.csv", index=False, encoding="utf-8-sig")
            continue
        clave = {"siniestros": "siniestros", "vehiculos": "vehiculos", "vehículos": "vehiculos",
                 "actor_vial": "actor_vial", "actor vial": "actor_vial"}[nombre.lower()]
        df.astype({c: "string" for c in df.columns if df[c].dtype == object}).to_parquet(OUT / f"{clave}_{sufijo}.parquet")
        print(f"{archivo} / {nombre}: {df.shape}")
