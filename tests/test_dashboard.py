"""Smoke test for scripts/dashboard.py. Uses temp ledger and data dirs and an isolated tmux socket."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        (t / "data").mkdir()
        (t / "approvals").mkdir()
        (t / "approvals" / "launch.md").write_text("---\ntitle: Launch batch one\nfrom: ads\nstatus: waiting\n---\n")
        (t / "approvals" / "old.md").write_text("---\ntitle: Old thing\nstatus: approved\n---\n")
        (t / "data" / "kpi.json").write_text(json.dumps({"average_order_value": 40, "product_cost_per_order": 8,
                                                          "shipping_cost_per_order": 5, "fees_per_order": 1.5}))
        self.env = {**os.environ, "HQ_LEDGER_DIR": str(t / "work"), "HQ_DATA_DIR": str(t / "data"),
                    "HQ_APPROVALS_DIR": str(t / "approvals"), "HQ_BACKEND": "tmux",
                    "HQ_TMUX_SOCKET": f"hqtest{os.getpid()}", "HQ_STATE_SAMPLE": "0.2"}
        subprocess.run([sys.executable, str(ROOT / "scripts" / "ledger"), "start", "--key", "d1", "--agent", "social",
                        "--title", "Plan next week"], env=self.env, check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_once(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "dashboard.py"), "--once"],
                             env=self.env, capture_output=True, text=True, check=True)
        s = json.loads(out.stdout)
        self.assertEqual([a["title"] for a in s["approvals"]], ["Launch batch one"])
        self.assertEqual(s["ledger"][0]["title"], "Plan next week")
        self.assertEqual(s["kpi"]["breakeven_roas"], round(40 / 25.5, 2))
        self.assertTrue(s["ads"]["_sample"])  # no live file, sample fallback
        self.assertEqual(s["agents"], [])      # no tmux session on the isolated socket

    def test_server(self):
        port = free_port()
        proc = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "dashboard.py"), "--port", str(port)],
                                env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                try:
                    body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read().decode()
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("dashboard did not start")
            for text in ("Emma <span>HQ</span>", "Launch batch one", "Plan next week", "SAMPLE", "1.57"):
                self.assertIn(text, body)
            api = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=5).read())
            self.assertIn("agents", api)
        finally:
            proc.terminate()
            proc.wait(5)


if __name__ == "__main__":
    unittest.main()
