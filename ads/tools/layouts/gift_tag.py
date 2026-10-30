"""pp05 Gift tag: a big tag on kraft paper with a ribbon, two product prints tucked behind."""

import random

NAME = "gift_tag"
FORMAT = "pp05"
FAMILY = "Handwritten and paper"
TITLE = "Kraft gift tag"
WHEN = "Constraint for gift buyers, or seasonal Outcome. Gift cards, holidays, birthdays."
PHOTOS = ["cropped square, white border, tilted", "cropped square, white border, tilted"]
REQUIRED = {"kicker": "str", "title": "str", "sub": "str", "footer": "str"}
OPTIONAL = {}
LIMITS = {}
COLORS = {"ground": "#C49A6C", "fibres": "#6B4A2A40", "ribbon": "#FD0082", "tag": "#FFFBF4", "tag_line": "#8B85C1",
          "string": "#F4E6D2", "band": "#5E106B"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=16)
    rnd = random.Random(8)
    fib = []
    for _ in range(260):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        fib += ["-draw", f"line {x},{y} {x + rnd.randint(-30, 30)},{y + rnd.randint(-6, 6)}"]
    k.m(c, "-stroke", C["fibres"], "-strokewidth", 1, *fib, c)
    k.m(c, "-fill", C["ribbon"], "-draw", f"polygon 0,140 {W},60 {W},120 0,200", c)
    k.white_card(k.photo(0), w("gc.png"), 330, 330, 14)
    k.rotate(w("gc.png"), w("gcr.png"), 8)
    k.shadow(w("gcr.png"), w("gcs.png"), 45, 14, 0, 12)
    k.comp(c, w("gcs.png"), 30, 760, "NorthEast")
    k.white_card(k.photo(1), w("mc.png"), 250, 250, 12)
    k.rotate(w("mc.png"), w("mcr.png"), -7)
    k.shadow(w("mcr.png"), w("mcs.png"), 45, 12, 0, 10)
    k.comp(c, w("mcs.png"), 80, 560, "NorthEast")
    tw, th = 640, 900
    k.m("-size", f"{tw}x{th}", "xc:none", "-fill", C["tag"],
        "-draw", f"polygon 110,0 {tw - 110},0 {tw},110 {tw},{th} 0,{th} 0,110",
        "-fill", "none", "-stroke", C["tag_line"], "-strokewidth", 3,
        "-draw", f"polygon 120,18 {tw - 120},18 {tw - 18},120 {tw - 18},{th - 18} 18,{th - 18} 18,120",
        "-stroke", "none", "-fill", C["ground"], "-draw", f"circle {tw // 2},72 {tw // 2 + 24},72", w("tag.png"))
    k.text(w("k.png"), t["kicker"], "p6", 34, C["purple"], width=540, gravity="Center")
    k.comp(w("tag.png"), w("k.png"), 0, 160, "North")
    k.text(w("tt.png"), t["title"], "head", 140, C["pink"], width=580, gravity="Center", interline=-20)
    k.comp(w("tag.png"), w("tt.png"), 0, 260, "North")
    _, tth = k.size_of(w("tt.png"))
    yl = 260 + tth + 40
    k.m(w("tag.png"), "-stroke", C["tag_line"], "-strokewidth", 3, "-draw", f"line 170,{yl} {tw - 170},{yl}", w("tag.png"))
    k.text(w("s.png"), t["sub"], "p5", 32, C["ink"], width=540, gravity="Center", interline=6)
    k.comp(w("tag.png"), w("s.png"), 0, yl + 34, "North")
    k.comp(w("tag.png"), k.logo(250, w("lg.png")), 0, 70, "South")
    k.rotate(w("tag.png"), w("tagr.png"), -4)
    k.shadow(w("tagr.png"), w("tags.png"), 45, 16, 0, 16)
    k.comp(c, w("tags.png"), 40, 200)
    k.m(c, "-fill", "none", "-stroke", C["string"], "-strokewidth", 5,
        "-draw", "path 'M 360,262 C 360,220 370,180 380,150'", c)
    k.m(c, "-fill", C["band"], "-draw", f"rectangle 0,{H - 120} {W},{H}", c)
    k.text(w("f.png"), t["footer"], "p6", 32, "white")
    k.comp(c, w("f.png"), 0, 42, "South")
    return c
