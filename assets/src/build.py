#!/usr/bin/env python3
"""Builds the Shoga-Speaks logo (assets/logo.svg) and keeps the vendored fonts.

    pip install fonttools
    python3 assets/src/build.py                                   # logo.svg
    SHOGA_FONTS=~/fonts python3 assets/src/build.py --vendor-fonts # refresh assets/src/fonts/

The banner and the social preview are built by assets/src/banner.py, which uses
the font and text machinery and Shoga's geometry from this file.

The logo is Shoga perched on a small terminal window, with a speech bubble. CSS
media queries inside an SVG follow the <img>'s own size, so at LOGO_SMALL px and
below the logo swaps in a bold head mark. Pure SVG for GitHub's <img>: no script,
no external files, every word an outlined path (glyphs are defined once and
reused with <use>).

Fonts (both SIL OFL): Inter and JetBrains Mono. Subsetted static instances, at
the exact settings the art uses (FACES), are vendored in assets/src/fonts/ (with
OFL.txt), so a fresh clone builds as is. To change a text that needs a glyph the
subsets lack, add it to CHARS, point SHOGA_FONTS at a folder with the full
variable fonts (Inter*.ttf, JetBrainsMono*.ttf) and refresh every subset with
--vendor-fonts. A missing glyph stops the build with a message.
"""
import glob
import os
import sys

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)


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
    "xb": ("Inter*.ttf", {"wght": 800, "opsz": 32}, "Inter-800-opsz32.ttf"),           # banner: wordmark, badges
    "b": ("Inter*.ttf", {"wght": 700, "opsz": 28}, "Inter-700-opsz28.ttf"),            # banner: stories, motto
    "sb": ("Inter*.ttf", {"wght": 600, "opsz": 18}, "Inter-600-opsz18.ttf"),           # banner: small text
    "mono": ("JetBrainsMono*.ttf", {"wght": 500}, "JetBrainsMono-500.ttf"),            # logo: the ▸ prompt
    "mono6": ("JetBrainsMono*.ttf", {"wght": 600}, "JetBrainsMono-600.ttf"),           # banner: jargon, prompt, cards
}
# what the subsets keep: printable ASCII plus the few extra marks the art uses,
# so most wording edits need no new subset
CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "’‘“”–—…·×→−›▸▾●⎿"


def find_font(pattern):
    d = os.environ.get("SHOGA_FONTS", "")
    if d and os.path.isdir(d):
        hits = sorted(glob.glob(os.path.join(d, "**", pattern), recursive=True))
        if hits:
            return hits[0]
    sys.exit(f"font not found: {pattern} in SHOGA_FONTS={d!r}")


_CACHE = {}


def load(key):
    """The face as a TTFont: the vendored subset, or with SHOGA_FONTS set, an
    instance of the full variable font at the same axis values."""
    if key not in _CACHE:
        pattern, axes, vendored = FACES[key]
        if os.environ.get("SHOGA_FONTS"):
            font = TTFont(find_font(pattern))
            have = {a.axisTag for a in font["fvar"].axes} if "fvar" in font else set()
            if have:
                font = instancer.instantiateVariableFont(font, {k: v for k, v in axes.items() if k in have})
        else:
            font = TTFont(os.path.join(FONTS, vendored))
        _CACHE[key] = font
    return _CACHE[key]


def vendor_fonts():
    """Writes the subsetted static instances to assets/src/fonts/ from SHOGA_FONTS."""
    from fontTools import subset
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
    for key, (_, _, name) in FACES.items():
        font = load(key)
        sub = subset.Subsetter(opts)
        sub.populate(text=CHARS)
        sub.subset(font)
        path = os.path.join(FONTS, name)
        font.recalcTimestamp = False             # the same sources give byte-identical subsets
        font["head"].modified = font["head"].created
        font.save(path)
        print(f"fonts/{name}: {os.path.getsize(path) / 1024:.1f} KB")


class Face:
    def __init__(self, sheet, key, face, em=100):
        self.sheet, self.key, self.em, self.face_key = sheet, key, em, face
        self.font = load(face)
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
                return getattr(v, "XAdvance", 0) or 0 if v else 0
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
                sys.exit(f"no glyph for {ch!r} in {FACES[self.face_key][2]}: add it to CHARS and run --vendor-fonts")
            if prev:
                x += self.kern(prev, name) * self.k
            items.append((name, x))
            x += self.gs[name].width * self.k + tracking * self.em
            prev = name
        return items, x - (tracking * self.em if items else 0)

    def adv(self, name):
        """A glyph's advance in EM units."""
        return self.gs[name].width * self.k

    def width(self, text, size, tracking=0.0):
        return self.layout(text, tracking)[1] * size / self.em

    def text(self, text, size, x, y, cls="", tracking=0.0, anchor="start", extra=""):
        """A <g> of <use> glyphs with its baseline at (x, y); returns (svg, width)."""
        items, adv = self.layout(text, tracking)
        s = size / self.em
        w = adv * s
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        uses = "".join(f'<use href="#{self.gid(n)}" x="{round(px)}"/>' for n, px in items if self.gid(n) not in self.empty)
        c = f' class="{cls}"' if cls else ""
        return f'<g{c}{extra} transform="translate({f(x)} {f(y)}) scale({f(s, 4)})">{uses}</g>', w


