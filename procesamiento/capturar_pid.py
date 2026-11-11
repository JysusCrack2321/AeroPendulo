#!/usr/bin/env python3
"""Captura un ensayo del firmware control-pid a CSV.

Uso:
    ./capturar_pid.py -n escalones -c S          # secuencia de escalones
    ./capturar_pid.py -n secador -c "R 90"       # referencia fija para perturbaciones
    ./capturar_pid.py -n moneda -c S             # robustez, con la masa puesta
    ./capturar_pid.py -k "2.2 3 0.22 0.02 0.3" -n escalones -c S

Graba desde #INICIO hasta #FIN (fin de la secuencia, corte o P).
Enter o Ctrl+C manda P (motor apagado) y guarda lo que haya.
Sale en datos/pid_<nombre>_AAAAMMDD_HHMMSS.csv con las lineas #K del firmware arriba.
"""
from __future__ import annotations

import argparse
import datetime as dt
import select
import sys
import time
from pathlib import Path

import serial

from registrar_serial import elegir_puerto


def main() -> None:
    ap = argparse.ArgumentParser(description="captura un ensayo del PID del aeropendulo")
    ap.add_argument("-p", "--puerto")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("-n", "--nombre", default="ensayo")
    ap.add_argument("-c", "--comando", default="S", help='S, "R 90", ...')
    ap.add_argument("-k", "--ganancias", help='"Kp Ki Kd Tf beta"')
    ap.add_argument("-s", "--salida", default=str(Path(__file__).parent / "datos"))
    args = ap.parse_args()

    puerto = elegir_puerto(args.puerto)
    ser = serial.Serial(puerto, args.baud, timeout=0.1)
    print("puerto:", puerto)
    time.sleep(2.0)   # el ESP32 se reinicia al abrir el puerto y captura el cero colgando
    t_fin = time.time() + 3
    while time.time() < t_fin:
        linea = ser.readline().decode("utf-8", "replace").strip()
        if linea.startswith("#reposo"):
            print(linea)
            break

    if args.ganancias:
        ser.write(f"K {args.ganancias}\n".encode())
        time.sleep(0.2)
    input(f"brazo colgando y quieto. Enter para mandar '{args.comando}' (Enter otra vez = parar)... ")
    ser.reset_input_buffer()
    ser.write(f"{args.comando}\n".encode())

    cabecera: list[str] = []
    filas: list[str] = []
    grabando = False
    motivo = "interrumpido"
    ultimo = 0.0
    try:
        while True:
            if select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.readline()
                ser.write(b"P\n")
            linea = ser.readline().decode("utf-8", "replace").strip()
            if not linea:
                continue
            if linea.startswith("#K"):
                cabecera.append(linea)
            elif linea == "#INICIO":
                grabando = True
            elif linea.startswith("#FIN"):
                motivo = linea[5:]
                break
            elif grabando and linea.startswith("t_ms"):
                cabecera.append(linea)
            elif grabando and linea[0].isdigit():
                filas.append(linea)
                if time.time() - ultimo > 0.1:
                    ultimo = time.time()
                    t, r, th, u, *resto = linea.split(",")
                    extra = ""
                    if len(resto) == 5:
                        p, i, d, thi, om = resto
                        extra = f"  P={p:>6} I={i:>6} D={d:>6}  imu={thi:>7} w={om:>6}"
                    print(f"  t={int(t)/1000:6.1f} s  ref={r:>6}  theta={th:>7}  u={u:>3}{extra}")
    except KeyboardInterrupt:
        ser.write(b"P\n")
    finally:
        ser.close()

    if not filas:
        sys.exit("no llego ningun dato")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    sello = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = salida / f"pid_{args.nombre}_{sello}.csv"
    if not any(c.startswith("t_ms") for c in cabecera):
        cabecera.append("t_ms,ref,theta,u")
    archivo.write_text("\n".join(cabecera + filas) + "\n", encoding="utf-8")
    print(f"fin: {motivo}. {len(filas)} muestras ({len(filas) / 100:.1f} s) -> {archivo}")


if __name__ == "__main__":
    main()
