#!/usr/bin/env python3
"""Builds assets/banner.svg and assets/logo.svg: the Shoga mascot.

    pip install fonttools
    python3 assets/src/build.py

Vector only, no external files. Light and dark palettes follow the viewer's colour
scheme. Animation is CSS and stops under reduced motion.
"""
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
FONT = os.environ.get("SHOGA_FONT", "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf")
SANS = "Inter, 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif"


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def text_path(text, size, x, y, tracking=0.0, font=FONT):
    font = TTFont(font)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen, cx = SVGPathPen(gs), 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        if not name:
            continue
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + cx, y)))
        cx += gs[name].width * scale + tracking
    return pen.getCommands(), cx - tracking


# ---------------------------------------------------------------- the mascot
# A chubby rose-ringed parakeet facing right. Outlines are drawn first as a thick
# stroke under the fills, so head and body read as one shape.

BODY = "M170 150 C242 150 272 220 270 282 C268 346 226 392 170 392 C112 392 72 346 72 282 C72 216 104 150 170 150 Z"
HEAD = "M190 40 C246 40 290 84 290 138 C290 192 246 232 190 232 C134 232 92 192 92 138 C92 84 134 40 190 40 Z"
TAIL = "M118 318 C96 360 74 400 54 452 C78 446 94 432 104 412 C112 438 130 452 150 456 C146 410 146 366 152 330 Z"
WING = "M104 238 C132 226 170 238 186 272 C200 304 194 348 168 380 C150 360 120 352 100 330 C84 304 84 262 104 238 Z"
BEAK_UP = "M266 104 C300 92 340 112 342 150 C344 176 332 196 314 206 C318 188 314 174 302 168 C294 164 284 164 276 168 Z"
BEAK_LO = "M276 168 C288 166 302 172 306 186 C300 198 286 202 272 194 Z"
FEET = ("M140 384 C138 398 132 406 124 410 C132 414 146 410 152 400 Z "
        "M184 386 C184 400 180 408 172 412 C180 416 194 412 198 402 Z")


