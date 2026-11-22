#!/usr/bin/env python3
"""
Entry point to launch the AuraLink Mobile Free Keys Admin Backend.
Usage:
  AURALINK_ADMIN_TOKEN=my-secret python3 mobile_backend/run.py
"""

import os
import sys

# Ensure project root is on sys.path so `mobile_backend.app` imports cleanly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import uvicorn
from mobile_backend.app import app


def main():
    host = os.environ.get("AURALINK_BACKEND_HOST", "0.0.0.0")
    # Railway injects PORT automatically; fallback to AURALINK_BACKEND_PORT or 8088
    port = int(os.environ.get("PORT") or os.environ.get("AURALINK_BACKEND_PORT") or "8088")
    env_token_set = bool(os.environ.get("AURALINK_ADMIN_TOKEN", "").strip())

    print("════════════════════════════════════════════════════════════")
    print("  AuraLink Mobile Free Keys Admin Backend")
    print(f"  Bind        : http://{host}:{port}")
    print(f"  Admin Panel : /admin")
    print(f"  Mobile Feed : /api/mobile/free-keys")
    print(f"  SQLite DB   : {app.state.db.db_path}")
    if env_token_set:
        print("  Admin Token : [loaded from AURALINK_ADMIN_TOKEN env var]")
    else:
        print(f"  Admin Token : {app.state.admin_token}")
    print("════════════════════════════════════════════════════════════")

    uvicorn.run(
        app,
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
