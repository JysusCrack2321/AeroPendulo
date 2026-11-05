"""Geometria compartida del aeropendulo: parametros, helpers y piezas armadas."""
import FreeCAD, Part

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
MPU = "/home/jysusman/Descargas/MPU6050 v2.step"

# ---------------- parametros de montaje ----------------
PIV = (24.7, -89.3, 0.0)            # eje del pivote (centro del buje)
BRIDA_POS = (24.7, -89.3, 0.0)      # brida colgando bajo la cara inferior
BRIDA_ROT_EJE, BRIDA_ROT_ANG = (1, 0, 0), 180.0
MOT_POS = (24.6, -220.0, 5.0)       # centro del motor
MOT_R, MOT_L = 3.5, 16.0
MOT_EJE, MOT_ANG = (0, 1, 0), 90.0
MPU_POS = (24.7, -89.3, 10.0)       # MPU sobre la cara superior del buje
MPU_ROT_EJE, MPU_ROT_ANG = (1, 0, 0), -90.0
MPU_MASA_G = 2.0
MOT_MASA_G = 2.5
AGUJEROS_BRIDA = ((16.7, -89.4), (32.7, -89.4))   # tornillos brazo -> brida
LARGO_TORNILLO = 10.0


def colocar(forma, rot_eje, rot_ang, destino, anclaje="centro"):
    """rota y traslada; anclaje: 'centro' | 'arriba' (cara sup.) | 'abajo' (cara inf.)"""
    f = forma.copy()
    f.transformShape(FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                       FreeCAD.Rotation(FreeCAD.Vector(*rot_eje), rot_ang)).toMatrix())
    bb = f.BoundBox
    if anclaje == "centro":
        dz = destino[2] - (bb.ZMin + bb.ZMax) / 2
    elif anclaje == "arriba":
        dz = destino[2] - bb.ZMax
    else:
        dz = destino[2] - bb.ZMin
    f.translate(FreeCAD.Vector(destino[0] - (bb.XMin + bb.XMax) / 2,
                               destino[1] - (bb.YMin + bb.YMax) / 2, dz))
    return f


def tornillo(x, y, z_cabeza, largo=None, d=3.0, cabe_d=5.5, cabe_h=2.0):
    largo = LARGO_TORNILLO if largo is None else largo
    vastago = Part.makeCylinder(d / 2, largo, FreeCAD.Vector(x, y, z_cabeza - largo))
    cabeza = Part.makeCylinder(cabe_d / 2, cabe_h, FreeCAD.Vector(x, y, z_cabeza))
    return vastago.fuse(cabeza)


def agujeros_mpu(mpu_shape):
    """centros de las perforaciones verticales del MPU ya colocado"""
    ag = set()
    for f in mpu_shape.Faces:
        if f.Surface.__class__.__name__ == "Cylinder" and 1.3 <= f.Surface.Radius <= 1.7 \
                and abs(f.Surface.Axis.z) > 0.9:
            c = f.Surface.Center
            ag.add((round(c.x, 2), round(c.y, 2)))
    return sorted(ag)


def construir():
    """devuelve {nombre: shape} con cada pieza ya colocada en su sitio"""
    placa = Part.Shape(); placa.read(PLACA)
    brida = Part.Shape(); brida.read(BRIDA)
    mpu = Part.Shape(); mpu.read(MPU)

    brida_pl = colocar(brida, BRIDA_ROT_EJE, BRIDA_ROT_ANG, BRIDA_POS, "arriba")
    mpu_pl = colocar(mpu, MPU_ROT_EJE, MPU_ROT_ANG, MPU_POS, "abajo")

    motor = Part.makeCylinder(MOT_R, MOT_L)
    motor.Placement = FreeCAD.Placement(FreeCAD.Vector(MOT_POS[0] - MOT_L / 2, MOT_POS[1], MOT_POS[2]),
                                        FreeCAD.Rotation(FreeCAD.Vector(*MOT_EJE), MOT_ANG))
    motor = motor.copy()
    motor.transformShape(motor.Placement.toMatrix())
    motor.Placement = FreeCAD.Placement()

    tr = [tornillo(x, y, MPU_POS[2] + 2.0) for (x, y) in agujeros_mpu(mpu_pl)]
    tr += [tornillo(x, y, 4.0) for (x, y) in AGUJEROS_BRIDA]

    return {"Brazo": placa, "Brida": brida_pl, "Motor": motor, "MPU": mpu_pl,
            "Tornillos": Part.makeCompound(tr)}