def mascot(talk=True):
    o = 'stroke="#15301F" stroke-linejoin="round" stroke-linecap="round"'
    parts = [
        '<g class="tail">',
        f'<path d="{TAIL}" fill="url(#tailG)" {o} stroke-width="9"/>',
        f'<path d="{TAIL}" fill="url(#tailG)"/>',
        '<path d="M120 336 C108 376 92 412 72 444" stroke="#BFF5EA" stroke-width="3" stroke-opacity=".6" fill="none" stroke-linecap="round"/>',
        '</g>',
        '<g class="bod">',
        # outline layer
        f'<g fill="#15301F" {o} stroke-width="11"><path d="{BODY}"/><path d="{HEAD}"/></g>',
        f'<path d="{FEET}" fill="#F6A38A" {o} stroke-width="6"/>',
        # fills
        f'<path d="{BODY}" fill="#4CC764"/>',
        f'<path d="{HEAD}" fill="#5BD46E"/>',
        '<clipPath id="mClip"><path d="' + BODY + '"/><path d="' + HEAD + '"/></clipPath>',
        '<g clip-path="url(#mClip)">',
        '<ellipse cx="214" cy="300" rx="52" ry="74" fill="#B4EC78"/>',
        '<path d="M60 300 C90 380 150 410 240 400 L260 430 L40 430 Z" fill="#2E9F55" opacity=".55"/>',
        '<path d="M92 160 C100 210 140 236 190 236 C150 250 100 230 84 190 Z" fill="#2E9F55" opacity=".45"/>',
        '<path d="M96 110 C100 80 120 58 146 50 C126 74 118 104 122 136 C112 132 100 124 96 110 Z" fill="#6FC3C9" opacity=".45"/>',
        '<path d="M150 62 C176 50 214 50 238 62" stroke="#E9FFC2" stroke-width="9" fill="none" stroke-linecap="round" opacity=".6"/>',
        # chin stripe and rose ring
        '<path d="M282 196 C258 236 190 246 116 210" stroke="#15301F" stroke-width="9" fill="none" stroke-linecap="round"/>',
        '<path d="M280 212 C254 254 184 262 104 222" stroke="#FF8DB8" stroke-width="10" fill="none" stroke-linecap="round"/>',
        '</g>',
        # wing
        f'<path d="{WING}" fill="#33A956" {o} stroke-width="5"/>',
        '<path d="M110 326 C124 316 140 318 152 330 M122 350 C136 342 150 344 160 354 M104 300 C118 292 134 294 146 304" '
        'stroke="#15301F" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".55"/>',
        '<path d="M112 250 C132 242 156 250 168 268" stroke="#9BE79A" stroke-width="4" fill="none" stroke-linecap="round" opacity=".7"/>',
        '</g>',
        # head features
        '<g class="headf">',
        '<g class="eye">',
        '<circle cx="222" cy="122" r="27" fill="#fff" stroke="#FF8A3D" stroke-width="6"/>',
        '<circle cx="222" cy="122" r="31" fill="none" stroke="#15301F" stroke-width="3"/>',
        '<circle class="pupil" cx="228" cy="125" r="15" fill="#15301F"/>',
        '<circle cx="234" cy="116" r="6" fill="#fff"/><circle cx="222" cy="133" r="2.6" fill="#fff"/>',
        '<path class="lid" d="M190 122 C192 88 252 88 254 122 Z" fill="#5BD46E" stroke="#15301F" stroke-width="3"/>',
        '</g>',
        f'<g class="jaw"><path d="{BEAK_LO}" fill="#8E1428" {o} stroke-width="5"/></g>',
        f'<path d="{BEAK_UP}" fill="url(#beakG)" {o} stroke-width="5"/>',
        '<path d="M280 108 C304 102 328 116 334 140" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>',
        '<circle cx="276" cy="112" r="3" fill="#15301F"/>',
        '</g>',
    ]
    if talk:
        parts.append('<g class="talk" stroke="#15301F" stroke-width="5" stroke-linecap="round" fill="none">'
                     '<path d="M358 150 L376 140"/><path d="M362 172 L384 172"/><path d="M358 194 L376 204"/></g>')
    return "\n".join(parts)


# ---------------------------------------------------------------- speech bubbles

BUBBLES = [
    ("Dev", "#22A35A", "Roman-Urdu", "N+1 query hai: ek hi query mein lao."),
    ("QA", "#2F7FE0", "Nederlands", "Test met een klant met 500+ orders."),
    ("PO", "#E08A12", "English", "Hold the release: two risks, small fix."),
]


def bubble(i, x, y, w=500, h=96):
    role, color, lang, text = BUBBLES[i]
    cw = 24 + len(role) * 12
    return f'''<g class="bub b{i}">
<g class="bubIn">
<path d="M{x + 22} {y} h{w - 44} a22 22 0 0 1 22 22 v{h - 44} a22 22 0 0 1 -22 22 h{-(w - 44)} a22 22 0 0 1 -22 -22 v{-(h - 66)} l-18 -6 l18 -10 v-6 a22 22 0 0 1 22 -22 z"
 class="bubFill" stroke="#15301F" stroke-width="3.5" stroke-linejoin="round"/>
<rect x="{x + 22}" y="{y + 18}" width="{cw}" height="26" rx="13" fill="{color}"/>
<text x="{x + 22 + cw / 2}" y="{y + 36}" text-anchor="middle" style="font: 700 14px/1 {SANS}; fill: #fff">{role}</text>
<text x="{x + 34 + cw}" y="{y + 36}" style="font: 600 14px/1 {SANS}; letter-spacing: .3px" class="lang">{lang}</text>
<text x="{x + 22}" y="{y + 74}" style="font: 700 22px/1 {SANS}; letter-spacing: -.2px" class="say">{text}</text>
</g></g>'''


