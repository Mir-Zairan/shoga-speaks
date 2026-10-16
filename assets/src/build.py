#!/usr/bin/env python3
"""Builds assets/banner.svg and assets/logo.svg: the Shoga mascot.

    pip install fonttools
    python3 assets/src/build.py

Vector only, no external files. The background is white in light and dark mode alike.
Animation is CSS and stops under reduced motion.
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
# One message per role, said in one language at a time: Roman-Urdu, then Dutch, then English.

LANGS = ["Roman-Urdu", "Nederlands", "English"]
ROLES = [
    ("Dev", "#22A35A", ["N+1 query hai: sab ek query mein lao.", "N+1-query: haal alles in één query op.", "N+1 query: load it all in one query."]),
    ("QA", "#2F7FE0", ["500+ orders wala customer test karo.", "Test met een klant met 500+ orders.", "Test with a customer with 500+ orders."]),
    ("PO", "#E08A12", ["Abhi release mat karo: do risk hain.", "Nog niet releasen: twee risico's.", "Don't release yet: two risks."]),
]

T = 14          # loop length, seconds
POP = [0.7, 1.3, 1.9]          # bubbles spring out (Roman-Urdu)
SWITCH = [5.4, 9.0]            # flip to Dutch, then English
OUT_AT = 12.6                  # bubbles leave
STAGGER = .14


def pct(t):
    return f(max(0, min(t, T)) / T * 100) + "%"


def bubble(i, x, y, w=480, h=88):
    role, color, texts = ROLES[i]
    cw = 24 + len(role) * 12
    lines = "".join(
        f'<text class="say t{i}{k}" x="{x + 26 + cw}" y="{y + h / 2 + 8}" style="font: 700 21px/1 {SANS}; letter-spacing: -.2px">{t}</text>'
        for k, t in enumerate(texts))
    return f'''<g class="bub b{i}">
<g class="bubIn">
<path d="M{x + 22} {y} h{w - 44} a22 22 0 0 1 22 22 v{h - 44} a22 22 0 0 1 -22 22 h{-(w - 44)} a22 22 0 0 1 -22 -22 v{-(h - 66)} l-18 -6 l18 -10 v-6 a22 22 0 0 1 22 -22 z"
 class="bubFill" stroke="#15301F" stroke-width="3.5" stroke-linejoin="round"/>
<rect x="{x + 16}" y="{y + h / 2 - 14}" width="{cw}" height="28" rx="14" fill="{color}"/>
<text x="{x + 16 + cw / 2}" y="{y + h / 2 + 5}" text-anchor="middle" style="font: 800 14px/1 {SANS}; fill: #fff">{role}</text>
{lines}
</g></g>'''


def tabs(x, y):
    out, cx = [], x
    for k, name in enumerate(LANGS):
        w = 30 + len(name) * 9.4
        out.append(f'<g class="tab tab{k}" transform="translate({f(cx)} {y})"><rect width="{f(w)}" height="32" rx="16"/>'
                   f'<text x="{f(w / 2)}" y="21" text-anchor="middle" style="font: 700 15px/1 {SANS}">{name}</text>'
                   f'<text class="on" x="{f(w / 2)}" y="21" text-anchor="middle" style="font: 700 15px/1 {SANS}">{name}</text></g>')
        cx += w + 10
    return "\n".join(out)


def css():
    starts = [0] + SWITCH
    ends = SWITCH + [OUT_AT + .4]
    rules = []
    # bubbles spring out of the beak, then leave together
    for i, t in enumerate(POP):
        rules.append(
            f"@keyframes pop{i} {{ 0%, {pct(t)} {{ opacity: 0; transform: translate(-150px, {f(100 - i * 100)}px) scale(.2) rotate(-8deg); }} "
            f"{pct(t + .28)} {{ opacity: 1; transform: translate(6px, 0) scale(1.06) rotate(1deg); }} "
            f"{pct(t + .42)} {{ transform: translate(-2px, 0) scale(.98) rotate(0deg); }} "
            f"{pct(t + .55)}, {pct(OUT_AT + i * .08)} {{ opacity: 1; transform: none; }} "
            f"{pct(OUT_AT + .35 + i * .08)}, 100% {{ opacity: 0; transform: translate(-40px, 0) scale(.6); }} }}\n"
            f".b{i} {{ animation: pop{i} {T}s infinite; }}")
    # each line flips in when its language starts and out when the next one comes
    for i in range(3):
        for k in range(3):
            s0, e0 = starts[k] + i * STAGGER, ends[k] + i * STAGGER
            if k == 0:
                frames = f"0%, {pct(e0 - .01)} {{ opacity: 1; transform: none; }} {pct(e0 + .14)}, 100% {{ opacity: 0; transform: scaleY(.1); }}"
            else:
                frames = (f"0%, {pct(s0 + .12)} {{ opacity: 0; transform: scaleY(.1); }} {pct(s0 + .3)} {{ opacity: 1; transform: scaleY(1.08); }} "
                          f"{pct(s0 + .4)} {{ transform: none; }} {pct(e0 - .01) if k < 2 else pct(T)} {{ opacity: 1; transform: none; }} "
                          + (f"{pct(e0 + .14)}, 100% {{ opacity: 0; transform: scaleY(.1); }}" if k < 2 else ""))
            rules.append(f"@keyframes l{i}{k} {{ {frames} }} .t{i}{k} {{ animation: l{i}{k} {T}s infinite; }}")
    # language tabs light up in turn
    for k in range(3):
        s0, e0 = starts[k], ends[k]
        rules.append(f"@keyframes tab{k} {{ 0%, {pct(s0)} {{ opacity: .45; }} {pct(s0 + .15)}, {pct(e0)} {{ opacity: 1; }} {pct(e0 + .15)}, 100% {{ opacity: .45; }} }}"
                     f" .tab{k} {{ animation: tab{k} {T}s infinite; }}"
                     f" @keyframes tabf{k} {{ 0%, {pct(s0)} {{ fill-opacity: 0; }} {pct(s0 + .15)}, {pct(e0)} {{ fill-opacity: 1; }} {pct(e0 + .15)}, 100% {{ fill-opacity: 0; }} }}"
                     f" .tab{k} rect {{ animation: tabf{k} {T}s infinite; }}"
                     f" @keyframes tabo{k} {{ 0%, {pct(s0)} {{ opacity: 0; }} {pct(s0 + .15)}, {pct(e0)} {{ opacity: 1; }} {pct(e0 + .15)}, 100% {{ opacity: 0; }} }}"
                     f" .tab{k} .on {{ animation: tabo{k} {T}s infinite; }}")
    talks = POP + SWITCH
    jaw = " ".join(f"{pct(t - .05)} {{ transform: rotate(0deg); }} {pct(t + .08)} {{ transform: rotate(18deg); }} {pct(t + .3)} {{ transform: rotate(0deg); }}" for t in talks)
    talk = " ".join(f"{pct(t)} {{ opacity: 0; transform: scale(.6); }} {pct(t + .1)} {{ opacity: 1; transform: scale(1); }} {pct(t + .35)} {{ opacity: 0; transform: scale(1.15); }}" for t in talks)
    nod = " ".join(f"{pct(t - .1)} {{ transform: none; }} {pct(t + .1)} {{ transform: rotate(3deg) translateX(4px); }} {pct(t + .4)} {{ transform: none; }}" for t in SWITCH)
    return f"""
