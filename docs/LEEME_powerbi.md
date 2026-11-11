# Tablero de monitoreo · Seguridad vial en Bogotá (Power BI)

Proyecto **PBIP** (igual a los de la clase 2): todo es texto (`.tmdl` y `.json`), se puede compartir y editar con IA.

## Datos: las 3 tablas del Anuario, 2015–2025
Carpeta `siniestros/data/anuario_consolidado/` (generada con `src/12_consolidar_anuario.py`):

| Tabla | 1 fila = | Filas |
|---|---|---|
| `siniestros.csv` | 1 siniestro (con Latitud y Longitud) | 290.187 |
| `actor_vial.csv` | 1 persona involucrada | 636.184 |
| `vehiculos.csv` | 1 vehículo | 543.142 |

Unen el Excel del Anuario 2024 (2015–2024) con el del Anuario 2025 (2025). Llave: `id_siniestro` (código + anuario).
Validación: 530 fallecidos en 2015 y 562 en 2025 = cifras oficiales SDM.

## Columnas
Se traen **todas** las columnas de los 3 Excel. Las banderas `Con_…` vienen vacías cuando el siniestro no tiene esa característica: en el modelo se rellenan con "NO". El Anuario 2025 no publica Con_Velocidad, Con_Embriaguez, Con_Huecos y otras: en 2025 quedan en "NO" (no es un dato real; ojo al analizarlas). Latitud/Longitud del 2025 venían con coma decimal y se corrigieron.
Columnas agregadas en Power Query: `hora_txt`, `dia_noche`, `franja` (siniestros); `estado`, `actor`, `grupo_edad` (actor_vial); `grupo_vehiculo` (vehiculos).

## Modelo
`Calendario` → `siniestros` → `actor_vial` y `vehiculos` (uno a varios). `Calendario` se crea en Power Query.
Tabla `Medidas` en carpetas: 1 Base, 2 Indicadores, 3 Año anterior, 4 Textos y colores, 5 Lectura ejecutiva.
Roles RLS: `Direccion` (todo) y `Alcaldia_Kennedy` (Modelado → Ver como).

## Páginas (pestañas en la barra lateral; en Desktop se usan con Ctrl+clic)
1. **Monitoreo**: 6 KPI con minigráfica y variación, fallecidos por localidad, lectura ejecutiva, dona por actor y meses frente al año anterior.
2. **Tendencias**: los gráficos del informe por capítulo (año, actor, % motociclistas, letalidad por hora, madrugada en moto, carga).
3. **Ficha de localidad**: KPI, mapa de puntos de siniestros mortales (Latitud/Longitud), fallecidos por hora y por actor.
4. **Mi tablero**: lienzo para construir.

## Abrir y compartir
1. Copia la carpeta `powerbi/` completa **y** `data/anuario_consolidado/`.
2. Abre `TableroSiniestros.pbip` y pulsa **Actualizar**.
3. En otro computador: Inicio → Transformar datos → Editar parámetros → `RutaDatos` = ruta de `anuario_consolidado\` (con `\` al final).
4. Con Año = 2025 debe mostrar **562 fallecidos**.

## Regenerar
Desde `siniestros`: `..\.venv\Scripts\python src\12_consolidar_anuario.py` y luego `..\.venv\Scripts\python src\13_generar_pbip_anuario.py`. **Sobrescribe la carpeta `powerbi/`**, incluidos los cambios hechos a mano: haz una copia antes.
