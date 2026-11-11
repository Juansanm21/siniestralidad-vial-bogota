"""Limpia y modela la base de siniestros viales de Bogotá.

Entrada : data/raw/*.parquet (tal como vienen del servicio de la SDM)
Salidas : data/processed/
    dim_fecha.csv, fact_siniestro.csv, fact_victima.csv, fact_vehiculo.csv, fact_causa.csv, fact_via.csv
    reporte_limpieza.csv  (cuántas filas entra/sale en cada paso, para la sustentación)
Cada decisión está documentada en docs/decisiones.md
"""
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
ANIO_MIN, ANIO_MAX = 2015, 2025          # años completos y con el sistema SIGAT actual
BBOX = dict(lat=(3.70, 4.85), lon=(-74.50, -73.95))  # caja que contiene a Bogotá (incluye Sumapaz)
SIN_INFO = {"SIN INFORMACION", "SIN INFORMACIÓN", "NO APLICA", "", "NONE", "NAN", "NULL", "-"}

log = []


def paso(tabla, accion, antes, despues, nota=""):
    log.append({"tabla": tabla, "paso": accion, "filas_antes": antes, "filas_despues": despues,
                "eliminadas": antes - despues, "nota": nota})
    print(f"[{tabla}] {accion}: {antes:,} -> {despues:,}  {nota}")


def texto(s):
    """Mayúsculas, sin tildes, sin espacios dobles; 'SIN INFORMACION' y vacíos -> NaN."""
    s = s.astype("string").str.strip().str.upper()
    s = s.map(lambda v: unicodedata.normalize("NFKD", v).encode("ascii", "ignore").decode() if isinstance(v, str) else v)
    s = s.str.replace(r"\s+", " ", regex=True)
    return s.mask(s.isin(SIN_INFO))


def fecha_ms(s):
    """Las fechas vienen como milisegundos desde 1970 (UTC). Se pasan a hora de Bogotá (UTC-5)."""
    return pd.to_datetime(s, unit="ms", utc=True).dt.tz_convert("America/Bogota").dt.tz_localize(None)


# =========================================================== SINIESTROS (accidente)
a = pd.read_parquet(RAW / "accidente.parquet")
n0 = len(a)
a = a.drop_duplicates(subset=["FORMULARIO"])
paso("siniestro", "quitar duplicados por FORMULARIO", n0, len(a))

a["anio"] = a["ANO_OCURRENCIA_ACC"].astype("Int64")
n0 = len(a)
a = a[a.anio.between(ANIO_MIN, ANIO_MAX)]
paso("siniestro", f"filtrar años {ANIO_MIN}-{ANIO_MAX}", n0, len(a),
     "antes de 2015 hay años casi vacíos (2001-2006); 2026 está incompleto")

# Hasta 2020 cada siniestro aparece DOS veces: una con FORMULARIO 'A…' y otra 'AA…' (mismo número, fecha, hora,
# dirección y gravedad; distinto CODIGO_ACCIDENTE). Se conserva la versión 'AA', que es la que enlaza con causas.
a["prefijo"] = a.FORMULARIO.str.extract(r"^([A-Z]*)")[0]
a["numero"] = a.FORMULARIO.str.replace(r"^[A-Z]+", "", regex=True).str.lstrip("0")
clave = a.numero + "|" + a.FECHA_OCURRENCIA_ACC.astype(str)
tiene_aa = clave.isin(set(clave[a.prefijo == "AA"]))
dup_a = (a.prefijo == "A") & tiene_aa
n0 = len(a)
a = a[~dup_a]
paso("siniestro", "quitar versión 'A' duplicada de siniestros que también existen como 'AA'", n0, len(a),
     "afecta 2015-2020: el sistema guardaba cada informe dos veces")

