# Decisiones técnicas — Siniestros viales de Bogotá

## Fuente
- **Secretaría Distrital de Movilidad (SDM)**, base de siniestralidad SIGAT (informes policiales de accidentes de tránsito).
- Servicio público ArcGIS: `https://sig.simur.gov.co/arcgis/rest/services/Accidentalidad/AccidentalidadAnalisis/FeatureServer`, publicado en https://datos.movilidadbogota.gov.co como "Siniestralidad_BD".
- Los conjuntos equivalentes del portal datosabiertos.bogota.gov.co ("Siniestros Viales Consolidados", "Histórico Siniestros", "Anuario") **ya no están públicos** (devuelven 404 / acceso denegado, revisado el 9-nov-2026).
- Descarga: `src/01_descargar.py`, por API, en bloques de 2.000 filas.

| Tabla | Filas crudas | Qué es |
|---|---|---|
| accidente | 907.363 | Un informe policial de siniestro |
| muerto | 16.055 | Personas fallecidas |
| lesionado | 485.889 | Personas heridas |
| vehiculo | 2.814.140 | Vehículos involucrados |
| causa | 1.916.111 | Hipótesis de causa del agente |
| via | 969.728 | Características de la vía |

## Privacidad
- No se descargó la **placa** de los vehículos ni la **fecha de nacimiento** de las personas.
- No se usó la tabla completa de actores viales (3,3 millones), que incluye ilesos con datos personales.

## Problemas encontrados y cómo se resolvieron (`src/02_limpiar.py`)
El registro paso a paso, con filas antes y después, queda en `data/processed/reporte_limpieza.csv`.

### 1. Siniestros duplicados (el más grave)
- **Hallazgo:** hasta 2020, cada informe aparece dos veces: una con `FORMULARIO` "A…" y otra con "AA…", con el mismo número.
- **Evidencia:** en 339.101 pares, el 99,9% tiene la misma fecha y hora, el 97,6% la misma dirección y el 100% la misma gravedad. Desde 2021 solo existe la versión "A".
- **Efecto si no se corrige:** los fallecidos de 2015 a 2019 salen al doble (≈1.086 contra ≈543 reales).
- **Decisión:** se conserva la versión "AA", que es la que enlaza con las tablas de causas y de vía. Se eliminan 178.908 siniestros duplicados.
- **Validación:** después de limpiar, la serie queda a menos de un 5% de las cifras oficiales de la SDM: 470 contra 460 en 2021, 560 contra 536 en 2022 y 564 contra 543 en 2023. La diferencia probable son las muertes ocurridas días después del siniestro.

### 2. No se debe "normalizar" el código del informe
- Se probó quitar los prefijos (A/AA) y los ceros a la izquierda para unir las tablas.
- **Resultado:** 907 mil códigos se fusionan en 465 mil; la normalización mezcla informes distintos. **Se descartó.**
- Las uniones se hacen con el `FORMULARIO` tal como viene: víctimas 100%, causas 94,5%, vehículos 100%.
- La tabla **vía** usa otro formato de `FORMULARIO`, así que se une por `CODIGO_ACCIDENTE`; cubre el 96,3% de los siniestros.

### 3. Cambio de clasificación de las víctimas en 2021
- **Hallazgo:** hasta 2020 los motociclistas y ciclistas se registraban como "CONDUCTOR"; desde 2021, como "MOTOCICLISTA" o "CICLISTA". Los "conductores" fallecidos pasan de ~230 a ~10 por año.
- **Efecto si no se corrige:** parecería que los motociclistas muertos se dispararon en 2021.
- **Decisión:** se crea `actor_vial` a partir del **vehículo en que iba la víctima** (unión por `formulario` + `codigo_vehiculo`): Peatón, Motociclista (cualquier persona en moto), Ciclista y Ocupante de otro vehículo. Se reclasificaron 37.453 víctimas.

### 4. Desaparecen los siniestros "solo daños"
- Pasan de ~20.000 al año a ~1.000 desde 2023: es un cambio en el registro, no una mejora real.
- **Decisión:** el análisis se hace sobre **víctimas** (heridos y fallecidos), cuyo registro es estable.

### 5. Otros arreglos
| Problema | Decisión |
|---|---|
| Fechas en milisegundos desde 1970 (UTC) | Se convierten a fecha de Bogotá (UTC−5) |
| Años 2001–2006 casi vacíos y 2026 incompleto | Periodo de análisis: 2015–2025 |
| `ACOMPA¿E` (tilde dañada) | Se corrige a "Acompañante" |
| Edades fuera de 0–100 (p. ej. 2008, que es un año) | Se dejan vacías (23 casos) |
| Persona en la tabla de heridos y en la de fallecidos | Cuenta solo como fallecida |
| Textos con tildes, espacios dobles o "SIN INFORMACION" | Se normalizan y "sin información" queda como vacío |
| Coordenadas fuera de Bogotá | Se validan contra una caja de Bogotá (0 casos) |
| 36% de las causas dicen solo "OTRA" | Se reporta como limitación y se excluye del ranking de causas |

## Definiciones
| Concepto | Definición |
|---|---|
| Siniestro con motociclista fallecido | Siniestro donde al menos una víctima fallecida tiene `actor_vial = Motociclista` |
| Contraparte | Otro vehículo del mismo siniestro, distinto de la moto de la víctima; "ninguno" = solo la moto |
| Madrugada | 0:00–5:59 |
| Riesgo relativo de la madrugada del fin de semana | % de muertes ocurridas en sábado/domingo de 0 a 5 h ÷ (12 / 168 horas de la semana) |
