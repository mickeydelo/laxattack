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


## Part 2b (this push)
### Changed runtime exports
- `lax_fan_a*`, `lax_fan_b*`, `lax_fan_c*`: **genuinely lightweight LODs**. LOD1 is about 50% and LOD2 about 25% of the base, using
  uniform decimation plus `_lod_repair` (no head protection, which is what caused the v9.6 shards). Validated in RealityKit up close and at
  seat distance: `v97_fan_a_lods.png`, `v97_fan_bc_lods.png`.
- `lax_arena_pinebrook_v9*`: first cozy step, a flower border along the fence base and warmer fence wood. **Known limitation:** at
  `camera_gameplay` distance the border is still too subtle and the corner drifts fall outside the frame (`v97_pinebrook_before_after.png`).
  Next iteration: larger, denser blooms and corner drifts placed in frame.
- **New** `lax_cinematic_cameras.json`: release, goal-impact, celebration, save, miss, replay-wide and a portrait four-character cast
  camera. Each has position, target, vFOV, duration, blend in/out, an explicit move (push / settle / arc) and peak time. The
  `goal_replay_2s` sequence is release → impact → celebration. All seven are RealityKit-captured in `v97_cinematic_cameras.png`.
  `lax_review_cameras.json` is unchanged.
- `lax_result_timing.json` (v2, `23e31cc`) re-verified: 16 entries, 0 violations of the clip-local rules.

### Performance budget (measured from the exports)
| Asset | Base tris | LOD1 | LOD2 | Tex MB (base) | Tex MB (LOD1/2) |
|---|---|---|---|---|---|
| `lax_shooter` | 30,736 | 30,736 | 30,736 | 16.0 | 16.0 |
| `lax_goalie` | 44,980 | 44,980 | 44,980 | 16.0 | 16.0 |
| `lax_team_home_7` | 39,344 | 39,344 | 39,344 | 16.0 | 16.0 |
| `lax_team_away_5` | 44,160 | 44,160 | 44,160 | 16.0 | 16.0 |
| `lax_boy_field` | 44,824 | 44,824 | 44,824 | 16.0 | 16.0 |
| `lax_girl_goalie` | 46,312 | 46,312 | 46,312 | 16.0 | 16.0 |
| `lax_fan_a` | 21,664 | 10,831 | 5,414 | 16.0 | 16.0 |
| `lax_fan_b` | 26,840 | 13,420 | 6,710 | 16.0 | 16.0 |
| `lax_fan_c` | 29,788 | 14,893 | 7,446 | 16.0 | 16.0 |

| Asset | Tris | Tex MB |
|---|---|---|
| `lax_arena_pinebrook_v9_lod1.usdz` | 294,975 | 37.3 |
| `lax_arena_pinebrook_v9_lod2.usdz` | 194,435 | 37.3 |
| `lax_arena_ambient_v9.usdz` | 138,112 | 10.7 |
| `lax_arena_life.usdz` | 4,020 | 10.7 |
| `lax_goal.usdz` | 7,688 | 16.0 |
| `lax_fx_confetti.usdz` | 1,080 | 10.7 |

**Recommended tiers:**
- **Standard / high:** arena LOD1 + ambient + life + goal; heroes at base; teammates at LOD1; **5 fans at LOD2** (about 32k tris total).
- **Low memory:** arena LOD2 + ambient + life; heroes at LOD1 (1K textures); teammates hidden or LOD2; **2 fans at LOD2**; confetti allowed.
- **Crowd culling:** fans more than 14 m from `camera_gameplay` use LOD2; cull fans more than 22 m away or outside the frustum.

### Ambient choreography recommendations (Swift)
- **Fans:** a per-instance random phase (0–100% of the loop) and playback speed 0.9–1.1×.
  - Idle pool: `crowd_idle` 50%, `crowd_watch_*` 30%, `crowd_anticipate` 15% (only while the shooter aims), `crowd_wave` 5%, at most once
    per 30 s per fan.
  - Reactions start staggered by 0 / 0.12 / 0.25 / 0.4 s so the crowd is never synchronised.
