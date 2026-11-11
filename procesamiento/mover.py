#!/usr/bin/env python3
"""Mueve el aeropendulo al angulo que se escriba, con el firmware control-pid.

Uso:
    ./mover.py                 # graba el ensayo en datos/pid_manual_AAAAMMDD_HHMMSS.csv
    ./mover.py --sin-grabar

Comandos (Enter despues de cada uno):
    <grados>   referencia nueva, de 0 a 160 (p. ej. 90). La primera arranca el control.
    (vacio)    muestra theta, referencia y u
    p          apaga el motor (el brazo cae; otra referencia lo vuelve a arrancar)
    z          toma el cero de nuevo (solo con el motor apagado y el brazo colgando quieto)
    q          apaga el motor y sale (Ctrl+C hace lo mismo)
"""
from __future__ import annotations

import argparse
import datetime as dt
import threading
import time
from pathlib import Path

import serial

from registrar_serial import elegir_puerto


class Planta:
    def __init__(self, puerto: str, grabar: bool):
        self.ser = serial.Serial()
        self.ser.port, self.ser.baudrate, self.ser.timeout = puerto, 115200, 0.1
        self.ser.dtr = self.ser.rts = False   # no reiniciar el ESP32 al abrir
        self.ser.open()
        self.theta = self.ref = None
        self.u = 0
        self.activo = False
        self.cabecera: list[str] = []
        self.columnas = "t_ms,ref,theta,u"
        self.filas: list[str] = []
        self.grabar = grabar
        self.parar = threading.Event()
        self.hilo = threading.Thread(target=self._leer, daemon=True)
        self.hilo.start()

    def _leer(self):
        while not self.parar.is_set():
            try:
                linea = self.ser.readline().decode("utf-8", "replace").strip()
            except serial.SerialException:
                break
            if not linea:
                continue
            if linea.startswith("#reposo"):
                self.activo = False
                self.theta = float(linea.split("theta=")[1].split()[0])
            elif linea.startswith("#K"):
                self.cabecera = [linea]
            elif linea.startswith("#FIN"):
                self.activo = False
                print(f"\n  [{linea[1:]}]")
            elif linea.startswith("t_ms"):
                self.columnas = linea
            elif linea[0].isdigit():
                t, r, th, u, *_ = linea.split(",")
                self.activo = True
                self.ref, self.theta, self.u = float(r), float(th), int(u)
                if self.grabar:
                    self.filas.append(linea)

    def enviar(self, texto: str):
        self.ser.write(f"{texto}\n".encode())

    def estado(self) -> str:
        if self.theta is None:
            return "sin datos todavia"
        if not self.activo:
            return f"motor apagado, theta = {self.theta:.1f}°"
        return f"theta = {self.theta:6.1f}°   ref = {self.ref:5.1f}°   u = {self.u:3d}"

    def cerrar(self):
        self.enviar("P")
        time.sleep(0.3)
        self.parar.set()
        self.ser.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="mover el aeropendulo a mano")
    ap.add_argument("-p", "--puerto")
    ap.add_argument("--sin-grabar", action="store_true")
    args = ap.parse_args()

    planta = Planta(elegir_puerto(args.puerto), not args.sin_grabar)
    time.sleep(1.0)
    planta.enviar("?")
    time.sleep(0.5)
    print("Planta:", planta.estado())
    if planta.theta is not None and abs(planta.theta) > 3:
        print("  ojo: el cero no coincide con el brazo colgando. Con el brazo quieto escribe z.")
    print("Escribe un angulo (0-160) y Enter. Vacio = estado, p = apagar, z = cero, q = salir.\n")

    try:
        while True:
            cmd = input("grados> ").strip().lower()
            if cmd == "":
                print(" ", planta.estado())
            elif cmd == "q":
                break
            elif cmd == "p":
                planta.enviar("P")
                print("  motor apagado")
            elif cmd == "z":
                if planta.activo:
                    print("  primero apaga el motor (p) y deja el brazo colgando quieto")
                else:
                    planta.enviar("Z")
                    time.sleep(0.5)
                    print("  cero tomado:", planta.estado())
            else:
                try:
                    g = float(cmd.replace(",", "."))
                except ValueError:
                    print("  no entendi; escribe un numero, p, z o q")
                    continue
                if not 0 <= g <= 160:
                    print("  fuera de rango: 0 a 160 grados")
                    continue
                planta.enviar(f"T {g}")
                print(f"  yendo a {g:.1f}°")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        planta.cerrar()
        print("motor apagado.")

    if planta.filas:
        sello = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        salida = Path(__file__).parent / "datos" / f"pid_manual_{sello}.csv"
        salida.write_text("\n".join(planta.cabecera + [planta.columnas] + planta.filas) + "\n", encoding="utf-8")
        print(f"{len(planta.filas)} muestras -> {salida}")


if __name__ == "__main__":
    main()