def rel(d):
    """Absolute integer path data to the shortest relative form."""
    import re
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


class Type:
    """The faces one document uses, sharing one glyph sheet.

    faces: attribute -> (glyph id prefix, FACES key, units per em)."""

    def __init__(self, faces):
        self.sheet = []
        for attr, (key, face, em) in faces.items():
            setattr(self, attr, Face(self.sheet, key, face, em=em))

    def defs(self):
        return "".join(self.sheet)


# ================================================================ palette
INK = "#15301F"
P = dict(mint="#EAF8EF", screen="#13261D", dim="#7FA391", str="#8FE3A6")

# ================================================================ Shoga
# A chubby rose-ringed parakeet facing right (banner.py also flies it and mirrors it).
# Outlines are a thick stroke under the fills, so head and body read as one shape.

BODY = "M170 150C242 150 272 220 270 282C268 346 226 392 170 392C112 392 72 346 72 282C72 216 104 150 170 150Z"
HEAD = "M190 40C246 40 290 84 290 138C290 192 246 232 190 232C134 232 92 192 92 138C92 84 134 40 190 40Z"
TAIL = "M118 318C96 360 74 400 54 452C78 446 94 432 104 412C112 438 130 452 150 456C146 410 146 366 152 330Z"
WING = "M104 238C132 226 170 238 186 272C200 304 194 348 168 380C150 360 120 352 100 330C84 304 84 262 104 238Z"
BEAK_UP = "M266 104C300 92 340 112 342 150C344 176 332 196 314 206C318 188 314 174 302 168C294 164 284 164 276 168Z"
BEAK_LO = "M276 168C288 166 302 172 306 186C300 198 286 202 272 194Z"
FEET = ("M140 384C138 398 132 406 124 410C132 414 146 410 152 400Z"
        "M184 386C184 400 180 408 172 412C180 416 194 412 198 402Z")
# flight and standing parts that banner.py draws (the logo's Shoga sits with its wings folded)
# spread wing for flight, in its own space: root at (0, 0), pointing up, leading edge right
FLY = ("M-6 14C34 -30 62 -112 46 -214C30 -200 16 -192 2 -190C6 -176 2 -166 -6 -160C-18 -160 -28 -152 -32 -142"
       "C-28 -130 -32 -120 -40 -114C-50 -112 -58 -104 -60 -94C-56 -82 -58 -72 -66 -66C-70 -36 -50 -6 -6 14Z")
FLY_TIP = ("M46 -214C30 -200 16 -192 2 -190C6 -176 2 -166 -6 -160C-18 -160 -28 -152 -32 -142C-28 -130 -32 -120 -40 -114"
           "C-50 -112 -58 -104 -60 -94C-56 -82 -58 -72 -66 -66C-40 -96 4 -150 46 -214Z")
FLY_COV = "M-6 14C30 -20 48 -60 46 -96C20 -90 -10 -82 -40 -60C-50 -30 -34 0 -6 14Z"
WROOT = (150, 214)
OL = f'stroke="{INK}" stroke-linejoin="round" stroke-linecap="round"'


def shoga_defs():
    return (
        '<linearGradient id="tailG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FB98F"/><stop offset="1" stop-color="#2F7FC4"/></linearGradient>'
        '<linearGradient id="beakG" x1="0" y1="0" x2=".5" y2="1"><stop offset="0" stop-color="#FF5A66"/><stop offset="1" stop-color="#D81E3C"/></linearGradient>'
        '<linearGradient id="flyG" x1="1" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#3DB65C"/><stop offset=".7" stop-color="#2E9F55"/><stop offset="1" stop-color="#2A7FB8"/></linearGradient>'
        f'<clipPath id="mClip"><path d="{BODY}"/><path d="{HEAD}"/></clipPath>'
    )