- **Ambient layer:** loop `ambient_v9_loop` at 1.0×. It is authored to be desynchronised internally, so don't randomise its speed.
- **Life layer:** unchanged; random phase at load.
- **Ready cycle:** as in part 1 (Rae 70 / 20 / 10, Kit 55 / 20 / 15 / 10, no repeat within 10–12 s).

### Gameplay readability
From `camera_gameplay`:
- Kit's `goalie_ready` stance leaves the five-hole and all four corners visible (see `v96_gameplay_camera.png`).
- The ambient motion (trees at the frame edges, a boat on the far lake, clouds) never crosses the shooter → goal lane.
- The life-layer butterflies stay over the hedges.

### Device-validation checklist
1. Load the arena LOD1 + `lax_arena_ambient_v9` + life + goal. The trees sway, the boat drifts, and nothing is duplicated or missing.
2. Fans: LOD2 at seat distance shows no shards; staggered phases.
3. `goal_replay_2s` plays release → impact → celebration from `lax_cinematic_cameras.json`; Rae's delighted face lands at the celebration
   peak.
4. The save and miss cameras show Kit's save and Rae's sheepish beat.
5. The four-character cast camera shows everyone head to toe with foreground framing hidden.
6. The frame rate holds with 5 fans + life + confetti + a result animation (standard tier).

### Known limitations and next steps
- The cozy-look pass needs a stronger second iteration (flower scale and density, corner drifts in frame, lake shallows, cabin glow as
  a true emissive).
- Flower and foreground foliage breeze is not animated yet (the merged meshes need splitting into pivots).
- There are no new fan choreography clips yet; the recommendations above use the existing 12 crowd clips.


## Part 2c (this push): cozy-look pass 2 + breeze (runtime exports)
Grounded in `camera_gameplay` geometry: the frame's bottom edge meets the ground at z ≈ 2.8 and is only about ±1.3 m wide there, and the
fence is about 12 m away. Pass 1's corner drifts sat outside the frame and its fence flowers were too small.

| File | Change |
|---|---|
| `lax_arena_ambient_v9.usdz` (+ clips) | Adds **16 swaying flower groups**: 14 fence-border segments of large clumps (cream / yellow / coral / lilac blooms with tall lupin spikes), plus right and left lower-corner drifts beside the shooter, clear of the shot lane. Breeze: 1.0–1.8° per group with its own phase and cycle count. **34 objects, 193k tris, 1 material, 7.0 MB.** Same timeline, `ambient_v9_loop` 0–340 |
| `lax_arena_pinebrook_v9*` | Flower groups moved to the ambient layer; **new lighter turquoise lake shallows** along the near shore; warmer fence planks. `_lod1` 284k / `_lod2` 190k tris |

- **Before/after from `camera_gameplay`:** `Previews/RealityKit/v97/v97_pinebrook_before_after.png`. The flowering fence line behind the
  goal and the framed lower corners now read at gameplay distance.
- **Short RealityKit sequence:** `v97_realitykit_sequence.png` runs Ready (loop frame 0) → Ready (frame 170, ambient motion) → release →
  goal impact → celebration → miss → save.
- **Cinematic captures re-rendered** with the new world: `v97_cinematic_cameras.png`.

**Budget update:**
- Standard tier: arena LOD1 284k + ambient 193k + life 4k + goal 8k ≈ **489k scenery tris**, plus characters.
- If frame time is tight, the ambient layer can skip the fence-border flower groups (`v9_flowers_00`–`13`, about 50k tris); the corner
  drifts are the most visible and cheapest to keep.

**Known limitations:**
- `cine_goal_impact` crops Kit at the left edge; it needs a small re-aim next pass.
- The cabin-window glow is still a bright albedo, not a true emissive (the palette material has no emissive channel).
- Fans are not placed in these captures: the v9 arena has no bleacher seats in `camera_gameplay` view, so the seat markers need review.


