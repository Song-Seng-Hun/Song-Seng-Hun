#!/usr/bin/env python3
"""Draw the animated covers for the Notion portfolio's project and study-note pages.

Run from anywhere:
    python3 tools/build_notion_covers.py
It writes assets/notion/covers/<name>.svg, one per scene in SCENES.

Each cover is a 240x64-cell night scene (4 px per cell) drawn with the world map's
palette, sprites and SMIL helpers from build_worldmap.py. Notion crops a cover to a
wide band and phones cut its sides, so every scene keeps its subject in rows 12-53
and the middle third (cells 80-160). The first frame is a complete picture on its
own, for viewers that show covers without animation.
"""

import math
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True     # importing the map tool should not leave tools/__pycache__ behind
from build_worldmap import (ICONS, PALETTES, TRAVELER, Canvas, claude_frame, codex_frame, frames_for, group,
                            outlined, svg_paths, tree)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "notion" / "covers"

P = 4                  # px per cell
CW, CH = 240, 64       # cover size in cells
HORIZON = 38           # first ground row
TICK = 1 / 16          # animation step in seconds
PAL = PALETTES["dark"]

# ---------------------------------------------------------------- timing


def _times(dur, frames):
    """keyTimes/values for a discrete animation from (t, value) pairs, t in seconds."""
    pairs = sorted((max(0.0, min(dur, t)), v) for t, v in frames)
    kt, vals = [], []
    for t, v in pairs:
        if vals and v == vals[-1]:
            continue
        if kt and abs(t - kt[-1]) < 1e-9:
            vals[-1] = v
            continue
        kt.append(t)
        vals.append(v)
    kt[0] = 0.0
    return ";".join(f"{t / dur:.4f}".rstrip("0").rstrip(".") or "0" for t in kt), ";".join(str(v) for v in vals)


def visible_at(spans, t=0.0):
    return any(a <= t < b for a, b in spans)


def rotate(dur, spans, offset):
    """The same spans for something running `offset` seconds ahead of the scene clock."""
    out = []
    for a, b in spans:
        a, b = (a - offset) % dur, (b - offset) % dur or dur
        out += [(a, b)] if a < b else [(a, dur), (0.0, b)]
    return out


def ease(kind, u):
    if kind == "in":
        return u * u
    if kind == "out":
        return 1 - (1 - u) ** 2
    if kind == "inout":
        return 0.5 - 0.5 * math.cos(math.pi * u)
    return u


def cycle(n, start, end, period):
    """Spans for frame k of an n-frame flipbook running from start to end."""
    out = [[] for _ in range(n)]
    t, k = start, 0
    while t < end - 1e-9:
        out[k % n].append((t, min(end, t + period)))
        t += period
        k += 1
    return out

# ---------------------------------------------------------------- drawing


def sprite(rows, x=0, y=0, edge=True):
    c = Canvas()
    c.sprite(rows, x, y)
    return outlined(c) if edge else c


def shifted(c, dx, dy):
    out = Canvas()
    out.px = {(x + dx, y + dy): col for (x, y), col in c.px.items()}
    return out


def on_ground(c, x, feet):
    """Shift a sprite so its left edge is x and its lowest row is feet."""
    xs = [p[0] for p in c.px]
    ys = [p[1] for p in c.px]
    return shifted(c, x - min(xs), feet - max(ys))


def paths(c):
    return svg_paths(c, PAL)


def glow_disc(c, cx, cy, r, col):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r:
                c.set(x, y, col)


def stroke(c, a, b, col, w=2):
    """A thick line from a to b (cell coordinates, floats allowed)."""
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        c.rect(round(x - (w - 1) / 2), round(y - (w - 1) / 2), w, w, col)


def traveler(x, feet, frame="idle"):
    """The portfolio owner's sprite."""
    return on_ground(frames_for(TRAVELER)[frame], x, feet)


