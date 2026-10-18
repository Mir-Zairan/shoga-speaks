#!/usr/bin/env python3
"""Builds the Shoga-Speaks logo (assets/logo.svg) and keeps the vendored fonts.

    pip install fonttools
    python3 assets/src/build.py                                            # logo.svg
    SHOGA_FONTS=~/fonts python3 assets/src/build.py --vendor-fonts          # refresh assets/src/fonts/

The banner and the social preview are built by assets/src/banner.py, which uses
the font and text machinery here and Shoga from mascot.py.

The logo is Shoga, the coloured mark from mascot.py, perched on a switch that is
on, on a dark app-icon tile. CSS media queries inside an SVG follow the <img>'s
own size, so at LOGO_SMALL px and below the logo swaps in a close-up of Shoga's
head. Pure SVG for GitHub's <img>: no script, no external files, no motion.

Fonts (both SIL OFL): Inter and JetBrains Mono. Subsetted static instances, at
the exact settings the art uses (FACES), are vendored in assets/src/fonts/ (with
OFL.txt); every build reads only those, so a fresh clone builds byte-identical
files. To change a text that needs a glyph the subsets lack, add it to CHARS,
point SHOGA_FONTS at a folder with the full variable fonts (Inter*.ttf,
JetBrainsMono*.ttf) and run --vendor-fonts, which rewrites every subset (the same
sources give byte-identical subsets). A missing glyph stops the build with a
message.
"""
import glob
import os
import re
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mascot  # noqa: E402


def f(x, d=1):
    """A number with at most d decimals and no trailing zeros."""
    s = f"{x:.{d}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ================================================================ fonts and text
# Text is drawn with glyph "sprites": each glyph is one <path id> in <defs>, at
# EM units per em, and every letter is a <use>. Kerning comes from the GPOS table.

FONTS = os.path.join(HERE, "fonts")
# the faces the art uses: key -> (variable font pattern, axis values, vendored file)
FACES = {
    "h": ("Inter*.ttf", {"wght": 800, "opsz": 32}, "Inter-800-opsz32.ttf"),     # wordmark, headline, motto
    "s": ("Inter*.ttf", {"wght": 600, "opsz": 20}, "Inter-600-opsz20.ttf"),     # answers, chips, tabs, cards
    "m": ("JetBrainsMono*.ttf", {"wght": 500}, "JetBrainsMono-500.ttf"),        # terminal: asks, replies, Technical
    "n": ("JetBrainsMono*.ttf", {"wght": 600}, "JetBrainsMono-600.ttf"),        # counter digits, code pill, install line
}
# what the subsets keep: printable ASCII plus the extra marks and letters the art
# uses (Dutch é and ë among them), so most wording edits need no new subset
CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "éëèäöüïÉ’‘“”–—…·×→−›▸▾○●⎿"


def find_font(pattern):
    d = os.environ.get("SHOGA_FONTS", "")
    if d and os.path.isdir(d):
        hits = sorted(glob.glob(os.path.join(d, "**", pattern), recursive=True))
        if hits:
            return hits[0]
    sys.exit(f"font not found: {pattern} in SHOGA_FONTS={d!r}")


_CACHE = {}


def load(key):
    """The vendored subset for a face."""
    if key not in _CACHE:
        path = os.path.join(FONTS, FACES[key][2])
        if not os.path.exists(path):
            sys.exit(f"missing fonts/{FACES[key][2]}: run --vendor-fonts with SHOGA_FONTS set")
        _CACHE[key] = TTFont(path)
    return _CACHE[key]


