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
