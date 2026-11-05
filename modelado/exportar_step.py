"""Exporta el ensamble a STEP y cada pieza por separado."""
import os, sys, FreeCAD, Part

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piezas

BASE = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(BASE, "steps")
os.makedirs(SALIDA, exist_ok=True)

p = piezas.construir()

# ensamble completo
comp = Part.makeCompound(list(p.values()))
comp.exportStep(os.path.join(BASE, "ensamble.step"))
print("ensamble.step", round(os.path.getsize(os.path.join(BASE, "ensamble.step")) / 1024, 1), "KB")

# piezas sueltas
for nombre, forma in p.items():
    ruta = os.path.join(SALIDA, "%s.step" % nombre.lower())
    forma.exportStep(ruta)
    print("  steps/%s.step  %.1f KB  vol %.1f mm3" % (
        nombre.lower(), os.path.getsize(ruta) / 1024, forma.Volume))
