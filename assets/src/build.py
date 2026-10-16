#!/usr/bin/env python3
"""Builds assets/banner.svg and assets/logo.svg.

    pip install fonttools
    python3 assets/src/build.py

Everything is vector and self-contained (no external fonts or images), so it renders
the same in a GitHub README. Animations are CSS + SMIL and stop under reduced motion.
"""
import math
import os
import random

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONT = os.environ.get("SHOGA_FONT", "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
W, H = 1280, 540
rnd = random.Random(7)


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- text → outlines

def text_path(text, size, x, y, tracking=0.0, font=FONT):
    font = TTFont(font)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    pen = SVGPathPen(gs)
    cx = 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        if not name:
            continue
        tp = TransformPen(pen, (scale, 0, 0, -scale, x + cx, y))
        gs[name].draw(tp)
        cx += gs[name].width * scale + tracking
    return pen.getCommands(), cx - tracking


# ---------------------------------------------------------------- scene pieces

def ridge(y0, amp, seed, step=14, rough=0.55):
    r = random.Random(seed)
    pts, y = [], y0
    for i in range(0, W + step * 2, step):
        y += r.uniform(-amp, amp) * rough + (y0 - y) * 0.08
        peak = amp * 2.2 * math.sin(i / (W / r.uniform(2.2, 3.4)) + seed) ** 6
        pts.append((i - step, y - peak))
    d = f"M-20 {H} " + " ".join(f"L{f(px)} {f(py)}" for px, py in pts) + f" L{W + 20} {H} Z"
    return d


def chinar_leaf():
    # palmate, five deep lobes; about 40 units across, stem at the bottom
    return ("M0 18 C-3 12 -9 13 -15 15 C-12 10 -16 6 -21 2 C-14 1 -12 -3 -13 -9 C-8 -6 -5 -8 -4 -14 "
            "C-2 -10 0 -12 0 -20 C0 -12 2 -10 4 -14 C5 -8 8 -6 13 -9 C12 -3 14 1 21 2 C16 6 12 10 15 15 "
            "C9 13 3 12 0 18 Z")


def scene():
    s = []
    # sky
    s.append('<rect width="1280" height="540" fill="url(#sky)"/>')
    s.append('<ellipse cx="380" cy="372" rx="520" ry="210" fill="url(#sun)"/>')
    # stars
    for i in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(0, 210)
        r = rnd.uniform(0.4, 1.3)
        cls = f"tw tw{i % 4}"
        s.append(f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#fff" opacity="{f(rnd.uniform(.25,.8))}"/>')
    # crescent moon
    s.append('<g filter="url(#glow)"><circle cx="118" cy="78" r="17" fill="#FFF4D6"/><circle cx="126" cy="72" r="15" fill="#0B1230"/></g>')
    s.append('<circle cx="118" cy="78" r="46" fill="#FFF4D6" opacity=".06"/>')
    # god rays
    s.append('<g class="rays" filter="url(#soft)" opacity=".5">')
    for i, (a, w) in enumerate([(-28, 40), (-14, 26), (-2, 54), (12, 30), (26, 44)]):
        s.append(f'<path d="M380 372 L{f(380 + 900 * math.sin(math.radians(a - w/10)))} -60 '
                 f'L{f(380 + 900 * math.sin(math.radians(a + w/10)))} -60 Z" fill="url(#ray)" class="ray r{i}"/>')
    s.append('</g>')
    # mountains: far → near, snow on the far range
    s.append(f'<path d="{ridge(300, 9, 3)}" fill="url(#m1)" filter="url(#haze)"/>')
    s.append(f'<path d="{ridge(300, 9, 3)}" fill="url(#snow)" opacity=".55" filter="url(#haze)"/>')
    s.append(f'<path d="{ridge(338, 7, 11, 18)}" fill="url(#m2)"/>')
    s.append(f'<path d="{ridge(372, 5, 21, 22, .4)}" fill="url(#m3)"/>')
    # lake with reflection and shimmer
    s.append('<rect y="398" width="1280" height="142" fill="url(#lake)"/>')
    s.append('<ellipse cx="380" cy="404" rx="260" ry="9" fill="#FFC27A" opacity=".55" filter="url(#soft)"/>')
    s.append('<g class="shimmer">')
    for i in range(60):
        y = 404 + rnd.uniform(0, 1) ** 1.6 * 130
        spread = 60 + (y - 404) * 2.2
        x = 380 + rnd.uniform(-spread, spread)
        w = rnd.uniform(6, 34) * (1 - (y - 404) / 200)
        a = max(.06, .6 - (y - 404) / 230) * rnd.uniform(.5, 1)
        s.append(f'<rect class="sh sh{i % 3}" x="{f(x)}" y="{f(y)}" width="{f(max(w, 3))}" height="1.3" rx=".6" fill="#FFD9A0" opacity="{f(a)}"/>')
    s.append('</g>')
    # shikara on the lake, with a lantern
    s.append('<g class="boat"><g transform="translate(600 420)">'
             '<ellipse cx="0" cy="14" rx="70" ry="4" fill="#FFD9A0" opacity=".12" filter="url(#blur3)"/>'
             '<path d="M-74 -8 C-60 4 -30 8 0 8 C30 8 60 4 76 -10 C70 2 60 10 40 12 L-40 12 C-60 10 -70 2 -74 -8 Z" fill="#0A0D18"/>'
             '<path d="M-30 6 L-30 -14 M24 6 L24 -14" stroke="#0A0D18" stroke-width="2"/>'
             '<path d="M-36 -14 C-20 -22 18 -22 30 -14 Z" fill="#0A0D18"/>'
             '<path d="M44 4 C50 -10 54 -20 58 -26" stroke="#0A0D18" stroke-width="2.4"/><circle cx="58" cy="-30" r="4" fill="#0A0D18"/>'
             '<path d="M52 6 L80 22" stroke="#0A0D18" stroke-width="1.6"/>'
             '<circle class="lantern" cx="-26" cy="-6" r="2.6" fill="#FFD27A" filter="url(#glow)"/>'
             '<rect class="lantern" x="-28" y="12" width="4" height="18" rx="2" fill="#FFD27A" opacity=".35" filter="url(#blur3)"/>'
             '</g></g>')
    # fog
    s.append('<rect y="350" width="1280" height="70" fill="url(#fog)" class="fog"/>')
    return "\n".join(s)


def fireflies():
    s = ['<g filter="url(#glow)">']
    for i in range(26):
        x, y = rnd.uniform(20, 760), rnd.uniform(120, 480)
        r = rnd.uniform(1.2, 2.6)
        s.append(f'<circle class="ff ff{i % 5}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#FFE9A8"/>')
    s.append('</g>')
    return "\n".join(s)


LEAF_CSS = []


def leaves():
    s = []
    cols = ["#E8572A", "#F08A24", "#C93A22", "#F2B13A", "#D9482B", "#EE7B2F", "#B8321F"]
    durs = [16, 19, 14, 22, 17, 21, 15, 24]
    for i in range(8):
        x = rnd.uniform(-40, 600)
        sc = rnd.uniform(.45, .9)
        drift = [rnd.uniform(-20, 60) for _ in range(4)]
        LEAF_CSS.append(
            f"@keyframes fall{i} {{ 0% {{ transform: translate({f(x)}px, -40px) rotate(0deg); opacity: 0; }} 5% {{ opacity: 1; }} "
            f"25% {{ transform: translate({f(x + drift[0])}px, 120px) rotate(120deg); }} 50% {{ transform: translate({f(x + drift[1])}px, 260px) rotate(220deg); }} "
            f"75% {{ transform: translate({f(x + drift[2])}px, 400px) rotate(330deg); }} 92% {{ opacity: 1; }} "
            f"100% {{ transform: translate({f(x + drift[3])}px, 560px) rotate(420deg); opacity: 0; }} }}\n"
            f".l{i} {{ animation: fall{i} {durs[i]}s linear infinite; animation-delay: -{f(rnd.uniform(0, durs[i]))}s; transform: translate({f(x)}px, -40px); }}")
        s.append(f'<g class="leaf l{i}"><g transform="scale({f(sc)})">'
                 f'<path d="{chinar_leaf()}" fill="{cols[i % len(cols)]}"/>'
                 f'<path d="M0 18 L0 -14 M0 4 L-12 -6 M0 4 L12 -6 M0 10 L-14 8 M0 10 L14 8" stroke="#7A1E10" '
                 f'stroke-width=".8" opacity=".55" fill="none"/></g></g>')
    return "\n".join(s)


def branch():
    s = []
    d = "M-30 452 C80 446 170 432 250 428 C330 424 420 414 520 392 L524 404 C430 428 340 440 252 444 C170 448 80 466 -30 474 Z"
    s.append(f'<path d="{d}" fill="url(#bark)"/>')
    s.append(f'<path d="{d}" fill="#000" opacity=".9" filter="url(#barkTex)" clip-path="url(#branchClip)"/>')
    s.append('<path d="M-30 452 C80 446 170 432 250 428 C330 424 420 414 520 392" stroke="#E9B98A" stroke-opacity=".55" stroke-width="2" fill="none"/>')
    # twig with chinar leaves
    s.append('<path d="M440 410 C470 380 488 360 520 340" stroke="#3B2618" stroke-width="5" fill="none" stroke-linecap="round"/>')
    s.append('<path d="M110 450 C96 470 92 490 96 520" stroke="#3B2618" stroke-width="6" fill="none" stroke-linecap="round"/>')
    for (x, y, r, sc, c) in [(520, 340, -30, 1.25, "#D9482B"), (496, 362, 25, 1.0, "#F08A24"), (98, 520, 160, 1.3, "#C93A22"), (60, 456, 200, 0.9, "#E8572A")]:
        s.append(f'<g transform="translate({x} {y}) rotate({r}) scale({sc})"><path d="{chinar_leaf()}" fill="{c}"/>'
                 f'<path d="{chinar_leaf()}" fill="url(#leafShade)"/>'
                 f'<path d="M0 18 L0 -14 M0 4 L-12 -6 M0 4 L12 -6" stroke="#6B1A0E" stroke-width=".9" opacity=".6" fill="none"/></g>')
    return "\n".join(s)


# ---------------------------------------------------------------- the parrot
# Rose-ringed parakeet, three-quarter profile facing right. One continuous outline for
# head and body; shading is painted on top with soft, clipped shapes.

SILHOUETTE = ("M292 92 C286 70 266 58 244 60 C222 62 204 76 198 98 C192 118 190 138 192 158 "
              "C196 188 184 226 183 268 C182 310 194 346 214 368 C226 378 244 382 256 376 "
              "C284 362 306 334 313 296 C320 256 312 222 298 204 C288 191 284 180 288 168 "
              "C290 160 294 154 296 150 Z")
WING = ("M220 178 C248 190 264 220 261 258 C257 298 240 344 214 404 C206 384 198 344 196 302 "
        "C192 250 198 204 220 178 Z")
BEAK_UP = ("M289 90 C313 80 340 96 340 124 C340 143 331 158 318 167 C321 152 317 141 307 137 "
           "C301 135 295 135 290 137 Z")
BEAK_LO = "M290 137 C301 137 311 143 313 154 C307 162 296 163 288 157 Z"
BODY = WING  # kept for clip ids used by callers
HEAD = SILHOUETTE


def painted_strokes(n, region, color, alpha, width, length, flow):
    """Short curved strokes that follow the feather flow inside a box: a painted texture."""
    x0, y0, x1, y1 = region
    out = []
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        ang = math.radians(flow(x, y) + rnd.uniform(-12, 12))
        ln = length * rnd.uniform(.6, 1.3)
        dx, dy = math.cos(ang) * ln, math.sin(ang) * ln
        bend = rnd.uniform(-3, 3)
        out.append(f"M{f(x)} {f(y)} q{f(dx / 2 + bend)} {f(dy / 2 - bend)} {f(dx)} {f(dy)}")
    return (f'<path d="{" ".join(out)}" stroke="{color}" stroke-opacity="{alpha}" stroke-width="{width}" '
            f'fill="none" stroke-linecap="round"/>')


def body_flow(x, y):
    # feathers lie down and slightly back along the body
    return 100 + (x - 250) * .15


def wing_feathers():
    s = []
    # primaries: long, dark blue-green, fanned toward the tip
    for i in range(7):
        t = i / 6
        bx, by = 224 + 18 * t, 280 + 30 * t
        tx, ty = 198 + 16 * t + rnd.uniform(-2, 2), 432 - 30 * t
        nx, ny = (ty - by), -(tx - bx)
        ln = math.hypot(nx, ny)
        nx, ny = nx / ln * 8, ny / ln * 8
        d = (f"M{f(bx - nx)} {f(by - ny)} C{f(bx - nx * .6)} {f((by + ty) / 2)} {f(tx - nx * .3)} {f(ty - 18)} {f(tx)} {f(ty)} "
             f"C{f(tx + nx * .5)} {f(ty - 16)} {f(bx + nx * .9)} {f((by + ty) / 2)} {f(bx + nx)} {f(by + ny)} Z")
        s.append(f'<path d="{d}" fill="url(#primary)" stroke="#0B3328" stroke-opacity=".55" stroke-width=".7"/>')
        s.append(f'<path d="M{f(bx)} {f(by)} Q{f((bx + tx) / 2 - 2)} {f((by + ty) / 2)} {f(tx + 1)} {f(ty - 4)}" stroke="#A6E6B0" stroke-opacity=".28" stroke-width=".8" fill="none"/>')
    # secondaries then coverts, lower rows first so upper rows overlap them
    rows = [(300, 6, 15, 22, "url(#covert2)"), (276, 6, 14, 20, "url(#covert2)"), (252, 7, 12, 17, "url(#covert)"),
            (230, 7, 11, 15, "url(#covert)"), (210, 6, 10, 13, "url(#covert)"), (196, 5, 9, 11, "url(#covertHi)")]
    for (y, n, w, h, fill) in rows:
        left = 200 + (y - 170) * 0.01
        right = 248 + 10 * math.sin((y - 150) / 140 * math.pi)
        for k in range(n):
            x = left + (right - left) * (k + .5) / n + rnd.uniform(-1, 1)
            yy = y + rnd.uniform(-1.5, 1.5) + (k % 2) * 3
            d = (f"M{f(x - w / 2)} {f(yy - h * .4)} C{f(x - w / 2)} {f(yy + h * .5)} {f(x - w * .2)} {f(yy + h)} {f(x)} {f(yy + h)} "
                 f"C{f(x + w * .2)} {f(yy + h)} {f(x + w / 2)} {f(yy + h * .5)} {f(x + w / 2)} {f(yy - h * .4)} Z")
            s.append(f'<path d="{d}" fill="{fill}" stroke="#0E4A30" stroke-opacity=".22" stroke-width=".6"/>')
            s.append(f'<path d="M{f(x - w * .38)} {f(yy + h * .6)} Q{f(x)} {f(yy + h * 1.04)} {f(x + w * .38)} {f(yy + h * .6)}" '
                     f'stroke="#C9F7A4" stroke-opacity=".22" stroke-width="1" fill="none"/>')
    return "\n".join(s)


def tail():
    return "\n".join([
        '<path d="M204 362 C190 450 160 556 108 676 C136 566 180 456 224 368 Z" fill="url(#tail1)"/>',
        '<path d="M214 366 C212 460 194 566 170 690 C190 572 226 460 236 370 Z" fill="url(#tail2)"/>',
        '<path d="M222 368 C228 450 228 536 220 606 C240 528 246 446 242 368 Z" fill="url(#tail1)" opacity=".85"/>',
        '<path d="M214 368 C202 466 182 560 154 664" stroke="#C8FFF6" stroke-opacity=".35" stroke-width="1.1" fill="none"/>',
        '<path d="M225 370 C222 468 206 566 186 674" stroke="#C8FFF6" stroke-opacity=".3" stroke-width="1" fill="none"/>',
    ])


def feet():
    return "\n".join([
        '<g fill="url(#foot)" stroke="#4E3C3C" stroke-opacity=".5" stroke-width=".6">',
        '<path d="M238 372 C238 384 234 392 228 396 C233 398 242 396 247 388 C248 382 247 376 246 372 Z"/>',
        '<path d="M245 382 C252 386 259 390 266 390 C263 396 253 397 246 392 Z"/>',
        '<path d="M258 370 C260 382 258 391 253 396 C260 398 267 392 269 384 C269 378 267 373 265 370 Z"/>',
        '<path d="M266 382 C273 385 280 388 285 386 C283 393 275 395 268 392 Z"/>',
        '</g>',
        '<g fill="#2A2020"><path d="M227 396 l-3 3 l5 -1 Z"/><path d="M266 390 l4 2 l-4 1 Z"/><path d="M253 396 l-2 3 l4 -1 Z"/></g>',
    ])


def parrot():
    p = []
    p.append('<g class="tail">' + tail() + '</g>')
    p.append('<g class="breathe">')
    p.append(f'<path d="{SILHOUETTE}" fill="url(#bodyG)"/>')
    p.append('<g clip-path="url(#birdClip)">')
    # head colour: lime crown, blue-grey nape, light belly, dark back
    p.append('<ellipse cx="252" cy="88" rx="46" ry="34" fill="#B9EE6E" opacity=".9" filter="url(#blur8)"/>')
    p.append('<ellipse cx="258" cy="70" rx="26" ry="10" fill="#F4FFD0" opacity=".55" filter="url(#blur8)"/>')
    p.append('<ellipse cx="208" cy="128" rx="20" ry="34" fill="#7DB9D2" opacity=".7" filter="url(#blur8)"/>')
    p.append('<ellipse cx="292" cy="290" rx="22" ry="70" fill="#D8F590" opacity=".6" filter="url(#blur8)"/>')
    p.append('<ellipse cx="196" cy="270" rx="18" ry="110" fill="#0B3F28" opacity=".6" filter="url(#blur8)"/>')
    p.append('<ellipse cx="250" cy="372" rx="50" ry="16" fill="#0B3F28" opacity=".5" filter="url(#blur8)"/>')
    p.append('<ellipse cx="270" cy="128" rx="22" ry="12" fill="#2E8C45" opacity=".45" filter="url(#blur8)"/>')
    # painted feather texture
    p.append(painted_strokes(260, (192, 150, 308, 372), "#E8FFB4", .16, 1.4, 9, body_flow))
    p.append(painted_strokes(260, (192, 150, 308, 372), "#145C34", .2, 1.4, 9, body_flow))
    p.append(painted_strokes(140, (200, 64, 296, 160), "#F2FFD2", .14, 1.1, 6, lambda x, y: 150 + (x - 250) * .4))
    p.append(painted_strokes(140, (200, 64, 296, 160), "#1E6E3C", .14, 1.1, 6, lambda x, y: 150 + (x - 250) * .4))
    p.append(f'<path d="{SILHOUETTE}" fill="#000" filter="url(#grainF)" opacity=".12"/>')
    # black chin stripe and rose collar, on the neck
    p.append('<path d="M293 160 C287 180 268 190 248 191" stroke="#0E0E10" stroke-width="6" fill="none" stroke-linecap="round"/>')
    p.append('<path d="M249 196 C228 194 210 176 199 150" stroke="#FF8FB8" stroke-width="6.5" fill="none" stroke-linecap="round"/>')
    p.append('<path d="M249 196 C228 194 210 176 199 150" stroke="#FFD3E3" stroke-width="1.3" fill="none" opacity=".7"/>')
    p.append('<path d="M247 191 C226 189 208 172 198 146" stroke="#0E0E10" stroke-width="2.2" fill="none" opacity=".85"/>')
    p.append('</g>')
    p.append('</g>')
    p.append(feet())
    # wing
    p.append('<g class="wing">')
    p.append(f'<path d="{WING}" fill="url(#wingG)" filter="url(#wingShadow)"/>')
    p.append('<g clip-path="url(#wingClip)">' + wing_feathers() +
             '<ellipse cx="200" cy="290" rx="14" ry="120" fill="#06281A" opacity=".45" filter="url(#blur8)"/>'
             '<ellipse cx="244" cy="190" rx="16" ry="40" fill="#D5FFA8" opacity=".2" filter="url(#blur8)"/></g>')
    p.append('</g>')
    # head details that move with the head
    p.append('<g class="head">')
    p.append('<path d="M283 92 C288 86 296 86 299 92 C294 95 288 96 283 94 Z" fill="#7E9B5A"/>')
    p.append(f'<path d="{BEAK_LO}" fill="url(#beakLo)"/>')
    p.append(f'<path d="{BEAK_UP}" fill="url(#beakUp)"/>')
    p.append('<path d="M297 92 C317 88 334 100 336 122" stroke="#FFD0CB" stroke-width="2.6" fill="none" stroke-linecap="round" opacity=".8"/>')
    p.append('<path d="M292 136 C304 135 314 142 318 155" stroke="#5A0C14" stroke-width="1.1" fill="none" opacity=".6"/>')
    p.append('<circle cx="294" cy="96" r="1.4" fill="#3B2A1A"/>')
    p.append('<g class="eye">')
    p.append('<ellipse cx="262" cy="104" rx="10.5" ry="10" fill="#FF7A33"/>')
    p.append('<ellipse cx="262" cy="104" rx="8" ry="7.8" fill="url(#iris)"/>')
    p.append('<circle class="pupil" cx="263.2" cy="104" r="3.8" fill="#07090A"/>')
    p.append('<circle cx="265.6" cy="101" r="2" fill="#fff"/>')
    p.append('<circle cx="259.8" cy="107.5" r=".9" fill="#fff" opacity=".8"/>')
    p.append('<path class="lid" d="M250 104 C251 92 273 92 274 104 C273 97 251 97 250 104 Z" fill="#8FDC5C"/>')
    p.append('</g>')
    p.append('</g>')
    # rim light from the sunset behind
    p.append('<g clip-path="url(#birdClip)" class="rim">')
    p.append(f'<path d="{SILHOUETTE}" fill="none" stroke="url(#rimG)" stroke-width="7" filter="url(#blur3)"/>')
    p.append('</g>')
    return "\n".join(p)


# ---------------------------------------------------------------- speech + product

PHRASES = [
    ("Samajh aaya?", "ROMAN-URDU", "lat"),
    ("سمجھ آیا؟", "URDU", "ur"),
    ("समझ आया?", "HINDI", "hi"),
    ("Got it?", "ENGLISH", "lat"),
    ("Duidelijk?", "NEDERLANDS", "lat"),
]
CYCLE = 15


def speech():
    s = []
    bx, by, bw, bh = 470, 64, 300, 112
    # particles streaming from the beak to the bubble
    s.append('<g filter="url(#glow)">')
    for i in range(14):
        d = f"M448 166 C470 {150 + rnd.uniform(-20, 20):.0f} 480 {130 + rnd.uniform(-20, 20):.0f} {500 + rnd.uniform(0, 40):.0f} {150 + rnd.uniform(-10, 18):.0f}"
        dur = rnd.uniform(1.6, 2.6)
        s.append(f'<circle r="{f(rnd.uniform(1, 2.2))}" fill="#BFFFE0"><animateMotion dur="{f(dur)}s" repeatCount="indefinite" begin="{f(i * 0.17)}s" path="{d}"/>'
                 f'<animate attributeName="opacity" values="0;1;0" dur="{f(dur)}s" repeatCount="indefinite" begin="{f(i * 0.17)}s"/></circle>')
    s.append('</g>')
    # glass bubble
    s.append('<g class="bubble">')
    s.append(f'<path d="M{bx + 22} {by} h{bw - 44} a22 22 0 0 1 22 22 v{bh - 44} a22 22 0 0 1 -22 22 h{-(bw - 92)} '
             f'l-34 26 l6 -26 h-8 a22 22 0 0 1 -22 -22 v{-(bh - 44)} a22 22 0 0 1 22 -22 z" fill="url(#glass)" stroke="url(#glassEdge)" stroke-width="1.5"/>')
    s.append(f'<rect x="{bx + 14}" y="{by + 8}" width="{bw - 28}" height="30" rx="15" fill="#fff" opacity=".07"/>')
    cx = bx + bw / 2
    for i, (txt, lab, kind) in enumerate(PHRASES):
        b = i * CYCLE / len(PHRASES)
        cls = {"ur": "say ur", "hi": "say hi"}.get(kind, "say")
        s.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.03;.18;.2;1" dur="{CYCLE}s" begin="{f(b)}s" repeatCount="indefinite"/>')
        s.append(f'<clipPath id="wipe{i}"><rect x="{bx}" y="{by}" height="{bh}" width="0">'
                 f'<animate attributeName="width" values="0;{bw};{bw}" keyTimes="0;.06;1" dur="{CYCLE}s" begin="{f(b)}s" repeatCount="indefinite"/></rect></clipPath>')
        s.append(f'<g clip-path="url(#wipe{i})">')
        y = by + 66 if kind == "lat" else by + 64
        s.append(f'<text class="{cls}" x="{f(cx)}" y="{y}" text-anchor="middle"{" direction=\"rtl\"" if kind == "ur" else ""}>{txt}</text>')
        s.append(f'<text class="lang" x="{f(cx)}" y="{by + 92}" text-anchor="middle">{lab}</text>')
        s.append('</g>')
        s.append(f'<rect y="{by + 10}" width="3" height="{bh - 20}" rx="1.5" fill="#BFFFE0" filter="url(#glow)" opacity="0">'
                 f'<animate attributeName="x" values="{bx};{bx + bw};{bx + bw}" keyTimes="0;.06;1" dur="{CYCLE}s" begin="{f(b)}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.03;.065;1" dur="{CYCLE}s" begin="{f(b)}s" repeatCount="indefinite"/></rect>')
        s.append('</g>')
    s.append('</g>')
    return "\n".join(s)


TERM = 14  # seconds per terminal loop


def term_line(i, x, y, parts, start, dur, end=TERM - 1.0, chars=44):
    """A line typed out by a growing clip, from `start` for `dur` seconds."""
    width = chars * 9.1
    k0, k1, k2, k3 = start / TERM, (start + dur) / TERM, end / TERM, min((end + .6) / TERM, 1)
    out = [f'<clipPath id="tl{i}"><rect x="{x - 2}" y="{y - 15}" height="21" width="0">'
           f'<animate attributeName="width" values="0;0;{f(width)};{f(width)};{f(width)}" keyTimes="0;{f(k0)};{f(k1)};{f(k2)};1" dur="{TERM}s" repeatCount="indefinite"/></rect></clipPath>',
           f'<g clip-path="url(#tl{i})"><g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{f(k2)};{f(k3)};1" dur="{TERM}s" repeatCount="indefinite"/>',
           f'<text class="mono" x="{x}" y="{y}">{parts}</text></g></g>']
    return "\n".join(out)


def terminal():
    x, y, w, h = 790, 172, 452, 236
    s = [f'<g class="term">',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#0A1416" fill-opacity=".86" stroke="#FFFFFF" stroke-opacity=".12"/>',
         f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="14" fill="#FFFFFF" fill-opacity=".05"/>',
         f'<circle cx="{x + 18}" cy="{y + 15}" r="5" fill="#FF5F57"/><circle cx="{x + 34}" cy="{y + 15}" r="5" fill="#FEBC2E"/><circle cx="{x + 50}" cy="{y + 15}" r="5" fill="#28C840"/>',
         f'<text class="mono dim" x="{x + w / 2}" y="{y + 19}" text-anchor="middle" style="font-size:12px">claude · shoga-speaks · Roman-Urdu · PO</text>']
    lx, ly = x + 18, y + 56
    L = [
        ('<tspan class="dim">&gt; </tspan>Is PR #482 ok to release?', 0.3, 1.0),
        ('<tspan class="ok">●</tspan> <tspan class="b">Release mat karein.</tspan> Do problems hain:', 1.8, 1.2),
        ('  <tspan class="dim">·</tspan> SQL injection: data leak ho sakta hai', 3.1, 1.1),
        ('  <tspan class="dim">·</tspan> N+1 query: 500 orders pe page slow', 4.3, 1.0),
    ]
    for i, (t, st, du) in enumerate(L):
        s.append(term_line(i, lx, ly + i * 24, t, st, du))
    # "▸ English" that flips to "▾ English" and unfolds the translation
    fy = ly + 4 * 24
    k = lambda t: f(t / TERM)
    s.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{k(5.5)};{k(5.7)};{k(7.2)};{k(7.25)};1" dur="{TERM}s" repeatCount="indefinite"/>'
             f'<text class="mono acc" x="{lx + 16}" y="{fy}">▸ English</text></g>')
    s.append(f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{k(7.2)};{k(7.25)};{k(TERM - 1)};{k(TERM - .4)};1" dur="{TERM}s" repeatCount="indefinite"/>'
             f'<text class="mono acc" x="{lx + 16}" y="{fy}">▾ English</text></g>')
    # click ripple on the toggle
    s.append(f'<circle cx="{lx + 22}" cy="{fy - 5}" r="0" fill="none" stroke="#5BD08A" stroke-width="2" opacity="0">'
             f'<animate attributeName="r" values="0;0;14;14" keyTimes="0;{k(7.0)};{k(7.6)};1" dur="{TERM}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="0;{k(7.0)};{k(7.05)};{k(7.6)};1" dur="{TERM}s" repeatCount="indefinite"/></circle>')
    s.append(term_line(10, lx + 16, fy + 24, '<tspan class="en">Don\'t release: a data-leak risk and a</tspan>', 7.5, 1.0))
    s.append(term_line(11, lx + 16, fy + 46, '<tspan class="en">page that gets slow with 500+ orders.</tspan>', 8.5, 1.0))
    # blinking cursor
    s.append(f'<rect class="cursor" x="{lx}" y="{fy + 60}" width="9" height="15" fill="#5BD08A"/>')
    s.append('</g>')
    return "\n".join(s)


def chips(x, y):
    names = ["Dev", "QA", "DevOps", "PO", "PM", "Support"]
    s, cx = [], x
    for i, n in enumerate(names):
        w = 22 + len(n) * 10
        s.append(f'<g class="chip c{i}" transform="translate({cx} {y})"><rect width="{w}" height="30" rx="15"/>'
                 f'<text x="{w / 2}" y="20" text-anchor="middle">{n}</text></g>')
        cx += w + 8
    return "\n".join(s)


# ---------------------------------------------------------------- defs + css

DEFS = """
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#070B1F"/><stop offset=".45" stop-color="#14254A"/>
  <stop offset=".68" stop-color="#3A3F6B"/><stop offset=".78" stop-color="#C46A4F"/><stop offset=".86" stop-color="#F2A65A"/>
</linearGradient>
<radialGradient id="sun" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="#FFE3A3" stop-opacity=".95"/><stop offset=".25" stop-color="#FFB86B" stop-opacity=".55"/>
  <stop offset=".6" stop-color="#E0745A" stop-opacity=".18"/><stop offset="1" stop-color="#E0745A" stop-opacity="0"/>
</radialGradient>
<linearGradient id="ray" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#FFE0B0" stop-opacity=".35"/><stop offset="1" stop-color="#FFE0B0" stop-opacity="0"/></linearGradient>
<linearGradient id="m1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6C6D99"/><stop offset="1" stop-color="#3A3D66"/></linearGradient>
<linearGradient id="snow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFF1E2"/><stop offset=".12" stop-color="#FFE7D0" stop-opacity=".4"/><stop offset=".2" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="m2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E3156"/><stop offset="1" stop-color="#1C2140"/></linearGradient>
<linearGradient id="m3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14192F"/><stop offset="1" stop-color="#0B0F1F"/></linearGradient>
<linearGradient id="lake" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3B3358"/><stop offset=".4" stop-color="#161C35"/><stop offset="1" stop-color="#070A16"/></linearGradient>
<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#C9A7C7" stop-opacity="0"/><stop offset=".6" stop-color="#C9A7C7" stop-opacity=".22"/><stop offset="1" stop-color="#C9A7C7" stop-opacity="0"/></linearGradient>
<linearGradient id="shade" x1="0" y1="0" x2="1" y2="0"><stop offset=".5" stop-color="#050A12" stop-opacity="0"/><stop offset=".64" stop-color="#050A12" stop-opacity=".55"/><stop offset="1" stop-color="#050A12" stop-opacity=".82"/></linearGradient>
<radialGradient id="vignette" cx=".45" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>

<linearGradient id="bark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7A5236"/><stop offset=".5" stop-color="#4E321F"/><stop offset="1" stop-color="#24160D"/></linearGradient>
<linearGradient id="leafShade" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".25"/><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".3"/></linearGradient>

<radialGradient id="headG" cx=".62" cy=".3" r=".8"><stop offset="0" stop-color="#C8F57A"/><stop offset=".45" stop-color="#7DD653"/><stop offset="1" stop-color="#2E9447"/></radialGradient>
<linearGradient id="bodyG" x1=".3" y1="0" x2=".7" y2="1"><stop offset="0" stop-color="#8FDD5E"/><stop offset=".35" stop-color="#5EC257"/><stop offset=".75" stop-color="#3A9E50"/><stop offset="1" stop-color="#226F45"/></linearGradient>
<linearGradient id="wingG" x1="0" y1="0" x2=".3" y2="1"><stop offset="0" stop-color="#4DB257"/><stop offset=".6" stop-color="#2A8848"/><stop offset="1" stop-color="#1A5E4A"/></linearGradient>
<linearGradient id="covert" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5CC25B"/><stop offset="1" stop-color="#2E8C4A"/></linearGradient>
<linearGradient id="covertHi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7FD86A"/><stop offset="1" stop-color="#43A653"/></linearGradient>
<linearGradient id="covert2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FA453"/><stop offset="1" stop-color="#1E6E48"/></linearGradient>
<linearGradient id="primary" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2F9A50"/><stop offset=".7" stop-color="#1F6E57"/><stop offset="1" stop-color="#174B66"/></linearGradient>
<linearGradient id="tail1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3AA35A"/><stop offset=".45" stop-color="#2C8A86"/><stop offset="1" stop-color="#2C6FA8"/></linearGradient>
<linearGradient id="tail2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#55BE6A"/><stop offset=".5" stop-color="#3FA7A3"/><stop offset="1" stop-color="#4C8FD0"/></linearGradient>
<linearGradient id="beakUp" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="#FF5A5F"/><stop offset=".5" stop-color="#E02A3A"/><stop offset="1" stop-color="#9E1424"/></linearGradient>
<linearGradient id="beakLo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7A1424"/><stop offset="1" stop-color="#2E0A10"/></linearGradient>
<radialGradient id="iris" cx=".45" cy=".4" r=".6"><stop offset="0" stop-color="#FFFBEA"/><stop offset=".7" stop-color="#F2E3A2"/><stop offset="1" stop-color="#C9A94F"/></radialGradient>
<linearGradient id="foot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B8A3A0"/><stop offset="1" stop-color="#7C6664"/></linearGradient>
<linearGradient id="rimG" x1="0" y1="0" x2="1" y2=".2"><stop offset="0" stop-color="#9FD8FF" stop-opacity=".55"/><stop offset=".45" stop-color="#FFE3B0" stop-opacity=".05"/><stop offset=".75" stop-color="#FFC27A" stop-opacity=".7"/><stop offset="1" stop-color="#FFB060" stop-opacity="1"/></linearGradient>

<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E9FFF6" stop-opacity=".22"/><stop offset="1" stop-color="#9FE8C8" stop-opacity=".08"/></linearGradient>
<linearGradient id="glassEdge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".75"/><stop offset=".5" stop-color="#7FF0C0" stop-opacity=".35"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".1"/></linearGradient>
<linearGradient id="word" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#E9FFF1"/><stop offset=".55" stop-color="#9BF0B4"/><stop offset="1" stop-color="#FFD58A"/></linearGradient>
<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>

<filter id="wingShadow" x="-30%" y="-10%" width="160%" height="130%"><feGaussianBlur in="SourceAlpha" stdDeviation="5"/><feOffset dx="4" dy="5"/><feComponentTransfer><feFuncA type="linear" slope=".45"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="10"/></filter>
<filter id="haze" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="1.2"/></filter>
<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="blur3" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grainF" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.4 1.1"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="barkTex" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".02 .35" numOctaves="3" seed="9"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.2"/><feComposite in2="SourceGraphic" operator="in"/></filter>
<filter id="filmGrain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".75" numOctaves="2" seed="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .5 -.18"/></filter>
<filter id="dropShadow" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur in="SourceAlpha" stdDeviation="10"/><feOffset dy="12"/><feComponentTransfer><feFuncA type="linear" slope=".45"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
"""

CSS = """
.say { font: 700 36px/1 Inter, "Segoe UI", system-ui, -apple-system, Roboto, sans-serif; fill: #F4FFF9; }
.say.ur { font-family: "Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", "Noto Naskh Arabic", "Segoe UI", "Geeza Pro", sans-serif; font-size: 34px; }
.say.hi { font-family: "Noto Sans Devanagari", "Nirmala UI", "Kohinoor Devanagari", "Segoe UI", sans-serif; }
.lang { font: 600 12px/1 Inter, "Segoe UI", system-ui, sans-serif; fill: #9FF0C8; letter-spacing: 2px; }
.tag { font: 500 20px/1.3 Inter, "Segoe UI", system-ui, -apple-system, Roboto, sans-serif; fill: #CFE6DD; }
.tag b { font-weight: 700; fill: #FFFFFF; }
.langs { font: 500 15px/1 Inter, "Segoe UI", system-ui, sans-serif; fill: #8FB3A8; }
.mono { font: 500 14.5px/1 "SF Mono", Menlo, Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace; fill: #E7F2EE; white-space: pre; }
.mono .dim, .mono.dim { fill: #7F948E; } .mono .ok { fill: #5BD08A; } .mono .b { font-weight: 700; fill: #FFFFFF; }
.mono.acc { fill: #5BD08A; font-weight: 700; } .mono .en { fill: #A9E7FF; }
.chip rect { fill: #FFFFFF; fill-opacity: .06; stroke: #FFFFFF; stroke-opacity: .16; }
.chip text { font: 600 14px/1 Inter, "Segoe UI", system-ui, sans-serif; fill: #DDEFE7; }
.chip { opacity: .5; animation: lit 12s infinite; }
.c1 { animation-delay: 2s; } .c2 { animation-delay: 4s; } .c3 { animation-delay: 6s; } .c4 { animation-delay: 8s; } .c5 { animation-delay: 10s; }
@keyframes lit { 0%, 15% { opacity: 1; } 18%, 100% { opacity: .5; } }

.tw { animation: tw 4s ease-in-out infinite; } .tw1 { animation-duration: 5.5s; } .tw2 { animation-duration: 3.2s; animation-delay: 1s; } .tw3 { animation-duration: 6.4s; animation-delay: 2s; }
@keyframes tw { 0%, 100% { opacity: .15; } 50% { opacity: .9; } }
.ray { animation: ray 9s ease-in-out infinite; } .r1 { animation-delay: 2s; } .r2 { animation-delay: 4s; } .r3 { animation-delay: 1s; } .r4 { animation-delay: 6s; }
@keyframes ray { 0%, 100% { opacity: .35; } 50% { opacity: 1; } }
.sh { animation: sh 3s ease-in-out infinite; } .sh1 { animation-delay: 1s; } .sh2 { animation-delay: 2s; }
@keyframes sh { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(14px); } }
.fog { animation: fog 18s ease-in-out infinite; }
@keyframes fog { 0%, 100% { transform: translateX(-30px); } 50% { transform: translateX(30px); } }
.ff { animation: ff 7s ease-in-out infinite; } .ff1 { animation-duration: 9s; animation-delay: 1s; } .ff2 { animation-duration: 6s; animation-delay: 2s; } .ff3 { animation-duration: 11s; animation-delay: .5s; } .ff4 { animation-duration: 8s; animation-delay: 3s; }
@keyframes ff { 0%, 100% { transform: translate(0, 0); opacity: .1; } 25% { opacity: 1; } 50% { transform: translate(18px, -26px); opacity: .5; } 75% { opacity: 1; } }

.breathe { transform-origin: 250px 376px; animation: breathe 3.4s ease-in-out infinite; }
@keyframes breathe { 0%, 100% { transform: scale(1, 1); } 50% { transform: scale(1.012, 1.018); } }
.head { transform-origin: 250px 150px; animation: tilt 9s ease-in-out infinite; }
@keyframes tilt { 0%, 12%, 100% { transform: rotate(0deg); } 18%, 34% { transform: rotate(-9deg) translate(2px, -2px); }
  40% { transform: rotate(4deg); } 48%, 60% { transform: rotate(2deg); } 66% { transform: rotate(0deg); }
  80% { transform: rotate(-3deg); } 84% { transform: rotate(1deg); } }
.lid { transform-origin: 262px 104px; transform: scaleY(0); animation: blink 4.6s infinite; }
@keyframes blink { 0%, 90%, 100% { transform: scaleY(0); } 93% { transform: scaleY(1.9); } 96% { transform: scaleY(0); } }
.pupil { transform-origin: 263.2px 104px; animation: pupil 6s ease-in-out infinite; }
@keyframes pupil { 0%, 100% { transform: scale(1); } 50% { transform: scale(.72); } }
.wing { transform-origin: 220px 184px; animation: wing 9s ease-in-out infinite; }
@keyframes wing { 0%, 70%, 100% { transform: rotate(0deg); } 74% { transform: rotate(-5deg); } 77% { transform: rotate(1deg); } 80% { transform: rotate(-3deg); } 84% { transform: rotate(0deg); } }
.tail { transform-origin: 222px 368px; animation: sway 6s ease-in-out infinite; }
@keyframes sway { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(2.2deg); } }
.rim { animation: rim 6s ease-in-out infinite; } @keyframes rim { 0%, 100% { opacity: .85; } 50% { opacity: 1; } }
.bubble { animation: float 6s ease-in-out infinite; } @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
.shine { animation: shine 7s ease-in-out infinite; } @keyframes shine { 0%, 55% { transform: translateX(-260px); } 85%, 100% { transform: translateX(620px); } }
.cursor { animation: cur 1s steps(1) infinite; }
.boat { animation: bob 5s ease-in-out infinite; } @keyframes bob { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(2px) rotate(-.6deg); } }
.lantern { animation: flick 2.2s ease-in-out infinite; } @keyframes flick { 0%, 100% { opacity: 1; } 40% { opacity: .7; } 60% { opacity: .95; } } @keyframes cur { 50% { opacity: 0; } }

@media (prefers-reduced-motion: reduce) {
  *, .leaf { animation: none !important; }
  .leaf { display: none; }
}
"""


def banner():
    word_d, word_w = text_path("Shoga-Speaks", 70, 0, 0, tracking=-1.2)
    scale = min(1.0, 452 / word_w)
    wx, wy = 790, 118
    dash_d, _ = text_path("Shoga", 70, 0, 0, tracking=-1.2)  # width of "Shoga" for the green dash
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Shoga-Speaks</title>',
        '<desc id="d">A green Kashmiri parrot on a chinar branch at dusk asks "Did you understand?" in Roman-Urdu, Urdu, Hindi, English and Dutch, '
        'while a Claude Code terminal answers a question in Roman-Urdu and unfolds the English. Shoga-Speaks is a Claude Code plugin that explains '
        'things in your language, your script and for your role.</desc>',
        '<defs>', DEFS,
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="26"/></clipPath>',
        f'<clipPath id="wingClip"><path d="{WING}"/></clipPath>',
        f'<clipPath id="birdClip"><path d="{SILHOUETTE}"/></clipPath>',
        '<clipPath id="branchClip"><path d="M-30 452 C80 446 170 432 250 428 C330 424 420 414 520 392 L524 404 C430 428 340 440 252 444 C170 448 80 466 -30 474 Z"/></clipPath>',
        f'<clipPath id="wordClip"><path transform="translate({wx} {wy}) scale({f(scale)})" d="{word_d}"/></clipPath>',
        '</defs>',
        '<g clip-path="url(#card)">',
        scene(),
        fireflies(),
        leaves(),
        '<style>' + CSS + '\n'.join(LEAF_CSS) + '</style>',
        '<rect width="1280" height="540" fill="url(#shade)"/>',
        branch(),
        '<g transform="translate(44 -32) scale(1.2)">', parrot(), '</g>',
        speech(),
        # wordmark: outlined Inter Display, gradient fill and a passing shine
        f'<g filter="url(#dropShadow)"><path transform="translate({wx} {wy}) scale({f(scale)})" d="{word_d}" fill="url(#word)"/></g>',
        f'<g clip-path="url(#wordClip)"><rect class="shine" x="{wx}" y="{wy - 70}" width="120" height="90" fill="url(#shine)" opacity=".55" transform="skewX(-20)"/></g>',
        f'<text class="tag" x="{wx + 2}" y="{wy + 36}">Claude Code, explained <tspan font-weight="700" fill="#fff">your way</tspan>.</text>',
        terminal(),
        chips(wx, 422),
        f'<text class="langs" x="{wx + 2}" y="482">Roman-Urdu · اردو · Hinglish · हिन्दी · Nederlands · English</text>',
        f'<text class="langs" x="{wx + 2}" y="508" style="fill:#6E8C83;font-size:13px">A plugin for Claude Code</text>',
        '<rect width="1280" height="540" fill="url(#vignette)" pointer-events="none"/>',
        '<rect width="1280" height="540" filter="url(#filmGrain)" opacity=".5" pointer-events="none"/>',
        '</g>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="26" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>',
        '</svg>',
    ]
    return "\n".join(parts)