def shoga():
    """Shoga perched, in local coordinates (about 54..342 x 40..456), facing right.

    The logo draws no feet: on its terminal they read as noise (banner.py draws
    them when Shoga stands on the underline)."""
    return "".join([
        '<g class="tail">',
        f'<path d="{TAIL}" fill="url(#tailG)" {OL} stroke-width="9"/>',
        '<path d="M120 336C108 376 92 412 72 444" stroke="#BFF5EA" stroke-width="3" stroke-opacity=".6" fill="none" stroke-linecap="round"/>',
        '</g>',
        '<g class="bod">',
        f'<g fill="{INK}" {OL} stroke-width="11"><path d="{BODY}"/><path d="{HEAD}"/></g>',
        f'<path d="{BODY}" fill="#4CC764"/><path d="{HEAD}" fill="#5BD46E"/>',
        '<g clip-path="url(#mClip)">',
        '<ellipse cx="214" cy="300" rx="52" ry="74" fill="#B4EC78"/>',
        '<path d="M60 300C90 380 150 410 240 400L260 430L40 430Z" fill="#2E9F55" opacity=".55"/>',
        '<path d="M92 160C100 210 140 236 190 236C150 250 100 230 84 190Z" fill="#2E9F55" opacity=".45"/>',
        '<path d="M96 110C100 80 120 58 146 50C126 74 118 104 122 136C112 132 100 124 96 110Z" fill="#6FC3C9" opacity=".45"/>',
        '<path d="M150 62C176 50 214 50 238 62" stroke="#E9FFC2" stroke-width="9" fill="none" stroke-linecap="round" opacity=".6"/>',
        f'<path d="M282 196C258 236 190 246 116 210" stroke="{INK}" stroke-width="9" fill="none" stroke-linecap="round"/>',
        '<path d="M280 212C254 254 184 262 104 222" stroke="#FF8DB8" stroke-width="10" fill="none" stroke-linecap="round"/>',
        '</g>',
        '<g class="fold">',
        f'<path d="{WING}" fill="#33A956" {OL} stroke-width="5"/>',
        '<path d="M110 326C124 316 140 318 152 330M122 350C136 342 150 344 160 354M104 300C118 292 134 294 146 304" '
        f'stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".55"/>',
        '<path d="M112 250C132 242 156 250 168 268" stroke="#9BE79A" stroke-width="4" fill="none" stroke-linecap="round" opacity=".7"/>',
        '</g>',
        '</g>',
        '<g class="headf">',
        '<circle cx="222" cy="122" r="27" fill="#fff" stroke="#FF8A3D" stroke-width="6"/>',
        f'<circle cx="222" cy="122" r="31" fill="none" stroke="{INK}" stroke-width="3"/>',
        f'<circle class="pupil" cx="228" cy="125" r="15" fill="{INK}"/>',
        '<circle cx="234" cy="116" r="6" fill="#fff"/><circle cx="222" cy="133" r="2.6" fill="#fff"/>',
        f'<path class="lid" d="M190 122C192 88 252 88 254 122Z" fill="#5BD46E" stroke="{INK}" stroke-width="3"/>',
        f'<g class="jaw"><path d="{BEAK_LO}" fill="#8E1428" {OL} stroke-width="5"/></g>',
        f'<path d="{BEAK_UP}" fill="url(#beakG)" {OL} stroke-width="5"/>',
        '<path d="M280 108C304 102 328 116 334 140" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>',
        f'<circle cx="276" cy="112" r="3" fill="{INK}"/>',
        '</g>',
    ])


LOGO_SMALL = 96   # drawn this size or smaller, the logo switches to the bold head mark


def logo_mark():
    """Shoga's head, drawn bold for small sizes (16 to 96 px): a big head, a big
    hooked beak, one eye and the neck ring, plus a terminal chip with a ▸.
    Strokes are 20 to 28 units, so they stay above a pixel at 32 px."""
    head = "M226 106A170 170 0 1 1 225.9 106Z"
    beak = "M346 178C420 146 496 196 492 282C490 332 464 368 430 384C440 344 432 310 402 300C384 294 364 296 346 304Z"
    jaw = "M346 304C378 294 410 306 416 338C398 358 368 358 342 344Z"
    return "".join([
        '<g class="sm">',
        f'<clipPath id="hc"><path d="{head}"/></clipPath>',
        f'<path d="{head}" fill="#5BD46E" stroke="{INK}" stroke-width="28"/>',
        '<g clip-path="url(#hc)">',
        '<path d="M40 300C70 420 170 470 300 470L40 470Z" fill="#2E9F55" opacity=".5"/>',
        f'<path d="M80 318C150 404 290 418 396 350" stroke="{INK}" stroke-width="24" fill="none"/>',
        '<path d="M80 348C150 434 290 446 404 378" stroke="#FF8DB8" stroke-width="24" fill="none"/>',
        '<path d="M110 196C130 156 170 130 212 124" stroke="#E9FFC2" stroke-width="20" fill="none" stroke-linecap="round" opacity=".7"/>',
        '</g>',
        f'<path d="{jaw}" fill="#8E1428" stroke="{INK}" stroke-width="18" stroke-linejoin="round"/>',
        f'<path d="{beak}" fill="#F0384F" stroke="{INK}" stroke-width="20" stroke-linejoin="round"/>',
        '<path d="M384 192C424 184 462 210 470 250" stroke="#fff" stroke-width="12" fill="none" stroke-linecap="round" opacity=".5"/>',
        f'<circle cx="290" cy="222" r="58" fill="#fff" stroke="{INK}" stroke-width="12"/>',
        '<circle cx="290" cy="222" r="44" fill="none" stroke="#FF8A3D" stroke-width="16"/>',
        f'<circle cx="300" cy="228" r="26" fill="{INK}"/><circle cx="310" cy="214" r="9" fill="#fff"/>',
        # the terminal chip, ringed in white so it separates from the head
        '<g class="chip">',
        f'<rect x="22" y="342" width="168" height="146" rx="34" fill="{P["screen"]}" stroke="#fff" stroke-width="18"/>',
        f'<rect x="22" y="342" width="168" height="146" rx="34" fill="none" stroke="{INK}" stroke-width="8"/>',
        f'<path d="M72 376L138 415L72 454Z" fill="{P["str"]}" stroke="{P["str"]}" stroke-width="10" stroke-linejoin="round"/>',
        '</g></g>'])


