"""Ensambla brazo + brida + motor en un FCStd editable.

Cada pieza queda como objeto independiente: mueve o rota su Placement en el panel
de propiedades y vuelve a correr este script (o abre el .FCStd y edita a mano).
El motor es un Part::Cylinder parametrico: puedes cambiar radio y altura.
"""
import FreeCAD, Part, math

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
SALIDA = "/home/jysusman/Proyectos/AeroPendulo/modelado/ensamble.FCStd"

# --- parametros de montaje (editar aqui) ---
PIV = (24.7, -89.3, 0.0)        # centro del buje del brazo = eje del pivote
BRIDA_POS = (24.7, -89.3, 10.0) # brida apoyada en la cara superior del buje
BRIDA_ROT_EJE = (0, 0, 1)       # eje de giro de la brida
BRIDA_ROT_ANG = 0.0
MOT_POS = (24.6, -220.0, 5.0)   # centro del motor
MOT_R = 3.5                     # radio (mm)
MOT_L = 16.0                    # largo (mm)
MOT_EJE = (0, 1, 0)             # el cilindro nace en Z; se rota para tumbarlo
MOT_ANG = 90.0

placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA)

doc = FreeCAD.newDocument("aeropendulo")

cont = doc.addObject("App::Part", "Aeropendulo")

brazo = doc.addObject("Part::Feature", "Brazo")
brazo.Shape = placa
brazo.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

bri = doc.addObject("Part::Feature", "Brida")
bri.Shape = brida
bri.Placement = FreeCAD.Placement(
    FreeCAD.Vector(*BRIDA_POS),
    FreeCAD.Rotation(FreeCAD.Vector(*BRIDA_ROT_EJE), BRIDA_ROT_ANG))

mot = doc.addObject("Part::Cylinder", "Motor")
mot.Radius = MOT_R
mot.Height = MOT_L
mot.Placement = FreeCAD.Placement(
    FreeCAD.Vector(MOT_POS[0] - MOT_L / 2 * math.cos(math.radians(0)), MOT_POS[1], MOT_POS[2]),
    FreeCAD.Rotation(FreeCAD.Vector(*MOT_EJE), MOT_ANG))

cont.addObject(brazo)
cont.addObject(bri)
cont.addObject(mot)
doc.recompute()
doc.saveAs(SALIDA)

# --- masas e inercia respecto al eje del pivote ---
RHOS = {"Brazo": 1.27e-6, "Brida": 7.85e-6}
print("cuerpo   masa[g]  d_pivote[mm]  I_pivote[g·cm2]")
tm = tmd = tI = 0.0
for obj, rho in ((brazo, RHOS["Brazo"]), (bri, RHOS["Brida"]), (mot, None)):
    forma = obj.Shape
    if rho is None:
        m = 2.5e-3
        Iz = 0.5 * m * (MOT_R * 1e-3) ** 2
    else:
        m = sum(s.Volume for s in forma.Solids) * rho
        Iz = sum(s.MatrixOfInertia.A33 * rho * 1e-6 for s in forma.Solids)
    sols = forma.Solids
    vt = sum(s.Volume for s in sols)
    c = FreeCAD.Vector(sum(s.CenterOfMass.x * s.Volume for s in sols) / vt,
                       sum(s.CenterOfMass.y * s.Volume for s in sols) / vt, 0)
    # ojo: el Shape ya lleva aplicado el Placement, el centroide viene en coords globales
    d = math.hypot(c.x - PIV[0], c.y - PIV[1]) / 1000.0
    Ip = Iz + m * d ** 2
    tm += m; tmd += m * d; tI += Ip
    print("%-8s %7.2f %12.2f %14.0f" % (obj.Label, m * 1e3, d * 1e3, Ip * 1e7))
print("%-8s %7.2f %12.2f %14.0f" % ("TOTAL", tm * 1e3, tmd / tm * 1e3, tI * 1e7))
print("I = %.3e kg·m2 ; m·d = %.1f g·mm" % (tI, tmd * 1e6))
print("guardado", SALIDA)
