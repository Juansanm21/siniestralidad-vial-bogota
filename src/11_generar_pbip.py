"""Genera el dashboard de monitoreo en Power BI como proyecto PBIP (texto: TMDL + PBIR).

Mismo formato que los proyectos de la clase 2 (power-bi-clase-2-main/proyectos): una carpeta con
  SiniestrosBogota.pbip, SiniestrosBogota.SemanticModel/ (modelo, medidas DAX, roles RLS) y
  SiniestrosBogota.Report/ (páginas y visuales), más datos/ con los CSV que lee el modelo.
Todo es texto, así que se puede compartir la carpeta y editar con IA.

Entrada : data/powerbi/*.csv (src/09_modelo_powerbi.py)
Salida  : powerbi/
Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\11_generar_pbip.py
"""
import hashlib
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "powerbi"
OUT = ROOT / "powerbi"
NOMBRE = "SiniestrosBogota"
SM, RP = OUT / f"{NOMBRE}.SemanticModel", OUT / f"{NOMBRE}.Report"
DATOS = OUT / "datos"

FONDO, TARJETA, BORDE, TEXTO, SUAVE = "#0B1220", "#121B2D", "#1F2A40", "#E6EDF5", "#8A97AD"
ACENTO, GRIS, ROJO, VERDE = "#F28C38", "#56627A", "#E05A4E", "#2E9E5B"
PREGUNTA = ("¿Por qué Bogotá sigue registrando un número elevado de víctimas viales y dónde intervenir? "
            "Seguimiento mensual de los indicadores del informe.")
FUENTE = ("Fuente: bases oficiales de los Anuarios de Siniestralidad Vial (SDM) · fallecido a 30 días · 2015–2025 · "
          "validación: 562 fallecidos en 2025 = cifra oficial · más víctimas no significa mayor riesgo individual "
          "(no hay datos de exposición)")


def gid(*partes, n=20):
    return hashlib.md5("|".join(partes).encode()).hexdigest()[:n]


def guid(*partes):
    return str(uuid.UUID(hashlib.md5(("guid|" + "|".join(partes)).encode()).hexdigest()))


def escribir(ruta, texto):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8", newline="\n")


