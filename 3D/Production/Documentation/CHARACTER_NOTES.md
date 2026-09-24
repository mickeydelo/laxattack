# Character Notes

Blender 5.2.2 LTS. Builders: `3D/Production/Tools/lax_figure.py` (skeleton, meshes, face, sticks), `lax_pose.py` (pose model),
`lax_anim.py` (clips, baking, secondary), `build_girl_field.py` (girl hero). Look: `VISUAL_STYLE_BIBLE.md` v2.

## Skeleton families
Both families share one bone layout so clips transfer; the goalie family adds `chest_pad` and `throat_guard`.

| Group | Bones |
|---|---|
| Body | root, pelvis, spine, chest, neck, head |
| Face | jaw, mouth_L/R (children of jaw), eye_L/R, lid_L/R, brow_L/R |
| Arms | clavicle, upperarm, forearm, hand, fingers, thumb (_L/_R) |
| Legs | thigh, shin, foot, toe (_L/_R) |
| Secondary | hair_01–03 (ponytail chain), hem_F, hem_B |
| Stick | stick (top-hand grip, +Y shaft, +Z pocket face), pocket_01 (bag belly), pocket_02 (upper channel) |
| Controls (not exported) | ik_hand_L/R (children of stick), ik_foot_L/R, pole_elbow_L/R, pole_knee_L/R |

`root` never moves. Jumps, dodges and saves use pelvis motion only.

## Proportions
Figures are designed in a 1.5 m design space and transformed at build time. Body segments scale by `body_scale` about the
ground. Head-driven parts scale by `head_k` about the neck top. Sticks are unscaled. Pose data is authored in design space and
`apply_pose` scales it by the rig's `body_scale` custom property.

| Hero | body_scale | head_k | Height | Tris (incl. stick) | Materials |
|---|---|---|---|---|---|
| Girl field (`lax_shooter`) | 0.82 | 1.15 | ≈1.46 m (1.61 m with raised stick) | 34,972 | 17 |
| Boy goalie (lookdev only; Phase 3) | 0.84 | 1.15 | ≈1.48 m | ≈36k | — |

## Facial system
Bone-driven, chosen because joint transforms export reliably to USD/RealityKit. Blend shapes were not used.

- **Lids:** skin shells authored closed and collapsed by lid-bone Y scale (0.1 open, 1.0 closed).
- **Mouth:** a decal authored open and collapsed by jaw Y scale (0.14 closed line, 1.0 open); mouth corners translate.
- **Brows and eyes:** brows translate and tilt; eyes rotate for aim.
- **Presets** (`lax_figure.FACE`): neutral, blink, focused, determined, smile, big_smile, strain, surprise, disappointed, smirk.
- **Eye aim:** `eye` pose parameter, in degrees.
- **Export check:** these face channels are baked into every clip and exported through UsdSkel. Blender-side renders confirm
  them. Runtime confirmation of joint *scale* playback is still pending (see KNOWN_ISSUES).

## Sockets (lax_shooter)

| Socket | Parent bone | Purpose |
|---|---|---|
| stick_socket | stick | Top-hand grip; stick frame (+Y shaft, +Z pocket face in Blender) |
| pocket_socket | pocket_01 | **Resting ball centre** for a 0.08 m ball; rides pocket compression |
| ball_contact_socket | pocket_01 | Bottom of the bag (extra) |
| helmet_socket | head | Helmet centre, identity orientation in asset space |
| effect_socket | chest | Chest front, identity orientation |
| left_hand_socket / right_hand_socket | hand_L / hand_R | Glove centres |

Rest positions in USD asset space are recorded in `3D/Production/Exports/lax_shooter_clips.json`.

## Girl field hero
Home team, #10.
- **Kit:** red helmet with cream stripe and light cage; hair below the helmet rim plus a ponytail with a red scrunchie; cream
  jersey with red numbers; red shorts; brown gloves; white socks and shoes.
- **Face:** dark toy eyes with two highlights, thin brows, lash line, blush.
- **Mesh parts** (separable for customization): head, face, hair, headgear, kit, limbs, gloves, shoes, stick.
- **Personality:** head-tilted focused idle with blink, bouncy celebrate jump, smirk on dodge recovery.

