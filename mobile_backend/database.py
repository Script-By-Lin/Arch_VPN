#!/usr/bin/env python3
"""
Dual-engine persistence layer (PostgreSQL + SQLite) for AuraLink Mobile Free Keys Admin Backend.

- Automatically connects to PostgreSQL when a database URL is provided via constructor or env vars:
  `AURALINK_DATABASE_URL`, `DATABASE_URL`, `POSTGRES_URL`, `POSTGRESQL_URL`,
  `DATABASE_PRIVATE_URL`, or `DATABASE_PUBLIC_URL`.
- Automatically falls back to SQLite (`free_keys.db`) when no PostgreSQL URL is set
  (or when an explicit local SQLite file path is passed via `db_path`).
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import os
import sqlite3
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple
import urllib.parse
import uuid


POSTGRES_ENV_VARS: Tuple[str, ...] = (
    "AURALINK_DATABASE_URL",
    "DATABASE_URL",
    "POSTGRES_URL",
    "POSTGRESQL_URL",
    "DATABASE_PRIVATE_URL",
    "DATABASE_PUBLIC_URL",
)


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


def is_postgres_url(value: Optional[str]) -> bool:
    if not value:
        return False
    lower = value.strip().lower()
    return lower.startswith(("postgresql://", "postgres://", "postgresql+psycopg://", "postgresql+psycopg2://"))


def normalize_postgres_url(url: str) -> str:
    """Normalizes postgres:// and SQLAlchemy-style prefixes to standard libpq postgresql://."""
    cleaned = url.strip()
    lower = cleaned.lower()
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgres://"):
        if lower.startswith(prefix):
            return "postgresql://" + cleaned[len(prefix) :]
    return cleaned


def redact_database_url(url: str) -> str:
    """Redacts password in a PostgreSQL URL for safe logging."""
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = f":{parsed.port}" if parsed.port else ""
        dbname = parsed.path or ""
        user = f"{parsed.username}:***@" if parsed.username else ""
        return f"{parsed.scheme}://{user}{host}{port}{dbname}"
    except Exception:
        return "postgresql://***"


