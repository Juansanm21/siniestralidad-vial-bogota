# Storytelling — Siniestros viales de Bogotá (v2)

## Pregunta
**¿Por qué los motociclistas se volvieron las principales víctimas de las vías de Bogotá, y dónde se puede actuar?**

- **Audiencia:** Secretaría de Movilidad y tomadores de decisión en seguridad vial.
- **Respuesta:** hay muchas más motos en la vía, y mueren donde se juntan la velocidad (madrugada, grandes avenidas) y los vehículos pesados.
- **Métrica clave:** **letalidad** = fallecidos por cada 100 víctimas (heridos + fallecidos). Separa "cuántos choques hay" de "qué tan graves son".

## Hilo del dashboard (una sola página)
| # | Título (afirma algo) | Visual | Por qué ese visual |
|---|---|---|---|
| Portada | En Bogotá muere un motociclista cada 31 horas | Cifra grande + 4 tarjetas (283 muertos, 47%, 11.384 heridos, +72%) | Un dato concreto y cercano abre la pregunta |
| 01 · El cambio | Los motociclistas reemplazaron a los peatones como principales víctimas | Gráfico de pendiente 2015 → 2024 por actor vial | Con dos momentos, la inclinación cuenta el cambio sin leer ejes |
| 02 · Por qué crece | No es que cada choque sea más mortal: es que hay muchos más | Índice 2015 = 100 (heridos ×2,4, muertos ×1,7, peatones −14%) + letalidad por año (3,4 → 2,4) | El índice compara ritmos de series de tamaños distintos; la letalidad lo confirma |
| 03 · Quiénes | La víctima típica: hombre de 28 años | Barras edad × género + 2 tarjetas (82% hombres, 80% de 18 a 39) | Perfil directo para campañas |
| 04 · Cuándo | De madrugada, un choque en moto es 4 veces más mortal | Columnas de letalidad por hora (0-4 h resaltadas) | El reloj en el eje X muestra el patrón de un vistazo |
| 05 · Dónde | 10 avenidas concentran 34% de las muertes de motociclistas | Mapa de densidad + ranking de avenidas | Concentran 34% de muertes pero solo 21% de heridos: corredores más letales |
| 06 · Contra qué | Chocar contra un camión es 12 veces más mortal que contra un carro | Barras de letalidad por contraparte + 2 tarjetas | Compara gravedad, no frecuencia (los choques con carros son los más comunes) |
| Respuesta | Hay muchas más motos en la vía, y mueren donde se juntan la velocidad y los vehículos pesados | Recuadro + 3 recomendaciones con cifras | Cierre accionable |
| 07 · Explora | Filtros por año, actor vial, localidad y heridos/fallecidos | KPIs + serie trimestral + top localidades | Monitoreo e interacción |

## Recomendaciones (salen de los datos)
1. Control de velocidad de 12 a 5 a. m. en las 10 avenidas más letales (letalidad ×4).
2. Separar motos de vehículos pesados: camiones y buses están en el 45% de las muertes, pero solo en el 13% de las víctimas.
3. Formación y campañas para hombres de 18 a 39 años (80% de los fallecidos).

## Matices para la sustentación
- Se compara 2015 con 2024 porque 2025 todavía puede recibir ajustes por muertes posteriores.
- Sin datos de exposición (motos registradas o kilómetros recorridos) no se puede calcular el riesgo por motociclista. Por eso la letalidad se mide por víctima, no por población.
- Contraparte = el vehículo más pesado del siniestro distinto a la moto de la víctima. Los grupos con menos de 500 víctimas se omiten del gráfico.
- La limpieza (duplicados A/AA, reclasificación de motociclistas) no aparece en el dashboard, pero está documentada en `decisiones.md` para responder si preguntan.