def vendor_fonts():
    """Writes every subsetted static instance in FACES to assets/src/fonts/ from
    the full variable fonts in SHOGA_FONTS, and removes subsets nothing uses."""
    from fontTools import subset
    from fontTools.varLib import instancer
    if not os.environ.get("SHOGA_FONTS"):
        sys.exit("--vendor-fonts needs SHOGA_FONTS (a folder with the full variable fonts)")
    os.makedirs(FONTS, exist_ok=True)
    opts = subset.Options()
    opts.layout_features = ["kern"]
    opts.hinting = False
    opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    opts.notdef_outline = True
    opts.glyph_names = False
    opts.drop_tables += ["DSIG", "STAT", "meta"]
    keep = set()
    for key, (pattern, axes, name) in FACES.items():
        font = TTFont(find_font(pattern))
        have = {a.axisTag for a in font["fvar"].axes} if "fvar" in font else set()
        if have:
            font = instancer.instantiateVariableFont(font, {k: v for k, v in axes.items() if k in have})
        sub = subset.Subsetter(opts)
        sub.populate(text=CHARS)
        sub.subset(font)
        path = os.path.join(FONTS, name)
        font.recalcTimestamp = False             # the same sources give byte-identical subsets
        font["head"].modified = font["head"].created
        font.save(path)
        keep.add(name)
        print(f"fonts/{name}: {os.path.getsize(path) / 1024:.1f} KB")
    for old in sorted(glob.glob(os.path.join(FONTS, "*.ttf"))):
        if os.path.basename(old) not in keep:
            os.remove(old)
            print(f"fonts/{os.path.basename(old)}: removed (unused)")


def rel(d):
    """Absolute integer path data to the shortest relative form."""
    toks = re.findall(r"[A-Za-z]|-?\d+", d)
    out, i, cx, cy, sx, sy, cmd, fresh = [], 0, 0, 0, 0, 0, None, True

    def nums(vals):
        s = ""
        for v in vals:
            s += ("" if (not s or v < 0) else " ") + str(v)
        return s
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd, fresh = t, True
            i += 1
            if cmd in "Zz":
                out.append("z")
                cx, cy = sx, sy
                continue
        n = {"M": 2, "L": 2, "H": 1, "V": 1, "Q": 4, "C": 6, "T": 2}[cmd]
        v = [int(x) for x in toks[i:i + n]]
        i += n
        if cmd == "H":
            r = [v[0] - cx]; cx = v[0]
        elif cmd == "V":
            r = [v[0] - cy]; cy = v[0]
        else:
            r = [v[k] - (cx if k % 2 == 0 else cy) for k in range(n)]
            cx, cy = v[-2], v[-1]
        if cmd == "M":
            sx, sy = cx, cy
        out.append(cmd.lower() + nums(r) if fresh else (nums(r) if r[0] < 0 else " " + nums(r)))
        fresh = False
        if cmd == "M":       # pairs after a moveto are linetos
            cmd, fresh = "L", True
    return "".join(out)


