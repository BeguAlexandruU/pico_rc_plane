import sys
import os
import csv
import time
import numpy as np
import folium
import io
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QWidget, 
                             QLabel, QSlider, QFrame, QStatusBar, QInputDialog,
                             QTabWidget, QSplitter, QStackedWidget)
from PyQt5.QtCore import QTimer, Qt
import serial
import serial.tools.list_ports
from stl import mesh
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PyQt5.QtWebEngineWidgets import QWebEngineView

class TelemetryGCS(QMainWindow):
    # --- Stiluri Vizuale Profesionale (Dark Mode vs Light Mode) ---
    DARK_STYLE = """
        QMainWindow { background-color: #121212; }
        QFrame#Card { background-color: #1E1E2E; border-radius: 12px; border: 1px solid #2B2B40; }
        QFrame#VLine { color: #2B2B40; }
        QLabel { color: #E0E0E0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QLabel#TeleTitle { color: #8A8D93; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        QLabel#TeleData { font-family: 'Consolas', monospace; font-size: 22px; color: #00E676; font-weight: bold; background-color: #151521; border-radius: 6px; padding: 6px; border: 1px solid #2B2B40; }
        QPushButton { background-color: #3D5AFE; color: white; border-radius: 6px; padding: 8px 14px; font-weight: bold; font-size: 13px; border: none; }
        QPushButton:hover { background-color: #536DFE; }
        QPushButton#ActiveBtn { background-color: #FF1744; color: white; }
        QPushButton#ActiveBtn:hover { background-color: #FF4569; }
        QComboBox { background-color: #151521; color: white; border: 1px solid #2B2B40; border-radius: 6px; padding: 6px; font-size: 13px; }
        QSlider::groove:horizontal { border: 1px solid #2B2B40; height: 8px; background: #151521; border-radius: 4px; }
        QSlider::handle:horizontal { background: #3D5AFE; width: 16px; margin-top: -4px; margin-bottom: -4px; border-radius: 8px; }
        QTabBar::tab { background: #1E1E2E; color: #8A8D93; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #3D5AFE; color: white; }
    """

    LIGHT_STYLE = """
        QMainWindow { background-color: #F5F5F7; }
        QFrame#Card { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #D2D2D7; }
        QFrame#VLine { color: #D2D2D7; }
        QLabel { color: #1D1D1F; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QLabel#TeleTitle { color: #6E6E73; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        QLabel#TeleData { font-family: 'Consolas', monospace; font-size: 22px; color: #1D1D1F; font-weight: bold; background-color: #E8E8ED; border-radius: 6px; padding: 6px; border: 1px solid #D2D2D7; }
        QPushButton { background-color: #0071E3; color: white; border-radius: 6px; padding: 8px 14px; font-weight: bold; font-size: 13px; border: none; }
        QPushButton:hover { background-color: #147CE5; }
        QPushButton#ActiveBtn { background-color: #FF3B30; color: white; }
        QPushButton#ActiveBtn:hover { background-color: #FF6961; }
        QComboBox { background-color: #FFFFFF; color: #1D1D1F; border: 1px solid #D2D2D7; border-radius: 6px; padding: 6px; font-size: 13px; }
        QSlider::groove:horizontal { border: 1px solid #D2D2D7; height: 8px; background: #E8E8ED; border-radius: 4px; }
        QSlider::handle:horizontal { background: #0071E3; width: 16px; margin-top: -4px; margin-bottom: -4px; border-radius: 8px; }
        QTabBar::tab { background: #E8E8ED; color: #6E6E73; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #0071E3; color: white; }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Ground Control Station & Flight Reconstructor")
        self.resize(1500, 950)

        self.log_folder = "telemetry_logs"
        if not os.path.exists(self.log_folder): 
            os.makedirs(self.log_folder)

        # Stări Interne
        self.serial_conn = None
        self.recorded_data = []  # Va stoca: [roll, pitch, yaw, alt, lat, lon, timestamp]
        self.flight_path_x = []
        self.flight_path_y = []
        
        self.is_recording = False
        self.is_replaying = False
        self.is_paused = False
        self.is_dark_mode = True
        self.base_interval = 16  # ~60 FPS țintă
        
        self.init_ui()
        self.apply_theme()
        
        # Focus tastatură dedicat pentru controlul prin taste
        self.setFocusPolicy(Qt.StrongFocus)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # =========================================================================
        # 1. BARA SUPERIOARĂ DE CONTROL (Conexiuni, Fișiere, Moduri)
        # =========================================================================
        top_frame = QFrame()
        top_frame.setObjectName("Card")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 10, 15, 10)
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.btn_connect = QPushButton("Conectare")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.btn_theme = QPushButton("☀️ Mod Luminos")
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        self.btn_record = QPushButton("Start Înregistrare")
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_record.setEnabled(False)

        self.file_selector = QComboBox()
        self.file_selector.setMinimumWidth(180)
        self.refresh_recordings_list()
        self.file_selector.currentIndexChanged.connect(self.on_replay_file_selected)
        
        self.btn_replay = QPushButton("Încarcă Replay")
        self.btn_replay.clicked.connect(self.toggle_replay)
        
        self.btn_rename = QPushButton("Redenumește Replay")
        self.btn_rename.clicked.connect(self.rename_current_replay)
        self.btn_rename.setEnabled(False)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1.0x", "2.0x", "4.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentIndexChanged.connect(self.update_speed)

        # Adăugare elemente în layout-ul superior
        top_layout.addWidget(QLabel("PORT:"))
        top_layout.addWidget(self.port_combo)
        top_layout.addWidget(self.btn_connect)
        top_layout.addWidget(self.btn_theme)
        
        v_line = QFrame(); v_line.setObjectName("VLine"); v_line.setFrameShape(QFrame.VLine)
        top_layout.addWidget(v_line)
        
        top_layout.addWidget(QLabel("LOGURI:"))
        top_layout.addWidget(self.file_selector)
        top_layout.addWidget(self.btn_replay)
        top_layout.addWidget(self.btn_rename)
        top_layout.addWidget(QLabel("VITEZĂ:"))
        top_layout.addWidget(self.speed_combo)
        
        top_layout.addStretch()
        top_layout.addWidget(self.btn_record)
        main_layout.addWidget(top_frame)

        # =========================================================================
        # 2. ZONA CENTRALĂ (Arhitectură pe Panouri Split)
        # =========================================================================
        horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # -------------------------------------------------------------------------
        # STÂNGA: Panou Monitorizare Date Active & Grafice Analitice (Tabs)
        # -------------------------------------------------------------------------
        left_tabs = QTabWidget()
        left_tabs.setFixedWidth(320)
        
        # Tab 1: Telemetrie Numerică (Design Prietenos)
        tele_frame = QFrame()
        tele_frame.setObjectName("Card")
        self.tele_panel = QVBoxLayout(tele_frame)
        self.tele_panel.setContentsMargins(15, 15, 15, 15)
        self.tele_panel.setSpacing(10)
        
        self.val_time = self.create_telemetry_gauge("Timp Zbor (s)", "0.00")
        self.val_roll = self.create_telemetry_gauge("Roll (Aripă) (°)", "0.00")
        self.val_pitch = self.create_telemetry_gauge("Pitch (Nas) (°)", "0.00")
        self.val_yaw = self.create_telemetry_gauge("Yaw (Busolă) (°)", "0.00")
        self.val_alt = self.create_telemetry_gauge("Altitudine (m)", "0.00")
        self.val_gps = self.create_telemetry_gauge("Poziție GPS (Lat, Lon)", "0.000000, 0.000000")
        self.tele_panel.addStretch()
        left_tabs.addTab(tele_frame, "Telemetrie")
        
        # Tab 2: Grafice Replay Analitice (Solicitat la selecția unui replay)
        charts_frame = QFrame()
        charts_layout = QVBoxLayout(charts_frame)
        self.chart_alt = pg.PlotWidget(title="Istoric Altitudine (m)")
        self.chart_angles = pg.PlotWidget(title="Dinamica Unghiurilor (°)")
        self.chart_angles.addLegend()
        charts_layout.addWidget(self.chart_alt)
        charts_layout.addWidget(self.chart_angles)
        left_tabs.addTab(charts_frame, "Analiză Chart-uri")
        
        horizontal_splitter.addWidget(left_tabs)

        # -------------------------------------------------------------------------
        # DREAPTA/CENTRU: Plan Principal de Redesenare (Hartă vs Mod Full 3D)
        # -------------------------------------------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Selector Layout-uri și Vizualizare
        view_control_bar = QHBoxLayout()
        self.map_style_combo = QComboBox()
        self.map_style_combo.addItems(["Default Layout", "Satelit Layout", "Terrain Layout"])
        self.map_style_combo.currentIndexChanged.connect(self.change_map_style)
        
        self.btn_view_mode = QPushButton("Comută în Mod Full 3D")
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        
        self.camera_mode_combo = QComboBox()
        self.camera_mode_combo.addItems(["Free Camera", "Lock pe Avion"])
        self.camera_mode_combo.setEnabled(False)  # Activ doar în mod Full 3D
        
        view_control_bar.addWidget(QLabel("Stil Hartă:"))
        view_control_bar.addWidget(self.map_style_combo)
        view_control_bar.addStretch()
        view_control_bar.addWidget(self.camera_mode_combo)
        view_control_bar.addWidget(self.btn_view_mode)
        right_layout.addLayout(view_control_bar)

        # Stacked Widget pentru Planul Principal de Lucru
        self.main_view_stack = QStackedWidget()
        
        # Plan Principal Mod A: Hartă 2D Verticală (cu Proiecție Traseu)
        
        # self.map_widget = pg.PlotWidget()
        # self.map_widget.setLabel('left', 'Latitudine (GPS)')
        # self.map_widget.setLabel('bottom', 'Longitudine (GPS)')
        # self.map_plot_path = self.map_widget.plot(pen=pg.mkPen('#00E676', width=3), name="Traseu parcurs")
        # self.map_current_pos = self.map_widget.plot(pen=None, symbol='o', symbolBrush='r', symbolSize=12)
        # self.main_view_stack.addWidget(self.map_widget)

        # 1. Inițializăm QWebEngineView pentru hartă
        self.map_widget = QWebEngineView()
        
        # 2. Creăm harta de bază folosind Folium
        # Coordonatele inițiale (Ieșire din raportul tău)
        start_coords = [47.150476, 27.636506]
        self.folium_map = folium.Map(location=start_coords, zoom_start=16, tiles=None, zoom_control=False)
        
        # 3. Adăugăm straturile (Tile-urile) de la Google Maps și OpenStreetMap în Folium
        folium.TileLayer(
            tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            name='Default Layout',
            attr='OpenStreetMap'
        ).add_to(self.folium_map)
        
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            name='Satelit Layout',
            attr='Google Satelit'
        ).add_to(self.folium_map)
        
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            name='Terrain Layout',
            attr='Google Terrain'
        ).add_to(self.folium_map)

        # 4. Injectăm scriptul JS ultra-optimizat pentru randare rapidă fără lag
        custom_js = """
        <script>
        var mapInstance = null;
        var flightPath = null;
        var droneMarker = null;
        var layersMap = {};

        window.onload = function() {
            // Identificăm automat obiectul hărții creat de Folium în fereastra globală
            for (var key in window) {
                if (key.indexOf('map_') === 0 && window[key] instanceof L.Map) {
                    mapInstance = window[key];
                    break;
                }
            }
            
            if (mapInstance) {
                // Salvăm referințele straturilor pentru a le schimba din Python rapid
                mapInstance.eachLayer(function(layer) {
                    if (layer instanceof L.TileLayer && layer.options.name) {
                        layersMap[layer.options.name] = layer;
                    }
                });

                // Creăm traseul și markerul dronei
                flightPath = L.polyline([], {color: '#00E676', weight: 4, smoothFactor: 1.5}).addTo(mapInstance);
                droneMarker = L.circleMarker([0, 0], {color: '#FF1744', fillColor: '#FF1744', fillOpacity: 1, radius: 6});
            }
        };

        function updateDronePosition(lat, lon) {
            if (!mapInstance || !flightPath) return;
            var newLatLng = new L.LatLng(lat, lon);
            
            // Adaugă punctul pe linie
            flightPath.addLatLng(newLatLng);
            
            // Pune markerul pe hartă dacă nu există deja
            if (!mapInstance.hasLayer(droneMarker)) { 
                droneMarker.addTo(mapInstance); 
            }
            droneMarker.setLatLng(newLatLng);
            
            # FOARTE IMPORTANT: setView cu animate:false oprește tranzițiile web asincrone care blocau aplicația ta
            mapInstance.setView(newLatLng, mapInstance.getZoom(), {animate: false}); 
        }

        function setMapStyle(styleName) {
            if (!mapInstance) return;
            // Scoatem toate straturile curente de tip Tile
            for (var name in layersMap) {
                mapInstance.removeLayer(layersMap[name]);
            }
            # Adăugăm doar stratul selectat
            if (layersMap[styleName]) {
                mapInstance.addLayer(layersMap[styleName]);
            }
        }
        </script>
        """
        # Atașăm scriptul de optimizare la structura hărții Folium
        self.folium_map.get_root().html.add_child(folium.Element(custom_js))
        
        # 5. Încărcăm harta generată de Folium în widget-ul PyQt5
        html_content = self.folium_map.get_root().render()
        self.map_widget.setHtml(html_content)
        
        # Adaugă widget-ul în layout-ul tău principal
        self.main_view_stack.addWidget(self.map_widget)
        
        # Inițializăm contorul de cadre pentru reducerea frecvenței
        self.map_update_counter = 0

        # HTML și JavaScript pentru generarea hărții și a straturilor tip Google Maps
        html_map = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>body, html, #map { height: 100%; margin: 0; padding: 0; background-color: #121212; }</style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Inițializare hartă pe coordonatele de test
                var map = L.map('map', {zoomControl: false}).setView([47.150476, 27.636506], 16); 
                
                // Definire Layout-uri (Tiles)
                var defaultLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png');
                
                // Straturi Google Maps neoficiale (folosite adesea pentru telemetrie)
                var satelliteLayer = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
                    maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']
                });
                
                var terrainLayer = L.tileLayer('http://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}', {
                    maxZoom: 20, subdomains:['mt0','mt1','mt2','mt3']
                });

                var currentLayer = defaultLayer;
                currentLayer.addTo(map);

                // Funcție apelată din Python pentru a schimba stilul hărții
                function setMapStyle(style) {
                    map.removeLayer(currentLayer);
                    if (style === 'Satelit Layout') {
                        currentLayer = satelliteLayer;
                    } else if (style === 'Terrain Layout') {
                        currentLayer = terrainLayer;
                    } else {
                        currentLayer = defaultLayer;
                    }
                    currentLayer.addTo(map);
                }

                // Variabile pentru traseu și poziția curentă
                var flightPath = L.polyline([], {color: '#00E676', weight: 4}).addTo(map);
                var droneMarker = L.circleMarker([0, 0], {color: 'red', fillColor: '#f03', fillOpacity: 1, radius: 6});

                // Funcție apelată din Python la fiecare cadru pentru a muta drona
                function updateDronePosition(lat, lon) {
                    var newLatLng = new L.LatLng(lat, lon);
                    flightPath.addLatLng(newLatLng);
                    
                    if (!map.hasLayer(droneMarker)) { droneMarker.addTo(map); }
                    droneMarker.setLatLng(newLatLng);
                    map.panTo(newLatLng); // Centrează camera pe dronă
                }
            </script>
        </body>
        </html>
        """
        self.map_widget.setHtml(html_map)
        self.main_view_stack.addWidget(self.map_widget)

        
        # Plan Principal Mod B: Vizualizare Full 3D Mediul înconjurător
        self.full_3d_view = gl.GLViewWidget()
        self.full_3d_view.setCameraPosition(distance=40, elevation=25, azimuth=45)
        self.main_view_stack.addWidget(self.full_3d_view)
        
        right_layout.addWidget(self.main_view_stack)
        horizontal_splitter.addWidget(right_container)
        
        # Plan Secundar: Mini-proiecție 3D a modelului local de avion (amplasat în colț / split)
        self.secondary_3d_box = QFrame()
        self.secondary_3d_box.setObjectName("Card")
        sec_3d_layout = QVBoxLayout(self.secondary_3d_box)
        sec_3d_layout.setContentsMargins(2, 2, 2, 2)
        sec_3d_layout.addWidget(QLabel("<b>Plan Secundar: Atitudine Locală</b>"), alignment=Qt.AlignCenter)
        self.local_3d_view = gl.GLViewWidget()
        self.local_3d_view.setCameraPosition(distance=15, elevation=15, azimuth=30)
        sec_3d_layout.addWidget(self.local_3d_view)
        
        horizontal_splitter.addWidget(self.secondary_3d_box)
        main_layout.addWidget(horizontal_splitter)

        # =========================================================================
        # 3. TIMELINE SLIDER & NAVIGARE REPLAY (Control Timp și Cadre)
        # =========================================================================
        nav_frame = QFrame()
        nav_frame.setObjectName("Card")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 8, 15, 8)
        
        self.btn_play_pause = QPushButton("⏸ Pauză")
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_play_pause.setEnabled(False)
        
        self.lbl_frames = QLabel("TIMP: 0.0s | CADRU: 0 / 0")
        self.lbl_frames.setFixedWidth(220)
        self.lbl_frames.setStyleSheet("font-family: 'Consolas', monospace;")
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.on_slider_move)
        
        nav_layout.addWidget(self.btn_play_pause)
        nav_layout.addWidget(self.lbl_frames)
        nav_layout.addWidget(self.slider)
        main_layout.addWidget(nav_frame)

        # Status Bar pentru diagnoză
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistem pregătit.")

        # Inițializări Componente Grafice 3D
        self.setup_3d_environments()
        self.load_airplane_models()

        # Timer-ul nucleu al aplicației
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)

    # --- Generatoare Elemente UI Interfețe ---
    def create_telemetry_gauge(self, title_text, initial_value):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        title = QLabel(title_text); title.setObjectName("TeleTitle")
        value = QLabel(initial_value); value.setObjectName("TeleData")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(title)
        layout.addWidget(value)
        self.tele_panel.addWidget(container)
        return value

    def setup_3d_environments(self):
        # Grid mediu secundar local
        grid_local = gl.GLGridItem()
        grid_local.setSize(20, 20); grid_local.setSpacing(2, 2)
        grid_local.translate(0, 0, -2)
        self.local_3d_view.addItem(grid_local)
        self.local_3d_view.addItem(gl.GLAxisItem())

        # Grid mediu principal Full 3D
        self.grid_main = gl.GLGridItem()
        self.grid_main.setSize(100, 100); self.grid_main.setSpacing(5, 5)
        self.grid_main.translate(0, 0, -5)
        self.full_3d_view.addItem(self.grid_main)
        self.full_3d_view.addItem(gl.GLAxisItem())

    def load_airplane_models(self):
        """Încarcă obiectul mesh 3D în ambele vederi (principală și secundară)"""
        try:
            stl_mesh = mesh.Mesh.from_file('plane_models/wildcat-scaled-144.stl')
            verts = stl_mesh.vectors.reshape(-1, 3) * 0.08
            center = (verts.min(axis=0) + verts.max(axis=0)) / 2.0
            verts = verts - center
            
            # --- ROTIRE 180 GRADE (Întoarcem nasul avionului) ---
            # Înmulțim coordonatele X și Y cu -1 pentru a roti modelul pe plan orizontal
            verts[:, 0] = -verts[:, 0]  # Inversare axa X
            verts[:, 1] = -verts[:, 1]  # Inversare axa Y
            # ----------------------------------------------------

            faces = np.arange(len(verts)).reshape(-1, 3)

            # Model pentru panoul secundar (Atitudine Locală)
            self.plane_local = gl.GLMeshItem(vertexes=verts, faces=faces, color=(0.1, 0.5, 0.9, 0.9), shader='shaded', smooth=True)
            self.local_3d_view.addItem(self.plane_local)

            # Model pentru vizualizarea Full 3D Principală
            self.plane_main = gl.GLMeshItem(vertexes=verts, faces=faces, color=(0.9, 0.2, 0.2, 0.9), shader='shaded', smooth=True)
            self.full_3d_view.addItem(self.plane_main)
            
        except Exception as e:
            self.status_bar.showMessage(f"Model STL lipsă. Se folosesc cuburi virtuale de test. Eroare: {e}", 8000)
            self.plane_local = gl.GLBoxItem(color=(0, 230, 118, 200))
            self.local_3d_view.addItem(self.plane_local)
            
            self.plane_main = gl.GLBoxItem(color=(255, 23, 68, 200))
            self.full_3d_view.addItem(self.plane_main)

    # =========================================================================
    # CORE LOGIC: PROCESARE DATE, TIMELINE ȘI REPLAY CONTROL
    # =========================================================================
    def refresh_ports(self):
        self.port_combo.clear()
        self.port_combo.addItems([p.device for p in serial.tools.list_ports.comports()])

    def refresh_recordings_list(self):
        self.file_selector.clear()
        files = [f for f in os.listdir(self.log_folder) if f.endswith('.csv')]
        self.file_selector.addItems(sorted(files, reverse=True))

    def on_replay_file_selected(self):
        self.btn_rename.setEnabled(bool(self.file_selector.currentText()))

    def toggle_connection(self):
        if self.serial_conn is None:
            try:
                self.serial_conn = serial.Serial(self.port_combo.currentText(), 115200, timeout=0.01)
                self.btn_connect.setText("Deconectare")
                self.btn_connect.setObjectName("ActiveBtn")
                self.btn_connect.setStyle(self.btn_connect.style())
                self.btn_record.setEnabled(True)
                self.is_replaying = False
                self.slider.setEnabled(False)
                self.btn_play_pause.setEnabled(False)
                
                self.flight_path_x.clear()
                self.flight_path_y.clear()
                
                self.timer.start(self.base_interval)
                self.status_bar.showMessage("Conectat la drona live.")
            except Exception as e:
                self.status_bar.showMessage(f"Eroare Port Serial: {e}", 5000)
        else:
            self.timer.stop()
            if self.is_recording: self.toggle_recording()
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.setText("Conectare")
            self.btn_connect.setObjectName("")
            self.btn_connect.setStyle(self.btn_connect.style())
            self.btn_record.setEnabled(False)
            self.status_bar.showMessage("Deconectat.")

    def toggle_recording(self):
        if not self.is_recording:
            self.recorded_data.clear()
            self.is_recording = True
            self.btn_record.setText("Stop Înregistrare")
            self.btn_record.setObjectName("ActiveBtn")
            self.btn_record.setStyle(self.btn_record.style())
            self.status_bar.showMessage("Salvare date în timp real pornită...")
        else:
            self.is_recording = False
            self.btn_record.setText("Start Înregistrare")
            self.btn_record.setObjectName("")
            self.btn_record.setStyle(self.btn_record.style())
            self.save_data_to_file()

    def save_data_to_file(self):
        if not self.recorded_data: return
        filename = f"log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(self.log_folder, filename)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['roll', 'pitch', 'yaw', 'alt', 'gps_lat', 'gps_lon', 'timestamp'])
            writer.writerows(self.recorded_data)
        self.refresh_recordings_list()
        self.status_bar.showMessage(f"Log salvat: {filename}", 6000)

    def rename_current_replay(self):
        old_name = self.file_selector.currentText()
        if not old_name: return
        new_name, ok = QInputDialog.getText(self, "Redenumește Replay", f"Nume nou pentru {old_name}:")
        if ok and new_name:
            if not new_name.endswith('.csv'): new_name += '.csv'
            try:
                os.rename(os.path.join(self.log_folder, old_name), os.path.join(self.log_folder, new_name))
                self.refresh_recordings_list()
                self.status_bar.showMessage(f"Fișier redenumit în: {new_name}")
            except Exception as e:
                self.status_bar.showMessage(f"Eroare redenumire: {e}")

    def toggle_replay(self):
        if not self.is_replaying:
            filename = self.file_selector.currentText()
            if not filename: return
            
            self.recorded_data.clear()
            self.flight_path_x.clear()
            self.flight_path_y.clear()
            
            try:
                with open(os.path.join(self.log_folder, filename), 'r') as f:
                    reader = csv.reader(f)
                    next(reader) # Sări peste header
                    for row in reader:
                        if len(row) >= 7:
                            self.recorded_data.append([float(x) for x in row])
                
                if not self.recorded_data: return
                if self.serial_conn: self.toggle_connection()
                
                # Configurare Timeline
                self.is_replaying = True
                self.is_paused = False
                self.btn_play_pause.setText("⏸ Pauză")
                self.btn_play_pause.setEnabled(True)
                self.slider.setEnabled(True)
                self.slider.setMaximum(len(self.recorded_data) - 1)
                self.slider.setValue(0)
                
                self.btn_replay.setText("Oprește Replay")
                self.btn_replay.setObjectName("ActiveBtn")
                self.btn_replay.setStyle(self.btn_replay.style())
                
                # Populare Chart-uri Analitice la încărcare log
                self.populate_analytics_charts()
                
                self.update_speed()
                self.timer.start()
                self.status_bar.showMessage(f"Se redă pachetul: {filename}")
            except Exception as e:
                self.status_bar.showMessage(f"Eroare citire fișier replay: {e}", 5000)
        else:
            self.stop_replay_engine()

    def stop_replay_engine(self):
        self.is_replaying = False
        self.is_paused = False
        self.btn_replay.setText("Încarcă Replay")
        self.btn_replay.setObjectName("")
        self.btn_replay.setStyle(self.btn_replay.style())
        self.btn_play_pause.setEnabled(False)
        self.btn_play_pause.setText("⏸ Pauză")
        self.slider.setEnabled(False)
        self.timer.stop()
        self.status_bar.showMessage("Replay oprit.")

    def toggle_play_pause(self):
        if not self.is_replaying: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_play_pause.setText("▶ Redă")
            self.status_bar.showMessage("Replay pus pe pauză.")
        else:
            self.btn_play_pause.setText("⏸ Pauză")
            self.status_bar.showMessage("Redare reluată.")

    def update_speed(self):
        speed_map = {"0.5x": 2.0, "1.0x": 1.0, "2.0x": 0.5, "4.0x": 0.25}
        multiplier = speed_map[self.speed_combo.currentText()]
        if self.timer.isActive() and self.is_replaying:
            self.timer.start(int(self.base_interval * multiplier))

    def populate_analytics_charts(self):
        """Generează graficele analitice complete pentru întreg zborul selectat"""
        data = np.array(self.recorded_data)
        timestamps = data[:, 6] / 1000.0  # Secunde
        
        # Plot Altitudine
        self.chart_alt.clear()
        self.chart_alt.plot(timestamps, data[:, 3], pen=pg.mkPen('#00E676', width=2))
        
        # Plot Unghiuri dinamice (Roll, Pitch, Yaw)
        self.chart_angles.clear()
        self.chart_angles.plot(timestamps, data[:, 0], pen=pg.mkPen('#FF1744', width=1.5), name="Roll")
        self.chart_angles.plot(timestamps, data[:, 1], pen=pg.mkPen('#29B6F6', width=1.5), name="Pitch")
        self.chart_angles.plot(timestamps, data[:, 2], pen=pg.mkPen('#FFEE58', width=1.5), name="Yaw")

    # =========================================================================
    # NAVIGARE PRIN TIMELINE ȘI OPERAȚIUNI DE INTERFAȚĂ
    # =========================================================================
    def on_slider_move(self):
        idx = self.slider.value()
        if 0 <= idx < len(self.recorded_data):
            roll, pitch, yaw, alt, lat, lon, ts = self.recorded_data[idx]
            self.lbl_frames.setText(f"TIMP: {ts/1000:.2f}s | CADRU: {idx} / {len(self.recorded_data)-1}")
            
            # Reconstrucție parcurs până la cadrul curent pe hartă
            slice_data = np.array(self.recorded_data[:idx+1])
            self.flight_path_x = slice_data[:, 5].tolist() # Longitudine
            self.flight_path_y = slice_data[:, 4].tolist() # Latitudine
            
            self.update_ui_elements(roll, pitch, yaw, alt, lat, lon, ts)

    def main_loop(self):
        if self.is_replaying:
            if not self.is_paused:
                current_idx = self.slider.value()
                if current_idx < self.slider.maximum():
                    self.slider.setValue(current_idx + 1)
                else:
                    self.stop_replay_engine()
        else:
            self.read_live_serial()

    def read_live_serial(self):
        """Procesează șirul de telemetrie extins conform noului protocol"""
        if self.serial_conn and self.serial_conn.in_waiting > 0:
            try:
                raw_bytes = self.serial_conn.read(self.serial_conn.in_waiting)
                raw_string = raw_bytes.decode('utf-8', errors='ignore')
                lines = raw_string.split('\n')
                
                # Procesează ultima linie completă primită serial
                for i in range(len(lines)-2, -1, -1):
                    parts = lines[i].strip().split(',')
                    if len(parts) >= 7:
                        # Parsare conform formatului de float-uri solicitat
                        r, p, y, a, lat, lon, t = [float(x) for x in parts[:6]] + [int(parts[6])]
                        
                        if self.is_recording: 
                            self.recorded_data.append([r, p, y, a, lat, lon, t])
                        
                        self.flight_path_x.append(lon)
                        self.flight_path_y.append(lat)
                        
                        self.update_ui_elements(r, p, y, a, lat, lon, t)
                        break
            except Exception:
                pass

    def update_ui_elements(self, roll, pitch, yaw, alt, lat, lon, timestamp):
        # Actualizare date interfață alfanumerică
        self.val_time.setText(f"{timestamp/1000:.2f}")
        self.val_roll.setText(f"{roll:>.2f}")
        self.val_pitch.setText(f"{pitch:>.2f}")
        self.val_yaw.setText(f"{yaw:>.2f}")
        self.val_alt.setText(f"{alt:>.2f}")
        self.val_gps.setText(f"{lat:.6f}, {lon:.6f}")
        
        # Planul Principal: Actualizare Hartă Verticală 2D
        self.map_update_counter += 1
    
        # Modulo 6 înseamnă că trimitem date către Google Maps o dată la 6 cadre.
        # Dacă replay-ul rulează la ~16ms, harta se va actualiza la fiecare ~100ms.
        # Este perfect vizual și elimină complet blocajele de procesor!
        if self.map_update_counter % 6 == 0:
            js_update_pos = f"updateDronePosition({lat}, {lon});"
            self.map_widget.page().runJavaScript(js_update_pos)
        
        # Planul Secundar: Rotație Atitudine Locală 3D (Z-X-Y Euler Coordonate)
        self.plane_local.resetTransform()
        self.plane_local.rotate(-yaw, 0, 0, 1)    # Direcție busolă (Yaw pe axa verticală Z)
        self.plane_local.rotate(-roll, 0, 1, 0)   # Înclinare aripă (Roll pe axa longitudinală Y)
        self.plane_local.rotate(pitch, 1, 0, 0)   # Unghi de atac nas (Pitch pe axa transversală X)

        # Planul Principal în Modul Full 3D
        self.plane_main.resetTransform()
        self.plane_main.rotate(-yaw, 0, 0, 1)
        self.plane_main.rotate(-roll, 0, 1, 0)
        self.plane_main.rotate(pitch, 1, 0, 0)
        
        # Calcul translație avion pe baza coordonatelor relative pentru zbor 3D (scalate pentru vizualizare)
        if len(self.flight_path_x) > 1:
            scale_factor = 10000 # Amplifică variațiile GPS mici pentru animația pe grid
            dx = (lon - self.flight_path_x[0]) * scale_factor
            dy = (lat - self.flight_path_y[0]) * scale_factor
            self.plane_main.translate(dx, dy, alt / 10.0)
            
            # Cameră atașată pe avion (Lock Mode)
            if self.camera_mode_combo.currentText() == "Lock pe Avion" and self.main_view_stack.currentIndex() == 1:
                self.full_3d_view.setCameraPosition(pos=pg.Vector(dx, dy, alt / 10.0))

    # =========================================================================
    # MODIFICĂRI LAYOUT ȘI CONTROALE DE TASTATURĂ (Săgeți/Pauză)
    # =========================================================================
    def change_map_style(self):
        """Schimbă layer-ul hărții Folium în funcție de selecția din ComboBox"""
        style = self.map_style_combo.currentText() # Va fi "Satelit Layout", "Terrain Layout" sau "Default Layout"
        js_code = f"setMapStyle('{style}');"
        self.map_widget.page().runJavaScript(js_code)

    def toggle_view_mode(self):
        """Comută planul principal între Harta 2D și modul Full 3D cu cameră liberă"""
        if self.main_view_stack.currentIndex() == 0:
            self.main_view_stack.setCurrentIndex(1)
            self.btn_view_mode.setText("Comută în Mod Hartă 2D")
            self.camera_mode_combo.setEnabled(True)
        else:
            self.main_view_stack.setCurrentIndex(0)
            self.btn_view_mode.setText("Comută în Mod Full 3D")
            self.camera_mode_combo.setEnabled(False)

    def keyPressEvent(self, event):
        """Navigare pas cu pas prin cadre folosind tastele direcționale stânga/dreapta și Space"""
        if self.is_replaying or self.slider.isEnabled():
            if event.key() == Qt.Key_Left:
                self.slider.setValue(max(0, self.slider.value() - 1))
                self.status_bar.showMessage(f"Navigare manuală înapoi. Cadrul: {self.slider.value()}")
            elif event.key() == Qt.Key_Right:
                self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 1))
                self.status_bar.showMessage(f"Navigare manuală înainte. Cadrul: {self.slider.value()}")
            elif event.key() == Qt.Key_Space:
                self.toggle_play_pause()
        else:
            super().keyPressEvent(event)

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(self.DARK_STYLE)
            self.local_3d_view.setBackgroundColor(18, 18, 26)
            self.full_3d_view.setBackgroundColor(12, 12, 18)
            self.grid_main.setColor((255, 255, 255, 30))
            self.btn_theme.setText("☀️ Mod Luminos")
        else:
            self.setStyleSheet(self.LIGHT_STYLE)
            self.local_3d_view.setBackgroundColor(240, 240, 245)
            self.full_3d_view.setBackgroundColor(245, 245, 247)
            self.grid_main.setColor((0, 0, 0, 40))
            self.btn_theme.setText("🌙 Mod Întunecat")
        self.change_map_style()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)
    
    window = TelemetryGCS()
    window.show()
    sys.exit(app.exec_())