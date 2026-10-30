"""The ten catalogue layouts, the spec validator, the ImageMagick 6 path and the sources list.

No client photos or brand fonts are needed: photos and the logo are drawn placeholders,
and the font folder is empty, so the font fallback is exercised too.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "ads" / "tools"
EXAMPLE = ROOT / "ads" / "batches" / "examples" / "2026-10-29" / "spec.json"
sys.path.insert(0, str(TOOLS))

import build_stills  # noqa: E402
import fetch_sources  # noqa: E402
from layouts import LAYOUTS  # noqa: E402

HAVE_IM = bool(shutil.which("magick") or shutil.which("convert"))
IM = ["magick"] if shutil.which("magick") else ["convert"]
IDENT = ["magick", "identify"] if shutil.which("magick") else ["identify"]


def placeholder_batch(folder: Path, ads=None) -> dict:
    """A batch with every catalogue layout, the example strings, and drawn stand in photos."""
    (folder / "photos").mkdir(parents=True, exist_ok=True)
    colors = ["#FD0082", "#2FBAD1", "#5E106B", "#8B85C1", "#F5B301", "#2B2330"]
    for i, col in enumerate(colors):
        subprocess.run(IM + ["-size", "640x800", "xc:white", "-fill", col, "-draw", "circle 220,400 220,260",
                             "-draw", "circle 420,400 420,260", str(folder / "photos" / f"p{i}.png")], check=True)
    subprocess.run(IM + ["-size", "400x80", "xc:none", "-fill", "#FD0082", "-draw", "roundrectangle 0,0 399,79 20,20",
                         str(folder / "photos" / "logo.png")], check=True)
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    spec = {"batch": "test", "brand": {"logo": "photos/logo.png", "colors": example["brand"]["colors"]}, "ads": []}
    for ad in ads or example["ads"]:
        ad = dict(ad)
        ad["photos"] = [f"photos/p{i}.png" for i in range(len(LAYOUTS[ad["layout"]].PHOTOS))]
        spec["ads"].append(ad)
    (folder / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    return spec


def run_builder(batch: Path, *extra, env=None):
    e = {**os.environ, **(env or {})}
    return subprocess.run([sys.executable, str(TOOLS / "build_stills.py"), str(batch), *extra],
                          capture_output=True, text=True, env=e)


@unittest.skipIf(not HAVE_IM, "ImageMagick not installed")
class LayoutsRenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = Path(self.tmp.name) / "batch"
        self.fonts = Path(self.tmp.name) / "nofonts"
        self.fonts.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def check_outputs(self, spec):
        for ad in spec["ads"]:
            png = self.batch / "final" / f"{ad['file']}.png"
            size = subprocess.run(IDENT + ["-format", "%wx%h", str(png)], capture_output=True, text=True).stdout
            self.assertEqual(size, "1080x1350", ad["layout"])
            md = (self.batch / "final" / f"{ad['file']}.md").read_text()
            self.assertIn("Edited, not generated", md)
            self.assertIn("## Every string that renders", md)
            self.assertIn(ad["headline"], md)
        self.assertTrue((self.batch / "sheet.jpg").exists())

    def test_every_layout_renders_with_fallback_fonts(self):
        spec = placeholder_batch(self.batch)
        self.assertEqual(sorted(a["layout"] for a in spec["ads"]), sorted(LAYOUTS))
        out = run_builder(self.batch, env={"EMMA_FONTS_DIR": str(self.fonts), "EMMA_NO_SYSTEM_FONTS": "1"})
        self.assertEqual(out.returncode, 0, out.stderr[-3000:])
        self.assertIn("warning: font", out.stderr)
        self.check_outputs(spec)

    def test_imagemagick6_path(self):
        """Forces the IM6 commands. With real IM6 installed they run as is; on an IM7 machine a shim
        maps them to IM7's legacy parser and makes `magick` itself fail, so any IM7 only call is caught."""
        env = {"EMMA_IM": "6", "EMMA_FONTS_DIR": str(self.fonts), "EMMA_NO_SYSTEM_FONTS": "1"}
        shim = Path(self.tmp.name) / "shim"
        if shutil.which("magick"):
            subprocess.run(["bash", str(ROOT / "tests" / "im6shim" / "make_shim.sh"), str(shim)], check=True)
            env["PATH"] = f"{shim}{os.pathsep}{os.environ['PATH']}"
        spec = placeholder_batch(self.batch)
        out = run_builder(self.batch, env=env)
        self.assertEqual(out.returncode, 0, out.stderr[-3000:])
        self.assertIn("ImageMagick 6", out.stdout)
        if shim.exists():
            self.assertFalse((shim / "magick-calls.log").exists(), "the IM6 path called magick")
            calls = (shim / "calls.log").read_text()
            self.assertIn("convert ", calls)
            self.assertIn("identify ", calls)
            self.assertIn("montage ", calls)
        self.check_outputs(spec)


