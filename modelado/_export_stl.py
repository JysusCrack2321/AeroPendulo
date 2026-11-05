"""Exporta cada pieza a STL (/tmp) para el render con matplotlib."""
import os, sys, FreeCAD, Part, MeshPart

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piezas

p = piezas.construir()
for nombre, forma in p.items():
    m = MeshPart.meshFromShape(Shape=forma, LinearDeflection=0.3, AngularDeflection=0.35)
    m.write("/tmp/ens_%s.stl" % nombre.lower())
    print("stl", nombre.lower(), m.CountFacets)
