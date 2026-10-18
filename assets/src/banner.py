#!/usr/bin/env python3
"""Builds the Shoga-Speaks banner (assets/banner.svg) and social preview (assets/social-preview.png).

    pip install fonttools
    python3 assets/src/banner.py            # banner.svg
    python3 assets/src/banner.py --png      # also social-preview.png, 1280 x 640 (needs Chrome or Chromium:
                                            # on PATH, or SHOGA_CHROME=/path/to/chrome)
    ROLES=3 python3 assets/src/banner.py    # without the Support role (a shorter loop)

A product hero, as a before/after of the same answer. On the left: the wordmark
with Shoga perched beside it, the headline, the motto (with a slow light sweep)
and the role chips. On the right: a Claude Code terminal. One incident (a payment
race that can charge a customer twice) is asked about by four roles, each in their
own words and language (content.py). With the Shoga-Speaks switch off the reply is
a wall of jargon and a word counter climbs; Shoga flies over from the wordmark,
pecks the switch on, the wall folds into "\u25b8 Technical" under a two-line answer
in the asker's language, the counter drops, a pointer clicks the highlighted term
and its meaning opens; the asker replies and Shoga flies home. Timed for reading:
one new text at a time, the answer alone for 4.6 s, the meaning for 2.9 s.

Pure SVG for GitHub's <img>: CSS keyframes only, no script, no external files.
Every element runs on one loop: its keyframes are shifted to start at 0 and played
with a negative delay (--d), so identical shapes share one @keyframes. Readable
text is outlined glyphs from the vendored fonts (build.py), defined once and reused
with <use>; the wall is <text> in the system monospace, fitted with textLength.
Under reduced motion every animation pauses at one frame (--o): Dev's answer with
Shoga on the switch and the term's meaning open. The social preview is that frame
plus the install line.
"""
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mascot  # noqa: E402
from build import Face, f  # noqa: E402
from content import ROLES, WALL_BODY  # noqa: E402

ONLY = int(os.environ.get("ROLES", "4"))
ROLES_ALL = ROLES
ROLES = ROLES_ALL[:ONLY]

SHEET = []
FH = Face(SHEET, "h")       # wordmark, headline, motto
FS = Face(SHEET, "s")       # answers, chips, tabs, cards
FM = Face(SHEET, "m")       # terminal: asks, replies, Technical
FM6 = Face(SHEET, "n")      # counter digits, code pill, install line

# ================================================================ palette


