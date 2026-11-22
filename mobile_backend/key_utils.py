#!/usr/bin/env python3
"""
Shadowsocks key validation & parser + country/flag helper for AuraLink Mobile Free Keys Backend.
"""

import base64
import json
import urllib.parse
from typing import Any, Dict, Optional, Tuple


COUNTRY_FLAGS: Dict[str, Tuple[str, str]] = {
    "JP": ("🇯🇵", "Japan"),
    "SG": ("🇸🇬", "Singapore"),
    "US": ("🇺🇸", "United States"),
    "DE": ("🇩🇪", "Germany"),
    "GB": ("🇬🇧", "United Kingdom"),
    "NL": ("🇳🇱", "Netherlands"),
    "HK": ("🇭🇰", "Hong Kong"),
    "KR": ("🇰🇷", "South Korea"),
    "TW": ("🇹🇼", "Taiwan"),
    "CA": ("🇨🇦", "Canada"),
    "FR": ("🇫🇷", "France"),
    "AU": ("🇦🇺", "Australia"),
    "IN": ("🇮🇳", "India"),
    "TH": ("🇹🇭", "Thailand"),
    "MY": ("🇲🇾", "Malaysia"),
    "FI": ("🇫🇮", "Finland"),
    "SE": ("🇸🇪", "Sweden"),
    "CH": ("🇨🇭", "Switzerland"),
}


def country_code_to_flag(code: str) -> str:
    """Converts a 2-letter ISO country code (e.g. 'JP') to its flag emoji ('🇯🇵')."""
    c = (code or "").strip().upper()
    if c in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[c][0]
    if len(c) == 2 and c.isalpha():
        return "".join(chr(0x1F1E6 + ord(ch) - ord("A")) for ch in c)
    return "🌐"


def default_region_for_code(code: str) -> str:
    c = (code or "").strip().upper()
    if c in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[c][1]
    return c or "Global"


def _b64_decode_flexible(data: str) -> str:
    s = data.strip().replace("-", "+").replace("_", "/")
    rem = len(s) % 4
    if rem != 0:
        s += "=" * (4 - rem)
    return base64.b64decode(s).decode("utf-8")


def _split_host_port(hostport: str) -> Tuple[str, int]:
    hostport = hostport.strip().rstrip("/")
    if hostport.startswith("["):
        close_idx = hostport.find("]")
        if close_idx == -1:
            raise ValueError(f"Malformed IPv6 host: {hostport}")
        host = hostport[1:close_idx]
        rest = hostport[close_idx + 1 :]
        port = int(rest[1:]) if rest.startswith(":") else 8388
        return host, port
    if ":" not in hostport:
        return hostport, 8388
    host, port_str = hostport.rsplit(":", 1)
    port_str = port_str.split("/")[0].split("?")[0]
    port = int(port_str)
    if port <= 0 or port > 65535:
        raise ValueError(f"Invalid server port: {port}")
    return host, port


def parse_free_key(raw_key: str) -> Dict[str, Any]:
    """
    Parses ss:// (SIP002 or legacy base64), ssconf://, https://, or raw Shadowsocks JSON.
    Returns extracted fields: server, server_port, method, password, prefix, parsed_name, source_type.
    """
    s = (raw_key or "").strip()
    if not s:
        raise ValueError("Key cannot be empty.")

    if s.startswith("ss://"):
        body = s[5:]
        parsed_name = ""
        if "#" in body:
            body, tag = body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()

        prefix: Optional[str] = None
        if "?" in body:
            body, q = body.split("?", 1)
            params = urllib.parse.parse_qs(q)
            if "prefix" in params and params["prefix"]:
                prefix = params["prefix"][0]

        if "@" in body:
            userinfo, hostport = body.rsplit("@", 1)
            try:
                decoded_user = _b64_decode_flexible(userinfo)
            except Exception:
                decoded_user = urllib.parse.unquote(userinfo)
            if ":" not in decoded_user:
                raise ValueError("Invalid ss:// credentials format.")
            method, password = decoded_user.split(":", 1)
            server, port = _split_host_port(hostport)
        else:
            decoded = _b64_decode_flexible(body)
            if "@" not in decoded:
                raise ValueError("Invalid legacy base64 ss:// payload.")
            userinfo, hostport = decoded.rsplit("@", 1)
            if ":" not in userinfo:
                raise ValueError("Invalid legacy method:password format.")
            method, password = userinfo.split(":", 1)
            server, port = _split_host_port(hostport)

        if not server or not password:
            raise ValueError("ss:// key missing server or password.")

        return {
            "source_type": "ss",
            "server": server,
            "server_port": port,
            "method": method or "chacha20-ietf-poly1305",
            "password": password,
            "prefix": prefix,
            "parsed_name": parsed_name,
        }

    if s.startswith("ssconf://") or s.startswith("https://") or s.startswith("http://"):
        url_body = s[len("ssconf://") :] if s.startswith("ssconf://") else s
        parsed_name = ""
        if "#" in url_body:
            url_body, tag = url_body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()
        if not url_body.startswith(("http://", "https://")):
            url_body = "https://" + url_body
        parsed_url = urllib.parse.urlparse(url_body)
        if not parsed_url.netloc:
            raise ValueError("Invalid ssconf:// or subscription URL.")
        return {
            "source_type": "ssconf" if s.startswith("ssconf://") else "url",
            "server": parsed_url.hostname or parsed_url.netloc,
            "server_port": parsed_url.port or 443,
            "method": "ssconf-remote",
            "password": "",
            "prefix": None,
            "parsed_name": parsed_name,
        }

    if s.startswith("{"):
        try:
            obj = json.loads(s)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON key: {e}") from e
        if not isinstance(obj, dict):
            raise ValueError("JSON config must be an object.")
        server = str(obj.get("server", "")).strip()
        password = str(obj.get("password", ""))
        if not server or not password:
            raise ValueError("JSON config missing required 'server' or 'password'.")
        port = int(obj.get("server_port", 443))
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid server_port: {port}")
        return {
            "source_type": "json",
            "server": server,
            "server_port": port,
            "method": str(obj.get("method") or "chacha20-ietf-poly1305"),
            "password": password,
            "prefix": obj.get("prefix"),
            "parsed_name": str(obj.get("remarks", "")).strip(),
        }

    raise ValueError("Unsupported key format. Expected ss://, ssconf://, https://, or JSON.")
