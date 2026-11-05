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

for nombre, forma in (("brazo", placa), ("brida", brida_pl), ("motor", motor), ("mpu", mpu_pl)):
    m = MeshPart.meshFromShape(Shape=forma, LinearDeflection=0.3, AngularDeflection=0.35)
    m.write("/tmp/ens_%s.stl" % nombre)
    print("stl", nombre, m.CountFacets)
