import sys
import os

# --- MOVE THESE TO THE VERY TOP ---
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QWidget, QLabel, QSlider)
from PyQt5.QtCore import QTimer, Qt
# ----------------------------------

import serial
import serial.tools.list_ports
import numpy as np
import csv
import time
from stl import mesh
import pyqtgraph.opengl as gl  # Now import this AFTER PyQt5

class Telemetry3D(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pico Drone Telemetry Viewer")
        self.resize(1300, 900)

        # Configurare stocare
        self.log_folder = "telemetry_logs"
        if not os.path.exists(self.log_folder): 
            os.makedirs(self.log_folder)

        # Stări sistem
        self.serial_conn = None
        self.recorded_data = []
        self.is_recording = False
        self.is_replaying = False
        self.base_interval = 16  # ~60 FPS
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 1. Panou Control Superior ---
        top_controls = QHBoxLayout()
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.btn_connect = QPushButton("Conectare")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.btn_record = QPushButton("Start Rec")
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_record.setEnabled(False)

        self.file_selector = QComboBox()
        self.refresh_recordings_list()
        
        self.btn_replay = QPushButton("Play Replay")
        self.btn_replay.clicked.connect(self.toggle_replay)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "2.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentIndexChanged.connect(self.update_speed)

        top_controls.addWidget(QLabel("Port:"))
        top_controls.addWidget(self.port_combo)
        top_controls.addWidget(self.btn_connect)
        top_controls.addSpacing(20)
        top_controls.addWidget(self.btn_record)
        top_controls.addSpacing(20)
        top_controls.addWidget(QLabel("Istoric:"))
        top_controls.addWidget(self.file_selector)
        top_controls.addWidget(self.btn_replay)
        top_controls.addWidget(QLabel("Viteză:"))
        top_controls.addWidget(self.speed_combo)
        top_controls.addStretch()
        main_layout.addLayout(top_controls)

        # --- 2. Zona Centrală (Telemetrie + 3D) ---
        center_content = QHBoxLayout()

        # Panou Telemetrie (Stânga)
        self.tele_panel = QVBoxLayout()
        self.tele_panel.setContentsMargins(10, 10, 10, 10)
        
        lbl_style = "font-family: 'Consolas'; font-size: 18px; font-weight: bold; color: #00ff00; background-color: #1e1e2d; padding: 10px; border: 1px solid #333; border-radius: 5px;"
        
        self.val_time = QLabel("TIME: 0.00 s")
        self.val_roll = QLabel("ROLL: 0.00°")
        self.val_pitch = QLabel("PITCH: 0.00°")
        self.val_alt = QLabel("ALT: 0.00 m")

        for lbl in [self.val_time, self.val_roll, self.val_pitch, self.val_alt]:
            lbl.setStyleSheet(lbl_style)
            lbl.setFixedWidth(220)
            self.tele_panel.addWidget(lbl)
        
        self.tele_panel.addStretch()
        center_content.addLayout(self.tele_panel)

        # Viewport 3D (Dreapta)
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(30, 30, 45)
        self.view.setCameraPosition(distance=25, elevation=25, azimuth=45)
        center_content.addWidget(self.view, stretch=4)
        
        main_layout.addLayout(center_content)

        # --- 3. Control Navigare (Slider) ---
        nav_bar = QHBoxLayout()
        self.lbl_frames = QLabel("Cadrul: 0/0")
        self.lbl_frames.setStyleSheet("color: white; font-weight: bold;")
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.on_slider_move)
        
        nav_bar.addWidget(self.lbl_frames)
        nav_bar.addWidget(self.slider)
        main_layout.addLayout(nav_bar)

        # --- Setup Elemente 3D ---
        grid = gl.GLGridItem()
        grid.setSize(20, 20)
        grid.setSpacing(1, 1)
        grid.translate(0, 0, -2) # Plasăm grid-ul sub avion
        self.view.addItem(grid)

        self.load_stl_model()

        # Timer Principal
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)

    def load_stl_model(self):
        try:
            stl_mesh = mesh.Mesh.from_file('plane_models/wildcat-scaled-144.stl')
            verts = stl_mesh.vectors.reshape(-1, 3) * 0.1
            
            # Centrarea modelului
            center = (verts.min(axis=0) + verts.max(axis=0)) / 2.0
            verts = verts - center
            
            self.plane = gl.GLMeshItem(
                vertexes=verts, 
                faces=np.arange(len(verts)).reshape(-1, 3), 
                color=(0.2, 0.6, 1.0, 0.8), 
                shader='shaded', smooth=True
            )
            self.view.addItem(self.plane)
        except Exception as e:
            print(f"Eroare STL: {e}")
            self.plane = gl.GLBoxItem(color=(1,0,0,1))
            self.view.addItem(self.plane)

    # --- Logica de Operare ---

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        self.port_combo.addItems([p.device for p in ports])

    def refresh_recordings_list(self):
        self.file_selector.clear()
        files = [f for f in os.listdir(self.log_folder) if f.endswith('.csv')]
        self.file_selector.addItems(sorted(files, reverse=True))

    def toggle_connection(self):
        if self.serial_conn is None:
            try:
                self.serial_conn = serial.Serial(self.port_combo.currentText(), 115200, timeout=0.001)
                self.btn_connect.setText("Deconectare")
                self.btn_record.setEnabled(True)
                self.is_replaying = False
                self.slider.setEnabled(False)
                self.timer.start(self.base_interval)
            except Exception as e: print(f"Eroare Serial: {e}")
        else:
            self.timer.stop()
            if self.is_recording: self.toggle_recording()
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.setText("Conectare")
            self.btn_record.setEnabled(False)

    def toggle_recording(self):
        if not self.is_recording:
            self.recorded_data = []
            self.is_recording = True
            self.btn_record.setText("Stop Rec")
            self.btn_record.setStyleSheet("background-color: #ff4c4c; color: white;")
        else:
            self.is_recording = False
            self.btn_record.setText("Start Rec")
            self.btn_record.setStyleSheet("")
            self.save_data_to_file()

    def save_data_to_file(self):
        if not self.recorded_data: return
        fname = f"log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.log_folder, fname)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['roll', 'pitch', 'alt', 'ts'])
            writer.writerows(self.recorded_data)
        self.refresh_recordings_list()

    def toggle_replay(self):
        if not self.is_replaying:
            filename = self.file_selector.currentText()
            if not filename: return
            
            # Load CSV
            self.recorded_data = []
            try:
                with open(os.path.join(self.log_folder, filename), 'r') as f:
                    reader = csv.reader(f); next(reader)
                    for row in reader: self.recorded_data.append([float(x) for x in row])
                
                if self.serial_conn: self.toggle_connection()
                
                self.is_replaying = True
                self.slider.setEnabled(True)
                self.slider.setMaximum(len(self.recorded_data) - 1)
                self.slider.setValue(0)
                self.btn_replay.setText("Stop Replay")
                self.update_speed()
                self.timer.start()
            except Exception as e: print(f"Eroare Replay: {e}")
        else:
            self.is_replaying = False
            self.btn_replay.setText("Play Replay")
            self.timer.stop()

    def update_speed(self):
        s_map = {"0.5x": 2.0, "1.0x": 1.0, "2.0x": 0.5, "4.0x": 0.25}
        mult = s_map[self.speed_combo.currentText()]
        if self.timer.isActive():
            self.timer.start(int(self.base_interval * mult))

    def on_slider_move(self):
        idx = self.slider.value()
        if 0 <= idx < len(self.recorded_data):
            roll, pitch, alt, ts = self.recorded_data[idx]
            self.lbl_frames.setText(f"Cadrul: {idx}/{len(self.recorded_data)-1}")
            self.update_ui_elements(roll, pitch, alt, ts)

    def main_loop(self):
        if self.is_replaying:
            c_idx = self.slider.value()
            if c_idx < self.slider.maximum():
                self.slider.setValue(c_idx + 1)
            else:
                self.toggle_replay()
        else:
            self.read_serial()

    def read_serial(self):
        if self.serial_conn and self.serial_conn.in_waiting > 0:
            try:
                raw = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                lines = raw.split('\n')
                for i in range(len(lines)-2, -1, -1):
                    parts = lines[i].strip().split(',')
                    if len(parts) >= 4:
                        r, p, a, t = [float(x) for x in parts[:4]]
                        if self.is_recording: self.recorded_data.append((r, p, a, t))
                        self.update_ui_elements(r, p, a, t)
                        break
            except: pass

    def update_ui_elements(self, roll, pitch, alt, ts):
        # Update text
        self.val_time.setText(f"TIME: {ts/1000:.2f} s")
        self.val_roll.setText(f"ROLL: {roll:>.2f}°")
        self.val_pitch.setText(f"PITCH: {pitch:>.2f}°")
        self.val_alt.setText(f"ALT: {alt:>.2f} m")
        
        # Update 3D
        self.plane.resetTransform()
        self.plane.rotate(roll, 0, 1, 0) 
        self.plane.rotate(-pitch, 1, 0, 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Telemetry3D()
    window.show()
    sys.exit(app.exec_())