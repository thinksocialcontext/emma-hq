"""pp02 What I tried, crossed out: a lined notepad of failed fixes, the last line circled."""

NAME = "notepad"
FORMAT = "pp02"
FAMILY = "Handwritten and paper"
TITLE = "Notepad list, crossed out"
WHEN = "Frustration or Skepticism. The buyer has tried everything; name the failures, then the fix."
PHOTOS = ["cropped square, white border, tape, tilted"]
REQUIRED = {"title": "str", "kicker": "str", "crossed": "list", "final": "str", "footer": "str"}
OPTIONAL = {"photo_caption": "str"}
LIMITS = {"crossed": 6}
COLORS = {"ground": "#EDEAF7", "dots": "#D9D4EE", "pad": "white", "pad_lines": "#BFE6EF", "hand": "#3A3340"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=6)
    dots = []
    for gy in range(30, H, 60):
        for gx in range(30 if (gy // 60) % 2 else 60, W, 60):
            dots += ["-draw", f"circle {gx},{gy} {gx + 4},{gy}"]
    k.m(c, "-fill", C["dots"], *dots, c)
    k.text(w("t.png"), t["title"], "head", 96, C["purple"], interline=-10)
    k.comp(c, w("t.png"), 60, 50)
    pw, ph = 600, 760
    k.m("-size", f"{pw}x{ph}", f"xc:{C['pad']}", w("pad.png"))
    lines = []
    for y in range(190, ph - 20, 74):
        lines += ["-draw", f"line 0,{y} {pw},{y}"]
    k.m(w("pad.png"), "-stroke", C["pad_lines"], "-strokewidth", 2, *lines,
        "-stroke", C["pink"], "-strokewidth", 3, "-draw", f"line 78,0 78,{ph}",
        "-stroke", "none", "-fill", C["purple"], "-draw", f"rectangle 0,0 {pw},46", w("pad.png"))
    holes = []
    for x in range(60, pw, 70):
        holes += ["-draw", f"circle {x},23 {x + 8},23"]
    k.m(w("pad.png"), "-fill", C["ground"], *holes, w("pad.png"))
    k.text(w("k.png"), t["kicker"], "marker", 36, C["purple"])
    k.comp(w("pad.png"), w("k.png"), 100, 98)
    y = 190 + 74 - 60
    for item in t["crossed"]:
        k.text(w("it.png"), item, "marker", 40, C["hand"])
        iw, ih = k.size_of(w("it.png"))
        k.comp(w("pad.png"), w("it.png"), 104, y)
        sy = y + ih // 2 + 2
        k.m(w("pad.png"), "-stroke", C["pink"] + "B0", "-strokewidth", 4, "-draw",
            f"stroke-linecap round line 94,{sy + 4} {110 + iw},{sy - 6}", w("pad.png"))
        y += 74
    k.text(w("it.png"), t["final"], "marker", 40, C["teal"])
    k.comp(w("pad.png"), w("it.png"), 104, y - 4)
    iw, ih = k.size_of(w("it.png"))
    k.m(w("pad.png"), "-fill", "none", "-stroke", C["teal"], "-strokewidth", 5,
        "-draw", f"ellipse {104 + iw // 2},{y + ih // 2 - 4} {iw // 2 + 24},{ih // 2 + 16} 0,360", w("pad.png"))
    k.rotate(w("pad.png"), w("padr.png"), -2.5)
    k.shadow(w("padr.png"), w("pads.png"), 35, 14, 0, 12)
    k.comp(c, w("pads.png"), 36, 300)
    k.white_card(k.photo(0), w("ph.png"), 320, 320, 16)
    k.m(w("ph.png"), "-gravity", "South", "-background", "white", "-splice", "0x70", w("ph.png"))
    if t.get("photo_caption"):
        k.text(w("pc.png"), t["photo_caption"], "marker", 34, C["purple"])
        k.comp(w("ph.png"), w("pc.png"), 0, 18, "South")
    k.comp(w("ph.png"), k.tape(w("tp.png")), 0, 0, "North")
    k.rotate(w("ph.png"), w("phr.png"), 5)
    k.shadow(w("phr.png"), w("phs.png"), 40, 12, 0, 10)
    k.comp(c, w("phs.png"), 22, 640, "NorthEast")
    k.text(w("f.png"), t["footer"], "p6", 32, C["purple"])
    k.comp(c, w("f.png"), 60, 1254)
    k.comp(c, k.logo_pill(220, w("lg.png")), 50, 1170, "NorthEast")
    return c
