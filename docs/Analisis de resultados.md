# Análisis de resultados

Registro de configuraciones y mediciones.

## Configuración 1 — brazo solo

Oscilación libre, sin masa adicional.

| | |
|---|---|
| masa | 31.72 g |
| $d$ | 24.5 mm |
| $I$ | $9.46\times10^{-5}$ kg·m² |
| período medido | 662 ms |
| fricción $b$ | $1.03\times10^{-4}$ kg·m²/s |

## Configuración 2 — brazo + masa de 32.5 g a 65 mm

Masa puntual añadida del lado del motor, a 65 mm del pivote (no en el centro de masa).

| | |
|---|---|
| masa total | 64.22 g |
| $d$ | 45.0 mm |
| $m\,d$ | 2 890 g·mm |
| $I$ | $2.32\times10^{-4}$ kg·m² |
| par de gravedad en horizontal | $28.4\times10^{-3}$ N·m |
| empuje necesario para sostenerlo horizontal | $217$ mN ≈ 22 gf |

El par necesario crece **3.7 veces** respecto a la configuración 1, porque $m\,d$ pasa de
778 a 2 890 g·mm.

## Pendiente

- Barrido de duty con la configuración 2 para obtener $F(u)$.
- Repetir la oscilación libre con la masa puesta: al cambiar $I$, la fricción se
  recalcula con el nuevo valor.
