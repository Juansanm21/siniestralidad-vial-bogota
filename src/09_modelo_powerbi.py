"""Genera el modelo estrella (CSV) para Power BI y para el informe en Streamlit.

Fuente: bases oficiales de los Anuarios de Siniestralidad Vial (SDM), 2015-2025, fallecido a 30 días.
Entrada : data/raw/anuarios/parquet/*.parquet  (creados por 06_cargar_anuario.py)
Salida  : data/powerbi/
    fact_victima.csv          1 fila = persona herida o fallecida (no incluye ilesos)
    dim_fecha.csv, dim_hora.csv, dim_localidad.csv, dim_actor.csv
    seg_usuario_localidad.csv tabla de ejemplo para RLS dinámico
    res_comparendos_hora.csv  comparendos 2021 por hora (si existe data/raw/comparendos_2021.parquet)
    res_percepcion_eprv.csv   cifras del informe oficial EPRV 2022
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\09_modelo_powerbi.py
"""
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "raw" / "anuarios" / "parquet"
OUT = ROOT / "data" / "powerbi"
OUT.mkdir(parents=True, exist_ok=True)


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def si(s):
    return s.astype(str).str.upper().eq("SI").astype(int)


def sin_tildes(x):
    return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()


# ---------------------------------------------------------------- unificar 2015-2024 y 2025
ren25 = {"Codigo_Siniestro": "Codigo_Accidente", "FechaSiniestro": "FechaAcc", "AnnoSiniestro": "AnnoAcc",
         "hourSiniestro": "hourAcc", "Fecha_Siniestro": "Fecha_Acc"}
av = pd.concat([pd.read_parquet(P / "actor_vial_2024.parquet"),
                pd.read_parquet(P / "actor_vial_2025.parquet").rename(columns=ren25)], ignore_index=True)
si_ = pd.concat([pd.read_parquet(P / "siniestros_2024.parquet"),
                 pd.read_parquet(P / "siniestros_2025.parquet").rename(columns=ren25)], ignore_index=True)
ve = pd.concat([pd.read_parquet(P / "vehiculos_2024.parquet"),
                pd.read_parquet(P / "vehiculos_2025.parquet").rename(columns=ren25)], ignore_index=True)

av["estado"] = av.Gravedad_Indicador_30d.str.upper().map({"MUERTO": "Fallecido", "HERIDO": "Herido"})
v = av[av.estado.notna()].copy()                      # solo víctimas (sin ilesos)
esp = v.Condicion_Especifica.fillna("")
v["actor"] = np.select([esp.isin(["Motociclista", "Pasajero Motocicleta"]), esp.eq("Peatón"),
                        esp.isin(["Ciclista", "Pasajero Bicicleta"])],
                       ["Motociclista", "Peatón", "Ciclista"], "Ocupante de otro vehículo")
v["localidad"] = v.Localidad.astype("string").str.strip().str.title().str.replace(" De ", " de ").fillna("Sin información")
v["fecha"] = pd.to_datetime(v.FechaAcc).dt.date
v["hora"] = pd.to_numeric(v.hourAcc, errors="coerce").astype("Int64")
v["edad"] = pd.to_numeric(v.Edad, errors="coerce")
v.loc[~v.edad.between(0, 105), "edad"] = np.nan
v["sexo"] = v.Sexo.astype("string").str.title()
for c in ["Con_Carga", "Con_Moto", "Con_Peaton", "Con_Velocidad", "Con_Embriaguez", "Con_Huecos"]:
    v[c.lower()] = si(v[c]) if c in v else np.nan
# 2025 no trae hipótesis de velocidad/embriaguez/huecos: se dejan vacías (no cero)
v.loc[v.AnnoAcc == 2025, ["con_velocidad", "con_embriaguez", "con_huecos"]] = np.nan

# coordenadas del siniestro
si_["lat"], si_["lon"] = num(si_.Latitud), num(si_.Longitud)
ok = si_.lat.between(3.7, 4.85) & si_.lon.between(-74.5, -73.95)
si_.loc[~ok, ["lat", "lon"]] = np.nan
v = v.merge(si_[["Codigo_Accidente", "lat", "lon"]].drop_duplicates("Codigo_Accidente"), on="Codigo_Accidente", how="left")

