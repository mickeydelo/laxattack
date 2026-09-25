# v8.1 Runtime Validation & Mobile Optimization (2026-09-24)

This pass validates the v8 exports and adds contingency and policy files. **No v8 production export was modified.**

## 1. Canonical reference render
- `Previews/Reference/canonical_reference_camera_gameplay.png`: 1206×2622, the iPhone 17 Pro native resolution.
- `Previews/Reference/canonical_reference_settings.json`: exact settings, visible and hidden groups, lights, scene frame.
- **Built only from packaged USDZs, in the app's current configuration (`dof_fallback`):**
  - **Visible groups:** gameplay, near_field, midground, far_background_soft, foreground_framing_soft.
  - **Hidden groups:** ambient_twins (the ambient layer is active), collision_only, far_background, foreground_framing,
    camera_markers, crowd_markers, shadow_only.
  - **Characters:** shooter in cradle (frame 70) with a white reference ball (r = 0.07 m) at `pocket_socket`; goalie in
    `goalie_ready`; six `_lod1` fans seated at bleacher markers with the corrected offsets.
  - **Layers:** ambient and life layers active.
- **Camera:** `camera_gameplay` (−0.30, 4.30, 7.00) aimed at (−0.15, 0.40, −3.50) in game space, 50° vertical FOV, no
  camera DOF.
- **Blender lighting approximates the intended look:**
  - warm sun (1.0, 0.84, 0.62) from high behind-left of the goal;
  - cool rim light and a sky-gradient world;
  - AgX view with no look, exposure +0.6.
  - RealityKit targets are in LIGHTING_KIT.md.
- **Finding for v8.2:** `far_background_soft` is hazed too strongly (55% toward sky blue). At phone size it reads as milky fog
  over the treeline, which matches the pale blobs in device screenshots. The v8.2 proposal is a lighter haze (about 25%) with
  saturation kept. Not changed here, per instructions.

## 2. Transform-animation exports: validated with RealityKit (macOS, `Entity.load(contentsOf:)`)
| File | Root animations | Root duration | Entities / models loaded |
|---|---|---|---|
| lax_arena_ambient.usdz | `global scene animation` (AnimationGroup) + `default subtree animation` | 11.333 s (= 340 frames) | 153 / 50 |
| lax_arena_life.usdz | same | 20.333 s (= 610 frames) | 92 / 35 |
| lax_fx_confetti.usdz | same | 3.200 s (96 frames; frames 96–105 are the static landed pose) | 183 / 90 |
| lax_shooter.usdz (reference) | same | 85.233 s (= 2557 frames) | 16 / 1 |

- **All child-transform tracks are exposed through the root as one playable timeline,** the same mechanism as the characters.
  Play `root.availableAnimations[0]` ("global scene animation") and slice by the JSON ranges. Descendants also carry "default
  subtree animation" entries; ignore them.
- **Packaged-file checks** (pxr, USDZ re-opened):
  - `ambient_loop` seam 0.000 m; `ambient_gust` starts and ends on the rest pose (0.000 m).
  - `life_loop` seam 0.000 m; `birds_startle` starts and ends exactly on the `life_loop` frame-0 pose (0.000 m), so it returns
    cleanly.
  - `confetti_burst`: all 90 pieces lie flat on the turf (max height 4 mm) from frame 96. Hiding the entity about 2 s later
    leaves no residual geometry, because the pieces are children of the one entity.
  - Every animated child transform survives export (46 / 35 / 90 animated prims).

## 3. Skinned fallbacks (contingency only; originals untouched)
| Alternate | Animated root / skeleton | Joints | Meshes / materials | Size | Textures | Entities / models in RealityKit |
|---|---|---|---|---|---|---|
| lax_arena_ambient_skinned.usdz | `lax_arena_ambient_skinned` / `lax_arena_ambient_skinned_rig` | 47 | 1 / 1 | 2.40 MB | 128² palette (same as original) | 6 / 1 |
| lax_arena_life_skinned.usdz | `lax_arena_life_skinned` / `lax_arena_life_skinned_rig` | 36 | 1 / 1 | 0.80 MB | 128² palette | 6 / 1 |
| lax_fx_confetti_skinned.usdz | `lax_fx_confetti_skinned` / `lax_fx_confetti_skinned_rig` | 91 | 1 / 1 | 0.32 MB | 128² palette | 6 / 1 |

- Each alternate has exactly one `SkelAnimation`, the same 30 fps timeline and frame ranges (manifests copied with
  `fallback_of`), and the same world placement and scale (identity transforms, game-space geometry).
- **Equivalence** (packaged files, USD skinning evaluator vs the transform originals): identical vertex counts, with centroid
  and bounds differences ≤ 0.006 mm at every sampled frame, including mid-gust, mid-startle and mid-confetti. Skeleton bone
  error vs the original transforms ≤ 0.011 mm.
