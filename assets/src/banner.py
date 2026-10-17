#!/usr/bin/env python3
"""Builds the Shoga-Speaks banner (assets/banner.svg) and social preview (assets/social-preview.png).

    pip install fonttools
    python3 assets/src/banner.py          # banner.svg
    python3 assets/src/banner.py --png    # also social-preview.png, 1280 x 640 (needs Chrome or Chromium)

"Seedhi" means straight. Every cycle starts with one question typed into Claude
Code ("why is the orders page slow?"). The answer spills out of the cursor as a
dense knot of thread with the task's jargon on it (bakwas). Shoga, the parrot,
catches the loose end and pulls it into one straight line: the jargon falls into
a "▸ Technical" tag, a plain two-line story rises out of the line, one term gets a
plain meaning, and the tag opens into a card with the same details put in order.
Shoga lets go, the line recoils into the underline of the wordmark and Shoga
lands on it, with the motto in Roman-Urdu and English. The same task plays three
times: a developer in Roman-Urdu, a QA tester in Dutch, a product owner in English.
The loop is timed for reading: each text beat stays alone on stage for at least
1.2 s + 0.25 s per word.

Pure SVG for GitHub's <img>: no script, no external files, every word an outlined
path. The thread is a SMIL path morph (the same cubic count in every keyframe),
and Shoga's position runs on the same SMIL clock, so the beak never leaves the
line; the rest is CSS. Under reduced motion the picture is a still of the Dev
story with its card open.

Fonts, text and Shoga's geometry come from build.py (vendored subsets in
assets/src/fonts/, or the full fonts with SHOGA_FONTS set; see build.py).
"""
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build import (BEAK_LO, BEAK_UP, BODY, FEET, FLY, FLY_COV, FLY_TIP, HEAD, OL, TAIL,  # noqa: E402
                   WING, WROOT, Type, f)

# the faces the banner uses: attribute -> (glyph id prefix, build.FACES key, units per em)
FACES = {"xb": ("x", "xb", 120), "b": ("b", "b", 100), "sb": ("s", "sb", 60), "mono": ("m", "mono6", 100)}


def new_type():
    return Type(FACES)


# ================================================================ palette and stage
INK = "#15301F"
PAPER = "#FBF8F2"
W, H = 1280, 480
LY = 270                  # the straight line
X0 = 84                   # the pin: the thread's fixed end
XE = 1146                 # where Shoga holds the line taut
LLINE = XE - X0
C0 = (300, 246)           # knot centre
KRX, KRY = 178, 128       # knot radii
G = (552, 322)            # the loose end, where Shoga catches it
TAGX = 132                # the ▸ Technical tag hangs here
N_SEG = 36                # cubic segments in every thread keyframe
CHUNK = 6                 # segments per over/under chunk
D = 840                   # dense samples along the thread
KNOT_SEED = 11            # one task, one knot: every role untangles the same work

PROMPT = "why is the orders page slow?"
JARGON = ["N+1", "OrderList.load()", "WHERE id IN (...)", "eager-load", "201→2", "p95 4.1s", "idx", "41 passed"]
ROLES = [
    dict(role="Dev", color="#1F9D55", lang="Roman-Urdu", twist=(1.0, 0), loops=11,
         say=["N+1 tha: har order ke liye alag query.", "Ab sab ek query mein: 201 → 2."],
         card=["src/orders/list.ts:42  one query per order → WHERE id IN (...)",
               "201 → 2 queries · p95 4.1s → 0.6s",
               "41 tests passed"],
         hint=("say", 0, "N+1", "har item ke liye database se alag call")),
    dict(role="QA", color="#2F7FE0", lang="Nederlands", twist=(0.97, 16), loops=23,
         say=["Test met een klant met 500+ orders:", "de pagina moet binnen 1 seconde openen."],
         card=["1. Log in as a customer with 500+ orders",
               "2. Open Orders → expect < 1 s (was 4.1 s)",
               "3. Every row shows its customer"],
         hint=("say", 0, "500+ orders", "genoeg data om de oude traagheid te zien")),
    dict(role="PO", color="#E08A12", lang="English", twist=(1.03, -14), loops=37,
         say=["The orders page now opens", "in under a second. Safe to ship."],
         card=["Scope: orders page only",
               "Risk: low · no visible UI change",
               "Rollback: one revert"],
         hint=("say", 1, "Safe to ship", "tested, low risk, ready to release")),
]
GREEN = "#1F9D55"

# ================================================================ timing (seconds inside one role; three roles make the loop)
# Timed for reading: each text beat is alone on stage for at least 1.2 s + 0.25 s per word.
N = len(ROLES)
PROMPT_TXT = "› " + PROMPT
T_TYPE0 = 0.35            # the question starts typing, big and central
CH_DT = 0.045             # per character
T_TYPED = T_TYPE0 + len(PROMPT_TXT) * CH_DT
T_SPILL0 = T_TYPED + 1.5  # read it; then the answer spills out of the cursor as a knot
T_SPILL1 = T_SPILL0 + 0.8
T_KNOT = T_SPILL1
T_SWOOP = T_KNOT + 2.0    # let the bakwas register before Shoga arrives
T_CATCH = T_SWOOP + 0.9
T_JERK = T_CATCH + 0.15
T_PULL = T_CATCH + 0.4
T_PULLEND = T_PULL + 2.0  # a slower, heavier pull
TWANG = [(T_PULLEND + 0.13, -8, -4), (T_PULLEND + 0.27, 5, 2), (T_PULLEND + 0.43, -2.5, -1), (T_PULLEND + 0.62, 0, 0)]
T_MSG = T_PULLEND + 0.12  # the story rises out of the line
WORD_DT = 0.055
T_STORY = T_MSG + 13 * WORD_DT + 0.5   # fully readable
T_HINT = T_STORY + 4.6    # the story alone, then one term gets its plain meaning
T_HINT_END = T_HINT + 0.3 + 2.8
T_CARD = T_HINT_END + 0.25
T_CARD_FULL = T_CARD + 0.45
T_FOLD = T_CARD_FULL + 4.8
T_REL = T_FOLD + 0.4      # Shoga lets go
RECOIL = [T_REL + 0.18, T_REL + 0.3, T_REL + 0.42]
T_WM = T_REL + 0.24       # wordmark rises
T_LAND = T_REL + 0.8      # Shoga lands on the end of the underline
T_BRAND = T_LAND + 0.6    # the brand frame is complete
T_WMOUT = T_BRAND + 4.0
T_TAKEOFF = T_WMOUT - 0.05
T_RETRACT = T_WMOUT + 0.12
L = T_WMOUT + 0.85
T = L * N
PULL_K = 8                # pull keyframes
HOLD_A = 50               # Shoga's lean while holding the line


def bez_ease(x1, y1, x2, y2):
    def bx(t):
        return 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3

    def by(t):
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3

    def e(x):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            if bx(m) < x:
                lo = m
            else:
                hi = m
        return by((lo + hi) / 2)
    return e