def escribir_json(ruta, obj):
    escribir(ruta, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# ============================================================ 1. DATOS (CSV limpios, sin BOM)
if OUT.exists():
    shutil.rmtree(OUT)
DATOS.mkdir(parents=True)
tablas = {}
for n in ["fact_victima", "dim_fecha", "dim_hora", "dim_localidad", "dim_actor", "seg_usuario_localidad"]:
    df = pd.read_csv(SRC / f"{n}.csv")
    if n == "fact_victima":
        for c in ["hora", "edad", "con_carga", "con_moto", "con_peaton", "con_velocidad", "con_embriaguez", "con_huecos"]:
            df[c] = df[c].round().astype("Int64")
        df["sexo"] = df["sexo"].fillna("Sin información").replace({"Sin Informacion": "Sin información"})
        df["contraparte"] = df["contraparte"].fillna("Sin otro vehículo")
    df.to_csv(DATOS / f"{n}.csv", index=False, encoding="utf-8")
    tablas[n] = df

# ============================================================ 2. MODELO SEMÁNTICO (TMDL)
T = "\t"
TIPOS = {"string": "type text", "int64": "Int64.Type", "double": "type number", "dateTime": "type date"}


def tabla_tmdl(nombre, columnas, oculta=False, extra_tabla=""):
    """columnas: lista de (nombre, tipo, dict de propiedades extra)."""
    lin = [f"table {nombre}", f"{T}lineageTag: {guid(nombre)}"]
    if oculta:
        lin.append(f"{T}isHidden")
    if extra_tabla:
        lin.append(f"{T}{extra_tabla}")
    lin.append("")
    for c, tipo, props in columnas:
        lin.append(f"{T}column {c}")
        lin.append(f"{T}{T}dataType: {tipo}")
        for k, v in props.items():
            lin.append(f"{T}{T}{k}" if v is True else f"{T}{T}{k}: {v}")
        if "summarizeBy" not in props:
            lin.append(f"{T}{T}summarizeBy: none")
        lin.append(f"{T}{T}sourceColumn: {c}")
        lin.append(f"{T}{T}lineageTag: {guid(nombre, c)}")
        lin.append("")
    tipos_m = ", ".join(f'{{"{c}", {TIPOS[t]}}}' for c, t, _ in columnas)
    lin += [f"{T}partition {nombre} = m", f"{T}{T}mode: import", f"{T}{T}source =",
            f"{T}{T}{T}{T}let",
            f'{T}{T}{T}{T}    Origen = Csv.Document(File.Contents(RutaDatos & "{nombre}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            f"{T}{T}{T}{T}    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars=true]),",
            f'{T}{T}{T}{T}    Vacios = Table.TransformColumns(Encabezados, {{}}, each if _ = "" then null else _),',
            f'{T}{T}{T}{T}    Tipos = Table.TransformColumnTypes(Vacios, {{{tipos_m}}}, "en-US")',
            f"{T}{T}{T}{T}in", f"{T}{T}{T}{T}    Tipos", "",
            f"{T}annotation PBI_ResultType = Table", ""]
    return "\n".join(lin)


S, I, D, F = "string", "int64", "double", "dateTime"
defs = {
    "fact_victima": [("id_victima", I, {}), ("id_siniestro", I, {"isHidden": True}), ("fecha", F, {"formatString": "dd/mm/yyyy"}),
                     ("anio", I, {"isHidden": True}), ("hora", I, {}), ("localidad", S, {}), ("actor", S, {}),
                     ("estado", S, {}), ("edad", I, {}), ("sexo", S, {}), ("con_carga", I, {}), ("con_moto", I, {}),
                     ("con_peaton", I, {}), ("con_velocidad", I, {}), ("con_embriaguez", I, {}), ("con_huecos", I, {}),
                     ("contraparte", S, {}), ("lat", D, {"dataCategory": "Latitude"}), ("lon", D, {"dataCategory": "Longitude"})],
    "dim_fecha": [("fecha", F, {"isKey": True, "formatString": "dd/mm/yyyy"}), ("anio", I, {}), ("mes_num", I, {"isHidden": True}),
                  ("mes", S, {"sortByColumn": "mes_num"}), ("anio_mes", S, {}), ("dia_semana_num", I, {"isHidden": True}),
                  ("dia_semana", S, {"sortByColumn": "dia_semana_num"}), ("fin_de_semana", S, {})],
    "dim_hora": [("hora", I, {}), ("hora_txt", S, {"sortByColumn": "hora"}), ("franja", S, {"sortByColumn": "franja_orden"}),
                 ("franja_orden", I, {"isHidden": True}), ("dia_noche", S, {})],
    "dim_localidad": [("localidad", S, {}), ("localidad_clave", S, {"isHidden": True}),
                      ("lat_centro", D, {"dataCategory": "Latitude"}), ("lon_centro", D, {"dataCategory": "Longitude"})],
    "dim_actor": [("actor", S, {"sortByColumn": "actor_orden"}), ("actor_orden", I, {"isHidden": True}), ("es_vulnerable", S, {})],
    "seg_usuario_localidad": [("correo", S, {}), ("localidad", S, {})],
}
for n, cols in defs.items():
    escribir(SM / "definition" / "tables" / f"{n}.tmdl",
             tabla_tmdl(n, cols, oculta=(n == "seg_usuario_localidad"),
                        extra_tabla="dataCategory: Time" if n == "dim_fecha" else ""))

# ---------------- medidas
QUITA_FECHA = "REMOVEFILTERS(dim_fecha)"
M = [  # (carpeta, nombre, expresión, formato)
    ("1 Base", "Fallecidos", 'CALCULATE(COUNTROWS(fact_victima), fact_victima[estado] = "Fallecido")', "#,0"),
    ("1 Base", "Lesionados", 'CALCULATE(COUNTROWS(fact_victima), fact_victima[estado] = "Herido")', "#,0"),
    ("1 Base", "Fallecidos AA", f"CALCULATE([Fallecidos], SAMEPERIODLASTYEAR(dim_fecha[fecha]), {QUITA_FECHA})", "#,0"),
    ("1 Base", "Lesionados AA", f"CALCULATE([Lesionados], SAMEPERIODLASTYEAR(dim_fecha[fecha]), {QUITA_FECHA})", "#,0"),
    ("1 Base", "Var Fallecidos", "DIVIDE([Fallecidos] - [Fallecidos AA], [Fallecidos AA])", "+0.0%;-0.0%;0.0%"),
    ("1 Base", "Var Lesionados", "DIVIDE([Lesionados] - [Lesionados AA], [Lesionados AA])", "+0.0%;-0.0%;0.0%"),
    ("1 Base", "Fallecidos por semana", "DIVIDE([Fallecidos], DIVIDE(COUNTROWS(dim_fecha), 7))", "0.0"),
    ("2 Indicadores", "% Motociclistas", 'DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"), [Fallecidos])', "0.0%"),
    ("2 Indicadores", "% De noche", 'DIVIDE(CALCULATE([Fallecidos], dim_hora[dia_noche] = "Noche (18-5 h)"), [Fallecidos])', "0.0%"),
    ("2 Indicadores", "% Con carga", "DIVIDE(CALCULATE([Fallecidos], fact_victima[con_carga] = 1), [Fallecidos])", "0.0%"),
    ("2 Indicadores", "% Moto madrugada",
     'DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista", dim_hora[hora] <= 5), '
     'CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"))', "0.0%"),
    ("2 Indicadores", "Letalidad moto",
     'DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"), '
     'CALCULATE([Fallecidos] + [Lesionados], dim_actor[actor] = "Motociclista")) * 100', "0.00"),
    ("2 Indicadores", "Letalidad", "DIVIDE([Fallecidos], [Fallecidos] + [Lesionados]) * 100", "0.00"),
]
for base in ["% Motociclistas", "% De noche", "% Con carga", "Letalidad moto"]:
    fmt = "0.00" if base.startswith("Letalidad") else "0.0%"
    M.append(("3 Año anterior", f"{base} AA", f"CALCULATE([{base}], SAMEPERIODLASTYEAR(dim_fecha[fecha]), {QUITA_FECHA})", fmt))


def txt_var(nombre, base, pp):
    if pp:
        cuerpo = (f"VAR aa = [{base} AA]\nVAR d = ([{base}] - aa) * {100 if base.startswith('%') else 1}\n"
                  f"RETURN IF(ISBLANK(aa) || ISBLANK([{base}]), \"Sin año anterior\", "
                  f"IF(d > 0, \"▲ \", \"▼ \") & FORMAT(ABS(d), \"0.0\") & \"{' pp' if base.startswith('%') else ''} vs año anterior\")")
    else:
        cuerpo = (f"VAR aa = [{base} AA]\nVAR v = [Var {base}]\n"
                  f"RETURN IF(ISBLANK(aa), \"Sin año anterior\", "
                  f"IF(v > 0, \"▲ \", \"▼ \") & FORMAT(ABS(v), \"0.0%\") & \" vs año anterior\")")
    color = (f"VAR aa = [{base} AA]\nRETURN IF(ISBLANK(aa), \"{SUAVE}\", IF([{base}] > aa, \"{ROJO}\", \"{VERDE}\"))")
    return [("4 Textos y colores", nombre, cuerpo, None), ("4 Textos y colores", f"Color {nombre}", color, None)]


for b, pp in [("Fallecidos", False), ("Lesionados", False), ("% Motociclistas", True), ("% De noche", True),
              ("% Con carga", True), ("Letalidad moto", True)]:
    M += txt_var(f"Txt {b}", b, pp)
M += [
    ("4 Textos y colores", "Color hora",
     f'VAR h = SELECTEDVALUE(dim_hora[hora])\nRETURN IF(h <= 5 || h >= 18, "{ACENTO}", "{GRIS}")', None),
    ("4 Textos y colores", "Color actor", f'IF(SELECTEDVALUE(dim_actor[actor]) = "Motociclista", "{ACENTO}", "{GRIS}")', None),
    ("4 Textos y colores", "Titulo Monitoreo",
     'VAR loc = IF(ISFILTERED(dim_localidad[localidad]), SELECTEDVALUE(dim_localidad[localidad], "varias localidades"), "Bogotá")\n'
     'VAR act = IF(ISFILTERED(dim_actor[actor]), SELECTEDVALUE(dim_actor[actor], "varios actores"), "todas las víctimas")\n'
     'VAR fr = IF(ISFILTERED(dim_hora[dia_noche]), " · " & SELECTEDVALUE(dim_hora[dia_noche], "día y noche"), "")\n'
     'VAR an = IF(ISFILTERED(dim_fecha[anio]), SELECTEDVALUE(dim_fecha[anio], "varios años") & "", "2015–2025")\n'
     'RETURN "Monitoreo de siniestralidad vial · " & loc & " · " & an & " · " & act & fr', None),
    ("4 Textos y colores", "Titulo Tendencias",
     'VAR loc = IF(ISFILTERED(dim_localidad[localidad]), SELECTEDVALUE(dim_localidad[localidad], "varias localidades"), "Bogotá")\n'
     'VAR act = IF(ISFILTERED(dim_actor[actor]), SELECTEDVALUE(dim_actor[actor], "varios actores"), "todas las víctimas")\n'
     'RETURN "Tendencias 2015–2025 · " & loc & " · " & act', None),
]


def nombre_tmdl(n):
    return n if n.replace("_", "").isalnum() else "'" + n.replace("'", "''") + "'"


lin = ["table Medidas", f"{T}lineageTag: {guid('Medidas')}", ""]
for carpeta, n, expr, fmt in M:
    if "\n" in expr:
        lin.append(f"{T}measure {nombre_tmdl(n)} =")
        lin += [f"{T}{T}{T}{x}" for x in expr.split("\n")]
    else:
        lin.append(f"{T}measure {nombre_tmdl(n)} = {expr}")
    if fmt:
        lin.append(f"{T}{T}formatString: {fmt}")
    lin.append(f"{T}{T}displayFolder: {carpeta}")
    lin.append(f"{T}{T}lineageTag: {guid('m', n)}")
    lin.append("")
lin += [f"{T}partition Medidas = m", f"{T}{T}mode: import", f"{T}{T}source =",
        f"{T}{T}{T}{T}let",
        f'{T}{T}{T}{T}    Origen = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Columna1 = _t]),',
        f'{T}{T}{T}{T}    Tipo = Table.TransformColumnTypes(Origen, {{{{"Columna1", type text}}}}),',
        f'{T}{T}{T}{T}    Quitada = Table.RemoveColumns(Tipo, {{"Columna1"}})',
        f"{T}{T}{T}{T}in", f"{T}{T}{T}{T}    Quitada", "",
        f"{T}annotation PBI_ResultType = Table", ""]
escribir(SM / "definition" / "tables" / "Medidas.tmdl", "\n".join(lin))

ruta_datos = str(DATOS.resolve()) + "\\"
escribir(SM / "definition" / "expressions.tmdl",
         f'expression RutaDatos = "{ruta_datos}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
         f"{T}lineageTag: {guid('RutaDatos')}\n\n{T}annotation PBI_ResultType = Text\n")

orden = ["RutaDatos", "dim_fecha", "dim_hora", "dim_localidad", "dim_actor", "seg_usuario_localidad", "fact_victima", "Medidas"]
escribir(SM / "definition" / "database.tmdl", "database SiniestrosBogota\n\tcompatibilityLevel: 1600\n")
escribir(SM / "definition" / "model.tmdl",
         "model Model\n\tculture: es-CO\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: es-CO\n"
         "\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
         f"annotation PBI_QueryOrder = {json.dumps(orden, ensure_ascii=False)}\n\n"
         'annotation PBI_ProTooling = ["DevMode","TMDLView_Desktop"]\n\n'
         + "".join(f"ref table {t}\n" for t in orden[1:]) + "\n"
         + "".join(f"ref role {r}\n" for r in ["Direccion", "Alcaldia_Kennedy", "Alcaldia_dinamico"]))
rels = [("fact_victima", "fecha", "dim_fecha", "fecha", ""), ("fact_victima", "hora", "dim_hora", "hora", ""),
        ("fact_victima", "localidad", "dim_localidad", "localidad", ""), ("fact_victima", "actor", "dim_actor", "actor", "")]
# seg_usuario_localidad queda desconectada: el rol dinámico la consulta con DAX (patrón estándar, sin relación bidireccional)
escribir(SM / "definition" / "relationships.tmdl", "\n".join(
    f"relationship {guid('rel', a, b)}\n{x}\tfromColumn: {a}.{ca}\n\ttoColumn: {b}.{cb}\n" for a, ca, b, cb, x in rels))
roles = {"Direccion": "", "Alcaldia_Kennedy": '\n\ttablePermission dim_localidad = [localidad] == "Kennedy"\n',
         "Alcaldia_dinamico": "\n\ttablePermission dim_localidad = [localidad] IN CALCULATETABLE(VALUES(seg_usuario_localidad[localidad]), "
                              "seg_usuario_localidad[correo] = USERPRINCIPALNAME())\n"}
for r, p in roles.items():
    escribir(SM / "definition" / "roles" / f"{r}.tmdl", f"role {r}\n\tmodelPermission: read\n{p}")
escribir_json(SM / "definition.pbism", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}})
escribir_json(SM / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "SemanticModel", "displayName": NOMBRE}, "config": {"version": "2.0", "logicalId": guid("sm")}})

