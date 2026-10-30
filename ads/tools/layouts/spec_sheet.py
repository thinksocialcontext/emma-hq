"""cd03 Spec sheet: a technical data sheet on grid paper, a framed figure, a quote and a table of facts."""

NAME = "spec_sheet"
FORMAT = "cd03"
FAMILY = "Comparison and data"
TITLE = "Material spec sheet"
WHEN = "Skepticism about quality or materials. Answer with the site's own facts, one per row."
PHOTOS = ["cropped square, thin frame"]
REQUIRED = {"kicker": "str", "title": "str", "rows": "rows", "figure": "str", "quote": "str", "quote_by": "str",
            "footer": "str"}
OPTIONAL = {}
LIMITS = {"rows": 6}
COLORS = {"ground": "white", "grid": "#2FBAD126", "row_tint": "#EAF8FB", "quote_bg": "#FFE6F3"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=4)
    g = []
    for x in range(0, W, 40):
        g += ["-draw", f"line {x},0 {x},{H}"]
    for y in range(0, H, 40):
        g += ["-draw", f"line 0,{y} {W},{y}"]
    k.m(c, "-stroke", C["grid"], "-strokewidth", 1, *g, c)
    k.m(c, "-fill", C["ground"], "-draw", "rectangle 40,30 1040,320", "-draw", "rectangle 40,800 1040,1320", c)
    k.text(w("k.png"), t["kicker"], "monob", 26, C["teal"], kern=6)
    k.comp(c, w("k.png"), 60, 60)
    k.m(c, "-stroke", C["purple"], "-strokewidth", 3, "-draw", "line 60,104 1020,104", c)
    k.text(w("t.png"), t["title"], "head", 96, C["purple"], interline=-10)
    k.comp(c, w("t.png"), 60, 122)
    k.fill_crop(k.photo(0), w("p.png"), 430, 430, "center")
    k.m(w("p.png"), "-bordercolor", C["purple"], "-border", 3, w("p.png"))
    k.comp(c, w("p.png"), 60, 340)
    k.text(w("fig.png"), t["figure"], "mono", 23, C["purple"])
    k.m(c, "-fill", C["ground"], "-draw", "rectangle 40,778 1040,826", c)
    k.comp(c, w("fig.png"), 60, 788)
    k.m(c, "-fill", C["quote_bg"], "-draw", "roundrectangle 530,340 1020,776 24,24", c)
    k.text(w("qm.png"), "“", "head", 160, C["pink"])
    k.comp(c, w("qm.png"), 556, 340)
    k.text(w("q.png"), t["quote"], "p6", 34, C["ink"], width=430, interline=6)
    k.comp(c, w("q.png"), 560, 470)
    _, qh = k.size_of(w("q.png"))
    k.text(w("qb.png"), t["quote_by"], "p5", 24, C["purple"])
    k.comp(c, w("qb.png"), 560, 490 + qh)
    y = 830
    for i, row in enumerate(t["rows"]):
        kk, v = row[0], row[1]
        if i % 2 == 0:
            k.m(c, "-fill", C["row_tint"], "-draw", f"rectangle 60,{y} 1020,{y + 56}", c)
        k.text(w("rk.png"), kk, "monob", 22, C["purple"], kern=2)
        k.comp(c, w("rk.png"), 80, y + 17)
        k.text(w("rv.png"), v, "p5", 28, C["ink"])
        k.comp(c, w("rv.png"), 380, y + 11)
        y += 56
    k.m(c, "-stroke", C["purple"], "-strokewidth", 3, "-draw", f"line 60,{y + 6} 1020,{y + 6}", c)
    k.text(w("f.png"), t["footer"], "p7", 32, C["pink"])
    k.comp(c, w("f.png"), 60, 1250)
    k.comp(c, k.logo(230, w("lg.png")), 60, 1252, "NorthEast")
    return c
