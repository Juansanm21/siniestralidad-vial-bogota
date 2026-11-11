"""Informe ejecutivo · Siniestralidad vial en Bogotá, 2015-2025.

Se presenta a la dirección de la Secretaría de Movilidad; después se muestra el tablero de Power BI como herramienta de seguimiento.
Formato de consultoría: una lámina por hallazgo, título de acción, gráfico a la izquierda y hallazgos numerados a la derecha.
Datos: data/powerbi/ (src/09_modelo_powerbi.py, bases de los Anuarios de Siniestralidad Vial, SDM).
Ejecutar desde la carpeta Proyecto:  .venv\\Scripts\\streamlit run siniestros\\app\\app.py --server.port 8502
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from comun import (ACENTO, BORDE, CFG, CSS, GRIS1, GRIS2, GRIS3, NAVY, NAVY2, SUAVE, TEXTO, VERDE, estilo, fuente,
                   graf_titulo, lamina, panel, barra, resumen, efectos, objetivos, fuentes_datos)

D = Path(__file__).resolve().parents[1] / "data" / "powerbi"
st.set_page_config(page_title="Siniestralidad vial en Bogotá · Informe ejecutivo", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def cargar():
    v = pd.read_csv(D / "fact_victima.csv", parse_dates=["fecha"])
    v["noche"] = (v.hora >= 18) | (v.hora <= 5)
    v["madrugada"] = v.hora <= 5
    return v, pd.read_csv(D / "res_comparendos_hora.csv"), pd.read_csv(D / "res_percepcion_eprv.csv")


def es(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


v, comp, eprv = cargar()
A0, A1 = int(v.anio.min()), int(v.anio.max())
FUENTE = "Fuente: bases de los Anuarios de Siniestralidad Vial, Secretaría Distrital de Movilidad · fallecido a 30 días"
f, h = v[v.estado == "Fallecido"], v[v.estado == "Herido"]
m = v[v.actor == "Motociclista"]
fm, hm = m[m.estado == "Fallecido"], m[m.estado == "Herido"]
rec = v[v.anio >= 2021]
f_rec, h_rec = rec[rec.estado == "Fallecido"], rec[rec.estado == "Herido"]
f1, fm1 = f[f.anio == A1], fm[fm.anio == A1]
por_anio = f.groupby("anio").size()
SEM = 365 / 7
p_f_noche, p_h_noche = f_rec.noche.mean(), h_rec.noche.mean()
pe = eprv.set_index("indicador").porcentaje
t = f.pivot_table(index="anio", columns="actor", values="id_victima", aggfunc="count").fillna(0)
sh = t.Motociclista / t.sum(axis=1)
let_dia = len(f_rec[~f_rec.noche]) / len(rec[~rec.noche]) * 100
let_noc = len(f_rec[f_rec.noche]) / len(rec[rec.noche]) * 100
cv, cc = comp.comparendos_velocidad, comp.comparendos_camaras
noc_c = (comp.hora >= 18) | (comp.hora <= 5)
fmn = fm[(fm.anio >= 2021) & fm.noche]
top = fmn.localidad.value_counts().head(8)
lideres = list(top[top >= top.iloc[2]].index)
loc_txt = ", ".join(lideres[:-1]) + " y " + lideres[-1]
prom_moto = fm[fm.anio >= 2021].groupby("anio").size().mean()

barra([("s1", "Contexto"), ("obj", "Enfoque"), ("met", "Datos"), ("s2", "Hallazgos"),
       ("s7", "Conclusiones")])

# =================================================================== PORTADA (pantalla completa) Y RESUMEN EJECUTIVO
p_vel_noche = cv[noc_c].sum() / cv.sum() * 100
p_f21_noche = (f[f.anio == 2021].noche.mean()) * 100
st.markdown(
    f'<div class="hero2"><div>'
    f'<div class="meta">Informe para la Secretaría Distrital de Movilidad · {A0}–{A1}</div>'
    f'<h1>Siniestralidad vial en Bogotá: dónde y cuándo se concentran las muertes</h1>'
    f'<div class="golpe">Cada {8760 / len(f1):.0f} horas muere una persona en las vías de Bogotá.</div>'
    f'<div class="preg">¿Por qué Bogotá sigue registrando un número elevado de víctimas viales y dónde intervenir?</div>'
    f'<div class="bajar">Desliza para ver los hallazgos <i>↓</i></div></div>'
    f'<div class="gran"><div class="num" data-n="{len(f)}">{es(len(f))}</div>'
    f'<div class="txt">personas murieron en las vías de Bogotá entre {A0} y {A1}</div>'
    f'<div class="sub">Unas <b>{round(len(f1) / SEM)} cada semana</b>. En {A1} fueron <b>{len(f1)}</b>: casi las mismas que hace una década.</div>'
    f'</div></div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="impactos">'
    f'<div class="impacto"><small>Quiénes mueren</small>'
    f'<div class="v"><span data-n="{sh.loc[A1] * 100:.0f}" data-suf="%">{sh.loc[A1]:.0%}</span></div>'
    f'<p>de los fallecidos son motociclistas, frente a {sh.loc[A0]:.0%} en {A0}</p>'
    f'<div class="mini"><span>{A0}</span><div class="pista"><i style="--w:{sh.loc[A0] * 100:.0f}%"></i></div><b>{sh.loc[A0]:.0%}</b>'
    f'<span>{A1}</span><div class="pista"><i class="ac" style="--w:{sh.loc[A1] * 100:.0f}%"></i></div><b>{sh.loc[A1]:.0%}</b></div></div>'
    f'<div class="impacto"><small>Cuándo mueren</small>'
    f'<div class="v"><span data-n="{p_f_noche * 100:.0f}" data-suf="%">{p_f_noche:.0%}</span></div>'
    f'<p>de las muertes ocurre de noche, aunque allí solo cae el {p_h_noche:.0%} de los heridos</p>'
    f'<div class="dividida"><i style="--w:{(1 - p_f_noche) * 100:.0f}%; background:#C3CAD5"></i>'
    f'<i style="--w:{p_f_noche * 100:.0f}%; background:#E8772E"></i></div>'
    f'<div class="leyenda-m"><span>Día · {1 - p_f_noche:.0%}</span><b>Noche · {p_f_noche:.0%}</b></div></div>'
    f'<div class="impacto"><small>La brecha de control · 2021</small>'
    f'<div class="v"><span data-n="{p_vel_noche:.1f}" data-dec="1" data-suf="%">{es(p_vel_noche, 1)}%</span></div>'
    f'<p>de los comparendos por velocidad fue de noche, cuando ocurrió el {p_f21_noche:.0f}% de las muertes</p>'
    f'<div class="mini"><span>Muertes</span><div class="pista"><i class="ac" style="--w:{p_f21_noche:.0f}%"></i></div><b>{p_f21_noche:.0f}%</b>'
    f'<span>Control</span><div class="pista"><i class="nv" style="--w:{max(p_vel_noche, 1.2):.1f}%"></i></div><b>{es(p_vel_noche, 1)}%</b></div></div>'
    f'</div>', unsafe_allow_html=True)
# =================================================================== 01 · PROBLEMÁTICA
lamina("s1", "01 · Contexto",
       f"Bogotá pierde unas {round(len(f1) / SEM)} personas cada semana en sus vías, y la cifra no baja desde hace una década",
       f"Las muertes viales se mantienen entre {por_anio.drop(2020).min()} y {por_anio.drop(2020).max()} al año. "
       "Mientras no se sepa dónde y cuándo se concentran, el control no puede enfocarse donde más vidas salvaría.")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Personas fallecidas en siniestros viales por año", f"{A0}–{A1} · la línea punteada es el promedio sin 2020")
    prom = por_anio.drop(2020).mean()
    colores = [GRIS2 if y == 2020 else (ACENTO if y == A1 else NAVY) for y in por_anio.index]
    fig = go.Figure(go.Bar(x=por_anio.index, y=por_anio.values, marker=dict(color=colores, cornerradius=4),
                           text=por_anio.values, textposition="outside", textfont=dict(color=TEXTO, size=12), cliponaxis=False,
                           hovertemplate="%{x}: %{y} fallecidos<extra></extra>"))
    fig.add_hline(y=prom, line_dash="dot", line_color=GRIS1)
    fig.add_annotation(x=A0 - 0.4, y=prom, text=f"Promedio {es(prom)}", showarrow=False, xanchor="left", yshift=12,
                       font=dict(color=SUAVE, size=12))
    fig.add_annotation(x=2020, y=por_anio.loc[2020], text="Pandemia", showarrow=False, yshift=-24, font=dict(color=SUAVE, size=11))
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, range=[0, por_anio.max() * 1.15])
    st.plotly_chart(estilo(fig, 420), width="stretch", config=CFG)
    fuente(FUENTE)
with b:
    panel([("La magnitud", f"{es(len(f))} personas fallecidas en once años; {len(f1)} solo en {A1}."),
           ("El estancamiento", f"{por_anio.loc[A0]} en {A0} y {len(f1)} en {A1}. Solo 2020, por la pandemia, rompió la franja "
                                f"({por_anio.loc[2020]})."),
           ("Lo que el total esconde", "La cifra estable oculta cambios en quién muere, a qué hora y en qué condiciones. "
                                       "Entenderlos es la base para decidir dónde intervenir.")], titulo="Por qué importa", acento=3)

# =================================================================== 02 · OBJETIVOS
lamina("obj", "02 · Enfoque",
       "Si el total no explica el problema, hay que buscar dónde se concentra el riesgo",
       "Dos propósitos guiaron el análisis, y cada hallazgo del informe responde a uno de ellos.")
objetivos("¿Por qué Bogotá sigue registrando un número elevado de víctimas viales y dónde intervenir?",
          [("Encontrar dónde se concentra el riesgo",
            "Quiénes mueren, a qué hora, en qué condiciones y si el control llega a esos momentos.", "Hallazgos 1 a 5"),
           ("Convertirlo en una prioridad que se pueda seguir",
            "Ordenar dónde y cuándo intervenir, y definir indicadores para monitorear si la situación mejora.",
            "Conclusiones y tablero de monitoreo")])

# =================================================================== 03 · DATOS Y METODOLOGÍA
lamina("met", "03 · Datos",
       f"Once años de registros oficiales, validados contra las cifras publicadas",
       "Trabajamos con las bases de la Secretaría Distrital de Movilidad y las convertimos en indicadores comparables año a año.")
a, b = st.columns([6, 6], gap="large")
with a:
    fuentes_datos([
        ("Anuarios de Siniestralidad Vial", f"{A0}–{A1}",
         "Bases oficiales en 3 tablas: 290.187 siniestros, 636.184 personas involucradas y 543.142 vehículos."),
        ("Víctimas analizadas", es(len(v)), f"{es(len(f))} fallecidas (a 30 días) y {es(len(h))} heridas."),
        ("Comparendos de tránsito", es(comp.comparendos.sum()), "Año 2021, el único publicado con hora y medio de detección."),
        ("Percepción y territorio", "3.284", "Encuestados de la Encuesta de Percepción de Riesgo Vial 2022 y límites oficiales "
                                           "de las 20 localidades."),
    ])
    fuente("Fuentes: Secretaría Distrital de Movilidad (Observatorio de Movilidad) y Datos Abiertos Bogotá")
with b:
    panel([("Consolidación", "Se unieron los anuarios 2024 (2015–2024) y 2025, homologando nombres de columnas."),
           ("Validación", f"Se verificó que el total coincidiera con lo publicado: {por_anio.loc[A0]} fallecidos en {A0} y "
                          f"{len(f1)} en {A1}."),
           ("Preparación", "Se definieron actor vial, franja día/noche, contraparte (vehículo más pesado) y localidad."),
           ("Indicadores", "Letalidad (muertos por cada 100 víctimas), % de motociclistas, % de muertes de noche y variación anual."),
           ("Herramientas", "Python para la preparación y este informe; Power BI para el tablero de monitoreo.")],
          titulo="De los datos a los indicadores")

# =================================================================== HALLAZGO 1 · VÍCTIMAS
lamina("s2", "04 · Hallazgo 1 · Quiénes mueren",
       f"Los motociclistas pasaron de {sh.loc[A0]:.0%} a {sh.loc[A1]:.0%} de los fallecidos en once años",
       "El total se mantiene, pero la composición cambió: menos peatones y muchos más motociclistas.")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Composición de los fallecidos por actor vial", f"% del total de cada año · {A0}–{A1}")
    orden = [("Motociclista", ACENTO), ("Peatón", NAVY2), ("Ciclista", GRIS1), ("Ocupante de otro vehículo", GRIS2)]
    pct = t[[o for o, _ in orden]].div(t.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for act, c in orden:
        fig.add_trace(go.Bar(x=pct.index, y=pct[act], name=act, marker=dict(color=c),
                             text=[f"{x:.0f}%" for x in pct[act]] if act in ("Motociclista", "Peatón") else None,
                             textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=11),
                             hovertemplate=act + " · %{x}: %{y:.0f}%<extra></extra>"))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, range=[0, 100])
    st.plotly_chart(estilo(fig, 420, leyenda=True), width="stretch", config=CFG)
    fuente(FUENTE)
with b:
    hm_a = hm.groupby("anio").size()
    let_m = fm.groupby("anio").size() / m.groupby("anio").size() * 100
    panel([("Más motociclistas fallecidos", f"{t.loc[A0, 'Motociclista']:.0f} en {A0} y {t.loc[A1, 'Motociclista']:.0f} en {A1} "
                                              f"({t.loc[A1, 'Motociclista'] / t.loc[A0, 'Motociclista'] - 1:+.0%})."),
           ("Menos peatones fallecidos", f"{t.loc[A0, 'Peatón']:.0f} en {A0} y {t.loc[A1, 'Peatón']:.0f} en {A1}."),
           ("La causa es el volumen, no la gravedad", f"Los heridos en moto se multiplicaron por {es(hm_a.loc[A1] / hm_a.loc[A0], 1)}, "
                                                       f"mientras la letalidad en moto bajó de {es(let_m.loc[A0], 1)} a {es(let_m.loc[A1], 1)} por cada 100 víctimas.")],
          acento=1)

# =================================================================== 03 · HORA
hh = rec.groupby(["hora", "estado"]).size().unstack(fill_value=0)
hh["let"] = hh.Fallecido / (hh.Fallecido + hh.Herido) * 100
pm = fm.groupby("anio").madrugada.mean() * 100
lamina("s3", "05 · Hallazgo 2 · Cuándo ocurren",
       f"La noche concentra el {p_f_noche:.0%} de las muertes, aunque solo registra el {p_h_noche:.0%} de los heridos",
       f"Un siniestro de noche es casi el doble de letal que uno de día. Periodo 2021–{A1}.")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Letalidad por hora del día", f"Muertos por cada 100 víctimas · 2021–{A1} · naranja = noche (6 p. m. a 6 a. m.)")
    fig = go.Figure(go.Bar(x=hh.index, y=hh.let, marker=dict(color=[ACENTO if (x >= 18 or x <= 5) else GRIS2 for x in hh.index],
                                                             cornerradius=3),
                           customdata=hh[["Fallecido", "Herido"]],
                           hovertemplate="%{x} h: %{y:.1f} muertos por cada 100 víctimas<br>%{customdata[0]} fallecidos · "
                                         "%{customdata[1]} heridos<extra></extra>"))
    fig.add_hline(y=let_dia, line_dash="dot", line_color=NAVY)
    fig.add_annotation(x=12, y=let_dia, text=f"Promedio de día: {es(let_dia, 1)}", showarrow=False, yshift=14,
                       font=dict(color=NAVY, size=12))
    fig.add_annotation(x=2, y=hh.let.max(), text=f"<b>Promedio de noche: {es(let_noc, 1)}</b>", showarrow=False, yshift=16,
                       font=dict(color=ACENTO, size=12))
    fig.update_xaxes(dtick=3, ticksuffix=" h", tickangle=0, range=[-0.6, 23.6])
    fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(estilo(fig, 420), width="stretch", config=CFG)
    fuente(FUENTE)
with b:
    panel([("Casi el doble de letal", f"De noche mueren {es(let_noc, 1)} de cada 100 víctimas; de día, {es(let_dia, 1)}."),
           ("La hora pico produce heridos, no muertes", f"El {1 - p_h_noche:.0%} de los heridos cae de día; el {p_f_noche:.0%} de los muertos, de noche."),
           ("La madrugada pesa cada vez más en moto", f"Los motociclistas fallecidos entre 0 y 5 h pasaron de {pm.loc[A0]:.0f}% en {A0} "
                                                       f"a {pm.loc[A1]:.0f}% en {A1}.")], acento=1)

# =================================================================== 04 · SEVERIDAD
lc = m.groupby(["contraparte", "estado"]).size().unstack(fill_value=0)
lc["n"] = lc.sum(axis=1)
lc["let"] = lc.Fallecido / lc.n * 100
lc = lc.sort_values("let")
x12 = lc.loc["Vehículo de carga", "let"] / lc.loc["Automóvil o taxi", "let"]
mm = m.assign(fr=np.where(m.hora <= 5, "mad", np.where(m.hora <= 17, "dia", "noc")))
lf = mm.groupby("fr").apply(lambda d: (d.estado == "Fallecido").mean() * 100, include_groups=False)
p_carga_f, p_carga_h = (fm.contraparte == "Vehículo de carga").mean(), (hm.contraparte == "Vehículo de carga").mean()
lamina("s4", "06 · Hallazgo 3 · Qué agrava el riesgo",
       f"Los choques de motocicletas con vehículos de carga son {x12:.0f} veces más letales que con automóviles",
       "La diferencia de masa determina la gravedad: pocos siniestros concentran gran parte de las muertes.")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Letalidad de los siniestros en moto según el otro vehículo",
                f"Muertos por cada 100 motociclistas víctimas · {A0}–{A1} · otro vehículo = el más pesado del siniestro")
    fig = go.Figure(go.Bar(y=lc.index, x=lc.let, orientation="h",
                           marker=dict(color=[ACENTO if i == "Vehículo de carga" else GRIS2 for i in lc.index], cornerradius=4),
                           text=[es(x, 1) for x in lc.let], textposition="outside", textfont=dict(color=TEXTO, size=13),
                           cliponaxis=False, customdata=lc[["Fallecido", "n"]],
                           hovertemplate="%{y}: %{x:.1f} muertos por cada 100 víctimas<br>%{customdata[0]} de %{customdata[1]}<extra></extra>"))
    fig.update_xaxes(showticklabels=False, range=[0, lc.let.max() * 1.15])
    fig.update_yaxes(tickfont=dict(color=TEXTO, size=13), showgrid=False)
    st.plotly_chart(estilo(fig, 400), width="stretch", config=CFG)
    fuente(FUENTE)
with b:
    panel([("Carga: 12 veces más letal", f"{es(lc.loc['Vehículo de carga', 'let'], 1)} muertos por cada 100 motociclistas víctimas, "
                                          f"frente a {es(lc.loc['Automóvil o taxi', 'let'], 1)} con un automóvil o taxi."),
           ("Pocos casos, muchas muertes", f"La carga participa en el {p_carga_f:.0%} de los motociclistas fallecidos y solo en el {p_carga_h:.0%} de los heridos."),
           ("La madrugada multiplica el riesgo", f"Un siniestro en moto entre 0 y 5 h es {es(lf['mad'] / lf['dia'], 1)} veces más letal que de día.")],
          acento=1)

# =================================================================== 05 · CONTROL
f21 = f[f.anio == 2021]
d21 = f21.groupby("hora").size().reindex(range(24), fill_value=0)
lamina("s5", "07 · Hallazgo 4 · La brecha de control",
       f"El control de velocidad se concentra de día: en 2021 las cámaras registraron {es(cc[noc_c].sum())} comparendo nocturno de {es(cc.sum())}",
       "Las muertes y el control ocurren a horas distintas. Esta es la brecha principal que identifica el informe.")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Distribución horaria de las muertes y de los comparendos por velocidad",
                "% del total del año en cada hora · 2021 · franjas sombreadas = noche")
    fig = go.Figure()
    for x0, x1 in [(-0.5, 5.5), (17.5, 23.5)]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor="#F1F3F7", opacity=1, line_width=0, layer="below")
    fig.add_trace(go.Scatter(x=comp.hora, y=cv / cv.sum() * 100, name="Comparendos por velocidad", mode="lines",
                             line=dict(color=NAVY, width=2.5, dash="dot"), hovertemplate="%{x} h: %{y:.1f}% de los comparendos<extra></extra>"))
    fig.add_trace(go.Scatter(x=d21.index, y=d21 / d21.sum() * 100, name="Personas fallecidas", mode="lines",
                             line=dict(color=ACENTO, width=4), hovertemplate="%{x} h: %{y:.1f}% de las muertes<extra></extra>"))
    fig.update_xaxes(dtick=2, ticksuffix=" h")
    fig.update_yaxes(ticksuffix="%", rangemode="tozero")
    st.plotly_chart(estilo(fig, 420, leyenda=True), width="stretch", config=CFG)
    fuente("Fuentes: comparendos 2021 (datos abiertos SDM), base del Anuario 2021 y Encuesta de Percepción de Riesgo Vial 2022 (SDM)")
with b:
    panel([("Control de día, muertes de noche", f"{cv[noc_c].sum() / cv.sum():.1%} de los comparendos por velocidad fue nocturno; "
                                                 f"ese año, el {f21.noche.mean():.0%} de las muertes fue de noche.".replace(".", ",", 1)),
           ("La percepción lo confirma", f"El {pe['Cree poco probable ser multado por conducir a alta velocidad']:.0f}% cree poco probable que "
                                         f"lo multen por velocidad (encuesta 2022)."),
           ("Y la conducta también", f"El {pe['Si la vía está desocupada, conduce a alta velocidad']:.0f}% admite acelerar cuando la vía "
                                     f"está desocupada, condición típica de la noche.")], acento=1)

# =================================================================== 06 · RESULTADOS
lamina("s6", "08 · Hallazgo 5 · Lo que funciona",
       "Donde la Secretaría gestionó la velocidad, la siniestralidad bajó",
       "Resultados reportados por la Secretaría en el Anuario 2025 (no recalculados en este informe).")
st.markdown(
    '<div class="stats">'
    '<div class="stat"><div class="v">&gt;90%</div><b>Cumplimiento</b><p>de los conductores respeta el límite en los tramos con resaltos (Av. Boyacá y otros, 118 resaltos).</p></div>'
    '<div class="stat"><div class="v">−45%</div><b>Lesionados vulnerables</b><p>en los tramos intervenidos: peatones, ciclistas y motociclistas.</p></div>'
    '<div class="stat"><div class="v">−39,6%</div><b>Fallecidos</b><p>donde hubo 8 o más operativos nocturnos de control, frente a tramos sin intervención.</p></div>'
    '</div>', unsafe_allow_html=True)
fuente("Fuente: Anuario de Siniestralidad Vial de Bogotá 2025, SDM, sección «Casos de éxito»")

# =================================================================== 07 · RECOMENDACIÓN
lamina("s7", "09 · Conclusiones",
       f"Llevar el control de velocidad a la noche, empezando por {loc_txt}",
       f"Si se mantiene el ritmo de 2021–{A1} ({prom_moto:.0f} al año), morirán unos {es(round(prom_moto * 5, -1))} motociclistas en los próximos cinco años.")
resumen([("La cifra total no baja", f"{len(f1)} fallecidos en {A1}, en la misma franja que hace una década. El problema persiste."),
         ("El riesgo cambió de lugar", f"Hoy el {sh.loc[A1]:.0%} de los fallecidos son motociclistas y el {p_f_noche:.0%} de las "
                                       f"muertes ocurre de noche, cuando un siniestro es casi el doble de letal."),
         ("El control no siguió al riesgo", f"De noche se puso el {es(p_vel_noche, 1)}% de los comparendos por velocidad. "
                                            "Donde sí se gestionó la velocidad, las muertes bajaron.")],
        acento=3, titulo="Conclusiones", ancla="concl")
st.markdown("&nbsp;")
a, b = st.columns([7, 5], gap="large")
with a:
    graf_titulo("Dónde mueren los motociclistas de noche",
                f"Mapa de calor sobre las calles · 6 p. m. a 6 a. m. · 2021–{A1} · {len(fmn)} personas · "
                "naranja más intenso = más concentración · acercar con la rueda del mouse")
    geo = json.loads((D / "localidades.geojson").read_text(encoding="utf-8"))
    conteo = fmn.localidad.value_counts().rename_axis("localidad").reset_index(name="n")
    centros = pd.read_csv(D / "dim_localidad.csv").merge(conteo, on="localidad", how="left").fillna({"n": 0})
    centros = centros[centros.localidad != "Sumapaz"]
    pts = fmn.dropna(subset=["lat", "lon"])
    fig = go.Figure(go.Densitymap(
        lat=pts.lat, lon=pts.lon, radius=11, opacity=0.85, hoverinfo="skip",
        colorscale=[[0, "rgba(232,119,46,0)"], [0.12, "rgba(246,178,107,0.35)"], [0.4, "rgba(240,140,60,0.7)"],
                    [0.7, "rgba(214,90,30,0.88)"], [1, "rgba(160,50,10,0.95)"]],
        showscale=False))
    # límites de las localidades como líneas finas (contexto territorial sin tapar las calles)
    lon_l, lat_l = [], []
    for ft in geo["features"]:
        if ft["properties"]["localidad"] == "Sumapaz":
            continue
        for pol in ft["geometry"]["coordinates"]:
            for anillo in pol[:1]:
                lon_l += [c[0] for c in anillo] + [None]
                lat_l += [c[1] for c in anillo] + [None]
    fig.add_trace(go.Scattermap(lon=lon_l, lat=lat_l, mode="lines", hoverinfo="skip",
                                line=dict(color="rgba(15,35,65,0.28)", width=1)))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=4.63, lon=-74.115), zoom=10.6),
                      height=560, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, width="stretch", config={**CFG, "scrollZoom": True})
with b:
    graf_titulo("Localidades con más motociclistas fallecidos de noche", f"Personas · 2021–{A1}")
    tt = top.sort_values()
    fig = go.Figure(go.Bar(y=tt.index, x=tt.values, orientation="h",
                           marker=dict(color=[ACENTO if i in lideres else GRIS2 for i in tt.index], cornerradius=4),
                           text=tt.values, textposition="outside", textfont=dict(color=TEXTO, size=13), cliponaxis=False))
    fig.update_xaxes(showticklabels=False, range=[0, tt.max() * 1.18])
    fig.update_yaxes(tickfont=dict(color=TEXTO, size=13), showgrid=False)
    st.plotly_chart(estilo(fig, 560), width="stretch", config=CFG)
fuente(FUENTE)
vsd = f1[f1.fecha.dt.day_of_week >= 4]
st.markdown(
    '<div class="reco">'
    '<div><small>QUÉ</small><b>Control de velocidad nocturno</b><p>Extender a la noche las cámaras y los operativos que ya redujeron '
    'hasta 39,6% los fallecidos donde se aplicaron.</p></div>'
    f'<div><small>DÓNDE</small><b>{loc_txt}</b><p>Las localidades con más motociclistas fallecidos de noche, y los corredores con tráfico de carga.</p></div>'
    f'<div><small>CUÁNDO</small><b>6 p. m. a 6 a. m., viernes a domingo</b><p>La noche concentra el {p_f_noche:.0%} de las muertes; '
    f'viernes a domingo, el {len(vsd) / len(f1):.0%}.</p></div>'
    '<div><small>CÓMO MEDIRLO</small><b>Tablero de monitoreo</b><p>% de muertes de noche, % de motociclistas y letalidad por localidad, '
    'mes a mes frente al año anterior (Power BI).</p></div>'
    '</div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="nota"><b>Alcance y limitaciones.</b> Datos: bases oficiales de los Anuarios de Siniestralidad Vial ({A0}–{A1}), '
    f'{es(len(v))} víctimas; validación: {len(f1)} fallecidos en {A1} y {por_anio.loc[A0]} en {A0}, iguales a las cifras publicadas. '
    f'No hay datos de exposición (viajes o kilómetros), por lo que el riesgo se mide por víctima y no por viaje. La noche y la carga se '
    f'asocian con mayor letalidad; no se prueba causalidad. Los comparendos son de 2021, único año publicado con hora. La proyección '
    f'mantiene el promedio 2021–{A1}. Los resultados del hallazgo 5 son los reportados por la Secretaría.</p>', unsafe_allow_html=True)
efectos()
