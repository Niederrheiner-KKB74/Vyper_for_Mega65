# Stage 5d-1a: confirmed B2 integration (Issue #41)

**Pending integrated XEMU acceptance; not Stable.** Branch `stage5d-1-b2` starts from the actual current Stage 5d-1 GitHub commit `e295fa81d5c18b009eb22841ea5db2da7c8a6279`. This includes the confirmed title/loader and HOTREG handoff (program commit `7d6e77f`). B2 source is commit `4cb73e71974f4102bdad003cdbc1cae1b0896407`, confirmed by the user in XEMU for Issue #39. No whole-branch merge from the test branch: the title integration remains the basis.

## Exact source changes

All new files are `src/engine/stage5d1a*.asm`; previous `stage5d1*.asm`, Stable sources/assets and releases remain untouched.

- Main source imports `stage5d1a_entry_projection.asm`.
- ENTRY initialization calls `ygeometry.clear`; per-frame processing calls `restore`; postframe tail goes to `ygeometry.postframe`.
- Only the final original ENTRY-byte branch calls `finish_entry` before setting phase RETURN and publishing via `e_mirror`.
- The projection module is byte-identical to confirmed B2, except `variant.inc` becomes a fixed compile-time `TEST_VARIANT=2`. No new movement algorithm.
- Remaining components are identical to Stage 5d-1 after filename/stage-name normalization. The builder enforces this, particularly `_attack`, `_level`, `_game`, `_palettes`, `_title`, loader, renderer and shots.

During ENTRY, original signed Y is restored before decoding each original byte, then projected by −16 for presentation/combat. Last submitted signed X/Y is cached before clipping. On the final byte, the cursor still advances and original duration remains unchanged; RETURN receives the preceding presentation point, rather than the raw endpoint. Existing RETURN then moves one pixel per axis to the same individual formation position plus current drift. No offset is applied to RETURN or ATTACK, and there is no pre-clipping clamp. A completely offscreen submission remains offscreen; no stale visible coordinate is substituted.

This corrects B's actual phase-order defect: the final byte changed to RETURN before the projection filter, yielding +13px in Levels 2/3 (last original dy −3 plus missing −16 projection) and +16px in Level 1. Last visible enemy-0 positions in B2 are Level 1 (120,13), Level 2 (115,54), Level 3 (124,49). The integrated build must publish these unchanged on ENTRY→RETURN.

## Memory and phase lifetimes

Assembly guards retain all fixed origins. ENTRY code $5700–$5B68 ends before retirement $5B80. New projection/state $7700–$7889 ends before aimed-shot initialization $7951. The title caches are disjoint: $12800–$13FFF, $15B00–$1F7FF, $5C500–$5F0FF; title Screen $F300–$FD4F, Color-RAM $FF82000–$FF82A4F. VYTI stages at $40000, is fully copied before VYLV replaces staging, and title remains active throughout the three game-DAT loads.

VYLV $40000, VYGR $54000, VYCL $5C300 are unchanged. The preserved loader still sets SETBNK, checks headers/lengths/checksums/DMA readback, closes channels and retains the disk device. Bootstrap $4000–$47FF is backed up after title shutdown to $15B00 and restored on exit; B2 does not touch these ranges. HOTREG, palette and cursor restore sequence is unchanged. Player Y=184, field Y=0..199, 38 types and all 100 records remain available.

## Reproduce

```sh
python tools/build_stage5d1a.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65 python -m unittest test_stage5d1a test_stage5d1a_entry -v
```

KickAssembler 5.25 checksum is required. Pillow and py65 are required for host conversion/tests. Release `releases/stage_5d_1_b2/` contains complete generated ASM, title-layout include, symbols, PRG, D81 and all four DATs including `VYTI.DAT`. Converter `tools/convert_stage5d1_title.py` remains unchanged and reproduces the original 352×240 image/palette.

The test models exercise actual assembled instructions and DMA descriptors; they are not XEMU or a raster simulation. Inherited Stage 5d-1 tests check protected title pixels, DMA bounds during loading, palette/HOTREG restoration, all-level management, graphics/combat and DOS behavior. ENTRY tests cover original points, signed coordinates/clipping, collision boxes, shots, explosions and per-enemy transitions in Levels 1–3. There is no diagnostic output inside raster-sensitive routines.

## XEMU protocol (not yet executed for integration)

1. Mount `VYPER_STAGE5D1A.d81`; `LOAD"STAGE5D1A",8`, then `RUN`.
2. Verify unchanged full title while all three game DATs load; Level 1 starts without upper-row artifacts or wrong palettes.
3. Use +/− to compare Levels 2/3 with confirmed B2. Bottom sweep, last point and return to the drifting formation must match; no jump on RETURN→FORMATION. Repeat Level 1 and additional above/below entries.
4. Verify ATTACK and attack reentry, two-frame formation drift, three-ATTACK/four-shot limits, player control/fire, collision/explosion/respawn, score/lives, HUD and original palettes.
5. Test level changes during ENTRY and RETURN, Level Clear/button, 100→1, Game Over/R and repeated restarts.
6. X must restore BASIC normally; DIRECTORY and subsequent RUN must reload and show title successfully. Stage 5d-1a remains untagged until explicit user confirmation.

The direct assembled-code comparison matches confirmed B2 for 1,000 complete object updates in each of Levels 1, 2, 3, 29, 60 and 100 (6,000 updates per build). Only actual enemy slots are compared; unused slots may retain irrelevant initialization bytes. Long Level-60 curves retain their word cursor and 1,260-frame delay semantics with the projected coordinate handoff. The pre-B2 Stage-4c position expectation and raw final-point expectation are deliberately replaced by these geometry-aware checks, rather than disabling tests.

## Executed validation results

59 distinct CPU-model checks pass across the broad run and corrected targeted reruns. The initial broad run took 934.015 s: 57 passed, two inherited checks still expected pre-B2 geometry. Their Stage-5d-1a replacements were rerun together: both passed in 82.384 s. Raw logs and `test-results.json` retain this distinction; no tests were disabled. All 128 transition events for the 64 enemies of Levels 1–3 match the confirmed B2 trace exactly. All 28 independent build outputs are byte-identical. Integrated XEMU testing is still pending.

A deterministic download bundle can be regenerated with `python tools/package_stage5d1a.py`; it includes the complete generated sources, DATs, PRG/D81, test evidence and documentation. Rebuilding requires the repository and its original assets/tags.
