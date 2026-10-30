#!/usr/bin/env python3
"""Zero credit ad still builder for Emma HQ.

Builds 4:5 Meta stills (1080x1350 PNG) from real product photos and type, with
ImageMagick only. No image model, no network, no credits. Every string comes from
copy.json, so the batch rebuilds the same way every time.

  python3 ads/tools/build_stills.py ads/batches/2026-11-04
      reads  ads/batches/2026-11-04/copy.json
      writes ads/batches/2026-11-04/final/<id>.png, <id>.md, and sheet.jpg

copy.json:
{
  "batch": "2026-11-04",
  "focus": "S",
  "ads": [
    {"id": "a1", "layout": "poster", "photo": "photos/faux-pearl.png",
     "on_image": "No metal touching the ear.", "sub": "Faux Pearl Studs",
     "headline": "...", "primary_text": "...", "description": "...", "focus": "O",
     "persona": "gave up for years", "why": "..."}
  ]
}

Layouts: poster, review, note, tried. Optional per ad: "bg" (hex), "quote_by",
"tried" (list of strings for the tried layout), "logo" (path).
Photo paths are relative to the batch folder.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1350
PINK, TEAL, PURPLE, CREAM, NOTE = "#FD0082", "#2FBAD1", "#5E106B", "#FFF8F2", "#FFF2A8"
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def im() -> list[str]:
    if shutil.which("magick"):
        return ["magick"]
    if shutil.which("convert"):
        return ["convert"]
    sys.exit("ImageMagick is not installed. Run ./setup.sh")


def identify() -> list[str]:
    return ["magick", "identify"] if shutil.which("magick") else ["identify"]


def montage() -> list[str]:
    return ["magick", "montage"] if shutil.which("magick") else ["montage"]


def font(kind: str) -> list[str]:
    """Use the brand fonts if they are in ads/assets/fonts, else ImageMagick's default."""
    names = {"head": ["FjallaOne-Regular.ttf"], "body": ["Poppins-Regular.ttf"], "bold": ["Poppins-Bold.ttf"],
             "hand": ["PermanentMarker-Regular.ttf", "Caveat-Bold.ttf"]}
    for name in names.get(kind, []):
        path = ASSETS / "fonts" / name
        if path.exists():
            return ["-font", str(path)]
    return []


def text_box(out: Path, text: str, width: int, height: int, size: int, color: str, kind: str = "body",
             gravity: str = "NorthWest") -> Path:
    subprocess.run(im() + ["-background", "none", "-fill", color, *font(kind), "-pointsize", str(size),
                           "-size", f"{width}x{height}", "-gravity", gravity, f"caption:{text}", str(out)], check=True)
    return out


def stars(out: Path, count: int = 5, size: int = 64, color: str = "#F5B301") -> Path:
    """Five drawn stars, so no font needs a star glyph."""
    import math
    gap = 14
    draws = []
    for n in range(count):
        cx, cy, r_out, r_in = n * (size + gap) + size / 2, size / 2, size / 2, size / 5
        pts = []
        for k in range(10):
            r = r_out if k % 2 == 0 else r_in
            a = math.pi / 2 + k * math.pi / 5
            pts.append(f"{cx + r * math.cos(a):.1f},{cy - r * math.sin(a):.1f}")
        draws += ["-draw", "polygon " + " ".join(pts)]
    subprocess.run(im() + ["-size", f"{count * (size + gap) - gap}x{size}", "xc:none", "-fill", color, *draws,
                           str(out)], check=True)
    return out


def photo(src: Path, out: Path, width: int, height: int, cover: bool = False) -> Path:
    geometry = f"{width}x{height}^" if cover else f"{width}x{height}"
    args = im() + [str(src), "-resize", geometry]
    if cover:
        args += ["-gravity", "center", "-extent", f"{width}x{height}"]
    subprocess.run(args + [str(out)], check=True)
    return out


def compose(base: list[str], layers: list[tuple[Path, str, int, int]], out: Path) -> None:
    args = im() + base
    for path, gravity, x, y in layers:
        args += [str(path), "-gravity", gravity, "-geometry", f"+{x}+{y}", "-composite"]
    subprocess.run(args + [str(out)], check=True)


