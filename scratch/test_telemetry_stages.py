#!/usr/bin/env python3
"""
Unit test for Download/Upload Telemetry and Real Connection Stages.
Tests:
1. StatsMonitor parsing, delta calculation, session persistence, smoothing, and zeroing.
2. VPNService stages: stage_changed notifications, session.json structure, and restore.
3. InteractiveTunnelModelWidget: rendering in idle, stage 1-4, connected, disconnecting, and error.
4. MainWindow UI updates: lbl_speed_down/up, lbl_total_down/up, sparklines.
"""

import os
import sys
import json
import time
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Set offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure Arch_VPN root is in path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.stats_monitor import StatsMonitor, format_bytes, format_speed
from core import vpn_service
from core.vpn_service import (
    VPNService,
    STATE_DISCONNECTED,
    STATE_CONNECTING,
    STATE_CONNECTED,
    STATE_DISCONNECTING,
    STATE_ERROR,
)


class TestStatsMonitor(unittest.TestCase):
    def test_format_bytes_and_speed(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1048576), "1.00 MB")
        self.assertEqual(format_bytes(1073741824), "1.00 GB")

        self.assertEqual(format_speed(0), "0 B/s")
        self.assertEqual(format_speed(1048576), "1.00 MB/s")

    def test_stats_monitor_stopped(self):
        monitor = StatsMonitor("tun0")
        st = monitor.get_stats()
        self.assertFalse(st["is_active"])
        self.assertEqual(st["rx_speed_str"], "0 B/s")
        self.assertEqual(st["tx_speed_str"], "0 B/s")
        self.assertEqual(st["rx_total_str"], "0 B")
        self.assertEqual(st["tx_total_str"], "0 B")
        self.assertEqual(st["duration_str"], "00:00")

    def test_stats_monitor_mocked_proc(self):
        mock_proc_data_1 = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
  tun0: 1000000     500    0    0    0     0          0         0   500000     250    0    0    0     0       0          0
"""
        mock_proc_data_2 = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
  tun0: 2048576     900    0    0    0     0          0         0  1024000     450    0    0    0     0       0          0
"""
        monitor = StatsMonitor("tun0")

        # Start monitor at t0 with initial bytes
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_proc_data_1)):
            monitor.start(start_time=time.time() - 60, initial_rx=500000, initial_tx=200000)

        # Query stats at t1
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_proc_data_2)):
            st = monitor.get_stats()

        self.assertTrue(st["is_active"])
        self.assertGreater(st["duration_sec"], 50)
        # Total bytes from initial_rx: 2048576 - 500000 = 1548576
        self.assertEqual(st["rx_bytes"], 1548576)
        self.assertIn("MB", st["rx_total_str"])
        self.assertGreater(st["rx_speed_bps"], 0)


