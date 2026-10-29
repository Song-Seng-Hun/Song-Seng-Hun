#!/usr/bin/env python3
"""Draw the animated pixel-art world map used in README.md.

Run from anywhere:
    python3 tools/build_worldmap.py
It writes assets/worldmap-dark.svg and assets/worldmap-light.svg.

Everything is drawn on a 240x100 grid (4 px per cell) and animated with SMIL,
which GitHub plays inside README images (scripts are stripped there).
"""

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

P = 4                 # px per grid cell
W, H = 240, 100       # grid size
T = 26.0              # loop length in seconds
DT = 1 / 16           # timeline step in seconds
FADE = T - 0.75       # everything resets from here

# ---------------------------------------------------------------- palettes

COMMON = {
    "skin": "#F1C9A5", "hair": "#3B2A22", "glass": "#1A1A2A",
    "coat": "#4A6FA5", "coat_d": "#38598A", "pants": "#2E3A55", "scarf": "#E8C468",
    "orange": "#D97757", "yellow": "#E3B341", "teal": "#4FA3A5",
    "green": "#6DBE73", "blue": "#5E8FD6", "red": "#E5566B",
    "dia": "#D8F3FF", "dia_d": "#8CC8E8", "nv": "#FF5A6E", "laser": "#6CFF8A",
    "white": "#F7F5EE",
    "codex": "#6E9BF5", "codex_d": "#4C72D9", "screen": "#17203B", "glyph": "#9FE3FF",
    "gem_b": "#4F8CF7", "gem_r": "#EA5A4F", "gem_y": "#F5C443", "gem_g": "#41B96A", "gem_c": "#E9F0FF",
}

PALETTES = {
    "dark": {
        **COMMON,
        "K": "#0B0E1C", "frame": "#B89B5E", "frame_d": "#5E4C2C", "panel": "#141A36",
        "sky0": "#0C1026", "sky1": "#111735", "sky2": "#171F45", "sky3": "#1D2855", "sky4": "#253366",
        "star": "#F4EBD9", "star_d": "#7F88B5", "moon": "#F1E7C9", "moon_d": "#C9BE9C",
        "cloud": "#2A3566", "cloud_d": "#222C58",
        "mtn_far": "#1A2350", "mtn_near": "#182D3E", "mtn_h": "#2B3A70",
        "g0": "#1F3B35", "g1": "#264840", "g2": "#19312C", "tuft": "#2F5A4D",
        "path": "#5C4B3F", "path_e": "#3F332B", "path_h": "#6E5A4B",
        "wall": "#8B8FA8", "wall_m": "#6C7192", "wall_d": "#4C5172",
        "roof": "#7B4A57", "roof_d": "#5A3442", "wood": "#6B4E3A", "wood_d": "#4A3527",
        "metal": "#9AA3B5", "metal_d": "#5F6880", "win": "#262E4D",
        "lit": "#FFD27A", "glow": ("#FFB85C", 0.32), "nv_glow": ("#FF5A6E", 0.35),
        "laser_glow": ("#6CFF8A", 0.3),
        "leaf": "#2C5A47", "leaf_d": "#20443A", "leaf_h": "#3A7059", "trunk": "#4A3527",
        "flower1": "#E8A0B4", "flower2": "#E8D27A", "rock": "#4E5A62",
        "text": "#F4EBD9", "sub": "#8E96C2", "shadow": "#0B0E1C",
        "fog": ("#AEB8DA", 0.34), "fog2": ("#C9D0EA", 0.24), "smoke": ("#9AA3B5", 0.7),
    },
    "light": {
        **COMMON,
        "K": "#2B2F45", "frame": "#C9A86A", "frame_d": "#8A6E3E", "panel": "#FFFDF6",
        "sky0": "#B9D8EA", "sky1": "#C6E0EE", "sky2": "#D2E7F0", "sky3": "#DDEDF1", "sky4": "#E8F2EF",
        "star": "#FFFFFF", "star_d": "#FFFFFF", "moon": "#FFF3C4", "moon_d": "#FFDF85",
        "cloud": "#FFFFFF", "cloud_d": "#E3ECF2",
        "mtn_far": "#A9C2D4", "mtn_near": "#98BAB5", "mtn_h": "#C4D6E2",
        "g0": "#B4CE98", "g1": "#C1D8A6", "g2": "#A2BE87", "tuft": "#8CB072",
        "path": "#E2D2AE", "path_e": "#C9B48C", "path_h": "#EEE2C6",
        "wall": "#F2EEE6", "wall_m": "#DAD3C6", "wall_d": "#B9B0A1",
        "roof": "#C97E6C", "roof_d": "#A8655A", "wood": "#A47C5B", "wood_d": "#86624A",
        "metal": "#C6CDD6", "metal_d": "#8E97A6", "win": "#7F95AA",
        "lit": "#FFE08A", "glow": ("#FFC94A", 0.38), "nv_glow": ("#FF5A6E", 0.32),
        "laser_glow": ("#3ED46A", 0.3),
        "leaf": "#6E9F5E", "leaf_d": "#557F4A", "leaf_h": "#8CBB76", "trunk": "#7A5A40",
        "flower1": "#E07A98", "flower2": "#F2C94C", "rock": "#9AA4A0",
        "text": "#2B2F45", "sub": "#6A7192", "shadow": "#F7F3E8",
        "fog": ("#FFFFFF", 0.6), "fog2": ("#FFFFFF", 0.42), "smoke": ("#8E97A6", 0.55),
    },
}

# sprite characters -> palette keys
CHARS = {
    "K": "K", "h": "hair", "f": "skin", "G": "glass", "c": "coat", "C": "coat_d",
    "n": "pants", "s": "scarf", "o": "orange", "w": "white", "t": "teal",
    "d": "dia", "D": "dia_d", "y": "yellow", "m": "metal", "M": "metal_d",
    "l": "lit", "r": "red", "g": "green", "b": "blue", "x": "text", "u": "sub",
    "B": "codex", "Q": "codex_d", "S": "screen", "W": "wood_d", "v": "wood",
}

# ---------------------------------------------------------------- canvas


class Canvas:
    def __init__(self):
        self.px = {}

    def set(self, x, y, col):
        self.px[(x, y)] = col

    def rect(self, x, y, w, h, col):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.px[(i, j)] = col

    def box(self, x, y, w, h, fill, edge="K"):
        self.rect(x, y, w, h, edge)
        if w > 2 and h > 2:
            self.rect(x + 1, y + 1, w - 2, h - 2, fill)

    def sprite(self, rows, x, y):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px[(x + i, y + j)] = CHARS[ch]

    def merge(self, other):
        self.px.update(other.px)


def outlined(c, col="K"):
    out = Canvas()
    for (x, y) in c.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in c.px:
                out.px[(x + dx, y + dy)] = col
    out.px.update(c.px)
    return out


def rects(cells):
    """Cover a set of cells with few rectangles (row runs merged downwards)."""
    rows = {}
    for x, y in cells:
        rows.setdefault(y, []).append(x)
    out, open_ = [], {}
    for y in sorted(rows):
        xs = sorted(rows[y])
        runs, start, prev = [], xs[0], xs[0]
        for x in xs[1:]:
            if x != prev + 1:
                runs.append((start, prev - start + 1))
                start = x
            prev = x
        runs.append((start, prev - start + 1))
        nxt = {}
        for key in runs:
            if key in open_ and sum(open_[key]) == y:
                y0, h = open_.pop(key)
                nxt[key] = (y0, h + 1)
            else:
                nxt[key] = (y, 1)
        out += [(k[0], y0, k[1], h) for k, (y0, h) in open_.items()]
        open_ = nxt
    out += [(k[0], y0, k[1], h) for k, (y0, h) in open_.items()]
    return out


