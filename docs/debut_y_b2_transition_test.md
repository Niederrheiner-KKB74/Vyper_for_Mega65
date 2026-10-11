# B2: signed ENTRY→RETURN handoff (Issue #39)

Unreleased test, **not Stable**. Branch `test-debut-y-b2` derives from Issue #37 commit `26e141dc5673b71957a1bd45eb7d324905d92bc7`, using its B sources. Stage 5c/5d and all A/B/C artifacts remain unchanged.

## Actual cause

In `stage5c_entry.asm`, `e_curve` consumes a byte, updates the signed coordinates and increments the cursor. On the final byte it sets phase 2 (RETURN) before `e_mirror`. Then `ygeometry.postframe` only projects phase 1. Consequently B renders the unprojected endpoint on this frame. The preceding submitted point was projected by −16. The observed delta is **16 plus the final original dy**, not necessarily 16: Level 2 (both groups) and Level 3 have final dy −3, hence +13 pixels. This happens before the first call to `e_return`.

At the next frame `restore` does not restore phase 2, and the existing RETURN routine takes one pixel per axis towards the current drifting formation goal. The defect originates in ENTRY completion, not ATTACK or RRB clipping.

## Minimal correction

`src/tests/debut_y_b2/y_geometry.asm` records each signed, projected ENTRY presentation coordinate, before clipping. Only the final-byte branch of `e_curve` calls `finish_entry`, which restores that last submitted X/Y before changing to RETURN. `e_mirror` publishes the same position to legacy consumers. No extra curve byte, timing tick or altered original byte is introduced. The final byte is still consumed; its logical endpoint is not published over the previous visible point. This intentionally holds that point for the transition frame, then the unchanged RETURN routine moves normally.

The cache records submitted coordinates, including offscreen coordinates, rather than clamped screen coordinates. Fully offscreen positions remain non-collidable through the existing clipping/hitbox checks. This avoids stale in-field positions when a curve exits the screen. For the Level 1–3 completion points the last submitted point is on the visible field. A cache-missing fallback projects the current signed coordinate once. Level initialization clears validity and projection flags.

ATTACK source, its curve interpretation, descriptor selection, reentry and return routines are byte-identical to B and Stage 5c. Formation targets and original assets are unchanged. Collision, explosion and shot consumers continue to use the same published coordinate arrays. ENTRY remains original-Y−16, player Y=184, playfield Y=0–199.

## Build and host validation

```sh
python tools/build_debut_y_b2.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65 python -m unittest test_debut_y_b2 -v
```

KickAssembler 5.25 is verified by SHA-256. The builder pins the B source commit and Stable Stage 5c; all three DATs come from the Stable tag. The D81 contains `VYPER_Y_B2` and all three SEQ DAT files. Complete generated sources and symbols are included alongside the PRG.

Memory: ENTRY segment $5700–$5B68 remains below row-retirement code $5B80. Private B2 module/state $7700–$7889 remains below aimed-shot initialization $7951. No existing fixed origin or high-memory data buffer moves.

`transition-traces.json` contains measured assembled-code transitions for every enemy in Levels 1, 2 and 3: previous logical/presented position, first RETURN position and formation target, plus RETURN→FORMATION points. These are CPU-model measurements, not XEMU raster observations. RETURN steps must be at most one pixel per axis and settle at the original Y target. Drift remains active.

## XEMU acceptance pending

Mount `VYPER_Y_B2.D81`, `LOAD"VYPER_Y_B2",8`, then `RUN`. Use +/− for Levels 2 and 3. Compare the bottom sweep and transition to formation with B and WinUAE: no extra jump, smooth return to the drifting individual slots. Check Level 1, animations, ENTRY/ATTACK fire, four enemy-shot limit, player movement/fire, collisions/explosions, respawn, HUD/palettes, Level Clear and Game Over/R. Change levels during ENTRY and RETURN. Test X, DIRECTORY and repeated RUN. Actual raster/palette/cursor behavior requires user XEMU confirmation; no Stable tag is created.

## Measured examples (enemy 0)

| Level | Last visible ENTRY | B first RETURN | B Y jump | B2 first RETURN | Moving target |
|---|---|---|---|---|---|
| 1 | [120, 13] | [120, 29] | 16 | [120, 13] | [98, 18] |
| 2 | [115, 54] | [118, 67] | 13 | [115, 54] | [53, 0] |
| 3 | [124, 49] | [123, 62] | 13 | [124, 49] | [61, 0] |

All 10 CPU-model tests passed in 33.479 seconds. Both original-B and B2 traces cover all 64 enemies across Levels 1–3. All 23 independent build outputs are byte-identical. XEMU not run.
