#!/usr/bin/env python3
"""
Stats Monitor for AuraLink Linux VPN.
Monitors interface traffic, live upload/download speed, connection duration,
and server ping / latency.
"""

import time
import socket
import subprocess
from typing import Dict, Optional, Tuple, Any


def format_bytes(num_bytes: float) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}" if unit != 'B' else f"{int(num_bytes)} B"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_speed(bps: float) -> str:
    """Format bytes per second into human-readable transfer rate."""
    return f"{format_bytes(bps)}/s"


class StatsMonitor:
    def __init__(self, interface: str = "tun0"):
        self.interface = interface
        self.last_rx = 0
        self.last_tx = 0
        self.last_time = time.time()
        self.start_time = None
        self.initial_rx = None
        self.initial_tx = None
        self._smoothed_rx_speed = 0.0
        self._smoothed_tx_speed = 0.0

    def start(self, start_time: Optional[float] = None, initial_rx: Optional[int] = None, initial_tx: Optional[int] = None):
        """Starts monitoring. Optionally restores a previous session start time and initial bytes."""
        now = time.time()
        self.start_time = float(start_time) if start_time is not None else now
        rx, tx = self._read_interface_bytes()
        self.initial_rx = int(initial_rx) if initial_rx is not None else rx
        self.initial_tx = int(initial_tx) if initial_tx is not None else tx
        self.last_rx = rx
        self.last_tx = tx
        self.last_time = now
        self._smoothed_rx_speed = 0.0
        self._smoothed_tx_speed = 0.0

    def stop(self):
        self.start_time = None
        self.initial_rx = None
        self.initial_tx = None
        self._smoothed_rx_speed = 0.0
        self._smoothed_tx_speed = 0.0

    def _read_interface_bytes(self) -> Tuple[int, int]:
        """Read rx_bytes and tx_bytes for exact interface from /proc/net/dev."""
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()
            for line in lines:
                if ":" in line:
                    iface_part, stats_part = line.split(":", 1)
                    if iface_part.strip() == self.interface:
                        cols = stats_part.split()
                        if len(cols) >= 9:
                            return int(cols[0]), int(cols[8])
        except Exception:
            pass
        return 0, 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns live telemetry:
        {
            "is_active": True,
            "duration_sec": 120,
            "duration_str": "02:00",
            "rx_bytes": 1024000,
            "tx_bytes": 512000,
            "rx_speed_bps": 20480.0,
            "tx_speed_bps": 10240.0,
            "rx_speed_str": "20.48 KB/s",
            "tx_speed_str": "10.24 KB/s",
            "rx_total_str": "1.02 MB",
            "tx_total_str": "512 KB"
        }
        """
        if self.start_time is None:
            return {
                "is_active": False,
                "duration_sec": 0,
                "duration_str": "00:00",
                "rx_bytes": 0,
                "tx_bytes": 0,
                "rx_speed_bps": 0.0,
                "tx_speed_bps": 0.0,
                "rx_speed_str": "0 B/s",
                "tx_speed_str": "0 B/s",
                "rx_total_str": "0 B",
                "tx_total_str": "0 B"
            }

        now = time.time()
        dt = max(now - self.last_time, 0.05)
        curr_rx, curr_tx = self._read_interface_bytes()

        if self.initial_rx is None:
            self.initial_rx = curr_rx
            self.initial_tx = curr_tx

        # Calculate live transfer rate with light smoothing (0.7 instant, 0.3 prior)
        rx_diff = max(curr_rx - self.last_rx, 0)
        tx_diff = max(curr_tx - self.last_tx, 0)
        instant_rx_speed = rx_diff / dt
        instant_tx_speed = tx_diff / dt

        if self._smoothed_rx_speed == 0.0 and instant_rx_speed > 0:
            self._smoothed_rx_speed = instant_rx_speed
        else:
            self._smoothed_rx_speed = 0.75 * instant_rx_speed + 0.25 * self._smoothed_rx_speed

        if self._smoothed_tx_speed == 0.0 and instant_tx_speed > 0:
            self._smoothed_tx_speed = instant_tx_speed
        else:
            self._smoothed_tx_speed = 0.75 * instant_tx_speed + 0.25 * self._smoothed_tx_speed

        self.last_rx = curr_rx
        self.last_tx = curr_tx
        self.last_time = now

        total_rx = max(curr_rx - self.initial_rx, 0)
        total_tx = max(curr_tx - self.initial_tx, 0)

        duration = max(int(now - self.start_time), 0)
        hours, rem = divmod(duration, 3600)
        mins, secs = divmod(rem, 60)
        if hours > 0:
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins:02d}:{secs:02d}"

        return {
            "is_active": True,
            "duration_sec": duration,
            "duration_str": duration_str,
            "rx_bytes": total_rx,
            "tx_bytes": total_tx,
            "rx_speed_bps": self._smoothed_rx_speed,
            "tx_speed_bps": self._smoothed_tx_speed,
            "rx_speed_str": format_speed(self._smoothed_rx_speed),
            "tx_speed_str": format_speed(self._smoothed_tx_speed),
            "rx_total_str": format_bytes(total_rx),
            "tx_total_str": format_bytes(total_tx)
        }

    @staticmethod
    def measure_ping(host: str, port: int = 443, timeout: float = 3.0) -> Optional[int]:
        """
        Measures TCP handshake latency to host:port in milliseconds.
        Returns latency in ms or None if unreachable.
        """
        start = time.perf_counter()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            s.close()
            elapsed = (time.perf_counter() - start) * 1000
            return max(int(elapsed), 1)
        except Exception:
            return None
        finally:
            try:
                s.close()
            except Exception:
                pass
