# Desarrollo matemático del aeropéndulo

Modelo dinámico del brazo. *(La linealización y la función de transferencia están en
revisión y por ahora no se incluyen.)*

![[imagenes/cuerpo-libre.svg]]

## 1. Punto de partida

El brazo gira alrededor del pivote. Se mide el ángulo $\theta$ desde la horizontal,
positivo hacia arriba, y el empuje $F$ actúa perpendicular al brazo, en la posición
del motor.

| símbolo | significado | valor |
| ------- | ---------------------------------------- | ------------------------------------- |
| $R$     | pivote → centro del motor (donde actúa $F$) | $130.7\ \text{mm} = 0.1307\ \text{m}$ |
| $L$     | pivote → punta de la placa | $145\ \text{mm}$ |
| $d$     | pivote → centro de masa del conjunto | $24.5\ \text{mm}$ |
| $I$     | momento de inercia respecto al pivote | $9.45\times10^{-5}\ \text{kg·m}^2$ |
| $m$     | masa del conjunto ensamblado | $31.7\ \text{g}$ |
| $b$     | fricción viscosa | $1.03\times10^{-4}\ \text{kg·m}^2/\text{s}$ (medido) |

### Datos del conjunto (modelo 3D + pesada)

| pieza | masa | $d_i$ | aporte a $I$ |
| -------------- | -------- | -------- | ------------ |
| brazo PETG | 13.40 g | 32.9 mm | 512 g·cm² |
| brida (acero) | 10.11 g | 0.0 mm | 4 g·cm² |
| motor | 2.50 g | 130.7 mm | 427 g·cm² |
| MPU6050 | 2.00 g | 0.3 mm | 1 g·cm² |
| 4 tornillos M3 | 3.71 g | 2.6 mm | 0 g·cm² |
| **total** | **31.72 g** | **24.5 mm** | **945 g·cm²** |

![[imagenes/centro-de-masa.svg]]

Los tornillos, la brida y el MPU están sobre el eje y casi no aportan inercia; el motor,
en la punta, aporta tanto como el brazo entero.

## 2. Suma de torques

La posición del centro de masa es $\vec r = d(\cos\theta,\ \sin\theta)$ y el peso actúa
hacia abajo, $\vec P = (0,\,-mg)$, así que su torque es

$$
\tau_g = r_x P_y - r_y P_x = -m g d \cos\theta .
$$

El empuje es perpendicular al brazo, de modo que su torque no depende de $\theta$:

$$
\tau_F = F R .
$$

La fricción se toma solo viscosa, proporcional a la velocidad angular:

$$
\tau_f = -b\,\dot\theta .
$$

Sumando, la ecuación de movimiento queda

$$
\boxed{\; I\,\ddot\theta = F R - m g d \cos\theta - b\,\dot\theta \;}
$$

## 3. Equilibrio

En reposo sostenido con empuje constante $F_0$ y ángulo constante $\theta_0$:

$$
0 = F_0 R - m g d \cos\theta_0
\quad\Longrightarrow\quad
F_0 R = m g d \cos\theta_0 .
$$

Esa es la relación que se usa para **identificar la ganancia del actuador**: barriendo
$F_0$ se obtiene el $\theta_0$ de equilibrio y de ahí $F_0(\theta_0)$.

## 4. Sobre la fricción

En este modelo la fricción es una sola línea: el término viscoso $b\dot\theta$. El
modelo de Coulomb no se usa: es no lineal y complica la identificación. La consecuencia
es que el modelo lineal sobreestima un poco el movimiento cerca del reposo, donde el
rozamiento seco frena más de lo que predice $b\dot\theta$.

Medido sobre la oscilación libre: $b = 1.03\times10^{-4}$ kg·m²/s
(ver [[Analisis de resultados]]).

## 5. Qué falta

| parámetro | estado |
|---|---|
| $R$, $d$, $I$, $m$ | medidos (CAD + báscula) |
| $b$ | medido del decaimiento |
| $F(u)$ | **pendiente**: barrido de duty en equilibrio |
