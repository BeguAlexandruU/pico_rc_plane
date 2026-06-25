import os
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QSlider, QFrame,
    QStatusBar, QInputDialog, QTabWidget, QSplitter,
    QStackedWidget, QSizePolicy,
)
from PyQt5.QtCore import QTimer, Qt

from .core.models import TelemetryFrame
from .core.serial_reader import SerialReader
from .core.recorder import Recorder
from .ui import themes
from .ui.telemetry_panel import TelemetryPanel
from .ui.map_view import MapView
from .ui.view_3d import Full3DView
from .ui.charts import AnalyticsCharts
from .utils.stl_loader import load_stl

_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_FOLDER = os.path.join(_BASE_DIR, "telemetry_logs")
_STL_PATH   = os.path.join(_BASE_DIR, "plane_models", "pico_plane.stl")
_SPEED_MAP  = {"0.5x": 2.0, "1.0x": 1.0, "2.0x": 0.5, "4.0x": 0.25}


class GCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ground Control Station")
        self.resize(1500, 950)

        self._recorder = Recorder(_LOG_FOLDER)
        self._serial = None
        self._replay_frames = []
        self._flight_path = []

        self._is_recording = False
        self._is_replaying = False
        self._is_paused = False
        self._is_dark_mode = True

        self._build_ui()
        self._load_3d_model()
        self._apply_theme()
        self.setFocusPolicy(Qt.StrongFocus)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(self._build_top_bar())
        layout.addWidget(self._build_center(), stretch=1)
        layout.addWidget(self._build_nav_bar())

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._lbl_mode = QLabel("  IDLE  ")
        self._lbl_mode.setStyleSheet(
            "font-family: 'Consolas', monospace; font-weight: bold; padding: 0 6px;"
        )
        self._status_bar.addPermanentWidget(self._lbl_mode)
        self._status_bar.showMessage("Sistem pregătit.")

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

    def _build_top_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self._led = QLabel("●")
        self._led.setToolTip("Stare conexiune")

        self._btn_refresh_ports = QPushButton("⟳")
        self._btn_refresh_ports.setObjectName("SmallBtn")
        self._btn_refresh_ports.setFixedWidth(36)
        self._btn_refresh_ports.setToolTip("Reîmprospătează lista de porturi")
        self._btn_refresh_ports.clicked.connect(self._refresh_ports)

        self._port_combo = QComboBox()
        self._port_combo.setMinimumWidth(100)
        self._refresh_ports()

        self._btn_connect = QPushButton("Conectare")
        self._btn_connect.setMinimumWidth(110)
        self._btn_connect.clicked.connect(self._toggle_connection)

        self._btn_theme = QPushButton("☀️ Mod Luminos")
        self._btn_theme.clicked.connect(self._toggle_theme)

        row1.addWidget(self._led)
        row1.addWidget(self._btn_refresh_ports)
        row1.addWidget(QLabel("PORT:"))
        row1.addWidget(self._port_combo)
        row1.addWidget(self._btn_connect)
        row1.addStretch()
        row1.addWidget(self._btn_theme)

        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self._file_combo = QComboBox()
        self._file_combo.setMinimumWidth(210)
        self._file_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._refresh_file_list()
        self._file_combo.currentIndexChanged.connect(
            lambda: self._btn_rename.setEnabled(bool(self._file_combo.currentText()))
        )

        self._btn_replay = QPushButton("▶ Încarcă Replay")
        self._btn_replay.clicked.connect(self._toggle_replay)

        self._btn_rename = QPushButton("Redenumește")
        self._btn_rename.clicked.connect(self._rename_log)
        self._btn_rename.setEnabled(False)

        self._speed_combo = QComboBox()
        self._speed_combo.addItems(list(_SPEED_MAP.keys()))
        self._speed_combo.setCurrentText("1.0x")
        self._speed_combo.currentIndexChanged.connect(self._update_replay_speed)

        self._btn_record = QPushButton("⏺ Start Înregistrare")
        self._btn_record.clicked.connect(self._toggle_recording)
        self._btn_record.setEnabled(False)

        sep = QFrame()
        sep.setObjectName("VLine")
        sep.setFrameShape(QFrame.VLine)

        row2.addWidget(QLabel("LOGURI:"))
        row2.addWidget(self._file_combo)
        row2.addWidget(self._btn_replay)
        row2.addWidget(self._btn_rename)
        row2.addWidget(sep)
        row2.addWidget(QLabel("VITEZĂ:"))
        row2.addWidget(self._speed_combo)
        row2.addStretch()
        row2.addWidget(self._btn_record)

        outer.addLayout(row1)
        outer.addLayout(row2)
        return frame

    def _build_center(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)

        left_tabs = QTabWidget()
        left_tabs.setFixedWidth(320)

        tele_frame = QFrame()
        tele_frame.setObjectName("Card")
        tele_box = QVBoxLayout(tele_frame)
        tele_box.setContentsMargins(0, 0, 0, 0)
        self._tele_panel = TelemetryPanel()
        tele_box.addWidget(self._tele_panel)
        left_tabs.addTab(tele_frame, "Telemetrie")

        self._charts = AnalyticsCharts()
        left_tabs.addTab(self._charts, "Analiză Chart-uri")
        splitter.addWidget(left_tabs)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)

        view_bar = QHBoxLayout()
        view_bar.setSpacing(6)
        self._map_style_combo = QComboBox()
        self._map_style_combo.addItems(["Default Layout", "Satelit Layout", "Terrain Layout"])
        self._map_style_combo.currentIndexChanged.connect(
            lambda: self._map_view.set_style(self._map_style_combo.currentText())
        )
        self._btn_view_mode = QPushButton("Comută în Mod Full 3D")
        self._btn_view_mode.clicked.connect(self._toggle_view_mode)
        self._camera_combo = QComboBox()
        self._camera_combo.addItems(["Free Camera", "Lock pe Avion"])
        self._camera_combo.setEnabled(False)

        view_bar.addWidget(QLabel("Stil Hartă:"))
        view_bar.addWidget(self._map_style_combo)
        view_bar.addStretch()
        view_bar.addWidget(self._camera_combo)
        view_bar.addWidget(self._btn_view_mode)
        center_layout.addLayout(view_bar)

        self._view_stack = QStackedWidget()
        self._map_view = MapView()
        self._full_3d  = Full3DView()
        self._view_stack.addWidget(self._map_view)
        self._view_stack.addWidget(self._full_3d)
        center_layout.addWidget(self._view_stack)
        splitter.addWidget(center)

        splitter.setSizes([320, 1180])
        return splitter

    def _build_nav_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(6)

        self._btn_jump_start = QPushButton("⏮")
        self._btn_jump_start.setObjectName("SmallBtn")
        self._btn_jump_start.setFixedWidth(36)
        self._btn_jump_start.setToolTip("Salt la început  (Home)")
        self._btn_jump_start.clicked.connect(lambda: self._slider.setValue(0))
        self._btn_jump_start.setEnabled(False)

        self._btn_play_pause = QPushButton("⏸ Pauză")
        self._btn_play_pause.setMinimumWidth(100)
        self._btn_play_pause.clicked.connect(self._toggle_play_pause)
        self._btn_play_pause.setEnabled(False)

        self._btn_jump_end = QPushButton("⏭")
        self._btn_jump_end.setObjectName("SmallBtn")
        self._btn_jump_end.setFixedWidth(36)
        self._btn_jump_end.setToolTip("Salt la sfârșit  (End)")
        self._btn_jump_end.clicked.connect(lambda: self._slider.setValue(self._slider.maximum()))
        self._btn_jump_end.setEnabled(False)

        self._lbl_frames = QLabel("TIMP: 0.0s | 0/0 (0%)")
        self._lbl_frames.setFixedWidth(240)
        self._lbl_frames.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setEnabled(False)
        self._slider.valueChanged.connect(self._on_slider_scrub)

        lbl_hint = QLabel("← → Space")
        lbl_hint.setStyleSheet("color: #555577; font-size: 11px;")
        lbl_hint.setToolTip("Taste: ← → cadru-cu-cadru, Space = pauză/redare, Home/End")

        layout.addWidget(self._btn_jump_start)
        layout.addWidget(self._btn_play_pause)
        layout.addWidget(self._btn_jump_end)
        layout.addWidget(self._lbl_frames)
        layout.addWidget(self._slider)
        layout.addWidget(lbl_hint)
        return frame

    def _load_3d_model(self):
        result = load_stl(_STL_PATH)
        if result:
            verts, faces = result
            self._full_3d.load_model(verts, faces)
        else:
            self._full_3d.load_fallback()
            self._status_bar.showMessage("pico_plane.stl lipsă — se folosesc cuburi virtuale.", 5000)

    def _update_led(self):
        if self._is_recording:
            color, tip, mode = "#FF1744", "Înregistrare activă", "REC"
        elif self._serial:
            color, tip, mode = "#00E676", "Conectat live", "LIVE"
        elif self._is_replaying:
            color, tip, mode = "#3D5AFE", "Replay activ", "REPLAY"
        else:
            color, tip, mode = "#444466", "Inactiv", "IDLE"
        self._led.setStyleSheet(f"color: {color}; font-size: 20px;")
        self._led.setToolTip(tip)
        self._lbl_mode.setText(f"  {mode}  ")

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        current = self._port_combo.currentText() if hasattr(self, "_port_combo") else ""
        self._port_combo.clear()
        self._port_combo.addItems(ports)
        if current in ports:
            self._port_combo.setCurrentText(current)
        if not ports:
            self._status_bar.showMessage("Niciun port serial detectat.", 4000)

    def _toggle_connection(self):
        if self._serial is None:
            port = self._port_combo.currentText()
            if not port:
                self._status_bar.showMessage("Selectează un port serial.", 3000)
                return
            self._serial = SerialReader(port)
            self._serial.frame_received.connect(self._on_live_frame)
            self._serial.error_occurred.connect(self._on_serial_error)
            self._serial.start()
            self._flight_path.clear()
            self._map_view.reset_path()
            self._full_3d.reset_origin()
            self._btn_connect.setText("⏹ Deconectare")
            self._set_active(self._btn_connect, True)
            self._btn_record.setEnabled(True)
            self._update_led()
            self._status_bar.showMessage(f"Conectat pe {port} @ 115200 baud.")
        else:
            if self._is_recording:
                self._toggle_recording()
            self._serial.stop()
            self._serial = None
            self._btn_connect.setText("Conectare")
            self._set_active(self._btn_connect, False)
            self._btn_record.setEnabled(False)
            self._update_led()
            self._status_bar.showMessage("Deconectat.")

    def _on_serial_error(self, msg: str):
        self._serial = None
        self._btn_connect.setText("Conectare")
        self._set_active(self._btn_connect, False)
        self._btn_record.setEnabled(False)
        self._is_recording = False
        self._update_led()
        self._status_bar.showMessage(f"Eroare serial: {msg}", 8000)

    def _on_live_frame(self, frame: TelemetryFrame):
        self._recorder.append(frame)
        self._flight_path.append((frame.lat, frame.lon))
        self._update_ui(frame)

    def _toggle_recording(self):
        if not self._is_recording:
            self._recorder.start()
            self._is_recording = True
            self._btn_record.setText("⏹ Stop Înregistrare")
            self._set_active(self._btn_record, True)
            self._update_led()
            self._status_bar.showMessage("⏺  Înregistrare pornită...")
        else:
            filename = self._recorder.stop()
            self._is_recording = False
            self._btn_record.setText("⏺ Start Înregistrare")
            self._set_active(self._btn_record, False)
            self._update_led()
            if filename:
                self._refresh_file_list()
                self._status_bar.showMessage(f"Log salvat: {filename}", 6000)

    def _refresh_file_list(self):
        current = self._file_combo.currentText()
        self._file_combo.clear()
        logs = self._recorder.list_logs()
        self._file_combo.addItems(logs)
        if current in logs:
            self._file_combo.setCurrentText(current)

    def _toggle_replay(self):
        if not self._is_replaying:
            filename = self._file_combo.currentText()
            if not filename:
                self._status_bar.showMessage("Niciun fișier de log selectat.", 3000)
                return
            try:
                self._replay_frames = self._recorder.load_log(filename)
            except Exception as e:
                self._status_bar.showMessage(f"Eroare citire fișier: {e}", 5000)
                return
            if not self._replay_frames:
                self._status_bar.showMessage("Fișierul log este gol.", 3000)
                return

            if self._serial:
                self._toggle_connection()

            self._flight_path.clear()
            self._map_view.reset_path()
            self._full_3d.reset_origin()

            self._is_replaying = True
            self._is_paused = False

            self._slider.setMaximum(len(self._replay_frames) - 1)
            self._slider.blockSignals(True)
            self._slider.setValue(0)
            self._slider.blockSignals(False)
            self._slider.setEnabled(True)

            self._btn_play_pause.setEnabled(True)
            self._btn_play_pause.setText("⏸ Pauză")
            self._btn_jump_start.setEnabled(True)
            self._btn_jump_end.setEnabled(True)
            self._btn_replay.setText("⏹ Oprește Replay")
            self._set_active(self._btn_replay, True)

            self._charts.populate(self._replay_frames)
            self._update_led()
            self._timer.start(self._compute_interval(0))
            self._status_bar.showMessage(f"Redare: {filename}")
        else:
            self._stop_replay()

    def _stop_replay(self):
        self._timer.stop()
        self._is_replaying = False
        self._is_paused = False
        self._btn_replay.setText("▶ Încarcă Replay")
        self._set_active(self._btn_replay, False)
        self._btn_play_pause.setEnabled(False)
        self._btn_play_pause.setText("⏸ Pauză")
        self._btn_jump_start.setEnabled(False)
        self._btn_jump_end.setEnabled(False)
        self._slider.setEnabled(False)
        self._update_led()
        self._status_bar.showMessage("Replay oprit.")

    def _toggle_play_pause(self):
        if not self._is_replaying:
            return
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._btn_play_pause.setText("▶ Redă")
            self._status_bar.showMessage("Pauză.  (Space = reia)")
        else:
            self._btn_play_pause.setText("⏸ Pauză")
            self._status_bar.showMessage("Redare reluată.")

    def _compute_interval(self, idx: int) -> int:
        if idx + 1 >= len(self._replay_frames):
            return 16
        dt = abs(self._replay_frames[idx + 1].timestamp_ms - self._replay_frames[idx].timestamp_ms)
        mult = _SPEED_MAP.get(self._speed_combo.currentText(), 1.0)
        return max(16, min(2000, int(dt * mult)))

    def _update_replay_speed(self):
        if self._is_replaying:
            self._timer.start(self._compute_interval(self._slider.value()))

    def _rename_log(self):
        old_name = self._file_combo.currentText()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(
            self, "Redenumește Log", f"Nume nou pentru «{old_name}»:"
        )
        if ok and new_name.strip():
            try:
                self._recorder.rename_log(old_name, new_name.strip())
                self._refresh_file_list()
                self._status_bar.showMessage("Fișier redenumit.", 3000)
            except Exception as e:
                self._status_bar.showMessage(f"Eroare redenumire: {e}", 5000)

    def _tick(self):
        if not self._is_replaying or self._is_paused:
            return
        idx = self._slider.value()
        if idx < self._slider.maximum():
            new_idx = idx + 1
            self._slider.blockSignals(True)
            self._slider.setValue(new_idx)
            self._slider.blockSignals(False)

            frame = self._replay_frames[new_idx]
            self._flight_path.append((frame.lat, frame.lon))
            self._update_frame_label(new_idx)
            self._update_ui(frame)
            self._timer.start(self._compute_interval(new_idx))
        else:
            self._stop_replay()

    def _on_slider_scrub(self):
        idx = self._slider.value()
        if not self._replay_frames or idx >= len(self._replay_frames):
            return
        frame = self._replay_frames[idx]
        self._update_frame_label(idx)
        self._flight_path = [(f.lat, f.lon) for f in self._replay_frames[:idx + 1]]
        self._map_view.draw_path(self._flight_path)
        self._full_3d.apply_pose(
            frame.roll, frame.pitch, frame.yaw,
            frame.altitude, frame.lat, frame.lon,
            self._camera_combo.currentText() == "Lock pe Avion" and self._view_stack.currentIndex() == 1,
        )
        self._tele_panel.update(frame)

    def _update_frame_label(self, idx: int):
        frame = self._replay_frames[idx]
        total = len(self._replay_frames)
        pct = int(idx / max(total - 1, 1) * 100)
        self._lbl_frames.setText(f"TIMP: {frame.timestamp_ms/1000:.2f}s | {idx}/{total-1} ({pct}%)")

    def _update_ui(self, frame: TelemetryFrame):
        self._tele_panel.update(frame)
        self._map_view.update_position(frame.lat, frame.lon)
        lock = (
            self._camera_combo.currentText() == "Lock pe Avion"
            and self._view_stack.currentIndex() == 1
        )
        self._full_3d.apply_pose(
            frame.roll, frame.pitch, frame.yaw,
            frame.altitude, frame.lat, frame.lon, lock,
        )

    def _toggle_view_mode(self):
        if self._view_stack.currentIndex() == 0:
            self._view_stack.setCurrentIndex(1)
            self._btn_view_mode.setText("Comută în Mod Hartă 2D")
            self._camera_combo.setEnabled(True)
        else:
            self._view_stack.setCurrentIndex(0)
            self._btn_view_mode.setText("Comută în Mod Full 3D")
            self._camera_combo.setEnabled(False)

    def _apply_theme(self):
        if self._is_dark_mode:
            self.setStyleSheet(themes.DARK)
            self._full_3d.set_background(12, 12, 18)
            self._full_3d.set_grid_color(255, 255, 255, 100)
            self._full_3d.set_plane_color((0.22, 0.82, 1.0, 1.0))
            self._btn_theme.setText("☀️ Mod Luminos")
        else:
            self.setStyleSheet(themes.LIGHT)
            self._full_3d.set_background(245, 245, 247)
            self._full_3d.set_grid_color(0, 0, 0, 100)
            self._full_3d.set_plane_color((0.05, 0.48, 0.92, 1.0))
            self._btn_theme.setText("🌙 Mod Întunecat")
        self._map_view.set_style(self._map_style_combo.currentText())
        self._update_led()

    def _toggle_theme(self):
        self._is_dark_mode = not self._is_dark_mode
        self._apply_theme()

    def keyPressEvent(self, event):
        if self._slider.isEnabled():
            key = event.key()
            if key == Qt.Key_Left:
                self._slider.setValue(max(0, self._slider.value() - 1))
            elif key == Qt.Key_Right:
                self._slider.setValue(min(self._slider.maximum(), self._slider.value() + 1))
            elif key == Qt.Key_Space:
                self._toggle_play_pause()
            elif key == Qt.Key_Home:
                self._slider.setValue(0)
            elif key == Qt.Key_End:
                self._slider.setValue(self._slider.maximum())
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    @staticmethod
    def _set_active(btn: QPushButton, active: bool):
        btn.setObjectName("ActiveBtn" if active else "")
        btn.setStyle(btn.style())
