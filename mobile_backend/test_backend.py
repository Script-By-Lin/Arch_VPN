#!/usr/bin/env python3
"""
Unit & Integration tests for the AuraLink Mobile Free Keys Admin Backend.
"""

import base64
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from mobile_backend.app import create_app


class TestMobileFreeKeysBackend(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test_free_keys.db")
        self.admin_token = "test-secret-admin-token"
        self.app = create_app(db_path=self.db_path, admin_token=self.admin_token)
        self.client = TestClient(self.app)
        self.admin_headers = {"X-Admin-Token": self.admin_token}

    def tearDown(self):
        self.tmp.cleanup()

    def _sample_ss_uri(self, host="77.83.241.82", port=443, tag="TokyoFree1"):
        userinfo = base64.urlsafe_b64encode(b"chacha20-ietf-poly1305:myPass123").decode().rstrip("=")
        return f"ss://{userinfo}@{host}:{port}#{tag}"

    def test_admin_auth_required(self):
        res = self.client.get("/api/admin/keys")
        self.assertEqual(res.status_code, 401)

        res_bad = self.client.post("/api/admin/auth/verify", headers={"X-Admin-Token": "wrong"})
        self.assertEqual(res_bad.status_code, 401)

        res_ok = self.client.post("/api/admin/auth/verify", headers=self.admin_headers)
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(res_ok.json()["authenticated"])

    def test_upload_publish_filter_and_delete_free_keys(self):
        # 1. Admin uploads a published Japan key
        jp_res = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={
                "raw_key": self._sample_ss_uri("198.51.100.10", 8443, "Tokyo Free #1"),
                "country_code": "JP",
                "city": "Tokyo",
                "label": "Tokyo Free #1",
                "is_published": True,
            },
        )
        self.assertEqual(jp_res.status_code, 201)
        jp_key = jp_res.json()["key"]
        self.assertEqual(jp_key["region"], "Japan")
        self.assertEqual(jp_key["flag"], "🇯🇵")
        self.assertEqual(jp_key["tier"], "FREE")
        self.assertEqual(jp_key["server"], "198.51.100.10")
        self.assertEqual(jp_key["server_port"], 8443)

        # 2. Admin uploads an UNPUBLISHED Singapore draft key
        sg_res = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={
                "raw_key": self._sample_ss_uri("198.51.100.20", 443, "SG Draft"),
                "country_code": "SG",
                "city": "Singapore",
                "label": "Singapore Free #1",
                "is_published": False,
            },
        )
        self.assertEqual(sg_res.status_code, 201)
        sg_id = sg_res.json()["key"]["id"]

        # 3. Mobile public feed ONLY returns published keys (Japan), hiding draft (Singapore)
        feed = self.client.get("/api/mobile/free-keys", headers={"X-AuraLink-Client": "mobile"})
        self.assertEqual(feed.status_code, 200)
        body = feed.json()
        self.assertEqual(body["scope"], "mobile-only")
        self.assertEqual(body["tier"], "FREE")
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["regions"], ["Japan"])
        self.assertEqual(body["keys"][0]["label"], "Tokyo Free #1")

        # 4. Non-mobile desktop client header is rejected on the mobile-only feed
        desk = self.client.get("/api/mobile/free-keys", headers={"X-AuraLink-Client": "desktop"})
        self.assertEqual(desk.status_code, 403)

        # 5. Admin publishes Singapore key -> now both Region Cards appear on Mobile
        pub = self.client.patch(
            f"/api/admin/keys/{sg_id}",
            headers=self.admin_headers,
            json={"is_published": True},
        )
        self.assertEqual(pub.status_code, 200)
        feed2 = self.client.get("/api/mobile/free-keys", headers={"X-AuraLink-Client": "mobile"}).json()
        self.assertEqual(feed2["count"], 2)
        self.assertEqual(set(feed2["regions"]), {"Japan", "Singapore"})
        self.assertEqual(len(feed2["region_cards"]), 2)

        # 6. Region filter works
        sg_only = self.client.get("/api/mobile/free-keys?country=SG").json()
        self.assertEqual(sg_only["count"], 1)
        self.assertEqual(sg_only["keys"][0]["country_code"], "SG")

        # 7. Delete key removes it cleanly
        del_res = self.client.delete(f"/api/admin/keys/{sg_id}", headers=self.admin_headers)
        self.assertEqual(del_res.status_code, 200)
        feed3 = self.client.get("/api/mobile/free-keys").json()
        self.assertEqual(feed3["count"], 1)

    def test_invalid_key_rejected_and_admin_html_served(self):
        bad = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": "not-a-valid-key", "country_code": "US"},
        )
        self.assertEqual(bad.status_code, 400)

        page = self.client.get("/admin")
        self.assertEqual(page.status_code, 200)
        self.assertIn("AuraLink Mobile Admin", page.text)

    def test_variable_key_formats_accepted(self):
        # 1. Exact OpenKeys.net UUID-only ss:// key with query params (encryption=none, type=ws)
        openkeys_ss = (
            "ss://4dc0eec9-f0e1-4755-be7e-7ba628522d1b@91.99.145.207:443"
            "?encryption=none&path=%2F&security=none&type=ws#Germany%20710%20/%20OpenKeys.net"
        )
        r1 = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": openkeys_ss, "country_code": "DE", "is_published": True},
        )
        self.assertEqual(r1.status_code, 201, r1.text)
        k1 = r1.json()["key"]
        self.assertEqual(k1["server"], "91.99.145.207")
        self.assertEqual(k1["server_port"], 443)
        self.assertEqual(k1["password"], "4dc0eec9-f0e1-4755-be7e-7ba628522d1b")
        self.assertEqual(k1["method"], "none")
        self.assertEqual(k1["label"], "Germany 710 / OpenKeys.net")
        self.assertEqual(k1["flag"], "🇩🇪")

        # 2. Plaintext SS2022 method:serverKey:userKey@host:port
        ss2022 = "ss://2022-blake3-aes-128-gcm:srvKey==:usrKey==@198.51.100.55:8443?plugin=v2ray-plugin%3Bmode%3Dwebsocket#SS2022-DE"
        r2 = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": ss2022, "country_code": "DE"},
        )
        self.assertEqual(r2.status_code, 201, r2.text)
        k2 = r2.json()["key"]
        self.assertEqual(k2["method"], "2022-blake3-aes-128-gcm")
        self.assertEqual(k2["password"], "srvKey==:usrKey==")

        # 3. vless://, trojan://, vmess:// keys
        vless_key = "vless://4dc0eec9-f0e1-4755-be7e-7ba628522d1b@91.99.145.207:443?encryption=none&security=tls&type=ws#VLESS-DE"
        r3 = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": vless_key, "country_code": "DE"},
        )
        self.assertEqual(r3.status_code, 201, r3.text)
        self.assertEqual(r3.json()["key"]["source_type"], "vless")

        trojan_key = "trojan://superSecretToken@203.0.113.9:443?security=tls&sni=example.com#Trojan-JP"
        r4 = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": trojan_key, "country_code": "JP"},
        )
        self.assertEqual(r4.status_code, 201, r4.text)
        self.assertEqual(r4.json()["key"]["source_type"], "trojan")

        vmess_payload = base64.b64encode(
            b'{"v":"2","ps":"VMess-SG","add":"198.51.100.8","port":"443","id":"11111111-2222-3333-4444-555555555555","scy":"auto"}'
        ).decode()
        r5 = self.client.post(
            "/api/admin/keys",
            headers=self.admin_headers,
            json={"raw_key": f"vmess://{vmess_payload}", "country_code": "SG"},
        )
        self.assertEqual(r5.status_code, 201, r5.text)
        k5 = r5.json()["key"]
        self.assertEqual(k5["source_type"], "vmess")
        self.assertEqual(k5["label"], "VMess-SG")
        self.assertEqual(k5["server"], "198.51.100.8")

    def test_mobile_apk_release_link_and_upload(self):
        # 1. Initially unavailable
        r0 = self.client.get("/api/mobile/release")
        self.assertEqual(r0.status_code, 200)
        self.assertFalse(r0.json()["available"])

        # 2. Admin sets external APK link
        r1 = self.client.put(
            "/api/admin/mobile-release",
            headers=self.admin_headers,
            json={
                "version": "1.2.0",
                "download_url": "https://example.com/AuraLink-1.2.0.apk",
                "release_notes": "Initial Android release",
            },
        )
        self.assertEqual(r1.status_code, 200)
        rel = self.client.get("/api/mobile/release").json()
        self.assertTrue(rel["available"])
        self.assertEqual(rel["version"], "1.2.0")
        self.assertEqual(rel["download_url"], "https://example.com/AuraLink-1.2.0.apk")

        # 3. Admin uploads APK binary directly and downloads it back
        fake_apk = b"PK\x03\x04fake-auralink-apk-payload"
        up = self.client.post(
            "/api/admin/mobile-release/upload-apk",
            headers={
                **self.admin_headers,
                "Content-Type": "application/octet-stream",
                "X-Release-Version": "1.3.0",
                "X-Release-Notes": "Direct Railway hosted APK",
                "X-Filename": "AuraLink-VPN-Android.apk",
            },
            content=fake_apk,
        )
        self.assertEqual(up.status_code, 201)
        rel2 = self.client.get("/api/mobile/release").json()
        self.assertTrue(rel2["available"])
        self.assertTrue(rel2["hosted_locally"])
        self.assertEqual(rel2["size_bytes"], len(fake_apk))
        self.assertTrue(rel2["download_url"].endswith("/api/mobile/download/apk"))

        dl = self.client.get("/api/mobile/download/apk")
        self.assertEqual(dl.status_code, 200)
        self.assertEqual(dl.content, fake_apk)

        # 4. Delete clears release
        d = self.client.delete("/api/admin/mobile-release", headers=self.admin_headers)
        self.assertEqual(d.status_code, 200)
        self.assertFalse(self.client.get("/api/mobile/release").json()["available"])

    def test_postgres_url_resolution_and_redaction(self):
        from mobile_backend.database import (
            is_postgres_url,
            normalize_postgres_url,
            redact_database_url,
            resolve_database_url,
        )

        self.assertTrue(is_postgres_url("postgres://user:secret@host:5432/railway"))
        self.assertTrue(is_postgres_url("postgresql://user:secret@host:5432/railway?sslmode=require"))
        self.assertFalse(is_postgres_url("/tmp/free_keys.db"))

        norm = normalize_postgres_url("postgres://user:supersecret@pg.railway.internal:5432/railway")
        self.assertEqual(norm, "postgresql://user:supersecret@pg.railway.internal:5432/railway")
        redacted = redact_database_url(norm)
        self.assertNotIn("supersecret", redacted)
        self.assertIn("pg.railway.internal:5432/railway", redacted)

        # Explicit SQLite file path overrides env DATABASE_URL for isolated tests
        prev = os.environ.get("DATABASE_URL")
        try:
            os.environ["DATABASE_URL"] = "postgres://u:p@localhost:5432/db"
            self.assertIsNone(resolve_database_url(db_path="/tmp/local.db"))
            self.assertEqual(
                resolve_database_url(),
                "postgresql://u:p@localhost:5432/db",
            )
        finally:
            if prev is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = prev


if __name__ == "__main__":
    unittest.main()