# ============================================================ 3. REPORTE (PBIR)
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def color(c):
    return {"solid": {"color": lit(f"'{c}'")}}


def col(t, c):
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}


def med(n):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": n}}


def proy(campo, activo=False):
    k = "Column" if "Column" in campo else "Measure"
    ent, prop = campo[k]["Expression"]["SourceRef"]["Entity"], campo[k]["Property"]
    p = {"field": campo, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if activo:
        p["active"] = True
    return p


def titulo(texto, tam=11):
    return {"title": [{"properties": {"show": lit("true"), "text": lit(f"'{texto}'"), "fontColor": color(TEXTO),
                                      "fontSize": lit(f"{tam}D"), "bold": lit("true")}}]}


def contenedor(pagina, nombre, x, y, w, h, visual, z):
    v = {"$schema": VC, "name": gid(pagina, nombre),
         "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": visual}
    return v


def sin_fondo():
    return {"background": [{"properties": {"show": lit("false")}}]}


def texto(parrafos):
    """parrafos: lista de (texto, tamaño_pt, color, negrita)."""
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", "color": c, "fontFamily": "Segoe UI",
                                                 **({"fontWeight": "bold"} if b else {})}}]}
        for t, s, c, b in parrafos]}}]}, "visualContainerObjects": sin_fondo()}


