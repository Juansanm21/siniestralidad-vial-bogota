# Hilo maestro v2 — "De día, Bogotá choca. De noche, muere."

Rige el informe (Streamlit, `siniestros/app/app.py`), el dashboard (Power BI) y la sustentación. Todas las cifras salen de `src/10_cifras_hilo.py` (bases de los Anuarios SDM 2015–2025, comparendos 2021, EPRV 2022).

## Pregunta (adoptada de la propuesta del compañero)
**¿Por qué Bogotá sigue registrando un número elevado de víctimas viales y qué nos revelan los siniestros y las percepciones ciudadanas sobre dónde intervenir?**

## Big Idea
**En once años el número de muertos en las vías de Bogotá no cambió, pero la muerte se mudó a la moto y a la noche, justo cuando el control de velocidad casi no existe; por lo tanto, la ciudad debe llevar a la noche la gestión de velocidad que ya le funcionó de día.**

## Apertura (60 segundos, palabra por palabra)
> Les hago una pregunta: ¿a qué hora creen que es más peligroso moverse por Bogotá? Casi todos pensamos en la hora pico. Y tenemos razón a medias: en la hora pico es cuando más gente resulta herida. Pero no es cuando más gente muere.
> En Bogotá mueren once personas cada semana en las vías. Cinco iban en moto. Y más de la mitad de esas muertes ocurre de noche, entre las seis de la tarde y las seis de la mañana.
> De día, Bogotá choca. De noche, muere.
> Hoy les vamos a mostrar a dónde se movió la muerte en las vías en los últimos once años, y por qué la ciudad casi no la está mirando. Este análisis es para la Secretaría de Movilidad, que decide dónde y cuándo poner el control.

## Historia de 3 minutos
> Entre 2015 y 2025 murieron 5.639 personas en las vías de Bogotá, y el número no se mueve: 530 en 2015, 562 en 2025. Parece un problema estancado. **Pero** por dentro cambió todo. Cambió la víctima: los motociclistas pasaron del 31% al 45% de los muertos. No porque cada siniestro en moto sea más grave —mueren 2,5 de cada 100 víctimas, menos que antes—, sino porque los heridos en moto casi se duplicaron. **Y** cambió la hora: 6 de cada 10 heridos caen de día, pero el 53% de los muertos cae de noche, cuando un siniestro es casi el doble de letal. En moto, la madrugada es 3,5 veces más letal que el día, y chocar con un vehículo de carga, 12 veces más que con un carro. **Pero** el control no siguió a la muerte: en 2021 las cámaras de velocidad pusieron 144.996 comparendos, y de noche pusieron uno. **Por lo tanto**, no se trata de más control, sino de control a otra hora. Y sabemos que funciona: donde la Secretaría gestionó la velocidad, más del 90% respeta el límite y los fallecidos bajaron hasta 39,6%. Si nada cambia, al ritmo actual morirán unos 1.190 motociclistas más en cinco años.

## El hilo, momento a momento
| # | Título = hallazgo | Evidencia (fuente) | Transición | Visual y justificación |
|---|---|---|---|---|
| 0 | De día, Bogotá choca. De noche, muere | 10,8 muertes por semana; 4,9 en moto; 5,4 cada fin de semana (vie–dom, 50%); 53% de noche en 2021–2025 (Anuarios) | "Empecemos por lo que no cambió" | 4 tarjetas con escala humana (Knaflic: número grande; Few: valor + periodo) |
| 1 | El número no se mueve: unas 11 muertes cada semana desde hace once años | 530 (2015) → 562 (2025); rango 460–565 sin 2020; 5.639 en total | **Pero** por dentro cambió todo | Línea desde cero con franja del rango (Tufte: sin truncar; Cleveland: posición) |
| 2 | Cambió la víctima: los motociclistas pasaron de 31% a 45% | Moto 163 → 255 (+56%); peatón 257 → 220 (−14%); heridos en moto ×1,9; letalidad 3,1 → 2,5 | **Entonces** la pregunta es cuándo un siniestro mata | Pendiente con un solo acento (Bertin; Knaflic) + índice base 100 sin doble eje (Cleveland) |
| 3 | Cambió la hora: de día chocamos, de noche morimos | 61% de los heridos de día; 53% de los muertos de noche; letalidad 3,3 vs 1,9; madrugada en moto 18% → 30% (38% en 2023) | **Y** hay algo más que multiplica el riesgo | Columnas de letalidad por hora, día/noche (Munzner: tarea correcta) + línea anual |
| 4 | En moto, contra un vehículo de carga se muere 12 veces más que contra un carro | 14,6 vs 1,2 muertos por 100 víctimas; carga = 29% de los motociclistas muertos y 4% de los heridos; madrugada ×3,5 | **Pero** ¿la ciudad está mirando ahí? | Barras horizontales ordenadas desde cero (Cleveland; Mackinlay) |
| 5 | **Clímax:** el control duerme cuando más se muere | 144.996 comparendos de cámaras en 2021, 1 de noche; 0,8% de los de velocidad de noche (1.114 de 143.654); 53% de las muertes de 2021 de noche; hipótesis "velocidad" 14,2% → 5,5%; 27% acelera con vía vacía, 35% no teme multa (EPRV) | **Por lo tanto** hay que mover el control. ¿Funciona? | Dos distribuciones horarias en un mismo eje % (Cleveland; Few) |
| 6 | Donde se gestionó la velocidad, funcionó | > 90% respeta el límite; −45% lesionados vulnerables; hasta −39,6% fallecidos con operativos nocturnos; Av. Boyacá deja de ser crítica (Anuario 2025) | **Entonces**, ¿qué está en juego? | Tarjetas en verde (Few: semáforo solo para resultado) |
| 7 | Lo que está en juego: unos 1.190 motociclistas en cinco años | Promedio 2021–2025 = 237 al año × 5; 670 motociclistas muertos de noche en 2021–2025; Kennedy 70, Engativá 57, Bosa 56 | Cierre | Mapa de densidad + ranking (Bertin: valor y posición) |

