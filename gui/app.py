#!/usr/bin/env python3
"""
AuraLink Daylight Desktop GUI for AuraLink Linux VPN.
Built with PyQt5 in a modern light theme, featuring an animated orbital
connect button, interactive live tunnel pipeline model, live speed sparklines,
DNS upstream selector, real-time log stream, and complete server management.
"""

import html , json
import math
import os
import re
import signal
import sys
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core import (
    ConfigError,
    DNS_PRESETS,
    SESSION_FILE,
    STATE_CONNECTED,
    STATE_CONNECTING,
    STATE_DISCONNECTED,
    STATE_DISCONNECTING,
    STATE_ERROR,
    VPNService,
)
from gui.theme import PALETTE, QSS_STYLE


def sigint_handler(signum, frame):
    """Handles Ctrl+C (SIGINT) cleanly from terminal."""
    print("\n[AuraLink] Terminating upon Ctrl+C...")
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
    stage_changed = pyqtSignal(dict)
    stats_updated = pyqtSignal(dict)
    log_updated = pyqtSignal(list)
    ping_result = pyqtSignal(str, int)
    log_message = pyqtSignal(str)
    import_finished = pyqtSignal(bool, str, dict)


def clean_and_format_log(raw: str) -> tuple:
    """
    Parses raw daemon outputs (sslocal, tun2socks) and system messages,
    stripping verbose Rust/Tokio worker internals, unescaped logfmt syntax,
    and bloated nanosecond timestamps, returning a clean fixed-width plain text
    line and an HTML-formatted line.
    """
    s = raw.strip()
    if not s:
        return "", ""

    source = "system"
    if s.startswith("[sslocal]"):
        source = "sslocal"
        s = s[len("[sslocal]"):].strip()
    elif s.startswith("[tun2socks]"):
        source = "tun2socks"
        s = s[len("[tun2socks]"):].strip()

    # Time extraction
    time_str = ""
    # 1. tun2socks: time="2026-11-19T00:54:36+06:30"
    tm = re.search(r'time="(?:\d{4}-\d{2}-\d{2}[T ])?(\d{2}:\d{2}:\d{2})', s)
    if tm:
        time_str = tm.group(1)
        s = re.sub(r'time="[^"]+"\s*', '', s)
    else:
        # 2. 12-hour or 24-hour [HH:MM:SS AM/PM]
        am = re.match(r"^\[(\d{1,2}):(\d{2}):(\d{2})\s*([AP]M)?\]\s*", s, re.IGNORECASE)
        if am:
            h, m, sec, meridiem = am.group(1), am.group(2), am.group(3), am.group(4)
            if meridiem:
                h_int = int(h)
                if meridiem.upper() == "PM" and h_int < 12:
                    h_int += 12
                elif meridiem.upper() == "AM" and h_int == 12:
                    h_int = 0
                h = f"{h_int:02d}"
            else:
                h = f"{int(h):02d}"
            time_str = f"{h}:{m}:{sec}"
            s = s[am.end():].strip()
        else:
            # 3. ISO format: 2026-11-19T00:54:36.219677544+06:30
            sm = re.match(r"^\[?(?:\d{4}-\d{2}-\d{2}[T ])?(\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:[+-]\d{2}:\d{2})?\]?\s*", s)
            if sm:
                time_str = sm.group(1)
                s = s[sm.end():].strip()

    # Level extraction
    level = "INFO"
    lm = re.search(r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL)\b", s, re.IGNORECASE)
    if lm:
        raw_lvl = lm.group(1).upper()
        level = "WARN" if "WARN" in raw_lvl else ("ERROR" if raw_lvl == "FATAL" else raw_lvl)
        s = s[:lm.start()] + s[lm.end():]
    elif "level=" in s:
        llm = re.search(r"level=([a-zA-Z]+)", s)
        if llm:
            raw_lvl = llm.group(1).upper()
            level = "WARN" if "WARN" in raw_lvl else ("ERROR" if raw_lvl == "FATAL" else raw_lvl)
            s = re.sub(r"level=[a-zA-Z]+\s*", "", s)

    # Clean tun2socks msg="..."
    msg_m = re.search(r'msg="([^"]+)"', s)
    if msg_m:
        s = msg_m.group(1)

    # Clean Tokio worker & Rust module boilerplate
    s = re.sub(r"tokio-rt-worker\s+ThreadId\(\d+\)\s*", "", s)
    s = re.sub(r"(?:shadowsocks_service::|[a-zA-Z0-9_]+::)+(?:[a-zA-Z0-9_]+:\s*)?", "", s)

    # Clean up redundant socket verbose clauses
    s = re.sub(r"through server ([0-9.:]+) \(outbound: [0-9.:]+\)", r"via \1", s)
    s = re.sub(r"\(outbound:\s*[0-9.:]+\)", "", s)
    s = re.sub(r"\bestablished tcp tunnel\b", "TCP tunnel", s, flags=re.IGNORECASE)
    s = re.sub(r"^through server\s*", "via ", s)
    s = s.strip()

    # Downgrade benign client-cancelled local SOCKS5 preconnect EOFs from alarming ERROR to DEBUG
    if source == "sslocal" and level == "ERROR" and "socks5 tcp client handler error: unexpected end of file" in s.lower():
        level = "DEBUG"
        s = "Local client closed SOCKS5 handshake early (harmless)"

    # If message has its own [TAG], use it if source was generic system
    if source == "system":
        tag_m = re.match(r"^\[([A-Za-z0-9_-]+)\]\s*", s)
        if tag_m:
            custom_tag = tag_m.group(1).lower()
            if custom_tag in ("dns", "ping", "import", "delete", "disconnect", "connect", "status", "cleanup", "warning", "error"):
                source = custom_tag
                s = s[tag_m.end():].strip()

    if not time_str:
        time_str = time.strftime("%H:%M:%S")

    # Colors
    src_colors = {
        "tun2socks": "#059669",
        "sslocal": "#0284C7",
        "system": "#6366F1",
        "connect": "#059669",
        "disconnect": "#D97706",
        "dns": "#0D9488",
        "ping": "#8B5CF6",
        "import": "#0284C7",
        "error": "#DC2626",
    }
    src_col = src_colors.get(source, "#475569")

    lvl_colors = {
        "DEBUG": "#94A3B8",
        "INFO": "#0284C7",
        "WARN": "#D97706",
        "ERROR": "#DC2626",
    }
    lvl_col = lvl_colors.get(level, "#64748B")

    pad_src = f"[{source}]".ljust(11)
    pad_lvl = level.ljust(5)

    plain = f"[{time_str}] {pad_src} {pad_lvl} {s}"

    esc_msg = html.escape(s)
    esc_msg = re.sub(r"(&lt;-&gt;|<->)", r'<span style="color:#10B981; font-weight:bold;"> ↔ </span>', esc_msg)
    esc_msg = re.sub(r"\b(\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?)\b", r'<span style="color:#0F172A; font-weight:600;">\1</span>', esc_msg)

    html_line = (
        f'<div style="white-space: nowrap; margin: 1px 0; font-family: monospace; font-size: 10.5px;">'
        f'<span style="color:#64748B;">[{time_str}]</span> '
        f'<span style="color:{src_col}; font-weight:bold;">{pad_src}</span> '
        f'<span style="color:{lvl_col}; font-weight:bold;">{pad_lvl}</span> '
        f'<span style="color:#334155;">{esc_msg}</span>'
        f'</div>'
    )

    return plain, html_line


