"""pp03 Receipt: the hidden cost itemised on a till receipt, then the cheaper answer in bold."""

import random

NAME = "receipt"
FORMAT = "pp03"
FAMILY = "Handwritten and paper"
TITLE = "Store receipt"
WHEN = "Unspoken cost or Constraint. Make the money visible. Every price must be on the site today."
PHOTOS = ["cropped into a round plate"]
REQUIRED = {"title": "str", "receipt_head": "pair", "rows": "rows", "foot": "str", "footer": "str"}
OPTIONAL = {}
LIMITS = {"rows": 8}
COLORS = {"ground": "#2FBAD1", "paper": "#FCFBF7", "receipt_ink": "#222222", "receipt_grey": "#555555",
          "title_color": "white", "footer_color": "white"}


def row_styles(rows):
    """Rows before the first blank row are struck through, rows after it are bold. A third item overrides."""
    styles, after_blank = [], False
    for r in rows:
        if not r[0]:
            styles.append("blank")
            after_blank = True
        elif len(r) > 2:
            styles.append(r[2])
        else:
            styles.append("bold" if after_blank else "struck")
    return styles


def build(k, t):
    C, w = k.c, k.w
    ink, grey = C["receipt_ink"], C["receipt_grey"]
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=8)
    k.text(w("t.png"), t["title"], "head", 100, C["title_color"], interline=-10)
    k.comp(c, w("t.png"), 60, 50)
    rw, rh = 600, 760
    zig = " ".join(f"{x},{rh - (14 if (x // 20) % 2 else 0)}" for x in range(rw, -1, -20))
    k.m("-size", f"{rw}x{rh}", "xc:none", "-fill", C["paper"], "-draw", f"polygon 0,0 {rw},0 {zig}", w("rc.png"))
    k.text(w("rh.png"), t["receipt_head"][0], "monob", 34, ink, kern=2)
    k.comp(w("rc.png"), w("rh.png"), 0, 44, "North")
    k.text(w("rh2.png"), t["receipt_head"][1], "mono", 22, grey)
    k.comp(w("rc.png"), w("rh2.png"), 0, 96, "North")

    def dotted(yy):
        k.m(w("rc.png"), "-stroke", grey, "-strokewidth", 2, "-draw", f"stroke-dasharray 6 8 line 30,{yy} {rw - 30},{yy}",
            w("rc.png"))
    y = 140
    dotted(y)
    y += 30
    for (row, style) in zip(t["rows"], row_styles(t["rows"])):
        if style == "blank":
            dotted(y + 14)
            y += 46
            continue
        bold = style == "bold"
        kk, v = row[0], row[1]
        k.text(w("rk.png"), kk, "monob" if bold else "mono", 26, ink)
        k.comp(w("rc.png"), w("rk.png"), 32, y)
        if v:
            k.text(w("rv.png"), v, "monob" if bold else "mono", 26, C["pink"] if bold else ink)
            k.comp(w("rc.png"), w("rv.png"), 32, y, "NorthEast")
        if style == "struck":
            _, kh = k.size_of(w("rk.png"))
            k.m(w("rc.png"), "-stroke", ink, "-strokewidth", 3, "-draw", f"line 28,{y + kh // 2 + 2} {rw - 28},{y + kh // 2 + 2}",
                w("rc.png"))
        y += 54
    dotted(y + 6)
    y += 36
    k.text(w("rf.png"), t["foot"], "mono", 22, ink, width=520, gravity="Center")
    k.comp(w("rc.png"), w("rf.png"), 0, y, "North")
    _, fh = k.size_of(w("rf.png"))
    y += fh + 30
    rnd = random.Random(5)
    bars, x = [], 90
    while x < rw - 90:
        bw = rnd.choice([2, 2, 3, 5])
        bars += ["-draw", f"rectangle {x},{y} {x + bw},{y + 80}"]
        x += bw + rnd.choice([3, 4, 6])
    k.m(w("rc.png"), "-fill", ink, *bars, w("rc.png"))
    k.rotate(w("rc.png"), w("rcr.png"), 2)
    k.shadow(w("rcr.png"), w("rcs.png"), 50, 14, 0, 14)
    k.comp(c, w("rcs.png"), 30, 300, "NorthEast")
    pd = 330
    k.fill_crop(k.photo(0), w("pp.png"), pd, pd, "center")
    k.m("-size", f"{pd}x{pd}", "xc:none", "-fill", "white", "-draw", f"circle {pd // 2},{pd // 2} {pd // 2},1", w("pm.png"))
    k.m(w("pp.png"), w("pm.png"), "-compose", "CopyOpacity", "-composite", w("pp.png"))
    k.shadow(w("pp.png"), w("pps.png"), 40, 14, 0, 12)
    k.comp(c, w("pps.png"), 26, 820)
    k.text(w("fn.png"), t["footer"], "p6", 26, C["footer_color"])
    k.comp(c, w("fn.png"), 60, 1262)
    k.comp(c, k.logo_pill(220, w("lg.png")), 54, 1170)
    return c
