import FreeCAD, Part, MeshPart

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
MPU = "/home/jysusman/Descargas/MPU6050 v2.step"

PIV = (24.7, -89.3, 0.0)
MOT = (24.6, -220.0, 5.0)
MPU_POS = (24.7, -122.2, 4.0)


def colocar(forma, rot_eje, rot_ang, destino):
    f = forma.copy()
    f.transformShape(FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                       FreeCAD.Rotation(FreeCAD.Vector(*rot_eje), rot_ang)).toMatrix())
    bb = f.BoundBox
    f.translate(FreeCAD.Vector(destino[0] - (bb.XMin + bb.XMax) / 2,
                               destino[1] - (bb.YMin + bb.YMax) / 2,
                               destino[2] - (bb.ZMin + bb.ZMax) / 2))
    return f


placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA)
mpu = Part.Shape(); mpu.read(MPU)

brida_pl = colocar(brida, (1, 0, 0), 180.0, (24.7, -89.3, 0.0))
mpu_pl = colocar(mpu, (1, 0, 0), -90.0, MPU_POS)

motor = Part.makeCylinder(3.5, 16.0)
motor.Placement = FreeCAD.Placement(FreeCAD.Vector(MOT[0] - 8.0, MOT[1], MOT[2]),
                                    FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90))

for nombre, forma in (("brazo", placa), ("brida", brida_pl), ("motor", motor), ("mpu", mpu_pl)):
    m = MeshPart.meshFromShape(Shape=forma, LinearDeflection=0.3, AngularDeflection=0.35)
    m.write("/tmp/ens_%s.stl" % nombre)
    print("stl", nombre, m.CountFacets)