class CircularConnectButton(QPushButton):
    """
    Animated Daylight circular connect button with smooth hover interpolation,
    tactile click compression spring, shockwave ripple bursts on click,
    rotating orbital ring during handshake, and dual ripple waves when connected.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(176, 176)
        self.setCursor(Qt.PointingHandCursor)
        self._state = STATE_DISCONNECTED
        self._hover = False
        self._hover_t = 0.0
        self._pressed = False
        self._press_t = 0.0
        self._pulse_phase = 0.0
        self._orbit_angle = 0.0
        self._shockwaves: List[Dict[str, Any]] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(30)

    def trigger_click_effect(self, is_disconnect: bool = False):
        """Trigger radial tactile shockwave radiating outward from center."""
        self._shockwaves.append({
            "progress": 0.0,
            "is_disconnect": is_disconnect,
            "max_span": 28.0,
        })
        self.update()

    def set_vpn_state(self, state: str):
        self._state = state
        self.update()

    def _on_tick(self):
        needs_repaint = False
        target_hover = 1.0 if self._hover else 0.0
        if abs(self._hover_t - target_hover) > 0.01:
            self._hover_t += (target_hover - self._hover_t) * 0.22
            needs_repaint = True
        elif self._hover_t != target_hover:
            self._hover_t = target_hover
            needs_repaint = True

        target_press = 1.0 if self._pressed else 0.0
        if abs(self._press_t - target_press) > 0.01:
            self._press_t += (target_press - self._press_t) * 0.35
            needs_repaint = True
        elif self._press_t != target_press:
            self._press_t = target_press
            needs_repaint = True

        if self._shockwaves:
            active_sw = []
            for sw in self._shockwaves:
                sw["progress"] += 0.055
                if sw["progress"] < 1.0:
                    active_sw.append(sw)
            self._shockwaves = active_sw
            needs_repaint = True

        if self._state == STATE_CONNECTED:
            self._pulse_phase = (self._pulse_phase + 0.055) % (math.pi * 2.0)
            needs_repaint = True
        elif self._state in (STATE_CONNECTING, STATE_DISCONNECTING):
            self._pulse_phase = (self._pulse_phase + 0.09) % (math.pi * 2.0)
            self._orbit_angle = (self._orbit_angle + 7.5) % 360.0
            needs_repaint = True

        if needs_repaint:
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self._hover = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._pressed = False
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = QPointF(rect.center())
        base_r = min(rect.width(), rect.height()) / 2.0 - 16.0
        radius = (base_r + self._hover_t * 2.0) * (1.0 - 0.045 * self._press_t)

        if self._state == STATE_CONNECTED:
            grad_start = QColor("#FFFFFF")
            grad_end = QColor("#ECFDF5")
            border_color = QColor("#10B981")
            icon_color = QColor("#059669")
            icon_bg = QColor(16, 185, 129, 28)
            text_color = QColor("#047857")
            sub_text = "CONNECTED • TAP TO STOP"
        elif self._state in (STATE_CONNECTING, STATE_DISCONNECTING):
            grad_start = QColor("#FFFFFF")
            grad_end = QColor("#FFFBEB")
            border_color = QColor("#F59E0B")
            icon_color = QColor("#D97706")
            icon_bg = QColor(245, 158, 11, 28)
            text_color = QColor("#B45309")
            sub_text = "CONNECTING • CANCEL" if self._state == STATE_CONNECTING else "DISCONNECTING..."
        elif self._state == STATE_ERROR:
            grad_start = QColor("#FFFFFF")
            grad_end = QColor("#FEF2F2")
            border_color = QColor("#EF4444")
            icon_color = QColor("#DC2626")
            icon_bg = QColor(239, 68, 68, 25)
            text_color = QColor("#B91C1C")
            sub_text = "RETRY CONNECTION"
        else:
            grad_start = QColor("#FFFFFF")
            grad_end = QColor("#F0F9FF") if self._hover_t > 0.2 else QColor("#F8FAFC")
            border_color = QColor("#0284C7") if self._hover_t > 0.2 else QColor("#CBD5E1")
            icon_color = QColor("#0284C7")
            icon_bg = QColor(2, 132, 199, int(22 + self._hover_t * 18))
            text_color = QColor("#0369A1") if self._hover_t > 0.2 else QColor("#475569")
            sub_text = "CLICK TO CONNECT"

        # Dual concentric ripples when connected
        if self._state == STATE_CONNECTED:
            for offset in (0.0, math.pi):
                wave = ((self._pulse_phase + offset) % (math.pi * 2.0)) / (math.pi * 2.0)
                ripple_r = radius + 2.0 + wave * 13.0
                alpha = int(110 * (1.0 - wave))
                painter.setPen(QPen(QColor(16, 185, 129, max(alpha, 0)), 2.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(center, ripple_r, ripple_r)

        # Expanding tactile click shockwaves
        for sw in self._shockwaves:
            prog = sw["progress"]
            sw_r = radius + 2.0 + prog * sw.get("max_span", 28.0)
            alpha = int((1.0 - prog) * 160)
            if alpha > 0:
                sw_col = QColor(245, 158, 11, alpha) if sw.get("is_disconnect") else QColor(16, 185, 129, alpha)
                painter.setPen(QPen(sw_col, max(1.0, 2.8 * (1.0 - prog * 0.5)), Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(center, sw_r, sw_r)

        # Soft outer elevation halo
        halo_alpha = int(28 + self._hover_t * 24)
        halo_color = QColor(border_color.red(), border_color.green(), border_color.blue(), halo_alpha)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(halo_color))
        painter.drawEllipse(center + QPointF(0, 4), radius + 5.0, radius + 5.0)

        # Main frosted ceramic circle
        radial = QRadialGradient(center - QPointF(0, radius * 0.25), radius * 1.25)
        radial.setColorAt(0.0, grad_start)
        radial.setColorAt(1.0, grad_end)
        painter.setBrush(QBrush(radial))
        painter.setPen(QPen(border_color, 2.5))
        painter.drawEllipse(center, radius, radius)

        # Rotating orbital arc while connecting/disconnecting
        if self._state in (STATE_CONNECTING, STATE_DISCONNECTING):
            arc_r = radius + 6.5
            arc_rect = QRectF(center.x() - arc_r, center.y() - arc_r, arc_r * 2.0, arc_r * 2.0)
            painter.setPen(QPen(QColor("#F59E0B"), 3.0, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(arc_rect, int(-self._orbit_angle * 16), 95 * 16)
            painter.setPen(QPen(QColor(245, 158, 11, 90), 2.0, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(arc_rect, int((-self._orbit_angle + 180) * 16), 60 * 16)

        # Soft circular badge behind Power icon
        icon_center = QPointF(center.x(), center.y() - 12.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(icon_bg))
        painter.drawEllipse(icon_center, 25.0, 25.0)

        # Power icon symbol
        icon_r = 14.5
        painter.setPen(QPen(icon_color, 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(
            QRectF(icon_center.x() - icon_r, icon_center.y() - icon_r, icon_r * 2, icon_r * 2),
            48 * 16,
            264 * 16,
        )
        painter.drawLine(
            QPointF(icon_center.x(), icon_center.y() - 17.5),
            QPointF(icon_center.x(), icon_center.y() - 3.5),
        )

        # Status text below icon
        painter.setPen(text_color)
        font = QFont("-apple-system", 7, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.7)
        painter.setFont(font)
        text_rect = QRectF(rect.left() + 10, center.y() + 20, rect.width() - 20, 26)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, sub_text)


class InteractiveTunnelModelWidget(QFrame):
    """
    Interactive live 4-hop Linux VPN packet-pipeline model:
        [Linux Apps] ---> [tun0 L3] ---> [sslocal] ---> [VPN Node]
    Real Connection Stages:
        1. Resolving VPN Node & checking physical route
        2. Starting Shadowsocks SOCKS5 daemon (sslocal)
        3. Provisioning Virtual L3 interface (tun0) & IPv6 leak shield
        4. Securing Linux Kernel routing table & DNS
        5. Live Flow Active with real-time throughput-driven animations
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(112)
        self.setMaximumHeight(120)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)

        self._state = STATE_DISCONNECTED
        self._stage = "idle"  # "idle", "resolving", "sslocal", "tun0", "routing", "connected", "teardown", "error"
        self._stage_info: Dict[str, Any] = {}
        self._selected_idx = 1  # Default highlight: tun0 L3
        self._hover_idx = -1
        self._packet_t = 0.0
        self._pulse_t = 0.0
        self._rx_bps = 0.0
        self._tx_bps = 0.0
        self._node_centers: List[QPointF] = []

        # Interactive modeling & click animation state
        self._modeling_mode: str = "none"  # "none", "connecting", "disconnecting"
        self._modeling_t: float = 0.0
        self._node_bursts: List[float] = [0.0, 0.0, 0.0, 0.0]
        self._node_click_ripples: List[Dict[str, Any]] = []

        self._meta: Dict[str, Any] = {
            "profile_name": "No Server",
            "server": "--",
            "port": "--",
            "method": "chacha20-ietf-poly1305",
            "dns": "1.1.1.1",
            "socks": "127.0.0.1:1080",
            "gateway_ip": None,
            "physical_dev": None,
            "ipv6_disabled": False,
            "ping_ms": None,
            "duration_str": "00:00",
            "rx_speed_str": "0 B/s",
            "tx_speed_str": "0 B/s",
            "rx_total_str": "0 B",
            "tx_total_str": "0 B",
            "error": "",
        }

        self._nodes = [
            {"id": "apps", "label": "Linux Apps", "tag": "L4 TCP/UDP"},
            {"id": "tun0", "label": "tun0 L3", "tag": "10.0.0.2"},
            {"id": "sslocal", "label": "sslocal", "tag": "SOCKS5"},
            {"id": "server", "label": "VPN Node", "tag": "Encrypted"},
        ]

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(35)

    def set_model_state(self, state: str, meta: Optional[Dict[str, Any]] = None):
        self._state = state
        if state == STATE_CONNECTED:
            self._stage = "connected"
        elif state == STATE_DISCONNECTED:
            self._stage = "idle"
            self._rx_bps = 0.0
            self._tx_bps = 0.0
        elif state == STATE_ERROR:
            self._stage = "error"
            self._rx_bps = 0.0
            self._tx_bps = 0.0

        if meta:
            self._meta.update(meta)
        self.update()

    def set_connection_stage(self, stage_data: Dict[str, Any]):
        self._stage = stage_data.get("stage", self._stage)
        self._stage_info = stage_data
        msg = stage_data.get("message")
        if msg:
            self._meta["status_msg"] = msg
        err = stage_data.get("error")
        if err:
            self._meta["error"] = err
        self.update()

    def update_telemetry(self, stats: Dict[str, Any]):
        self._rx_bps = stats.get("rx_speed_bps", 0.0)
        self._tx_bps = stats.get("tx_speed_bps", 0.0)
        self._meta["rx_speed_str"] = stats.get("rx_speed_str", "0 B/s")
        self._meta["tx_speed_str"] = stats.get("tx_speed_str", "0 B/s")
        self._meta["rx_total_str"] = stats.get("rx_total_str", "0 B")
        self._meta["tx_total_str"] = stats.get("tx_total_str", "0 B")
        self._meta["duration_str"] = stats.get("duration_str", "00:00")
        self.update()

    def trigger_connect_modeling(self):
        """Trigger sequential energetic photon beam animation across the 4 nodes."""
        self._modeling_mode = "connecting"
        self._modeling_t = 0.0
        self._node_bursts = [1.0, 0.0, 0.0, 0.0]
        self.update()

    def trigger_disconnect_modeling(self):
        """Trigger reverse dissolution teardown wave sweeping across the nodes."""
        self._modeling_mode = "disconnecting"
        self._modeling_t = 0.0
        self._node_bursts = [0.0, 0.0, 0.0, 1.0]
        self.update()

    def _tick(self):
        needs_update = False

        # Advance modeling animation
        if self._modeling_mode == "connecting":
            self._modeling_t += 0.038
            if self._modeling_t >= 0.33 and self._node_bursts[1] == 0.0:
                self._node_bursts[1] = 1.0
            if self._modeling_t >= 0.66 and self._node_bursts[2] == 0.0:
                self._node_bursts[2] = 1.0
            if self._modeling_t >= 0.95 and self._node_bursts[3] == 0.0:
                self._node_bursts[3] = 1.0

            if self._modeling_t >= 1.0:
                self._modeling_mode = "none"
                self._modeling_t = 0.0
            needs_update = True

        elif self._modeling_mode == "disconnecting":
            self._modeling_t += 0.042
            if self._modeling_t >= 0.33 and self._node_bursts[2] == 0.0:
                self._node_bursts[2] = 1.0
            if self._modeling_t >= 0.66 and self._node_bursts[1] == 0.0:
                self._node_bursts[1] = 1.0
            if self._modeling_t >= 0.95 and self._node_bursts[0] == 0.0:
                self._node_bursts[0] = 1.0

            if self._modeling_t >= 1.0:
                self._modeling_mode = "none"
                self._modeling_t = 0.0
            needs_update = True

        # Decay node acoustic bursts
        for i in range(4):
            if self._node_bursts[i] > 0.0:
                self._node_bursts[i] = max(0.0, self._node_bursts[i] - 0.055)
                needs_update = True

        # Advance direct node click ripples
        if self._node_click_ripples:
            active_ripples = []
            for rip in self._node_click_ripples:
                rip["progress"] += 0.075
                if rip["progress"] < 1.0:
                    active_ripples.append(rip)
            self._node_click_ripples = active_ripples
            needs_update = True

        if self._state == STATE_CONNECTED:
            # Packet animation step scales with real throughput
            throughput = self._rx_bps + self._tx_bps
            speed_mult = min(throughput / 4_000_000.0, 0.045)
            step = 0.020 + speed_mult
            self._packet_t = (self._packet_t + step) % 1.0
            needs_update = True
        elif self._state in (STATE_CONNECTING, STATE_DISCONNECTING):
            self._packet_t = (self._packet_t + 0.035) % 1.0
            self._pulse_t = (self._pulse_t + 0.08) % (math.pi * 2.0)
            needs_update = True

        if needs_update:
            self.update()

    def _hit_test(self, pos: QPointF) -> int:
        for idx, c in enumerate(self._node_centers):
            dx = pos.x() - c.x()
            dy = pos.y() - c.y()
            if dx * dx + dy * dy <= 28 * 28:
                return idx
        return -1

    def mouseMoveEvent(self, event):
        idx = self._hit_test(QPointF(event.pos()))
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_idx != -1:
            self._hover_idx = -1
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            idx = self._hit_test(QPointF(event.pos()))
            if idx != -1:
                self._selected_idx = idx
                self._node_click_ripples.append({
                    "node_idx": idx,
                    "progress": 0.0,
                })
                self._node_bursts[idx] = 1.0
                self.update()
        super().mousePressEvent(event)

    def _get_node_status(self, idx: int) -> str:
        """Returns: 'active', 'connecting', 'standby', 'inactive', 'error'."""
        if self._state == STATE_ERROR:
            return "error"
        if self._state == STATE_CONNECTED:
            return "active"
        if self._state == STATE_DISCONNECTING:
            return "connecting"

        if self._state == STATE_CONNECTING:
            stage = self._stage
            if stage == "resolving":
                if idx == 3: return "connecting"
                if idx == 0: return "standby"
                return "inactive"
            elif stage == "sslocal":
                if idx == 3: return "active"
                if idx == 2: return "connecting"
                if idx == 0: return "standby"
                return "inactive"
            elif stage == "tun0":
                if idx in (2, 3): return "active"
                if idx == 1: return "connecting"
                return "standby"
            elif stage == "routing":
                if idx in (1, 2, 3): return "active"
                if idx == 0: return "connecting"
                return "active"
            elif stage == "verifying":
                if idx in (0, 1, 2): return "active"
                return "connecting"
            return "connecting"

        # STATE_DISCONNECTED
        if idx == 0:
            return "standby"
        elif idx == 3:
            return "standby"
        return "inactive"

    def _get_link_status(self, seg_idx: int) -> str:
        """Returns: 'active', 'connecting', 'inactive', 'error'."""
        if self._state == STATE_ERROR:
            return "error"
        if self._state == STATE_CONNECTED:
            return "active"
        if self._state == STATE_DISCONNECTING:
            return "connecting"

        if self._state == STATE_CONNECTING:
            stage = self._stage
            if stage == "resolving":
                return "connecting" if seg_idx == 2 else "inactive"
            elif stage == "sslocal":
                return "active" if seg_idx == 2 else ("connecting" if seg_idx == 1 else "inactive")
            elif stage == "tun0":
                return "active" if seg_idx in (1, 2) else ("connecting" if seg_idx == 0 else "inactive")
            elif stage == "routing":
                return "active"
            elif stage == "verifying":
                return "connecting"
            return "connecting"

        return "inactive"

    def _inspector_text(self) -> str:
        idx = self._hover_idx if self._hover_idx != -1 else self._selected_idx
        idx = max(0, min(idx, 3))
        node_id = self._nodes[idx]["id"]
        is_conn = self._state == STATE_CONNECTED
        is_busy = self._state == STATE_CONNECTING
        is_err = self._state == STATE_ERROR

        if is_err:
            err = self._meta.get("error") or "Connection error occurred"
            return f"Error • {err}"

        if node_id == "apps":
            if is_conn:
                rx_str = self._meta.get("rx_speed_str", "0 B/s")
                tx_str = self._meta.get("tx_speed_str", "0 B/s")
                return f"Linux Apps • 100% Full-Tunnel Captured • DNS {self._meta.get('dns', '1.1.1.1')} • Live: ↓ {rx_str}  ↑ {tx_str}"
            elif is_busy and self._stage == "verifying":
                return "Linux Apps • Verifying real internet & DNS reachability through tun0..."
            elif is_busy:
                return f"Linux Apps • Preparing kernel default route redirect -> tun0 (10.0.0.2/24)"
            else:
                gw = self._meta.get("gateway_ip") or "Default"
                dev = self._meta.get("physical_dev") or "NIC"
                return f"Linux Apps • Direct Physical Route • Gateway: {gw} ({dev}) • Standard DNS"

        if node_id == "tun0":
            if is_conn:
                ipv6_tag = "IPv6 Shield Active" if self._meta.get("ipv6_disabled") else "IPv6 Active"
                rx_tot = self._meta.get("rx_total_str", "0 B")
                tx_tot = self._meta.get("tx_total_str", "0 B")
                return f"tun0 L3 • 10.0.0.2/24 • {ipv6_tag} • Total: {rx_tot} ↓ / {tx_tot} ↑"
            elif is_busy:
                return f"tun0 L3 • Provisioning Layer 3 interface & IPv6 leak shield..."
            else:
                return f"tun0 L3 • Interface Standby • IPv6 Guard Ready • 10.0.0.2/24"

        if node_id == "sslocal":
            socks = self._meta.get("socks", "127.0.0.1:1080")
            method = self._meta.get("method", "chacha20-ietf-poly1305")
            if is_conn:
                return f"sslocal • SOCKS5 {socks} • Cipher: {method} • shadowsocks-rust daemon"
            elif is_busy:
                return f"sslocal • Launching SOCKS5 proxy daemon on {socks} with {method}..."
            else:
                return f"sslocal • SOCKS5 Daemon Stopped • Configured for {socks}"

        # node_id == "server"
        prof_name = self._meta.get("profile_name", "No Server")
        srv = self._meta.get("server", "--")
        port = self._meta.get("port", "--")
        ping = self._meta.get("ping_ms")
        ping_str = f"{ping}ms" if isinstance(ping, int) and ping >= 0 else "--"
        dur = self._meta.get("duration_str", "00:00")

        if is_conn:
            return f"VPN Node • {prof_name} ({srv}:{port}) • Latency: {ping_str} • Uptime: {dur}"
        elif is_busy and self._stage == "verifying":
            return f"VPN Node • Probing internet & DNS traffic via {prof_name} ({srv}:{port})..."
        elif is_busy:
            return f"VPN Node • Resolving {srv} & handshaking via physical gateway..."
        else:
            return f"VPN Node • {prof_name} ({srv}:{port}) • Latency: {ping_str} • Standby"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        # Card background
        painter.setBrush(QBrush(QColor("#F8FAFC")))
        painter.setPen(QPen(QColor("#E2E8F0"), 1.0))
        painter.drawRoundedRect(rect, 12.0, 12.0)

        # Header micro-caption
        painter.setPen(QColor("#64748B"))
        header_font = QFont("monospace", 7, QFont.Bold)
        painter.setFont(header_font)
        painter.drawText(QRectF(12, 6, rect.width() - 24, 14), Qt.AlignLeft | Qt.AlignVCenter, "INTERACTIVE TUNNEL MODEL")

        # Top-right real connection stage badge
        if self._state == STATE_CONNECTED:
            badge_text = "LIVE FLOW"
            badge_color = QColor("#059669")
        elif self._state == STATE_CONNECTING:
            stage = self._stage
            total = self._stage_info.get("stage_total", 5) if isinstance(self._stage_info, dict) else 5
            if stage == "resolving":
                badge_text = f"1/{total}: RESOLVING NODE"
            elif stage == "sslocal":
                badge_text = f"2/{total}: SOCKS5 CORE"
            elif stage == "tun0":
                badge_text = f"3/{total}: TUNNEL ARMED"
            elif stage == "routing":
                badge_text = f"4/{total}: ROUTES & DNS"
            elif stage == "verifying":
                badge_text = f"5/{total}: VERIFYING NET"
            else:
                badge_text = "HANDSHAKE"
            badge_color = QColor("#D97706")
        elif self._state == STATE_DISCONNECTING:
            badge_text = "TEARDOWN..."
            badge_color = QColor("#D97706")
        elif self._state == STATE_ERROR:
            badge_text = "CONNECTION FAILED"
            badge_color = QColor("#DC2626")
        else:
            badge_text = "IDLE • PHYSICAL ROUTE"
            badge_color = QColor("#64748B")

        painter.setPen(badge_color)
        painter.drawText(QRectF(12, 6, rect.width() - 24, 14), Qt.AlignRight | Qt.AlignVCenter, badge_text)

        # Compute 4 node centers
        margin_x = 46.0
        span_w = max(rect.width() - margin_x * 2.0, 100.0)
        y_center = 48.0
        self._node_centers = [
            QPointF(margin_x + (span_w * i) / 3.0, y_center)
            for i in range(4)
        ]

        # Draw connecting links & animated packets
        for i in range(3):
            p1 = self._node_centers[i]
            p2 = self._node_centers[i + 1]

            if self._modeling_mode == "connecting":
                # Background track line
                painter.setPen(QPen(QColor("#CBD5E1"), 1.6, Qt.DashLine, Qt.RoundCap))
                painter.drawLine(p1, p2)

                seg_start = i / 3.0
                if self._modeling_t > seg_start:
                    frac = min(1.0, (self._modeling_t - seg_start) / (1.0 / 3.0))
                    p_head = QPointF(p1.x() + (p2.x() - p1.x()) * frac, p1.y())
                    # Glowing wavefront halo
                    painter.setPen(QPen(QColor(16, 185, 129, 65), 5.5, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(p1, p_head)
                    # Core energetic beam
                    painter.setPen(QPen(QColor("#10B981"), 2.6, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(p1, p_head)
                    # Leading photon head
                    if frac < 1.0:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QBrush(QColor(52, 211, 153, 130)))
                        painter.drawEllipse(p_head, 8.5, 8.5)
                        painter.setBrush(QBrush(QColor("#FFFFFF")))
                        painter.drawEllipse(p_head, 3.5, 3.5)

            elif self._modeling_mode == "disconnecting":
                # Background track line
                painter.setPen(QPen(QColor("#CBD5E1"), 1.6, Qt.DashLine, Qt.RoundCap))
                painter.drawLine(p1, p2)

                t_rem = 1.0 - self._modeling_t
                seg_start = i / 3.0
                if t_rem > seg_start:
                    frac = min(1.0, (t_rem - seg_start) / (1.0 / 3.0))
                    p_head = QPointF(p1.x() + (p2.x() - p1.x()) * frac, p1.y())
                    painter.setPen(QPen(QColor(245, 158, 11, 60), 4.0, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(p1, p_head)
                    painter.setPen(QPen(QColor("#F59E0B"), 2.0, Qt.DashLine, Qt.RoundCap))
                    painter.drawLine(p1, p_head)
                    if frac < 1.0:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QBrush(QColor(239, 68, 68, 110)))
                        painter.drawEllipse(p_head, 7.0, 7.0)
                        painter.setBrush(QBrush(QColor("#FDE68A")))
                        painter.drawEllipse(p_head, 3.0, 3.0)

            else:
                status = self._get_link_status(i)
                if status == "active":
                    painter.setPen(QPen(QColor("#10B981"), 2.2, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(p1, p2)
                    # Staggered animated packets
                    for offset in (0.0, 0.5):
                        t = (self._packet_t + offset + i * 0.16) % 1.0
                        px = p1.x() + (p2.x() - p1.x()) * t
                        py = p1.y()
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QBrush(QColor(16, 185, 129, 75)))
                        painter.drawEllipse(QPointF(px, py), 6.5, 6.5)
                        painter.setBrush(QBrush(QColor("#059669")))
                        painter.drawEllipse(QPointF(px, py), 3.0, 3.0)
                elif status == "connecting":
                    painter.setPen(QPen(QColor("#F59E0B"), 2.0, Qt.SolidLine, Qt.RoundCap))
                    painter.drawLine(p1, p2)
                    # Handshake pulse packet
                    t = (self._packet_t + i * 0.22) % 1.0
                    px = p1.x() + (p2.x() - p1.x()) * t
                    py = p1.y()
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(245, 158, 11, 80)))
                    painter.drawEllipse(QPointF(px, py), 6.0, 6.0)
                    painter.setBrush(QBrush(QColor("#D97706")))
                    painter.drawEllipse(QPointF(px, py), 3.0, 3.0)
                elif status == "error":
                    painter.setPen(QPen(QColor("#FCA5A5"), 1.6, Qt.DashLine, Qt.RoundCap))
                    painter.drawLine(p1, p2)
                else:
                    painter.setPen(QPen(QColor("#CBD5E1"), 1.6, Qt.DashLine, Qt.RoundCap))
                    painter.drawLine(p1, p2)

        # Draw nodes
        label_font = QFont("-apple-system", 7, QFont.Bold)
        for idx, node in enumerate(self._nodes):
            c = self._node_centers[idx]
            is_sel = idx == self._selected_idx
            is_hov = idx == self._hover_idx
            n_status = self._get_node_status(idx)

            # Outer ring & glow
            if n_status == "active":
                if is_sel or is_hov:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(16, 185, 129, 45)))
                    painter.drawEllipse(c, 19.0, 19.0)
                stroke_col = QColor("#059669") if is_sel else QColor("#10B981")
                inner_col = QColor("#059669")
            elif n_status == "connecting":
                glow_r = 16.0 + 3.0 * math.sin(self._pulse_t)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(245, 158, 11, 55)))
                painter.drawEllipse(c, glow_r, glow_r)
                stroke_col = QColor("#D97706")
                inner_col = QColor("#D97706")
            elif n_status == "error":
                if is_sel or is_hov:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(239, 68, 68, 45)))
                    painter.drawEllipse(c, 19.0, 19.0)
                stroke_col = QColor("#EF4444")
                inner_col = QColor("#DC2626")
            else:
                # Standby or Inactive
                if is_sel or is_hov:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(2, 132, 199, 40)))
                    painter.drawEllipse(c, 19.0, 19.0)
                stroke_col = QColor("#0284C7") if is_sel else (QColor("#94A3B8") if n_status == "standby" else QColor("#CBD5E1"))
                inner_col = QColor("#0284C7") if is_sel else (QColor("#64748B") if n_status == "standby" else QColor("#94A3B8"))

            # Acoustic shockwave burst on node
            burst = self._node_bursts[idx]
            if burst > 0.01:
                burst_r = 13.5 + (1.0 - burst) * 16.0
                alpha = int(burst * 170)
                b_col = QColor(245, 158, 11, alpha) if self._modeling_mode == "disconnecting" else QColor(16, 185, 129, alpha)
                painter.setPen(QPen(b_col, max(1.2, 2.6 * burst), Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(c, burst_r, burst_r)

            # Direct tactile click ripple on node
            for rip in self._node_click_ripples:
                if rip.get("node_idx") == idx:
                    r_prog = rip["progress"]
                    rip_r = 13.5 + r_prog * 18.0
                    r_alpha = int((1.0 - r_prog) * 160)
                    painter.setPen(QPen(QColor(2, 132, 199, r_alpha), max(1.0, 2.2 * (1.0 - r_prog)), Qt.SolidLine))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(c, rip_r, rip_r)

            # White node body with border
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.setPen(QPen(stroke_col, 2.0 if is_sel else 1.5))
            painter.drawEllipse(c, 13.5, 13.5)

            # Center dot
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(inner_col))
            painter.drawEllipse(c, 4.5, 4.5)

            # Node label below circle
            painter.setFont(label_font)
            painter.setPen(QColor("#0F172A") if is_sel else QColor("#475569"))
            painter.drawText(QRectF(c.x() - 36, c.y() + 15, 72, 15), Qt.AlignCenter, node["label"])

        # Inspector footer pill
        pill_rect = QRectF(10, rect.height() - 25, rect.width() - 20, 19)
        if self._state == STATE_CONNECTED:
            pill_bg = QColor("#ECFDF5")
            pill_border = QColor("#A7F3D0")
            pill_fg = QColor("#047857")
        elif self._state in (STATE_CONNECTING, STATE_DISCONNECTING):
            pill_bg = QColor("#FFFBEB")
            pill_border = QColor("#FDE68A")
            pill_fg = QColor("#B45309")
        elif self._state == STATE_ERROR:
            pill_bg = QColor("#FEF2F2")
            pill_border = QColor("#FCA5A5")
            pill_fg = QColor("#B91C1C")
        else:
            pill_bg = QColor("#F1F5F9")
            pill_border = QColor("#E2E8F0")
            pill_fg = QColor("#475569")

        painter.setBrush(QBrush(pill_bg))
        painter.setPen(QPen(pill_border, 1.0))
        painter.drawRoundedRect(pill_rect, 6.0, 6.0)

        painter.setFont(QFont("monospace", 7, QFont.DemiBold))
        painter.setPen(pill_fg)
        fm = painter.fontMetrics()
        elided = fm.elidedText(self._inspector_text(), Qt.ElideRight, int(pill_rect.width() - 16))
        painter.drawText(pill_rect.adjusted(8, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, elided)


class MiniSparkline(QWidget):
    """Lightweight animated throughput waveform for speed telemetry cards."""

    def __init__(self, line_color: str = "#0284C7", fill_color: str = "rgba(2,132,199,35)", parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self._values = deque([0.0] * 18, maxlen=18)
        self._line_color = QColor(line_color)
        self._fill_rgba = fill_color

    def push_value(self, bps: float):
        self._values.append(max(float(bps), 0.0))
        self.update()

    def clear(self):
        self._values = deque([0.0] * 18, maxlen=18)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        vals = list(self._values)
        max_v = max(max(vals), 1024.0)

        path = QPainterPath()
        fill_path = QPainterPath()
        n = len(vals)
        step_x = w / max(n - 1, 1)

        for i, v in enumerate(vals):
            x = i * step_x
            norm = min(v / max_v, 1.0)
            y = h - 3.0 - norm * (h - 6.0)
            if i == 0:
                path.moveTo(x, y)
                fill_path.moveTo(x, h)
                fill_path.lineTo(x, y)
            else:
                path.lineTo(x, y)
                fill_path.lineTo(x, y)

        fill_path.lineTo(w, h)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, 0, 0, h)
        top_c = QColor(self._line_color)
        top_c.setAlpha(60)
        bot_c = QColor(self._line_color)
        bot_c.setAlpha(4)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(fill_path)

        painter.setPen(QPen(self._line_color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)


class ModernDropdown(QPushButton):
    """
    Clean Daylight Dropdown Selector using a styled frameless QMenu.
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
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 5px;
                color: #0F172A;
            }
            QMenu#ModernDropdownMenu::item {
                background-color: transparent;
                padding: 8px 14px;
                border-radius: 7px;
                color: #1E293B;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            }
            QMenu#ModernDropdownMenu::item:selected {
                background-color: #E0F2FE;
                color: #0369A1;
                font-weight: bold;
            }
        """)
        self.setMenu(self.menu)
        self.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 9px 12px;
                color: #0F172A;
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
                text-align: left;
            }
            QPushButton:hover {
                border: 1px solid #0284C7;
                background-color: #F0F9FF;
                color: #0369A1;
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


class ModernDeleteConfirmDialog(QDialog):
    """
    Daylight-themed confirmation modal for server profile deletion.
    """

    def __init__(self, profile_data: dict, is_connected: bool, is_active: bool, is_only: bool, parent=None):
        super().__init__(parent)
        self.profile_data = profile_data or {}
        self.is_connected = is_connected
        self.is_active = is_active
        self.is_only = is_only
        self._drag_pos = None

        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(450)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)

        self.container = QFrame(self)
        self.container.setObjectName("ModernConfirmCard")
        self.container.setStyleSheet("""
            QFrame#ModernConfirmCard {
                background-color: #FFFFFF;
                border: 1px solid #FECACA;
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(15, 23, 42, 48))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        card_vbox = QVBoxLayout(self.container)
        card_vbox.setContentsMargins(20, 18, 20, 20)
        card_vbox.setSpacing(14)

        # Header
        header_hbox = QHBoxLayout()
        header_hbox.setSpacing(12)

        icon_badge = QLabel("🗑")
        icon_badge.setFixedSize(40, 40)
        icon_badge.setAlignment(Qt.AlignCenter)
        icon_badge.setStyleSheet("""
            background-color: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 20px;
            font-size: 18px;
            color: #DC2626;
        """)
        header_hbox.addWidget(icon_badge)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        lbl_title = QLabel("Delete Server Profile")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0F172A;")
        title_vbox.addWidget(lbl_title)

        lbl_sub = QLabel("Are you sure you want to delete this configuration?")
        lbl_sub.setStyleSheet("font-size: 11px; color: #64748B;")
        title_vbox.addWidget(lbl_sub)

        header_hbox.addLayout(title_vbox, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(26, 26)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748B;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                color: #DC2626;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_hbox.addWidget(btn_close)

        card_vbox.addLayout(header_hbox)

        # Server metadata box
        prof_name = html.escape(str(self.profile_data.get("name", "Unnamed Profile")))
        server_ip = str(self.profile_data.get("server", "Unknown Host"))
        server_port = str(self.profile_data.get("server_port", ""))
        method = str(self.profile_data.get("method", "aes-256-gcm"))
        prefix = self.profile_data.get("prefix", "")

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        info_vbox = QVBoxLayout(info_frame)
        info_vbox.setContentsMargins(12, 10, 12, 10)
        info_vbox.setSpacing(8)

        lbl_prof_name = QLabel(f"<b>Profile:</b> {prof_name}")
        lbl_prof_name.setStyleSheet("font-size: 12px; color: #0F172A; font-weight: 600;")
        info_vbox.addWidget(lbl_prof_name)

        badges_hbox = QHBoxLayout()
        badges_hbox.setSpacing(8)

        endpoint_str = f"🌐 {server_ip}" + (f":{server_port}" if server_port else "")
        lbl_endpoint = QLabel(endpoint_str)
        lbl_endpoint.setStyleSheet("""
            background-color: #E0F2FE;
            color: #0369A1;
            border: 1px solid #BAE6FD;
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 10px;
            font-family: monospace;
            font-weight: 600;
        """)
        badges_hbox.addWidget(lbl_endpoint)

        lbl_method = QLabel(f"🔒 {method}")
        lbl_method.setStyleSheet("""
            background-color: #F3E8FF;
            color: #7E22CE;
            border: 1px solid #E9D5FF;
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 10px;
            font-family: monospace;
            font-weight: 600;
        """)
        badges_hbox.addWidget(lbl_method)

        if prefix:
            lbl_anti = QLabel("🛡️ Anti-DPI")
            lbl_anti.setStyleSheet("""
                background-color: #ECFDF5;
                color: #047857;
                border: 1px solid #A7F3D0;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 10px;
                font-family: monospace;
                font-weight: 600;
            """)
            badges_hbox.addWidget(lbl_anti)

        badges_hbox.addStretch(1)
        info_vbox.addLayout(badges_hbox)

        card_vbox.addWidget(info_frame)

        # Contextual warning
        if self.is_connected:
            warn_frame = QFrame()
            warn_frame.setStyleSheet("""
                QFrame {
                    background-color: #FEF2F2;
                    border: 1px solid #FECACA;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            warn_hbox = QHBoxLayout(warn_frame)
            warn_hbox.setContentsMargins(10, 8, 10, 8)
            warn_hbox.setSpacing(8)

            lbl_warn_ico = QLabel("⚠️")
            lbl_warn_ico.setStyleSheet("font-size: 15px; background: transparent;")
            warn_hbox.addWidget(lbl_warn_ico)

            lbl_warn_msg = QLabel("<b>Active Tunnel Warning:</b> You are currently connected to this server. Deleting it will immediately terminate the VPN connection.")
            lbl_warn_msg.setStyleSheet("color: #991B1B; font-size: 11px; background: transparent;")
            lbl_warn_msg.setWordWrap(True)
            warn_hbox.addWidget(lbl_warn_msg, 1)
            card_vbox.addWidget(warn_frame)
        elif self.is_only:
            notice_frame = QFrame()
            notice_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFFBEB;
                    border: 1px solid #FDE68A;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            notice_hbox = QHBoxLayout(notice_frame)
            notice_hbox.setContentsMargins(10, 8, 10, 8)
            notice_hbox.setSpacing(8)

            lbl_notice_ico = QLabel("ℹ️")
            lbl_notice_ico.setStyleSheet("font-size: 14px; background: transparent;")
            notice_hbox.addWidget(lbl_notice_ico)

            lbl_notice_msg = QLabel("This is your only configured server profile. You will need to import a new profile to connect.")
            lbl_notice_msg.setStyleSheet("color: #92400E; font-size: 11px; background: transparent;")
            lbl_notice_msg.setWordWrap(True)
            notice_hbox.addWidget(lbl_notice_msg, 1)
            card_vbox.addWidget(notice_frame)

        # Action buttons
        btn_hbox = QHBoxLayout()
        btn_hbox.setSpacing(10)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                color: #334155;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #94A3B8;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_cancel.setDefault(True)
        btn_hbox.addWidget(self.btn_cancel)

        self.btn_delete = QPushButton("🗑 Delete Profile")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setFixedHeight(38)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                border: 1px solid #DC2626;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 700;
                padding: 0 18px;
            }
            QPushButton:hover {
                background-color: #B91C1C;
                border: 1px solid #B91C1C;
            }
        """)
        self.btn_delete.clicked.connect(self.accept)
        btn_hbox.addWidget(self.btn_delete)

        card_vbox.addLayout(btn_hbox)
        root_layout.addWidget(self.container)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.btn_cancel.hasFocus():
                self.reject()
            else:
                self.accept()
        else:
            super().keyPressEvent(event)


def get_app_icon() -> QIcon:
    """Finds or creates a guaranteed non-null QIcon for Window and Tray."""
    possible_paths = [
        os.path.join(BASE_DIR, "gui", "assets", "icon.png"),
        os.path.join(BASE_DIR, "gui", "assets", "icon.svg"),
        os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/auralink.png"),
        os.path.expanduser("~/.local/share/icons/auralink.png"),
        os.path.expanduser("~/.local/share/pixmaps/auralink.png"),
        "/opt/auralink/gui/assets/icon.png",
        "/opt/auralink/gui/assets/icon.svg",
        "/usr/share/pixmaps/auralink.png",
        "/usr/share/icons/hicolor/256x256/apps/auralink.png",
        "/usr/share/icons/hicolor/scalable/apps/auralink.svg",
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
    painter.setBrush(QBrush(QColor("#0284C7")))
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
        self.signals.stage_changed.connect(self.on_stage_changed)
        self.signals.stats_updated.connect(self.on_stats_updated)
        self.signals.log_updated.connect(self.on_log_updated)
        self.signals.ping_result.connect(self.on_ping_result)
        self.signals.log_message.connect(self._on_log_message_received)
        self.signals.import_finished.connect(self._on_import_finished)

        self.service.add_listener(self._service_listener)
        self.updating_combo = False
        self._last_ping_ms: Optional[int] = None
        self._last_verify_info: Dict[str, Any] = {}

        self.init_ui()
        self.init_tray()
        self.init_timers()

        self.update_profiles_list()
        self.refresh_ui_state()
        self.trigger_all_pings()

    def _service_listener(self, event_type: str, data: dict):
        if event_type == "stage_changed":
            self.signals.stage_changed.emit(data)
        else:
            self.signals.state_changed.emit(event_type, data)

        msg = data.get("message")
        err = data.get("error")
        if msg:
            self.signals.log_message.emit(f"[{event_type.upper()}] {msg}")
        elif err:
            self.signals.log_message.emit(f"[ERROR] {err}")

        if event_type == "connected" and data.get("verify_detail"):
            tag = "VERIFY" if data.get("verified", True) else "WARN"
            self.signals.log_message.emit(f"[{tag}] {data['verify_detail']}")

    def _apply_soft_shadow(self, widget: QWidget, blur: int = 20, alpha: int = 22):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setColor(QColor(15, 23, 42, alpha))
        shadow.setOffset(0, 4)
        widget.setGraphicsEffect(shadow)

    def init_ui(self):
        self.setWindowTitle("AuraLink VPN — Daylight")
        self.setWindowIcon(get_app_icon())
        self.resize(1080, 640)
        self.setMinimumSize(980, 580)
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

        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(6)
        for color in ("#EF4444", "#F59E0B", "#10B981"):
            dot = QLabel()
            dot.setFixedSize(11, 11)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
            dots_layout.addWidget(dot)
        header.addLayout(dots_layout)

        lbl_app_name = QLabel("AuraLink VPN")
        lbl_app_name.setStyleSheet("font-size: 14px; font-weight: 800; color: #0F172A; font-family: monospace; margin-left: 6px;")
        header.addWidget(lbl_app_name)

        lbl_badge = QLabel("DAYLIGHT")
        lbl_badge.setStyleSheet("background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; border-radius: 8px; padding: 2px 7px; font-size: 9.5px; font-weight: 700; font-family: monospace;")
        header.addWidget(lbl_badge)

        header.addStretch(1)

        # IPv6 Protection Pill
        self.ipv6_pill = QLabel("IPv6 GUARD READY")
        self.ipv6_pill.setStyleSheet("background-color: #F8FAFC; color: #64748B; border: 1px solid #CBD5E1; border-radius: 12px; padding: 4px 10px; font-size: 10px; font-weight: 700; font-family: monospace;")
        header.addWidget(self.ipv6_pill)

        # Status Pill Badge
        self.status_pill = QLabel("DISCONNECTED")
        self.status_pill.setProperty("class", "status-pill")
        header.addWidget(self.status_pill)

        # Window Action Controls
        win_controls = QHBoxLayout()
        win_controls.setSpacing(4)

        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setProperty("class", "btn-win-control")
        self.btn_minimize.setToolTip("Minimize to Tray")
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

        # LEFT PANEL: Animated Connect Hub + Interactive Tunnel Model + Speed Sparklines
        left_panel = QFrame()
        left_panel.setProperty("class", "surface")
        left_panel.setMinimumWidth(500)
        left_panel.setMaximumWidth(580)
        self._apply_soft_shadow(left_panel)
        left_vbox = QVBoxLayout(left_panel)
        left_vbox.setContentsMargins(18, 16, 18, 16)
        left_vbox.setSpacing(12)

        btn_wrapper = QVBoxLayout()
        btn_wrapper.setAlignment(Qt.AlignCenter)

        self.btn_circular = CircularConnectButton()
        self.btn_circular.clicked.connect(self.on_connect_toggle)
        btn_wrapper.addWidget(self.btn_circular, 0, Qt.AlignCenter)

        self.lbl_route_status = QLabel("System using standard physical route")
        self.lbl_route_status.setAlignment(Qt.AlignCenter)
        self.lbl_route_status.setWordWrap(True)
        self.lbl_route_status.setStyleSheet("font-size: 11px; color: #64748B; font-family: monospace; margin-top: 4px;")
        btn_wrapper.addWidget(self.lbl_route_status, 0, Qt.AlignCenter)

        left_vbox.addStretch(1)
        left_vbox.addLayout(btn_wrapper)
        left_vbox.addStretch(1)

        # Interactive 4-Hop Tunnel Pipeline Model
        self.tunnel_model = InteractiveTunnelModelWidget()
        left_vbox.addWidget(self.tunnel_model)
        left_vbox.addSpacing(8)

        # Bottom Speed Tiles Split Box with live sparklines
        speed_grid = QHBoxLayout()
        speed_grid.setSpacing(10)

        # Download Speed Tile
        card_down = QFrame()
        card_down.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;")
        cd_outer = QVBoxLayout(card_down)
        cd_outer.setContentsMargins(10, 8, 10, 8)
        cd_outer.setSpacing(5)

        cd_top = QHBoxLayout()
        cd_top.setSpacing(8)

        badge_down = QLabel("↓")
        badge_down.setAlignment(Qt.AlignCenter)
        badge_down.setFixedSize(30, 30)
        badge_down.setStyleSheet("background-color: #E0F2FE; color: #0284C7; border: 1px solid #BAE6FD; border-radius: 8px; font-weight: bold; font-size: 14px;")
        cd_top.addWidget(badge_down)

        down_info = QVBoxLayout()
        down_info.setSpacing(1)
        lbl_d_tag = QLabel("DOWNLOAD")
        lbl_d_tag.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px;")
        down_info.addWidget(lbl_d_tag)

        self.lbl_speed_down = QLabel("0 B/s")
        self.lbl_speed_down.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #0F172A; font-family: monospace;")
        down_info.addWidget(self.lbl_speed_down)
        cd_top.addLayout(down_info)
        cd_top.addStretch(1)

        total_d_box = QVBoxLayout()
        total_d_box.setSpacing(1)
        lbl_d_tot_tag = QLabel("SESSION")
        lbl_d_tot_tag.setAlignment(Qt.AlignRight)
        lbl_d_tot_tag.setStyleSheet("font-size: 8px; font-weight: 700; color: #94A3B8; font-family: monospace; letter-spacing: 0.5px;")
        total_d_box.addWidget(lbl_d_tot_tag)
        self.lbl_total_down = QLabel("0 B")
        self.lbl_total_down.setAlignment(Qt.AlignRight)
        self.lbl_total_down.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; font-family: monospace;")
        total_d_box.addWidget(self.lbl_total_down)
        cd_top.addLayout(total_d_box)

        cd_outer.addLayout(cd_top)
        self.spark_down = MiniSparkline(line_color="#0284C7")
        cd_outer.addWidget(self.spark_down)

        speed_grid.addWidget(card_down)

        # Upload Speed Tile
        card_up = QFrame()
        card_up.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;")
        cu_outer = QVBoxLayout(card_up)
        cu_outer.setContentsMargins(10, 8, 10, 8)
        cu_outer.setSpacing(5)

        cu_top = QHBoxLayout()
        cu_top.setSpacing(8)

        badge_up = QLabel("↑")
        badge_up.setAlignment(Qt.AlignCenter)
        badge_up.setFixedSize(30, 30)
        badge_up.setStyleSheet("background-color: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; border-radius: 8px; font-weight: bold; font-size: 14px;")
        cu_top.addWidget(badge_up)

        up_info = QVBoxLayout()
        up_info.setSpacing(1)
        lbl_u_tag = QLabel("UPLOAD")
        lbl_u_tag.setStyleSheet("font-size: 8.5px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px;")
        up_info.addWidget(lbl_u_tag)

        self.lbl_speed_up = QLabel("0 B/s")
        self.lbl_speed_up.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #0F172A; font-family: monospace;")
        up_info.addWidget(self.lbl_speed_up)
        cu_top.addLayout(up_info)
        cu_top.addStretch(1)

        total_u_box = QVBoxLayout()
        total_u_box.setSpacing(1)
        lbl_u_tot_tag = QLabel("SESSION")
        lbl_u_tot_tag.setAlignment(Qt.AlignRight)
        lbl_u_tot_tag.setStyleSheet("font-size: 8px; font-weight: 700; color: #94A3B8; font-family: monospace; letter-spacing: 0.5px;")
        total_u_box.addWidget(lbl_u_tot_tag)
        self.lbl_total_up = QLabel("0 B")
        self.lbl_total_up.setAlignment(Qt.AlignRight)
        self.lbl_total_up.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; font-family: monospace;")
        total_u_box.addWidget(self.lbl_total_up)
        cu_top.addLayout(total_u_box)

        cu_outer.addLayout(cu_top)
        self.spark_up = MiniSparkline(line_color="#059669")
        cu_outer.addWidget(self.spark_up)

        speed_grid.addWidget(card_up)

        left_vbox.addLayout(speed_grid)
        content_layout.addWidget(left_panel, 0)

        # RIGHT PANEL: Config Controls & Log Stream
        right_panel = QFrame()
        right_panel.setProperty("class", "surface")
        self._apply_soft_shadow(right_panel)
        right_vbox = QVBoxLayout(right_panel)
        right_vbox.setContentsMargins(14, 14, 14, 14)
        right_vbox.setSpacing(12)

        # 1. Active Subscription Node Box
        node_card = QFrame()
        node_card.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;")
        nc_vbox = QVBoxLayout(node_card)
        nc_vbox.setContentsMargins(12, 10, 12, 12)
        nc_vbox.setSpacing(8)

        node_header = QHBoxLayout()
        lbl_node_title = QLabel("ACTIVE SUBSCRIPTION NODE")
        lbl_node_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #475569; font-family: monospace; letter-spacing: 0.5px;")
        node_header.addWidget(lbl_node_title)
        node_header.addStretch(1)

        self.btn_ping_refresh = QPushButton("⟳ Ping")
        self.btn_ping_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_ping_refresh.setStyleSheet("background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; border-radius: 6px; padding: 3px 9px; font-size: 10px; font-weight: 700; font-family: monospace;")
        self.btn_ping_refresh.clicked.connect(self.trigger_all_pings)
        node_header.addWidget(self.btn_ping_refresh)
        nc_vbox.addLayout(node_header)

        server_row = QHBoxLayout()
        server_row.setSpacing(6)

        self.combo_servers = ModernDropdown("Select Server...")
        self.combo_servers.currentIndexChanged.connect(self.on_server_dropdown_changed)
        server_row.addWidget(self.combo_servers, 1)

        self.btn_delete_server = QPushButton("🗑 Delete")
        self.btn_delete_server.setCursor(Qt.PointingHandCursor)
        self.btn_delete_server.setToolTip("Delete currently selected server profile (Del)")
        self.btn_delete_server.setFixedHeight(38)
        self.btn_delete_server.setStyleSheet("""
            QPushButton {
                background-color: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 10px;
                padding: 0px 14px;
                font-size: 11px;
                font-weight: 700;
                font-family: monospace;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                color: #B91C1C;
                border: 1px solid #FCA5A5;
            }
            QPushButton:pressed {
                background-color: #DC2626;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border: 1px solid #E2E8F0;
            }
        """)
        self.btn_delete_server.clicked.connect(self.on_delete_server)
        server_row.addWidget(self.btn_delete_server)

        shortcut_del = QShortcut(QKeySequence(Qt.Key_Delete), self)
        shortcut_del.activated.connect(self.on_delete_server)

        nc_vbox.addLayout(server_row)

        # DNS Picker
        lbl_dns_title = QLabel("DNS UPSTREAM RESOLVER")
        lbl_dns_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; font-family: monospace; letter-spacing: 0.5px; margin-top: 4px;")
        nc_vbox.addWidget(lbl_dns_title)

        self.combo_dns = ModernDropdown("Select DNS...")
        preset_keys = list(DNS_PRESETS.keys())
        self.combo_dns.addItems(preset_keys)

        saved_preset = self.service.config_mgr.get_setting("dns_preset")
        saved_primary = self.service.config_mgr.get_setting("dns", "1.1.1.1")
        initial_idx = 0
        if saved_preset and saved_preset in preset_keys:
            initial_idx = preset_keys.index(saved_preset)
        elif saved_primary:
            for idx, p_key in enumerate(preset_keys):
                if DNS_PRESETS[p_key][0] == saved_primary:
                    initial_idx = idx
                    break
        self.combo_dns.setCurrentIndex(initial_idx)
        self.combo_dns.currentIndexChanged.connect(self.on_dns_changed)
        nc_vbox.addWidget(self.combo_dns)

        right_vbox.addWidget(node_card)

        # 2. Real-Time Log Stream Box
        log_card = QFrame()
        log_card.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;")
        lc_vbox = QVBoxLayout(log_card)
        lc_vbox.setContentsMargins(12, 10, 12, 10)
        lc_vbox.setSpacing(6)

        log_header = QHBoxLayout()
        lbl_log_title = QLabel(">_ Real-Time Log Stream")
        lbl_log_title.setStyleSheet("font-size: 10.5px; font-weight: 700; color: #334155; font-family: monospace;")
        log_header.addWidget(lbl_log_title)
        log_header.addStretch(1)

        self.btn_clear_logs = QPushButton("Clear")
        self.btn_clear_logs.setCursor(Qt.PointingHandCursor)
        self.btn_clear_logs.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                color: #475569;
                font-size: 9px;
                font-weight: 700;
                font-family: monospace;
                padding: 1px 7px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        log_header.addWidget(self.btn_clear_logs)

        self.btn_wrap_logs = QPushButton("Wrap: Off")
        self.btn_wrap_logs.setCursor(Qt.PointingHandCursor)
        self.btn_wrap_logs.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                color: #475569;
                font-size: 9px;
                font-weight: 700;
                font-family: monospace;
                padding: 1px 7px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.btn_wrap_logs.clicked.connect(self.toggle_log_wrap)
        log_header.addWidget(self.btn_wrap_logs)

        lbl_live_badge = QLabel("● LIVE")
        lbl_live_badge.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #059669; font-family: monospace; margin-left: 4px;")
        log_header.addWidget(lbl_live_badge)
        lc_vbox.addLayout(log_header)

        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.txt_logs.setMaximumBlockCount(1000)
        self.txt_logs.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 10px;
                color: #1E293B;
                font-family: 'JetBrains Mono', 'Fira Code', 'DejaVu Sans Mono', monospace;
                font-size: 10.5px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F8FAFC;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94A3B8;
            }
            QScrollBar:horizontal {
                height: 8px;
                background: #F8FAFC;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #CBD5E1;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #94A3B8;
            }
        """)
        lc_vbox.addWidget(self.txt_logs, 1)

        settings = self.service.config_mgr.get_settings()
        socks_endpoint = f"{settings.get('socks_host', '127.0.0.1')}:{settings.get('socks_port', 1080)}"

        log_footer = QHBoxLayout()
        lbl_proc = QLabel("Direct /proc/net/dev telemetry")
        lbl_proc.setStyleSheet("font-size: 9.5px; color: #64748B; font-family: monospace;")
        log_footer.addWidget(lbl_proc)
        log_footer.addStretch(1)

        self.lbl_ep = QLabel(socks_endpoint)
        self.lbl_ep.setStyleSheet("font-size: 9.5px; font-weight: 700; color: #0284C7; font-family: monospace;")
        log_footer.addWidget(self.lbl_ep)
        lc_vbox.addLayout(log_footer)

        right_vbox.addWidget(log_card, 1)

        content_layout.addWidget(right_panel, 1)
        main_vbox.addLayout(content_layout, 1)

        # Bottom Management Row (Quick Import)
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(8)

        self.input_import_key = QLineEdit()
        self.input_import_key.setPlaceholderText("Paste ssconf:// URL, ss:// URI, or JSON config...")
        self.input_import_key.returnPressed.connect(self.on_quick_import)
        mgmt_row.addWidget(self.input_import_key, 1)

        self.btn_quick_import = QPushButton("Import Node")
        self.btn_quick_import.setProperty("class", "btn-primary")
        self.btn_quick_import.setCursor(Qt.PointingHandCursor)
        self.btn_quick_import.clicked.connect(self.on_quick_import)
        mgmt_row.addWidget(self.btn_quick_import)

        main_vbox.addLayout(mgmt_row)

    def on_dns_changed(self):
        dns_choice = self.combo_dns.currentText()
        if not dns_choice or dns_choice not in DNS_PRESETS:
            return

        p_dns, b_dns = DNS_PRESETS[dns_choice]
        self.service.set_dns(primary_dns=p_dns, backup_dns=b_dns, preset_name=dns_choice)
        provider_name = dns_choice.split(" ")[0]

        if self.service.state == STATE_CONNECTED:
            self.append_ui_log(f"[DNS] Live upstream updated to {provider_name} ({p_dns})")
        else:
            self.append_ui_log(f"[DNS] Upstream resolver set to {provider_name} ({p_dns})")
        self._sync_tunnel_model()

    def on_quick_import(self):
        raw = self.input_import_key.text().strip()
        if not raw:
            return

        self.btn_quick_import.setEnabled(False)
        self.btn_quick_import.setText("Importing...")

        def _worker():
            try:
                profile = self.service.config_mgr.parse_key(raw)
                saved = self.service.config_mgr.add_or_update_profile(profile)
                self.service.config_mgr.set_active_profile(saved.get("id"))
                self.signals.import_finished.emit(True, "", saved)
            except ConfigError as e:
                self.signals.import_finished.emit(False, str(e), {})
            except Exception as e:
                self.signals.import_finished.emit(False, str(e), {})

        threading.Thread(target=_worker, daemon=True).start()

    def _on_import_finished(self, ok: bool, err: str, saved: dict):
        self.btn_quick_import.setEnabled(True)
        self.btn_quick_import.setText("Import Node")
        if ok:
            self.input_import_key.clear()
            self.update_profiles_list()
            self.refresh_ui_state()
            self.append_ui_log(f"[IMPORT] Imported profile '{saved.get('name')}' successfully.")
            self.trigger_all_pings()
        else:
            QMessageBox.critical(self, "Import Error", err)

    def clear_logs(self):
        self.txt_logs.clear()

    def toggle_log_wrap(self):
        if self.txt_logs.lineWrapMode() == QPlainTextEdit.NoWrap:
            self.txt_logs.setLineWrapMode(QPlainTextEdit.WidgetWidth)
            self.btn_wrap_logs.setText("Wrap: On")
        else:
            self.txt_logs.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.btn_wrap_logs.setText("Wrap: Off")

    def _append_formatted_log_line(self, raw_line: str):
        if not raw_line:
            return
        for sub_line in raw_line.splitlines():
            s = sub_line.strip()
            if s:
                plain, html_line = clean_and_format_log(s)
                if html_line:
                    self.txt_logs.appendHtml(html_line)

    def append_ui_log(self, msg: str):
        self.signals.log_message.emit(msg)

    def _on_log_message_received(self, msg: str):
        self._append_formatted_log_line(msg)
        self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def on_server_dropdown_changed(self, index: int):
        if self.updating_combo or index < 0:
            return
        p_id = self.combo_servers.itemData(index)
        if p_id:
            self.service.config_mgr.set_active_profile(p_id)
            self.refresh_ui_state()
            self.trigger_all_pings()

    def update_profiles_list(self):
        self.updating_combo = True
        self.combo_servers.clear()

        profiles = self.service.config_mgr.get_profiles()
        active_id = self.service.config_mgr.get_active_profile_id()
        selected_index = 0

        if profiles and not any(p.get("id") == active_id for p in profiles):
            active_id = profiles[0].get("id")
            self.service.config_mgr.set_active_profile(active_id)

        for idx, p in enumerate(profiles):
            p_id = p.get("id", "")
            p_name = p.get("name", "Unnamed")
            self.combo_servers.addItem(f"{p_name} ({p.get('server')})", p_id)
            if p_id == active_id:
                selected_index = idx

        if profiles:
            self.combo_servers.setCurrentIndex(selected_index)
            if hasattr(self, "btn_delete_server"):
                self.btn_delete_server.setEnabled(True)
        else:
            if hasattr(self, "btn_delete_server"):
                self.btn_delete_server.setEnabled(False)

        self.updating_combo = False

    def on_delete_server(self, target_prof: Optional[dict] = None):
        p_id = None
        prof = None

        if target_prof and isinstance(target_prof, dict):
            p_id = target_prof.get("id")
            prof = target_prof

        if not p_id:
            idx = self.combo_servers.currentIndex()
            if idx >= 0:
                p_id = self.combo_servers.itemData(idx)

        if not p_id:
            active = self.service.config_mgr.get_active_profile()
            if active:
                p_id = active.get("id")

        if not p_id:
            QMessageBox.information(self, "No Server", "No server profile is currently selected.")
            return

        if not prof:
            prof = self.service.config_mgr.get_profile_by_id(p_id)

        name = prof.get("name", "Unnamed") if prof else "Selected Profile"
        server = prof.get("server", "") if prof else ""
        label = f"'{name}' ({server})" if server else f"'{name}'"

        active_id = self.service.config_mgr.get_active_profile_id()
        is_active_profile = active_id == p_id
        is_tunnel_connected = self.service.state == STATE_CONNECTED and is_active_profile
        is_only_profile = self.combo_servers.count() <= 1

        dialog = ModernDeleteConfirmDialog(
            profile_data=prof or {"name": name, "server": server},
            is_connected=is_tunnel_connected,
            is_active=is_active_profile,
            is_only=is_only_profile,
            parent=self,
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        if is_tunnel_connected:
            self.append_ui_log(f"[DISCONNECT] Terminating active tunnel before deleting {label}...")
            self.service.disconnect()

        deleted = self.service.config_mgr.delete_profile(p_id)
        if deleted:
            self.append_ui_log(f"[DELETE] Deleted server profile {label}")
            self.update_profiles_list()
            self.refresh_ui_state()
            self.trigger_all_pings()
        else:
            QMessageBox.critical(self, "Error", f"Failed to delete profile {label}.")

    def on_connect_toggle(self):
        state = self.service.state
        if state == STATE_CONNECTED:
            self.btn_circular.trigger_click_effect(is_disconnect=True)
            self.tunnel_model.trigger_disconnect_modeling()
            self.append_ui_log("[DISCONNECT] Terminating tun0 interface...")
            threading.Thread(target=self.service.disconnect, daemon=True).start()
        elif state == STATE_CONNECTING:
            self.btn_circular.trigger_click_effect(is_disconnect=True)
            self.tunnel_model.trigger_disconnect_modeling()
            self.append_ui_log("[CANCEL] Cancelling in-flight connection...")
            self.service.cancel_connect()
        elif state in (STATE_DISCONNECTED, STATE_ERROR):
            profiles = self.service.config_mgr.get_profiles()
            if not profiles:
                QMessageBox.warning(self, "No Servers", "Please import a Shadowsocks profile first.")
                return
            self.btn_circular.trigger_click_effect(is_disconnect=False)
            self.tunnel_model.trigger_connect_modeling()
            self.append_ui_log("[CONNECT] Initializing full-tunnel connection...")
            threading.Thread(target=self.service.connect, daemon=True).start()

    def on_state_changed(self, event_type: str, data: dict):
        if event_type == "connected":
            self._last_verify_info = dict(data or {})
        elif event_type in ("disconnected", "error"):
            self._last_verify_info = {}
        self.refresh_ui_state()

    def on_stage_changed(self, stage_data: dict):
        self.tunnel_model.set_connection_stage(stage_data)
        stage_lbl = stage_data.get("stage_label", "")
        msg = stage_data.get("message", "")
        if stage_lbl and msg:
            self.lbl_route_status.setText(f"{stage_lbl} • {msg}")
        elif msg:
            self.lbl_route_status.setText(msg)

    def _sync_tunnel_model(self):
        settings = self.service.config_mgr.get_settings()
        active_prof = self.service.active_profile if self.service.state == STATE_CONNECTED else self.service.config_mgr.get_active_profile()
        ipv6_off = self.service.network_mgr.is_ipv6_disabled()

        # Attempt to read cached gateway & dev
        gw = None
        dev = None
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    sess = json.load(f)
                gw = sess.get("gateway_ip")
                dev = sess.get("physical_dev")
            except Exception:
                pass

        if not gw or not dev:
            try:
                gw, dev = self.service.network_mgr.get_physical_route()
            except Exception:
                gw, dev = "192.168.1.1", "wlan0"

        st = self.service.stats_monitor.get_stats() if self.service.state == STATE_CONNECTED else {}

        self.tunnel_model.set_model_state(
            self.service.state,
            {
                "profile_name": active_prof.get("name", "No Server") if active_prof else "No Server",
                "server": active_prof.get("server", "--") if active_prof else "--",
                "port": active_prof.get("server_port", "--") if active_prof else "--",
                "method": active_prof.get("method", "chacha20-ietf-poly1305") if active_prof else "--",
                "dns": settings.get("dns", "1.1.1.1"),
                "socks": f"{settings.get('socks_host', '127.0.0.1')}:{settings.get('socks_port', 1080)}",
                "gateway_ip": gw,
                "physical_dev": dev,
                "ipv6_disabled": ipv6_off,
                "ping_ms": self._last_ping_ms,
                "rx_speed_str": st.get("rx_speed_str", "0 B/s"),
                "tx_speed_str": st.get("tx_speed_str", "0 B/s"),
                "rx_total_str": st.get("rx_total_str", "0 B"),
                "tx_total_str": st.get("tx_total_str", "0 B"),
                "duration_str": st.get("duration_str", "00:00"),
                "error": self.service.last_error,
            },
        )

    def refresh_ui_state(self):
        state = self.service.state
        active_prof = self.service.active_profile if state == STATE_CONNECTED else self.service.config_mgr.get_active_profile()
        prof_name = active_prof.get("name", "No Server") if active_prof else "No Server"
        ipv6_off = self.service.network_mgr.is_ipv6_disabled()

        if state == STATE_CONNECTED:
            self.status_pill.setText("CONNECTED")
            self.status_pill.setStyleSheet("""
                background-color: #ECFDF5;
                color: #047857;
                border: 1px solid #6EE7B7;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
                font-family: monospace;
            """)
            if ipv6_off:
                self.ipv6_pill.setText("IPv6 DISABLED")
                self.ipv6_pill.setStyleSheet("background-color: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; border-radius: 12px; padding: 4px 10px; font-size: 10px; font-weight: 700; font-family: monospace;")
            else:
                self.ipv6_pill.setText("IPv6 ACTIVE")
                self.ipv6_pill.setStyleSheet("background-color: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; border-radius: 12px; padding: 4px 10px; font-size: 10px; font-weight: 700; font-family: monospace;")

            self.btn_circular.set_vpn_state(STATE_CONNECTED)
            ipv6_tag = "IPv6 disabled" if ipv6_off else "IPv6 active"
            v_info = getattr(self, "_last_verify_info", {}) or {}
            if v_info.get("verified") is False:
                self.lbl_route_status.setText(f"Virtual tun0 active • {ipv6_tag} • probe timed out (check {prof_name})")
                self.lbl_route_status.setStyleSheet("font-size: 11px; color: #B45309; font-family: monospace; font-weight: 600; margin-top: 4px;")
            else:
                v_lat = v_info.get("verify_latency_ms")
                lat_part = f" • verified {v_lat}ms" if isinstance(v_lat, int) else ""
                self.lbl_route_status.setText(f"Virtual tun0 active • {ipv6_tag}{lat_part} • routed via {prof_name}")
                self.lbl_route_status.setStyleSheet("font-size: 11px; color: #047857; font-family: monospace; font-weight: 600; margin-top: 4px;")

            # Trigger immediate stats update if already connected
            st = self.service.stats_monitor.get_stats()
            self.lbl_speed_down.setText(st.get("rx_speed_str", "0 B/s"))
            self.lbl_speed_up.setText(st.get("tx_speed_str", "0 B/s"))
            self.lbl_total_down.setText(st.get("rx_total_str", "0 B"))
            self.lbl_total_up.setText(st.get("tx_total_str", "0 B"))
        elif state in (STATE_CONNECTING, STATE_DISCONNECTING):
            label = "CONNECTING..." if state == STATE_CONNECTING else "DISCONNECTING..."
            self.status_pill.setText(label)
            self.status_pill.setStyleSheet("""
                background-color: #FFFBEB;
                color: #B45309;
                border: 1px solid #FCD34D;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
                font-family: monospace;
            """)
            self.btn_circular.set_vpn_state(state)
            self.lbl_route_status.setText("Probing remote proxy & provisioning tun0...")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #B45309; font-family: monospace; font-weight: 600; margin-top: 4px;")
            self.lbl_speed_down.setText("0 B/s")
            self.lbl_speed_up.setText("0 B/s")
            self.lbl_total_down.setText("0 B")
            self.lbl_total_up.setText("0 B")
            self.spark_down.clear()
            self.spark_up.clear()
        elif state == STATE_ERROR:
            self.status_pill.setText("ERROR")
            self.status_pill.setStyleSheet("""
                background-color: #FEF2F2;
                color: #B91C1C;
                border: 1px solid #FCA5A5;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
                font-family: monospace;
            """)
            self.btn_circular.set_vpn_state(STATE_ERROR)
            err_msg = (self.service.last_error or "Connection failed").splitlines()[0][:64]
            self.lbl_route_status.setText(f"Error: {err_msg}")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #DC2626; font-family: monospace; font-weight: 600; margin-top: 4px;")
            self.lbl_speed_down.setText("0 B/s")
            self.lbl_speed_up.setText("0 B/s")
            self.lbl_total_down.setText("0 B")
            self.lbl_total_up.setText("0 B")
            self.spark_down.clear()
            self.spark_up.clear()
        else:
            self.status_pill.setText("DISCONNECTED")
            self.status_pill.setStyleSheet("""
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 700;
                font-family: monospace;
            """)
            self.ipv6_pill.setText("IPv6 GUARD READY")
            self.ipv6_pill.setStyleSheet("background-color: #F8FAFC; color: #64748B; border: 1px solid #CBD5E1; border-radius: 12px; padding: 4px 10px; font-size: 10px; font-weight: 700; font-family: monospace;")
            self.btn_circular.set_vpn_state(STATE_DISCONNECTED)
            self.lbl_route_status.setText("System using standard physical route")
            self.lbl_route_status.setStyleSheet("font-size: 11px; color: #64748B; font-family: monospace; margin-top: 4px;")
            self.lbl_speed_down.setText("0 B/s")
            self.lbl_speed_up.setText("0 B/s")
            self.lbl_total_down.setText("0 B")
            self.lbl_total_up.setText("0 B")
            self.spark_down.clear()
            self.spark_up.clear()

        self._sync_tunnel_model()

    def on_stats_updated(self, stats: dict):
        if self.service.state == STATE_CONNECTED:
            rx_speed = stats.get("rx_speed_str", "0 B/s")
            tx_speed = stats.get("tx_speed_str", "0 B/s")
            rx_total = stats.get("rx_total_str", "0 B")
            tx_total = stats.get("tx_total_str", "0 B")
            self.lbl_speed_down.setText(rx_speed)
            self.lbl_speed_up.setText(tx_speed)
            self.lbl_total_down.setText(rx_total)
            self.lbl_total_up.setText(tx_total)

            self.spark_down.push_value(stats.get("rx_speed_bps", 0.0))
            self.spark_up.push_value(stats.get("tx_speed_bps", 0.0))
            self.tunnel_model.update_telemetry(stats)

    def on_log_updated(self, logs: list):
        if logs:
            for l in logs:
                self._append_formatted_log_line(l)
            self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def on_ping_result(self, p_id: str, ms: int):
        self._last_ping_ms = ms
        self.btn_ping_refresh.setText(f"⟳ Ping: {ms}ms" if ms >= 0 else "⟳ Timeout")
        self._sync_tunnel_model()

    def trigger_all_pings(self):
        active = self.service.config_mgr.get_active_profile()
        if not active:
            self.btn_ping_refresh.setText("⟳ Ping")
            return

        self.btn_ping_refresh.setText("⟳ Pinging...")

        def _worker():
            host = active.get("server")
            port = int(active.get("server_port", 8388))
            raw_ms = self.service.stats_monitor.measure_ping(host, port)
            ms = raw_ms if isinstance(raw_ms, int) else -1
            self.signals.ping_result.emit(str(active.get("id", "")), ms)
            self.append_ui_log(
                f"[PING] Response from {active.get('name')}: {ms}ms"
                if ms >= 0
                else f"[PING] Timeout reaching {active.get('name')}"
            )

        threading.Thread(target=_worker, daemon=True).start()

    def init_timers(self):
        self._log_offset_ss = 0
        self._log_offset_tun = 0
        self._init_logs()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._poll_stats)
        self.stats_timer.start(1000)

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._poll_live_logs)
        self.log_timer.start(400)

    def _init_logs(self):
        recent = self.service.process_mgr.get_recent_logs(max_lines=35)
        if recent:
            for line in recent:
                self._append_formatted_log_line(line)
        else:
            self._append_formatted_log_line(
                f"[AuraLink] Daylight GUI ready. Select server and connect."
            )
        self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

        if os.path.exists(self.service.process_mgr.sslocal_log):
            self._log_offset_ss = os.path.getsize(self.service.process_mgr.sslocal_log)
        if os.path.exists(self.service.process_mgr.tun2socks_log):
            self._log_offset_tun = os.path.getsize(self.service.process_mgr.tun2socks_log)

    def _poll_live_logs(self):
        new_ss, self._log_offset_ss = self.service.process_mgr._read_new_lines(
            self.service.process_mgr.sslocal_log, self._log_offset_ss
        )
        new_tun, self._log_offset_tun = self.service.process_mgr._read_new_lines(
            self.service.process_mgr.tun2socks_log, self._log_offset_tun
        )

        batch = []
        for line in new_ss:
            s = line.strip()
            if s:
                batch.append((self.service.process_mgr._parse_timestamp(s), f"[sslocal] {s}"))
        for line in new_tun:
            s = line.strip()
            if s:
                batch.append((self.service.process_mgr._parse_timestamp(s), f"[tun2socks] {s}"))

        if batch:
            batch.sort(key=lambda x: x[0])
            for _, raw_line in batch:
                self._append_formatted_log_line(raw_line)
            self.txt_logs.verticalScrollBar().setValue(self.txt_logs.verticalScrollBar().maximum())

    def _poll_stats(self):
        if self.service.state == STATE_CONNECTED:
            st = self.service.stats_monitor.get_stats()
            self.signals.stats_updated.emit(st)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_app_icon())
        self.tray_icon.activated.connect(self.on_tray_activated)

        tray_menu = QMenu()
        act_show = QAction("Show AuraLink", self)
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
        if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "AuraLink VPN",
                "Minimized to system tray. Click tray icon to restore.",
                QSystemTrayIcon.Information,
                1500,
            )

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            if hasattr(self, "btn_maximize"):
                self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            if hasattr(self, "btn_maximize"):
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
    app.setApplicationName("AuraLink")
    app.setWindowIcon(get_app_icon())

    win = MainWindow()
    app._main_win = win
    win.show()

    return app.exec_()


def main():
    sys.exit(launch_gui())


if __name__ == "__main__":
    main()