def tarjeta(medida, tam=26, color_medida=None, etiqueta=True, fondo=True, color_txt=TEXTO):
    lab = {"fontSize": lit(f"{tam}D"), "color": {"solid": {"color": {"expr": med(color_medida)}}} if color_medida else color(color_txt)}
    vco = {} if fondo else sin_fondo()
    return {"visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proy(med(medida))]}}},
            "objects": {"labels": [{"properties": lab}],
                        "categoryLabels": [{"properties": {"show": lit("true" if etiqueta else "false"), "color": color(SUAVE),
                                                           "fontSize": lit("10D")}}]},
            "visualContainerObjects": vco, "drillFilterOtherVisuals": True}


def segmentador(tabla, columna, rotulo, valor_inicial=None, unico=False):
    obj = {"data": [{"properties": {"mode": lit("'Dropdown'")}}],
           "header": [{"properties": {"show": lit("true"), "text": lit(f"'{rotulo}'"), "fontColor": color(SUAVE),
                                      "textSize": lit("10D")}}],
           "items": [{"properties": {"fontColor": color(TEXTO), "background": color(TARJETA), "textSize": lit("11D")}}],
           "selection": [{"properties": {"singleSelect": lit("true" if unico else "false"),
                                         "selectAllCheckboxEnabled": lit("false" if unico else "true")}}]}
    if valor_inicial is not None:
        obj["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "s", "Entity": tabla, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}},
                                                                      "Property": columna}}],
                                            "Values": [[{"Literal": {"Value": valor_inicial}}]]}}}]}}}}]
    return {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [proy(col(tabla, columna), True)]}}},
            "objects": obj, "drillFilterOtherVisuals": True}


