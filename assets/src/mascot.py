"""Shoga, the Shoga-Speaks parakeet: geometry and the coloured mark.

Shared by build.py (the logo) and banner.py (the banner and social preview).
All shapes live in one space: about 18..342 x 40..556, facing right, feet at
about (170, 414). The silhouette (head, body, long tail, hooked beak, feet)
is one mask with a few gaps cut in (beak, mouth, tail split); the colour sits
inside it: an emerald-to-lime body, teal-blue tail, coral beak, rose-and-black
neck ring, a white eye and one sheen on the head. No outline, so it stays
crisp from 16 px up and on light and dark.
"""

HEAD = "M190 40C246 40 290 84 290 138C290 192 246 232 190 232C134 232 92 192 92 138C92 84 134 40 190 40Z"
BODY = "M170 150C242 150 272 220 270 282C268 346 226 392 170 392C112 392 72 346 72 282C72 216 104 150 170 150Z"
# a long, tapered tail: two pointed feathers swept down-left
TAIL = ("M104 312C88 384 58 446 18 498C56 488 84 468 102 444"
        "C98 482 86 518 66 556C112 516 142 446 158 340Z")
BEAK_UP = "M266 104C300 92 340 112 342 150C344 176 332 196 314 206C318 188 314 174 302 168C294 164 284 164 276 168Z"
BEAK_LO = "M276 168C288 166 302 172 306 186C300 198 286 202 272 194Z"
FEET = ("M136 380C134 398 128 408 118 414C130 420 148 414 156 400Z"
        "M182 382C182 400 178 410 168 416C180 422 198 416 204 402Z")
RING = "M284 194C258 238 188 250 112 210"          # the neck ring
TAIL_SPLIT = "M98 462C106 436 114 412 120 392"    # gaps cut out of the silhouette
BEAK_GAP = "M268 100C258 124 262 150 278 170"
MOUTH = "M278 172C290 166 302 170 308 180"
EYE = (224, 122)
FEET_AT = (170, 414)                              # where Shoga stands
# the spread wing for flight, root at (0, 0), pointing up; placed at WROOT
FLY = ("M-6 14C34 -30 62 -112 46 -214C30 -200 16 -192 2 -190C6 -176 2 -166 -6 -160C-18 -160 -28 -152 -32 -142"
       "C-28 -130 -32 -120 -40 -114C-50 -112 -58 -104 -60 -94C-56 -82 -58 -72 -66 -66C-70 -36 -50 -6 -6 14Z")
WROOT = (150, 214)

INKC = "#10231A"


def mark(uid, feet=True, fly=False, eye_cls="", wing_cls=""):
    """(defs, art) of Shoga, perched (wing folded) or in flight (fly: the spread wing,
    class wing_cls, turns about the shoulder). uid keeps gradient and mask ids
    unique; eye_cls goes on the eyelid, for blinking."""
    ex, ey = EYE
    k = 'stroke="#000" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    sil = f'<path d="{HEAD}"/><path d="{BODY}"/><path d="{TAIL}"/><path d="{BEAK_UP}"/><path d="{BEAK_LO}"/>' + (f'<path d="{FEET}"/>' if feet else "")
    d = (f'<linearGradient id="{uid}g" gradientUnits="userSpaceOnUse" x1="300" y1="50" x2="90" y2="400">'
         '<stop offset="0" stop-color="#8EDB5A"/><stop offset=".42" stop-color="#34B866"/><stop offset="1" stop-color="#0C8A57"/></linearGradient>'
         f'<linearGradient id="{uid}t" gradientUnits="userSpaceOnUse" x1="150" y1="330" x2="40" y2="550">'
         '<stop offset="0" stop-color="#16A08A"/><stop offset="1" stop-color="#2F68B4"/></linearGradient>'
         f'<linearGradient id="{uid}w" gradientUnits="userSpaceOnUse" x1="180" y1="240" x2="110" y2="390">'
         '<stop offset="0" stop-color="#1E9A57"/><stop offset="1" stop-color="#0B6B45"/></linearGradient>'
         f'<linearGradient id="{uid}b" gradientUnits="userSpaceOnUse" x1="300" y1="96" x2="330" y2="210">'
         '<stop offset="0" stop-color="#FF7A66"/><stop offset="1" stop-color="#E2434A"/></linearGradient>'
         f'<mask id="{uid}m" maskUnits="userSpaceOnUse" x="-60" y="-260" width="480" height="860">'
         f'<g fill="#fff">{sil}</g><g {k}><path d="{BEAK_GAP}" stroke-width="11"/><path d="{MOUTH}" stroke-width="8"/>'
         f'<path d="{TAIL_SPLIT}" stroke-width="7"/></g></mask>')
    art = (f'<g mask="url(#{uid}m)">'
           f'<path d="{TAIL}" fill="url(#{uid}t)"/>'
           f'<path d="{BODY}" fill="url(#{uid}g)"/><path d="{HEAD}" fill="url(#{uid}g)"/>'
           + (f'<path d="{FEET}" fill="#7F8C86"/>' if feet else "")
           + ("" if fly else f'<path d="M100 240C134 222 176 238 190 276C202 312 194 352 164 384C140 366 112 352 96 326C82 300 84 262 100 240Z" fill="url(#{uid}w)"/>')
           + ("" if fly else '<path d="M104 244C134 230 170 242 184 274C196 302 192 336 172 366" stroke="#7FDB8F" stroke-opacity=".45" stroke-width="5" fill="none" stroke-linecap="round"/>')
           + f'<path d="{RING}" stroke="{INKC}" stroke-width="10" fill="none" stroke-linecap="round"/>'
           f'<path d="{RING}" transform="translate(-3 11)" stroke="#F493B6" stroke-width="9" fill="none" stroke-linecap="round"/>'
           f'<path d="{BEAK_UP}" fill="url(#{uid}b)"/><path d="{BEAK_LO}" fill="#B9343C"/>'
           '<path d="M120 100C132 74 158 58 190 54" stroke="#fff" stroke-opacity=".38" stroke-width="13" fill="none" stroke-linecap="round"/>'
           '</g>'
           f'<circle cx="{ex}" cy="{ey}" r="28" fill="#fff"/>'
           f'<circle cx="{ex}" cy="{ey}" r="28" fill="none" stroke="#F2A541" stroke-width="4"/>'
           f'<circle cx="{ex + 6}" cy="{ey + 3}" r="15" fill="{INKC}"/><circle cx="{ex + 11}" cy="{ey - 4}" r="5" fill="#fff"/>'
           + (f'<ellipse class="{eye_cls}" cx="{ex}" cy="{ey}" rx="31" ry="31" fill="url(#{uid}g)"/>' if eye_cls else ""))
    if fly:
        art += (f'<g transform="translate({WROOT[0]} {WROOT[1]})"><g class="{wing_cls}">'
                f'<linearGradient id="{uid}f" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="40" y2="-210">'
                '<stop offset="0" stop-color="#159A5C"/><stop offset="1" stop-color="#1D8C9A"/></linearGradient>'
                f'<path d="{FLY}" fill="url(#{uid}f)"/>'
                '<path d="M-6 -20C10 -70 18 -120 16 -170M-30 -40C-20 -80 -16 -110 -18 -140" stroke="#0A5E3C" stroke-opacity=".55" stroke-width="7" fill="none" stroke-linecap="round"/>'
                '</g></g>')
    return d, art
