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

## Status (2026-10-07): built, gated and filmed; photos passed by Rusty

- Gate: 6 GameTests and the booth (12 checks) green.
- Built: the model and its wheel, both profiles (with Rotorcraft's hull and rotor radii), the
  chassis recipe and unlock, the lang, the rotor loop, the booth, the wiki page.
- Rusty passed the booth photos on 2026-10-07 ("Looks good"), after the cockpit glass was made to
  meet the slant and the third-person cameras were set. Not done: the playtest on the 4070.
- Nothing released; no GitHub repo yet (created at release on Rusty's word). Ships with Vanilla
  Wheels 1.12.0, Rotorcraft 1.0.0 and the Huey as pack 1.75.0.

## Shape

`devtools/art/build.py` writes every file under `src/main/resources` and the gametests' pad; edit
it, never the outputs. Judge the model with `../tools/bbgen/render.py` (`--bounds` to lay it over the
3-view at a fixed frame, `--look` and a zoom for a joint) and in the booth.
