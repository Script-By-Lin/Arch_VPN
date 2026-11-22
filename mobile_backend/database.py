#!/usr/bin/env python3
"""
SQLite persistence layer for AuraLink Mobile Free Keys Admin Backend.
Stores region-tagged free VPN keys published exclusively for the Flutter mobile app.
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def resolve_data_dir() -> str:
    """
    Resolves persistent data directory in priority order:
    1. AURALINK_DATA_DIR (explicit override)
    2. RAILWAY_VOLUME_MOUNT_PATH (automatically set when a Railway Volume is attached)
    3. /data (if pre-mounted inside Docker)
    4. mobile_backend/data (local dev fallback)
    """
    for env_key in ("AURALINK_DATA_DIR", "RAILWAY_VOLUME_MOUNT_PATH"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val
    if os.path.isdir("/data") and os.access("/data", os.W_OK):
        return "/data"
    return os.path.join(os.path.dirname(__file__), "data")


DEFAULT_DB_PATH = os.path.join(resolve_data_dir(), "free_keys.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FreeKeysDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = (
            db_path
            or os.environ.get("AURALINK_DB_PATH")
            or os.path.join(resolve_data_dir(), "free_keys.db")
        )
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS free_keys (
                    id TEXT PRIMARY KEY,
                    region TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    flag TEXT NOT NULL,
                    city TEXT NOT NULL DEFAULT '',
                    label TEXT NOT NULL,
                    raw_key TEXT NOT NULL,
                    source_type TEXT NOT NULL DEFAULT 'ss',
                    server TEXT NOT NULL,
                    server_port INTEGER NOT NULL,
                    method TEXT NOT NULL,
                    password TEXT NOT NULL DEFAULT '',
                    prefix TEXT,
                    tier TEXT NOT NULL DEFAULT 'FREE',
                    is_published INTEGER NOT NULL DEFAULT 1,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_free_keys_published ON free_keys (is_published, sort_order, region)"
            )
            conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "region": row["region"],
            "country_code": row["country_code"],
            "flag": row["flag"],
            "city": row["city"],
            "label": row["label"],
            "raw_key": row["raw_key"],
            "source_type": row["source_type"],
            "server": row["server"],
            "server_port": row["server_port"],
            "method": row["method"],
            "password": row["password"],
            "prefix": row["prefix"],
            "tier": row["tier"],
            "is_published": bool(row["is_published"]),
            "sort_order": row["sort_order"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_keys(
        self,
        published_only: bool = False,
        region: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if published_only:
            clauses.append("is_published = 1")
        if region:
            clauses.append("LOWER(region) = LOWER(?)")
            params.append(region.strip())
        if country_code:
            clauses.append("UPPER(country_code) = UPPER(?)")
            params.append(country_code.strip())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT * FROM free_keys
            {where_sql}
            ORDER BY sort_order ASC, region ASC, created_at DESC
        """
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM free_keys WHERE id = ?", (key_id,)).fetchone()
            return self._row_to_dict(row) if row else None

    def create_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = _utc_now()
        key_id = uuid.uuid4().hex[:10]
        record = {
            "id": key_id,
            "region": data["region"],
            "country_code": data["country_code"].upper(),
            "flag": data["flag"],
            "city": data.get("city", ""),
            "label": data["label"],
            "raw_key": data["raw_key"],
            "source_type": data.get("source_type", "ss"),
            "server": data["server"],
            "server_port": int(data["server_port"]),
            "method": data["method"],
            "password": data.get("password", ""),
            "prefix": data.get("prefix"),
            "tier": "FREE",
            "is_published": 1 if data.get("is_published", True) else 0,
            "sort_order": int(data.get("sort_order", 0)),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO free_keys (
                    id, region, country_code, flag, city, label, raw_key, source_type,
                    server, server_port, method, password, prefix, tier,
                    is_published, sort_order, created_at, updated_at
                ) VALUES (
                    :id, :region, :country_code, :flag, :city, :label, :raw_key, :source_type,
                    :server, :server_port, :method, :password, :prefix, :tier,
                    :is_published, :sort_order, :created_at, :updated_at
                )
                """,
                record,
            )
            conn.commit()
        return self.get_key(key_id)  # type: ignore[return-value]

    def update_key(self, key_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_key(key_id)
        if not existing:
            return None

        allowed = {
            "region",
            "country_code",
            "flag",
            "city",
            "label",
            "raw_key",
            "source_type",
            "server",
            "server_port",
            "method",
            "password",
            "prefix",
            "is_published",
            "sort_order",
        }
        set_parts = []
        params: List[Any] = []
        for k, v in updates.items():
            if k not in allowed:
                continue
            if k == "is_published":
                v = 1 if v else 0
            elif k == "country_code" and isinstance(v, str):
                v = v.upper()
            set_parts.append(f"{k} = ?")
            params.append(v)

        if not set_parts:
            return existing

        set_parts.append("updated_at = ?")
        params.append(_utc_now())
        params.append(key_id)

        with self._connect() as conn:
            conn.execute(f"UPDATE free_keys SET {', '.join(set_parts)} WHERE id = ?", params)
            conn.commit()
        return self.get_key(key_id)

    def delete_key(self, key_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM free_keys WHERE id = ?", (key_id,))
            conn.commit()
            return cur.rowcount > 0
