import FreeCAD, Part, math

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
SALIDA = "/home/jysusman/Proyectos/AeroPendulo/modelado/ensamble.FCStd"

placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA)

PIV = (24.7, -89.3, 0.0)      # centro del buje del brazo
MOT = (24.6, -220.0, 5.0)     # centro entre los dos agujeros de la punta

brida_pl = brida.copy()
brida_pl.translate(FreeCAD.Vector(*PIV))

motor = Part.makeCylinder(3.5, 16.0)
motor.Placement = FreeCAD.Placement(FreeCAD.Vector(MOT[0] - 8.0, MOT[1], MOT[2]),
                                    FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90))

doc = FreeCAD.newDocument("aeropendulo")
for nombre, forma in (("brazo_petg", placa), ("brida_acero", brida_pl), ("motor", motor)):
    obj = doc.addObject("Part::Feature", nombre)
    obj.Shape = forma
doc.recompute()
doc.saveAs(SALIDA)

RHOS = {"brazo_petg": 1.27e-6, "brida_acero": 7.85e-6}   # kg/mm3

print("cuerpo          masa[g]  d_pivote[mm]  I_pivote[g·cm2]")
tm = tmd = tI = 0.0
for nombre, forma in (("brazo_petg", placa), ("brida_acero", brida_pl), ("motor", motor)):
    if nombre == "motor":
        m = 2.5e-3
        Iz = 0.5 * m * (3.5e-3) ** 2
        c = motor.Solids[0].CenterOfMass
    else:
        m = sum(s.Volume for s in forma.Solids) * RHOS[nombre]
        Iz = sum(s.MatrixOfInertia.A33 * RHOS[nombre] * 1e-6 for s in forma.Solids)
        # centro de masa ponderado por volumen
        vt = sum(s.Volume for s in forma.Solids)
        cx = sum(s.CenterOfMass.x * s.Volume for s in forma.Solids) / vt
        cy = sum(s.CenterOfMass.y * s.Volume for s in forma.Solids) / vt
        c = FreeCAD.Vector(cx, cy, 0)
    d = math.hypot(c.x - PIV[0], c.y - PIV[1]) / 1000.0        # m
    Ip = Iz + m * d ** 2
    tm += m; tmd += m * d; tI += Ip
    print("%-14s %7.2f %12.2f %12.0f" % (nombre, m * 1e3, d * 1e3, Ip * 1e7))

print("%-14s %7.2f %12.2f %12.0f" % ("TOTAL", tm * 1e3, tmd / tm * 1e3, tI * 1e7))
print("I_pivote = %.3e kg·m2   (%.0f g·cm2)" % (tI, tI * 1e7))
print("m·d = %.1f g·mm" % (tmd * 1e6))
print("guardado", SALIDA)
