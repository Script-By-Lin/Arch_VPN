#!/usr/bin/env python3
"""
Network Manager for AuraLink Linux VPN.
Handles interface detection, gateway resolution, static route pinning,
TUN interface creation, DNS configuration (systemd-resolved & resolv.conf),
IPv6 leak protection, and atomic network teardown.
"""

import os
import sys
import re
import socket
import subprocess
import shutil
from typing import Dict, Optional, Tuple


class NetworkError(Exception):
    """Custom exception for network routing errors."""
    pass


class NetworkManager:
    def __init__(self, helper_path: Optional[str] = None):
        # Look for vpn-core-helper in bin or system path
        if helper_path and os.path.exists(helper_path):
            self.helper_path = helper_path
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            local_helper = os.path.join(base_dir, "bin", "vpn-core-helper")
            if os.path.exists(local_helper):
                self.helper_path = local_helper
            elif shutil.which("vpn-core-helper"):
                self.helper_path = shutil.which("vpn-core-helper")
            else:
                self.helper_path = local_helper

    def run_cmd(self, cmd_args: list, check: bool = True, use_sudo: bool = True) -> subprocess.CompletedProcess:
        """Run a command, using sudo or pkexec if not running as root."""
        full_cmd = []
        if use_sudo and os.geteuid() != 0:
            full_cmd = ["sudo", "-n"] + cmd_args
        else:
            full_cmd = cmd_args

        try:
            res = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            # If sudo -n failed due to password needed and pkexec exists, fallback to pkexec
            if res.returncode != 0 and use_sudo and os.geteuid() != 0 and "password is required" in res.stderr.lower():
                if shutil.which("pkexec"):
                    pkexec_cmd = ["pkexec"] + cmd_args
                    res = subprocess.run(
                        pkexec_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False
                    )
            
            if check and res.returncode != 0:
                raise NetworkError(f"Command failed ({' '.join(full_cmd)}): {res.stderr.strip()}")
            return res
        except FileNotFoundError as e:
            raise NetworkError(f"Required command not found: {e}")

    def get_physical_route(self, tun_name: str = "tun0") -> Tuple[str, str]:
        """
        Finds the default physical gateway IP and interface name, ignoring TUN devices.
        Returns (gateway_ip, device_name) e.g. ('192.168.1.1', 'wlan0').
        """
        # Try ip route show default
        try:
            res = subprocess.run(
                ["ip", "-4", "route", "show", "default"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            lines = res.stdout.strip().splitlines()
            for line in lines:
                # skip if this line mentions tun
                if tun_name in line or "tun" in line:
                    continue
                # line format: default via 192.168.1.1 dev wlan0 proto ...
                parts = line.split()
                if "via" in parts and "dev" in parts:
                    via_idx = parts.index("via")
                    dev_idx = parts.index("dev")
                    gw = parts[via_idx + 1]
                    dev = parts[dev_idx + 1]
                    return gw, dev
        except Exception:
            pass

        # Fallback to ip route get to public IP (e.g. 1.1.1.1 or 8.8.8.8)
        try:
            res = subprocess.run(
                ["ip", "-4", "route", "get", "1.1.1.1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            # Output format: 1.1.1.1 via 192.168.1.1 dev wlan0 src ...
            line = res.stdout.strip().splitlines()[0]
            parts = line.split()
            gw = None
            dev = None
            if "via" in parts:
                gw = parts[parts.index("via") + 1]
            if "dev" in parts:
                dev = parts[parts.index("dev") + 1]
            if gw and dev and dev != tun_name:
                return gw, dev
        except Exception as e:
            raise NetworkError(f"Could not determine physical default gateway and interface: {e}")

        raise NetworkError("Could not detect active physical gateway/interface.")

    def resolve_server_ip(self, host: str) -> str:
        """Resolves hostname to IPv4 address."""
        # Check if already an IPv4 address
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host):
            return host
        try:
            addr_info = socket.getaddrinfo(host, None, socket.AF_INET)
            if addr_info and len(addr_info) > 0:
                return addr_info[0][4][0]
        except Exception as e:
            raise NetworkError(f"Could not resolve server hostname '{host}': {e}")
        raise NetworkError(f"Failed to resolve server hostname: {host}")

    def is_tun_active(self, tun_name: str = "tun0") -> bool:
        res = subprocess.run(
            ["ip", "link", "show", tun_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return res.returncode == 0

    def setup_tun_interface(self, tun_name: str = "tun0", tun_ip: str = "10.0.0.2/24"):
        """Creates and configures TUN interface."""
        if not self.is_tun_active(tun_name):
            self.run_cmd(["ip", "tuntap", "add", "mode", "tun", "dev", tun_name])
            self.run_cmd(["ip", "addr", "add", tun_ip, "dev", tun_name])
            self.run_cmd(["ip", "link", "set", tun_name, "up"])

    def apply_routes(self, server_ip: str, gateway_ip: str, physical_dev: str, tun_name: str = "tun0"):
        """
        Pins server IP to physical gateway, then directs default route to tun.
        """
        # 1. Route server traffic via physical dev/gateway
        self.run_cmd(["ip", "route", "replace", f"{server_ip}/32", "via", gateway_ip, "dev", physical_dev])
        # 2. Set default route to TUN interface
        self.run_cmd(["ip", "route", "replace", "default", "dev", tun_name])
        # 3. Disable IPv6 default route to prevent leaks
        self.run_cmd(["ip", "-6", "route", "del", "default"], check=False)

    def configure_dns(self, tun_name: str = "tun0", primary_dns: str = "1.1.1.1", backup_dns: str = "8.8.8.8"):
        """Configures DNS on TUN interface using resolvectl with fallback."""
        if shutil.which("resolvectl"):
            self.run_cmd(["resolvectl", "dns", tun_name, primary_dns, backup_dns], check=False)
            self.run_cmd(["resolvectl", "domain", tun_name, "~."], check=False)
            self.run_cmd(["resolvectl", "default-route", tun_name, "yes"], check=False)
        elif shutil.which("systemd-resolve"):
            self.run_cmd(["systemd-resolve", "-i", tun_name, f"--set-dns={primary_dns}", "--set-domain=~."], check=False)

    def teardown_network(self, server_ip: Optional[str], gateway_ip: Optional[str], physical_dev: Optional[str], tun_name: str = "tun0"):
        """Restores physical route, reverts DNS, and deletes TUN interface."""
        # 1. Restore physical default route if known
        if gateway_ip and physical_dev:
            self.run_cmd(["ip", "route", "replace", "default", "via", gateway_ip, "dev", physical_dev], check=False)
        
        # 2. Delete server route
        if server_ip:
            self.run_cmd(["ip", "route", "del", f"{server_ip}/32"], check=False)

        # 3. Revert resolvectl DNS
        if shutil.which("resolvectl"):
            self.run_cmd(["resolvectl", "revert", tun_name], check=False)
        elif shutil.which("systemd-resolve"):
            self.run_cmd(["systemd-resolve", "--revert", "-i", tun_name], check=False)

        # 4. Remove TUN device
        if self.is_tun_active(tun_name):
            self.run_cmd(["ip", "link", "delete", tun_name], check=False)
