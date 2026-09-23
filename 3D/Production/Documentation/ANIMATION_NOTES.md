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


## lax_goalie (boy goalie) — Phase 3
**LEFT/RIGHT = SHOOTER'S PERSPECTIVE.** `goalie_*_left` moves toward the shooter's left (game −X), which is the goalie's own
right. This matches the aiming coordinates. The asset faces +Z toward the shooter.

| Clip | Start | End | Loop | Save contact | Notes |
|---|---|---|---|---|---|
| goalie_ready | 0 | 40 | yes | — | set position; toe bounce; eyes track |
| goalie_shuffle_left | 50 | 70 | yes | — | in place; runtime slides root toward shooter-left (game -X) along the crease arc |
| goalie_shuffle_right | 80 | 100 | yes | — | in place; runtime slides root toward shooter-right (game +X) |
| goalie_read_left | 110 | 128 | no | — | anticipation toward shooter-left; ends loaded (chain into goalie_save_left) |
| goalie_read_right | 135 | 153 | no | — | anticipation toward shooter-right |
| goalie_save_left | 160 | 190 | no | contact 167 (local 7) | stick save at mid height, shooter-left; contact local 7 |
| goalie_save_right | 200 | 230 | no | contact 207 (local 7) | stick save at mid height, shooter-right; contact local 7 |
| goalie_goal_against | 240 | 285 | no | — | looks back at the net, slumps; blend to ready |
| goalie_save_high_left | 295 | 325 | no | contact 302 (local 7) | extra |
| goalie_save_high_right | 335 | 365 | no | contact 342 (local 7) | extra |
| goalie_save_low_left | 375 | 405 | no | contact 382 (local 7) | extra; stick head drops to the turf |
| goalie_save_low_right | 415 | 445 | no | contact 422 (local 7) | extra |
| goalie_five_hole_close | 455 | 475 | no | contact 460 (local 5) | extra; knees + stick close the gap |
| goalie_body_save | 485 | 509 | no | contact 490 (local 5) | extra; chest block with recoil |
| goalie_celebrate | 520 | 556 | no | — | extra; stick pumps |

**Chaining:**
- Shuffles are in place; the runtime slides the root along the crease arc.
- `goalie_read_*` ends loaded, and `goalie_save_*` starts from the matching read pose, so read → save chains without a pop.
- Every save recovers to the `goalie_ready` pose by its last frame.

**Save beats:** read, push-off, explosive reach to the CONTACT frame, overshoot with deepest pocket compression, then
recovery. Low saves and the five-hole close put the stick head on the turf (lowest point 1–2 cm above field level).

**Validation:**
- 0 errors.
- Max hand-IK error 1.1 cm (body save).
- Loop seams ≤ 4e-5.
- Root is static.
- Baked mesh Y range 0.000…1.685 m.

## lax_stick_goalie
Same 9 pocket clips, frame ranges, sockets and axes as `lax_stick_attack`.
- Deeper pocket (0.10 m); the resting ball centre sits at the rim plane.
- Sockets in USD: grip (0,0,0), pocket (0,−0.002,0.547), ball_contact (0,−0.088,0.547), effect (0,0,0.88).
- 3,744 tris.


## Expanded library (2026-09-23)
Everything is appended after the previous ranges; the earlier ranges and events are unchanged. The boy field player and the teammates share the shooter timeline; the girl goalie shares the goalie timeline. Roll dodges rotate the feet with the body (`feet_yaw`); all motion stays in place.

