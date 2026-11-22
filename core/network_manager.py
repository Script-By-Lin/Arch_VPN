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
import time
import socket
import subprocess
import shutil
import threading
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple


IPV6_CONF_DIR = "/proc/sys/net/ipv6/conf"


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
        """Creates and configures TUN interface (prefers single helper call)."""
        if not self.is_tun_active(tun_name):
            helper = self._select_helper("tun-up")
            if helper:
                res = self.run_cmd([helper, "tun-up", tun_name, tun_ip], check=False)
                if res.returncode == 0 and self.is_tun_active(tun_name):
                    return
            self.run_cmd(["ip", "tuntap", "add", "mode", "tun", "dev", tun_name])
            self.run_cmd(["ip", "addr", "add", tun_ip, "dev", tun_name])
            self.run_cmd(["ip", "link", "set", tun_name, "up"])

    def apply_routes(self, server_ip: str, gateway_ip: str, physical_dev: str, tun_name: str = "tun0"):
        """
        Pins server IP to physical gateway, then directs default route to tun.
        """
        helper = self._select_helper("routes-up")
        if helper:
            res = self.run_cmd([helper, "routes-up", server_ip, gateway_ip, physical_dev, tun_name], check=False)
            if res.returncode == 0:
                return
        # Fallback: direct ip commands
        self.run_cmd(["ip", "route", "replace", f"{server_ip}/32", "via", gateway_ip, "dev", physical_dev])
        self.run_cmd(["ip", "route", "replace", "default", "dev", tun_name])
        self.run_cmd(["ip", "-6", "route", "del", "default"], check=False)

    def activate_tunnel_network(
        self,
        server_ip: str,
        gateway_ip: str,
        physical_dev: str,
        tun_name: str = "tun0",
        primary_dns: str = "1.1.1.1",
        backup_dns: str = "8.8.8.8",
        disable_ipv6: bool = True,
        ipv6_prev_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Atomically disables IPv6 (if requested), applies server + default TUN routes,
        and configures DNS with cache flush in a single privileged helper invocation.
        Falls back to individual methods if an older helper is installed.
        """
        lo_val = 0
        if disable_ipv6:
            if ipv6_prev_state and isinstance(ipv6_prev_state.get("interfaces"), dict):
                lo_val = 1 if ipv6_prev_state["interfaces"].get("lo", 0) else 0
            else:
                cur_lo = self._read_ipv6_sysctl("lo")
                if cur_lo is not None:
                    lo_val = cur_lo

        helper = self._select_helper("net-activate")
        if helper:
            p_dns = (primary_dns or "1.1.1.1").strip()
            b_dns = (backup_dns or "").strip() or "-"
            args = [
                helper,
                "net-activate",
                server_ip,
                gateway_ip,
                physical_dev,
                tun_name,
                p_dns,
                b_dns,
                "1" if disable_ipv6 else "0",
                str(lo_val),
            ]
            res = self.run_cmd(args, check=False)
            if res.returncode == 0:
                ipv6_ok = self.is_ipv6_disabled(physical_dev=physical_dev) if disable_ipv6 else False
                return {
                    "batched": True,
                    "ipv6_disabled": ipv6_ok,
                    "routes_applied": True,
                    "dns_configured": True,
                }

        # Fallback to individual calls
        ipv6_ok = False
        if disable_ipv6:
            ipv6_ok = self.disable_ipv6(physical_dev=physical_dev, prev_state=ipv6_prev_state)
        self.apply_routes(
            server_ip=server_ip,
            gateway_ip=gateway_ip,
            physical_dev=physical_dev,
            tun_name=tun_name,
        )
        dns_ok = self.configure_dns(
            tun_name=tun_name,
            primary_dns=primary_dns,
            backup_dns=backup_dns,
        )
        return {
            "batched": False,
            "ipv6_disabled": ipv6_ok,
            "routes_applied": True,
            "dns_configured": dns_ok,
        }

    def verify_tunnel_connectivity(
        self,
        timeout: float = 12.0,
        retry_interval: float = 0.45,
        check_alive: Optional[Callable[[], bool]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> Dict[str, Any]:
        """
        Verifies real end-to-end internet & DNS flow through the active TUN route.
        Retries rapidly until either HTTP/DNS succeeds, cancel_event fires, or timeout expires.
        Bypasses environment HTTP_PROXY variables so traffic genuinely traverses tun0.
        """
        start = time.monotonic()
        deadline = start + max(1.0, float(timeout))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        http_probes = [
            "http://cp.cloudflare.com/generate_204",
            "http://connectivitycheck.gstatic.com/generate_204",
        ]
        ip_tcp_probes = [
            ("1.1.1.1", 443),
            ("8.8.8.8", 443),
        ]

        attempt = 0
        last_err = ""
        ip_only_ok = False
        ip_latency_ms: Optional[int] = None

        while time.monotonic() < deadline:
            if cancel_event and cancel_event.is_set():
                return {
                    "verified": False,
                    "dns_ok": False,
                    "aborted": False,
                    "cancelled": True,
                    "latency_ms": None,
                    "endpoint": "",
                    "elapsed_sec": round(time.monotonic() - start, 2),
                    "detail": "Connection cancelled by user",
                }
            if check_alive and not check_alive():
                return {
                    "verified": False,
                    "dns_ok": False,
                    "aborted": True,
                    "cancelled": False,
                    "latency_ms": None,
                    "endpoint": "",
                    "elapsed_sec": round(time.monotonic() - start, 2),
                    "detail": "Tunnel daemon stopped during verification",
                }

            url = http_probes[attempt % len(http_probes)]
            remaining = deadline - time.monotonic()
            per_req_timeout = min(2.0, max(0.8, remaining))

            t0 = time.monotonic()
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={"User-Agent": "AuraLink-Probe/1.0", "Connection": "close"},
                )
                with opener.open(req, timeout=per_req_timeout) as resp:
                    if cancel_event and cancel_event.is_set():
                        return {
                            "verified": False,
                            "dns_ok": False,
                            "aborted": False,
                            "cancelled": True,
                            "latency_ms": None,
                            "endpoint": "",
                            "elapsed_sec": round(time.monotonic() - start, 2),
                            "detail": "Connection cancelled by user",
                        }
                    status = getattr(resp, "status", 200)
                    if 200 <= status < 400:
                        lat_ms = int((time.monotonic() - t0) * 1000)
                        return {
                            "verified": True,
                            "dns_ok": True,
                            "aborted": False,
                            "cancelled": False,
                            "latency_ms": lat_ms,
                            "endpoint": url,
                            "elapsed_sec": round(time.monotonic() - start, 2),
                            "detail": f"Internet & DNS verified ({lat_ms}ms)",
                        }
            except Exception as e:
                last_err = str(e)

            if cancel_event and cancel_event.is_set():
                return {
                    "verified": False,
                    "dns_ok": False,
                    "aborted": False,
                    "cancelled": True,
                    "latency_ms": None,
                    "endpoint": "",
                    "elapsed_sec": round(time.monotonic() - start, 2),
                    "detail": "Connection cancelled by user",
                }

            # After 2 failed hostname attempts (~4s), also test raw IP TCP connectivity
            # so we know if the tunnel forwards packets even when DNS is slow/restricted.
            if attempt >= 1 and not ip_only_ok and time.monotonic() < deadline:
                host, port = ip_tcp_probes[attempt % len(ip_tcp_probes)]
                t_ip = time.monotonic()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(min(1.5, max(0.5, deadline - time.monotonic())))
                try:
                    s.connect((host, port))
                    ip_only_ok = True
                    ip_latency_ms = int((time.monotonic() - t_ip) * 1000)
                except Exception:
                    pass
                finally:
                    try:
                        s.close()
                    except Exception:
                        pass

            attempt += 1
            sleep_for = min(retry_interval, max(0.0, deadline - time.monotonic()))
            if sleep_for > 0:
                if cancel_event:
                    if cancel_event.wait(sleep_for):
                        return {
                            "verified": False,
                            "dns_ok": False,
                            "aborted": False,
                            "cancelled": True,
                            "latency_ms": None,
                            "endpoint": "",
                            "elapsed_sec": round(time.monotonic() - start, 2),
                            "detail": "Connection cancelled by user",
                        }
                else:
                    time.sleep(sleep_for)

        elapsed = round(time.monotonic() - start, 2)
        if ip_only_ok:
            return {
                "verified": True,
                "dns_ok": False,
                "aborted": False,
                "cancelled": False,
                "latency_ms": ip_latency_ms,
                "endpoint": "1.1.1.1:443",
                "elapsed_sec": elapsed,
                "detail": f"Tunnel TCP verified ({ip_latency_ms}ms), DNS warming up",
            }

        return {
            "verified": False,
            "dns_ok": False,
            "aborted": False,
            "cancelled": False,
            "latency_ms": None,
            "endpoint": "",
            "elapsed_sec": elapsed,
            "detail": f"Probe timed out after {elapsed}s ({last_err[:80]})" if last_err else f"Probe timed out after {elapsed}s",
        }

    def _select_helper(self, required_action: Optional[str] = None) -> Optional[str]:
        """Selects vpn-core-helper, preferring /usr/local/bin/vpn-core-helper for sudoers match."""
        candidates = []
        installed_helper = "/usr/local/bin/vpn-core-helper"
        if os.path.exists(installed_helper):
            candidates.append(installed_helper)
        if self.helper_path and os.path.exists(self.helper_path) and self.helper_path not in candidates:
            candidates.append(self.helper_path)

        for path in candidates:
            if not required_action:
                return path
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    if f"{required_action})" in f.read():
                        return path
            except Exception:
                continue
        return None

    @staticmethod
    def _read_ipv6_sysctl(iface: str) -> Optional[int]:
        """Reads /proc/sys/net/ipv6/conf/<iface>/disable_ipv6 as 0 or 1."""
        path = os.path.join(IPV6_CONF_DIR, iface, "disable_ipv6")
        try:
            with open(path, "r", encoding="utf-8") as f:
                val = int(f.read().strip())
                return 1 if val else 0
        except Exception:
            return None

    def get_ipv6_state(self, physical_dev: Optional[str] = None) -> Dict[str, Any]:
        """
        Snapshots current kernel IPv6 disable_ipv6 sysctl state before disabling IPv6,
        so it can be restored accurately on VPN disconnect.
        """
        if not os.path.isdir(IPV6_CONF_DIR):
            return {"available": False, "all": 0, "default": 0, "interfaces": {}}

        all_val = self._read_ipv6_sysctl("all")
        default_val = self._read_ipv6_sysctl("default")
        interfaces: Dict[str, int] = {}

        try:
            for entry in sorted(os.listdir(IPV6_CONF_DIR)):
                if entry in ("all", "default"):
                    continue
                val = self._read_ipv6_sysctl(entry)
                if val is not None:
                    interfaces[entry] = val
        except Exception:
            pass

        if physical_dev and physical_dev not in interfaces:
            val = self._read_ipv6_sysctl(physical_dev)
            if val is not None:
                interfaces[physical_dev] = val

        return {
            "available": all_val is not None,
            "all": all_val if all_val is not None else 0,
            "default": default_val if default_val is not None else 0,
            "interfaces": interfaces,
        }

    def is_ipv6_disabled(self, physical_dev: Optional[str] = None) -> bool:
        """Returns True if IPv6 is disabled globally (and on physical_dev when provided)."""
        if not os.path.isdir(IPV6_CONF_DIR):
            return True
        all_val = self._read_ipv6_sysctl("all")
        if all_val != 1:
            return False
        if physical_dev:
            dev_val = self._read_ipv6_sysctl(physical_dev)
            if dev_val is not None and dev_val != 1:
                return False
        return True

    def disable_ipv6(
        self,
        physical_dev: Optional[str] = None,
        prev_state: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Disables IPv6 on all network interfaces via kernel sysctl while preserving
        loopback (lo) if it was enabled, preventing IPv6 traffic & RA/DHCPv6 leaks.
        """
        if not os.path.isdir(IPV6_CONF_DIR):
            return True

        lo_val = 0
        if prev_state and isinstance(prev_state.get("interfaces"), dict):
            lo_val = 1 if prev_state["interfaces"].get("lo", 0) else 0
        else:
            cur_lo = self._read_ipv6_sysctl("lo")
            if cur_lo is not None:
                lo_val = cur_lo

        # 1. Drop any active IPv6 default route immediately
        self.run_cmd(["ip", "-6", "route", "del", "default"], check=False)

        # 2. Prefer vpn-core-helper (already authorized via sudoers)
        helper = self._select_helper("ipv6-disable")
        if helper:
            args = [helper, "ipv6-disable", str(lo_val)]
            if physical_dev and re.match(r"^[a-zA-Z0-9_.:-]+$", physical_dev):
                args.append(physical_dev)
            res = self.run_cmd(args, check=False)
            if res.returncode == 0 and self.is_ipv6_disabled(physical_dev=physical_dev):
                return True

        # 3. Fallback to sysctl directly
        sysctl_bin = shutil.which("sysctl")
        if sysctl_bin:
            params: List[str] = [
                "net.ipv6.conf.all.disable_ipv6=1",
                "net.ipv6.conf.default.disable_ipv6=1",
            ]
            if physical_dev and re.match(r"^[a-zA-Z0-9_.:-]+$", physical_dev):
                safe_dev = physical_dev.replace(".", "/")
                params.append(f"net.ipv6.conf.{safe_dev}.disable_ipv6=1")
            if os.path.exists(os.path.join(IPV6_CONF_DIR, "lo", "disable_ipv6")):
                params.append(f"net.ipv6.conf.lo.disable_ipv6={lo_val}")

            self.run_cmd([sysctl_bin, "-w"] + params, check=False)

        return self.is_ipv6_disabled(physical_dev=physical_dev)

    def restore_ipv6(self, prev_state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Restores kernel IPv6 disable_ipv6 sysctl state saved before VPN connection.
        """
        if not os.path.isdir(IPV6_CONF_DIR):
            return True

        all_val = 0
        default_val = 0
        interfaces: Dict[str, int] = {}

        if isinstance(prev_state, dict):
            all_val = 1 if prev_state.get("all", 0) else 0
            default_val = 1 if prev_state.get("default", 0) else 0
            raw_ifaces = prev_state.get("interfaces")
            if isinstance(raw_ifaces, dict):
                for iface, val in raw_ifaces.items():
                    if (
                        isinstance(iface, str)
                        and re.match(r"^[a-zA-Z0-9_.:-]+$", iface)
                        and os.path.exists(os.path.join(IPV6_CONF_DIR, iface, "disable_ipv6"))
                    ):
                        interfaces[iface] = 1 if val else 0

        # 1. Prefer vpn-core-helper
        helper = self._select_helper("ipv6-restore")
        if helper:
            args = [helper, "ipv6-restore", str(all_val), str(default_val)]
            for iface, val in interfaces.items():
                args.append(f"{iface}={val}")
            res = self.run_cmd(args, check=False)
            if res.returncode == 0:
                return True

        # 2. Fallback to sysctl directly
        sysctl_bin = shutil.which("sysctl")
        if sysctl_bin:
            params: List[str] = [
                f"net.ipv6.conf.all.disable_ipv6={all_val}",
                f"net.ipv6.conf.default.disable_ipv6={default_val}",
            ]
            for iface, val in interfaces.items():
                safe_iface = iface.replace(".", "/")
                params.append(f"net.ipv6.conf.{safe_iface}.disable_ipv6={val}")
            res = self.run_cmd([sysctl_bin, "-w"] + params, check=False)
            return res.returncode == 0

        return False

    def configure_dns(self, tun_name: str = "tun0", primary_dns: str = "1.1.1.1", backup_dns: str = "8.8.8.8") -> bool:
        """
        Configures DNS on TUN interface across all Linux distros
        (systemd-resolved, systemd-resolve, openresolv/resolvconf, or /etc/resolv.conf via vpn-core-helper).
        """
        p_dns = primary_dns.strip()
        b_dns = (backup_dns or "").strip()

        # 1. Prefer vpn-core-helper (supports systemd-resolved, openresolv, and /etc/resolv.conf passwordlessly)
        helper = self._select_helper("dns-up")
        if helper:
            args = [helper, "dns-up", tun_name, p_dns]
            if b_dns:
                args.append(b_dns)
            res = self.run_cmd(args, check=False)
            if res.returncode == 0:
                return True

        dns_args = [p_dns]
        if b_dns:
            dns_args.append(b_dns)

        # 2. Direct resolvectl fallback
        if shutil.which("resolvectl"):
            try:
                res = self.run_cmd(["resolvectl", "dns", tun_name] + dns_args, check=False)
                if res.returncode == 0:
                    self.run_cmd(["resolvectl", "domain", tun_name, "~."], check=False)
                    self.run_cmd(["resolvectl", "default-route", tun_name, "yes"], check=False)
                    self.run_cmd(["resolvectl", "dnsovertls", tun_name, "opportunistic"], check=False)
                    self.run_cmd(["resolvectl", "flush-caches"], check=False)
                    return True
            except Exception:
                pass

        # 3. Direct legacy systemd-resolve fallback
        if shutil.which("systemd-resolve"):
            try:
                res = self.run_cmd(["systemd-resolve", "-i", tun_name, f"--set-dns={p_dns}", "--set-domain=~."], check=False)
                if res.returncode == 0:
                    self.run_cmd(["systemd-resolve", "--flush-caches"], check=False)
                    return True
            except Exception:
                pass

        return False

    def teardown_network(
        self,
        server_ip: Optional[str],
        gateway_ip: Optional[str],
        physical_dev: Optional[str],
        tun_name: str = "tun0",
        ipv6_prev_state: Optional[Dict[str, Any]] = None,
        restore_ipv6_flag: bool = False,
    ):
        """Restores physical route, reverts DNS, restores IPv6, and deletes TUN interface."""
        # 1. Restore physical default route if known
        if gateway_ip and physical_dev:
            self.run_cmd(["ip", "route", "replace", "default", "via", gateway_ip, "dev", physical_dev], check=False)
        
        # 2. Delete server route
        if server_ip:
            self.run_cmd(["ip", "route", "del", f"{server_ip}/32"], check=False)

        # 3. Revert DNS via vpn-core-helper (handles resolvectl, resolvconf, and /etc/resolv.conf backup)
        helper = self._select_helper("dns-down")
        dns_reverted = False
        if helper:
            res = self.run_cmd([helper, "dns-down", tun_name], check=False)
            dns_reverted = (res.returncode == 0)

        if not dns_reverted:
            if shutil.which("resolvectl"):
                self.run_cmd(["resolvectl", "revert", tun_name], check=False)
            elif shutil.which("systemd-resolve"):
                self.run_cmd(["systemd-resolve", "--revert", "-i", tun_name], check=False)

        # 4. Remove TUN device
        if self.is_tun_active(tun_name):
            self.run_cmd(["ip", "link", "delete", tun_name], check=False)

        # 5. Restore IPv6 sysctl state if disabled during VPN session
        if restore_ipv6_flag or ipv6_prev_state is not None:
            self.restore_ipv6(prev_state=ipv6_prev_state)