def svg_paths(c, pal, unit=P, ox=0, oy=0):
    by_col = {}
    for xy, col in c.px.items():
        by_col.setdefault(col, set()).add(xy)
    out = []
    for col in sorted(by_col):
        d = "".join(f"M{x*unit+ox} {y*unit+oy}h{w*unit}v{h*unit}h{-w*unit}z"
                    for x, y, w, h in sorted(rects(by_col[col]), key=lambda r: (r[1], r[0])))
        fill = pal[col]
        if isinstance(fill, tuple):
            out.append(f'<path fill="{fill[0]}" fill-opacity="{fill[1]}" d="{d}"/>')
        else:
            out.append(f'<path fill="{fill}" d="{d}"/>')
    return "".join(out)

# ---------------------------------------------------------------- font (5x7)


FONT_SRC = """
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I ### .#. .#. .#. .#. .#. ###
J ..### ...#. ...#. ...#. ...#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# #...# ##..# #.#.# #..## #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 .#. ##. .#. .#. .#. .#. ###
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ####. ....# ....# .###. ....# ....# ####.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 .###. #.... #.... ####. #...# #...# .###.
. . . . . . . #
! # # # # # . #
? .###. #...# ....# ...#. ..#.. ..... ..#..
- ... ... ... ### ... ... ...
"""

FONT = {" ": ["..."] * 7}
for line in FONT_SRC.strip().splitlines():
    ch, *rows = line.split()
    FONT[ch] = rows


