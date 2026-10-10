# Chinook

A life-size Boeing CH-47 for [Rotorcraft](https://github.com/the-rusty-shackleford/minecraft-rotorcraft),
the helicopter protocol layered on [Vanilla Wheels](https://github.com/the-rusty-shackleford/minecraft-vanilla-wheels),
on NeoForge 1.21.1. One block a metre: 15.9 blocks long, two three-bladed rotors 18.3 across turning
opposite ways, the aft a metre higher than the forward. A pilot (the right-hand seat) and a copilot
up front, twelve on red troop seats in the cabin, and behind them room for six grown animals (or
twelve young) and two chests, loaded up the rear ramp; four wheels; a cargo hook under the middle
of the belly; a mount for a fifteen-block crop sprayer. There is no Java in it: the helicopter is
two datapack profiles, two Blockbench meshes (the body and a wheel) and a sound, and the protocols
do the rest, so flying, the sling and the sprayer are documented in Rotorcraft's README and the
keys, fuel, paint, doors, cargo and repairs in Vanilla Wheels'.

## Getting one

- **Chassis**: a glass pane, a steel block and a glass pane over six steel blocks
  (`G B G / B B B / B B B`).
- **Build**: the chassis, an engine and four wheels in a Mechanic Lift, and Build. It comes out
  Army green; paint it there with a dye.

## Using it

Rotorcraft's keys fly it: Space and Left Shift move the collective lever, which stays where it is
let go and holds the height in its detent (Rotorcraft 1.2.0's D-0005), W and S tilt the stick, R
gets out (within three blocks of the ground), G hooks and lets go a sling load, V switches the crop
sprayer, H the lights. Blows wear it a twelfth as much as a point of damage wears a boat (its
`durability`, 12, Vanilla Wheels' D-0034: ten pistol rounds to a wreck). Its
rotors spool for four seconds before it lifts. The ramp is Vanilla Wheels' door: crouch and
right-click it empty-handed to lower or raise it; with it down, right-click the Chinook holding a
lead and every animal on your leads nearby walks aboard while there is room; crouch and right-click
with a lead to let them out behind.

In third person the camera stands 22 blocks behind the pilot's eye (the profile's `camera`), just
clear of the aft rotor. Between the cabin and the cockpit is an open frame, so the front row sees out
of the windshield.

Numbers: 1.2 blocks a tick at the top, 0.35 reverse; climbs 0.35 and descends 0.45 a tick; turns
2.5 degrees a tick; tilts up to 10 degrees; 48 000 ticks of fuel; repaired with steel ingots, 32 for
a wreck. Two landing lights under the nose light the ground 18 blocks ahead.

## How it is made

`devtools/art/build.py` writes everything: the model (`chinook.bbmodel`) and the wheel
(`chinook_wheel.bbmodel`), cubes in named folders on generated textures of one texel a model pixel;
both profiles; the recipe and its unlock; the lang, `sounds.json` and the gametests' pad. Run from
the repository root:

```
uv run --no-project python devtools/art/build.py
uv run --no-project --with numpy python devtools/art/build.py sounds    # needs ffmpeg
```

The model is built in metres with the shared `tools/bbgen/metric.py`, from the CH-47's published
dimensions and the U.S. Army's 3-view (`devtools/art/reference/`, with `SOURCES.md`), whose side
view it lies on within a few pixels. The origin is on the ground midway between the rotors, the
hull's middle; Rotorcraft's `hull` names five boxes (the fuselage with its pods, the two pylons with
the engines, the shaft tunnel, the wheels), and the rotors' radii keep it drawn while only a blade
is in view and are how far a spinning rotor strikes what it touches (both discs pass over anyone
standing beside it). The windshield, the side windows and the cockpit's rounded roof edge meet along
the windshield's slant a pixel at a time, under a pillar at each corner, as the Huey's do. The
folders the profiles select by: `paint` (dyed), `glass` (translucent), `cockpit` (the windshield's
posts, hidden from riders' own eyes), `rotor_fwd` and `rotor_aft` (spun, opposite ways), `ramp` (the
door, swung down about its foot), `spray_boom` (drawn while a sprayer is fitted), `lenses` (lit with
the lights), `needle_speed` and `needle_fuel` (the pilot's gauges). The rotor loop is cut from a CC0
recording made aboard a CH-47 (`devtools/art/sounds/SOURCES.md`).

## Verifying it

```
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
./gradlew clean build -PskipBooth
```

Rotorcraft and Vanilla Wheels come from Maven Local (`./gradlew publishToMavenLocal` in each,
Vanilla Wheels first). Six gametests on a 48-block pad: the profiles; the chassis recipe; the lift
builds it from the chassis, an engine and four wheels and paints it; it climbs, crosses the pad,
turns and lands softly with nobody hurt; cows board up the lowered ramp and not through it shut; and
it carries the Sling Container on its hook and sets it down whole. The booth (`./gradlew
runPhotoBooth` on a display) films it parked, dyed, with its ramp down, full, from the pilot's
seat, hovering, carrying the container, and spraying a field.

## License

AGPL-3.0-or-later. Copyright Rusty Shackleford and nfx.