def oklch(L, C, h):
    """OKLCH to sRGB hex: role colours share one lightness and chroma."""
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)

    def enc(x):
        x = max(0, min(1, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return "#%02X%02X%02X" % tuple(round(enc(v) * 255) for v in rgb)


for _r in ROLES_ALL:
    _r["cd"] = oklch(0.78, 0.12, _r["h"])    # on the dark terminal (about 9:1)
    _r["c"] = oklch(0.52, 0.12, _r["h"])     # on white (about 5:1)

W, H = 1280, 600
GREEN = "#168B49"         # brand green on white: the motto (large text, 4.4:1)
GREEN_T = "#1A7A42"       # small green text on white (5.6:1)
GREEN_D = oklch(0.78, 0.12, 152)   # brand green on the terminal
AMBER_D = oklch(0.78, 0.12, 72)
INK = "#0F1A14"
INK2 = "#4F5B55"
TERM = "#0E1011"          # terminal content
CHROME = "#16191C"        # title bar and tab strip
LINE = "#272B2F"
ROWBG = "#1A1E21"
INBG = "#121518"
TXT = "#E7E9EA"
DIM = "#8B9298"           # 6:1 on TERM
DIMMER = "#7A8188"        # 4.8:1 on TERM

# ================================================================ layout
WX, WY, WW = 476, 96, 764
WR = WX + WW
TB = 40
TABY, TABH = WY + TB, 34
CV0 = TABY + TABH
XL, XT, IN_X = 500, 520, 528
ASK_Y = 200
WALL0 = 222
WALL_LH, WALL_FS = 17, 12
ANS_Y = (252, 284)
ANS_FS = 21
TECH_Y = 317
HINT_Y0 = 302
HINT_PUSH = 46
REPLY_Y = TECH_Y + HINT_PUSH + 38
CV1 = 466
IN_Y0, IN_Y1 = 476, 516
IN_BASE = 502
WB = IN_Y1 + 16
WH = WB - WY
MONO_FS = 17
ADV = FM.layout("0")[1] * MONO_FS / 100
# the switch: [knob] Shoga-Speaks off|on
LBL = "Shoga-Speaks"
LBL_FS = 13.5
_lw = FS.width(LBL, LBL_FS) + 5 + FS.width("off", LBL_FS)
SX = round(WR - 16 - _lw - 46)
KNOB_OFF = SX + 11
SHOGA_S = 0.18
PX, PY = KNOB_OFF - round(50 * SHOGA_S / 0.16), WY    # Shoga's feet on the switch
# left column
LX = 56
WMY = 176                  # wordmark baseline
WM_FS = 30
WM_W = FH.width("Shoga-Speaks", WM_FS, -0.01)
HX, HY = round(LX + WM_W + 34), WMY                    # Shoga's home: right of the wordmark

# ================================================================ timeline
CH = 0.043
FLIGHT = 1.35


def words(s):
    return len(s.replace("{", "").replace("}", "").split())


def plan():
    t, out = 0.0, []
    for r in ROLES:
        b = {"start": t}
        b["type0"] = t + 0.6
        b["type1"] = b["type0"] + len(r["ask"]) * CH
        b["submit"] = b["type1"] + 1.1
        b["wall0"] = b["submit"] + 0.3
        b["reveal1"] = b["wall0"] + 0.75
        b["wall1"] = b["wall0"] + 2.5
        b["fly0"] = b["wall1"] + 0.45
        b["land"] = b["fly0"] + FLIGHT
        b["peck0"] = b["land"] + 0.35
        b["contact"] = b["peck0"] + 0.17
        b["collapse"] = b["contact"] + 0.25
        b["ans"] = b["collapse"] + 0.45
        b["tech"] = b["ans"] + 0.6
        if r["hint"]:
            b["h0"] = b["ans"] + 4.6          # the answer alone for 4.6 s
            b["click"] = b["h0"] + 1.2
            b["card"] = b["click"] + 0.1
            b["reply0"] = b["card"] + 2.9     # the meaning alone for 2.9 s
        else:
            b["reply0"] = b["ans"] + 4.8
        b["reply1"] = b["reply0"] + (len(r["reply"]) + (2 if r["thumb"] else 0)) * 0.06
        b["rsubmit"] = b["reply1"] + 0.55
        b["takeoff"] = b["rsubmit"] + 0.9
        b["home"] = b["takeoff"] + FLIGHT
        b["end"] = b["rsubmit"] + 1.6
        b["nwords"] = sum(words(x) for x in r["ans"])
        out.append(b)
        t = b["end"]
    return out, t


BEATS, T = plan()
STILL_T = BEATS[0]["click"] + 1.6     # reduced motion: Dev, Shoga on the switch, hint open


class TL:
    """Keyframes on one shared loop. Each element's frames are shifted to start at
    0 and played with a negative delay (--d), so identical shapes share one
    @keyframes; reduced motion pauses everything at STILL_T through --o."""

    def __init__(self):
        self.kf = {}

    def attrs(self, frames, origin=None, cls=""):
        frames = sorted(((fr[0] % T,) + tuple(fr[1:]) for fr in frames), key=lambda x: x[0])
        t0 = frames[0][0]
        parts, last = [], None
        for fr in frames:
            t, decl = fr[0], fr[1]
            ease = fr[2] if len(fr) > 2 else None
            p = f((t - t0) / T * 100, 3)
            if p == last:
                sys.exit(f"keyframes collide at {t}: {frames}")
            last = p
            parts.append(f"{p}%{{{decl}" + (f";animation-timing-function:{ease}" if ease else "") + "}")
        parts.append(f"100%{{{frames[0][1]}}}")
        body = "".join(parts)
        if body not in self.kf:
            self.kf[body] = f"k{len(self.kf)}"
        d = (t0 % T) - T if t0 % T else 0
        st = f"animation-name:{self.kf[body]};--d:{f(d, 3)}s"     # always set: custom properties inherit
        if origin:
            st = f"transform-origin:{f(origin[0])}px {f(origin[1])}px;" + st
        c = ("A " + cls).strip()
        return f' class="{c}" style="{st}"'

    def css(self):
        return "".join(f"@keyframes {n}{{{b}}}" for b, n in self.kf.items())


TLX = TL()
EPS = 0.004


def vis(spans, fi=0.25, fo=0.25):
    fr = []
    for a, b in spans:
        fr += [(a - (fi or EPS), "opacity:0"), (a, "opacity:1"), (b, "opacity:1"), (b + (fo or EPS), "opacity:0")]
    return fr


def on(spans, fi=0.25, fo=0.25, origin=None, cls=""):
    return TLX.attrs(vis(spans, fi, fo), origin, cls)


# ================================================================ helpers
def runs(line, x, y, fs, fill):
    """An answer line: plain runs in Inter, {code} runs in mono on a pill."""
    out, spans = [], []
    for part in re.split(r"(\{[^}]*\})", line):
        if not part:
            continue
        if part.startswith("{"):
            code = part[1:-1]
            cs = fs * 0.84
            w = FM6.width(code, cs)
            out.append(f'<rect x="{f(x)}" y="{f(y - fs * 0.86)}" width="{f(w + 12)}" height="{f(fs * 1.18)}" rx="5" fill="#1B2620"/>')
            out.append(FM6.text(code, cs, x + 6, y - 0.5, fill="#8FD3A8")[0])
            spans.append((code, x, x + w + 12, True))
            x += w + 12 + fs * 0.12
        else:
            g, w = FS.text(part, fs, x, y, fill=fill)
            out.append(g)
            spans.append((part, x, x + w, False))
            x += w
    return "".join(out), spans, x


def term_x(spans, term):
    for text, x0, x1, code in spans:
        i = text.find(term)
        if i >= 0 and not code:
            a = x0 + FS.width(text[:i], ANS_FS)
            return a, a + FS.width(term, ANS_FS)
    sys.exit(f"term {term!r} not found")


THUMB = ('<g transform="translate({x} {y}) scale(.95)" fill="#E9B949">'
         '<path d="M1 8.5h3.6v9.5H1z"/>'
         '<path d="M5.6 17.6V8.6l3.9-6.9c1.6-.2 2.8 1 2.5 2.7l-.8 3.6h5.1c1.4 0 2.4 1.3 2.1 2.6l-1.4 5.6c-.3 1.1-1.2 1.8-2.3 1.8z"/>'
         '</g>')

# a macOS-style arrow pointer, tip at (0, 0)
POINTER = "M0 0V17.2L4.1 13.3L6.9 19.8L9.8 18.6L7.1 12.3H12.8Z"


def wall_lines(r):
    rows = [("o", r["wall"][0]), ("o", r["wall"][1])] + WALL_BODY
    o = []
    for k, (kind, s) in enumerate(rows):
        y = WALL0 + 12 + k * WALL_LH
        w = len(s) * WALL_FS * 0.6
        cls = {"o": "wo", "h": "wh", "p": "wp", "c": "wc", "e": "we", "d": "wd"}[kind]
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        o.append(f'<text x="{XT}" y="{y}" textLength="{f(w)}" class="{cls}">{s}</text>')
    o.insert(0, f'<circle cx="{XL + 6}" cy="{WALL0 + 8}" r="4" fill="{DIM}"/>')
    return '<g xml:space="preserve">' + "".join(o) + '</g>', len(rows) * WALL_LH


def counter_digits(n, xr, y, fill, size=15):
    return FM6.text(str(n), size, xr, y, fill=fill, anchor="end")[0]


# ================================================================ static frame
def window_chrome():
    o = [f'<rect x="{WX + 14}" y="{WY + 34}" width="{WW - 28}" height="{WH - 14}" rx="24" fill="#0A0D0C" opacity=".2" filter="url(#fs1)"/>',
         f'<rect x="{WX + 2}" y="{WY + 3}" width="{WW - 4}" height="{WH - 1}" rx="15" fill="#0A0D0C" opacity=".18" filter="url(#fs2)"/>',
         f'<rect x="{WX}" y="{WY}" width="{WW}" height="{WH}" rx="14" fill="{TERM}"/>',
         f'<g clip-path="url(#win)"><rect x="{WX}" y="{WY}" width="{WW}" height="{TB + TABH}" fill="{CHROME}"/>'
         f'<path d="M{WX} {TABY + TABH - .5}H{WR}" stroke="{LINE}"/></g>']
    for k, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        o.append(f'<circle cx="{WX + 22 + k * 20}" cy="{WY + TB / 2}" r="6" fill="{c}"/>')
    o.append(FM.text("claude  ~/checkout-api", 13, WX + WW / 2 - 40, WY + 25, fill=DIM, anchor="middle")[0])
    return "".join(o)


def window_border():
    return (f'<rect x="{WX + .5}" y="{WY + .5}" width="{WW - 1}" height="{WH - 1}" rx="13.5" fill="none" stroke="#fff" stroke-opacity=".06"/>'
            f'<rect x="{WX - .5}" y="{WY - .5}" width="{WW + 1}" height="{WH + 1}" rx="14.5" fill="none" stroke="#000" stroke-opacity=".5"/>')


def tab_layout():
    x, tabs = WX + 10, []
    for r in ROLES_ALL:
        w1 = FS.width(r["tab"], 15)
        w2 = FS.width(r["lang"], 13)
        tabs.append((x, 14 + 8 + w1 + 7 + w2 + 14, w1))
        x += tabs[-1][1] + 2
    return tabs


def tabs_static(tabs):
    o = []
    for (x, w, w1), r in zip(tabs, ROLES_ALL):
        o.append(f'<circle cx="{f(x + 17)}" cy="{TABY + TABH / 2}" r="3.5" fill="{r["cd"]}" opacity=".5"/>')
        o.append(FS.text(r["tab"], 15, x + 26, TABY + 22, fill=DIM)[0])
        o.append(FS.text(r["lang"], 13, x + 26 + w1 + 7, TABY + 22, fill=DIMMER)[0])
    return "".join(o)


def tab_active(i, tabs, attrs=""):
    (x, w, w1), r = tabs[i], ROLES[i]
    return (f'<g{attrs}>'
            f'<rect x="{f(x)}" y="{TABY + 1}" width="{f(w)}" height="{TABH - 1}" fill="{TERM}"/>'
            f'<rect x="{f(x)}" y="{TABY + 1}" width="{f(w)}" height="2" fill="{r["cd"]}"/>'
            f'<circle cx="{f(x + 17)}" cy="{TABY + TABH / 2}" r="3.5" fill="{r["cd"]}"/>'
            + FS.text(r["tab"], 15, x + 26, TABY + 22, fill=TXT)[0]
            + FS.text(r["lang"], 13, x + 26 + w1 + 7, TABY + 22, fill=r["cd"])[0]
            + '</g>')


def input_box():
    return (f'<rect x="{XL - 8}" y="{IN_Y0}" width="{WR - 16 - (XL - 8)}" height="{IN_Y1 - IN_Y0}" rx="8" fill="{INBG}" stroke="{LINE}"/>'
            + FM.text("›", MONO_FS, XL + 4, IN_BASE, fill=DIM)[0])


# ================================================================ left column
CHIP_GEOM = []


def left_column(defs):
    o = []
    o.append(FH.text("Shoga-Speaks", WM_FS, LX, WMY, fill=INK, tracking=-0.01)[0])
    # headline, as large as fits the column
    col = WX - 48 - LX
    hs = 46
    while FH.width("explained for you.", hs, -0.026) > col:
        hs -= 1
    o.append(FH.text("Claude Code,", hs, LX - 2, 256, fill=INK, tracking=-0.026)[0])
    o.append(FH.text("explained for you.", hs, LX - 2, 256 + round(hs * 1.18), fill=INK, tracking=-0.026)[0])
    # the motto: a highlighter band and a slow light sweep across the Roman-Urdu line
    my = 368
    g, mw = FH.text("Seedhi baat, no bakwas.", 28, LX, my, tracking=-0.012)
    defs.append(f'<g id="motto">{g}</g>'
                '<linearGradient id="shg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                '<stop offset=".5" stop-color="#fff" stop-opacity=".62"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                f'<mask id="mm" maskUnits="userSpaceOnUse" x="{LX - 10}" y="{my - 40}" width="{f(mw + 30)}" height="60"><use href="#motto" fill="#fff"/></mask>')
    o.append(f'<rect x="{LX - 6}" y="{my - 12}" width="{f(mw + 12)}" height="17" rx="3" fill="#DDF2E3"/>')
    o.append(f'<use href="#motto" fill="{GREEN}"/>')
    o.append(f'<g mask="url(#mm)"><g transform="translate({LX - 84} {my - 12}) skewX(-18)">'
             f'<rect class="sheen" x="0" y="-26" width="64" height="44" fill="url(#shg)" style="--w:{f(mw + 150)}px"/></g></g>')
    o.append(FS.text("Straight talk, no nonsense.", 18, LX, my + 32, fill=GREEN_T)[0])
    # role chips, two rows, a step smaller so the motto leads
    cy, cx = 440, LX
    for i, r in enumerate(ROLES_ALL):
        tw = FS.width(r["chip"], 13)
        w = 12 + 8 + 5 + tw + 12
        if i == 2:
            cy, cx = cy + 36, LX
        CHIP_GEOM.append((cx, cy, w))
        o.append(f'<rect x="{f(cx + .5)}" y="{cy + .5}" width="{f(w - 1)}" height="27" rx="13.5" fill="#fff" stroke="#DADFDC"/>')
        o.append(f'<circle cx="{f(cx + 15)}" cy="{cy + 14}" r="3.5" fill="{r["c"]}"/>')
        o.append(FS.text(r["chip"], 13, cx + 24, cy + 18.5, fill="#36413B")[0])
        cx += w + 8
    return "".join(o)


def chip_active(i, attrs=""):
    cx, cy, w = CHIP_GEOM[i]
    r = ROLES[i]
    return (f'<g{attrs}><rect x="{f(cx)}" y="{cy}" width="{f(w)}" height="28" rx="14" fill="{r["c"]}"/>'
            f'<circle cx="{f(cx + 15)}" cy="{cy + 14}" r="3.5" fill="#fff"/>'
            + FS.text(r["chip"], 13, cx + 24, cy + 18.5, fill="#fff")[0] + '</g>')


# ================================================================ scene
def build():
    tabs = tab_layout()
    defs = ['<filter id="fs1" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="22"/></filter>'
            '<filter id="fs2" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3"/></filter>'
            '<filter id="fs3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1"/></filter>'
            f'<clipPath id="cv"><rect x="{WX}" y="{CV0}" width="{WW}" height="{CV1 - CV0}"/></clipPath>'
            f'<clipPath id="win"><rect x="{WX}" y="{WY}" width="{WW}" height="{WH}" rx="14"/></clipPath>']
    scene = [f'<rect width="{W}" height="{H}" fill="#fff"/>', left_column(defs), window_chrome(), tabs_static(tabs), input_box()]
    a = []
    # tab and chip highlights
    for i, b in enumerate(BEATS):
        a.append(tab_active(i, tabs, on([(b["start"], b["end"])], fi=0.25, fo=0.25)))
        a.append(chip_active(i, on([(b["start"], b["end"])], fi=0.25, fo=0.25)))

    # ---- word counter (tab strip, right)
    CR = WR - 16
    cpx = CR - 132
    wl = FS.text("words", 12.5, CR - 10, TABY + 22, fill=DIM, anchor="end")
    NUM_R = CR - 10 - wl[1] - 6
    a.append(f'<g{on([(b["wall0"] - 0.1, b["end"] - 0.3) for b in BEATS], fi=0.2, fo=0.3)}>'
             f'<rect x="{cpx}" y="{TABY + 6}" width="{CR - cpx}" height="23" rx="11.5" fill="#202427"/>{wl[0]}</g>')
    for b, r in zip(BEATS, ROLES):
        N = r["words"]
        ups = [round(N * (1 - (1 - k / 11) ** 1.6)) for k in range(1, 12)]
        tk = [b["wall0"] + 2.5 * (1 - (1 - k / 11) ** 1.3) * 0.98 for k in range(0, 11)]
        for k, n in enumerate(ups):
            t0 = tk[k] if k < len(tk) else tk[-1]
            t1 = tk[k + 1] if k + 1 < len(tk) else b["collapse"]
            a.append(f'<g{on([(t0, t1)], fi=0.01, fo=0.01)}>{counter_digits(n, NUM_R, TABY + 22, AMBER_D if k == len(ups) - 1 else TXT)}</g>')
        downs = [round(N - (N - b["nwords"]) * (k / 6) ** 0.7) for k in range(1, 7)]
        for k, n in enumerate(downs):
            t0 = b["collapse"] + k * 0.12
            t1 = b["collapse"] + (k + 1) * 0.12 if k < 5 else b["end"] - 0.3
            a.append(f'<g{on([(t0, t1)], fi=0.01, fo=0.01 if k < 5 else 0.3)}>{counter_digits(n, NUM_R, TABY + 22, GREEN_D)}</g>')
        wn = FM6.width(str(b["nwords"]), 15)
        xo = NUM_R - wn - 9 - 12
        wo = FM6.width(str(N), 13)
        a.append(f'<g{on([(b["collapse"] + 0.75, b["end"] - 0.3)], fi=0.3, fo=0.3)}>{counter_digits(N, xo - 6, TABY + 22, DIMMER, 13)}'
                 f'<path d="M{f(xo - 8 - wo)} {TABY + 17.5}h{f(wo + 4)}" stroke="{DIMMER}" stroke-width="1.4"/>'
                 f'<path d="M{f(xo)} {TABY + 17.5}h9m-3.5-3.5 3.5 3.5-3.5 3.5" stroke="{DIM}" stroke-width="1.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>')
        a.append(f'<rect x="{cpx}" y="{TABY + 6}" width="{CR - cpx}" height="23" rx="11.5" fill="none" stroke="{GREEN_D}" stroke-width="1.2"'
                 f'{on([(b["collapse"], b["collapse"] + 1.6)], fi=0.15, fo=0.8)}/>')

    # ---- conversation (clipped)
    conv, cur_frames, ptr = [], [], []
    for i, (b, r) in enumerate(zip(BEATS, ROLES)):
        g = []
        ask_hist = (f'<rect x="{XL - 8}" y="{ASK_Y - 21}" width="{WR - 16 - (XL - 8)}" height="30" rx="6" fill="{ROWBG}"/>'
                    + FM.text("›", MONO_FS, XL + 4, ASK_Y, fill=DIM)[0]
                    + f'<use href="#ask{i}" x="{IN_X - 8}" y="{ASK_Y}" fill="{TXT}"/>')
        wl_, wh = wall_lines(r)
        S = wh - (CV1 - WALL0) + 6
        scroll = TLX.attrs([(b["start"], "transform:translateY(0)"), (b["reveal1"], "transform:translateY(0)", "cubic-bezier(.5,0,.7,1)"),
                            (b["wall1"], f"transform:translateY(-{f(S)}px)"), (b["collapse"], f"transform:translateY(-{f(S)}px)", "cubic-bezier(.6,0,.3,1)"),
                            (b["collapse"] + 0.45, "transform:translateY(0)")])
        wall_anim = TLX.attrs([(b["start"], "transform:scaleY(1);opacity:0"), (b["wall0"] - EPS, "transform:scaleY(1);opacity:0"),
                               (b["wall0"], "transform:scaleY(1);opacity:1"), (b["collapse"], "transform:scaleY(1);opacity:1", "cubic-bezier(.6,0,.3,1)"),
                               (b["collapse"] + 0.42, "transform:scaleY(.015);opacity:.6"), (b["collapse"] + 0.55, "transform:scaleY(.015);opacity:0")],
                              origin=(0, WALL0))
        g.append(f'<g{scroll}><g{on([(b["submit"], b["end"] - 0.3)], fi=0.01, fo=0.3)}>{ask_hist}</g><g{wall_anim}>{wl_}</g></g>')
        nrev = int((CV1 - WALL0) / WALL_LH) + 1
        cover = TLX.attrs([(b["start"], "transform:translateY(0)"), (b["wall0"], "transform:translateY(0)", f"steps({nrev},end)"),
                           (b["reveal1"], f"transform:translateY({nrev * WALL_LH}px)"), (b["end"] - 0.1, f"transform:translateY({nrev * WALL_LH}px)", "step-end")])
        g.append(f'<rect x="{WX}" y="{WALL0 - 2}" width="{WW}" height="{CV1 - WALL0 + 4}" fill="{TERM}"{cover}/>')
        # the answer
        ans = [f'<circle cx="{XL + 6}" cy="{ANS_Y[0] - 7}" r="4.5" fill="{GREEN_D}"/>']
        spans_all = []
        for k, line in enumerate(r["ans"]):
            sv, sp, xe = runs(line, XT, ANS_Y[k], ANS_FS, TXT)
            assert xe < WR - 26, (line, xe)
            ans.append(sv)
            spans_all.append(sp)
        g.append(f'<g{TLX.attrs([(b["start"], "opacity:0;transform:translateY(6px)"), (b["ans"] - EPS, "opacity:0;transform:translateY(6px)"), (b["ans"] + 0.4, "opacity:1;transform:translateY(0)"), (b["end"] - 0.3, "opacity:1;transform:translateY(0)"), (b["end"], "opacity:0;transform:translateY(0)")])}>{"".join(ans)}</g>')
        push = HINT_PUSH if r["hint"] else 0
        if r["hint"]:
            hl, term, meaning = r["hint"]
            x0, x1 = term_x(spans_all[hl], term)
            yb = ANS_Y[hl]
            g.append(f'<g{on([(b["h0"], b["end"] - 0.3)], fi=0.3, fo=0.3)}>'
                     f'<rect x="{f(x0 - 3)}" y="{yb - 18}" width="{f(x1 - x0 + 6)}" height="25" rx="4" fill="{r["cd"]}" fill-opacity=".15"/>'
                     f'<path d="M{f(x0 + 1)} {yb + 6}H{f(x1)}" stroke="{r["cd"]}" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="0 4.6"/></g>')
            tw, mw = FS.width(term, 16.5), FS.width(meaning, 16.5)
            cw = 14 + tw + 12 + mw + 14
            assert XT + cw < WR - 20, (meaning, cw)
            card = (f'<rect x="{XT - 2}" y="{HINT_Y0}" width="{f(cw)}" height="36" rx="8" fill="#F4F5F5"/>'
                    f'<rect x="{XT - 2}" y="{HINT_Y0}" width="4" height="36" rx="2" fill="{r["c"]}"/>'
                    + FS.text(term, 16.5, XT + 12, HINT_Y0 + 24, fill=r["c"])[0]
                    + FS.text(meaning, 16.5, XT + 12 + tw + 12, HINT_Y0 + 24, fill="#1B2420")[0])
            g.append(f'<g{TLX.attrs([(b["start"], "opacity:0;transform:scale(.96)"), (b["card"], "opacity:0;transform:scale(.96)"), (b["card"] + 0.28, "opacity:1;transform:scale(1)"), (b["end"] - 0.3, "opacity:1;transform:scale(1)"), (b["end"], "opacity:0;transform:scale(1)")], origin=(XT, HINT_Y0))}>{card}</g>')
            # the pointer glides in, rests on the term, clicks, drifts away
            tx, ty = (x0 + x1) / 2 - 4, yb - 4
            sx, sy = tx + 170, ty + 120
            c = b["click"]
            ptr += [(b["h0"] + 0.15, f"transform:translate({f(sx)}px,{f(sy)}px) scale(1);opacity:0"),
                    (b["h0"] + 0.3, f"transform:translate({f(sx - 12)}px,{f(sy - 9)}px) scale(1);opacity:1", "cubic-bezier(.2,.7,.2,1)"),
                    (b["h0"] + 0.95, f"transform:translate({f(tx)}px,{f(ty)}px) scale(1);opacity:1"),
                    (c, f"transform:translate({f(tx)}px,{f(ty)}px) scale(1);opacity:1", "ease-out"),
                    (c + 0.08, f"transform:translate({f(tx)}px,{f(ty)}px) scale(.84);opacity:1", "ease-out"),
                    (c + 0.22, f"transform:translate({f(tx)}px,{f(ty)}px) scale(1);opacity:1"),
                    (c + 0.75, f"transform:translate({f(tx)}px,{f(ty)}px) scale(1);opacity:1", "cubic-bezier(.4,0,.6,1)"),
                    (c + 1.35, f"transform:translate({f(tx + 80)}px,{f(ty + 96)}px) scale(1);opacity:0")]
            g.append(f'<circle cx="{f(tx)}" cy="{f(ty)}" r="12" fill="none" stroke="{r["cd"]}" stroke-width="2"'
                     + TLX.attrs([(c - EPS, "opacity:0;transform:scale(.3)"), (c + 0.04, "opacity:.9;transform:scale(.3)", "ease-out"), (c + 0.5, "opacity:0;transform:scale(1.5)")], origin=(tx, ty)) + '/>')
        tech = (FM.text("▸", 14, XT, TECH_Y, fill=DIM)[0] + FM.text("Technical", 14, XT + 15, TECH_Y, fill=DIM)[0]
                + FM.text("· 47 lines", 14, XT + 15 + FM.width("Technical ", 14), TECH_Y, fill=DIMMER)[0])
        tf = [(b["start"], "opacity:0;transform:translateY(-6px)"), (b["tech"] - EPS, "opacity:0;transform:translateY(-6px)"), (b["tech"] + 0.35, "opacity:1;transform:translateY(0)")]
        if r["hint"]:
            tf += [(b["card"], "opacity:1;transform:translateY(0)"), (b["card"] + 0.3, f"opacity:1;transform:translateY({push}px)")]
        tf += [(b["end"] - 0.3, f"opacity:1;transform:translateY({push}px)"), (b["end"], f"opacity:0;transform:translateY({push}px)")]
        g.append(f'<g{TLX.attrs(tf)}>{tech}</g>')
        ry = REPLY_Y - HINT_PUSH + push
        rep = (f'<rect x="{XL - 8}" y="{ry - 21}" width="{f(IN_X - XL + 22 + ADV * (len(r["reply"]) + (2 if r["thumb"] else 0)) + 10)}" height="30" rx="6" fill="{ROWBG}"/>'
               + FM.text("›", MONO_FS, XL + 4, ry, fill=DIM)[0]
               + f'<use href="#rep{i}" x="{IN_X - 8}" y="{ry}"/>')
        g.append(f'<g{on([(b["rsubmit"], b["end"] - 0.3)], fi=0.01, fo=0.3)}>{rep}</g>')
        conv.append("".join(g))
    th = CV1 - CV0 - 12
    sb = []
    for b in BEATS:
        sb.append(f'<rect x="{WR - 9}" y="{CV0 + 6}" width="4" height="{th}" rx="2" fill="#464C51"'
                  + TLX.attrs([(b["start"], "opacity:0;transform:scaleY(.6)"), (b["reveal1"] - 0.15, "opacity:0;transform:scaleY(.6)"), (b["reveal1"], "opacity:1;transform:scaleY(.6)", "cubic-bezier(.2,.6,.4,1)"),
                               (b["wall1"], "opacity:1;transform:scaleY(.045)"), (b["collapse"], "opacity:1;transform:scaleY(.045)"), (b["collapse"] + 0.4, "opacity:0;transform:scaleY(1)")],
                              origin=(0, CV0 + 6 + th)) + '/>')

    # ---- input: typing with a stepped clip, and the cursor
    inp = []
    for i, (b, r) in enumerate(zip(BEATS, ROLES)):
        for kind, text, t0, t1, t2 in (("ask", r["ask"], b["type0"], b["type1"], b["submit"]),
                                       ("rep", r["reply"] + ("  " if r["thumb"] else ""), b["reply0"], b["reply1"], b["rsubmit"])):
            n = len(text)
            cid = f"c{kind}{i}"
            clip = TLX.attrs([(t0 - 0.05, "transform:scaleX(0)"), (t0, "transform:scaleX(0)", f"steps({n},end)"), (t1, "transform:scaleX(1)")], origin=(IN_X, 0))
            defs.append(f'<clipPath id="{cid}"><rect x="{IN_X}" y="{IN_Y0}" width="{f(n * ADV)}" height="{IN_Y1 - IN_Y0}"{clip}/></clipPath>')
            inp.append(f'<g clip-path="url(#{cid})"><use href="#{kind}{i}" x="{IN_X}" y="{IN_BASE}" fill="{TXT}"{on([(t0, t2)], fi=0.01, fo=0.01)}/></g>')
            cur_frames += [(t0, "transform:translateX(0)", f"steps({n},end)"), (t1, f"transform:translateX({f(n * ADV)}px)", "step-end"),
                           (t2, "transform:translateX(0)", "step-end")]
    cursor = f'<g{TLX.attrs(cur_frames)}><rect class="blink" x="{IN_X}" y="{IN_BASE - 15}" width="{f(ADV - 1)}" height="20" rx="1.5" fill="{TXT}" opacity=".85"/></g>'
    for i, r in enumerate(ROLES):
        defs.append(f'<g id="ask{i}">{FM.text(r["ask"], MONO_FS, 0, 0)[0]}</g>')
        rep = FM.text(r["reply"], MONO_FS, 0, 0)[0]
        if r["thumb"]:
            rep += THUMB.format(x=f(ADV * (len(r["reply"]) + 1) - 1), y=-16)
        defs.append(f'<g id="rep{i}" fill="{TXT}">{rep}</g>')

    # ---- the switch: a before/after of the same answer, without and with Shoga-Speaks
    knob, track, tap = [], [], []
    for b in BEATS:
        knob += [(b["contact"], "transform:translateX(0)", "cubic-bezier(.3,1.5,.6,1)"), (b["contact"] + 0.22, "transform:translateX(16px)"),
                 (b["end"] - 0.05, "transform:translateX(16px)", "ease-in-out"), (b["end"] + 0.2, "transform:translateX(0)")]
        track += [(b["contact"], "opacity:0"), (b["contact"] + 0.18, "opacity:1"), (b["end"] - 0.05, "opacity:1"), (b["end"] + 0.2, "opacity:0")]
        tap += [(b["contact"] - EPS, "opacity:0;transform:scale(.6)"), (b["contact"], "opacity:.8;transform:scale(.6)"), (b["contact"] + 0.4, "opacity:0;transform:scale(2.2)")]
    lx = SX + 46
    lw = FS.width(LBL, LBL_FS)
    off = [(fr[0], fr[1].replace("opacity:0", "opacity:X").replace("opacity:1", "opacity:0").replace("opacity:X", "opacity:1")) + tuple(fr[2:]) for fr in track]
    tog = [f'<rect x="{SX}" y="{WY + 9}" width="38" height="22" rx="11" fill="#353A3E"/>',
           f'<rect x="{SX}" y="{WY + 9}" width="38" height="22" rx="11" fill="{GREEN}"{TLX.attrs(track)}/>',
           f'<circle cx="{KNOB_OFF}" cy="{WY + 20}" r="8" fill="none" stroke="{GREEN_D}" stroke-width="2"{TLX.attrs(tap, origin=(KNOB_OFF, WY + 20))}/>',
           f'<circle cx="{KNOB_OFF}" cy="{WY + 20}" r="8" fill="#fff"{TLX.attrs(knob)}/>',
           FS.text(LBL, LBL_FS, lx, WY + 25, fill=TXT)[0],
           f'<g{TLX.attrs(off)}>' + FS.text("off", LBL_FS, lx + lw + 5, WY + 25, fill=DIM)[0] + '</g>',
           f'<g{TLX.attrs(track)}>' + FS.text("on", LBL_FS, lx + lw + 5, WY + 25, fill=GREEN_D)[0] + '</g>']

    # ---- the pointer
    pointer = (f'<g{TLX.attrs(ptr)}><g transform="scale(1.3)">'
               f'<path d="{POINTER}" transform="translate(.8 1.6)" fill="#000" opacity=".35" filter="url(#fs3)"/>'
               f'<path d="{POINTER}" fill="#fff" stroke="#16191C" stroke-width="1.15" stroke-linejoin="round"/></g></g>')

    body = (scene + a + tog
            + [f'<g clip-path="url(#cv)">{"".join(conv)}{"".join(sb)}</g>'] + inp + [cursor, window_border(), pointer, shoga_anim()])
    return "".join(body), defs


def flight(a, b, lift, n=9):
    """Points along a lifted arc from a to b, eased in time: (u, x, y, heading deg)."""
    cx, cy = (a[0] + b[0]) / 2, min(a[1], b[1]) - lift
    out = []
    for k in range(n):
        s = k / (n - 1)
        u = 0.5 - 0.5 * math.cos(math.pi * s)            # ease in-out along the path
        x = (1 - u) ** 2 * a[0] + 2 * (1 - u) * u * cx + u * u * b[0]
        y = (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * cy + u * u * b[1]
        dx = 2 * (1 - u) * (cx - a[0]) + 2 * u * (b[0] - cx)
        dy = 2 * (1 - u) * (cy - a[1]) + 2 * u * (b[1] - cy)
        out.append((s, x, y, math.degrees(math.atan2(dy, abs(dx)))))
    return out


def shoga_anim():
    """Shoga lives beside the wordmark. Per role it flies across to the terminal,
    lands on the title bar, pecks the switch on, reads along, and flies home."""
    perch_d, perch_b = mascot.mark("sp", eye_cls="lid")
    fly_d, fly_b = mascot.mark("sf", fly=True, wing_cls="flap", feet=False)
    geo = f'scale({SHOGA_S}) translate(-170 -414)'
    P = (PX - HX, PY - HY)
    fly, mir, perch, flym, peck, sq, tilt, lid = [], [], [], [], [], [], [], []

    def tr(x, y, r):
        return f"transform:translate({f(x)}px,{f(y)}px) rotate({f(r)}deg)"
    for b in BEATS:
        # out: home -> switch, facing right
        pts = flight((0, 0), P, 110)
        a0, L_ = b["fly0"], b["land"]
        for k, (s, x, y, hd) in enumerate(pts):
            t = a0 + s * FLIGHT
            r = max(-10, min(48, 38 + 0.45 * hd)) if 0 < k < len(pts) - 1 else 0
            if k == len(pts) - 2:
                r = -12                                   # flare before touching down
            fly.append((t, tr(x, y, r), "linear"))
        fly.append((b["takeoff"], tr(*P, 0), "linear"))
        # back: switch -> home, facing left (mirrored)
        pts = flight(P, (0, 0), 120)
        for k, (s, x, y, hd) in enumerate(pts[1:], 1):
            t = b["takeoff"] + s * FLIGHT
            r = -max(-10, min(48, 38 + 0.45 * hd)) if k < len(pts) - 1 else 0
            if k == len(pts) - 2:
                r = 12
            fly.append((t, tr(x, y, r), "linear"))
        mir += [(b["takeoff"] - 0.02, "transform:scaleX(1)"), (b["takeoff"] + 0.12, "transform:scaleX(-1)"),
                (b["home"] + 0.35, "transform:scaleX(-1)"), (b["home"] + 0.5, "transform:scaleX(1)")]
        flym += [(a0 - EPS, "opacity:0"), (a0 + 0.08, "opacity:0"), (a0 + 0.08 + EPS, "opacity:1"), (L_ - EPS, "opacity:1"), (L_, "opacity:0"),
                 (b["takeoff"] + 0.08, "opacity:0"), (b["takeoff"] + 0.08 + EPS, "opacity:1"), (b["home"] - EPS, "opacity:1"), (b["home"], "opacity:0")]
        perch += [(a0 + 0.08, "opacity:1"), (a0 + 0.08 + EPS, "opacity:0"), (L_ - EPS, "opacity:0"), (L_, "opacity:1"),
                  (b["takeoff"] + 0.08, "opacity:1"), (b["takeoff"] + 0.08 + EPS, "opacity:0"), (b["home"] - EPS, "opacity:0"), (b["home"], "opacity:1")]
        for tl in (L_, b["home"]):
            sq += [(tl, "transform:scale(1,1)"), (tl + 0.08, "transform:scale(1.14,.8)"), (tl + 0.22, "transform:scale(.95,1.06)"), (tl + 0.36, "transform:scale(1,1)")]
        for to in (a0, b["takeoff"]):
            sq += [(to - 0.2, "transform:scale(1,1)"), (to - 0.06, "transform:scale(1.1,.86)"), (to + 0.08, "transform:scale(1,1)")]
        c = b["contact"]
        sq += [(c + 0.45, "transform:scale(1,1)"), (c + 0.55, "transform:scale(1.08,.9)"), (c + 0.7, "transform:scale(.96,1.06) translateY(-7px)"),
               (c + 0.86, "transform:scale(1.06,.93)"), (c + 1.0, "transform:scale(1,1)")]
        p0 = b["peck0"]
        peck += [(p0 - 0.12, "transform:rotate(0deg)", "ease-in-out"), (p0, "transform:rotate(-8deg)", "cubic-bezier(.5,0,.9,.5)"), (c, "transform:rotate(73deg)"),
                 (c + 0.06, "transform:rotate(73deg)", "cubic-bezier(.2,.7,.3,1)"), (c + 0.36, "transform:rotate(0deg)")]
        # at home it watches the wall pile up; on the switch it reads along
        tilt += [(b["wall0"] + 0.4, "transform:rotate(0deg)", "ease-in-out"), (b["wall0"] + 0.75, "transform:rotate(14deg)"), (b["wall1"] - 0.2, "transform:rotate(14deg)", "ease-in-out"),
                 (b["wall1"] + 0.15, "transform:rotate(0deg)"),
                 (b["ans"] + 0.6, "transform:rotate(0deg)", "ease-in-out"), (b["ans"] + 0.95, "transform:rotate(-12deg)"), (b["ans"] + 1.9, "transform:rotate(-12deg)", "ease-in-out"),
                 (b["ans"] + 2.25, "transform:rotate(0deg)")]
        if "click" in b:
            tilt += [(b["h0"] + 0.2, "transform:rotate(0deg)", "ease-in-out"), (b["h0"] + 0.5, "transform:rotate(9deg)"), (b["click"] + 0.6, "transform:rotate(9deg)", "ease-in-out"),
                     (b["click"] + 0.9, "transform:rotate(0deg)")]
        for tb in (b["start"] + 1.4, b["wall0"] + 1.8, c + 1.25, b["ans"] + 3.4, b["reply0"] + 0.4):
            lid += [(tb - EPS, "transform:scaleY(0)"), (tb, "transform:scaleY(0)", "ease-in"), (tb + 0.07, "transform:scaleY(1)", "ease-out"), (tb + 0.16, "transform:scaleY(0)")]
    lid_attr = TLX.attrs(lid, origin=mascot.EYE)
    perch_b = perch_b.replace(' class="lid"', lid_attr)
    return (f'<g transform="translate({HX} {HY})">'
            f'<g{TLX.attrs(fly)}><g{TLX.attrs(mir)}><g{TLX.attrs(peck, origin=(0, 0))}><g{TLX.attrs(sq, origin=(0, 0))}><g{TLX.attrs(tilt, origin=(0, -40))}>'
            f'<g{TLX.attrs(perch)}><g transform="{geo}">{perch_d}{perch_b}</g></g>'
            f'<g{TLX.attrs(flym)}><g transform="{geo}">{fly_d}{fly_b}</g></g>'
            '</g></g></g></g></g></g>')


def document():
    body, defs = build()
    css = ("text{white-space:pre;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;font-size:12px}"
           ".wo,.wh{fill:#CDD9E5}.wh{font-weight:700}.wp{fill:#768390}.wc{fill:#ADBAC7}.we{fill:#E5726A}.wd{fill:#636E7B}"
           f".A{{animation-duration:{f(T, 3)}s;animation-iteration-count:infinite;animation-timing-function:cubic-bezier(.3,0,.2,1);animation-delay:calc(var(--d,0s) + var(--o,0s))}}"
           ".blink{animation:bl 1.1s steps(1,end) infinite}@keyframes bl{50%{opacity:0}}"
           ".flap{transform-origin:0 0;animation:fl .19s ease-in-out infinite alternate}@keyframes fl{from{transform:rotate(-40deg)}to{transform:rotate(34deg)}}"
           ".sheen{animation:sh 6.5s cubic-bezier(.45,0,.25,1) 1.4s infinite}@keyframes sh{0%{translate:0}24%,100%{translate:var(--w)}}"
           + TLX.css() +
           f"@media (prefers-reduced-motion:reduce){{svg{{--o:-{f(STILL_T, 3)}s}}.A{{animation-play-state:paused}}.blink,.flap,.sheen{{animation:none}}}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">'
           '<title id="t">Shoga-Speaks: Claude Code, explained for you</title>'
           '<desc id="d">A before and after in a Claude Code terminal. Four people ask about the same payment bug, each in their own '
           'language and role. Without Shoga-Speaks the reply is a wall of jargon. Shoga the parakeet flies over from the logo and pecks '
           'the Shoga-Speaks switch on: the wall folds into a short answer in their language, with the technical detail tucked under '
           'Technical and a hard word explained on click.</desc>'
           f'<defs>{"".join(SHEET)}{"".join(defs)}</defs><style>{css}</style>' + body + '</svg>')
    return svg


def social(svg):
    """1280 x 640: the reduced-motion frame of the banner, paused outright (so it does
    not depend on the renderer's motion setting), plus the install line."""
    n0 = len(SHEET)
    cmd = "/plugin marketplace add Mir-Zairan/shoga-speaks"
    cw = FM6.width(cmd, 21)
    k = 0.94
    inner = svg.replace(f'width="{W}" height="{H}"', f'overflow="visible" x="{f((1280 - W * k) / 2)}" y="0" width="{f(W * k)}" height="{f(H * k)}"', 1)
    py = 572
    soc = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 640" width="1280" height="640">'
           f'<style>svg{{--o:-{f(STILL_T, 3)}s}}.A{{animation-play-state:paused!important}}.blink,.flap,.sheen{{animation:none!important}}</style>'
           '<rect width="1280" height="640" fill="#fff"/>' + inner
           + f'<rect x="{f(640 - cw / 2 - 52)}" y="{py}" width="{f(cw + 104)}" height="46" rx="12" fill="{TERM}"/>'
           + FM6.text("$", 21, 640 - cw / 2 - 30, py + 30, fill=GREEN_D)[0]
           + FM6.text(cmd, 21, 640 - cw / 2 + 4, py + 30, fill=TXT)[0])
    return soc + f'<defs>{"".join(SHEET[n0:])}</defs></svg>'


def render_png(svg_path, png_path, w, h):
    """A still of the SVG, as an <img> in headless Chrome (SHOGA_CHROME, or found on PATH)."""
    chrome = os.environ.get("SHOGA_CHROME") or next(
        (shutil.which(c) for c in ("google-chrome", "chromium", "chromium-browser", "chrome") if shutil.which(c)), None)
    if not chrome:
        sys.exit("--png needs Chrome or Chromium (set SHOGA_CHROME)")
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "p.html")
        with open(page, "w") as fh:
            fh.write(f'<html><body style="margin:0;background:#fff"><img src="file://{svg_path}" width="{w}" height="{h}"></body></html>')
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-prefers-reduced-motion",
                        f"--user-data-dir={tmp}/u", f"--window-size={w},{h}", f"--screenshot={png_path}", f"file://{page}"],
                       check=True, capture_output=True)


if __name__ == "__main__":
    svg = document()
    with open(os.path.join(OUT, "banner.svg"), "w") as fh:
        fh.write(svg)
    print(f"banner.svg: {len(svg.encode()) / 1024:.1f} KB, a {T:.1f} s loop, {len(ROLES)} roles")
    if "--png" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "social.svg")
            with open(src, "w") as fh:
                fh.write(social(svg))
            out = os.path.join(OUT, "social-preview.png")
            render_png(src, out, 1280, 640)
            print(f"social-preview.png: {os.path.getsize(out) / 1024:.0f} KB")
