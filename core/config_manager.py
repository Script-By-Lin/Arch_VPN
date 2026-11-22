#!/usr/bin/env python3
"""
Config Manager for AuraLink Linux VPN.
Handles parsing ssconf://, ss://, JSON configs, fetching remote subscription configs,
injecting local_address/local_port, and persistent profile management.
"""

import os
import re
import sys
import json
import uuid
import base64
import urllib.request
import urllib.parse
import ssl
import shutil
from typing import Dict, List, Optional, Tuple, Any

LEGACY_CONFIG_DIR = os.path.expanduser("~/.config/shadowtun")
CONFIG_DIR = os.path.expanduser("~/.config/auralink")

# Auto-migrate legacy configuration if present
if os.path.exists(LEGACY_CONFIG_DIR) and not os.path.exists(CONFIG_DIR):
    try:
        shutil.copytree(LEGACY_CONFIG_DIR, CONFIG_DIR)
    except Exception:
        pass

PROFILES_FILE = os.path.join(CONFIG_DIR, "profiles.json")
ACTIVE_CONFIG_FILE = os.path.join(CONFIG_DIR, "active_config.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


DNS_PRESETS = {
    "Cloudflare (1.1.1.1 / 1.0.0.1)": ("1.1.1.1", "1.0.0.1"),
    "Google (8.8.8.8 / 8.8.4.4)": ("8.8.8.8", "8.8.4.4"),
    "Quad9 (9.9.9.9 / 149.112.112.112)": ("9.9.9.9", "149.112.112.112"),
    "AdGuard (94.140.14.14 / 94.140.15.15)": ("94.140.14.14", "94.140.15.15")
}


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
                "dns_preset": "Cloudflare (1.1.1.1 / 1.0.0.1)",
                "socks_host": "127.0.0.1",
                "socks_port": 1080,
                "tun_device": "tun0",
                "tun_ip": "10.0.0.2/24",
                "disable_ipv6": True,
                "udp_relay": True,
                "verify_tunnel": True,
                "verify_timeout": 12.0,
                "auto_reconnect": True,
                "killswitch": True,
                "active_profile_id": None
            }
            self.save_settings(default_settings)

    def get_settings(self) -> Dict[str, Any]:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except Exception:
            data = {}

        defaults = {
            "dns": "1.1.1.1",
            "dns_backup": "8.8.8.8",
            "dns_preset": "Cloudflare (1.1.1.1 / 1.0.0.1)",
            "socks_host": "127.0.0.1",
            "socks_port": 1080,
            "tun_device": "tun0",
            "tun_ip": "10.0.0.2/24",
            "disable_ipv6": True,
            "udp_relay": True,
            "verify_tunnel": True,
            "verify_timeout": 12.0,
            "auto_reconnect": True,
            "killswitch": True,
            "active_profile_id": None
        }
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def save_settings(self, settings: Dict[str, Any]):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.get_settings().get(key, default)

    def set_setting(self, key: str, value: Any):
        settings = self.get_settings()
        settings[key] = value
        self.save_settings(settings)

    def get_active_profile_id(self) -> Optional[str]:
        return self.get_settings().get("active_profile_id")

    def set_active_profile(self, profile_id: Optional[str]):
        self.set_setting("active_profile_id", profile_id)

    def get_active_profile(self) -> Optional[Dict[str, Any]]:
        active_id = self.get_active_profile_id()
        if active_id:
            p = self.get_profile_by_id(active_id)
            if p:
                return p
        profiles = self.get_profiles()
        return profiles[0] if profiles else None

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
        target_id = profile_id.strip().lower()
        # 1. Exact match (case-insensitive)
        for p in self.get_profiles():
            if p.get("id", "").lower() == target_id:
                return p
        # 2. Prefix match (e.g. first 4-7 chars)
        for p in self.get_profiles():
            if p.get("id", "").lower().startswith(target_id):
                return p
        return None

    def get_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        target_name = name.strip().lower()
        # 1. Exact match (case-insensitive)
        for p in self.get_profiles():
            if p.get("name", "").lower() == target_name:
                return p
        # 2. Prefix or substring match
        for p in self.get_profiles():
            if target_name in p.get("name", "").lower():
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
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AuraLink/1.0",
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

    @staticmethod
    def _b64_decode_flexible(data: str) -> str:
        s = data.strip().replace("-", "+").replace("_", "/")
        rem = len(s) % 4
        if rem != 0:
            s += "=" * (4 - rem)
        return base64.b64decode(s).decode("utf-8")

    @staticmethod
    def _parse_query_params(query_str: str) -> Dict[str, str]:
        params: Dict[str, str] = {}
        if not query_str:
            return params
        for k, vals in urllib.parse.parse_qs(query_str, keep_blank_values=True).items():
            if vals:
                params[k] = vals[0]
        return params

    @staticmethod
    def _split_host_port(hostport: str, default_port: int = 8388) -> Tuple[str, int]:
        hp = hostport.strip().split("?", 1)[0].strip().rstrip("/")
        if hp.startswith("["):
            close_idx = hp.find("]")
            if close_idx == -1:
                raise ConfigError(f"Malformed IPv6 host: {hp}")
            host = hp[1:close_idx]
            rest = hp[close_idx + 1 :]
            port_str = rest[1:].split("/")[0] if rest.startswith(":") else str(default_port)
            port = int(port_str) if port_str else default_port
            if port <= 0 or port > 65535:
                raise ConfigError(f"Invalid server port: {port}")
            return host, port
        if ":" not in hp:
            return hp.split("/")[0].strip(), default_port
        host, port_str = hp.rsplit(":", 1)
        host = host.strip()
        port_str = port_str.split("/")[0].strip()
        port = int(port_str) if port_str else default_port
        if port <= 0 or port > 65535:
            raise ConfigError(f"Invalid server port: {port}")
        return host, port

    @classmethod
    def _extract_ss_credentials(cls, userinfo: str, params: Dict[str, str]) -> Tuple[str, str]:
        raw = userinfo.strip()
        if ":" in raw:
            raw_m, raw_p = raw.split(":", 1)
            return urllib.parse.unquote(raw_m).strip(), urllib.parse.unquote(raw_p)
        unquoted = urllib.parse.unquote(raw)
        if ":" in unquoted:
            m, p = unquoted.split(":", 1)
            return m.strip(), p
        try:
            decoded = cls._b64_decode_flexible(raw)
            if ":" in decoded and all((32 <= ord(ch) <= 126) or ord(ch) >= 160 for ch in decoded):
                cand_m, cand_p = decoded.split(":", 1)
                if cand_m and cand_p and re.fullmatch(r"[A-Za-z0-9._-]+", cand_m):
                    return cand_m, cand_p
        except Exception:
            pass
        method = (
            params.get("method")
            or params.get("cipher")
            or params.get("encryption")
            or "chacha20-ietf-poly1305"
        ).strip()
        return method or "chacha20-ietf-poly1305", unquoted

    def parse_key(self, raw_input: str) -> Dict[str, Any]:
        """
        Parses ssconf://, ss:// (SIP002, legacy base64, plaintext, SS2022, or bare UUID+query),
        vless://, trojan://, vmess://, ssr://, https://, raw JSON, or local file.
        Returns a profile dict.
        """
        raw_input = raw_input.strip()
        if not raw_input:
            raise ConfigError("Key / URL cannot be empty.")

        if not raw_input.startswith("{") and not os.path.exists(raw_input):
            raw_input = re.sub(r"[\r\n]+", "", raw_input).strip()

        settings = self.get_settings()
        local_addr = settings.get("socks_host", "127.0.0.1")
        local_port = int(settings.get("socks_port", 1080))

        profile_name = "Shadowsocks Server"
        config_data: Dict[str, Any] = {}
        uri_params: Dict[str, str] = {}
        source_type = "unknown"
        lower = raw_input.lower()

        # 1. ssconf:// schema
        if lower.startswith("ssconf://"):
            source_type = "ssconf"
            url_part = raw_input[len("ssconf://"):]
            if "#" in url_part:
                target_url, tag = url_part.split("#", 1)
                profile_name = urllib.parse.unquote(tag).strip()
            else:
                target_url = url_part
                profile_name = "AuraLink Server"

            if not target_url.lower().startswith(("http://", "https://")):
                target_url = "https://" + target_url

            config_data = self.fetch_url_json(target_url)

        # 2. http:// or https:// schema
        elif lower.startswith(("http://", "https://")):
            source_type = "url"
            url_part = raw_input
            if "#" in url_part:
                target_url, tag = url_part.split("#", 1)
                profile_name = urllib.parse.unquote(tag).strip()
            else:
                target_url = url_part
                profile_name = urllib.parse.urlparse(target_url).netloc

            config_data = self.fetch_url_json(target_url)

        # 3. Flexible ss:// URI schema (SIP002, legacy base64, plaintext, SS2022, bare UUID + query)
        elif lower.startswith("ss://"):
            source_type = "ss"
            uri_body = raw_input[5:].strip()
            if "#" in uri_body:
                main_part, tag = uri_body.split("#", 1)
                profile_name = urllib.parse.unquote(tag).strip() or profile_name
            else:
                main_part = uri_body

            if "?" in main_part:
                main_part, q = main_part.split("?", 1)
                uri_params = self._parse_query_params(q)

            if "@" in main_part:
                userinfo, hostport = main_part.rsplit("@", 1)
                method, password = self._extract_ss_credentials(userinfo, uri_params)
                server, server_port = self._split_host_port(hostport, default_port=8388)
            else:
                try:
                    decoded = self._b64_decode_flexible(main_part)
                except Exception as e:
                    raise ConfigError(f"Invalid legacy ss:// base64 payload: {e}") from e
                if "#" in decoded and profile_name == "Shadowsocks Server":
                    decoded, tag = decoded.split("#", 1)
                    profile_name = urllib.parse.unquote(tag).strip() or profile_name
                if "?" in decoded:
                    decoded, q2 = decoded.split("?", 1)
                    uri_params = {**self._parse_query_params(q2), **uri_params}
                if "@" not in decoded:
                    raise ConfigError("Invalid legacy ss:// base64 payload.")
                userinfo, hostport = decoded.rsplit("@", 1)
                method, password = self._extract_ss_credentials(userinfo, uri_params)
                server, server_port = self._split_host_port(hostport, default_port=8388)

            if profile_name == "Shadowsocks Server" and server:
                profile_name = server

            config_data = {
                "server": server,
                "server_port": server_port,
                "password": password,
                "method": method or "chacha20-ietf-poly1305",
            }
            if uri_params.get("prefix"):
                config_data["prefix"] = uri_params["prefix"]
            raw_plugin = (uri_params.get("plugin") or "").strip()
            if raw_plugin:
                if ";" in raw_plugin:
                    p_name, p_opts = raw_plugin.split(";", 1)
                    config_data["plugin"] = p_name.strip()
                    config_data["plugin_opts"] = p_opts.strip()
                else:
                    config_data["plugin"] = raw_plugin

        # 4. vless:// and trojan:// URI schemas
        elif lower.startswith(("vless://", "trojan://")):
            scheme = "vless" if lower.startswith("vless://") else "trojan"
            source_type = scheme
            uri_body = raw_input[len(scheme) + 3 :].strip()
            profile_name = "VLESS Server" if scheme == "vless" else "Trojan Server"
            if "#" in uri_body:
                main_part, tag = uri_body.split("#", 1)
                profile_name = urllib.parse.unquote(tag).strip() or profile_name
            else:
                main_part = uri_body
            if "?" in main_part:
                main_part, q = main_part.split("?", 1)
                uri_params = self._parse_query_params(q)
            if "@" not in main_part:
                raise ConfigError(f"Invalid {scheme}:// URI: missing credentials.")
            userinfo, hostport = main_part.rsplit("@", 1)
            password = urllib.parse.unquote(userinfo).strip()
            server, server_port = self._split_host_port(hostport, default_port=443)
            method = (
                uri_params.get("encryption")
                or uri_params.get("method")
                or uri_params.get("security")
                or scheme
            ).strip() or scheme
            if profile_name in ("VLESS Server", "Trojan Server") and server:
                profile_name = server
            config_data = {
                "server": server,
                "server_port": server_port,
                "password": password,
                "method": method,
            }

        # 5. vmess:// URI schema
        elif lower.startswith("vmess://"):
            source_type = "vmess"
            uri_body = raw_input[8:].strip()
            profile_name = "VMess Server"
            if "#" in uri_body:
                uri_body, tag = uri_body.split("#", 1)
                profile_name = urllib.parse.unquote(tag).strip() or profile_name
            if "@" not in uri_body:
                try:
                    obj = json.loads(self._b64_decode_flexible(uri_body))
                except Exception as e:
                    raise ConfigError(f"Invalid vmess:// base64 JSON payload: {e}") from e
                server = str(obj.get("add") or obj.get("server") or "").strip()
                password = str(obj.get("id") or obj.get("password") or "").strip()
                server_port = int(obj.get("port") or 443)
                method = str(obj.get("scy") or obj.get("cipher") or "auto").strip() or "auto"
                profile_name = str(obj.get("ps") or profile_name).strip() or server
                uri_params = {k: str(v) for k, v in obj.items() if v is not None}
            else:
                if "?" in uri_body:
                    uri_body, q = uri_body.split("?", 1)
                    uri_params = self._parse_query_params(q)
                userinfo, hostport = uri_body.rsplit("@", 1)
                password = urllib.parse.unquote(userinfo).strip()
                server, server_port = self._split_host_port(hostport, default_port=443)
                method = (uri_params.get("encryption") or uri_params.get("cipher") or "auto").strip() or "auto"
                if profile_name == "VMess Server" and server:
                    profile_name = server
            config_data = {
                "server": server,
                "server_port": server_port,
                "password": password,
                "method": method,
            }

        # 6. ssr:// URI schema
        elif lower.startswith("ssr://"):
            source_type = "ssr"
            try:
                decoded = self._b64_decode_flexible(raw_input[6:].strip())
            except Exception as e:
                raise ConfigError(f"Invalid ssr:// base64 payload: {e}") from e
            main_part = decoded
            if "/?" in decoded:
                main_part, q = decoded.split("/?", 1)
                uri_params = self._parse_query_params(q)
            elif "?" in decoded:
                main_part, q = decoded.split("?", 1)
                uri_params = self._parse_query_params(q)
            parts = main_part.split(":")
            if len(parts) < 6:
                raise ConfigError("Invalid ssr:// payload structure.")
            server = parts[0].strip()
            server_port = int(parts[1])
            method = parts[3].strip() or "chacha20-ietf-poly1305"
            try:
                password = self._b64_decode_flexible(parts[5])
            except Exception:
                password = parts[5]
            profile_name = server
            if uri_params.get("remarks"):
                try:
                    profile_name = self._b64_decode_flexible(uri_params["remarks"]).strip() or server
                except Exception:
                    profile_name = uri_params["remarks"].strip() or server
            config_data = {
                "server": server,
                "server_port": server_port,
                "password": password,
                "method": method,
            }

        # 7. JSON string or file path
        elif raw_input.startswith("{") or os.path.exists(raw_input):
            source_type = "json"
            if os.path.exists(raw_input):
                with open(raw_input, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            else:
                config_data = json.loads(raw_input)
            profile_name = config_data.get(
                "remarks",
                config_data.get("ps", config_data.get("server", config_data.get("add", "Custom JSON Server"))),
            )
            if "server" not in config_data and "add" in config_data:
                config_data["server"] = config_data["add"]
            if "password" not in config_data and "id" in config_data:
                config_data["password"] = config_data["id"]
            if "server_port" not in config_data and "port" in config_data:
                config_data["server_port"] = config_data["port"]
        else:
            raise ConfigError(
                "Unrecognized format. Expected ss://, vless://, trojan://, vmess://, ssr://, ssconf://, https://, or JSON."
            )

        # Validate config_data
        if not isinstance(config_data, dict):
            raise ConfigError("Invalid configuration structure received.")

        if not config_data.get("server") or not config_data.get("password"):
            raise ConfigError("VPN configuration missing required fields (server, password).")

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
            "params": uri_params,
            "config": config_data,
        }

        return profile

    def export_active_config(self, profile: Dict[str, Any]) -> str:
        """Write active Shadowsocks JSON config file to disk for sslocal."""
        config_data = dict(profile.get("config", {}))
        settings = self.get_settings()
        config_data["local_address"] = settings.get("socks_host", "127.0.0.1")
        config_data["local_port"] = int(settings.get("socks_port", 1080))

        # Enable TCP+UDP relay so UDP DNS (port 53) and QUIC/HTTP3 work immediately
        # without waiting 5-10s for systemd-resolved UDP->TCP fallback timeouts.
        if settings.get("udp_relay", True) and "mode" not in config_data:
            config_data["mode"] = "tcp_and_udp"

        # Enable TCP_NODELAY for snappier TLS/DNS handshakes
        if "no_delay" not in config_data:
            config_data["no_delay"] = True

        with open(ACTIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        return ACTIVE_CONFIG_FILE
