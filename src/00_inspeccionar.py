"""Perfil rápido de las tablas crudas: tamaño, nulos, valores raros. Salida: docs/perfil_datos_crudos.md"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
lineas = ["# Perfil de los datos crudos\n"]
for f in sorted(RAW.glob("*.parquet")):
    df = pd.read_parquet(f)
    lineas.append(f"\n## {f.stem} — {len(df):,} filas × {df.shape[1]} columnas\n")
    lineas.append("| columna | tipo | % nulos | valores distintos | ejemplo |\n|---|---|---|---|---|")
    for c in df.columns:
        s = df[c]
        ej = s.dropna().astype(str).value_counts().index[:3].tolist()
        lineas.append(f"| {c} | {s.dtype} | {s.isna().mean():.1%} | {s.nunique():,} | {', '.join(ej)[:70]} |")
    dup_col = {"accidente": "FORMULARIO", "muerto": "CODIGO_ACCIDENTADO", "lesionado": "CODIGO_ACCIDENTADO",
               "vehiculo": "CODIGO", "causa": "CODIGO", "via": "CODIGO"}.get(f.stem)
    if dup_col:
        lineas.append(f"\nDuplicados por `{dup_col}`: {df[dup_col].duplicated().sum():,}")
    for c in ["GRAVEDAD", "CONDICION", "CLASE", "ANO_OCURRENCIA_ACC"]:
        if c in df:
            lineas.append(f"\n`{c}`: " + ", ".join(f"{k} ({v:,})" for k, v in df[c].value_counts(dropna=False).head(14).items()))
    if "EDAD" in df:
        e = pd.to_numeric(df.EDAD, errors="coerce")
        lineas.append(f"\n`EDAD`: nulos {e.isna().sum():,} · < 0: {(e < 0).sum():,} · > 100: {(e > 100).sum():,} · max {e.max()}")
(ROOT / "docs" / "perfil_datos_crudos.md").write_text("\n".join(lineas), encoding="utf-8")
print("\n".join(l for l in lineas if l.startswith("##") or l.startswith("Dupl") or l.startswith("\n`")))
