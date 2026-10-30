"""Builds a four layout batch from a drawn stand in photo (no client photos needed)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IM = "magick" if shutil.which("magick") else ("convert" if shutil.which("convert") else None)


@unittest.skipIf(IM is None, "ImageMagick not installed")
class BuildStillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = Path(self.tmp.name)
        (self.batch / "photos").mkdir()
        subprocess.run([IM, "-size", "800x800", "xc:white", "-fill", "#FD0082", "-draw", "circle 300,400 300,250",
                        "-fill", "#2FBAD1", "-draw", "circle 520,400 520,250", str(self.batch / "photos" / "pair.png")],
                       check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, ads):
        (self.batch / "copy.json").write_text(json.dumps({"batch": "test", "ads": ads}))

    def run_builder(self):
        return subprocess.run([sys.executable, str(ROOT / "ads" / "tools" / "build_stills.py"), str(self.batch)],
                              capture_output=True, text=True)

    def test_four_layouts(self):
        common = {"photo": "photos/pair.png", "headline": "Wear earrings again", "primary_text": "No metal touching the ear.",
                  "description": "Plastic posts", "focus": "O"}
        self.write([
            {**common, "id": "a1", "layout": "poster", "on_image": "No metal touching the ear.", "sub": "Faux Pearl Studs"},
            {**common, "id": "a2", "layout": "review", "on_image": "I can wear earrings again.", "quote_by": "Sample R."},
            {**common, "id": "a3", "layout": "note", "on_image": "Mom, they don't itch!"},
            {**common, "id": "a4", "layout": "tried", "on_image": "What worked: plastic posts.",
             "tried": ["Titanium", "Surgical steel", "Clear nail polish"]},
        ])
        out = self.run_builder()
        self.assertEqual(out.returncode, 0, out.stderr)
        for ad in ("a1", "a2", "a3", "a4"):
            png = self.batch / "final" / f"{ad}.png"
            size = subprocess.run([IM, "identify", "-format", "%wx%h", str(png)] if IM == "magick"
                                  else ["identify", "-format", "%wx%h", str(png)], capture_output=True, text=True).stdout
            self.assertEqual(size, "1080x1350", ad)
            self.assertIn("Edited, not generated", (self.batch / "final" / f"{ad}.md").read_text())
        self.assertTrue((self.batch / "sheet.jpg").exists())

    def test_rejects_dashes(self):
        self.write([{"id": "x", "photo": "photos/pair.png", "on_image": "Cute — and comfy", "headline": "h",
                     "primary_text": "p", "description": "d"}])
        out = self.run_builder()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("dash", out.stderr)


if __name__ == "__main__":
    unittest.main()