def text_width(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1


def draw_text(c, s, x, y, col, shadow="shadow"):
    for pass_col, dy in ((shadow, 1), (col, 0)):
        if pass_col is None:
            continue
        cx = x
        for ch in s:
            for j, row in enumerate(FONT[ch]):
                for i, v in enumerate(row):
                    if v == "#":
                        c.set(cx + i, y + j + dy, pass_col)
            cx += len(FONT[ch][0]) + 1
    return x + text_width(s)

# ---------------------------------------------------------------- sprites


TRAVELER = {
    "idle": [
        "..hhhhh..",
        ".hhhhhhh.",
        ".hhffffh.",
        ".fGGfGGf.",
        ".fffffff.",
        "..fffff..",
        "..sssss..",
        ".ccsccCc.",
        "fcccccCcf",
        ".ccccccC.",
        "..nn.nn..",
        "..nn.nn..",
        "..KK.KK..",
    ],
    "step": [
        "..hhhhh..",
        ".hhhhhhh.",
        ".hhffffh.",
        ".fGGfGGf.",
        ".fffffff.",
        "..fffff..",
        "..sssss..",
        ".ccsccCc.",
        "fcccccCcf",
        ".ccccccC.",
        "..nn.nn..",
        ".nn...nn.",
        ".KK...KK.",
    ],
}

# Claude is assembled from parts: (col, row) offsets from the body's top-left,
# body = cols 1-11 x rows 0-7, arms beside it, legs on rows 8-9.
CLAUDE_EYES = {
    "happy": [(2, 2), (3, 3), (2, 4), (10, 2), (9, 3), (10, 4)],   # > <
    "dot": [(3, 2), (3, 3), (9, 2), (9, 3)],
    "blink": [(2, 3), (3, 3), (9, 3), (10, 3)],
    "left": [(2, 2), (2, 3), (8, 2), (8, 3)],
    "right": [(4, 2), (4, 3), (10, 2), (10, 3)],
    "wow": [(2, 2), (3, 2), (2, 3), (3, 3), (9, 2), (10, 2), (9, 3), (10, 3)],
}
_ARM_L, _ARM_R = [(0, 3), (0, 4), (0, 5)], [(12, 3), (12, 4), (12, 5)]
_UP_L, _UP_R = [(0, -2), (0, -1), (0, 0)], [(12, -2), (12, -1), (12, 0)]
CLAUDE_ARMS = {
    "down": _ARM_L + _ARM_R,
    "up": _UP_L + _UP_R,
    "swingA": [(0, 2), (0, 3), (0, 4), (12, 4), (12, 5), (12, 6)],
    "swingB": [(0, 4), (0, 5), (0, 6), (12, 2), (12, 3), (12, 4)],
    "wave1": _UP_L + _ARM_R,                  # waves with the outer (left) arm
    "wave2": [(0, 1), (-1, 0), (-1, -1)] + _ARM_R,
}
CLAUDE_LEGS = {
    "stand": [(x, y) for x in (2, 4, 8, 10) for y in (8, 9)],
    "stepA": [(2, 8), (2, 9), (8, 8), (8, 9), (4, 8), (10, 8)],
    "stepB": [(4, 8), (4, 9), (10, 8), (10, 9), (2, 8), (8, 8)],
}


def claude_frame(eyes, arms, legs, bob):
    c = Canvas()
    ox, oy = 1, 3 - bob          # two spare rows on top for raised arms
    c.rect(ox + 1, oy, 11, 8, "orange")
    for x, y in CLAUDE_ARMS[arms] + CLAUDE_LEGS[legs]:
        c.set(ox + x, oy + y, "orange")
    for x, y in CLAUDE_EYES[eyes]:
        c.set(ox + x, oy + y, "K")
    if eyes == "wow":
        c.set(ox + 2, oy + 2, "white")
        c.set(ox + 9, oy + 2, "white")
    return outlined(c)


CODEX_BODY = [
    "...BBBBB...",
    ".BBBBBBBBB.",
    "BBSSSSSSSBB",
    "BBSSSSSSSBQ",
    "BBSSSSSSSBQ",
    "BBSSSSSSSBQ",
    "BBSSSSSSSBQ",
    ".BBBBBBBBQ.",
    "QBBBBBBBBBQ",
    "..BBBBBBQ..",
]
CODEX_FACES = {                                   # drawn on the screen
    "prompt": [(3, 3), (4, 4), (3, 5), (6, 5), (7, 5)],     # >_
    "cursor_off": [(3, 3), (4, 4), (3, 5)],
    "happy": [(2, 4), (3, 3), (4, 4), (6, 4), (7, 3), (8, 4)],   # ^ ^
}
CODEX_LEGS = {
    "stand": [(3, 10), (3, 11), (7, 10), (7, 11)],
    "stepA": [(3, 10), (3, 11), (7, 10)],
    "stepB": [(3, 10), (7, 10), (7, 11)],
}


def codex_frame(face, legs, bob):
    c = Canvas()
    ox, oy = 1, 2 - bob
    c.sprite(CODEX_BODY, ox, oy)
    for x, y in CODEX_LEGS[legs]:
        c.set(ox + x, oy + y, "codex")
    for x, y in CODEX_FACES[face]:
        c.set(ox + x, oy + y, "glyph")
    return outlined(c)


def gemini_frame(eyes, shine):
    """Four-point star: blue top, green right, yellow bottom, red left."""
    c = Canvas()
    cx = cy = 7
    cols = {-90: "gem_b", 0: "gem_g", 90: "gem_y", 180: "gem_r", -180: "gem_r"}
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            if abs(dx) ** 0.7 + abs(dy) ** 0.7 > 6 ** 0.7 + 1e-9:
                continue
            ang = math.degrees(math.atan2(dy, dx))
            near = sorted(cols, key=lambda a: abs(a - ang))
            col = cols[near[0]]
            if abs(abs(near[0] - ang) - 45) < 12 and (dx + dy) % 2:
                col = cols[near[1]]                          # dither across the seams
            if abs(dx) + abs(dy) <= (2 if shine else 1):
                col = "white" if shine else "gem_c"
            c.set(cx + dx, cy + dy, col)
    if shine:
        for dx, dy in ((0, -6), (0, 6), (-6, 0), (6, 0), (0, -5), (0, 5), (-5, 0), (5, 0)):
            c.set(cx + dx, cy + dy, "white")
    for ex in (-2, 2):
        c.set(cx + ex, cy, "K")
        if eyes == "dot":
            c.set(cx + ex, cy - 1, "K")
    return outlined(c)

BUBBLE = [
    ".KKKKK.",
    "KwwwwwK",
    "KwwKwwK",
    "KwwKwwK",
    "KwwKwwK",
    "KwwwwwK",
    "KwwKwwK",
    "KwwwwwK",
    ".KKKKK.",
    "..KK...",
    "..K....",
]

NOTE = [
    "..KK",
    "..Kw",
    "..K.",
    "KKK.",
    "KKK.",
]


def frames_for(rows_by_name):
    """Outlined frames: idle, step (legs apart) and bob (idle raised by one)."""
    out = {}
    for name, rows in (("idle", rows_by_name["idle"]), ("step", rows_by_name["step"]),
                       ("bob", rows_by_name["idle"])):
        c = Canvas()
        c.sprite(rows, 1, 0 if name == "bob" else 1)
        out[name] = outlined(c)
    return out

# ---------------------------------------------------------------- route


NODES = [(24, 79), (62, 64), (100, 81), (138, 64), (176, 80), (214, 67)]
NAMES = ["PHYSICS", "ROBOTS", "VISION", "SENSES", "AI TEAM", "GAMES"]
# low stops are labelled under the path, high ones above their building
LABEL_Y = [83, 41, 85, 37, 84, 38]
ROUTE = [(2, 79)] + NODES + [(238, 58)]


def bezier(a, b, n=160):
    (x0, y0), (x1, y1) = a, b
    dx = (x1 - x0) * 0.5
    c1, c2 = (x0 + dx, y0), (x1 - dx, y1)
    pts = []
    for i in range(n + 1):
        t = i / n
        m = 1 - t
        pts.append((m**3 * x0 + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t**3 * x1,
                    m**3 * y0 + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t**3 * y1))
    return pts


SAMPLES = []      # (x, y, s)
NODE_S = []
_s = 0.0
for k in range(len(ROUTE) - 1):
    pts = bezier(ROUTE[k], ROUTE[k + 1])
    if k == 0:
        SAMPLES.append((*pts[0], 0.0))
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        _s += math.hypot(xb - xa, yb - ya)
        SAMPLES.append((xb, yb, _s))
    if 0 <= k < len(NODES):
        NODE_S.append(_s)


def pos_at(s):
    lo, hi = 0, len(SAMPLES) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if SAMPLES[mid][2] < s:
            lo = mid
        else:
            hi = mid
    xa, ya, sa = SAMPLES[lo]
    xb, yb, sb = SAMPLES[hi]
    u = 0 if sb == sa else min(1, max(0, (s - sa) / (sb - sa)))
    return xa + (xb - xa) * u, ya + (yb - ya) * u

# ---------------------------------------------------------------- timeline


GAP = 13                          # Claude walks this far behind; Codex and Gemini 14 more each
STOP = [0, 0, 0, -8, 0, 16]       # left of the senses lab door; last stop inside the fog
PAUSE = {1: 0.9, 2: 0.9, 3: 2.8, 4: 2.6}
START_HOLD = 1.4
END_ARRIVE = T - 5.5

STOP_S = [s + d for s, d in zip(NODE_S, STOP)]
_walk = STOP_S[-1] - STOP_S[0]
SPEED = _walk / (END_ARRIVE - START_HOLD - sum(PAUSE.values()))

SEGS = [(0.0, START_HOLD, STOP_S[0], STOP_S[0])]
ARRIVE = {0: 0.5}
_t = START_HOLD
for i in range(1, len(NODES)):
    dur = (STOP_S[i] - STOP_S[i - 1]) / SPEED
    SEGS.append((_t, _t + dur, STOP_S[i - 1], STOP_S[i]))
    _t += dur
    ARRIVE[i] = _t
    if i in PAUSE:
        SEGS.append((_t, _t + PAUSE[i], STOP_S[i], STOP_S[i]))
        _t += PAUSE[i]
SEGS.append((_t, T, STOP_S[-1], STOP_S[-1]))

JOIN = ARRIVE[3] + 0.35
TICKS = [k * DT for k in range(int(T / DT))]


def traveler_s(t):
    for t0, t1, s0, s1 in SEGS:
        if t0 <= t < t1:
            return s0 + (s1 - s0) * (t - t0) / (t1 - t0)
    return STOP_S[-1]


def claude_pos(t):
    """Grid position of Claude's feet, or None before joining."""
    if t < JOIN:
        return None
    dt = t - JOIN
    door = (NODES[3][0] + 1, NODES[3][1] - 4)
    land = pos_at(STOP_S[3] - GAP)
    if dt < 0.35:
        return door[0], door[1] - 3 * math.sin(math.pi * dt / 0.35)
    if dt < 1.15:
        u = (dt - 0.35) / 0.8
        return (door[0] + (land[0] - door[0]) * u,
                door[1] + (land[1] - door[1]) * u - 9 * math.sin(math.pi * u))
    return pos_at(max(STOP_S[3] - GAP, traveler_s(t) - GAP))


LEAVE_SENSES = ARRIVE[3] + PAUSE[3]


def claude_pose(t, k, moving):
    """(eyes, arms, legs, bob, hop) for Claude at time t."""
    dt = t - JOIN
    if dt < 0.35:
        return "wow", "up", "stand", 0, 0                    # pops out of the lab
    if dt < 1.15:
        return "happy", "up", "stand", 0, 0                  # leaps over the traveler
    if t < LEAVE_SENSES:
        arms = "down" if dt < 1.3 else ("wave1" if (k // 4) % 2 else "wave2")
        return "happy", arms, "stand", 0, 0
    if moving:
        legs, arms, bob = (("stepA", "swingA", 0), ("stand", "down", 1),
                           ("stepB", "swingB", 0), ("stand", "down", 1))[(k // 3) % 4]
        return ("blink" if k % 40 < 2 else "dot"), arms, legs, bob, 0
    if ARRIVE[4] <= t < ARRIVE[5]:                           # the team hall: watches the others join
        u = t - ARRIVE[4]
        if u < 0.6:
            return "right", "down", "stand", 0, 0
        if u < 1.6:
            return "left", "down", "stand", 0, 0
        if u < 2.2:
            hop = 2 if u < 1.75 else 0
            return "happy", ("up" if hop else ("wave1" if (k // 4) % 2 else "wave2")), "stand", 0, hop
        return ("blink" if k % 40 < 2 else "dot"), "down", "stand", 0, 0
    u = t - ARRIVE[5]                                        # at the edge of the fog
    if u < 0.6:
        return "right", "down", "stand", 0, 0
    if u < 1.0:
        return "wow", "down", "stand", 0, 0
    if u < 2.4:
        v = (u - 1.0) % 0.7
        hop = round(3 * math.sin(math.pi * v / 0.35)) if v < 0.35 else 0
        return "happy", ("up" if hop else "down"), "stand", 0, hop
    if u < 3.4:
        return "happy", ("wave1" if (k // 4) % 2 else "wave2"), "stand", 0, 0
    return ("blink" if k % 40 < 2 else "dot"), "down", "stand", 0, 0


# The rest of the party waits at the team hall: Codex beside it, Gemini
# floating by the left tower. When the traveler arrives they fall in behind.
HALL = ARRIVE[4]
LEAVE_HALL = HALL + PAUSE[4]
CODEX_WAIT = (NODES[4][0] + 13, NODES[4][1] - 3)
GEMINI_WAIT = (NODES[4][0] - 13, NODES[4][1] - 16)


def follower_pos(back, wait, t_leap, leap_dur, peak, t):
    land_s = STOP_S[4] - back
    if t < t_leap:
        return wait
    land = pos_at(land_s)
    if t < t_leap + leap_dur:
        u = (t - t_leap) / leap_dur
        return (wait[0] + (land[0] - wait[0]) * u,
                wait[1] + (land[1] - wait[1]) * u - peak * math.sin(math.pi * u))
    return pos_at(max(land_s, traveler_s(t) - back))


def codex_pos(t):
    return follower_pos(GAP + 14, CODEX_WAIT, HALL + 0.6, 0.8, 14, t)


def gemini_pos(t):
    """Floats over the party at the hall, then drifts down to the back of the line."""
    u = min(1.0, max(0.0, (t - LEAVE_HALL) / 3.0))
    back, lift = GAP + 7 + 21 * u, 12 * (1 - u)
    if t < HALL + 1.0:
        x, y = GEMINI_WAIT
    else:
        x, y = pos_at(max(STOP_S[4] - back, traveler_s(t) - back))
        y -= lift
        if t < HALL + 2.0:
            v = t - HALL - 1.0
            x = GEMINI_WAIT[0] + (x - GEMINI_WAIT[0]) * v
            y = GEMINI_WAIT[1] + (y - GEMINI_WAIT[1]) * v - 4 * math.sin(math.pi * v)
    return x, y - 3 - math.sin(2 * math.pi * t / 1.4)        # always hovering


def codex_pose(t, k, moving):
    """(face, legs, bob, hop) for Codex at time t."""
    idle = "prompt" if (k // 8) % 2 else "cursor_off"         # blinking cursor
    if t < HALL + 0.2:
        return idle, "stand", 0, 0
    if t < HALL + 1.4:                                        # cheers, then leaps to the back
        return "happy", "stand", 0, (2 if HALL + 0.3 <= t < HALL + 0.45 else 0)
    if t < LEAVE_HALL:
        return ("happy" if t < HALL + 2.0 else idle), "stand", 0, 0
    if moving:
        legs, bob = (("stepA", 0), ("stand", 1), ("stepB", 0), ("stand", 1))[((k + 2) // 3) % 4]
        return "prompt", legs, bob, 0
    u = t - ARRIVE[5]
    if 1.15 <= u < 2.55:
        v = (u - 1.15) % 0.7
        return "happy", "stand", 0, (round(3 * math.sin(math.pi * v / 0.35)) if v < 0.35 else 0)
    return idle, "stand", 0, 0


def gemini_pose(t, k):
    """(eyes, shine) for Gemini at time t."""
    u = t - ARRIVE[5]
    shine = HALL + 0.2 <= t < HALL + 0.5 or k % 48 < 2 or (1.3 <= u < 2.7 and (k // 3) % 2 == 0)
    return ("blink" if k % 56 in (20, 21) else "dot"), shine


def snap(x, y):
    return f"{round(x) * P} {round(y) * P}"

# ---------------------------------------------------------------- animation helpers


def _kt(t):
    return f"{t / T:.4f}".rstrip("0").rstrip(".")


def _steps(changes):
    ts, vs = [], []
    for t, v in changes:
        if vs and vs[-1] == v:
            continue
        if ts and abs(t - ts[-1]) < 1e-9:
            vs[-1] = v
            continue
        ts.append(t)
        vs.append(v)
    ts[0] = 0.0
    return ";".join(_kt(t) or "0" for t in ts), ";".join(str(v) for v in vs)


def timeline(attr, changes):
    """Discrete animation on the shared T-second loop."""
    k, v = _steps(changes)
    if attr == "translate":
        return (f'<animateTransform attributeName="transform" type="translate" dur="{T}s" '
                f'repeatCount="indefinite" calcMode="discrete" keyTimes="{k}" values="{v}"/>')
    return (f'<animate attributeName="{attr}" dur="{T}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{k}" values="{v}"/>')


def loop(attr, dur, values, keytimes=None, begin=0.0, discrete=True, translate=False):
    """Free-running ambient animation with its own period."""
    kt = f' keyTimes="{keytimes}"' if keytimes else ""
    mode = ' calcMode="discrete"' if discrete else ""
    beg = f' begin="{begin:.2f}s"' if begin else ""
    if translate:
        return (f'<animateTransform attributeName="transform" type="translate" dur="{dur}s"'
                f'{beg} repeatCount="indefinite"{mode}{kt} values="{values}"/>')
    return f'<animate attributeName="{attr}" dur="{dur}s"{beg} repeatCount="indefinite"{mode}{kt} values="{values}"/>'


def group(inner, anim="", opacity=None, transform=None):
    attrs = ""
    if opacity is not None:
        attrs += f' opacity="{opacity}"'
    if transform:
        attrs += f' transform="{transform}"'
    return f"<g{attrs}>{inner}{anim}</g>"


def lit_window(t_on):
    return [(0, 0), (t_on, 1), (FADE, 0)]

# ---------------------------------------------------------------- regions
# Each region draws into `base` (static), adds overlay canvases to `lit`
# (list of (canvas, t_on)) and free-running pieces to `ambient` (svg strings).


def window(c, lit, x, y, w=2, h=2):
    c.box(x - 1, y - 1, w + 2, h + 2, "win")
    glow = Canvas()
    glow.rect(x - 2, y - 2, w + 4, h + 4, "glow")
    for j in range(y - 1, y + h + 1):
        for i in range(x - 1, x + w + 1):
            glow.px.pop((i, j), None)
    glow.rect(x, y, w, h, "lit")
    lit.append(glow)


def roof(c, x0, x1, y, fill, step=1):
    k = 0
    while x0 + k * step <= x1 - k * step:
        a, b = x0 + k * step, x1 - k * step
        c.rect(a, y - k, b - a + 1, 1, fill)
        c.set(a, y - k, "K")
        c.set(b, y - k, "K")
        if step > 1:
            c.rect(a, y - k, step, 1, "K")
            c.rect(b - step + 1, y - k, step, 1, "K")
        k += 1
    c.rect(x0 + k * step - step, y - k + 1, x1 - x0 - 2 * (k - 1) * step + 1, 1, "K")


def region_physics(base, lit, amb, pal, cx, by):
    base.box(cx - 11, by - 7, 13, 7, "wall")
    base.rect(cx, by - 6, 1, 5, "wall_m")
    dome = set()
    ox, oy, r = cx - 5, by - 7, 6.5
    for y in range(oy - 7, oy + 1):
        for x in range(ox - 7, ox + 8):
            if (x - ox) ** 2 + (y - oy) ** 2 <= r * r:
                dome.add((x, y))
    for x, y in dome:
        edge = any((x + dx, y + dy) not in dome for dx, dy in ((1, 0), (-1, 0), (0, -1)))
        base.set(x, y, "K" if edge else ("metal_d" if x > ox + 2 else "metal"))
    base.rect(ox, oy - 6, 1, 6, "win")
    base.box(cx - 7, by - 4, 5, 4, "wood")
    window(base, lit, cx - 10, by - 5, 1, 2)
    window(base, lit, cx - 1, by - 5, 1, 2)
    # pedestal with the NV-centre diamond and a pump laser
    base.box(cx + 3, by - 5, 3, 5, "metal")
    base.box(cx + 2, by - 6, 5, 2, "metal")
    gem = Canvas()
    gem.sprite([".dDd.", "dDdDD", ".dDD.", "..D.."], cx + 2, by - 11)
    base.merge(outlined(gem))
    base.box(cx + 9, by - 12, 3, 3, "metal_d")
    base.rect(cx + 10, by - 9, 1, 9, "metal_d")
    beam = Canvas()
    beam.rect(cx + 8, by - 11, 1, 1, "laser")
    beam.rect(cx + 8, by - 12, 1, 1, "laser_glow")
    beam.rect(cx + 8, by - 10, 1, 1, "laser_glow")
    amb.append(group(svg_paths(beam, pal), loop("opacity", 1.4, "1;0.35", "0;0.6")))
    nv = Canvas()
    for x, y in [(cx + 3, by - 11), (cx + 4, by - 11), (cx + 5, by - 11), (cx + 2, by - 10),
                 (cx + 3, by - 10), (cx + 4, by - 10), (cx + 5, by - 10), (cx + 6, by - 10),
                 (cx + 3, by - 9), (cx + 4, by - 9), (cx + 5, by - 9), (cx + 4, by - 8)]:
        nv.set(x, y, "nv")
    for x in range(cx, cx + 9):
        for y in range(by - 14, by - 5):
            if (x, y) not in nv.px and (x, y) not in gem.px and abs(x - cx - 4) + abs(y - by + 10) <= 5:
                if (x, y) not in base.px or base.px[(x, y)] not in ("K",):
                    nv.set(x, y, "nv_glow")
    lit.append(nv)


def region_robots(base, lit, amb, pal, cx, by):
    base.box(cx - 11, by - 8, 13, 8, "wall")
    base.rect(cx, by - 7, 1, 6, "wall_m")
    roof(base, cx - 12, cx + 2, by - 9, "roof", step=2)
    base.box(cx - 9, by - 6, 6, 6, "metal")
    for y in range(by - 4, by, 2):
        base.rect(cx - 8, y, 4, 1, "metal_d")
    window(base, lit, cx - 1, by - 6)
    # robot arm picking coloured blocks
    base.box(cx + 3, by - 3, 6, 3, "metal_d")
    base.box(cx + 4, by - 11, 3, 9, "yellow")
    base.box(cx + 4, by - 13, 3, 3, "metal")
    base.box(cx + 6, by - 13, 7, 3, "yellow")
    base.box(cx + 9, by - 10, 4, 2, "metal")
    base.set(cx + 9, by - 8, "K")
    base.set(cx + 12, by - 8, "K")
    cubes = []
    for col in ("red", "green", "yellow"):
        cube = Canvas()
        cube.box(cx + 9, by - 7, 4, 4, col)
        cubes.append(svg_paths(cube, pal))
    for i, svg in enumerate(cubes):
        vals = ";".join("1" if j == i else "0" for j in range(3))
        amb.append(group(svg, loop("opacity", 4.5, vals, "0;0.3333;0.6667"), opacity=1 if i == 0 else 0))
    led = Canvas()
    led.set(cx + 7, by - 2, "green")
    lit.append(led)


def region_vision(base, lit, amb, pal, cx, by):
    base.box(cx - 12, by - 8, 16, 8, "wall")
    for i in range(3):
        xs = cx - 12 + 5 * i
        for k in range(4):
            y = by - 9 - k
            for x in range(xs + k, xs + 5):
                base.set(x, y, "win" if x == xs + 4 else "roof")
            base.set(xs + k, y, "K")
        base.set(xs + 4, by - 13, "K")
    base.rect(cx - 12, by - 9, 16, 1, "K")
    base.box(cx + 0, by - 15, 3, 7, "wall_d")
    for k in range(3):
        puff = Canvas()
        puff.rect(cx + 1, by - 17, 2, 2, "smoke")
        puff.set(cx + 0, by - 16, "smoke")
        amb.append(group(svg_paths(puff, pal),
                         loop("", 3.0, "0 0;0 -4;4 -8;4 -12", "0;0.25;0.5;0.75", begin=-k, translate=True)
                         + loop("opacity", 3.0, "1;0.7;0.4;0", "0;0.25;0.5;0.75", begin=-k)))
    base.box(cx - 11, by - 7, 6, 5, "white")
    photo = ["bbbb", "bgbb", "gggb"]
    for j, row in enumerate(photo):
        for i, ch in enumerate(row):
            base.set(cx - 10 + i, by - 6 + j, {"b": "blue", "g": "green"}[ch])
    window(base, lit, cx - 3, by - 6)
    window(base, lit, cx + 1, by - 6)
    base.box(cx - 4, by - 3, 4, 3, "wood")
    # camera on a tripod
    for x, y in [(cx + 7, by - 1), (cx + 8, by - 2), (cx + 9, by - 3), (cx + 9, by - 4),
                 (cx + 10, by - 2), (cx + 11, by - 1), (cx + 9, by - 2), (cx + 9, by - 1)]:
        base.set(x, y, "K")
    base.box(cx + 6, by - 9, 7, 5, "metal_d")
    base.box(cx + 7, by - 10, 3, 2, "metal_d")
    base.box(cx + 7, by - 8, 3, 3, "dia_d")
    base.set(cx + 8, by - 7, "white")
    led = Canvas()
    led.set(cx + 11, by - 8, "red")
    amb.append(group(svg_paths(led, pal), loop("opacity", 1.2, "1;0", "0;0.5")))


def region_senses(base, lit, amb, pal, cx, by):
    base.box(cx - 5, by - 10, 11, 10, "wall")
    base.rect(cx + 4, by - 9, 1, 8, "wall_m")
    base.rect(cx, by - 12, 1, 2, "K")
    eye = [
        "...KKKKK...",
        ".KKwtttwKK.",
        "KwwwtKtwwwK",
        ".KKwtttwKK.",
        "...KKKKK...",
    ]
    base.sprite(eye, cx - 5, by - 17)
    lid = Canvas()
    lid.rect(cx - 2, by - 16, 5, 1, "metal")
    lid.rect(cx - 4, by - 15, 9, 1, "K")
    lid.rect(cx - 2, by - 14, 5, 1, "metal")
    lid.rect(cx - 3, by - 16, 1, 3, "metal")
    lid.rect(cx + 3, by - 16, 1, 3, "metal")
    amb.append(group(svg_paths(lid, pal), loop("opacity", 4.0, "0;1;0", "0;0.92;0.96"), opacity=0))
    base.rect(cx - 4, by - 14, 1, 3, "K")
    tip = Canvas()
    tip.set(cx - 4, by - 15, "red")
    amb.append(group(svg_paths(tip, pal), loop("opacity", 1.6, "1;0.2", "0;0.5")))
    base.box(cx - 2, by - 5, 5, 5, "wood")
    base.rect(cx + 1, by - 3, 1, 1, "yellow")
    window(base, lit, cx - 3, by - 8, 1, 2)
    window(base, lit, cx + 3, by - 8, 1, 2)
    for k in range(2):
        note = Canvas()
        note.sprite(NOTE, cx + 7 + 2 * k, by - 9 - 2 * k)
        amb.append(group(svg_paths(note, pal),
                         loop("", 3.2, "0 0;0 -4;4 -8;4 -12", "0;0.25;0.5;0.75", begin=-1.6 * k, translate=True)
                         + loop("opacity", 3.2, "1;1;0.6;0", "0;0.25;0.5;0.75", begin=-1.6 * k)))


def region_team(base, lit, amb, pal, cx, by):
    base.box(cx - 8, by - 9, 17, 9, "wall")
    roof(base, cx - 8, cx + 8, by - 10, "roof", step=2)
    for tx in (cx - 12, cx + 8):
        base.box(tx, by - 13, 5, 13, "wall_m")
        for k in range(0, 5, 2):
            base.rect(tx + k, by - 14, 1, 1, "K")
    base.rect(cx, by - 19, 1, 6, "K")
    flags = []
    for f in range(2):
        fl = Canvas()
        for j, col in enumerate(("orange", "green", "blue")):
            for i in range(5):
                lift = 1 if (i + f) % 4 >= 2 else 0
                fl.set(cx + 1 + i, by - 19 + j - lift + 1, col)
        flags.append(svg_paths(fl, pal))
    amb.append(group(flags[0], loop("opacity", 0.8, "1;0", "0;0.5")))
    amb.append(group(flags[1], loop("opacity", 0.8, "0;1", "0;0.5"), opacity=0))
    base.box(cx - 2, by - 5, 5, 5, "wood")
    base.rect(cx - 1, by - 6, 3, 1, "K")
    for i, col in enumerate(("orange", "green", "blue")):
        base.set(cx - 1 + i, by - 8, col)
    for x in (cx - 6, cx + 5):
        window(base, lit, x, by - 7)
    for x in (cx - 10, cx + 10):
        window(base, lit, x, by - 10, 1, 2)


def region_games(base, lit, amb, pal, cx, by):
    base.box(cx - 12, by - 6, 8, 6, "wall")
    roof(base, cx - 13, cx - 4, by - 7, "roof")
    base.box(cx - 10, by - 4, 3, 4, "wood")
    base.box(cx + 4, by - 7, 8, 7, "wall")
    roof(base, cx + 3, cx + 12, by - 8, "roof_d")
    window(base, lit, cx + 6, by - 5)
    window(base, lit, cx - 6, by - 4, 1, 1)
    for x in (cx - 3, cx + 2):
        base.rect(x, by - 12, 1, 12, "wood_d")
    for y in (by - 12, by - 7):
        base.rect(cx - 3, y, 6, 1, "wood")
    base.box(cx - 2, by - 3, 4, 3, "wall_m")
    base.box(cx - 3, by - 19, 7, 7, "wood")
    q = Canvas()
    q.sprite(["lll.", "..l.", ".ll.", "....", ".l.."], cx - 1, by - 18)
    lit.append(q)
    base.sprite([".ww.", "...w", "..w.", "....", "..w."], cx - 2, by - 18)

# ---------------------------------------------------------------- scenery


def draw_sky(c, pal, theme, rng):
    bands = [(2, "sky0"), (11, "sky1"), (20, "sky2"), (28, "sky3"), (35, "sky4")]
    for k, (y0, col) in enumerate(bands):
        y1 = bands[k + 1][0] if k + 1 < len(bands) else 48
        c.rect(2, y0, W - 4, y1 - y0, col)
        if k + 1 < len(bands):
            for x in range(2 + (y1 % 2), W - 2, 2):
                c.set(x, y1 - 1, bands[k + 1][1])
    # moon or sun
    mx, my = 150, 12
    for y in range(my - 5, my + 6):
        for x in range(mx - 5, mx + 6):
            d = (x - mx) ** 2 + (y - my) ** 2
            if d <= 25:
                c.set(x, y, "moon_d" if (theme == "dark" and (x - mx - 2) ** 2 + (y - my + 1) ** 2 <= 6)
                      or (theme == "light" and d >= 17) else "moon")
    if theme == "light":
        for dx, dy in ((0, -8), (0, 8), (-8, 0), (8, 0), (-6, -6), (6, 6), (-6, 6), (6, -6)):
            c.set(mx + dx, my + dy, "moon_d")


def stars(pal, rng):
    static, twinkle = Canvas(), []
    for k in range(70):
        x, y = rng.randrange(4, W - 4), rng.randrange(3, 34)
        if x < 80 and y < 16 or x > 168 and y < 18 or abs(x - 150) < 9 and abs(y - 12) < 9:
            continue
        if k % 5 == 0:
            s = Canvas()
            s.set(x, y, "star")
            if k % 10 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    s.set(x + dx, y + dy, "star_d")
            twinkle.append(group(svg_paths(s, pal),
                                 loop("opacity", round(rng.uniform(1.8, 3.6), 2), "1;0.15;1", "0;0.5;1",
                                      begin=-rng.uniform(0, 3), discrete=False)))
        else:
            static.set(x, y, "star" if k % 3 else "star_d")
    return static, twinkle


def cloud(c, x, y, w):
    for i in range(w):
        h = 2 + int(2.2 * math.sin(math.pi * i / (w - 1)))
        c.rect(x + i, y - h, 1, h, "cloud")
        c.set(x + i, y, "cloud_d")


def draw_land(c, rng):
    for x in range(2, W - 2):
        top = int(31 + 3.5 * math.sin(x / 11.0) + 2.5 * math.sin(x / 4.7 + 1.3) + 1.2 * math.sin(x / 2.1))
        c.rect(x, top, 1, 48 - top, "mtn_far")
        c.set(x, top, "mtn_h")
    for x in range(2, W - 2):
        top = int(39 + 2.5 * math.sin(x / 8.0 + 2) + 1.5 * math.sin(x / 3.3))
        c.rect(x, top, 1, 48 - top, "mtn_near")
    c.rect(2, 46, W - 4, H - 48, "g0")
    for x in range(2, W - 2):
        if rng.random() < 0.55:
            c.set(x, 45, "tuft")
    for y in range(47, H - 2):
        for x in range(2, W - 2):
            r = rng.random()
            if r < 0.06:
                c.set(x, y, "g1")
            elif r < 0.10:
                c.set(x, y, "g2")
    for _ in range(60):
        x, y = rng.randrange(4, W - 4), rng.randrange(48, H - 3)
        c.set(x, y, "tuft")
        c.set(x - 1, y - 1, "tuft")
        c.set(x + 1, y - 1, "tuft")


def draw_path(c, rng):
    cells_e, cells = set(), set()
    for x, y, _ in SAMPLES:
        for j in range(int(y) - 3, int(y) + 4):
            for i in range(int(x) - 3, int(x) + 4):
                d = (i + 0.5 - x) ** 2 + (j + 0.5 - y) ** 2
                if d <= 2.6 ** 2:
                    cells_e.add((i, j))
                if d <= 1.9 ** 2:
                    cells.add((i, j))
    for xy in cells_e:
        if 2 <= xy[0] < W - 2:
            c.px[xy] = "path_e"
    for xy in cells:
        if 2 <= xy[0] < W - 2:
            c.px[xy] = "path_h" if rng.random() < 0.08 else "path"
    return cells_e


def tree(kind):
    t = Canvas()
    if kind == "round":
        for y in range(-9, -2):
            for x in range(-4, 5):
                d = x * x + (y + 6) ** 2 * 1.2
                if d <= 13:
                    col = "leaf_h" if x + y < -8 else ("leaf_d" if x - y > 7 or y > -4 else "leaf")
                    t.set(x, y, col)
        t.rect(0, -3, 1, 3, "trunk")
    else:
        for k, (y, half) in enumerate(((-11, 0), (-10, 1), (-9, 1), (-8, 2), (-7, 1), (-6, 2),
                                       (-5, 3), (-4, 2), (-3, 3))):
            for x in range(-half, half + 1):
                t.set(x, y, "leaf_d" if x > 0 else ("leaf_h" if x < 0 and k % 3 == 0 else "leaf"))
        t.rect(0, -2, 1, 2, "trunk")
    return outlined(t)


def decorate(c, rng, blocked):
    placed = []
    for _ in range(900):
        x, y = rng.randrange(5, W - 5), rng.randrange(52, H - 3)
        if any(abs(x - px) < 8 and abs(y - py) < 7 for px, py in placed):
            continue
        if any((i, j) in blocked for i in range(x - 5, x + 6) for j in range(y - 12, y + 2)):
            continue
        tr = tree("pine" if rng.random() < 0.4 else "round")
        for (i, j), col in tr.px.items():
            c.px[(x + i, y + j)] = col
        placed.append((x, y))
        if len(placed) >= 20:
            break
    for _ in range(160):
        x, y = rng.randrange(4, W - 4), rng.randrange(48, H - 3)
        if (x, y) in blocked or (x, y) in c.px and c.px[(x, y)] in ("K", "leaf", "leaf_d", "leaf_h", "trunk"):
            continue
        r = rng.random()
        if r < 0.35:
            c.set(x, y, "flower1")
        elif r < 0.7:
            c.set(x, y, "flower2")
        elif r < 0.8:
            c.rect(x, y, 2, 1, "rock")

# ---------------------------------------------------------------- assemble


def characters(pal):
    tf = frames_for(TRAVELER)
    rest = ("happy", "down", "stand", 0)
    cf = {rest: claude_frame(*rest)}
    trav_pos, trav_frame, cl_pos, cl_frame, cl_vis = [], [], [], [], []
    prev_t = prev_c = None
    for k, t in enumerate(TICKS):
        s = traveler_s(t)
        trav_pos.append((t, snap(*pos_at(s))))
        moving = prev_t is not None and abs(s - prev_t) > 1e-6
        trav_frame.append((t, ("step" if (k // 3) % 2 else "bob") if moving else "idle"))
        prev_t = s
        cp = claude_pos(t)
        if cp is None:
            cl_vis.append((t, 0))
            cl_pos.append((t, snap(NODES[3][0] + 1, NODES[3][1] - 4)))
            cl_frame.append((t, rest))
            continue
        moving = prev_c is not None and math.dist(cp, prev_c) > 1e-6
        prev_c = cp
        *look, hop = claude_pose(t, k, moving)
        look = tuple(look)
        cf.setdefault(look, claude_frame(*look))
        cl_vis.append((t, 1 if t < FADE else 0))
        cl_pos.append((t, snap(cp[0], cp[1] - hop)))
        cl_frame.append((t, look))

    def frames_svg(frames, seq, half_w, height, first):
        out = ""
        for name, fc in frames.items():
            ch = [(t, 1 if f == name else 0) for t, f in seq]
            out += group(svg_paths(fc, pal), timeline("opacity", ch), opacity=1 if name == first else 0)
        return group(out, transform=f"translate({-half_w * P} {-height * P})")

    co_pos, co_frame, ge_pos, ge_frame, cof, gef = [], [], [], [], {}, {}
    prev_x = None
    for k, t in enumerate(TICKS):
        xp = codex_pos(t)
        moving = prev_x is not None and math.dist(xp, prev_x) > 1e-6
        prev_x = xp
        *look, hop = codex_pose(t, k, moving)
        look = tuple(look)
        cof.setdefault(look, codex_frame(*look))
        co_pos.append((t, snap(xp[0], xp[1] - hop)))
        co_frame.append((t, look))
        look = gemini_pose(t, k)
        gef.setdefault(look, gemini_frame(*look))
        ge_pos.append((t, snap(*gemini_pos(t))))
        ge_frame.append((t, look))

    fade = [(0, 0), (0.25, 0.5), (0.5, 1), (FADE, 0.6), (FADE + 0.25, 0.3), (FADE + 0.5, 0)]
    trav = group(group(frames_svg(tf, trav_frame, 5.5, 14, "idle"), timeline("opacity", fade), opacity=0),
                 timeline("translate", trav_pos))
    bub = Canvas()
    bub.sprite(BUBBLE, 4, -10)
    bubble = group(svg_paths(bub, pal),
                   timeline("opacity", [(0, 0), (JOIN + 1.15, 1), (JOIN + 2.2, 0)]), opacity=0)
    claude = group(group(frames_svg(cf, cl_frame, 7.5, 13, rest) + group(bubble, transform=f"translate({-7.5 * P} {-13 * P})"),
                         timeline("opacity", cl_vis), opacity=0),
                   timeline("translate", cl_pos))
    codex = group(group(frames_svg(cof, co_frame, 6.5, 14, co_frame[0][1]), timeline("opacity", fade), opacity=0),
                  timeline("translate", co_pos))
    gemini = group(group(frames_svg(gef, ge_frame, 7.5, 15, ge_frame[0][1]), timeline("opacity", fade), opacity=0),
                   timeline("translate", ge_pos))
    return trav + claude + codex + gemini, tf


def hud(pal, tf):
    c = Canvas()          # unit 2 px
    slots, sy = (378, 402, 426, 450), 8
    draw_text(c, "PARTY", slots[0] - 33, sy + 7, "text")
    for sx in slots:
        c.box(sx, sy, 22, 22, "panel")
        c.rect(sx + 1, sy + 1, 20, 1, "frame_d")
        c.rect(sx + 1, sy + 20, 20, 1, "frame_d")
        c.rect(sx + 1, sy + 1, 1, 20, "frame_d")
        c.rect(sx + 20, sy + 1, 1, 20, "frame_d")
    out = svg_paths(c, pal, unit=2)
    out += svg_paths(tf["idle"], pal, unit=2, ox=(slots[0] + 5) * 2 + 1, oy=(sy + 3) * 2 + 2)
    members = (
        (claude_frame("happy", "down", "stand", 0), (slots[1] + 3) * 2 + 2, (sy + 5) * 2 - 2, JOIN + 0.5),
        (codex_frame("happy", "stand", 0), slots[2] * 2 + 9, sy * 2 + 6, HALL + 0.7),
        (gemini_frame("dot", False), slots[3] * 2 + 7, sy * 2 + 7, HALL + 1.1),
    )
    for (frame, ox, oy, t_on), sx in zip(members, slots[1:]):
        q = Canvas()
        draw_text(q, "?", sx + 9, sy + 7, "sub", shadow=None)
        out += group(svg_paths(q, pal, unit=2), timeline("opacity", [(0, 1), (t_on, 0), (FADE + 0.5, 1)]))
        out += group(svg_paths(frame, pal, unit=2, ox=ox, oy=oy),
                     timeline("opacity", [(0, 0), (t_on, 1), (FADE + 0.5, 0)]), opacity=0)
    return out


def sparkle(pal, x, y, t_on):
    small, big = Canvas(), Canvas()
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        small.set(x + dx, y + dy, "lit")
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        big.set(x + dx, y + dy, "lit" if abs(dx) + abs(dy) < 2 else "white")
    return (group(svg_paths(small, pal), timeline("opacity", [(0, 0), (t_on, 1), (t_on + 0.2, 0),
                                                            (t_on + 0.45, 1), (t_on + 0.65, 0)]), opacity=0)
            + group(svg_paths(big, pal), timeline("opacity", [(0, 0), (t_on + 0.2, 1), (t_on + 0.45, 0)]),
                    opacity=0))


def fog(pal, cx, by):
    layers = ""
    for k, (key, dur, shift) in enumerate((("fog", 7.0, 6), ("fog2", 11.0, -8))):
        f = Canvas()
        rng = random.Random(7 + k)
        for _ in range(13):
            x0, y0 = cx - 16 + rng.randrange(0, 34), by - 20 + rng.randrange(0, 22)
            w = rng.randrange(8, 15)
            for i in range(w):
                h = 1 + int(1.8 * math.sin(math.pi * i / (w - 1)))
                f.rect(x0 + i, y0 - h, 1, 2 * h, key)
        layers += group(svg_paths(f, pal), loop("", dur, f"0 0;{shift * P} 0;0 0", discrete=False, translate=True))
    return layers


def build(theme):
    pal = PALETTES[theme]
    rng = random.Random(42)
    bg = Canvas()
    draw_sky(bg, pal, theme, rng)
    st, twinkle = stars(pal, rng)
    if theme == "dark":
        bg.merge(st)
    else:
        twinkle = []
    land = Canvas()
    draw_land(land, rng)
    path_cells = draw_path(land, rng)

    regions = [region_physics, region_robots, region_vision, region_senses, region_team, region_games]
    blocked = set(path_cells)
    lit_svg, amb = "", []
    base = Canvas()
    for i, (fn, (nx, ny)) in enumerate(zip(regions, NODES)):
        lit = []
        fn(base, lit, amb, pal, nx, ny - 3)
        t_on = ARRIVE[i]
        for k, lc in enumerate(lit):
            step = 0.12 * k if fn is region_team else 0
            lit_svg += group(svg_paths(lc, pal), timeline("opacity", lit_window(t_on + step)), opacity=0)
        lit_svg += sparkle(pal, nx + 9, ny - 20, t_on)
        for x in range(nx - 15, nx + 16):
            for y in range(ny - 24, ny + 10):
                blocked.add((x, y))
    decorate(land, rng, blocked)
    land.merge(base)

    labels = Canvas()     # unit 2 px
    for i, ((nx, ny), name) in enumerate(zip(NODES, NAMES)):
        num = f"{i + 1:02d} "
        wdt = text_width(num + name)
        x = nx * 2 - wdt // 2
        ly = LABEL_Y[i] * 2
        x = draw_text(labels, num, x, ly, "sub") + 1
        draw_text(labels, name, x, ly, "text")

    title = Canvas()      # unit 3 px
    draw_text(title, "THE ROAD SO FAR", 9, 8, "text")

    party, tf = characters(pal)

    end = Canvas()        # unit 2 px
    msg = "TO BE CONTINUED"
    ex = 466 - text_width(msg + "...")
    dx = draw_text(end, msg, ex, 181, "text")
    dots = ""
    for k in range(3):
        d = Canvas()
        draw_text(d, ".", dx + 2 + 2 * k, 181, "text")
        dots += group(svg_paths(d, pal, unit=2),
                      loop("opacity", 1.6, "0;1", f"0;{0.25 * (k + 1):.2f}"))
    t_end = ARRIVE[5] + 0.6
    ending = group(svg_paths(end, pal, unit=2) + dots,
                   timeline("opacity", [(0, 0), (t_end, 1), (FADE + 0.4, 0)]), opacity=0)

    frame = Canvas()
    frame.rect(0, 0, W, H, "frame_d")
    frame.rect(1, 1, W - 2, H - 2, "frame")
    for y in range(2, H - 2):
        for x in range(2, W - 2):
            frame.px.pop((x, y), None)
    for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
        frame.px.pop((x, y), None)
    for x, y in ((1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2)):
        frame.set(x, y, "frame_d")

    clouds = ""
    for k, (cy, w, dur) in enumerate(((10, 18, 140), (19, 12, 100), (27, 22, 180))):
        cc = Canvas()
        cloud(cc, 0, cy, w)
        begin = -dur * (0.2 + 0.3 * k)
        clouds += group(svg_paths(cc, pal),
                        loop("", dur, f"{-30 * P} 0;{(W + 10) * P} 0", discrete=False, begin=begin, translate=True))

    desc = ("Pixel-art world map: a traveler walks from a physics lab past a robot workshop and a "
            "vision data factory; the Claude mascot joins at the senses lab, the Codex mascot and the "
            "Gemini star join at the AI team hall, and all four head into a fog-covered game village. "
            "To be continued.")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W * P} {H * P}" width="{W * P}" '
        f'height="{H * P}" shape-rendering="crispEdges" role="img" aria-labelledby="t d">'
        f'<title id="t">The road so far</title><desc id="d">{desc}</desc>'
        f'<defs><clipPath id="in"><rect x="{2 * P}" y="{2 * P}" width="{(W - 4) * P}" '
        f'height="{(H - 4) * P}"/></clipPath></defs>'
        f'<g clip-path="url(#in)">'
        + svg_paths(bg, pal) + "".join(twinkle) + clouds + svg_paths(land, pal)
        + "".join(amb) + lit_svg + svg_paths(labels, pal, unit=2)
        + fog(pal, NODES[5][0], NODES[5][1] - 3) + party
        + "</g>"
        + svg_paths(title, pal, unit=3) + hud(pal, tf) + ending + svg_paths(frame, pal)
        + "</svg>\n"
    )
    return svg


# ---------------------------------------------------------------- section headers

HEADER_ICONS = {
    "quest": [".yyy.", ".yyy.", ".yyy.", ".yyy.", "..y..", ".....", ".yyy."],     # quest marker !
    "log": [".wwwwww.", "wuuuuuuw", "wwwwwwww", "wuuuuuww", "wwwwwwww", "wuuuuuuw", ".wwwwww."],
    "bag": [".WWWWWWW.", "WvvvvvvvW", "WvvvlvvvW", "KKKKlKKKK", "WvvvvvvvW", "WvvvvvvvW", ".WWWWWWW."],
}
HEADERS = {"current-quest": ("CURRENT QUEST", "quest"), "quest-log": ("QUEST LOG", "log"),
           "inventory": ("INVENTORY", "bag")}
HEADER_W = 200        # in 3 px cells -> 600 px wide


def build_header(theme, label, icon):
    pal = PALETTES[theme]
    c = Canvas()
    ic = Canvas()
    ic.sprite(HEADER_ICONS[icon], 1, 1)
    c.merge(outlined(ic))
    x = draw_text(c, label, 13, 2, "text") + 4
    for i in range(x, HEADER_W - 1, 3):
        c.set(i, 5, "sub")
    w, h = HEADER_W * 3, 11 * 3
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{label.title()}">'
            f'<title>{label.title()}</title>{svg_paths(c, pal, unit=3)}</svg>\n')



def main():
    OUT.mkdir(exist_ok=True)
    for theme in PALETTES:
        svg = build(theme)
        path = OUT / f"worldmap-{theme}.svg"
        path.write_text(svg)
        print(f"{path.relative_to(ROOT)}: {len(svg.encode()) / 1024:.1f} KB")
        for name, (label, icon) in HEADERS.items():
            (OUT / f"header-{name}-{theme}.svg").write_text(build_header(theme, label, icon))


if __name__ == "__main__":
    main()
