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

## 1.1.0 — built and gated 2026-10-10, unreleased (durability 12, on Rotorcraft 1.2.0)

Its profile names `durability` 12 (Vanilla Wheels 1.14.0's D-0034): ten pistol rounds, five rifle
rounds or two to three rockets wreck it, where one did. It nests Rotorcraft 1.2.0 (the collective
lever and its dial, Rotorcraft's D-0005; the gametests and the booth put the lever in its detent where
they hover). Gate: the release gate (2026-10-10, `clean build --no-build-cache`) green with 6 gametests and the booth's 12 checks.

## 1.0.1 — rebuilt on Rotorcraft 1.1.0, with the submarines

Nothing of the Chinook's own changes. It nests Rotorcraft 1.1.0, which nests Vanilla Wheels 1.13.0:
- the hull, crash judging and the keys are Vanilla Wheels' now (its D-0031);
- a key acts once a press (its D-0032);
- the boarding line names R, not Shift (its D-0033);
- a broken Chinook set down from its item stays to be mended (Rotorcraft's D-0004; a friend's Huey
  could not be).

The gametests read `Keys.UP` and `Condition.MAX` (`64a803e`). Rusty: "plus the Huey and Chinook
rebuilt on the new Rotorcraft (both are released, so they need version bumps)".

Released 2026-10-08 in pack 1.78.0: tag `v1.0.1` at `36fd8a0`; the release gate green with 6
GameTests and the booth's 12 checks; sha1 `addbc8d2` on GitHub and on the server (the server repo's
`knowledge/releases/pack-1.78.0.md`).

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
