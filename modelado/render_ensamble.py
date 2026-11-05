import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def leer_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = int.from_bytes(f.read(4), "little")
        d = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
        return d[:, 12:48].copy().view("<f4").reshape(n, 3, 3)


cuerpos = [("brazo PETG", "/tmp/ens_brazo.stl", "#6c8ea8"),
           ("brida acero", "/tmp/ens_brida.stl", "#b9bec6"),
           ("motor", "/tmp/ens_motor.stl", "#e8590c"),
           ("MPU", "/tmp/ens_mpu.stl", "#2b8a3e")]

fig = plt.figure(figsize=(14, 7.5))
for i, (elev, azim, titulo) in enumerate([(22, -62, "ensamble - isometrica"), (89, -90, "ensamble - planta")], 1):
    ax = fig.add_subplot(1, 2, i, projection="3d")
    for n, p, col in cuerpos:
        tri = leer_stl(p)
        ax.add_collection3d(Poly3DCollection(tri, facecolor=col, edgecolor="#33414a", linewidths=0.08))
    ax.set_xlim(5, 45); ax.set_ylim(-245, -55); ax.set_zlim(-20, 25)
    try:
        ax.set_box_aspect((40, 190, 45))
    except Exception:
        pass
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(titulo)
    ax.set_xlabel("X"); ax.set_ylabel("Y"); ax.set_zlabel("Z")
plt.tight_layout()
plt.savefig("/home/jysusman/Proyectos/AeroPendulo/modelado/ensamble.png", dpi=120)
print("ok")
