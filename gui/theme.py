"""
Professional Theme and QSS Stylesheet for ShadowTun Linux VPN.
Features a clean, minimalist dark aesthetic with refined slate/zinc tones,
professional royal blue accents, crisp typography, and subtle status indicators.
"""

PALETTE = {
    "bg_main": "#111217",
    "bg_surface": "#181A22",
    "bg_card": "#1E202B",
    "bg_card_hover": "#252836",
    "bg_input": "#14151D",
    "border": "#282B38",
    "border_light": "#34384A",
    "border_focus": "#3B82F6",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_active": "#1E40AF",
    "primary_text": "#FFFFFF",
    "success": "#10B981",
    "success_bg": "rgba(16, 185, 129, 0.12)",
    "success_border": "rgba(16, 185, 129, 0.3)",
    "warning": "#F59E0B",
    "warning_bg": "rgba(245, 158, 11, 0.12)",
    "warning_border": "rgba(245, 158, 11, 0.3)",
    "danger": "#EF4444",
    "danger_bg": "rgba(239, 68, 68, 0.12)",
    "danger_border": "rgba(239, 68, 68, 0.3)",
    "danger_hover": "#DC2626",
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "text_muted": "#6B7280"
}

QSS_STYLE = """
/* Global Application Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #111217;
    color: #F9FAFB;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
}

/* Card & Surface Containers */
QFrame.surface {
    background-color: #181A22;
    border: 1px solid #282B38;
    border-radius: 10px;
}

QFrame.card {
    background-color: #1E202B;
    border: 1px solid #282B38;
    border-radius: 8px;
}

QFrame.card:hover {
    border: 1px solid #34384A;
}

/* Typography & Labels */
QLabel {
    color: #F9FAFB;
}

QLabel.app-title {
    font-size: 15px;
    font-weight: 700;
    color: #F9FAFB;
    letter-spacing: 0.5px;
}

QLabel.app-subtitle {
    font-size: 11px;
    color: #6B7280;
}

QLabel.section-header {
    font-size: 12px;
    font-weight: 600;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Status Badges */
QLabel.status-pill {
    background-color: #181A22;
    color: #9CA3AF;
    border: 1px solid #282B38;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.status-pill-connected {
    background-color: rgba(16, 185, 129, 0.12);
    color: #10B981;
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.status-pill-connecting {
    background-color: rgba(245, 158, 11, 0.12);
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.status-pill-error {
    background-color: rgba(239, 68, 68, 0.12);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

/* Inputs */
QLineEdit {
    background-color: #14151D;
    border: 1px solid #282B38;
    border-radius: 6px;
    padding: 7px 10px;
    color: #F9FAFB;
    font-size: 12px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #3B82F6;
    background-color: #171922;
}

/* Buttons */
QPushButton {
    background-color: #1E202B;
    border: 1px solid #282B38;
    border-radius: 6px;
    color: #F9FAFB;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #252836;
    border: 1px solid #34384A;
}

QPushButton:pressed {
    background-color: #181A22;
}

QPushButton:disabled {
    background-color: #161720;
    border-color: #232531;
    color: #555A6B;
}

QPushButton.btn-primary {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #1D4ED8;
    border-color: #2563EB;
}

QPushButton.btn-primary:pressed {
    background-color: #1E40AF;
}

QPushButton.btn-connect {
    background-color: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton.btn-connect:hover {
    background-color: #1D4ED8;
}

QPushButton.btn-disconnect {
    background-color: #1E202B;
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton.btn-disconnect:hover {
    background-color: rgba(239, 68, 68, 0.15);
    border-color: #EF4444;
}

QPushButton.btn-connecting {
    background-color: #1E202B;
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 8px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton.btn-danger {
    background-color: transparent;
    color: #9CA3AF;
    border: none;
    border-radius: 4px;
    padding: 4px;
}

QPushButton.btn-danger:hover {
    background-color: rgba(239, 68, 68, 0.15);
    color: #EF4444;
}

/* ComboBox */
QComboBox {
    background-color: #14151D;
    border: 1px solid #282B38;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F9FAFB;
    font-size: 12px;
}

QComboBox:hover {
    border: 1px solid #34384A;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #181A22;
    border: 1px solid #282B38;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    color: #F9FAFB;
    padding: 4px;
    outline: none;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #282B38;
    border-radius: 8px;
    background-color: #181A22;
    padding: 10px;
}

QTabBar::tab {
    background: transparent;
    color: #6B7280;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 2px;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #F9FAFB;
    border-bottom: 2px solid #2563EB;
}

QTabBar::tab:hover:!selected {
    color: #9CA3AF;
}

/* Scroll Area & Viewports */
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
    background-color: transparent;
    background: transparent;
    border: none;
}

QScrollArea QWidget#qt_scrollarea_viewport {
    background-color: transparent;
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #282B38;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #3B82F6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 0px;
    border: none;
}

/* Log Box */
QPlainTextEdit.log-box {
    background-color: #0F1015;
    border: 1px solid #232531;
    border-radius: 6px;
    color: #9CA3AF;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 6px;
}

/* CheckBox */
QCheckBox {
    color: #D1D5DB;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #282B38;
    border-radius: 3px;
    background-color: #14151D;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #3B82F6;
}
"""
