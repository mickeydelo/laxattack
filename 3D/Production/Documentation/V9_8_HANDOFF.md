# v9.8 handoff (separate from v9.7)

## Part A: face rendering fix (P0 Kit eyes) + blink timing
### Root cause of the narrow sideways "C" eyes
- `Head.place()` positions every face feature (eyes, eye highlights, nose, blush, mouth patch) using a (tangent, normal, up) frame whose
  determinant is **−1**, i.e. mirrored. That silently flipped the winding of every placed feature, so its normals pointed into the head.
- **Blender** draws both sides of every face, so the eyes always looked solid there.
- **RealityKit** culls back faces. It skipped the eye's front surface and drew the inside of its far side, which sits under the skin
  except at the rim. The result was a dark outline ring with a skin-coloured centre: the "C" / narrow-eye look (and the grey-centred eyes
  seen on earlier device passes). The nose showed the same outline ring.
- **Fix** (`lax_figure.py`): `place()` reverses the face winding whenever the frame is mirrored. **Guard:** every placed or hand-built surface
  must be counter-clockwise from outside; validate faces in RealityKit, never only in Blender.

### Other face and readability changes
- **Blink:** now **3 visible frames**, fully closed for 1 frame with half-closed lids on the frame either side. Before it was 3 frames fully
  closed plus the ramp. Blink frame numbers are unchanged (`lax_expression_frames.json` still applies).
- **Eyes:** near-black iris (sRGB 0.07 / 0.045 / 0.035) and ~25% smaller highlights, so each eye reads as a solid dark oval with a sparkle.
- **Kit (and Ollie on his rebuild):** eyes ~18% larger, to read through the helmet cage.
- **Eye darts:** reduced to ±2.5° / ±1.5°.

### RealityKit validation (`Previews/RealityKit/v98/`)
- `v98_kit_face_BEFORE.png` vs `v98_kit_face_AFTER.png`: close-up (outline rings → solid glossy eyes, nose and blush).
- `v98_kit_gameplay_distance_BEFORE.png` vs `_AFTER.png`: telephoto from the `camera_gameplay_cozy_PROPOSAL` position. Each row pair is
  the mid frame and the blink frame of `goalie_ready` (20, 28), `goalie_ready_lively` (1542, 1538), `goalie_center_taps` (1434, 1439) and
  `goalie_scan` (594, 588), followed by `goalie_read_left` 119, `goalie_save_high_left` 310, `goalie_save_low_right` 430,
  `goalie_goal_against` (262, 255) and `goalie_celebrate` 538. The worst blink frames are included. Config: `rk_kit_gameplay_distance.json`.
- `v98_rae_face_after.png`: Rae at Ready 756, blink 742 and delighted 159.

### Changed files (this part)
| File | SHA-256 (first 16) | Tris |
|---|---|---|
| `lax_shooter.usdz` | 3df8920102866ec8 | 31,440 |
| `lax_shooter_lod1.usdz` | 52f3b08e9c892c86 | 31,440 |
| `lax_shooter_lod2.usdz` | ab3566a511c9b547 | 31,440 |
| `lax_shooter_clips.json` | d6c95d14256833e3 | — |
| `lax_goalie.usdz` | 47cc4110631b9ee3 | 45,684 |
| `lax_goalie_lod1.usdz` | c3317276fa760da0 | 45,684 |
| `lax_goalie_lod2.usdz` | 70c717c8c933f012 | 45,684 |
| `lax_goalie_clips.json` | 8dbd878ff2192aab | — |

Rigs, joint order, clips, frame ranges, events, sockets, facing and origins are unchanged.

### Still to re-export with the face fix (next parts)
`lax_team_home_7*` (Mina), `lax_team_away_5*` (Ollie), `lax_boy_field*`, `lax_girl_goalie*`, `lax_fan_a/b/c*`. Their eyes still have the
outline defect until re-exported.

