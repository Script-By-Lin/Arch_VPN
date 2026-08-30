#!/usr/bin/env python3
"""
VPN Service Orchestrator for ShadowTun Linux VPN.
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

SESSION_FILE = os.path.expanduser("~/.config/shadowtun/state/session.json")


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
                    self.stats_monitor.start()
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
        """Internal teardown of network routes, DNS, processes, and session."""
        server_ip = None
        gw = None
        dev = None
        tun_dev = "tun0"

        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    session = json.load(f)
                server_ip = session.get("server_ip")
                gw = session.get("gateway_ip")
                dev = session.get("physical_dev")
                tun_dev = session.get("tun_dev", "tun0")
            except Exception:
                pass

        # 1. Teardown network routing & DNS
        self.network_mgr.teardown_network(
            server_ip=server_ip,
            gateway_ip=gw,
            physical_dev=dev,
            tun_name=tun_dev
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

                # Step 1: Detect physical gateway & interface
                self._notify("progress", {"message": "Detecting physical network gateway..."})
                gw, dev = self.network_mgr.get_physical_route(tun_name=tun_dev)

                # Step 2: Resolve server domain to IPv4
                server_host = profile["server"]
                self._notify("progress", {"message": f"Resolving server {server_host}..."})
                server_ip = self.network_mgr.resolve_server_ip(server_host)

                # Step 3: Write active config for sslocal
                config_path = self.config_mgr.export_active_config(profile)

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
                    "dns_backup": dns_backup
                }
                with open(SESSION_FILE, "w") as f:
                    json.dump(session_data, f, indent=2)

                # Step 4: Start sslocal
                self._notify("progress", {"message": "Starting Shadowsocks core..."})
                self.process_mgr.start_sslocal(config_path, host=socks_host, port=socks_port)

                # Step 5: Setup TUN interface
                self._notify("progress", {"message": f"Creating TUN interface {tun_dev}..."})
                self.network_mgr.setup_tun_interface(tun_name=tun_dev, tun_ip=tun_ip)

                # Step 6: Start tun2socks
                self._notify("progress", {"message": "Starting tun2socks engine..."})
                self.process_mgr.start_tun2socks(
                    tun_device=tun_dev,
                    proxy_url=f"socks5://{socks_host}:{socks_port}"
                )

                # Step 7: Apply routing & route pinning
                self._notify("progress", {"message": "Routing system traffic through VPN..."})
                self.network_mgr.apply_routes(
                    server_ip=server_ip,
                    gateway_ip=gw,
                    physical_dev=dev,
                    tun_name=tun_dev
                )

                # Step 8: Configure DNS
                self._notify("progress", {"message": "Configuring secure DNS..."})
                self.network_mgr.configure_dns(
                    tun_name=tun_dev,
                    primary_dns=dns_primary,
                    backup_dns=dns_backup
                )

                # Step 9: Start stats monitor
                self.stats_monitor = StatsMonitor(interface=tun_dev)
                self.stats_monitor.start()

                self._state = STATE_CONNECTED
                self._notify("connected", {
                    "message": "VPN Connected Successfully",
                    "profile": profile,
                    "server_ip": server_ip,
                    "tun_dev": tun_dev
                })
                return True

            except Exception as e:
                self._last_error = str(e)
                self._rollback_on_error()
                self._state = STATE_ERROR
                self._notify("error", {"error": self._last_error})
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
            self._notify("state_changed", {"message": "Disconnecting VPN..."})

            try:
                self._teardown_internal()
                self._state = STATE_DISCONNECTED
                self._notify("disconnected", {"message": "VPN Disconnected"})
                return True

            except Exception as e:
                self._last_error = str(e)
                self._state = STATE_ERROR
                self._notify("error", {"error": self._last_error})
                return False

    def get_stats(self) -> Dict[str, Any]:
        return self.stats_monitor.get_stats()
