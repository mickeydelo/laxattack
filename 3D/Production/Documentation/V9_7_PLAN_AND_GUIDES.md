# v9.7: supporting cast + animation, world and cosmetic guides

## Part 1 (this push): supporting cast in the v9 style (runtime exports)
| File | New look | Contract |
|---|---|---|
| `lax_boy_field*` | #22 home field: cream helmet with coral stripe, curls, cream/coral kit, gloves, tan pocket | Original `BOY_FIELD` rig, 78 clips, facing −Z |
| `lax_girl_goalie*` | #30 away goalie: navy helmet with gold stripe, low bun, navy/gold kit with pads | Original `GIRL_GOALIE` rig, 38 clips, facing +Z |
| `lax_fan_a*` | Pigtails with coral ties, coral home tee; big cheer | Original spectator rig, 12 crowd clips |
| `lax_fan_b*` | Navy ball cap with cyan brim, navy away tee; cool reactions | Same |
| `lax_fan_c*` | Small kid: teal knit beanie with gold pom-pom, gold sweater | Same (smaller body scale) |

- **Style:** v9 face (open glossy eyes, "^" delighted, sheepish glance), clear coat 0, roughness floor 0.35, official palette.
- **LODs:** full-body with 1K textures and **no decimation**. The fan builder's old destructive 55% "hero" decimation is removed for v9.
- **Validation:** RealityKit, `Previews/RealityKit/v97/`. `v97_cast_body_lods.png` shows all five at base / LOD1 / LOD2;
  `v97_cast_faces.png` shows Ready / blink / delighted / sheepish for #22 and #30, and Ready / cheer / groan for each fan.
- **Validation frames:** #22 uses the field timeline (Ready 756, blink 742, delighted 159, sheepish 530). #30 uses the goalie timeline
  (13, 28, 525, 256). Fans: Ready `crowd_idle` 24, cheer 240, groan 340.

## Result performances (`Exports/lax_result_timing.json`)
Clip-local peak times for Swift to hold (0.25–0.35 s) while the result camera is on:
- **Goal:** Rae `celebrate` delighted peak; Kit `goalie_goal_against` → `goalie_stick_spin`; the net impact clip for the zone;
  `confetti_burst` at impact; `birds_startle` at impact + 0.1 s; fans `crowd_goal_cheer` staggered by 0 / 0.15 / 0.3 s.
- **Miss:** Rae `disappointed` sheepish peak (alternates `near_miss_reaction`, `weak_miss`, `pipe_reaction`); Kit a restrained nod.
- **Save:** Kit `goalie_save_*` contact frame, then the `goalie_stick_raise` proud peak; Rae `save_reaction`.

## Ready-state weighted cycle (recommendation)
| Character | Primary (weight) | Secondary | Rare personality | Rules |
|---|---|---|---|---|
| Rae | `cradle` / `idle_competitive` (70%) | `idle_relaxed` (20%, every 6–10 s) | `idle_nervous` or `goal_glance_back` (10%, ≥ 20 s apart) | Never repeat a variation within 12 s. Start each loop at a random phase |
| Kit | `goalie_ready` (55%) | `goalie_ready_lively` (20%), `goalie_scan` (15%) | `goalie_center_taps` (10%, every 8–14 s) | `goalie_stick_spin` only after a goal against. Minimum repeat 10 s |
| Teammates | `idle_relaxed` / `idle_competitive` | `cradle` | `goal_glance_back` | Random phase per instance |
| Fans | `crowd_idle` / `crowd_watch_*` | `crowd_anticipate` before a shot | `crowd_wave` (rare) | Per-fan phase 0 / 33 / 66%; reactions staggered 0–0.3 s |

- **Blinks** are authored every 2–3.5 s; random loop phases keep characters unsynchronised.
- Use the non-blink frames in `lax_expression_frames.json` for deterministic captures.

