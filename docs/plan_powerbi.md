# Plan del dashboard de monitoreo en Power BI

Propósito: **monitorear** (no repetir el informe). Pregunta del tablero: *¿cómo evolucionan las muertes viales y sus factores de riesgo, y qué localidad requiere atención este periodo?* Usuarios: dirección de seguridad vial (toda la ciudad) y alcaldías locales (su localidad, con RLS).

## 1. Cargar datos (carpeta `siniestros/data/powerbi/`)
Obtener datos → Texto/CSV (origen UTF-8) para: `fact_victima`, `dim_fecha`, `dim_hora`, `dim_localidad`, `dim_actor`, `seg_usuario_localidad`. Opcionales: `res_comparendos_hora`, `res_percepcion_eprv`.
Tipos: `fecha` = Fecha; `anio`, `hora` = número entero; `lat`, `lon`, `lat_centro`, `lon_centro` = decimal (categoría de datos Latitud/Longitud).

## 2. Modelo (vista Modelo)
| Desde (muchos) | Hacia (uno) | Nota |
|---|---|---|
| fact_victima[fecha] | dim_fecha[fecha] | Marcar dim_fecha como tabla de fechas |
| fact_victima[hora] | dim_hora[hora] | |
| fact_victima[localidad] | dim_localidad[localidad] | |
| fact_victima[actor] | dim_actor[actor] | Ordenar `actor` por `actor_orden` |
| seg_usuario_localidad[localidad] | dim_localidad[localidad] | Dirección de filtro **Ambas** + "Aplicar filtro de seguridad en ambas direcciones" |
Ordenar `dim_fecha[mes]` por `mes_num`, `dia_semana` por `dia_semana_num`, `dim_hora[franja]` por `franja_orden`.

## 3. Medidas DAX (tabla nueva "Medidas")
```
Fallecidos = CALCULATE(COUNTROWS(fact_victima), fact_victima[estado] = "Fallecido")
Lesionados = CALCULATE(COUNTROWS(fact_victima), fact_victima[estado] = "Herido")
Fallecidos AA = CALCULATE([Fallecidos], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
Lesionados AA = CALCULATE([Lesionados], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
Var Fallecidos = DIVIDE([Fallecidos] - [Fallecidos AA], [Fallecidos AA])
Var Lesionados = DIVIDE([Lesionados] - [Lesionados AA], [Lesionados AA])
% Motociclistas = DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"), [Fallecidos])
% Motociclistas AA = CALCULATE([% Motociclistas], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
% De noche = DIVIDE(CALCULATE([Fallecidos], dim_hora[dia_noche] = "Noche (18-5 h)"), [Fallecidos])
% De noche AA = CALCULATE([% De noche], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
% Moto madrugada = DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista", dim_hora[hora] <= 5),
                          CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"))
% Con carga = DIVIDE(CALCULATE([Fallecidos], fact_victima[con_carga] = 1), [Fallecidos])
% Con carga AA = CALCULATE([% Con carga], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
Letalidad moto = DIVIDE(CALCULATE([Fallecidos], dim_actor[actor] = "Motociclista"),
                        CALCULATE([Fallecidos] + [Lesionados], dim_actor[actor] = "Motociclista")) * 100
Letalidad moto AA = CALCULATE([Letalidad moto], SAMEPERIODLASTYEAR(dim_fecha[fecha]))
Fallecidos por semana = DIVIDE([Fallecidos], DISTINCTCOUNT(dim_fecha[fecha]) / 7)
Color variacion = IF([Var Fallecidos] > 0, "#E05A4E", "#2E9E5B")
Titulo Monitoreo =
VAR loc = IF(ISFILTERED(dim_localidad[localidad]), SELECTEDVALUE(dim_localidad[localidad], "varias localidades"), "Bogotá")
VAR act = IF(ISFILTERED(dim_actor[actor]), SELECTEDVALUE(dim_actor[actor], "varios actores"), "todas las víctimas")
VAR fr = IF(ISFILTERED(dim_hora[dia_noche]), " · " & SELECTEDVALUE(dim_hora[dia_noche]), "")
RETURN "Fallecidos · " & act & " · " & loc & " · " & SELECTEDVALUE(dim_fecha[anio], "varios años") & fr
```
**Validar** con una tarjeta y año = 2025: Fallecidos 562, Lesionados 19.605, % Motociclistas 45,4%, % Moto madrugada 29,8%, % Con carga 20,1%, Letalidad moto 2,48.