# contraparte de las víctimas en moto: el vehículo más pesado del siniestro distinto al de la víctima
PRIO = {"CARGA": (0, "Vehículo de carga"), "TRANSPORTE DE PASAJEROS": (1, "Bus"), "SERVICIO ESPECIAL": (1, "Bus"),
        "LIVIANO": (2, "Automóvil o taxi"), "TAXI": (2, "Automóvil o taxi"), "MOTOCICLETA": (3, "Otra moto"),
        "BICICLETA": (4, "Bicicleta")}
ve["tipo"] = ve.Vehiculo_Viajaba_Clasificado.astype(str).str.upper()
ve = ve[ve.tipo.isin(PRIO)]
ve["prio"] = ve.tipo.map(lambda t: PRIO[t][0])
ve["contraparte"] = ve.tipo.map(lambda t: PRIO[t][1])
m = v[v.actor == "Motociclista"][["Codigo_Accidentado", "Codigo_Accidente", "Codigo_Vehiculo"]]
otros = m.merge(ve[["Codigo_Accidente", "Codigo_Vehiculo", "prio", "contraparte"]], on="Codigo_Accidente", suffixes=("", "_o"))
otros = otros[otros.Codigo_Vehiculo != otros.Codigo_Vehiculo_o].sort_values("prio").drop_duplicates("Codigo_Accidentado")
v = v.merge(otros[["Codigo_Accidentado", "contraparte"]], on="Codigo_Accidentado", how="left")
v.loc[(v.actor == "Motociclista") & v.contraparte.isna(), "contraparte"] = "Sin otro vehículo"

fact = v.rename(columns={"Codigo_Accidentado": "id_victima", "Codigo_Accidente": "id_siniestro", "AnnoAcc": "anio"})[
    ["id_victima", "id_siniestro", "fecha", "anio", "hora", "localidad", "actor", "estado", "edad", "sexo",
     "con_carga", "con_moto", "con_peaton", "con_velocidad", "con_embriaguez", "con_huecos", "contraparte", "lat", "lon"]]
fact.to_csv(OUT / "fact_victima.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- dimensiones
MES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
       "Noviembre", "Diciembre"]
DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
f = pd.DataFrame({"fecha": pd.date_range("2015-01-01", "2025-12-31")})
f["anio"], f["mes_num"] = f.fecha.dt.year, f.fecha.dt.month
f["mes"] = f.mes_num.map(lambda i: MES[i - 1])
f["anio_mes"] = f.fecha.dt.strftime("%Y-%m")
f["dia_semana_num"] = f.fecha.dt.dayofweek + 1
f["dia_semana"] = f.dia_semana_num.map(lambda i: DIA[i - 1])
f["fin_de_semana"] = np.where(f.dia_semana_num >= 5, "Viernes a domingo", "Lunes a jueves")
f["fecha"] = f.fecha.dt.date
f.to_csv(OUT / "dim_fecha.csv", index=False, encoding="utf-8-sig")

h = pd.DataFrame({"hora": range(24)})
h["hora_txt"] = h.hora.map(lambda x: f"{x:02d}:00")
h["franja"] = pd.cut(h.hora, [-1, 5, 11, 17, 23], labels=["Madrugada (0-5 h)", "Mañana (6-11 h)", "Tarde (12-17 h)",
                                                         "Noche (18-23 h)"])
h["franja_orden"] = pd.cut(h.hora, [-1, 5, 11, 17, 23], labels=[1, 2, 3, 4])
h["dia_noche"] = np.where(h.hora.between(6, 17), "Día (6-17 h)", "Noche (18-5 h)")
h.to_csv(OUT / "dim_hora.csv", index=False, encoding="utf-8-sig")

loc = pd.DataFrame({"localidad": sorted(fact.localidad.unique())})
loc["localidad_clave"] = loc.localidad.map(lambda x: sin_tildes(x).upper())
# centro de cada localidad = promedio de las coordenadas de sus siniestros (para ubicar la burbuja en el mapa)
centro = fact.groupby("localidad")[["lat", "lon"]].mean().round(5).rename(columns={"lat": "lat_centro", "lon": "lon_centro"})
loc = loc.merge(centro, left_on="localidad", right_index=True, how="left")
pob = ROOT / "data" / "raw" / "poblacion_localidad.csv"   # opcional: localidad_clave, poblacion, fuente
if pob.exists():
    loc = loc.merge(pd.read_csv(pob), on="localidad_clave", how="left")
loc.to_csv(OUT / "dim_localidad.csv", index=False, encoding="utf-8-sig")

pd.DataFrame({"actor": ["Motociclista", "Peatón", "Ciclista", "Ocupante de otro vehículo"], "actor_orden": [1, 2, 3, 4],
              "es_vulnerable": ["Sí", "Sí", "Sí", "No"]}).to_csv(OUT / "dim_actor.csv", index=False, encoding="utf-8-sig")