## Collision
Keep RealityKit's simple character collider. Do not use skinned meshes for collision.


Phase 1 commit: `3ef396d58503f5e7844da3cee169684900893c22`.


## Boy goalie (Phase 3)
Away team, #3.
- **Kit:** navy helmet with teal stripe and throat guard; navy jersey with white numbers; chest protector worn under the
  jersey colour (skinned to `chest_pad`); black oversized gloves.
- **Stick and stance:** goalie stick with a teal head and white pocket; goalie stance ±0.13 m wider.
- **Proportions:** body_scale 0.84, head_k 1.15; 36,164 tris incl. stick; 17 materials.
- **Sockets:** 6 required + ball_contact_socket. Asset-space positions are in `lax_goalie_clips.json`; they lie on the +Z side,
  confirming the facing.
- **Export:** `face_plus_z=True`. The rig prim gets `rotateY(180)` before the axis conversion; the `/lax_goalie` root stays
  identity at field level.
- **Runtime note:** the procedural goalie was lifted to a 0.625 m base height. This asset's origin is at field level (y = 0).


## Phase 7 heroes
Both heroes are built by `Tools/build_phase7_heroes.py` from the shared rigs and clip libraries. An additive personality layer
changes how they move, not when, so all frame ranges match the family hero.

- **lax_boy_field** (home #22): brown skin, short dark hair under the red helmet, black gloves, attack stick. 34,192 tris.
  - Personality: confident swagger (chest up, head bob, side sway, smirks).
  - Clips: same names and ranges as `lax_shooter` (see ANIMATION_NOTES).
  - Faces −Z.
- **lax_girl_goalie** (away #30): deep skin tone, ponytail and hair below the navy helmet, goalie stick. 38,088 tris.
  - Personality: springier knee bounce, head sway, big-smile celebrations.
  - Clips: same names and ranges as `lax_goalie`, with shooter-perspective left/right.
  - Faces +Z.

**Validation:** 0 errors; reach errors ≤1.8 cm; loop seams ≤4e-5; baked Y 0.000…1.630 (boy) and −0.017…1.656 (girl goalie).


## Women's field kit (girl shooter update)
Women's field lacrosse uses a different kit from the men's game, per Mickey's reference photo.
- `lax_shooter` now wears protective **goggles** (no helmet), a white headband and ponytail, a red jersey with a cream #10, a
  red **kilt**, and bare hands on the stick.
- **Unchanged:** clip names, frame ranges, release/contact frames and sockets. `helmet_socket` still marks the head centre.
- 24,948 tris (lighter than the helmet version).
- `lax_boy_field` keeps the men's kit (helmet, gloves, shorts); its spec is now pinned explicitly.
- Goalies of both genders keep helmets, throat guards and chest protectors, which is correct for women's goalies too.


## Update: face without joint scale; new sockets; women's gloves
- **Lids:** skin patches hugging the head over each eye, rotated by `lid_L/R` about the head centre (open = rotated up onto the
  forehead).
- **Mouth:** a skin cover over the mouth decal, rotated down by `jaw` to open it. When closed, a smile line stays visible and
  the corners still translate.
- **No joint scale anywhere.** Presets are unchanged: blink, squint (`focused`), smile, open cheer (`big_smile`), grimace
  (`strain`), determined brows.
- **Eyes and mouth decals** are flattened to 3–6 mm so the patches sit nearly flush.
- **New sockets on every character:** `eyes_socket`, `camera_focus_socket`, `chest_socket`, in addition to the previous
  seven.
- **Women's field kit** now has thin white/red gloves, per the brief.


## Teammates (2026-09-23)
| Asset | Side | Kit | Facing |
|---|---|---|---|
| `lax_team_home_7` | home | women's field kit (goggles, headband + ponytail, jersey, kilt, gloves), deep skin, #7 | −Z |
| `lax_team_away_5` | away | navy helmet with teal stripe, navy kit, blond, #5 | +Z (faces the shooter) |

- Both use the full shooter-timeline library.
- **Behaviour mapping:** track ball = `idle_competitive`/`watch`; cut = `split_dodge_*`/`roll_dodge_*`; catch = `quick_stick_catch`;
  pass = `release_sidearm`; check = `face_dodge_*`; celebrate/react = the celebration and reaction clips.
- Add more variants by copying a spec line in `build_phase7_heroes.py`.


## v5: painted-vinyl texture atlases (2026-09-23)
Every character (heroes, teammates, fans) is now **one skinned mesh with one material** carrying a baked atlas
(`Tools/lax_atlas.py`). This replaces the 13–19 flat materials each character had before.

- **Albedo** (`<asset>_albedo.jpg`, 2048; 1024 for fans):
  - the original paint colours with subtle mottling (skin and face paint stay clean);
  - a soft top-lit gradient;
  - baked ambient occlusion (blurred, floor-clamped, 20% strength) for contact shading in creases.
- **Roughness** (`<asset>_rough.jpg`): per-material values ±0.07 noise, so there's no uniform plastic gloss.
- **Normal** (`<asset>_normal.png`, 1024): fabric weave on kits and gloves, sculpted strand bands on hair.
- Final material: UsdPreviewSurface with base colour, roughness and normal textures, metallic 0, a light coat.
- Textures live in `Characters/<Folder>/Textures/` and are packed inside each USDZ.
- LOD files reference 1024 copies (`*_1k`).
- **Packaged round trip** (`Previews/RoundTrip/atlas_characters_roundtrip.png`): all atlas textures load from the USDZs; eyes are
  open and mouths closed at rest; fans are seated on bleacher markers.
- **Thumbnails:** `Previews/Deliverables/characters_atlas_thumbnails.png`.


## v6 (2026-09-23): face finish, personality layer, props atlased
- **Clean faces.**
  - The lid and mouth-cover skin patches now taper flush with the skin at their borders and sit closer to it (lids 5.0 mm,
    mouth cover 4.5 mm), so no rectangles or shadow lines show.
  - Atlases force a perfectly flat normal everywhere except fabric and hair, using a baked material mask. This removes the
    UV-seam lines on skin, helmets and plastic.
- **Personality layer**, baked into every character's clips:
  - **Auto-blinks** every ~2–3.5 s on clips of 36+ frames. They never fall within 4 frames of a release or contact event or a
    loop seam. Short focused loops (`cradle`, `aim_*`) stay unblinking on purpose.
  - **Eye darts:** small saccades (±4°, ±2.5°) on calm clips (idles, cradle, aims, `goalie_ready`, `goalie_scan`, crowd
    idle/watch/anticipate, `run_loop`). Loops start and end on the authored gaze.
  - **Crowd:** each fan module has its own loop phase (0, ⅓, ⅔), so neighbours never move in sync.
- **Props atlased:** `lax_goal` (one material, 1024 atlas, 0.6 MB) and both sticks (`lax_stick_attack`, `lax_stick_goalie`;
  1024 atlases).
- **Clip ranges, events, sockets and manifests are unchanged.** The goal frame is now rigidly skinned to `goal_root` (merged
  with the net), and the hierarchy note in `lax_goal_clips.json` still applies.


## v7: charm pass (Mickey's device review, 2026-09-24)
- **Eyes:** 16% larger toy eyes with larger highlights. Lids stay open across expressions (`focused` 0.13, `determined` 0.15,
  `strain` 0.40) and brows are softer. This removes the sleepy/grumpy look.
- **Pocket:** a solid woven backing (`pocket_bag`) under the cords, skinned to the same pocket bones. The ball no longer shows
  through the string gaps from behind. The cradle pose now angles the pocket toward the gameplay camera.
- **Albedo:** atlases are lighter (softer baked occlusion, flatter top-lit gradient).
- **Goalie idles** (all goalies):
  - `goalie_center_taps`: tap the left pipe, re-centre, tap the right pipe, nod.
  - `goalie_stick_spin`: after a goal against, spins the stick twice in his hands and re-sets.
  - `goalie_ready_lively`: bounce, stick waggle, tracking head.
  - Existing idles remain: `goalie_tap_pipes`, `goalie_scan`, `goalie_reset_gloves`, `goalie_helmet_nod`.
