"""pr02 Giant quote poster: a real review in huge type on a brand colour, with a rounded photo."""

NAME = "quote_poster"
FORMAT = "pr02"
FAMILY = "Proof and review"
TITLE = "Giant quote poster"
WHEN = "Outcome or Skepticism, when one real review says it better than the brand could."
PHOTOS = ["cropped from the right, rounded white frame, tilted"]
REQUIRED = {"big": "str", "big2": "str", "attribution": "str", "footer": "str"}
OPTIONAL = {"photo_caption": "str", "photo_gravity": "str"}
LIMITS = {}
COLORS = {"ground": "#FD0082", "type": "white", "rule": "#2FBAD1", "quote_mark": "#FFFFFF55"}


def build(k, t):
    C, w = k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=6)
    k.text(w("qm.png"), "“", "head", 300, C["quote_mark"])
    k.comp(c, w("qm.png"), 40, 24)
    k.text(w("b1.png"), t["big"], "head", 70, C["type"], width=960, interline=-4)
    k.comp(c, w("b1.png"), 60, 140)
    _, b1h = k.size_of(w("b1.png"))
    k.text(w("b2.png"), t["big2"], "head", 128, C["type"], width=960, interline=-14)
    k.comp(c, w("b2.png"), 60, 140 + b1h + 24)
    _, b2h = k.size_of(w("b2.png"))
    y = 140 + b1h + 24 + b2h + 30
    k.m(c, "-fill", C["rule"], "-draw", f"rectangle 60,{y} 180,{y + 8}", c)
    k.text(w("at.png"), t["attribution"], "p5", 28, C["type"], width=520, interline=4)
    k.comp(c, w("at.png"), 60, y + 30)
    pw, ph = 430, 500
    k.fill_crop(k.photo(0), w("p.png"), pw, ph, t.get("photo_gravity", "East"))
    k.m("-size", f"{pw}x{ph}", "xc:none", "-fill", "white", "-draw", f"roundrectangle 0,0 {pw - 1},{ph - 1} 36,36",
        w("pm.png"))
    k.m(w("p.png"), w("pm.png"), "-compose", "CopyOpacity", "-composite", w("p.png"))
    k.m("-size", f"{pw + 24}x{ph + 80}", "xc:none", "-fill", "white", "-draw",
        f"roundrectangle 0,0 {pw + 23},{ph + 79} 46,46", w("pf.png"))
    k.comp(w("pf.png"), w("p.png"), 12, 12)
    if t.get("photo_caption"):
        k.text(w("pcap.png"), t["photo_caption"], "p5", 24, C["purple"])
        k.comp(w("pf.png"), w("pcap.png"), 0, 20, "South")
    k.rotate(w("pf.png"), w("pr.png"), 3)
    k.shadow(w("pr.png"), w("ps.png"), 45, 16, 0, 14)
    k.comp(c, w("ps.png"), 30, 60, "SouthEast")
    k.text(w("f.png"), t["footer"], "p7", 34, C["type"])
    k.comp(c, w("f.png"), 60, 1254)
    k.comp(c, k.logo_pill(220, w("lg.png")), 54, 1150)
    return c
