# Control PID del aeropéndulo

θ en grados desde la posición colgada: 0° colgado, 90° horizontal, 180° vertical arriba.

## Modelo

$$I\ddot\theta = F(u)\,R - m g d\sin\theta - b\dot\theta,\qquad u\in[0,255]$$

Linealizado en θ₀, con la ganancia incremental del actuador $k(\theta_0)=F'(u_0)R/I$:

$$G(s)=\frac{\Theta(s)}{U(s)}=\frac{k(\theta_0)}{s^2+(b/I)\,s+(mgd/I)\cos\theta_0}$$

| parámetro | valor | origen |
|---|---|---|
| $K_a$ | 8.04e-4 N/duty (R² = 0.995, F(255) ≈ 200 mN) | barrido de 5 ciclos, masa de 32.5 g a 65 mm (`registro_lastre_barrido_20261106_b.csv`) |
| $mgd/I$ | 93.8 ± 0.6 s⁻² | 3 oscilaciones libres, ajuste no lineal (ode45) |
| $b/I$ | 0.90 ± 0.05 s⁻¹ | ídem |
| $I$ | 8.13e-5 kg·m² (CAD 9.45e-5, −14 %) | $mgd$ del CAD / ω² medido |
| $K_a R/I$ | 74.1 °/s² por duty | |
| ruido del ángulo | σ ≈ 0.39° con el motor encendido | barrido, tramos en reposo |

## PID

$$u = K_p(\beta r - y) + K_i\!\int(r-y)\,dt - \frac{K_d s}{T_f s+1}\,y$$

Kp = 1, Ki = 1, Kd = 0.2, Tf = 0.02 s, β = 0, Ts = 10 ms. Salen de `diseno_pid.m` por lugar de las raíces:

$$C(s) = K\,\frac{(s+z_1)(s+z_2)}{s\,(T_f s+1)},\qquad K_d + K_pT_f = K,\quad K_p + K_iT_f = K(z_1+z_2),\quad K_i = Kz_1z_2$$

- **Ceros**: z₁ = 1.4 rad/s (integral, casi se cancela con el polo en el origen) y z₂ = 3.2 rad/s (derivada, jala hacia la izquierda la rama del polo inestable de arriba de 90°). Filtro en 1/Tf = 50 rad/s.
- **K**: el K mínimo estable sube por encima de 90° (0.14 en 120°, 0.19 en 135°, 0.22 en 150°); en el modelo no hay máximo. Se elige el menor K que estabiliza el rango: K = 0.22, estable hasta 145° (menos ruido en u, menos exigencia al motor; las ganancias altas oscilaron en el banco).
- **Márgenes**: MF 57–59° hasta 135°; MG al bajar la ganancia −4.2 dB (120°), −1.6 dB (135°), ≈ 0 (150°). Al subirla el modelo no tiene límite (la fase no cruza −180°), así que no se reporta.
- Con K = 0.22: Kp = 0.99, Ki = 0.99, Kd = 0.200 → redondeadas a 1, 1, 0.2.

150° queda en el borde y en el banco oscila ±2–4°. K = 0.3–0.4 daría margen ahí (sin probar con el sensor corregido).

## Archivos

| archivo | qué hace |
|---|---|
| `parametros.m` | planta, ganancias y secuencia de escalones (la misma del firmware) |
| `identificar_planta.m` | Ka, F(u) y mgd/I, b/I desde `procesamiento/datos` → `id_*.png` |
| `diseno_pid.m` | punto de operación, lugar de las raíces y elección de K, Bode, polos de lazo cerrado, β, Nyquist, sensibilidades, discreto, Monte Carlo → `dis_*.png`, `resultados_diseno.txt` |
| `simular_pid.m` | simulación no lineal con el controlador discreto idéntico al del ESP32, F(u) medida, ruido y cuantización del ADC, PWM entero |
| `simulacion_escalones.m` | secuencia de escalones, perturbación de par y robustez hasta 120° → `sim_*.png` |
| `graficar_experimento.m` | ensayos reales `procesamiento/datos/pid_*.csv` sobre la simulación (θ y u), con métricas por escalón → `exp_*.png`, `resultados/` |
| `comparar_ensayos.m` | repetibilidad entre las dos corridas → `exp_repetibilidad.png` |

## En el banco

1. **Encoder**: con el brazo colgando, la salida del AS5600 tiene que dar 0.3–0.5 V (`procesamiento/monitor_encoder.py`). Si da más de ~2.4 V, el ADC del ESP32 se satura y a unos 85° el sensor salta de 3.3 a 0 V: girar el imán.
2. Cargar `firmware/control-pid` con el brazo colgando quieto (toma el cero al arrancar; `Z` lo vuelve a tomar).
3. Ensayos (Python con pyserial, p. ej. `~/.local/share/thonny-venv/bin/python`):
   ```
   cd procesamiento
   ./capturar_pid.py -n escalones150 -c S       # 45, 90, 105, 120, 135, 150, 135, 120, 105, 90, 45 (10 s cada uno)
   ./capturar_pid.py -n directo -c "R 120"      # referencia fija; Enter para parar
   ```
4. En MATLAB, desde `control/`: `graficar_experimento`.

Para mover el brazo a mano: `procesamiento/mover.py` (escribes el ángulo y Enter; graba en `datos/pid_manual_*.csv`).

Comandos serie: `S` secuencia, `R <grados>` referencia fija, `T <grados>` cambia la referencia sin reiniciar el control, `P` parar, `Z` recapturar el cero, `K kp ki kd tf beta` (solo en reposo), `?`.
Corte de seguridad si |θ| > 190°.
