import sys
import os

# Ensure CWD is always desktop_app/ so relative paths (telemetry_logs/, plane_models/) work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from app.gcs_window import GCSWindow


def main() -> None:
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = GCSWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