T = 12  # loop length, seconds
POP = [0.7, 1.35, 2.0]


def pct(t):
    return f(t / T * 100) + "%"


def css():
    bub = []
    for i, t in enumerate(POP):
        bub.append(
            f"@keyframes pop{i} {{ 0%, {pct(t)} {{ opacity: 0; transform: translate(-150px, {f(110 - i * 105)}px) scale(.2) rotate(-8deg); }} "
            f"{pct(t + .28)} {{ opacity: 1; transform: translate(6px, 0) scale(1.06) rotate(1deg); }} "
            f"{pct(t + .42)} {{ transform: translate(-2px, 0) scale(.98) rotate(0deg); }} "
            f"{pct(t + .55)}, {pct(9.6 + i * .08)} {{ opacity: 1; transform: none; }} "
            f"{pct(9.95 + i * .08)}, 100% {{ opacity: 0; transform: translate(-40px, 0) scale(.6); }} }}\n"
            f".b{i} {{ animation: pop{i} {T}s infinite; }}")
    jaw = " ".join(f"{pct(t - .05)} {{ transform: rotate(0deg); }} {pct(t + .08)} {{ transform: rotate(18deg); }} {pct(t + .3)} {{ transform: rotate(0deg); }}" for t in POP)
    talk = " ".join(f"{pct(t)} {{ opacity: 0; transform: scale(.6); }} {pct(t + .1)} {{ opacity: 1; transform: scale(1); }} {pct(t + .35)} {{ opacity: 0; transform: scale(1.15); }}" for t in POP)
    return f"""
.bg {{ fill: #EAF8EF; }} .spot {{ fill: #D2F1DF; }} .word {{ fill: #15301F; }} .tag {{ fill: #4B6B5B; }}
.bubFill {{ fill: #FFFFFF; }} .say {{ fill: #15301F; }} .lang {{ fill: #5E7A6C; }} .dot {{ fill: #15301F; opacity: .08; }}
@media (prefers-color-scheme: dark) {{
  .bg {{ fill: #0E1A15; }} .spot {{ fill: #15291F; }} .word {{ fill: #F1F7F3; }} .tag {{ fill: #9BB8A9; }}
  .bubFill {{ fill: #F7FBF8; }} .dot {{ fill: #fff; opacity: .06; }}
}}
.bub {{ transform-box: fill-box; transform-origin: 0% 60%; opacity: 0; }}
{chr(10).join(bub)}
.bubIn {{ animation: drift 6s ease-in-out infinite; }} .b1 .bubIn {{ animation-delay: -2s; }} .b2 .bubIn {{ animation-delay: -4s; }}
@keyframes drift {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}

.jaw {{ transform-origin: 278px 170px; animation: jaw {T}s infinite; }}
@keyframes jaw {{ 0% {{ transform: rotate(0deg); }} {jaw} 100% {{ transform: rotate(0deg); }} }}
.talk {{ transform-origin: 356px 172px; opacity: 0; animation: talk {T}s infinite; }}
@keyframes talk {{ 0% {{ opacity: 0; }} {talk} 100% {{ opacity: 0; }} }}

.mascot {{ transform-origin: 170px 410px; animation: body {T}s infinite; }}
@keyframes body {{ 0%, {pct(.3)} {{ transform: none; }} {pct(.55)} {{ transform: scale(1.03, .96); }}
  {pct(.75)} {{ transform: rotate(4deg) translateX(6px); }} {pct(2.3)} {{ transform: rotate(4deg) translateX(6px); }}
  {pct(2.55)} {{ transform: scale(1.04, .94); }} {pct(2.8)} {{ transform: translateY(-26px) scale(.98, 1.04); }}
  {pct(3.05)} {{ transform: scale(1.05, .94); }} {pct(3.3)}, 100% {{ transform: none; }} }}
.bod {{ transform-origin: 170px 392px; animation: breathe 3.2s ease-in-out infinite; }}
@keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.012, 1.02); }} }}
.tail {{ transform-origin: 140px 330px; animation: wag 4s ease-in-out infinite; }}
@keyframes wag {{ 0%, 100% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(4deg); }} }}
.lid {{ transform-origin: 222px 92px; transform: scaleY(0); animation: blink 4.4s infinite; }}
@keyframes blink {{ 0%, 88%, 100% {{ transform: scaleY(0); }} 92% {{ transform: scaleY(1); }} 96% {{ transform: scaleY(0); }} }}
.pupil {{ animation: look {T}s ease-in-out infinite; }}
@keyframes look {{ 0%, {pct(.5)} {{ transform: translate(0, 0); }} {pct(.8)}, {pct(9)} {{ transform: translate(3px, 1px); }} {pct(9.6)}, 100% {{ transform: translate(0, 0); }} }}

@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; }}
  .bub {{ opacity: 1 !important; transform: none !important; }}
}}
"""