PULL_EASE = bez_ease(.62, 0, .22, 1)      # resistance, then a long glide into taut


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ================================================================ the knot
def resample(pts, n):
    """Points evenly spaced by arc length."""
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    total = acc[-1]
    out, j = [], 0
    for i in range(n + 1):
        s = total * i / n
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        seg = acc[j + 1] - acc[j] or 1
        u = (s - acc[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out, total


def make_knot(seed):
    rnd = random.Random(seed)
    cx, cy = C0
    pts = [(X0, LY)]
    x, y = X0, LY
    th = -0.55
    ds = 2.0
    kappa, target, until = 0.0, 0.0, 0
    # pin strand: a short lazy curve into the knot
    length = 2350
    steps = int(length / ds)
    for i in range(steps):
        if i >= until:
            mag = rnd.uniform(1 / 70, 1 / 24)
            sign = -1 if target > 0 else 1
            if rnd.random() < 0.35:
                sign = -sign
            target = sign * mag
            until = i + int(rnd.uniform(35, 110) / ds)
        kappa += (target - kappa) * 0.08
        qx, qy = (x - cx) / KRX, (y - cy) / KRY
        r = math.hypot(qx, qy)
        steer = 0.0
        if r > 0.62 and i > 25:
            want = math.atan2(cy - y, cx - x)
            diff = (want - th + math.pi) % (2 * math.pi) - math.pi
            steer = diff * 0.012 * (r - 0.62) * 6
        th += kappa * ds + steer
        x += math.cos(th) * ds
        y += math.sin(th) * ds
        pts.append((x, y))
    # the loose end: out of the knot to the right, hanging a little
    px, py = pts[-1]
    hx, hy = math.cos(th), math.sin(th)
    c1 = (px + hx * 90, py + hy * 90)
    c2 = (G[0] - 70, G[1] - 40)
    for k in range(1, 81):
        t = k / 80
        pts.append(cubic_pt((px, py), c1, c2, G, t))
    dense, total = resample(pts, D)
    return dense, total


def cubic_pt(p0, p1, p2, p3, t):
    a = (1 - t) ** 3
    b = 3 * (1 - t) ** 2 * t
    c = 3 * (1 - t) * t * t
    d = t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def straight(x1, bow=0.0, x0=X0, y=LY):
    return [(x0 + (x1 - x0) * i / D, y + bow * math.sin(math.pi * i / D)) for i in range(D + 1)]


def follow_end(pts, B, wt=0.10):
    """Drag the loose end to B, fading the displacement back along the thread."""
    ex, ey = pts[-1]
    dx, dy = B[0] - ex, B[1] - ey
    out = []
    for i, (x, y) in enumerate(pts):
        u = i / D
        w = smooth((u - (1 - wt)) / wt)
        out.append((x + dx * w, y + dy * w))
    return out


def tighten(pts, s, rot=0.0, shift=(0, 0)):
    cx, cy = C0
    c, sn = math.cos(rot), math.sin(rot)
    out = []
    for i, (x, y) in enumerate(pts):
        u = i / D
        g = smooth(u / 0.05) * smooth((1 - u) / 0.08)
        dx, dy = (x - cx) * s, (y - cy) * s
        nx, ny = cx + dx * c - dy * sn + shift[0], cy + dx * sn + dy * c + shift[1]
        out.append((x + (nx - x) * g, y + (ny - y) * g))
    return out


def unravel(knot, p, B, ustar=0.27, w=0.13):
    """The thread at pull progress p (0..1) with the beak at B.

    Both ends draw out straight: from the pin along the line, and from the knot to
    the beak. The fronts eat into the knot from both sides while what is left of it
    turns, tightens and slides onto the line, where the last loop vanishes at u*.
    """
    uL = -w + p * (ustar + w)
    uR = 1 + w - p * (1 - ustar + w)
    e = p
    cf = (X0 + ustar * LLINE, LY)
    s = 1 - 0.62 * e
    rot = math.radians(-70) * e
    shift = ((cf[0] - C0[0]) * e, (cf[1] - C0[1]) * e)
    k2 = tighten(knot, s, rot, shift)
    out = []
    for i in range(D + 1):
        u = i / D
        inside = smooth(min((u - uL) / w, (uR - u) / w))
        if u <= ustar:
            sx, sy = X0 + u * LLINE, LY
        else:
            back = (1 - u) * LLINE
            sx = B[0] - back
            sy = LY + (B[1] - LY) * max(0.0, 1 - back / 220)
        kx, ky = k2[i]
        out.append((sx + (kx - sx) * inside, sy + (ky - sy) * inside))
    out[0] = (X0, LY)
    return follow_end(out, B, 0.04)


# ================================================================ extra loops: static detail that rides the knot core
USTAR = 0.27


def walk(rnd, x, y, th, length, cx, cy, rx, ry, kmin, kmax):
    pts, ds = [(x, y)], 2.0
    kappa, target, until = 0.0, 0.0, 0
    for i in range(int(length / ds)):
        if i >= until:
            mag = rnd.uniform(kmin, kmax)
            sign = -1 if target > 0 else 1
            if rnd.random() < 0.3:
                sign = -sign
            target = sign * mag
            until = i + int(rnd.uniform(30, 90) / ds)
        kappa += (target - kappa) * 0.1
        r = math.hypot((x - cx) / rx, (y - cy) / ry)
        steer = 0.0
        if r > 0.6:
            want = math.atan2(cy - y, cx - x)
            diff = (want - th + math.pi) % (2 * math.pi) - math.pi
            steer = diff * 0.07 * (r - 0.6)
        th += kappa * ds + steer
        x += math.cos(th) * ds
        y += math.sin(th) * ds
        pts.append((x, y))
    return pts, th


def extra_loops(seed, n=4):
    """Closed, curly strands inside the knot: the same cord, drawn at full detail."""
    rnd = random.Random(seed * 7 + 1)
    out = []
    for i in range(n):
        cx = C0[0] + rnd.uniform(-0.3, 0.3) * KRX
        cy = C0[1] + rnd.uniform(-0.25, 0.25) * KRY
        rx, ry = KRX * rnd.uniform(.5, .72), KRY * rnd.uniform(.5, .72)
        th0 = rnd.uniform(0, 6.3)
        x0, y0 = cx + math.cos(th0 + 1.6) * rx * .5, cy + math.sin(th0 + 1.6) * ry * .5
        pts, th = walk(rnd, x0, y0, th0, rnd.uniform(650, 900), cx, cy, rx, ry, 1 / 46, 1 / 17)
        # close it smoothly back to the start
        (px, py), h0 = pts[-1], th
        c1 = (px + math.cos(h0) * 60, py + math.sin(h0) * 60)
        c2 = (x0 - math.cos(th0) * 60, y0 - math.sin(th0) * 60)
        pts += [cubic_pt((px, py), c1, c2, (x0, y0), k / 40) for k in range(1, 40)]
        dense, total = resample(pts, 600)
        nodes = max(16, int(total / 26))
        sel = [dense[round(j * 600 / nodes)] for j in range(nodes)]
        d = f"M{round(sel[0][0])} {round(sel[0][1])}"
        for j in range(nodes):
            p0, p1, p2, p3 = sel[j - 1], sel[j], sel[(j + 1) % nodes], sel[(j + 2) % nodes]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            d += "C" + " ".join(str(round(v)) for v in (*c1, *c2, *p2))
        out.append(rel_abs(d) + "z")
    return out


def rel_abs(d):
    """Absolute M/C path to relative m/c."""
    nums = [int(v) for v in re.findall(r"-?\d+", d)]
    x, y = nums[0], nums[1]
    out = f"m{x} {y}c"
    s = ""
    for k in range(2, len(nums), 6):
        seg = nums[k:k + 6]
        r = [seg[0] - x, seg[1] - y, seg[2] - x, seg[3] - y, seg[4] - x, seg[5] - y]
        for v in r:
            s += ("" if (not s or v < 0) else " ") + str(v)
        x, y = seg[4], seg[5]
    return out + s


def core_css(p, a0=4.0, s0=0.96, cinch=1.0):
    """CSS transform equal to tighten() at pull progress p, about C0 (cinch < 1 tightens harder)."""
    cf = (X0 + USTAR * LLINE, LY)
    sh = ((cf[0] - C0[0]) * p, (cf[1] - C0[1]) * p)
    return f"translate({f(sh[0])}px,{f(sh[1])}px) rotate({f(a0 - 70 * p)}deg) scale({f(s0 * (1 - 0.62 * p) * cinch, 3)})"


# ================================================================ fitting to cubic chunks
def tangent(pts, i, k=3):
    a = pts[max(0, i - k)]
    b = pts[min(D, i + k)]
    span = min(D, i + k) - max(0, i - k)
    return ((b[0] - a[0]) / span, (b[1] - a[1]) / span)


def fit(pts, nseg=None, chunk=None):
    """N_SEG cubic segments through the dense thread, split into over/under chunks."""
    nseg, chunk = nseg or N_SEG, chunk or CHUNK
    h = D / nseg
    nodes = []
    for k in range(nseg + 1):
        i = round(k * h)
        t = tangent(pts, i)
        nodes.append((pts[i], t))
    chunks = []
    for c in range(0, nseg, chunk):
        p0 = nodes[c][0]
        cur = (round(p0[0]), round(p0[1]))
        d = f"M{cur[0]} {cur[1]}c"
        nums = []
        for k in range(c, c + chunk):
            (pa, ta), (pb, tb) = nodes[k], nodes[k + 1]
            c1 = (round(pa[0] + ta[0] * h / 3), round(pa[1] + ta[1] * h / 3))
            c2 = (round(pb[0] - tb[0] * h / 3), round(pb[1] - tb[1] * h / 3))
            e = (round(pb[0]), round(pb[1]))
            nums += [c1[0] - cur[0], c1[1] - cur[1], c2[0] - cur[0], c2[1] - cur[1], e[0] - cur[0], e[1] - cur[1]]
            cur = e
        s = ""
        for v in nums:
            s += ("" if (not s or v < 0) else " ") + str(v)
        chunks.append(d + s)
    return chunks


# ================================================================ Shoga (geometry from build.py)
FOOT = (162, 404)          # where the toes close around a line
GRIP = (300, 184)          # between the mandibles: the thread ends here
BS = 0.44                  # Shoga's scale


def shoga_defs():
    return (
        '<linearGradient id="tailG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3FB98F"/><stop offset="1" stop-color="#2F7FC4"/></linearGradient>'
        '<linearGradient id="beakG" x1="0" y1="0" x2=".5" y2="1"><stop offset="0" stop-color="#FF5A66"/><stop offset="1" stop-color="#D81E3C"/></linearGradient>'
        f'<clipPath id="mClip"><path d="{BODY}"/><path d="{HEAD}"/></clipPath>'
    )


def shoga(part="all"):
    """Shoga facing right, in its own coordinates. part: back, front or all.

    Flight parts (spread wings) have class pf, perch parts (folded wing, feet) class pp.
    """
    wx, wy = WROOT
    far = (f'<g class="pf"><g transform="translate({wx + 40} {wy - 10}) scale(1.3)"><g class="wf"><path d="{FLY}" fill="#25864A" {OL} stroke-width="8"/>'
           f'<path d="{FLY_TIP}" fill="#1F5F8F" opacity=".6"/></g></g></g>')
    near = (f'<g class="pf"><g transform="translate({wx} {wy}) scale(1.4)"><g class="wn"><path d="{FLY}" fill="#3DB65C" {OL} stroke-width="8"/>'
            f'<path d="{FLY_TIP}" fill="#2A78B4"/><path d="{FLY_COV}" fill="#5BD46E"/>'
            f'<path d="M-30 -136C-6 -150 16 -170 30 -196M-50 -96C-20 -108 6 -126 20 -150" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".35"/>'
            f'<path d="M-6 14C34 -30 62 -112 46 -214" fill="none" {OL} stroke-width="8"/></g></g></g>')
    fold = (f'<g class="pp"><path d="{WING}" fill="#33A956" {OL} stroke-width="5"/>'
            '<path d="M110 326C124 316 140 318 152 330M122 350C136 342 150 344 160 354M104 300C118 292 134 294 146 304" '
            f'stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".55"/>'
            '<path d="M112 250C132 242 156 250 168 268" stroke="#9BE79A" stroke-width="4" fill="none" stroke-linecap="round" opacity=".7"/></g>')
    parts = [
        far,
        '<g class="tl">',
        f'<path d="{TAIL}" fill="url(#tailG)" {OL} stroke-width="9"/>',
        '<path d="M120 336C108 376 92 412 72 444" stroke="#BFF5EA" stroke-width="3" stroke-opacity=".6" fill="none" stroke-linecap="round"/>',
        '</g>',
        f'<g fill="{INK}" {OL} stroke-width="11"><path d="{BODY}"/><path d="{HEAD}"/></g>',
        f'<path class="pp" d="{FEET}" fill="#F6A38A" {OL} stroke-width="6"/>',
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
        fold,
        None,
        '<circle cx="222" cy="122" r="27" fill="#fff" stroke="#FF8A3D" stroke-width="6"/>',
        f'<circle cx="222" cy="122" r="31" fill="none" stroke="{INK}" stroke-width="3"/>',
        f'<g class="pu"><circle cx="228" cy="125" r="15" fill="{INK}"/>'
        '<circle cx="234" cy="116" r="6" fill="#fff"/><circle cx="222" cy="133" r="2.6" fill="#fff"/></g>',
        f'<path class="lid" d="M189 122C189 78 255 78 255 122C255 166 189 166 189 122Z" fill="#5BD46E" stroke="{INK}" stroke-width="3"/>',
        f'<path class="joy" d="M202 130C210 112 234 112 242 130" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>',
        f'<g class="jaw"><path d="{BEAK_LO}" fill="#8E1428" {OL} stroke-width="5"/></g>',
        f'<path d="{BEAK_UP}" fill="url(#beakG)" {OL} stroke-width="5"/>',
        '<path d="M280 108C304 102 328 116 334 140" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>',
        f'<circle cx="276" cy="112" r="3" fill="{INK}"/>',
        near,
    ]
    cut = parts.index(None)
    back, front = parts[:cut], parts[cut + 1:]
    return "".join(back if part == "back" else front if part == "front" else back + front)


# ================================================================ keyframe helpers
def pc(t, dur):
    return f(max(0.0, min(t, dur)) / dur * 100, 2) + "%"


def kf(name, frames, dur=L):
    """frames: [(t or (t, t2, ...), css)]; times in seconds."""
    frames = sorted(frames, key=lambda fr: fr[0] if not isinstance(fr[0], tuple) else fr[0][0])
    body = "".join(f"{','.join(pc(x, dur) for x in (t if isinstance(t, tuple) else (t,)))}{{{css}}}" for t, css in frames)
    return f"@keyframes {name}{{{body}}}"


def tr(x, y, a=None, s=None):
    out = f"translate({f(x, 0)}px,{f(y, 0)}px)"
    if a is not None:
        out += f" rotate({f(a, 0)}deg)"
    if s is not None:
        out += f" scale({f(s, 2).lstrip('0') or '0'})"
    return out


# ================================================================ choreography
def quad(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


SW0, SW1 = (-230, 70), (300, 40)        # swoop start and control point (top left, arcing down to G)
JERK = (G[0] - 16, G[1] - 6)


def pull_beak(p):
    x = JERK[0] + (XE - JERK[0]) * p
    y = JERK[1] + (LY - JERK[1]) * p - 22 * math.sin(math.pi * p)
    return (x, y)


def pull_times():
    return [T_PULL + (T_PULLEND - T_PULL) * k / PULL_K for k in range(PULL_K + 1)]


def thread_frames(knot, short_x):
    """[(t, dense points)] for one role, t inside the role."""
    dot = straight(X0 + 2)
    fr = [(0.0, dot), (T_SPILL0 - 0.02, knot), (T_CATCH, knot)]
    held = tighten(knot, 0.96, math.radians(4))
    fr.append((T_PULL, follow_end(held, JERK, 0.06)))
    for k, t in enumerate(pull_times()[1:], 1):
        p = PULL_EASE(k / PULL_K)
        if k == PULL_K:
            fr.append((t, straight(XE + 16, 11)))
        else:
            fr.append((t, unravel(held, p, pull_beak(p))))
    for t, bow, dx in TWANG:
        fr.append((t, straight(XE + dx, bow)))
    fr.append((T_REL, straight(XE)))
    fr.append((RECOIL[0], straight(short_x - 30)))
    fr.append((RECOIL[1], straight(short_x + 8)))
    fr.append((RECOIL[2], straight(short_x)))
    fr.append((T_LAND, straight(short_x)))
    fr.append((T_LAND + 0.1, droop(short_x, 9)))
    fr.append((T_LAND + 0.3, straight(short_x)))
    fr.append((T_RETRACT, straight(short_x)))
    fr.append((T_RETRACT + 0.32, straight(X0 - 6)))
    fr.append((T_RETRACT + 0.42, dot))
    return fr


def droop(x1, a):
    """The free end bends like a cantilever under a load at its tip."""
    out = []
    for i in range(D + 1):
        u = i / D
        out.append((X0 + (x1 - X0) * u, LY + a * u * u))
    return out


def perch_beak(short_x):
    """Beak position for Shoga standing (mirrored, facing the wordmark) with its toes on the line's end."""
    fx, fy = short_x - 16, LY + 1
    return (fx + BS * (FOOT[0] - GRIP[0]), fy - BS * (FOOT[1] - GRIP[1]))


def bird_track(short_x):
    """[(t, x, y, angle, mirror)] for the beak on the role clock; mirror -1 faces left."""
    out = [(0.0, -260, -300, 20, 1), (T_SWOOP - 0.01, -260, 70, 20, 1)]
    n = 9
    for k in range(n + 1):
        u = k / n
        ue = 1 - (1 - u) ** 1.35
        x, y = quad(SW0, SW1, G, ue)
        x2, y2 = quad(SW0, SW1, G, min(1, ue + 0.02))
        v = math.degrees(math.atan2(y2 - y, x2 - x)) if k < n else math.degrees(math.atan2(G[1] - SW1[1], G[0] - SW1[0]))
        out.append((T_SWOOP + (T_CATCH - T_SWOOP) * u, x, y, v + 35, 1))
    out.append((T_JERK, JERK[0], JERK[1], 12, 1))
    out.append((T_PULL, JERK[0], JERK[1], 30, 1))
    for k, t in enumerate(pull_times()[1:], 1):
        p = PULL_EASE(k / PULL_K)
        if k == PULL_K:
            out.append((t, XE + 16, LY, 48, 1))
        else:
            x, y = pull_beak(p)
            out.append((t, x, y, 58 - 8 * p, 1))
    for t, bow, dx in TWANG:
        out.append((t, XE + dx, LY, HOLD_A + dx * 0.5, 1))
    # hover: a slow sway around the beak; it leans back to look at the term
    t, k = TWANG[-1][0], 0
    while t + 0.9 < T_HINT:
        t += 0.9
        out.append((t, XE, LY, HOLD_A + (1.5 if k % 2 == 0 else -1), 1))
        k += 1
    out += [(T_HINT, XE, LY, HOLD_A, 1), (T_HINT + 0.25, XE, LY, HOLD_A - 5, 1), (T_HINT_END - 0.2, XE, LY, HOLD_A - 5, 1),
            (T_HINT_END + 0.1, XE, LY, HOLD_A, 1)]
    t, k = T_HINT_END + 0.1, 0
    while t + 0.9 < T_REL:
        t += 0.9
        out.append((t, XE, LY, HOLD_A + (1.5 if k % 2 == 0 else -1), 1))
        k += 1
    out.append((T_REL, XE, LY, HOLD_A - 1, 1))
    out += [(T_REL + 0.22, XE + 70, LY - 110, 10, 1), (T_REL + 0.4, XE + 260, LY - 380, -4, 1),
            (T_REL + 0.41, 1440, -210, -50, -1)]
    bx, by = perch_beak(short_x)
    for u, a in [(0.35, -48), (0.68, -30), (0.9, -12)]:
        x, y = quad((1440, -210), (bx + 380, by - 150), (bx, by), u)
        out.append((T_REL + 0.41 + (T_LAND - T_REL - 0.41) * u, x, y, a, -1))
    out += [(T_LAND, bx, by, 8, -1), (T_LAND + 0.12, bx, by, 0, -1), (T_TAKEOFF, bx, by, 0, -1),
            (T_TAKEOFF + 0.14, bx - 50, by - 70, 10, -1), (T_TAKEOFF + 0.5, -170, -320, 18, -1), (T_TAKEOFF + 0.51, -260, -300, 20, 1),
            (L, -260, -300, 20, 1)]
    return out


def smil_bird(track):
    kt = ";".join(f(t / L, 4) for t, *_ in track)
    tv = ";".join(f"{f(x, 0)} {f(y, 0)}" for _, x, y, _, _ in track)
    rv = ";".join(f(a, 0) for _, _, _, a, _ in track)
    sv = ";".join(f"{m} 1" for *_, m in track)
    common = f'dur="{f(L)}s" repeatCount="indefinite" keyTimes="{kt}"'
    return (f'<animateTransform attributeName="transform" type="translate" {common} values="{tv}"/>'
            f'<animateTransform attributeName="transform" type="rotate" additive="sum" {common} values="{rv}"/>'
            f'<animateTransform attributeName="transform" type="scale" additive="sum" calcMode="discrete" {common} values="{sv}"/>')


def flaps():
    """Wing angle keyframes on the role clock: effort sets the beat."""
    UP, DOWN = -48, -168
    fr = [(0, -140), (T_SWOOP - 0.3, -140)]

    def beat(t0, t1, period, up=UP, down=DOWN):
        out, t = [], t0
        while t + period <= t1 + 1e-6:
            out += [(t, up), (t + period * 0.5, down)]
            t += period
        return out, t
    a, t = beat(T_SWOOP - 0.2, T_SWOOP + 0.4, 0.2)
    fr += a
    fr += [(T_SWOOP + 0.4, UP), (T_SWOOP + 0.48, -62), (T_CATCH - 0.13, -66), (T_CATCH - 0.03, -150), (T_CATCH + 0.05, -150),
           (T_JERK, -110), (T_PULL, -30)]
    a, t = beat(T_PULL + 0.04, T_PULLEND, 0.22)
    fr += a
    a, t = beat(t, T_PULLEND + 0.8, 0.32, -80, -158)
    fr += a
    a, t = beat(t, T_REL - 0.05, 0.75, -128, -166)          # hover: an easy, shallow beat, wings swept back
    fr += a
    a, t = beat(T_REL, T_REL + 0.4, 0.18)
    fr += a
    fr += [(T_REL + 0.42, -72), (T_LAND - 0.2, -78), (T_LAND - 0.06, -150), (T_LAND + 0.05, -100), (T_TAKEOFF, -100)]
    a, t = beat(T_TAKEOFF + 0.02, T_TAKEOFF + 0.56, 0.18)
    fr += a
    fr += [(T_TAKEOFF + 0.6, -140), (L, -140)]
    css = []
    for tt, ang in fr:
        sy = 0.82 if ang < -140 else 1
        css.append((tt, f"transform:rotate({ang}deg)" + (f" scaleY({sy})" if sy != 1 else "")))
    return css


# ================================================================ jargon on the knot
def knot_words(ty, knot, words, seed, size=18):
    """Place each word along a gentle stretch of the knot; long words may shrink a little to fit."""
    rnd = random.Random(seed)
    step = math.dist(knot[1], knot[2])
    heading = [math.atan2(knot[min(D, i + 2)][1] - knot[max(0, i - 2)][1], knot[min(D, i + 2)][0] - knot[max(0, i - 2)][0]) for i in range(D + 1)]
    placed, taken = [], []
    for word in words:
        items, adv = ty.mono.layout(word)
        best = None
        for sz in (size, size * 0.86, size * 0.76):
            s = sz / ty.mono.em
            wlen = adv * s + 10
            nspan = int(wlen / step) + 1
            for _ in range(9000):
                i0 = rnd.randint(int(D * 0.06), int(D * 0.86) - nspan)
                i1 = i0 + nspan
                turn = 0
                for i in range(i0, i1):
                    dh = (heading[i + 1] - heading[i] + math.pi) % (2 * math.pi) - math.pi
                    turn = max(turn, abs(dh))
                span = abs(((heading[i1] - heading[i0]) + math.pi) % (2 * math.pi) - math.pi)
                if span > 1.0 or turn > 0.11:
                    continue
                mid = knot[(i0 + i1) // 2]
                if any(math.dist(mid, q) < 24 + wlen * 0.28 + ql * 0.28 for q, ql in taken):
                    continue
                if not (C0[0] - KRX * 1.05 < mid[0] < C0[0] + KRX * 1.15 and C0[1] - KRY * 1.1 < mid[1] < C0[1] + KRY * 1.1):
                    continue
                best = (i0, i1, s, wlen)
                break
            if best:
                break
        if not best:
            print(f"note: no gentle stretch of the knot fits {word!r}; it is left out there", file=sys.stderr)
            continue
        i0, i1, s, wlen = best
        mid = knot[(i0 + i1) // 2]
        taken.append((mid, wlen))
        forward = knot[i1][0] - knot[i0][0] >= 0
        glyphs = []
        for name, px in items:
            gx = px * s + ty.mono.adv(name) * s / 2 + 5
            si = i0 + gx / step if forward else i1 - gx / step
            si = max(0, min(D - 1, si))
            j = int(si)
            fr_ = si - j
            ax, ay = knot[j]
            bx, by = knot[j + 1]
            x, y = ax + (bx - ax) * fr_, ay + (by - ay) * fr_
            h = heading[j] if forward else heading[j] + math.pi
            nx, ny = math.sin(h), -math.cos(h)
            x, y = x + nx * 5, y + ny * 5
            glyphs.append((name, x, y, math.degrees(h), s))
        placed.append((word, glyphs, ((i0 + i1) / 2) / D, mid[0], mid[1]))
    return placed


# ================================================================ the document
def banner():
    ty = new_type()
    roles = ROLES
    wm_size = 58
    wm_w = ty.xb.width("Shoga-Speaks", wm_size, tracking=-0.02)
    short_x = X0 + wm_w + 96

    # one task, one knot: each role gets the same tangle, given a small twist so it never looks pasted
    base = make_knot(KNOT_SEED)[0]
    knots = [tighten(base, r["twist"][0], math.radians(r["twist"][1])) for r in roles]
    frames = [thread_frames(k, short_x) for k in knots]

    # ---- SMIL thread: one values list on the whole loop per chunk
    times, shapes = [], []
    for ri, fr in enumerate(frames):
        for t, pts in fr:
            times.append(ri * L + t)
            shapes.append(fit(pts))
    times.append(T)
    shapes.append(shapes[0])
    nch = N_SEG // CHUNK
    kt = ";".join(f(t / T, 4) for t in times)
    chunk_defs = []
    for c in range(nch):
        vals = ";".join(s[c] for s in shapes)
        chunk_defs.append(f'<path id="c{c}" d="{shapes[0][c]}"><animate attributeName="d" dur="{f(T)}s" repeatCount="indefinite" '
                          f'keyTimes="{kt}" values="{vals}"/></path>')

    css = []
    add = css.append
    add(f"svg{{background:{PAPER}}}")
    add(kf("vis", [(0, "opacity:1"), (L - 0.001, "opacity:1"), ((L, T), "opacity:0")], T))
    for i in range(N):
        add(f".r{i}{{animation:vis {f(T)}s steps(1,end) infinite;animation-delay:{f(-((N - i) % N) * L)}s}}")
    add(".r1,.r2{opacity:0}")

    # ---- thread look: halo gap + offset shadow + cord + sheen
    cord_cols = []
    for i in range(nch):
        k = i / (nch - 1)
        a, b = (0x0B, 0x1E, 0x15), (0x24, 0x42, 0x33)
        cord_cols.append("#%02X%02X%02X" % tuple(round(a[j] + (b[j] - a[j]) * k) for j in range(3)))
    col_frames = []
    for ri, r in enumerate(roles):
        o = ri * L
        col_frames += [(o + 0.0, f"stroke:{GREEN}"), (o + T_SPILL0 - 0.05, f"stroke:{GREEN}"), (o + T_SPILL0 + 0.05, "stroke:var(--ink)"), (o + T_PULL + 1.3, "stroke:var(--ink)"),
                       (o + T_PULLEND, f"stroke:{r['color']}"), (o + T_REL, f"stroke:{r['color']}"), (o + RECOIL[1], f"stroke:{GREEN}")]
    col_frames.append((T, f"stroke:{GREEN}"))
    add(kf("cord", col_frames, T))
    for i, c in enumerate(cord_cols):
        add(f".k{i}{{--ink:{c}}}")
    add(f".cd{{fill:none;stroke-width:5.6;stroke-linecap:round;stroke:{GREEN};animation:cord {f(T)}s linear infinite}}")
    add(".hl{fill:none;stroke:#fff;stroke-width:1.4;stroke-linecap:butt;opacity:0;animation:hl 8s linear infinite}")
    add(kf("hl", [((0, T_SPILL0), "opacity:0"), ((T_SPILL0 + 0.3, T_PULL + 1.2), "opacity:.2"), ((T_PULLEND, L), "opacity:0")]))
    add(f".ha{{fill:none;stroke:{PAPER};stroke-width:11;stroke-linecap:butt;opacity:0;animation:ha 8s linear infinite}}")
    add(kf("ha", [((0, T_SPILL0), "opacity:0"), ((T_SPILL0 + 0.25, T_PULL + 1.1), "opacity:1"), ((T_PULLEND - 0.1, L), "opacity:0")]))
    add(f".sh{{fill:none;stroke:{INK};stroke-width:7;stroke-linecap:butt;opacity:.07;animation:sh 8s linear infinite}}")
    add(kf("sh", [((0, T_SPILL0), "opacity:.07"), ((T_SPILL0 + 0.3, T_PULL + 1.1), "opacity:.16"), ((T_PULLEND, L), "opacity:.07")]))

    jit = [(0, "transform:none"), (T_KNOT, "transform:none")]
    rnd = random.Random(3)
    t = T_KNOT
    while t < T_CATCH - 0.12:
        t += 0.08
        jit.append((t, f"transform:translate({f(rnd.uniform(-1.6, 1.6), 0)}px,{f(rnd.uniform(-1.3, 1.3), 0)}px) rotate({f(rnd.uniform(-.5, .5), 1)}deg)"))
    jit += [((T_CATCH, L), "transform:none")]
    add(kf("jit", jit))
    add(f".jit{{transform-origin:{C0[0]}px {C0[1]}px;animation:jit 8s linear infinite}}")

    # ---- Shoga: position on the SMIL clock (same as the thread), body language in CSS
    track = bird_track(short_x)
    bird_anim = smil_bird(track)
    add(kf("flap", flaps()))
    add(".wn,.wf{transform-origin:0 0;animation:flap 8s ease-in-out infinite}.wn{transform:rotate(-140deg)}.wf{transform:rotate(-128deg);animation-delay:-.05s}")
    add(kf("tl", [((0, T_CATCH), "transform:rotate(14deg)"), (T_JERK, "transform:rotate(-12deg)"), (T_PULL + 0.3, "transform:rotate(10deg)"),
                  (T_PULLEND, "transform:rotate(-6deg)"), (T_PULLEND + 0.4, "transform:rotate(4deg)"), ((T_PULLEND + 0.8, T_REL), "transform:rotate(0deg)"),
                  (T_REL + 0.3, "transform:rotate(16deg)"), (T_LAND - 0.1, "transform:rotate(18deg)"), (T_LAND + 0.15, "transform:rotate(-6deg)"),
                  ((T_LAND + 0.4, T_TAKEOFF), "transform:rotate(0deg)"), ((T_TAKEOFF + 0.3, L), "transform:rotate(16deg)")]))
    add(".tl{transform-origin:140px 330px;animation:tl 8s ease-in-out infinite}")
    add(kf("jaw", [((0, T_CATCH - 0.35), "transform:none"), ((T_CATCH - 0.2, T_CATCH - 0.05), "transform:rotate(24deg)"), ((T_CATCH, T_REL - 0.04), "transform:none"),
                   (T_REL + 0.06, "transform:rotate(26deg)"), ((T_REL + 0.4, L), "transform:none")]))
    add(".jaw{transform-origin:278px 170px;animation:jaw 8s ease-in-out infinite}")
    b1, b2, b3 = T_STORY + 1.6, T_CARD_FULL + 2.6, T_LAND + 0.6
    add(kf("lid", [((0, b1), "transform:scaleY(0)"), (b1 + 0.1, "transform:scaleY(1)"), (b1 + 0.55, "transform:scaleY(1)"),
                   ((b1 + 0.68, b2), "transform:scaleY(0)"), (b2 + 0.07, "transform:scaleY(1)"), ((b2 + 0.16, b3), "transform:scaleY(0)"),
                   (b3 + 0.07, "transform:scaleY(1)"), ((b3 + 0.16, L), "transform:scaleY(0)")]))
    add(".lid{transform-origin:222px 89px;transform:scaleY(0);animation:lid 8s ease-in-out infinite}")
    add(kf("joy", [((0, b1 + 0.08), "opacity:0"), ((b1 + 0.12, b1 + 0.55), "opacity:1"), ((b1 + 0.6, L), "opacity:0")]))
    add(".joy{opacity:0;animation:joy 8s steps(1,end) infinite}")
    look, back = "transform:translate(-5px,-1px)", "transform:translate(-10px,7px)"
    add(kf("pu", [((0, T_PULLEND), "transform:none"), ((T_PULLEND + 0.5, T_HINT), look), ((T_HINT + 0.15, T_HINT_END - 0.2), back),
                  ((T_HINT_END + 0.05, T_REL), look), (T_REL + 0.2, "transform:none"), ((T_LAND + 0.15, T_TAKEOFF), look), ((T_TAKEOFF + 0.2, L), "transform:none")]))
    add(f".pu{{{look};animation:pu 8s ease-in-out infinite}}")
    add(kf("pp", [((0, T_LAND - 0.06), "opacity:0"), ((T_LAND - 0.05, T_TAKEOFF + 0.03), "opacity:1"), ((T_TAKEOFF + 0.04, L), "opacity:0")]))
    add(kf("pf", [((0, T_LAND - 0.06), "opacity:1"), ((T_LAND - 0.05, T_TAKEOFF + 0.03), "opacity:0"), ((T_TAKEOFF + 0.04, L), "opacity:1")]))
    add(".pp{opacity:0;animation:pp 8s steps(1,end) infinite}.pf{animation:pf 8s steps(1,end) infinite}")

    # ---- the question: typed big and central, then docked top left as "you asked"
    QS = 40
    qitems, qadv = ty.mono.layout(PROMPT_TXT)
    qs = QS / ty.mono.em
    qw = qadv * qs
    boxW, boxH = qw + 60 + 30, 84
    bxq, byq = (W - boxW) / 2, 140
    DOCK = (70, 46)
    DS = 0.43
    dock_css = f"transform:translate({f(DOCK[0] - bxq, 1)}px,{f(DOCK[1] - byq, 1)}px) scale({DS})"
    chars, curk = [], []
    tx0 = bxq + 30
    for i, (name, px) in enumerate(qitems):
        gid = ty.mono.gid(name)
        ti = T_TYPE0 + i * CH_DT
        if gid not in ty.mono.empty:
            col = "#5BD46E" if i == 0 else "#EAF8EF"
            chars.append(f'<use class="y{i}" href="#{gid}" fill="{col}" transform="translate({f(tx0 + px * qs, 1)} {byq + 55}) scale({f(qs, 3)})"/>')
            add(kf(f"y{i}", [((0, ti), "opacity:0"), ((ti + 0.01, L), "opacity:1")]))
            add(f".y{i}{{animation:y{i} 8s steps(1,end) infinite}}")
        curk.append((ti, f"opacity:1;transform:translateX({f((px + ty.mono.adv(name)) * qs, 0)}px)"))
    curk = [((0, T_TYPE0), "opacity:1;transform:none")] + curk + [(T_SPILL0, "opacity:1;transform:translateX(" + f(qw, 0) + "px)"), ((T_SPILL0 + 0.01, L), "opacity:0")]
    add(kf("cur", curk))
    add(".cur{opacity:0;animation:cur 8s steps(1,end) infinite}.cbl{animation:cbl 1s steps(1,end) infinite}@keyframes cbl{50%{opacity:0}}")
    cur = (f'<g class="cur"><rect class="cbl" x="{f(tx0 + 4, 1)}" y="{byq + 22}" width="19" height="42" rx="2" fill="#5BD46E"/></g>')
    term = (f'<g class="qt"><rect x="{f(bxq, 1)}" y="{byq + 4}" width="{f(boxW, 1)}" height="{boxH}" rx="16" fill="{INK}" opacity=".14"/>'
            f'<rect x="{f(bxq, 1)}" y="{byq}" width="{f(boxW, 1)}" height="{boxH}" rx="16" fill="{INK}"/>{"".join(chars)}{cur}</g>')
    add(kf("qt", [(0, "opacity:0;transform:scale(.97)"), ((0.25, T_SPILL0 + 0.1), "opacity:1;transform:none"),
                  ((T_SPILL0 + 0.75, L - 0.45), "opacity:1;" + dock_css), ((L - 0.2, L), "opacity:0;" + dock_css)]))
    add(f".qt{{transform-origin:{f(bxq, 1)}px {byq}px;{dock_css};animation:qt 8s ease-in-out infinite}}")
    asked = ty.sb.text("YOU ASKED", 13, DOCK[0] + 2, DOCK[1] - 8, tracking=0.1, extra=' fill="#5F766A"')[0]
    add(kf("ya", [((0, T_SPILL0 + 0.7), "opacity:0"), ((T_SPILL0 + 0.95, L - 0.45), "opacity:1"), ((L - 0.2, L), "opacity:0")]))
    add(".ya{animation:ya 8s linear infinite}")
    caption = term + f'<g class="ya">{asked}</g>'
    bx0 = DOCK[0] + boxW * DS + 14
    cap_y = DOCK[1] + boxH * DS / 2 + 6
    spill_from = (tx0 + qw + 14, byq + 44)

    # ---- jargon on the knot: the task's own words, the same in every role
    tag_txt, tag_w = ty.mono.text("▸ Technical", 17, 0, 0)
    tw = tag_w + 30
    CARD = (TAGX - 14, LY + 24)
    tag_cx, tag_cy = CARD[0] + tw / 2, CARD[1] + 18
    word_svg = []
    for ri, r in enumerate(roles):
        placed = knot_words(ty, knots[ri], JARGON, 100 + ri * 7)
        groups = []
        ordered = sorted(range(len(placed)), key=lambda j: -abs(placed[j][2] - 0.27))
        for rank, j in enumerate(ordered):
            word, glyphs, um, cx, cy = placed[j]
            uses = "".join(f'<use href="#{ty.mono.gid(n)}" transform="translate({round(x)} {round(y)})rotate({round(a)})scale({f(gs, 3)})" x="{round(-ty.mono.adv(n) / 2)}"/>'
                           for n, x, y, a, gs in glyphs if ty.mono.gid(n) not in ty.mono.empty)
            name = f"w{ri}_{j}"
            t0 = T_PULL + 0.06 + rank * (0.9 / max(1, len(placed) - 1))
            sx = 18 if um > 0.27 else -10
            dx, dy = tag_cx - cx, tag_cy - cy
            rot = (rank % 2 * 2 - 1) * (25 + rank * 3)
            fr = [((0, T_SPILL1 - 0.15 + rank * 0.03), "opacity:0;transform:none"), ((T_SPILL1 + 0.15 + rank * 0.03, t0), "opacity:1;transform:none"),
                  (t0 + 0.14, f"opacity:1;transform:{tr(sx, -6)}")]
            for k in range(1, 4):
                u = k / 3
                x = sx + (dx - sx) * u
                y = -6 + (dy + 6) * u * u - 12 * math.sin(math.pi * u)
                op = 1 if u < 0.75 else 0.6 if u < 1 else 0
                fr.append((t0 + 0.14 + 0.46 * u, f"opacity:{op};transform:{tr(x, y, rot * u, 1 - 0.65 * u)}"))
            fr[-1] = ((fr[-1][0], L), fr[-1][1])
            add(kf(name, fr))
            add(f".{name}{{transform-origin:{f(cx, 0)}px {f(cy, 0)}px;animation:{name} 8s linear infinite}}")
            groups.append(f'<g class="{name}">{uses}</g>')
        word_svg.append(f'<g class="r{ri} kw"><g fill="#9A3B1E" stroke="{PAPER}" stroke-width="20" stroke-linejoin="round" paint-order="stroke">{"".join(groups)}</g></g>')

    # ---- the story: two lines rising out of the line
    MS = 36
    maxw = max(ty.b.width(t, MS) for r in roles for t in r["say"])
    MS = min(MS, MS * 860 / maxw)
    lh = MS * 1.24
    MX = X0 + 4
    msg_svg, hints = [], []
    HL = "#F2B705"

    def highlight(x0, w, yb, size):
        return (f'<rect x="{f(x0 - 4)}" y="{f(yb - size * 0.8)}" width="{f(w + 8)}" height="{f(size * 1.02)}" rx="5" fill="#FFD166" opacity=".34"/>'
                f'<path d="M{f(x0)} {f(yb + size * 0.17)}H{f(x0 + w)}" stroke="{HL}" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="0 5.5"/>')

    def popover(r, term, meaning, tip, up=True):
        ts, ms_ = 18, 18
        w1 = ty.b.width(term, ts)
        w2 = ty.sb.width(meaning, ms_)
        pw, ph = w1 + 14 + w2 + 34, 42
        px = max(16, min(W - 16 - pw, tip[0] - 34))
        py = tip[1] - 9 - ph if up else tip[1] + 9
        ax = tip[0]
        if up:
            arrow = f'M{f(ax - 8)} {f(py + ph - 1)}L{f(ax)} {f(tip[1])}L{f(ax + 8)} {f(py + ph - 1)}Z'
        else:
            arrow = f'M{f(ax - 8)} {f(py + 1)}L{f(ax)} {f(tip[1])}L{f(ax + 8)} {f(py + 1)}Z'
        tb = py + ph / 2 + 6.5
        body = (f'<rect x="{f(px + 1)}" y="{f(py + 4)}" width="{f(pw)}" height="{ph}" rx="12" fill="{INK}" opacity=".1"/>'
                f'<path d="{arrow}" fill="#fff" stroke="{r["color"]}" stroke-width="1.6" stroke-linejoin="round"/>'
                f'<rect x="{f(px)}" y="{f(py)}" width="{f(pw)}" height="{ph}" rx="12" fill="#fff" stroke="{r["color"]}" stroke-width="1.6"/>'
                f'<path d="{arrow}" fill="#fff" transform="translate(0 {-2 if up else 2})"/>'
                + ty.b.text(term, ts, px + 17, tb, extra=f' fill="{r["color"]}"')[0]
                + ty.sb.text(meaning, ms_, px + 17 + w1 + 14, tb, extra=f' fill="{INK}"')[0])
        return f'<g class="hp" style="transform-origin:{f(tip[0])}px {f(tip[1])}px">{body}</g>'

    for ri, r in enumerate(roles):
        groups = []
        j = 0
        hint_kind, hint_line, term, meaning = r["hint"]
        hint_svg = ""
        for li, line in enumerate(r["say"]):
            yb = LY - 15 - (len(r["say"]) - 1 - li) * lh
            off = LY - yb + MS * 0.8 + 8
            x = MX
            sp = ty.b.width(" ", MS)
            for wd in line.split(" "):
                g, w = ty.b.text(wd, MS, x, yb, extra=f' fill="{INK}"')
                frac = (XE - (x + w)) / (XE - short_x + 30)
                d_in = j * WORD_DT
                d_out = max(0.0, frac) * (RECOIL[0] - T_REL) - 0.02
                groups.append(f'<g class="mr{li}" style="animation-delay:{f(d_in - L, 3)}s"><g class="ms{li}" style="animation-delay:{f(d_out - L, 3)}s">{g}</g></g>')
                x += w + sp
                j += 1
            if hint_kind == "say" and li == hint_line:
                x0 = MX + ty.b.width(line[:line.index(term)], MS)
                w = ty.b.width(term, MS)
                last = li == len(r["say"]) - 1
                tip = (x0 + w / 2, LY + 7) if last else (x0 + w / 2, yb - MS * 0.8 - 5)
                hint_svg = f'<g class="hh">{highlight(x0, w, yb, MS)}</g>' + popover(r, term, meaning, tip, up=not last)
        bw = ty.xb.width(r["role"], 16) + 26
        badge = (f'<g class="bdg"><rect x="{f(bx0)}" y="{cap_y - 22}" width="{f(bw)}" height="30" rx="15" fill="{r["color"]}"/>'
                 + ty.xb.text(r["role"], 16, bx0 + bw / 2, cap_y - 1.5, anchor="middle", extra=' fill="#fff"')[0]
                 + ty.sb.text(r["lang"], 18, bx0 + bw + 11, cap_y - 1, extra=' fill="#5F766A"')[0] + '</g>')
        msg_svg.append(f'<g class="r{ri}">{badge}<g clip-path="url(#above)">{"".join(groups)}</g></g>')
        offs = [LY - (LY - 15 - (len(r["say"]) - 1 - li) * lh) + MS * 0.8 + 8 for li in range(len(r["say"]))]
        hints.append((ri, hint_svg))
    for li, off in enumerate(offs):
        o = f"transform:translateY({f(off, 0)}px)"
        add(kf(f"mr{li}", [((0, T_MSG), o), (T_MSG + 0.32, "transform:translateY(-3px)"), ((T_MSG + 0.48, T_REL + 0.45), "transform:none"), ((T_REL + 0.47, L), o)]))
        add(kf(f"ms{li}", [((0, T_REL), "opacity:1;transform:none"), ((T_REL + 0.16, L), "opacity:0;" + o)]))
        add(f".mr{li}{{animation:mr{li} 8s ease-out infinite}}.ms{li}{{animation:ms{li} 8s ease-in infinite}}")
    add(kf("bdg", [((0, T_MSG + 0.2), "opacity:0;transform:translateX(-10px)"), ((T_MSG + 0.5, T_REL), "opacity:1;transform:none"),
                   ((T_REL + 0.2, L), "opacity:0;transform:none")]))
    add(".bdg{animation:bdg 8s ease-out infinite}")
    add(kf("hh", [((0, T_HINT), "opacity:0"), ((T_HINT + 0.15, T_REL - 0.05), "opacity:1"), ((T_REL + 0.05, L), "opacity:0")]))
    add(kf("hh2", [((0, T_HINT), "opacity:0"), ((T_HINT + 0.15, T_FOLD - 0.05), "opacity:1"), ((T_FOLD + 0.05, L), "opacity:0")]))
    add(".hh{opacity:0;animation:hh 8s linear infinite}.hc .hh{animation-name:hh2}")
    add(kf("hp", [((0, T_HINT + 0.12), "opacity:0;transform:scale(.6)"), (T_HINT + 0.3, "opacity:1;transform:scale(1.04)"),
                  ((T_HINT + 0.4, T_HINT_END - 0.15), "opacity:1;transform:none"), ((T_HINT_END, L), "opacity:0;transform:scale(.9)")]))
    add(".hp{opacity:0;animation:hp 8s ease-out infinite}")

    # ---- ▸ Technical: the tag the jargon falls into, then the card it unfolds into
    first_land = T_PULL + 0.04 + 0.6
    add(kf("tag", [((0, first_land - 0.05), "opacity:0;transform:rotate(-88deg)"), (first_land + 0.12, "opacity:1;transform:rotate(14deg)"),
                   (first_land + 0.4, "transform:rotate(-8deg)"), (first_land + 0.7, "transform:rotate(4deg)"),
                   (first_land + 1.0, "transform:rotate(-1.5deg)"), ((first_land + 1.3, T_REL), "opacity:1;transform:none"),
                   (T_REL + 0.04, "opacity:1;transform:rotate(-6deg)"), ((T_REL + 0.3, L), "opacity:0;transform:translateY(46px) rotate(24deg)")]))
    add(f".tag{{transform-origin:{TAGX}px {LY}px;animation:tag 8s ease-in-out infinite}}")
    CS, CLH = 17, 24
    tri_name = ty.mono.cmap[ord("▸")]
    tri_adv = ty.mono.adv(tri_name) * CS / ty.mono.em
    tri = ty.mono.text("▸", CS, 15, 24.5, extra=' fill="#4F6359"')[0]
    tech = ty.mono.text("Technical", CS, 15 + ty.mono.width("▸ ", CS), 24.5, extra=' fill="#4F6359"')[0]
    add(kf("tri", [((0, T_CARD), "transform:none"), ((T_CARD + 0.22, T_FOLD + 0.05), "transform:rotate(90deg)"), ((T_FOLD + 0.25, L), "transform:none")]))
    add(f".tri{{transform-origin:{f(15 + tri_adv / 2)}px 18.5px;transform:rotate(90deg);animation:tri 8s ease-in-out infinite}}")
    add(kf("cl", [((0, T_CARD + 0.22), "opacity:0;transform:translateY(-6px)"), ((T_CARD + 0.42, T_FOLD - 0.1), "opacity:1;transform:none"),
                  ((T_FOLD + 0.05, L), "opacity:0;transform:translateY(-6px)")]))
    add(".cl{animation:cl 8s ease-out infinite}")
    tags = []
    for ri, r in enumerate(roles):
        cwid = max(ty.mono.width(t, CS) for t in r["card"]) + 36
        chei = 36 + CLH * len(r["card"]) + 14
        sx0, sy0 = tw / cwid, 36 / chei
        name = f"cb{ri}"
        add(kf(name, [((0, T_CARD), f"transform:scale({f(sx0, 3)},{f(sy0, 3)})"), (T_CARD + 0.26, "transform:scale(1,1.03)"),
                      ((T_CARD + 0.36, T_FOLD), "transform:none"), ((T_FOLD + 0.3, L), f"transform:scale({f(sx0, 3)},{f(sy0, 3)})")]))
        add(f".{name}{{transform-origin:0 0;animation:{name} 8s ease-in-out infinite}}")
        lines = []
        for k, t in enumerate(r["card"]):
            yb = 36 + CLH * (k + 1) - 2
            lines.append(f'<g class="cl" style="animation-delay:{f(k * 0.07 - L, 2)}s">'
                         + ty.mono.text(t, CS, 18, yb, extra=' fill="#2E4238"')[0] + '</g>')
        hint_in_card = ""
        kind, li, term, meaning = r["hint"]
        if kind == "card":
            t = r["card"][li]
            x0 = 18 + ty.mono.width(t[:t.index(term)], CS)
            w = ty.mono.width(term, CS)
            yb = 36 + CLH * (li + 1) - 2
            hint_in_card = f'<g class="hc"><g class="hh">{highlight(x0, w, yb, CS)}</g></g>'
            hints[ri] = (ri, popover(r, term, meaning, (CARD[0] + x0 + w / 2, CARD[1] + yb + 6), up=False))
        tags.append(f'<g class="r{ri}"><g class="tag"><path d="M{TAGX} {LY + 2}V{LY + 24}" stroke="{INK}" stroke-opacity=".55" stroke-width="1.6"/>'
                    f'<g transform="translate({CARD[0]} {CARD[1]})">'
                    f'<rect class="{name}" x="1" y="3" width="{f(cwid)}" height="{chei}" rx="10" fill="{INK}" opacity=".08"/>'
                    f'<rect class="{name}" width="{f(cwid)}" height="{chei}" rx="10" fill="#fff" stroke="{INK}" stroke-opacity=".28" stroke-width="1.5" vector-effect="non-scaling-stroke"/>'
                    f'<circle cx="14" cy="0" r="3.2" fill="#fff" stroke="{INK}" stroke-opacity=".5" stroke-width="1.5"/>'
                    f'<g class="tri">{tri}</g>{tech}'
                    f'<g class="cl"><path d="M14 36H{f(cwid - 14)}" stroke="{INK}" stroke-opacity=".1" stroke-width="1.5"/></g>'
                    f'{hint_in_card}{"".join(lines)}</g></g></g>')

    # ---- brand: wordmark on the recoiled line, motto below, Shoga perched on the end, the promise on the right
    wm = ty.xb.text("Shoga-Speaks", wm_size, X0 + 2, LY - 16, tracking=-0.02, extra=f' fill="{INK}"')[0]
    m1, mw1 = ty.b.text("Seedhi baat, no bakwas.", 24, X0 + 3, LY + 44, extra=f' fill="{GREEN}"')
    m2 = ty.sb.text("Straight talk, no nonsense.", 21, X0 + 3 + mw1 + 29, LY + 44, extra=' fill="#62786C"')[0]
    motto = m1 + f'<path d="M{f(X0 + 3 + mw1 + 14)} {LY + 25}V{LY + 49}" stroke="{INK}" stroke-opacity=".25" stroke-width="2" stroke-linecap="round"/>' + m2
    add(kf("wm", [((0, T_WM), "transform:translateY(70px)"), (T_WM + 0.3, "transform:translateY(-3px)"), ((T_WM + 0.45, T_WMOUT), "transform:none"),
                  ((T_WMOUT + 0.25, L), "transform:translateY(70px)")]))
    add(".wm{animation:wm 8s ease-out infinite}")
    add(kf("mo", [((0, T_WM + 0.12), "transform:translateY(-58px)"), (T_WM + 0.42, "transform:translateY(2px)"), ((T_WM + 0.55, T_WMOUT - 0.05), "transform:none"),
                  ((T_WMOUT + 0.2, L), "transform:translateY(-58px)")]))
    add(".mo{animation:mo 8s ease-out infinite}")
    tx = short_x + 118
    tag1 = ty.b.text("Claude Code explains what it did", 22, tx, LY - 62, extra=' fill="#3E5A4B"')[0]
    tag2 = ty.b.text("in your language, for your role.", 22, tx, LY - 34, extra=' fill="#3E5A4B"')[0]
    chips, cx_ = [], tx
    for i, r in enumerate(roles):
        bw = ty.xb.width(r["role"], 14) + 22
        lw = ty.sb.width(r["lang"], 16)
        chips.append(f'<g class="ch" style="animation-delay:{f(i * 0.1 - L, 2)}s"><rect x="{f(cx_)}" y="{LY - 12}" width="{f(bw)}" height="26" rx="13" fill="{r["color"]}"/>'
                     + ty.xb.text(r["role"], 14, cx_ + bw / 2, LY + 6, anchor="middle", extra=' fill="#fff"')[0]
                     + ty.sb.text(r["lang"], 16, cx_ + bw + 8, LY + 6.5, extra=' fill="#5F766A"')[0] + '</g>')
        cx_ += bw + 8 + lw + 26
    rule = f'<path d="M{f(tx - 26)} {LY - 84}V{LY + 14}" stroke="{INK}" stroke-opacity=".16" stroke-width="2" stroke-linecap="round"/>'
    tagline = f'<g class="tg">{rule}{tag1}{tag2}</g>{"".join(chips)}'
    add(kf("tg", [((0, T_LAND), "opacity:0;transform:translateX(-14px)"), ((T_LAND + 0.35, T_WMOUT - 0.05), "opacity:1;transform:none"),
                  ((T_WMOUT + 0.2, L), "opacity:0;transform:none")]))
    add(kf("ch", [((0, T_LAND + 0.12), "opacity:0;transform:translateY(8px)"), ((T_LAND + 0.4, T_WMOUT - 0.02), "opacity:1;transform:none"),
                  ((T_WMOUT + 0.14, L), "opacity:0;transform:none")]))
    add(".tg{opacity:0;animation:tg 8s ease-out infinite}.ch{opacity:0;animation:ch 8s ease-out infinite}")

    pin = (f'<circle cx="{X0 + 1}" cy="{LY + 3}" r="7.5" fill="{INK}" opacity=".12"/>'
           f'<circle cx="{X0}" cy="{LY}" r="7" fill="{INK}"/><circle cx="{X0 - 2}" cy="{LY - 2.2}" r="2.2" fill="#fff" opacity=".55"/>')

    # ---- thread with the extra detail loops interleaved
    thread = []
    loops = [extra_loops(r["loops"]) for r in roles]
    xl_defs = []
    slots = {0: 0, 2: 1, 3: 2, 4: 3}
    for c in range(nch):
        thread.append(f'<g class="k{c}"><use href="#c{c}" class="sh" x="1" y="6"/><use href="#c{c}" class="ha"/>'
                      f'<use href="#c{c}" class="cd"/><use href="#c{c}" class="hl" y="-1"/></g>')
        if c in slots:
            j = slots[c]
            grp = []
            for ri in range(N):
                xl_defs.append(f'<path id="q{ri}{j}" vector-effect="non-scaling-stroke" d="{loops[ri][j]}"/>')
                grp.append(f'<g class="r{ri}"><use href="#q{ri}{j}" class="sh" x="1" y="6"/><use href="#q{ri}{j}" class="ha"/>'
                           f'<use href="#q{ri}{j}" class="xd" stroke="{cord_cols[c]}"/><use href="#q{ri}{j}" class="hl" y="-1"/></g>')
            thread.append(f'<g class="xl">{"".join(grp)}</g>')
    xf = [((0, T_SPILL0 - 0.01), "opacity:0;transform:none"), ((T_SPILL0, T_CATCH), "opacity:1;transform:none"),
          (T_PULL, "opacity:1;transform:" + core_css(0))]
    for k, t in enumerate(pull_times()[1:], 1):
        p = PULL_EASE(k / PULL_K)
        op = 1 - smooth((p - 0.72) / 0.2)
        xf.append((t, f"opacity:{f(op, 2)};transform:" + core_css(p, cinch=(1 - smooth(p / 0.8)) * 0.85 + 0.15)))
    xf.append(((T_PULLEND + 0.01, L), "opacity:0;transform:" + core_css(1, cinch=.15)))
    add(kf("xl", xf))
    add(f".xl{{transform-origin:{C0[0]}px {C0[1]}px;animation:xl 8s linear infinite}}.xd{{fill:none;stroke-width:5.6}}")
    sdx, sdy = spill_from[0] - C0[0], spill_from[1] - C0[1]
    add(kf("sp", [((0, T_SPILL0), f"opacity:0;transform:translate({f(sdx, 0)}px,{f(sdy, 0)}px) scale(.03) rotate(-80deg)"),
                  (T_SPILL0 + 0.05, f"opacity:1;transform:translate({f(sdx * .92, 0)}px,{f(sdy * .92, 0)}px) scale(.08) rotate(-70deg)"),
                  (T_SPILL0 + 0.4, f"opacity:1;transform:translate({f(sdx * .3, 0)}px,{f(sdy * .1, 0)}px) scale(.7) rotate(-14deg)"),
                  (T_SPILL0 + 0.62, "opacity:1;transform:translate(0px,0px) scale(1.04) rotate(3deg)"),
                  ((T_SPILL1, L - 0.32), "opacity:1;transform:none"), ((L - 0.12, L), "opacity:0;transform:none")]))
    add(f".sp{{transform-origin:{C0[0]}px {C0[1]}px;animation:sp 8s ease-out infinite}}")
    still_line = f'<path class="still" d="M{X0} {LY}H{XE}" stroke="{ROLES[0]["color"]}" stroke-width="5.6" stroke-linecap="round" fill="none"/>'
    add(".still{display:none}")
    add(kf("held", [((0, T_CATCH - 0.01), "opacity:0"), ((T_CATCH, T_REL), "opacity:1"), ((T_REL + 0.01, L), "opacity:0")]))
    add(f".held{{opacity:0;animation:held 8s steps(1,end) infinite,cord {f(T)}s linear infinite}}")
    add("@media (prefers-reduced-motion:reduce){*{animation:none!important}"
        ".anim,.kw,.wm,.mo,.tg,.ch,.held,.hp,.hh{display:none}.still{display:inline}.r0{opacity:1}"
        f".bird{{transform:translate({XE}px,{LY}px) rotate({HOLD_A}deg)!important}}}}")

    gt = f"scale({BS}) translate({-GRIP[0]} {-GRIP[1]})"
    defs = (shoga_defs() + "".join(chunk_defs) + "".join(xl_defs) + ty.defs()
            + f'<clipPath id="above"><rect width="{W}" height="{LY - 3}"/></clipPath>'
            + f'<clipPath id="below"><rect y="{LY + 3}" width="{W}" height="{H}"/></clipPath>'
)
    body = "".join([
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        caption,
        "".join(tags),
        '<g class="sp"><g class="jit">',
        f'<g class="anim">{"".join(thread)}</g>{still_line}',
        "".join(word_svg),
        '</g>',
        pin, '</g>',
        "".join(msg_svg),
        f'<g clip-path="url(#above)"><g class="wm">{wm}</g></g>',
        f'<g clip-path="url(#below)"><g class="mo">{motto}</g></g>', tagline,
        f'<g class="bird">{bird_anim}<g transform="{gt}">{shoga("back")}</g></g>',
        f'<use href="#c{nch - 1}" class="cd held"/>',
        f'<path class="still" d="M{XE - 150} {LY}H{XE}" stroke="{ROLES[0]["color"]}" stroke-width="5.6" stroke-linecap="round"/>',
        f'<g class="bird">{bird_anim}<g transform="{gt}">{shoga("front")}</g></g>',
        "".join(f'<g class="r{ri}">{h}</g>' for ri, h in hints),
        '<g class="still">' + ty.b.text("Seedhi baat, no bakwas.", 20, W - 40 - ty.b.width("Seedhi baat, no bakwas.", 20) - 24 - ty.sb.width("Straight talk, no nonsense.", 18), H - 30, extra=f' fill="{GREEN}"')[0]
        + f'<path d="M{f(W - 40 - ty.sb.width("Straight talk, no nonsense.", 18) - 12)} {H - 46}V{H - 26}" stroke="{INK}" stroke-opacity=".25" stroke-width="2" stroke-linecap="round"/>'
        + ty.sb.text("Straight talk, no nonsense.", 18, W - 40, H - 30, anchor="end", extra=' fill="#62786C"')[0] + '</g>',
    ])
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Shoga-Speaks</title>',
        f'<desc id="d">{DESC}</desc>',
        f'<defs>{defs}</defs>',
        f'<style>{re.sub(r"(?<![0-9.])8s", f(L) + "s", "".join(css))}</style>',
        body, '</svg>'])


DESC = ("One Claude Code task, why is the orders page slow, starts as a dense knot of thread covered in technical words. "
        "Shoga, a green parrot, catches the loose end and pulls it into one straight line. The jargon falls into a "
        "Technical tag and a plain two-line story rises from the line, told three times for three readers: a developer "
        "in Roman-Urdu, a QA tester in Dutch and a product owner in English. The tag then opens into a card with the "
        "same details put in order, and one term gets a plain explanation. The line finally becomes the underline of "
        "Shoga-Speaks, where Shoga lands: seedhi baat, no bakwas.")


def social():
    """1280 x 640 still for GitHub's social preview: knot to line, the Dev story, its card opened, plus the install line."""
    ty = new_type()
    W2, H2 = 1280, 640
    r = ROLES[0]
    LYs, XEs = 372, 1222
    k = 0.72
    cxn, cyn = 232, LYs - 6
    knot = make_knot(KNOT_SEED)[0]

    def T_(p):
        return (cxn + (p[0] - C0[0]) * k, cyn + (p[1] - C0[1]) * k)
    cut = int(D * 0.9)
    body = [T_(p) for p in knot[:cut]]
    pin = body[0]
    (ax, ay), (bx, by) = body[-1], body[-4]
    hx, hy = ax - bx, ay - by
    hn = math.hypot(hx, hy) or 1
    tail = [cubic_pt((ax, ay), (ax + hx / hn * 70, ay + hy / hn * 70), (408, LYs), (466, LYs), t / 30) for t in range(1, 31)]
    line = [(466 + (XEs - 466) * t / 40, LYs) for t in range(1, 41)]
    dense, _ = resample(body + tail + line, D)
    chunks = fit(dense, 120, 10)
    cols = []
    for i in range(len(chunks)):
        q = i / (len(chunks) - 1)
        a_, b_ = (0x0B, 0x1E, 0x15), (0x24, 0x42, 0x33)
        cols.append("#%02X%02X%02X" % tuple(round(a_[j] + (b_[j] - a_[j]) * q) for j in range(3)))
    loops = extra_loops(r["loops"])
    gt = f'translate({f(cxn)} {f(cyn)}) scale({k}) translate({-C0[0]} {-C0[1]})'
    defs = [shoga_defs()]
    out = []
    for i, d in enumerate(chunks):
        defs.append(f'<path id="t{i}" d="{d}"/>')
    slots = {2: 0, 4: 1, 6: 2, 8: 3}
    for i in range(len(chunks)):
        col = cols[i] if i < 9 else r["color"]
        out.append(f'<use href="#t{i}" class="sh" x="1" y="5"/><use href="#t{i}" class="ha"/><use href="#t{i}" class="cd" stroke="{col}"/>'
                   + (f'<use href="#t{i}" class="hl" y="-1"/>' if i < 9 else ""))
        if i in slots:
            j = slots[i]
            defs.append(f'<path id="q{j}" vector-effect="non-scaling-stroke" d="{loops[j]}"/>')
            out.append(f'<g transform="{gt}"><use href="#q{j}" class="sh" x="1" y="6"/><use href="#q{j}" class="ha"/>'
                       f'<use href="#q{j}" class="cd" stroke="{cols[i]}"/><use href="#q{j}" class="hl" y="-1"/></g>')
    placed = knot_words(ty, knot, JARGON, 100, size=22)
    words = "".join(f'<use href="#{ty.mono.gid(n)}" transform="translate({round(x)} {round(y)})rotate({round(a)})scale({f(gs, 3)})" x="{round(-ty.mono.adv(n) / 2)}"/>'
                    for _, glyphs, _, _, _ in placed for n, x, y, a, gs in glyphs if ty.mono.gid(n) not in ty.mono.empty)
    out.append(f'<g transform="{gt}" fill="#9A3B1E" stroke="{PAPER}" stroke-width="20" stroke-linejoin="round" paint-order="stroke">{words}</g>')
    thread = "".join(out)
    # the story on the straight part, its card under it
    mx, ms = 486, 26
    msg = (ty.b.text(r["say"][0], ms, mx, LYs - 14 - ms * 1.24, extra=f' fill="{INK}"')[0]
           + ty.b.text(r["say"][1], ms, mx, LYs - 14, extra=f' fill="{INK}"')[0])
    term_w = ty.b.width("N+1", ms)
    yb0 = LYs - 14 - ms * 1.24
    hl = (f'<rect x="{mx - 4}" y="{f(yb0 - ms * 0.8)}" width="{f(term_w + 8)}" height="{f(ms * 1.02)}" rx="5" fill="#FFD166" opacity=".34"/>'
          f'<path d="M{mx} {f(yb0 + ms * 0.17)}H{f(mx + term_w)}" stroke="#F2B705" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0 5"/>')
    cs, clh = 15, 21
    cwid = max(ty.mono.width(t, cs) for t in r["card"]) + 32
    chei = 32 + clh * 3 + 12
    cx0, cy0 = mx + 16, LYs + 22
    card = (f'<path d="M{cx0 + 14} {LYs + 2}V{cy0}" stroke="{INK}" stroke-opacity=".55" stroke-width="1.6"/>'
            f'<g transform="translate({cx0} {cy0})"><rect x="1" y="3" width="{f(cwid)}" height="{chei}" rx="10" fill="{INK}" opacity=".08"/>'
            f'<rect width="{f(cwid)}" height="{chei}" rx="10" fill="#fff" stroke="{INK}" stroke-opacity=".28" stroke-width="1.5"/>'
            f'<circle cx="14" cy="0" r="3.2" fill="#fff" stroke="{INK}" stroke-opacity=".5" stroke-width="1.5"/>'
            + ty.mono.text("▾ Technical", cs, 15, 21.5, extra=' fill="#4F6359"')[0]
            + f'<path d="M14 32H{f(cwid - 14)}" stroke="{INK}" stroke-opacity=".1" stroke-width="1.5"/>'
            + "".join(ty.mono.text(t, cs, 16, 32 + clh * (i + 1) - 2, extra=' fill="#2E4238"')[0] for i, t in enumerate(r["card"])) + '</g>')
    pinsvg = (f'<circle cx="{f(pin[0] + 1)}" cy="{f(pin[1] + 3)}" r="7.5" fill="{INK}" opacity=".12"/>'
              f'<circle cx="{f(pin[0])}" cy="{f(pin[1])}" r="7" fill="{INK}"/>')
    rot = f'translate({XEs} {LYs}) rotate({HOLD_A})'
    bird = (f'<g transform="{rot}"><g transform="scale({BS}) translate({-GRIP[0]} {-GRIP[1]})">{shoga("back")}</g></g>'
            f'<path d="M{XEs - 160} {LYs}H{XEs}" stroke="{r["color"]}" stroke-width="5.6" stroke-linecap="round"/>'
            f'<g transform="{rot}"><g transform="scale({BS}) translate({-GRIP[0]} {-GRIP[1]})">{shoga("front")}</g></g>')
    # header: prompt, wordmark and promise
    wm = ty.xb.text("Shoga-Speaks", 60, 84, 112, tracking=-0.02, extra=f' fill="{INK}"')[0]
    m1, mw1 = ty.b.text("Seedhi baat, no bakwas.", 25, 86, 154, extra=f' fill="{GREEN}"')
    m2 = ty.sb.text("Straight talk, no nonsense.", 22, 86 + mw1 + 30, 154, extra=' fill="#62786C"')[0]
    motto = m1 + f'<path d="M{f(86 + mw1 + 15)} {134}V{159}" stroke="{INK}" stroke-opacity=".25" stroke-width="2" stroke-linecap="round"/>' + m2
    t1 = ty.b.text("Claude Code explains what it did", 23, 1196, 96, anchor="end", extra=' fill="#3E5A4B"')[0]
    t2 = ty.b.text("in your language, for your role.", 23, 1196, 127, anchor="end", extra=' fill="#3E5A4B"')[0]
    qsz = 24
    capw = ty.mono.width("› " + PROMPT, qsz)
    cap_y = 236
    qx = mx - 6
    caption = (ty.sb.text("YOU ASKED", 13, qx + 2, cap_y - 32, tracking=0.1, extra=' fill="#5F766A"')[0]
               + f'<rect x="{qx}" y="{cap_y - 4 - 22}" width="{f(capw + 36)}" height="46" rx="11" fill="{INK}"/>'
               + ty.mono.text("›", qsz, qx + 18, cap_y + 5, extra=' fill="#5BD46E"')[0]
               + ty.mono.text(PROMPT, qsz, qx + 18 + ty.mono.width("› ", qsz), cap_y + 5, extra=' fill="#EAF8EF"')[0])
    bw = ty.xb.width(r["role"], 15) + 24
    bxx = qx + capw + 36 + 14
    badge = (f'<rect x="{f(bxx)}" y="{cap_y - 17}" width="{f(bw)}" height="28" rx="14" fill="{r["color"]}"/>'
             + ty.xb.text(r["role"], 15, bxx + bw / 2, cap_y + 2.5, anchor="middle", extra=' fill="#fff"')[0]
             + ty.sb.text(r["lang"], 17, bxx + bw + 10, cap_y + 3, extra=' fill="#5F766A"')[0])
    # install line
    cmd = "/plugin marketplace add Mir-Zairan/shoga-speaks"
    lab = "Install in Claude Code"
    lw = ty.sb.width(lab, 20)
    cw = ty.mono.width(cmd, 22)
    total = lw + 22 + cw + 44
    x0 = (W2 - total) / 2
    yb = 590
    install = (ty.sb.text(lab, 20, x0, yb + 7, extra=' fill="#5F766A"')[0]
               + f'<rect x="{f(x0 + lw + 22)}" y="{yb - 22}" width="{f(cw + 44)}" height="44" rx="12" fill="#fff" stroke="{INK}" stroke-opacity=".8" stroke-width="2"/>'
               + ty.mono.text(cmd, 22, x0 + lw + 44, yb + 8, extra=f' fill="{INK}"')[0])
    css = (f".sh{{fill:none;stroke:{INK};stroke-width:7;opacity:.16}}.ha{{fill:none;stroke:{PAPER};stroke-width:11}}"
           ".cd{fill:none;stroke-width:5.6;stroke-linecap:round}.hl{fill:none;stroke:#fff;stroke-width:1.4;opacity:.2}"
           ".wn{transform:rotate(-140deg)}.wf{transform:rotate(-128deg)}.lid,.pp{display:none}.joy{opacity:0}.pu{transform:translate(-5px,-1px)}")
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H2}" width="{W2}" height="{H2}">',
        f'<defs>{"".join(defs)}{ty.defs()}</defs>',
        f'<style>{css}</style>',
        f'<rect width="{W2}" height="{H2}" fill="{PAPER}"/>',
        wm, motto, t1, t2, caption, badge, card, thread, pinsvg, hl, msg, bird, install, '</svg>'])


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
    svg = banner()
    with open(os.path.join(OUT, "banner.svg"), "w") as fh:
        fh.write(svg)
    print(f"banner.svg: {len(svg.encode()) / 1024:.1f} KB")
    if "--png" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "social.svg")
            with open(src, "w") as fh:
                fh.write(social())
            out = os.path.join(OUT, "social-preview.png")
            render_png(src, out, 1280, 640)
            print(f"social-preview.png: {os.path.getsize(out) / 1024:.0f} KB")