def logo():
    """Square badge: the parakeet close up, with a bubble that cycles A · ع · अ."""
    glyphs = [("A", "lat"), ("ع", "ur"), ("अ", "hi")]
    bubble = ['<g transform="translate(318 58)"><g class="bubble">',
              '<path d="M24 0 h112 a24 24 0 0 1 24 24 v58 a24 24 0 0 1 -24 24 h-70 l-40 30 l10 -30 h-12 a24 24 0 0 1 -24 -24 v-58 a24 24 0 0 1 24 -24 z" '
              'fill="url(#glass)" stroke="url(#glassEdge)" stroke-width="2"/>']
    for i, (g, kind) in enumerate(glyphs):
        cls = {"ur": "say ur", "hi": "say hi"}.get(kind, "say")
        bubble.append(f'<text class="{cls}" x="80" y="{70 if kind == "lat" else 68}" text-anchor="middle" style="font-size:56px" opacity="0">{g}'
                      f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.3;.34;1" dur="9s" begin="{i * 3}s" repeatCount="indefinite"/></text>')
    bubble.append('</g></g>')
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-labelledby="t">',
        '<title id="t">Shoga-Speaks: a green Kashmiri parrot with a speech bubble</title>',
        '<defs>', DEFS,
        '<clipPath id="card"><circle cx="256" cy="256" r="250"/></clipPath>',
        f'<clipPath id="wingClip"><path d="{WING}"/></clipPath>',
        f'<clipPath id="birdClip"><path d="{SILHOUETTE}"/></clipPath>',
        '<clipPath id="branchClip"><path d="M-30 452 C80 446 170 432 250 428 C330 424 420 414 520 392 L524 404 C430 428 340 440 252 444 C170 448 80 466 -30 474 Z"/></clipPath>',
        '</defs>',
        f'<style>{CSS}</style>',
        '<g clip-path="url(#card)">',
        '<rect width="512" height="512" fill="#070B1F"/>',
        '<g transform="translate(-132 34) scale(.92)">', scene(), fireflies(), branch(),
        '<g transform="translate(44 -32) scale(1.2)">', parrot(), '</g>', '</g>',
        "\n".join(bubble),
        '<rect width="512" height="512" filter="url(#filmGrain)" opacity=".45"/>',
        '</g>',
        '<circle cx="256" cy="256" r="249" fill="none" stroke="#9BF0B4" stroke-opacity=".35" stroke-width="2"/>',
        '</svg>',
    ])


if __name__ == "__main__":
    svg = banner()
    with open(os.path.join(OUT, "banner.svg"), "w") as fh:
        fh.write(svg)
    print(f"banner.svg: {len(svg) / 1024:.0f} KB")
    svg = logo()
    with open(os.path.join(OUT, "logo.svg"), "w") as fh:
        fh.write(svg)
    print(f"logo.svg: {len(svg) / 1024:.0f} KB")
