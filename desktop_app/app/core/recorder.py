import csv
import os
import time
from .models import TelemetryFrame

_CSV_HEADER = ["roll", "pitch", "yaw", "alt", "gps_lat", "gps_lon", "timestamp"]


class Recorder:
    def __init__(self, log_folder: str):
        self.log_folder = log_folder
        os.makedirs(log_folder, exist_ok=True)
        self._frames: list[TelemetryFrame] = []
        self.active = False

    def start(self):
        self._frames.clear()
        self.active = True

    def stop(self) -> str | None:
        self.active = False
        if not self._frames:
            return None
        filename = f"log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.log_folder, filename)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(_CSV_HEADER)
            writer.writerows(frame.to_row() for frame in self._frames)
        return filename

    def append(self, frame: TelemetryFrame):
        if self.active:
            self._frames.append(frame)

    def list_logs(self) -> list[str]:
        files = [f for f in os.listdir(self.log_folder) if f.endswith(".csv")]
        return sorted(files, reverse=True)

    def load_log(self, filename: str) -> list[TelemetryFrame]:
        frames = []
        with open(os.path.join(self.log_folder, filename), "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 7:
                    try:
                        frames.append(TelemetryFrame.from_row(row))
                    except ValueError:
                        continue
        return frames

    def rename_log(self, old_name: str, new_name: str) -> str:
        if not new_name.endswith(".csv"):
            new_name += ".csv"
        os.rename(
            os.path.join(self.log_folder, old_name),
            os.path.join(self.log_folder, new_name),
        )
        return new_name