def regla_color(medida_color):
    return [{"properties": {"fill": {"solid": {"color": {"expr": med(medida_color)}}}},
             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}}]


def barras(tipo, categoria, medida, rotulo, medida_color=None, orden_por_medida=True):
    obj = {"labels": [{"properties": {"show": lit("true"), "color": color(TEXTO), "fontSize": lit("9D")}}],
           "valueAxis": [{"properties": {"show": lit("false" if tipo == "clusteredBarChart" else "true"),
                                         "gridlineShow": lit("false")}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE)}}]}
    if medida_color:
        obj["dataPoint"] = regla_color(medida_color)
    q = {"queryState": {"Category": {"projections": [proy(categoria, True)]}, "Y": {"projections": [proy(med(medida))]}}}
    if orden_por_medida:
        q["sortDefinition"] = {"sort": [{"field": med(medida), "direction": "Descending"}], "isDefaultSort": True}
    else:
        q["sortDefinition"] = {"sort": [{"field": categoria, "direction": "Ascending"}]}
    return {"visualType": tipo, "query": q, "objects": obj, "visualContainerObjects": titulo(rotulo),
            "drillFilterOtherVisuals": True}


def lineas(categoria, medidas, rotulo, colores, punteadas=(), etiquetas=False):
    obj = {"dataPoint": [{"properties": {"fill": color(c)}, "selector": {"metadata": f"Medidas.{m}"}}
                         for m, c in zip(medidas, colores)],
           "valueAxis": [{"properties": {"start": lit("0D"), "gridlineColor": color(BORDE), "labelColor": color(SUAVE)}}],
           "categoryAxis": [{"properties": {"labelColor": color(SUAVE), "axisType": lit("'Categorical'")}}],
           "lineStyles": [{"properties": {"strokeWidth": lit("3D")}}]
           + [{"properties": {"lineStyle": lit("'dashed'"), "strokeWidth": lit("2D")}, "selector": {"metadata": f"Medidas.{m}"}}
              for m in punteadas],
           "legend": [{"properties": {"show": lit("true" if len(medidas) > 1 else "false"), "position": lit("'Top'"),
                                      "labelColor": color(SUAVE)}}],
           "labels": [{"properties": {"show": lit("true" if etiquetas else "false"), "color": color(TEXTO), "fontSize": lit("9D")}}]}
    q = {"queryState": {"Category": {"projections": [proy(categoria, True)]},
                        "Y": {"projections": [proy(med(m)) for m in medidas]}},
         "sortDefinition": {"sort": [{"field": categoria, "direction": "Ascending"}]}}
    return {"visualType": "lineChart", "query": q, "objects": obj, "visualContainerObjects": titulo(rotulo),
            "drillFilterOtherVisuals": True}


