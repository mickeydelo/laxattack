# Lax Attack — Visual Style Bible (art-direction checkpoint)

Status: **v1 — superseded.** Mickey supplied reference key art on 2026-09-23 (vinyl-toy figures, ~45% head+helmet, dark glossy toy eyes, helmets on all field players, red/cream home vs navy/teal away, golden-hour light, lush textured turf, stronger miniature DOF, broadleaf woods + fence + lakeside). A reference-aligned v2 revision of this bible follows in the next commit. (v1 rendered 2026-09-23, Blender 5.2.2 LTS, EEVEE.)
Source scene: `3D/Production/StyleValidation/LaxAttackStyleValidation.blend` (rebuild: `3D/Production/Tools/style_validation.py`).
Renders: `3D/Production/Previews/StyleValidation/`.

The target is an original handcrafted miniature lacrosse playset: collectible toy figures on a tabletop diorama,
photographed with a gentle miniature lens. Toy-diorama principles only — no copied characters, shapes, UI or places.

## 1. Proportions (figurine standard)

| Measure | Girl field hero | Boy goalie | Rule |
|---|---|---|---|
| Overall height (to hair/helmet top) | ≈1.51 m | ≈1.53 m | Game scale stays 1.5 m (graybox contract) |
| Head height / total | ≈38% | ≈35% bare head, ≈40% with helmet | 35–42% |
| Head radii (x, y, z) | 0.262, 0.248, 0.268 | 0.268, 0.250, 0.262 | Cranium dome +5–7%, jaw taper 12–16% |
| Shoulder half-width / height | 0.19 / 0.875 | same | Shoulders tuck just under the chin |
| Upper / fore arm | 0.23 / 0.26 | same | Kept from graybox so pose data transfers |
| Glove size | 0.135 × 0.12 × 0.15 | 0.17 × 0.15 × 0.18 | Oversized: glove ≈ half the head width |
| Leg (hip→ankle) | 0.39 | 0.39, wide stance ±0.13 | Short, sturdy, chunky shoes (0.245 m long) |
| Eye (half-width × half-height) | 0.050 × 0.059 | 0.049 × 0.057 | Eyes ≈ 19% of face width each; big irises + two highlights |

Accepted example: `04_character_close.png`, `04b_character_bust.png`.
Rejected: `R1_rejected_realistic_head_ratio.png` — head scaled to ≈25% reads as a generic mobile athlete; loses charm and face readability at phone size.

## 2. Shape language
- Every form is a rounded "manufactured" volume: superellipsoids (exponent 0.4–0.7) for gloves, shoes, pads, boards; lofts for torso, kilt, shorts; swept tubes for limbs, pipes, cords, hair locks.
- Characters are **rigid toy segments** (head, torso, arm and leg segments, gloves, shoes) that meet at hidden joint balls — intentional assembly seams, no skin-stretch artifacts.
- Hair is sculpted grouped locks on a smooth shell with a clean hairline; never strands.
- Faces are painted-on toy faces: sclera, iris, pupil, two highlights, a thin upper lash line, small nose bump, blush discs, a dark mouth decal.
- Equipment silhouettes are exaggerated: big helmet shell with a four-bar cage, oversized stick heads, chunky cleats.
- Environment: rounded diorama slab with a visible soil skirt; tiered scalloped pines; clustered-blob deciduous canopies; faceted-then-bevelled rocks; cloud clusters with flattened bases.

## 3. Bevel / softness standards
- No knife edges anywhere a camera can see. Box-like forms use superellipsoid exponents ≤0.4 (≈2–4 cm apparent bevel at character scale).
- Rocks: convex hull, limited dissolve, 3-segment bevel at 18% of the smallest dimension.
- Minimum tube radius on visible cords/strings is 4.5 mm (stick pocket) and 12 mm (goal net) — enlarged so strings survive at phone size.

## 4. Materials and roughness ranges
One flat UsdPreviewSurface value per material (no textures in the checkpoint). Values in `lax_core.MATS` are the runtime values.

