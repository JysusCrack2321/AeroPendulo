#!/usr/bin/env python3
"""Monitor en tiempo real del firmware control-pid: encoder, IMU y acciones del PID.

Uso:
    ./monitor_pid.py               # graba lo que corra en datos/pid_monitor_AAAAMMDD_HHMMSS.csv
    ./monitor_pid.py --sin-grabar

Comandos (Enter despues de cada uno):
    <grados>   referencia nueva, de 0 a 160 (la primera arranca el control)
    s          secuencia de escalones
    p          apaga el motor
    z          cero del encoder y de la IMU (motor apagado, brazo colgando quieto)
    q          apaga el motor y sale (Ctrl+C hace lo mismo)
"""
from __future__ import annotations

import argparse
import collections
import curses
import datetime as dt
import re
import threading
import time
from pathlib import Path

import serial

from registrar_serial import elegir_puerto

REPOSO = re.compile(r"#reposo theta=(\S+) adc=(\d+) mv=(\d+)(?: imu=(\S+) omega=(\S+))?")
CAMPOS = ["t_ms", "ref", "theta", "u", "p", "i", "d", "theta_imu", "omega_imu"]


def numero(texto: str | None) -> float:
    try:
        return float(texto)
    except (TypeError, ValueError):
        return float("nan")


class Planta:
    def __init__(self, puerto: str, grabar: bool):
        self.ser = serial.Serial()
        self.ser.port, self.ser.baudrate, self.ser.timeout = puerto, 115200, 0.1
        self.ser.dtr = self.ser.rts = False   # no reiniciar el ESP32 al abrir
        self.ser.open()
        self.dato: dict[str, float] = {}
        self.activo = False
        self.mensajes: collections.deque[str] = collections.deque(maxlen=6)
        self.cabecera: list[str] = []
        self.columnas = ",".join(CAMPOS)
        self.filas: list[str] = []
        self.grabar = grabar
        self.n = 0
        self.parar = threading.Event()
        self.hilo = threading.Thread(target=self._leer, daemon=True)
        self.hilo.start()

    def _leer(self):
        while not self.parar.is_set():
            try:
                linea = self.ser.readline().decode("utf-8", "replace").strip()
            except serial.SerialException:
                self.mensajes.append("puerto cerrado")
                break
            if not linea:
                continue
            m = REPOSO.match(linea)
            if m:
                self.activo = False
                th, adc, mv, imu, om = m.groups()
                self.dato = {"theta": numero(th), "adc": numero(adc), "mv": numero(mv),
                             "theta_imu": numero(imu), "omega_imu": numero(om)}
            elif linea.startswith("t_ms"):
                self.columnas = linea
            elif linea[0].isdigit() or linea[0] == "-":
                valores = linea.split(",")
                self.dato = {k: numero(v) for k, v in zip(self.columnas.split(","), valores)}
                self.activo = True
                self.n += 1
                if self.grabar:
                    self.filas.append(linea)
            else:
                if linea.startswith("#K"):
                    self.cabecera = [linea]
                elif linea.startswith("#FIN"):
                    self.activo = False
                self.mensajes.append(linea)

    def enviar(self, texto: str):
        self.ser.write(f"{texto}\n".encode())

    def cerrar(self):
        self.enviar("P")
        time.sleep(0.3)
        self.parar.set()
        self.ser.close()


def fmt(d: dict[str, float], clave: str, ancho: int = 8, dec: int = 2) -> str:
    v = d.get(clave, float("nan"))
    return f"{v:{ancho}.{dec}f}" if v == v else f"{'--':>{ancho}}"


