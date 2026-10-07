---
title: Chinook — project
type: overview
layer: store
tags: [overview]
---

# Chinook

## What this is

A life-size Boeing CH-47 for Rotorcraft (Rusty, 2026-10-06): data only, nesting Rotorcraft (which
nests Vanilla Wheels). The plan is `~/.claude/plans/i-want-to-add-curious-locket.md`; D-0001 is the
model, the origin, the ramp and the sound.

## Status: 1.0.0 released 2026-10-07 in pack 1.75.0

- Gate: 6 GameTests and the booth (12 checks) green.
- Built: the model and its wheel, both profiles (with Rotorcraft's hull and rotor radii), the
  chassis recipe and unlock, the lang, the rotor loop, the booth, the wiki page.
- Rusty passed the booth photos on 2026-10-07 ("Looks good"), after the cockpit glass was made to
  meet the slant and the third-person cameras were set. Not done: the playtest on the 4070.
- Released 2026-10-07 in pack 1.75.0 on Rusty's "looks good, fix the latent key bug then release"
  (the server repo's `knowledge/releases/pack-1.75.0.md`): public repo created then, the jar's sha1
  `de4f6058` on GitHub and on the server. Not yet seen: anyone flying it on the box. Rusty flew it
  in the 4070 playtest before the release.

## Shape

`devtools/art/build.py` writes every file under `src/main/resources` and the gametests' pad; edit
it, never the outputs. Judge the model with `../tools/bbgen/render.py` (`--bounds` to lay it over the
3-view at a fixed frame, `--look` and a zoom for a joint) and in the booth.
