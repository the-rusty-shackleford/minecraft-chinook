"""The Chinook, as code: its model and its wheel (a life-size Boeing CH-47, one block a metre), its
two profiles, its recipe, and its rotor loop.

Run from the repository root:

    uv run --no-project python devtools/art/build.py
    uv run --no-project --with numpy python devtools/art/build.py sounds    # needs ffmpeg

Everything it writes is committed; this script is the source of truth for those files. The shape is
measured from public-domain references (devtools/art/reference/SOURCES.md); the model is original
work. Copyright 2026 Rusty Shackleford and nfx. SPDX-License-Identifier: AGPL-3.0-or-later.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parent / "tools/bbgen"))
import bbgen  # noqa: E402  (the shared Blockbench writer: minecraft mods/tools/bbgen)
import metric  # noqa: E402  (building it in metres, the shared way)

ASSETS = ROOT / "src/main/resources/assets/chinook"
DATA = ROOT / "src/main/resources/data/chinook"

# ------------------------------------------------------------------ units

# Built in metres, written in Blockbench pixels (16 a metre). A station `s` is metres aft of the
# nose; the origin is on the ground midway between the rotors, which is the hull's middle too.
PX = 16.0
LENGTH = 15.9
FWD_HUB = (1.95, 4.58)      # the forward rotor's hub: station, height
AFT_HUB = (13.90, 5.59)     # the aft rotor's, 11.95 behind and a metre higher
ORIGIN = (FWD_HUB[0] + AFT_HUB[0]) / 2
ROTOR_R = 9.145             # half of 18.29
BLADE_CHORD = 0.81

# The fuselage's section: a box with chamfered corners (half-width, heights).
HW = 1.275                  # 2.55 across; the cabin inside is 2.29
BELLY, FLOOR, ROOF = 0.57, 0.80, 3.30
SKIN = 0.07
POD_OUT = 1.89              # the fuel pods along the lower sides: 3.78 across them
POD = (0.62, 1.70, 3.90, 12.75)   # bottom, top, from, to
COCKPIT_FLOOR = 1.05
SEAT_Y = 1.13               # the cabin's seat cushions
PILOT_Y = 1.40              # the pilots' cushions
RAMP_HINGE = (12.35, FLOOR)
RAMP_TOP = (15.05, 2.35)
GEAR = (6.10, 12.50)        # the front and rear wheels' stations
TRACK = 1.75                # the wheels' half-track
WHEEL_R = 0.32


def z(s: float) -> float:
    return (ORIGIN - s) * PX


def p(v: float) -> float:
    return v * PX


# ---------------------------------------------------------------- the atlas

def make_atlas() -> bbgen.TexelAtlas:
    a = bbgen.TexelAtlas(size=256, density=1.0, seed=0xC47)
    a.material("paint", (232, 232, 226), w=160, h=64, grain=9)
    a.material("glass", (172, 206, 212), w=64, h=32, grain=6, alpha=110)
    a.material("blade", (44, 46, 50), w=160, h=16, grain=6)
    a.material("frame", (52, 58, 46), w=32, h=32, grain=8)
    a.material("chin", (42, 54, 62), w=32, h=32, grain=6)
    a.material("metal", (140, 144, 150), w=32, h=32, grain=10)
    a.material("dark", (36, 38, 42), w=32, h=32, grain=8)
    a.material("exhaust", (74, 64, 58), w=32, h=32, grain=16)
    a.material("tyre", (30, 30, 32), w=32, h=32, grain=8)
    a.material("floor", (60, 62, 60), w=64, h=32, grain=10,
               pattern=lambda x, y, c: bbgen.shade(c, -10) if (x + 2 * y) % 6 == 0 else c)
    a.material("interior", (150, 154, 142), w=64, h=32, grain=8)

    def weave(x, y, c):
        return bbgen.shade(c, -26) if x % 3 == 0 or y % 3 == 0 else c

    a.material("webbing", (176, 48, 38), w=32, h=32, grain=10, pattern=weave)
    a.material("seat", (72, 76, 72), w=32, h=32, grain=8)
    a.material("panel", (30, 32, 34), w=32, h=32, grain=6)

    def dials(x, y, c):
        dx, dy = x % 5 - 2, y % 5 - 2
        if max(abs(dx), abs(dy)) == 2:
            return c
        if max(abs(dx), abs(dy)) == 1:
            return (150, 152, 150) if (dx, dy) != (1, -1) else (226, 226, 214)
        return (12, 12, 14)

    a.material("instruments", (30, 32, 34), w=64, h=16, grain=4, pattern=dials, scale=2.0)
    a.material("gauge", (14, 14, 16), w=16, h=16, grain=4)
    a.material("needle", (244, 244, 232), w=16, h=16, grain=2)
    a.material("lamp", (250, 246, 220), w=16, h=16, grain=4)
    a.material("beacon", (210, 30, 26), w=16, h=16, grain=6)
    a.material("tip", (218, 192, 64), w=16, h=16, grain=6)
    a.material("boom", (198, 176, 64), w=64, h=16, grain=8)
    a.material("grille", (52, 54, 56), w=32, h=32, grain=4,
               pattern=lambda x, y, c: bbgen.shade(c, 26) if y % 2 == 0 else c)
    return a


class Chinook(metric.Metric):
    def __init__(self) -> None:
        super().__init__(bbgen.Model("chinook", make_atlas(), seed="chinook/chinook"), ORIGIN, PX)


# ------------------------------------------------------------- the airframe

# The nose below the windshield, in layers a pixel thick: each layer's front (a station by height),
# its section narrowing toward the belly, rounded in plan by a quarter circle out to the fuselage's
# half-width. The lower front corners are the chin windows, dark.
FRONT = [(BELLY, 1.15), (0.70, 0.70), (0.85, 0.40), (1.00, 0.20), (1.20, 0.07), (1.40, 0.01), (1.60, 0.0),
         (1.80, 0.03), (2.00, 0.12)]
NARROW = [(BELLY, 0.82), (0.75, 0.92), (0.95, 0.98), (1.10, 1.0), (2.00, 1.0)]
NOSE_BACK = 2.42
REACH = 1.15                # how far behind its front a layer reaches the fuselage's width
TIP = 0.55
CHIN = (0.75, 1.45, 1.20)   # the chin windows: from, to (heights), back to (station)
WINDSHIELD = ((0.12, 2.00), (0.95, 3.22))


def interp(table, y):
    for (ya, va), (yb, vb) in zip(table, table[1:]):
        if ya <= y <= yb:
            return va + (y - ya) / (yb - ya) * (vb - va)
    return table[0][1] if y < table[0][0] else table[-1][1]


def plan(d: float) -> float:
    f = min(max(d, 0.0) / REACH, 1.0)
    return TIP + (HW - TIP) * math.sqrt(1.0 - (1.0 - f) ** 2)


PANEL_S = 0.74              # inside the instrument panel (0.72 to 0.82): the nose above the cockpit's floor ends here,
                            # clear of the panel's face, which would flicker against a face in its own plane


def nose(c: Chinook) -> None:
    """Under the cockpit's floor the nose runs back to the cabin; above it, only to the panel, so the
    pilots sit in a cockpit, not in the nose."""
    layer = 1.0 / PX
    y, i = BELLY, 0
    while y < WINDSHIELD[0][1] - 1e-6:
        y1 = min(y + layer, WINDSHIELD[0][1])
        mid = (y + y1) / 2
        front, narrow = interp(FRONT, mid), interp(NARROW, mid)
        chin = CHIN[0] <= mid < CHIN[1]
        back_s = NOSE_BACK if mid < COCKPIT_FLOOR else PANEL_S
        s0, j = front, 0
        while s0 < back_s - 1e-6:
            hw_px = round(plan(s0 + 0.5 / PX - front) * narrow * PX)
            glass = chin and s0 < CHIN[2]
            s1 = s0 + 1.0 / PX
            while s1 < back_s - 1e-6:
                nxt = round(plan(s1 + 0.5 / PX - front) * narrow * PX)
                if nxt != hw_px or (chin and (s1 < CHIN[2]) != glass):
                    break
                s1 += 1.0 / PX
            s1 = min(s1, back_s)
            hw = hw_px / PX
            c.box("chin" if glass else "paint/nose", f"l{i:02d}b{j:02d}", -hw, hw, y, y1, s0, s1, "chin" if glass else "paint")
            s0, j = s1, j + 1
        y, i = y1, i + 1
    c.box("paint/nose", "rib", -0.10, 0.10, CHIN[0], CHIN[1], -0.012, 0.45, "paint")


def cockpit(c: Chinook) -> None:
    """Over the nose: the windshield's two panes and its post, the side windows back to the cabin,
    the cockpit roof under the forward pylon, the panel and the pilots' seats."""
    low, high = WINDSHIELD
    wall_top, edge_top = (HW, 3.10), (HW - 0.20, ROOF)    # the cockpit's round upper edge

    def at(y):
        """The slant's station at height y."""
        return low[0] + (y - low[1]) / (high[1] - low[1]) * (high[0] - low[0])

    def edge(y):
        """How wide the cockpit is at height y: the side wall, then the round edge."""
        if y <= wall_top[1]:
            return HW
        return wall_top[0] + (y - wall_top[1]) / (edge_top[1] - wall_top[1]) * (edge_top[0] - wall_top[0])

    # Every piece meets its neighbour along the slant a pixel at a time, as on the Huey: the panes
    # across in bands a pixel high, as wide as the cockpit at their height; the side windows back from
    # the slant in bands a pixel high; a pillar along each corner; the round edge cut to the slant.
    joint = {"north": None, "south": None}
    for i, (ya, yb) in enumerate(bands(low[1], high[1])):
        hw = edge((ya + yb) / 2) - 0.015
        c.along("glass/windshield", f"pane{i:02d}", (at(ya), ya), (at(yb), yb), -hw, hw, 0.04, "glass", grow=0.0, faces=joint)
    c.along("cockpit/frame", "post", low, high, -0.05, 0.05, 0.08, "frame")
    c.along("paint/windshield", "sill", (low[0] - 0.03, low[1] - 0.01), (low[0] + 0.03, low[1] + 0.03), -HW, HW, 0.05, "paint")
    for i, (ya, yb) in enumerate(bands(low[1], wall_top[1])):
        c.pair("glass/side", f"side{i:02d}", HW - 0.03, HW - 0.01, ya, yb, at((ya + yb) / 2), 2.30, "glass", faces={"up": None, "down": None})
    c.along("paint/windshield", "pillar", (at(low[1]), low[1]), (at(wall_top[1]), wall_top[1]), HW - 0.05, HW + 0.012, 0.09, "paint", mirror=True)
    c.rod("paint/windshield", "corner_rod", (wall_top[0] - 0.01, wall_top[1], at(wall_top[1])),
          (edge_top[0] - 0.01, edge_top[1], at(edge_top[1])), 0.08, "paint", mirror=True)
    c.pair("paint/cab", "side_low", HW - SKIN, HW, COCKPIT_FLOOR - 0.10, 2.00, PANEL_S - 0.02, 2.42, "paint")
    c.pair("cockpit/frame", "side_post", HW - 0.06, HW, 2.00, wall_top[1], 1.30, 1.36, "frame")
    c.pair("paint/cab", "side_back", HW - SKIN, HW, 2.00, ROOF, 2.30, 2.42, "paint")
    # The cockpit's roof, from the windshield's head back to the cabin, and its round edges, cut to
    # the slant in slices meeting edge to edge.
    c.box("paint/cab", "roof", -(HW - 0.20), HW - 0.20, ROOF - SKIN, ROOF, high[0] - 0.05, 2.42, "paint")
    n = 4
    for k in range(n):
        a = (wall_top[0] + (edge_top[0] - wall_top[0]) * k / n, wall_top[1] + (edge_top[1] - wall_top[1]) * k / n)
        b = (wall_top[0] + (edge_top[0] - wall_top[0]) * (k + 1) / n, wall_top[1] + (edge_top[1] - wall_top[1]) * (k + 1) / n)
        c.across("paint/cab", f"upper{k}", a, b, at((a[1] + b[1]) / 2), 2.42, SKIN, "paint", grow=0.0)
    c.box("floor", "cockpit_floor", -(HW - SKIN), HW - SKIN, COCKPIT_FLOOR - 0.06, COCKPIT_FLOOR, 0.75, 2.42, "floor")
    # The instrument panel, its glare shield, two working gauges in front of the pilot (the right seat).
    c.box("panel", "panel", -1.12, 1.12, 1.55, 2.00, 0.72, 0.82, "panel", faces={"north": "instruments"})
    # The glare shield overhangs the panel's face only a little: any more and it hides the dials from the pilot's eye.
    c.box("panel", "shield", -1.14, 1.14, 2.00, 2.05, 0.66, 0.86, "panel")
    for kind, x in (("speed", -0.45), ("fuel", -0.78)):
        c.box("panel", f"dial_{kind}", x - 0.11, x + 0.11, 1.66, 1.88, 0.82, 0.83, "gauge")
        c.box(f"needle_{kind}", "needle", x - 0.01, x + 0.01, 1.77, 1.86, 0.83, 0.84, "needle")
    for side in (1, -1):
        x, tag = side * 0.60, "l" if side > 0 else "r"
        c.box("seats", f"pilot_pan_{tag}", x - 0.27, x + 0.27, COCKPIT_FLOOR + 0.20, PILOT_Y - 0.04, 1.35, 1.85, "seat")
        c.box("seats", f"pilot_back_{tag}", x - 0.27, x + 0.27, PILOT_Y - 0.04, 2.35, 1.85, 1.95, "seat")
        c.box("seats", f"pilot_leg_{tag}", x - 0.20, x + 0.20, COCKPIT_FLOOR, COCKPIT_FLOOR + 0.20, 1.40, 1.80, "dark")