DEFS = """
<linearGradient id="tailG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FB98F"/><stop offset="1" stop-color="#2F7FC4"/></linearGradient>
<linearGradient id="beakG" x1="0" y1="0" x2=".5" y2="1"><stop offset="0" stop-color="#FF5A66"/><stop offset="1" stop-color="#D81E3C"/></linearGradient>
<filter id="lift" x="-10%" y="-20%" width="120%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#15301F" flood-opacity=".14"/></filter>
"""


def banner():
    W, H = 1280, 500
    word, ww = text_path("Shoga-Speaks", 54, 0, 0, tracking=-1.1)
    dots = "".join(f'<circle class="dot" cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
                   [(70, 70, 5), (1200, 90, 7), (1120, 430, 5), (470, 455, 4), (1230, 300, 4), (520, 40, 3)])
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Shoga-Speaks</title>',
        '<desc id="d">Shoga, a cheerful green parrot, speaks three speech bubbles: for a developer in Roman-Urdu, '
        'for a QA tester in Dutch and for a product owner in English. Shoga-Speaks makes Claude Code explain things '
        'in your language and for your role.</desc>',
        f'<defs>{DEFS}<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>',
        f'<style>{css()}</style>',
        '<g clip-path="url(#card)">',
        f'<rect class="bg" width="{W}" height="{H}"/>',
        '<circle class="spot" cx="300" cy="270" r="230"/>',
        dots,
        '<g transform="translate(130 34) scale(.94)"><g class="mascot">', mascot(), '</g></g>',
        '<g filter="url(#lift)">', bubble(0, 560, 40), bubble(1, 604, 148), bubble(2, 560, 256), '</g>',
        f'<path class="word" transform="translate(560 434)" d="{word}"/>',
        f'<text class="tag" x="{560 + ww + 24}" y="432" style="font: 500 19px/1.2 {SANS}">Claude Code, explained</text>',
        f'<text class="tag" x="{560 + ww + 24}" y="456" style="font: 500 19px/1.2 {SANS}">in your language and role.</text>',
        '</g>',
        '</svg>',
    ])


def logo():
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" role="img" aria-labelledby="t">',
        '<title id="t">Shoga-Speaks: Shoga the parrot</title>',
        f'<defs>{DEFS}</defs>',
        '<style>' + css() + '.talk { display: none; } .mascot, .jaw, .pupil { animation: none; }</style>',
        '<circle class="bg" cx="256" cy="256" r="252"/>',
        '<circle class="spot" cx="256" cy="270" r="200"/>',
        '<g transform="translate(92 52) scale(.9)"><g class="mascot">', mascot(talk=False), '</g></g>',
        '</svg>',
    ])


if __name__ == "__main__":
    for name, fn in [("banner.svg", banner), ("logo.svg", logo)]:
        svg = fn()
        with open(os.path.join(OUT, name), "w") as fh:
            fh.write(svg)
        print(f"{name}: {len(svg) / 1024:.0f} KB")
