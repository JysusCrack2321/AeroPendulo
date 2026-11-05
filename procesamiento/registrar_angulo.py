#!/usr/bin/env python3
"""Registra en CSV el angulo que manda el sketch lectorA0.

Uso:
    python3 registrar_angulo.py [PUERTO]

    Enter   -> START (abre el CSV y empieza a escribir)
    Enter   -> STOP  (cierra el CSV)
    Ctrl+C  -> salir

El CSV se guarda en esta misma carpeta como registro_AAAAMMDD_HHMMSS.csv
con dos columnas: tiempo_ms, angulo_grados
"""

import csv
import datetime
import os
import select
import sys
import time

import serial

PUERTO = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUDIOS = 115200
CARPETA = os.path.dirname(os.path.abspath(__file__))


def main():
    ser = serial.Serial(PUERTO, BAUDIOS, timeout=0.1)
    time.sleep(2)  # el UNO se reinicia al abrir el puerto
    ser.reset_input_buffer()

    print(f"Conectado a {PUERTO} @ {BAUDIOS}")
    print("Enter = START  |  Enter otra vez = STOP  |  Ctrl+C = salir")

    while True:
        input("\nEnter para START... ")
        ser.write(b"START\n")

        nombre = os.path.join(
            CARPETA, datetime.datetime.now().strftime("registro_%Y%m%d_%H%M%S.csv")
        )
        filas = 0
        with open(nombre, "w", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["tiempo_ms", "angulo_grados"])
            cabecera_lista = True
            t_inicio = time.time()

            while True:
                linea = ser.readline().decode("utf-8", "replace").strip()
                if linea == "#STOP":
                    break
                if linea and linea != "#START":
                    partes = linea.split(",")
                    try:
                        if len(partes) == 2:
                            t = float(partes[0])
                            ang = float(partes[1])
                        else:
                            # el sketch manda solo el angulo: el tiempo lo pone el script
                            t = 1000.0 * (time.time() - t_inicio)
                            ang = float(partes[0])
                    except ValueError:
                        continue  # cabecera del Arduino u otra linea de texto
                    escritor.writerow([f"{t:.0f}", f"{ang:.2f}"])
                    filas += 1
                    if filas % 50 == 0:
                        archivo.flush()
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.readline()
                    ser.write(b"STOP\n")

        print(f"Guardado: {nombre}  ({filas} filas)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo.")
    except serial.SerialException as error:
        print(f"Error de puerto serie: {error}", file=sys.stderr)
        sys.exit(1)
