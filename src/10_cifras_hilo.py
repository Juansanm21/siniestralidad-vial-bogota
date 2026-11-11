"""Calcula y muestra las cifras del hilo maestro v2 a partir de data/powerbi (trazabilidad de cada número)."""
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parents[1] / "data" / "powerbi"
v = pd.read_csv(D / "fact_victima.csv", parse_dates=["fecha"])
c = pd.read_csv(D / "res_comparendos_hora.csv")
f = v[v.estado == "Fallecido"]
m = v[v.actor == "Motociclista"]
fm = m[m.estado == "Fallecido"]
noche = lambda d: (d.hora >= 18) | (d.hora <= 5)
dow = f.fecha.dt.dayofweek

print("== Escala humana 2025")
f25, fm25 = f[f.anio == 2025], fm[fm.anio == 2025]
print(f"fallecidos/semana: {len(f25) / 52.14:.1f} | moto/semana: {len(fm25) / 52.14:.1f} | horas por muerte moto: {8760 / len(fm25):.0f}")
vsd = f25[f25.fecha.dt.dayofweek >= 4]
print(f"viernes-domingo: {len(vsd)} ({len(vsd) / len(f25):.0%}) = {len(vsd) / 52.14:.1f} por fin de semana; moto {(vsd.actor == 'Motociclista').sum() / 52.14:.1f}")
print(f"de noche (18-5 h) 2025: todos {noche(f25).mean():.0%} | moto {noche(fm25).mean():.0%} | 2021-25 todos {noche(f[f.anio >= 2021]).mean():.0%} moto {noche(fm[fm.anio >= 2021]).mean():.0%}")
print("moto 0-5 h por año %:", (fm.assign(x=fm.hora <= 5).groupby("anio").x.mean() * 100).round(0).to_dict())
print("moto de noche (18-5) por año %:", (fm.assign(x=noche(fm)).groupby("anio").x.mean() * 100).round(0).to_dict())

print("\n== Miedo vs realidad")
t = f.pivot_table(index="anio", columns="actor", values="id_victima", aggfunc="count")
print(t.loc[[2015, 2022, 2024, 2025]].to_string())
print("moto/ciclista 2022:", round(t.loc[2022, "Motociclista"] / t.loc[2022, "Ciclista"], 1), "| 2025:", round(t.loc[2025, "Motociclista"] / t.loc[2025, "Ciclista"], 1))

print("\n== Letalidad moto (fallecidos por cada 100 víctimas), 2015-2025")
def let(d, by):
    g = d.groupby([by, "estado"]).size().unstack(fill_value=0)
    g["n"] = g.sum(axis=1); g["let"] = (g.Fallecido / g.n * 100).round(2)
    return g
m2 = m.assign(franja=pd.cut(m.hora, [-1, 5, 17, 23], labels=["0-5 h", "6-17 h", "18-23 h"]))
print(let(m2, "franja").to_string())
print(let(m, "contraparte").sort_values("let", ascending=False).to_string())
lc = let(m, "contraparte").let
print("carga vs automóvil:", round(lc["Vehículo de carga"] / lc["Automóvil o taxi"], 1), "x")
print("moto fallecidos con carga como contraparte:", f"{(fm.contraparte == 'Vehículo de carga').mean():.0%}", "| heridos:", f"{(m[m.estado == 'Herido'].contraparte == 'Vehículo de carga').mean():.1%}")
print("letalidad moto por año:", let(m, "anio").let.to_dict())
print("heridos moto:", m[m.estado == "Herido"].groupby("anio").size().to_dict())

print("\n== Control (comparendos 2021)")
tot, vel, cam = c.comparendos.sum(), c.comparendos_velocidad.sum(), c.comparendos_camaras.sum()
n = (c.hora >= 18) | (c.hora <= 5)
print(f"total {tot:,} | velocidad {vel:,} ({vel / tot:.0%}) | cámaras {cam:,}")
print(f"de noche (18-5 h): todos {c[n].comparendos.sum() / tot:.1%} | velocidad {c[n].comparendos_velocidad.sum()} ({c[n].comparendos_velocidad.sum() / vel:.2%}) | cámaras {c[n].comparendos_camaras.sum()}")
f21 = f[f.anio == 2021]
print(f"fallecidos 2021 de noche: {noche(f21).mean():.0%} ({noche(f21).sum()} de {len(f21)})")

print("\n== Hipótesis de velocidad en fallecidos %:", (f[f.anio <= 2024].groupby("anio").con_velocidad.mean() * 100).round(1).to_dict())

print("\n== Lo que está en juego (supuesto: se mantiene el promedio 2021-2025)")
pm, pf = fm[fm.anio >= 2021].groupby("anio").size().mean(), f[f.anio >= 2021].groupby("anio").size().mean()
print(f"promedio anual 2021-25: moto {pm:.0f}, total {pf:.0f} -> 2026-2030: moto {pm * 5:.0f}, total {pf * 5:.0f}")
print("total 2015-2025:", len(f), "| moto:", len(fm))
