#!/usr/bin/env python3
"""
Config Manager for ShadowTun Linux VPN.
Handles parsing ssconf://, ss://, JSON configs, fetching remote subscription configs,
injecting local_address/local_port, and persistent profile management.
"""

import os
import sys
import json
import uuid
import base64
import urllib.request
import urllib.parse
import ssl
from typing import Dict, List, Optional, Tuple, Any

CONFIG_DIR = os.path.expanduser("~/.config/shadowtun")
PROFILES_FILE = os.path.join(CONFIG_DIR, "profiles.json")
ACTIVE_CONFIG_FILE = os.path.join(CONFIG_DIR, "active_config.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


class ConfigError(Exception):
    """Custom exception for configuration or fetching errors."""
    pass


class ConfigManager:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(PROFILES_FILE):
            self.save_profiles([])
        if not os.path.exists(SETTINGS_FILE):
            default_settings = {
                "dns": "1.1.1.1",
                "dns_backup": "8.8.8.8",
                "socks_host": "127.0.0.1",
                "socks_port": 1080,
                "tun_device": "tun0",
                "tun_ip": "10.0.0.2/24",
                "auto_reconnect": True,
                "killswitch": True,
                "active_profile_id": None
            }
            self.save_settings(default_settings)

    def get_settings(self) -> Dict[str, Any]:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "dns": "1.1.1.1",
                "dns_backup": "8.8.8.8",
                "socks_host": "127.0.0.1",
                "socks_port": 1080,
                "tun_device": "tun0",
                "tun_ip": "10.0.0.2/24",
                "auto_reconnect": True,
                "killswitch": True,
                "active_profile_id": None
            }

    def save_settings(self, settings: Dict[str, Any]):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def get_profiles(self) -> List[Dict[str, Any]]:
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_profiles(self, profiles: List[Dict[str, Any]]):
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)

    def get_profile_by_id(self, profile_id: str) -> Optional[Dict[str, Any]]:
        for p in self.get_profiles():
            if p.get("id") == profile_id:
                return p
        return None

    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for p in self.get_profiles():
            if p.get("name", "").lower() == name.lower():
                return p
        return None

    def add_or_update_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        profiles = self.get_profiles()
        if "id" not in profile or not profile["id"]:
            profile["id"] = str(uuid.uuid4())[:8]
        
        # Check if already exists by id or url
        existing_idx = None
        for i, p in enumerate(profiles):
            if p.get("id") == profile["id"] or (profile.get("raw_key") and p.get("raw_key") == profile.get("raw_key")):
                existing_idx = i
                break
        
        if existing_idx is not None:
            profiles[existing_idx] = profile
        else:
            profiles.append(profile)
        
        self.save_profiles(profiles)
        return profile

    def delete_profile(self, profile_id: str) -> bool:
        profiles = self.get_profiles()
        new_profiles = [p for p in profiles if p.get("id") != profile_id]
        if len(new_profiles) != len(profiles):
            self.save_profiles(new_profiles)
            settings = self.get_settings()
            if settings.get("active_profile_id") == profile_id:
                settings["active_profile_id"] = None
                self.save_settings(settings)
            return True
        return False

    def fetch_url_json(self, url: str) -> Dict[str, Any]:
        """Fetch remote JSON config with proper user-agent and SSL fallback."""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ShadowTun/1.0",
            "Accept": "application/json, text/plain, */*"
        }
        req = urllib.request.Request(url, headers=headers)
        
        # Attempt with default SSL context, fallback to unverified if self-signed/proxy cert
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                content = response.read().decode("utf-8")
        except Exception as e1:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, context=ctx, timeout=12) as response:
                    content = response.read().decode("utf-8")
            except Exception as e2:
                raise ConfigError(f"Failed to fetch config from {url}: {e2}")

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise ConfigError(f"Server response is not valid JSON:\n{content[:200]}")

        # Check if server returned an error payload
        if isinstance(data, dict):
            if "error" in data:
                err = data["error"]
                if isinstance(err, dict) and "message" in err:
                    msg = err["message"]
                    details = err.get("details", "")
                    raise ConfigError(f"Subscription Error: {msg}\n{details}".strip())
                else:
                    raise ConfigError(f"Subscription Error: {err}")

        return data

    def parse_key(self, raw_input: str) -> Dict[str, Any]:
        """
        Parses ssconf://, ss://, https://, raw JSON, or local file.
        Returns a profile dict:
        {
            "id": "...",
            "name": "...",
            "raw_key": "...",
            "source_type": "ssconf" | "ss" | "json" | "url",
            "config": { ... shadowsocks json with local_address/port ... },
            "server": "...",
            "server_port": 443,
            "method": "...",
            "password": "..."
        }
        """
        raw_input = raw_input.strip()
        if not raw_input:
            raise ConfigError("Key / URL cannot be empty.")

        settings = self.get_settings()
        local_addr = settings.get("socks_host", "127.0.0.1")
        local_port = int(settings.get("socks_port", 1080))

        profile_name = "Shadowsocks Server"
        config_data = {}
        source_type = "unknown"

        # 1. ssconf:// schema
        if raw_input.startswith("ssconf://"):
            source_type = "ssconf"
            # Remove ssconf://
            url_part = raw_input[len("ssconf://"):]
            
            # Extract profile name from # anchor if present
            if "#" in url_part:
                target_url, tag = url_part.split("#", 1)
                profile_name = urllib.parse.unquote(tag)
            else:
                target_url = url_part
                profile_name = "ShadowTun Server"

            # Prepend https:// if not present
            if not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = "https://" + target_url

            config_data = self.fetch_url_json(target_url)

        # 2. http:// or https:// schema
        elif raw_input.startswith("http://") or raw_input.startswith("https://"):
            source_type = "url"
            url_part = raw_input
            if "#" in url_part:
                target_url, tag = url_part.split("#", 1)
                profile_name = urllib.parse.unquote(tag)
            else:
                target_url = url_part
                profile_name = urllib.parse.urlparse(target_url).netloc

            config_data = self.fetch_url_json(target_url)

        # 3. Standard ss:// URI schema (SIP002)
        elif raw_input.startswith("ss://"):
            source_type = "ss"
            uri_body = raw_input[5:]
            if "#" in uri_body:
                main_part, tag = uri_body.split("#", 1)
                profile_name = urllib.parse.unquote(tag)
            else:
                main_part = uri_body

            # Handle base64 encoded userinfo vs unencoded
            if "@" in main_part:
                userinfo, hostport = main_part.split("@", 1)
                try:
                    padding = 4 - (len(userinfo) % 4)
                    if padding != 4:
                        userinfo += "=" * padding
                    decoded_userinfo = base64.urlsafe_b64decode(userinfo).decode("utf-8")
                    method, password = decoded_userinfo.split(":", 1)
                except Exception:
                    method, password = userinfo.split(":", 1)

                if ":" in hostport:
                    server, port_str = hostport.split(":", 1)
                    server_port = int(port_str.split("/")[0].split("?")[0])
                else:
                    server = hostport
                    server_port = 8388
            else:
                padding = 4 - (len(main_part) % 4)
                if padding != 4:
                    main_part += "=" * padding
                decoded = base64.urlsafe_b64decode(main_part).decode("utf-8")
                userinfo, hostport = decoded.split("@", 1)
                method, password = userinfo.split(":", 1)
                server, port_str = hostport.split(":", 1)
                server_port = int(port_str.split("/")[0].split("?")[0])

            config_data = {
                "server": server,
                "server_port": server_port,
                "password": password,
                "method": method
            }

        # 4. JSON string or file path
        elif raw_input.startswith("{") or os.path.exists(raw_input):
            source_type = "json"
            if os.path.exists(raw_input):
                with open(raw_input, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                config_data = json.loads(raw_input)
            profile_name = config_data.get("remarks", config_data.get("server", "Custom JSON Server"))
        else:
            raise ConfigError(f"Unrecognized format. Expected ssconf://..., ss://..., https://..., or JSON.")

        # Validate config_data
        if not isinstance(config_data, dict):
            raise ConfigError("Invalid configuration structure received.")

        if "server" not in config_data or "password" not in config_data:
            raise ConfigError("Shadowsocks configuration missing required fields (server, password).")

        # Inject local_address and local_port
        config_data["local_address"] = local_addr
        config_data["local_port"] = local_port

        profile = {
            "id": str(uuid.uuid4())[:8],
            "name": profile_name,
            "raw_key": raw_input,
            "source_type": source_type,
            "server": config_data["server"],
            "server_port": int(config_data.get("server_port", 443)),
            "method": config_data.get("method", "chacha20-ietf-poly1305"),
            "prefix": config_data.get("prefix", None),
            "config": config_data
        }

        return profile

    def export_active_config(self, profile: Dict[str, Any]) -> str:
        """Write active Shadowsocks JSON config file to disk for sslocal."""
        config_data = dict(profile.get("config", {}))
        settings = self.get_settings()
        config_data["local_address"] = settings.get("socks_host", "127.0.0.1")
        config_data["local_port"] = int(settings.get("socks_port", 1080))
        
        with open(ACTIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
            
        return ACTIVE_CONFIG_FILE
