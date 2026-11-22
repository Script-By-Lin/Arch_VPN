#!/usr/bin/env python3
"""
Shadowsocks key validation & parser + country/flag helper for AuraLink Mobile Free Keys Backend.
"""

import base64
import json
import re
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


_METHOD_TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _b64_decode_flexible(data: str) -> str:
    s = data.strip().replace("-", "+").replace("_", "/")
    rem = len(s) % 4
    if rem != 0:
        s += "=" * (4 - rem)
    return base64.b64decode(s).decode("utf-8")


def _is_printable_text(text: str) -> bool:
    return bool(text) and all((32 <= ord(ch) <= 126) or ord(ch) >= 160 for ch in text)


def _parse_query_params(query_str: str) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if not query_str:
        return params
    for key, values in urllib.parse.parse_qs(query_str, keep_blank_values=True).items():
        if values:
            params[key] = values[0]
    return params


def _extract_ss_credentials(userinfo: str, params: Dict[str, str]) -> Tuple[str, str]:
    """
    Flexibly extracts (method, password) from an ss:// userinfo segment.
    Supports:
      1. Plaintext `method:password` (including SS2022 `method:k1:k2` and URL-encoded variants)
      2. Base64-encoded `method:password` (SIP002 standard & URL-safe, padded or unpadded)
      3. Bare password / UUID tokens without `method:` (e.g. OpenKeys.net `ss://<uuid>@host:port?encryption=none...`)
    """
    raw = userinfo.strip()
    if ":" in raw:
        raw_method, raw_pass = raw.split(":", 1)
        return urllib.parse.unquote(raw_method).strip(), urllib.parse.unquote(raw_pass)

    unquoted = urllib.parse.unquote(raw)
    if ":" in unquoted:
        method, password = unquoted.split(":", 1)
        return method.strip(), password

    # Attempt base64 decode ONLY when it produces printable `valid_method:nonempty_password`
    try:
        decoded = _b64_decode_flexible(raw)
        if ":" in decoded and _is_printable_text(decoded):
            cand_method, cand_pass = decoded.split(":", 1)
            if cand_method and cand_pass and _METHOD_TOKEN_RE.fullmatch(cand_method):
                return cand_method, cand_pass
    except Exception:
        pass

    # Bare UUID / token / password without method prefix
    method = (
        params.get("method")
        or params.get("cipher")
        or params.get("encryption")
        or "chacha20-ietf-poly1305"
    ).strip()
    return method or "chacha20-ietf-poly1305", unquoted


def _split_host_port(hostport: str, default_port: int = 8388) -> Tuple[str, int]:
    hostport = hostport.strip().split("?", 1)[0].strip().rstrip("/")
    if hostport.startswith("["):
        close_idx = hostport.find("]")
        if close_idx == -1:
            raise ValueError(f"Malformed IPv6 host: {hostport}")
        host = hostport[1:close_idx]
        rest = hostport[close_idx + 1 :]
        port_str = rest[1:].split("/")[0] if rest.startswith(":") else str(default_port)
        port = int(port_str) if port_str else default_port
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid server port: {port}")
        return host, port
    if ":" not in hostport:
        host = hostport.split("/")[0].strip()
        return host, default_port
    host, port_str = hostport.rsplit(":", 1)
    host = host.strip()
    port_str = port_str.split("/")[0].strip()
    port = int(port_str) if port_str else default_port
    if port <= 0 or port > 65535:
        raise ValueError(f"Invalid server port: {port}")
    return host, port


