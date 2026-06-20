_TELE_DATA_COMMON = (
    "font-family: 'Consolas', monospace; font-size: 22px; font-weight: bold;"
    " border-radius: 6px; padding: 6px;"
)

DARK = f"""
    QMainWindow {{ background-color: #121212; }}
    QFrame#Card {{ background-color: #1E1E2E; border-radius: 12px; border: 1px solid #2B2B40; }}
    QFrame#VLine {{ color: #2B2B40; }}
    QLabel {{ color: #E0E0E0; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }}
    QLabel#TeleTitle {{ color: #8A8D93; font-size: 11px; font-weight: bold; }}
    QLabel#TeleData {{
        {_TELE_DATA_COMMON}
        color: #00E676; background-color: #151521; border: 1px solid #2B2B40;
    }}
    QLabel#TeleData_warn {{
        {_TELE_DATA_COMMON}
        color: #FFAB00; background-color: #151521; border: 1px solid #3A3000;
    }}
    QLabel#TeleData_crit {{
        {_TELE_DATA_COMMON}
        color: #FF1744; background-color: #151521; border: 1px solid #3A0010;
    }}
    QPushButton {{
        background-color: #3D5AFE; color: white; border-radius: 6px;
        padding: 8px 14px; font-weight: bold; font-size: 13px; border: none;
    }}
    QPushButton:hover {{ background-color: #536DFE; }}
    QPushButton:disabled {{ background-color: #2A2A3E; color: #5A5A7A; }}
    QPushButton#ActiveBtn {{ background-color: #FF1744; color: white; }}
    QPushButton#ActiveBtn:hover {{ background-color: #FF4569; }}
    QPushButton#SmallBtn {{
        background-color: #2B2B40; color: #E0E0E0; border-radius: 6px;
        padding: 6px 10px; font-weight: bold; font-size: 13px; border: 1px solid #3D3D5C;
    }}
    QPushButton#SmallBtn:hover {{ background-color: #3D3D5C; }}
    QComboBox {{
        background-color: #151521; color: white; border: 1px solid #2B2B40;
        border-radius: 6px; padding: 6px; font-size: 13px;
    }}
    QComboBox::drop-down {{ border: none; }}
    QSlider::groove:horizontal {{
        border: 1px solid #2B2B40; height: 8px; background: #151521; border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: #3D5AFE; width: 16px; margin-top: -4px; margin-bottom: -4px; border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{ background: #3D5AFE; border-radius: 4px; }}
    QTabBar::tab {{
        background: #1E1E2E; color: #8A8D93; padding: 8px 16px;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{ background: #3D5AFE; color: white; }}
    QTabWidget::pane {{ border: 1px solid #2B2B40; background-color: #1E1E2E; }}
    QStatusBar {{ background-color: #1E1E2E; color: #8A8D93; font-size: 12px; }}
    QStatusBar::item {{ border: none; }}
"""

LIGHT = f"""
    QMainWindow {{ background-color: #F5F5F7; }}
    QFrame#Card {{ background-color: #FFFFFF; border-radius: 12px; border: 1px solid #D2D2D7; }}
    QFrame#VLine {{ color: #D2D2D7; }}
    QLabel {{ color: #1D1D1F; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }}
    QLabel#TeleTitle {{ color: #6E6E73; font-size: 11px; font-weight: bold; }}
    QLabel#TeleData {{
        {_TELE_DATA_COMMON}
        color: #1D1D1F; background-color: #E8E8ED; border: 1px solid #D2D2D7;
    }}
    QLabel#TeleData_warn {{
        {_TELE_DATA_COMMON}
        color: #9C5C00; background-color: #E8E8ED; border: 1px solid #C8A060;
    }}
    QLabel#TeleData_crit {{
        {_TELE_DATA_COMMON}
        color: #CC0000; background-color: #E8E8ED; border: 1px solid #CC8080;
    }}
    QPushButton {{
        background-color: #0071E3; color: white; border-radius: 6px;
        padding: 8px 14px; font-weight: bold; font-size: 13px; border: none;
    }}
    QPushButton:hover {{ background-color: #147CE5; }}
    QPushButton:disabled {{ background-color: #C7C7CC; color: #8E8E93; }}
    QPushButton#ActiveBtn {{ background-color: #FF3B30; color: white; }}
    QPushButton#ActiveBtn:hover {{ background-color: #FF6961; }}
    QPushButton#SmallBtn {{
        background-color: #E8E8ED; color: #1D1D1F; border-radius: 6px;
        padding: 6px 10px; font-weight: bold; font-size: 13px; border: 1px solid #C7C7CC;
    }}
    QPushButton#SmallBtn:hover {{ background-color: #D2D2D7; }}
    QComboBox {{
        background-color: #FFFFFF; color: #1D1D1F; border: 1px solid #D2D2D7;
        border-radius: 6px; padding: 6px; font-size: 13px;
    }}
    QComboBox::drop-down {{ border: none; }}
    QSlider::groove:horizontal {{
        border: 1px solid #D2D2D7; height: 8px; background: #E8E8ED; border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: #0071E3; width: 16px; margin-top: -4px; margin-bottom: -4px; border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{ background: #0071E3; border-radius: 4px; }}
    QTabBar::tab {{
        background: #E8E8ED; color: #6E6E73; padding: 8px 16px;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{ background: #0071E3; color: white; }}
    QTabWidget::pane {{ border: 1px solid #D2D2D7; background-color: #FFFFFF; }}
    QStatusBar {{ background-color: #FFFFFF; color: #6E6E73; font-size: 12px; }}
    QStatusBar::item {{ border: none; }}
"""