@unittest.skipIf(not HAVE_IM, "ImageMagick not installed")
class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.batch = Path(self.tmp.name)
        self.spec = placeholder_batch(self.batch)

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self):
        return build_stills.validate(self.spec, self.batch)

    def test_clean_spec_passes(self):
        self.assertEqual(self.errors(), [])

    def test_rejects_dash_on_image(self):
        for dash in ("-", "–", "—"):
            self.spec["ads"][0]["on_image"]["title"] = f"Cute {dash} and comfy"
            self.assertTrue(any("dash" in e for e in self.errors()), dash)

    def test_rejects_dash_in_a_list_field(self):
        self.spec["ads"][0]["on_image"]["crossed"][1] = "Nickel-free posts"
        self.assertTrue(any("dash" in e and "Nickel-free" in e for e in self.errors()))

    def test_allows_e_commerce(self):
        self.spec["ads"][0]["primary_text"] += " Shop our e-commerce store."
        self.assertEqual(self.errors(), [])

    def test_rejects_missing_photo(self):
        self.spec["ads"][3]["photos"][1] = "photos/nope.png"
        self.assertTrue(any("photo not found" in e for e in self.errors()))

    def test_rejects_too_few_photos(self):
        self.spec["ads"][5]["photos"] = self.spec["ads"][5]["photos"][:2]
        self.assertTrue(any("needs 6 photo" in e for e in self.errors()))

    def test_rejects_unknown_layout(self):
        self.spec["ads"][0]["layout"] = "hologram"
        self.assertTrue(any("unknown layout" in e for e in self.errors()))

    def test_rejects_missing_and_unknown_fields(self):
        del self.spec["ads"][2]["on_image"]["stamp"]
        self.spec["ads"][2]["on_image"]["subtitle"] = "x"
        errs = self.errors()
        self.assertTrue(any("needs on_image.stamp" in e for e in errs))
        self.assertTrue(any("no field on_image.subtitle" in e for e in errs))

    def test_rejects_duplicate_ids_and_bad_focus(self):
        self.spec["ads"][1]["id"] = self.spec["ads"][0]["id"]
        self.spec["ads"][4]["focus"] = "Z"
        errs = self.errors()
        self.assertTrue(any("unique id" in e for e in errs))
        self.assertTrue(any("focus" in e for e in errs))

    def test_builder_refuses_and_builds_nothing(self):
        self.spec["ads"][0]["on_image"]["final"] = "No metal — ever"
        (self.batch / "spec.json").write_text(json.dumps(self.spec))
        out = run_builder(self.batch)
        self.assertEqual(out.returncode, 1)
        self.assertIn("dash", out.stderr)
        self.assertFalse((self.batch / "final").exists())


class ExampleSpecTest(unittest.TestCase):
    def test_example_batch_is_valid_apart_from_photos(self):
        """The committed example spec only fails on photos that have not been fetched yet."""
        spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        errs = [e for e in build_stills.validate(spec, EXAMPLE.parent) if "photo not found" not in e]
        self.assertEqual(errs, [])
        self.assertEqual(len(spec["ads"]), 10)
        self.assertEqual(len({a["layout"] for a in spec["ads"]}), 10)

    def test_example_photos_are_in_the_url_list(self):
        spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        listed = {name for name, _, _ in fetch_sources.read_list(fetch_sources.DEFAULT_LIST)}
        for ad in spec["ads"]:
            for p in ad["photos"]:
                self.assertIn(Path(p).name, listed, ad["id"])
        self.assertIn("logo.svg", listed)


class SourcesListTest(unittest.TestCase):
    def test_parses_and_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            good = Path(d) / "good.tsv"
            good.write_text("# comment\na.jpg\tA photo\thttps://cdn.example.com/a.jpg\nb.svg\thttps://x.example.com/b.svg\n")
            rows = fetch_sources.read_list(good)
            self.assertEqual(rows[0], ("a.jpg", "A photo", "https://cdn.example.com/a.jpg"))
            self.assertEqual(fetch_sources.dest_for("b.svg").parent.name, "logo")
            for bad in ("a.jpg\tA\thttp://insecure.example.com/a.jpg\n", "../a.jpg\tA\thttps://x.example.com/a\n"):
                p = Path(d) / "bad.tsv"
                p.write_text(bad)
                with self.assertRaises(SystemExit):
                    fetch_sources.read_list(p)


if __name__ == "__main__":
    unittest.main()
