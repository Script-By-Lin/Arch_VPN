"""
Theme and QSS Stylesheet for ShadowTun Linux VPN.
Features a modern dark theme with sleek neon cyan/purple accents,
glassmorphic panels, and polished UI elements.
"""

DARK_PALETTE = {
    "bg_main": "#0F111A",
    "bg_card": "#181B26",
    "bg_card_hover": "#222636",
    "bg_input": "#12141F",
    "border": "#282D42",
    "border_focus": "#00E5FF",
    "primary": "#00E5FF",
    "primary_hover": "#33EBFF",
    "primary_dark": "#009BB0",
    "accent_purple": "#7C4DFF",
    "accent_green": "#00E676",
    "accent_red": "#FF5252",
    "accent_yellow": "#FFD600",
    "text_primary": "#FFFFFF",
    "text_secondary": "#8F9CAE",
    "text_muted": "#576275"
}

QSS_STYLE = """
/* Global Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #0F111A;
    color: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Card Containers */
QFrame.card {
    background-color: #181B26;
    border: 1px solid #282D42;
    border-radius: 12px;
}

QFrame.card:hover {
    border: 1px solid #3B4261;
}

/* Text & Labels */
QLabel {
    color: #FFFFFF;
}

QLabel.title {
    font-size: 20px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel.subtitle {
    font-size: 13px;
    color: #8F9CAE;
}

QLabel.badge {
    background-color: #222636;
    color: #00E5FF;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.badge-green {
    background-color: rgba(0, 230, 118, 0.15);
    color: #00E676;
    border: 1px solid rgba(0, 230, 118, 0.3);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.badge-red {
    background-color: rgba(255, 82, 82, 0.15);
    color: #FF5252;
    border: 1px solid rgba(255, 82, 82, 0.3);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Inputs */
QLineEdit {
    background-color: #12141F;
    border: 1px solid #282D42;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
    font-size: 13px;
    selection-background-color: #00E5FF;
    selection-color: #000000;
}

QLineEdit:focus {
    border: 1px solid #00E5FF;
    background-color: #161927;
}

/* Buttons */
QPushButton {
    background-color: #222636;
    border: 1px solid #282D42;
    border-radius: 8px;
    color: #FFFFFF;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2D3349;
    border: 1px solid #3B4261;
}

QPushButton:pressed {
    background-color: #1B1E2C;
}

QPushButton.primary {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C9FF, stop:1 #92FE9D);
    color: #0F111A;
    border: none;
    border-radius: 8px;
    font-weight: bold;
}

QPushButton.primary:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1AD0FF, stop:1 #A5FFAF);
}

QPushButton.action-connect {
    background-color: #00E676;
    color: #0F111A;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
}

QPushButton.action-connect:hover {
    background-color: #33EB91;
}

QPushButton.action-delete {
    background-color: rgba(255, 82, 82, 0.15);
    color: #FF5252;
    border: 1px solid rgba(255, 82, 82, 0.3);
    border-radius: 6px;
    padding: 4px 8px;
}

QPushButton.action-delete:hover {
    background-color: rgba(255, 82, 82, 0.3);
}

/* Scroll Area & Lists */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #12141F;
    width: 6px;
    border-radius: 3px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #282D42;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #00E5FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #282D42;
    border-radius: 10px;
    background-color: #181B26;
    padding: 10px;
}

QTabBar::tab {
    background: transparent;
    color: #8F9CAE;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #00E5FF;
    border-bottom: 2px solid #00E5FF;
}

QTabBar::tab:hover:!selected {
    color: #FFFFFF;
}

/* Log Box */
QPlainTextEdit.log-box {
    background-color: #0B0D13;
    border: 1px solid #202434;
    border-radius: 8px;
    color: #A0B0C5;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12px;
    padding: 8px;
}

/* Combo Box */
QComboBox {
    background-color: #12141F;
    border: 1px solid #282D42;
    border-radius: 8px;
    padding: 6px 12px;
    color: #FFFFFF;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #3B4261;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #181B26;
    border: 1px solid #282D42;
    selection-background-color: #2D3349;
    color: #FFFFFF;
    padding: 4px;
}
"""