def resolve_database_url(
    database_url: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[str]:
    """
    Determines whether to use PostgreSQL and returns the normalized URL, or None for SQLite.
    If a non-URL `db_path` (e.g. a temp SQLite file in tests) is explicitly provided and
    `database_url` is not passed, SQLite is used so unit tests stay isolated.
    """
    if database_url and is_postgres_url(database_url):
        return normalize_postgres_url(database_url)
    if db_path:
        if is_postgres_url(db_path):
            return normalize_postgres_url(db_path)
        return None
    for env_key in POSTGRES_ENV_VARS:
        val = os.environ.get(env_key, "").strip()
        if is_postgres_url(val):
            return normalize_postgres_url(val)
    return None


DEFAULT_DB_PATH = os.path.join(resolve_data_dir(), "free_keys.db")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_postgres_driver() -> Tuple[str, Any]:
    """Loads psycopg (v3) first, falling back to psycopg2 if installed."""
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore

        return "psycopg3", (psycopg, dict_row)
    except ImportError:
        pass
    try:
        import psycopg2  # type: ignore
        from psycopg2.extras import RealDictCursor  # type: ignore

        return "psycopg2", (psycopg2, RealDictCursor)
    except ImportError as e:
        raise RuntimeError(
            "PostgreSQL DATABASE_URL detected, but no PostgreSQL driver is installed. "
            "Install `psycopg[binary]` (included in mobile_backend/requirements.txt)."
        ) from e


class FreeKeysDB:
    def __init__(
        self,
        db_path: Optional[str] = None,
        database_url: Optional[str] = None,
        pg_connect_retries: int = 5,
    ):
        pg_url = resolve_database_url(database_url=database_url, db_path=db_path)
        if pg_url:
            self.backend_type = "postgresql"
            self.database_url: Optional[str] = pg_url
            self.db_path = pg_url
            self.display_target = redact_database_url(pg_url)
            self._ph = "%s"
            self._pg_driver_name, self._pg_driver = _load_postgres_driver()
            self._init_schema_with_retry(retries=pg_connect_retries)
        else:
            self.backend_type = "sqlite"
            self.database_url = None
            self.db_path = (
                db_path
                or os.environ.get("AURALINK_DB_PATH")
                or os.path.join(resolve_data_dir(), "free_keys.db")
            )
            self.display_target = self.db_path
            self._ph = "?"
            self._pg_driver_name = ""
            self._pg_driver = None
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            self._init_schema()

    @property
    def releases_dir(self) -> str:
        """Directory used to persist directly uploaded Android .apk binaries."""
        if self.backend_type == "sqlite":
            return os.path.join(os.path.dirname(os.path.abspath(self.db_path)), "releases")
        return os.path.join(resolve_data_dir(), "releases")

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        if self.backend_type == "postgresql":
            if self._pg_driver_name == "psycopg3":
                psycopg_mod, dict_row = self._pg_driver
                conn = psycopg_mod.connect(
                    self.database_url,
                    row_factory=dict_row,
                    connect_timeout=10,
                )
            else:
                psycopg2_mod, _ = self._pg_driver
                conn = psycopg2_mod.connect(
                    self.database_url,
                    connect_timeout=10,
                )
            try:
                yield conn
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise
            finally:
                conn.close()

    def _execute(self, conn: Any, sql: str, params: Tuple[Any, ...] = ()) -> Any:
        if self.backend_type == "postgresql":
            if self._pg_driver_name == "psycopg2":
                _, real_dict_cursor = self._pg_driver
                cur = conn.cursor(cursor_factory=real_dict_cursor)
            else:
                cur = conn.cursor()
            cur.execute(sql, params)
            return cur
        return conn.execute(sql, params)

    def _init_schema_with_retry(self, retries: int = 5):
        last_err: Optional[Exception] = None
        for attempt in range(max(1, retries)):
            try:
                self._init_schema()
                return
            except Exception as e:
                last_err = e
                if attempt + 1 < retries:
                    time.sleep(min(2.0, 0.5 * (attempt + 1)))
        if last_err is not None:
            raise last_err

    def _init_schema(self):
        size_col_type = "BIGINT" if self.backend_type == "postgresql" else "INTEGER"
        with self._connection() as conn:
            self._execute(
                conn,
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
                """,
            )
            self._execute(
                conn,
                "CREATE INDEX IF NOT EXISTS idx_free_keys_published ON free_keys (is_published, sort_order, region)",
            )
            self._execute(
                conn,
                f"""
                CREATE TABLE IF NOT EXISTS mobile_release (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL DEFAULT 'android',
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    download_url TEXT NOT NULL DEFAULT '',
                    local_file_path TEXT NOT NULL DEFAULT '',
                    filename TEXT NOT NULL DEFAULT 'AuraLink-VPN-Android.apk',
                    size_bytes {size_col_type} NOT NULL DEFAULT 0,
                    sha256 TEXT NOT NULL DEFAULT '',
                    release_notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """,
            )

    @staticmethod
    def _row_to_dict(row: Any) -> Dict[str, Any]:
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
            "server_port": int(row["server_port"]),
            "method": row["method"],
            "password": row["password"],
            "prefix": row["prefix"],
            "tier": row["tier"],
            "is_published": bool(row["is_published"]),
            "sort_order": int(row["sort_order"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_keys(
        self,
        published_only: bool = False,
        region: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        ph = self._ph
        clauses = []
        params: List[Any] = []
        if published_only:
            clauses.append("is_published = 1")
        if region:
            clauses.append(f"LOWER(region) = LOWER({ph})")
            params.append(region.strip())
        if country_code:
            clauses.append(f"UPPER(country_code) = UPPER({ph})")
            params.append(country_code.strip())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT * FROM free_keys
            {where_sql}
            ORDER BY sort_order ASC, region ASC, created_at DESC
        """
        with self._connection() as conn:
            cur = self._execute(conn, sql, tuple(params))
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        ph = self._ph
        with self._connection() as conn:
            cur = self._execute(conn, f"SELECT * FROM free_keys WHERE id = {ph}", (key_id,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None

    def create_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ph = self._ph
        now = _utc_now()
        key_id = uuid.uuid4().hex[:10]
        values = (
            key_id,
            data["region"],
            data["country_code"].upper(),
            data["flag"],
            data.get("city", ""),
            data["label"],
            data["raw_key"],
            data.get("source_type", "ss"),
            data["server"],
            int(data["server_port"]),
            data["method"],
            data.get("password", ""),
            data.get("prefix"),
            "FREE",
            1 if data.get("is_published", True) else 0,
            int(data.get("sort_order", 0)),
            now,
            now,
        )
        placeholders = ", ".join([ph] * len(values))
        with self._connection() as conn:
            self._execute(
                conn,
                f"""
                INSERT INTO free_keys (
                    id, region, country_code, flag, city, label, raw_key, source_type,
                    server, server_port, method, password, prefix, tier,
                    is_published, sort_order, created_at, updated_at
                ) VALUES ({placeholders})
                """,
                values,
            )
        return self.get_key(key_id)  # type: ignore[return-value]

    def update_key(self, key_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_key(key_id)
        if not existing:
            return None

        ph = self._ph
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
            set_parts.append(f"{k} = {ph}")
            params.append(v)

        if not set_parts:
            return existing

        set_parts.append(f"updated_at = {ph}")
        params.append(_utc_now())
        params.append(key_id)

        with self._connection() as conn:
            self._execute(
                conn,
                f"UPDATE free_keys SET {', '.join(set_parts)} WHERE id = {ph}",
                tuple(params),
            )
        return self.get_key(key_id)

    def delete_key(self, key_id: str) -> bool:
        ph = self._ph
        with self._connection() as conn:
            cur = self._execute(conn, f"DELETE FROM free_keys WHERE id = {ph}", (key_id,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Mobile APK Release Metadata
    # ------------------------------------------------------------------
    def get_mobile_release(self, platform: str = "android") -> Optional[Dict[str, Any]]:
        ph = self._ph
        with self._connection() as conn:
            cur = self._execute(
                conn, f"SELECT * FROM mobile_release WHERE id = {ph}", (platform,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "platform": row["platform"],
                "version": row["version"],
                "download_url": row["download_url"],
                "local_file_path": row["local_file_path"],
                "filename": row["filename"],
                "size_bytes": int(row["size_bytes"]),
                "sha256": row["sha256"],
                "release_notes": row["release_notes"],
                "updated_at": row["updated_at"],
            }

    def upsert_mobile_release(
        self,
        *,
        platform: str = "android",
        version: str = "1.0.0",
        download_url: str = "",
        local_file_path: str = "",
        filename: str = "AuraLink-VPN-Android.apk",
        size_bytes: int = 0,
        sha256: str = "",
        release_notes: str = "",
    ) -> Dict[str, Any]:
        ph = self._ph
        now = _utc_now()
        values = (
            platform,
            platform,
            version,
            download_url,
            local_file_path,
            filename,
            int(size_bytes),
            sha256,
            release_notes,
            now,
        )
        placeholders = ", ".join([ph] * len(values))
        with self._connection() as conn:
            self._execute(
                conn,
                f"""
                INSERT INTO mobile_release (
                    id, platform, version, download_url, local_file_path,
                    filename, size_bytes, sha256, release_notes, updated_at
                ) VALUES ({placeholders})
                ON CONFLICT(id) DO UPDATE SET
                    version = excluded.version,
                    download_url = excluded.download_url,
                    local_file_path = excluded.local_file_path,
                    filename = excluded.filename,
                    size_bytes = excluded.size_bytes,
                    sha256 = excluded.sha256,
                    release_notes = excluded.release_notes,
                    updated_at = excluded.updated_at
                """,
                values,
            )
        return self.get_mobile_release(platform)  # type: ignore[return-value]

    def delete_mobile_release(self, platform: str = "android") -> bool:
        ph = self._ph
        with self._connection() as conn:
            cur = self._execute(
                conn, f"DELETE FROM mobile_release WHERE id = {ph}", (platform,)
            )
            return cur.rowcount > 0
