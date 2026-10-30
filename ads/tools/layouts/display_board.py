"""cd04 Variant grid: six product display cards hung on a pegboard, with an offer pill."""

NAME = "display_board"
FORMAT = "cd04"
FAMILY = "Comparison and data"
TITLE = "Display card board"
WHEN = "Outcome for collectors, or a live bundle offer. Shows range, sells the second and third pair."
PHOTOS = ["cropped onto a display card"] * 6
REQUIRED = {"title": "str", "cards": "cards", "offer": "str", "offer2": "str", "footer": "str"}
OPTIONAL = {}
LIMITS = {"cards": 6}
COLORS = {"ground": "#5E106B", "holes": "#4A0C55", "card": "white", "footer_color": "#E7DDF0", "offer_bg": "#FD0082"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=8)
    holes = []
    for gy in range(24, H, 48):
        for gx in range(24, W, 48):
            holes += ["-draw", f"circle {gx},{gy} {gx + 4},{gy}"]
    k.m(c, "-fill", C["holes"], *holes, c)
    k.text(w("t.png"), t["title"], "head", 104, "white")
    k.comp(c, w("t.png"), 0, 50, "North")
    cw, ch = 300, 430
    pos = [(60, 200), (390, 210), (720, 200), (60, 650), (390, 660), (720, 650)]
    rots = [-2, 1.5, -1, 1.5, -1.5, 2]
    for i, (nm, pr) in enumerate(t["cards"]):
        k.m("-size", f"{cw}x{ch}", f"xc:{C['card']}", w("card.png"))
        k.m(w("card.png"), "-fill", C["purple"], "-draw", f"roundrectangle {cw // 2 - 34},16 {cw // 2 + 34},30 7,7", w("card.png"))
        k.fill_crop(k.photo(i), w("ci.png"), 260, 250, "center")
        k.comp(w("card.png"), w("ci.png"), 0, 40, "North")
        k.text(w("cn.png"), nm, "p6", 24, C["ink"], width=270, gravity="Center")
        k.comp(w("card.png"), w("cn.png"), 0, 300, "North")
        k.text(w("cp.png"), pr, "head", 34, C["pink"])
        k.comp(w("card.png"), w("cp.png"), 0, 16, "South")
        k.rotate(w("card.png"), w("cardr.png"), rots[i])
        k.shadow(w("cardr.png"), w("cards.png"), 45, 10, 0, 10)
        k.comp(c, w("cards.png"), pos[i][0] - 10, pos[i][1] - 10)
    k.text(w("o1.png"), t["offer"], "head", 60, "white")
    k.text(w("o2.png"), t["offer2"], "p6", 30, "white")
    o1w, o1h = k.size_of(w("o1.png"))
    o2w, o2h = k.size_of(w("o2.png"))
    bw, bh = max(o1w, o2w) + 100, o1h + o2h + 60
    k.m("-size", f"{bw}x{bh}", "xc:none", "-fill", C["offer_bg"], "-draw", f"roundrectangle 0,0 {bw - 1},{bh - 1} 30,30",
        w("ob.png"))
    k.comp(w("ob.png"), w("o1.png"), 0, 24, "North")
    k.comp(w("ob.png"), w("o2.png"), 0, 24 + o1h + 12, "North")
    k.shadow(w("ob.png"), w("obs.png"), 50, 10, 0, 8)
    k.comp(c, w("obs.png"), 50, 1112)
    k.text(w("f.png"), t["footer"], "p5", 26, C["footer_color"])
    k.comp(c, w("f.png"), 64, 70, "SouthEast")
    k.comp(c, k.logo_pill(220, w("lg.png")), 54, 1150, "NorthEast")
    return c
