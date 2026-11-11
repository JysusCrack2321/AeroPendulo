#!/usr/bin/env python3
"""Monitor en vivo del AS5600 con el firmware control-pid en reposo (motor apagado).

Uso:
    ./monitor_encoder.py            # Ctrl+C para salir

Colgando, el voltaje debe quedar entre 0.3 y 0.5 V: asi todo el recorrido 0-180 grados
cae en la zona lineal del ADC del ESP32 (~0.15-2.45 V a 11 dB), lejos del salto 3.3 V -> 0 V.
"""
from __future__ import annotations

import argparse
import re
import sys
import time

import serial

from registrar_serial import elegir_puerto

PATRON = re.compile(r"#reposo theta=(-?[\d.]+) adc=(\d+) mv=(\d+)")
V_MIN, V_MAX = 0.3, 0.5
V_LINEAL = 2.45
VDD = 3.3


def estado(v: float) -> str:
    if v < 0.15:
        return "\033[31mPISO DEL ADC: sigue girando\033[0m"
    if v < V_MIN:
        return "\033[33mun poco bajo\033[0m"
    if v <= V_MAX:
        return "\033[32mBIEN: fijalo aqui\033[0m"
    if v <= V_LINEAL:
        return "\033[33malto: gira hacia abajo\033[0m"
    return "\033[31mZONA PLANA DEL ADC: gira hacia abajo\033[0m"


def main() -> None:
    ap = argparse.ArgumentParser(description="voltaje del AS5600 en vivo")
    ap.add_argument("-p", "--puerto")
    args = ap.parse_args()

    ser = serial.Serial(elegir_puerto(args.puerto), 115200, timeout=0.5)
    time.sleep(2.0)   # el ESP32 se reinicia al abrir el puerto
    print("brazo colgando: objetivo %.1f-%.1f V. Ctrl+C para salir.\n" % (V_MIN, V_MAX))
    try:
        while True:
            m = PATRON.match(ser.readline().decode("utf-8", "replace").strip())
            if not m:
                continue
            theta, adc, mv = float(m[1]), int(m[2]), int(m[3])
            v = mv / 1000
            libre = (V_LINEAL - v) / VDD * 360   # grados que puede subir antes de la zona plana
            barra = "#" * int(30 * min(v, VDD) / VDD)
            sys.stdout.write(f"\r{v:5.2f} V  adc {adc:4d}  [{barra:<30}]  theta {theta:7.2f}  "
                             f"margen hasta zona plana {libre:5.0f} grados  {estado(v)}        ")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print()
    finally:
        ser.close()


if __name__ == "__main__":
    main()