class TestVPNServiceStages(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.session_file = os.path.join(self.tmp_dir.name, "session.json")
        self.orig_session_file = vpn_service.SESSION_FILE
        vpn_service.SESSION_FILE = self.session_file

    def tearDown(self):
        vpn_service.SESSION_FILE = self.orig_session_file
        self.tmp_dir.cleanup()

    @patch("core.vpn_service.ConfigManager")
    @patch("core.vpn_service.ProcessManager")
    @patch("core.vpn_service.NetworkManager")
    def test_connection_stages_emitted(self, mock_net_cls, mock_proc_cls, mock_cfg_cls):
        mock_cfg = mock_cfg_cls.return_value
        mock_proc = mock_proc_cls.return_value
        mock_net = mock_net_cls.return_value

        mock_cfg.get_settings.return_value = {
            "tun_device": "tun0",
            "tun_ip": "10.0.0.2/24",
            "socks_host": "127.0.0.1",
            "socks_port": 1080,
            "dns": "1.1.1.1",
            "dns_backup": "8.8.8.8",
            "disable_ipv6": True
        }
        mock_cfg.get_profiles.return_value = [{
            "id": "p1",
            "name": "Test Tokyo",
            "server": "1.2.3.4",
            "server_port": 8388,
            "method": "chacha20-ietf-poly1305",
            "password": "secret"
        }]
        mock_cfg.get_profile_by_id.return_value = mock_cfg.get_profiles.return_value[0]
        mock_net.get_physical_route.return_value = ("192.168.1.1", "wlan0")
        mock_net.resolve_server_ip.return_value = "1.2.3.4"
        mock_net.get_ipv6_state.return_value = {"all": 0, "default": 0, "interfaces": {}}
        mock_net.disable_ipv6.return_value = True

        service = VPNService()
        emitted_stages = []

        def on_event(event_type, data):
            if event_type == "stage_changed":
                emitted_stages.append(data.get("stage"))

        service.add_listener(on_event)

        with patch.object(StatsMonitor, "_read_interface_bytes", return_value=(1000, 500)):
            res = service.connect("p1")

        self.assertTrue(res)
        self.assertEqual(service.state, STATE_CONNECTED)

        # Verify stages were sequenced correctly:
        # resolving -> sslocal -> tun0 -> routing
        self.assertIn("resolving", emitted_stages)
        self.assertIn("sslocal", emitted_stages)
        self.assertIn("tun0", emitted_stages)
        self.assertIn("routing", emitted_stages)

        # Verify session file was written with start timestamp and initial bytes
        self.assertTrue(os.path.exists(self.session_file))
        with open(self.session_file) as f:
            saved = json.load(f)
        self.assertIn("connected_at", saved)
        self.assertIn("initial_rx", saved)
        self.assertIn("initial_tx", saved)


class TestGUIWidgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt5.QtWidgets import QApplication
        if not QApplication.instance():
            cls.app = QApplication([sys.argv[0], "-platform", "offscreen", "-style", "Fusion"])
        else:
            cls.app = QApplication.instance()

    def test_interactive_tunnel_model_rendering(self):
        from gui.app import InteractiveTunnelModelWidget
        from PyQt5.QtGui import QPixmap, QPainter

        widget = InteractiveTunnelModelWidget()
        widget.resize(500, 116)

        # 1. Test Idle / Disconnected state
        widget.set_model_state(STATE_DISCONNECTED, {
            "profile_name": "Tokyo-01",
            "server": "1.2.3.4",
            "port": 8388,
            "method": "chacha20-ietf-poly1305",
            "dns": "1.1.1.1",
            "socks": "127.0.0.1:1080",
            "gateway_ip": "192.168.1.1",
            "physical_dev": "wlan0",
            "ipv6_disabled": False,
        })
        pix = QPixmap(500, 116)
        painter = QPainter(pix)
        widget.render(painter)
        painter.end()

        # Check inspector text in idle for all 4 nodes
        for idx in range(4):
            widget._selected_idx = idx
            txt = widget._inspector_text()
            self.assertTrue(len(txt) > 0)
            self.assertNotIn("100% Full-Tunnel", txt)  # Should not claim tunnel is captured when idle

        # 2. Test Connecting stages (1 to 4)
        for stage in ("resolving", "sslocal", "tun0", "routing"):
            widget.set_model_state(STATE_CONNECTING)
            widget.set_connection_stage({
                "stage": stage,
                "stage_label": f"Testing {stage}",
                "message": f"Step {stage}"
            })
            pix = QPixmap(500, 116)
            painter = QPainter(pix)
            widget.render(painter)
            painter.end()

        # 3. Test Connected state with live telemetry
        widget.set_model_state(STATE_CONNECTED, {
            "profile_name": "Tokyo-01",
            "server": "1.2.3.4",
            "port": 8388,
            "method": "chacha20-ietf-poly1305",
            "dns": "1.1.1.1",
            "socks": "127.0.0.1:1080",
            "gateway_ip": "192.168.1.1",
            "physical_dev": "wlan0",
            "ipv6_disabled": True,
            "ping_ms": 22,
        })
        widget.update_telemetry({
            "rx_speed_bps": 1500000.0,
            "tx_speed_bps": 350000.0,
            "rx_speed_str": "1.50 MB/s",
            "tx_speed_str": "350 KB/s",
            "rx_total_str": "45.2 MB",
            "tx_total_str": "8.4 MB",
            "duration_str": "05:22"
        })

        pix = QPixmap(500, 116)
        painter = QPainter(pix)
        widget.render(painter)
        painter.end()

        # Check connected inspector text for apps and tun0
        widget._selected_idx = 0
        self.assertIn("100% Full-Tunnel Captured", widget._inspector_text())
        widget._selected_idx = 1
        self.assertIn("IPv6 Shield Active", widget._inspector_text())
        self.assertIn("45.2 MB", widget._inspector_text())

        # 4. Test Error state
        widget.set_model_state(STATE_ERROR, {"error": "Handshake timed out"})
        pix = QPixmap(500, 116)
        painter = QPainter(pix)
        widget.render(painter)
        painter.end()
        self.assertIn("Error", widget._inspector_text())

    def test_circular_button_click_animation(self):
        from gui.app import CircularConnectButton
        from PyQt5.QtGui import QPixmap, QPainter
        from PyQt5.QtCore import Qt, QPoint
        from PyQt5.QtGui import QMouseEvent

        btn = CircularConnectButton()
        btn.resize(176, 176)

        # Trigger click effect
        btn.trigger_click_effect(is_disconnect=False)
        self.assertEqual(len(btn._shockwaves), 1)
        self.assertFalse(btn._shockwaves[0]["is_disconnect"])

        # Test tick advances shockwave progress
        btn._on_tick()
        self.assertGreater(btn._shockwaves[0]["progress"], 0.0)

        # Test tactile press
        press_ev = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(88, 88), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        btn.mousePressEvent(press_ev)
        self.assertTrue(btn._pressed)
        btn._on_tick()
        self.assertGreater(btn._press_t, 0.0)

        # Test tactile release
        rel_ev = QMouseEvent(QMouseEvent.MouseButtonRelease, QPoint(88, 88), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        btn.mouseReleaseEvent(rel_ev)
        self.assertFalse(btn._pressed)

        # Test offscreen render with shockwave and press state
        btn.trigger_click_effect(is_disconnect=True)
        pix = QPixmap(176, 176)
        painter = QPainter(pix)
        btn.render(painter)
        painter.end()

    def test_tunnel_model_click_and_modeling_animations(self):
        from gui.app import InteractiveTunnelModelWidget
        from PyQt5.QtGui import QPixmap, QPainter
        from PyQt5.QtCore import Qt, QPoint
        from PyQt5.QtGui import QMouseEvent

        widget = InteractiveTunnelModelWidget()
        widget.resize(500, 116)

        # 1. Connect modeling animation
        widget.trigger_connect_modeling()
        self.assertEqual(widget._modeling_mode, "connecting")
        self.assertEqual(widget._modeling_t, 0.0)
        self.assertEqual(widget._node_bursts[0], 1.0)

        # Advance frames and verify beam progression and node bursts
        for _ in range(15):
            widget._tick()
        self.assertGreater(widget._modeling_t, 0.3)
        self.assertGreater(widget._node_bursts[1], 0.0)

        # Render during active connect modeling
        pix = QPixmap(500, 116)
        painter = QPainter(pix)
        widget.render(painter)
        painter.end()

        # 2. Disconnect modeling animation
        widget.trigger_disconnect_modeling()
        self.assertEqual(widget._modeling_mode, "disconnecting")
        self.assertEqual(widget._node_bursts[3], 1.0)

        for _ in range(15):
            widget._tick()
        self.assertGreater(widget._modeling_t, 0.3)
        self.assertGreater(widget._node_bursts[2], 0.0)

        # Render during active disconnect modeling
        pix = QPixmap(500, 116)
        painter = QPainter(pix)
        widget.render(painter)
        painter.end()

        # 3. Direct node click ripple
        click_ev = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(int(widget._node_centers[1].x()), int(widget._node_centers[1].y())), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        widget.mousePressEvent(click_ev)
        self.assertEqual(widget._selected_idx, 1)
        self.assertEqual(len(widget._node_click_ripples), 1)
        self.assertEqual(widget._node_click_ripples[0]["node_idx"], 1)
        self.assertEqual(widget._node_bursts[1], 1.0)

        # Advance tick to verify ripple progress
        widget._tick()
        self.assertGreater(widget._node_click_ripples[0]["progress"], 0.0)

    def test_mini_sparkline_waveform(self):
        from gui.app import MiniSparkline
        from PyQt5.QtGui import QPixmap, QPainter

        spark = MiniSparkline()
        spark.resize(100, 22)
        for val in [1000, 5000, 25000, 100000, 500000, 1500000]:
            spark.push_value(val)

        pix = QPixmap(100, 22)
        painter = QPainter(pix)
        spark.render(painter)
        painter.end()
        self.assertEqual(len(spark._values), 18)

    @patch("gui.app.VPNService")
    def test_main_window_speed_and_stage_updates(self, mock_svc_cls):
        from gui.app import MainWindow
        mock_svc = mock_svc_cls.return_value
        mock_svc.state = STATE_CONNECTED
        mock_svc.active_profile = {"id": "1", "name": "Tokyo-01", "server": "1.1.1.1", "server_port": 8388, "method": "chacha20-ietf-poly1305"}
        mock_svc.config_mgr.get_settings.return_value = {"dns": "1.1.1.1", "socks_host": "127.0.0.1", "socks_port": 1080}
        mock_svc.config_mgr.get_profiles.return_value = [mock_svc.active_profile]
        mock_svc.config_mgr.get_active_profile.return_value = mock_svc.active_profile
        mock_svc.network_mgr.is_ipv6_disabled.return_value = True
        mock_svc.network_mgr.get_physical_route.return_value = ("192.168.1.1", "wlan0")
        mock_svc.stats_monitor.get_stats.return_value = {
            "is_active": True,
            "duration_sec": 300,
            "duration_str": "05:00",
            "rx_bytes": 5000000,
            "tx_bytes": 1000000,
            "rx_speed_bps": 2500000.0,
            "tx_speed_bps": 400000.0,
            "rx_speed_str": "2.50 MB/s",
            "tx_speed_str": "400 KB/s",
            "rx_total_str": "5.00 MB",
            "tx_total_str": "1.00 MB",
        }
        mock_svc.process_mgr.get_recent_logs.return_value = []

        win = MainWindow()
        win.resize(840, 580)

        # Trigger stats updated signal
        stats_payload = {
            "rx_speed_str": "3.12 MB/s",
            "tx_speed_str": "850 KB/s",
            "rx_total_str": "128.5 MB",
            "tx_total_str": "14.2 MB",
            "rx_speed_bps": 3120000.0,
            "tx_speed_bps": 850000.0,
            "duration_str": "12:34"
        }
        win.on_stats_updated(stats_payload)

        self.assertEqual(win.lbl_speed_down.text(), "3.12 MB/s")
        self.assertEqual(win.lbl_speed_up.text(), "850 KB/s")
        self.assertEqual(win.lbl_total_down.text(), "128.5 MB")
        self.assertEqual(win.lbl_total_up.text(), "14.2 MB")
        self.assertAlmostEqual(win.spark_down._values[-1], 3120000.0)

        # Trigger stage changed signal
        win.on_stage_changed({
            "stage": "tun0",
            "stage_label": "3/4: TUNNEL ARMED",
            "message": "Creating virtual tun0..."
        })
        self.assertIn("3/4: TUNNEL ARMED", win.lbl_route_status.text())
        self.assertEqual(win.tunnel_model._stage, "tun0")

        # Test log formatting & line-by-line controls
        win.clear_logs()
        self.assertEqual(win.txt_logs.toPlainText(), "")

        # Verify default line wrap is NoWrap (line by line)
        from PyQt5.QtWidgets import QPlainTextEdit
        self.assertEqual(win.txt_logs.lineWrapMode(), QPlainTextEdit.NoWrap)

        # Toggle wrap
        win.toggle_log_wrap()
        self.assertEqual(win.txt_logs.lineWrapMode(), QPlainTextEdit.WidgetWidth)
        self.assertEqual(win.btn_wrap_logs.text(), "Wrap: On")
        win.toggle_log_wrap()
        self.assertEqual(win.txt_logs.lineWrapMode(), QPlainTextEdit.NoWrap)
        self.assertEqual(win.btn_wrap_logs.text(), "Wrap: Off")

        # Feed screenshot raw logs and verify clean line-by-line output
        test_raw_lines = [
            '[tun2socks] time="2026-11-19T00:54:36+06:30" level=warning msg="[UDP] dial 15.235.197.63:123: client handshake: UDP ASSOCIATE: command not supported"',
            "[sslocal] 2026-11-19T00:54:36.219677544+06:30 DEBUG tokio-rt-worker ThreadId(04) shadowsocks_service::local::socks::server::socks5::tcprelay: UDP ASSOCIATE from 0.0.0.0:0",
            '[tun2socks] time="2026-11-19T00:54:43+06:30" level=info msg="[TCP] 10.0.0.2:56386 <-> 1.1.1.1:53"',
            "[sslocal] 2026-11-19T00:54:43.016622604+06:30 DEBUG tokio-rt-worker ThreadId(04) shadowsocks_service::local::utils: established tcp tunnel 127.0.0.1:53676 <-> 1.1.1.1:53 through server 77.83.241.82:80 (outbound: 77.83.241.82:80)",
            "[CONNECT] Initializing full-tunnel connection...",
            "[12:54:36 AM] [DNS] Upstream resolver set to Cloudflare (1.1.1.1)"
        ]
        for l in test_raw_lines:
            win._append_formatted_log_line(l)

        rendered_text = win.txt_logs.toPlainText()
        self.assertNotIn("tokio-rt-worker", rendered_text)
        self.assertNotIn("shadowsocks_service::", rendered_text)
        self.assertNotIn("time=\"2026", rendered_text)
        self.assertIn("[00:54:36]", rendered_text)
        self.assertIn("[tun2socks]", rendered_text)
        self.assertIn("[sslocal]", rendered_text)
        self.assertIn("[dns]", rendered_text)
        self.assertIn("1.1.1.1:53", rendered_text)

        # Test panel width constraints in full screen
        cl = win.centralWidget().layout().itemAt(1).layout()
        left_panel = cl.itemAt(0).widget()
        right_panel = cl.itemAt(1).widget()
        win.show()

        # At default size
        win.resize(1080, 640)
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().processEvents()
        self.assertGreaterEqual(left_panel.width(), 480)
        self.assertLessEqual(left_panel.width(), 550)

        # At full screen 1920x1080: left_panel must stay between 480px and 550px
        win.resize(1920, 1080)
        QApplication.instance().processEvents()
        self.assertGreaterEqual(left_panel.width(), 480)
        self.assertLessEqual(left_panel.width(), 550)
        self.assertGreaterEqual(right_panel.width(), 1300)
        self.assertLessEqual(win.tunnel_model.width(), 510)
        # Verify tunnel model and speed tiles are docked at the bottom
        self.assertGreater(win.tunnel_model.geometry().y(), win.btn_circular.geometry().y())


if __name__ == "__main__":
    unittest.main()
