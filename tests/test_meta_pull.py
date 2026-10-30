"""ads/tools/meta_pull.py: parses a recorded Graph API bundle and an Ads Manager CSV, talks only GET to a
local fake Graph API, and never shows the token. No real Meta call is made."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "ads" / "tools" / "meta_pull.py"
FIX = Path(__file__).resolve().parent / "fixtures"
TOKEN = "EAAtestTOKENdoNotShow0123456789"


class FakeGraph(BaseHTTPRequestHandler):
    seen: list = []
    fail_with_token = False

    def do_GET(self):  # noqa: N802
        parts = urlsplit(self.path)
        query = parse_qs(parts.query)
        FakeGraph.seen.append({"path": parts.path, "query": query, "auth": self.headers.get("Authorization"),
                               "method": self.command})
        port = self.server.server_address[1]
        if FakeGraph.fail_with_token:
            body, code = {"error": {"message": f"Invalid OAuth access token {TOKEN}", "code": 190}}, 400
        elif parts.path == "/v23.0/act_123":
            body, code = {"name": "Sample Store Ads", "currency": "USD", "account_status": 1}, 200
        elif parts.path == "/v23.0/act_123/insights" and query.get("level") == ["ad"] and "after" not in query:
            bundle = json.loads((FIX / "meta_bundle.json").read_text())
            rows = bundle["insights"]["data"]
            # page one; Meta's next links carry access_token, which the tool must strip and never print
            body = {"data": rows[:2], "paging": {"next": f"http://127.0.0.1:{port}/v23.0/act_123/insights?level=ad"
                                                          f"&after=p2&access_token={TOKEN}"}}
            code = 200
        elif parts.path == "/v23.0/act_123/insights" and query.get("level") == ["ad"]:
            body, code = {"data": json.loads((FIX / "meta_bundle.json").read_text())["insights"]["data"][2:]}, 200
        elif parts.path == "/v23.0/act_123/ads":
            body, code = json.loads((FIX / "meta_bundle.json").read_text())["ads"], 200
        elif parts.path == "/v23.0/act_123/insights":
            body, code = json.loads((FIX / "meta_bundle.json").read_text())["account_7d"], 200
        else:
            body, code = {"error": {"message": "unknown"}}, 404
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class MetaPullTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        (self.t / ".env").write_text(f"META_ACCESS_TOKEN={TOKEN}\nMETA_AD_ACCOUNT_ID=act_123\n")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("META_")}
        self.env.update(HQ_ENV_FILE=str(self.t / ".env"), HQ_AD_TAGS=str(self.t / "none.json"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, env=None):
        out = subprocess.run([sys.executable, str(TOOL), *args, "--today", "2026-10-30"] if "--check" not in args
                             else [sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env or self.env)
        for stream in (out.stdout, out.stderr):
            self.assertNotIn(TOKEN, stream)
        return out

    def ads(self, path):
        doc = json.loads(path.read_text())
        self.assertNotIn(TOKEN, path.read_text())
        return doc, {a["id"]: a for a in doc["ads"]}

    def test_recorded_bundle(self):
        out = self.run_tool("--from-json", str(FIX / "meta_bundle.json"), "--out", str(self.t / "ads.json"))
        self.assertEqual(out.returncode, 0, out.stderr)
        doc, by = self.ads(self.t / "ads.json")
        self.assertEqual(len(doc["ads"]), 3)  # the ad that spent nothing is left out
        a = by["120000000000000001"]
        self.assertEqual((a["focus"], a["batch"], a["format"], a["status"]), ("O", "2026-10-07", "still", "active"))
        self.assertEqual((a["purchases"], a["revenue"], a["roas"], a["cpa"], a["ctr"]), (21, 1010.0, 2.4, 20.0, 2.1))
        self.assertEqual(a["days_live"], 23)
        b = by["120000000000000002"]
        self.assertEqual((b["focus"], b["status"], b["purchases"]), ("S", "paused", 12))
        c = by["120000000000000003"]
        self.assertEqual((c["focus"], c["format"], c["purchases"], c["cpa"], c["ctr"]), ("", "video", 0, None, 0.9))
        self.assertEqual((doc["spend_7d"], doc["purchase_value_7d"], doc["source"]), (350.0, 910.0, "meta_api"))
        for key in ("id", "name", "focus", "batch", "format", "status", "spend", "purchases", "revenue", "roas",
                    "cpa", "ctr", "days_live"):
            self.assertIn(key, a)

    def test_csv_export(self):
        out = self.run_tool("--csv", str(FIX / "ads_manager_export.csv"), "--out", str(self.t / "ads.json"))
        self.assertEqual(out.returncode, 0, out.stderr)
        doc, _ = self.ads(self.t / "ads.json")
        self.assertEqual(doc["source"], "ads_manager_csv")
        self.assertEqual(len(doc["ads"]), 2)
        first, second = doc["ads"]
        self.assertEqual((first["name"], first["focus"], first["batch"], first["status"]),
                         ("C | Holiday stack, Buy 3 get 1", "C", "2026-10-07", "active"))
        self.assertEqual((first["spend"], first["purchases"], first["revenue"], first["ctr"], first["days_live"]),
                         (1230.4, 4, 150.0, 0.91, 22))
        self.assertEqual((second["focus"], second["status"], second["roas"]), ("F", "paused", 1.67))

    def test_csv_without_ad_name(self):
        bad = self.t / "bad.csv"
        bad.write_text("Campaign name,Amount spent (USD)\nX,10\n")
        out = self.run_tool("--csv", str(bad), "--dry-run")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Ad name", out.stderr)

    def test_missing_credentials(self):
        (self.t / ".env").write_text("META_ACCESS_TOKEN=\n")
        out = self.run_tool("--check")
        self.assertEqual(out.returncode, 1)
        self.assertIn("META_ACCESS_TOKEN and META_AD_ACCOUNT_ID missing", out.stderr)

    def with_fake_graph(self):
        FakeGraph.seen, FakeGraph.fail_with_token = [], False
        server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGraph)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return {**self.env, "META_GRAPH_URL": f"http://127.0.0.1:{server.server_address[1]}",
                "META_API_VERSION": "v23.0"}

    def test_api_pull_against_fake_graph(self):
        env = self.with_fake_graph()
        check = self.run_tool("--check", env=env)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("Sample Store Ads", check.stdout)
        out = self.run_tool("--out", str(self.t / "ads.json"), env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        doc, by = self.ads(self.t / "ads.json")
        self.assertEqual(len(doc["ads"]), 3)  # both insight pages were followed
        self.assertEqual(by["120000000000000003"]["format"], "video")
        for request in FakeGraph.seen:
            self.assertEqual(request["method"], "GET")
            self.assertEqual(request["auth"], f"Bearer {TOKEN}")  # token only in the header
            self.assertNotIn("access_token", request["query"])  # stripped from Meta's next links too

    def test_errors_hide_the_token(self):
        env = self.with_fake_graph()
        FakeGraph.fail_with_token = True
        out = self.run_tool("--check", env=env)
        self.assertEqual(out.returncode, 1)
        self.assertIn("[hidden]", out.stderr)
        self.assertIn("(error 190)", out.stderr)

    def test_refuses_other_hosts(self):
        sys.path.insert(0, str(TOOL.parent))
        try:
            import meta_pull
        finally:
            sys.path.pop(0)
        with self.assertRaises(meta_pull.PullError):
            meta_pull.graph_get("https://example.com/v23.0/me", TOKEN)


if __name__ == "__main__":
    unittest.main()