def bands(y0: float, y1: float):
    """The heights from y0 to y1 in bands a pixel high, the last one whatever is left."""
    out, y = [], y0
    while y < y1 - 1e-6:
        out.append((y, min(y + 1.0 / PX, y1)))
        y += 1.0 / PX
    return out


PORTHOLES = (3.44, 5.48, 7.49, 9.49, 11.52)
PORT_Y = 2.09
DOOR = (2.62, 3.78)         # the crew door on the right, forward


def cabin(c: Chinook) -> None:
    """The cabin: belly, sides, roof and chamfered corners as sheets, portholes along both sides, the
    crew door on the right, the floor and the troop seats, the shaft tunnel along the roof."""
    s0, s1 = NOSE_BACK - 0.02, RAMP_HINGE[0]
    c.across("paint/cabin", "belly", (-(HW - 0.20), BELLY + SKIN / 2), (HW - 0.20, BELLY + SKIN / 2), s0, s1, SKIN, "paint", mirror=False)
    c.across("paint/cabin", "lower", (HW - 0.20, BELLY), (HW, BELLY + 0.20), s0, s1, SKIN, "paint")
    c.pair("paint/cabin", "side", HW - SKIN, HW, BELLY + 0.20, 2.95, s0, s1, "paint")
    c.across("paint/cabin", "upper", (HW, 2.95), (HW - 0.32, ROOF), s0, s1, SKIN, "paint")
    c.box("paint/cabin", "roof", -(HW - 0.32), HW - 0.32, ROOF - SKIN, ROOF, s0, s1 + 0.4, "paint")
    for i, s in enumerate(PORTHOLES):
        c.disc("chin", f"port{i}_l", (s, PORT_Y, HW), 0.30, 0.025, "chin", side=1)
        c.disc("chin", f"port{i}_r", (s, PORT_Y, -HW), 0.30, 0.025, "chin", side=-1)
        c.disc("paint/rims", f"rim{i}_l", (s, PORT_Y, HW - 0.005), 0.36, 0.02, "paint", side=1)
        c.disc("paint/rims", f"rim{i}_r", (s, PORT_Y, -(HW - 0.005)), 0.36, 0.02, "paint", side=-1)
    # The crew door's frame, a hair proud of the right side, round its porthole.
    a, b = DOOR
    out = (-(HW + 0.03), -HW)
    c.box("paint/door", "door_top", *out, 2.62, 2.70, a, b, "paint")
    c.box("paint/door", "door_fore", *out, FLOOR, 2.70, a, a + 0.06, "paint")
    c.box("paint/door", "door_aft", *out, FLOOR, 2.70, b - 0.06, b, "paint")
    c.box("dark", "door_handle", -(HW + 0.06), -(HW + 0.03), 1.55, 1.62, b - 0.30, b - 0.14, "dark")
    # Inside: the floor, a bulkhead behind the pilots, three rows of troop seats facing forward.
    c.box("floor", "floor", -(HW - SKIN), HW - SKIN, FLOOR - 0.06, FLOOR, s0, s1, "floor")
    # Behind the pilots, an open frame two metres across, not a bulkhead: every seat of the front row
    # looks through to the windshield (a doorway a metre wide left the outer seats facing a wall).
    c.pair("interior", "frame_side", 1.00, HW - SKIN, COCKPIT_FLOOR, 2.95, 2.42, 2.48, "interior")
    c.box("interior", "frame_head", -1.00, 1.00, 2.70, 2.95, 2.42, 2.48, "interior")
    for row, s_pan in enumerate(ROWS):
        s_back = s_pan + 0.44
        c.box("seats", f"row{row}_pan", -1.12, 1.12, SEAT_Y - 0.06, SEAT_Y - 0.02, s_pan, s_back, "webbing")
        c.box("seats", f"row{row}_back", -1.12, 1.12, SEAT_Y - 0.02, SEAT_Y + 0.62, s_back - 0.04, s_back, "webbing")
        c.box("seats", f"row{row}_rail", -1.14, 1.14, SEAT_Y - 0.08, SEAT_Y - 0.04, s_pan - 0.02, s_pan + 0.02, "metal")
        for i, x in enumerate((-1.0, 0.0, 1.0)):
            c.rod("seats", f"row{row}_leg{i}", (x, FLOOR, s_pan + 0.08), (x, SEAT_Y - 0.06, s_pan + 0.02), 0.04, "metal")
    # The shaft tunnel along the roof, between the pylons.
    c.box("paint/tunnel", "tunnel", -0.42, 0.42, ROOF, 3.56, 4.30, 11.60, "paint")