- **Cost difference:**
  - Texture memory: identical.
  - Runtime memory: slightly higher (4 joint indices and weights per vertex, about +0.9 MB for the ambient layer; negligible
    for the others).
  - CPU: much lower. The transform versions update 46 / 35 / 90 entity transforms every frame and submit 50 / 35 / 90
    mesh draws; the skinned versions update one skeleton and submit one draw each.
  - GPU: skinning cost is tiny.
  - **Recommendation:** keep the transform versions unless device profiling or testing shows a problem. The skinned versions
    are drop-in replacements (same clips) and are the better choice on low-tier devices.

## 4. Mobile performance audit (all production exports)
Texture memory is an upper-bound estimate: RGBA8 with mip chain, before any GPU compression.

| Asset | MB | Meshes | Tris | Joints | Animated prims | Materials | Tex mem MB |
|---|---|---|---|---|---|---|---|
| lax_arena_ambient | 2.22 | 50 | 53762 | 0 | 46 | 1 | 0.2 |
| lax_arena_ambient_skinned | 2.40 | 1 | 53762 | 47 | 0 | 1 | 0.2 |
| lax_arena_life | 0.43 | 35 | 4020 | 0 | 35 | 1 | 0.2 |
| lax_arena_life_skinned | 0.80 | 1 | 4020 | 36 | 0 | 1 | 0.2 |
| lax_arena_pinebrook | 19.00 | 107 | 189526 | 0 | 0 | 4 | 72.9 |
| lax_arena_pinebrook_lod1 | 7.77 | 107 | 94986 | 0 | 0 | 4 | 22.5 |
| lax_arena_pinebrook_lod2 | 5.52 | 107 | 38652 | 0 | 0 | 4 | 22.5 |
| lax_arena_pinebrook_mobile | 10.55 | 107 | 189526 | 0 | 0 | 4 | 22.5 |
| lax_boy_field | 6.70 | 1 | 34456 | 43 | 10 | 1 | 50.3 |
| lax_boy_field_lod1 | 4.92 | 1 | 20673 | 43 | 10 | 1 | 16.8 |
| lax_boy_field_lod2 | 4.87 | 1 | 19945 | 43 | 10 | 1 | 16.8 |
| lax_fan_a | 2.75 | 1 | 12360 | 43 | 0 | 1 | 16.8 |
| lax_fan_a_lod1 | 2.49 | 1 | 5562 | 43 | 0 | 1 | 16.8 |
| lax_fan_a_lod2 | 2.33 | 1 | 2224 | 43 | 0 | 1 | 16.8 |
| lax_fan_b | 2.27 | 1 | 10311 | 43 | 0 | 1 | 16.8 |
| lax_fan_b_lod1 | 2.06 | 1 | 4638 | 43 | 0 | 1 | 16.8 |
| lax_fan_b_lod2 | 1.92 | 1 | 1854 | 43 | 0 | 1 | 16.8 |
| lax_fan_c | 2.49 | 1 | 11109 | 43 | 0 | 1 | 16.8 |
| lax_fan_c_lod1 | 2.25 | 1 | 4998 | 43 | 0 | 1 | 16.8 |
| lax_fan_c_lod2 | 2.11 | 1 | 1998 | 43 | 0 | 1 | 16.8 |
| lax_fx_confetti | 0.34 | 90 | 1080 | 0 | 90 | 1 | 0.2 |
| lax_fx_confetti_skinned | 0.32 | 1 | 1080 | 91 | 0 | 1 | 0.2 |
| lax_girl_goalie | 5.90 | 1 | 38352 | 45 | 10 | 1 | 50.3 |
| lax_girl_goalie_lod1 | 4.03 | 1 | 23010 | 45 | 10 | 1 | 16.8 |
| lax_girl_goalie_lod2 | 3.95 | 1 | 21623 | 45 | 10 | 1 | 16.8 |
| lax_goal | 0.64 | 1 | 5208 | 10 | 0 | 1 | 16.8 |
| lax_goalie | 5.82 | 1 | 36428 | 45 | 10 | 1 | 50.3 |
| lax_goalie_lod1 | 3.96 | 1 | 21855 | 45 | 10 | 1 | 16.8 |
| lax_goalie_lod2 | 3.87 | 1 | 20234 | 45 | 10 | 1 | 16.8 |
| lax_shooter | 6.52 | 1 | 27008 | 43 | 10 | 1 | 50.3 |
| lax_shooter_lod1 | 4.96 | 1 | 16201 | 43 | 10 | 1 | 16.8 |
| lax_shooter_lod2 | 4.81 | 1 | 13511 | 43 | 10 | 1 | 16.8 |
| lax_stick_attack | 0.82 | 1 | 3744 | 3 | 4 | 1 | 16.8 |
| lax_stick_goalie | 0.90 | 1 | 3744 | 3 | 4 | 1 | 16.8 |
| lax_team_away_5 | 6.70 | 1 | 33792 | 43 | 10 | 1 | 50.3 |
| lax_team_away_5_lod1 | 4.90 | 1 | 20274 | 43 | 10 | 1 | 16.8 |
| lax_team_away_5_lod2 | 4.88 | 1 | 19912 | 43 | 10 | 1 | 16.8 |
| lax_team_home_7 | 6.52 | 1 | 26480 | 43 | 10 | 1 | 50.3 |
| lax_team_home_7_lod1 | 4.95 | 1 | 15886 | 43 | 10 | 1 | 16.8 |
| lax_team_home_7_lod2 | 4.81 | 1 | 13512 | 43 | 10 | 1 | 16.8 |

