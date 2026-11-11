"""Genera el tablero de Power BI (PBIP: TMDL + PBIR) a partir de las 3 tablas consolidadas del Anuario 2015-2025.

Modelo  : siniestros (1) -> actor_vial (*), siniestros (1) -> vehiculos (*), Calendario (1) -> siniestros (*)
Páginas : "Tablero de ejemplo" (estilo claro, barra lateral con filtros) y "Mi tablero" (lienzo en blanco).
Entrada : data/anuario_consolidado/*.csv  (src/12_consolidar_anuario.py)
Salida  : powerbi/TableroSiniestros.pbip (+ .SemanticModel y .Report)
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\13_generar_pbip_anuario.py
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "data" / "anuario_consolidado"
OUT = ROOT / "powerbi"
NOMBRE = "TableroSiniestros"
SM, RP = OUT / f"{NOMBRE}.SemanticModel", OUT / f"{NOMBRE}.Report"

# ---------------- paleta clara
FONDO, TARJETA, BORDE = "#F4F6F9", "#FFFFFF", "#E4E7EC"
TEXTO, SUAVE = "#1D2939", "#667085"
NAVY, NAVY_TXT = "#16213A", "#C9D2E3"
ACENTO, PIZARRA, GRIS = "#E8772E", "#8C9BB0", "#C5CDD8"
ROJO, VERDE = "#D92D20", "#079455"
T = "\t"


def gid(*p, n=20):
    return hashlib.md5("|".join(p).encode()).hexdigest()[:n]


def guid(*p):
    return str(uuid.UUID(hashlib.md5(("guid|" + "|".join(p)).encode()).hexdigest()))


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def escribir_json(ruta, obj):
    escribir(ruta, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


if OUT.exists():
    shutil.rmtree(OUT)

# ============================================================ MODELO (TMDL)
TIPOS = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}
S, I, D, F = "string", "int64", "double", "dateTime"


def inferir(archivo):
    """Todas las columnas del CSV con su tipo: Fecha* = fecha; números enteros = int64; decimales = double; resto = texto."""
    import pandas as pd
    d = pd.read_csv(DATOS / archivo, low_memory=False)
    cols = []
    for c in d.columns:
        s = d[c]
        if c.startswith("Fecha"):
            t = F
        elif c == "id_siniestro" or not pd.api.types.is_numeric_dtype(s):
            t = S
        elif pd.api.types.is_float_dtype(s) and not (s.dropna() % 1 == 0).all():
            t = D
        else:
            t = I
        cols.append((c, t))
    return cols


def lectura_csv(archivo, columnas):
    """Pasos M comunes: leer CSV (UTF-8 con BOM), quitar BOM, vacíos a null, tipos y banderas Con_* vacías = "NO"."""
    tipos = ", ".join(f'{{"{c}", {TIPOS[t]}}}' for c, t, *_ in columnas)
    banderas = ", ".join(f'{{"{c}", each if _ = null then "NO" else _, type text}}' for c, *_ in columnas if c.startswith("Con_"))
    return [
        # RutaDatos puede ser una carpeta local o una URL (GitHub): el archivo viene comprimido (.csv.gz)
        f'Binario = if Text.StartsWith(RutaDatos, "http") then Web.Contents(RutaDatos & "{archivo}.gz") '
        f'else File.Contents(RutaDatos & "{archivo}.gz"),',
        'Origen = Csv.Document(Binary.Decompress(Binario, Compression.GZip), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),",
        "SinBOM = Table.TransformColumnNames(Encabezados, each Text.Replace(_, Character.FromNumber(65279), \"\")),",
        'Vacios = Table.TransformColumns(SinBOM, {}, each if _ = "" then null else _),',
        f'Tipos = Table.TransformColumnTypes(Vacios, {{{tipos}}}, "en-US"),',
        f"Banderas = Table.TransformColumns(Tipos, {{{banderas}}}),",
    ]


def tabla(nombre, cols_fuente, cols_nuevas, pasos_m, ultimo, oculta_cols=(), props=None, tabla_extra=""):
    """cols_fuente / cols_nuevas: (nombre, tipo). props: dict columna -> dict de propiedades TMDL."""
    props = props or {}
    lin = [f"table {nombre}", f"{T}lineageTag: {guid(nombre)}"]
    if tabla_extra:
        lin.append(f"{T}{tabla_extra}")
    lin.append("")
    for c, tipo in cols_fuente + cols_nuevas:
        lin += [f"{T}column {c}", f"{T}{T}dataType: {tipo}"]
        for k, v in props.get(c, {}).items():
            lin.append(f"{T}{T}{k}" if v is True else f"{T}{T}{k}: {v}")
        if c in oculta_cols:
            lin.append(f"{T}{T}isHidden")
        lin += [f"{T}{T}summarizeBy: none", f"{T}{T}sourceColumn: {c}", f"{T}{T}lineageTag: {guid(nombre, c)}", ""]
    lin += [f"{T}partition {nombre} = m", f"{T}{T}mode: import", f"{T}{T}source =", f"{T}{T}{T}{T}let"]
    lin += [f"{T}{T}{T}{T}    {p}" for p in pasos_m]
    lin += [f"{T}{T}{T}{T}in", f"{T}{T}{T}{T}    {ultimo}", "", f"{T}annotation PBI_ResultType = Table", ""]
    escribir(SM / "definition" / "tables" / f"{nombre}.tmdl", "\n".join(lin))


# ---- siniestros
cs = inferir("siniestros.csv")
pasos = lectura_csv("siniestros.csv", cs) + [
    'Loc = Table.TransformColumns(Banderas, {{"Localidad", each if _ = null then "Sin información" else Text.Proper(_), type text}}),',
    'HoraTxt = Table.AddColumn(Loc, "hora_txt", each if [Hora_Acc] = null then null else Text.PadStart(Text.From([Hora_Acc]), 2, "0") & " h", type text),',
    'DiaNoche = Table.AddColumn(HoraTxt, "dia_noche", each if [Hora_Acc] = null then "Sin hora" else if [Hora_Acc] <= 5 or [Hora_Acc] >= 18 then "Noche" else "Día", type text),',
    'Franja = Table.AddColumn(DiaNoche, "franja", each if [Hora_Acc] = null then "Sin hora" else if [Hora_Acc] <= 5 then "1 Madrugada (0-5 h)" else if [Hora_Acc] <= 11 then "2 Mañana (6-11 h)" else if [Hora_Acc] <= 17 then "3 Tarde (12-17 h)" else "4 Noche (18-23 h)", type text)',
]
tabla("siniestros", cs, [("hora_txt", S), ("dia_noche", S), ("franja", S)], pasos, "Franja",
      oculta_cols=("Codigo_Accidente",),
      props={"id_siniestro": {"isKey": True}, "Fecha_Acc": {"formatString": "dd/mm/yyyy"},
             "Latitud": {"dataCategory": "Latitude"}, "Longitud": {"dataCategory": "Longitude"}})

# ---- actor_vial
ca = inferir("actor_vial.csv")
pasos = lectura_csv("actor_vial.csv", ca) + [
    'Estado = Table.AddColumn(Banderas, "estado", each let g = Text.Upper(if [Gravedad_Indicador_30d] = null then "" else [Gravedad_Indicador_30d]) in if g = "MUERTO" then "Fallecido" else if g = "HERIDO" then "Herido" else if g = "ILESO" then "Ileso" else "Sin dato", type text),',
    'Actor = Table.AddColumn(Estado, "actor", each let e = if [Condicion_Especifica] = null then "" else [Condicion_Especifica] in if List.Contains({"Motociclista", "Pasajero Motocicleta"}, e) then "Motociclista" else if e = "Peatón" then "Peatón" else if List.Contains({"Ciclista", "Pasajero Bicicleta"}, e) then "Ciclista" else "Ocupante de otro vehículo", type text),',
    'Sexo = Table.TransformColumns(Actor, {{"Sexo", each if _ = null or Text.Upper(_) = "SIN INFORMACION" then "Sin información" else Text.Proper(_), type text}}),',
    'Edad = Table.AddColumn(Sexo, "grupo_edad", each if [Edad] = null then "Sin dato" else if [Edad] < 18 then "0-17" else if [Edad] < 30 then "18-29" else if [Edad] < 45 then "30-44" else if [Edad] < 60 then "45-59" else "60 o más", type text)',
]
tabla("actor_vial", ca, [("estado", S), ("actor", S), ("grupo_edad", S)], pasos, "Edad",
      oculta_cols=("id_siniestro",))

# ---- vehiculos
cv = inferir("vehiculos.csv")
pasos = lectura_csv("vehiculos.csv", cv) + [
    'Grupo = Table.AddColumn(Banderas, "grupo_vehiculo", each let c = Text.Lower(if [Clase] = null then "" else [Clase]) in '
    'if Text.Contains(c, "moto") then "Moto" else if c = "bicicleta" then "Bicicleta" '
    'else if List.Contains({"camion, furgon", "tractocamion", "volqueta"}, c) then "Carga" '
    'else if List.Contains({"bus", "buseta", "microbus"}, c) then "Bus" else if c = "" or c = "no identificado" then "Sin dato" else "Liviano", type text)',
]
tabla("vehiculos", cv, [("grupo_vehiculo", S)], pasos, "Grupo", oculta_cols=("id_siniestro",))

# ---- Calendario (Power Query)
pasos = [
    "Inicio = #date(2015, 1, 1),",
    "Lista = List.Dates(Inicio, Duration.Days(#date(2025, 12, 31) - Inicio) + 1, #duration(1, 0, 0, 0)),",
    'Tabla = Table.TransformColumnTypes(Table.FromList(Lista, Splitter.SplitByNothing(), {"Fecha"}), {{"Fecha", type date}}),',
    'Anio = Table.AddColumn(Tabla, "Año", each Date.Year([Fecha]), Int64.Type),',
    'MesNum = Table.AddColumn(Anio, "MesNum", each Date.Month([Fecha]), Int64.Type),',
    'Mes = Table.AddColumn(MesNum, "Mes", each Text.Proper(Text.Start(Date.ToText([Fecha], "MMMM", "es-CO"), 3)), type text),',
    'DiaNum = Table.AddColumn(Mes, "DiaSemanaNum", each Date.DayOfWeek([Fecha], Day.Monday) + 1, Int64.Type),',
    'Dia = Table.AddColumn(DiaNum, "DiaSemana", each Text.Proper(Date.ToText([Fecha], "dddd", "es-CO")), type text),',
    'Finde = Table.AddColumn(Dia, "FinDeSemana", each if [DiaSemanaNum] >= 5 then "Viernes a domingo" else "Lunes a jueves", type text)',
]
tabla("Calendario", [], [("Fecha", F), ("Año", I), ("MesNum", I), ("Mes", S), ("DiaSemanaNum", I), ("DiaSemana", S),
                         ("FinDeSemana", S)], pasos, "Finde", oculta_cols=("MesNum", "DiaSemanaNum"),
      props={"Fecha": {"isKey": True, "formatString": "dd/mm/yyyy"}, "Mes": {"sortByColumn": "MesNum"},
             "DiaSemana": {"sortByColumn": "DiaSemanaNum"}}, tabla_extra="dataCategory: Time")

# ---- Meta (parámetro que elige el usuario): % de reducción frente al año anterior
tabla("Meta", [], [("Reduccion", I)],
      ['Lista = {0, 5, 10, 15, 20, 25, 30},',
       'Tabla = Table.FromList(Lista, Splitter.SplitByNothing(), {"Reduccion"}),',
       'Tipos = Table.TransformColumnTypes(Tabla, {{"Reduccion", Int64.Type}})'], "Tipos",
      props={"Reduccion": {"formatString": '0"%"'}})

# ---- Medidas
QF = "REMOVEFILTERS(Calendario)"
MOTO = 'actor_vial[actor] = "Motociclista"'
M = [
    ("1 Base", "Fallecidos", 'CALCULATE(COUNTROWS(actor_vial), actor_vial[estado] = "Fallecido")', "#,0"),
    ("1 Base", "Lesionados", 'CALCULATE(COUNTROWS(actor_vial), actor_vial[estado] = "Herido")', "#,0"),
    ("1 Base", "Víctimas", "[Fallecidos] + [Lesionados]", "#,0"),
    ("1 Base", "Siniestros", "COUNTROWS(siniestros)", "#,0"),
    ("1 Base", "Fallecidos AA", f"CALCULATE([Fallecidos], SAMEPERIODLASTYEAR(Calendario[Fecha]), {QF})", "#,0"),
    ("1 Base", "Lesionados AA", f"CALCULATE([Lesionados], SAMEPERIODLASTYEAR(Calendario[Fecha]), {QF})", "#,0"),
    ("1 Base", "Var Fallecidos", "DIVIDE([Fallecidos] - [Fallecidos AA], [Fallecidos AA])", "+0.0%;-0.0%;0.0%"),
    ("1 Base", "Var Lesionados", "DIVIDE([Lesionados] - [Lesionados AA], [Lesionados AA])", "+0.0%;-0.0%;0.0%"),
    ("1 Base", "Fallecidos por semana", "DIVIDE([Fallecidos], DIVIDE(COUNTROWS(Calendario), 7))", "0.0"),
    ("2 Indicadores", "% Motociclistas", f"DIVIDE(CALCULATE([Fallecidos], {MOTO}), [Fallecidos])", "0.0%"),
    ("2 Indicadores", "% De noche", 'DIVIDE(CALCULATE([Fallecidos], siniestros[dia_noche] = "Noche"), [Fallecidos])', "0.0%"),
    ("2 Indicadores", "% Con carga", 'DIVIDE(CALCULATE([Fallecidos], actor_vial[Con_Carga] = "SI"), [Fallecidos])', "0.0%"),
    ("2 Indicadores", "% Moto madrugada",
     f"DIVIDE(CALCULATE([Fallecidos], {MOTO}, siniestros[Hora_Acc] <= 5), CALCULATE([Fallecidos], {MOTO}))", "0.0%"),
    ("2 Indicadores", "Letalidad", "DIVIDE([Fallecidos], [Víctimas]) * 100", "0.00"),
    ("2 Indicadores", "Letalidad moto", f"CALCULATE([Letalidad], {MOTO})", "0.00"),
    ("2 Indicadores", "Letalidad noche", 'CALCULATE([Letalidad], siniestros[dia_noche] = "Noche")', "0.00"),
    ("2 Indicadores", "Letalidad día", 'CALCULATE([Letalidad], siniestros[dia_noche] = "Día")', "0.00"),
]
for b in ["% Motociclistas", "% De noche", "% Con carga", "Letalidad moto"]:
    M.append(("3 Año anterior", f"{b} AA", f"CALCULATE([{b}], SAMEPERIODLASTYEAR(Calendario[Fecha]), {QF})",
              "0.00" if b.startswith("Letalidad") else "0.0%"))


def txt_var(base, pp):
    if pp:
        f = 100 if base.startswith("%") else 1
        u = " pp" if base.startswith("%") else ""
        cuerpo = (f"VAR aa = [{base} AA]\nVAR d = ([{base}] - aa) * {f}\n"
                  f'RETURN IF(ISBLANK(aa) || ISBLANK([{base}]), "Sin año anterior", '
                  f'IF(d > 0, "▲ ", "▼ ") & FORMAT(ABS(d), "0.0") & "{u} vs año anterior")')
    else:
        cuerpo = (f"VAR aa = [{base} AA]\nVAR v = [Var {base}]\n"
                  f'RETURN IF(ISBLANK(aa), "Sin año anterior", IF(v > 0, "▲ ", "▼ ") & FORMAT(ABS(v), "0.0%") & " vs año anterior")')
    color = f'VAR aa = [{base} AA]\nRETURN IF(ISBLANK(aa), "{SUAVE}", IF([{base}] > aa, "{ROJO}", "{VERDE}"))'
    return [("4 Textos y colores", f"Txt {base}", cuerpo, None), ("4 Textos y colores", f"Color Txt {base}", color, None)]


KPIS = [("Fallecidos", False), ("Lesionados", False), ("% Motociclistas", True), ("% De noche", True),
        ("% Con carga", True), ("Letalidad moto", True)]
for b, pp in KPIS:
    M += txt_var(b, pp)

# ---- Estado de cada indicador frente a la meta (semáforo de monitoreo)
#  1 = cumple la meta · 2 = mejora pero no cumple · 3 = empeora · 0 = sin año anterior para comparar
AMBAR = "#F79009"
M.append(("6 Meta y estado", "Meta reducción", "SELECTEDVALUE(Meta[Reduccion], 10) / 100", "0%"))


def estado(base, nombre=None):
    n = nombre or base
    return [
        ("6 Meta y estado", f"Meta {n}", f"[{base} AA] * (1 - [Meta reducción])", None),
        ("6 Meta y estado", f"Estado {n}",
         f"VAR aa = [{base} AA]\nVAR x = [{base}]\n"
         f"RETURN IF(ISBLANK(aa) || ISBLANK(x), 0, IF(x <= aa * (1 - [Meta reducción]), 1, IF(x <= aa, 2, 3)))", "0"),
        ("6 Meta y estado", f"Txt estado {n}",
         f'SWITCH([Estado {n}], 1, "● Cumple la meta", 2, "● Mejora, sin cumplir la meta", 3, "● Empeora frente al año anterior", '
         f'"● Sin año anterior para comparar")', None),
        ("6 Meta y estado", f"Fondo estado {n}",
         f'SWITCH([Estado {n}], 1, "#DCFAE6", 2, "#FEF0C7", 3, "#FEE4E2", "#F2F4F7")', None),
        ("6 Meta y estado", f"Texto estado {n}",
         f'SWITCH([Estado {n}], 1, "#067647", 2, "#B54708", 3, "#B42318", "{SUAVE}")', None),
    ]


for b, _ in KPIS:
    M += estado(b)
M += estado("Fallecidos", "localidad")
LOC = "siniestros[Localidad]"
M += [
    ("4 Textos y colores", "Color variación localidad",
     f'SWITCH([Estado localidad], 1, "{VERDE}", 2, "{AMBAR}", 3, "{ROJO}", "{PIZARRA}")', None),
    ("4 Textos y colores", "Titulo",
     'VAR loc = IF(ISFILTERED(siniestros[Localidad]), SELECTEDVALUE(siniestros[Localidad], "varias localidades"), "Bogotá")\n'
     'VAR act = IF(ISFILTERED(actor_vial[actor]), SELECTEDVALUE(actor_vial[actor], "varios actores"), "todas las víctimas")\n'
     'VAR an = IF(ISFILTERED(Calendario[Año]), SELECTEDVALUE(Calendario[Año], "varios años") & "", "2015-2025")\n'
     'VAR corte = CALCULATE(MAX(siniestros[Fecha_Acc]), REMOVEFILTERS())\n'
     'RETURN loc & " · " & an & " · " & act & "  |  datos al " & FORMAT(corte, "dd/mm/yyyy")', None),
    ("5 Lectura ejecutiva", "Top localidad",
     f"VAR t = TOPN(1, FILTER(VALUES({LOC}), NOT ISBLANK([Fallecidos])), [Fallecidos], DESC)\nRETURN CONCATENATEX(t, {LOC}, \", \")", None),
    ("5 Lectura ejecutiva", "Top localidad detalle",
     f"VAR loc = [Top localidad]\nVAR f = CALCULATE([Fallecidos], {LOC} = loc)\nVAR n = CALCULATE([% De noche], {LOC} = loc)\n"
     'RETURN FORMAT(f, "#,0") & " fallecidos · " & FORMAT(n, "0%") & " de noche"', None),
    ("5 Lectura ejecutiva", "Mayor aumento",
     f"VAR t = TOPN(1, FILTER(VALUES({LOC}), [Fallecidos AA] >= 5 && [Fallecidos] > [Fallecidos AA]), [Fallecidos] - [Fallecidos AA], DESC)\n"
     f'RETURN IF(COUNTROWS(t) = 0, "Ninguna localidad aumentó", CONCATENATEX(t, {LOC}, ", "))', None),
    ("5 Lectura ejecutiva", "Mayor aumento detalle",
     f"VAR loc = [Mayor aumento]\nVAR f = CALCULATE([Fallecidos], {LOC} = loc)\nVAR aa = CALCULATE([Fallecidos AA], {LOC} = loc)\n"
     'RETURN IF(ISBLANK(aa), "Elige un año para comparar", "De " & FORMAT(aa, "#,0") & " a " & FORMAT(f, "#,0") & " fallecidos frente al año anterior")', None),
    ("5 Lectura ejecutiva", "Mayor reducción",
     f"VAR t = TOPN(1, FILTER(VALUES({LOC}), [Fallecidos AA] >= 5 && [Fallecidos] < [Fallecidos AA]), [Fallecidos AA] - [Fallecidos], DESC)\n"
     f'RETURN IF(COUNTROWS(t) = 0, "Ninguna localidad bajó", CONCATENATEX(t, {LOC}, ", "))', None),
    ("5 Lectura ejecutiva", "Mayor reducción detalle",
     f"VAR loc = [Mayor reducción]\nVAR f = CALCULATE([Fallecidos], {LOC} = loc)\nVAR aa = CALCULATE([Fallecidos AA], {LOC} = loc)\n"
     'RETURN IF(ISBLANK(aa), "Elige un año para comparar", "De " & FORMAT(aa, "#,0") & " a " & FORMAT(f, "#,0") & " fallecidos frente al año anterior")', None),
    ("5 Lectura ejecutiva", "Hora crítica",
     'VAR t = TOPN(1, FILTER(VALUES(siniestros[hora_txt]), NOT ISBLANK(siniestros[hora_txt]) && NOT ISBLANK([Fallecidos])), [Fallecidos], DESC)\n'
     'RETURN CONCATENATEX(t, siniestros[hora_txt], ", ")', None),
    ("5 Lectura ejecutiva", "Hora crítica detalle",
     'RETURN "De noche mueren " & FORMAT([Letalidad noche], "0.0") & " de cada 100 víctimas; de día, " & FORMAT([Letalidad día], "0.0")'
     .replace("RETURN ", "", 1), None),
    ("4 Textos y colores", "Color hora",
     f'VAR h = SELECTEDVALUE(siniestros[Hora_Acc])\nRETURN IF(ISBLANK(h), "{GRIS}", IF(h <= 5 || h >= 18, "{ACENTO}", "{GRIS}"))', None),
    ("4 Textos y colores", "Color actor", f'IF(SELECTEDVALUE(actor_vial[actor]) = "Motociclista", "{ACENTO}", "{GRIS}")', None),
    ("4 Textos y colores", "Color vehículo",
     f'IF(SELECTEDVALUE(vehiculos[Vehiculo_Viajaba_Clasificado]) = "CARGA", "{ACENTO}", "{GRIS}")', None),
    ("2 Indicadores", "% Siniestros mortales",
     'DIVIDE(CALCULATE(DISTINCTCOUNT(vehiculos[id_siniestro]), siniestros[Gravedad_indicador_30d] = "Con Muertos"),\n'
     '       CALCULATE(DISTINCTCOUNT(vehiculos[id_siniestro]), siniestros[Gravedad_indicador_30d] IN {"Con Muertos", "Con Heridos"}))', "0.0%"),
    ("4 Textos y colores", "Titulo ficha",
     'VAR loc = IF(HASONEVALUE(siniestros[Localidad]), VALUES(siniestros[Localidad]), "Elige una localidad")\n'
     'VAR an = IF(HASONEVALUE(Calendario[Año]), VALUES(Calendario[Año]) & "", "2015-2025")\n'
     'RETURN "Ficha de localidad · " & loc & " · " & an', None),
]


def nom(n):
    return n if n.replace("_", "").isalnum() else "'" + n.replace("'", "''") + "'"


lin = ["table Medidas", f"{T}lineageTag: {guid('Medidas')}", ""]
for carpeta, n, expr, fmt in M:
    if "\n" in expr:
        lin.append(f"{T}measure {nom(n)} =")
        lin += [f"{T}{T}{T}{x}" for x in expr.split("\n")]
    else:
        lin.append(f"{T}measure {nom(n)} = {expr}")
    if fmt:
        lin.append(f"{T}{T}formatString: {fmt}")
    lin += [f"{T}{T}displayFolder: {carpeta}", f"{T}{T}lineageTag: {guid('m', n)}", ""]
lin += [f"{T}partition Medidas = m", f"{T}{T}mode: import", f"{T}{T}source =", f"{T}{T}{T}{T}let",
        f'{T}{T}{T}{T}    Origen = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Columna1 = _t]),',
        f'{T}{T}{T}{T}    Quitada = Table.RemoveColumns(Origen, {{"Columna1"}})',
        f"{T}{T}{T}{T}in", f"{T}{T}{T}{T}    Quitada", "", f"{T}annotation PBI_ResultType = Table", ""]
escribir(SM / "definition" / "tables" / "Medidas.tmdl", "\n".join(lin))

# RUTA_DATOS (variable de entorno) = URL base en GitHub para que cualquiera abra el tablero sin configurar nada;
# si no se define, se usa la carpeta local.
import os
RUTA = os.environ.get("RUTA_DATOS") or f"{DATOS.resolve()}\\"
escribir(SM / "definition" / "expressions.tmdl",
         f'expression RutaDatos = "{RUTA}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
         f"{T}lineageTag: {guid('RutaDatos')}\n\n{T}annotation PBI_ResultType = Text\n")
orden = ["RutaDatos", "Calendario", "siniestros", "actor_vial", "vehiculos", "Meta", "Medidas"]
escribir(SM / "definition" / "database.tmdl", f"database {NOMBRE}\n\tcompatibilityLevel: 1600\n")
escribir(SM / "definition" / "model.tmdl",
         "model Model\n\tculture: es-CO\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: es-CO\n"
         "\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
         f"annotation PBI_QueryOrder = {json.dumps(orden, ensure_ascii=False)}\n\n"
         'annotation PBI_ProTooling = ["DevMode","TMDLView_Desktop"]\n\n'
         + "".join(f"ref table {t}\n" for t in orden[1:]) + "\n"
         + "".join(f"ref role {r}\n" for r in ["Direccion", "Alcaldia_Kennedy"]))
rels = [("siniestros", "Fecha_Acc", "Calendario", "Fecha"), ("actor_vial", "id_siniestro", "siniestros", "id_siniestro"),
        ("vehiculos", "id_siniestro", "siniestros", "id_siniestro")]
# actor_vial <-> siniestros en ambas direcciones: así los filtros de actor vial y sexo llegan también a siniestros
# (mapa, conteo de siniestros) y desde ahí a vehiculos. Sin esto, esos visuales ignoraban esos filtros.
AMBAS = {"actor_vial": "\tcrossFilteringBehavior: bothDirections\n"}
escribir(SM / "definition" / "relationships.tmdl", "\n".join(
    f"relationship {guid('rel', a, b)}\n{AMBAS.get(a, '')}\tfromColumn: {a}.{ca_}\n\ttoColumn: {b}.{cb}\n" for a, ca_, b, cb in rels))
escribir(SM / "definition" / "roles" / "Direccion.tmdl", "role Direccion\n\tmodelPermission: read\n")
escribir(SM / "definition" / "roles" / "Alcaldia_Kennedy.tmdl",
         'role Alcaldia_Kennedy\n\tmodelPermission: read\n\n\ttablePermission siniestros = [Localidad] == "Kennedy"\n')
escribir_json(SM / "definition.pbism", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}})
escribir_json(SM / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": NOMBRE}, "config": {"version": "2.0", "logicalId": guid("sm2")}})

# ============================================================ REPORTE (PBIR)
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def color(c):
    return {"solid": {"color": lit(f"'{c}'")}}


def color_med(m):
    return {"solid": {"color": {"expr": med(m)}}}


def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def med(n):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": n}}


def proy(campo, activo=False):
    k = "Column" if "Column" in campo else "Measure"
    e, p = campo[k]["Expression"]["SourceRef"]["Entity"], campo[k]["Property"]
    r = {"field": campo, "queryRef": f"{e}.{p}", "nativeQueryRef": p}
    if activo:
        r["active"] = True
    return r


def sin_fondo():
    return {"background": [{"properties": {"show": lit("false")}}], "border": [{"properties": {"show": lit("false")}}]}


def titulo(texto, sub=None):
    t = {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{texto}'"), "fontColor": color(TEXTO),
                                   "fontSize": lit("12D"), "bold": lit("true")}}]}
    if sub:
        t["subTitle"] = [{"properties": {"show": lit("true"), "text": lit(f"'{sub}'"), "fontColor": color(SUAVE),
                                         "fontSize": lit("9D")}}]
    return t


def texto(parrafos, fondo=None, borde=None):
    vco = {"background": [{"properties": {"show": lit("true" if fondo else "false"), **({"color": color(fondo), "transparency": lit("0D")} if fondo else {})}}],
           "border": [{"properties": {"show": lit("true" if borde else "false"), **({"color": color(borde), "radius": lit("10D")} if borde else {})}}]}
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": c, "fontFamily": "Segoe UI",
                                                 **({"fontWeight": "bold"} if b else {})}}]} for t, s, c, b in parrafos]}}]},
            "visualContainerObjects": vco}


def tarjeta(medida, tam, color_txt=TEXTO, color_medida=None, negrita=True):
    lab = {"fontSize": lit(f"{tam}D"), "bold": lit("true" if negrita else "false"),
           "color": color_med(color_medida) if color_medida else color(color_txt)}
    return {"visualType": "card", "query": {"queryState": {"Values": {"projections": [proy(med(medida))]}}},
            "objects": {"labels": [{"properties": lab}], "categoryLabels": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": sin_fondo(), "drillFilterOtherVisuals": True}


def chispa(medida, c):
    obj = {"dataPoint": [{"properties": {"fill": color(c)}}],
           "categoryAxis": [{"properties": {"show": lit("false")}}], "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "legend": [{"properties": {"show": lit("false")}}], "lineStyles": [{"properties": {"strokeWidth": lit("2D")}}]}
    q = {"queryState": {"Category": {"projections": [proy(col("Calendario", "Mes"), True)]}, "Y": {"projections": [proy(med(medida))]}},
         "sortDefinition": {"sort": [{"field": col("Calendario", "Mes"), "direction": "Ascending"}]}}
    vco = sin_fondo()
    vco["title"] = [{"properties": {"show": lit("false")}}]
    return {"visualType": "lineChart", "query": q, "objects": obj, "visualContainerObjects": vco, "drillFilterOtherVisuals": True}


def segmentador(tabla_, columna, rotulo, inicial=None, unico=False):
    obj = {"data": [{"properties": {"mode": lit("'Dropdown'")}}],
           "header": [{"properties": {"show": lit("true"), "text": lit(f"'{rotulo}'"), "fontColor": color(NAVY_TXT), "textSize": lit("10D")}}],
           "items": [{"properties": {"fontColor": color(TEXTO), "background": color(TARJETA), "textSize": lit("10D")}}],
           "selection": [{"properties": {"singleSelect": lit("true" if unico else "false"),
                                         "selectAllCheckboxEnabled": lit("false" if unico else "true")}}]}
    if inicial is not None:
        obj["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "s", "Entity": tabla_, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": columna}}],
                                            "Values": [[{"Literal": {"Value": inicial}}]]}}}]}}}}]
    return {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [proy(col(tabla_, columna), True)]}}},
            "objects": obj, "visualContainerObjects": sin_fondo(), "drillFilterOtherVisuals": True}


def barras_loc():
    q = {"queryState": {"Category": {"projections": [proy(col("siniestros", "Localidad"), True)]},
                        "Y": {"projections": [proy(med("Fallecidos"))]}},
         "sortDefinition": {"sort": [{"field": med("Fallecidos"), "direction": "Descending"}], "isDefaultSort": True}}
    obj = {"dataPoint": [{"properties": {"fill": color_med("Color variación localidad")},
                          "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}],
           "labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("8D")}}],
           "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE), "fontSize": lit("8D"), "axisType": lit("'Categorical'")}}]}
    return {"visualType": "clusteredColumnChart", "query": q, "objects": obj,
            "visualContainerObjects": titulo("Fallecidos por localidad", "Verde cumple la meta · ámbar mejora sin cumplirla · rojo sube frente al año anterior"),
            "drillFilterOtherVisuals": True}


def dona():
    q = {"queryState": {"Category": {"projections": [proy(col("actor_vial", "actor"), True)]},
                        "Y": {"projections": [proy(med("Fallecidos"))]}},
         "sortDefinition": {"sort": [{"field": med("Fallecidos"), "direction": "Descending"}], "isDefaultSort": True}}
    obj = {"legend": [{"properties": {"show": lit("true"), "position": lit("'Right'"), "labelColor": color(SUAVE)}}],
           "labels": [{"properties": {"show": lit("true"), "color": color(TEXTO)}}],
           "slices": [{"properties": {"innerRadiusRatio": lit("62L")}}]}
    return {"visualType": "donutChart", "query": q, "objects": obj,
            "visualContainerObjects": titulo("¿Quiénes mueren en las vías?", "Fallecidos por actor vial · clic en una porción para filtrar"),
            "drillFilterOtherVisuals": True}


def combo():
    mes = col("Calendario", "Mes")
    q = {"queryState": {"Category": {"projections": [proy(mes, True)]}, "Y": {"projections": [proy(med("Fallecidos"))]},
                        "Y2": {"projections": [proy(med("Fallecidos AA"))]}},
         "sortDefinition": {"sort": [{"field": mes, "direction": "Ascending"}]}}
    obj = {"dataPoint": [{"properties": {"fill": color(PIZARRA)}, "selector": {"metadata": "Medidas.Fallecidos"}},
                         {"properties": {"fill": color(TEXTO)}, "selector": {"metadata": "Medidas.Fallecidos AA"}}],
           "lineStyles": [{"properties": {"lineStyle": lit("'dashed'"), "strokeWidth": lit("2D"), "showMarker": lit("false")},
                           "selector": {"metadata": "Medidas.Fallecidos AA"}}],
           "valueAxis": [{"properties": {"start": lit("0D"), "gridlineColor": color(BORDE), "labelColor": color(SUAVE)}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE)}}],
           "legend": [{"properties": {"show": lit("true"), "position": lit("'BottomCenter'"), "labelColor": color(SUAVE)}}],
           "labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("8D")},
                       "selector": {"metadata": "Medidas.Fallecidos"}}]}
    return {"visualType": "lineClusteredColumnComboChart", "query": q, "objects": obj,
            "visualContainerObjects": titulo("Fallecidos por mes frente al año anterior", "Columnas = año elegido · línea punteada = año anterior"),
            "drillFilterOtherVisuals": True}


def pagina(pid, nombre, visuales, sin_filtro=()):
    """sin_filtro: pares (visual origen, visual destino) en los que el origen NO filtra al destino
    (p. ej. el segmentador de año no filtra la serie histórica 2015-2025)."""
    base = RP / "definition" / "pages" / pid
    pj = {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
          "name": pid, "displayName": nombre, "displayOption": "FitToPage", "height": 720, "width": 1280,
          "objects": {"background": [{"properties": {"color": color(FONDO), "transparency": lit("0D")}}],
                      "outspace": [{"properties": {"color": color(FONDO)}}]}}
    if sin_filtro:
        pj["visualInteractions"] = [{"source": gid(pid, s), "target": gid(pid, t), "type": "NoFilter"} for s, t in sin_filtro]
    escribir_json(base / "page.json", pj)
    for i, (n, x, y, w, h, v) in enumerate(visuales):
        c = {"$schema": VC, "name": gid(pid, n),
             "position": {"x": x, "y": y, "z": (i + 1) * 1000, "height": h, "width": w, "tabOrder": (i + 1) * 1000}, "visual": v}
        escribir_json(base / "visuals" / c["name"] / "visual.json", c)


P1, P2, P3, P4 = gid("p", "como"), gid("p", "cuando"), gid("p", "donde"), gid("p", "mio")
PESTANAS = [(P1, "1 · ¿Cómo vamos?"), (P2, "2 · ¿Cuándo es más grave?"), (P3, "3 · ¿Dónde intervenir?"), (P4, "Mi tablero")]


def boton(destino, rotulo, activo):
    sel = {"id": "default"}
    return {"visualType": "actionButton",
            "objects": {"icon": [{"properties": {"shapeType": lit("'blank'")}, "selector": sel}],
                        "text": [{"properties": {"show": lit("true"), "text": lit(f"'{rotulo}'"),
                                                 "fontColor": color("#FFFFFF" if activo else NAVY_TXT), "fontSize": lit("11D"),
                                                 "bold": lit("true" if activo else "false"),
                                                 "horizontalAlignment": lit("'left'"), "leftMargin": lit("14D")}, "selector": sel}],
                        "fill": [{"properties": {"show": lit("true"), "fillColor": color("#24314F" if activo else NAVY),
                                                 "transparency": lit("0D")}, "selector": sel}],
                        "outline": [{"properties": {"show": lit("false")}, "selector": sel}]},
            "visualContainerObjects": {"visualLink": [{"properties": {"show": lit("true"), "type": lit("'PageNavigation'"),
                                                                      "navigationSection": lit(f"'{destino}'")}}],
                                       **sin_fondo()}}


def lateral(pagina_actual, filtros):
    """Barra lateral azul: marca, pestañas (botones de navegación) y segmentadores."""
    vs = [("lateral", 0, 0, 196, 720, texto([("SEGURIDAD VIAL", 14, "#FFFFFF", True), ("BOGOTÁ", 14, ACENTO, True)], fondo=NAVY))]
    for i, (pid, rot) in enumerate(PESTANAS):
        activo = pid == pagina_actual
        vs.append((f"tab_{i}", 8, 74 + i * 34, 180, 30, boton(pid, rot, activo)))
        if activo:
            vs.append((f"tab_marca_{i}", 8, 74 + i * 34, 4, 30, texto([("", 6, ACENTO, False)], fondo=ACENTO)))
    for i, (t_, c_, r_, ini, u) in enumerate(filtros):
        vs.append((f"seg_{c_}", 12, 222 + i * 68, 172, 62, segmentador(t_, c_, r_, ini, u)))
    vs.append(("lema", 14, 650, 170, 64, texto([("De día, Bogotá choca. De noche, muere.", 9, "#FFFFFF", True),
                                                ("Fuente: Anuarios de Siniestralidad Vial, SDM · fallecido a 30 días", 7, NAVY_TXT, False)])))
    return vs


def encabezado(pregunta, frase, lectura):
    """Título = pregunta de la página; frase del pitch; lectura (qué hacer con lo que se ve)."""
    return [("titulo", 212, 6, 700, 36, texto([(pregunta, 20, TEXTO, True)])),
            ("frase", 212, 40, 700, 26, texto([(frase, 11, ACENTO, True)])),
            ("contexto", 920, 8, 348, 30, tarjeta("Titulo", 9, SUAVE, negrita=False)),
            ("lectura", 920, 36, 348, 32, texto([(lectura, 8, SUAVE, False)]))]


def chip_estado(n):
    """Franja de estado que cambia de color según la meta: verde cumple, ámbar mejora sin cumplir, rojo empeora, gris sin dato."""
    return {"visualType": "card", "query": {"queryState": {"Values": {"projections": [proy(med(f"Txt estado {n}"))]}}},
            "objects": {"labels": [{"properties": {"fontSize": lit("8D"), "bold": lit("true"),
                                                   "color": color_med(f"Texto estado {n}")}}],
                        "categoryLabels": [{"properties": {"show": lit("false")}}]},
            "visualContainerObjects": {"background": [{"properties": {"show": lit("true"),
                                                                      "color": {"solid": {"color": {"expr": med(f"Fondo estado {n}")}}},
                                                                      "transparency": lit("0D")}}],
                                       "border": [{"properties": {"show": lit("false")}}]},
            "drillFilterOtherVisuals": True}


def bloque_kpi(pre, k, x, y, w, etiqueta, acento, chispa_on=True):
    vs = [(f"{pre}_fondo", x, y, w, 100, texto([(etiqueta, 10, SUAVE, False)], fondo=TARJETA, borde=BORDE)),
          (f"{pre}_valor", x + 4, y + 16, w - 80 if chispa_on else w - 8, 42, tarjeta(k, 22, ACENTO if acento else TEXTO))]
    if chispa_on:
        vs.append((f"{pre}_chispa", x + w - 78, y + 16, 72, 40, chispa(k, ACENTO if acento else PIZARRA)))
    vs.append((f"{pre}_var", x + 4, y + 54, w - 8, 22, tarjeta(f"Txt {k}", 8, color_medida=f"Color Txt {k}")))
    vs.append((f"{pre}_estado", x + 6, y + 76, w - 12, 20, chip_estado(k)))
    return vs


def columnas(categoria, medida, rot, sub, medida_color=None, horizontal=False, orden_medida=False):
    q = {"queryState": {"Category": {"projections": [proy(categoria, True)]}, "Y": {"projections": [proy(med(medida))]}},
         "sortDefinition": {"sort": [{"field": med(medida) if orden_medida else categoria,
                                      "direction": "Descending" if orden_medida else "Ascending"}]}}
    obj = {"labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("8D")}}],
           "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE), "axisType": lit("'Categorical'")}}]}
    if medida_color:
        obj["dataPoint"] = [{"properties": {"fill": color_med(medida_color)},
                             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]
    return {"visualType": "clusteredBarChart" if horizontal else "clusteredColumnChart", "query": q, "objects": obj,
            "visualContainerObjects": titulo(rot, sub), "drillFilterOtherVisuals": True}


def tendencia(medida, medida_aa, rot, sub):
    """Serie mensual del año elegido (naranja) frente al año anterior (gris punteado): el corazón del monitoreo."""
    mes = col("Calendario", "Mes")
    q = {"queryState": {"Category": {"projections": [proy(mes, True)]},
                        "Y": {"projections": [proy(med(medida)), proy(med(medida_aa))]}},
         "sortDefinition": {"sort": [{"field": mes, "direction": "Ascending"}]}}
    obj = {"dataPoint": [{"properties": {"fill": color(ACENTO)}, "selector": {"metadata": f"Medidas.{medida}"}},
                         {"properties": {"fill": color(PIZARRA)}, "selector": {"metadata": f"Medidas.{medida_aa}"}}],
           "lineStyles": [{"properties": {"strokeWidth": lit("3D"), "showMarker": lit("true")}},
                          {"properties": {"lineStyle": lit("'dashed'"), "strokeWidth": lit("2D")}, "selector": {"metadata": f"Medidas.{medida_aa}"}}],
           "valueAxis": [{"properties": {"start": lit("0D"), "gridlineColor": color(BORDE), "labelColor": color(SUAVE)}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE)}}],
           "legend": [{"properties": {"show": lit("true"), "position": lit("'Top'"), "labelColor": color(SUAVE)}}]}
    return {"visualType": "lineChart", "query": q, "objects": obj, "visualContainerObjects": titulo(rot, sub),
            "drillFilterOtherVisuals": True}


def barras_vs(categoria, rot, sub):
    """Fallecidos del año elegido frente al año anterior, por categoría."""
    q = {"queryState": {"Category": {"projections": [proy(categoria, True)]},
                        "Y": {"projections": [proy(med("Fallecidos")), proy(med("Fallecidos AA"))]}},
         "sortDefinition": {"sort": [{"field": med("Fallecidos"), "direction": "Descending"}], "isDefaultSort": True}}
    obj = {"dataPoint": [{"properties": {"fill": color(ACENTO)}, "selector": {"metadata": "Medidas.Fallecidos"}},
                         {"properties": {"fill": color(GRIS)}, "selector": {"metadata": "Medidas.Fallecidos AA"}}],
           "labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("8D")}}],
           "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE)}}],
           "legend": [{"properties": {"show": lit("true"), "position": lit("'Top'"), "labelColor": color(SUAVE)}}]}
    return {"visualType": "clusteredBarChart", "query": q, "objects": obj, "visualContainerObjects": titulo(rot, sub),
            "drillFilterOtherVisuals": True}


def matriz_calor(filas, columnas_, medida, rot, sub):
    q = {"queryState": {"Rows": {"projections": [proy(filas, True)]}, "Columns": {"projections": [proy(columnas_, True)]},
                        "Values": {"projections": [proy(med(medida))]}}}
    obj = {"columnHeaders": [{"properties": {"fontColor": color(SUAVE), "backColor": color(TARJETA), "fontSize": lit("8D")}}],
           "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(TARJETA), "fontSize": lit("8D")}}],
           "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(TARJETA),
                                      "backColorSecondary": color(TARJETA), "fontSize": lit("8D")}},
                      {"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
                          "Input": med(medida),
                          "FillRule": {"linearGradient2": {"min": {"color": lit("'#FFFFFF'")}, "max": {"color": lit(f"'{ACENTO}'")},
                                                           "nullColoringStrategy": {"strategy": lit("'asZero'")}}}}}}}}},
                       "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"Medidas.{medida}"}}],
           "subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}]}
    return {"visualType": "pivotTable", "query": q, "objects": obj, "visualContainerObjects": titulo(rot, sub),
            "drillFilterOtherVisuals": True}


def tabla_seguimiento():
    """Tablero de control anual: una fila por año y una columna por indicador (seguimiento año a año)."""
    a = col("Calendario", "Año")
    ms = ["Fallecidos", "Var Fallecidos", "% Motociclistas", "% De noche", "% Con carga", "Letalidad moto"]
    q = {"queryState": {"Rows": {"projections": [proy(a, True)]}, "Values": {"projections": [proy(med(m)) for m in ms]}},
         "sortDefinition": {"sort": [{"field": a, "direction": "Descending"}]}}
    obj = {"columnHeaders": [{"properties": {"fontColor": color(SUAVE), "backColor": color(TARJETA), "fontSize": lit("8D"),
                                             "wordWrap": lit("true")}}],
           "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(TARJETA), "fontSize": lit("9D")}}],
           "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(TARJETA),
                                      "backColorSecondary": color(FONDO), "fontSize": lit("9D")}},
                      {"properties": {"fontColor": color_med("Color Txt Fallecidos")},
                       "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "Medidas.Var Fallecidos"}}],
           "subTotals": [{"properties": {"rowSubtotals": lit("false")}}]}
    return {"visualType": "pivotTable", "query": q, "objects": obj,
            "visualContainerObjects": titulo("Seguimiento anual de indicadores", "Una fila por año · variación en rojo si sube, verde si baja"),
            "drillFilterOtherVisuals": True}


def tabla_localidades():
    loc = col("siniestros", "Localidad")
    ms = ["Fallecidos", "Fallecidos AA", "Var Fallecidos", "% De noche", "% Motociclistas"]
    q = {"queryState": {"Rows": {"projections": [proy(loc, True)]}, "Values": {"projections": [proy(med(m)) for m in ms]}},
         "sortDefinition": {"sort": [{"field": med("Fallecidos"), "direction": "Descending"}], "isDefaultSort": True}}
    obj = {"columnHeaders": [{"properties": {"fontColor": color(SUAVE), "backColor": color(TARJETA), "fontSize": lit("8D")}}],
           "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(TARJETA), "fontSize": lit("9D")}}],
           "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(TARJETA),
                                      "backColorSecondary": color(FONDO), "fontSize": lit("9D")}},
                      {"properties": {"fontColor": color_med("Color variación localidad")},
                       "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "Medidas.Var Fallecidos"}},
                      {"properties": {"backColor": color_med("Fondo estado localidad"), "fontColor": color_med("Texto estado localidad")},
                       "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": "Medidas.Fallecidos"}}]}
    return {"visualType": "pivotTable", "query": q, "objects": obj,
            "visualContainerObjects": titulo("Localidades frente a la meta",
                                             "Verde cumple · ámbar mejora sin cumplir · rojo empeora frente al año anterior"),
            "drillFilterOtherVisuals": True}


def puntos():
    """Mapa de puntos con Latitud/Longitud (dispersión): no depende de servicios de mapas."""
    agg = lambda c_: {"Aggregation": {"Expression": col("siniestros", c_), "Function": 1}}
    q = {"queryState": {"Category": {"projections": [proy(col("siniestros", "id_siniestro"), True)]},
                        "X": {"projections": [{"field": agg("Longitud"), "queryRef": "Avg(siniestros.Longitud)", "nativeQueryRef": "Longitud"}]},
                        "Y": {"projections": [{"field": agg("Latitud"), "queryRef": "Avg(siniestros.Latitud)", "nativeQueryRef": "Latitud"}]}}}
    obj = {"dataPoint": [{"properties": {"fill": color(ACENTO)}}],
           "categoryAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "valueAxis": [{"properties": {"show": lit("false"), "gridlineShow": lit("false")}}],
           "legend": [{"properties": {"show": lit("false")}}]}
    return {"visualType": "scatterChart", "query": q, "objects": obj,
            "visualContainerObjects": titulo("¿Dónde ocurren los siniestros mortales?", "Cada punto = un siniestro con muertos (Latitud y Longitud)"),
            "drillFilterOtherVisuals": True}


def filtro_igual(tabla_, columna, valor):
    return {"filters": [{"name": gid("filtro", tabla_, columna, valor), "field": col(tabla_, columna), "type": "Categorical",
                         "filter": {"Version": 2, "From": [{"Name": "s", "Entity": tabla_, "Type": 0}],
                                    "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}},
                                                                                               "Property": columna}}],
                                                                    "Values": [[{"Literal": {"Value": f"'{valor}'"}}]]}}}]}}]}


def poner_filtro(pid, nombre_visual, filtro):
    ruta = RP / "definition" / "pages" / pid / "visuals" / gid(pid, nombre_visual) / "visual.json"
    j = json.loads(ruta.read_text(encoding="utf-8"))
    j["filterConfig"] = filtro
    escribir_json(ruta, j)


F_ANIO = ("Calendario", "Año", "Año", "2025L", False)   # selección múltiple: permite ver periodos (p. ej. 2021-2025)


def anual(medida, rot, sub):
    """Serie histórica 2015-2025 (contexto): no la filtran los segmentadores de año y mes."""
    a = col("Calendario", "Año")
    q = {"queryState": {"Category": {"projections": [proy(a, True)]}, "Y": {"projections": [proy(med(medida))]}},
         "sortDefinition": {"sort": [{"field": a, "direction": "Ascending"}]}}
    obj = {"dataPoint": [{"properties": {"fill": color(ACENTO)}}],
           "lineStyles": [{"properties": {"strokeWidth": lit("3D"), "showMarker": lit("true")}}],
           "labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("8D")}}],
           "valueAxis": [{"properties": {"start": lit("0D"), "gridlineColor": color(BORDE), "labelColor": color(SUAVE)}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE), "axisType": lit("'Categorical'")}}],
           "legend": [{"properties": {"show": lit("false")}}]}
    return {"visualType": "lineChart", "query": q, "objects": obj, "visualContainerObjects": titulo(rot, sub),
            "drillFilterOtherVisuals": True}


def filtro_excluir(tabla_, columna, valor):
    return {"filters": [{"name": gid("excluir", tabla_, columna, valor), "field": col(tabla_, columna), "type": "Categorical",
                         "filter": {"Version": 2, "From": [{"Name": "s", "Entity": tabla_, "Type": 0}],
                                    "Where": [{"Condition": {"Not": {"Expression": {"In": {
                                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": columna}}],
                                        "Values": [[{"Literal": {"Value": f"'{valor}'"}}]]}}}}}]}}]}
F_MES = ("Calendario", "Mes", "Mes", None, False)
F_LOC = ("siniestros", "Localidad", "Localidad", None, False)
F_ACT = ("actor_vial", "actor", "Actor vial", None, False)
F_DN = ("siniestros", "dia_noche", "Día o noche", None, False)
F_SEX = ("actor_vial", "Sexo", "Sexo", None, False)
F_META = ("Meta", "Reduccion", "Meta: reducir frente al año anterior (%)", "10L", True)
etiquetas = {"Fallecidos": "Fallecidos", "Lesionados": "Lesionados", "% Motociclistas": "% de los fallecidos que iban en moto",
             "% De noche": "% de los fallecidos de noche (18 a 5 h)", "% Con carga": "% de fallecidos con vehículo de carga",
             "Letalidad moto": "Letalidad en moto (por 100 víctimas)"}
hora = col("siniestros", "hora_txt")

# ---------------- Página 1 · ¿Cómo vamos?
v = lateral(P1, [F_META, F_ANIO, F_MES, F_LOC, F_ACT, F_SEX])
v += encabezado("¿Cómo vamos?", "El número no baja: unas 11 muertes cada semana",
                "Elige la meta en la barra lateral: cada indicador se pinta verde, ámbar o rojo según si la cumple. Gris = sin año anterior.")
for i, k in enumerate(["Fallecidos", "Lesionados", "% Motociclistas"]):
    v += bloque_kpi(f"k{i}", k, 212 + i * 266, 74, 258, etiquetas[k], k != "Lesionados")
v += [("k3_fondo", 1010, 74, 258, 100, texto([("Fallecidos por semana", 10, SUAVE, False)], fondo=TARJETA, borde=BORDE)),
      ("k3_valor", 1014, 94, 250, 46, tarjeta("Fallecidos por semana", 22, ACENTO)),
      ("k3_nota", 1014, 140, 250, 30, texto([("Escala humana: una cifra que se recuerda", 9, SUAVE, False)]))]
v += [("combo", 212, 182, 620, 268, combo()),
      ("hist_fallecidos", 840, 182, 428, 268, anual("Fallecidos", "Contexto 2015–2025 · fallecidos por año",
                                                   "El número no baja: 530 en 2015, 562 en 2025")),
      ("actor", 212, 458, 520, 254, barras_vs(col("actor_vial", "actor"), "¿Quiénes mueren? Año elegido frente al anterior",
                                             "Fallecidos por actor vial · clic en una barra para filtrar la página")),
      ("hist_moto", 740, 458, 528, 254, tabla_seguimiento())]
pagina(P1, "1 · ¿Cómo vamos?", v,
       sin_filtro=[(s, t) for s in ("seg_Año", "seg_Mes") for t in ("hist_fallecidos", "hist_moto")])

# ---------------- Página 2 · ¿Cuándo es más grave?
v = lateral(P2, [F_META, F_ANIO, F_LOC, F_ACT, F_DN])
v += encabezado("¿Cuándo es más grave?", "De día, Bogotá choca. De noche, muere.",
                "Filtra «Noche»: la letalidad se dispara después de las 6 p. m. El color de cada indicador muestra si cumple la meta.")
for i, k in enumerate(["% De noche", "Letalidad moto", "% Con carga"]):
    v += bloque_kpi(f"k{i}", k, 212 + i * 266, 74, 258, etiquetas[k], i == 0)
v += [("k3_fondo", 1010, 74, 258, 100, texto([("Letalidad de noche frente al día", 10, SUAVE, False)], fondo=TARJETA, borde=BORDE)),
      ("k3_valor", 1014, 94, 120, 46, tarjeta("Letalidad noche", 22, ACENTO)),
      ("k3_dia", 1140, 94, 120, 46, tarjeta("Letalidad día", 22, PIZARRA)),
      ("k3_nota", 1014, 140, 250, 30, texto([("Muertos por cada 100 víctimas: noche (naranja) y día (gris)", 8, SUAVE, False)]))]
v += [("hora", 212, 182, 680, 268, columnas(hora, "Letalidad", "Letalidad por hora del día",
                                             "Muertos por cada 100 víctimas · naranja = noche (18 a 5 h)", "Color hora")),
      ("vehiculo", 900, 182, 368, 268, columnas(col("vehiculos", "Vehiculo_Viajaba_Clasificado"), "% Siniestros mortales",
                                                "¿Con qué vehículo es más mortal?",
                                                "De cada 100 siniestros con víctimas donde participa ese vehículo, cuántos son mortales",
                                                "Color vehículo", True, True)),
      ("noche_mes", 212, 458, 520, 254, tendencia("% De noche", "% De noche AA", "% de fallecidos de noche, por mes",
                                                  "Año elegido (naranja) frente al anterior (gris)")),
      ("calor", 740, 458, 528, 254, matriz_calor(col("Calendario", "DiaSemana"), col("siniestros", "Hora_Acc"), "Fallecidos",
                                                 "¿Qué día y a qué hora?", "Fallecidos por día y hora · más naranja = más muertes"))]
pagina(P2, "2 · ¿Cuándo es más grave?", v)
poner_filtro(P2, "vehiculo", filtro_excluir("vehiculos", "Vehiculo_Viajaba_Clasificado", "SIN INFORMACIÓN"))

# ---------------- Página 3 · ¿Dónde intervenir?
v = lateral(P3, [F_META, F_ANIO, F_ACT, F_DN])
v += encabezado("¿Dónde intervenir?", "Empezar por Kennedy, Engativá y Bosa",
                "Clic en una localidad (barras o tabla) filtra el mapa. Para un periodo, marca varios años (p. ej. 2021–2025).")
insights = [("Localidad con más fallecidos", "Top localidad", ROJO, "#FEF3F2"),
            ("Mayor aumento frente al año anterior", "Mayor aumento", ACENTO, "#FFF6ED"),
            ("Mayor reducción frente al año anterior", "Mayor reducción", VERDE, "#ECFDF3"),
            ("Hora con más fallecidos", "Hora crítica", "#344054", "#F2F4F7")]
for i, (rot, m_, c_, bg) in enumerate(insights):
    x = 212 + i * 266
    v += [(f"ins_fondo_{i}", x, 74, 258, 100, texto([(rot, 9, c_, True)], fondo=bg)),
          (f"ins_valor_{i}", x + 4, 96, 250, 38, tarjeta(m_, 16, TEXTO)),
          (f"ins_det_{i}", x + 4, 134, 250, 36, tarjeta(f"{m_} detalle", 8, SUAVE, negrita=False))]
v += [("loc", 212, 182, 600, 268, barras_loc()),
      ("mapa", 820, 182, 448, 530, puntos()),
      ("tabla", 212, 458, 600, 254, tabla_localidades())]
pagina(P3, "3 · ¿Dónde intervenir?", v)
poner_filtro(P3, "mapa", filtro_igual("siniestros", "Gravedad_indicador_30d", "Con Muertos"))

# ---------------- Página 4 · Mi tablero
v = lateral(P4, [F_ANIO, F_LOC, F_ACT])
v += [("guia", 212, 12, 1000, 60, texto([("Mi tablero", 18, TEXTO, True),
                                        ("Lienzo para construir: usa los campos de siniestros, actor_vial, vehiculos y las medidas de la tabla Medidas.", 10, SUAVE, False)]))]
pagina(P4, "Mi tablero", v)
escribir_json(RP / "definition" / "pages" / "pages.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [P1, P2, P3, P4], "activePageName": P1})

TEMA = "TemaClaro.json"
escribir_json(RP / "StaticResources" / "RegisteredResources" / TEMA, {
    "name": "Seguridad vial · claro",
    "dataColors": [ACENTO, NAVY, PIZARRA, GRIS, "#4E79A7", "#F2B880", "#98A2B3", "#D0D5DD"],
    "background": TARJETA, "foreground": TEXTO, "tableAccent": ACENTO, "good": VERDE, "bad": ROJO, "neutral": SUAVE,
    "textClasses": {"callout": {"fontSize": 20, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": SUAVE}},
    "visualStyles": {
        "*": {"*": {"background": [{"show": True, "color": {"solid": {"color": TARJETA}}, "transparency": 0}],
                    "border": [{"show": True, "color": {"solid": {"color": BORDE}}, "radius": 10}],
                    "dropShadow": [{"show": False}],
                    "padding": [{"top": 10, "bottom": 8, "left": 12, "right": 12}]}},
        "page": {"*": {"background": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}]}},
    }})
escribir_json(RP / "definition" / "report.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "themeCollection": {"customTheme": {"name": TEMA, "reportVersionAtImport": {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"},
                                        "type": "RegisteredResources"}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": TEMA, "path": TEMA, "type": "CustomTheme"}]}],
    "settings": {"useEnhancedTooltips": True}})
escribir_json(RP / "definition" / "version.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
escribir_json(RP / "definition.pbir", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}}})
escribir_json(RP / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": NOMBRE}, "config": {"version": "2.0", "logicalId": guid("rp2")}})
escribir_json(OUT / f"{NOMBRE}.pbip", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}], "settings": {"enableAutoRecovery": True}})
escribir(OUT / ".gitignore", "**/.pbi/\n*.tmp\n~$*\n")
shutil.copy(ROOT / "docs" / "LEEME_powerbi.md", OUT / "LEEME.md")
print(f"PBIP en {OUT} · {len(M)} medidas · {sum(1 for _ in RP.rglob('visual.json'))} visuales · datos: {DATOS}")