ROWS = (3.10, 4.40, 5.70, 7.00)


def pods(c: Chinook) -> None:
    """The fuel pods along the lower sides, their ends rounded, with the landing gear under them."""
    y0, y1, a, b = POD
    w = POD_OUT - HW
    c.pair("paint/pods", "pod", HW - 0.02, POD_OUT, y0 + 0.12, y1 - 0.12, a + 0.35, b - 0.25, "paint")
    c.pair("paint/pods", "pod_low", HW - 0.02, POD_OUT - 0.12, y0, y0 + 0.12, a + 0.40, b - 0.30, "paint")
    c.pair("paint/pods", "pod_top", HW - 0.02, POD_OUT - 0.12, y1 - 0.12, y1, a + 0.40, b - 0.30, "paint")
    # The front: stepped back toward the fuselage; the back: a shorter taper.
    for k, (inset, ds) in enumerate(((0.16, 0.0), (0.08, 0.12), (0.03, 0.24))):
        c.pair("paint/pods", f"front{k}", HW - 0.02, POD_OUT - inset - 0.10 * (2 - k), y0 + 0.12 + 0.05 * (2 - k), y1 - 0.12 - 0.05 * (2 - k),
               a + ds, a + 0.36, "paint")
    for k, (inset, ds) in enumerate(((0.14, 0.0), (0.05, 0.12))):
        c.pair("paint/pods", f"back{k}", HW - 0.02, POD_OUT - inset, y0 + 0.12, y1 - 0.12, b - 0.26, b - ds, "paint")
    c.pair("dark", "fuel_cap", POD_OUT, POD_OUT + 0.02, y1 - 0.30, y1 - 0.18, a + 2.0, a + 2.12, "dark")
    # Each wheel's strut and its oleo, from the pod down to the axle.
    for s in GEAR:
        c.rod("gear", f"strut_{s:.0f}", (TRACK, y0 + 0.05, s), (TRACK, WHEEL_R, s), 0.14, "metal", mirror=True)
        c.rod("gear", f"brace_{s:.0f}", (HW + 0.05, y0 + 0.10, s - 0.35), (TRACK, WHEEL_R + 0.10, s), 0.07, "dark", mirror=True)
        c.pair("gear", f"axle_{s:.0f}", TRACK - 0.10, TRACK + 0.10, WHEEL_R - 0.05, WHEEL_R + 0.05, s - 0.05, s + 0.05, "metal")


