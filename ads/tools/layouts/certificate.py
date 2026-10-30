"""pr03 Guarantee certificate: the store's own promise on a bordered certificate, stamped and sealed."""

import math

NAME = "certificate"
FORMAT = "pr03"
FAMILY = "Proof and review"
TITLE = "Stamped certificate"
WHEN = "Skepticism. A guarantee or refund policy the buyer has not noticed. Quote the policy exactly."
PHOTOS = ["cropped into a round window"]
REQUIRED = {"kicker": "str", "title": "str", "body": "str", "stamp": "pair", "seal": "pair", "sign": "str",
            "footer": "str"}
OPTIONAL = {}
LIMITS = {}
COLORS = {"ground": "#8B85C1", "paper": "#FEFCE8", "seal_color": "#2FBAD1", "stamp_color": "#FD0082"}


def rosette(k, out, d, color, lines, text_color="white"):
    r = d // 2
    pts = []
    for i in range(48):
        rr = r if i % 2 == 0 else r - 14
        a = i * math.pi / 24
        pts.append(f"{r + rr * math.cos(a):.0f},{r + rr * math.sin(a):.0f}")
    k.m("-size", f"{d}x{d}", "xc:none", "-fill", color, "-draw", "polygon " + " ".join(pts),
        "-fill", "none", "-stroke", "#FFFFFFAA", "-strokewidth", 3, "-draw", f"circle {r},{r} {r},{30}", out)
    k.text(k.w("r1.png"), lines[0], "head", 42, text_color)
    k.comp(out, k.w("r1.png"), 0, -22, "center")
    k.text(k.w("r2.png"), lines[1], "p7", 18, text_color, kern=1)
    k.comp(out, k.w("r2.png"), 0, 30, "center")
    return out


def build(k, t):
    C, w = k.c, k.w
    c = w("canvas.png")
    k.paper(c, C["ground"], amt=8)
    cw, ch = 960, 1150
    k.paper(w("cert.png"), C["paper"], cw, ch, 5)
    k.m(w("cert.png"), "-fill", "none", "-stroke", C["purple"], "-strokewidth", 8, "-draw",
        f"rectangle 22,22 {cw - 23},{ch - 23}", "-strokewidth", 2, "-draw", f"rectangle 40,40 {cw - 41},{ch - 41}",
        w("cert.png"))
    for (x, y) in [(40, 40), (cw - 41, 40), (40, ch - 41), (cw - 41, ch - 41)]:
        k.m(w("cert.png"), "-fill", C["pink"], "-stroke", "none", "-draw", f"circle {x},{y} {x + 10},{y}", w("cert.png"))
    k.text(w("k.png"), t["kicker"], "p7", 26, C["teal"], kern=5)
    k.comp(w("cert.png"), w("k.png"), 0, 92, "North")
    k.text(w("tt.png"), t["title"], "head", 112, C["purple"], gravity="Center", interline=-14)
    k.comp(w("cert.png"), w("tt.png"), 0, 150, "North")
    _, th = k.size_of(w("tt.png"))
    yb = 150 + th + 34
    k.m(w("cert.png"), "-fill", C["pink"], "-draw", f"rectangle {cw // 2 - 60},{yb} {cw // 2 + 60},{yb + 6}", w("cert.png"))
    k.text(w("b.png"), t["body"], "p5", 34, C["ink"], width=760, gravity="Center", interline=8)
    k.comp(w("cert.png"), w("b.png"), 0, yb + 36, "North")
    _, bh = k.size_of(w("b.png"))
    ys = yb + 36 + bh + 70
    k.text(w("sg.png"), t["sign"], "marker", 40, C["purple"])
    k.comp(w("cert.png"), w("sg.png"), 90, ys)
    k.m(w("cert.png"), "-stroke", C["purple"], "-strokewidth", 2, "-draw", f"line 90,{ys + 66} 470,{ys + 66}", w("cert.png"))
    pd = 300
    k.fill_crop(k.photo(0), w("pp.png"), pd, pd, "center")
    k.m("-size", f"{pd}x{pd}", "xc:none", "-fill", "white", "-draw", f"circle {pd // 2},{pd // 2} {pd // 2},2", w("pm.png"))
    k.m(w("pp.png"), w("pm.png"), "-compose", "CopyOpacity", "-composite", w("pp.png"))
    k.m("-size", f"{pd + 16}x{pd + 16}", "xc:none", "-fill", C["purple"], "-draw",
        f"circle {(pd + 16) // 2},{(pd + 16) // 2} {(pd + 16) // 2},0", w("pr.png"))
    k.comp(w("pr.png"), w("pp.png"), 8, 8)
    k.comp(w("cert.png"), w("pr.png"), 80, 120, "SouthEast")
    k.text(w("f.png"), t["footer"], "p6", 28, C["ink"])
    k.comp(w("cert.png"), w("f.png"), 90, 136, "SouthWest")
    k.comp(w("cert.png"), k.logo(230, w("lg.png")), 90, 78, "SouthWest")
    k.shadow(w("cert.png"), w("certs.png"), 40, 16, 0, 14)
    k.comp(c, w("certs.png"), 0, 70, "North")
    s = 300
    sc = C["stamp_color"]
    k.m("-size", f"{s}x{s}", "xc:none", "-fill", "none", "-stroke", sc, "-strokewidth", 9,
        "-draw", f"circle {s // 2},{s // 2} {s // 2},12", "-strokewidth", 3, "-draw", f"circle {s // 2},{s // 2} {s // 2},32",
        w("st.png"))
    k.text(w("s1.png"), t["stamp"][0], "head", 50, sc)
    k.comp(w("st.png"), w("s1.png"), 0, -26, "center")
    k.text(w("s2.png"), t["stamp"][1], "p8", 30, sc, kern=1)
    k.comp(w("st.png"), w("s2.png"), 0, 36, "center")
    k.rough(w("st.png"))
    k.m(w("st.png"), "-resize", "66%", w("st.png"))
    k.rotate(w("st.png"), w("str.png"), -14)
    k.comp(c, w("str.png"), 350, 822)
    rosette(k, w("ros.png"), 190, C["seal_color"], t["seal"])
    k.rotate(w("ros.png"), w("rosr.png"), 8)
    k.comp(c, w("rosr.png"), 120, 836)
    return c
