# v9 Handoff: concept-matched characters + environment (first device test)

## What changed
| File(s) | Change |
|---|---|
| `lax_shooter.usdz` (+ `_lod1`, `_lod2`, `_clips.json`) | **v9 look** matching the concept turnaround: cream #10 jersey with red trim and V-neck, red shorts with cream piping, white goggles with dark strap, sculpted brown hair with a bun, tall glossy toy eyes, bare hands. **Same file name, rig, 78 clips, frame ranges, events, sockets and facing (−Z).** 6.6 MB, 1 material |
| `lax_goalie.usdz` (+ `_lod1`, `_lod2`, `_clips.json`) | **v9 look: now the female #2 goalie** (navy/cyan helmet with cyan stripe and white cage, bun, navy #2 kit with rounded pads, navy/white gloves). **Same file name, rig, 38 clips, frame ranges, root-motion metadata, sockets and facing (+Z).** 6.1 MB, 1 material |
| **NEW** `lax_arena_pinebrook_v9.usdz`, `_v9_lod1`, `_v9_lod2`, `_v9_mobile` | v9 environment: bubbly trees, pine forest across a wide blue lake, rocky shore, split-rail fence with flowering bushes, lush tufts, clouds. **Same root and group names as v8** (`/lax_arena_pinebrook/lax_arena_content/...`, same markers), so it is a drop-in swap |

v8 arena files are unchanged and remain available as a fallback.

## Arena v9 budget
| File | Tris | Size |
|---|---|---|
| `lax_arena_pinebrook_v9.usdz` | 685k (includes hidden sharp/soft pairs) | 37.7 MB |
| **`lax_arena_pinebrook_v9_lod1.usdz` (use for the first device test)** | **343k** | 18.7 MB |
| `lax_arena_pinebrook_v9_lod2.usdz` | 137k | 10.6 MB |
| `lax_arena_pinebrook_v9_mobile.usdz` | LOD0 geometry, 1K textures | 29.2 MB |

## Runtime notes
- **Ambient layer:** with the v9 arena, **do not load `lax_arena_ambient`**. Its v8 trees and boats would overlap the new scenery, and v9 has no `ambient_twins` content.
- **Life layer:** `lax_arena_life` still works (the fence line is unchanged). Keep it.
- **Sharp/soft groups:** same rules as before. The v9 far background is still hazy in the soft group; this is a known polish item.
- **Not yet in the v9 look:** teammates, fans, the boy field player and the girl goalie variant. Only the shooter and goalie heroes changed.
- **Look targets:** `Previews/V9/v9_behind_shooter.png` (gameplay) and `Previews/RoundTrip/v9_packaged_roundtrip.png` (packaged files, re-imported).

## Validation
- **Shooter:** 78 clips; 0 errors; no hand-grip gap over 2.5 cm; loops seamless.
- **Goalie:** 38 clips; 0 errors; no hand-grip gap over 2.5 cm; loops seamless.
- **Arena v9:** 0 meshes near the origin; 4 materials.


## v9.1 (device review follow-up)
- **Goalie eyes:** the packaged file shows the eyes **open in every `goalie_ready` frame** (`Previews/RoundTrip/v9_goalie_eye_check.png`). Auto-blinks run
  every 2–3.5 s, so a still can land on a blink. The parked eyelids now sit 40° up, under the hairline and helmet brim, so the forehead no longer
  shows pale rectangles. If eyes still look closed in a Ready capture, please report the clip name and time.
- **Contrast and grounding:** stronger baked contact shading on the shooter and goalie; the far background soft haze is reduced from 55% to 22%
  (`lax_arena_pinebrook_v9*`); the foreground soft haze is reduced from 25% to 12%.
- **Lighting (washed-out fix):** the image-based light EXR was brightened 2.2× for the earlier "night" issue, and it now over-fills alongside the sun.
  - **Image-based light intensity exponent:** 1.0 → **0.0** (try −0.5 if still flat).
  - **Directional sun:** keep it warm at **7,000–9,000 lux** with shadows **on**.
  - **Shadow casting:** enable it for arena `near_field` and `midground` (trees, fence, bushes) per `lax_render_policy.json`.
  - **Grounding shadows:** keep them on the characters, sticks, ball and goal.


## v9.2 (device screenshots 2026-09-25)
| Device issue | Fix |
|---|---|
| Goalie eyes read as "C" outlines on device (solid in Blender at every LOD) | Eyes now sit clearly proud of the skin (4 mm), with the highlights, lids and brows lifted to match. Small runtime depth or skinning differences can no longer bury the eye centre |
| Shooter hair looked like a "pumpkin" (grooves converging at the crown) | Strand grooves now flow from the centre part back into the bun (meridians around the bun), for both shooter and goalie |
| Faceted, hexagonal trees | The arena LODs no longer decimate trees, fence, shore bushes or foreground bushes (`export_lods(keep=...)`) |
| Ghostly pale far forest, and the lake glaring white | Soft background haze 22% → 10% with gentler smoothing; the lake is excluded from the soft copy; water is deeper blue and rougher (0.35) |

