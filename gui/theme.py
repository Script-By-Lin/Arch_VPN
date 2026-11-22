"""
AuraLink Daylight Light Theme and QSS Stylesheet for AuraLink Linux VPN.
Clean frosted alabaster aesthetic with high-contrast slate typography,
vibrant sky/emerald accents, and smooth interactive controls.
"""

PALETTE = {
    "bg_main": "#F1F5F9",
    "bg_surface": "#FFFFFF",
    "bg_card": "#F8FAFC",
    "bg_card_hover": "#EFF6FF",
    "bg_input": "#FFFFFF",
    "border": "#E2E8F0",
    "border_light": "#CBD5E1",
    "border_focus": "#0284C7",
    "primary": "#0284C7",
    "primary_hover": "#0369A1",
    "primary_active": "#075985",
    "primary_text": "#FFFFFF",
    "success": "#059669",
    "success_bg": "rgba(16, 185, 129, 0.12)",
    "success_border": "rgba(16, 185, 129, 0.35)",
    "warning": "#D97706",
    "warning_bg": "rgba(245, 158, 11, 0.14)",
    "warning_border": "rgba(245, 158, 11, 0.38)",
    "danger": "#DC2626",
    "danger_bg": "rgba(239, 68, 68, 0.10)",
    "danger_border": "rgba(239, 68, 68, 0.35)",
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#64748B",
}

QSS_STYLE = """
/* Global Application Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #F1F5F9;
    color: #0F172A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
}

/* Card & Surface Containers */
QFrame.surface {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
}

QFrame.card {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QFrame.card:hover {
    border: 1px solid #38BDF8;
    background-color: #F0F9FF;
}

/* Typography & Labels */
QLabel {
    color: #0F172A;
}

QLabel.app-title {
    font-size: 15px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: 0.4px;
}

QLabel.app-subtitle {
    font-size: 11px;
    color: #64748B;
    font-family: monospace;
}

QLabel.section-header {
    font-size: 11px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: monospace;
}

/* Status Badges */
QLabel.status-pill {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-connected {
    background-color: #ECFDF5;
    color: #047857;
    border: 1px solid #6EE7B7;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-connecting {
    background-color: #FFFBEB;
    color: #B45309;
    border: 1px solid #FCD34D;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-error {
    background-color: #FEF2F2;
    color: #B91C1C;
    border: 1px solid #FCA5A5;
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

/* Inputs */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 9px 13px;
    color: #0F172A;
    font-size: 12px;
    selection-background-color: #0284C7;
    selection-color: #FFFFFF;
}

QLineEdit:hover {
    border: 1px solid #94A3B8;
}

QLineEdit:focus {
    border: 1.5px solid #0284C7;
    background-color: #FFFFFF;
}

/* Buttons */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    color: #1E293B;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #F0F9FF;
    border: 1px solid #0284C7;
    color: #0369A1;
}

QPushButton:pressed {
    background-color: #E0F2FE;
}

QPushButton.btn-primary {
    background-color: #0284C7;
    color: #FFFFFF;
    border: 1px solid #0284C7;
    font-weight: 700;
}

QPushButton.btn-primary:hover {
    background-color: #0369A1;
    border-color: #0369A1;
    color: #FFFFFF;
}

QPushButton.btn-primary:pressed {
    background-color: #075985;
    color: #FFFFFF;
}

QPushButton.btn-danger {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FECACA;
    font-weight: 700;
}

QPushButton.btn-danger:hover {
    background-color: #DC2626;
    color: #FFFFFF;
    border-color: #DC2626;
}

QPushButton.btn-danger:pressed {
    background-color: #B91C1C;
    color: #FFFFFF;
}

QPushButton.btn-danger:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
    border: 1px solid #E2E8F0;
}

/* Window Control Buttons */
QPushButton.btn-win-control {
    background-color: transparent;
    color: #64748B;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 26px;
    max-height: 26px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton.btn-win-control:hover {
    background-color: #E2E8F0;
    color: #0F172A;
    border: 1px solid #CBD5E1;
}

QPushButton.btn-win-close:hover {
    background-color: #EF4444;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}

/* ComboBox */
QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 7px 12px;
    color: #0F172A;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    min-height: 20px;
}

QComboBox:hover, QComboBox:on {
    border: 1px solid #0284C7;
    background-color: #F8FAFC;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #E2E8F0;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    background-color: #F8FAFC;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #0284C7;
    width: 0px;
    height: 0px;
}

QComboBoxPrivateContainer, QComboBoxPrivateContainer QFrame, QComboBox QFrame {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 0px;
    margin: 0px;
}

QComboBox QAbstractItemView, QListView {
    background-color: #FFFFFF;
    border: none;
    border-radius: 10px;
    color: #0F172A;
    padding: 4px;
    outline: 0px;
    selection-background-color: #E0F2FE;
    selection-color: #0369A1;
    font-size: 12px;
}

QComboBox QAbstractItemView::item, QListView::item {
    min-height: 30px;
    padding: 6px 10px;
    border-radius: 6px;
    color: #1E293B;
}

QComboBox QAbstractItemView::item:hover, QListView::item:hover {
    background-color: #F0F9FF;
    color: #0284C7;
}

QComboBox QAbstractItemView::item:selected, QListView::item:selected {
    background-color: #E0F2FE;
    color: #0369A1;
    font-weight: bold;
}

/* Scroll Area & Scrollbars */
QScrollArea, QScrollArea > QWidget {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #0284C7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Log Box */
QPlainTextEdit.log-box {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    color: #334155;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 8px;
}

/* CheckBox */
QCheckBox {
    color: #334155;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #0284C7;
    border-color: #0284C7;
}

/* Dialogs & Alert Windows */
QDialog {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
}

QMessageBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
}

QMessageBox QLabel {
    color: #0F172A;
    font-size: 12px;
    background-color: transparent;
}

QMessageBox QPushButton {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    color: #0F172A;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 600;
    min-width: 68px;
}

QMessageBox QPushButton:hover {
    background-color: #F0F9FF;
    border: 1px solid #0284C7;
    color: #0369A1;
}

QMessageBox QPushButton:pressed {
    background-color: #E0F2FE;
}
"""
