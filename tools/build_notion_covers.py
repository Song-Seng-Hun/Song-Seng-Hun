#!/usr/bin/env python3
"""Draw the animated covers for the Notion portfolio's project and study-note pages.

Run from anywhere:
    python3 tools/build_notion_covers.py
It writes assets/notion/covers/<name>.svg, one per scene in SCENES.

Each cover is a 240x64-cell night scene (4 px per cell) drawn with the world map's
palette, sprites and SMIL helpers from build_worldmap.py. Notion crops a cover to a
wide band and phones cut its sides, so every scene keeps its subject in the middle
third (cells 80-160). The first frame is a complete picture on its own, for viewers
that show covers without animation.
"""

import math
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True     # importing the map tool should not leave tools/__pycache__ behind
from build_worldmap import ICONS, PALETTES, TRAVELER, Canvas, frames_for, group, outlined, svg_paths, tree

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


def shown(dur, spans):
    """Opacity animation: visible during the (start, end) spans of a dur-second loop."""
    frames = [(0.0, 0)]
    for a, b in spans:
        frames += [(a, 1), (b, 0)]
    kt, vals = _times(dur, frames)
    return (f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/>')


def visible_at(spans, t=0.0):
    return any(a <= t < b for a, b in spans)


def ease(kind, u):
    if kind == "in":
        return u * u
    if kind == "out":
        return 1 - (1 - u) ** 2
    if kind == "inout":
        return 0.5 - 0.5 * math.cos(math.pi * u)
    return u


def moves(dur, segments):
    """Cell-snapped translate animation. segments: (t0, t1, (x0, y0), (x1, y1), ease)."""
    frames = []
    for t0, t1, a, b, kind in segments:
        steps = max(1, round((t1 - t0) / TICK))
        for k in range(steps + 1):
            u = ease(kind, k / steps)
            x = round(a[0] + (b[0] - a[0]) * u)
            y = round(a[1] + (b[1] - a[1]) * u)
            frames.append((t0 + (t1 - t0) * k / steps, f"{x * P} {y * P}"))
    kt, vals = _times(dur, frames)
    return (f'<animateTransform attributeName="transform" type="translate" dur="{dur}s" '
            f'repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vals}"/>'), frames[0][1]


def cycle(dur, n, start=0.0, end=None, period=None):
    """Spans for frame k of an n-frame flipbook running from start to end."""
    end = dur if end is None else end
    period = period or (end - start) / n
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


def paths(c):
    return svg_paths(c, PAL)


def layer(c, anim="", spans=None, transform=None):
    """An overlay canvas; with spans it shows only then (and starts in its t=0 state)."""
    if spans is not None:
        return group(paths(c), shown(DUR, spans), opacity=1 if visible_at(spans) else 0, transform=transform)
    return group(paths(c), anim, transform=transform)


def glow_disc(c, cx, cy, r, col):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r:
                c.set(x, y, col)


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


def traveler(x, y, frame="idle"):
    """The portfolio owner's sprite with its feet on row y."""
    f = frames_for(TRAVELER)[frame]
    return shifted(f, x - 1, y - 13)


def cover_svg(title, desc, base, layers):
    w, h = CW * P, CH * P
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges" role="img" aria-labelledby="t d">'
            f'<title id="t">{title}</title><desc id="d">{desc}</desc>'
            f'{paths(base)}{"".join(layers)}</svg>\n')

# ---------------------------------------------------------------- scenes

DUR = 8.0


def scene_v2i():
    """V2I: the traffic light reads the car's RFID, talks to it over Bluetooth, then turns green."""
    c, amb = night("v2i", trees=False)
    for x, w, h, seed in ((10, 14, 9, 1), (30, 11, 7, 2), (196, 13, 8, 3), (216, 16, 10, 4)):
        house(c, amb, x, 42, w, h, seed)
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
    lamps = {}
    for name, y, col, glow in (("red", 15, "red", "nv_glow"), ("yellow", 20, "yellow", "glow"),
                               ("green", 25, "green", "laser_glow")):
        lc = Canvas()
        glow_disc(lc, 140, y + 1, 5, glow)
        lc.rect(138, y, 6, 3, col)
        lc.rect(138, y, 2, 1, "white")
        lamps[name] = lc
    # the car waits at the stop line, leaves on green and the next one rolls in
    car = sprite(ICONS["car"])
    wait = (109, 43)
    anim, _ = moves(DUR, [(0.0, 1.8, wait, wait, "lin"),
                          (1.8, 4.2, wait, (250, 43), "in"),
                          (4.2, 5.0, (-20, 43), (-20, 43), "lin"),
                          (5.0, 7.4, (-20, 43), wait, "out"),
                          (7.4, DUR, wait, wait, "lin")])
    car_layer = group(paths(car), anim, transform=f"translate({wait[0] * P} {wait[1] * P})")
    # RFID read flash on the reader, then Bluetooth arcs from the box towards the car
    flash = Canvas()
    glow_disc(flash, 134, 36, 4, "laser_glow")
    flash.rect(132, 34, 4, 4, "glyph")
    arcs = []
    for r in (4, 8, 12):
        a = Canvas()
        for k in range(2 * r + 3):
            ang = math.pi * (0.62 + 0.3 * k / (2 * r + 2))
            if k % 2 == 0:
                a.set(round(142 + r * math.cos(ang)), round(35 + r * math.sin(ang) * 0.75), "glyph")
        arcs.append(a)
    talk = cycle(DUR, 3, start=7.6, end=DUR, period=0.25)
    talk0 = cycle(DUR, 3, start=0.0, end=1.75, period=0.25)
    layers = amb + [car_layer,
                    layer(lamps["red"], spans=[(0, 1.8), (4.4, DUR)]),
                    layer(lamps["green"], spans=[(1.8, 3.8)]),
                    layer(lamps["yellow"], spans=[(3.8, 4.4)]),
                    layer(flash, spans=[(7.3, 7.6)])]
    layers += [layer(a, spans=talk0[k] + talk[k]) for k, a in enumerate(arcs)]
    c.merge(traveler(92, 42))
    return cover_svg("V2I signal",
                     "Pixel-art night street: a car waits at a red light while the light's controller talks to it "
                     "over Bluetooth; the light turns green, the car drives off, and the next car rolls in and is "
                     "recognised by its RFID card.",
                     c, layers)


SCENES = {
    "v2i": scene_v2i,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in SCENES.items():
        svg = draw()
        path = OUT / f"{name}.svg"
        path.write_text(svg)
        print(f"{path.relative_to(ROOT)}: {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
