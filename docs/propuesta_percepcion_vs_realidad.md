# Propuesta de historia: percepción vs. control vs. realidad

## Pregunta
**¿Estamos mirando los riesgos equivocados?**
Lo que los bogotanos creen y lo que se sanciona, frente a lo que realmente mata en las vías.

- **Audiencia:** Secretaría Distrital de Movilidad.
- **Decisión que apoya:** dónde reorientar el control y las campañas.

## Tres fuentes, tres lentes (todas de la Secretaría de Movilidad)
| Lente | Fuente | Qué aporta | Estado |
|---|---|---|---|
| **Lo que creemos** | Encuesta de Percepción de Riesgo Vial (EPRV) 2022, con microdatos de 3.284 personas, 374 preguntas y factor de expansión; informe oficial. La EPRV 2019 solo tiene informe y diccionario. | Percepción de riesgo por modo, quién se cree que es peligroso, creencias sobre velocidad, causas percibidas | Descargada en `data/raw/encuestas/` |
| **Lo que sancionamos** | Comparendos 2015–2021 (2021: 482.885 comparendos con hora, tipo de vehículo e infracción) | Dónde, cuándo y a quién se dirige el control | Explorado, sin descargar a la carpeta |
| **Lo que mata** | Siniestros SIGAT 2015–2025 (ya limpios) | Muertes, letalidad, contraparte, hora, lugar | Listo |

## Los contrastes (cifras verificadas)

### 1. ¿Quién es el peligro?
| Lente | Dato |
|---|---|
| Creemos | Los motociclistas son los que más irritan (74%) y los que más exceden la velocidad (88%). Los conductores de camión aparecen al final de la lista (51% y 54%). |
| Sancionamos | El 39% de los comparendos de 2021 fue a motos; a camiones, cerca del 1,5%. |
| Mata | Cuando muere un motociclista, en el 45% de los casos la contraparte es un camión o un bus. Chocar con un camión es **12 veces** más mortal que con un carro. |

**Mensaje:** culpamos al motociclista, pero el vehículo que convierte el choque en muerte es el pesado, y casi no se le sanciona.

### 2. ¿Cuándo?
| Lente | Dato |
|---|---|
| Creemos | El 27% admite que, si la vía está desocupada, conduce a alta velocidad. El 35% cree poco probable que lo multen por exceso de velocidad. |
| Sancionamos | Solo el 0,8% de los comparendos ocurre entre las 12 y las 5 a. m. En velocidad, el 0,4%. |
| Mata | El 28% de los motociclistas muere de madrugada, y a esa hora un choque es **4 veces** más mortal. |

**Mensaje:** el control trabaja de día; la muerte, de madrugada.

### 3. ¿Qué es inseguro?
| Lente | Dato |
|---|---|
| Creemos | La bicicleta es el modo más inseguro (86% "nada o poco seguro"), por encima de la moto (82%). |
| Mata | En 2024 murieron 283 motociclistas y 66 ciclistas: 4 veces más motociclistas. |

**Mensaje:** el miedo no está donde están los muertos. Matiz: hay más motos que bicicletas circulando.

### 4. ¿Por qué ocurren?
| Lente | Dato |
|---|---|
| Creemos | Las causas percibidas son el alcohol (90%), el exceso de velocidad (88%) y el mal estado de las vías (88%). |
| Mata | En los siniestros con motociclista fallecido, los agentes registran: desobedecer señales 9,5%, transitar entre vehículos 7,3%, exceso de velocidad 6,8%, embriaguez 4,5% y huecos 2,8%. |

**Mensaje:** se sobreestima el alcohol y el estado de las vías, y se subestiman las maniobras. Matiz: el 36% de las causas registradas dice solo "otra".

### 5. Sesgo de optimismo (cierre humano)
- El 78% de los conductores cree que los demás conducen peor que él.
- El 68% cree que "pasan pocos siniestros para la cantidad de imprudencias".

## Estructura sugerida del dashboard
1. **Portada:** "En Bogotá muere un motociclista cada 31 horas. ¿Estamos mirando los riesgos equivocados?"
2. **01 · Lo que mata:** síntesis de lo que ya tenemos (motociclistas = 47% de las muertes, madrugada, camiones, 10 avenidas).
3. **02 · ¿Quién es el peligro?** Barras comparadas: percepción (% que cree que excede la velocidad) frente a comparendos (% de multas) y letalidad como contraparte, por tipo de vehículo.
4. **03 · ¿Cuándo?** Una línea por hora con tres series indexadas: % de comparendos, % de muertes de motociclistas y letalidad.
5. **04 · ¿Qué es inseguro?** Gráfico de pendiente o barras pareadas: % que percibe inseguro frente a % de muertes por modo.
6. **05 · ¿Por qué?** Barras pareadas: causa percibida frente a causa registrada.
7. **Respuesta + recomendaciones:**
   - Control de velocidad nocturno.
   - Control y diseño vial para vehículos pesados.
   - Campañas que corrijan percepciones (las maniobras matan más que los huecos).
8. **Explora:** filtros.

## Limitaciones a declarar
- Los años no coinciden exactamente: encuesta 2022, comparendos 2021 y siniestros 2021–2024. Se comparan proporciones y patrones, no cifras del mismo año.
- No hay datos de exposición (km recorridos por modo y hora), así que el riesgo se mide por víctima, no por viaje.
- La EPRV 2022 se debe ponderar con el factor de expansión `fexp`. Las cifras de este documento salen del informe oficial y se recalcularán con los microdatos.
