#!/usr/bin/env python3
"""Genera los SVG del proyecto a partir de la geometria medida en el STEP.

Medidas del modelo (mm): placa de 200.3 de largo, 10 de ancho, 4 de espesor;
buje de D27 con barreno pasante y 4 tornillos M5 a 8 mm del centro, situado a
55 mm de un extremo y 145 mm del otro; extremos ahusados y buje realzado 10 mm.
"""
import math, pathlib

VAULT = pathlib.Path("/home/jysusman/My-obsidian-vault/Universidad 2026-2/Tecnicas de contro/proyecto")

K = 1.50           # px por mm
L_LARGO = 145.0    # pivote -> punta del motor
L_CORTO = 55.0     # pivote -> extremo trasero
ANCHO = 10.0
BUJE_D = 27.0
THETA = 32.0       # grados sobre la horizontal
COS, SEN = math.cos(math.radians(THETA)), math.sin(math.radians(THETA))


def P(piv, u, v):
    """(u a lo largo del brazo, v perpendicular) en mm -> px"""
    return (piv[0] + (u * COS + v * SEN) * K,
            piv[1] + (-u * SEN + v * COS) * K)


def poly(piv, pts):
    return " ".join("%.1f,%.1f" % P(piv, u, v) for u, v in pts)


DEFS = '''  <defs>
    <marker id="ab" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,1 L10,5 L0,9 z" fill="#1c7ed6"/></marker>
    <marker id="ag" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,1 L10,5 L0,9 z" fill="#2b8a3e"/></marker>
    <marker id="ao" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,1 L10,5 L0,9 z" fill="#e8590c"/></marker>
    <marker id="agr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
      <path d="M0,1 L10,5 L0,9 z" fill="#868e96"/></marker>
  </defs>
'''


def placa(piv):
    """contorno de la placa: barra de 10 mm con los dos extremos ahusados"""
    w = ANCHO / 2
    pts = [(-L_CORTO, 0), (-L_CORTO + 7, -3.0), (-L_CORTO + 9, -w),
           (L_LARGO - 14, -w), (L_LARGO - 3, -2.4), (L_LARGO, 0),
           (L_LARGO - 3, 2.4), (L_LARGO - 14, w), (-L_CORTO + 9, w),
           (-L_CORTO + 7, 3.0)]
    return '<polygon points="%s" fill="#495057" stroke="#343a40" stroke-width="1.6"/>' % poly(piv, pts)


def arco(piv, r_px, n=14):
    """arco del angulo como polilinea: de la horizontal al brazo"""
    o = []
    for i in range(n + 1):
        a = math.radians(-THETA * i / n)
        o.append("%.1f,%.1f" % (piv[0] + r_px * math.cos(a), piv[1] + r_px * math.sin(a)))
    return ('  <polyline points="%s" fill="none" stroke="#1c7ed6" stroke-width="1.6"/>' % " ".join(o),
            (piv[0] + r_px * math.cos(math.radians(-THETA / 2)),
             piv[1] + r_px * math.sin(math.radians(-THETA / 2))))


def buje(piv, tornillos=True):
    x, y = piv
    o = ['  <circle cx="%.1f" cy="%.1f" r="%.1f" fill="#868e96" stroke="#343a40" stroke-width="1.6"/>'
         % (x, y, BUJE_D / 2 * K)]
    if tornillos:
        for du, dv in ((8, 8), (8, -8), (-8, 8), (-8, -8)):
            sx, sy = P(piv, du, dv)
            o.append('  <circle cx="%.1f" cy="%.1f" r="3.4" fill="#f1f3f5" stroke="#343a40" stroke-width="1.1"/>' % (sx, sy))
    o.append('  <circle cx="%.1f" cy="%.1f" r="9" fill="#ffffff" stroke="#1c7ed6" stroke-width="3"/>' % (x, y))
    o.append('  <circle cx="%.1f" cy="%.1f" r="2.4" fill="#1c7ed6"/>' % (x, y))
    return "\n".join(o)


