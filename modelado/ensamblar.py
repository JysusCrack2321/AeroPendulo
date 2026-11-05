"""Ensambla brazo + brida + motor + MPU + tornillos en un FCStd editable.

Los parametros de montaje estan en piezas.py: muevelos ahi y vuelve a correr.
El motor queda como Part::Cylinder parametrico (Radius / Height).
"""
import os, sys, math, FreeCAD, Part

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piezas

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensamble.FCStd")

p = piezas.construir()

doc = FreeCAD.newDocument("aeropendulo")
cont = doc.addObject("App::Part", "Aeropendulo")

brazo = doc.addObject("Part::Feature", "Brazo"); brazo.Shape = p["Brazo"]
bri = doc.addObject("Part::Feature", "Brida"); bri.Shape = p["Brida"]
mpu_obj = doc.addObject("Part::Feature", "MPU"); mpu_obj.Shape = p["MPU"]
tor = doc.addObject("Part::Feature", "Tornillos"); tor.Shape = p["Tornillos"]

mot = doc.addObject("Part::Cylinder", "Motor")
mot.Radius, mot.Height = piezas.MOT_R, piezas.MOT_L
mot.Placement = FreeCAD.Placement(
    FreeCAD.Vector(piezas.MOT_POS[0] - piezas.MOT_L / 2, piezas.MOT_POS[1], piezas.MOT_POS[2]),
    FreeCAD.Rotation(FreeCAD.Vector(*piezas.MOT_EJE), piezas.MOT_ANG))

for o in (brazo, bri, mot, mpu_obj, tor):
    cont.addObject(o)
doc.recompute()
doc.saveAs(SALIDA)

# ---------------- masa e inercia respecto al pivote ----------------
RHOS = {"Brazo": 1.27e-6, "Brida": 7.85e-6, "Tornillos": 7.85e-6}
print("cuerpo     masa[g]  d_pivote[mm]  I_pivote[g·cm2]")
tm = tmd = tI = 0.0
for obj in (brazo, bri, mot, mpu_obj, tor):
    forma = obj.Shape
    sols = forma.Solids
    vt = sum(s.Volume for s in sols)
    cm = FreeCAD.Vector(sum(s.CenterOfMass.x * s.Volume for s in sols) / vt,
                        sum(s.CenterOfMass.y * s.Volume for s in sols) / vt, 0)
    if obj.Name == "Motor":
        m = piezas.MOT_MASA_G * 1e-3
        Iz = 0.5 * m * (piezas.MOT_R * 1e-3) ** 2
    elif obj.Name == "MPU":
        m = piezas.MPU_MASA_G * 1e-3
        Iz = m * (0.008 ** 2)
    else:
        m = vt * RHOS[obj.Name]
        Iz = sum(s.MatrixOfInertia.A33 * RHOS[obj.Name] * 1e-6 for s in sols)
    d = math.hypot(cm.x - piezas.PIV[0], cm.y - piezas.PIV[1]) / 1000.0
    Ip = Iz + m * d ** 2
    tm += m; tmd += m * d; tI += Ip
    print("%-10s %7.2f %12.2f %16.0f" % (obj.Label, m * 1e3, d * 1e3, Ip * 1e7))

print("%-10s %7.2f %12.2f %16.0f" % ("TOTAL", tm * 1e3, tmd / tm * 1e3, tI * 1e7))
print("I = %.3e kg·m2 ; m·d = %.1f g·mm" % (tI, tmd * 1e6))
print("guardado", SALIDA)
