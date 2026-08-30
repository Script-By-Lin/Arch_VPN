#!/usr/bin/env python3
"""
Minimalist Desktop Widget GUI for ShadowTun Linux VPN.
Built with PyQt5, featuring a clean professional dark theme,
compact layout, live telemetry, profile selector, and settings.
"""

import os
import sys
import time
import signal
import threading
from typing import Optional, Dict, Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush, QPen, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QTabWidget,
    QPlainTextEdit, QComboBox, QCheckBox, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QSizePolicy
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


class ProfileRowWidget(QFrame):
    """Clean, high-density card representing a single server."""
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
                background-color: #181A22;
                border: 1px solid #282B38;
                border-radius: 8px;
            }
            QFrame#ServerCard:hover {
                border: 1px solid #34384A;
                background-color: #1D1F29;
            }
        """)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(10, 8, 10, 8)
        main_vbox.setSpacing(4)

        # Top Row: [Dot] [Server Name] ... [Ping Badge] [Connect/Switch/Active Button] [Delete Button]
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        # Status Dot
        self.dot = QLabel("●")
        dot_color = "#10B981" if self.is_connected else ("#3B82F6" if self.is_active else "#6B7280")
        self.dot.setStyleSheet(f"color: {dot_color}; font-size: 11px;")
        top_row.addWidget(self.dot)

        # Server Name
        self.name_label = QLabel(self.profile.get("name", "Unnamed Server"))
        self.name_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #F9FAFB;")
        top_row.addWidget(self.name_label, 1)

        # Ping Badge
        self.ping_label = QLabel("...")
        self.ping_label.setStyleSheet("background-color: #14151D; color: #6B7280; border: 1px solid #282B38; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600;")
        top_row.addWidget(self.ping_label)

        # Action / Select Button
        self.btn_select = QPushButton()
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.update_action_button()
        self.btn_select.clicked.connect(lambda: self.on_connect_callback(self.profile))
        top_row.addWidget(self.btn_select)

        # Delete Button
        btn_delete = QPushButton("✕")
        btn_delete.setFixedSize(20, 20)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet("QPushButton { background-color: transparent; color: #6B7280; border: none; border-radius: 3px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: rgba(239, 68, 68, 0.15); color: #EF4444; }")
        btn_delete.clicked.connect(lambda: self.on_delete_callback(self.profile))
        top_row.addWidget(btn_delete)

        main_vbox.addLayout(top_row)

        # Bottom Row: Host:Port • Method • Anti-DPI
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(4)

        server_str = f"{self.profile.get('server')}:{self.profile.get('server_port')}  •  {self.profile.get('method')}"
        if self.profile.get("prefix"):
            server_str += "  •  Anti-DPI"
        sub_label = QLabel(server_str)
        sub_label.setStyleSheet("font-size: 10px; color: #6B7280;")
        bottom_row.addWidget(sub_label, 1)

        main_vbox.addLayout(bottom_row)

    def update_action_button(self):
        if self.is_connected:
            self.btn_select.setText("Connected")
            self.btn_select.setStyleSheet("background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 600;")
        elif self.is_active:
            self.btn_select.setText("Selected")
            self.btn_select.setStyleSheet("background-color: rgba(59, 130, 246, 0.15); color: #3B82F6; border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 600;")
        else:
            self.btn_select.setText("Switch")
            self.btn_select.setStyleSheet("background-color: #1E202B; color: #D1D5DB; border: 1px solid #282B38; border-radius: 4px; padding: 3px 8px; font-size: 10px; font-weight: 600;")

    def set_ping(self, ms: Optional[int]):
        if ms is not None and ms >= 0:
            if ms < 150:
                color = "#10B981"
            elif ms < 350:
                color = "#F59E0B"
            else:
                color = "#EF4444"
            self.ping_label.setText(f"{ms}ms")
            self.ping_label.setStyleSheet(f"background-color: #14151D; color: {color}; border: 1px solid #282B38; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600;")
        else:
            self.ping_label.setText("timeout")
            self.ping_label.setStyleSheet("background-color: #14151D; color: #EF4444; border: 1px solid #282B38; border-radius: 4px; padding: 2px 6px; font-size: 10px;")


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
        self.setWindowTitle("ShadowTun VPN")
        self.resize(420, 580)
        self.setMinimumSize(380, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setStyleSheet(QSS_STYLE)

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Header Bar
        header = QHBoxLayout()
        header.setSpacing(8)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        lbl_app_name = QLabel("ShadowTun")
        lbl_app_name.setProperty("class", "app-title")
        title_layout.addWidget(lbl_app_name)

        lbl_app_sub = QLabel("Universal Linux VPN")
        lbl_app_sub.setProperty("class", "app-subtitle")
        title_layout.addWidget(lbl_app_sub)
        header.addLayout(title_layout)

        header.addStretch(1)

        # Status Pill Badge
        self.status_pill = QLabel("● Disconnected")
        self.status_pill.setProperty("class", "status-pill")
        header.addWidget(self.status_pill)
        main_layout.addLayout(header)

        # 2. Main Connection Widget Card
        main_card = QFrame()
        main_card.setProperty("class", "surface")
        card_layout = QVBoxLayout(main_card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        # Server Selector Dropdown
        server_sel_layout = QVBoxLayout()
        server_sel_layout.setSpacing(3)
        lbl_server_title = QLabel("Active Server")
        lbl_server_title.setStyleSheet("font-size: 11px; font-weight: 600; color: #9CA3AF;")
        server_sel_layout.addWidget(lbl_server_title)

        self.combo_servers = QComboBox()
        self.combo_servers.setCursor(Qt.PointingHandCursor)
        self.combo_servers.currentIndexChanged.connect(self.on_server_dropdown_changed)
        server_sel_layout.addWidget(self.combo_servers)
        card_layout.addLayout(server_sel_layout)

        # Prominent Connect / Disconnect Action Button
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setCursor(Qt.PointingHandCursor)
        self.btn_connect.setProperty("class", "btn-connect")
        self.btn_connect.clicked.connect(self.on_connect_toggle)
        card_layout.addWidget(self.btn_connect)

        # Telemetry Stats Strip
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("background-color: #14151D; border: 1px solid #282B38; border-radius: 6px;")
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 6, 10, 6)
        stats_layout.setSpacing(8)

        self.lbl_speed_down = QLabel("↓ 0 KB/s")
        self.lbl_speed_down.setStyleSheet("color: #3B82F6; font-size: 11px; font-weight: 600;")
        stats_layout.addWidget(self.lbl_speed_down)

        self.lbl_speed_up = QLabel("↑ 0 KB/s")
        self.lbl_speed_up.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
        stats_layout.addWidget(self.lbl_speed_up)

        stats_layout.addStretch(1)

        self.lbl_duration = QLabel("00:00")
        self.lbl_duration.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        stats_layout.addWidget(self.lbl_duration)

        self.lbl_total_data = QLabel("0 MB")
        self.lbl_total_data.setStyleSheet("color: #6B7280; font-size: 11px;")
        stats_layout.addWidget(self.lbl_total_data)

        card_layout.addWidget(self.stats_frame)
        main_layout.addWidget(main_card)

        # 3. Compact Segmented Tabs
        self.tabs = QTabWidget()
        self.tab_servers = QWidget()
        self.tab_servers.setStyleSheet("background-color: transparent;")
        self.tab_import = QWidget()
        self.tab_import.setStyleSheet("background-color: transparent;")
        self.tab_settings = QWidget()
        self.tab_settings.setStyleSheet("background-color: transparent;")
        self.tab_logs = QWidget()
        self.tab_logs.setStyleSheet("background-color: transparent;")

        self.init_tab_servers()
        self.init_tab_import()
        self.init_tab_settings()
        self.init_tab_logs()

        self.tabs.addTab(self.tab_servers, "Servers")
        self.tabs.addTab(self.tab_import, "Import")
        self.tabs.addTab(self.tab_settings, "Settings")
        self.tabs.addTab(self.tab_logs, "Logs")
        main_layout.addWidget(self.tabs, 1)

    def init_tab_servers(self):
        layout = QVBoxLayout(self.tab_servers)
        layout.setContentsMargins(2, 6, 2, 2)
        layout.setSpacing(6)

        # Top Action Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)

        self.lbl_server_count = QLabel("CONFIGURED SERVERS")
        self.lbl_server_count.setStyleSheet("font-size: 10px; font-weight: 700; color: #6B7280; letter-spacing: 0.5px;")
        top_bar.addWidget(self.lbl_server_count)

        top_bar.addStretch(1)

        btn_refresh_pings = QPushButton("↻ Test Latencies")
        btn_refresh_pings.setCursor(Qt.PointingHandCursor)
        btn_refresh_pings.setStyleSheet("background-color: #181A22; color: #9CA3AF; border: 1px solid #282B38; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 600;")
        btn_refresh_pings.clicked.connect(self.trigger_all_pings)
        top_bar.addWidget(btn_refresh_pings)

        layout.addLayout(top_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.scroll_area.viewport().setStyleSheet("background-color: transparent;")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.profiles_layout = QVBoxLayout(self.scroll_content)
        self.profiles_layout.setContentsMargins(2, 2, 2, 2)
        self.profiles_layout.setSpacing(6)
        self.profiles_layout.addStretch(1)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area)

    def init_tab_import(self):
        layout = QVBoxLayout(self.tab_import)
        layout.setContentsMargins(6, 8, 6, 6)
        layout.setSpacing(8)

        lbl_info = QLabel("Paste ssconf:// URL, ss:// key, or JSON config:")
        lbl_info.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        layout.addWidget(lbl_info)

        self.input_key = QLineEdit()
        self.input_key.setPlaceholderText("ssconf://... or ss://...")
        layout.addWidget(self.input_key)

        self.btn_import = QPushButton("Import & Add Server")
        self.btn_import.setProperty("class", "btn-primary")
        self.btn_import.setCursor(Qt.PointingHandCursor)
        self.btn_import.clicked.connect(self.on_import_key)
        layout.addWidget(self.btn_import)

        layout.addStretch(1)

    def init_tab_settings(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(6, 8, 6, 6)
        layout.setSpacing(8)

        # DNS Setting
        lbl_dns = QLabel("DNS Resolver:")
        lbl_dns.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        layout.addWidget(lbl_dns)

        self.combo_dns = QComboBox()
        self.combo_dns.addItems([
            "Cloudflare (1.1.1.1, 1.0.0.1)",
            "Google DNS (8.8.8.8, 8.8.4.4)",
            "Quad9 (9.9.9.9, 149.112.112.112)",
            "AdGuard DNS (94.140.14.14, 94.140.15.15)"
        ])
        layout.addWidget(self.combo_dns)

        # Port & TUN row
        row = QHBoxLayout()
        row.setSpacing(8)

        port_col = QVBoxLayout()
        port_col.setSpacing(2)
        port_lbl = QLabel("SOCKS Port:")
        port_lbl.setStyleSheet("font-size: 10px; color: #6B7280;")
        port_col.addWidget(port_lbl)
        self.input_port = QLineEdit("1080")
        port_col.addWidget(self.input_port)
        row.addLayout(port_col)

        tun_col = QVBoxLayout()
        tun_col.setSpacing(2)
        tun_lbl = QLabel("TUN Device:")
        tun_lbl.setStyleSheet("font-size: 10px; color: #6B7280;")
        tun_col.addWidget(tun_lbl)
        self.input_tun = QLineEdit("tun0")
        tun_col.addWidget(self.input_tun)
        row.addLayout(tun_col)

        layout.addLayout(row)

        self.chk_killswitch = QCheckBox("IPv6 Leak Protection (Killswitch)")
        self.chk_killswitch.setChecked(True)
        layout.addWidget(self.chk_killswitch)

        self.chk_auto_reconnect = QCheckBox("Auto-reconnect on network drop")
        self.chk_auto_reconnect.setChecked(True)
        layout.addWidget(self.chk_auto_reconnect)

        layout.addStretch(1)

        btn_save_settings = QPushButton("Save Settings")
        btn_save_settings.setProperty("class", "btn-primary")
        btn_save_settings.clicked.connect(self.save_user_settings)
        layout.addWidget(btn_save_settings)

    def init_tab_logs(self):
        layout = QVBoxLayout(self.tab_logs)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(6)

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setProperty("class", "log-box")
        layout.addWidget(self.txt_logs, 1)

        btn_row = QHBoxLayout()
        btn_refresh_logs = QPushButton("Refresh")
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
        p.setBrush(QBrush(QColor(PALETTE["primary"])))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, 24, 24, 6, 6)
        p.end()
        self.tray.setIcon(QIcon(pix))
        self.tray.setToolTip("ShadowTun VPN")

        tray_menu = QMenu()
        act_open = QAction("Open ShadowTun", self)
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
        if self.isMinimized():
            self.showNormal()
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

        # Periodic timer (200ms) to allow Python interpreter to catch SIGINT / Ctrl+C
        self.sig_timer = QTimer(self)
        self.sig_timer.timeout.connect(lambda: None)
        self.sig_timer.start(200)

    def poll_stats(self):
        if self.service.state == STATE_CONNECTED:
            stats = self.service.get_stats()
            self.signals.stats_updated.emit(stats)

    def poll_logs(self):
        if self.tabs.currentIndex() == 3:
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
        connected_prof = self.service.active_profile if self.service.state == STATE_CONNECTED else None
        connected_id = connected_prof.get("id") if connected_prof else None

        self.updating_combo = True
        self.combo_servers.clear()

        selected_idx = 0
        for idx, p in enumerate(profiles):
            is_active = (p["id"] == active_id)
            is_connected = (self.service.state == STATE_CONNECTED and p["id"] == connected_id)
            if is_active or is_connected:
                selected_idx = idx

            card = ProfileRowWidget(
                profile=p,
                is_active=is_active,
                is_connected=is_connected,
                on_connect=self.on_profile_select_and_connect,
                on_delete=self.on_profile_delete,
                on_ping=self.on_ping_profile,
                parent=self.scroll_content
            )
            self.card_widgets[p["id"]] = card
            self.profiles_layout.insertWidget(self.profiles_layout.count() - 1, card)
            self.combo_servers.addItem(p.get("name", "Unnamed Server"), p["id"])

        if profiles:
            self.combo_servers.setCurrentIndex(selected_idx)
            self.combo_servers.setEnabled(True)
            self.lbl_server_count.setText(f"CONFIGURED SERVERS ({len(profiles)})")
        else:
            self.combo_servers.addItem("No Profiles (Add in Import tab)", "")
            self.combo_servers.setEnabled(False)
            self.lbl_server_count.setText("CONFIGURED SERVERS (0)")

        self.updating_combo = False

    def on_server_dropdown_changed(self, idx: int):
        if self.updating_combo or idx < 0:
            return
        prof_id = self.combo_servers.itemData(idx)
        if not prof_id:
            return
        profile = self.service.config_mgr.get_profile_by_id(prof_id)
        if not profile:
            return

        settings = self.service.config_mgr.get_settings()
        settings["active_profile_id"] = prof_id
        self.service.config_mgr.save_settings(settings)

        # Update card visuals
        connected_prof = self.service.active_profile if self.service.state == STATE_CONNECTED else None
        connected_id = connected_prof.get("id") if connected_prof else None
        for pid, card in self.card_widgets.items():
            card.is_active = (pid == prof_id)
            card.is_connected = (self.service.state == STATE_CONNECTED and pid == connected_id)
            card.dot.setStyleSheet(f"color: {'#10B981' if card.is_connected else ('#3B82F6' if card.is_active else '#6B7280')}; font-size: 11px;")
            card.update_action_button()

        # If currently connected to a DIFFERENT server, automatically hot-switch!
        if self.service.state == STATE_CONNECTED and connected_id != prof_id:
            self.start_connect_thread(profile)

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
            "Delete Server",
            f"Remove profile '{profile.get('name')}'?",
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
        self.btn_connect.setText("Connecting...")
        self.btn_connect.setProperty("class", "btn-connecting")
        self.btn_connect.setStyle(self.btn_connect.style())

        self.status_pill.setText("● Connecting...")
        self.status_pill.setProperty("class", "status-pill-connecting")
        self.status_pill.setStyle(self.status_pill.style())

        def _connect_worker():
            self.service.connect(target)

        threading.Thread(target=_connect_worker, daemon=True).start()

    def start_disconnect_thread(self):
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Disconnecting...")
        self.btn_connect.setProperty("class", "btn-connecting")
        self.btn_connect.setStyle(self.btn_connect.style())

        self.status_pill.setText("● Disconnecting...")
        self.status_pill.setProperty("class", "status-pill-connecting")
        self.status_pill.setStyle(self.status_pill.style())

        def _disconnect_worker():
            self.service.disconnect()

        threading.Thread(target=_disconnect_worker, daemon=True).start()

    def on_state_changed(self, event_type: str, data: dict):
        self.btn_connect.setEnabled(True)
        state = self.service.state

        if event_type == "import_success":
            self.btn_import.setEnabled(True)
            self.btn_import.setText("Import & Add Server")
            self.input_key.clear()
            self.update_profiles_list()
            self.trigger_all_pings()
            self.tabs.setCurrentIndex(0)
            prof = data.get("profile")
            if prof:
                self.start_connect_thread(prof)

        elif event_type == "import_error":
            self.btn_import.setEnabled(True)
            self.btn_import.setText("Import & Add Server")
            QMessageBox.critical(self, "Import Failed", f"Could not import key:\n\n{data.get('error')}")

        elif state == STATE_CONNECTED:
            self.status_pill.setText("● Connected")
            self.status_pill.setProperty("class", "status-pill-connected")
            self.status_pill.setStyle(self.status_pill.style())

            self.btn_connect.setText("Disconnect")
            self.btn_connect.setProperty("class", "btn-disconnect")
            self.btn_connect.setStyle(self.btn_connect.style())

            self.combo_servers.setEnabled(True)
            self.act_tray_connect.setText("Disconnect")
            self.tray.showMessage("ShadowTun VPN", "Connected to VPN", QSystemTrayIcon.Information, 1500)

        elif state == STATE_DISCONNECTED:
            self.status_pill.setText("● Disconnected")
            self.status_pill.setProperty("class", "status-pill")
            self.status_pill.setStyle(self.status_pill.style())

            self.btn_connect.setText("Connect")
            self.btn_connect.setProperty("class", "btn-connect")
            self.btn_connect.setStyle(self.btn_connect.style())

            self.combo_servers.setEnabled(True)
            self.act_tray_connect.setText("Connect")
            self.lbl_speed_down.setText("↓ 0 KB/s")
            self.lbl_speed_up.setText("↑ 0 KB/s")
            self.lbl_duration.setText("00:00")
            self.lbl_total_data.setText("0 MB")

        elif state == STATE_ERROR:
            self.status_pill.setText("● Error")
            self.status_pill.setProperty("class", "status-pill-error")
            self.status_pill.setStyle(self.status_pill.style())

            self.btn_connect.setText("Connect")
            self.btn_connect.setProperty("class", "btn-connect")
            self.btn_connect.setStyle(self.btn_connect.style())

            self.combo_servers.setEnabled(True)
            if data.get("error"):
                QMessageBox.critical(self, "VPN Connection Error", f"Failed to establish VPN connection:\n\n{data.get('error')}")

        self.update_profiles_list()

    def on_stats_updated(self, stats: dict):
        self.lbl_speed_down.setText(f"↓ {stats['rx_speed_str']}")
        self.lbl_speed_up.setText(f"↑ {stats['tx_speed_str']}")
        self.lbl_duration.setText(f"{stats['duration_str']}")
        self.lbl_total_data.setText(f"{stats['rx_total_str']}")

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
        if state == STATE_CONNECTED:
            self.status_pill.setText("● Connected")
            self.status_pill.setProperty("class", "status-pill-connected")
            self.btn_connect.setText("Disconnect")
            self.btn_connect.setProperty("class", "btn-disconnect")
        elif state in (STATE_CONNECTING, STATE_DISCONNECTING):
            self.status_pill.setText("● Connecting...")
            self.status_pill.setProperty("class", "status-pill-connecting")
            self.btn_connect.setText("Connecting...")
            self.btn_connect.setProperty("class", "btn-connecting")
        else:
            self.status_pill.setText("● Disconnected")
            self.status_pill.setProperty("class", "status-pill")
            self.btn_connect.setText("Connect")
            self.btn_connect.setProperty("class", "btn-connect")
        self.status_pill.setStyle(self.status_pill.style())
        self.btn_connect.setStyle(self.btn_connect.style())

    def quit_app(self):
        if self.service.state == STATE_CONNECTED:
            reply = QMessageBox.question(
                self,
                "Quit VPN",
                "VPN is currently active. Disconnect before exiting?",
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
                "Running in system tray.",
                QSystemTrayIcon.Information,
                1000
            )
            event.ignore()
        else:
            event.accept()


def launch_gui():
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)

    app = QApplication(sys.argv)
    app.setApplicationName("ShadowTun VPN")
    app.setQuitOnLastWindowClosed(False)
    win = MainWindow()
    app._main_win = win
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_gui()