def cuerpo_libre():
    piv = (225.0, 318.0)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 470" font-family="sans-serif" font-size="13">',
         DEFS,
         '  <rect x="1" y="1" width="678" height="468" rx="12" fill="#ffffff" stroke="#dee2e6" stroke-width="1.5"/>',
         '  <text x="25" y="32" fill="#212529" font-size="16" font-weight="bold">Diagrama de cuerpo libre del brazo</text>',
         '  <line x1="25" y1="44" x2="655" y2="44" stroke="#e9ecef" stroke-width="1.5"/>']

    px, py = piv
    # apoyo fijo (triangulo con rayado) bajo el pivote
    o.append('  <path d="M%.0f,%.0f L%.0f,%.0f L%.0f,%.0f Z" fill="#e9ecef" stroke="#495057" stroke-width="1.6"/>'
             % (px, py + 14, px - 22, py + 50, px + 22, py + 50))
    o.append('  <g stroke="#adb5bd" stroke-width="1.5">')
    for dx in (-26, -13, 0, 13, 26):
        o.append('    <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f"/>' % (px + dx, py + 50, px + dx - 10, py + 60))
    o.append('  </g>')

    # referencia horizontal
    o.append('  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#adb5bd" stroke-width="1.2" stroke-dasharray="7 5"/>'
             % (px, py, px + 330, py))

    # eje del brazo (punteado) y placa
    a0, a1 = P(piv, -L_CORTO - 8, 0), P(piv, L_LARGO + 12, 0)
    o.append('  <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ced4da" stroke-width="1" stroke-dasharray="4 4"/>'
             % (a0[0], a0[1], a1[0], a1[1]))
    o.append('  ' + placa(piv))
    o.append(buje(piv))

    # arco del angulo
    linea_arco, etiqueta = arco(piv, 120)
    o.append(linea_arco)
    o.append('  <text x="%.0f" y="%.0f" fill="#1c7ed6" font-size="16" font-style="italic">&#952;</text>'
             % (etiqueta[0] + 2, etiqueta[1] + 4))

    # peso en el centro de masa
    cx, cy = P(piv, 70.0, 0)
    o.append('  <circle cx="%.1f" cy="%.1f" r="4.4" fill="#2b8a3e"/>' % (cx, cy))
    o.append('  <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#2b8a3e" stroke-width="2.6" marker-end="url(#ag)"/>'
             % (cx, cy + 4, cx, cy + 100))
    o.append('  <text x="%.1f" y="%.1f" fill="#2b8a3e" font-size="14" font-style="italic">m g</text>' % (cx + 9, cy + 96))
    o.append('  <text x="%.1f" y="%.1f" fill="#2b8a3e" font-size="11" text-anchor="end">CM</text>' % (cx - 8, cy - 7))

    # empuje perpendicular al brazo en la punta
    tx, ty = P(piv, L_LARGO, 0)
    fx, fy = P(piv, L_LARGO, -48)
    o.append('  <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e8590c" stroke-width="3.2" marker-end="url(#ao)"/>'
             % (tx, ty, fx, fy))
    o.append('  <text x="%.1f" y="%.1f" fill="#e8590c" font-size="15" font-style="italic">F</text>' % (fx - 20, fy + 2))
    o.append('  <text x="%.1f" y="%.1f" fill="#e8590c" font-size="11" text-anchor="end">empuje</text>' % (fx - 24, fy + 16))
    o.append('  <circle cx="%.1f" cy="%.1f" r="3.6" fill="#e8590c"/>' % (tx, ty))

    # cota L, desplazada por debajo del brazo
    d0, d1 = P(piv, -2, -34), P(piv, L_LARGO + 2, -34)
    o.append('  <g stroke="#868e96" stroke-width="1.2">')
    o.append('    <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" marker-start="url(#agr)" marker-end="url(#agr)"/>'
             % (d0[0], d0[1], d1[0], d1[1]))
    o.append('    <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (px, py, P(piv, 0, -38)[0], P(piv, 0, -38)[1]))
    o.append('    <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (tx, ty, P(piv, L_LARGO, -38)[0], P(piv, L_LARGO, -38)[1]))
    o.append('  </g>')
    mx, my = P(piv, L_LARGO / 2, -34)
    o.append('  <text x="%.1f" y="%.1f" fill="#868e96" font-size="12" text-anchor="middle">L = 145 mm</text>'
             % (mx + 4, my - 7))

    o.append('</svg>')
    (VAULT / "cuerpo-libre.svg").write_text("\n".join(o) + "\n", encoding="utf-8")


def planta():
    piv = (250.0, 250.0)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 470" font-family="sans-serif" font-size="13">',
         DEFS,
         '  <rect x="1" y="1" width="678" height="468" rx="12" fill="#ffffff" stroke="#dee2e6" stroke-width="1.5"/>',
         '  <text x="25" y="32" fill="#212529" font-size="16" font-weight="bold">Planta: aeropendulo (brazo de 200 mm, motor-helice en la punta)</text>',
         '  <line x1="25" y1="44" x2="655" y2="44" stroke="#e9ecef" stroke-width="1.5"/>']

    # base + columna
    o.append('  <rect x="150" y="404" width="230" height="16" rx="3" fill="#e9ecef" stroke="#ced4da" stroke-width="1.5"/>')
    o.append('  <g stroke="#adb5bd" stroke-width="1.5">')
    for x in range(165, 380, 22):
        o.append('    <line x1="%d" y1="420" x2="%d" y2="430"/>' % (x, x - 10))
    o.append('  </g>')
    o.append('  <path d="M%.0f,404 L%.0f,272 L%.0f,272 L%.0f,404 Z" fill="#f1f3f5" stroke="#495057" stroke-width="1.8"/>'
             % (piv[0] - 46, piv[0] - 13, piv[0] + 13, piv[0] + 46))
    o.append('  <text x="208" y="446" fill="#495057" font-size="12">base</text>')

    o.append('  <line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="#adb5bd" stroke-width="1.2" stroke-dasharray="7 5"/>'
             % (piv[0], piv[1], piv[0] + 330, piv[1]))

    o.append('  ' + placa(piv))
    o.append(buje(piv))

    # angulo
    linea_arco, etiqueta = arco(piv, 95)
    o.append(linea_arco)
    o.append('  <text x="%.0f" y="%.0f" fill="#1c7ed6" font-size="16" font-style="italic">&#952;</text>'
             % (etiqueta[0] + 2, etiqueta[1] + 4))

    # motor + helice en la punta
    tx, ty = P(piv, L_LARGO, 0)
    o.append('  <g transform="rotate(%.1f, %.1f, %.1f)">' % (-THETA, tx, ty))
    o.append('    <rect x="%.1f" y="%.1f" width="30" height="20" rx="3" fill="#ffe8cc" stroke="#e8590c" stroke-width="2"/>'
             % (tx - 34, ty - 10))
    o.append('    <ellipse cx="%.1f" cy="%.1f" rx="3.2" ry="22" fill="#ffa94d" fill-opacity="0.9" stroke="#e8590c" stroke-width="1.4"/>'
             % (tx + 5, ty))
    o.append('  </g>')
    o.append('  <circle cx="%.1f" cy="%.1f" r="3.4" fill="#e8590c"/>' % (tx, ty))

    # empuje perpendicular, arrancando mas alla de las aspas
    ox, oy = P(piv, L_LARGO + 16, 0)
    fx, fy = P(piv, L_LARGO + 16, -50)
    o.append('  <line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#e8590c" stroke-width="3" marker-end="url(#ao)"/>'
             % (ox, oy, fx, fy))
    o.append('  <text x="%.1f" y="%.1f" fill="#e8590c" font-size="15" font-style="italic">F</text>' % (fx - 18, fy + 2))
    o.append('  <text x="%.1f" y="%.1f" fill="#e8590c" font-size="11" text-anchor="end">empuje</text>' % (fx - 22, fy + 16))
    o.append('  <text x="%.1f" y="%.1f" fill="#e8590c" font-size="12">motor + helice</text>' % (ox + 12, oy + 22))

    o.append('</svg>')
    (VAULT / "planta.svg").write_text("\n".join(o) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cuerpo_libre()
    planta()
    print("escritos")
