"""pp09 Chalkboard: chalk lettering on a slate in a wooden frame, a pinned print and a product card."""

import random

NAME = "chalkboard"
FORMAT = "pp09"
FAMILY = "Handwritten and paper"
TITLE = "Chalkboard"
WHEN = "Frustration for teachers and school themes. Calls out the persona before a word is read."
PHOTOS = ["cropped into a pinned print", "cropped square, white border, tilted"]
REQUIRED = {"title": "str", "sub": "str", "quote": "str", "quote_by": "str", "footer": "str"}
OPTIONAL = {"photo_caption": "str"}
LIMITS = {}
COLORS = {"frame": "#9A6B3E", "board": "#26332D", "tray": "#7A512C", "chalk": "#F4F4EE", "chalk_blue": "#9EE3F0",
          "chalk_pink": "#FFD1E9", "chalk_grey": "#E6E6DD", "underline": "#FD0082"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["frame"], amt=20)
    k.m(c, "-motion-blur", "0x12+0", c)
    bw, bh = W - 60, H - 150
    k.m("-size", f"{bw}x{bh}", f"xc:{C['board']}", "-seed", k.seed, "-attenuate", "0.35", "+noise", "Gaussian",
        "-blur", "0x1", w("b.png"))
    rnd = random.Random(9)
    sm = []
    for _ in range(30):
        x, y = rnd.randint(0, bw), rnd.randint(0, bh)
        sm += ["-draw", f"ellipse {x},{y} {rnd.randint(60, 200)},{rnd.randint(10, 40)} 0,360"]
    k.m(w("b.png"), "(", "-size", f"{bw}x{bh}", "xc:none", "-fill", "#FFFFFF10", *sm, "-blur", "0x14", ")", "-composite",
        w("b.png"))
    k.comp(c, w("b.png"), 30, 30)
    k.m(c, "-fill", C["tray"], "-draw", f"rectangle 0,{H - 120} {W},{H - 96}", c)

    def chalk(out, s, font, size, color, width=None, interline=0):
        k.text(out, s, font, size, color, width=width, interline=interline)
        return k.rough(out, 0.4)
    chalk(w("t.png"), t["title"], "head", 150, C["chalk"], interline=-18)
    k.comp(c, w("t.png"), 80, 80)
    _, th = k.size_of(w("t.png"))
    k.m(c, "-stroke", C["underline"], "-strokewidth", 8, "-draw", f"stroke-linecap round line 84,{100 + th} 470,{94 + th}", c)
    chalk(w("s.png"), t["sub"], "marker", 50, C["chalk_blue"], interline=4)
    k.comp(c, w("s.png"), 80, 140 + th)
    _, sh = k.size_of(w("s.png"))
    chalk(w("q.png"), t["quote"], "marker", 40, C["chalk_pink"], width=480, interline=2)
    k.comp(c, w("q.png"), 80, 220 + th + sh)
    _, qh = k.size_of(w("q.png"))
    chalk(w("qb.png"), t["quote_by"], "p5", 24, C["chalk_grey"])
    k.comp(c, w("qb.png"), 80, 240 + th + sh + qh)
    k.fill_crop(k.photo(0), w("p.png"), 400, 440, "center")
    k.m(w("p.png"), "-bordercolor", "white", "-border", 16, "-gravity", "South", "-background", "white", "-splice", "0x60",
        w("p.png"))
    if t.get("photo_caption"):
        k.text(w("pcap.png"), t["photo_caption"], "p5", 22, "#4A4450")
        k.comp(w("p.png"), w("pcap.png"), 0, 20, "South")
    pw_, _ = k.size_of(w("p.png"))
    k.m(w("p.png"), "-fill", C["pink"], "-draw", f"circle {pw_ // 2},14 {pw_ // 2 + 12},14", w("p.png"))
    k.rotate(w("p.png"), w("pr.png"), 5)
    k.shadow(w("pr.png"), w("ps.png"), 55, 14, 0, 12)
    k.comp(c, w("ps.png"), 60, 600, "NorthEast")
    k.white_card(k.photo(1), w("pc.png"), 220, 220, 10)
    k.rotate(w("pc.png"), w("pcr.png"), -6)
    k.shadow(w("pcr.png"), w("pcs.png"), 50, 10, 0, 8)
    k.comp(c, w("pcs.png"), 80, 930)
    k.text(w("f.png"), t["footer"], "p6", 30, "white")
    k.comp(c, w("f.png"), 60, 1266)
    k.comp(c, k.logo_pill(200, w("lg.png")), 50, 1250, "NorthEast")
    return c
