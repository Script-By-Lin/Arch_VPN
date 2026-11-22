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


if __name__ == "__main__":
    unittest.main()