def build(ad: dict, batch: Path, tmp: Path, out: Path) -> None:
    layout = ad.get("layout", "poster")
    src = batch / ad["photo"]
    if not src.exists():
        raise FileNotFoundError(f"{ad['id']}: photo not found: {src}")
    layers: list[tuple[Path, str, int, int]] = []
    if layout == "poster":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', CREAM)}"]
        layers.append((text_box(tmp / "h.png", ad["on_image"], 940, 420, 104, ad.get("ink", PURPLE), "head", "North"),
                       "North", 0, 90))
        layers.append((photo(src, tmp / "p.png", 820, 640), "South", 0, 170))
        if ad.get("sub"):
            layers.append((text_box(tmp / "s.png", ad["sub"], 940, 80, 40, PINK, "bold", "South"), "South", 0, 70))
    elif layout == "review":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', PINK)}"]
        card = tmp / "card.png"
        subprocess.run(im() + ["-size", "940x620", "xc:none", "-fill", "white", "-draw",
                               "roundrectangle 0,0 939,619 36,36", str(card)], check=True)
        layers.append((card, "North", 0, 70))
        layers.append((stars(tmp / "st.png"), "North", 0, 110))
        layers.append((text_box(tmp / "q.png", f"“{ad['on_image']}”", 840, 380, 50, PURPLE, "bold", "Center"),
                       "North", 0, 190))
        if ad.get("quote_by"):
            layers.append((text_box(tmp / "by.png", ad["quote_by"], 840, 60, 34, "#857A8A", "body", "North"),
                           "North", 0, 590))
        layers.append((photo(src, tmp / "p.png", 760, 560), "South", 0, 50))
    elif layout == "note":
        base = [str(photo(src, tmp / "bg.png", W, H, cover=True))]
        note = tmp / "note.png"
        subprocess.run(im() + ["-size", "560x560", f"xc:{NOTE}", "-bordercolor", NOTE, "-border", "0",
                               "(", "+clone", "-background", "#00000066", "-shadow", "60x12+10+14", ")",
                               "+swap", "-background", "none", "-layers", "merge", "+repage", str(note)], check=True)
        noted = tmp / "noted.png"
        txt = text_box(tmp / "nt.png", ad["on_image"], 480, 480, 64, "#2B2330", "hand", "Center")
        subprocess.run(im() + [str(note), str(txt), "-gravity", "NorthWest", "-geometry", "+40+40", "-composite",
                               "-background", "none", "-rotate", "-4", str(noted)], check=True)
        layers.append((noted, "NorthEast", 50, 70))
    elif layout == "tried":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', CREAM)}"]
        layers.append((text_box(tmp / "t.png", "What I tried:", 900, 90, 64, PURPLE, "head"), "NorthWest", 90, 80))
        y = 190
        for i, item in enumerate(ad.get("tried", [])[:5]):
            line = text_box(tmp / f"l{i}.png", item, 820, 70, 50, "#857A8A", "body")
            struck = tmp / f"ls{i}.png"
            trimmed = tmp / f"lt{i}.png"
            subprocess.run(im() + [str(line), "-trim", "+repage", str(trimmed)], check=True)
            mid = int(subprocess.run(identify() + ["-format", "%h", str(trimmed)],
                                     capture_output=True, text=True, check=True).stdout) // 2 + 2
            subprocess.run(im() + [str(trimmed), "-stroke", PINK, "-strokewidth", "6",
                                   "-draw", f"line 0,{mid} 2000,{mid}", str(struck)], check=True)
            layers.append((struck, "NorthWest", 110, y))
            y += 84
        layers.append((text_box(tmp / "w.png", ad["on_image"], 900, 140, 60, TEAL, "head"), "NorthWest", 90, y + 20))
        layers.append((photo(src, tmp / "p.png", 700, 1350 - y - 220), "South", 0, 50))
    else:
        raise ValueError(f"{ad['id']}: unknown layout {layout}")
    logo = ad.get("logo")
    if logo and (batch / logo).exists():
        layers.append((photo(batch / logo, tmp / "logo.png", 220, 60), "SouthEast", 30, 24))
    compose(base, layers, out)


def record(ad: dict, batch: Path, out: Path) -> None:
    lines = [f"# {ad['id']} ({ad.get('layout', 'poster')})", "",
             "Edited, not generated. No image model touched this still and no credits were spent.", "",
             "| Source | What it is | What was done |", "| --- | --- | --- |",
             f"| `{ad['photo']}` | product photo | resized and placed, not retouched |"]
    if ad.get("logo"):
        lines.append(f"| `{ad['logo']}` | logo | resized |")
    lines += ["", "## Every string on the image", ""]
    for key in ("on_image", "sub", "quote_by"):
        if ad.get(key):
            lines.append(f"* {key}: {ad[key]}")
    for item in ad.get("tried", []):
        lines.append(f"* tried: {item}")
    lines += ["", "## Ad copy", "", f"* Headline: {ad.get('headline', '')}", f"* Primary text: {ad.get('primary_text', '')}",
              f"* Description: {ad.get('description', '')}", f"* F.O.C.U.S.: {ad.get('focus', '')}",
              f"* Persona: {ad.get('persona', '')}", f"* Why it should win: {ad.get('why', '')}", ""]
    out.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    batch = Path(argv[0]).resolve()
    spec = json.loads((batch / "copy.json").read_text(encoding="utf-8"))
    final = batch / "final"
    final.mkdir(exist_ok=True)
    tmp = batch / ".build"
    tmp.mkdir(exist_ok=True)
    ids = [ad["id"] for ad in spec["ads"]]
    if len(ids) != len(set(ids)):
        sys.exit("every ad needs a unique id")
    built = []
    for ad in spec["ads"]:
        for field in ("on_image", "headline", "primary_text", "description"):
            for dash in ("-", "–", "—"):
                if dash in ad.get(field, "").replace("e-commerce", ""):
                    sys.exit(f"{ad['id']}: {field} has a dash. Rewrite it without one.")
        out = final / f"{ad['id']}.png"
        build(ad, batch, tmp, out)
        record(ad, batch, out)
        built.append(out)
        print(f"built {out.relative_to(batch)}")
    shutil.rmtree(tmp, ignore_errors=True)
    args = montage()
    for out in built:
        args += ["-label", out.stem, str(out)]
    subprocess.run(args + ["-tile", "4x", "-geometry", "400x500+10+10", "-background", "white",
                           str(batch / "sheet.jpg")], check=True)
    print(f"contact sheet: {batch / 'sheet.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