def matriz(filas, columnas, medidas, rotulo, orden=None, colores_fuente=None, gradiente=None):
    qs = {"Rows": {"projections": [proy(f, True) for f in filas]}, "Values": {"projections": [proy(med(m)) for m in medidas]}}
    if columnas:
        qs["Columns"] = {"projections": [proy(c, True) for c in columnas]}
    q = {"queryState": qs}
    if orden:
        q["sortDefinition"] = {"sort": [{"field": med(orden), "direction": "Descending"}], "isDefaultSort": True}
    obj = {"columnHeaders": [{"properties": {"fontColor": color(SUAVE), "backColor": color(TARJETA), "fontSize": lit("9D")}}],
           "rowHeaders": [{"properties": {"fontColor": color(TEXTO), "backColor": color(TARJETA), "fontSize": lit("9D")}}],
           "values": [{"properties": {"fontColorPrimary": color(TEXTO), "backColorPrimary": color(TARJETA),
                                      "fontColorSecondary": color(TEXTO), "backColorSecondary": color(TARJETA),
                                      "fontSize": lit("9D")}}],
           "grid": [{"properties": {"gridHorizontal": lit("false"), "gridVertical": lit("false"), "outlineColor": color(BORDE)}}],
           "subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}],
           "total": [{"properties": {"fontColor": color(TEXTO), "backColor": color(BORDE)}}]}
    for m, mc in (colores_fuente or {}).items():
        obj["values"].append({"properties": {"fontColor": {"solid": {"color": {"expr": med(mc)}}}},
                              "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"Medidas.{m}"}})
    if gradiente:
        obj["values"].append({"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
            "Input": med(gradiente),
            "FillRule": {"linearGradient2": {"min": {"color": lit(f"'{TARJETA}'")}, "max": {"color": lit(f"'{ACENTO}'")},
                                             "nullColoringStrategy": {"strategy": lit("'asZero'")}}}}}}}}},
            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"Medidas.{gradiente}"}})
    return {"visualType": "pivotTable", "query": q, "objects": obj, "visualContainerObjects": titulo(rotulo),
            "drillFilterOtherVisuals": True}


