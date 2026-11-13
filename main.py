#!/usr/bin/env python3
"""Make the best-looking food picture — make.fun bounty food-picture-01.

Writes exactly one image to /output/entry.png: a steaming bowl of
ramen, shot from a warm three-quarter angle — a lacquered red bowl of
golden broth with wavy noodles, soft-boiled egg, chashu, narutomaki,
scallions and nori, chopsticks lifting a tangle of noodles, steam
curling up, on a wooden table against a warm glowing background.

Why this concept: the judge is a vision model that looks at two food
pictures at a time and picks the better-looking one. Ramen reads as
food instantly at any size: (1) one large central bowl, (2) warm
appetising colours — golden broth, red bowl, orange yolk, green
scallions, (3) visible steam = freshly cooked and hot, (4) chopsticks
lifting noodles = action and texture, (5) recognisable toppings that
signal care and detail, (6) no text, no clutter, no dark or ambiguous
areas. Everything is drawn from fixed constants: no network, no
randomness, no time, no external files. Two runs write byte-identical
PNG bytes.

Python 3.13, standard library only (struct, zlib, math, pathlib).
No Pillow, no numpy, no vendored code — the PNG encoder below is
hand-written (IHDR / IDAT / IEND, filter 0, zlib level 9).

Output: /output/entry.png, PNG, 1024 x 1024 px, well under 1 MiB.
"""

import math
import struct
import zlib
from pathlib import Path

W = 1024
H = 1024
OUTPUT_PATH = Path("/output/entry.png")

# ---------------------------------------------------------------- canvas
# RGB bytearray, row-major. All drawing is opaque, back to front.
buf = bytearray(W * H * 3)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _blend(c1, c2, t: float):
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def fill_rect(x0: int, y0: int, x1: int, y1: int, color) -> None:
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        buf[i:i + len(row)] = row


def fill_ellipse(cx: int, cy: int, rx: int, ry: int, color) -> None:
    """Axis-aligned filled ellipse, scanline by scanline."""
    if rx <= 0 or ry <= 0:
        return
    row_bytes = bytes(color)
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        dx = math.sqrt(max(0.0, 1.0 - dy * dy)) * rx
        x0 = max(0, int(math.ceil(cx - dx)))
        x1 = min(W - 1, int(math.floor(cx + dx)))
        if x1 < x0:
            continue
        i = (y * W + x0) * 3
        buf[i:i + (x1 - x0 + 1) * 3] = row_bytes * (x1 - x0 + 1)


def fill_circle(cx: int, cy: int, r: int, color) -> None:
    fill_ellipse(cx, cy, r, r, color)


