#!/usr/bin/env python3
"""
AuraLink Mobile Free Keys Admin Backend (FastAPI + SQLite).

Purpose:
- Strictly publishes FREE VPN keys tagged with Region Cards exclusively for the Flutter Mobile App.
- Admin dashboard (`/admin`) + token-protected REST API (`/api/admin/keys`) to upload, toggle, edit, and remove keys.
- Public Mobile feed (`GET /api/mobile/free-keys`) returns only published free keys grouped by region.
"""

import hmac
import os
import secrets
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .database import FreeKeysDB, resolve_data_dir
from .key_utils import COUNTRY_FLAGS, country_code_to_flag, default_region_for_code, parse_free_key


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _load_or_create_admin_token() -> str:
    env_tok = os.environ.get("AURALINK_ADMIN_TOKEN", "").strip()
    if env_tok:
        return env_tok
    token_file = os.path.join(resolve_data_dir(), ".admin_token")
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as f:
            tok = f.read().strip()
            if tok:
                return tok
    tok = "auralink-admin-" + secrets.token_hex(16)
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(tok)
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        pass
    return tok


class CreateFreeKeyRequest(BaseModel):
    raw_key: str = Field(..., min_length=5, description="ss://, ssconf://, https://, or Shadowsocks JSON")
    country_code: str = Field(..., min_length=2, max_length=3, description="ISO 2-letter country code, e.g. JP, SG, US")
    region: Optional[str] = Field(None, description="Display region name, e.g. Japan, Singapore")
    city: str = Field("", max_length=64, description="Optional city name, e.g. Tokyo")
    label: Optional[str] = Field(None, max_length=80, description="Card title, e.g. Tokyo Free #1")
    flag: Optional[str] = Field(None, max_length=16, description="Flag emoji override")
    is_published: bool = Field(True, description="Whether immediately visible in Mobile Free Region Cards")
    sort_order: int = Field(0, description="Display sort priority (lower appears first)")


class UpdateFreeKeyRequest(BaseModel):
    raw_key: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    label: Optional[str] = None
    flag: Optional[str] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