def forward_pylon(c: Chinook) -> None:
    """The low pylon over the cockpit, its front sloping down to the windshield's head; the mast."""
    top = 4.02
    c.along("paint/pylon_fwd", "front", (0.95, 3.18), (1.55, top), -0.80, 0.80, 0.12, "paint")
    c.box("paint/pylon_fwd", "body", -0.82, 0.82, ROOF - 0.05, top - 0.12, 1.30, 4.30, "paint")
    c.box("paint/pylon_fwd", "crown", -0.68, 0.68, top - 0.12, top, 1.45, 4.10, "paint")
    c.along("paint/pylon_fwd", "back", (4.05, top - 0.02), (4.70, ROOF + 0.20), -0.70, 0.70, 0.12, "paint")
    c.pair("grille", "louvre", 0.82, 0.84, 3.45, 3.80, 2.60, 3.70, "grille")
    c.box("metal", "mast", -0.11, 0.11, top, FWD_HUB[1] - 0.10, FWD_HUB[0] - 0.11, FWD_HUB[0] + 0.11, "metal")
    c.box("metal", "swashplate", -0.36, 0.36, top + 0.04, top + 0.12, FWD_HUB[0] - 0.36, FWD_HUB[0] + 0.36, "metal")


def aft_pylon(c: Chinook) -> None:
    """The tall pylon at the back, the engines on its flanks, the beacon, and the rear fuselage
    over the ramp."""
    top = 4.96
    # Its front rises steeply from the roof; its body tapers a little toward the top.
    c.along("paint/pylon_aft", "front", (11.30, ROOF), (12.25, top), -0.92, 0.92, 0.14, "paint")
    c.box("paint/pylon_aft", "body", -0.95, 0.95, ROOF - 0.05, 4.30, 11.80, LENGTH - 0.10, "paint")
    c.box("paint/pylon_aft", "upper", -0.82, 0.82, 4.30, top - 0.14, 12.10, LENGTH - 0.45, "paint")
    c.box("paint/pylon_aft", "crown", -0.66, 0.66, top - 0.14, top, 12.25, LENGTH - 0.65, "paint")
    c.along("paint/pylon_aft", "rear", (LENGTH - 0.70, top - 0.02), (LENGTH, 3.60), -0.80, 0.80, 0.14, "paint")
    c.box("beacon", "beacon", -0.07, 0.07, top, top + 0.12, 12.60, 12.74, "beacon")
    c.box("metal", "mast", -0.12, 0.12, top, AFT_HUB[1] - 0.10, AFT_HUB[0] - 0.12, AFT_HUB[0] + 0.12, "metal")
    c.box("metal", "swashplate", -0.38, 0.38, top + 0.04, top + 0.12, AFT_HUB[0] - 0.38, AFT_HUB[0] + 0.38, "metal")
    # The rear fuselage's flanks, over the ramp: in layers a pixel thick, each reaching back from
    # where the shut ramp's line crosses its height, so the underside rises with the ramp to the
    # tail; above the ramp's top they run to the end. The lintel closes the back over the ramp.
    (hs, hy), (ts, ty) = RAMP_HINGE, RAMP_TOP
    y, k = hy, 0
    while y < ROOF - 1e-6:
        y1 = min(y + 1.0 / PX, ROOF)
        mid = (y + y1) / 2
        # Back to where the ramp's line is at this height, or to the tail above the ramp's top.
        back = LENGTH - 0.10 if mid >= ty else hs + (mid - hy) / (ty - hy) * (ts - hs) + 0.06
        c.pair("paint/rear", f"flank{k:02d}", HW - SKIN, HW, y, y1, hs - 0.02, back, "paint")
        y, k = y1, k + 1
    c.box("paint/rear", "roof", -HW + 0.25, HW - 0.25, ROOF - SKIN, ROOF, RAMP_HINGE[0], LENGTH - 0.10, "paint")
    c.box("paint/rear", "lintel", -HW, HW, ty, ROOF, LENGTH - 0.40, LENGTH - 0.10, "paint")
    # The engines: an octagonal nacelle on each flank, an intake ring at the front, the exhaust behind.
    for side in (1, -1):
        cx = side * 1.32
        tag = "l" if side > 0 else "r"
        c.octagon("paint/engines", f"nacelle_{tag}", (cx, 3.80), 0.38, 11.70, 14.10, "paint")
        c.octagon("grille", f"intake_{tag}", (cx, 3.80), 0.30, 11.62, 11.70, "grille")
        c.octagon("exhaust", f"exhaust_{tag}", (cx, 3.80), 0.30, 14.10, 14.45, "exhaust")
        c.octagon("dark", f"mouth_{tag}", (cx, 3.80), 0.22, 14.44, 14.47, "dark")
    c.pair("paint/engines", "mount", 0.90, 1.05, 3.60, 4.00, 12.20, 13.60, "paint")


