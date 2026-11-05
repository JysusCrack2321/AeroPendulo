# Desarrollo matemático del aeropéndulo

Del modelo a la función de transferencia, paso a paso.

![[cuerpo-libre.svg]]

## 1. Punto de partida

El brazo gira alrededor del pivote. Se mide el ángulo $\theta$ desde la horizontal,
positivo hacia arriba (como en el diagrama), y el empuje $F$ actúa en la punta,
perpendicular al brazo, a distancia $R$.

| símbolo | significado                             | valor medido                       |
| ------- | --------------------------------------- | ---------------------------------- |
| $R$     | pivote → punto de aplicación del empuje | $145\ \text{mm} = 0.145\ \text{m}$ |
| $d$     | pivote → centro de masa del conjunto    | $24.5\ \text{mm}$                  |
| $I$     | momento de inercia respecto al pivote   | $9.45\times10^{-5}\ \text{kg·m}^2$ |
| $m$     | masa del conjunto ensamblado            | $31.7\ \text{g}$                   |
| $b$     | fricción viscosa                        | por identificar                    |

### Datos del conjunto (modelo 3D + pesada)

Suma de masas puntuales a la distancia medida de cada pieza al pivote:

| pieza          | masa     | $d_i$    | $I_i$ propio | aporte a $I$ |
| -------------- | -------- | -------- | ------------ | ------------ |
| brazo PETG     | 13.40 g  | 32.9 mm  | 367 g·cm²    | 512 g·cm²    |
| brida (acero)  | 10.11 g  | 0.0 mm   | 4 g·cm²      | 4 g·cm²      |
| motor          | 2.50 g   | 130.7 mm | —            | 427 g·cm²    |
| MPU6050        | 2.00 g   | 0.3 mm   | —            | 1 g·cm²      |
| 4 tornillos M3 | 3.71 g   | 2.6 mm   | —            | 0 g·cm²      |
| **total**      | **31.72 g** | **24.5 mm** | —        | **945 g·cm²** |

De ahí $m\,d = 778\ \text{g·mm}$, que es lo que multiplica la gravedad en la
ecuación. Con $\theta_0 = 30^\circ$ resulta $a = m g d\operatorname{sen}\theta_0 =
3.8\times10^{-3}\ \text{N·m}$ y el polo inestable en $\sqrt{a/I} = 6.4\ \text{s}^{-1}$
(unos 1.0 s de constante de tiempo).

Los tornillos y la brida casi no aportan inercia porque están sobre el eje; el motor,
en la punta, aporta tanto como el brazo entero.

## 2. Suma de torques

La posición del centro de masa es $\vec r = d(\cos\theta,\ \sin\theta)$ y el peso
actúa hacia abajo, $\vec P = (0,\ -mg)$, así que su torque es

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

Sumando, la ecuación de movimiento es

$$
\boxed{\; I\,\ddot\theta = F R - m g d \cos\theta - b\,\dot\theta \;}
$$

## 3. Por qué todavía no se puede aplicar Laplace

La ecuación anterior es no lineal porque $\cos\theta$ depende de $\theta$. Laplace
solo trabaja con sistemas lineales de coeficientes constantes, así que hay que
linealizar alrededor de un punto de operación.

## 4. Equilibrio

En reposo sostenido con empuje constante $F_0$ y ángulo constante $\theta_0$:

$$
0 = F_0 R - m g d \cos\theta_0
\quad\Longrightarrow\quad
F_0 R = m g d \cos\theta_0 .
$$

Esa es la relación que se usa para **identificar la ganancia del actuador**: barriendo
$F_0$ se obtiene el $\theta_0$ de equilibrio y de ahí $F_0(\theta_0)$.

## 5. Linealización

Sea $\theta = \theta_0 + \delta$ y $F = F_0 + \Delta F$, con $\delta$ y $\Delta F$
pequeños. Entonces

$$
\cos\theta \approx \cos\theta_0 - \operatorname{sen}\theta_0\,\delta,
\qquad
\dot\theta = \dot\delta,
\qquad
\ddot\theta = \ddot\delta .
$$

Reemplazando y usando la condición de equilibrio,

$$
I\ddot\delta = (F_0 + \Delta F)R - m g d(\cos\theta_0 - \operatorname{sen}\theta_0\,\delta)
- b\dot\delta ,
$$

los términos $F_0R$ y $m g d\cos\theta_0$ se cancelan y queda

$$
\boxed{\; I\,\ddot\delta + b\,\dot\delta - \underbrace{m g d\operatorname{sen}\theta_0}_{a}\,\delta
= R\,\Delta F \;}
$$

El signo menos en el término de rigidez es la clave física: si el brazo está por
encima de la horizontal ($\theta_0>0$), la gravedad **desestabiliza**, y $a>0$.

