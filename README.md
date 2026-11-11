# Siniestralidad vial en Bogotá, 2015–2025

**Pregunta:** ¿Por qué Bogotá sigue registrando un número elevado de víctimas viales y dónde intervenir?

Proyecto final de Herramientas de Visualización (Maestría en Analítica). Tiene dos componentes:

| Componente | Herramienta | Para qué | Dónde |
|---|---|---|---|
| **Informe de resultados** | Streamlit | Contar el hallazgo: contexto, enfoque, datos, hallazgos y conclusiones | `app/` · enlace web (ver abajo) |
| **Tablero de monitoreo** | Power BI | Seguir los indicadores mes a mes, con meta y semáforo | `powerbi/TableroSiniestros.pbip` |

## Ver el informe
- **En la web:** el enlace de Streamlit Community Cloud que comparta el equipo.
- **En tu computador:**
  ```
  pip install -r requirements.txt
  streamlit run app/app.py
  ```

## Abrir y editar el tablero de Power BI
1. Descarga el repositorio completo (**Code → Download ZIP**) o clónalo con Git. No copies solo el `.pbip`.
2. Abre `powerbi/TableroSiniestros.pbip` con Power BI Desktop.
3. Si pide credenciales para `raw.githubusercontent.com`, elige **Anónimo** y aplica el permiso.
4. Pulsa **Actualizar**. Con Año = 2025 debe mostrar **562 fallecidos** (cifra oficial).
5. Para trabajar sin internet: *Inicio → Transformar datos → Editar parámetros → RutaDatos* = la carpeta `data/anuario_consolidado\` de tu copia (con `\` al final).

El tablero está en formato **PBIP** (texto): Git muestra qué cambió cada persona. Antes de editar, descarga los últimos cambios; al terminar, súbelos con un mensaje claro.

## Datos
| Carpeta | Contenido |
|---|---|
| `data/anuario_consolidado/*.csv.gz` | Las 3 tablas oficiales del Anuario 2015–2025 (siniestros, actores viales, vehículos), comprimidas. Las usa Power BI |
| `data/powerbi/` | Tablas que usa el informe (víctimas, dimensiones, comparendos 2021, encuesta 2022, límites de localidades) |

Fuente: Secretaría Distrital de Movilidad (Anuarios de Siniestralidad Vial, comparendos, Encuesta de Percepción de Riesgo Vial) y Datos Abiertos Bogotá (límites de localidades). Validación: 530 fallecidos en 2015 y 562 en 2025, iguales a lo publicado.

## Reproducir desde cero (opcional)
Los scripts de `src/` descargan y preparan todo (las fuentes crudas no se suben por tamaño):
`05_descargar_anuarios` → `06_cargar_anuario` → `09_modelo_powerbi` → `12_consolidar_anuario` → `13_generar_pbip_anuario` → `14_localidades_geo` → `15_comprimir_para_compartir`.

## Estructura
| Carpeta | Contenido |
|---|---|
| `app/` | Informe en Streamlit (`app.py`, `comun.py`) |
| `powerbi/` | Tablero de monitoreo (PBIP) |
| `src/` | Scripts de descarga, limpieza y generación |
| `docs/` | Hilo narrativo, plan del tablero y decisiones |
