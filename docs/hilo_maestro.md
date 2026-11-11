# Hilo maestro — "El número no cambió; cambió quién muere"

Documento rector del **informe analítico (Streamlit)**, el **dashboard de monitoreo (Power BI)** y la sustentación (12 min). Los momentos 0–9 van en el informe; el 10 es el dashboard. Consolida `estructura_historia.md`, `propuesta_percepcion_vs_realidad.md` y los análisis previos. Cifras: `.claude/skills/sustentacion-visualizacion/references/proyecto.md`.

## Contexto (Knaflic, paso 0)
- **Quién:** Secretaría Distrital de Movilidad; en monitoreo, cada alcaldía local.
- **Qué queremos que haga:** concentrar control de velocidad y gestión moto–carga en madrugada, fin de semana y corredores críticos.
- **Cómo:** sustentación en vivo de 12 min con Power BI + informe leído.

## Big Idea (una frase)
**En 11 años el número de muertos en las vías de Bogotá casi no cambió, pero el riesgo se movió a la moto, a la madrugada y a las grandes avenidas junto a vehículos pesados; por lo tanto, la ciudad debe llevar el control a esos lugares y horas, como ya funcionó en la Av. Boyacá.**

## Historia de 3 minutos (para decir en voz alta)
> Entre 2015 y 2025 murieron 5.639 personas en las vías de Bogotá, y cada año son casi las mismas: 530 en 2015, 562 en 2025. **Pero** detrás de ese número estable, cambió quién muere: los motociclistas pasaron de 3 a casi 5 de cada 10 muertos. No es que cada choque sea más grave —la letalidad está estable—: es que los heridos en moto se duplicaron. **Y** cambió cuándo: las muertes de motociclistas de madrugada pasaron del 18% al 30–38%, y a esa hora un choque es 4 veces más mortal. Ocurren en 10 avenidas que concentran un tercio de las muertes, y contra camiones, que son 12 veces más letales que un carro. **Pero** la ciudad no está mirando ahí: solo el 0,8% de las multas se pone de madrugada, la velocidad aparece cada vez menos en los informes y uno de cada cuatro conductores admite acelerar cuando la vía está vacía. **Por lo tanto**, la respuesta no es más control en general, sino control donde se movió la muerte. Y sabemos que funciona: en la Av. Boyacá, gestionando la velocidad, 9 de cada 10 respetan el límite y los heridos vulnerables bajaron 45%.

## El hilo, momento a momento
Conectores entre momentos: **pero / por lo tanto** (no "y además").

| # | Momento (arco) | Título = hallazgo | Evidencia clave | Visual y por qué (autor) | Capítulo del informe (Streamlit) |
|---|---|---|---|---|---|
| 0 | Gancho | En Bogotá muere un motociclista cada 34 horas | 255 motociclistas fallecidos en 2025 | Número grande + pregunta (Knaflic: una cifra = número grande) | 1 |
| 1 | Situación | El número no cambió: ~500 muertos al año desde 2015 | 530 (2015) · 562 (2025); 5.639 en 11 años | Línea con banda del rango; eje desde cero (Tufte) | 1 |
| 2 | Complicación | Pero cambió quién muere: los motociclistas pasaron de 31% a 47% | % moto por año; 69% de muertes con moto involucrada | Pendiente 2015→2024 por actor, moto en naranja (Cleveland: posición; Bertin: tono para resaltar) | 2 |
| 3 | Explicación | No son choques más graves: son muchos más | Heridos moto ×2,2; letalidad estable 2,2–2,5 | Índice 2015 = 100 en un solo eje (Cleveland: una escala común) | 2 |
| 4 | Cuándo | La muerte se mudó a la madrugada | Moto 0–5 h: 18% → 30–38%; letalidad ×4; 50% en fin de semana | Columnas por hora con 0–5 h resaltadas; matriz día × hora (Bertin: valor para intensidad) | 3 |
| 5 | Dónde | 10 avenidas concentran un tercio de las muertes de motociclistas | 34% de muertes vs 21% de heridos; Kennedy 1.ª en 10 de 11 años | Mapa de calor + ranking de avenidas (Bertin: posición para ordenar) | 3 |
| 6 | Contra qué | Contra un camión es 12 veces más mortal que contra un carro | 15,3 vs 1,3 muertos/100 víctimas; carga en ~20% de muertes cada año | Barras horizontales ordenadas desde cero (Cleveland: longitud) | 3 |
| 7 | Contradicción (clímax) | El control trabaja de día; la muerte, de madrugada | 0,8% de comparendos de 0 a 5 h; velocidad en informes 14% → 5,5%; 27% acelera con vía vacía; 35% cree que no lo multan | Dos series alineadas por hora en un eje (muertes vs comparendos, en %) + 3 tarjetas EPRV (Few: comparación explícita) | 4 |
| 8 | Prueba | Donde se gestionó la velocidad, funcionó | Av. Boyacá: > 90% respeta el límite, −45% heridos vulnerables; controles priorizados hasta −39,6% fallecidos; 2025: −2,3% | Tarjetas antes/después (Few: valor + comparación) | 5 |
| 9 | Acción | Llevar el control a donde se movió la muerte | 3 recomendaciones con lugar y hora | Lista numerada con cifra de respaldo (Knaflic: llamado a la acción) | 5 |
| 10 | Explorar | Monitoreo para seguir cada indicador | KPIs con periodo, comparación y meta; RLS por localidad | Tablero F + filtros + drill-through + RLS (Few, Segel y Heer: martini) | **Dashboard en Power BI** |

## Recomendaciones (resolución)
1. **Control de velocidad de madrugada y fin de semana** en las 10 avenidas más letales (0–5 h concentra 30–38% de las muertes de motociclistas y apenas 0,8% de los comparendos).
2. **Gestión moto–carga**: carriles, horarios de cargue y puntos ciegos en corredores con tráfico pesado (carga presente en ~1 de cada 5 muertes, cada año).
3. **Replicar el modelo Av. Boyacá** (resaltos + controles priorizados por datos) en los siguientes corredores críticos.
4. **Mejorar el registro de hipótesis** en el informe policial: lo que no se registra no se gestiona.

## Lógica horizontal (solo títulos, en orden)
1. En Bogotá muere un motociclista cada 34 horas.
2. El número no cambió: ~500 muertos al año desde 2015.
3. Pero cambió quién muere: los motociclistas pasaron de 31% a 47%.
4. No son choques más graves: son muchos más.
5. La muerte se mudó a la madrugada.
6. 10 avenidas concentran un tercio de las muertes de motociclistas.
7. Contra un camión es 12 veces más mortal que contra un carro.
8. El control trabaja de día; la muerte, de madrugada.
9. Donde se gestionó la velocidad, funcionó.
10. Llevar el control a donde se movió la muerte.

## Cautelas de redacción (clase: "El relato que exagera")
- Decir "la velocidad **se registra menos** en los informes", no "desapareció".
- La letalidad ×4 de madrugada y ×12 con camión son asociaciones observadas, no causas probadas.
- El 0,8% de comparendos nocturnos también refleja menos tráfico de noche; el punto es que coincide con la mayor letalidad.
- Comparamos patrones entre fuentes de años distintos (EPRV 2022, comparendos 2021, siniestros 2015–2025).
