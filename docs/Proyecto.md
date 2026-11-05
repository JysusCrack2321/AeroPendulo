# Proyecto: aeropéndulo

![[imagenes/planta.svg]]

![[imagenes/cuerpo-libre.svg]]

![[imagenes/centro-de-masa.svg]]

## Ensamble

![[imagenes/ensamble.png]]

Análisis del conjunto (CAD + pesada):

| pieza          | masa        | d al pivote |
| -------------- | ----------- | ----------- |
| brazo PETG     | 13.40 g     | 32.9 mm     |
| brida acero    | 10.11 g     | 0.0 mm      |
| motor          | 2.50 g      | 130.7 mm    |
| MPU6050        | 2.00 g      | 0.3 mm      |
| 4 tornillos M3 | 3.71 g      | 2.6 mm      |
| **total**      | **31.72 g** | **24.5 mm** |

$m = 31.7$ g, $d = 24.5$ mm, $I = 9.45\times10^{-5}$ kg·m², $R = 130.7$ mm (centro del motor), $L = 145$ mm (punta de la placa).

## Notas

- [[Desarrollo matematico]]
- [[Analisis de resultados]]
- [[Como se calculo la inercia]]

## Archivos del repo

En `AeroPendulo/modelado`: `ensamble.FCStd` (editable), `ensamble.step` y
`steps/` con cada pieza suelta (brazo, brida, motor, mpu, tornillos).
