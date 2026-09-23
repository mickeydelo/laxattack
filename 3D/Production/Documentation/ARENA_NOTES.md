# Arena Notes — Pinebrook (v3)

Rebuilt by `3D/Production/Tools/build_arena.py`. Source: `3D/Production/Arena/LaxAttack_Arena.blend`.

## Exports
| File | Triangles | Size |
|---|---|---|
| `lax_arena_pinebrook.usdz` (LOD0) | 144254 | 16336 KB |
| `lax_arena_pinebrook_lod1.usdz` | 72244 | 14513 KB |
| `lax_arena_pinebrook_lod2.usdz` | 29073 | 13014 KB |

Every prim is identity (axes baked into geometry).

**Transform acceptance test** (Codex): no foliage or prop mesh may sit inside a 4 m cube at the origin.
- LOD0: 50 meshes checked, **0** near the origin.
- LOD2: **0** near the origin.

**Root cause of the old defect:** objects placed via `.location` were baked from a stale `matrix_world`. The exporter now
forces a depsgraph update first.

## Grass recipe (per brief)
1. **Field turf:** one unique 2048² PBR set covering the whole field (`field_albedo.jpg`, `field_normal.png`,
   `field_roughness.jpg`).
   - Contents: blade streaks, clump noise, baked micro-AO, 1.6 m mowing bands, large-scale colour variation, and a brighter
     maintained centre lane.
   - The meadow outside the field keeps the tileable 1K `turf_albedo.png`.
2. **Story masks** (baked into the unique set): worn crease ring, heavy goal-mouth wear, and a worn shooting spot. Field
   lines remain separate crisp geometry (`field_markings`).
3. **Hero tufts** (`hero_tufts`): sparse, full modeled clumps along the crease edge, around the shooter and in the camera
   foreground. The ball corridor (|x| < 0.9 m between shooter and goal) is kept clear.
4. **Foreground frame** (`foreground_framing`): corner hedges, post with bottle, rock, bag, balls.

## Depth-of-field fallback
Toggle one of each pair at runtime.

| Sharp group | Pre-softened group |
|---|---|
| `far_background` | `far_background_soft`: smoothed geometry, haze-tinted toward sky blue, matte |
| `foreground_framing` | `foreground_framing_soft`: smoothed, lighter/desaturated, matte |

- A painted `sky_backdrop` gradient cylinder sits behind everything, so no black void can show.
- Gameplay groups (turf, goal, players, ball) stay sharp.

## Ambient life (`lax_arena_ambient.usdz`, 2026-09-23)
A separate animated asset so it can be toggled per performance tier. Source: `Arena/LaxAttack_Ambient.blend`
(`Tools/build_ambient.py`). One skinned mesh, about 55k tris, 2.5 MB.

**Contents:** 7 broadleaf trees and 2 pines (height-weighted sway: trunks planted, canopies lead), 9 hedges behind the goal,
4 pennant flags on fence poles (3-bone flutter chains), 2 sailboats (bob, roll, slow drift), 5 clouds (glide).

**Clips:**
- `ambient_loop` 0–240: seamless 8 s breeze.
- `ambient_gust` 250–340: stronger gust, blended from the loop.

**Usage:** place it at the origin with the arena. While it is shown, **hide the static arena group `midground_trees`**; those
are the static twins of the same trees and hedges.

## Mobile variant
`lax_arena_pinebrook_mobile.usdz` is identical but uses 1024 field textures (about 8 MB vs 16 MB). The LOD1/LOD2 files also
use the 1024 set.

## Groups
Under `/lax_arena_pinebrook/lax_arena_content`: gameplay, near_field, midground, midground_trees (static twins of the ambient trees/hedges), far_background, far_background_soft,
foreground_framing, foreground_framing_soft, shadow_only (reserved), collision_only (`collision_ground`; hide it),
camera_markers.

## Camera markers
Each has a `_target` empty:
- `camera_gameplay`, `camera_aim`, `camera_release`
- `camera_goal_left`, `camera_goal_right`
- `camera_save_left`, `camera_save_right`
- `camera_celebration`, `camera_results`

## Still to do
- 4K source texture set.
- Flag, water and tree animation.
- Material atlasing (49 materials).
