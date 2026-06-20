import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ..core.models import TelemetryFrame


class AnalyticsCharts(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._chart_alt = pg.PlotWidget(title="Istoric Altitudine (m)")
        self._chart_angles = pg.PlotWidget(title="Dinamica Unghiurilor (°)")
        self._chart_angles.addLegend()

        layout.addWidget(self._chart_alt)
        layout.addWidget(self._chart_angles)

    def populate(self, frames: list[TelemetryFrame]):
        if not frames:
            return
        data = np.array([[f.roll, f.pitch, f.yaw, f.altitude, f.timestamp_ms] for f in frames])
        ts = data[:, 4] / 1000.0

        self._chart_alt.clear()
        self._chart_alt.plot(ts, data[:, 3], pen=pg.mkPen("#00E676", width=2))

        self._chart_angles.clear()
        self._chart_angles.plot(ts, data[:, 0], pen=pg.mkPen("#FF1744", width=1.5), name="Roll")
        self._chart_angles.plot(ts, data[:, 1], pen=pg.mkPen("#29B6F6", width=1.5), name="Pitch")
        self._chart_angles.plot(ts, data[:, 2], pen=pg.mkPen("#FFEE58", width=1.5), name="Yaw")