a["fecha"] = fecha_ms(a["FECHA_OCURRENCIA_ACC"]).dt.normalize()
hora = pd.to_datetime(a["HORA_OCURRENCIA_ACC"].astype("string"), format="%H:%M:%S", errors="coerce")
a["hora"] = hora.dt.hour.astype("Int64")
for c in ["GRAVEDAD", "CLASE_ACC", "LOCALIDAD", "BARRIO", "DIA_OCURRENCIA_ACC", "MVINOMBRE"]:
    a[c] = texto(a[c])
a.loc[a.MVINOMBRE == "SIN_NMG", "MVINOMBRE"] = pd.NA
fuera = ~(a.LATITUD.between(*BBOX["lat"]) & a.LONGITUD.between(*BBOX["lon"]))
a.loc[fuera, ["LATITUD", "LONGITUD"]] = np.nan
paso("siniestro", "coordenadas fuera de Bogotá -> vacías", len(a), len(a), f"{int(fuera.sum()):,} puntos anulados")

DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
a["dia_semana"] = pd.Categorical(a.DIA_OCURRENCIA_ACC, categories=DIAS, ordered=True)
a["fin_de_semana"] = a.DIA_OCURRENCIA_ACC.isin(["SABADO", "DOMINGO"])
a["franja"] = pd.cut(a.hora, [-1, 5, 11, 17, 23], labels=["Madrugada (0-5)", "Mañana (6-11)", "Tarde (12-17)",
                                                       "Noche (18-23)"])
a["gravedad"] = a.GRAVEDAD.replace({"CON MUERTOS": "Con muertos", "CON HERIDOS": "Con heridos",
                                    "SOLO DANOS": "Solo daños"})
sin = fact = a.rename(columns={"FORMULARIO": "formulario", "CODIGO_ACCIDENTE": "codigo_accidente",
                               "CLASE_ACC": "clase", "LOCALIDAD": "localidad", "BARRIO": "barrio",
                               "LATITUD": "lat", "LONGITUD": "lon", "MVINOMBRE": "via_principal",
                               "DIRECCION": "direccion"})
sin = sin[["formulario", "codigo_accidente", "fecha", "anio", "hora", "franja", "dia_semana", "fin_de_semana",
           "gravedad", "clase", "localidad", "barrio", "via_principal", "direccion", "lat", "lon"]]
forms = set(sin.formulario)
cods = set(sin.codigo_accidente.dropna().astype("int64"))

# =========================================================== VÍCTIMAS (muertos + lesionados)
vict = []
for nombre, estado in [("muerto", "Fallecido"), ("lesionado", "Herido")]:
    v = pd.read_parquet(RAW / f"{nombre}.parquet")
    n0 = len(v)
    v = v.drop_duplicates(subset=["CODIGO_ACCIDENTADO"])
    paso(nombre, "quitar duplicados por CODIGO_ACCIDENTADO", n0, len(v))
    n0 = len(v)
    v = v[v.FORMULARIO.isin(forms)]
    paso(nombre, "conservar víctimas de siniestros en el periodo", n0, len(v))
    v["estado"] = estado
    vict.append(v)
v = pd.concat(vict, ignore_index=True)
# Una persona que aparece como herida y luego como fallecida cuenta solo como fallecida
n0 = len(v)
v = v.sort_values("estado").drop_duplicates(subset=["CODIGO_ACCIDENTADO"], keep="first")
paso("victima", "persona en ambas tablas -> se deja como fallecida", n0, len(v))
v["CONDICION"] = v.CONDICION.astype("string").str.replace(r"^ACOMPA.*$", "ACOMPANANTE", regex=True)  # 'ACOMPA¿E': tilde dañada
v["condicion"] = texto(v.CONDICION).replace({"PEATON": "Peatón", "MOTOCICLISTA": "Motociclista",
                                             "CICLISTA": "Ciclista", "CONDUCTOR": "Conductor",
                                             "PASAJERO": "Pasajero", "ACOMPANANTE": "Acompañante"})