def _extract_plugin_fields(params: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    raw_plugin = (params.get("plugin") or "").strip()
    if not raw_plugin:
        return None, None
    if ";" in raw_plugin:
        name, opts = raw_plugin.split(";", 1)
        return name.strip() or None, opts.strip() or None
    return raw_plugin, None


def parse_free_key(raw_key: str) -> Dict[str, Any]:
    """
    Parses variable VPN key formats:
      - ss:// (SIP002 base64, legacy full-base64, plaintext method:pass, SS2022,
        and OpenKeys.net bare UUID/password + query params like encryption=none&type=ws)
      - vless:// and trojan:// URIs
      - vmess:// (base64 JSON or URI)
      - ssr:// (ShadowsocksR base64)
      - ssconf://, https://, http:// subscription links
      - Raw Shadowsocks JSON object
    Returns extracted fields: server, server_port, method, password, prefix, parsed_name, source_type.
    """
    s = (raw_key or "").strip()
    if not s:
        raise ValueError("Key cannot be empty.")

    # Normalize accidental line breaks in copied URIs (but preserve multiline JSON)
    if not s.startswith("{"):
        s = re.sub(r"[\r\n]+", "", s).strip()

    lower = s.lower()

    if lower.startswith("ss://"):
        body = s[5:].strip()
        parsed_name = ""
        if "#" in body:
            body, tag = body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()

        params: Dict[str, str] = {}
        if "?" in body:
            body, q = body.split("?", 1)
            params = _parse_query_params(q)

        if "@" in body:
            userinfo, hostport = body.rsplit("@", 1)
            method, password = _extract_ss_credentials(userinfo, params)
            server, port = _split_host_port(hostport, default_port=8388)
        else:
            try:
                decoded = _b64_decode_flexible(body)
            except Exception as e:
                raise ValueError("Invalid legacy base64 ss:// payload.") from e
            if "#" in decoded and not parsed_name:
                decoded, tag = decoded.split("#", 1)
                parsed_name = urllib.parse.unquote(tag).strip()
            if "?" in decoded:
                decoded, q2 = decoded.split("?", 1)
                params = {**_parse_query_params(q2), **params}
            if "@" not in decoded:
                raise ValueError("Invalid legacy base64 ss:// payload.")
            userinfo, hostport = decoded.rsplit("@", 1)
            method, password = _extract_ss_credentials(userinfo, params)
            server, port = _split_host_port(hostport, default_port=8388)

        if not server or not password:
            raise ValueError("ss:// key missing server or password.")

        plugin, plugin_opts = _extract_plugin_fields(params)
        prefix = params.get("prefix") or None

        return {
            "source_type": "ss",
            "server": server,
            "server_port": port,
            "method": method or "chacha20-ietf-poly1305",
            "password": password,
            "prefix": prefix,
            "plugin": plugin,
            "plugin_opts": plugin_opts,
            "params": params,
            "parsed_name": parsed_name,
        }

    if lower.startswith("vless://") or lower.startswith("trojan://"):
        scheme = "vless" if lower.startswith("vless://") else "trojan"
        body = s[len(scheme) + 3 :].strip()
        parsed_name = ""
        if "#" in body:
            body, tag = body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()

        params = {}
        if "?" in body:
            body, q = body.split("?", 1)
            params = _parse_query_params(q)

        if "@" not in body:
            raise ValueError(f"Invalid {scheme}:// URI: missing '@' credentials separator.")
        userinfo, hostport = body.rsplit("@", 1)
        password = urllib.parse.unquote(userinfo).strip()
        server, port = _split_host_port(hostport, default_port=443)
        if not server or not password:
            raise ValueError(f"{scheme}:// key missing server or credential.")

        method = (
            params.get("encryption")
            or params.get("method")
            or params.get("security")
            or scheme
        ).strip() or scheme

        return {
            "source_type": scheme,
            "server": server,
            "server_port": port,
            "method": method,
            "password": password,
            "prefix": params.get("prefix") or None,
            "params": params,
            "parsed_name": parsed_name,
        }

    if lower.startswith("vmess://"):
        body = s[8:].strip()
        parsed_name = ""
        if "#" in body:
            body, tag = body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()

        # Standard V2RayN base64 JSON format
        if "@" not in body:
            try:
                decoded = _b64_decode_flexible(body)
                obj = json.loads(decoded)
            except Exception as e:
                raise ValueError(f"Invalid vmess:// base64 JSON payload: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError("vmess:// payload must decode to a JSON object.")
            server = str(obj.get("add") or obj.get("server") or "").strip()
            password = str(obj.get("id") or obj.get("password") or "").strip()
            if not server or not password:
                raise ValueError("vmess:// key missing required 'add' (server) or 'id'.")
            port = int(obj.get("port") or 443)
            if port <= 0 or port > 65535:
                raise ValueError(f"Invalid server port: {port}")
            method = str(obj.get("scy") or obj.get("cipher") or "auto").strip() or "auto"
            remarks = str(obj.get("ps") or parsed_name).strip()
            return {
                "source_type": "vmess",
                "server": server,
                "server_port": port,
                "method": method,
                "password": password,
                "prefix": None,
                "params": {k: str(v) for k, v in obj.items() if v is not None},
                "parsed_name": remarks,
            }

        # Alternate URI form: vmess://uuid@host:port?params#tag
        params = {}
        if "?" in body:
            body, q = body.split("?", 1)
            params = _parse_query_params(q)
        userinfo, hostport = body.rsplit("@", 1)
        password = urllib.parse.unquote(userinfo).strip()
        server, port = _split_host_port(hostport, default_port=443)
        if not server or not password:
            raise ValueError("vmess:// key missing server or id.")
        method = (params.get("encryption") or params.get("cipher") or "auto").strip() or "auto"
        return {
            "source_type": "vmess",
            "server": server,
            "server_port": port,
            "method": method,
            "password": password,
            "prefix": None,
            "params": params,
            "parsed_name": parsed_name,
        }

    if lower.startswith("ssr://"):
        body = s[6:].strip()
        try:
            decoded = _b64_decode_flexible(body)
        except Exception as e:
            raise ValueError(f"Invalid ssr:// base64 payload: {e}") from e

        main_part = decoded
        params = {}
        if "/?" in decoded:
            main_part, q = decoded.split("/?", 1)
            params = _parse_query_params(q)
        elif "?" in decoded:
            main_part, q = decoded.split("?", 1)
            params = _parse_query_params(q)

        parts = main_part.split(":")
        if len(parts) < 6:
            raise ValueError("Invalid ssr:// payload structure.")
        server = parts[0].strip()
        port = int(parts[1])
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid server port: {port}")
        method = parts[3].strip() or "chacha20-ietf-poly1305"
        try:
            password = _b64_decode_flexible(parts[5])
        except Exception:
            password = parts[5]
        parsed_name = ""
        if params.get("remarks"):
            try:
                parsed_name = _b64_decode_flexible(params["remarks"]).strip()
            except Exception:
                parsed_name = params["remarks"].strip()
        if not server or not password:
            raise ValueError("ssr:// key missing server or password.")
        return {
            "source_type": "ssr",
            "server": server,
            "server_port": port,
            "method": method,
            "password": password,
            "prefix": None,
            "params": params,
            "parsed_name": parsed_name,
        }

    if lower.startswith("ssconf://") or lower.startswith("https://") or lower.startswith("http://"):
        url_body = s[len("ssconf://") :] if lower.startswith("ssconf://") else s
        parsed_name = ""
        if "#" in url_body:
            url_body, tag = url_body.split("#", 1)
            parsed_name = urllib.parse.unquote(tag).strip()
        if not url_body.lower().startswith(("http://", "https://")):
            url_body = "https://" + url_body
        parsed_url = urllib.parse.urlparse(url_body)
        if not parsed_url.netloc:
            raise ValueError("Invalid ssconf:// or subscription URL.")
        return {
            "source_type": "ssconf" if lower.startswith("ssconf://") else "url",
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
        server = str(obj.get("server") or obj.get("add") or "").strip()
        password = str(obj.get("password") or obj.get("id") or "")
        if not server or not password:
            raise ValueError("JSON config missing required 'server' or 'password'.")
        port = int(obj.get("server_port") or obj.get("port") or 443)
        if port <= 0 or port > 65535:
            raise ValueError(f"Invalid server_port: {port}")
        return {
            "source_type": "json",
            "server": server,
            "server_port": port,
            "method": str(obj.get("method") or obj.get("encryption") or obj.get("scy") or "chacha20-ietf-poly1305"),
            "password": password,
            "prefix": obj.get("prefix"),
            "parsed_name": str(obj.get("remarks") or obj.get("ps") or "").strip(),
        }

    raise ValueError(
        "Unsupported key format. Expected ss://, vless://, trojan://, vmess://, ssr://, ssconf://, https://, or JSON."
    )
