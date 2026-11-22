#!/usr/bin/env python3
"""
VPN Service Orchestrator for AuraLink Linux VPN.
Coordinates ConfigManager, ProcessManager, NetworkManager, and StatsMonitor.
Provides thread-safe state management, events, and automatic rollback on failure.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, Optional, Callable, List, Any

from .config_manager import ConfigManager, ConfigError
from .network_manager import NetworkManager, NetworkError
from .process_manager import ProcessManager, ProcessError
from .stats_monitor import StatsMonitor


STATE_DISCONNECTED = "DISCONNECTED"
STATE_CONNECTING = "CONNECTING"
STATE_CONNECTED = "CONNECTED"
STATE_DISCONNECTING = "DISCONNECTING"
STATE_ERROR = "ERROR"

SESSION_FILE = os.path.expanduser("~/.config/auralink/state/session.json")


class VPNService:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.process_mgr = ProcessManager()
        self.network_mgr = NetworkManager()
        self.stats_monitor = StatsMonitor()

        self._state = STATE_DISCONNECTED
        self._last_error = ""
        self._active_profile: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._listeners: List[Callable[[str, Dict[str, Any]], None]] = []

        # Check existing state on startup
        self._restore_existing_state()

    def _restore_existing_state(self):
        """Detects if VPN was already active or in inconsistent state."""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    session = json.load(f)
                tun_dev = session.get("tun_dev", "tun0")
                if self.process_mgr.is_running() and self.network_mgr.is_tun_active(tun_dev):
                    self._state = STATE_CONNECTED
                    self.stats_monitor = StatsMonitor(tun_dev)
                    conn_time = session.get("connected_at")
                    init_rx = session.get("initial_rx")
                    init_tx = session.get("initial_tx")
                    self.stats_monitor.start(start_time=conn_time, initial_rx=init_rx, initial_tx=init_tx)
                    profile_id = session.get("profile_id")
                    if profile_id:
                        self._active_profile = self.config_mgr.get_profile_by_id(profile_id)
                else:
                    # Clean up dangling state
                    self._state = STATE_DISCONNECTED
            except Exception:
                self._state = STATE_DISCONNECTED

    @property
    def state(self) -> str:
        return self._state

    @property
    def active_profile(self) -> Optional[Dict[str, Any]]:
        return self._active_profile

    @property
    def last_error(self) -> str:
        return self._last_error

    def add_listener(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Subscribe to VPN state and event updates."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, Dict[str, Any]], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self, event_type: str, data: Dict[str, Any] = None):
        if data is None:
            data = {}
        data["state"] = self._state
        for listener in list(self._listeners):
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"[VPNService] Listener error: {e}", file=sys.stderr)

    def _teardown_internal(self):
        """Internal teardown of network routes, DNS, IPv6, processes, and session."""
        server_ip = None
        gw = None
        dev = None
        tun_dev = "tun0"
        ipv6_disabled = False
        ipv6_prev_state = None

        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    session = json.load(f)
                server_ip = session.get("server_ip")
                gw = session.get("gateway_ip")
                dev = session.get("physical_dev")
                tun_dev = session.get("tun_dev", "tun0")
                ipv6_disabled = bool(session.get("ipv6_disabled", False))
                ipv6_prev_state = session.get("ipv6_prev_state")
            except Exception:
                pass

        # 1. Teardown network routing, DNS & restore IPv6
        self.network_mgr.teardown_network(
            server_ip=server_ip,
            gateway_ip=gw,
            physical_dev=dev,
            tun_name=tun_dev,
            ipv6_prev_state=ipv6_prev_state if ipv6_disabled else None,
            restore_ipv6_flag=ipv6_disabled
        )

        # 2. Stop daemon processes
        self.process_mgr.stop_all(tun_device=tun_dev)

        # 3. Stop stats monitor
        if hasattr(self, "stats_monitor") and self.stats_monitor:
            try:
                self.stats_monitor.stop()
            except Exception:
                pass

        # 4. Clean session file
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass

    def connect(self, target: Any = None) -> bool:
        """
        Connect to VPN.
        Target can be a profile Dict, profile ID, profile Name, or ssconf:// / ss:// key string.
        If already connected to another server, seamlessly switches to the new server.
        """
        with self._lock:
            if self._state == STATE_CONNECTING:
                return True

            try:
                profile = None
                if target is None:
                    # Use active profile or first profile
                    settings = self.config_mgr.get_settings()
                    active_id = settings.get("active_profile_id")
                    if active_id:
                        profile = self.config_mgr.get_profile_by_id(active_id)
                    if not profile:
                        profiles = self.config_mgr.get_profiles()
                        if profiles:
                            profile = profiles[0]
                    if not profile:
                        raise ConfigError("No profiles available. Please enter a key or ssconf URL.")
                elif isinstance(target, dict):
                    profile = target
                elif isinstance(target, str):
                    if target.startswith("ssconf://") or target.startswith("ss://") or target.startswith("http") or target.startswith("{"):
                        profile = self.config_mgr.parse_key(target)
                        self.config_mgr.add_or_update_profile(profile)
                    else:
                        # Try by ID or Name
                        profile = self.config_mgr.get_profile_by_id(target) or self.config_mgr.get_profile_by_name(target)
                        if not profile:
                            # Try parsing as raw input
                            profile = self.config_mgr.parse_key(target)
                            self.config_mgr.add_or_update_profile(profile)

                if not profile:
                    raise ConfigError(f"Could not load profile from: {target}")

                # If already connected to the SAME profile, nothing to do
                if self._state == STATE_CONNECTED and self._active_profile and self._active_profile.get("id") == profile.get("id"):
                    return True

                # If currently connected to a DIFFERENT profile, seamlessly switch
                if self._state == STATE_CONNECTED:
                    old_name = self._active_profile.get("name", "previous server") if self._active_profile else "previous server"
                    self._notify("progress", {"message": f"Switching from {old_name} to {profile.get('name')}..."})
                    self._teardown_internal()

                self._state = STATE_CONNECTING
                self._last_error = ""
                self._notify("state_changed", {"message": f"Connecting to {profile.get('name')}..."})

                self._active_profile = profile
                settings = self.config_mgr.get_settings()
                settings["active_profile_id"] = profile["id"]
                self.config_mgr.save_settings(settings)

                tun_dev = settings.get("tun_device", "tun0")
                tun_ip = settings.get("tun_ip", "10.0.0.2/24")
                socks_host = settings.get("socks_host", "127.0.0.1")
                socks_port = int(settings.get("socks_port", 1080))
                dns_primary = settings.get("dns", "1.1.1.1")
                dns_backup = settings.get("dns_backup", "8.8.8.8")
                disable_ipv6_opt = bool(settings.get("disable_ipv6", True))

                # Step 1: Detect physical gateway & interface
                self._notify("stage_changed", {
                    "stage": "resolving",
                    "stage_index": 1,
                    "stage_total": 4,
                    "stage_label": "Resolving VPN Node",
                    "message": "Detecting physical network gateway...",
                    "node_id": "server"
                })
                gw, dev = self.network_mgr.get_physical_route(tun_name=tun_dev)

                # Step 2: Resolve server domain to IPv4
                server_host = profile["server"]
                self._notify("stage_changed", {
                    "stage": "resolving",
                    "stage_index": 1,
                    "stage_total": 4,
                    "stage_label": "Resolving VPN Node",
                    "message": f"Resolving server {server_host}...",
                    "node_id": "server"
                })
                server_ip = self.network_mgr.resolve_server_ip(server_host)

                # Step 3: Write active config for sslocal
                config_path = self.config_mgr.export_active_config(profile)

                # Snapshot IPv6 sysctl state before mutating network
                ipv6_prev_state = self.network_mgr.get_ipv6_state(physical_dev=dev) if disable_ipv6_opt else None

                connect_time = time.time()
                # Save session state before applying routes
                session_data = {
                    "profile_id": profile["id"],
                    "server_host": server_host,
                    "server_ip": server_ip,
                    "gateway_ip": gw,
                    "physical_dev": dev,
                    "tun_dev": tun_dev,
                    "socks_port": socks_port,
                    "dns_primary": dns_primary,
                    "dns_backup": dns_backup,
                    "ipv6_disabled": False,
                    "ipv6_prev_state": ipv6_prev_state,
                    "connected_at": connect_time,
                    "initial_rx": 0,
                    "initial_tx": 0
                }
                with open(SESSION_FILE, "w") as f:
                    json.dump(session_data, f, indent=2)

                # Step 4: Start sslocal (Stage 2: SOCKS5 Core)
                self._notify("stage_changed", {
                    "stage": "sslocal",
                    "stage_index": 2,
                    "stage_total": 4,
                    "stage_label": "Starting SOCKS5 Core",
                    "message": f"Starting Shadowsocks core daemon ({socks_host}:{socks_port})...",
                    "node_id": "sslocal"
                })
                self.process_mgr.start_sslocal(config_path, host=socks_host, port=socks_port)

                # Step 5: Setup TUN interface & start tun2socks (Stage 3: TUN & IPv6 Guard)
                self._notify("stage_changed", {
                    "stage": "tun0",
                    "stage_index": 3,
                    "stage_total": 4,
                    "stage_label": "Provisioning Virtual L3 tun0",
                    "message": f"Creating TUN interface {tun_dev} (10.0.0.2/24)...",
                    "node_id": "tun0"
                })
                self.network_mgr.setup_tun_interface(tun_name=tun_dev, tun_ip=tun_ip)

                self.process_mgr.start_tun2socks(
                    tun_device=tun_dev,
                    proxy_url=f"socks5://{socks_host}:{socks_port}"
                )

                # Step 6: Disable network IPv6 to prevent IPv6 leaks
                ipv6_disabled_ok = False
                if disable_ipv6_opt:
                    self._notify("stage_changed", {
                        "stage": "tun0",
                        "stage_index": 3,
                        "stage_total": 4,
                        "stage_label": "Arming IPv6 Leak Shield",
                        "message": "Disabling network IPv6 to prevent IPv6 leaks...",
                        "node_id": "tun0"
                    })
                    session_data["ipv6_disabled"] = True
                    with open(SESSION_FILE, "w") as f:
                        json.dump(session_data, f, indent=2)
                    ipv6_disabled_ok = self.network_mgr.disable_ipv6(
                        physical_dev=dev,
                        prev_state=ipv6_prev_state
                    )

                # Step 7: Apply routing & route pinning (Stage 4: Full-Tunnel Routing)
                self._notify("stage_changed", {
                    "stage": "routing",
                    "stage_index": 4,
                    "stage_total": 4,
                    "stage_label": "Securing Kernel Routes",
                    "message": "Routing system traffic through VPN...",
                    "node_id": "apps"
                })
                self.network_mgr.apply_routes(
                    server_ip=server_ip,
                    gateway_ip=gw,
                    physical_dev=dev,
                    tun_name=tun_dev
                )

                # Step 8: Configure DNS
                self.network_mgr.configure_dns(
                    tun_name=tun_dev,
                    primary_dns=dns_primary,
                    backup_dns=dns_backup
                )

                # Step 9: Start real stats monitor & persist session initial telemetry
                self.stats_monitor = StatsMonitor(interface=tun_dev)
                self.stats_monitor.start(start_time=connect_time)
                session_data["initial_rx"] = self.stats_monitor.initial_rx
                session_data["initial_tx"] = self.stats_monitor.initial_tx
                with open(SESSION_FILE, "w") as f:
                    json.dump(session_data, f, indent=2)

                self._state = STATE_CONNECTED
                self._notify("connected", {
                    "stage": "connected",
                    "stage_index": 4,
                    "stage_label": "Live Flow Active",
                    "message": "VPN Connected Successfully",
                    "profile": profile,
                    "server_ip": server_ip,
                    "tun_dev": tun_dev,
                    "gateway_ip": gw,
                    "physical_dev": dev,
                    "ipv6_disabled": ipv6_disabled_ok
                })
                return True

            except Exception as e:
                self._last_error = str(e)
                self._rollback_on_error()
                self._state = STATE_ERROR
                self._notify("error", {
                    "stage": "error",
                    "stage_index": -1,
                    "stage_label": "Connection Error",
                    "error": self._last_error,
                    "message": self._last_error
                })
                return False

    def _rollback_on_error(self):
        """Rollback all state and routing on failure."""
        try:
            self._teardown_internal()
        except Exception:
            pass

    def disconnect(self) -> bool:
        """Disconnect VPN and restore all network routes and DNS."""
        with self._lock:
            if self._state in (STATE_DISCONNECTED, STATE_DISCONNECTING):
                return True

            self._state = STATE_DISCONNECTING
            self._notify("stage_changed", {
                "stage": "teardown",
                "stage_index": 0,
                "stage_total": 4,
                "stage_label": "Restoring Kernel Routes & IPv6",
                "message": "Disconnecting VPN..."
            })
            self._notify("state_changed", {"message": "Disconnecting VPN..."})

            try:
                self._teardown_internal()
                self._state = STATE_DISCONNECTED
                self._notify("disconnected", {
                    "stage": "idle",
                    "stage_index": 0,
                    "stage_total": 4,
                    "stage_label": "Direct Physical Route",
                    "message": "VPN Disconnected"
                })
                return True

            except Exception as e:
                self._last_error = str(e)
                self._state = STATE_ERROR
                self._notify("error", {
                    "stage": "error",
                    "stage_index": -1,
                    "stage_label": "Disconnect Error",
                    "error": self._last_error,
                    "message": self._last_error
                })
                return False

    def set_dns(self, primary_dns: str, backup_dns: Optional[str] = "8.8.8.8", preset_name: Optional[str] = None) -> bool:
        """
        Updates DNS settings and applies them live if VPN is currently connected.
        """
        p_dns = primary_dns.strip()
        b_dns = (backup_dns or "").strip()

        settings = self.config_mgr.get_settings()
        settings["dns"] = p_dns
        settings["dns_backup"] = b_dns
        if preset_name:
            settings["dns_preset"] = preset_name
        self.config_mgr.save_settings(settings)

        if self._state == STATE_CONNECTED:
            tun_dev = settings.get("tun_device", "tun0")
            success = self.network_mgr.configure_dns(
                tun_name=tun_dev,
                primary_dns=p_dns,
                backup_dns=b_dns
            )
            if os.path.exists(SESSION_FILE):
                try:
                    with open(SESSION_FILE, "r") as f:
                        session_data = json.load(f)
                    session_data["dns_primary"] = p_dns
                    session_data["dns_backup"] = b_dns
                    with open(SESSION_FILE, "w") as f:
                        json.dump(session_data, f, indent=2)
                except Exception:
                    pass

            self._notify("dns_updated", {
                "message": f"Updated active DNS to {p_dns} ({preset_name or 'Custom'})",
                "primary_dns": p_dns,
                "backup_dns": b_dns,
                "preset": preset_name
            })
            return success
        else:
            self._notify("dns_updated", {
                "message": f"DNS resolver set to {preset_name or p_dns}",
                "primary_dns": p_dns,
                "backup_dns": b_dns,
                "preset": preset_name
            })
            return True

    def get_stats(self) -> Dict[str, Any]:
        return self.stats_monitor.get_stats()