v["genero"] = texto(v.GENERO).str.capitalize()
edad = pd.to_numeric(v.EDAD, errors="coerce")
mala = ~edad.between(0, 100)
v["edad"] = edad.mask(mala)
paso("victima", "edades fuera de 0-100 -> vacías", len(v), len(v), f"{int((mala & edad.notna()).sum()):,} corregidas")
v["grupo_edad"] = pd.cut(v.edad, [-1, 17, 28, 39, 59, 120], labels=["0-17", "18-28", "29-39", "40-59", "60+"])
v["muerte_posterior"] = texto(v.get("MUERTE_POSTERIOR", pd.Series(index=v.index, dtype="string"))).eq("S")
vic = v.rename(columns={"FORMULARIO": "formulario", "CODIGO_ACCIDENTADO": "codigo_victima",
                        "CODIGO_VEHICULO": "codigo_vehiculo"})[
    ["codigo_victima", "formulario", "codigo_vehiculo", "estado", "condicion", "genero", "edad", "grupo_edad",
     "muerte_posterior"]]

# =========================================================== VEHÍCULOS
ve = pd.read_parquet(RAW / "vehiculo.parquet")
# Las víctimas del duplicado 'A' ya quedaron fuera porque su FORMULARIO no está en `forms`.
n0 = len(ve)
ve = ve[ve.FORMULARIO.isin(forms)].drop_duplicates(subset=["CODIGO"])
paso("vehiculo", "conservar vehículos del periodo y quitar duplicados", n0, len(ve))
ve["clase"] = texto(ve.CLASE)
GRUPO = {"MOTOCICLETA": "Moto", "MOTOCICLO": "Moto", "CICLOMOTOR": "Moto", "MOTOCARRO": "Moto", "CUATRIMOTO": "Moto",
         "BICICLETA": "Bicicleta", "AUTOMOVIL": "Automóvil", "CAMPERO": "Automóvil", "CAMIONETA": "Automóvil",
         "BUS": "Bus / buseta", "BUSETA": "Bus / buseta", "MICROBUS": "Bus / buseta", "BUS ALIMENTADOR": "Bus / buseta",
         "BUS ARTICULADO": "Bus / buseta", "CAMION, FURGON": "Camión", "CAMION": "Camión", "TRACTOCAMION": "Camión",
         "VOLQUETA": "Camión"}
ve["grupo_vehiculo"] = ve.clase.map(GRUPO).fillna("Otro")
ve["servicio"] = texto(ve.SERVICIO)
ve["en_fuga"] = texto(ve.ENFUGA).eq("S")
veh = ve.rename(columns={"FORMULARIO": "formulario", "CODIGO_VEHICULO": "codigo_vehiculo"})[
    ["formulario", "codigo_vehiculo", "clase", "grupo_vehiculo", "servicio", "en_fuga"]]

# Actor vial homogéneo. Hasta 2020 los motociclistas y ciclistas se registraban como "Conductor"; desde 2021 como
# "Motociclista"/"Ciclista". Para comparar años se clasifica a la víctima por el VEHÍCULO en que iba.
vic = vic.merge(veh[["formulario", "codigo_vehiculo", "grupo_vehiculo"]], on=["formulario", "codigo_vehiculo"],
                how="left")
vic["actor_vial"] = np.select(
    [vic.condicion.eq("Peatón"),
     vic.grupo_vehiculo.eq("Moto") | vic.condicion.eq("Motociclista"),
     vic.grupo_vehiculo.eq("Bicicleta") | vic.condicion.eq("Ciclista")],
    ["Peatón", "Motociclista", "Ciclista"], "Ocupante de otro vehículo")
paso("victima", "actor vial homogéneo según el vehículo de la víctima", len(vic), len(vic),
     f"{int((vic.condicion.eq('Conductor') & vic.actor_vial.isin(['Motociclista', 'Ciclista'])).sum()):,} "
     "'conductores' reclasificados como motociclistas o ciclistas")

