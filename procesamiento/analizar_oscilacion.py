#!/usr/bin/env python3
"""Analiza una oscilacion libre: periodo, envolvente y friccion viscosa b.

Uso:
    ./analizar_oscilacion.py datos/registro_XXX.csv
    ./analizar_oscilacion.py registro.csv --columna degrees --guardar decaimiento.png

Modelo: I*theta'' + b*theta' + m*g*d*theta = 0  (colgando, angulo pequeno)
     ->  sigma = b / (2I)          decaimiento de la envolvente
     ->  omega_n = sqrt(m*g*d/I)   pulsacion natural

Con la envolvente A(t) = A0*exp(-sigma*t) medida sobre los picos, se despeja
    b = 2*I*sigma.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

# valores del ensamble medido (kg, m)
MASA = 31.72e-3
D_CM = 24.52e-3
INERCIA = 9.455e-5
G = 9.81


def cargar(ruta: Path, columna: str) -> tuple[np.ndarray, np.ndarray]:
    """lee el CSV sin pandas: solo csv + numpy"""
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        campos = [c.strip() for c in (lector.fieldnames or [])]
        lector.fieldnames = campos
        if columna not in campos:
            cand = [c for c in campos if any(k in c.lower() for k in ("deg", "ang", "theta"))]
            if not cand:
                raise SystemExit(f"no encuentro columna de angulo en {campos}")
            columna = cand[0]
            print(f"(usando columna '{columna}')")
        tcol = "t_s" if "t_s" in campos else campos[0]
        t, y = [], []
        for fila in lector:
            try:
                tv, yv = float(fila[tcol]), float(fila[columna])
            except (TypeError, ValueError):
                continue
            t.append(tv)
            y.append(yv)
    t = np.asarray(t)
    y = np.asarray(y)
    if t.size == 0:
        raise SystemExit("el archivo no tiene filas numericas")
    if t.max() > 1000:                     # venia en ms
        t = t / 1000.0
    return t, y


def desenvolver(y: np.ndarray) -> np.ndarray:
    """si el angulo viene envuelto en 0-360, lo deja continuo"""
    dy = np.diff(y)
    saltos = np.abs(dy) > 180
    if saltos.sum() == 0:
        return y
    y = y.copy()
    for i in np.flatnonzero(saltos):
        y[i + 1:] -= 360.0 * np.sign(dy[i])
    return y


def picos(t: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import find_peaks
    # picos (maximos) separados al menos un cuarto del periodo esperado
    try:
        from scipy.signal import periodogram
        f, P = periodogram(y - y.mean(), fs=1.0 / np.median(np.diff(t)))
        fdom = f[1:][np.argmax(P[1:])]
        dist = max(3, int(0.25 / (fdom * np.median(np.diff(t)))))
    except Exception:
        dist = 3
    idx, _ = find_peaks(y, distance=dist, prominence=max(1e-9, 0.05 * np.ptp(y)))
    return t[idx], y[idx]


def main() -> None:
    ap = argparse.ArgumentParser(description="friccion viscosa y periodo desde una oscilacion libre")
    ap.add_argument("archivo", type=Path)
    ap.add_argument("--columna", default="degrees")
    ap.add_argument("--inercia", type=float, default=INERCIA, help="kg·m2")
    ap.add_argument("--masa", type=float, default=MASA, help="kg")
    ap.add_argument("--d", type=float, default=D_CM, help="kg... distancia CM-pivote en m")
    ap.add_argument("--guardar", type=Path, help="PNG de salida")
    args = ap.parse_args()

    t, y = cargar(args.archivo, args.columna)
    y = desenvolver(y)
    y = y - y.mean()

    tp, yp = picos(t, y)
    if len(tp) < 3:
        raise SystemExit(f"solo {len(tp)} picos: la grabacion no alcanza para ajustar la envolvente")

    A = np.abs(yp)
    coef = np.polyfit(tp, np.log(A), 1)
    sigma = -coef[0]
    A0 = np.exp(coef[1])
    pred = np.polyval(coef, tp)
    ss_res = np.sum((np.log(A) - pred) ** 2)
    ss_tot = np.sum((np.log(A) - np.log(A).mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    I, m, d = args.inercia, args.masa, args.d
    b = 2 * I * sigma
    wn = np.sqrt(m * G * d / I)
    zeta = b / (2 * np.sqrt(I * m * G * d))
    periodos = np.diff(tp)
    T_med = float(np.median(periodos))

    print(f"archivo:      {args.archivo}")
    print(f"muestras:     {len(t)} en {t.max() - t.min():.2f} s")
    print(f"picos:        {len(tp)}")
    print(f"periodo:      {T_med * 1000:.1f} ms   (wn medido {2 * np.pi / T_med:.2f} rad/s)")
    print(f"wn esperado:  {wn:.2f} rad/s   (T = {2 * np.pi / wn * 1000:.0f} ms)")
    print(f"envolvente:   A0 = {A0:.2f} deg,  sigma = {sigma:.4f} 1/s  (R2 = {r2:.4f})")
    print(f"friccion:     b = {b:.3e} kg·m2/s   zeta = {zeta:.4f}")
    tau = 1 / sigma if sigma > 0 else float("inf")
    print(f"constante de tiempo de la envolvente: {tau:.2f} s"
          + (f"  ({np.log(2) * tau:.2f} s para caer a la mitad)" if np.isfinite(tau) else ""))

    if args.guardar:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(t, y, lw=0.9, color="#495057", label="angulo")
        ax.plot(tp, yp, "o", ms=3, color="#1c7ed6", label="picos")
        tt = np.linspace(t.min(), t.max(), 400)
        ax.plot(tt, A0 * np.exp(-sigma * tt), "--", color="#e8590c", label="envolvente")
        ax.plot(tt, -A0 * np.exp(-sigma * tt), "--", color="#e8590c")
        ax.set_xlabel("t (s)")
        ax.set_ylabel("angulo (deg)")
        ax.set_title(f"sigma = {sigma:.3f} 1/s   ->   b = {b:.2e} kg·m2/s")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout()
        fig.savefig(args.guardar, dpi=130)
        print("grafica:", args.guardar)


if __name__ == "__main__":
    main()