## Remaining v9.8 queue
- **P0:** floating far shore; vegetation animation planted with rotation only, in named groups (`ambient_trees` … `ambient_bushes`);
  redone women's markings with a labelled diagram.
- **P1:** stick pass for #30 and the standalone sticks, and a replay-safe near-miss capture.
- **P2:** foreground bush masses.


## Part B: face fix for the rest of the cast (+ #30 women's goalie stick)
- **Re-exported with the part A fixes** (outward-wound face features, 3-frame blinks, near-black eyes, smaller highlights, gentler darts):
  Mina, Ollie (with the larger helmet-cage eyes), #22, #30, Fan A, Fan B and Fan C.
- **#30** now uses the women's goalie stick with string tails.
- **Fans** keep the lightweight LODs.
- **RealityKit validation (`Previews/RealityKit/v98/`):**
  - `v98_cast_gameplay_distance.png`: telephoto at about 10 m. Mina, Ollie and #22 at Ready 756 / blink 742 / delighted 159; #30 at
    13 / 28 / 525; fans at `crowd_idle` 24 / cheer 240 / groan 340.
  - `v98_cast_face_closeups.png`: every face renders solid (no outline rings).
  - Config: `rk_cast_faces.json`.

### Changed files (part B)
| File | SHA-256 (first 16) | Tris |
|---|---|---|
| `lax_team_home_7.usdz` | 1b7b375524486c77 | 40,048 |
| `lax_team_home_7_lod1.usdz` | c637158e6513cfb5 | 40,048 |
| `lax_team_home_7_lod2.usdz` | d6e9aad6775778a9 | 40,048 |
| `lax_team_home_7_clips.json` | dc9b85b9a6ad002f | — |
| `lax_team_away_5.usdz` | 05c99dddcef99fe8 | 44,160 |
| `lax_team_away_5_lod1.usdz` | 3dcb1c1627a7e964 | 44,160 |
| `lax_team_away_5_lod2.usdz` | 6f0f791d4c0d7124 | 44,160 |
| `lax_team_away_5_clips.json` | 9bc896178fece1f1 | — |
| `lax_boy_field.usdz` | 1312607414d3714a | 44,824 |
| `lax_boy_field_lod1.usdz` | 01ff0e2b08354415 | 44,824 |
| `lax_boy_field_lod2.usdz` | 7de6056ecdd814a1 | 44,824 |
| `lax_boy_field_clips.json` | fd38ef494084aa84 | — |
| `lax_girl_goalie.usdz` | e9c2ff8b3c6ae9e9 | 47,016 |
| `lax_girl_goalie_lod1.usdz` | 4b1f24c7d6241e17 | 47,016 |
| `lax_girl_goalie_lod2.usdz` | 12058101f7c77669 | 47,016 |
| `lax_girl_goalie_clips.json` | 912bdc36396657bb | — |
| `lax_fan_a.usdz` | daac5c9712c4b933 | 21,664 |
| `lax_fan_a_lod1.usdz` | e816aafc7e48da1e | 10,831 |
| `lax_fan_a_lod2.usdz` | b00f0affea540b6c | 5,415 |
| `lax_fan_a_clips.json` | a87347e3a06f57bd | — |
| `lax_fan_b.usdz` | 5500cdc450fab030 | 26,840 |
| `lax_fan_b_lod1.usdz` | 745b4b10429aefac | 13,420 |
| `lax_fan_b_lod2.usdz` | 8452f2de0a51d080 | 6,710 |
| `lax_fan_b_clips.json` | 7961f5b99e2ed7c8 | — |
| `lax_fan_c.usdz` | 60ef1d2987ffb94c | 29,788 |
| `lax_fan_c_lod1.usdz` | 7b60d1722de1312e | 14,893 |
| `lax_fan_c_lod2.usdz` | 864952ba3e317066 | 7,446 |
| `lax_fan_c_clips.json` | 54fe95058c108a9d | — |

Rigs, joint order, clips, frame ranges, events, sockets, facing and origins are unchanged. **All v9 characters now carry the face fix.**