.bg {{ fill: #FFFFFF; }} .spot {{ fill: #EAF8EF; }} .word {{ fill: #15301F; }} .tag {{ fill: #4B6B5B; }}
.bubFill {{ fill: #FFFFFF; }} .say {{ fill: #15301F; }} .dot {{ fill: #15301F; opacity: .08; }}
.tab rect {{ fill: #5BD46E; stroke: #15301F; stroke-width: 2; }} .tab text {{ fill: #15301F; }} .tab .on {{ fill: #0E1A15; opacity: 0; }}
}}
.tab text {{ mix-blend-mode: normal; }}
.bub {{ transform-box: fill-box; transform-origin: 0% 60%; opacity: 0; }}
.say {{ transform-box: fill-box; transform-origin: 50% 60%; }}
{chr(10).join(rules)}
.bubIn {{ animation: drift 6s ease-in-out infinite; }} .b1 .bubIn {{ animation-delay: -2s; }} .b2 .bubIn {{ animation-delay: -4s; }}
@keyframes drift {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-3px); }} }}

.jaw {{ transform-origin: 278px 170px; animation: jaw {T}s infinite; }}
@keyframes jaw {{ 0% {{ transform: rotate(0deg); }} {jaw} 100% {{ transform: rotate(0deg); }} }}
.talk {{ transform-origin: 356px 172px; opacity: 0; animation: talk {T}s infinite; }}
@keyframes talk {{ 0% {{ opacity: 0; }} {talk} 100% {{ opacity: 0; }} }}
.headf {{ transform-origin: 200px 200px; animation: nod {T}s infinite; }}
@keyframes nod {{ 0% {{ transform: none; }} {nod} 100% {{ transform: none; }} }}

