"""pp08 Composition notebook: a marbled cover, a lined page with ticked lines, a sticky note quote and a taped photo."""

NAME = "notebook"
FORMAT = "pp08"
FAMILY = "Handwritten and paper"
TITLE = "School notebook with taped photo"
WHEN = "Constraint, for parents and back to school. Keep any safety line from the site on the page."
PHOTOS = ["cropped, white print border, tape", "cropped square, white border, tilted"]
REQUIRED = {"title": "str", "lines": "list", "quote": "str", "quote_by": "str", "note": "str", "footer": "str"}
OPTIONAL = {"photo_caption": "str"}
LIMITS = {"lines": 3}
COLORS = {"page": "#FFFEF8", "page_lines": "#9FD9E6", "sticky": "#FFC3E2", "hand": "#2F2A36",
          "marble_dark": "#141414", "marble_light": "#F2F2F2"}


def build(k, t):
    W, H, C, w = 1080, 1350, k.c, k.w
    c = w("canvas.png")
    k.m("-size", f"{W}x{H}", "xc:white", "-seed", k.seed, "+noise", "Random", "-channel", "G", "-separate", "+channel",
        "-blur", "0x3", "-threshold", "52%", "-morphology", "Open", "Disk:2", "-negate", c)
    k.m(c, "-fill", C["marble_dark"], "-opaque", "white", "-fill", C["marble_light"], "-opaque", "black", c)
    px, py, pw, ph = 50, 40, 980, 1200
    k.m("-size", f"{pw}x{ph}", f"xc:{C['page']}", w("pg.png"))
    ln = []
    for y in range(330, ph, 62):
        ln += ["-draw", f"line 0,{y} {pw},{y}"]
    k.m(w("pg.png"), "-stroke", C["page_lines"], "-strokewidth", 2, *ln, "-stroke", C["pink"], "-strokewidth", 3,
        "-draw", f"line 96,0 96,{ph}", w("pg.png"))
    k.text(w("t.png"), t["title"], "head", 82, C["purple"], interline=-6)
    k.comp(w("pg.png"), w("t.png"), 126, 70)
    y = 330 - 52
    for line in t["lines"]:
        k.m(w("pg.png"), "-fill", "none", "-stroke", C["teal"], "-strokewidth", 5,
            "-draw", f"stroke-linecap round stroke-linejoin round polyline 126,{y + 30} 140,{y + 46} 168,{y + 12}",
            w("pg.png"))
        k.text(w("l.png"), line, "marker", 34, C["hand"])
        k.comp(w("pg.png"), w("l.png"), 186, y + 6)
        y += 124
    sw_, sh_ = 420, 315
    k.m("-size", f"{sw_}x{sh_}", f"xc:{C['sticky']}", w("st.png"))
    k.text(w("q.png"), t["quote"], "p6", 28, C["ink"], width=365, interline=4)
    k.comp(w("st.png"), w("q.png"), 30, 30)
    k.text(w("qb.png"), t["quote_by"], "p5", 22, C["purple"])
    k.comp(w("st.png"), w("qb.png"), 30, 28, "SouthWest")
    k.rotate(w("st.png"), w("str.png"), -3)
    k.shadow(w("str.png"), w("sts.png"), 35, 8, 0, 8)
    k.comp(w("pg.png"), w("sts.png"), 110, 660)
    k.text(w("n.png"), t["note"], "p6", 30, C["ink"], width=400, interline=2)
    k.comp(w("pg.png"), w("n.png"), 126, 1002)
    k.text(w("f.png"), t["footer"], "p7", 34, C["purple"])
    k.comp(w("pg.png"), w("f.png"), 126, 1098)
    k.comp(w("pg.png"), k.logo(200, w("lg.png")), 128, 1150)
    k.shadow(w("pg.png"), w("pgs.png"), 50, 12, 0, 10)
    k.comp(c, w("pgs.png"), px - 10, py - 10)
    k.fill_crop(k.photo(0), w("k.png"), 330, 380, "center")
    k.m(w("k.png"), "-bordercolor", "white", "-border", 16, "-gravity", "South", "-background", "white", "-splice", "0x56",
        w("k.png"))
    if t.get("photo_caption"):
        k.text(w("kc.png"), t["photo_caption"], "p5", 20, C["purple"])
        k.comp(w("k.png"), w("kc.png"), 0, 18, "South")
    k.comp(w("k.png"), k.tape(w("tp.png"), 160, 46), 0, -6, "North")
    k.rotate(w("k.png"), w("kr.png"), 4)
    k.shadow(w("kr.png"), w("ks.png"), 40, 12, 0, 10)
    k.comp(c, w("ks.png"), 70, 690, "NorthEast")
    k.white_card(k.photo(1), w("g.png"), 150, 150, 10)
    k.rotate(w("g.png"), w("gr.png"), -6)
    k.shadow(w("gr.png"), w("gs.png"), 35, 10, 0, 8)
    k.comp(c, w("gs.png"), 26, 628, "NorthEast")
    return c
