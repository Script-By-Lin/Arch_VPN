#!/usr/bin/env python3
"""
Stats Monitor for ShadowTun Linux VPN.
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
            return f"{num_bytes:.2f} {unit}" if unit in ['MB', 'GB', 'TB'] else f"{int(num_bytes)} {unit}"
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

    def start(self):
        self.start_time = time.time()
        rx, tx = self._read_interface_bytes()
        self.initial_rx = rx
        self.initial_tx = tx
        self.last_rx = rx
        self.last_tx = tx
        self.last_time = time.time()

    def stop(self):
        self.start_time = None
        self.initial_rx = None
        self.initial_tx = None

    def _read_interface_bytes(self) -> Tuple[int, int]:
        """Read rx_bytes and tx_bytes for interface from /proc/net/dev."""
        try:
            with open("/proc/net/dev", "r") as f:
                lines = f.readlines()
            for line in lines:
                if f"{self.interface}:" in line:
                    data = line.split(f"{self.interface}:")[1].split()
                    rx_bytes = int(data[0])
                    tx_bytes = int(data[8])
                    return rx_bytes, tx_bytes
        except Exception:
            pass
        return 0, 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns live statistics:
        {
            "connected_duration_sec": 120,
            "connected_duration_str": "02:00",
            "rx_bytes": 1024000,
            "tx_bytes": 512000,
            "rx_speed_bps": 20480,
            "tx_speed_bps": 10240,
            "rx_speed_str": "20.48 KB/s",
            "tx_speed_str": "10.24 KB/s",
            "rx_total_str": "1.02 MB",
            "tx_total_str": "512 KB"
        }
        """
        now = time.time()
        dt = max(now - self.last_time, 0.1)
        curr_rx, curr_tx = self._read_interface_bytes()

        if self.initial_rx is None:
            self.initial_rx = curr_rx
            self.initial_tx = curr_tx

        # Calculate live speed
        rx_diff = max(curr_rx - self.last_rx, 0)
        tx_diff = max(curr_tx - self.last_tx, 0)
        rx_speed = rx_diff / dt
        tx_speed = tx_diff / dt

        self.last_rx = curr_rx
        self.last_tx = curr_tx
        self.last_time = now

        total_rx = max(curr_rx - self.initial_rx, 0)
        total_tx = max(curr_tx - self.initial_tx, 0)

        duration = int(now - self.start_time) if self.start_time else 0
        hours, rem = divmod(duration, 3600)
        mins, secs = divmod(rem, 60)
        if hours > 0:
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins:02d}:{secs:02d}"

        return {
            "duration_sec": duration,
            "duration_str": duration_str,
            "rx_bytes": total_rx,
            "tx_bytes": total_tx,
            "rx_speed_bps": rx_speed,
            "tx_speed_bps": tx_speed,
            "rx_speed_str": format_speed(rx_speed),
            "tx_speed_str": format_speed(tx_speed),
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
