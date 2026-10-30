"""The dashboard's ads pages render from the samples in data/examples, and the image and memory routes
refuse anything outside their folders. Temp folders and an isolated tmux socket only."""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dashboard  # noqa: E402

sys.path.pop(0)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start(env):
    port = free_port()
    proc = subprocess.Popen([sys.executable, str(ROOT / "scripts" / "dashboard.py"), "--port", str(port)],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/memory", timeout=5).read()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.terminate()
    raise RuntimeError("dashboard did not start")


def raw_get(port, path):
    """Send the path exactly as written, so ../ and %2e%2e reach the server unnormalized."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.putrequest("GET", path, skip_host=False, skip_accept_encoding=True)
    conn.endheaders()
    response = conn.getresponse()
    body = response.read()
    conn.close()
    return response.status, response.getheader("Content-Type", ""), body


class Base(unittest.TestCase):
    @classmethod
    def make_env(cls, t):
        (t / "data").mkdir()
        shutil.copytree(ROOT / "data" / "examples", t / "data" / "examples")
        (t / "approvals").mkdir()
        return {**os.environ, "HQ_LEDGER_DIR": str(t / "work"), "HQ_DATA_DIR": str(t / "data"),
                "HQ_APPROVALS_DIR": str(t / "approvals"), "HQ_BATCHES_DIR": str(t / "batches"),
                "HQ_MEMORY_DIR": str(t / "memory"), "HQ_BACKEND": "tmux",
                "HQ_TMUX_SOCKET": f"hqpages{os.getpid()}", "HQ_STATE_SAMPLE": "0.2"}

    def get(self, path):
        status, kind, body = raw_get(self.port, path)
        return status, kind, body


class SamplePagesTest(Base):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = Path(cls.tmp.name)
        cls.outside = t / "secret.png"
        cls.outside.write_bytes(b"\x89PNG not for the dashboard")
        cls.proc, cls.port = start(cls.make_env(t))

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        cls.tmp.cleanup()

    def page(self, path):
        status, kind, body = self.get(path)
        self.assertEqual(status, 200, path)
        self.assertIn("text/html", kind)
        text = body.decode()
        self.assertIn('<nav>', text)
        return text

    def test_overview_keeps_its_panels(self):
        text = self.page("/")
        for part in ("Waiting on you", "Agents", "Meta ads, last 7 days", "Store sales", "Recent work", "SAMPLE", "1.57"):
            self.assertIn(part, text)

    def test_launch(self):
        text = self.page("/launch")
        for part in ("Next launch", 'id="count" data-target="', "America/Chicago", "Wednesday", "SAMPLE",
                     "Short bucket", "Unspoken cost", "/img/2026-11-04/b1.png", "/img/2026-11-04/b2.png",
                     "What is winning", "Wear earrings again, review card", "Kill switch proposals",
                     "Holiday stack, Buy 3 get 1", "failed the critic gate"):
            self.assertIn(part, text)
        self.assertNotIn("/img/2026-11-04/b6.png", text)  # the critic fail is held back

    def test_tracker(self):
        text = self.page("/tracker")
        for part in ("break even ROAS", "1.57", "1.96", "$20.40", "$204.00", "Kill candidate", "SAMPLE", "Too early"):
            self.assertIn(part, text)
        order = [text.index(name) for name in ("Wear earrings again, review card", "First dangles for my daughter",
                                               "Titanium still itched", "Holes closing up")]
        self.assertEqual(order, sorted(order), "best ROAS first")

    def test_focus(self):
        text = self.page("/focus")
        self.assertIn('<div class="bucket short"><b class="l">U</b>', text)
        self.assertIn("The gap", text)
        self.assertIn("SAMPLE", text)
        for letter in "FOCUS":
            self.assertIn(f'<b class="l">{letter}</b>', text)

    def test_batches(self):
        text = self.page("/batches")
        for part in ("2026-11-04", "SAMPLE", "7/10", "1 failed", "/img/2026-11-04/b1.png", "Contact sheet",
                     "Are your piercings closing up?"):
            self.assertIn(part, text)

    def test_memory(self):
        text = self.page("/memory")
        self.assertIn("STARTER", text)
        self.assertIn('href="/memory/offers.md"', text)
        self.assertIn("project", text)
        doc = self.page("/memory/offers.md")
        self.assertIn("Buy 3, Get 1 FREE", doc)
        for bad in ("/memory/../CLAUDE.md", "/memory/..%2fCLAUDE.md", "/memory/%2e%2e%2fREADME.md",
                    "/memory/.env", "/memory/x/../../setup.sh"):
            self.assertEqual(self.get(bad)[0], 404, bad)

    def test_images(self):
        status, kind, body = self.get("/img/2026-11-04/b1.png")
        self.assertEqual((status, kind), (200, "image/png"))
        self.assertTrue(body.startswith(b"\x89PNG"))
        self.assertEqual(self.get("/img/2026-11-04/sheet.jpg")[0], 200)

    def test_image_route_refuses_traversal(self):
        for bad in ("/img/../../etc/passwd", "/img/2026-11-04/../copy.json", "/img/..%2f..%2fetc/passwd",
                    "/img/2026-11-04/..%2f..%2f..%2fsecret.png", "/img/2026-11-04/%2e%2e%2fsheet.jpg",
                    "/img/%2e%2e/secret.png", "/img/2026-11-04/..%5c..%5csecret.png", "/img/2026-11-04/copy.json",
                    "/img/2026-11-04/photos%2fstandin-studs.png", "/img/2026-11-04/b1.md", "/img/.git/config",
                    "/img/2026-11-04/../../../../scripts/dashboard.py", "/img//etc%2fpasswd"):
            status, _, body = self.get(bad)
            self.assertEqual(status, 404, bad)
            self.assertNotIn(b"not for the dashboard", body)

    def test_api_state(self):
        api = json.loads(self.get("/api/state")[2])
        self.assertEqual(api["focus"]["short"], "U")
        self.assertEqual(api["launch"]["upcoming"], "2026-11-04")
        self.assertEqual(api["kpi"]["kill_spend"], 204.0)


class RealBatchTest(Base):
    """A real batch in ads/batches wins over the sample, and a symlink out of the folder is refused."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t = Path(cls.tmp.name)
        env = cls.make_env(t)
        batch = t / "batches" / "2026-12-02"
        (batch / "final").mkdir(parents=True)
        shutil.copy(ROOT / "data" / "examples" / "batches" / "2026-11-04" / "final" / "b4.png", batch / "final" / "r1.png")
        (batch / "copy.json").write_text(json.dumps({"focus": "S", "ads": [{"id": "r1", "focus": "S", "headline": "Real one"}]}))
        (t / "outside.png").write_bytes(b"\x89PNG outside the batch root")
        os.symlink(t / "outside.png", batch / "final" / "leak.png")
        cls.proc, cls.port = start(env)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(5)
        cls.tmp.cleanup()

    def test_real_batch_shown(self):
        text = self.get("/batches")[2].decode()
        self.assertIn("2026-12-02", text)
        self.assertNotIn("2026-11-04", text)
        self.assertNotIn('<span class="tag">SAMPLE</span></h2>', text.split("2026-12-02", 1)[1][:60])
        self.assertEqual(self.get("/img/2026-12-02/r1.png")[0], 200)
        self.assertEqual(self.get("/img/2026-11-04/b1.png")[0], 404)

    def test_symlink_out_is_refused(self):
        status, _, body = self.get("/img/2026-12-02/leak.png")
        self.assertEqual(status, 404)
        self.assertNotIn(b"outside the batch root", body)


class RulesTest(unittest.TestCase):
    def test_money_rules(self):
        k = dashboard.kpi_numbers({"average_order_value": 40, "product_cost_per_order": 8,
                                   "shipping_cost_per_order": 5, "fees_per_order": 1.5})
        self.assertEqual((k["breakeven_roas"], k["target_roas"], k["breakeven_cpa"], k["target_cpa"], k["kill_spend"]),
                         (1.57, 1.96, 25.5, 20.4, 204.0))
        self.assertIsNone(dashboard.kpi_numbers({})["breakeven_roas"])

    def test_kill_switch(self):
        k = {"breakeven_roas": 1.57, "kill_spend": 204.0}
        row = {"status": "active", "days_live": 23, "spend": 230, "roas": 0.65}
        self.assertEqual(dashboard.kill_switch(row, k), "Kill candidate")
        self.assertEqual(dashboard.kill_switch({**row, "days_live": 6}, k), "Too early")
        self.assertEqual(dashboard.kill_switch({**row, "spend": 150}, k), "Under kill threshold")
        self.assertEqual(dashboard.kill_switch({**row, "roas": 1.8}, k), "Above break even")
        self.assertEqual(dashboard.kill_switch({**row, "status": "paused"}, k), "")

    def test_next_launch_central_time(self):
        settings = {"day": "Wednesday", "time": "10:00", "timezone": "America/Chicago"}
        moment, note = dashboard.next_launch(datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc), settings)
        self.assertEqual(note, "")
        self.assertEqual(moment.astimezone(timezone.utc), datetime(2026, 11, 4, 16, 0, tzinfo=timezone.utc))  # CST
        same_day, _ = dashboard.next_launch(datetime(2026, 11, 4, 15, 59, tzinfo=timezone.utc), settings)
        self.assertEqual(same_day.day, 4)
        next_week, _ = dashboard.next_launch(datetime(2026, 11, 4, 16, 1, tzinfo=timezone.utc), settings)
        self.assertEqual(next_week.day, 11)
        _, note = dashboard.next_launch(datetime(2026, 10, 30, tzinfo=timezone.utc), {**settings, "timezone": "Mars/Base"})
        self.assertIn("UTC", note)

    def test_batch_size(self):
        self.assertEqual(dashboard.batch_size(50, 0)["total"], 3)
        self.assertEqual(dashboard.batch_size(800, 0.25), {"tier": 2, "range": "5 to 10", "total": 8, "videos": 2,
                                                           "stills": 6})

    def test_critic_and_diversity(self):
        critic = dashboard.parse_critic("| a1 | pass | ok |\n| a2 | FAIL | cut off |\n", ["a1", "a2", "a10"])
        self.assertEqual(critic["per_ad"], {"a1": "pass", "a2": "fail"})
        self.assertEqual(critic["summary"], "1 failed")
        self.assertEqual(dashboard.parse_diversity("**Overall: 7/10.** fine"), 7.0)
        self.assertEqual(dashboard.parse_diversity("Overall score 6.5 out of 10"), 6.5)


if __name__ == "__main__":
    unittest.main()
