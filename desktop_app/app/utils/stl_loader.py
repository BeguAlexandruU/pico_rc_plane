import numpy as np
from stl import mesh

_SCALE = 10


def load_stl(path: str) -> tuple | None:
    try:
        stl_mesh = mesh.Mesh.from_file(path)
        verts = stl_mesh.vectors.reshape(-1, 3) * _SCALE
        center = (verts.min(axis=0) + verts.max(axis=0)) / 2.0
        verts = verts - center
        verts[:, 0] = -verts[:, 0]
        verts[:, 1] = -verts[:, 1]
        faces = np.arange(len(verts)).reshape(-1, 3)
        return verts, faces
    except Exception:
        return None
