import sys
import serial
import serial.tools.list_ports
import numpy as np
from stl import mesh
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QWidget, QLabel)
from PyQt5.QtCore import QTimer


class Telemetry3D(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pico Drone Telemetry")
        self.resize(1200, 800)

        self.serial_conn = None
        self.init_ui()

    def init_ui(self):
        # --- UI Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Panou Control
        controls = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        self.btn_connect = QPushButton("Conectare")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        controls.addWidget(QLabel("Port Receptor:"))
        controls.addWidget(self.port_combo)
        controls.addWidget(self.btn_connect)
        controls.addStretch()
        main_layout.addLayout(controls)

        # --- Viewport 3D ---
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(30, 30, 45)
        self.view.setCameraPosition(distance=20, elevation=25, azimuth=45)
        main_layout.addWidget(self.view)

        # Grid sol
        grid = gl.GLGridItem()
        grid.setSize(20, 20)
        grid.setSpacing(1, 1)
        grid.translate(0, 0, -1)
        self.view.addItem(grid)

        # --- Încărcare Model STL ---
        try:
            # Încarcă fișierul tău
            stl_mesh = mesh.Mesh.from_file('plane_models/wildcat-scaled-144.stl')
            
            # Extragere date pentru OpenGL
            # Scalăm cu 0.1 sau cât este necesar pentru vizibilitate
            verts = (stl_mesh.vectors.reshape(-1, 3) * 0.1) - np.array([0, 0, 0.5]) 
            faces = np.arange(len(verts)).reshape(-1, 3)

            # Avionul
            self.plane = gl.GLMeshItem(
                vertexes=verts, 
                faces=faces, 
                color=(0.2, 0.6, 1.0, 0.5), 
                shader='shaded',
                smooth=True,
            )

            self.view.addItem(self.plane)
            
        except Exception as e:
            print(f"Eroare la încărcarea STL: {e}")
            # Fallback la un cub dacă STL-ul lipsește
            self.plane = gl.GLBoxItem(color=(1,0,0,1))
            self.view.addItem(self.plane)

        # Timer pentru loop-ul de date (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo.clear()
        self.port_combo.addItems([p.device for p in ports])

    def toggle_connection(self):
        if self.serial_conn is None:
            try:
                port = self.port_combo.currentText()
                # Descentralizăm flow-ul serial pentru a nu bloca UI-ul
                self.serial_conn = serial.Serial(port, 115200, timeout=0.001)
                self.btn_connect.setText("Deconectare")
                self.timer.start(16) 
            except Exception as e:
                print(f"Eroare Conectare: {e}")
        else:
            self.timer.stop()
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.setText("Conectare")
            self.btn_connect.setStyleSheet("")

    def update_data(self):
        if self.serial_conn and self.serial_conn.in_waiting > 0:
            try:
                # --- STRATEGIA ANTI-LAG ---
                # Citim tot ce s-a acumulat în buffer
                raw_data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                lines = raw_data.split('\n')
                
                # Căutăm ultima linie completă din buffer (cea mai recentă)
                last_valid_line = None
                for i in range(len(lines)-1, -1, -1):
                    if len(lines[i].split(',')) >= 4:
                        last_valid_line = lines[i].strip()
                        break
                
                if last_valid_line:
                    # Format așteptat de la Pico: v_batt, roll, pitch, alt
                    parts = last_valid_line.split(',')
                    _, roll, pitch, _ = [float(x) for x in parts[:4]]
                    # print(f"Received Telemetry: Roll={roll:.2f}, Pitch={pitch:.2f}")

                    # pitch = np.clip(pitch, -90, 90)
                    # roll = np.clip(roll, -90, 90)
                    
                    # --- Update Avion ---
                    self.plane.resetTransform()
                    self.plane.rotate(roll, 0, 1, 0) # Rotație bot sus/jos (Axa Y)
                    self.plane.rotate(-pitch, 1, 0, 0) # Rotație aripi (Axa X) - am pus minus pentru direcție corectă

            except Exception as e:
                # Erorile de conversie sunt ignorate (pachete corupte)
                print(f"Eroare la procesarea datelor: {e}")
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Telemetry3D()
    window.show()
    sys.exit(app.exec_())