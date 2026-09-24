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


## v4 update (Codex brief: ambient fix, boats, DOF staging, crowd markers)
- **Ambient v2 is transform animation only (no skeleton).** Every animated object has its own local pivot:
  - trees: `amb_tree_NN` at the trunk base, `amb_tree_NN_canopy` on the trunk (canopy lags the trunk);
  - hedges: `amb_hedge_NN`; flags: `amb_flag_NN` plus the `_seg1..3` chain;
  - boats: `amb_boat_NN` at the waterline; clouds: `amb_cloud_NN`.
  - The axis conversion sits on `lax_arena_ambient_content`; `/lax_arena_ambient` is identity.
- **Static twins group renamed:** `midground_trees` → **`ambient_twins`** (trees, hedges, flags, boats, clouds). It is built
  from the same geometry functions.
- **Packaged-USDZ validation** (vertex-accurate, both files reopened):
  - frame 0 of `ambient_loop` == static twins: max offset **0.000 m** (seamless swap);
  - loop seam 0.000 m; `ambient_gust` starts and ends on the rest pose (0.000 m);
  - no objects in the lake except the two boats; nothing near the origin (50/50 objects checked);
  - round-trip render from `camera_gameplay`: `Previews/RoundTrip/arena_ambient_camera_gameplay.png`.
- **Boats rebuilt:** closed hull (red, seated about 30% below the waterline), deck, mast, two closed double-sided sails, and a
  pennant. They sit behind the field at game (5.0, −26) and (−8.0, −30). Motion is asynchronous bob, roll, yaw and lateral
  drift, all seamless.
- **Foliage:** leaf-cluster canopies (20 clusters, dark interior, sunlit tops), fuller hedges.
- **DOF focus references** (in `camera_markers`, game space), with distances from `camera_gameplay`:
  - `gameplay_focus_center` (−0.36, 0.9, −1.99): about 9.5 m
  - `foreground_focus_reference` (0, 0.4, 3.0): about 5.4 m
  - `far_background_focus_reference` (0, 1.0, −31): about 38.5 m
  - Suggested native DOF: focus on `gameplay_focus_center`, f-stop about 1.2–2.0 equivalent. The shooter (about 7.5 m) and
    goal (about 12.5 m) should stay inside the sharp band.
- **Crowd markers** (group `crowd_markers`, plus `Exports/lax_arena_pinebrook_markers.json` with game positions and yaw):
  - `bleacher_home_seat_01..06` on the new home bleacher (game +X side) and `bleacher_away_seat_01..06` (game −X side);
  - `sideline_home_01..03` and `sideline_away_01..03` on benches at game x = ±6.0;
  - Markers sit on the seat surface. Place a fan root at marker − `fan_root_offset_below_seat_m` (in the JSON), rotated by
    `yaw_deg_about_game_Y`.
- **Turf:** a flattened traffic path from the shooter spot to the crease front. Hero tufts appear only near the camera, with
  varied scale, lean and colour (including dry tips).
