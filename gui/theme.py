"""
Cyber-Obsidian Theme and QSS Stylesheet for ShadowTun Linux VPN.
Matches the modern, high-contrast dark aesthetic of the ShadowTun web interface.
"""

PALETTE = {
    "bg_main": "#07090E",
    "bg_surface": "#090D16",
    "bg_card": "#0C101A",
    "bg_card_hover": "#131A29",
    "bg_input": "#060A12",
    "border": "#1A2538",
    "border_light": "#2A3B59",
    "border_focus": "#00E5FF",
    "primary": "#00E5FF",
    "primary_hover": "#38BDF8",
    "primary_active": "#0284C7",
    "primary_text": "#07090E",
    "success": "#10B981",
    "success_bg": "rgba(16, 185, 129, 0.15)",
    "success_border": "rgba(16, 185, 129, 0.4)",
    "warning": "#F59E0B",
    "warning_bg": "rgba(245, 158, 11, 0.15)",
    "warning_border": "rgba(245, 158, 11, 0.4)",
    "danger": "#EF4444",
    "danger_bg": "rgba(239, 68, 68, 0.15)",
    "danger_border": "rgba(239, 68, 68, 0.4)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B"
}

QSS_STYLE = """
/* Global Application Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #07090E;
    color: #F8FAFC;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
}

/* Card & Surface Containers */
QFrame.surface {
    background-color: #090D16;
    border: 1px solid #1A2538;
    border-radius: 16px;
}

QFrame.card {
    background-color: #0C101A;
    border: 1px solid #1A2538;
    border-radius: 12px;
}

QFrame.card:hover {
    border: 1px solid #00E5FF;
}

/* Typography & Labels */
QLabel {
    color: #F8FAFC;
}

QLabel.app-title {
    font-size: 15px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 0.5px;
}

QLabel.app-subtitle {
    font-size: 11px;
    color: #64748B;
    font-family: monospace;
}

QLabel.section-header {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: monospace;
}

/* Status Badges */
QLabel.status-pill {
    background-color: #0F172A;
    color: #94A3B8;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-connected {
    background-color: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-connecting {
    background-color: rgba(245, 158, 11, 0.18);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.45);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

QLabel.status-pill-error {
    background-color: rgba(239, 68, 68, 0.18);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.45);
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: monospace;
}

/* Inputs */
QLineEdit {
    background-color: #060A12;
    border: 1px solid #1A2538;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
    font-size: 12px;
    selection-background-color: #00E5FF;
    selection-color: #07090E;
}

QLineEdit:focus {
    border: 1px solid #00E5FF;
    background-color: #090D16;
}

/* Buttons */
QPushButton {
    background-color: #0C101A;
    border: 1px solid #1A2538;
    border-radius: 8px;
    color: #F8FAFC;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #131A29;
    border: 1px solid #00E5FF;
}

QPushButton:pressed {
    background-color: #090D16;
}

QPushButton.btn-primary {
    background-color: #00E5FF;
    color: #07090E;
    border: 1px solid #38BDF8;
    font-weight: 700;
}

QPushButton.btn-primary:hover {
    background-color: #38BDF8;
    border-color: #00E5FF;
}

QPushButton.btn-primary:pressed {
    background-color: #0284C7;
}

QPushButton.btn-danger {
    background-color: rgba(239, 68, 68, 0.12);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.35);
    font-weight: 700;
}

QPushButton.btn-danger:hover {
    background-color: #EF4444;
    color: #FFFFFF;
    border-color: #EF4444;
}

QPushButton.btn-danger:pressed {
    background-color: #DC2626;
    color: #FFFFFF;
}

QPushButton.btn-danger:disabled {
    background-color: #0C101A;
    color: #475569;
    border: 1px solid #1A2538;
}

/* Window Control Buttons */
QPushButton.btn-win-control {
    background-color: transparent;
    color: #64748B;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 0px;
    min-width: 26px;
    max-width: 26px;
    min-height: 24px;
    max-height: 24px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton.btn-win-control:hover {
    background-color: #131A29;
    color: #F8FAFC;
    border: 1px solid #1A2538;
}

QPushButton.btn-win-close:hover {
    background-color: #EF4444;
    color: #FFFFFF;
    border: 1px solid #EF4444;
}

/* ComboBox */
QComboBox {
    background-color: #060A12;
    border: 1px solid #1A2538;
    border-radius: 8px;
    padding: 7px 12px;
    color: #F8FAFC;
    font-size: 12px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    min-height: 20px;
}

QComboBox:hover {
    border: 1px solid #00E5FF;
    background-color: #090D16;
}

QComboBox:on {
    border: 1px solid #00E5FF;
    background-color: #090D16;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 26px;
    border-left: 1px solid #1A2538;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: #0C101A;
}

QComboBox::drop-down:hover {
    background-color: #131A29;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #00E5FF;
    width: 0px;
    height: 0px;
    margin-right: 0px;
}

/* ComboBox Popup Container & List View */
QComboBoxPrivateContainer, QComboBoxPrivateContainer QFrame, QComboBox QFrame {
    background-color: #080C14;
    border: 1px solid #00E5FF;
    border-radius: 8px;
    padding: 0px;
    margin: 0px;
}

QComboBox QAbstractItemView, QListView {
    background-color: #080C14;
    border: none;
    border-radius: 8px;
    color: #F8FAFC;
    padding: 4px;
    outline: 0px;
    selection-background-color: #131A29;
    selection-color: #00E5FF;
    font-size: 12px;
}

QComboBox QAbstractItemView::item, QListView::item {
    min-height: 30px;
    padding: 6px 10px;
    border-radius: 6px;
    color: #E2E8F0;
}

QComboBox QAbstractItemView::item:hover, QListView::item:hover {
    background-color: #131A29;
    color: #00E5FF;
}

QComboBox QAbstractItemView::item:selected, QListView::item:selected {
    background-color: rgba(0, 229, 255, 0.18);
    color: #00E5FF;
    font-weight: bold;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #1A2538;
    border-radius: 12px;
    background-color: #090D16;
    padding: 10px;
}

QTabBar::tab {
    background: transparent;
    color: #64748B;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-family: monospace;
}

QTabBar::tab:selected {
    color: #00E5FF;
    border-bottom: 2px solid #00E5FF;
}

QTabBar::tab:hover:!selected {
    color: #94A3B8;
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
    background: #1A2538;
    min-height: 24px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #00E5FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Log Box */
QPlainTextEdit.log-box {
    background-color: #060A12;
    border: 1px solid #1A2538;
    border-radius: 8px;
    color: #94A3B8;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    padding: 8px;
}

/* CheckBox */
QCheckBox {
    color: #D1D5DB;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #1A2538;
    border-radius: 4px;
    background-color: #060A12;
}

QCheckBox::indicator:checked {
    background-color: #00E5FF;
    border-color: #00E5FF;
}
"""