## Part 2d (this push): fans in view, impact camera, cabin glow, lakeside
| File | Change |
|---|---|
| `lax_arena_pinebrook_v9*` | **New `v9_benches`:** two warm toy benches with backrests behind the goal, flanking it at game z −10, x ±2.55–3.65, facing the field. **New `M_glow_window_v9`:** a true emissive material (emissiveColor 1.0, 0.66, 0.30) on the cabin windows, kept out of the palette (arena materials: palette, glow, sky, turf ×2). **New `v9_lakeside`:** a small dock and reed clusters. `_lod1` 287k / `_lod2` 191k tris |
| **NEW** `lax_arena_pinebrook_v9_seats.json` | Six bench seats (`bench_left_seat_01..03`, `bench_right_seat_01..03`), seat-top y 0.445, yaw 180; the same `fan_root_offset_below_seat_m` contract; tier picks (standard: 5 fans on LOD2 with idle phases; low: 2) |
| `lax_cinematic_cameras.json` (v2) | `cine_goal_impact` re-aimed to position (2.6, 0.9, −3.3), target (−0.45, 0.85, −5.4), vFOV 48, so Kit is fully in frame |

**Why:** the legacy `bleacher_*` seats (game z −14.4) sit behind the v9 fence and flower border and outside the portrait frustum, so fans
there are never seen. The markers file is unchanged; use the new seats file for v9.

**RealityKit validation (`Previews/RealityKit/v97/`):**
- `v97_gameplay_fans.png`: five LOD2 fans visible on the benches from `camera_gameplay`, clear of the goal mouth and the shot lane.
- `v97_save_fans.png`: fans in the save shot.
- `v97_cine_goal_impact.png`: the re-aimed impact camera.
- `v97_cabin_glow.png`, `v97_dock.png`: detail checks.

**Known limitations:**
- The cabin glow is subtle in full daylight at that distance; it will matter for the future dusk and night fields.
- The dock and reeds are mostly hidden by the shore bushes from gameplay angles (cheap, about 3k tris; kept for the wide and cinematic
  shots).


## Part 2e (this push): concept-comparison pass + camera proposal (no asset changes)
Side by side, the concept gameplay mockup vs the RealityKit `camera_gameplay` frame. Gaps ranked by impact:
1. **Camera framing (biggest gap):**
   - The concept camera is further back, lower and tighter: the goal spans ~45% of the width, Kit is large, and Rae is full-body in the
     lower third.
   - Ours is high (4.3 m) and wide (50°), looking steeply down, which leaves a band of empty grass and a small goal.
   - **Proposal `camera_gameplay_cozy_PROPOSAL`** (in `lax_cinematic_cameras.json` v3): position (−0.3, 3.0, 10.0), target (−0.1, 0.8, −4.5),
     vFOV 34. See `v97_camera_proposal_cozyD.png`; A–C are the rejected explorations (C puts Rae over the left post).
   - **Adopting it needs aim-mapping and hit-zone recalibration on the Swift side;** `camera_gameplay` is unchanged.
2. **Foreground framing:** the concept has soft, out-of-focus bushes along the bottom edge. With the cozy camera, the flower and tuft
   foreground already frames the bottom. True blur needs runtime depth of field, which is still unavailable, so larger low bush masses
   at the bottom corners are the asset-side next step.
3. **Field lines:** the concept's are cream and about 1.5× thicker. Next: switch the line material to cream #FFF9F4 and widen the lines.
4. **Warmth on the characters:** mostly runtime (sun colour 1.0 / 0.84 / 0.62 is already warm). Optionally try image-based light exponent
   0.25 for a softer fill if faces read hard.
5. **Lakeside detail:** from the cozy camera the lake band and sailboat read well. The dock and reeds are hidden by shore bushes (kept,
   cheap).
6. **Sky:** the capture tool hides the sky group; on device confirm the sky backdrop fills the top band with the cozy camera.