## Environment roadmap (briefs only; do not build yet, Pinebrook first)
All five reuse the Pinebrook modular kit (turf tile, crease and lines, goal, fence sections, popcorn tree, pine, rock stacks,
bushes, flowers, cabin, clouds) through palette swaps plus a few hero props.
- **Maple Hollow (autumn park / fieldhouse):**
  - Popcorn trees in orange, red and gold palettes, with leaf litter decals on the turf.
  - A brick fieldhouse, a gazebo (from the kit sheet) and lamp posts.
  - Golden-hour sun; a cream / rust / plum palette.
- **Beacon Lights (night game):**
  - Floodlight poles (kit sheet) with warm spill; bleachers and banners; fireflies in the life layer.
  - Deep navy sky, lit windows, rim-lit characters.
  - Needs a night image-based-light EXR and point or spot lights.
- **Harbor Point (sunset coast):**
  - Rock shoreline, a lighthouse, cottages and dune grass, with sailboats.
  - Coral/peach sky EXR; water glints are warmer.
- **Cedar Fieldhouse (indoor, rainy day):**
  - A wood-panel gym, banners, skylights with rain streaks, and warm interior light.
  - The turf tile becomes a sport-court variant.
- **Snowcap Meadow (winter):**
  - The snowy evergreen (kit sheet), snow caps on the fence and rocks, a frozen pond, and bright cool light with warm accents.

## Cosmetic-ready construction
| Variant | Method | Animation impact |
|---|---|---|
| Jersey colorways (Coral Classic, Harbor Blue, Maple Gold) | **Material swap:** a second atlas albedo per colorway, same UVs | None |
| Stick wraps and pocket colours | **Material swap** on the stick region of the atlas, or a small per-stick atlas | None |
| Helmet stripe and decal variants | **Material swap** (stripe colour in the atlas) | None |
| Hair ties, headbands, ribbons | **Optional child meshes** skinned to `head` (toggle visibility) | None; same skeleton |
| Ball trail colours | Runtime particle / trail colour; references `#31D8FF`, `#FFC629`, `#FF5A3C` | n/a |
| Celebration variants (hop, raised stick, spin) | **Extra clips** on the same rig, appended to the manifest | Additive; same rig |
| New hair styles or silhouettes | **Separate exported asset**, only if the silhouette changes | Same rig and clips |

## Queued for v9.7 part 2+
Ambient choreography (fans chatting and clapping, breeze on trees and flowers, cabin glow, slow clouds), result-performance polish,
cinematic camera JSON with RealityKit captures, the Pinebrook cozy-look pass with before/after captures, a short RealityKit capture
sequence, and the performance budget.


## Part 2a (this push): Pinebrook ambient choreography (runtime exports)
| File | Change |
|---|---|
| **NEW** `lax_arena_ambient_v9.usdz` (+ `_clips.json`) | One root timeline, `ambient_v9_loop` (0–340, 11.33 s, seamless). 10 near trees + 6 shore trees sway 0.6–1.3° with per-tree phase, amplitude and whole-cycle frequencies (never in sync); the sailboat drifts ±0.9 m, bobs and rolls; clouds drift ±1.6 m. 18 objects, 138k tris, 1 palette material, 4.8 MB |
| `lax_arena_pinebrook_v9*` | The static trees, shore trees, clouds and boat **moved** into the ambient layer (no duplicates). `_lod1` is 284k tris; arena + ambient total about 421k, the same as before |

**Runtime:**
- Load `lax_arena_ambient_v9.usdz` at the origin alongside the v9 arena, and play `root.availableAnimations[0]` looped (the same pattern
  as the v8 ambient).
- Keep `lax_arena_life.usdz` (birds, butterflies, duck, glints).
- **Do not load** the old `lax_arena_ambient.usdz` with v9.
- **The ambient layer is now required:** without it the arena has no near trees, shore trees, clouds or sailboat.

**Validation:** `Previews/RealityKit/v97/v97_ambient_loop_f000_f170.png` shows the production stack from `camera_gameplay` at loop
frames 0 and 170.

**Exporter note for future ambient assets:** animate **pivot empties**, never mesh objects. The USD post-process clears mesh xform ops,
which is why meshes must sit at identity under an animated pivot. Capture world matrices before deleting any parents.
