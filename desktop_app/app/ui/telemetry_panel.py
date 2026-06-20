from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from ..core.models import TelemetryFrame

_ROLL_WARN,  _ROLL_CRIT  = 25.0, 45.0
_PITCH_WARN, _PITCH_CRIT = 20.0, 35.0
_ALT_WARN = 3.0


def _alert_level(value: float, warn: float, crit: float, negate=False) -> str:
    if negate:
        if value <= crit: return "crit"
        if value <= warn: return "warn"
    else:
        v = abs(value)
        if v >= crit: return "crit"
        if v >= warn: return "warn"
    return "normal"


class TelemetryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self._time  = self._gauge("Timp Zbor (s)",           "0.00",               layout)
        self._roll  = self._gauge("Roll (Aripă) (°)",        "0.00",               layout)
        self._pitch = self._gauge("Pitch (Nas) (°)",         "0.00",               layout)
        self._yaw   = self._gauge("Yaw (Busolă) (°)",        "0.00",               layout)
        self._alt   = self._gauge("Altitudine (m)",          "0.00",               layout)
        self._gps   = self._gauge("Poziție GPS (Lat, Lon)", "0.000000, 0.000000",  layout)
        layout.addStretch()

    @staticmethod
    def _gauge(title_text, initial, parent_layout) -> QLabel:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        title = QLabel(title_text)
        title.setObjectName("TeleTitle")
        value = QLabel(initial)
        value.setObjectName("TeleData")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vbox.addWidget(title)
        vbox.addWidget(value)
        parent_layout.addWidget(container)
        return value

    @staticmethod
    def _color(label: QLabel, level: str):
        name = {"normal": "TeleData", "warn": "TeleData_warn", "crit": "TeleData_crit"}[level]
        if label.objectName() != name:
            label.setObjectName(name)
            label.setStyle(label.style())

    def update(self, frame: TelemetryFrame):
        self._time.setText(f"{frame.timestamp_ms / 1000:.2f}")
        self._color(self._time, "normal")

        self._roll.setText(f"{frame.roll:.2f}")
        self._color(self._roll, _alert_level(frame.roll, _ROLL_WARN, _ROLL_CRIT))

        self._pitch.setText(f"{frame.pitch:.2f}")
        self._color(self._pitch, _alert_level(frame.pitch, _PITCH_WARN, _PITCH_CRIT))

        self._yaw.setText(f"{frame.yaw:.2f}")
        self._color(self._yaw, "normal")

        self._alt.setText(f"{frame.altitude:.2f}")
        self._color(self._alt, _alert_level(frame.altitude, _ALT_WARN, 0.0, negate=True))

        self._gps.setText(f"{frame.lat:.6f}, {frame.lon:.6f}")
        self._color(self._gps, "normal")