## Part 2f (this push): women's lacrosse field markings
`lax_arena_pinebrook_v9*` (all LODs), group `gameplay` (object `field_markings`, unchanged name). Replaces the stylised v8 lines
(2.2 m crease and a 6.4 m arc) with the **women's goal-area layout**, scaled to the game field (goal centre at game z −5.7):

| Marking | Spec |
|---|---|
| Crease (goal circle) | radius **2.75 m** (18 ft diameter); goal line across the 2 m mouth |
| Goal line extended | from the crease edge to each sideline: the 12 m fan's straight edge |
| **8 m arc** | radius 8 m, ±50° about the field axis; **5 hash marks** at 0°, ±18°, ±36°; **two radial lines** from the arc ends to the crease (the pie slice) |
| **12 m fan** | radius 12 m, clipped by the stylised sidelines (x ±6.3), meeting them at game z ≈ +4.5 |
| Sidelines | x ±6.3 (unchanged) |

- **Lines:** cream (#FDF5E6-ish) and about 1.5× thicker (tube radius 0.06 m, strips 8–10 cm), per the concept-gap list.
- **Turf:** the worn ring in the field turf texture now follows the 2.75 m crease.
- **Gameplay fit:** Rae's default spot (−0.72, 0, 1.72) is 7.45 m from the goal centre, on the 8 m arc (the free-position spot). Kit
  (z −4.95) is inside the crease.
- **Captures:** `v97_markings_top.png` (top-down layout check), `v97_markings_gameplay.png`, `v97_markings_cozy.png`.
- **Runtime:** if any gameplay logic referenced the old 2.2 m crease radius (e.g. a crease-violation check), update it to **2.75 m**.


## Part 2g (this push): women's lacrosse sticks + dangling string tails (baked + cloth-ready)
**Characters re-exported** (`lax_shooter*`, `lax_goalie*`, `lax_team_home_7*`; rigs, joint order, clips, sockets and metadata unchanged):
- **Rae and Mina, women's field head:** flared scoop, slim throat, side-profile offset with a scoop hook, a **shallow** diamond pocket
  (depth 4.5 cm) with **two thick vertical runners**, and the shooting strings.
- **Kit:** her goalie head gains the tails.
- **Boys keep men's sticks:** Ollie and #22 (not re-exported).
- **Dangling tails**, in the pocket colour: two long ones at the throat and two short ties per sidewall. **Baked physics:** each tail is
  weighted from `stick` at the knot to `pocket_01` / `pocket_02` at the tip, so it swings and lags with the existing baked pocket motion.
  **No new joints.**
- **Fix:** the pocket backing now follows the true teardrop outline. Previously it poked past the rim at the scoop.
- **Validation:** `Previews/RealityKit/v97/v97_womens_stick_rae_cradle.png` (cradle frames 60 / 66 / 72 / 78 plus release 114; the tails
  visibly change angle) and `v97_womens_sticks_mina_kit.png`.

**Cloth-ready tails for RealityKit cloth simulation (iOS 27), opt-in:**
- **NEW** `lax_stick_tails_womens_attack.usdz` and `lax_stick_tails_womens_goalie.usdz`: six thin double-sided ribbon tails per stick,
  generated from the same definitions as the baked tails and authored in **stick-socket space**. Stage is Y-up with raw coordinates, so no
  rotation is needed.
- **NEW** `lax_stick_tails_cloth.json`: prim names, **pin vertex indices** per tail (the knot pair, to be set kinematic), lengths, root
  positions, per-character colours and suggested cloth settings.
- **Runtime recipe:**
  1. Parent the tails entity to the transform that follows the `stick` joint (the same follow system as the ball), with an identity local
     transform.
  2. Add a `ClothSimulationComponent` on a root and a `ClothBodyComponent` per tail (the ribbon is both simulation and visual mesh).
  3. Mark the `pin_vertices` kinematic.
  4. Suggested behaviour: inextensible strings, low bend, medium-high damping so they settle in ~0.4 s.
- **To avoid doubled strings:** the character files still carry the baked tails as the working fallback. If cloth tails are adopted,
  request the no-baked-tail character exports (build flag `STICK_TAILS_NONE`).