def house(c, amb, x, y, w, h, seed):
    """A small house with its base on row y; some windows are lit and one flickers."""
    rng = random.Random(seed)
    c.box(x, y - h, w, h, "wall_m")
    c.rect(x + 1, y - h + 1, w - 2, 1, "wall")
    for k in range(w // 2 + 2):                       # gable roof
        c.rect(x - 1 + k, y - h - k // 2 - 1, w + 2 - 2 * k, 1, "roof" if k % 3 else "roof_d")
        if w + 2 - 2 * k <= 2:
            break
    for wx in range(x + 2, x + w - 3, 4):
        lit = rng.random() < 0.6
        c.box(wx, y - h + 3, 3, 3, "lit" if lit else "win")
        if lit and rng.random() < 0.4:
            f = Canvas()
            f.rect(wx + 1, y - h + 4, 1, 1, "win")
            beat = round(rng.uniform(3, 6), 1)
            amb.append(group(paths(f), f'<animate attributeName="opacity" dur="{beat}s" repeatCount="indefinite" '
                                       f'calcMode="discrete" keyTimes="0;0.8" values="0;1"/>', opacity=0))
    c.rect(x + w // 2 - 1, y - 4, 3, 4, "wood")


def night(seed, keep_clear=(70, 170), trees=True):
    """Sky, stars, two ridges and grass; trees stay out of the middle span."""
    rng = random.Random(seed)
    c, amb = Canvas(), []
    bands = [(0, "sky0"), (8, "sky1"), (15, "sky2"), (22, "sky3"), (28, "sky4")]
    for k, (y0, col) in enumerate(bands):
        y1 = bands[k + 1][0] if k + 1 < len(bands) else HORIZON
        c.rect(0, y0, CW, y1 - y0, col)
        if k + 1 < len(bands):
            for x in range(y1 % 2, CW, 2):
                c.set(x, y1 - 1, bands[k + 1][1])
    for k in range(46):
        x, y = rng.randrange(1, CW - 1), rng.randrange(1, 24)
        if k % 6 == 0:
            s = Canvas()
            s.set(x, y, "star")
            if k % 12 == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    s.set(x + dx, y + dy, "star_d")
            beat = round(rng.uniform(1.8, 3.4), 2)
            amb.append(group(paths(s), f'<animate attributeName="opacity" dur="{beat}s" '
                                       f'begin="-{rng.uniform(0, beat):.2f}s" repeatCount="indefinite" '
                                       f'keyTimes="0;0.5;1" values="1;0.15;1"/>'))
        else:
            c.set(x, y, "star" if k % 3 else "star_d")
    phase = rng.uniform(0, 6)
    for x in range(CW):
        top = int(25 + 3 * math.sin(x / 13.0 + phase) + 2 * math.sin(x / 5.1 + 2 * phase))
        c.rect(x, top, 1, HORIZON - top, "mtn_far")
        c.set(x, top, "mtn_h")
    for x in range(CW):
        top = int(32 + 2 * math.sin(x / 9.0 + phase + 1) + 1.2 * math.sin(x / 3.7))
        c.rect(x, top, 1, HORIZON - top, "mtn_near")
    c.rect(0, HORIZON, CW, CH - HORIZON, "g0")
    for x in range(CW):
        if rng.random() < 0.55:
            c.set(x, HORIZON - 1, "tuft")
    for y in range(HORIZON + 1, CH):
        for x in range(CW):
            r = rng.random()
            if r < 0.05:
                c.set(x, y, "g1")
            elif r < 0.08:
                c.set(x, y, "g2")
    if trees:
        lo, hi = keep_clear
        spots = [x for x in range(8, lo - 6, 13)] + [x for x in range(hi + 6, CW - 6, 13)]
        for x in spots:
            x += rng.randrange(-3, 4)
            y = HORIZON + rng.randrange(1, 4)
            t = tree("pine" if rng.random() < 0.45 else "round")
            for (i, j), col in t.px.items():
                c.px[(x + i, y + j)] = col
    return c, amb


class Scene:
    """A night backdrop plus overlays on one dur-second loop."""

    def __init__(self, seed, dur, **night_kw):
        self.dur = dur
        self.base, self.layers = night(seed, **night_kw)

    def show(self, c, spans):
        """Overlay visible only during spans (it starts in its t=0 state)."""
        frames = [(0.0, 0)]
        for a, b in spans:
            frames += [(a, 1), (b, 0)]
        kt, vals = _times(self.dur, frames)
        anim = (f'<animate attributeName="opacity" dur="{self.dur}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/>')
        self.layers.append(group(paths(c), anim, opacity=1 if visible_at(spans) else 0))

    def flip(self, frames, start=0.0, end=None, period=None):
        end = self.dur if end is None else end
        for c, spans in zip(frames, cycle(len(frames), start, end, period or (end - start) / len(frames))):
            self.show(c, spans)

    def timeline(self, keys):
        """Show one canvas at a time: keys are (t, canvas) in order, each lasting until the next."""
        spans = {}
        for k, (t, c) in enumerate(keys):
            end = keys[k + 1][0] if k + 1 < len(keys) else self.dur
            spans.setdefault(id(c), (c, []))[1].append((t, end))
        for c, sp in spans.values():
            self.show(c, sp)

    def move(self, c, segments, offset=0.0, inner="", spans=None):
        """Translate canvas c (drawn at the origin) along cell-snapped segments
        (t0, t1, (x0, y0), (x1, y1), ease); offset runs it ahead of the scene clock,
        spans (scene time) limits when it is visible."""
        frames = []
        for t0, t1, a, b, kind in segments:
            steps = max(1, round((t1 - t0) / TICK))
            for k in range(steps + 1):
                u = ease(kind, k / steps)
                frames.append((t0 + (t1 - t0) * k / steps,
                               (round(a[0] + (b[0] - a[0]) * u), round(a[1] + (b[1] - a[1]) * u))))
        self.move_frames(c, frames, offset, inner, spans)

    def move_frames(self, c, cells, offset=0.0, inner="", spans=None):
        """Like move, from explicit (t, (x, y)) cell positions."""
        frames = [(t, f"{x * P} {y * P}") for t, (x, y) in cells]
        at = lambda t: [v for s, v in sorted(frames) if s <= t + 1e-9][-1]
        first = at(offset % self.dur)
        frames = [((t - offset) % self.dur, v) for t, v in frames] + [(0.0, first)]
        kt, vals = _times(self.dur, frames)
        anim = (f'<animateTransform attributeName="transform" type="translate" dur="{self.dur}s" '
                f'repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vals}"/>')
        moving = group(paths(c) + inner, anim, transform=f"translate({first})")
        self.layers.append(moving if spans is None else shown_inner(self.dur, moving, spans, raw=True))

    def svg(self, title, desc):
        w, h = CW * P, CH * P
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                f'shape-rendering="crispEdges" role="img" aria-labelledby="t d">'
                f'<title id="t">{title}</title><desc id="d">{desc}</desc>'
                f'{paths(self.base)}{"".join(self.layers)}</svg>\n')


def shown_inner(dur, c, spans, raw=False):
    """A group visible during spans, for nesting inside a moving layer (raw: c is SVG already)."""
    frames = [(0.0, 0)]
    for a, b in spans:
        frames += [(a, 1), (b, 0)]
    kt, vals = _times(dur, frames)
    return group(c if raw else paths(c), f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
                           f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/>',
                 opacity=1 if visible_at(spans) else 0)

# ---------------------------------------------------------------- machines


def arm_pose(shoulder, l1, l2, wrist):
    """Elbow-up two-link solution: returns elbow and the reachable wrist."""
    dx, dy = wrist[0] - shoulder[0], wrist[1] - shoulder[1]
    d = max(1e-6, min(l1 + l2 - 1e-6, math.hypot(dx, dy)))
    base = math.atan2(dy, dx)
    bend = math.acos((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))
    best = None
    for s in (1, -1):
        a = base + s * bend
        elbow = (shoulder[0] + l1 * math.cos(a), shoulder[1] + l1 * math.sin(a))
        if best is None or elbow[1] < best[1]:
            best = elbow
    w = (shoulder[0] + d * math.cos(base), shoulder[1] + d * math.sin(base))
    return best, w


def arm_frame(shoulder, wrist, l1=12, l2=11, grip="open", load=None, col="yellow"):
    """Side view of a two-link arm with a gripper; load is a canvas hung from the gripper."""
    elbow, w = arm_pose(shoulder, l1, l2, wrist)
    c = Canvas()
    stroke(c, shoulder, elbow, col, 3)
    stroke(c, elbow, w, col, 2)
    wx, wy = round(w[0]), round(w[1])
    c.rect(wx - 2, wy, 5, 1, "metal_d")
    gap = 2 if grip == "open" else 1
    for sx in (-gap, gap):
        c.rect(wx + sx, wy + 1, 1, 3, "metal_d")
    for x, y in (shoulder, elbow):
        c.rect(round(x) - 1, round(y) - 1, 3, 3, "metal")
    out = outlined(c)
    if load is not None:
        width = max(x for x, _ in load.px) + 1
        out.merge(shifted(load, wx - (width - 1) // 2, wy + 2))
    return out


def crate(col="wood"):
    c = Canvas()
    c.box(0, 0, 5, 4, col)
    c.rect(1, 1, 3, 1, "wood_d" if col == "wood" else "K")
    return c


def road(c, y=42, marks=True):
    """Far curb on row y, a two-lane road below it and a paved sidewalk in front."""
    c.rect(0, y, CW, 1, "path_e")
    c.rect(0, y + 1, CW, 1, "metal_d")
    c.rect(0, y + 2, CW, 10, "win")
    c.rect(0, y + 12, CW, 1, "metal_d")
    if marks:
        for x in range(2, CW, 12):
            c.rect(x, y + 6, 6, 1, "sub")
    c.rect(0, y + 13, CW, 4, "path")
    for x in range(0, CW, 7):
        c.rect(x, y + 13, 1, 4, "path_e")
    c.rect(0, y + 17, CW, 1, "path_e")


PED = {   # a passer-by, two walking frames
    "a": ["..hh.", ".hff.", "..f..", ".ttt.", "t.t.t", "..t..", ".n.n.", ".n.n.", ".K.K."],
    "b": ["..hh.", ".hff.", "..f..", ".ttt.", ".tt.t", "..t..", ".n.n.", "n...n", "K...K"],
}

GLYPHS = {   # 7x6 Korean syllables for "speech becomes text" moments
    "ga": ["xxxx.x.", "...x.x.", "...x.xx", "..x..x.", ".x...x.", "x....x."],
    "na": ["x....x.", "x....x.", "x....xx", "x....x.", "xxxx.x.", ".....x."],
    "da": ["xxxx.x.", "x....x.", "x....xx", "x....x.", "xxxx.x.", ".....x."],
}


def glyph(c, name, x, y, col):
    for j, row in enumerate(GLYPHS[name]):
        for i, ch in enumerate(row):
            if ch == "x":
                c.set(x + i, y + j, col)


def easel(c, x, y, w, h, fill="panel"):
    """A wooden board on legs with its top-left at (x, y); returns the inner box."""
    c.box(x, y, w, h, fill, "K")
    c.rect(x - 1, y - 1, w + 2, 1, "wood")
    c.rect(x - 1, y + h, w + 2, 1, "wood")
    for lx in (x + 2, x + w - 4):
        c.rect(lx, y + h + 1, 2, HORIZON + 6 - (y + h + 1), "wood_d")
    return x + 1, y + 1, w - 2, h - 2


def wrist_path(keys, step):
    """Sample (t, wrist, grip, holding) keyframes every `step` seconds with ease in-out between them."""
    out, t, end = [], 0.0, keys[-1][0]
    while t < end - 1e-9:
        k = max(i for i, kk in enumerate(keys) if kk[0] <= t + 1e-9)
        a, b = keys[k], keys[min(k + 1, len(keys) - 1)]
        u = 0 if b[0] == a[0] else ease("inout", (t - a[0]) / (b[0] - a[0]))
        out.append((t, (round(a[1][0] + (b[1][0] - a[1][0]) * u), round(a[1][1] + (b[1][1] - a[1][1]) * u)),
                    a[2], a[3]))
        t += step
    return out

# ---------------------------------------------------------------- scenes


def scene_v2i():
    """V2I: the traffic light reads the car's RFID, talks to it over Bluetooth, then turns green."""
    s = Scene("v2i", 8.0, trees=False)
    c = s.base
    for x, w, h, seed in ((10, 14, 9, 1), (30, 11, 7, 2), (196, 13, 8, 3), (216, 16, 10, 4)):
        house(c, s.layers, x, 42, w, h, seed)
    for x in (52, 63, 180, 236):
        t = tree("pine" if x % 2 else "round")
        for (i, j), col in t.px.items():
            c.px[(x + i, 42 + j)] = col
    # far curb, road with lane marks, crosswalk and stop line, near sidewalk
    c.rect(0, 42, CW, 1, "path_e")
    c.rect(0, 43, CW, 1, "metal_d")
    c.rect(0, 44, CW, 10, "win")
    c.rect(0, 54, CW, 1, "metal_d")
    for x in range(2, CW, 12):
        c.rect(x, 48, 6, 1, "sub")
    for y in range(45, 54, 2):
        c.rect(128, y, 9, 1, "star_d")
    c.rect(125, 49, 1, 5, "white")
    c.rect(0, 55, CW, 4, "path")
    for x in range(0, CW, 7):
        c.rect(x, 55, 1, 4, "path_e")
    c.rect(0, 59, CW, 1, "path_e")
    # traffic light on the far curb: pole, hooded head, ESP32 box with an RFID reader facing the road
    c.rect(140, 31, 2, 12, "metal_d")
    c.rect(139, 42, 4, 1, "metal")
    c.box(136, 13, 10, 18, "screen", "K")
    c.rect(135, 13, 12, 1, "K")
    for y in (15, 20, 25):
        c.rect(138, y, 6, 3, "win")
        c.rect(137, y - 1, 8, 1, "K")                  # little visors
    c.box(143, 32, 8, 7, "teal")
    c.rect(144, 33, 6, 2, "screen")
    c.rect(145, 36, 1, 1, "green")
    c.box(131, 33, 6, 6, "metal")                     # the RFID reader
    for k in range(3):
        c.rect(132 + k, 34 + k, 4 - 2 * k, 1, "metal_d")
    c.merge(traveler(92, 42))
    lamps = {}
    for name, y, col, glow in (("red", 15, "red", "nv_glow"), ("yellow", 20, "yellow", "glow"),
                               ("green", 25, "green", "laser_glow")):
        lc = Canvas()
        glow_disc(lc, 140, y + 1, 5, glow)
        lc.rect(138, y, 6, 3, col)
        lc.rect(138, y, 2, 1, "white")
        lamps[name] = lc
    # the car waits at the stop line, leaves on green and the next one rolls in
    wait, gone, far = (109, 43), (250, 43), (-20, 43)
    s.move(sprite(ICONS["car"]), [(0.0, 1.8, wait, wait, "lin"), (1.8, 4.2, wait, gone, "in"),
                                  (4.2, 5.0, far, far, "lin"), (5.0, 7.4, far, wait, "out"),
                                  (7.4, 8.0, wait, wait, "lin")])
    s.show(lamps["red"], [(0, 1.8), (4.4, 8.0)])
    s.show(lamps["green"], [(1.8, 3.8)])
    s.show(lamps["yellow"], [(3.8, 4.4)])
    # RFID read flash on the reader, then Bluetooth arcs from the box towards the car
    flash = Canvas()
    glow_disc(flash, 134, 36, 4, "laser_glow")
    flash.rect(132, 34, 4, 4, "glyph")
    s.show(flash, [(7.3, 7.6)])
    arcs = []
    for r in (4, 8, 12):
        a = Canvas()
        for k in range(2 * r + 3):
            ang = math.pi * (0.62 + 0.3 * k / (2 * r + 2))
            if k % 2 == 0:
                a.set(round(142 + r * math.cos(ang)), round(35 + r * math.sin(ang) * 0.75), "glyph")
        arcs.append(a)
    talk0 = cycle(3, 0.0, 1.75, 0.25)
    talk = cycle(3, 7.6, 8.0, 0.25)
    for k, a in enumerate(arcs):
        s.show(a, talk0[k] + talk[k])
    return s.svg("V2I signal",
                 "Pixel-art night street: a car waits at a red light while the light's controller talks to it "
                 "over Bluetooth; the light turns green, the car drives off, and the next car rolls in and is "
                 "recognised by its RFID card.")


DANCE = [   # head, neck, hip, l-elbow, l-hand, r-elbow, r-hand, l-knee, l-foot, r-knee, r-foot
    [(0, 2), (0, 5), (0, 11), (-3, 3), (-5, 0), (3, 3), (5, 0), (-2, 14), (-4, 17), (2, 14), (4, 17)],
    [(0, 2), (0, 5), (0, 11), (-4, 6), (-8, 6), (4, 6), (8, 5), (-1, 14), (-1, 17), (3, 12), (2, 15)],
    [(-1, 2), (-1, 5), (0, 11), (-4, 8), (-6, 10), (2, 8), (5, 10), (-3, 14), (-6, 17), (2, 14), (3, 17)],
    [(1, 2), (1, 5), (1, 11), (-3, 7), (-5, 10), (4, 3), (6, 0), (0, 14), (-1, 17), (4, 14), (6, 17)],
]
BONES = [(1, 2), (1, 3), (3, 4), (1, 5), (5, 6), (2, 7), (7, 8), (2, 9), (9, 10)]
ENDS = [4, 6, 8, 10]


def scene_video_lens():
    """LLM Video Lens: dots follow a dancer on screen and leave onion-skin trails; Claude and Codex watch."""
    s = Scene("video-lens", 4.8, keep_clear=(64, 186))
    c = s.base
    c.box(96, 12, 48, 27, "metal_d")
    c.rect(98, 14, 44, 23, "screen")
    for y in (14, 35):                                  # film strip edges with sprocket holes
        c.rect(98, y, 44, 2, "K")
        for x in range(100, 141, 4):
            c.rect(x, y + (1 if y == 14 else 0), 2, 1, "sub")
    c.rect(117, 39, 6, 4, "metal_d")
    c.box(110, 43, 20, 2, "metal")
    c.merge(traveler(80, 47))
    ox, oy = 120, 16

    def pt(pose, j):
        return (ox + DANCE[pose][j][0], oy + DANCE[pose][j][1])

    frames = []
    for k in range(4):
        f = Canvas()
        for back, col in ((2, "win"), (1, "sub")):     # onion skin of the two previous poses
            q = (k - back) % 4
            for a, b in BONES:
                stroke(f, pt(q, a), pt(q, b), col, 1)
        for j in ENDS:                                  # trails from the last pose to this one
            stroke(f, pt((k - 1) % 4, j), pt(k, j), "orange", 1)
        for a, b in BONES:
            stroke(f, pt(k, a), pt(k, b), "white", 1)
        hx, hy = pt(k, 0)
        f.rect(hx - 1, hy - 1, 3, 3, "white")
        for j in ENDS:
            x, y = pt(k, j)
            f.set(x, y, "glyph")
            f.set(x + 1, y, "glyph")
        frames.append(f)
    s.flip(frames, 0.0, 4.8, 0.6)
    # Claude watches the screen and blinks, Codex's cursor blinks
    look = on_ground(claude_frame("left", "down", "stand", 0), 150, 47)
    blink = on_ground(claude_frame("blink", "down", "stand", 0), 150, 47)
    s.timeline([(0.0, look), (2.9, blink), (3.05, look)])
    prompt = on_ground(codex_frame("prompt", "stand", 0), 168, 47)
    off = on_ground(codex_frame("cursor_off", "stand", 0), 168, 47)
    s.flip([prompt, off], 0.0, 4.8, 0.6)
    rec = Canvas()
    rec.rect(138, 17, 2, 2, "red")
    s.flip([rec, Canvas()], 0.0, 4.8, 0.6)
    return s.svg("LLM Video Lens",
                 "Pixel-art night scene: a monitor framed like a film strip shows a dancer; dots follow the hands "
                 "and feet and leave fading onion-skin trails. The portfolio owner stands on the left; Claude and "
                 "Codex watch from the right.")


CARD_ART = [   # 6x5 pictures on the cards: leaf, cell, bolt, landscape
    ["..gg..", ".gggg.", "gggggg", ".gggg.", "...v.."],
    [".pppp.", "pprrpp", "pprrpp", "pppppp", ".pppp."],
    ["..mm..", ".mMMm.", "mMwwMm", ".mMMm.", "..mm.."],
    ["bbbbyy", "bbbbyy", "bbbbbb", "gggbbg", "gggggg"],
]


def scene_vision_data():
    """Vision data work: picture cards ride a belt through a scanner, get a check or a question mark."""
    dur = 6.0
    s = Scene("vision-data", dur, keep_clear=(34, 214))
    c = s.base
    c.rect(44, 40, 146, 1, "metal")                   # belt
    c.rect(44, 41, 146, 2, "metal_d")
    for x in range(46, 190, 6):
        c.set(x, 42, "K")
    for x in range(48, 190, 24):
        c.rect(x, 43, 2, 5, "metal_d")
    c.box(110, 20, 20, 5, "metal")                    # scanner arch
    c.rect(112, 25, 3, 15, "metal_d")
    c.rect(125, 25, 3, 15, "metal_d")
    c.box(117, 23, 6, 3, "dia_d")
    c.set(119, 24, "white")
    c.box(160, 18, 18, 12, "metal_d")                 # a monitor with a falling loss curve
    c.rect(161, 19, 16, 10, "screen")
    for i, y in enumerate((20, 21, 23, 24, 25, 26, 26, 27, 27, 27, 27, 27, 27, 27)):
        c.set(162 + i, y, "green")
    c.rect(168, 30, 2, 10, "metal_d")
    c.merge(traveler(146, 53))
    beam = Canvas()
    beam.rect(115, 26, 10, 14, "laser_glow")
    s.flip([beam, Canvas()], 0.0, dur, 0.25)
    x0, x1, row = 40, 184, 33
    t_belt, t_scan = 5.2, (128 - x0) / (x1 - x0) * 5.2
    for k, art in enumerate(CARD_ART):
        card = Canvas()
        card.box(0, 0, 8, 7, "white")
        for j, rowtxt in enumerate(art):
            for i, ch in enumerate(rowtxt):
                if ch != ".":
                    card.set(1 + i, 1 + j, {"g": "green", "v": "wood", "p": "flower1", "r": "red", "m": "metal",
                                            "M": "metal_d", "w": "white", "b": "blue", "y": "yellow"}[ch])
        ok = k != 2
        tag = Canvas()
        tag.box(2, -6, 5, 5, "green" if ok else "yellow")
        for x, y in (((3, -4), (4, -3), (5, -4)) if ok else ((4, -5), (5, -4), (4, -3), (4, -2))):
            tag.set(x, y, "white" if ok else "K")
        bin_x = 193 if ok else 206
        offset = k * dur / 4
        inner = shown_inner(dur, tag, rotate(dur, [(t_scan, t_belt)], offset))
        s.move(card, [(0.0, t_belt, (x0, row), (x1, row), "lin"),
                      (t_belt, dur, (x1, row), (bin_x, row + 9), "in")], offset=offset, inner=inner)
    front = Canvas()                                  # hopper and bins in front of the cards
    front.box(32, 27, 13, 14, "wood")
    front.rect(33, 28, 11, 2, "wood_d")
    for x, col in ((190, "green"), (203, "yellow")):
        front.box(x, 38, 12, 10, col)
        front.rect(x + 1, 39, 10, 1, "K")
    s.layers.append(paths(front))
    return s.svg("Vision data work",
                 "Pixel-art night workshop: picture cards leave a hopper on a conveyor belt and pass a scanner "
                 "arch; each comes out with a green check or a yellow question mark and drops into the matching "
                 "bin, while the portfolio owner watches beside a monitor with a falling loss curve.")


def scene_amr_arm():
    """AMR and robot arm: the AMR brings a crate, the arm lifts it onto rollers, the AMR goes for another."""
    s = Scene("amr-arm", 8.0, keep_clear=(56, 196))
    c = s.base
    c.rect(52, 41, 140, 9, "path")                    # concrete work pad
    c.rect(52, 41, 140, 1, "path_h")
    for x in range(52, 192, 10):
        c.rect(x, 42, 1, 8, "path_e")
    c.box(117, 26, 9, 16, "metal_d")                  # arm pedestal
    for y in (28, 33, 38):
        c.rect(118, y, 7, 1, "metal")
    c.box(132, 36, 44, 3, "metal")                    # roller table into a shed
    for x in range(134, 176, 4):
        c.set(x, 37, "K")
    for x in (134, 172):
        c.rect(x, 39, 2, 3, "metal_d")
    c.box(146, 16, 7, 5, "metal_d")                   # camera on a pole, watching the pick
    c.box(144, 17, 3, 3, "dia_d")
    c.rect(149, 21, 1, 15, "metal_d")
    front = Canvas()                                  # desk with a laptop for the owner, in front of the pad
    front.box(62, 48, 18, 4, "wood")
    front.rect(64, 52, 2, 2, "wood_d")
    front.rect(76, 52, 2, 2, "wood_d")
    front.box(66, 42, 11, 6, "metal_d")
    front.rect(67, 43, 9, 4, "screen")
    front.box(69, 44, 4, 2, "screen", "lit")
    front.merge(traveler(82, 53))
    shed = Canvas()
    shed.box(176, 24, 18, 18, "wall_m")
    for k in range(11):
        shed.rect(175 + k, 23 - k // 2, 20 - 2 * k, 1, "roof" if k % 3 else "roof_d")
    shed.rect(177, 32, 6, 10, "win")
    led = Canvas()
    led.set(151, 17, "red")
    shoulder = (121.5, 25.0)
    pick, hover, up, place = (106, 31), (106, 24), (121, 14), (135, 30)
    # AMR with a crate that is on board until the arm grips it
    amr = Canvas()
    amr.box(0, 3, 17, 5, "metal")
    amr.rect(1, 5, 15, 1, "teal")
    amr.rect(6, 1, 4, 2, "metal_d")
    for x in (2, 12):
        amr.rect(x, 8, 3, 2, "K")
    load = crate()
    station, away = (98, 33), (-24, 33)
    on_amr = shown_inner(8.0, shifted(load, 6, -3), [(0.0, 0.9), (5.0, 8.0)])
    s.move(amr, [(0.0, 2.8, station, station, "lin"), (2.8, 4.6, station, away, "in"),
                 (4.6, 5.0, away, away, "lin"), (5.0, 7.0, away, station, "out"),
                 (7.0, 8.0, station, station, "lin")], inner=on_amr)
    s.move(load, [(0.0, 2.8, (133, 32), (133, 32), "lin"), (2.8, 4.8, (133, 32), (179, 32), "in"),
                  (4.8, 8.0, (179, 32), (179, 32), "lin")], spans=[(2.8, 4.8)])
    # arm keyframes: (t, wrist, grip, holding)
    keys = [(0.0, pick, "open", False), (0.8, pick, "shut", True), (1.6, up, "shut", True),
            (2.4, place, "shut", True), (2.8, place, "open", False), (3.6, up, "open", False),
            (4.4, hover, "open", False), (7.4, hover, "open", False), (8.0, pick, "open", False)]
    frames, last = [], None
    t = 0.0
    while t < 8.0 - 1e-9:
        k = max(i for i, kk in enumerate(keys) if kk[0] <= t + 1e-9)
        a, b = keys[k], keys[min(k + 1, len(keys) - 1)]
        u = 0 if b[0] == a[0] else ease("inout", (t - a[0]) / (b[0] - a[0]))
        wrist = (a[1][0] + (b[1][0] - a[1][0]) * u, a[1][1] + (b[1][1] - a[1][1]) * u)
        key = (round(wrist[0]), round(wrist[1]), a[2], a[3])
        if key != last:
            frames.append((t, arm_frame(shoulder, key[:2], grip=key[2], load=load if key[3] else None)))
            last = key
        t += 0.125
    s.timeline(frames)
    s.layers.append(paths(shed) + paths(front))
    s.flip([led, Canvas()], 0.0, 8.0, 0.5)
    return s.svg("AMR and robot arm",
                 "Pixel-art night work pad: an AMR brings a crate to a yellow robot arm, the arm lifts it onto a "
                 "roller table that carries it into a shed, and the AMR leaves for the next one; a camera on a "
                 "pole watches while the portfolio owner checks a laptop.")


def scene_gpt_ros():
    """GPT-ROS: a typed command becomes parsed steps that drive a robot arm and a mobile robot."""
    s = Scene("gpt-ros", 8.0, keep_clear=(52, 196))
    c = s.base
    c.box(70, 40, 18, 4, "wood")                      # desk and laptop
    c.box(73, 34, 12, 6, "metal_d")
    c.rect(74, 35, 10, 4, "screen")
    c.merge(traveler(58, 47))
    c.box(104, 34, 7, 8, "teal")                      # relay box bridging the two ROS domains
    c.rect(105, 35, 5, 2, "screen")
    c.rect(107, 27, 1, 7, "metal_d")
    c.box(126, 40, 9, 5, "metal_d")                   # arm pedestal
    c.rect(52, 47, 150, 1, "path_e")                  # floor line the mobile robot drives on
    # chat bubble: the command is typed, then parsed into an ARM chip and a MOVE chip
    bubble = Canvas()
    bubble.box(62, 14, 34, 14, "white")
    for x, y in ((70, 28), (71, 29), (72, 30)):
        bubble.set(x, y, "K")
    s.base.merge(bubble)
    typed = []
    words = [(64, 16, 6), (71, 16, 4), (76, 16, 7), (84, 16, 5), (64, 19, 5), (70, 19, 8)]
    for n in range(len(words) + 1):
        f = Canvas()
        for x, y, w in words[:n]:
            f.rect(x, y, w, 2, "blue")
        typed.append(f)
    chips = Canvas()
    chips.box(64, 23, 13, 4, "yellow")
    chips.rect(66, 24, 9, 2, "K")
    chips.box(79, 23, 15, 4, "teal")
    chips.rect(81, 24, 11, 2, "K")
    typed[-1].merge(chips)
    keys = [(0.0, typed[-1])] + [(4.2 + 0.35 * n, typed[n]) for n in range(len(typed))]
    s.timeline(keys)
    # packets: laptop -> relay -> arm and robot
    dot = Canvas()
    dot.rect(0, 0, 2, 2, "lit")
    s.move(dot, [(0.0, 0.6, (86, 35), (104, 33), "lin"), (0.6, 8.0, (-9, -9), (-9, -9), "lin")], offset=-6.6)
    for target in ((124, 30), (150, 38)):
        s.move(dot, [(0.0, 0.7, (110, 31), target, "lin"), (0.7, 8.0, (-9, -9), (-9, -9), "lin")], offset=-7.3)
    antenna = Canvas()
    glow_disc(antenna, 107, 27, 2, "laser_glow")
    antenna.set(107, 26, "glyph")
    s.flip([antenna, Canvas()], 0.0, 8.0, 0.4)
    # robot arm picks a block and sets it down again; the mobile robot drives out and back, then speaks
    shoulder = (130.5, 39.0)
    block = crate("red")
    arm_keys = [(0.0, (138, 34), "open", False), (0.6, (138, 34), "shut", True), (1.6, (128, 24), "shut", True),
                (2.6, (138, 34), "shut", True), (3.0, (138, 34), "open", False), (3.6, (134, 26), "open", False),
                (8.0, (134, 26), "open", False)]
    frames, last, t = [], None, 0.0
    while t < 8.0 - 1e-9:
        k = max(i for i, kk in enumerate(arm_keys) if kk[0] <= t + 1e-9)
        a, b = arm_keys[k], arm_keys[min(k + 1, len(arm_keys) - 1)]
        u = 0 if b[0] == a[0] else ease("inout", (t - a[0]) / (b[0] - a[0]))
        wrist = (a[1][0] + (b[1][0] - a[1][0]) * u, a[1][1] + (b[1][1] - a[1][1]) * u)
        key = (round(wrist[0]), round(wrist[1]), a[2], a[3])
        if key != last:
            f = arm_frame(shoulder, key[:2], l1=9, l2=8, grip=key[2], load=block if key[3] else None, col="orange")
            if not key[3]:
                f.merge(shifted(block, 136, 39))
            frames.append((t, f))
            last = key
        t += 0.125
    s.timeline(frames)
    bot = Canvas()
    bot.box(0, 3, 12, 6, "metal")
    bot.rect(1, 4, 10, 1, "teal")
    bot.box(3, 0, 6, 3, "metal_d")
    bot.set(6, 1, "glyph")
    for x in (1, 8):
        bot.rect(x, 9, 3, 1, "K")
    home, out = (150, 37), (178, 37)
    s.move(bot, [(0.0, 1.6, home, out, "inout"), (1.6, 2.2, out, out, "lin"), (2.2, 3.8, out, home, "inout"),
                 (3.8, 8.0, home, home, "lin")])
    say = Canvas()
    for k, h in enumerate((1, 3, 2, 3, 1)):
        say.rect(166 + 2 * k, 31 - h, 1, 2 * h - 1, "glyph")
    s.show(say, [(4.0, 5.6)])
    return s.svg("GPT-ROS",
                 "Pixel-art night scene: the portfolio owner types a command at a laptop; a chat bubble turns it "
                 "into an arm step and a move step, which travel through a relay box to an orange robot arm that "
                 "lifts a red block and a mobile robot that drives out, comes back and speaks.")



def place_tree(c, x, y, kind):
    for (i, j), col in tree(kind).px.items():
        c.px[(x + i, y + j)] = col


def walker(s, segments, spans, extra=None):
    """A pedestrian following segments, legs alternating while visible; extra is drawn with it."""
    frames = {}
    for name, rows in PED.items():
        f = sprite(rows)
        if extra is not None:
            f.merge(extra)
        frames[name] = f
    steps = cycle(2, 0.0, s.dur, 0.25)
    for k, name in enumerate(("a", "b")):
        vis = [(max(a, c0), min(b, c1)) for a, b in spans for c0, c1 in steps[k] if max(a, c0) < min(b, c1)]
        s.move(frames[name], segments, spans=vis)


def scene_carla():
    """Carla right-turn helper: a detector boxes the pedestrian on the crosswalk; the turn light waits for them."""
    s = Scene("carla", 8.0, trees=False)
    c = s.base
    for x, w, h, seed in ((8, 15, 9, 11), (28, 12, 7, 12), (198, 12, 8, 13), (216, 17, 10, 14)):
        house(c, s.layers, x, 42, w, h, seed)
    for x, kind in ((50, "round"), (60, "pine"), (184, "pine")):
        place_tree(c, x, 42, kind)
    road(c, 42)
    for y in range(45, 54, 2):
        c.rect(126, y, 16, 1, "star_d")
    c.rect(123, 49, 1, 5, "white")
    c.rect(150, 26, 1, 16, "metal_d")                 # right-turn sign and the alert light built in the project
    c.box(146, 19, 9, 7, "blue")
    for x, y in ((148, 24), (148, 23), (148, 22), (149, 21), (150, 21), (151, 21), (152, 20), (152, 22), (153, 21)):
        c.set(x, y, "white")
    c.box(152, 30, 6, 9, "screen")
    for y in (31, 35):
        c.rect(154, y, 2, 2, "win")
    lamp_r, lamp_g = Canvas(), Canvas()
    glow_disc(lamp_r, 155, 32, 3, "nv_glow")
    lamp_r.rect(154, 31, 2, 2, "red")
    glow_disc(lamp_g, 155, 36, 3, "laser_glow")
    lamp_g.rect(154, 35, 2, 2, "green")
    s.show(lamp_r, [(0.0, 3.2), (6.6, 8.0)])
    s.show(lamp_g, [(3.2, 6.6)])
    box = Canvas()                                    # detection box with a label tab, around the walker
    for x in range(-3, 8):
        for y in (-3, 10):
            if x % 2 == 0:
                box.set(x, y, "lit")
    for y in range(-3, 11):
        for x in (-3, 7):
            if y % 2 == 0:
                box.set(x, y, "lit")
    box.rect(-3, -5, 6, 2, "lit")
    walker(s, [(0.0, 3.0, (131, 40), (131, 54), "lin"), (3.0, 6.5, (131, 54), (131, 54), "lin"),
               (6.5, 8.0, (131, 33), (131, 40), "lin")], [(0.0, 3.0), (6.5, 8.0)], extra=box)
    wait = (103, 43)
    s.move(sprite(ICONS["car"]), [(0.0, 3.4, wait, wait, "lin"), (3.4, 5.4, wait, (250, 43), "in"),
                                  (5.4, 5.8, (-20, 43), (-20, 43), "lin"), (5.8, 7.8, (-20, 43), wait, "out"),
                                  (7.8, 8.0, wait, wait, "lin")])
    hud = Canvas()                                    # simulator view brackets
    for x, y, dx, dy in ((66, 14, 1, 1), (174, 14, -1, 1), (66, 53, 1, -1), (174, 53, -1, -1)):
        for k in range(5):
            hud.set(x + dx * k, y, "glyph")
            hud.set(x, y + dy * k, "glyph")
    s.layers.append(paths(hud))
    return s.svg("Carla right-turn alert",
                 "Pixel-art simulator view of a night street: a dashed detection box follows a pedestrian across "
                 "the crosswalk while a car waits at the stop line; when the crossing is clear the alert light "
                 "turns green and the car drives on, and the next car rolls in.")


PIPS = {1: [(2, 2)], 2: [(1, 1), (3, 3)], 3: [(1, 1), (2, 2), (3, 3)], 4: [(1, 1), (3, 1), (1, 3), (3, 3)],
        5: [(1, 1), (3, 1), (2, 2), (1, 3), (3, 3)], 6: [(1, 1), (3, 1), (1, 2), (3, 2), (1, 3), (3, 3)]}


def scene_board_games():
    """Board game EDA: a die tumbles beside meeples while a bar chart of game trends grows on an easel."""
    s = Scene("board-games", 6.0, keep_clear=(62, 188))
    c = s.base
    c.box(76, 36, 44, 4, "wood")                      # table
    for x in (79, 115):
        c.rect(x, 40, 2, 7, "wood_d")
    c.box(80, 21, 18, 15, "orange")                   # a game box standing up
    c.rect(81, 23, 16, 2, "yellow")
    c.rect(83, 27, 12, 7, "roof_d")
    pawn = [".x.", "xxx", ".x.", "xxx", "xxx"]
    for x, col in ((101, "red"), (105, "blue"), (109, "green")):
        c.merge(sprite([r.replace("x", {"red": "r", "blue": "b", "green": "g"}[col]) for r in pawn], x, 30))
    ix, iy, iw, ih = easel(c, 128, 12, 38, 26)
    c.rect(ix + 2, iy + ih - 3, iw - 4, 1, "sub")     # axes
    c.rect(ix + 2, iy + 2, 1, ih - 4, "sub")
    heights = (6, 9, 8, 13, 17, 20)
    def bars(frac):
        f = Canvas()
        for k, h in enumerate(heights):
            hh = max(0, round(h * frac))
            f.rect(ix + 5 + 5 * k, iy + ih - 3 - hh, 3, hh, ("blue", "teal", "green", "yellow", "orange", "red")[k])
        return f
    full = bars(1.0)
    trend = Canvas()
    pts = [(ix + 6 + 5 * k, iy + ih - 5 - h) for k, h in enumerate(heights)]
    for a, b in zip(pts, pts[1:]):
        stroke(trend, a, b, "white", 1)
    full_line = Canvas()
    full_line.merge(full)
    full_line.merge(trend)
    grow = [bars(f) for f in (0.0, 0.25, 0.5, 0.75)]
    s.timeline([(0.0, full_line), (3.6, grow[0]), (3.9, grow[1]), (4.2, grow[2]), (4.5, grow[3]), (4.8, full),
                (5.3, full_line)])
    dice = []
    for face in (3, 5, 2, 6, 1, 4):
        d = Canvas()
        d.box(0, 0, 5, 5, "white")
        for x, y in PIPS[face]:
            d.set(x, y, "K")
        dice.append(d)
    rest = dice[3]
    keys = [(0.0, shifted(rest, 112, 31))]
    for k, d in enumerate(dice):
        keys.append((3.6 + 0.15 * k, shifted(d, 112 + (k % 2), 31 - (2 if k % 2 == 0 else 0))))
    keys.append((3.6 + 0.15 * len(dice), shifted(rest, 112, 31)))
    s.timeline(keys)
    s.base.merge(traveler(122, 53))
    return s.svg("Board game trends",
                 "Pixel-art night scene: a die tumbles on a table beside a game box and three pawns, while a bar "
                 "chart of board game trends grows on an easel and a trend line is drawn over it.")


def ring(r_out, r_in, col):
    c = Canvas()
    for y in range(-r_out, r_out + 1):
        for x in range(-r_out, r_out + 1):
            d = x * x + y * y
            if r_in * r_in < d <= r_out * r_out + r_out:
                c.set(x, y, col)
    return c


def scene_chest_ct():
    """Chest CT: the couch slides through the gantry while lights circle it; the scan line sweeps the lungs."""
    s = Scene("chest-ct", 6.0, keep_clear=(62, 190))
    c = s.base
    cx, cy = 112, 30
    c.merge(shifted(outlined(ring(14, 8, "wall")), cx, cy))
    c.merge(shifted(ring(8, -1, "screen"), cx, cy))
    c.box(105, 44, 15, 3, "wall_m")                   # gantry foot
    c.rect(72, 34, 80, 2, "metal")                    # couch, level with the middle of the bore
    for x in (80, 140):
        c.box(x, 36, 8, 9, "metal_d")
    patient = Canvas()
    patient.rect(0, 0, 20, 3, "blue")
    patient.rect(1, 0, 18, 1, "dia_d")
    patient.rect(20, 0, 3, 3, "skin")
    patient.set(21, 0, "hair")
    patient = outlined(patient)
    s.move(patient, [(0.0, 2.6, (100, 30), (100, 30), "lin"), (2.6, 4.2, (100, 30), (76, 30), "inout"),
                     (4.2, 4.8, (76, 30), (76, 30), "lin"), (4.8, 6.0, (76, 30), (100, 30), "inout")])
    s.layers.append(paths(shifted(outlined(ring(14, 8, "wall")), cx, cy)))
    lights = []
    for k in range(8):
        f = Canvas()
        a = k * math.pi / 4
        x, y = round(cx + 11 * math.cos(a)), round(cy + 11 * math.sin(a))
        f.rect(x, y, 1, 1, "glyph")
        glow_disc(f, x, y, 1, "laser_glow")
        lights.append(f)
    s.flip(lights, 0.0, 6.0, 0.15)
    c.box(146, 14, 26, 21, "metal_d")                 # viewer with the lungs
    c.rect(147, 15, 24, 19, "screen")
    c.merge(sprite(ICONS["lungs"], 152, 18, edge=False))
    c.rect(158, 35, 2, 9, "metal_d")
    sweep = []
    for y in range(18, 31, 2):
        f = Canvas()
        f.rect(149, y, 20, 1, "glyph")
        sweep.append(f)
    s.flip(sweep, 0.0, 2.6, 2.6 / len(sweep))
    badge = Canvas()
    badge.box(164, 29, 6, 4, "green")
    badge.set(166, 31, "white")
    badge.set(167, 30, "white")
    s.show(badge, [(2.6, 6.0)])
    s.base.merge(traveler(176, 53))
    return s.svg("Chest CT classification",
                 "Pixel-art night scene: a patient on a couch slides through a CT gantry with lights circling "
                 "inside it, while a scan line sweeps over a pair of lungs on a viewer and a result badge appears.")


def hanoi_moves(n, a, b, c):
    if n == 0:
        return []
    return hanoi_moves(n - 1, a, c, b) + [(a, c)] + hanoi_moves(n - 1, b, a, c)


def scene_hanoi():
    """Tower of Hanoi: the arm moves three discs from the left peg to the right and back, one rule-abiding move a second."""
    moves_ = hanoi_moves(3, 0, 1, 2) + hanoi_moves(3, 2, 1, 0)
    dur = float(len(moves_))
    s = Scene("hanoi", dur, keep_clear=(70, 184))
    c = s.base
    c.box(126, 17, 5, 23, "metal_d")                  # arm column behind the middle peg
    c.box(98, 40, 60, 4, "wood")
    for x in (100, 152):                              # ArUco markers on the board's front
        c.box(x, 41, 4, 3, "white")
        c.set(x + 1, 42, "K")
        c.set(x + 2, 41, "K")
    pegs = (112, 128, 144)
    for x in pegs:
        c.rect(x, 26, 1, 14, "wood_d")
    c.rect(90, 16, 1, 24, "metal_d")                  # camera on a pole
    c.box(88, 12, 6, 5, "metal_d")
    c.box(92, 13, 3, 3, "dia_d")
    widths = {0: 11, 1: 9, 2: 7}
    cols = {0: "red", 1: "yellow", 2: "blue"}
    stacks = [[0, 1, 2], [], []]
    shoulder = (128.5, 16.0)
    hover = 19
    keys, held = [], []
    for k, (a, b) in enumerate(moves_):
        t0 = float(k)
        d = stacks[a][-1]
        pick_y = 35 - 3 * (len(stacks[a]) - 1)
        place_y = 35 - 3 * len(stacks[b])
        keys += [(t0, (pegs[a], hover), "open", None), (t0 + 0.15, (pegs[a], pick_y), "shut", d),
                 (t0 + 0.25, (pegs[a], pick_y), "shut", d), (t0 + 0.4, (pegs[a], hover), "shut", d),
                 (t0 + 0.7, (pegs[b], hover), "shut", d), (t0 + 0.85, (pegs[b], place_y), "open", None),
                 (t0 + 0.9, (pegs[b], place_y), "open", None)]
        held.append((t0 + 0.15, t0 + 0.85, d, a, b))
        stacks[b].append(stacks[a].pop())
    keys.append((dur, (pegs[0], hover), "open", None))
    path = wrist_path(keys, 0.125)
    arm_frames, last = [], None
    for t, w, grip, _ in path:
        key = (w, grip)
        if key != last:
            arm_frames.append((t, arm_frame(shoulder, w, l1=13, l2=13, grip=grip, col="white")))
            last = key
    # each disc: on its peg, or hanging from the gripper while held
    stacks = [[0, 1, 2], [], []]
    where = {0: (0, 0), 1: (0, 1), 2: (0, 2)}
    events = []
    for t_on, t_off, d, a, b in held:
        events.append((t_on, t_off, d, b, len(stacks[b])))
        stacks[b].append(stacks[a].pop())
    disc_frames = {d: [] for d in widths}
    for t, w, grip, _ in path:
        for d in widths:
            hold = [e for e in events if e[2] == d and e[0] <= t + 1e-9 < e[1]]
            if hold:
                pos = (w[0] - (widths[d] - 1) // 2, w[1] + 2)
            else:
                done = [e for e in events if e[2] == d and e[1] <= t + 1e-9]
                peg, level = (done[-1][3], done[-1][4]) if done else where[d]
                pos = (pegs[peg] - (widths[d] - 1) // 2, 37 - 3 * level)
            disc_frames[d].append((t, pos))
    for d in widths:
        disc = Canvas()
        disc.rect(0, 0, widths[d], 2, cols[d])
        disc.rect(0, 2, widths[d], 1, "K")
        disc.set(1, 0, "white")
        s.move_frames(disc, disc_frames[d])
    s.timeline(arm_frames)
    led = Canvas()
    led.set(89, 13, "red")
    s.flip([led, Canvas()], 0.0, dur, 0.5)
    s.base.merge(traveler(164, 53))
    return s.svg("Tower of Hanoi with a robot arm",
                 "Pixel-art night scene: a white robot arm moves three coloured discs between three pegs by the "
                 "Tower of Hanoi rules, from the left peg to the right and back, watched by a camera on a pole; "
                 "markers sit on the board's corners.")


def scene_loan():
    """Loan default: applicant records scroll past with green or red flags; a scale weighs coins."""
    s = Scene("loan", 6.0, keep_clear=(56, 192))
    c = s.base
    ix, iy, iw, ih = easel(c, 92, 12, 52, 28)
    rng = random.Random("loan")
    records = [(rng.randrange(8, 22), rng.randrange(4, 12), rng.random() < 0.3) for _ in range(9)]
    frames = []
    for k in range(len(records)):
        f = Canvas()
        for j in range(8):
            w1, w2, risky = records[(k + j) % len(records)]
            y = iy + 1 + 3 * j
            f.rect(ix + 2, y, 2, 2, "skin")
            f.set(ix + 2, y, "hair")
            f.rect(ix + 6, y, w1, 1, "sub")
            f.rect(ix + 6, y + 1, w2, 1, "star_d")
            f.rect(ix + iw - 5, y, 2, 2, "red" if risky else "green")
            if risky:
                f.rect(ix + iw - 9, y, 3, 1, "red")
        frames.append(f)
    s.flip(frames, 0.0, 6.0, 6.0 / len(frames))
    c.rect(74, 22, 2, 23, "metal_d")                  # balance scale
    c.box(70, 44, 10, 2, "metal")
    tilt = []
    for d in (-2, 2):
        f = Canvas()
        stroke(f, (62, 22 + d), (88, 22 - d), "metal", 1)
        for px_, py_ in ((62, 22 + d), (88, 22 - d)):
            stroke(f, (px_, py_), (px_ - 3, py_ + 5), "metal_d", 1)
            stroke(f, (px_, py_), (px_ + 3, py_ + 5), "metal_d", 1)
            f.rect(px_ - 4, py_ + 6, 9, 1, "metal")
        for k in range(3 if d < 0 else 2):
            f.rect(59, 22 + d + 4 - k, 5, 1, "yellow")
        for k in range(2 if d < 0 else 3):
            f.rect(86, 22 - d + 4 - k, 5, 1, "yellow")
        tilt.append(f)
    s.flip(tilt, 0.0, 6.0, 1.5)
    s.base.merge(sprite(ICONS["coins"], 60, 47))
    s.base.merge(traveler(150, 53))
    return s.svg("Loan default prediction",
                 "Pixel-art night scene: rows of applicant records scroll past on a board, each with a green or "
                 "red status light, while a balance scale with coin stacks tips back and forth.")


def truck(face):
    c = Canvas()
    c.box(0, 0, 11, 7, "wall")
    c.rect(1, 1, 9, 1, "wall_m")
    cab = 11 if face > 0 else -4
    c.box(cab, 2, 5, 5, "blue")
    c.rect(cab + (2 if face > 0 else 1), 3, 2, 2, "glyph")
    for x in (2, 8):
        c.rect(x, 7, 3, 2, "K")
    c.rect(cab + 1, 7, 3, 2, "K")
    return outlined(c)


def scene_traffic():
    """Traffic forecast: trucks run both ways under a billboard where the forecast line keeps extending."""
    s = Scene("traffic", 6.0, trees=False)
    c = s.base
    for x, kind in ((20, "pine"), (34, "round"), (190, "round"), (206, "pine"), (222, "round")):
        place_tree(c, x, 41, kind)
    road(c, 42)
    for x in (100, 140):
        c.rect(x, 33, 2, 9, "metal_d")
    c.box(84, 12, 74, 22, "metal_d")
    c.rect(85, 13, 72, 20, "screen")
    c.rect(87, 30, 68, 1, "sub")
    hist = [24 - round(4 * math.sin(i / 3.0) + 2 * math.sin(i / 1.3) + i / 10) for i in range(42)]
    for i in range(41):
        stroke(c, (88 + i, hist[i]), (89 + i, hist[i + 1]), "glyph", 1)
    now = 129
    fc = [hist[-1] + round(-4 * math.sin((i + 42) / 3.0) + 4 * math.sin(41 / 3.0)) for i in range(24)]
    reveal = []
    for n in (4, 8, 12, 16, 20, 24):
        f = Canvas()
        for i in range(n):
            if i % 2 == 0:
                f.rect(now + i, fc[i], 1, 1, "orange")
                f.set(now + i, fc[i] - 2, "win")
                f.set(now + i, fc[i] + 2, "win")
        reveal.append(f)
    s.timeline([(0.0, reveal[-1])] + [(3.0 + 0.4 * k, f) for k, f in enumerate(reveal)])
    marker = Canvas()
    marker.rect(now, 14, 1, 16, "sub")
    s.flip([marker, Canvas()], 0.0, 6.0, 0.5)
    for k, (lane, face, speed_off) in enumerate(((49, 1, 0.0), (49, 1, 3.0), (43, -1, 1.5), (43, -1, 4.5))):
        a, b = ((-18, lane), (244, lane)) if face > 0 else ((244, lane), (-18, lane))
        s.move(truck(face), [(0.0, 6.0, a, b, "lin")], offset=speed_off)
    s.base.merge(traveler(66, 42))
    return s.svg("Freight traffic forecast",
                 "Pixel-art night highway: trucks run both ways under a billboard that plots past freight "
                 "traffic as a solid line and keeps extending a dotted forecast from the marked present.")


def scene_personal_llm():
    """Personal LLM setup: a GPU box trains (fans spin, loss falls) and a small robot answers in Korean."""
    s = Scene("personal-llm", 6.0, keep_clear=(60, 192))
    c = s.base
    c.box(86, 38, 66, 4, "wood")                      # desk
    for x in (88, 148):
        c.rect(x, 42, 2, 6, "wood_d")
    c.box(90, 16, 16, 22, "metal_d")                  # GPU tower
    c.rect(91, 17, 14, 1, "metal")
    for y in (24, 32):
        c.merge(shifted(ring(4, 0, "K"), 98, y))
        c.merge(shifted(ring(3, 0, "screen"), 98, y))
    fans = []
    for k in range(2):
        f = Canvas()
        for y in (24, 32):
            for d in range(1, 4):
                if k == 0:
                    f.set(98 + d, y, "metal")
                    f.set(98 - d, y, "metal")
                    f.set(98, y + d, "metal")
                    f.set(98, y - d, "metal")
                else:
                    f.set(98 + d, y + d, "metal")
                    f.set(98 - d, y - d, "metal")
                    f.set(98 + d, y - d, "metal")
                    f.set(98 - d, y + d, "metal")
        fans.append(f)
    s.flip(fans, 0.0, 6.0, 0.125)
    leds = Canvas()
    for x in range(92, 104, 3):
        leds.set(x, 19, "green")
    s.flip([leds, Canvas()], 0.0, 6.0, 0.4)
    c.box(112, 16, 32, 20, "metal_d")                 # monitor with the loss curve and a LoRA adapter
    c.rect(113, 17, 30, 18, "screen")
    c.rect(126, 36, 4, 2, "metal_d")
    c.box(115, 19, 9, 6, "metal")
    c.rect(116, 20, 7, 1, "metal_d")
    loss = [(127 + i, 19 + round(13 * (1 - math.exp(-i / 4)))) for i in range(15)]
    curves = []
    for n in (3, 6, 9, 12, 15):
        f = Canvas()
        for a, b in zip(loss[:n], loss[1:n]):
            stroke(f, a, b, "green", 1)
        curves.append(f)
    s.timeline([(0.0, curves[-1])] + [(3.4 + 0.3 * k, f) for k, f in enumerate(curves)])
    adapter = Canvas()
    adapter.box(0, 0, 4, 4, "orange")
    s.move(adapter, [(0.0, 3.4, (124, 20), (124, 20), "lin"), (3.4, 3.5, (114, 28), (114, 28), "lin"),
                     (3.5, 4.4, (114, 28), (124, 20), "inout"), (4.4, 6.0, (124, 20), (124, 20), "lin")])
    for x in range(144, 160, 2):                      # cable to the robot
        c.set(x, 40, "K")
    bot = Canvas()
    bot.box(0, 0, 9, 7, "metal")
    bot.rect(2, 2, 2, 2, "glyph")
    bot.rect(5, 2, 2, 2, "glyph")
    bot.rect(4, -2, 1, 2, "metal_d")
    bot.box(1, 7, 7, 6, "metal_d")
    bot.rect(2, 13, 2, 2, "K")
    bot.rect(5, 13, 2, 2, "K")
    c.merge(shifted(outlined(bot), 158, 33))
    bubble = Canvas()
    bubble.box(166, 20, 13, 10, "white")
    bubble.set(167, 30, "K")
    bubble.set(166, 31, "K")
    glyph(bubble, "ga", 169, 22, "K")
    s.show(bubble, [(0.0, 3.2), (4.6, 6.0)])
    s.base.merge(traveler(74, 53))
    return s.svg("Personal LLM setup",
                 "Pixel-art night desk: a GPU tower with spinning fans trains a model, a monitor shows a falling "
                 "loss curve as a small orange adapter clicks onto the model block, and a little robot at the "
                 "end of a cable answers with the Korean syllable 'ga'.")


HANDS = {
    "fist": [".xxxx....", "xxxxxx...", "xxxxxxx..", "xxxxxxx..", ".xxxxx...", "..xxx....", "..xxx...."],
    "open": ["x.x.x.x..", "x.x.x.x..", "xxxxxxx..", "xxxxxxx.x", "xxxxxxxx.", ".xxxxxx..", "..xxxx..."],
    "peace": [".x...x...", ".x...x...", "..x.x....", "..xxx....", ".xxxxx...", ".xxxxx...", "..xxx...."],
}


def scene_competitions():
    """Three competitions: hand gestures to classify, a radar antenna to tune, comments to filter."""
    s = Scene("competitions", 6.0, keep_clear=(56, 194))
    c = s.base
    for x in range(62, 180):                          # bunting string
        c.set(x, 12 + round(2 * math.sin(math.pi * (x - 62) / 118)), "metal_d")
    flags = []
    for k in range(2):
        f = Canvas()
        for i, x in enumerate(range(66, 178, 8)):
            y = 13 + round(2 * math.sin(math.pi * (x - 62) / 118))
            col = ("red", "yellow", "teal", "orange")[i % 4]
            for j in range(4):
                f.rect(x + j // 2 + (k if j > 1 else 0), y + j, 4 - j, 1, col)
        flags.append(f)
    s.flip(flags, 0.0, 6.0, 0.6)
    boards = [easel(c, x, 19, 26, 18) for x in (68, 107, 146)]
    (ax, ay, _, _), (bx, by, _, _), (cx, cy, cw, _) = boards
    hands = []
    for name in ("fist", "open", "peace"):
        f = Canvas()
        for j, row in enumerate(HANDS[name]):
            for i, ch in enumerate(row):
                if ch == "x":
                    f.set(ax + 8 + i, ay + 4 + j, "skin")
        hands.append(outlined(f))
    s.flip(hands, 0.0, 6.0, 0.8)
    dishes = []
    for d in (-2, 0, 2):
        f = Canvas()
        f.rect(bx + 11, by + 9, 2, 7, "metal_d")
        for i in range(-4, 5):
            f.set(bx + 12 + i, by + 6 + round(i * i / 6) + (d * i) // 4, "metal")
        f.set(bx + 12 + d, by + 2, "glyph")
        stroke(f, (bx + 12, by + 7), (bx + 12 + d, by + 3), "metal_d", 1)
        dishes.append(f)
    s.flip(dishes + [dishes[1]], 0.0, 6.0, 0.5)
    rows_ = []
    for k in range(3):
        f = Canvas()
        for j in range(3):
            y = cy + 2 + 5 * j
            bad = j == 1 and k > 0
            f.box(cx + 2, y, cw - 4, 4, "red" if bad else "white")
            f.rect(cx + 4, y + 1, cw - 12, 1, "K" if not bad else "white")
            if bad and k == 2:
                stroke(f, (cx + 2, y), (cx + cw - 3, y + 3), "K", 1)
        rows_.append(f)
    s.timeline([(0.0, rows_[2]), (2.0, rows_[0]), (3.2, rows_[1]), (4.0, rows_[2])])
    s.base.merge(traveler(116, 53))
    return s.svg("Three competitions",
                 "Pixel-art night fair under bunting: one board flips through hand gestures, one shows a radar "
                 "dish swinging, and one shows comments where a rude one turns red and gets struck out.")


def scene_korean_stt():
    """Korean speech recognition: a voice goes into a container and comes out as Korean syllables."""
    s = Scene("korean-stt", 6.0, keep_clear=(54, 192))
    c = s.base
    c.merge(traveler(64, 47))
    c.merge(sprite(ICONS["mic"], 78, 28))
    c.rect(82, 40, 1, 7, "metal_d")
    c.rect(79, 47, 7, 1, "metal_d")
    waves = []
    for r in (3, 6, 9):                               # sound arcs travelling from the mic to the container
        f = Canvas()
        for i in range(-r // 2, r // 2 + 1):
            if i % 2 == 0:
                f.set(86 + r - abs(i) // 2, 33 + i, "glyph")
        waves.append(f)
    s.flip(waves, 0.0, 6.0, 0.3)
    c.box(100, 22, 42, 20, "blue")                    # container running the recogniser
    for x in range(102, 140, 3):
        c.rect(x, 23, 1, 18, "codex_d")
    c.rect(100, 22, 42, 1, "K")
    c.box(106, 26, 22, 8, "screen")
    bars = []
    rng = random.Random("stt")
    heights = [rng.randrange(1, 4) for _ in range(30)]
    for k in range(4):
        f = Canvas()
        for i in range(10):
            h = heights[(i + 3 * k) % 30]
            f.rect(108 + 2 * i, 30 - h, 1, 2 * h, "green")
        bars.append(f)
    s.flip(bars, 0.0, 6.0, 0.25)
    ix, iy, iw, ih = easel(c, 150, 16, 28, 20, "white")
    texts = []
    for n in range(4):
        f = Canvas()
        for k, name in enumerate(("ga", "na", "da")[:n]):
            glyph(f, name, ix + 2 + 8 * k, iy + 3, "K")
        if n == 3:
            f.rect(ix + 2, iy + 12, 18, 1, "sub")
        texts.append(f)
    s.timeline([(0.0, texts[3]), (3.0, texts[0]), (3.6, texts[1]), (4.2, texts[2]), (4.8, texts[3])])
    dot = Canvas()
    dot.rect(0, 0, 2, 2, "lit")
    for k in range(3):
        s.move(dot, [(0.0, 1.0, (142, 30), (150, 26), "lin"), (1.0, 6.0, (-9, -9), (-9, -9), "lin")],
               offset=-(2.8 + 0.6 * k))
    return s.svg("Korean speech recognition",
                 "Pixel-art night scene: the portfolio owner speaks into a microphone, sound waves go into a "
                 "blue container whose window shows a moving waveform, and Korean syllables appear one by one "
                 "on a board beside it.")



def scene_notes():
    """Study notes: a desk under a lamp beside a small library, with lines being written in a notebook."""
    s = Scene("notes", 6.0, trees=False)
    c = s.base
    house(c, s.layers, 150, 44, 26, 15, "library")
    for x, kind in ((40, "pine"), (54, "round"), (196, "round"), (210, "pine"), (226, "round")):
        place_tree(c, x, 42, kind)
    c.box(84, 38, 58, 4, "wood")                      # desk
    for x in (87, 137):
        c.rect(x, 42, 2, 8, "wood_d")
    for k, (w, col) in enumerate(((16, "red"), (14, "teal"), (15, "yellow"), (13, "blue"), (16, "green"))):
        c.box(88 + (16 - w) // 2, 34 - 3 * k, w, 3, col)  # a stack of books
        c.rect(90 + (16 - w) // 2, 35 - 3 * k, 2, 1, "lit")
    c.box(108, 33, 22, 5, "white")                    # open notebook
    c.rect(118, 33, 1, 5, "sub")
    c.rect(133, 25, 1, 13, "metal_d")                 # desk lamp
    c.rect(129, 24, 5, 1, "metal_d")
    c.box(124, 24, 7, 4, "metal")
    c.rect(125, 28, 5, 1, "lit")
    glow = Canvas()                                   # a pool of light on the notebook
    for y in range(29, 38):
        half = 2 + (y - 29) // 2
        glow.rect(127 - half, y, 2 * half + 1, 1, "glow")
    s.layers.append(paths(glow))
    mug = Canvas()
    mug.box(137, 34, 4, 4, "orange")
    mug.set(141, 35, "K")
    c.merge(mug)
    steam = []
    for k in range(3):
        f = Canvas()
        for j in range(3):
            f.set(138 + (j + k) % 2, 31 - j, "smoke")
        steam.append(f)
    s.flip(steam, 0.0, 6.0, 0.4)
    lines = []
    for n in range(5):
        f = Canvas()
        for j in range(n):
            f.rect(109 if j < 3 else 120, 34 + (j % 3), 8 if j % 3 != 2 else 6, 1, "sub")
        lines.append(f)
    s.timeline([(0.0, lines[4])] + [(3.0 + 0.5 * k, f) for k, f in enumerate(lines)])
    s.base.merge(traveler(70, 50))
    return s.svg("Study notes",
                 "Pixel-art night study corner: a desk with a stack of books, an open notebook filling with lines "
                 "under a desk lamp and a steaming mug, beside a small lit library.")


def chalkboard(seed, dur):
    """The shared stage for study topics: a chalkboard on the hill, books and the owner beside it."""
    s = Scene(seed, dur, keep_clear=(60, 186))
    ix, iy, iw, ih = easel(s.base, 86, 12, 68, 28, "g2")
    for k, (w, col) in enumerate(((10, "red"), (9, "blue"), (11, "yellow"))):
        s.base.box(160 + (11 - w) // 2, 43 - 3 * k, w, 3, col)
    s.base.merge(traveler(68, 50))
    stick = Canvas()                                  # pointer from the owner's hand to the board
    stroke(stick, (79, 42), (88, 34), "wood", 1)
    s.base.merge(stick)
    return s, (ix, iy, iw, ih)


def scene_quality():
    s, (ix, iy, iw, ih) = chalkboard("quality", 6.0)
    mid, ucl, lcl = iy + 13, iy + 5, iy + 21
    for x in range(ix + 4, ix + iw - 10):
        s.base.set(x, mid, "star_d")
        if x % 3:
            s.base.set(x, ucl, "red")
            s.base.set(x, lcl, "red")
    s.base.merge(sprite(ICONS["shield"], ix + iw - 9, iy + 2, edge=False))
    rng = random.Random("quality")
    vals = [mid + rng.randrange(-5, 6) for _ in range(40)]
    vals[30] = ucl - 2                                # one point breaks the limit
    frames = []
    for k in range(16):
        f = Canvas()
        window = vals[k:k + 24]
        for i, v in enumerate(window):
            x = ix + 4 + 2 * i
            f.rect(x, v, 1, 1, "white")
            if i:
                stroke(f, (x - 2, window[i - 1]), (x, v), "star", 1)
            if v < ucl:
                glow_disc(f, x, v, 2, "nv_glow")
                f.set(x, v, "red")
        frames.append(f)
    s.flip(frames, 0.0, 6.0, 6.0 / len(frames))
    return s.svg("Quality and reliability",
                 "Pixel-art night chalkboard with a control chart: points scroll along between red control "
                 "limits, one breaks the upper limit and glows red, and a shield sits in the corner.")


def scene_supervised():
    s, (ix, iy, iw, ih) = chalkboard("supervised", 6.0)
    rng = random.Random("supervised")
    pts = []
    for _ in range(26):
        x, y = rng.randrange(ix + 4, ix + iw - 4), rng.randrange(iy + 3, iy + ih - 3)
        cls = (x - ix) * 0.4 + (y - iy) > 22
        pts.append((x, y, cls))
    for x, y, cls in pts:
        if cls:
            for dx, dy in ((0, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                s.base.set(x + dx, y + dy, "flower1")
        else:
            s.base.rect(x - 1, y - 1, 2, 2, "lit")
    angles = [0.9, 0.2, -0.6, -0.35, -0.45, -0.4]
    frames = []
    for a in angles:
        f = Canvas()
        cx, cy = ix + iw / 2, iy + ih / 2
        for k in range(-40, 41):
            x, y = cx + k * math.cos(a), cy + k * math.sin(a)
            if ix + 1 <= x < ix + iw - 1 and iy + 1 <= y < iy + ih - 1 and k % 2 == 0:
                f.set(round(x), round(y), "white")
        frames.append(f)
    s.timeline([(0.0, frames[-1])] + [(3.0 + 0.4 * k, f) for k, f in enumerate(frames)])
    return s.svg("Supervised learning",
                 "Pixel-art night chalkboard: two classes of points, yellow dots and pink crosses, and a dashed "
                 "decision boundary that swings around until it separates them.")


def scene_unsupervised():
    s, (ix, iy, iw, ih) = chalkboard("unsupervised", 6.0)
    rng = random.Random("unsupervised")
    centres = [(ix + 14, iy + 8, "lit"), (ix + 46, iy + 9, "glyph"), (ix + 30, iy + 20, "flower1")]
    pts = []
    for k in range(27):
        cx, cy, col = centres[k % 3]
        pts.append(((rng.randrange(ix + 3, ix + iw - 3), rng.randrange(iy + 3, iy + ih - 3)),
                    (cx + rng.randrange(-4, 5), cy + rng.randrange(-3, 4)), col))
    frames = []
    for n in range(6):
        u = ease("inout", n / 5)
        f = Canvas()
        for (a, b, col) in pts:
            x, y = round(a[0] + (b[0] - a[0]) * u), round(a[1] + (b[1] - a[1]) * u)
            f.rect(x, y, 2, 2, col if n == 5 else "star")
        if n == 5:
            for cx, cy, col in centres:
                for k in range(16):
                    ang = 2 * math.pi * k / 16
                    f.set(round(cx + 7 * math.cos(ang)), round(cy + 5 * math.sin(ang)), col)
        frames.append(f)
    s.timeline([(0.0, frames[-1]), (3.2, frames[0])] + [(3.8 + 0.35 * k, f) for k, f in enumerate(frames[1:])])
    return s.svg("Unsupervised learning",
                 "Pixel-art night chalkboard: scattered chalk dots drift together into three coloured clusters, "
                 "which get circled.")


def scene_causal():
    s, (ix, iy, iw, ih) = chalkboard("causal", 6.0)
    nodes = {"Z": (ix + 33, iy + 4), "X": (ix + 12, iy + 18), "Y": (ix + 54, iy + 18), "M": (ix + 33, iy + 21)}
    edges = [("Z", "X"), ("Z", "Y"), ("X", "M"), ("M", "Y")]
    for a, b in edges:
        stroke(s.base, nodes[a], nodes[b], "star_d", 1)
    for name, (x, y) in nodes.items():
        s.base.merge(shifted(outlined(ring(3, -1, {"Z": "flower1", "X": "lit", "Y": "glyph", "M": "white"}[name])),
                             x, y))
    dot = Canvas()
    dot.rect(-1, -1, 2, 2, "white")
    glow_disc(dot, 0, 0, 2, "glow")
    for k, (a, b) in enumerate(edges):
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        s.move(dot, [(0.0, 1.0, (x0, y0), (x1, y1), "inout"), (1.0, 6.0, (x1, y1), (x1, y1), "lin")],
               offset=-1.2 * k, spans=rotate(6.0, [(0.0, 1.0)], -1.2 * k))
    return s.svg("Causal inference",
                 "Pixel-art night chalkboard with a causal graph: a confounder points to both cause and effect, "
                 "the cause acts through a mediator, and glowing pulses travel along each arrow in turn.")


def scene_xai():
    s, (ix, iy, iw, ih) = chalkboard("xai", 6.0)
    layers_ = [3, 4, 4, 2]
    pos = []
    for li, n in enumerate(layers_):
        x = ix + 10 + li * 16
        pos.append([(x, iy + 4 + round((ih - 8) * (k + 0.5) / n)) for k in range(n)])
    for a, b in zip(pos, pos[1:]):
        for p in a:
            for q in b:
                stroke(s.base, p, q, "mtn_near", 1)
    for col in pos:
        for x, y in col:
            s.base.merge(shifted(outlined(ring(2, -1, "star")), x, y))
    path = [pos[0][1], pos[1][2], pos[2][1], pos[3][0]]
    lens = Canvas()
    lens.merge(outlined(ring(5, 3, "metal")))
    stroke(lens, (4, 4), (8, 8), "wood", 2)
    heat = []
    for k, (x, y) in enumerate(path):
        f = Canvas()
        for (px_, py_) in path[:k + 1]:
            glow_disc(f, px_, py_, 3, "glow")
            f.rect(px_ - 1, py_ - 1, 3, 3, "orange")
        heat.append(f)
    segs = []
    for k in range(len(path) - 1):
        segs.append((1.2 * k, 1.2 * k + 1.0, path[k], path[k + 1], "inout"))
        segs.append((1.2 * k + 1.0, 1.2 * (k + 1), path[k + 1], path[k + 1], "lin"))
    segs.append((3.6, 6.0, path[-1], path[-1], "lin"))
    s.timeline([(0.0, heat[0]), (1.0, heat[1]), (2.2, heat[2]), (3.4, heat[3])])
    s.move(lens, segs)
    return s.svg("Explainable AI",
                 "Pixel-art night chalkboard with a small neural network: a magnifying glass moves from input to "
                 "output and the nodes it passes light up orange, tracing what drove the prediction.")


def scene_radar():
    s, (ix, iy, iw, ih) = chalkboard("radar", 4.8)
    cx, cy, r = ix + 22, iy + 13, 11
    s.base.merge(shifted(ring(r + 1, r, "green"), cx, cy))
    for rr in (4, 8):
        for k in range(24):
            a = 2 * math.pi * k / 24
            s.base.set(round(cx + rr * math.cos(a)), round(cy + rr * math.sin(a)), "mtn_near")
    s.base.rect(cx - r, cy, 2 * r + 1, 1, "mtn_near")
    s.base.rect(cx, cy - r, 1, 2 * r + 1, "mtn_near")
    blips = [(cx + 6, cy - 4), (cx - 7, cy + 3), (cx + 3, cy + 7)]
    sweeps = []
    n = 16
    for k in range(n):
        a = 2 * math.pi * k / n - math.pi / 2
        f = Canvas()
        for t_ in range(1, r):
            for da, col in ((0.0, "laser"), (-0.2, "green"), (-0.4, "g1")):
                f.set(round(cx + t_ * math.cos(a + da)), round(cy + t_ * math.sin(a + da)), col)
        for bx, by in blips:
            ang = (math.atan2(by - cy, bx - cx) + math.pi / 2) % (2 * math.pi)
            age = ((2 * math.pi * k / n) - ang) % (2 * math.pi)
            if age < 2.4:
                f.rect(bx, by, 2, 2, "laser" if age < 0.8 else "green")
        sweeps.append(f)
    s.flip(sweeps, 0.0, 4.8, 4.8 / n)
    dx, dy = ix + 48, iy + 6                          # the dish beside the scope
    s.base.rect(dx + 6, dy + 10, 2, 10, "metal_d")
    for i in range(-6, 7):
        s.base.set(dx + 7 + i, dy + 6 + round(i * i / 8), "metal")
    stroke(s.base, (dx + 7, dy + 8), (dx + 7, dy + 2), "metal_d", 1)
    s.base.set(dx + 7, dy + 1, "glyph")
    return s.svg("Radar",
                 "Pixel-art night chalkboard with a radar scope: a green sweep circles and three blips flare as it "
                 "passes, next to a sketch of a dish antenna.")


def scene_misc():
    s, (ix, iy, iw, ih) = chalkboard("misc", 6.0)
    doodles = [("dice", 4), ("coins", 20), ("apple", 36), ("gear", 52)]
    frames = []
    for n in range(len(doodles) + 1):
        f = Canvas()
        for name, dx in doodles[:n]:
            rows = ICONS[name]
            cells = {(i, j) for j, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}
            for i, j in cells:                        # chalk outlines plus the dark details (pips, stems)
                edge = any((i + a, j + b) not in cells for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge or rows[j][i] == "K":
                    f.set(ix + dx + i, iy + 6 + j, "white")
        frames.append(f)
    s.timeline([(0.0, frames[-1]), (3.0, frames[0])] + [(3.4 + 0.55 * k, f) for k, f in enumerate(frames[1:])])
    return s.svg("Other notes",
                 "Pixel-art night chalkboard where chalk doodles of a die, coins, an apple and a gear are drawn "
                 "one after another.")


SCENES = {
    "v2i": scene_v2i,
    "llm-video-lens": scene_video_lens,
    "vision-data": scene_vision_data,
    "amr-arm": scene_amr_arm,
    "gpt-ros": scene_gpt_ros,
    "carla": scene_carla,
    "board-games": scene_board_games,
    "chest-ct": scene_chest_ct,
    "hanoi": scene_hanoi,
    "loan": scene_loan,
    "traffic": scene_traffic,
    "personal-llm": scene_personal_llm,
    "competitions": scene_competitions,
    "korean-stt": scene_korean_stt,
    "notes": scene_notes,
    "notes-quality": scene_quality,
    "notes-supervised": scene_supervised,
    "notes-unsupervised": scene_unsupervised,
    "notes-causal": scene_causal,
    "notes-xai": scene_xai,
    "notes-radar": scene_radar,
    "notes-misc": scene_misc,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    for name, draw in SCENES.items():
        if only and name not in only:
            continue
        svg = draw()
        path = OUT / f"{name}.svg"
        path.write_text(svg)
        print(f"{path.relative_to(ROOT)}: {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
