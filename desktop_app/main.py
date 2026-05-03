import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QWidget, 
                             QLabel, QSlider, QFrame, QStatusBar)
from PyQt5.QtCore import QTimer, Qt
import serial
import serial.tools.list_ports
import numpy as np
import csv
import time
from stl import mesh
import pyqtgraph.opengl as gl

class Telemetry3D(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pico Drone GCS (Ground Control Station)")
        self.resize(1400, 900)

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
        
        self.apply_styles()
        self.init_ui()

    def apply_styles(self):
        """Aplică tema Dark Mode și stilul de tip Card / Material Design"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QFrame#Card {
                background-color: #1E1E2E;
                border-radius: 12px;
                border: 1px solid #2B2B40;
            }
            QLabel {
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QLabel#TeleTitle {
                color: #8A8D93;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                margin-bottom: -5px;
            }
            QLabel#TeleData {
                font-family: 'Consolas', monospace;
                font-size: 28px;
                color: #00E676;
                font-weight: bold;
                background-color: #151521;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #2B2B40;
            }
            QPushButton {
                background-color: #3D5AFE;
                color: white;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { background-color: #536DFE; }
            QPushButton:pressed { background-color: #304FFE; }
            QPushButton:disabled { background-color: #2B2B40; color: #5C5C70; }
            
            QComboBox {
                background-color: #151521;
                color: white;
                border: 1px solid #2B2B40;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                min-width: 120px;
            }
            QComboBox::drop-down { border: none; }
            
            QSlider::groove:horizontal {
                border: 1px solid #2B2B40;
                height: 8px;
                background: #151521;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3D5AFE;
                width: 18px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:disabled { background: #5C5C70; }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Bara de Status (Jos) ---
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #8A8D93; background-color: #121212; border-top: 1px solid #2B2B40;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistem inițializat. Așteptare conexiune...")

        # --- 1. Panou Control Superior (Card) ---
        top_frame = QFrame()
        top_frame.setObjectName("Card")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 15, 20, 15)
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.btn_connect = QPushButton("Conectare")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.btn_record = QPushButton("Start Inregistrare")
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_record.setEnabled(False)

        self.file_selector = QComboBox()
        self.file_selector.setMinimumWidth(200)
        self.refresh_recordings_list()
        
        self.btn_replay = QPushButton("Play Replay")
        self.btn_replay.clicked.connect(self.toggle_replay)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "2.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentIndexChanged.connect(self.update_speed)

        top_layout.addWidget(QLabel("PORT SERIAL:"))
        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(self.btn_connect)
        top_layout.addSpacing(30)
        
        # Linie despărțitoare verticală
        v_line = QFrame()
        v_line.setFrameShape(QFrame.VLine)
        v_line.setStyleSheet("color: #2B2B40;")
        top_layout.addWidget(v_line)
        top_layout.addSpacing(30)
        
        top_layout.addWidget(QLabel("REPLAY DATE:"))
        top_layout.addWidget(self.file_selector)
        top_layout.addWidget(self.btn_replay)
        top_layout.addWidget(QLabel("VITEZĂ:"))
        top_layout.addWidget(self.speed_combo)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_record) # Punem butonul de REC la capăt

        main_layout.addWidget(top_frame)

        # --- 2. Zona Centrală (Telemetrie + 3D) ---
        center_content = QHBoxLayout()
        center_content.setSpacing(15)

        # Panou Telemetrie (Card Stânga)
        tele_frame = QFrame()
        tele_frame.setObjectName("Card")
        tele_frame.setFixedWidth(280)
        self.tele_panel = QVBoxLayout(tele_frame)
        self.tele_panel.setContentsMargins(20, 25, 20, 25)
        self.tele_panel.setSpacing(15)
        
        header_lbl = QLabel("DATE TELEMETRIE")
        header_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px;")
        header_lbl.setAlignment(Qt.AlignCenter)
        self.tele_panel.addWidget(header_lbl)
        
        # Generare perechi (Titlu + Valoare)
        self.val_time = self.create_telemetry_gauge("TIMP ZBOR (s)", "0.00")
        self.val_roll = self.create_telemetry_gauge("ROLL (°)", "0.00")
        self.val_pitch = self.create_telemetry_gauge("PITCH (°)", "0.00")
        self.val_alt = self.create_telemetry_gauge("ALTITUDINE (m)", "0.00")

        self.tele_panel.addStretch()
        center_content.addWidget(tele_frame)

        # Viewport 3D (Card Dreapta)
        view_frame = QFrame()
        # view_frame.setObjectName("Card")
        view_layout = QVBoxLayout(view_frame)
        view_layout.setContentsMargins(2, 2, 2, 2)

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(18, 18, 18) # Deep dark pentru 3D
        self.view.setCameraPosition(distance=30, elevation=20, azimuth=45)
        view_layout.addWidget(self.view)
        
        center_content.addWidget(view_frame, stretch=1)
        main_layout.addLayout(center_content, stretch=1)

        # --- 3. Control Navigare (Slider Card) ---
        nav_frame = QFrame()
        nav_frame.setObjectName("Card")
        nav_bar = QHBoxLayout(nav_frame)
        nav_bar.setContentsMargins(20, 10, 20, 10)
        
        self.lbl_frames = QLabel("CADRU: 0 / 0")
        self.lbl_frames.setFixedWidth(150)
        self.lbl_frames.setStyleSheet("font-family: 'Consolas', monospace; color: #8A8D93;")
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.on_slider_move)
        
        nav_bar.addWidget(self.lbl_frames)
        nav_bar.addWidget(self.slider)
        main_layout.addWidget(nav_frame)

        # --- Setup Elemente 3D ---
        self.setup_3d_environment()
        self.load_stl_model()

        # Timer Principal
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)

    def create_telemetry_gauge(self, title_text, initial_value):
        """Creează un grup vizual pentru o valoare de telemetrie"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        title = QLabel(title_text)
        title.setObjectName("TeleTitle")
        
        value = QLabel(initial_value)
        value.setObjectName("TeleData")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(title)
        layout.addWidget(value)
        self.tele_panel.addWidget(container)
        return value

    def setup_3d_environment(self):
        """Adaugă grid și axe ajutătoare în scena 3D"""
        grid = gl.GLGridItem()
        grid.setSize(30, 30)
        grid.setSpacing(2, 2)
        grid.translate(0, 0, -2) 
        # Culoare subtilă pentru grid
        grid.setColor((255, 255, 255, 40)) 
        self.view.addItem(grid)

        # Adăugare axe de coordonate (X=Roșu, Y=Verde, Z=Albastru)
        axis = gl.GLAxisItem()
        axis.setSize(x=5, y=5, z=5)
        self.view.addItem(axis)

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
                color=(0.24, 0.35, 1.0, 0.9), # Culoare #3D5AFE translucid
                shader='shaded', smooth=True
            )
            self.view.addItem(self.plane)
        except Exception as e:
            self.status_bar.showMessage(f"Avertisment: Model STL lipsă. Se folosește un cub de test. Eroare: {e}", 10000)
            self.plane = gl.GLBoxItem(color=(255, 23, 68, 200)) # Roșu
            self.plane.translate(-0.5, -0.5, -0.5) # Centrare vizuală cub
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
                self.btn_connect.setStyleSheet("background-color: #FF1744;") # Buton roșu la deconectare
                self.btn_record.setEnabled(True)
                self.is_replaying = False
                self.slider.setEnabled(False)
                self.timer.start(self.base_interval)
                self.status_bar.showMessage(f"Conectat cu succes la {self.port_combo.currentText()}")
            except Exception as e: 
                self.status_bar.showMessage(f"Eroare Serial: {e}", 5000)
        else:
            self.timer.stop()
            if self.is_recording: self.toggle_recording()
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.setText("Conectare")
            self.btn_connect.setStyleSheet("") # Revine la stilul default din CSS
            self.btn_record.setEnabled(False)
            self.status_bar.showMessage("Deconectat.")

    def toggle_recording(self):
        if not self.is_recording:
            self.recorded_data = []
            self.is_recording = True
            self.btn_record.setText("Stop Inregistrare")
            self.btn_record.setStyleSheet("background-color: #FF1744; color: white;") # Roșu aprins
            self.status_bar.showMessage("Înregistrare telemetrie pornită...")
        else:
            self.is_recording = False
            self.btn_record.setText("Start Inregistrare")
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
        self.status_bar.showMessage(f"Fișier salvat: {fname}", 5000)

    def toggle_replay(self):
        if not self.is_replaying:
            filename = self.file_selector.currentText()
            if not filename: return
            
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
                self.btn_replay.setStyleSheet("background-color: #00E676; color: #121212;") # Verde pentru Replay activ
                self.update_speed()
                self.timer.start()
                self.status_bar.showMessage(f"Se redă: {filename}")
            except Exception as e: 
                self.status_bar.showMessage(f"Eroare citire Replay: {e}", 5000)
        else:
            self.is_replaying = False
            self.btn_replay.setText("Play Replay")
            self.btn_replay.setStyleSheet("")
            self.timer.stop()
            self.status_bar.showMessage("Replay oprit.")

    def update_speed(self):
        s_map = {"0.5x": 2.0, "1.0x": 1.0, "2.0x": 0.5, "4.0x": 0.25}
        mult = s_map[self.speed_combo.currentText()]
        if self.timer.isActive():
            self.timer.start(int(self.base_interval * mult))

    def on_slider_move(self):
        idx = self.slider.value()
        if 0 <= idx < len(self.recorded_data):
            roll, pitch, alt, ts = self.recorded_data[idx]
            self.lbl_frames.setText(f"CADRU: {idx} / {len(self.recorded_data)-1}")
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
                # Citim doar ultima linie completă pentru a nu decala UI-ul
                for i in range(len(lines)-2, -1, -1):
                    parts = lines[i].strip().split(',')
                    if len(parts) >= 4:
                        r, p, a, t = [float(x) for x in parts[:4]]
                        if self.is_recording: self.recorded_data.append((r, p, a, t))
                        self.update_ui_elements(r, p, a, t)
                        break
            except: pass

    def update_ui_elements(self, roll, pitch, alt, ts):
        # Update text labels (doar valorile, fără text extra)
        self.val_time.setText(f"{ts/1000:.2f}")
        self.val_roll.setText(f"{roll:>.2f}")
        self.val_pitch.setText(f"{pitch:>.2f}")
        self.val_alt.setText(f"{alt:>.2f}")
        
        # Update 3D Model
        self.plane.resetTransform()
        self.plane.rotate(-roll, 0, 1, 0) 
        self.plane.rotate(pitch, 1, 0, 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Setare font global pentru elementele fără stil explicit
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    
    window = Telemetry3D()
    window.show()
    sys.exit(app.exec_())