def pintar(pant, planta: Planta, entrada: str):
    pant.erase()
    alto, ancho = pant.getmaxyx()
    d = planta.dato
    filas = [f"AeroPendulo PID   {'CONTROL' if planta.activo else 'motor apagado'}   muestras: {planta.n}", ""]
    if planta.activo:
        e = d.get("ref", float("nan")) - d.get("theta", float("nan"))
        dif = d.get("theta_imu", float("nan")) - d.get("theta", float("nan"))
        filas += [
            f"  t          {d.get('t_ms', float('nan')) / 1000:8.2f} s",
            f"  ref        {fmt(d, 'ref')} °",
            f"  theta enc  {fmt(d, 'theta')} °      error {e:8.2f} °",
            f"  theta IMU  {fmt(d, 'theta_imu')} °      IMU-enc {dif:6.2f} °",
            f"  omega IMU  {fmt(d, 'omega_imu', dec=1)} °/s",
            "",
            f"  P {fmt(d, 'p', dec=1)}   I {fmt(d, 'i', dec=1)}   D {fmt(d, 'd', dec=1)}   ->  u {fmt(d, 'u', 4, 0)} / 255",
        ]
        u = d.get("u", 0.0)
        if u == u:
            barra = max(0, ancho - 8)
            llenas = int(round(barra * min(max(u, 0.0), 255.0) / 255.0))
            filas.append("  [" + "#" * llenas + " " * (barra - llenas) + "]")
    else:
        dif = d.get("theta_imu", float("nan")) - d.get("theta", float("nan"))
        filas += [
            f"  theta enc  {fmt(d, 'theta')} °      adc {fmt(d, 'adc', 5, 0)}   {fmt(d, 'mv', 5, 0)} mV",
            f"  theta IMU  {fmt(d, 'theta_imu')} °      IMU-enc {dif:6.2f} °",
            f"  omega IMU  {fmt(d, 'omega_imu', dec=1)} °/s",
        ]
    filas += ["", "mensajes:"] + [f"  {m}" for m in planta.mensajes]
    for y, texto in enumerate(filas[: alto - 2]):
        pant.addnstr(y, 0, texto, ancho - 1)
    pant.addnstr(alto - 2, 0, "<grados> 0-160 | s secuencia | p apagar | z cero | q salir", ancho - 1)
    pant.addnstr(alto - 1, 0, "> " + entrada, ancho - 1)
    pant.refresh()


def bucle(pant, planta: Planta):
    curses.curs_set(1)
    pant.nodelay(True)
    entrada = ""
    planta.enviar("?")
    while True:
        pintar(pant, planta, entrada)
        tecla = pant.getch()
        if tecla == -1:
            time.sleep(0.05)
            continue
        if tecla in (curses.KEY_ENTER, 10, 13):
            cmd, entrada = entrada.strip().lower(), ""
            if cmd == "q":
                return
            elif cmd == "p":
                planta.enviar("P")
            elif cmd == "s":
                planta.enviar("S")
            elif cmd == "z":
                if planta.activo:
                    planta.mensajes.append("primero apaga el motor (p) y deja el brazo colgando quieto")
                else:
                    planta.enviar("Z")
            elif cmd:
                try:
                    g = float(cmd.replace(",", "."))
                except ValueError:
                    planta.mensajes.append(f"no entendi '{cmd}'")
                    continue
                if 0 <= g <= 160:
                    planta.enviar(f"T {g}")
                else:
                    planta.mensajes.append("fuera de rango: 0 a 160 grados")
        elif tecla in (curses.KEY_BACKSPACE, 127, 8):
            entrada = entrada[:-1]
        elif 32 <= tecla < 127:
            entrada += chr(tecla)


def main() -> None:
    ap = argparse.ArgumentParser(description="monitor en tiempo real del PID del aeropendulo")
    ap.add_argument("-p", "--puerto")
    ap.add_argument("--sin-grabar", action="store_true")
    args = ap.parse_args()

    planta = Planta(elegir_puerto(args.puerto), not args.sin_grabar)
    try:
        curses.wrapper(bucle, planta)
    except KeyboardInterrupt:
        pass
    finally:
        planta.cerrar()
        print("motor apagado.")

    if planta.filas:
        sello = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        salida = Path(__file__).parent / "datos" / f"pid_monitor_{sello}.csv"
        salida.write_text("\n".join(planta.cabecera + [planta.columnas] + planta.filas) + "\n", encoding="utf-8")
        print(f"{len(planta.filas)} muestras -> {salida}")


if __name__ == "__main__":
    main()
