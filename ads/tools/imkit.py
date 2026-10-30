"""Shared ImageMagick helpers for the ad still layouts.

Works with ImageMagick 7 (`magick`) and ImageMagick 6 (`convert`, `identify`,
`montage`, as shipped by Ubuntu and WSL apt). Every command goes through `Kit.m`,
which picks the right binary, so a layout never names one.

Environment overrides (used by the tests, handy for debugging):
  EMMA_IM=6 or 7         force a version instead of detecting it
  EMMA_FONTS_DIR=<dir>   look for fonts here instead of ads/assets/fonts
  EMMA_NO_SYSTEM_FONTS=1 ignore system font folders (tests the fallback)
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1350
ADS = Path(__file__).resolve().parent.parent

# Earrings by Emma brand tokens, from the earringsbyemma.com theme CSS and logo SVG.
PALETTE = {
    "pink": "#FD0082",
    "teal": "#2FBAD1",
    "purple": "#5E106B",
    "lav": "#8B85C1",
    "cream": "#FEFCE8",
    "ink": "#231A2B",
}

# Font roles used by the layouts, each with fallbacks in order.
FONT_FILES = {
    "head": ["FjallaOne-Regular.ttf"],
    "p4": ["Poppins-Regular.ttf"],
    "p5": ["Poppins-Medium.ttf", "Poppins-Regular.ttf"],
    "p6": ["Poppins-SemiBold.ttf", "Poppins-Bold.ttf", "Poppins-Regular.ttf"],
    "p7": ["Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Regular.ttf"],
    "p8": ["Poppins-ExtraBold.ttf", "Poppins-Bold.ttf", "Poppins-Regular.ttf"],
    "marker": ["PermanentMarker-Regular.ttf", "Caveat-Bold.ttf"],
    "mono": ["LiberationMono-Regular.ttf", "Cousine-Regular.ttf"],
    "monob": ["LiberationMono-Bold.ttf", "Cousine-Bold.ttf", "LiberationMono-Regular.ttf", "Cousine-Regular.ttf"],
}
# Used only when no font file is found: a fontconfig family per role.
FONT_GENERIC = {"mono": "monospace", "monob": "monospace:bold", "head": "sans:bold", "p7": "sans:bold",
                "p8": "sans:bold", "p6": "sans:bold"}
SYSTEM_FONT_DIRS = ["/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/liberation2",
                    "/usr/share/fonts/liberation", "/usr/share/fonts/truetype/cousine", "/usr/share/fonts/TTF",
                    "/usr/share/fonts/truetype/google-fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts"),
                    str(Path.home() / ".local/share/fonts")]


def im_version() -> int:
    forced = os.environ.get("EMMA_IM", "").strip()
    if forced in ("6", "7"):
        return int(forced)
    if shutil.which("magick"):
        return 7
    if shutil.which("convert"):
        return 6
    sys.exit("ImageMagick is not installed. Run ./setup.sh (it installs the apt package imagemagick).")


def im_cmd(tool: str = "convert") -> list[str]:
    """The command for one ImageMagick tool: convert, identify, montage or composite."""
    if im_version() == 7:
        return ["magick"] if tool == "convert" else ["magick", tool]
    return [tool]


_warned: set[str] = set()


def warn(msg: str) -> None:
    if msg not in _warned:
        _warned.add(msg)
        print(f"warning: {msg}", file=sys.stderr)


def font_dirs() -> list[Path]:
    dirs = [Path(os.environ["EMMA_FONTS_DIR"])] if os.environ.get("EMMA_FONTS_DIR") else [ADS / "assets" / "fonts"]
    if not os.environ.get("EMMA_NO_SYSTEM_FONTS"):
        dirs += [Path(d) for d in SYSTEM_FONT_DIRS]
    return dirs


def resolve_font(role: str) -> str | None:
    """Path to the font file for a role, a fallback with a warning, or None for ImageMagick's default."""
    wanted = FONT_FILES.get(role, ["Poppins-Regular.ttf"])
    for i, name in enumerate(wanted):
        for d in font_dirs():
            p = d / name
            if p.is_file():
                if i:
                    warn(f"font {wanted[0]} not found, using {name}. Run ./setup.sh to fetch the brand fonts.")
                return str(p)
    if not os.environ.get("EMMA_NO_SYSTEM_FONTS") and shutil.which("fc-match"):
        fam = FONT_GENERIC.get(role, "sans")
        r = subprocess.run(["fc-match", "-f", "%{file}", fam], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout and Path(r.stdout).is_file():
            warn(f"font {wanted[0]} not found, using system {Path(r.stdout).name}. Run ./setup.sh to fetch the brand fonts.")
            return r.stdout
    warn(f"font {wanted[0]} not found, using ImageMagick's default font. Run ./setup.sh to fetch the brand fonts.")
    return None


class Kit:
    """One ad's drawing context: its work folder, colours, photos and logo."""

    def __init__(self, work: Path, colors: dict | None = None, photos: list[Path] | None = None,
                 logo: Path | None = None, seed: int = 1):
        self.work = Path(work)
        self.work.mkdir(parents=True, exist_ok=True)
        self.c = {**PALETTE, **(colors or {})}
        self.photos = photos or []
        self.logo_path = logo
        self.seed = seed
        self._fonts: dict[str, str | None] = {}

    # basic plumbing ---------------------------------------------------------
    def m(self, *args) -> None:
        args = [str(a) for a in args]
        if args[-1].endswith(".png") and not args[-1].startswith("PNG"):
            args[-1] = "PNG32:" + args[-1]
        r = subprocess.run(im_cmd("convert") + args, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"ImageMagick failed: {' '.join(args[:6])} ...\n{r.stderr.strip()}")

    def w(self, name: str) -> str:
        return str(self.work / name)

    def photo(self, i: int) -> str:
        return str(self.photos[i]) + "[0]"

    def font(self, role: str) -> list[str]:
        if role not in self._fonts:
            self._fonts[role] = resolve_font(role)
        f = self._fonts[role]
        return ["-font", f] if f else []

    def size_of(self, path: str) -> tuple[int, int]:
        r = subprocess.run(im_cmd("identify") + ["-format", "%w %h", path], capture_output=True, text=True, check=True)
        return tuple(int(v) for v in r.stdout.split()[:2])

    # drawing helpers, ported one for one from the October 2026 sample build --
    def text(self, out, s, font, size, color, width=None, gravity="West", interline=0, kern=0):
        a = ["-background", "none", "-fill", color, *self.font(font), "-pointsize", size,
             "-interline-spacing", interline, "-kerning", kern, "-gravity", gravity]
        a += ["-size", f"{width}x", "caption:" + s] if width else ["label:" + s]
        self.m(*a, "-trim", "+repage", out)
        return out

    def comp(self, base, over, x, y, gravity="NorthWest"):
        self.m(base, over, "-gravity", gravity, "-geometry", f"{x:+d}{y:+d}", "-composite", base)

    def shadow(self, inp, out, op=45, sigma=14, dx=0, dy=12):
        self.m(inp, "(", "+clone", "-background", "black", "-shadow", f"{op}x{sigma}{dx:+d}{dy:+d}", ")",
               "+swap", "-background", "none", "-layers", "merge", "+repage", out)
        return out

    def rotate(self, inp, out, deg):
        self.m(inp, "-background", "none", "-rotate", deg, out)
        return out

    def fill_crop(self, inp, out, ww, hh, gravity="center"):
        self.m(inp, "-resize", f"{ww}x{hh}^", "-gravity", gravity, "-extent", f"{ww}x{hh}", "+repage", out)
        return out

    def paper(self, out, color, ww=W, hh=H, amt=8):
        """A flat colour with fine paper grain."""
        self.m("-size", f"{ww}x{hh}", f"xc:{color}",
               "(", "-size", f"{ww}x{hh}", "xc:gray50", "-seed", self.seed, "-attenuate", "1", "+noise", "Gaussian",
               "-modulate", "100,0", "-blur", "0x0.7", "+level", f"{50 - amt / 2}%,{50 + amt / 2}%", ")",
               "-compose", "overlay", "-composite", "-colorspace", "sRGB", out)
        return out

    def logo(self, width, out):
        """The real logo file, unchanged, scaled to a width. SVG via ImageMagick, else rsvg-convert."""
        if not self.logo_path or not Path(self.logo_path).exists():
            warn("no logo file found, building without the logo. Run ads/tools/fetch_sources.py.")
            self.m("-size", "2x2", "xc:none", out)
            return out
        lp = str(self.logo_path)
        try:
            self.m("-background", "none", "-density", 400, lp, "-trim", "+repage", "-resize", f"{width}x", out)
        except RuntimeError:
            if lp.endswith(".svg") and shutil.which("rsvg-convert"):
                raster = self.w("_logo_raster.png")
                subprocess.run(["rsvg-convert", "-w", str(width * 4), lp, "-o", raster], check=True)
                self.m(raster, "-trim", "+repage", "-resize", f"{width}x", out)
            else:
                raise RuntimeError("cannot render the SVG logo. Install librsvg2-bin (apt) or save the logo as PNG.")
        return out

    def logo_pill(self, width, out, pill="white"):
        """The real wordmark, unchanged, on a small pill so it reads on any ground."""
        l = self.logo(width, self.w("_l.png"))
        lw, lh = self.size_of(l)
        pw, ph = lw + 44, lh + 30
        self.m("-size", f"{pw}x{ph}", "xc:none", "-fill", pill, "-draw",
               f"roundrectangle 0,0 {pw - 1},{ph - 1} {ph // 2},{ph // 2}", l, "-gravity", "center", "-composite", out)
        return out

    def white_card(self, photo, out, ww, hh, border=16, gravity="center", color="white"):
        self.fill_crop(photo, self.w("_wc.png"), ww, hh, gravity)
        self.m(self.w("_wc.png"), "-bordercolor", color, "-border", border, out)
        return out

    def marker_arrow(self, c, pts, color, width=7):
        (x1, y1), (cx, cy), (x2, y2) = pts
        self.m(c, "-fill", "none", "-stroke", color, "-strokewidth", width,
               "-draw", f"stroke-linecap round path 'M {x1},{y1} Q {cx},{cy} {x2},{y2}'", c)
        ang = math.atan2(y2 - cy, x2 - cx)
        for d in (2.6, -2.6):
            hx = x2 + 30 * math.cos(ang + d)
            hy = y2 + 30 * math.sin(ang + d)
            self.m(c, "-stroke", color, "-strokewidth", width, "-draw",
                   f"stroke-linecap round line {x2},{y2} {hx:.0f},{hy:.0f}", c)

    def rough(self, out, amt=0.6):
        """Wear the edges of a stamp or chalk mark: multiply its alpha by sparse dropout noise."""
        self.m(out, "-alpha", "extract", self.w("_a.png"))
        self.m(self.w("_a.png"), "-fill", "white", "-colorize", 100, "-seed", self.seed, "-attenuate", amt,
               "+noise", "Impulse", "-threshold", "35%", self.w("_n.png"))
        self.m(self.w("_a.png"), self.w("_n.png"), "-compose", "multiply", "-composite", self.w("_a2.png"))
        self.m(out, self.w("_a2.png"), "-alpha", "off", "-compose", "CopyOpacity", "-composite", out)
        return out

    def tape(self, out, ww=150, hh=44, color="#F6EFC8C8"):
        self.m("-size", f"{ww}x{hh}", f"xc:{color}", out)
        return out

    def round_mask(self, inp, out, d):
        """Crop a photo into a circle of diameter d."""
        self.fill_crop(inp, out, d, d, "center")
        self.m("-size", f"{d}x{d}", "xc:none", "-fill", "white", "-draw", f"circle {d // 2},{d // 2} {d // 2},1",
               self.w("_rm.png"))
        self.m(out, self.w("_rm.png"), "-compose", "CopyOpacity", "-composite", out)
        return out
