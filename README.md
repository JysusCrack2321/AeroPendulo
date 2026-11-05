# AeroPéndulo

Proyecto de Técnicas de Control (UNAL 2022888). Brazo con propulsor: el empuje `F`
a distancia `R` del pivote genera el par de control; el peso `mg` actúa en el CM.

## Estructura

    firmware/TDC/      ESP32 (PlatformIO): AS5600 + MPU6050 por serial a 20 Hz
    procesamiento/     captura y carga de datos (Python / MATLAB) + datos/ CSV
    docs/              notas del proyecto (enlace a la carpeta del vault Obsidian,
                       que es la fuente de verdad; Obsidian sigue siendo el maestro)

## Estado

- `firmware/TDC/src/main.cpp` solo sensa: AS5600 por ADC (GPIO34) y MPU6050 por I2C
  (21/22), salida `>clave:valor` cada 50 ms. **No hay salida PWM**, así que todavía
  no se puede barrer duty para identificar el actuador.
- `procesamiento/datos/` tiene registros de oscilación libre: `tiempo_ms,angulo_grados`.

## Caracterización pendiente

- Fricción: decaimiento libre, ajuste de `b` (viscoso) y `tau_c` (Coulomb) en
  `I·θ¨ = F·R − m·g·L·senθ − b·θ˙ − tau_c·sgn(θ˙)`.
- Ganancia del actuador: duty constante, equilibrio `F·R = m·g·L·senθ`, barrido de
  duty → `F(u)` y su pendiente.

## Compilar

    cd firmware/TDC && pio run -t upload

Monitor a 115200 baud.