def create_app(db_path: Optional[str] = None, admin_token: Optional[str] = None) -> FastAPI:
    db = FreeKeysDB(db_path=db_path)
    resolved_token = admin_token or _load_or_create_admin_token()

    app = FastAPI(
        title="AuraLink Mobile Free Keys Admin Backend",
        description="Mobile-only FREE VPN key publishing backend with Region Cards.",
        version="1.0.0",
    )
    app.state.db = db
    app.state.admin_token = resolved_token

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def require_admin(
        x_admin_token: Optional[str] = Header(default=None),
        authorization: Optional[str] = Header(default=None),
    ) -> None:
        candidate = (x_admin_token or "").strip()
        if not candidate and authorization and authorization.lower().startswith("bearer "):
            candidate = authorization[7:].strip()
        if not candidate or not hmac.compare_digest(candidate, resolved_token):
            raise HTTPException(status_code=401, detail="Invalid or missing Admin Token.")

    # ------------------------------------------------------------------
    # Admin Web Dashboard (Daylight Light Theme)
    # ------------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    @app.get("/admin", response_class=HTMLResponse)
    def admin_dashboard():
        html_path = os.path.join(STATIC_DIR, "admin.html")
        if os.path.exists(html_path):
            return FileResponse(html_path, media_type="text/html")
        return HTMLResponse("<h1>AuraLink Mobile Admin Backend Running</h1>")

    @app.get("/api/health")
    def health() -> Dict[str, Any]:
        published = db.list_keys(published_only=True)
        return {
            "status": "ok",
            "service": "auralink-mobile-free-keys",
            "scope": "mobile-only",
            "published_free_keys": len(published),
        }

    # ------------------------------------------------------------------
    # Public Mobile-Only Free Region Keys Feed
    # ------------------------------------------------------------------
    @app.get("/api/mobile/free-keys")
    def get_mobile_free_keys(
        region: Optional[str] = Query(default=None),
        country: Optional[str] = Query(default=None),
        x_auralink_client: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        """
        Publishes ONLY active FREE keys for the Flutter Mobile app Region Cards.
        """
        if x_auralink_client and x_auralink_client.lower() not in ("mobile", "flutter", "android", "ios"):
            raise HTTPException(
                status_code=403,
                detail="This free-keys endpoint is restricted to AuraLink Mobile clients.",
            )

        keys = db.list_keys(published_only=True, region=region, country_code=country)
        regions: List[str] = []
        region_summary: Dict[str, Dict[str, Any]] = {}
        for k in keys:
            reg = k["region"]
            if reg not in region_summary:
                regions.append(reg)
                region_summary[reg] = {
                    "region": reg,
                    "country_code": k["country_code"],
                    "flag": k["flag"],
                    "count": 0,
                }
            region_summary[reg]["count"] += 1

        return {
            "scope": "mobile-only",
            "tier": "FREE",
            "count": len(keys),
            "regions": regions,
            "region_cards": list(region_summary.values()),
            "keys": keys,
        }

    # ------------------------------------------------------------------
    # Protected Admin Endpoints
    # ------------------------------------------------------------------
    @app.post("/api/admin/auth/verify", dependencies=[Depends(require_admin)])
    def admin_verify() -> Dict[str, Any]:
        return {
            "authenticated": True,
            "presets": [
                {"country_code": cc, "flag": fl, "region": name}
                for cc, (fl, name) in COUNTRY_FLAGS.items()
            ],
        }

    @app.get("/api/admin/keys", dependencies=[Depends(require_admin)])
    def admin_list_keys() -> Dict[str, Any]:
        keys = db.list_keys(published_only=False)
        return {
            "total": len(keys),
            "published": sum(1 for k in keys if k["is_published"]),
            "keys": keys,
        }

    @app.post("/api/admin/keys", status_code=201, dependencies=[Depends(require_admin)])
    def admin_create_key(body: CreateFreeKeyRequest) -> Dict[str, Any]:
        try:
            parsed = parse_free_key(body.raw_key)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        cc = body.country_code.strip().upper()
        region = (body.region or "").strip() or default_region_for_code(cc)
        flag = (body.flag or "").strip() or country_code_to_flag(cc)
        city = (body.city or "").strip()
        label = (body.label or "").strip() or parsed.get("parsed_name") or (
            f"{city} Free" if city else f"{region} Free Node"
        )

        created = db.create_key(
            {
                "region": region,
                "country_code": cc,
                "flag": flag,
                "city": city,
                "label": label,
                "raw_key": body.raw_key.strip(),
                "source_type": parsed["source_type"],
                "server": parsed["server"],
                "server_port": parsed["server_port"],
                "method": parsed["method"],
                "password": parsed["password"],
                "prefix": parsed["prefix"],
                "is_published": body.is_published,
                "sort_order": body.sort_order,
            }
        )
        return {"ok": True, "key": created}

    @app.patch("/api/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
    def admin_update_key(key_id: str, body: UpdateFreeKeyRequest) -> Dict[str, Any]:
        existing = db.get_key(key_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Key not found.")

        updates: Dict[str, Any] = {}
        if body.raw_key is not None:
            try:
                parsed = parse_free_key(body.raw_key)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            updates.update(
                {
                    "raw_key": body.raw_key.strip(),
                    "source_type": parsed["source_type"],
                    "server": parsed["server"],
                    "server_port": parsed["server_port"],
                    "method": parsed["method"],
                    "password": parsed["password"],
                    "prefix": parsed["prefix"],
                }
            )
        if body.country_code is not None:
            cc = body.country_code.strip().upper()
            updates["country_code"] = cc
            if body.flag is None:
                updates["flag"] = country_code_to_flag(cc)
        if body.region is not None:
            updates["region"] = body.region.strip()
        if body.flag is not None:
            updates["flag"] = body.flag.strip()
        if body.city is not None:
            updates["city"] = body.city.strip()
        if body.label is not None:
            updates["label"] = body.label.strip()
        if body.is_published is not None:
            updates["is_published"] = body.is_published
        if body.sort_order is not None:
            updates["sort_order"] = body.sort_order

        updated = db.update_key(key_id, updates)
        return {"ok": True, "key": updated}

    @app.delete("/api/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
    def admin_delete_key(key_id: str) -> Dict[str, Any]:
        deleted = db.delete_key(key_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Key not found.")
        return {"ok": True, "deleted_id": key_id}

    return app


app = create_app()
