#!/usr/bin/env python3
"""
Modern Dark-Mode GUI for ShadowTun Linux VPN.
Built with PyQt5, featuring animated glowing connect button,
live speed graphs, profile manager, and settings.
"""

import os
import sys
import time
import threading
from typing import Optional, Dict, Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QTabWidget,
    QPlainTextEdit, QComboBox, QCheckBox, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QSpacerItem, QSizePolicy
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
from gui.theme import QSS_STYLE, DARK_PALETTE


class BridgeSignals(QObject):
    state_changed = pyqtSignal(str, dict)
    stats_updated = pyqtSignal(dict)
    log_updated = pyqtSignal(list)
    ping_result = pyqtSignal(str, int)


class CircularConnectButton(QPushButton):
    """Custom glowing circular connect button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self.setCursor(Qt.PointingHandCursor)
        self.state = STATE_DISCONNECTED
        self.pulse_angle = 0

    def set_state(self, state: str):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = rect.width() / 2 - 8

        # Colors based on state
        if self.state == STATE_CONNECTED:
            ring_color = QColor(DARK_PALETTE["accent_green"])
            bg_grad_start = QColor("#00E676")
            bg_grad_end = QColor("#008940")
            status_text = "CONNECTED"
            action_text = "STOP"
        elif self.state in (STATE_CONNECTING, STATE_DISCONNECTING):
            ring_color = QColor(DARK_PALETTE["accent_yellow"])
            bg_grad_start = QColor("#FFD600")
            bg_grad_end = QColor("#FF9100")
            status_text = "CONNECTING..." if self.state == STATE_CONNECTING else "STOPPING..."
            action_text = "WAIT"
        elif self.state == STATE_ERROR:
            ring_color = QColor(DARK_PALETTE["accent_red"])
            bg_grad_start = QColor("#FF5252")
            bg_grad_end = QColor("#B71C1C")
            status_text = "ERROR"
            action_text = "RETRY"
        else:
            ring_color = QColor(DARK_PALETTE["primary"])
            bg_grad_start = QColor("#00C9FF")
            bg_grad_end = QColor("#0072FF")
            status_text = "DISCONNECTED"
            action_text = "CONNECT"

        # Outer Glow Ring
        pen = QPen(ring_color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius + 2, radius + 2)

        # Inner Gradient Circle
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, bg_grad_start)
        gradient.setColorAt(1, bg_grad_end)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, radius - 4, radius - 4)

        # Center Power Icon
        painter.setPen(QPen(QColor("#FFFFFF"), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(int(center.x() - 16), int(center.y() - 20), 32, 32, 45 * 16, 270 * 16)
        painter.drawLine(int(center.x()), int(center.y() - 20), int(center.x()), int(center.y() - 6))

        # Main Action Text
        painter.setPen(QColor("#0F111A"))
        font = QFont("sans-serif", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect.adjusted(0, 48, 0, 0), Qt.AlignHCenter | Qt.AlignTop, action_text)


class ProfileCard(QFrame):
    """Card widget representing a single VPN profile."""
    def __init__(self, profile: dict, is_active: bool, on_connect, on_delete, on_ping, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.is_active = is_active
        self.on_connect_callback = on_connect
        self.on_delete_callback = on_delete
        self.on_ping_callback = on_ping
        self.setObjectName("ProfileCard")
        self.setProperty("class", "card")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name_label = QLabel(self.profile.get("name", "Unnamed Server"))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        info_layout.addWidget(name_label)

        server_str = f"{self.profile.get('server')}:{self.profile.get('server_port')}  •  {self.profile.get('method')}"
        if self.profile.get("prefix"):
            server_str += "  •  Anti-DPI"
        sub_label = QLabel(server_str)
        sub_label.setStyleSheet("font-size: 11px; color: #8F9CAE;")
        info_layout.addWidget(sub_label)

        layout.addLayout(info_layout, 1)

        # Ping Badge
        self.ping_label = QLabel("Ping...")
        self.ping_label.setProperty("class", "badge")
        self.ping_label.setStyleSheet("background-color: #222636; color: #00E5FF; border-radius: 6px; padding: 4px 8px; font-size: 11px;")
        layout.addWidget(self.ping_label)

        # Action Buttons
        btn_connect = QPushButton("Select & Connect" if not self.is_active else "Active")
        btn_connect.setCursor(Qt.PointingHandCursor)
        if self.is_active:
            btn_connect.setStyleSheet("background-color: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid #00E676; border-radius: 6px; padding: 5px 12px; font-weight: bold;")
        else:
            btn_connect.setStyleSheet("background-color: #222636; color: #FFFFFF; border: 1px solid #282D42; border-radius: 6px; padding: 5px 12px; font-weight: bold;")
        btn_connect.clicked.connect(lambda: self.on_connect_callback(self.profile))
        layout.addWidget(btn_connect)

        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(28, 28)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setProperty("class", "action-delete")
        btn_delete.clicked.connect(lambda: self.on_delete_callback(self.profile))
        layout.addWidget(btn_delete)

    def set_ping(self, ms: Optional[int]):
        if ms is not None:
            color = "#00E676" if ms < 150 else ("#FFD600" if ms < 350 else "#FF5252")
            self.ping_label.setText(f"{ms} ms")
            self.ping_label.setStyleSheet(f"background-color: rgba(0,0,0,0.3); color: {color}; border: 1px solid {color}; border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: bold;")
        else:
            self.ping_label.setText("Timeout")
            self.ping_label.setStyleSheet("background-color: rgba(255,82,82,0.2); color: #FF5252; border-radius: 6px; padding: 4px 8px; font-size: 11px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.service = VPNService()
        self.signals = BridgeSignals()
        self.signals.state_changed.connect(self.on_state_changed)
        self.signals.stats_updated.connect(self.on_stats_updated)
        self.signals.log_updated.connect(self.on_log_updated)
        self.signals.ping_result.connect(self.on_ping_result)

        self.service.add_listener(self._service_listener)
        self.card_widgets: Dict[str, ProfileCard] = {}

        self.init_ui()
        self.init_tray()
        self.init_timers()

        self.update_profiles_list()
        self.refresh_ui_state()
        self.trigger_all_pings()

    def _service_listener(self, event_type: str, data: dict):
        self.signals.state_changed.emit(event_type, data)

    def init_ui(self):
        self.setWindowTitle("ShadowTun VPN")
        self.resize(520, 720)
        self.setStyleSheet(QSS_STYLE)

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        lbl_app_name = QLabel("SHADOWTUN VPN")
        lbl_app_name.setStyleSheet("font-size: 18px; font-weight: 800; color: #00E5FF; letter-spacing: 1px;")
        title_layout.addWidget(lbl_app_name)

        lbl_app_sub = QLabel("Universal Shadowsocks & tun2socks Engine")
        lbl_app_sub.setStyleSheet("font-size: 11px; color: #8F9CAE;")
        title_layout.addWidget(lbl_app_sub)
        header.addLayout(title_layout)

        header.addStretch(1)

        # Status Pill Badge
        self.status_pill = QLabel("DISCONNECTED")
        self.status_pill.setStyleSheet("background-color: #181B26; color: #8F9CAE; border: 1px solid #282D42; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")
        header.addWidget(self.status_pill)
        main_layout.addLayout(header)

        # Hero Connect Card
        hero_card = QFrame()
        hero_card.setProperty("class", "card")
        hero_card.setStyleSheet("background-color: #141722; border: 1px solid #222738; border-radius: 14px;")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(16, 18, 16, 18)
        hero_layout.setAlignment(Qt.AlignCenter)
        hero_layout.setSpacing(12)

        # Big Connect Button
        self.btn_connect = CircularConnectButton()
        self.btn_connect.clicked.connect(self.on_connect_toggle)
        hero_layout.addWidget(self.btn_connect, 0, Qt.AlignCenter)

        # Current Server Label
        self.lbl_current_server = QLabel("No Server Selected")
        self.lbl_current_server.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        self.lbl_current_server.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(self.lbl_current_server)

        # Live Stats Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # Speed Down
        self.lbl_speed_down = QLabel("↓ 0.0 KB/s")
        self.lbl_speed_down.setStyleSheet("color: #00E5FF; font-weight: bold; font-size: 12px;")
        stats_row.addWidget(self.lbl_speed_down, 0, Qt.AlignCenter)

        # Speed Up
        self.lbl_speed_up = QLabel("↑ 0.0 KB/s")
        self.lbl_speed_up.setStyleSheet("color: #00E676; font-weight: bold; font-size: 12px;")
        stats_row.addWidget(self.lbl_speed_up, 0, Qt.AlignCenter)

        # Duration
        self.lbl_duration = QLabel("⏱ 00:00")
        self.lbl_duration.setStyleSheet("color: #8F9CAE; font-size: 12px;")
        stats_row.addWidget(self.lbl_duration, 0, Qt.AlignCenter)

        # Total Data
        self.lbl_total_data = QLabel("📊 0 MB")
        self.lbl_total_data.setStyleSheet("color: #8F9CAE; font-size: 12px;")
        stats_row.addWidget(self.lbl_total_data, 0, Qt.AlignCenter)

        hero_layout.addLayout(stats_row)
        main_layout.addWidget(hero_card)

        # Quick Key Import Bar
        import_card = QFrame()
        import_card.setProperty("class", "card")
        import_layout = QHBoxLayout(import_card)
        import_layout.setContentsMargins(10, 8, 10, 8)
        import_layout.setSpacing(8)

        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("Paste ssconf:// URL, ss:// key, or JSON config...")
        import_layout.addWidget(self.input_key, 1)

        self.btn_import = QPushButton("Import & Connect")
        self.btn_import.setProperty("class", "primary")
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.clicked.connect(self.on_import_key)
        import_layout.addWidget(self.btn_import)

        main_layout.addWidget(import_card)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_profiles = QWidget()
        self.tab_settings = QWidget()
        self.tab_logs = QWidget()

        self.init_tab_profiles()
        self.init_tab_settings()
        self.init_tab_logs()

        self.tabs.addTab(self.tab_profiles, "Servers / Profiles")
        self.tabs.addTab(self.tab_settings, "Settings")
        self.tabs.addTab(self.tab_logs, "Logs")
        main_layout.addWidget(self.tabs, 1)

    def init_tab_profiles(self):
        layout = QVBoxLayout(self.tab_profiles)
        layout.setContentsMargins(4, 8, 4, 4)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.profiles_layout = QVBoxLayout(self.scroll_content)
        self.profiles_layout.setContentsMargins(0, 0, 0, 0)
        self.profiles_layout.setSpacing(8)
        self.profiles_layout.addStretch(1)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area)

    def init_tab_settings(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # DNS Setting
        dns_box = QVBoxLayout()
        dns_box.setSpacing(4)
        dns_label = QLabel("DNS Resolver")
        dns_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #FFFFFF;")
        dns_box.addWidget(dns_label)

        self.combo_dns = QComboBox()
        self.combo_dns.addItems([
            "Cloudflare (1.1.1.1, 1.0.0.1) - Recommended",
            "Google DNS (8.8.8.8, 8.8.4.4)",
            "Quad9 (9.9.9.9, 149.112.112.112)",
            "AdGuard DNS (94.140.14.14, 94.140.15.15)"
        ])
        dns_box.addWidget(self.combo_dns)
        layout.addLayout(dns_box)

        # Port & TUN Row
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        port_box = QVBoxLayout()
        port_box.addWidget(QLabel("Local SOCKS Port:"))
        self.input_port = QLineEdit("1080")
        port_box.addWidget(self.input_port)
        row2.addLayout(port_box)

        tun_box = QVBoxLayout()
        tun_box.addWidget(QLabel("TUN Device Name:"))
        self.input_tun = QLineEdit("tun0")
        tun_box.addWidget(self.input_tun)
        row2.addLayout(tun_box)

        layout.addLayout(row2)

        self.chk_killswitch = QCheckBox("Enable IPv6 Leak Protection (Killswitch)")
        self.chk_killswitch.setChecked(True)
        layout.addWidget(self.chk_killswitch)

        self.chk_auto_reconnect = QCheckBox("Auto-reconnect on network drop")
        self.chk_auto_reconnect.setChecked(True)
        layout.addWidget(self.chk_auto_reconnect)

        layout.addStretch(1)

        btn_save_settings = QPushButton("Save Settings")
        btn_save_settings.setProperty("class", "primary")
        btn_save_settings.clicked.connect(self.save_user_settings)
        layout.addWidget(btn_save_settings)

    def init_tab_logs(self):
        layout = QVBoxLayout(self.tab_logs)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setProperty("class", "log-box")
        layout.addWidget(self.txt_logs, 1)

        btn_row = QHBoxLayout()
        btn_refresh_logs = QPushButton("Refresh Logs")
        btn_refresh_logs.clicked.connect(self.refresh_logs)
        btn_row.addWidget(btn_refresh_logs)

        btn_clear_logs = QPushButton("Clear")
        btn_clear_logs.clicked.connect(lambda: self.txt_logs.clear())
        btn_row.addWidget(btn_clear_logs)

        layout.addLayout(btn_row)

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(DARK_PALETTE["primary"])))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, 28, 28)
        p.end()
        self.tray.setIcon(QIcon(pix))
        self.tray.setToolTip("ShadowTun VPN")

        tray_menu = QMenu()
        act_open = QAction("Open ShadowTun VPN", self)
        act_open.triggered.connect(self.show_and_raise)
        tray_menu.addAction(act_open)

        self.act_tray_connect = QAction("Connect", self)
        self.act_tray_connect.triggered.connect(self.on_connect_toggle)
        tray_menu.addAction(self.act_tray_connect)

        tray_menu.addSeparator()
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(act_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_raise()

    def init_timers(self):
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.poll_stats)
        self.stats_timer.start(1000)

        self.logs_timer = QTimer(self)
        self.logs_timer.timeout.connect(self.poll_logs)
        self.logs_timer.start(3000)

    def poll_stats(self):
        if self.service.state == STATE_CONNECTED:
            stats = self.service.get_stats()
            self.signals.stats_updated.emit(stats)

    def poll_logs(self):
        if self.tabs.currentIndex() == 2:
            self.refresh_logs()

    def refresh_logs(self):
        logs = self.service.process_mgr.get_recent_logs(50)
        self.txt_logs.setPlainText("\n".join(logs))
        self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def update_profiles_list(self):
        for card in self.card_widgets.values():
            self.profiles_layout.removeWidget(card)
            card.deleteLater()
        self.card_widgets.clear()

        profiles = self.service.config_mgr.get_profiles()
        settings = self.service.config_mgr.get_settings()
        active_id = settings.get("active_profile_id")

        for p in profiles:
            is_active = (p["id"] == active_id)
            card = ProfileCard(
                profile=p,
                is_active=is_active,
                on_connect=self.on_profile_select_and_connect,
                on_delete=self.on_profile_delete,
                on_ping=self.on_ping_profile,
                parent=self.scroll_content
            )
            self.card_widgets[p["id"]] = card
            self.profiles_layout.insertWidget(self.profiles_layout.count() - 1, card)

        active_prof = self.service.config_mgr.get_profile_by_id(active_id) if active_id else None
        if active_prof:
            self.lbl_current_server.setText(f"{active_prof.get('name')}")
        elif profiles:
            self.lbl_current_server.setText(f"{profiles[0].get('name')}")
        else:
            self.lbl_current_server.setText("No Server Selected")

    def trigger_all_pings(self):
        profiles = self.service.config_mgr.get_profiles()
        for p in profiles:
            threading.Thread(target=self._async_ping, args=(p["id"], p["server"], p.get("server_port", 443)), daemon=True).start()

    def _async_ping(self, profile_id: str, server: str, port: int):
        ms = StatsMonitor.measure_ping(server, port, timeout=3.0)
        self.signals.ping_result.emit(profile_id, ms if ms is not None else -1)

    def on_ping_result(self, profile_id: str, ms: int):
        if profile_id in self.card_widgets:
            self.card_widgets[profile_id].set_ping(ms if ms >= 0 else None)

    def on_ping_profile(self, profile: dict):
        threading.Thread(target=self._async_ping, args=(profile["id"], profile["server"], profile.get("server_port", 443)), daemon=True).start()

    def on_profile_select_and_connect(self, profile: dict):
        settings = self.service.config_mgr.get_settings()
        settings["active_profile_id"] = profile["id"]
        self.service.config_mgr.save_settings(settings)
        self.update_profiles_list()
        self.start_connect_thread(profile)

    def on_profile_delete(self, profile: dict):
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete profile '{profile.get('name')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.service.config_mgr.delete_profile(profile["id"])
            self.update_profiles_list()

    def on_import_key(self):
        key = self.input_key.text().strip()
        if not key:
            QMessageBox.warning(self, "Input Required", "Please paste a valid ssconf:// URL, ss:// key, or JSON config.")
            return

        self.btn_import.setEnabled(False)
        self.btn_import.setText("Importing...")

        def _import_worker():
            try:
                profile = self.service.config_mgr.parse_key(key)
                saved = self.service.config_mgr.add_or_update_profile(profile)
                settings = self.service.config_mgr.get_settings()
                settings["active_profile_id"] = saved["id"]
                self.service.config_mgr.save_settings(settings)
                self.signals.state_changed.emit("import_success", {"profile": saved})
            except Exception as e:
                self.signals.state_changed.emit("import_error", {"error": str(e)})

        threading.Thread(target=_import_worker, daemon=True).start()

    def on_connect_toggle(self):
        if self.service.state == STATE_CONNECTED:
            self.start_disconnect_thread()
        elif self.service.state in (STATE_DISCONNECTED, STATE_ERROR):
            self.start_connect_thread()

    def start_connect_thread(self, target: Any = None):
        self.btn_connect.setEnabled(False)
        self.btn_connect.set_state(STATE_CONNECTING)
        self.status_pill.setText("CONNECTING...")
        self.status_pill.setStyleSheet("background-color: rgba(255, 214, 0, 0.15); color: #FFD600; border: 1px solid #FFD600; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")

        def _connect_worker():
            self.service.connect(target)

        threading.Thread(target=_connect_worker, daemon=True).start()

    def start_disconnect_thread(self):
        self.btn_connect.setEnabled(False)
        self.btn_connect.set_state(STATE_DISCONNECTING)
        self.status_pill.setText("STOPPING...")
        self.status_pill.setStyleSheet("background-color: rgba(255, 214, 0, 0.15); color: #FFD600; border: 1px solid #FFD600; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")

        def _disconnect_worker():
            self.service.disconnect()

        threading.Thread(target=_disconnect_worker, daemon=True).start()

    def on_state_changed(self, event_type: str, data: dict):
        self.btn_connect.setEnabled(True)
        state = self.service.state
        self.btn_connect.set_state(state)

        if event_type == "import_success":
            self.btn_import.setEnabled(True)
            self.btn_import.setText("Import & Connect")
            self.input_key.clear()
            self.update_profiles_list()
            self.trigger_all_pings()
            prof = data.get("profile")
            if prof:
                self.start_connect_thread(prof)

        elif event_type == "import_error":
            self.btn_import.setEnabled(True)
            self.btn_import.setText("Import & Connect")
            QMessageBox.critical(self, "Import Failed", f"Could not import key:\n\n{data.get('error')}")

        elif state == STATE_CONNECTED:
            self.status_pill.setText("CONNECTED")
            self.status_pill.setStyleSheet("background-color: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")
            self.act_tray_connect.setText("Disconnect")
            self.tray.showMessage("ShadowTun VPN", "Connected to VPN", QSystemTrayIcon.Information, 2000)

        elif state == STATE_DISCONNECTED:
            self.status_pill.setText("DISCONNECTED")
            self.status_pill.setStyleSheet("background-color: #181B26; color: #8F9CAE; border: 1px solid #282D42; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")
            self.act_tray_connect.setText("Connect")
            self.lbl_speed_down.setText("↓ 0.0 KB/s")
            self.lbl_speed_up.setText("↑ 0.0 KB/s")
            self.lbl_duration.setText("⏱ 00:00")

        elif state == STATE_ERROR:
            self.status_pill.setText("ERROR")
            self.status_pill.setStyleSheet("background-color: rgba(255, 82, 82, 0.15); color: #FF5252; border: 1px solid #FF5252; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")
            if data.get("error"):
                QMessageBox.critical(self, "VPN Connection Error", f"Failed to establish VPN connection:\n\n{data.get('error')}")

        self.update_profiles_list()

    def on_stats_updated(self, stats: dict):
        self.lbl_speed_down.setText(f"↓ {stats['rx_speed_str']}")
        self.lbl_speed_up.setText(f"↑ {stats['tx_speed_str']}")
        self.lbl_duration.setText(f"⏱ {stats['duration_str']}")
        self.lbl_total_data.setText(f"📊 {stats['rx_total_str']}")

    def on_log_updated(self, logs: list):
        self.txt_logs.setPlainText("\n".join(logs))

    def save_user_settings(self):
        settings = self.service.config_mgr.get_settings()
        idx = self.combo_dns.currentIndex()
        dns_map = [
            ("1.1.1.1", "1.0.0.1"),
            ("8.8.8.8", "8.8.4.4"),
            ("9.9.9.9", "149.112.112.112"),
            ("94.140.14.14", "94.140.15.15")
        ]
        p_dns, b_dns = dns_map[idx]
        settings["dns"] = p_dns
        settings["dns_backup"] = b_dns
        settings["socks_port"] = int(self.input_port.text().strip() or 1080)
        settings["tun_device"] = self.input_tun.text().strip() or "tun0"
        settings["killswitch"] = self.chk_killswitch.isChecked()
        settings["auto_reconnect"] = self.chk_auto_reconnect.isChecked()

        self.service.config_mgr.save_settings(settings)
        QMessageBox.information(self, "Settings Saved", "VPN configuration updated successfully.")

    def refresh_ui_state(self):
        state = self.service.state
        self.btn_connect.set_state(state)
        if state == STATE_CONNECTED:
            self.status_pill.setText("CONNECTED")
            self.status_pill.setStyleSheet("background-color: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676; border-radius: 12px; padding: 5px 12px; font-size: 11px; font-weight: bold;")
        else:
            self.status_pill.setText("DISCONNECTED")

    def quit_app(self):
        if self.service.state == STATE_CONNECTED:
            reply = QMessageBox.question(
                self,
                "Quit VPN",
                "VPN is currently active. Do you want to disconnect before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.service.disconnect()
            elif reply == QMessageBox.Cancel:
                return
        QApplication.quit()

    def closeEvent(self, event):
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "ShadowTun VPN",
                "ShadowTun VPN is running in the background.",
                QSystemTrayIcon.Information,
                1500
            )
            event.ignore()
        else:
            event.accept()


def launch_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("ShadowTun VPN")
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_gui()