class Face:
    """One face's glyph sprites in a shared sheet: glyph ids are the face key plus a
    number, in order of first use."""

    def __init__(self, sheet, key, em=100):
        self.sheet, self.key, self.em = sheet, key, em
        self.font = load(key)
        self.gs, self.cmap = self.font.getGlyphSet(), self.font.getBestCmap()
        self.k = em / self.font["head"].unitsPerEm
        self.ids, self.empty = {}, set()
        self._kern = self._kern_tables()

    def _kern_tables(self):
        if "GPOS" not in self.font:
            return []
        gpos = self.font["GPOS"].table
        idx = sorted({i for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern" for i in fr.Feature.LookupListIndex})
        subs = []
        for i in idx:
            lk = gpos.LookupList.Lookup[i]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if getattr(st, "Format", 0) in (1, 2) and hasattr(st, "Coverage"):
                    subs.append(st)
        return subs

    def kern(self, a, b):
        for st in self._kern:
            cov = st.Coverage.glyphs
            if a not in cov:
                continue
            if st.Format == 1:
                for rec in st.PairSet[cov.index(a)].PairValueRecord:
                    if rec.SecondGlyph == b:
                        return getattr(rec.Value1, "XAdvance", 0) or 0
            else:
                c1 = st.ClassDef1.classDefs.get(a, 0)
                c2 = st.ClassDef2.classDefs.get(b, 0)
                v = st.Class1Record[c1].Class2Record[c2].Value1
                return (getattr(v, "XAdvance", 0) or 0) if v else 0
        return 0

    def gid(self, name):
        if name not in self.ids:
            pen = SVGPathPen(self.gs, ntos=lambda v: str(round(v)))
            self.gs[name].draw(TransformPen(pen, (self.k, 0, 0, -self.k, 0, 0)))
            d = rel(pen.getCommands())
            gid = f"{self.key}{len(self.ids)}"
            self.ids[name] = gid
            if d:
                self.sheet.append(f'<path id="{gid}" d="{d}"/>')
            else:
                self.empty.add(gid)
        return self.ids[name]

    def layout(self, text, tracking=0.0):
        """Glyph names and pen positions in EM units; returns (items, advance)."""
        items, x, prev = [], 0.0, None
        for ch in text:
            name = self.cmap.get(ord(ch))
            if not name:
                sys.exit(f"no glyph for {ch!r} in fonts/{FACES[self.key][2]}: add it to CHARS and run --vendor-fonts")
            if prev:
                x += self.kern(prev, name) * self.k
            items.append((name, x))
            x += self.gs[name].width * self.k + tracking * self.em
            prev = name
        return items, x - (tracking * self.em if items else 0)

    def width(self, text, size, tracking=0.0):
        return self.layout(text, tracking)[1] * size / self.em

    def text(self, text, size, x, y, fill=None, tracking=0.0, anchor="start", extra=""):
        """A <g> of <use> glyphs with its baseline at (x, y); returns (svg, width)."""
        items, adv = self.layout(text, tracking)
        s = size / self.em
        w = adv * s
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        uses = "".join(f'<use href="#{self.gid(n)}" x="{round(px)}"/>' for n, px in items if self.gid(n) not in self.empty)
        fl = f' fill="{fill}"' if fill else ""
        return f'<g{fl}{extra} transform="translate({f(x)} {f(y)}) scale({f(s, 4)})">{uses}</g>', w


# ================================================================ logo
TILE = "#0E1011"          # the terminal's near-black
SWITCH = "#1F9D55"        # the switch, on
LOGO_SMALL = 64           # drawn this size or smaller, the logo shows Shoga's head close up


def logo():
    """Square mark: Shoga perched on a switch that is on, on a dark tile. At
    LOGO_SMALL px or smaller (an avatar, a favicon) a CSS media query, which in an
    <img> follows the image's own size, swaps in a close-up of the head."""
    big_d, big = mascot.mark("lg")
    sm_d, sm = mascot.mark("ls", feet=False)
    fx, fy = mascot.FEET_AT
    s = 0.8                                  # Shoga on the switch
    px, py = 236, 370                        # its feet: the switch's top edge
    css = (f".sm{{display:none}}@media (max-width:{LOGO_SMALL}px){{.lg{{display:none}}.sm{{display:inline}}}}")
    return "".join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-labelledby="t">',
        '<title id="t">Shoga-Speaks: Shoga the parakeet on a switch that is on</title>',
        f'<defs>{big_d}{sm_d}<clipPath id="tc"><rect width="512" height="512" rx="112"/></clipPath></defs>',
        f'<style>{css}</style>',
        f'<rect width="512" height="512" rx="112" fill="{TILE}"/>',
        '<g clip-path="url(#tc)">',
        '<g class="lg">',
        # the switch, on
        f'<rect x="150" y="362" width="236" height="84" rx="42" fill="{SWITCH}"/>',
        '<circle cx="344" cy="404" r="30" fill="#fff"/>',
        f'<g transform="translate({px} {py}) scale({s}) translate({-fx} {-fy})">{big}</g>',
        '</g>',
        # small sizes: the head, close up
        f'<g class="sm"><g transform="translate(-118 -8) scale(1.72)">{sm}</g></g>',
        '</g>',
        '<rect x=".5" y=".5" width="511" height="511" rx="111.5" fill="none" stroke="#fff" stroke-opacity=".08"/>',
        '</svg>'])


if __name__ == "__main__":
    if "--vendor-fonts" in sys.argv:
        vendor_fonts()
        sys.exit(0)
    svg = logo()
    with open(os.path.join(OUT, "logo.svg"), "w") as fh:
        fh.write(svg)
    print(f"logo.svg: {len(svg.encode()) / 1024:.1f} KB")