## 6. Transformada de Laplace

Con condiciones iniciales nulas, $\delta(0)=\dot\delta(0)=0$:

$$
I s^2 \Delta(s) + b s \Delta(s) - a \Delta(s) = R\,U(s),
$$

donde $\Delta(s) = \mathcal L\{\delta(t)\}$ y $U(s) = \mathcal L\{\Delta F(t)\}$. Sacando
factor común,

$$
\left(I s^2 + b s - a\right)\Delta(s) = R\,U(s).
$$

## 7. Función de transferencia

$$
\boxed{\; G(s) = \frac{\Delta(s)}{U(s)} = \frac{R}{I s^2 + b s - a} \;}
$$

Normalizando por $I$ y definiendo

$$
\omega_n^2 = \frac{a}{I}, \qquad 2\zeta\omega_n = \frac{b}{I}
\quad\Longrightarrow\quad
G(s) = \frac{R/I}{s^2 + 2\zeta\omega_n s - \omega_n^2}.
$$

Los polos son

$$
s_{1,2} = -\zeta\omega_n \pm \omega_n\sqrt{\zeta^2 + 1},
$$

y como $\sqrt{\zeta^2+1}>\zeta$, uno de ellos tiene parte real positiva:

$$
s_1 = -\zeta\omega_n + \omega_n\sqrt{\zeta^2+1} > 0 .
$$

Un polo en el semiplano derecho: el sistema es inestable en lazo abierto, que es
exactamente lo esperado en un péndulo invertido.

## 8. Solución temporal de un escalón

Con $\Delta F(t) = U_0\,u(t)$, es decir $U(s) = U_0/s$:

$$
\Delta(s) = \frac{R\,U_0}{I}\cdot\frac{1}{s\left(s^2 + \frac{b}{I}s - \frac{a}{I}\right)} .
$$

Fracciones parciales y antitransformada (verificado numéricamente contra la solución
de la EDO):

$$
\delta(t) = \frac{R\,U_0}{a}\left[-1 + e^{-\frac{b}{2I}t}
\left(\cosh(\beta t) + \frac{b}{2I\beta}\operatorname{senh}(\beta t)\right)\right],
\qquad
\beta = \sqrt{\frac{a}{I} + \left(\frac{b}{2I}\right)^2}.
$$

Comprobaciones: en $t=0$ el corchete vale $-1+1=0$, así que $\delta(0)=0$, y la
derivada inicial también es nula (el término en senh la hace crecer recién en $t>0$).

Como el polo dominante es positivo, $\cosh$ y $\operatorname{senh}$ dominan: la
respuesta al escalón **diverge exponencialmente**. Eso es el comportamiento del
péndulo sin control, y es la razón por la que necesita realimentación.

## 9. Sobre la fricción

En este modelo la fricción es **una sola línea**: el término viscoso $b\dot\theta$.
El modelo de Coulomb ($\tau_c\operatorname{sgn}\dot\theta$) no se usa: es no lineal,
no tiene transformada de Laplace limpia y complica la identificación, así que queda
fuera del planteamiento.

La consecuencia práctica es que el modelo lineal sobreestima un poco el movimiento
cerca del reposo, donde el rozamiento seco frena más de lo que predice $b\dot\theta$.
Si más adelante hace falta, se recupera como perturbación, pero no forma parte de
$G(s)$.

## 10. El caso $\theta_0 = 0$

Si el equilibrio es horizontal, $\operatorname{sen}\theta_0 = 0$ y entonces $a = 0$:

$$
G(s) = \frac{R}{I s^2 + b s} = \frac{R/I}{s\left(s + b/I\right)} .
$$

Es un doble integrador con un polo en el origen: no diverge exponencialmente, pero
tampoco tiene punto de equilibrio estable con empuje constante, porque cualquier $F_0$
produce aceleración. Es un caso aparte y conviene tratarlo separado al identificar.

## 11. Estado de la identificación

| parámetro | valor | de dónde sale |
|---|---|---|
| $R$ | 145 mm | cota del modelo STEP |
| $m$, $d$, $I$ | 31.72 g, 24.5 mm, 9.45×10⁻⁵ kg·m² | ensamble 3D + pesada de las piezas |
| $b$ | **pendiente** | decaimiento de la oscilación libre |
| $F(u)$ | **pendiente** | barrido de duty en equilibrio |

Los tres primeros ya no son incógnitas: salieron del modelo CAD con las densidades
reales (PETG 1.27 y acero 7.85 g/cm³) y del pesaje del conjunto, que dio 31 g y coincide
con los 31.7 g calculados. Quedan la fricción y la ganancia del actuador, que son
justamente las dos que necesitan la planta funcionando.