### lax_shooter (37 clips)
| Clip | Start | End | Loop | Event |
|---|---|---|---|---|
| idle | 0 | 48 | yes | — |
| cradle | 60 | 88 | yes | — |
| release_overhand | 100 | 133 | no | release 114 |
| celebrate | 150 | 186 | no | — |
| aim_overhand | 200 | 230 | yes | — |
| aim_bounce | 240 | 270 | yes | — |
| aim_sidearm | 280 | 310 | yes | — |
| split_dodge_left | 320 | 344 | no | — |
| split_dodge_right | 350 | 374 | no | — |
| release_bounce | 380 | 413 | no | release 394 |
| release_sidearm | 420 | 453 | no | release 433 |
| quick_stick_catch | 460 | 478 | no | contact 466 |
| quick_stick_release | 490 | 506 | no | release 495 |
| disappointed | 520 | 560 | no | — |
| near_miss_reaction | 570 | 600 | no | — |
| pipe_reaction | 610 | 634 | no | — |
| save_reaction | 645 | 675 | no | — |
| run_loop | 685 | 705 | yes | — |
| idle_relaxed | 720 | 792 | yes | — |
| idle_competitive | 800 | 848 | yes | — |
| idle_nervous | 860 | 920 | yes | — |
| roll_dodge_left | 930 | 960 | no | — |
| roll_dodge_right | 970 | 1000 | no | — |
| face_dodge_left | 1010 | 1034 | no | — |
| face_dodge_right | 1045 | 1069 | no | — |
| celebrate_fist_pump | 1080 | 1110 | no | — |
| celebrate_stick_twirl | 1120 | 1160 | no | — |
| celebrate_jump_tuck | 1170 | 1200 | no | — |
| celebrate_knee_slide | 1210 | 1250 | no | — |
| celebrate_point | 1260 | 1284 | no | — |
| celebrate_restrained | 1295 | 1325 | no | — |
| celebrate_clutch | 1335 | 1389 | no | — |
| weak_miss | 1400 | 1424 | no | — |
| goal_glance_back | 1435 | 1465 | no | — |
| run_start | 1475 | 1491 | no | — |
| run_stop | 1500 | 1518 | no | — |
| stumble_recover | 1528 | 1558 | no | — |

### lax_goalie (35 clips)
| Clip | Start | End | Loop | Event |
|---|---|---|---|---|
| goalie_ready | 0 | 40 | yes | — |
| goalie_shuffle_left | 50 | 70 | yes | — |
| goalie_shuffle_right | 80 | 100 | yes | — |
| goalie_read_left | 110 | 128 | no | — |
| goalie_read_right | 135 | 153 | no | — |
| goalie_save_left | 160 | 190 | no | contact 167 |
| goalie_save_right | 200 | 230 | no | contact 207 |
| goalie_goal_against | 240 | 285 | no | — |
| goalie_save_high_left | 295 | 325 | no | contact 302 |
| goalie_save_high_right | 335 | 365 | no | contact 342 |
| goalie_save_low_left | 375 | 405 | no | contact 382 |
| goalie_save_low_right | 415 | 445 | no | contact 422 |
| goalie_five_hole_close | 455 | 475 | no | contact 460 |
| goalie_body_save | 485 | 509 | no | contact 490 |
| goalie_celebrate | 520 | 556 | no | — |
| goalie_scan | 570 | 618 | yes | — |
| goalie_tap_pipes | 628 | 668 | no | contact 639 |
| goalie_reset_gloves | 678 | 714 | no | — |
| goalie_crossover_left | 724 | 744 | yes | — |
| goalie_crossover_right | 754 | 774 | yes | — |
| goalie_read_high | 784 | 802 | no | — |
| goalie_read_low | 812 | 830 | no | — |
| goalie_kick_save_left | 840 | 870 | no | contact 847 |
| goalie_kick_save_right | 880 | 910 | no | contact 887 |
| goalie_doorstep_stuff | 920 | 950 | no | contact 926 |
| goalie_desperation_dive_left | 960 | 996 | no | contact 969 |
| goalie_desperation_dive_right | 1006 | 1042 | no | contact 1015 |
| goalie_trail_stick_recovery | 1052 | 1082 | no | — |
| goalie_frustrated_tap | 1092 | 1122 | no | — |
| goalie_shrug | 1132 | 1156 | no | — |
| goalie_reset | 1166 | 1196 | no | — |
| goalie_stick_raise | 1206 | 1236 | no | — |
| goalie_helmet_nod | 1246 | 1270 | no | — |
| goalie_small_dance | 1280 | 1328 | no | — |
| goalie_big_clutch_save | 1338 | 1398 | no | contact 1345 |
