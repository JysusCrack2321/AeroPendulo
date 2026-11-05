"""Ensambla brazo + brida + motor + MPU en un FCStd editable.

Cada pieza es un objeto independiente con su Placement: muevela en el panel de
propiedades y vuelve a correr el script para recalcular masa e inercia.
El motor es un Part::Cylinder parametrico (Radius / Height).
"""
import FreeCAD, Part, math

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
MPU = "/home/jysusman/Descargas/MPU6050 v2.step"
SALIDA = "/home/jysusman/Proyectos/AeroPendulo/modelado/ensamble.FCStd"

# ---------------- parametros de montaje ----------------
PIV = (24.7, -89.3, 0.0)          # eje del pivote (centro del buje)
BRIDA_POS = (24.7, -89.3, 0.0)    # brida colgando bajo la cara inferior
BRIDA_ROT_EJE, BRIDA_ROT_ANG = (1, 0, 0), 180.0
MOT_POS = (24.6, -220.0, 5.0)     # centro del motor
MOT_R, MOT_L = 3.5, 16.0
MOT_EJE, MOT_ANG = (0, 1, 0), 90.0
MPU_POS = (24.7, -89.3, 10.0)    # MPU sobre la cara superior del buje
MPU_ROT_EJE, MPU_ROT_ANG = (1, 0, 0), -90.0   # tumbada sobre el brazo
MPU_MASA_G = 2.0                  # pesala y ajusta este numero

placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA)
mpu = Part.Shape(); mpu.read(MPU)


def colocar(forma, rot_eje, rot_ang, destino, anclaje="centro"):
    """rota y traslada. anclaje='centro' centra la caja; 'arriba' apoya la cara superior"""
    f = forma.copy()
    f.transformShape(FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                       FreeCAD.Rotation(FreeCAD.Vector(*rot_eje), rot_ang)).toMatrix())
    bb = f.BoundBox
    if anclaje == "centro":
        dz = destino[2] - (bb.ZMin + bb.ZMax) / 2
    elif anclaje == "arriba":
        dz = destino[2] - bb.ZMax
    else:                      # "abajo": apoya la cara inferior
        dz = destino[2] - bb.ZMin
    f.translate(FreeCAD.Vector(destino[0] - (bb.XMin + bb.XMax) / 2,
                               destino[1] - (bb.YMin + bb.YMax) / 2, dz))
    return f


brida_pl = colocar(brida, BRIDA_ROT_EJE, BRIDA_ROT_ANG, BRIDA_POS, "arriba")
mpu_pl = colocar(mpu, MPU_ROT_EJE, MPU_ROT_ANG, MPU_POS, "abajo")

def tornillo(x, y, z_cabeza, largo=10.0, d=3.0, cabe_d=5.5, cabe_h=2.0):
    """M3 simplificado: vastago + cabeza, cabeza apoyada en z_cabeza y vastago hacia abajo"""
    vastago = Part.makeCylinder(d / 2, largo, FreeCAD.Vector(x, y, z_cabeza - largo))
    cabeza = Part.makeCylinder(cabe_d / 2, cabe_h, FreeCAD.Vector(x, y, z_cabeza))
    return vastago.fuse(cabeza)


# agujeros del MPU ya colocado (verticales, r ~1.5)
agujeros_mpu = set()
for f in mpu_pl.Faces:
    if f.Surface.__class__.__name__ == "Cylinder" and 1.3 <= f.Surface.Radius <= 1.7 \
            and abs(f.Surface.Axis.z) > 0.9:
        c = f.Surface.Center
        agujeros_mpu.add((round(c.x, 2), round(c.y, 2)))
agujeros_mpu = sorted(agujeros_mpu)
print("agujeros MPU:", agujeros_mpu)

tornillos = []
for (x, y) in agujeros_mpu:                       # 2 tornillos MPU -> brazo
    tornillos.append(tornillo(x, y, MPU_POS[2] + 2.0))
for (x, y) in ((16.7, -89.4), (32.7, -89.4)):     # 2 tornillos brazo -> brida
    tornillos.append(tornillo(x, y, 4.0))

doc = FreeCAD.newDocument("aeropendulo")
cont = doc.addObject("App::Part", "Aeropendulo")

brazo = doc.addObject("Part::Feature", "Brazo")
brazo.Shape = placa

bri = doc.addObject("Part::Feature", "Brida")
bri.Shape = brida_pl

mot = doc.addObject("Part::Cylinder", "Motor")
mot.Radius, mot.Height = MOT_R, MOT_L
mot.Placement = FreeCAD.Placement(
    FreeCAD.Vector(MOT_POS[0] - MOT_L / 2, MOT_POS[1], MOT_POS[2]),
    FreeCAD.Rotation(FreeCAD.Vector(*MOT_EJE), MOT_ANG))

mpu_obj = doc.addObject("Part::Feature", "MPU")
mpu_obj.Shape = mpu_pl

tor = doc.addObject("Part::Feature", "Tornillos")
tor.Shape = Part.makeCompound(tornillos)

for o in (brazo, bri, mot, mpu_obj, tor):
    cont.addObject(o)
doc.recompute()
doc.saveAs(SALIDA)

# ---------------- masa e inercia respecto al pivote ----------------
RHOS = {"Brazo": 1.27e-6, "Brida": 7.85e-6}
print("cuerpo   masa[g]  d_pivote[mm]  I_pivote[g·cm2]")
tm = tmd = tI = 0.0
for obj in (brazo, bri, mot, mpu_obj, tor):
    forma = obj.Shape
    sols = forma.Solids
    vt = sum(s.Volume for s in sols)
    cm = FreeCAD.Vector(sum(s.CenterOfMass.x * s.Volume for s in sols) / vt,
                        sum(s.CenterOfMass.y * s.Volume for s in sols) / vt, 0)
    if obj.Name == "Motor":
        m = 2.5e-3
        Iz = 0.5 * m * (MOT_R * 1e-3) ** 2
    elif obj.Name == "Tornillos":
        m = vt * 7.85e-6
        Iz = sum(s.MatrixOfInertia.A33 * 7.85e-6 * 1e-6 for s in sols)
    elif obj.Name == "MPU":
        m = MPU_MASA_G * 1e-3
        Iz = m * (0.008 ** 2)          # despreciable, solo por completitud
    else:
        m = vt * RHOS[obj.Name]
        Iz = sum(s.MatrixOfInertia.A33 * RHOS[obj.Name] * 1e-6 for s in sols)
    d = math.hypot(cm.x - PIV[0], cm.y - PIV[1]) / 1000.0
    Ip = Iz + m * d ** 2
    tm += m; tmd += m * d; tI += Ip
    print("%-8s %7.2f %12.2f %14.0f" % (obj.Label, m * 1e3, d * 1e3, Ip * 1e7))

print("%-8s %7.2f %12.2f %14.0f" % ("TOTAL", tm * 1e3, tmd / tm * 1e3, tI * 1e7))
print("I = %.3e kg·m2 ; m·d = %.1f g·mm" % (tI, tmd * 1e6))
print("guardado", SALIDA)