def ramp(c: Chinook) -> None:
    """The loading ramp, shut: hinged at its foot on the cabin floor, sloping up to the rear
    fuselage. Its folder is the door the profile swings down to the ground."""
    c.along("ramp/paint", "ramp", RAMP_HINGE, RAMP_TOP, -(HW - 0.08), HW - 0.08, 0.10, "paint")
    c.along("ramp", "ramp_floor", (RAMP_HINGE[0] + 0.05, RAMP_HINGE[1] + 0.07), (RAMP_TOP[0] - 0.05, RAMP_TOP[1] + 0.07),
            -(HW - 0.20), HW - 0.20, 0.04, "floor")
    for side in (1, -1):
        x = side * (HW - 0.14)
        c.along("ramp", f"hinge_{'l' if side > 0 else 'r'}", (RAMP_HINGE[0] - 0.06, RAMP_HINGE[1] - 0.04),
                (RAMP_HINGE[0] + 0.20, RAMP_HINGE[1] + 0.12), x - 0.06, x + 0.06, 0.10, "dark")


def rotors(c: Chinook) -> None:
    """Two three-bladed rotors, the forward turning counter-clockwise seen from above, the aft
    clockwise; the aft a metre higher, so the blades pass over each other."""
    for name, (s_hub, y_hub), phase in (("rotor_fwd", FWD_HUB, 0.0), ("rotor_aft", AFT_HUB, 60.0)):
        c.octagon(name, "hub", (0.0, y_hub), 0.30, s_hub - 0.30, s_hub + 0.30, "metal")
        c.box(name, "cap", -0.16, 0.16, y_hub + 0.10, y_hub + 0.30, s_hub - 0.16, s_hub + 0.16, "dark")
        for k in range(3):
            heading = math.radians(phase + 120.0 * k)
            # A blade lying along +z from the hub, turned about y to its heading.
            yaw = math.degrees(heading)
            for part, r0, r1, mat in (("blade", 0.45, ROTOR_R - 0.40, "blade"), ("tip", ROTOR_R - 0.40, ROTOR_R, "tip"),
                                      ("grip", 0.20, 0.75, "dark")):
                width = BLADE_CHORD if part != "grip" else 0.34
                thick = 0.09 if part != "grip" else 0.18
                c.m.cube(name, f"{part}{k}", [p(-width / 2), p(y_hub - thick / 2), z(s_hub) + p(r0)],
                         [p(width / 2), p(y_hub + thick / 2), z(s_hub) + p(r1)], mat,
                         rotation=(0, yaw, 0), origin=[0, p(y_hub), z(s_hub)])