def pagina(pid, nombre, visuales):
    base = RP / "definition" / "pages" / pid
    escribir_json(base / "page.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pid, "displayName": nombre, "displayOption": "FitToPage", "height": 720, "width": 1280,
        "objects": {"background": [{"properties": {"color": color(FONDO), "transparency": lit("0D")}}],
                    "outspace": [{"properties": {"color": color(FONDO)}}]}})
    for i, (n, x, y, w, h, v) in enumerate(visuales):
        c = contenedor(pid, n, x, y, w, h, v, (i + 1) * 1000)
        escribir_json(base / "visuals" / c["name"] / "visual.json", c)


# ---------------- Página 1 · Monitoreo
P1, P2 = gid("pagina", "monitoreo"), gid("pagina", "tendencias")
v1 = [("titulo", 16, 8, 900, 40, tarjeta("Titulo Monitoreo", 17, etiqueta=False, fondo=False)),
      ("pregunta", 16, 46, 900, 34, texto([(PREGUNTA, 10, SUAVE, False)])),
      ("rol", 930, 14, 334, 60, texto([("Dashboard de monitoreo · componente 2 de 2", 9, ACENTO, True),
                                        ("El hallazgo se explica en el informe (Streamlit). Aquí se sigue el indicador.", 8, SUAVE, False)]))]
seg = [("dim_fecha", "anio", "Año", "2025L", True), ("dim_fecha", "mes", "Mes", None, False),
       ("dim_localidad", "localidad", "Localidad", None, False), ("dim_actor", "actor", "Actor vial", None, False),
       ("dim_hora", "dia_noche", "Día / noche", None, False), ("fact_victima", "sexo", "Sexo", None, False)]
for i, (t, c, r, ini, u) in enumerate(seg):
    v1.append((f"seg_{c}", 16 + i * 210, 84, 202, 56, segmentador(t, c, r, ini, u)))
kpis = ["Fallecidos", "Lesionados", "% Motociclistas", "% De noche", "% Con carga", "Letalidad moto"]
for i, k in enumerate(kpis):
    v1.append((f"kpi_{k}", 16 + i * 210, 148, 202, 76, tarjeta(k, 26, color_txt=ACENTO if k in ("Fallecidos", "% Motociclistas", "% De noche") else TEXTO)))
    v1.append((f"var_{k}", 16 + i * 210, 222, 202, 26, tarjeta(f"Txt {k}", 10, color_medida=f"Color Txt {k}", etiqueta=False)))
v1 += [("linea_mes", 16, 258, 620, 214, lineas(col("dim_fecha", "mes"), ["Fallecidos", "Fallecidos AA"],
                                               "Fallecidos por mes · año seleccionado vs año anterior", [ACENTO, GRIS], ["Fallecidos AA"])),
       ("hora", 644, 258, 620, 214, barras("clusteredColumnChart", col("dim_hora", "hora_txt"), "Fallecidos",
                                         "Fallecidos por hora del día · naranja = noche (18 a 5 h)", "Color hora", False)),
       ("actor", 16, 480, 400, 214, barras("clusteredBarChart", col("dim_actor", "actor"), "Fallecidos",
                                         "Fallecidos por actor vial · clic para filtrar", "Color actor")),
       ("matriz_loc", 424, 480, 840, 214, matriz([col("dim_localidad", "localidad")], None,
                                                 ["Fallecidos", "Fallecidos AA", "Var Fallecidos", "% Motociclistas", "% De noche", "% Con carga"],
                                                 "Localidades · ordenadas por fallecidos (verde baja, rojo sube)", "Fallecidos",
                                                 {"Var Fallecidos": "Color Txt Fallecidos"})),
       ("fuente", 16, 698, 1248, 20, texto([(FUENTE, 7, SUAVE, False)]))]
pagina(P1, "Monitoreo", v1)

# ---------------- Página 2 · Tendencias
anio = col("dim_fecha", "anio")
v2 = [("titulo", 16, 8, 900, 40, tarjeta("Titulo Tendencias", 17, etiqueta=False, fondo=False)),
      ("pregunta", 16, 46, 900, 30, texto([("¿Los indicadores mejoran o empeoran? Un gráfico por indicador, sin doble eje.", 10, SUAVE, False)])),
      ("seg_localidad", 930, 14, 164, 56, segmentador("dim_localidad", "localidad", "Localidad")),
      ("seg_actor", 1100, 14, 164, 56, segmentador("dim_actor", "actor", "Actor vial"))]
