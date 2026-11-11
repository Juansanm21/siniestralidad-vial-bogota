# Estructura de la historia — 11 años de siniestralidad en Bogotá (2015–2025)

Fuente principal: **bases oficiales de los Anuarios de Siniestralidad Vial** (Observatorio de Movilidad).
- La base 2024 trae la serie 2015–2024 y la base 2025 completa el último año.
- Usan la definición oficial de fallecido: muere dentro de los **30 días** posteriores al siniestro.
- Las cifras coinciden con las publicadas (562 fallecidos en 2025).
- Cálculos: `src/07_patrones_anuario.py`.

Fuentes complementarias:
- **EPRV 2022:** percepción del riesgo vial.
- **Comparendos 2021:** control.
- **Informe del Anuario 2025:** caso Av. Boyacá.

## Arco narrativo
**Situación → complicación → contradicción → resolución → recomendación**

### 0. Portada — el gancho
"En 11 años murieron **5.639 personas** en las vías de Bogotá. El total casi no cambió (530 en 2015, 562 en 2025), pero cambió **quién muere, cuándo y por qué**."

### 1. Situación — lo que NO cambió (patrones estructurales)
| Constante | Dato año a año | Visual sugerido |
|---|---|---|
| Total de muertos estable | 482–565 cada año (salvo 2020: 364) | Línea con banda del rango |
| Perfil de la víctima en moto | Edad mediana entre **27 y 30** años los 11 años; 55–71% tiene de 20 a 34 | Línea plana de edad mediana |
| Vehículos de carga | Presentes en **~1 de cada 5 muertes** cada año (16–22%) | Barras por año casi iguales |
| Geografía | **Kennedy** es la localidad con más muertes en 10 de 11 años; el top 5 casi no cambia | Tabla de ranking por año (bump chart) |
| Sin estacionalidad estable | El mes con más muertes cambia cada año | Mapa de calor mes × año |

**Mensaje:** el problema es estructural, no coyuntural.

### 2. Complicación — lo que SÍ cambió (tendencias)
| Tendencia | 2015 → 2024/2025 | Visual |
|---|---|---|
| Motociclistas como víctimas | 31% → **47%** de los muertos (2024); 45% en 2025 | Área 100% apilada por actor |
| Moto involucrada en la muerte (como víctima o como vehículo que golpea) | 46% → **69%** (2024) | Línea |
| Motociclistas heridos | 5.166 → 11.393 (**×2,2**) | Índice 2015 = 100 |
| Letalidad en moto | Estable en ~2,2–2,5 muertos por cada 100 víctimas desde 2018 | Línea plana → hay más choques, no choques más graves |
| Madrugada (0–5 h) en muertes de motociclistas | 18% → **38%** (2023), 30% (2025) | Línea, el cambio más fuerte |
| Fin de semana (vie–dom) | 40–46% → **50%** (2024–2025) | Línea |
| Peatones de 60 años o más | 40% → **60%** de los peatones fallecidos (2024) | Línea |

**Mensaje:** la siniestralidad se trasladó a la moto, a la noche y al fin de semana.

### 3. Contradicción — lo que se dice y se controla vs. lo que pasa
| Lente | Dato |
|---|---|
| **Registro** | Las muertes con hipótesis de **velocidad** en el informe policial bajaron de 12–14% a **5,5%** (2024), justo cuando más se mueren motociclistas de madrugada. |
| **Percepción** (EPRV 2022) | El 88% cree que la velocidad es de las principales causas; el 27% admite acelerar cuando la vía está vacía; el 35% cree que no lo van a multar. |
| **Control** (comparendos 2021) | Solo el **0,8%** de los comparendos se impone entre 0 y 5 h. A camiones va ~1,5% de las multas, aunque están en el ~20% de las muertes. |

**Mensaje:** la velocidad casi desapareció de los informes y del control nocturno, pero no de las vías.

Matiz: la baja de "velocidad" en los informes puede reflejar cambios en cómo se registra la hipótesis, no menos velocidad real.

### 4. Resolución — 2025, la primera señal de que se puede
- 2025 es el primer año de baja después de la pandemia: 565 → **562** muertes; heridos −13,6%.
- **Av. Boyacá:** con 102 resaltos para gestionar la velocidad, más del 90% de los conductores respeta el límite, los heridos vulnerables bajan más del 45% y la avenida deja de ser corredor crítico (Anuario 2025).
- **Controles nocturnos priorizados por datos:** en los tramos con 8 o más operativos, las muertes cayeron hasta 39,6% (Anuario 2025).

**Mensaje:** donde se gestionó la velocidad, las muertes bajaron.

### 5. Recomendación (cierre)
1. Llevar el control de velocidad a la **madrugada y el fin de semana**, cuando ocurre el 30–38% de las muertes de motociclistas.
2. Gestionar la convivencia **moto – vehículo de carga**, presente cada año en ~20% de las muertes.
3. Replicar el modelo **Av. Boyacá** en los corredores críticos.
4. Mejorar el **registro de hipótesis**: si la velocidad no se anota, no se puede gestionar.

## Limitaciones
- 2025 no trae las banderas de velocidad, embriaguez y huecos; las tendencias de hipótesis llegan hasta 2024.
- No hay datos de exposición (motos en circulación por año). El Anuario 2025 menciona que el registro de motos creció 32% frente a 2024 en Bogotá y Cundinamarca; sirve como contexto, no como serie.
- Las hipótesis son el juicio del agente de tránsito, no causas comprobadas.
