#!/usr/bin/env python3
"""
Process Manager for ShadowTun Linux VPN.
Manages sslocal and tun2socks processes, PID tracking, socket readiness checks,
and graceful termination.
"""

import os
import sys
import time
import socket
import signal
import subprocess
import shutil
from typing import Optional, List

STATE_DIR = os.path.expanduser("~/.config/shadowtun/state")
LOG_DIR = os.path.expanduser("~/.config/shadowtun/logs")


class ProcessError(Exception):
    pass


class ProcessManager:
    def __init__(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        self.sslocal_pid_file = os.path.join(STATE_DIR, "sslocal.pid")
        self.tun2socks_pid_file = os.path.join(STATE_DIR, "tun2socks.pid")
        self.sslocal_log = os.path.join(LOG_DIR, "sslocal.log")
        self.tun2socks_log = os.path.join(LOG_DIR, "tun2socks.log")

    def _read_pid(self, pid_file: str) -> Optional[int]:
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    return int(f.read().strip())
            except Exception:
                return None
        return None

    def _write_pid(self, pid_file: str, pid: int):
        with open(pid_file, "w") as f:
            f.write(str(pid))

    def _clear_pid(self, pid_file: str):
        if os.path.exists(pid_file):
            try:
                os.remove(pid_file)
            except Exception:
                pass

    def is_pid_alive(self, pid: Optional[int]) -> bool:
        if not pid or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def wait_for_port(self, host: str, port: int, timeout: float = 6.0) -> bool:
        """Polls until TCP port is accepting connections or timeout expires."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                s.close()
                return True
            except (socket.error, ConnectionRefusedError):
                time.sleep(0.2)
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return False

    def start_sslocal(self, config_path: str, host: str = "127.0.0.1", port: int = 1080) -> int:
        """Starts sslocal daemon with the given config."""
        sslocal_bin = shutil.which("sslocal")
        if not sslocal_bin:
            raise ProcessError("sslocal binary not found. Please install shadowsocks-rust.")

        self.stop_sslocal()

        log_f = open(self.sslocal_log, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                [sslocal_bin, "-c", config_path, "-v"],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            self._write_pid(self.sslocal_pid_file, proc.pid)
        except Exception as e:
            log_f.close()
            raise ProcessError(f"Failed to start sslocal: {e}")

        # Wait for local port to become ready
        if not self.wait_for_port(host, port, timeout=5.0):
            if proc.poll() is not None:
                log_f.close()
                with open(self.sslocal_log, "r", encoding="utf-8", errors="ignore") as f:
                    err_lines = f.read()
                raise ProcessError(f"sslocal exited prematurely (code {proc.returncode}):\n{err_lines[-300:]}")
            log_f.close()
            raise ProcessError(f"sslocal started but failed to listen on {host}:{port} within timeout.")

        return proc.pid

    def start_tun2socks(self, tun_device: str = "tun0", proxy_url: str = "socks5://127.0.0.1:1080", restapi_addr: str = "127.0.0.1:17070") -> int:
        """Starts tun2socks process with sudo."""
        tun2socks_bin = shutil.which("tun2socks") or "/usr/local/bin/tun2socks"
        if not os.path.exists(tun2socks_bin) and not shutil.which("tun2socks"):
            raise ProcessError("tun2socks binary not found. Please install tun2socks.")

        self.stop_tun2socks()

        cmd = [
            tun2socks_bin,
            "--device", tun_device,
            "--proxy", proxy_url,
            "--loglevel", "info"
        ]
        
        if os.geteuid() != 0:
            full_cmd = ["sudo", "-n"] + cmd
        else:
            full_cmd = cmd

        log_f = open(self.tun2socks_log, "w", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                full_cmd,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            self._write_pid(self.tun2socks_pid_file, proc.pid)
        except Exception as e:
            log_f.close()
            raise ProcessError(f"Failed to start tun2socks: {e}")

        time.sleep(0.8)
        if proc.poll() is not None:
            log_f.close()
            with open(self.tun2socks_log, "r", encoding="utf-8", errors="ignore") as f:
                err_lines = f.read()
            raise ProcessError(f"tun2socks exited prematurely (code {proc.returncode}):\n{err_lines[-300:]}")

        return proc.pid

    def stop_sslocal(self):
        pid = self._read_pid(self.sslocal_pid_file)
        if pid and self.is_pid_alive(pid):
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                time.sleep(0.3)
                if self.is_pid_alive(pid):
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
        self._clear_pid(self.sslocal_pid_file)
        subprocess.run(["pkill", "-u", str(os.getuid()), "-f", "sslocal -c"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop_tun2socks(self, tun_device: str = "tun0"):
        pid = self._read_pid(self.tun2socks_pid_file)
        if pid and self.is_pid_alive(pid):
            try:
                subprocess.run(["sudo", "-n", "kill", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        self._clear_pid(self.tun2socks_pid_file)
        subprocess.run(["sudo", "-n", "pkill", "-f", f"tun2socks --device {tun_device}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "-n", "pkill", "-f", "tun2socks"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop_all(self, tun_device: str = "tun0"):
        self.stop_tun2socks(tun_device)
        self.stop_sslocal()

    def is_running(self) -> bool:
        sslocal_pid = self._read_pid(self.sslocal_pid_file)
        tun2socks_pid = self._read_pid(self.tun2socks_pid_file)
        return bool(self.is_pid_alive(sslocal_pid) and self.is_pid_alive(tun2socks_pid))

    def get_recent_logs(self, max_lines: int = 50) -> List[str]:
        logs = []
        if os.path.exists(self.sslocal_log):
            try:
                with open(self.sslocal_log, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    logs.extend([f"[sslocal] {l.strip()}" for l in lines[-max_lines:]])
            except Exception:
                pass
        if os.path.exists(self.tun2socks_log):
            try:
                with open(self.tun2socks_log, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    logs.extend([f"[tun2socks] {l.strip()}" for l in lines[-max_lines:]])
            except Exception:
                pass
        return logs[-max_lines:]
