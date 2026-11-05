#!/usr/bin/env python3
"""Graba por serial lo que manda el firmware, con Enter para arrancar y parar.

Uso:
    ./registrar_serial.py                  # detecta el puerto solo
    ./registrar_serial.py -p /dev/ttyUSB0  # puerto explicito
    ./registrar_serial.py -g               # con grafica en vivo

Flujo: esperas Enter -> graba -> Enter otra vez -> guarda CSV y resume.

Entiende los dos formatos del proyecto:
  * lineas ">clave:valor" (firmware AS5600 + MPU6050)  -> CSV ancho, una fila por ciclo
  * lineas con comas (firmware del encoder)            -> se guardan tal cual en *_crudo.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import queue
import select
import sys
import threading
import time
from pathlib import Path

import serial
from serial.tools import list_ports

# ----------------------------------------------------------------------------
# puerto
# ----------------------------------------------------------------------------
PISTAS = ("cp210", "ch340", "ch910", "ft23", "usb serial", "usb-serial", "esp32", "uart")


def elegir_puerto(preferido: str | None = None) -> str:
    if preferido:
        return preferido
    puertos = list(list_ports.comports())
    if not puertos:
        sys.exit("no hay puertos seriales; revisa el cable")
    for p in puertos:
        texto = " ".join(str(x) for x in (p.description, p.manufacturer, p.product) if x).lower()
        if any(k in texto for k in PISTAS):
            return p.device
    return puertos[0].device


# ----------------------------------------------------------------------------
# lectura en segundo plano
# ----------------------------------------------------------------------------
class Lector(threading.Thread):
    def __init__(self, puerto: str, baud: int, cola: queue.Queue):
        super().__init__(daemon=True)
        self.ser = serial.Serial(puerto, baud, timeout=0.05)
        self.cola = cola
        self.parar = threading.Event()

    def run(self):
        buf = b""
        while not self.parar.is_set():
            try:
                trozo = self.ser.read(256)
            except Exception:
                break
            if not trozo:
                continue
            buf += trozo
            while b"\n" in buf:
                linea, buf = buf.split(b"\n", 1)
                texto = linea.decode("utf-8", "replace").strip()
                if texto:
                    self.cola.put((time.time(), texto))   # sello al recibir, no al procesar

    def cerrar(self):
        self.parar.set()
        try:
            self.ser.close()
        except Exception:
            pass


def _numero(texto: str) -> bool:
    try:
        float(texto)
        return True
    except ValueError:
        return False


def esperar_enter(prompt: str) -> None:
    print(prompt, end="", flush=True)
    while True:
        r, _, _ = select.select([sys.stdin], [], [], 0.2)
        if r:
            if sys.stdin.readline() == "":     # EOF: nadie va a teclear otro Enter
                time.sleep(0.2)
                continue
            return


# ----------------------------------------------------------------------------
# grabacion
# ----------------------------------------------------------------------------
def grabar(puerto: str, baud: int, salida: Path, graficar: bool) -> Path:
    salida.mkdir(parents=True, exist_ok=True)
    sello = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ancho = salida / f"registro_{sello}.csv"
    crudo = salida / f"registro_{sello}_crudo.csv"

    cola: queue.Queue[str] = queue.Queue()
    lector = Lector(puerto, baud, cola)
    lector.start()

    esperar_enter("Enter para empezar a grabar...")
    # tira lo que se acumulo mientras esperabamos: si no, arranca con t negativos
    while not cola.empty():
        try:
            cola.get_nowait()
        except queue.Empty:
            break
    print("grabando. Enter para detener.")
    t0 = time.time()
    t0_wall = dt.datetime.now()

    orden: list[str] = []          # columnas en el orden en que aparecen
    actual: dict[str, float] = {}  # ciclo en curso
    filas: list[dict] = []
    crudas: list[str] = []
    cabecera_crudo = ""
    detener = threading.Event()

    def vigilar_enter():
        try:
            esperar_enter("")
        except (OSError, ValueError):
            return
        detener.set()

    threading.Thread(target=vigilar_enter, daemon=True).start()

    ultimo_dibujo = 0.0
    fig = ax1 = ax2 = None
    if graficar:
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        fig.canvas.manager.set_window_title("aeropendulo - en vivo")

    try:
        while not detener.is_set():
            try:
                t_llegada, linea = cola.get(timeout=0.1)
            except queue.Empty:
                continue
            t = t_llegada - t0

            if ">" in linea and ":" in linea:
                for parte in linea.split():
                    if not parte.startswith(">") or ":" not in parte:
                        continue
                    clave, _, valor = parte[1:].partition(":")
                    try:
                        v = float(valor)
                    except ValueError:
                        continue
                    if clave in actual:      # empieza un ciclo nuevo
                        fila = {"t_s": round(actual.pop("_t", t), 4)}
                        for k in orden:
                            fila[k] = actual.get(k, "")
                        filas.append(fila)
                        actual.clear()
                    if clave not in orden:
                        orden.append(clave)
                    actual[clave] = v
                    actual.setdefault("_t", t)
            elif "," in linea:
                campos = [c.strip() for c in linea.split(",")]
                if not crudas and not _numero(campos[-1]):
                    cabecera_crudo = linea        # encabezado del firmware de comas
                else:
                    crudas.append(linea)

            if graficar and t - ultimo_dibujo > 0.4 and filas:
                ultimo_dibujo = t
                import matplotlib.pyplot as plt
                ts = [f["t_s"] for f in filas]
                if "degrees" in orden:
                    ax1.clear(); ax1.plot(ts, [f.get("degrees", None) for f in filas], color="#1c7ed6")
                    ax1.set_ylabel("grados")
                if "accel_x" in orden:
                    ax2.clear()
                    for k, c in (("accel_x", "#2b8a3e"), ("accel_y", "#e8590c"), ("accel_z", "#7048e8")):
                        if k in orden:
                            ax2.plot(ts, [f.get(k, None) for f in filas], color=c, label=k)
                    ax2.set_ylabel("g"); ax2.legend(loc="upper right", fontsize=8)
                ax2.set_xlabel("t (s)")
                fig.suptitle(f"{len(filas)} muestras")
                fig.tight_layout(); fig.canvas.draw(); fig.canvas.flush_events()
    except KeyboardInterrupt:
        print("\ninterrumpido")
    finally:
        lector.cerrar()

    # ultimo ciclo: solo si trae al menos la mitad de las columnas
    if actual and len([k for k in actual if not k.startswith("_")]) >= max(2, len(orden) // 2):
        fila = {"t_s": round(actual.pop("_t", 0.0), 4)}
        for k in orden:
            fila[k] = actual.get(k, "")
        filas.append(fila)

    dur = time.time() - t0
    campo_t = "t_s"
    if filas:
        with open(ancho, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[campo_t] + orden)
            w.writeheader()
            for fila in filas:
                w.writerow({k: fila.get(k, "") for k in [campo_t] + orden})
    if crudas:
        texto = (cabecera_crudo + "\n" if cabecera_crudo else "") + "\n".join(crudas) + "\n"
        crudo.write_text(texto, encoding="utf-8")

    print(f"\n{dur:.1f} s de grabacion, {len(filas)} muestras"
          + (f" ({len(filas) / dur:.1f} Hz)" if dur > 0 and filas else ""))
    if filas:
        print("columnas:", ", ".join([campo_t] + orden))
        print("archivo:", ancho)
        for k in ("degrees", "raw"):
            if k in orden:
                vals = [f[k] for f in filas if f.get(k) not in ("", None)]
                if vals:
                    print(f"  {k}: min {min(vals):.2f}  max {max(vals):.2f}")
    if crudas:
        print("lineas con comas (serial crudo):", crudo)
    print("inicio:", t0_wall.strftime("%Y-%m-%d %H:%M:%S"))
    return ancho


def main() -> None:
    ap = argparse.ArgumentParser(description="graba el serial del aeropendulo a CSV")
    ap.add_argument("-p", "--puerto", help="p.ej. /dev/ttyUSB0 (por defecto se detecta)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("-s", "--salida", default=str(Path(__file__).parent / "datos"))
    ap.add_argument("-g", "--grafico", action="store_true", help="ventana con grafica en vivo")
    args = ap.parse_args()

    puerto = elegir_puerto(args.puerto)
    print("puerto:", puerto, "a", args.baud, "baudios")
    grabar(puerto, args.baud, Path(args.salida), args.grafico)


if __name__ == "__main__":
    main()
