# Animation Notes

30 fps. Each character has one baked timeline. The runtime slices clips by frame range, as `prepareShooter()` already does.
Manifests: `3D/Production/Exports/lax_shooter_clips.json`, `3D/Production/Exports/lax_stick_attack_clips.json`.

**Left/right convention:** shooter clips use the shooter's own left/right. Shooter-left is game −X; the shooter faces −Z.
Goalie clips (Phase 3) will use the **shooter's perspective**.

## lax_shooter (girl field hero)
The four graybox ranges are unchanged, so the current Swift trims keep working.

| Clip | Start | End | Loop | Key frame | Notes |
|---|---|---|---|---|---|
| idle | 0 | 48 | yes | — | breathing/look; blink at local 30 |
| cradle | 60 | 88 | yes | — | pocket lags the cradle sweep |
| release_overhand | 100 | 133 | no | release 114 (local 14 = 0.467 s) | graybox timing kept |
| celebrate | 150 | 186 | no | — | jump via pelvis |
| aim_overhand | 200 | 230 | yes | — | loaded hold for aiming |
| aim_bounce | 240 | 270 | yes | — | first frame of release_bounce |
| aim_sidearm | 280 | 310 | yes | — | first frame of release_sidearm |
| split_dodge_left | 320 | 344 | no | — | in place; move root toward game −X between local 6–16 |
| split_dodge_right | 350 | 374 | no | — | in place; move root toward game +X between local 6–16 |
| release_bounce | 380 | 413 | no | release 394 (local 14) | starts from aim_bounce |
| release_sidearm | 420 | 453 | no | release 433 (local 13) | starts from aim_sidearm |
| quick_stick_catch | 460 | 478 | no | contact 466 (local 6) | ends in quick-stick ready pose |
| quick_stick_release | 490 | 506 | no | release 495 (local 5) | starts from the ready pose |
| disappointed | 520 | 560 | no | — | ends slumped; blend to idle |
| near_miss_reaction | 570 | 600 | no | — | extra |
| pipe_reaction | 610 | 634 | no | — | extra |
| save_reaction | 645 | 675 | no | — | extra |
| run_loop | 685 | 705 | yes | — | extra, in place |

**Shot structure.** Every release follows the same beats: anticipation (counter-dip or aim), loaded pose, acceleration,
release key on an ease-in into the release frame, overshooting follow-through, settle, and recovery to base.

**Pocket.** `pocket_01`/`pocket_02` translate along −Z of the stick frame. This gives compression on load and catch, a
forward snap at release, and recoil afterwards. `pocket_socket` rides with it.

**Secondary motion (baked, no runtime simulation).** Ponytail pitch/roll and hem swing come from damped springs driven by
pelvis bounce, lateral shift and torso yaw. Loops are pre-rolled so their seams match.

**Validation** (`lax_validate.py`, see EXPORT_NOTES):
- 0 errors.
- Max hand-IK error 1.6 cm (cradle) and 1.3 cm (celebrate).
- Loop seams ≤ 1e-5.
- Root is static in every clip.
- Baked mesh Y range −0.002…1.606 m.

Recommended transitions: 0.12 s by default. Use 0.08 s into releases and 0.2 s out of reactions.

## Recommended release timing (for Swift)
| Clip | Release delay after clip start |
|---|---|
| release_overhand | 14/30 s |
| release_bounce | 14/30 s |
| release_sidearm | 13/30 s |
| quick_stick_release | 5/30 s |

## lax_stick_attack pocket clips

| Clip | Start–End | Loop | Notes |
|---|---|---|---|
| pocket_idle | 0–30 | yes | resting weight |
| pocket_cradle_left | 40–60 | yes | ball rolls to stick-left with lag |
| pocket_cradle_right | 70–90 | yes | mirror |
| pocket_catch_soft | 100–115 | no | contact local 2, peak 4 |
| pocket_catch_hard | 120–138 | no | contact local 1, deep compression, overshoot |
| pocket_load | 145–157 | no | presses back during wind-up |
| pocket_release | 160–168 | no | release local 3 |
| pocket_recoil | 170–185 | no | empty rebound |
| pocket_pipe_vibration | 190–214 | no | whole-stick buzz about the grip |

The shooter asset already carries its own pocket motion inside each clip. The standalone stick is for customization, pickups
and equipment previews.


Phase 1 commit: `3ef396d58503f5e7844da3cee169684900893c22`.
