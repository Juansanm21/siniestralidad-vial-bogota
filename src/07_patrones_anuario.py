import pandas as pd, numpy as np
pd.set_option("display.width", 250)
P = "siniestros/data/raw/anuarios/parquet/"
a24 = pd.read_parquet(P + "actor_vial_2024.parquet")
a25 = pd.read_parquet(P + "actor_vial_2025.parquet").rename(columns={
    "AnnoSiniestro": "AnnoAcc", "hourSiniestro": "hourAcc", "mesSiniestro": "mesAcc", "Dia_Semana_Siniestro": "Dia_Semana_Acc",
    "Gravedad_Indicador_30d": "Gravedad_Indicador_30d", "Codigo_Siniestro": "Codigo_Accidente"})
av = pd.concat([a24, a25], ignore_index=True)
av["grav"] = av.Gravedad_Indicador_30d.str.upper()
esp = av.Condicion_Especifica.fillna("")
av["actor"] = np.select([esp.isin(["Motociclista", "Pasajero Motocicleta"]), esp.eq("Peatón"),
                         esp.isin(["Ciclista", "Pasajero Bicicleta"])], ["Moto", "Peatón", "Bici"], "Otros")
f = av[av.grav == "MUERTO"]; h = av[av.grav == "HERIDO"]
print("== Fallecidos por año y actor")
t = f.pivot_table(index="AnnoAcc", columns="actor", values="Codigo_Accidentado", aggfunc="count", margins=True)
t["%moto"] = (t.Moto / t.All * 100).round(0)
print(t.to_string())
print("\n== Lesionados moto por año y letalidad moto (muertos/100 víctimas)")
lm = pd.DataFrame({"her": h[h.actor == "Moto"].groupby("AnnoAcc").size(), "mue": f[f.actor == "Moto"].groupby("AnnoAcc").size()})
lm["let"] = (lm.mue / (lm.mue + lm.her) * 100).round(2)
print(lm.T.to_string())
# Banderas en fallecidos (solo hasta 2024: 2025 no trae velocidad/embriaguez/huecos)
print("\n== % de fallecidos en siniestros con cada hipótesis/actor (por año)")
b = {}
for c in ["Con_Velocidad", "Con_Embriaguez", "Con_Huecos", "Con_Carga", "Con_Moto", "Con_Peaton", "Con_Persona_Mayor"]:
    if c in f:
        b[c] = f.groupby("AnnoAcc")[c].apply(lambda s: (s.astype(str).str.upper() == "SI").mean() * 100).round(1)
print(pd.DataFrame(b).T.to_string())
fm = f[f.actor == "Moto"]
print("\n== Motociclistas fallecidos: % en siniestros con carga / velocidad")
print(pd.DataFrame({c: fm.groupby("AnnoAcc")[c].apply(lambda s: (s.astype(str).str.upper() == "SI").mean() * 100).round(1)
                    for c in ["Con_Carga", "Con_Velocidad", "Con_Embriaguez"] if c in fm}).T.to_string())
hr = pd.to_numeric(f.hourAcc, errors="coerce")
f = f.assign(hora=hr)
print("\n== % fallecidos 0-5h y 21-23h por año (todos / moto)")
print(pd.DataFrame({"madrug_todos": f.groupby("AnnoAcc").hora.apply(lambda s: s.between(0, 5).mean() * 100).round(0),
                    "madrug_moto": f[f.actor == "Moto"].groupby("AnnoAcc").hora.apply(lambda s: s.between(0, 5).mean() * 100).round(0),
                    "noche_todos": f.groupby("AnnoAcc").hora.apply(lambda s: s.between(18, 23).mean() * 100).round(0)}).T.to_string())
dia = f.Dia_Semana_Acc.astype(str).str.lower()
f = f.assign(finde=dia.str.contains("vier|sáb|sab|dom"))
print("\n== % fallecidos vie-sáb-dom por año:", f.groupby("AnnoAcc").finde.mean().mul(100).round(0).to_dict())
ed = pd.to_numeric(f.Edad, errors="coerce")
f = f.assign(edad=ed)
print("\n== Edad mediana moto fallecidos:", f[f.actor == "Moto"].groupby("AnnoAcc").edad.median().to_dict())
print("== % peatones fallecidos >=60:", f[f.actor == "Peatón"].groupby("AnnoAcc").edad.apply(lambda s: (s >= 60).mean() * 100).round(0).to_dict())
print("== % moto fallecidos 20-34:", f[f.actor == "Moto"].groupby("AnnoAcc").edad.apply(lambda s: s.between(20, 34).mean() * 100).round(0).to_dict())
# estacionalidad
mes = f.mesAcc.astype(str).str.capitalize()
f = f.assign(mes=mes)
tab = f.pivot_table(index="mes", columns="AnnoAcc", values="Codigo_Accidentado", aggfunc="count")
orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
tab = tab.reindex([m for m in orden if m in tab.index])
print("\n== Fallecidos por mes (índice vs promedio mensual del año, 100 = promedio)")
print((tab / tab.mean() * 100).round(0).to_string())
print("\n== Top 5 localidades por año (fallecidos)")
for y, g in f.groupby("AnnoAcc"):
    print(y, g.Localidad.astype(str).str.upper().value_counts().head(5).index.tolist())
