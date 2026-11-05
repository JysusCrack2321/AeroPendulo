# Desarrollo matemático del aeropéndulo

Del modelo a la función de transferencia, paso a paso.

![[cuerpo-libre.svg]]

## 1. Punto de partida

El brazo gira alrededor del pivote. Se mide el ángulo $\theta$ desde la horizontal,
positivo hacia arriba (como en el diagrama), y el empuje $F$ actúa en la punta,
perpendicular al brazo, a distancia $R$.

| símbolo | significado | valor medido |
|---|---|---|
| $R$ | pivote → punto de aplicación del empuje | $145\ \text{mm} = 0.145\ \text{m}$ |
| $d$ | pivote → centro de masa | $32.9\ \text{mm}$ (solo la placa) |
| $I$ | momento de inercia respecto al pivote | por medir |
| $m$ | masa del conjunto brazo + motor + hélice | por medir |
| $b$ | fricción viscosa | por identificar |
| $\tau_c$ | fricción de Coulomb | por identificar |

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

La fricción se modela con dos términos, uno viscoso y uno de Coulomb (constante,
opuesto al movimiento):

$$
\tau_f = -b\,\dot\theta - \tau_c\,\operatorname{sgn}(\dot\theta).
$$

Sumando, la ecuación de movimiento es

$$
\boxed{\; I\,\ddot\theta = F R - m g d \cos\theta - b\,\dot\theta
- \tau_c\,\operatorname{sgn}(\dot\theta) \;}
$$

## 3. Por qué todavía no se puede aplicar Laplace

La ecuación anterior es no lineal por dos razones: $\cos\theta$ depende de $\theta$ y
$\operatorname{sgn}(\dot\theta)$ es discontinuo. Laplace solo trabaja con sistemas
lineales de coeficientes constantes, así que hay que linealizar alrededor de un punto
de operación.

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
- b\dot\delta - \tau_c\operatorname{sgn}(\dot\delta),
$$

los términos $F_0R$ y $m g d\cos\theta_0$ se cancelan y queda

$$
\boxed{\; I\,\ddot\delta + b\,\dot\delta - \underbrace{m g d\operatorname{sen}\theta_0}_{a}\,\delta
= R\,\Delta F - \tau_c\operatorname{sgn}(\dot\delta) \;}
$$

El signo menos en el término de rigidez es la clave física: si el brazo está por
encima de la horizontal ($\theta_0>0$), la gravedad **desestabiliza**, y $a>0$.

## 6. Transformada de Laplace

Se desprecia por ahora la fricción de Coulomb (ver sección 9) y se toman condiciones
iniciales nulas, $\delta(0)=\dot\delta(0)=0$:

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

## 9. Qué hacer con la fricción de Coulomb

$\operatorname{sgn}(\dot\delta)$ no tiene transformada de Laplace limpia porque no es
lineal, así que no entra en $G(s)$. Tres salidas prácticas:

1. **Tratarla como perturbación** que actúa en la entrada, con $\tau_c$ conocido: en
   el lazo se comporta como un escalón de torque que el integrador del controlador
   debe rechazar.
2. **Ignorarla fuera de la zona muerta**: cuando el brazo ya se mueve, $\tau_c$ es
   constante y solo corre el punto de operación; por eso la ganancia del actuador se
   mide en movimiento y no cerca del reposo.
3. **Función descriptora**: para análisis por frecuencia, reemplazar el signo por su
   aproximación de primer armónico.

En dinámica, el efecto visible es el decaimiento casi lineal de la amplitud en la
oscilación libre (a diferencia del decaimiento exponencial del término viscoso); de
ahí se identifican $b$ y $\tau_c$ a la vez.

## 10. El caso $\theta_0 = 0$

Si el equilibrio es horizontal, $\operatorname{sen}\theta_0 = 0$ y entonces $a = 0$:

$$
G(s) = \frac{R}{I s^2 + b s} = \frac{R/I}{s\left(s + b/I\right)} .
$$

Es un doble integrador con un polo en el origen: no diverge exponencialmente, pero
tampoco tiene punto de equilibrio estable con empuje constante, porque cualquier $F_0$
produce aceleración. Es un caso aparte y conviene tratarlo separado al identificar.

## 11. Qué falta medir

| parámetro | cómo se obtiene |
|---|---|
| $I$ | masa total y geometría (o péndulo físico: $T = 2\pi\sqrt{I/mgd}$) |
| $m$, $d$ | báscula y centro de masa del conjunto armado |
| $R$ | cota del modelo: 145 mm |
| $b$, $\tau_c$ | decaimiento de la oscilación libre |
| $F(u)$ | barrido de duty en equilibrio |