**Arena v9 budget now:** `_lod1` 460k tris / 22.0 MB; `_lod2` 325k tris / 16.5 MB (trees stay full quality in both).
Use `_lod1` on iPhone 17/18 Pro. Use `_lod2` if frame time is tight.


## v9.3: new cast, palette lock, dense net (concept sheets 2026-09-25)
| File(s) | Change |
|---|---|
| `lax_team_home_7.usdz` (+ LODs, clips) | **Mina #7** (v9): curly puff buns with purple headbands, goggles with purple hinges, cream/purple kit. Same name, rig, 78 clips, facing (−Z) |
| `lax_team_away_5.usdz` (+ LODs, clips) | **Ollie #5** (v9): teal helmet with gold stripe, curls under the helmet, gold/teal kit, gloves. Same name, rig, 78 clips, facing (+Z) |
| `lax_goal.usdz` | **Dense cream net** matching the props sheet (19 cords per side, 12 depth rings). Same 8 net clips and all sockets |
| `lax_shooter*`, `lax_goalie*` | Re-exported with the **official palette** (navy #0D2B52, coral #FF5A3C, cyan #31D8FF, gold #FFC629, cream #FFF9F4) |

All four characters validate with 0 errors, seamless loops and grip gaps of 2.5 cm or less. Preview: `Previews/RoundTrip/v9_cast_roundtrip.png`.
**Not converted yet:** fans, the boy field player and the girl goalie variant (still the v8 look).


## v9.4: expressions (from the expression sheet)
- **Delighted** (preset `big_smile`, used by every celebration clip): eyes close into happy "^" arcs, the mouth opens and the brows lift.
- **Sheepish** (preset `disappointed`, used by the miss reactions): worried brows, a small frown and the eyes glancing aside.
- **Blinks** now read as cute closed eyes (oval lids with the "^" arc) instead of skin rectangles.
- **Parked lids** sit 55° up, fully under the hair and helmet, so there are no forehead artifacts at rest.
- **Rig:** new joints `happy_L` / `happy_R` (reserved, in the head-protected set) and `lid_open_deg` = 55 on all v9 characters.
- **Re-exported:** `lax_shooter*`, `lax_goalie*`, `lax_team_home_7*` (Mina), `lax_team_away_5*` (Ollie). Clip names, frame ranges and sockets are unchanged.
- **Preview:** `Previews/V9/v9_expressions.png`.


## v9.5: props + environment kit
- **Sticks** (props sheet): cream heads and pockets, silver shafts, wrapped grips, on all v9 characters.
  - Rae: dark wrap. Kit: navy wrap. Mina: purple strings and wrap. Ollie: teal strings.
  - The standalone `lax_stick_attack` / `lax_stick_goalie` match.
- **Arena v9 (`lax_arena_pinebrook_v9*`):**
  - plank fence with bolts and stone footings;
  - ground foliage, flowers and a rock at every tree base;
  - daisy tufts;
  - a lakeside log cabin with glowing windows, and distant snow-capped mountains (both in `far_background`).
  - `_lod1` is now 495k tris; use `_lod2` (352k) if frame time is tight.
- **Re-exported:** `lax_shooter*`, `lax_goalie*`, `lax_team_home_7*`, `lax_team_away_5*`, `lax_stick_attack*`, `lax_stick_goalie*`, `lax_arena_pinebrook_v9*`.


## v9.1 corrective export (Codex device review of `dda6ac2`), validated in **RealityKit**
Validation uses Apple RealityKit's offscreen `RealityRenderer` on macOS 27 (`Tools/rkcap.swift`): the packaged USDZs are loaded
with `Entity.load`, lit by the kit EXR as image-based light plus a warm directional sun with shadows, with `GroundingShadowComponent`
on characters and goal, from `camera_gameplay`. Captures are in `Previews/RealityKit/`.

| Device issue | Root cause (found in RealityKit, not Blender) | Fix |
|---|---|---|
| Pale, washed out; skin grey-green; weak whites and navy | Atlas materials had a **clear coat (0.12) at near-mirror roughness (0.03)**. RealityKit renders it as a mirror film reflecting the bright sky and grass over every surface. The EXR was also 2.2× brighter than intended | Clear coat 0; roughness floored at 0.35 in every character atlas; **EXR restored to its original brightness** |
| Eyes look closed or narrow | Near-mirror glossy eyes reflected the grey sky, so only the dark rims read | Roughness floor; the eyes now read as open, dark and glossy with white highlights (`v91_ready_face_*.png`) |
| Faint grounding | Over-bright image-based fill washed out the sun and grounding shadows | Dimmer EXR, so shadows read at the same sun intensity |
| Distant shore reads as a wall of pale spikes | Uniform cones plus the hazed, smoothed soft copy | Mixed pines and round trees, varied heights and tier counts, irregular spacing with gaps, undulating ground, varied rocks; the shoreline is now in `midground` (no haze copy) |
| Thin, low-contrast stick pocket | Cream on cream against a white ball | Warm tan pocket and backing under the cream rim (shooter) |

**Recommended RealityKit lighting** (see `v91_game_recommended.png`):
- image-based light intensity exponent **0.5** (1.0 also works now that the EXR is corrected);
- warm directional sun at **8,000–9,000 lux** with shadows;
- `GroundingShadowComponent` on the characters, sticks, ball and goal.

**Re-exported:** `lax_shooter*`, `lax_goalie*`, `lax_arena_pinebrook_v9*` (`_lod1` now 422k tris) and `Lighting/lax_env_pinebrook_1k.exr`.
Filenames, skeletons, clips, frame ranges, events, root motion, sockets, arena root, groups and markers are unchanged.

**Pending:** `lax_team_home_7` / `lax_team_away_5` (Mina, Ollie) still carry the old clear coat and will be re-exported next.


## v9.6: teammate "triangular shards", root cause and fix (release blocker)
**Reproduced** in RealityKit (`Tools/rkbatch.swift`, captures in `Previews/RealityKit/v96/`, with the before state in
`v96_BEFORE_teammates_lods_shards.png`). The **base** teammate files were correct; **every `_lod1` / `_lod2` file** shattered, even at rest
with no animation. The app loads teammates at LOD1, which is why only Mina and Ollie showed it. Hero LODs had the same defect but are
loaded at LOD0.

**Root cause:**
- `export_lods()` protected every head/face-weighted vertex from decimation (for readable faces) while still demanding a global target
  of 60% / 30%.
- The v9 heads (curls, puffs, lids, goggles, cage) hold most of each mesh's vertices, so the decimator pushed **all of the reduction onto
  the torso and legs**. Those collapsed into a few huge triangles spanning unrelated atlas islands: multicoloured, disconnected shards.
- Collapse decimation also flipped windings on the overlapping toy shells. Blender draws both sides of every face; RealityKit culls back
  faces. That's why Blender-side checks, which also framed only the faces, missed it.
- A USD audit of skinning, joint order, bind/rest, animation samples, subsets, n-gons and vertex counts found nothing wrong: the defect
  was purely geometric.

**Fix and exporter guard:**
- Character LODs no longer decimate geometry (`CHAR_LOD_DECIMATE = False`). They carry the full mesh with **1024 textures** (lower
  memory); about 40–47k tris per character is well within budget.
- Any future LOD decimation runs `_lod_repair()` (consistent outward winding, custom normals cleared, smooth shading).
- The arena keeps its (correct) tree-protected decimation via `protect=False`.
- **Guard for future characters:** validate every LOD full-body in RealityKit (`rkbatch`), never just the face.

**Re-exported with the fixed LOD step and the v9.1 material fix** (clear coat 0, roughness floor 0.35):
- `lax_team_home_7*` (Mina) and `lax_team_away_5*` (Ollie): base, `_lod1`, `_lod2`, clips.
- `lax_shooter*` and `lax_goalie*`: LODs repaired.

Filenames, skeletons, joint order, 78 / 38 clips, frame ranges, events, sockets, facing, scale and origin are unchanged. All four
validate with 0 errors and grip gaps of 2.5 cm or less.

**RealityKit validation** (image-based light exponent 0.0, 8,000 lux sun with shadows, grounding shadows):
- `v96_teammates_lods_and_clips.png`: Mina and Ollie base / LOD1 / LOD2 at rest, plus LOD1 in `idle_relaxed` (730), `idle_competitive`
  (810), cradle (68), aim (210), release (214), celebrate (168), disappointed (540). All full-body intact.
- `v96_heroes_lods.png`: Rae and Kit base / LOD1 / LOD2.

**Validation workflow:** `Tools/rkbatch.swift` renders any list of packaged characters, LODs, frames and cameras from a JSON config
(examples `rk_val.json`, `rk_heroes.json`). Build: `swiftc -O -parse-as-library -o rkbatch rkbatch.swift`; run: `./rkbatch config.json`.

**Still to deliver (next pass):** expression and blink frame tables with close-ups, a held-stick readability pass at `camera_gameplay`,
and the `camera_result_goal` / `_miss` / `_save` / `camera_cast_review` markers with reference captures.