| Class | Roughness | Metallic | Coat |
|---|---|---|---|
| Skin (painted resin) | 0.50–0.55 | 0 | 0 |
| Hair (sculpted vinyl) | 0.40–0.42 | 0 | 0 |
| Eyes / pupils (gloss paint) | 0.20–0.30 | 0 | 0 |
| Fabric kit (jersey, kilt, shorts, socks) | 0.72–0.75 | 0 | 0 |
| Molded plastic (helmet, goggles, stick head, pads) | 0.28–0.35 | 0 | 0.25 |
| Rubber (soles, grips) | 0.85 | 0 | 0 |
| Painted metal pipes (goal) | 0.32 | 0.35 | 0.3 |
| Cage metal | 0.30 | 0.85 | 0 |
| Cord / net | 0.80–0.85 | 0 | 0 |
| Turf / soil / bark / rock | 0.78–0.90 | 0 | 0 |
| Water | 0.12–0.15 | 0 | 0 |

The **roughness spread is the material language**: fabric vs. plastic vs. skin must differ.
Rejected: `R2_rejected_uniform_gloss.png` — roughness 0.12 + coat on everything turns skin and cloth into wet plastic and flattens material separation.

## 5. Palette
- Team identity: blue `kit_blue (0.02,0.16,0.62)`, navy `(0.01,0.03,0.13)`, white `(0.86,0.87,0.88)` (linear).
- Accents: coral `(0.95,0.28,0.14)`, gold reward `(1.0,0.62,0.05)`, teal `(0,0.45,0.45)`.
- Goal pipes: painted red `(0.75,0.035,0.02)`. Ball: yellow `(1.0,0.72,0.02)`.
- Environment greens stay slightly desaturated relative to the kit so characters pop: turf `(0.10,0.36,0.06)` / mow stripe `(0.075,0.28,0.045)`, pine `(0.02,0.16,0.08)`.
- Distance is cooled: mountains `(0.20,0.30,0.42)` → far `(0.38,0.50,0.66)`; sky horizon warm cream → zenith blue.
- Skin set: light / tan / brown / deep. Neutral lineup clay `(0.62,0.60,0.57)`.
Accepted: `02_lineup_final.png` vs neutral `01_lineup_neutral.png` (shapes must read in clay first).

## 6. Lighting setup (look-dev reference for RealityKit)
- Key: warm sun `(1.0,0.93,0.82)`, 4.6 W/m², soft angle 11°, from front-left above the shooter (Blender euler 48°, 0, −35°).
- Rim: cool area light `(0.80,0.88,1.0)`, 900 W, 6 m, behind the goal (3.5, −9, 5).
- Fill: the sky gradient only (horizon `(0.95,0.86,0.70)` → mid `(0.52,0.68,0.93)` → zenith `(0.16,0.38,0.95)`, strength 1.1).
- AgX view transform, Punchy look, exposure +0.25. EEVEE ray-traced shadows + AO for soft contact shadows.
- RealityKit equivalent: one warm directional light with soft shadows + a sky-gradient IBL; do not add harsh fill.

## 7. Camera and lens
- **Runtime camera (current Swift):** from (0, 2.9, 6.1) to (0, 0.95, −3.85), vertical FOV 52°. Validated in `03_gameplay_portrait_runtime_camera.png` — readable, recommended to keep.
- **Candidate three-quarter camera:** game coords from (0.35, 3.6, 7.2) to (−0.3, 0.7, −3.6), vertical FOV 44° (`cam_three_quarter`). Slightly offset to the shooter's stick side; keeps the whole shooter, goalie and goal in frame. Offered for evaluation, not a contract change.
- The portrait frame is narrow (horizontal FOV ≈25° at 52° vertical): anything framing the playfield must sit inside ±0.23×distance of the view axis.

## 8. Depth of field
- Restrained miniature blur only: f/1.4 equivalent (Blender lens ≈44 mm), focus ≈7.8 m (between shooter at ≈5.6 m and goal at ≈12.8 m). Foreground corners ≈14 px blur, far background ≈6 px at 720 px width; shooter/goalie/goal stay sharp.
- Accepted: `07_portrait_three_quarter_dof.png` vs `08_portrait_three_quarter_no_dof.png`.
- Rejected: `R3_rejected_heavy_dof.png` (f/0.4) — blurs the goalie and goal; never allowed.
- DOF is optional polish for RealityKit (post-process); gameplay must read without it.

