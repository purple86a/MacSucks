"""QSS theme — neon purple utility (flat, single bg)."""

# Accent: RGB(138, 43, 226) = #8A2BE2 (true violet, not magenta)
TOKENS = {
    "bg": "#121016",
    "surface": "#121016",
    "surface_alt": "#121016",
    "border": "#3a2f4a",
    "text": "#f0eaf8",
    "text_muted": "#a898bc",
    "accent": "#8A2BE2",
    "accent_hover": "#9B4AED",
    "accent_pressed": "#6F22B8",
    "accent_dim": "#2a1a3d",
    "danger": "#e05a6a",
    "success": "#5ecf8a",
    "radius": "6px",
    "space": 12,
}


def build_stylesheet() -> str:
    t = TOKENS
    return f"""
    QWidget {{
        background-color: {t["bg"]};
        color: {t["text"]};
        font-family: "Segoe UI", "SF Pro Text", sans-serif;
        font-size: 13px;
    }}
    QLabel {{
        background-color: transparent;
    }}
    QWidget#settingsWindow {{
        background-color: {t["bg"]};
        border: 1px solid {t["border"]};
    }}
    QWidget#titleBar {{
        background-color: {t["bg"]};
        border-bottom: 1px solid {t["border"]};
    }}
    QLabel#titleBarLabel {{
        color: {t["text"]};
        font-weight: 600;
        font-size: 13px;
        background: transparent;
    }}
    QPushButton#titleBarBtn, QPushButton#titleBarCloseBtn {{
        background: transparent;
        border: none;
        border-radius: 4px;
        color: {t["text_muted"]};
        padding: 0;
        min-height: 0;
    }}
    QPushButton#titleBarBtn:hover {{
        background-color: {t["accent_dim"]};
        color: {t["text"]};
    }}
    QPushButton#titleBarCloseBtn:hover {{
        background-color: {t["danger"]};
        color: #ffffff;
    }}
    QMainWindow, QDialog, QTabWidget {{
        background-color: {t["bg"]};
    }}
    QGroupBox {{
        background-color: {t["bg"]};
        border: none;
        border-top: 1px solid {t["border"]};
        border-radius: 0;
        margin-top: 10px;
        padding-top: 10px;
        padding-bottom: 2px;
        font-weight: 600;
        font-size: 11px;
        color: {t["accent"]};
    }}
    QGroupBox#firstSection {{
        border-top: none;
        margin-top: 0;
        padding-top: 4px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 0;
        top: 0;
        padding: 0 0 2px 0;
        color: {t["accent"]};
        background-color: {t["bg"]};
    }}
    QLineEdit, QPlainTextEdit {{
        background-color: {t["bg"]};
        border: none;
        border-bottom: 1px solid {t["border"]};
        border-radius: 0;
        padding: 8px 2px;
        color: {t["text"]};
        selection-background-color: {t["accent"]};
    }}
    QLineEdit:focus, QPlainTextEdit:focus {{
        border-bottom-color: {t["accent"]};
        background-color: {t["bg"]};
    }}
    QPlainTextEdit {{
        font-family: Consolas, "Cascadia Mono", monospace;
        font-size: 12px;
        border: 1px solid {t["border"]};
        border-radius: {t["radius"]};
        padding: 8px;
        background-color: {t["bg"]};
    }}
    QPlainTextEdit:focus {{
        border-color: {t["accent"]};
    }}
    QPushButton {{
        background-color: {t["bg"]};
        border: 1px solid {t["border"]};
        border-radius: {t["radius"]};
        padding: 8px 14px;
        color: {t["text"]};
        min-height: 18px;
    }}
    QPushButton:hover {{
        border-color: {t["accent"]};
        color: {t["text"]};
        background-color: {t["accent_dim"]};
    }}
    QPushButton:pressed {{
        background-color: {t["accent_pressed"]};
        border-color: {t["accent_pressed"]};
    }}
    QPushButton#primary {{
        background-color: {t["accent"]};
        border-color: {t["accent"]};
        color: #ffffff;
        font-weight: 600;
    }}
    QPushButton#primary:hover {{
        background-color: {t["accent_hover"]};
        border-color: {t["accent_hover"]};
    }}
    QPushButton#primary:pressed {{
        background-color: {t["accent_pressed"]};
        border-color: {t["accent_pressed"]};
    }}
    QPushButton:disabled {{
        color: {t["text_muted"]};
        background-color: {t["bg"]};
        border-color: {t["border"]};
    }}
    QCheckBox {{
        spacing: 8px;
        color: {t["text"]};
        background-color: {t["bg"]};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {t["border"]};
        border-radius: 4px;
        background-color: {t["bg"]};
    }}
    QCheckBox::indicator:checked {{
        background: {t["accent"]};
        border-color: {t["accent"]};
    }}
    QLabel#status_ok {{
        color: {t["success"]};
        background: transparent;
    }}
    QLabel#status_err {{
        color: {t["danger"]};
        background: transparent;
    }}
    QLabel#muted {{
        color: {t["text_muted"]};
        background: transparent;
    }}
    QLabel#hotkey_value {{
        font-size: 14px;
        font-weight: 600;
        color: {t["text"]};
        background: transparent;
    }}
    QTabWidget::pane {{
        border: none;
        border-top: 1px solid {t["border"]};
        background: {t["bg"]};
        top: -1px;
        padding-top: 8px;
        margin: 0;
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 14px;
        margin-right: 2px;
        color: {t["text_muted"]};
    }}
    QTabBar::tab:hover {{
        color: {t["text"]};
    }}
    QTabBar::tab:selected {{
        color: {t["accent_hover"]};
        border-bottom: 2px solid {t["accent"]};
        background: transparent;
    }}
    QComboBox {{
        background-color: {t["bg"]};
        border: 1px solid {t["border"]};
        border-radius: {t["radius"]};
        padding: 8px 10px;
        color: {t["text"]};
        min-height: 18px;
    }}
    QComboBox:hover, QComboBox:focus {{
        border-color: {t["accent"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t["bg"]};
        border: 1px solid {t["border"]};
        selection-background-color: {t["accent_dim"]};
        selection-color: {t["text"]};
        color: {t["text"]};
        outline: none;
        padding: 4px;
    }}
    QScrollArea#settingsScroll {{
        background-color: {t["bg"]};
        border: none;
    }}
    QScrollArea#settingsScroll > QWidget > QWidget {{
        background-color: {t["bg"]};
    }}
    QScrollBar:vertical {{
        background: {t["bg"]};
        width: 10px;
        margin: 2px 0;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: #5a3d7a;
        border-radius: 5px;
        min-height: 28px;
        margin: 0 1px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t["accent"]};
    }}
    QScrollBar::handle:vertical:pressed {{
        background: {t["accent_pressed"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        width: 0;
        background: none;
        border: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: {t["bg"]};
        height: 10px;
        margin: 0 2px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: #5a3d7a;
        border-radius: 5px;
        min-width: 28px;
        margin: 1px 0;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {t["accent"]};
    }}
    QScrollBar::handle:horizontal:pressed {{
        background: {t["accent_pressed"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        height: 0;
        width: 0;
        background: none;
        border: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QMenu {{
        background-color: {t["bg"]};
        border: 1px solid {t["border"]};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
        background: transparent;
    }}
    QMenu::item:selected {{
        background-color: {t["accent_dim"]};
        color: {t["text"]};
    }}
    QToolTip {{
        background-color: {t["bg"]};
        color: {t["text"]};
        border: 1px solid {t["accent"]};
        padding: 4px 8px;
    }}
    """