def lamps(c: Chinook) -> None:
    for name, x, s in (("landing_l", 0.42, 1.10), ("landing_r", -0.42, 1.10)):
        c.box("lenses", name, x - 0.13, x + 0.13, BELLY - 0.08, BELLY, s - 0.13, s + 0.13, "lamp")
        c.box("frame", name + "_rim", x - 0.16, x + 0.16, BELLY - 0.03, BELLY, s - 0.16, s + 0.16, "frame")


HOOK = (0.0, BELLY - 0.24, ORIGIN)


def hook(c: Chinook) -> None:
    x, y, s0 = HOOK
    c.box("hook", "mount", -0.16, 0.16, BELLY - 0.06, BELLY, s0 - 0.24, s0 + 0.24, "dark")
    c.box("hook", "hanger", -0.03, 0.03, y + 0.04, BELLY - 0.06, s0 - 0.03, s0 + 0.03, "metal")
    c.box("hook", "hook", -0.05, 0.05, y, y + 0.05, s0 - 0.09, s0 + 0.07, "metal")


SPRAY_S, SPRAY_Y, SPRAY_HALF = 9.00, 0.36, 7.5


def spray_boom(c: Chinook) -> None:
    """The crop sprayer's rig, drawn only while fitted: a boom 15 across under the belly between
    the wheels, nozzles along it, braces up to the pods."""
    d = 0.09
    c.box("spray_boom", "boom", -SPRAY_HALF, SPRAY_HALF, SPRAY_Y - d / 2, SPRAY_Y + d / 2, SPRAY_S - d / 2, SPRAY_S + d / 2, "boom")
    n = 31
    for i in range(n):
        x = -SPRAY_HALF + 0.2 + (2 * SPRAY_HALF - 0.4) * i / (n - 1)
        c.box("spray_boom", f"nozzle{i:02d}", x - 0.025, x + 0.025, SPRAY_Y - 0.14, SPRAY_Y - d / 2, SPRAY_S - 0.025, SPRAY_S + 0.025, "dark")
    c.rod("spray_boom", "brace", (POD_OUT - 0.10, POD[0], SPRAY_S - 0.40), (4.6, SPRAY_Y, SPRAY_S), 0.06, "boom", mirror=True)
    c.rod("spray_boom", "stay", (1.0, BELLY - 0.02, SPRAY_S), (2.4, SPRAY_Y + 0.02, SPRAY_S), 0.05, "metal", mirror=True)
    c.box("spray_boom", "pump", -0.30, 0.30, SPRAY_Y + 0.03, BELLY - 0.02, SPRAY_S - 0.25, SPRAY_S + 0.25, "dark")


