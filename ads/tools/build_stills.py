#!/usr/bin/env python3
"""Zero credit ad still builder for Emma HQ.

Builds 4:5 Meta stills (1080x1350 PNG) from real product photos, the real logo, fonts
and shapes drawn in code, with ImageMagick 6 or 7. No image model, no network, no
credits. Every string comes from the batch spec, so a batch rebuilds the same way.

  python3 ads/tools/build_stills.py ads/batches/2026-11-04            build every ad
  python3 ads/tools/build_stills.py ads/batches/2026-11-04 --check    validate only
  python3 ads/tools/build_stills.py ads/batches/2026-11-04 --only EE03 EE07
  python3 ads/tools/build_stills.py --layouts                         list the layouts

Reads <batch>/spec.json (or an older <batch>/copy.json). Writes <batch>/final/<file>.png,
a Markdown record beside each, and <batch>/sheet.jpg.

spec.json, in short (full guide: ads/docs/how-the-sample-ads-were-made.md):
{
  "batch": "2026-11-04",
  "status": "Not live, not posted.",
  "brand": {"logo": "assets/logo/logo.svg", "colors": {"pink": "#FD0082"}},
  "ads": [{
    "id": "EE01", "file": "EE01-tried-everything-notepad", "layout": "notepad",
    "focus": "F", "persona": "...", "link": "https://...",
    "photos": ["assets/photos/clear-posts.jpg"],
    "colors": {"ground": "#EDEAF7"},
    "on_image": {"title": "...", "kicker": "...", "crossed": ["..."], "final": "...", "footer": "..."},
    "headline": "...", "primary_text": "...", "description": "...", "why": "..."
  }]
}
Paths are tried relative to the batch folder, then ads/, then the repository root.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import imkit  # noqa: E402
from layouts import CLASSIC, LAYOUTS, classic  # noqa: E402

ADS = imkit.ADS
ROOT = ADS.parent
DASHES = ("-", "‐", "‑", "‒", "–", "—", "―", "−")
FOCUS = {"F": "Frustration", "O": "Outcome", "C": "Constraint", "U": "Unspoken cost", "S": "Skepticism"}
DEFAULT_LOGO = "assets/logo/logo.svg"


# reading -------------------------------------------------------------------
def load_spec(batch: Path) -> dict:
    for name in ("spec.json", "copy.json"):
        p = batch / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    sys.exit(f"no spec.json or copy.json in {batch}")


def resolve(batch: Path, rel: str) -> Path | None:
    for base in (batch, ADS, ROOT):
        p = (base / rel)
        if p.is_file():
            return p
    return None


def photo_list(ad: dict) -> list[dict]:
    """Photos as [{"path": ..., "what": ...}], from "photos" (list of str or dict) or a single "photo"."""
    raw = ad.get("photos") if "photos" in ad else ([ad["photo"]] if ad.get("photo") else [])
    return [p if isinstance(p, dict) else {"path": p} for p in raw]


def strings(v, out=None) -> list[str]:
    out = [] if out is None else out
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, list):
        for x in v:
            strings(x, out)
    elif isinstance(v, dict):
        for x in v.values():
            strings(x, out)
    return out


def on_image(ad: dict):
    """The strings drawn on the image. Classic layouts keep them as flat fields."""
    if ad.get("layout", "poster") in CLASSIC:
        return {k: ad[k] for k in ("on_image", "sub", "quote_by", "tried") if ad.get(k)}
    return ad.get("on_image", {})


def has_dash(s: str) -> bool:
    s = s.replace("e-commerce", "").replace("E-commerce", "")
    return any(d in s for d in DASHES)


# validating ----------------------------------------------------------------
def check_shape(ad_id, field, value, shape) -> list[str]:
    bad = f"{ad_id}: on_image.{field} must be "
    if shape == "str" and not (isinstance(value, str) and value.strip()):
        return [bad + "a non empty string"]
    if shape == "list" and not (isinstance(value, list) and value and all(isinstance(x, str) for x in value)):
        return [bad + "a list of strings"]
    if shape == "pair" and not (isinstance(value, list) and len(value) == 2 and all(isinstance(x, str) for x in value)):
        return [bad + "a list of two strings"]
    if shape in ("rows", "cards") and not (isinstance(value, list) and value and all(
            isinstance(r, list) and len(r) >= 2 and all(isinstance(x, str) for x in r) for r in value)):
        return [bad + "a list of [label, value] pairs"]
    return []


def validate(spec: dict, batch: Path) -> list[str]:
    errors = []
    ads = spec.get("ads")
    if not isinstance(ads, list) or not ads:
        return ["the spec needs an \"ads\" list with at least one ad"]
    ids = [a.get("id") for a in ads]
    if None in ids:
        errors.append("every ad needs an id")
    dupes = sorted({i for i in ids if i and ids.count(i) > 1})
    if dupes:
        errors.append(f"every ad needs a unique id, repeated: {', '.join(dupes)}")
    for ad in ads:
        aid = ad.get("id", "?")
        layout = ad.get("layout", "poster")
        mod = LAYOUTS.get(layout)
        meta = CLASSIC.get(layout)
        if not mod and not meta:
            errors.append(f"{aid}: unknown layout \"{layout}\". Known: {', '.join(sorted(LAYOUTS) + sorted(CLASSIC))}")
            continue
        required = mod.REQUIRED if mod else meta["REQUIRED"]
        slots = mod.PHOTOS if mod else meta["PHOTOS"]
        fields = on_image(ad)
        if mod and not isinstance(fields, dict):
            errors.append(f"{aid}: on_image must be an object of named fields for layout {layout}")
            continue
        for f, shape in required.items():
            if f not in fields:
                errors.append(f"{aid}: layout {layout} needs on_image.{f}")
            else:
                errors += check_shape(aid, f, fields[f], shape)
        if mod:
            for f, shape in mod.OPTIONAL.items():
                if f in fields:
                    errors += check_shape(aid, f, fields[f], shape)
            for f in fields:
                if f not in mod.REQUIRED and f not in mod.OPTIONAL:
                    errors.append(f"{aid}: layout {layout} has no field on_image.{f} (it would not render)")
            for f, n in mod.LIMITS.items():
                if isinstance(fields.get(f), list) and len(fields[f]) > n:
                    errors.append(f"{aid}: on_image.{f} has {len(fields[f])} items, layout {layout} fits {n}")
            if layout == "display_board" and isinstance(fields.get("cards"), list) and len(fields["cards"]) != 6:
                errors.append(f"{aid}: layout display_board needs exactly 6 cards")
        photos = photo_list(ad)
        if len(photos) < len(slots):
            errors.append(f"{aid}: layout {layout} needs {len(slots)} photo(s), the spec gives {len(photos)}")
        for p in photos:
            if not p.get("path") or not resolve(batch, p["path"]):
                errors.append(f"{aid}: photo not found: {p.get('path')} (run ads/tools/fetch_sources.py?)")
        for s in strings(fields):
            if has_dash(s):
                errors.append(f"{aid}: on image text has a dash: \"{s}\". Rewrite it without one.")
        for f in ("headline", "primary_text", "description"):
            if has_dash(ad.get(f, "") or ""):
                errors.append(f"{aid}: {f} has a dash. Rewrite it without one.")
        focus = str(ad.get("focus", "")).strip()
        if focus and focus[:1].upper() not in FOCUS:
            errors.append(f"{aid}: focus \"{focus}\" is not one of F, O, C, U, S")
    return errors


# building ------------------------------------------------------------------
def source_rows() -> dict[str, dict]:
    """sources.csv written by fetch_sources.py: file name to product and public URL."""
    rows = {}
    p = ADS / "assets" / "photos" / "sources.csv"
    if p.exists():
        with p.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows[Path(r.get("file", "")).name] = r
    return rows


def logo_for(spec: dict, ad: dict, batch: Path) -> Path | None:
    if ad.get("layout", "poster") in CLASSIC:
        return resolve(batch, ad["logo"]) if ad.get("logo") else None
    rel = ad.get("logo") or spec.get("brand", {}).get("logo") or DEFAULT_LOGO
    return resolve(batch, rel)


def build_one(spec: dict, ad: dict, batch: Path, out: Path) -> None:
    layout = ad.get("layout", "poster")
    photos = [resolve(batch, p["path"]) for p in photo_list(ad)]
    colors = {**spec.get("brand", {}).get("colors", {})}
    if layout in LAYOUTS:
        colors.update(LAYOUTS[layout].COLORS)
    colors.update(ad.get("colors", {}))
    k = imkit.Kit(batch / ".build" / ad["id"], colors, photos, logo_for(spec, ad, batch), seed=ad.get("seed", 1))
    canvas = LAYOUTS[layout].build(k, ad["on_image"]) if layout in LAYOUTS else classic.build(k, ad)
    k.m(canvas, "-resize", f"{imkit.W}x{imkit.H}!", "-strip", "-define", "png:compression-level=9", str(out))


def record(spec: dict, ad: dict, batch: Path, out: Path, srcs: dict) -> None:
    layout = ad.get("layout", "poster")
    mod = LAYOUTS.get(layout)
    slots = mod.PHOTOS if mod else CLASSIC[layout]["PHOTOS"]
    focus = str(ad.get("focus", "")).strip()
    letter = focus[:1].upper()
    md = [f"# {ad['id']} {ad.get('headline') or ''}".rstrip(), "",
          "Edited, not generated. No image model touched this still and no credits were spent.", ""]
    if spec.get("status"):
        md += [spec["status"], ""]
    md += [f"* Layout: {layout}" + (f" ({mod.TITLE}, format {mod.FORMAT})" if mod else ""),
           f"* Persona: {ad.get('persona', '')}",
           f"* F.O.C.U.S.: {letter} ({FOCUS.get(letter, focus)})" if focus else "* F.O.C.U.S.: ",
           f"* Link: {ad.get('link', '')}", "",
           "## Sources", "", "| path | what it is | what was done | public URL |", "|---|---|---|---|"]
    for i, p in enumerate(photo_list(ad)):
        row = srcs.get(Path(p["path"]).name, {})
        done = slots[i] if i < len(slots) else "placed"
        md.append(f"| {p['path']} | {p.get('what') or row.get('product', '')} | {done} | {row.get('url', '')} |")
    lp = logo_for(spec, ad, batch)
    if lp:
        row = srcs.get(lp.name, {})
        shown = lp.relative_to(ADS) if ADS in lp.parents else lp.name
        md.append(f"| {shown} | {row.get('product') or 'logo'} | rendered from the file, colours unchanged, "
                  f"on a white pill where the ground is dark | {row.get('url', '')} |")
    md += ["", "## Ground and fonts", "",
           "Grounds, paper, shapes, stamps, arrows and textures are drawn in code by ads/tools/layouts/"
           f"{layout if mod else 'classic'}.py. Fonts: Fjalla One (headings) and Poppins (body), the fonts on "
           "earringsbyemma.com; Permanent Marker for handwriting and chalk; Liberation Mono or Cousine for receipts "
           "and labels.", "", "## Every string that renders", ""]
    md += [f"* {s}".replace("\n", " / ") for s in strings(on_image(ad))]
    md += ["", "## Ad copy", "", f"* Headline: {ad.get('headline', '')}", f"* Primary text: {ad.get('primary_text', '')}",
           f"* Description: {ad.get('description', '')}", f"* Why: {ad.get('why', '')}", ""]
    out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")


def contact_sheet(batch: Path, built: list[Path]) -> Path:
    sheet = batch / "sheet.jpg"
    args = imkit.im_cmd("montage")
    for p in built:
        args += ["-label", p.stem, str(p)]
    r = subprocess.run(args + ["-tile", "4x", "-geometry", "400x500+10+10", "-background", "white", str(sheet)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"montage failed: {r.stderr.strip()}")
    return sheet


def list_layouts() -> None:
    for name, mod in LAYOUTS.items():
        opt = f" (optional {', '.join(mod.OPTIONAL)})" if mod.OPTIONAL else ""
        print(f"{name:14} {mod.FORMAT}  {mod.TITLE}. Photos: {len(mod.PHOTOS)}. Fields: {', '.join(mod.REQUIRED)}{opt}")
        print(f"{'':20}{mod.WHEN}")
    print("classic: " + ", ".join(CLASSIC) + " (one photo, flat fields, kept from the first kit)")


def main(argv: list[str]) -> int:
    if "--layouts" in argv:
        list_layouts()
        return 0
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    batch = Path(args[0]).resolve()
    only = args[1:] if "--only" in argv else []
    spec = load_spec(batch)
    errors = validate(spec, batch)
    if errors:
        print("The spec has problems, nothing was built:", file=sys.stderr)
        for e in errors:
            print(f"  * {e}", file=sys.stderr)
        return 1
    print(f"spec ok: {len(spec['ads'])} ads, ImageMagick {imkit.im_version()}")
    if "--check" in argv:
        return 0
    final = batch / "final"
    final.mkdir(exist_ok=True)
    srcs = source_rows()
    built = []
    for ad in spec["ads"]:
        out = final / f"{ad.get('file') or ad['id']}.png"
        if only and ad["id"] not in only:
            if out.exists():
                built.append(out)
            continue
        build_one(spec, ad, batch, out)
        record(spec, ad, batch, out, srcs)
        built.append(out)
        print(f"built {out.relative_to(batch)}")
    if "--keep-work" not in argv:
        shutil.rmtree(batch / ".build", ignore_errors=True)
    print(f"contact sheet: {contact_sheet(batch, built)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