## 4. Página 1 · Monitoreo general (lienzo 16:9, lectura en F)
```
[ Título dinámico                                   | etiqueta rol RLS · fecha de corte ]
[ Año | Mes | Localidad | Actor vial | Día/Noche | Con carga ]        ← segmentadores
[ KPI Fallecidos | Lesionados | % Motociclistas | % De noche | % Con carga | Letalidad moto ]
[ Línea mensual: año actual vs anterior      | Mapa de burbujas por localidad ]
[ Columnas por hora | Barras por actor vial  | Matriz de localidades con variación ]
[ Nota al pie: fuente, definición a 30 días, fecha de corte ]
```
| Visual | Tipo exacto | Campos | Formato |
|---|---|---|---|
| Título | Cuadro de texto → valor dinámico, o Tarjeta | `[Titulo Monitoreo]` | 18 pt, sin fondo |
| Segmentadores | Segmentación de datos (desplegable) | dim_fecha[anio] (selección única, 2025), dim_fecha[mes], dim_localidad[localidad], dim_actor[actor], dim_hora[dia_noche], fact_victima[con_carga]; en el panel de filtros: fact_victima[sexo] y fact_victima[estado] (tipo de víctima) | Franja superior; **Ver → Sincronizar segmentaciones** en las 3 páginas |
| 6 KPIs | **Tarjeta (nueva)** | Valor: medida; Etiqueta de referencia: su medida AA y la variación | Color de la variación con fx: verde si baja, rojo si sube |
| Tendencia | Gráfico de líneas | Eje X dim_fecha[mes]; Y `[Fallecidos]` y `[Fallecidos AA]` | Actual naranja #F28C38 sólida; anterior gris punteada; eje Y desde 0; título "Fallecidos por mes · año actual vs anterior" |
| Mapa | **Azure Maps** (o "Mapa" si no está habilitado) | Latitud dim_localidad[lat_centro]; Longitud [lon_centro]; Tamaño `[Fallecidos]`; Información sobre herramientas: localidad, `[Var Fallecidos]` | Color de burbuja fx → valor de campo `[Color variacion]`; estilo de mapa gris oscuro |
| Hora | Gráfico de columnas agrupadas | X dim_hora[hora]; Y `[Fallecidos]` | Color por regla: hora ≤ 5 o ≥ 18 naranja; resto gris |
| Actor | Gráfico de barras agrupadas | Y dim_actor[actor]; X `[Fallecidos]` | Motociclista naranja, resto gris; etiquetas de datos activas; el clic filtra todo |
| Matriz | Matriz | Filas dim_localidad[localidad]; Valores `[Fallecidos]`, `[Fallecidos AA]`, `[Var Fallecidos]` | Iconos de formato condicional en la variación; ordenar por Fallecidos |
Cuatro claves (Tufte) en cada visual: periodo (en el título dinámico), unidad (personas, %), comparación (vs año anterior) y fuente (nota al pie).

## 5. Página 2 · Ficha de localidad (drill-through)
- Arrastrar dim_localidad[localidad] a **Obtención de detalles**. Queda el botón Atrás.
- Contenido: título `"Ficha · " & SELECTEDVALUE(dim_localidad[localidad])`, los 6 KPIs, línea anual 2015–2025 de `[Fallecidos]`, columnas por hora, barras por actor y **mapa de puntos** (Azure Maps con fact_victima[lat]/[lon], filtro de nivel visual estado = "Fallecido").
- Uso: clic derecho sobre una localidad en la matriz o el mapa → Obtener detalles → Ficha.

## 6. Página 3 · Tendencias 2015–2025
- Línea anual `[Fallecidos]`; línea `[% Motociclistas]`; línea `[% De noche]` y `[% Moto madrugada]`; línea `[% Con carga]`; línea `[Letalidad moto]`. Un gráfico por indicador (sin doble eje), mismos colores.
- Sin segmentador de año en esta página (quitarlo de la sincronización).