# =========================================================== CAUSAS (hipótesis del agente de tránsito)
ca = pd.read_parquet(RAW / "causa.parquet")
n0 = len(ca)
ca = ca[ca.FORMULARIO.isin(forms)].drop_duplicates(subset=["CODIGO"])
paso("causa", "conservar causas del periodo y quitar duplicados", n0, len(ca))
ca["causa"] = texto(ca.NOMBRE)
cau = ca.rename(columns={"FORMULARIO": "formulario", "CODIGO_VEHICULO": "codigo_vehiculo", "TIPO": "tipo"})[
    ["formulario", "codigo_vehiculo", "causa", "tipo"]]

# =========================================================== VÍA
vi = pd.read_parquet(RAW / "via.parquet")
vi["cod"] = pd.to_numeric(vi.CODIGO_ACCIDENTE, errors="coerce").astype("Int64")
n0 = len(vi)
vi = vi[vi.cod.isin(cods) & (vi.ES_PRINCIPAL == 1)].drop_duplicates(subset=["cod"])
paso("via", "conservar vía principal de siniestros del periodo", n0, len(vi),
     "se une por CODIGO_ACCIDENTE: en esta tabla FORMULARIO tiene otro formato")
via = pd.DataFrame({"codigo_accidente": vi.cod, "iluminacion": texto(vi.ILUMINACION_ARTIFICIAL),
                    "estado_via": texto(vi.ESTADO), "condicion_via": texto(vi.CONDICIONES),
                    "semaforo": texto(vi.SEMAFORO), "geometria": texto(vi.GEOMETRICAA)})

# =========================================================== EXPORTAR
sin.to_csv(OUT / "fact_siniestro.csv", index=False, encoding="utf-8")
vic.to_csv(OUT / "fact_victima.csv", index=False, encoding="utf-8")
veh.to_csv(OUT / "fact_vehiculo.csv", index=False, encoding="utf-8")
cau.to_csv(OUT / "fact_causa.csv", index=False, encoding="utf-8")
via.to_csv(OUT / "fact_via.csv", index=False, encoding="utf-8")
pd.DataFrame(log).to_csv(OUT / "reporte_limpieza.csv", index=False, encoding="utf-8")
# Copias en Parquet para que el dashboard cargue rápido (mismo contenido que los CSV)
for nombre, df in [("fact_siniestro", sin), ("fact_victima", vic), ("fact_vehiculo", veh), ("fact_causa", cau),
                   ("fact_via", via)]:
    df.astype({c: "string" for c in df.select_dtypes(["category", "object"]).columns}).to_parquet(
        OUT / f"{nombre}.parquet", index=False)
# Serie cruda de fallecidos (sin limpiar) para mostrar el efecto de la limpieza
m = pd.read_parquet(RAW / "muerto.parquet")
m = m[m.ANO_OCURRENCIA_ACC.between(ANIO_MIN, ANIO_MAX)]
m.groupby(["ANO_OCURRENCIA_ACC", "CONDICION"]).size().rename("fallecidos").reset_index().rename(
    columns={"ANO_OCURRENCIA_ACC": "anio", "CONDICION": "condicion_cruda"}).to_csv(
    OUT / "fallecidos_crudo_por_anio.csv", index=False, encoding="utf-8")

# =========================================================== VALIDACIÓN
print("\nSiniestros por año y gravedad:")
print(sin.pivot_table(index="anio", columns="gravedad", values="formulario", aggfunc="count").to_string())
f = vic[vic.estado == "Fallecido"].merge(sin[["formulario", "anio"]], on="formulario")
print("\nFallecidos por año y condición:")
print(f.pivot_table(index="anio", columns="actor_vial", values="codigo_victima", aggfunc="count", margins=True)
      .to_string())
print("\nCobertura de uniones: siniestros con vehículos", sin.formulario.isin(veh.formulario).mean().round(3),
      "| con víctimas (si gravedad != solo daños):",
      sin[sin.gravedad != "Solo daños"].formulario.isin(vic.formulario).mean().round(3),
      "| siniestros con vía:", sin.codigo_accidente.isin(via.codigo_accidente).mean().round(3),
      "| siniestros con causa:", sin.formulario.isin(cau.formulario).mean().round(3))
