"""pp11 Annotated photo: one product print with handwritten notes, marker arrows and a price sticker."""

NAME = "annotated"
FORMAT = "pp11"
FAMILY = "Handwritten and paper"
TITLE = "Annotated photo with marker arrows"
WHEN = "Unspoken cost, Constraint or Skepticism, when the product needs two or three features pointed out."
PHOTOS = ["cropped square, white border, tilted"]
REQUIRED = {"title": "str", "sub": "str", "notes": "list", "quote": "str", "quote_by": "str", "footer": "str"}
OPTIONAL = {}
LIMITS = {"notes": 3}
COLORS = {"ground": "#FFE6F3", "note_color": "#5E106B", "sticker": "#FD0082", "quote_bar": "#2FBAD1"}


def build(k, t):
    C, w = k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=6)
    k.text(w("t.png"), t["title"], "head", 80, C["purple"], interline=-8)
    k.comp(c, w("t.png"), 60, 46)
    _, th = k.size_of(w("t.png"))
    k.text(w("s.png"), t["sub"], "head", 80, C["pink"])
    k.comp(c, w("s.png"), 60, 46 + th + 6)
    k.white_card(k.photo(0), w("p.png"), 600, 600, 18)
    k.rotate(w("p.png"), w("pr.png"), -2)
    k.shadow(w("pr.png"), w("ps.png"), 35, 14, 0, 12)
    k.comp(c, w("ps.png"), 230, 320)
    n = list(t["notes"]) + [""] * (3 - len(t["notes"]))
    if n[0]:
        k.text(w("n1.png"), n[0], "marker", 42, C["note_color"], interline=-6)
        k.comp(c, w("n1.png"), 40, 380)
        k.marker_arrow(c, [(150, 500), (230, 560), (330, 520)], C["note_color"])
    if n[1]:
        k.text(w("n2.png"), n[1], "marker", 42, C["note_color"], interline=-6)
        k.comp(c, w("n2.png"), 40, 990)
        k.marker_arrow(c, [(210, 980), (330, 820), (560, 640)], C["note_color"])
    if n[2]:
        s = 210
        k.m("-size", f"{s}x{s}", "xc:none", "-fill", C["sticker"], "-draw", f"circle {s // 2},{s // 2} {s // 2},2", w("ps2.png"))
        k.text(w("pt.png"), n[2], "head", 46, "white", width=170, gravity="Center", interline=-6)
        k.comp(w("ps2.png"), w("pt.png"), 0, 0, "center")
        k.rotate(w("ps2.png"), w("ps2r.png"), 10)
        k.shadow(w("ps2r.png"), w("ps2s.png"), 40, 8, 0, 8)
        k.comp(c, w("ps2s.png"), 40, 360, "NorthEast")
    k.text(w("q.png"), t["quote"], "p5", 28, C["ink"], width=500, interline=4)
    qw, qh = k.size_of(w("q.png"))
    k.text(w("qb.png"), t["quote_by"], "p6", 22, C["purple"])
    k.m("-size", f"{qw + 60}x{qh + 90}", "xc:white", w("qc.png"))
    k.comp(w("qc.png"), w("q.png"), 30, 26)
    k.comp(w("qc.png"), w("qb.png"), 30, 26, "SouthWest")
    k.m(w("qc.png"), "-fill", C["quote_bar"], "-draw", f"rectangle 0,0 8,{qh + 90}", w("qc.png"))
    k.shadow(w("qc.png"), w("qcs.png"), 30, 10, 0, 8)
    k.comp(c, w("qcs.png"), 40, 70, "SouthEast")
    k.text(w("f.png"), t["footer"], "p7", 27, C["purple"])
    k.comp(c, w("f.png"), 60, 1180)
    k.comp(c, k.logo_pill(200, w("lg.png")), 54, 1240)
    return c