## Lógica horizontal
1. De día, Bogotá choca. De noche, muere.
2. El número no se mueve.
3. Pero cambió la víctima.
4. Y cambió la hora.
5. En moto, la carga y la madrugada multiplican la muerte.
6. El control duerme cuando más se muere.
7. Donde se gestionó la velocidad, funcionó.
8. Lo que está en juego: unos 1.190 motociclistas.

## Cierre (60 segundos)
> El total no cambió en once años. Lo que cambió es quién muere y a qué hora. La muerte se mudó a la noche y a la moto; el control se quedó de día. La Secretaría ya demostró que gestionar la velocidad salva vidas. Nuestra recomendación cabe en una frase: control de velocidad nocturno, de seis de la tarde a seis de la mañana, de viernes a domingo, empezando por Kennedy, Engativá y Bosa. Y para saber si funciona, el tablero de Power BI sigue cada mes estos mismos indicadores.

## Recomendaciones
1. **Qué:** extender a la noche el control de velocidad (cámaras y operativos priorizados con datos).
2. **Dónde:** Kennedy, Engativá y Bosa primero; corredores con tráfico de carga.
3. **Cuándo:** 6 p. m. a 6 a. m., de viernes a domingo.
4. **Registro:** volver a anotar la hipótesis de velocidad en el informe policial.

## Límites que se declaran
- Sin datos de exposición: letalidad por víctima, no por viaje.
- Madrugada y carga son asociaciones, no causas probadas.
- Comparendos solo de 2021 (único año con hora publicada); el control pudo cambiar.
- Hipótesis de velocidad: juicio del agente; su caída puede ser de registro.
- La proyección solo mantiene el promedio 2021–2025.
- Resultados de la Av. Boyacá: reportados por la SDM, no recalculados.

## Guion de 12 minutos
| Min | Qué | Dónde |
|---|---|---|
| 0–1 | Apertura (pregunta + frase) | Portada del informe |
| 1–2 | Pregunta, audiencia, datos y validación (562 = oficial) | Desplegable de la portada |
| 2–3 | El número no se mueve | Cap. 1 |
| 3–4:30 | Cambió la víctima | Cap. 2 |
| 4:30–6 | Cambió la hora + carga | Caps. 3 y 4 |
| 6–7:30 | Clímax: el control duerme | Cap. 5 |
| 7:30–8:30 | La prueba y lo que está en juego | Caps. 6 y 7 |
| 8:30–10:30 | Demo Power BI: KPIs, filtro "Noche", clic en Motociclista, drill-through a Kennedy, RLS "Ver como" | Power BI |
| 10:30–11:30 | Diferencia informe vs. monitoreo + límites | — |
| 11:30–12 | Cierre | — |

## Integración con la propuesta del compañero (ChatGPT, "El riesgo que no estamos viendo")
| Su propuesta | Decisión | Por qué |
|---|---|---|
| Pregunta: ¿por qué Bogotá sigue con muchas víctimas y dónde intervenir? | **Se adopta** (decisión del equipo) | Es más amplia y conecta siniestros con percepción; el hilo responde "dónde y cuándo" |
| Título "El riesgo que no estamos viendo" | **Se adopta** como nombre del capítulo 5 (clímax) y subtítulo del proyecto | Resume exactamente el punto ciego: control de día, muerte de noche |
| Tabla "hallazgo vs. indicador" | **Se adopta** al final del informe y en la sustentación (min 10:30) | Es lo que más pide la profesora |
| Cifras: 565 fallecidos y 22.593 lesionados en 2024; 47,3% motociclistas; 364 en 2020 | **Coinciden** con nuestra base oficial | Validación cruzada entre equipos |
| Base reconstruida 2024 = 576 vs oficial 565 | **Coincide** con nuestro hallazgo: usamos solo la base oficial del Anuario | Misma conclusión metodológica |
| Filtros por sexo y tipo de víctima; matriz día × hora; exportar | **Se adoptan** en Power BI | Suman en "manejo de la herramienta" |
| Advertencia de exposición | Ya estaba en límites; se repite en la ficha de localidad | |
| Entregables en Word y HTML | **No se adoptan** | La entrega acordada es informe en Streamlit + dashboard en Power BI |
| Sin Anuario 2025 ni microdatos EPRV | Nosotros sí los tenemos | Nuestra serie llega a 2025 |

## Qué se quitó del hilo anterior y por qué
- **"10 avenidas concentran el 34%":** salía de la base SIGAT con solo 59% de vías identificadas; se reemplazó por mapa y localidades de la base oficial.
- **Letalidad ×4 de madrugada:** con la base oficial es ×3,5.
- **"Solo el 0,8% de los comparendos de 0 a 5 h":** se reemplazó por un dato más fuerte y preciso (cámaras: 1 comparendo de noche).
- **Bici percibida como más insegura que la moto:** sin datos de exposición no se sostiene como "miedo equivocado".
- **Peatones mayores, estacionalidad, Kennedy 10 de 11 años:** ciertos, pero distraen; pasan al dashboard.
