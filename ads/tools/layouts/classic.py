"""The four simple layouts from the first kit: poster, review, note, tried.

They take flat fields on the ad (one photo, "on_image" as a string, plus "sub", "quote_by",
"tried", "bg", "ink") so an older copy.json still builds. New batches should use the ten
catalogue layouts in this folder.
"""

import math

W, H = 1080, 1350
NOTE = "#FFF2A8"
CREAM = "#FFF8F2"
FONT_ROLE = {"head": "head", "body": "p4", "bold": "p7", "hand": "marker"}


def text_box(k, out, text, width, height, size, color, kind="body", gravity="NorthWest"):
    k.m("-background", "none", "-fill", color, *k.font(FONT_ROLE[kind]), "-pointsize", size,
        "-size", f"{width}x{height}", "-gravity", gravity, f"caption:{text}", out)
    return out


def stars(k, out, count=5, size=64, color="#F5B301"):
    """Five drawn stars, so no font needs a star glyph."""
    gap = 14
    draws = []
    for n in range(count):
        cx, cy, r_out, r_in = n * (size + gap) + size / 2, size / 2, size / 2, size / 5
        pts = []
        for j in range(10):
            r = r_out if j % 2 == 0 else r_in
            a = math.pi / 2 + j * math.pi / 5
            pts.append(f"{cx + r * math.cos(a):.1f},{cy - r * math.sin(a):.1f}")
        draws += ["-draw", "polygon " + " ".join(pts)]
    k.m("-size", f"{count * (size + gap) - gap}x{size}", "xc:none", "-fill", color, *draws, out)
    return out


def photo(k, src, out, width, height, cover=False):
    args = [src, "-resize", f"{width}x{height}^" if cover else f"{width}x{height}"]
    if cover:
        args += ["-gravity", "center", "-extent", f"{width}x{height}"]
    k.m(*args, out)
    return out


def compose(k, base, layers, out):
    args = list(base)
    for path, gravity, x, y in layers:
        args += [path, "-gravity", gravity, "-geometry", f"+{x}+{y}", "-composite"]
    k.m(*args, out)
    return out


def build(k, ad):
    C, w = k.c, k.w
    layout = ad.get("layout", "poster")
    src = k.photo(0)
    layers = []
    if layout == "poster":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', CREAM)}"]
        layers.append((text_box(k, w("h.png"), ad["on_image"], 940, 420, 104, ad.get("ink", C["purple"]), "head", "North"),
                       "North", 0, 90))
        layers.append((photo(k, src, w("p.png"), 820, 640), "South", 0, 170))
        if ad.get("sub"):
            layers.append((text_box(k, w("s.png"), ad["sub"], 940, 80, 40, C["pink"], "bold", "South"), "South", 0, 70))
    elif layout == "review":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', C['pink'])}"]
        k.m("-size", "940x620", "xc:none", "-fill", "white", "-draw", "roundrectangle 0,0 939,619 36,36", w("card.png"))
        layers.append((w("card.png"), "North", 0, 70))
        layers.append((stars(k, w("st.png")), "North", 0, 110))
        layers.append((text_box(k, w("q.png"), f"“{ad['on_image']}”", 840, 380, 50, C["purple"], "bold", "Center"),
                       "North", 0, 190))
        if ad.get("quote_by"):
            layers.append((text_box(k, w("by.png"), ad["quote_by"], 840, 60, 34, "#857A8A", "body", "North"),
                           "North", 0, 590))
        layers.append((photo(k, src, w("p.png"), 760, 560), "South", 0, 50))
    elif layout == "note":
        base = [photo(k, src, w("bg.png"), W, H, cover=True)]
        k.m("-size", "560x560", f"xc:{NOTE}", "(", "+clone", "-background", "#00000066", "-shadow", "60x12+10+14", ")",
            "+swap", "-background", "none", "-layers", "merge", "+repage", w("note.png"))
        txt = text_box(k, w("nt.png"), ad["on_image"], 480, 480, 64, "#2B2330", "hand", "Center")
        k.m(w("note.png"), txt, "-gravity", "NorthWest", "-geometry", "+40+40", "-composite",
            "-background", "none", "-rotate", "-4", w("noted.png"))
        layers.append((w("noted.png"), "NorthEast", 50, 70))
    elif layout == "tried":
        base = ["-size", f"{W}x{H}", f"xc:{ad.get('bg', CREAM)}"]
        layers.append((text_box(k, w("t.png"), "What I tried:", 900, 90, 64, C["purple"], "head"), "NorthWest", 90, 80))
        y = 190
        for i, item in enumerate(ad.get("tried", [])[:5]):
            line = text_box(k, w(f"l{i}.png"), item, 820, 70, 50, "#857A8A", "body")
            k.m(line, "-trim", "+repage", w(f"lt{i}.png"))
            mid = k.size_of(w(f"lt{i}.png"))[1] // 2 + 2
            k.m(w(f"lt{i}.png"), "-stroke", C["pink"], "-strokewidth", "6", "-draw", f"line 0,{mid} 2000,{mid}",
                w(f"ls{i}.png"))
            layers.append((w(f"ls{i}.png"), "NorthWest", 110, y))
            y += 84
        layers.append((text_box(k, w("wk.png"), ad["on_image"], 900, 140, 60, C["teal"], "head"), "NorthWest", 90, y + 20))
        layers.append((photo(k, src, w("p.png"), 700, 1350 - y - 220), "South", 0, 50))
    else:
        raise ValueError(f"{ad['id']}: unknown layout {layout}")
    if k.logo_path:
        layers.append((photo(k, str(k.logo_path), w("logo.png"), 220, 60), "SouthEast", 30, 24))
    return compose(k, base, layers, w("canvas.png"))


def _meta(name, title, when, required):
    return {"NAME": name, "FORMAT": "", "FAMILY": "classic", "TITLE": title, "WHEN": when,
            "PHOTOS": ["resized and placed, not retouched"], "REQUIRED": required}


LAYOUTS = {
    "poster": _meta("poster", "Big type over a cutout", "Any letter; the simplest still.", {"on_image": "str"}),
    "review": _meta("review", "Review card with stars", "Skepticism or Outcome with a real review.", {"on_image": "str"}),
    "note": _meta("note", "Sticky note on a full bleed photo", "Constraint or Unspoken cost.", {"on_image": "str"}),
    "tried": _meta("tried", "What I tried, simple list", "Skepticism or Frustration.", {"on_image": "str", "tried": "list"}),
}