## 6b. Aportes integrados de la propuesta del compañero (ChatGPT)
- **Matriz día × hora** en la página 3: visual Matriz con filas dim_fecha[dia_semana], columnas dim_hora[hora], valores `[Fallecidos]`, formato condicional de color de fondo en una sola escala (Bertin: valor para intensidad).
- **Exportar datos filtrados:** habilitar en Archivo → Opciones → Exportar datos (los usuarios técnicos descargan lo que filtraron).
- **Serie oficial separada de cálculos propios:** todas las medidas salen de la base del Anuario (2024 = 565, 2025 = 562); no mezclar con la base SIGAT reconstruida (2024 ≈ 576). Indicarlo en la nota al pie.
- **Advertencia de exposición** en la ficha de localidad: "más víctimas no significa mayor riesgo individual; no hay datos de exposición al tránsito".

## 7. Interacciones
- **Filtro cruzado:** Formato → Editar interacciones; que el clic en Actor y en Hora filtre (no resalte) los demás.
- **Tooltip de página:** página nueva tamaño "Información sobre herramientas" con `[Fallecidos]`, `[% De noche]`, `[% Motociclistas]`; asignarla al mapa y a la matriz.
- **Marcadores:** "Todo el día" y "Solo noche" (segmentador Día/Noche) con dos botones; sirven para la demo.
- **Botón "Borrar filtros":** marcador con todos los segmentadores vacíos.

## 8. RLS por localidad
**Estático:** Modelado → Administrar roles → Nuevo `Alcaldia_Kennedy` → tabla dim_localidad → `[localidad] = "Kennedy"`. Crear también `Direccion` sin filtro.
**Dinámico:** rol `Alcaldia_dinamico` → tabla seg_usuario_localidad → `[correo] = USERPRINCIPALNAME()`. Requiere la relación bidireccional con filtro de seguridad (sección 2).
**Probar:** Modelado → Ver como → marcar el rol (y "Otro usuario" = `regional.sur@ejemplo.gov.co` para el dinámico: debe ver solo Bosa y Ciudad Bolívar). Un usuario sin filas ve el tablero vacío: es lo correcto.
**En la sustentación:** mostrar Ver como → Kennedy y decir que el segmentador es una selección del lector y RLS es seguridad del modelo. Si no se publica, declarar que se demostró en Desktop.

## 9. Diseño (coherente con el informe)
- Fondo #0B1220; tarjetas #121B2D; texto #E6EDF5; secundario #8A97AD; **acento #F28C38** (motociclistas y noche); gris #56627A para el resto; verde #2E9E5B / rojo #E05A4E solo para variación.
- Una tipografía (Segoe UI); títulos 12–14 pt, KPI 28 pt; márgenes 24 px; sin bordes, sombras ni 3D; ejes desde cero; etiquetas directas.
- Ver → Tema → Personalizar tema actual con esos colores (así todos los visuales los heredan).

## 10. Lista de verificación contra la rúbrica
| Criterio | Evidencia |
|---|---|
| Narrativa y fluidez (20%) | El tablero usa los mismos indicadores del informe; título dinámico; se presenta como "seguir lo que el informe explicó" |
| Manejo de la herramienta (25%) | Modelo estrella, DAX con comparación anual, tarjetas nuevas, segmentadores sincronizados, drill-through, tooltip de página, marcadores, RLS estático y dinámico |
| Dominio técnico (25%) | Validación 562 = Anuario; definición a 30 días; letalidad; límites declarados |
| Coherencia visual (15%) | Misma paleta que el informe; un acento; lectura en F; 4 claves en cada visual |
| Tiempo y estructura (15%) | Demo de 2 minutos ensayada: filtro Noche → clic Motociclista → ficha Kennedy → Ver como |

## Primeros 3 pasos
1. Cargar los 6 CSV y crear las relaciones de la sección 2.
2. Crear las medidas y validar las seis cifras de 2025.
3. Armar la franja de segmentadores y las 6 tarjetas KPI de la página 1.