def build_model() -> bbgen.Model:
    c = Chinook()
    nose(c)
    cockpit(c)
    cabin(c)
    pods(c)
    forward_pylon(c)
    aft_pylon(c)
    ramp(c)
    rotors(c)
    lamps(c)
    hook(c)
    spray_boom(c)
    return c.m


def build_wheel() -> bbgen.Model:
    """A wheel at its axle, the axle along x: an octagonal tyre, a hub, a cap."""
    a = bbgen.TexelAtlas(size=64, density=1.0, seed=0xC48)
    a.material("tyre", (30, 30, 32), w=32, h=32, grain=8)
    a.material("hub", (150, 154, 158), w=16, h=16, grain=8)
    m = bbgen.Model("chinook_wheel", a, seed="chinook/wheel")
    w = metric.Metric(m, 0.0, PX)
    w.disc("tyre", "tyre", (0.0, 0.0, -0.13), WHEEL_R, 0.26, "tyre", side=1)
    w.disc("hub", "hub", (0.0, 0.0, -0.135), 0.17, 0.27, "hub", side=1)
    return m


# ------------------------------------------------------------- the profiles


def v(x: float, y: float, s: float) -> list:
    return [round(p(x), 3), round(p(y), 3), round(z(s), 3)]


SEATS = [(-0.60, PILOT_Y, 1.62, True), (0.60, PILOT_Y, 1.62, False)] \
    + [(x, SEAT_Y, s + 0.22, False) for s in ROWS for x in (-0.76, 0.0, 0.76)]
CARGO_SLOTS = [(x, s) for s in (9.10, 10.30, 11.50) for x in (-0.55, 0.55)]


def vehicle_profile() -> dict:
    return {
        "mesh": "chinook:chinook",
        "wheel_mesh": "chinook:chinook_wheel",
        "scale": 0.0625,
        "handedness": "right",
        "body": {
            "width": 3.8, "length": LENGTH, "height": 3.6,
            "parts": [{"at": v(0, BELLY, 1.70), "width": 3.0, "height": 2.75},
                      {"at": v(0, BELLY, 4.50), "width": 3.0, "height": 2.75},
                      {"at": v(0, BELLY, 11.50), "width": 3.0, "height": 2.75},
                      {"at": v(0, BELLY, 14.30), "width": 2.6, "height": 4.40}],
        },
        "seats": [{"at": v(x, y, s), "driver": True} if driver else {"at": v(x, y, s)} for x, y, s, driver in SEATS],
        "wheels": {"radius": round(p(WHEEL_R), 3),
                   "positions": [{"forward": round(z(s), 3), "right": round(p(side * TRACK), 3)}
                                 for s in GEAR for side in (-1, 1)]},
        "engine": {"max_speed": 1.2, "acceleration": 0.025, "reverse_speed": 0.35, "brake": 0.035},
        "climb": 0.5,
        "mass": 4.0,
        "fuel": {"capacity": 48000},
        "storage": {"chests": [{"at": v(0.82, FLOOR, 8.30), "yaw": 270, "scale": 0.8, "rows": 6},
                               {"at": v(-0.82, FLOOR, 8.30), "yaw": 90, "scale": 0.8, "rows": 6}]},
        "cargo": {"adults": 6, "young": 12, "slots": [v(x, FLOOR, s) for x, s in CARGO_SLOTS]},
        "doors": [{"part": {"group": "ramp"}, "hinge": v(0, RAMP_HINGE[1], RAMP_HINGE[0]), "axis": [1, 0, 0], "open": -0.78,
                   "from": v(-HW, RAMP_HINGE[1], RAMP_TOP[0]), "to": v(HW, RAMP_TOP[1] + 0.1, RAMP_HINGE[0])}],
        "gauges": [
            {"kind": "speed", "part": {"group": "needle_speed"}, "pivot": v(-0.45, 1.77, 0.83),
             "axis": [0, 0, 1], "zero": -2.094, "sweep": 4.189},
            {"kind": "fuel", "part": {"group": "needle_fuel"}, "pivot": v(-0.78, 1.77, 0.83),
             "axis": [0, 0, 1], "zero": -2.094, "sweep": 4.189},
        ],
        "headlights": {"at": [v(0.42, BELLY - 0.08, 1.10), v(-0.42, BELLY - 0.08, 1.10)], "part": {"group": "lenses"}, "range": 18},
        "paint": {"part": {"group": "paint"}, "default": "green", "factory": "#424a37"},
        "glass": {"group": "glass"},
        "cockpit": {"group": "cockpit"},
        "sounds": {"engine": "chinook:rotor", "pitch": [0.6, 1.03], "volume": [0.4, 1.0]},
        # Third person: 22 behind the pilot's eye (who sits in the nose) stands just clear of the aft
        # rotor's disc; the length rule's 25 left the Chinook small on the screen.
        "camera": 22.0,
        "repair": {"ingredient": {"tag": "c:ingots/steel"}, "full_cost": 32},
    }