- **No transparent materials anywhere** (no alpha-blend overdraw). All geometry is opaque.
- **Top findings and recommendations:**
  1. **Character texture memory dominates.** LOD0 heroes carry a 2048 albedo + 2048 roughness + 1024 normal set (about 50 MB
     each uncompressed); `_lod1` / `_lod2` use 1024 sets (about 17 MB). Six LOD0 heroes would be about 300 MB. Use LOD0 only
     for the shooter and goalie, and `_lod1` for teammates. At gameplay distance the 1024 atlas is visually equivalent.
  2. **Helmeted LOD2s save little geometry** (about 20k tris) because heads are protected from decimation for face
     readability. For distant use, `_lod1` vs `_lod2` makes little difference except on the shooter and teammate #7.
  3. **The arena is 107 meshes and 4 materials** (190k tris in the full and mobile versions, including hidden sharp/soft and
     twin duplicates). Only about 55% of those tris are visible in a given mode. A future "merged by group and material"
     export could cut draw calls from about 100 to about 15 without changing the view.
  4. **Flower beds are relatively tri-heavy for their size.** They are candidates for decimation in a merged-arena export.
  5. **Animated prims:** 46 (ambient) + 35 (life) + 90 (confetti) entity transforms per frame. Swap to the `_skinned`
     alternates on the low tier: identical visuals, one draw each.
- **Tier recommendation** (also in `lax_render_policy.json` → `tiers`):
  - **Low:** arena `_lod1`; heroes `_lod1`; up to 6 fans `_lod2`; ambient and life off (or `_skinned`); confetti on (or
    `_skinned`) with shadows off; key-light shadows only.
  - **Mid:** arena `_mobile`; shooter and goalie LOD0 with the rest `_lod1`; fans `_lod1` near and `_lod2` far; ambient, life
    and confetti on.
  - **High:** everything LOD0 except distant fans.

## 5. Machine-readable rendering policy
`Exports/lax_render_policy.json` (schema v1), documented in `RENDER_POLICY.md`. It encodes:
- default visibility, sharp/soft pairs, and the `native_dof` / `dof_fallback` modes;
- image-based light, unlit, shadow cast/receive, tier, optional, animated and post-exclusion flags per group or entity pattern;
- grounding-shadow scope and the tier configurations.

## 6. Contact and grounding
Lowest point of the baked skin at rest frames:

| Asset | Result | App offset needed |
|---|---|---|
| Shooter, goalie, boy field, girl goalie, teammates | 0.0 mm (feet exactly at root / field level) | **None** |
| Fans a/b/c | Feet 0.0–0.1 mm at root; hip contact 0.086 / 0.082 / 0.070 m above root (the manifest values) | **None beyond the manifest offset** |
| Goal | Rear ground bar lowest point −35 mm, intentionally half-sunk into the turf | **None** |
| Sticks | Origin is the grip; the shaft below reaches −64 mm | Attach at the hand socket; **none** |
| Ball | App-owned; ride `pocket_socket` (instantaneous ball centre) | — |

- **Sliding:**
  - Goalie shuffles and crossovers are authored against `root_motion_curve` (0.0 / ≤ 0.5 cm measured).
  - The switch dodges are authored against their root curves too.
  - The older dodges have no authored root motion; play them in place.
- **Shadows:** no baked shadow cards. Grounding shadows are runtime-only (see the policy file), so they attach to the contact
  points automatically.

## 7. Diagnostic scene
**Deferred.** Composing referenced USDZ packages into one package needs verification that RealityKit loads nested and
flattened skinned assets reliably. The canonical reference render plus the per-asset RealityKit probe cover most regression
checks in the meantime.

## Required runtime changes
1. Play only `root.availableAnimations[0]` ("global scene animation") on ambient, life and confetti, sliced by the JSON
   ranges. The current approach is correct.
2. Optionally adopt `lax_render_policy.json` instead of name-based rules.
3. Tiering: LOD0 textures only for the shooter and goalie on mid tier; `_skinned` alternates on low tier.
