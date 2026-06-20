from dataclasses import dataclass


@dataclass
class TelemetryFrame:
    roll: float
    pitch: float
    yaw: float
    altitude: float
    lat: float
    lon: float
    timestamp_ms: int

    @classmethod
    def from_row(cls, row: list[str]) -> "TelemetryFrame":
        return cls(
            roll=float(row[0]),
            pitch=float(row[1]),
            yaw=float(row[2]),
            altitude=float(row[3]),
            lat=float(row[4]),
            lon=float(row[5]),
            timestamp_ms=int(float(row[6])),
        )

    def to_row(self) -> list:
        return [self.roll, self.pitch, self.yaw, self.altitude,
                self.lat, self.lon, self.timestamp_ms]