#       x0      x1     y0      y1     s0     s1
HULL = [(-POD_OUT, POD_OUT, BELLY, ROOF, 0.0, LENGTH),          # the fuselage and its pods
        (-0.82, 0.82, ROOF, 4.02, 1.00, 4.70),                  # the forward pylon
        (-0.42, 0.42, ROOF, 3.56, 4.30, 11.60),                 # the shaft tunnel
        (-1.72, 1.72, ROOF, 4.96, 11.30, LENGTH),               # the aft pylon and its engines
        (-(TRACK + 0.16), TRACK + 0.16, 0.0, BELLY, GEAR[0] - 0.4, GEAR[1] + 0.4)]   # the wheels


def aircraft_profile() -> dict:
    return {
        "climb_rate": 0.35, "descent_rate": 0.45, "vertical_acceleration": 0.025,
        "yaw_rate": 2.5, "spool_ticks": 80, "tilt": 10,
        "rotors": [
            {"part": {"group": "rotor_fwd"}, "pivot": v(0, FWD_HUB[1], FWD_HUB[0]), "axis": [0, 1, 0], "speed": 1.0,
             "radius": round(p(ROTOR_R), 2)},
            {"part": {"group": "rotor_aft"}, "pivot": v(0, AFT_HUB[1], AFT_HUB[0]), "axis": [0, 1, 0], "speed": -1.0,
             "radius": round(p(ROTOR_R), 2)},
        ],
        "hook": v(*HOOK),
        "sprayer": {"part": {"group": "spray_boom"}, "at": v(0, SPRAY_Y, SPRAY_S), "width": 15},
        "hull": [{"from": v(x0, y0, s1), "to": v(x1, y1, s0)} for x0, x1, y0, y1, s0, s1 in HULL],
    }


CHASSIS_RECIPE = {
    "type": "minecraft:crafting_shaped", "category": "misc",
    "pattern": ["GBG", "BBB", "BBB"],
    "key": {"G": {"tag": "c:glass_panes"}, "B": {"tag": "c:storage_blocks/steel"}},
    "result": {"id": "vanillawheels:chassis", "count": 1, "components": {"vanillawheels:vehicle": "chinook:chinook"}},
}


def unlock(recipe: str, tag: str) -> dict:
    return {"parent": "minecraft:recipes/root",
            "criteria": {"has_the_recipe": {"trigger": "minecraft:recipe_unlocked", "conditions": {"recipe": recipe}},
                         "has_it": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": tag}]}}},
            "requirements": [["has_the_recipe", "has_it"]],
            "rewards": {"recipes": [recipe]}}


SOUNDS_JSON = {"rotor": {"sounds": [{"name": "chinook:rotor", "attenuation_distance": 80}]}}
LANG = {"vehicle.chinook.chinook": "Chinook"}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def template(path: Path, size) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{DataVersion: 3955, size: [%d, %d, %d], data: [], entities: [], palette: [{Name: \"minecraft:air\"}]}\n" % tuple(size), encoding="utf-8")


def main() -> None:
    build_model().write(ASSETS / "vanillawheels/mesh/chinook.bbmodel")
    build_wheel().write(ASSETS / "vanillawheels/mesh/chinook_wheel.bbmodel")
    write_json(DATA / "vanillawheels/vehicle/chinook.json", vehicle_profile())
    write_json(DATA / "rotorcraft/aircraft/chinook.json", aircraft_profile())
    write_json(DATA / "recipe/chinook_chassis.json", CHASSIS_RECIPE)
    write_json(DATA / "advancement/recipes/chinook_chassis.json", unlock("chinook:chinook_chassis", "#c:storage_blocks/steel"))
    write_json(ASSETS / "sounds.json", SOUNDS_JSON)
    write_json(ASSETS / "lang/en_us.json", LANG)
    # The pad the gametests fly over: room for sixteen metres of hull either way it turns.
    template(ROOT / "devtools/gameteststructures/pad.snbt", (48, 40, 48))


SOUND_SRC = ROOT / "devtools/art/sounds/src"


def sounds() -> None:
    sys.path.insert(0, str(ROOT.parent / "tools/sound"))
    import cutlib  # noqa: E402
    start, length, fade = LOOP
    cutlib.write_ogg(ASSETS / "sounds/rotor.ogg",
                     cutlib.loop(SOUND_SRC / "162243-ch-47-chinook.ogg", start, start + length + fade, fade, 0.8))


LOOP = (13.728, 3.340, 0.20)   # 38 beats of 88 ms, where the crossfade's ends correlate best (0.69)


if __name__ == "__main__":
    if sys.argv[1:] == ["sounds"]:
        sounds()
    else:
        main()
