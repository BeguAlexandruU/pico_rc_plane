import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class Full3DView(QWidget):
    _SCALE = 10_000

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.gl_view = gl.GLViewWidget()
        self.gl_view.setCameraPosition(distance=40, elevation=25, azimuth=45)
        layout.addWidget(self.gl_view)

        self.grid = gl.GLGridItem()
        self.grid.setSize(100, 100)
        self.grid.setSpacing(5, 5)
        self.grid.translate(0, 0, -1)
        self.gl_view.addItem(self.grid)
        self.gl_view.addItem(gl.GLAxisItem())

        self._plane = None
        self._origin = None

    def load_model(self, verts: np.ndarray, faces: np.ndarray):
        self._plane = gl.GLMeshItem(
            vertexes=verts, faces=faces,
            color=(0.20, 0.80, 1.0, 1.0), shader="shaded", smooth=True,
        )
        self.gl_view.addItem(self._plane)

    def load_fallback(self):
        self._plane = gl.GLBoxItem(color=(60, 200, 255, 220))
        self.gl_view.addItem(self._plane)

    def replace_model(self, verts: np.ndarray, faces: np.ndarray):
        if self._plane is not None:
            self.gl_view.removeItem(self._plane)
            self._plane = None
        self.load_model(verts, faces)

    def reset_origin(self):
        self._origin = None

    def apply_pose(self, roll, pitch, yaw, altitude, lat, lon, lock_camera=False):
        if self._plane is None:
            return
        if self._origin is None:
            self._origin = (lat, lon)

        dx = (lon - self._origin[1]) * self._SCALE
        dy = (lat - self._origin[0]) * self._SCALE
        dz = altitude / 10.0

        self._plane.resetTransform()
        # self._plane.rotate(-yaw,   0, 0, 1)
        self._plane.rotate(roll,   0, 1, 0)
        self._plane.rotate(-pitch, 1, 0, 0)
        self._plane.translate(dx, dy, dz)

        if lock_camera:
            self.gl_view.setCameraPosition(pos=pg.Vector(dx, dy, dz))

    def set_background(self, r, g, b):
        self.gl_view.setBackgroundColor(r, g, b)

    def set_grid_color(self, r, g, b, a):
        self.grid.setColor((r, g, b, a))

    def set_plane_color(self, color):
        if self._plane is None:
            return
        self._plane.opts['color'] = color
        self._plane.update()