## 9. Character and environment scale
- Game units are meters. Characters ≈1.5 m. Goal mouth 2.0 × 2.0 m, pipe radius 0.045, net depth 2.1 m, crease radius 2.2 m (stylized smaller than regulation for readability).
- **Ball:** production sticks are sized for a **0.08 m visual ball radius**. The runtime currently renders a 0.12 m sphere, which is larger than any believable stick head. Recommendation for the Xcode agent: render the ball at 0.08 m visual radius (the physics collider can stay 0.12 m).
- Diorama layers used in the checkpoint: foreground rocks/grass/props (y 2.4–4.6), field slab (y −13…6, 0.45 m soil skirt), boards/benches, bleachers + fans behind the goal flanks (y −13.6), woods at the sides (y −14…−25), lake (y −42), far pine line (y −58), mountains (y −95/−130), clouds (z 12–22).
- Keep the area directly behind the goal low (bushes ≤0.9 m) so the lake band and dark woods give contrast behind the net and ball.

## 10. Detail budget rules
- Hero figure 25–45k triangles (girl ≈25k, goalie ≈33k incl. stick). Spectator figures reuse the hero builder at lower segment counts.
- Nothing smaller than ~1.5 cm at character scale unless it is a face feature; expressions must read at 60 px head height.
- Stick pocket: ≈20 swept cords (enlarged); goal net: grid of 12 mm cords; no strand hair, no dense foliage cards near camera.
- One material per class; share materials across heroes; no texture sets yet (≤1× 2048 per hero allowed later).
- Test everything at iPhone scale: `09_iphone_scale_contact_sheet.png` shows frames at 390 px width.

## 11. Facial system (checkpoint result)
Bone-driven, export-safe (joint transforms only): lids collapse by bone scale (0.1 open → 1.0 closed), mouth decal authored open and collapsed by jaw scale (0.14 closed line → 1.0 open), mouth corners translate, brows translate/tilt, eyes rotate for aim. Presets: neutral, blink, focused, determined, smile, big_smile, strain, surprise, disappointed, smirk. See `10_facial_expressions.png`.
Fixes made during the checkpoint: authored mouth enlarged (it was unreadable in `big_smile`), expression ranges increased ~1.5×, goggle frame placed along the surface normal so it no longer covers the mouth.

## 12. Accepted examples
`02_lineup_final.png`, `03_gameplay_portrait_runtime_camera.png`, `04_character_close.png`, `04b_character_bust.png`, `05_goal_net.png`, `06_environment_layers.png`, `07_portrait_three_quarter_dof.png`, `09_iphone_scale_contact_sheet.png`, `10_facial_expressions.png`.

## 13. Rejected experiments and reasons
| Experiment | File | Reason |
|---|---|---|
| Realistic head ratio (~25%) | `R1_rejected_realistic_head_ratio.png` | Generic, faces unreadable at phone size, loses toy charm |
| Uniform high gloss | `R2_rejected_uniform_gloss.png` | No material separation; skin/fabric look wet |
| Heavy tilt-shift (f/0.4) | `R3_rejected_heavy_dof.png` | Blurs goalie/goal — breaks gameplay readability |
| Radial-scaled face gear placement | (iteration) | Goggles drifted down over the mouth; fixed by normal-offset placement |
| Flat turf stripe tiles | (iteration) | Soil showed between stripe slabs as dirt lines; fixed with a continuous base + stripe bands |
| Cage bar at eye level | (iteration) | Hid the goalie's eyes; bars moved to brow / below-mouth / chin |

## 14. Known look-dev limits
- Blender preview uses EEVEE ray tracing and AO; RealityKit will need its own light tuning to match.
- No baked textures yet: all tonal variation comes from lighting and geometry.
- Trees and crowd in the checkpoint are static; motion arrives in Phases 5–6.
