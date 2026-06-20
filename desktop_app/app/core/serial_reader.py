import serial
from PyQt5.QtCore import QThread, pyqtSignal
from .models import TelemetryFrame


class SerialReader(QThread):
    frame_received = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, port: str, baud: int = 115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = False

    def run(self):
        self._running = True
        try:
            conn = serial.Serial(self.port, self.baud, timeout=0.01)
            buffer = ""
            while self._running:
                if conn.in_waiting > 0:
                    raw = conn.read(conn.in_waiting).decode("utf-8", errors="ignore")
                    buffer += raw
                    lines = buffer.split("\n")
                    buffer = lines[-1]
                    for line in reversed(lines[:-1]):
                        parts = line.strip().split(",")
                        if len(parts) >= 7:
                            try:
                                self.frame_received.emit(TelemetryFrame.from_row(parts))
                                break
                            except ValueError:
                                continue
                else:
                    self.msleep(5)
            conn.close()
        except serial.SerialException as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._running = False
        self.wait(2000)
