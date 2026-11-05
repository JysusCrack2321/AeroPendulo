import FreeCAD, Part, MeshPart

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
MPU = "/home/jysusman/Descargas/MPU6050 v2.step"

PIV = (24.7, -89.3, 0.0)
MOT = (24.6, -220.0, 5.0)
MPU_POS = (24.7, -89.3, 10.0)


def colocar(forma, rot_eje, rot_ang, destino, anclaje="centro"):
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


placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA)
mpu = Part.Shape(); mpu.read(MPU)

brida_pl = colocar(brida, (1, 0, 0), 180.0, (24.7, -89.3, 0.0), "arriba")
mpu_pl = colocar(mpu, (1, 0, 0), -90.0, MPU_POS, "abajo")

motor = Part.makeCylinder(3.5, 16.0)
motor.Placement = FreeCAD.Placement(FreeCAD.Vector(MOT[0] - 8.0, MOT[1], MOT[2]),
                                    FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90))

def tornillo(x, y, z_cabeza, largo=10.0, d=3.0, cabe_d=5.5, cabe_h=2.0):
    vastago = Part.makeCylinder(d / 2, largo, FreeCAD.Vector(x, y, z_cabeza - largo))
    cabeza = Part.makeCylinder(cabe_d / 2, cabe_h, FreeCAD.Vector(x, y, z_cabeza))
    return vastago.fuse(cabeza)


agujeros = set()
for f in mpu_pl.Faces:
    if f.Surface.__class__.__name__ == "Cylinder" and 1.3 <= f.Surface.Radius <= 1.7 \
            and abs(f.Surface.Axis.z) > 0.9:
        c = f.Surface.Center
        agujeros.add((round(c.x, 2), round(c.y, 2)))

tornillos = [tornillo(x, y, MPU_POS[2] + 2.0) for (x, y) in sorted(agujeros)]
tornillos += [tornillo(x, y, 4.0) for (x, y) in ((16.7, -89.4), (32.7, -89.4))]

for nombre, forma in (("brazo", placa), ("brida", brida_pl), ("motor", motor),
                      ("mpu", mpu_pl), ("tornillos", Part.makeCompound(tornillos))):
    m = MeshPart.meshFromShape(Shape=forma, LinearDeflection=0.3, AngularDeflection=0.35)
    m.write("/tmp/ens_%s.stl" % nombre)
    print("stl", nombre, m.CountFacets)
