# Cómo se calculó la inercia y el centro de masa

Solo el procedimiento y el código. Modelo en `modelado/`, script `modelado/ensamblar.py`.

## Fórmulas

$$
m = \sum_i m_i, \qquad
d = \frac{\sum_i m_i d_i}{\sum_i m_i}, \qquad
I = \sum_i \left(I_i + m_i d_i^2\right)
$$

$d_i$ = distancia del centro de masa de la pieza $i$ al eje del pivote.
$I_i$ = inercia propia de la pieza respecto a la recta paralela al pivote que pasa por
su centro de masa (teorema de Steiner).

## Pesos y densidades

```python
RHOS = {"Brazo": 1.27e-6, "Brida": 7.85e-6, "Tornillos": 7.85e-6}  # kg/mm3
MOT_MASA_G = 2.5   # pesado
MPU_MASA_G = 2.0   # pesado
```

PETG 1.27 g/cm³, acero 7.85 g/cm³. Motor y MPU no se pesan por volumen: se meten como
masa puntual conocida.

## De FreeCAD

```python
sols = forma.Solids
vt   = sum(s.Volume for s in sols)                    # mm3

# centro de masa ponderado por volumen
cm = Vector(sum(s.CenterOfMass.x*s.Volume for s in sols)/vt,
            sum(s.CenterOfMass.y*s.Volume for s in sols)/vt, 0)

# inercia: MatrixOfInertia viene en mm5 con densidad 1
#   -> x rho[kg/mm3] x 1e-6  da kg·m2
Iz = sum(s.MatrixOfInertia.A33 * rho * 1e-6 for s in sols)
```

`MatrixOfInertia.A33` es la inercia respecto al eje Z **del centro de masa** de ese
sólido. Comprobación del factor de escala: una caja de 100×10×10 mm devuelve
`A11 = 166666`, y a mano $m(y^2+z^2)/12 = 10^4 \cdot 200/12 = 166666$.

Dos trampas del API:

```python
# Part.Shape no tiene CenterOfMass; hay que ir al solido
forma.CenterOfMass            # AttributeError
forma.Solids[0].CenterOfMass  # ok

# el Shape ya lleva aplicado el Placement: el centroide viene en coordenadas
# globales, asi que NO hay que volver a transformarlo
```

## Steiner y suma

```python
d  = math.hypot(cm.x - PIV[0], cm.y - PIV[1]) / 1000.0   # m
Ip = Iz + m * d**2
```

## Resultado

| pieza | masa | $d_i$ | $I_i$ | $I_i + m_i d_i^2$ |
|---|---|---|---|---|
| brazo PETG | 13.40 g | 32.9 mm | 367 g·cm² | 512 g·cm² |
| brida acero | 10.11 g | 0.0 mm | 4 g·cm² | 4 g·cm² |
| motor | 2.50 g | 130.7 mm | — | 427 g·cm² |
| MPU6050 | 2.00 g | 0.3 mm | — | 1 g·cm² |
| 4 tornillos M3 | 3.71 g | 2.6 mm | — | 0 g·cm² |
| **total** | **31.72 g** | **24.5 mm** | | **945 g·cm² = 9.45×10⁻⁵ kg·m²** |

El motor se modela como cilindro de 7 × 16 mm con eje perpendicular al brazo y centro a
130.7 mm (punto medio de los dos agujeros de la punta). Su inercia propia
$\tfrac12 m r^2 = 1.5\times10^{-8}$ kg·m² es despreciable frente a $m d^2 = 4.3\times10^{-4}$.
