import FreeCAD, Part, MeshPart

PLACA = "/home/jysusman/Proyectos/AeroPendulo/modelado/Estructura-Pendulo-3D.step"
BRIDA = "/home/jysusman/Descargas/5mm Flange Coupling Connector.step"
PIV = (24.7, -89.3, 0.0)
MOT = (24.6, -220.0, 5.0)

placa = Part.Shape(); placa.read(PLACA)
brida = Part.Shape(); brida.read(BRIDA); brida.translate(FreeCAD.Vector(PIV[0], PIV[1], 10.0))
motor = Part.makeCylinder(3.5, 16.0)
motor.Placement = FreeCAD.Placement(FreeCAD.Vector(MOT[0] - 8.0, MOT[1], MOT[2]),
                                    FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90))

for nombre, forma in (("brazo", placa), ("brida", brida), ("motor", motor)):
    m = MeshPart.meshFromShape(Shape=forma, LinearDeflection=0.3, AngularDeflection=0.35)
    m.write("/tmp/ens_%s.stl" % nombre)
    print("stl", nombre, m.CountFacets)