pd.DataFrame({"correo": ["alcaldia.kennedy@ejemplo.gov.co", "alcaldia.suba@ejemplo.gov.co",
                         "alcaldia.engativa@ejemplo.gov.co", "regional.sur@ejemplo.gov.co", "regional.sur@ejemplo.gov.co"],
              "localidad": ["Kennedy", "Suba", "Engativá", "Bosa", "Ciudad Bolívar"]}).to_csv(
    OUT / "seg_usuario_localidad.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- tablas resumen (no se relacionan con los hechos)
comp = ROOT / "data" / "raw" / "comparendos_2021.parquet"
if comp.exists():
    c = pd.read_parquet(comp)
    c["hora"] = pd.to_numeric(c.HORA_OCURR.str[:2], errors="coerce")
    c["vel"] = c.DES_INFRAC.str.contains("VELOCIDAD", na=False).astype(int)
    c["cam"] = c.MEDIO_DETE.eq("Cámaras Salvavidas").astype(int)
    r = c.groupby("hora").agg(comparendos=("vel", "size"), comparendos_velocidad=("vel", "sum"),
                              comparendos_camaras=("cam", "sum")).reindex(range(24), fill_value=0).reset_index()
    r["anio"] = 2021
    r.to_csv(OUT / "res_comparendos_hora.csv", index=False, encoding="utf-8-sig")

FU = "EPRV 2022, informe oficial SDM"
# grupo: seguridad (por medio), causa (causa frecuente de siniestros), actor_velocidad / actor_irrita (Tabla 1),
# conducta (comportamiento declarado). pagina = página del informe PDF.
pd.DataFrame([
    ("seguridad", "Bicicleta", "Considera nada o poco seguro moverse en bicicleta", 86, 38),
    ("seguridad", "Moto", "Considera nada o poco seguro moverse en moto", 82, 38),
    ("causa", "Alcohol", "Transitar después de haber bebido alcohol", 90, 34),
    ("causa", "Velocidad", "Manejar con exceso de velocidad", 88, 34),
    ("causa", "Huecos", "Mal estado de las vías", 88, 34),
    ("actor_velocidad", "Motociclistas", "Cree que sobrepasan los límites de velocidad", 87.7, 25),
    ("actor_velocidad", "Taxis", "Cree que sobrepasan los límites de velocidad", 86.2, 25),
    ("actor_velocidad", "Buses", "Cree que sobrepasan los límites de velocidad", 78.6, 25),
    ("actor_velocidad", "Particulares", "Cree que sobrepasan los límites de velocidad", 69.1, 25),
    ("actor_velocidad", "Bicitaxis", "Cree que sobrepasan los límites de velocidad", 68.2, 25),
    ("actor_velocidad", "Ciclistas", "Cree que sobrepasan los límites de velocidad", 54.9, 25),
    ("actor_velocidad", "Camiones y pesados", "Cree que sobrepasan los límites de velocidad", 50.9, 25),
    ("actor_irrita", "Motociclistas", "Le molesta o irrita su comportamiento", 74.2, 25),
    ("actor_irrita", "Camiones y pesados", "Le molesta o irrita su comportamiento", 53.5, 25),
    ("conducta", "Los demás, peor", "Cree que los demás conducen de forma más imprudente que él", 78, 24),
    ("conducta", "Vía vacía", "Si la vía está desocupada, conduce a alta velocidad", 27, 26),
    ("conducta", "Multa improbable", "Cree poco probable ser multado por conducir a alta velocidad", 35, 26),
], columns=["grupo", "categoria", "indicador", "porcentaje", "pagina"]).assign(fuente=FU).to_csv(
    OUT / "res_percepcion_eprv.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- validación
fa = fact[fact.estado == "Fallecido"]
print(f"fact_victima: {len(fact):,} filas | fallecidos {len(fa):,} | heridos {(fact.estado == 'Herido').sum():,}")
print("Fallecidos por año:", fa.groupby("anio").size().to_dict())
assert fa[fa.anio == 2025].shape[0] == 562, "2025 debe dar 562 fallecidos (Anuario 2025)"
assert fa[fa.anio == 2015].shape[0] == 530
print("Validación OK: 562 fallecidos en 2025, 530 en 2015")
print("Fallecidos con coordenadas:", f"{fa.lat.notna().mean():.1%}", "| localidades:", fact.localidad.nunique())
