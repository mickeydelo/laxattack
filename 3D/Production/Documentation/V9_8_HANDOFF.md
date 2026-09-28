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
