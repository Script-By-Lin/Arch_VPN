# AuraLink Mobile Free Keys Admin Backend

Lightweight **FastAPI + SQLite** admin backend strictly for publishing **FREE region-tagged VPN keys** to the **AuraLink Flutter Mobile App** (`mobile/`).

---

## Run Locally

```bash
# Install dependencies (already present if fastapi + uvicorn are installed)
pip install -r mobile_backend/requirements.txt

# Start server (set your own secret admin token)
AURALINK_ADMIN_TOKEN="change-me-super-secret" python3 mobile_backend/run.py
```

- **Admin Web Panel**: `http://127.0.0.1:8088/admin`
- **Mobile Free Keys Feed**: `GET http://127.0.0.1:8088/api/mobile/free-keys`
- **Health Check**: `GET http://127.0.0.1:8088/api/health`

> If `AURALINK_ADMIN_TOKEN` is not set, a random token is automatically generated and saved to `mobile_backend/data/.admin_token` (printed on startup).

---

## REST API Summary

| Endpoint | Auth | Purpose |
| :--- | :---: | :--- |
| `GET /admin` | — | Built-in Daylight Admin Dashboard to upload, toggle & delete free keys |
| `GET /api/mobile/free-keys` | Public *(Mobile-only)* | Returns **published FREE keys** with `region`, `country_code`, `flag`, `city`, and `region_cards` summary |
| `POST /api/admin/auth/verify` | `X-Admin-Token` | Verifies admin token & returns country/flag presets |
| `GET /api/admin/keys` | `X-Admin-Token` | Lists all keys (published + hidden drafts) |
| `POST /api/admin/keys` | `X-Admin-Token` | Uploads a new free key (`ss://`, `ssconf://`, or JSON) with region card metadata |
| `PATCH /api/admin/keys/{id}` | `X-Admin-Token` | Edits metadata/key or toggles `is_published` |
| `DELETE /api/admin/keys/{id}` | `X-Admin-Token` | Deletes a free key |

### Example Upload via `curl`
```bash
curl -X POST http://127.0.0.1:8088/api/admin/keys \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: change-me-super-secret" \
  -d '{
    "country_code": "JP",
    "region": "Japan",
    "city": "Tokyo",
    "label": "Tokyo Free #1",
    "raw_key": "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNzQDE5OC41MS4xMDAuMTA6ODQ0Mw#TokyoFree1",
    "is_published": true
  }'
```

---

## Deploy on Railway (Docker)

The repository root includes a Railway-ready [Dockerfile](../Dockerfile), [.dockerignore](../.dockerignore), and [railway.toml](../railway.toml) so you can deploy directly with zero extra setup:

1. In **Railway**, click **New Project → Deploy from GitHub Repo** and select this repository.
   - Railway automatically detects `railway.toml` + `Dockerfile` and verifies `/api/health`.
2. In your Railway Service → **Variables**, add:
   - `AURALINK_ADMIN_TOKEN` = `<your-strong-secret-token>`
   *(Railway injects `PORT` automatically — no need to set it.)*
3. *(Recommended for persistence)* In your Railway Service → **Volumes**, click **Add Volume** and set **Mount Path** to:
   - `/data`
   *(The backend automatically detects `RAILWAY_VOLUME_MOUNT_PATH` / `/data` and stores `free_keys.db` there so uploaded keys survive redeploys.)*
4. Generate a public domain in **Settings → Networking → Generate Domain** (e.g. `https://auralink-mobile-admin.up.railway.app`).
   - Open `https://<your-railway-domain>/admin` to upload free region keys.
   - Enter `https://<your-railway-domain>` in **AuraLink Mobile → Settings → Mobile Free Keys Admin Backend**.

### Test Locally with Docker Compose
```bash
AURALINK_ADMIN_TOKEN="my-local-secret" docker compose -f mobile_backend/docker-compose.yml up --build
```

---

## Connecting the Flutter Mobile App

1. Open **AuraLink Mobile** → **Settings** → **Free Keys Backend URL**.
   - Android Emulator: `http://10.0.2.2:8088` (default)
   - iOS Simulator: `http://127.0.0.1:8088`
   - Real Phone / Production: `https://your-domain.com` (or LAN IP `http://192.168.x.x:8088`)
2. Open the **Free** tab in the bottom navigation bar to browse **Region Cards** and connect with one tap!
