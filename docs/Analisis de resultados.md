# Análisis de resultados

Primera identificación de la fricción con datos reales.

## Datos

| | |
|---|---|
| archivo | `procesamiento/datos/registro_20261105_175149.csv` |
| muestras | 1047 (20 Hz) |
| duración | 12.2 s |
| tramo útil | 5.0 – 12.2 s (oscilación libre, 618 muestras) |

Hasta el segundo 5 el brazo está sostenido con la mano; ahí se suelta desde unos
75° y de ahí en adelante decae solo. Solo ese tramo sirve para identificar.

![[imagenes/decaimiento-20261105.png]]

## Resultados

| cantidad | valor | cómo |
|---|---|---|
| período | 662 ms | mediana entre picos consecutivos |
| $\omega_n$ medido | 9.49 rad/s | $2\pi/T$ |
| $\omega_n$ del modelo | 8.98 rad/s | $\sqrt{mgd/I}$ |
| decaimiento $\sigma$ | 0.544 s⁻¹ | ajuste de $\ln A(t)$ sobre 16 picos, $R^2 = 0.943$ |
| $b$ (con $I$ del CAD) | $1.03\times10^{-4}$ kg·m²/s | $b = 2I\sigma$ |
| $\zeta$ | 0.060 | $b/(2\sqrt{Imgd})$ |
| constante de tiempo | 1.84 s | $1/\sigma$ |

Con eso la fricción ya no es una incógnita: es viscosa, del orden de $10^{-4}$ kg·m²/s,
y la envolvente cae a la mitad cada 1.3 s.

## Chequeo cruzado de la inercia

Del período se puede despejar la inercia real, $I = mgd\,T^2/4\pi^2$:

$$
I_{\text{período}} = 8.48\times10^{-5}\ \text{kg·m}^2
\qquad\text{contra}\qquad
I_{\text{CAD}} = 9.46\times10^{-5}\ \text{kg·m}^2,
$$

o sea el modelo está **10% arriba**. La explicación más probable es que el PETG del
CAD se tomó macizo (1.27 g/cm³) y la pieza impresa tiene relleno, así que su masa real
es menor. Si se usa $I_{\text{período}}$, la fricción queda en
$b = 9.2\times10^{-5}$ kg·m²/s.

El 5.6% de diferencia en $\omega_n$ es consistente con eso y con la cuantización de
1° del AS5600.

## Limitaciones de esta corrida

- Solo 8 ciclos completos antes de que la amplitud baje al nivel del ruido (1°).
- El tramo inicial tiene energía extra del soltar con la mano: el primer pico queda
  por encima de la recta de ajuste, y por eso $A_0$ extrapolado da 98° en vez de 75°.
- La fricción de Coulomb no está en el modelo (decisión del proyecto), así que este
  $b$ absorbe también parte del rozamiento seco: es una cota superior del viscoso puro.
- El MPU6050 no está calibrado ni sellado en tiempo, así que la parte de aceleración
  no se usó todavía.

## Para la próxima

1. Soltar siempre desde el mismo ángulo y sin empujar, para tener más ciclos útiles.
2. Subir el muestreo a 100 Hz (hoy el firmware va a 20 Hz) y así tener 10 veces más
   puntos por ciclo.
3. Repetir tres veces y comparar $b$: si varía mucho, la fricción no es solo viscosa.
4. Con $b$ fijo, medir $F(u)$ por equilibrio y ya queda el modelo completo.
