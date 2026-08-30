#!/usr/bin/env python3
"""
Cyber-Obsidian Desktop GUI for ShadowTun Linux VPN.
Built with PyQt5, featuring a glowing circular connect button,
live download/upload speedometers, quick node switcher, DNS selector,
real-time log stream, and complete server management.
"""

import os
import sys
import time
import math
import signal
import threading
from typing import Optional, Dict, Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize, QEvent, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen, QIcon, QPixmap, QRadialGradient, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QTabWidget,
    QPlainTextEdit, QComboBox, QCheckBox, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QSizePolicy, QSplitter, QListView
)

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import (
    VPNService,
    ConfigManager,
    ConfigError,
    StatsMonitor,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_DISCONNECTING,
    STATE_ERROR
)
from gui.theme import QSS_STYLE, PALETTE


def sigint_handler(signum, frame):
    """Handles Ctrl+C (SIGINT) cleanly from terminal."""
    print("\n[ShadowTun] Terminating upon Ctrl+C...")
    app_inst = QApplication.instance()
    if app_inst and hasattr(app_inst, "_main_win"):
        win = app_inst._main_win
        if win and hasattr(win, "service") and win.service.state == STATE_CONNECTED:
            try:
                win.service.disconnect()
            except Exception:
                pass
    QApplication.quit()
    sys.exit(0)


class BridgeSignals(QObject):
    state_changed = pyqtSignal(str, dict)
    stats_updated = pyqtSignal(dict)
    log_updated = pyqtSignal(list)
    ping_result = pyqtSignal(str, int)
    log_message = pyqtSignal(str)