.mascot {{ transform-origin: 170px 410px; animation: body {T}s infinite; }}
@keyframes body {{ 0%, {pct(.3)} {{ transform: none; }} {pct(.55)} {{ transform: scale(1.03, .96); }}
  {pct(.75)} {{ transform: rotate(4deg) translateX(6px); }} {pct(2.2)} {{ transform: rotate(4deg) translateX(6px); }}
  {pct(2.45)} {{ transform: scale(1.04, .94); }} {pct(2.7)} {{ transform: translateY(-26px) scale(.98, 1.04); }}
  {pct(2.95)} {{ transform: scale(1.05, .94); }} {pct(3.2)}, 100% {{ transform: none; }} }}
.bod {{ transform-origin: 170px 392px; animation: breathe 3.2s ease-in-out infinite; }}
@keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.012, 1.02); }} }}
.tail {{ transform-origin: 140px 330px; animation: wag 4s ease-in-out infinite; }}
@keyframes wag {{ 0%, 100% {{ transform: rotate(0deg); }} 50% {{ transform: rotate(4deg); }} }}
.lid {{ transform-origin: 222px 92px; transform: scaleY(0); animation: blink 4.4s infinite; }}
@keyframes blink {{ 0%, 88%, 100% {{ transform: scaleY(0); }} 92% {{ transform: scaleY(1); }} 96% {{ transform: scaleY(0); }} }}
.pupil {{ animation: look {T}s ease-in-out infinite; }}
@keyframes look {{ 0%, {pct(.5)} {{ transform: translate(0, 0); }} {pct(.8)}, {pct(12)} {{ transform: translate(3px, 1px); }} {pct(12.6)}, 100% {{ transform: translate(0, 0); }} }}

@media (prefers-reduced-motion: reduce) {{
  * {{ animation: none !important; }}
  .bub {{ opacity: 1 !important; transform: none !important; }}
  .say {{ opacity: 0 !important; }} .t00, .t10, .t20 {{ opacity: 1 !important; }}
  .tab {{ opacity: .45 !important; }} .tab0 {{ opacity: 1 !important; }} .tab rect {{ fill-opacity: 0 !important; }} .tab0 rect {{ fill-opacity: 1 !important; }} .tab0 .on {{ opacity: 1 !important; }}
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
        '<desc id="d">Shoga, a cheerful green parrot, speaks three speech bubbles, one each for a developer, a QA tester and '
        'a product owner. The same three messages are said in Roman-Urdu, then Dutch, then English. Shoga-Speaks makes '
        'Claude Code explain things in your language and for your role.</desc>',
        f'<defs>{DEFS}<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath></defs>',
        f'<style>{css()}</style>',
        '<g clip-path="url(#card)">',
        f'<rect class="bg" width="{W}" height="{H}"/>',
        '<circle class="spot" cx="300" cy="270" r="230"/>',
        dots,
        '<g transform="translate(130 34) scale(.94)"><g class="mascot">', mascot(), '</g></g>',
        tabs(586, 34),
        '<g filter="url(#lift)">', bubble(0, 560, 92), bubble(1, 600, 192), bubble(2, 560, 292), '</g>',
        f'<path class="word" transform="translate(560 452)" d="{word}"/>',
        f'<text class="tag" x="{560 + ww + 24}" y="430" style="font: 500 19px/1.2 {SANS}">Claude Code, explained</text>',
        f'<text class="tag" x="{560 + ww + 24}" y="454" style="font: 500 19px/1.2 {SANS}">in your language and role.</text>',
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