def logo():
    """Square mark: Shoga perched on a small terminal window, with a speech bubble.
    At LOGO_SMALL px or smaller (an avatar, a favicon) a CSS media query, which in
    an <img> follows the image's own size, swaps in the bold head mark."""
    ty = Type({"mono": ("m", "mono", 100)})
    s = 0.72
    feet = (214, 292)
    bx, by = feet[0] - s * 160, feet[1] - s * 414
    tri = ty.mono.text("▸", 104, 62, 438, extra=f' fill="{P["str"]}"')[0]
    css_ = ("@keyframes blink{0%,90%,100%{transform:scaleY(0)}94%{transform:scaleY(1)}}"
            ".lid{transform-origin:222px 92px;transform:scaleY(0);animation:blink 4s infinite}"
            ".cur{animation:cur 1.2s steps(1,end) infinite}@keyframes cur{0%{opacity:1}50%{opacity:0}}"
            f".sm{{display:none}}@media (max-width:{LOGO_SMALL}px){{.lg{{display:none}}.sm{{display:inline}}}}"
            "@media (max-width:24px){.chip{display:none}}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    return "".join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-labelledby="t">',
        '<title id="t">Shoga-Speaks: Shoga the parrot on a terminal</title>',
        f'<defs>{shoga_defs()}{ty.defs()}</defs>',
        f'<style>{css_}</style>',
        '<rect width="512" height="512" rx="112" fill="#fff"/>',
        '<g class="lg">',
        f'<circle cx="224" cy="196" r="168" fill="{P["mint"]}"/>',
        # terminal window
        f'<rect x="30" y="286" width="452" height="196" rx="38" fill="{P["screen"]}" stroke="{INK}" stroke-width="14"/>',
        "".join(f'<circle cx="{66 + k * 27}" cy="326" r="10" fill="{c}"/>' for k, c in enumerate(["#FF7A7A", "#FFD166", "#5BD46E"])),
        tri,
        '<rect x="180" y="362" width="236" height="28" rx="14" fill="#F4FFF7"/>',
        f'<rect x="180" y="410" width="140" height="28" rx="14" fill="{P["dim"]}"/>',
        f'<rect class="cur" x="338" y="406" width="22" height="36" rx="4" fill="{P["str"]}"/>',
        # speech bubble
        f'<path d="M382 44H460A30 30 0 0 1 490 74V128A30 30 0 0 1 460 158H418L384 184L392 158H382A30 30 0 0 1 352 128V74A30 30 0 0 1 382 44Z" fill="#fff" stroke="{INK}" stroke-width="12" stroke-linejoin="round"/>',
        "".join(f'<circle cx="{388 + k * 33}" cy="101" r="12" fill="{c}"/>' for k, c in enumerate(["#1F9D55", "#2F7FE0", "#E08A12"])),
        f'<g transform="translate({f(bx)} {f(by)}) scale({s})">{shoga()}</g>',
        '</g>',
        logo_mark(),
        '</svg>'])


if __name__ == "__main__":
    if "--vendor-fonts" in sys.argv:
        vendor_fonts()
        sys.exit(0)
    svg = logo()
    with open(os.path.join(OUT, "logo.svg"), "w") as fh:
        fh.write(svg)
    print(f"logo.svg: {len(svg.encode()) / 1024:.1f} KB")