class CircularConnectButton(QPushButton):
    """
    High-fidelity circular connect button with glowing concentric rings,
    state-aware radial gradients, and dynamic power icon.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(170, 170)
        self.setCursor(Qt.PointingHandCursor)
        self._state = "DISCONNECTED"
        self._hover = False
        self._pulse_phase = 0.0
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(45)

    def set_vpn_state(self, state: str):
        self._state = state
        self.update()

    def _on_tick(self):
        if self._state in ("CONNECTED", "CONNECTING"):
            self._pulse_phase += 0.08
            self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2.0 - 10.0

        if self._state == "CONNECTED":
            grad_start = QColor("#0e3b2e")
            grad_end = QColor("#041712")
            border_color = QColor("#10B981")
            icon_color = QColor("#10B981")
            text_color = QColor("#FFFFFF")
            sub_text = "CLICK TO DISCONNECT"
        elif self._state == "CONNECTING":
            grad_start = QColor("#3b2a0e")
            grad_end = QColor("#1a1205")
            border_color = QColor("#F59E0B")
            icon_color = QColor("#F59E0B")
            text_color = QColor("#FBBF24")
            sub_text = "CONNECTING..."
        else:
            grad_start = QColor("#141b2d")
            grad_end = QColor("#080b13")
            border_color = QColor("#00E5FF") if self._hover else QColor("#1E293B")
            icon_color = QColor("#00E5FF")
            text_color = QColor("#E2E8F0")
            sub_text = "CLICK TO CONNECT"

        # Concentric glowing pulse waves when active
        if self._state in ("CONNECTED", "CONNECTING"):
            pulse = (math.sin(self._pulse_phase) + 1.0) / 2.0
            pulse_radius = radius + 3.0 + pulse * 6.0
            alpha = int(70 * (1.0 - pulse * 0.7))
            
            p_color = QColor(16, 185, 129, alpha) if self._state == "CONNECTED" else QColor(245, 158, 11, alpha)
            painter.setPen(QPen(p_color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, int(pulse_radius), int(pulse_radius))

        # Main Radial Gradient Circle
        radial = QRadialGradient(center, radius)
        radial.setColorAt(0.0, grad_start)
        radial.setColorAt(1.0, grad_end)
        painter.setBrush(QBrush(radial))
        painter.setPen(QPen(border_color, 2.5))
        painter.drawEllipse(center, int(radius), int(radius))

        # Draw Power Icon Symbol
        icon_cx = center.x()
        icon_cy = center.y() - 14
        icon_r = 17
        painter.setPen(QPen(icon_color, 3.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        # Power arc
        painter.drawArc(
            int(icon_cx - icon_r), 
            int(icon_cy - icon_r), 
            int(icon_r * 2), 
            int(icon_r * 2), 
            45 * 16, 
            270 * 16
        )
        # Power vertical line
        painter.drawLine(int(icon_cx), int(icon_cy - 21), int(icon_cx), int(icon_cy - 4))

        # Status text below icon
        painter.setPen(text_color)
        font = QFont("-apple-system", 8, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        painter.setFont(font)
        text_rect = rect.adjusted(0, int(center.y() + 20), 0, -10)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, sub_text)


class ModernDropdown(QPushButton):
    """
    Sleek Cyber-Obsidian Dropdown Selector.
    Uses a custom translucent QMenu to completely eliminate OS-level white box artifacts.
    """
    currentIndexChanged = pyqtSignal(int)

    def __init__(self, placeholder="Select...", parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._items = []
        self._current_index = -1
        self._placeholder = placeholder
        self.setText(f"{placeholder}  ▾")

        self.menu = QMenu(self)
        self.menu.setObjectName("ModernDropdownMenu")
        self.menu.setAttribute(Qt.WA_TranslucentBackground, True)
        self.menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.menu.setStyleSheet("""
            QMenu#ModernDropdownMenu {
                background-color: #080C14;
                border: 1px solid #00E5FF;
                border-radius: 8px;
                padding: 4px;
                color: #F8FAFC;
            }
            QMenu#ModernDropdownMenu::item {
                background-color: transparent;
                padding: 8px 14px;
                border-radius: 6px;
                color: #E2E8F0;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            }
            QMenu#ModernDropdownMenu::item:selected {
                background-color: rgba(0, 229, 255, 0.18);
                color: #00E5FF;
                font-weight: bold;
            }
        """)
        self.setMenu(self.menu)
        self.setStyleSheet("""
            QPushButton {
                background-color: #060A12;
                border: 1px solid #1A2538;
                border-radius: 8px;
                padding: 9px 12px;
                color: #F8FAFC;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
                text-align: left;
            }
            QPushButton:hover {
                border: 1px solid #00E5FF;
                background-color: #090D16;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)

    def addItem(self, text, data=None):
        idx = len(self._items)
        self._items.append((text, data))
        act = QAction(text, self.menu)
        act.triggered.connect(lambda checked, i=idx: self.setCurrentIndex(i))
        self.menu.addAction(act)
        if self._current_index == -1:
            self.setCurrentIndex(0)

    def addItems(self, texts):
        for t in texts:
            self.addItem(t, t)

    def clear(self):
        self._items = []
        self._current_index = -1
        self.menu.clear()
        self.setText(f"{self._placeholder}  ▾")

    def count(self):
        return len(self._items)

    def currentIndex(self):
        return self._current_index

    def currentText(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index][0]
        return ""

    def itemData(self, index):
        if 0 <= index < len(self._items):
            return self._items[index][1]
        return None

    def setCurrentIndex(self, index):
        if 0 <= index < len(self._items):
            self._current_index = index
            self.setText(f"{self._items[index][0]}  ▾")
            self.currentIndexChanged.emit(index)


class ProfileRowWidget(QFrame):
    """Clean card representing a single server profile."""
    def __init__(self, profile: dict, is_active: bool, is_connected: bool, on_connect, on_delete, on_ping, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.is_active = is_active
        self.is_connected = is_connected
        self.on_connect_callback = on_connect
        self.on_delete_callback = on_delete
        self.on_ping_callback = on_ping
        self.setObjectName("ServerCard")
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame#ServerCard {
                background-color: #0C101A;
                border: 1px solid #1A2538;
                border-radius: 8px;
            }
            QFrame#ServerCard:hover {
                border: 1px solid #00E5FF;
                background-color: #111726;
            }
        """)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(10, 8, 10, 8)
        main_vbox.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        self.dot = QLabel("●")
        dot_color = "#10B981" if self.is_connected else ("#00E5FF" if self.is_active else "#64748B")
        self.dot.setStyleSheet(f"color: {dot_color}; font-size: 11px;")
        top_row.addWidget(self.dot)

        self.name_label = QLabel(self.profile.get("name", "Unnamed Server"))
        self.name_label.setStyleSheet("font-weight: 700; font-size: 12px; color: #FFFFFF;")
        top_row.addWidget(self.name_label, 1)

        self.ping_label = QLabel("...")
        self.ping_label.setStyleSheet("background-color: #060A12; color: #64748B; border: 1px solid #1A2538; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; font-family: monospace;")
        top_row.addWidget(self.ping_label)

        self.btn_select = QPushButton()
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.update_action_button()
        self.btn_select.clicked.connect(lambda: self.on_connect_callback(self.profile))
        top_row.addWidget(self.btn_select)

        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(20, 20)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("QPushButton { background-color: transparent; color: #64748B; border: none; border-radius: 3px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; }")
        btn_delete.clicked.connect(lambda: self.on_delete_callback(self.profile))
        top_row.addWidget(btn_delete)

        main_vbox.addLayout(top_row)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(4)

        server_str = f"{self.profile.get('server')}:{self.profile.get('server_port')}  •  {self.profile.get('method')}"
        if self.profile.get("prefix"):
            server_str += "  •  Anti-DPI"
        sub_label = QLabel(server_str)
        sub_label.setStyleSheet("font-size: 10px; color: #64748B; font-family: monospace;")
        bottom_row.addWidget(sub_label, 1)

        main_vbox.addLayout(bottom_row)

    def update_action_button(self):
        if self.is_connected:
            self.btn_select.setText("Connected")
            self.btn_select.setStyleSheet("background-color: rgba(16, 185, 129, 0.18); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 700;")
        elif self.is_active:
            self.btn_select.setText("Selected")
            self.btn_select.setStyleSheet("background-color: rgba(0, 229, 255, 0.18); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.4); border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 700;")
        else:
            self.btn_select.setText("Switch")
            self.btn_select.setStyleSheet("background-color: #0C101A; color: #94A3B8; border: 1px solid #1A2538; border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 600;")

    def set_ping(self, ms: Optional[int]):
        if ms is not None and ms >= 0:
            color = "#10B981" if ms < 150 else ("#F59E0B" if ms < 350 else "#EF4444")
            self.ping_label.setText(f"{ms}ms")
            self.ping_label.setStyleSheet(f"background-color: #060A12; color: {color}; border: 1px solid #1A2538; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700; font-family: monospace;")
        else:
            self.ping_label.setText("timeout")
            self.ping_label.setStyleSheet("background-color: #060A12; color: #EF4444; border: 1px solid #1A2538; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-family: monospace;")


def get_app_icon() -> QIcon:
    """Finds or creates a guaranteed non-null QIcon for Window and Tray."""
    possible_paths = [
        os.path.join(BASE_DIR, "gui", "assets", "icon.png"),
        os.path.join(BASE_DIR, "gui", "assets", "icon.svg"),
        "/opt/shadowtun/gui/assets/icon.png",
        "/opt/shadowtun/gui/assets/icon.svg",
        "/usr/share/icons/hicolor/256x256/apps/shadowtun.png",
        "/usr/share/icons/hicolor/scalable/apps/shadowtun.svg"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            icon = QIcon(p)
            if not icon.isNull():
                return icon

    theme_icon = QIcon.fromTheme("network-vpn")
    if not theme_icon.isNull():
        return theme_icon

    pix = QPixmap(32, 32)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor("#00E5FF")))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(2, 2, 28, 28, 8, 8)
    painter.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.service = VPNService()
        self.signals = BridgeSignals()
        self.signals.state_changed.connect(self.on_state_changed)
        self.signals.stats_updated.connect(self.on_stats_updated)
        self.signals.log_updated.connect(self.on_log_updated)
        self.signals.ping_result.connect(self.on_ping_result)
        self.signals.log_message.connect(self._on_log_message_received)

        self.service.add_listener(self._service_listener)
        self.card_widgets: Dict[str, ProfileRowWidget] = {}
        self.updating_combo = False

        self.init_ui()
        self.init_tray()
        self.init_timers()

        self.update_profiles_list()
        self.refresh_ui_state()
        self.trigger_all_pings()

    def _service_listener(self, event_type: str, data: dict):
        self.signals.state_changed.emit(event_type, data)

    def init_ui(self):
        self.setWindowTitle("ShadowTun GUI")
        self.setWindowIcon(get_app_icon())
        self.resize(780, 520)
        self.setMinimumSize(700, 480)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet(QSS_STYLE)

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_vbox = QVBoxLayout(central)
        main_vbox.setContentsMargins(16, 14, 16, 14)
        main_vbox.setSpacing(12)

        # 1. TOP HEADER BAR
        header = QHBoxLayout()
        header.setSpacing(10)

        # Window Dots
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(6)
        for color in ("#EF4444", "#F59E0B", "#10B981"):
            dot = QLabel()
            dot.setFixedSize(11, 11)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
            dots_layout.addWidget(dot)
        header.addLayout(dots_layout)

        lbl_app_name = QLabel("ShadowTun GUI")
        lbl_app_name.setStyleSheet("font-size: 13px; font-weight: 800; color: #FFFFFF; font-family: monospace; margin-left: 6px;")
        header.addWidget(lbl_app_name)

        header.addStretch(1)

        # Status Pill Badge
        self.status_pill = QLabel("DISCONNECTED")
        self.status_pill.setProperty("class", "status-pill")
        header.addWidget(self.status_pill)

        # Window Action Controls
        win_controls = QHBoxLayout()
        win_controls.setSpacing(4)

        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setProperty("class", "btn-win-control")
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.clicked.connect(self.minimize_window)
        win_controls.addWidget(self.btn_minimize)

        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setProperty("class", "btn-win-control")
        self.btn_maximize.setToolTip("Maximize / Restore")
        self.btn_maximize.setCursor(Qt.PointingHandCursor)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        win_controls.addWidget(self.btn_maximize)

        self.btn_close = QPushButton("✕")
        self.btn_close.setProperty("class", "btn-win-control btn-win-close")
        self.btn_close.setToolTip("Close")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        win_controls.addWidget(self.btn_close)

        header.addLayout(win_controls)
        main_vbox.addLayout(header)

        # 2. MAIN SPLIT CONTENT
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        # LEFT PANEL: Virtual Client GUI Window
        left_panel = QFrame()
        left_panel.setProperty("class", "surface")
        left_vbox = QVBoxLayout(left_panel)
        left_vbox.setContentsMargins(18, 18, 18, 18)
        left_vbox.setSpacing(14)

        # Central Button Wrapper
        btn_wrapper = QVBoxLayout()
        btn_wrapper.setAlignment(Qt.AlignCenter)
        
        self.btn_circular = CircularConnectButton()
        self.btn_circular.clicked.connect(self.on_connect_toggle)
        btn_wrapper.addWidget(self.btn_circular, 0, Qt.AlignCenter)

        self.lbl_route_status = QLabel("System using standard physical route")
        self.lbl_route_status.setAlignment(Qt.AlignCenter)
        self.lbl_route_status.setStyleSheet("font-size: 11px; color: #64748B; font-family: monospace; margin-top: 8px;")
        btn_wrapper.addWidget(self.lbl_route_status, 0, Qt.AlignCenter)

        left_vbox.addLayout(btn_wrapper, 1)

        # Bottom Speed Tiles Split Box
        speed_grid = QHBoxLayout()
        speed_grid.setSpacing(10)

        # Download Speed Tile
        card_down = QFrame()
        card_down.setStyleSheet("background-color: #060A12; border: 1px solid #1A2538; border-radius: 12px;")
        cd_layout = QHBoxLayout(card_down)
        cd_layout.setContentsMargins(12, 10, 12, 10)
        cd_layout.setSpacing(10)

        badge_down = QLabel("↓")
        badge_down.setAlignment(Qt.AlignCenter)
        badge_down.setFixedSize(32, 32)
        badge_down.setStyleSheet("background-color: rgba(0, 229, 255, 0.15); color: #00E5FF; border-radius: 8px; font-weight: bold; font-size: 15px;")
        cd_layout.addWidget(badge_down)

        down_info = QVBoxLayout()
        down_info.setSpacing(1)
        lbl_d_tag = QLabel("DOWNLOAD SPEED")
        lbl_d_tag.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px;")
        down_info.addWidget(lbl_d_tag)

        self.lbl_speed_down = QLabel("0.0 MB/s")
        self.lbl_speed_down.setStyleSheet("font-size: 15px; font-weight: 800; color: #FFFFFF; font-family: monospace;")
        down_info.addWidget(self.lbl_speed_down)
        cd_layout.addLayout(down_info)

        speed_grid.addWidget(card_down)

        # Upload Speed Tile
        card_up = QFrame()
        card_up.setStyleSheet("background-color: #060A12; border: 1px solid #1A2538; border-radius: 12px;")
        cu_layout = QHBoxLayout(card_up)
        cu_layout.setContentsMargins(12, 10, 12, 10)
        cu_layout.setSpacing(10)

        badge_up = QLabel("↑")
        badge_up.setAlignment(Qt.AlignCenter)
        badge_up.setFixedSize(32, 32)
        badge_up.setStyleSheet("background-color: rgba(16, 185, 129, 0.15); color: #10B981; border-radius: 8px; font-weight: bold; font-size: 15px;")
        cu_layout.addWidget(badge_up)

        up_info = QVBoxLayout()
        up_info.setSpacing(1)
        lbl_u_tag = QLabel("UPLOAD SPEED")
        lbl_u_tag.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px;")
        up_info.addWidget(lbl_u_tag)

        self.lbl_speed_up = QLabel("0.0 MB/s")
        self.lbl_speed_up.setStyleSheet("font-size: 15px; font-weight: 800; color: #FFFFFF; font-family: monospace;")
        up_info.addWidget(self.lbl_speed_up)
        cu_layout.addLayout(up_info)

        speed_grid.addWidget(card_up)

        left_vbox.addLayout(speed_grid)
        content_layout.addWidget(left_panel, 7)

        # RIGHT PANEL: Config Controls & Log Stream
        right_panel = QFrame()
        right_panel.setProperty("class", "surface")
        right_vbox = QVBoxLayout(right_panel)
        right_vbox.setContentsMargins(14, 14, 14, 14)
        right_vbox.setSpacing(12)

        # 1. Active Subscription Node Box
        node_card = QFrame()
        node_card.setStyleSheet("background-color: #0C101A; border: 1px solid #1A2538; border-radius: 10px;")
        nc_vbox = QVBoxLayout(node_card)
        nc_vbox.setContentsMargins(10, 10, 10, 10)
        nc_vbox.setSpacing(8)

        node_header = QHBoxLayout()
        lbl_node_title = QLabel("ACTIVE SUBSCRIPTION NODE")
        lbl_node_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #94A3B8; font-family: monospace; letter-spacing: 0.5px;")
        node_header.addWidget(lbl_node_title)
        node_header.addStretch(1)

        self.btn_ping_refresh = QPushButton("⟳ Ping")
        self.btn_ping_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_ping_refresh.setStyleSheet("background-color: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 700; font-family: monospace;")
        self.btn_ping_refresh.clicked.connect(self.trigger_all_pings)
        node_header.addWidget(self.btn_ping_refresh)
        nc_vbox.addLayout(node_header)

        self.combo_servers = ModernDropdown("Select Server...")
        self.combo_servers.currentIndexChanged.connect(self.on_server_dropdown_changed)
        nc_vbox.addWidget(self.combo_servers)

        # DNS Picker
        lbl_dns_title = QLabel("DNS UPSTREAM RESOLVER")
        lbl_dns_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px; margin-top: 4px;")
        nc_vbox.addWidget(lbl_dns_title)

        self.combo_dns = ModernDropdown("Select DNS...")
        self.combo_dns.addItems([
            "Cloudflare (1.1.1.1 / 1.0.0.1)",
            "Google (8.8.8.8 / 8.8.4.4)",
            "Quad9 (9.9.9.9 / 149.112.112.112)",
            "AdGuard (94.140.14.14 / 94.140.15.15)"
        ])
        self.combo_dns.currentIndexChanged.connect(self.on_dns_changed)
        nc_vbox.addWidget(self.combo_dns)

        right_vbox.addWidget(node_card)

        # 2. Real-Time Log Stream Box
        log_card = QFrame()
        log_card.setStyleSheet("background-color: #060A12; border: 1px solid #1A2538; border-radius: 10px;")
        lc_vbox = QVBoxLayout(log_card)
        lc_vbox.setContentsMargins(10, 10, 10, 10)
        lc_vbox.setSpacing(6)

        log_header = QHBoxLayout()
        lbl_log_title = QLabel(">_ Real-Time Log Stream")
        lbl_log_title.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #CBD5E1; font-family: monospace;")
        log_header.addWidget(lbl_log_title)
        log_header.addStretch(1)

        lbl_live_badge = QLabel("● LIVE")
        lbl_live_badge.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #10B981; font-family: monospace;")
        log_header.addWidget(lbl_live_badge)
        lc_vbox.addLayout(log_header)

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("background-color: transparent; border: none; color: #94A3B8; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 10.5px; line-height: 1.4;")
        lc_vbox.addWidget(self.txt_logs, 1)

        log_footer = QHBoxLayout()
        lbl_proc = QLabel("Direct /proc/net/dev telemetry")
        lbl_proc.setStyleSheet("font-size: 9.5px; color: #64748B; font-family: monospace;")
        log_footer.addWidget(lbl_proc)
        log_footer.addStretch(1)

        lbl_ep = QLabel("127.0.0.1:1080")
        lbl_ep.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #00E5FF; font-family: monospace;")
        log_footer.addWidget(lbl_ep)
        lc_vbox.addLayout(log_footer)

        right_vbox.addWidget(log_card, 1)

        content_layout.addWidget(right_panel, 5)
        main_vbox.addLayout(content_layout, 1)

        # Bottom Management Row (Import / Server List / Settings modal/drawer)
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(8)

        self.input_import_key = QLineEdit()
        self.input_import_key.setPlaceholderText("Paste ssconf:// URL or ss:// key...")
        mgmt_row.addWidget(self.input_import_key, 1)

        btn_quick_import = QPushButton("Import Node")
        btn_quick_import.setProperty("class", "btn-primary")
        btn_quick_import.setCursor(Qt.PointingHandCursor)
        btn_quick_import.clicked.connect(self.on_quick_import)
        mgmt_row.addWidget(btn_quick_import)

        main_vbox.addLayout(mgmt_row)

    def on_dns_changed(self):
        dns_choice = self.combo_dns.currentText()
        self.service.config_mgr.set_setting("dns_server", dns_choice)
        self.append_ui_log(f"[DNS] Resolver set to {dns_choice.split(' ')[0]}")

    def on_quick_import(self):
        raw = self.input_import_key.text().strip()
        if not raw:
            return
        try:
            profile = self.service.config_mgr.parse_key(raw)
            saved = self.service.config_mgr.add_or_update_profile(profile)
            self.input_import_key.clear()
            self.update_profiles_list()
            self.append_ui_log(f"[IMPORT] Imported profile '{saved.get('name')}' successfully.")
            self.trigger_all_pings()
        except ConfigError as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def append_ui_log(self, msg: str):
        self.signals.log_message.emit(msg)

    def _on_log_message_received(self, msg: str):
        timestamp = time.strftime("%I:%M:%S %p")
        self.txt_logs.appendPlainText(f"[{timestamp}] {msg}")
        self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def on_server_dropdown_changed(self, index: int):
        if self.updating_combo or index < 0:
            return
        p_id = self.combo_servers.itemData(index)
        if p_id:
            self.service.config_mgr.set_active_profile(p_id)
            self.refresh_ui_state()

    def update_profiles_list(self):
        self.updating_combo = True
        self.combo_servers.clear()

        profiles = self.service.config_mgr.get_profiles()
        active_id = self.service.config_mgr.get_active_profile_id()
        selected_index = 0

        for idx, p in enumerate(profiles):
            p_id = p.get("id", "")
            p_name = p.get("name", "Unnamed")
            self.combo_servers.addItem(f"{p_name} ({p.get('server')})", p_id)
            if p_id == active_id:
                selected_index = idx

        if profiles:
            self.combo_servers.setCurrentIndex(selected_index)
        self.updating_combo = False

    def on_connect_toggle(self):
        state = self.service.state
        if state == STATE_CONNECTED:
            self.append_ui_log("[DISCONNECT] Terminating tun0 interface...")
            threading.Thread(target=self.service.disconnect, daemon=True).start()
        elif state == STATE_DISCONNECTED:
            profiles = self.service.config_mgr.get_profiles()
            if not profiles:
                QMessageBox.warning(self, "No Servers", "Please import a Shadowsocks profile first.")
                return
            self.append_ui_log("[CONNECT] Initializing full-tunnel connection...")
            threading.Thread(target=self.service.connect, daemon=True).start()

    def on_state_changed(self, event_type: str, data: dict):
        self.refresh_ui_state()

    def refresh_ui_state(self):
        state = self.service.state
        active_prof = self.service.config_mgr.get_active_profile()
        prof_name = active_prof.get("name", "No Server") if active_prof else "No Server"

        if state == STATE_CONNECTED:
            self.status_pill.setText("CONNECTED")
            self.status_pill.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.2); 
                color: #10B981; 
                border: 1px solid rgba(16, 185, 129, 0.4); 
                border-radius: 12px; 
                padding: 3px 10px; 
                font-weight: 700; 
                font-family: monospace;
            """)
            self.btn_circular.set_vpn_state("CONNECTED")
            self.lbl_route_status.setText(f"Virtual tun0 adapter active • 100% full-tunnel routed via {prof_name}")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #10B981; font-family: monospace; margin-top: 8px;")
        elif state == STATE_CONNECTING:
            self.status_pill.setText("CONNECTING...")
            self.status_pill.setStyleSheet("""
                background-color: rgba(245, 158, 11, 0.2); 
                color: #F59E0B; 
                border: 1px solid rgba(245, 158, 11, 0.4); 
                border-radius: 12px; 
                padding: 3px 10px; 
                font-weight: 700; 
                font-family: monospace;
            """)
            self.btn_circular.set_vpn_state("CONNECTING")
            self.lbl_route_status.setText("Probing remote proxy & provisioning tun0...")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #F59E0B; font-family: monospace; margin-top: 8px;")
        else:
            self.status_pill.setText("DISCONNECTED")
            self.status_pill.setStyleSheet("""
                background-color: #0F172A; 
                color: #94A3B8; 
                border: 1px solid #1E293B; 
                border-radius: 12px; 
                padding: 3px 10px; 
                font-weight: 700; 
                font-family: monospace;
            """)
            self.btn_circular.set_vpn_state("DISCONNECTED")
            self.lbl_route_status.setText("System using standard physical route")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #64748B; font-family: monospace; margin-top: 8px;")
            self.lbl_speed_down.setText("0.0 MB/s")
            self.lbl_speed_up.setText("0.0 MB/s")

    def on_stats_updated(self, stats: dict):
        if self.service.state == STATE_CONNECTED:
            rx_bytes_sec = stats.get("rx_rate", 0.0)
            tx_bytes_sec = stats.get("tx_rate", 0.0)
            
            rx_mb = rx_bytes_sec / (1024 * 1024)
            tx_mb = tx_bytes_sec / (1024 * 1024)
            
            self.lbl_speed_down.setText(f"{rx_mb:.1f} MB/s")
            self.lbl_speed_up.setText(f"{tx_mb:.1f} MB/s")

    def on_log_updated(self, logs: list):
        if logs:
            self.txt_logs.clear()
            for l in logs[-25:]:
                self.txt_logs.appendPlainText(l)
            self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def on_ping_result(self, p_id: str, ms: int):
        self.btn_ping_refresh.setText(f"⟳ Ping: {ms}ms" if ms >= 0 else "⟳ Timeout")

    def trigger_all_pings(self):
        active = self.service.config_mgr.get_active_profile()
        if not active:
            return
        
        self.btn_ping_refresh.setText("⟳ Pinging...")
        
        def _worker():
            host = active.get("server")
            port = int(active.get("server_port", 8388))
            ms = self.service.stats_monitor.measure_ping(host, port)
            self.signals.ping_result.emit(active.get("id"), ms)
            self.append_ui_log(f"[PING] Response from {active.get('name')}: {ms}ms" if ms >= 0 else f"[PING] Timeout reaching {active.get('name')}")

        threading.Thread(target=_worker, daemon=True).start()

    def init_timers(self):
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._poll_stats)
        self.stats_timer.start(1000)

    def _poll_stats(self):
        if self.service.state == STATE_CONNECTED:
            st = self.service.stats_monitor.get_stats()
            self.signals.stats_updated.emit(st)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_app_icon())
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        tray_menu = QMenu()
        act_show = QAction("Show ShadowTun", self)
        act_show.triggered.connect(self.show_window)
        tray_menu.addAction(act_show)

        act_toggle = QAction("Toggle Connection", self)
        act_toggle.triggered.connect(self.on_connect_toggle)
        tray_menu.addAction(act_toggle)

        tray_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(QApplication.quit)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.hide()
        super().changeEvent(event)

    def on_tray_activated(self, reason):
        if self.isHidden() or self.isMinimized() or not self.isVisible():
            self.show_window()
        else:
            self.minimize_window()

    def minimize_window(self):
        self.showMinimized()
        self.hide()
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage("ShadowTun GUI", "Minimized to system tray. Click tray icon to restore.", QSystemTrayIcon.Information, 1500)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            if hasattr(self, 'btn_maximize'):
                self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            if hasattr(self, 'btn_maximize'):
                self.btn_maximize.setText("❐")

    def show_window(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()


def launch_gui():
    """Entry point for launching the PyQt5 Desktop GUI."""
    signal.signal(signal.SIGINT, sigint_handler)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setApplicationName("ShadowTun")
    app.setWindowIcon(get_app_icon())

    win = MainWindow()
    app._main_win = win
    win.show()

    return app.exec_()


def main():
    sys.exit(launch_gui())


if __name__ == "__main__":
    main()