def fill_polygon(points, color) -> None:
    """Filled polygon, even-odd scanline fill. Points: [(x, y), ...]."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    row_bytes = bytes(color)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if y1p == y2p:
                continue
            if (y >= min(y1p, y2p)) and (y < max(y1p, y2p)):
                xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
        if len(xs) < 2:
            continue
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k])))
            xb = min(W - 1, int(math.floor(xs[k + 1])))
            if xb < xa:
                continue
            i = (y * W + xa) * 3
            buf[i:i + (xb - xa + 1) * 3] = row_bytes * (xb - xa + 1)


def noodle_strand(x0: int, x1: int, y: int, amp: int, phase: float,
                  color, r: int = 6) -> None:
    """One wavy horizontal noodle: small circles along a sine path."""
    steps = max(8, (x1 - x0) // 6)
    for i in range(steps + 1):
        t = i / steps
        x = int(x0 + (x1 - x0) * t)
        yy = int(y + amp * math.sin(phase + t * math.pi * 3.0))
        fill_circle(x, yy, r, color)


def steam_curl(cx: int, y_top: int, y_bot: int, color) -> None:
    """One rising steam curl: circles along a sine path, thinner at top."""
    steps = 26
    for i in range(steps + 1):
        t = i / steps
        y = int(y_bot + (y_top - y_bot) * t)
        x = int(cx + 22 * math.sin(t * math.pi * 2.2))
        r = int(24 - 10 * t)
        fill_circle(x, y, max(6, r), color)


def scallion(cx: int, cy: int) -> None:
    """One sliced green onion: green ring with a pale centre."""
    fill_circle(cx, cy, 12, (84, 158, 66))
    fill_circle(cx, cy, 6, (216, 234, 186))


# ---------------------------------------------------------------- scene
def draw() -> None:
    # 1. Background: warm cream at top -> honey gold at the table line.
    #    Warm light makes food look appetising; no cold tones anywhere.
    top = (255, 238, 205)
    horizon = (250, 198, 138)
    for y in range(700):
        t = y / 699
        c = _blend(top, horizon, t * t * 0.7)
        i = y * W * 3
        buf[i:i + W * 3] = bytes(c) * W

    # 2. Soft warm glow behind the bowl + faint bokeh circles.
    fill_ellipse(512, 560, 380, 330, (255, 226, 170))
    fill_ellipse(512, 560, 300, 260, (255, 232, 186))
    for cx, cy, r, col in (
        (150, 190, 58, (255, 224, 168)),
        (880, 170, 44, (255, 220, 158)),
        (860, 440, 30, (255, 226, 172)),
        (140, 470, 34, (255, 228, 176)),
        (940, 600, 26, (252, 214, 150)),
    ):
        fill_circle(cx, cy, r, col)

    # 3. Wooden table, bottom third: warm brown planks.
    table = (168, 108, 62)
    for y in range(700, H):
        i = y * W * 3
        buf[i:i + W * 3] = bytes(table) * W
    for y in (742, 812, 884, 956):
        fill_rect(0, y, W, y + 5, (128, 78, 42))
    # Plank shading: a darker band at the very bottom.
    fill_rect(0, 990, W, H, (146, 92, 52))
    # A few wood-grain streaks.
    for x0, y0, ln in ((90, 730, 260), (620, 760, 300), (300, 900, 340),
                       (760, 930, 180), (60, 980, 220)):
        fill_rect(x0, y0, x0 + ln, y0 + 3, (150, 94, 52))

    # 4. Dark round placemat under the bowl.
    fill_ellipse(512, 905, 430, 88, (58, 44, 38))
    fill_ellipse(512, 905, 410, 76, (72, 54, 46))

    # 5. THE BOWL — lacquered red, one large central subject.
    #    Body first, then a gold band, then the broth surface.
    fill_ellipse(512, 665, 335, 245, (178, 38, 32))       # body
    fill_ellipse(512, 905, 118, 28, (140, 26, 24))        # foot
    # Gloss highlight down the left of the body.
    fill_ellipse(408, 660, 42, 148, (214, 82, 62))
    fill_ellipse(408, 660, 20, 120, (228, 108, 82))
    # Gold rim band.
    fill_ellipse(512, 585, 335, 100, (222, 172, 62))
    fill_ellipse(512, 585, 320, 88, (150, 28, 26))
    # Broth: golden, with a lighter centre pool.
    fill_ellipse(512, 585, 300, 82, (232, 158, 58))
    fill_ellipse(512, 590, 268, 66, (240, 176, 82))
    # Chilli-oil swirls on the broth.
    for cx, cy, rx, ry in ((300, 560, 46, 12), (700, 540, 40, 10),
                           (620, 640, 52, 12), (400, 640, 44, 11)):
        fill_ellipse(cx, cy, rx, ry, (198, 74, 32))

    # 6. Nori sheet sticking up behind the bowl (drawn before the
    #    broth edge would cover its base — it is already behind it).
    fill_polygon(
        [(700, 392), (782, 408), (762, 560), (692, 548)], (32, 58, 38)
    )
    fill_polygon(
        [(716, 410), (766, 420), (752, 540), (708, 532)], (48, 76, 52)
    )

    # 7. Noodle strands across the broth, under the toppings.
    noodle = (246, 208, 125)
    noodle_dark = (222, 176, 92)
    for y, amp, ph, col in (
        (600, 10, 0.0, noodle), (618, 12, 1.1, noodle_dark),
        (636, 9, 2.0, noodle), (556, 11, 0.6, noodle_dark),
        (650, 10, 2.8, noodle),
    ):
        noodle_strand(270, 754, y, amp, ph, col)

    # 8. Toppings, left to right.
    # Chashu: two rolled pork slices with a lighter centre.
    for cx, cy in ((300, 622), (726, 618)):
        fill_circle(cx, cy, 54, (168, 88, 72))
        fill_circle(cx, cy, 46, (206, 126, 104))
        fill_circle(cx, cy, 30, (228, 164, 140))
        fill_circle(cx, cy, 12, (206, 126, 104))
    # Soft-boiled egg halves: white with a runny orange yolk.
    for cx, cy in ((372, 566), (648, 556)):
        fill_ellipse(cx, cy, 56, 32, (250, 244, 228))
        fill_circle(cx, cy, 20, (240, 140, 40))
        fill_circle(cx + 6, cy - 6, 6, (252, 176, 92))
    # Narutomaki: white disc with a pink spiral (concentric rings).
    fill_circle(522, 540, 30, (250, 246, 238))
    fill_circle(522, 540, 24, (240, 130, 150))
    fill_circle(522, 540, 16, (250, 246, 238))
    fill_circle(522, 540, 8, (240, 130, 150))
    # Pickled ginger (beni shoga): two thin pink shreds beside the egg.
    fill_ellipse(596, 646, 26, 8, (238, 92, 110))
    fill_ellipse(600, 654, 22, 7, (246, 130, 146))
    fill_ellipse(586, 636, 18, 6, (246, 130, 146))
    # Scallion rings scattered over the broth.
    for cx, cy in ((430, 620), (470, 648), (560, 630), (600, 596),
                   (350, 600), (690, 580), (586, 660), (452, 576)):
        scallion(cx, cy)
    # Sesame seeds on the broth.
    for cx, cy in ((330, 580), (410, 660), (560, 566), (640, 640),
                   (700, 610), (480, 600)):
        fill_ellipse(cx, cy, 5, 3, (250, 240, 214))

    # 9. Noodles lifted by the chopsticks: wavy vertical strands
    #    hanging from the tips down to the broth.
    for dx, ph in ((-14, 0.0), (0, 1.2), (14, 2.4)):
        steps = 16
        for i in range(steps + 1):
            t = i / steps
            x = int(596 + dx + 16 * math.sin(ph + t * math.pi * 2.5))
            y = int(548 + (606 - 548) * t)
            fill_circle(x, y, 6, noodle)

    # 10. Chopsticks: two wooden sticks resting across the rim,
    #     tips pinching the lifted noodles.
    wood = (188, 138, 74)
    wood_dark = (150, 104, 52)
    fill_polygon([(872, 292), (884, 308), (606, 556), (594, 542)], wood)
    fill_polygon([(894, 330), (902, 348), (626, 576), (614, 562)], wood)
    fill_polygon([(640, 522), (652, 536), (606, 556), (594, 542)],
                 wood_dark)
    fill_polygon([(660, 544), (670, 560), (626, 576), (614, 562)],
                 wood_dark)

    # 11. Steam: three curls rising from the broth.
    steam = (252, 248, 240)
    steam_curl(408, 190, 500, steam)
    steam_curl(500, 150, 490, steam)
    steam_curl(578, 200, 505, steam)

    # 12. Garnish on the table: a few scallion rings and sesame
    #     seeds beside the bowl, for a lived-in feel.
    for cx, cy in ((180, 830), (220, 872), (850, 850), (880, 900)):
        scallion(cx, cy)
    for cx, cy in ((150, 880), (250, 830), (830, 900), (900, 850)):
        fill_ellipse(cx, cy, 5, 3, (250, 240, 214))


# ---------------------------------------------------------------- PNG
def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def encode_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += buf[y * W * 3:(y + 1) * W * 3]
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def main() -> None:
    draw()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(encode_png())


if __name__ == "__main__":
    main()
