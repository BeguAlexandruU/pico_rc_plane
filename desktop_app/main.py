import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QWidget, QLabel)
from PyQt5.QtCore import QTimer
import pyqtgraph.opengl as gl
import numpy as np

# import time
# import math

class Telemetry3D(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pico Drone Telemetry - 3D View")
        self.resize(1024, 768)

        self.serial_conn = None
        self.init_ui()

    def init_ui(self):
        # Layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Control Panel (Port selection)
        controls = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        self.btn_connect = QPushButton("Conectare")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        controls.addWidget(QLabel("Port:"))
        controls.addWidget(self.port_combo)
        controls.addWidget(self.btn_connect)
        main_layout.addLayout(controls)

        # 3D Viewport
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=15)
        main_layout.addWidget(self.view)

        # Adăugăm un grid și axele
        grid = gl.GLGridItem()
        self.view.addItem(grid)
        
        # Creăm "Avionul" (un box simplu pentru început, îl poți înlocui cu un mesh STL)
        # Dimensiuni: Lungime 4, lățime 2, grosime 0.5
        verts = np.array([
            [2, 1, 0.25], [-2, 1, 0.25], [-2, -1, 0.25], [2, -1, 0.25],
            [2, 1, -0.25], [-2, 1, -0.25], [-2, -1, -0.25], [2, -1, -0.25]
        ])
        faces = np.array([
            [0,1,2], [0,2,3], [0,1,5], [0,5,4], [1,2,6], [1,6,5],
            [2,3,7], [2,7,6], [3,0,4], [3,4,7], [4,5,6], [4,6,7]
        ])
        colors = np.array([[0.8, 0.2, 0.2, 1.0]] * 12) # Roșu

        self.plane = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=True)
        self.view.addItem(self.plane)

        # Timer pentru citirea datelor (60 FPS refresh)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo.addItems([p.device for p in ports])

    def toggle_connection(self):
        if self.serial_conn is None:
            try:
                port = self.port_combo.currentText()
                self.serial_conn = serial.Serial(port, 115200, timeout=0.01)
                self.btn_connect.setText("Deconectare")
                self.timer.start(16) # ~60 Hz
            except Exception as e:
                print(f"Eroare: {e}")
        else:
            self.timer.stop()
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.setText("Conectare")

    def update_data(self):
        if self.serial_conn and self.serial_conn.in_waiting > 0:
            try:
                line = self.serial_conn.readline().decode('utf-8').strip()
                data = line.split(',')
                if len(data) >= 3:
                    # Presupunem formatul: v_batt, pitch, roll, alt
                    _, roll, pitch, _ = map(float, data[:4])
                    
                    pitch = np.clip(pitch, -90, 90)
                    roll = np.clip(roll, -90, 90)
                    roll = -roll

                    # print(f"Pitch: {pitch:.2f}, Roll: {roll:.2f}", end="\r")

                    # Resetăm rotația și aplicăm noile valori
                    self.plane.resetTransform()
                    self.plane.rotate(pitch, 0, 1, 0) # Rotație pe axa Y
                    self.plane.rotate(roll, 1, 0, 0)  # Rotație pe axa X
            except:
                pass
        # else:
        #     # --- MOD DEMO (Simulare) ---
        #     t = time.time()
        #     pitch = math.sin(t * 2) * 20
        #     roll = math.cos(t * 2) * 20
            
        #     self.plane.resetTransform()
        #     self.plane.rotate(pitch, 0, 1, 0)
        #     self.plane.rotate(roll, 1, 0, 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = Telemetry3D()
    gui.show()
    sys.exit(app.exec_())