graf = [("Fallecidos", "Fallecidos por año"), ("% Motociclistas", "% de motociclistas entre los fallecidos"),
        ("% De noche", "% de fallecidos de noche (18 a 5 h)"), ("% Con carga", "% de fallecidos con vehículo de carga"),
        ("% Moto madrugada", "% de motociclistas fallecidos de madrugada (0 a 5 h)"),
        ("Letalidad moto", "Letalidad en moto · muertos por cada 100 víctimas")]
for i, (m_, r) in enumerate(graf):
    x, y = 16 + (i % 3) * 418, 84 + (i // 3) * 196
    v2.append((f"t_{m_}", x, y, 410, 188, lineas(anio, [m_], r, [ACENTO], etiquetas=True)))
v2 += [("dia_hora", 16, 476, 1248, 218, matriz([col("dim_fecha", "dia_semana")], [col("dim_hora", "hora")], ["Fallecidos"],
                                               "Fallecidos por día de la semana y hora · más oscuro = menos, naranja = más",
                                               gradiente="Fallecidos")),
       ("fuente", 16, 698, 1248, 20, texto([(FUENTE, 7, SUAVE, False)]))]
pagina(P2, "Tendencias", v2)

escribir_json(RP / "definition" / "pages" / "pages.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [P1, P2], "activePageName": P1})

# ---------------- tema
TEMA = "TemaSiniestros.json"
tema = {
    "name": "Siniestros Bogotá · noche",
    "dataColors": [ACENTO, GRIS, "#4EA8F0", "#4FBF9F", "#C9D4E3", SUAVE, "#C96A24", "#2E3B55"],
    "background": FONDO, "foreground": TEXTO, "tableAccent": ACENTO, "good": VERDE, "bad": ROJO, "neutral": SUAVE,
    "maximum": ACENTO, "center": GRIS, "minimum": TARJETA,
    "textClasses": {"callout": {"fontSize": 26, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
                    "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": SUAVE}},
    "visualStyles": {
        "*": {"*": {"background": [{"show": True, "color": {"solid": {"color": TARJETA}}, "transparency": 0}],
                    "border": [{"show": False}], "dropShadow": [{"show": False}],
                    "title": [{"fontColor": {"solid": {"color": TEXTO}}}],
                    "categoryAxis": [{"labelColor": {"solid": {"color": SUAVE}}, "titleColor": {"solid": {"color": SUAVE}},
                                      "gridlineShow": False}],
                    "valueAxis": [{"labelColor": {"solid": {"color": SUAVE}}, "titleColor": {"solid": {"color": SUAVE}},
                                   "gridlineColor": {"solid": {"color": BORDE}}}],
                    "legend": [{"labelColor": {"solid": {"color": SUAVE}}}],
                    "padding": [{"top": 8, "bottom": 8, "left": 10, "right": 10}]}},
        "page": {"*": {"background": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}],
                       "outspace": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}]}},
        "textbox": {"*": {"background": [{"show": False}]}},
    },
}
escribir_json(RP / "StaticResources" / "RegisteredResources" / TEMA, tema)
escribir_json(RP / "definition" / "report.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "themeCollection": {"customTheme": {"name": TEMA, "reportVersionAtImport": {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"},
                                        "type": "RegisteredResources"}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": TEMA, "path": TEMA, "type": "CustomTheme"}]}],
    "settings": {"useEnhancedTooltips": True, "exportDataMode": "AllowSummarizedAndUnderlying"}})
escribir_json(RP / "definition" / "version.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0"})
escribir_json(RP / "definition.pbir", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}}})
escribir_json(RP / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": NOMBRE}, "config": {"version": "2.0", "logicalId": guid("rp")}})
escribir_json(OUT / f"{NOMBRE}.pbip", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}], "settings": {"enableAutoRecovery": True}})
escribir(OUT / ".gitignore", "# Caché y configuración local de Power BI Desktop\n**/.pbi/\n*.tmp\n~$*\n")
n_vis = sum(1 for _ in RP.rglob("visual.json"))
print(f"PBIP generado en {OUT} · {len(M)} medidas · {n_vis} visuales · datos en {DATOS}")
