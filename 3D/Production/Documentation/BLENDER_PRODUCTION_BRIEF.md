# Lax Attack — Blender Production Brief

This is the authoritative art handoff for the iOS runtime. The target is an original, toy-like miniature sports diorama: warm saturated color, rounded silhouettes, softly beveled forms, gentle painted sheen, readable faces, and bouncy animation. Use the mood of a photographed tabletop playset without copying any Nintendo character, prop, logo, or location.

## Runtime contract

- Blender 4.x, 30 fps, meters, Y-up at export, identity root transforms.
- Gameplay forward is world `-Z`; shooters and goalie face one another on that axis.
- Keep each character root at field level. Animate locomotion in place unless a clip explicitly says otherwise.
- One USDZ and one JSON clip manifest per asset. Include clip start/end, loop flag, event frames, and socket names.
- Unique, stable ASCII names. No duplicate `.001` nodes. Apply mesh transforms before skinning.
- Maximum four joint influences per vertex. No negative scale. Verify bind poses after round-tripping the USDZ.
- Materials must survive USDZ: base color, normal, roughness, metallic, emissive, opacity. Pack ORM only if the exporter/runtime test confirms it.
- Deliver a neutral thumbnail render, wireframe/polycount sheet, texture list, and a RealityKit round-trip screenshot with every export.
- Character LOD targets: LOD0 45–70k triangles, LOD1 20–35k, LOD2 8–15k. Environment pieces need comparable 50% and 20% LODs.
- Texture budget: characters 2K atlases; hero goal/field 2K; small props 1K. Power-of-two maps with mipmaps and padding.

## Priority 0 — make the current match production-safe

1. **Female field shooter** (`lax_shooter.usdz`)
   - Women's field kit: goggles, ponytail, jersey, kilt, cleats, gloves; no helmet.
   - Fix the combined skinned-mesh bind transform problem currently seen in RealityKit.
   - Preserve sockets: `pocket_socket`, `ball_contact_socket`, both hands, head/eyes, and camera focus.
   - Add facial controls that work without joint-scale animation: blink, squint, smile, open-mouth cheer, grimace, determined brows.

2. **Male goalie** (`lax_goalie.usdz`)
   - Helmet/cage, throat guard, chest protector, goalie gloves, padded shorts and goalie stick.
   - Root at field level; no hidden base-height offset.
   - Sockets: stick hands, pocket, ball contact, chest, head/eyes, camera focus.

3. **Goal and net** (`lax_goal.usdz`)
   - Orange/red beveled pipe, thick readable white net, believable pocket depth.
   - Keep visual net separate from simple runtime collision proxies.
   - Sockets: sensor center, collision half-extents reference, center/high-left/high-right/low-left/low-right impacts.
   - Bake directional net impacts plus heavy impact, ripple, settle, and subtle wind idle. Net must return exactly to its rest pose.

4. **Pinebrook arena** (`lax_arena_pinebrook.usdz`)
   - Field, crease, boards/fence, benches, signs, lake, sailboat, rocks, layered trees and distant mountains.
   - Separate named groups: gameplay, near-field, midground, far-background, foreground-framing, shadow-only, collision-only.
   - Remove malformed or zero-area meshes and verify every node renders in RealityKit.

## Character animation library

All motion needs clear anticipation, readable key poses, 1–3 frames of impact compression, overshoot, and settle. Preserve foot plants and keep the ball release/contact event exact.

### Shooter core

- `idle_relaxed`, `idle_competitive`, `idle_nervous`, each 2–4 seconds with breathing, weight shifts, eye darts and occasional blink.
- `cradle_idle`, `aim_overhand`, `aim_bounce`, `aim_sidearm` seamless loops.
- `release_overhand`, `release_bounce`, `release_sidearm` with exact ball-release event frames.
- `quick_stick_catch` and `quick_stick_release` with pocket contact/release events.
- `split_dodge_left/right`, `roll_dodge_left/right`, `face_dodge_left/right`; in place, with root-motion metadata.
- Run start, run loop, stop, plant left/right, stumble recovery.
- Reactions: near miss, pipe, robbed/save, weak miss, goal glance-back.
- Celebrations: fist pump, jump-turn, stick twirl, knee slide, teammate point, restrained win, huge clutch win. Each needs short/medium versions.
- Transitions: every aim to every release; release to celebrate/disappointed/idle; avoid visible pose pops.

### Goalie core

- Ready, breathe, scan, tap pipes, reset gloves, tiny crease shuffles.
- Read left/right/high/low; shuffle and crossover steps.
- Saves: stick high/low left/right, body, five-hole clamp, kick, doorstep stuff, desperation dive, trail-stick recovery.
- Exact stick/body contact event frames and ball-contact sockets for every save.
- Goal-against reactions: look back, frustrated tap, shrug, reset; never mean-spirited.
- Celebrations: stick raise, helmet nod, small dance, big clutch save.

### Secondary motion

- Ponytail/hair, kilt hem, loose jersey, laces/tassels, net and stick pocket should use authored secondary rigs or baked simulation.
- Keep motion broad and stable for mobile. Avoid noisy high-frequency cloth simulation and interpenetration.
- Export bones/joints and bake the secondary result. Do not depend on unsupported runtime cloth.

## Sticks, balls, players, and crowd

- Separate attack and goalie sticks with replaceable shaft/head materials and pocket deformation clips: cradle, load, release, catch, save impact, settle.
- White hero ball plus color/texture variants; preserve regulation scale while exaggerating visible seams only slightly.
- Two modular base bodies (field and goalie), then inclusive face/hair/skin options. Boy and girl field players both need helmeted and women's-goggle configurations where rules require them.
- Teammate defenders/attackers: idle, track ball, cut, catch, pass, check, celebrate and react. Start with three silhouette/readability variants per side.
- Crowd modules: 6–10 low-poly spectators per repeating block, 3 palette variants, seated idle/cheer/gasp/wave loops. Keep faces simple and animation asynchronous.

## Grass recipe for the mockup look

Do not model a full field from individual blades. Use four layers:

1. **Turf base:** gently crowned field mesh with a tileable PBR set: saturated but plausible albedo, fine normal, roughness, AO and subtle height. Include large-scale color variation and mowing bands so repetition is invisible.
2. **Story masks:** vertex-color or secondary-mask control for worn crease/goal mouth, brighter maintained lanes, damp/darker edges and foot-wear patches. Field lines should be crisp decal/overlay geometry, not baked into the repeating tile.
3. **Hero tufts:** sparse instanced clumps only around the shooter, crease edge and camera foreground. Supply 3–5 crossed-card/low-poly tuft variants with wind phases and LODs.
4. **Foreground frame:** separate close grass, leaves, fence and bench props designed to sit out of focus at the lower corners. These sell the miniature lens more than adding geometry everywhere.

Required maps: base color, normal, roughness, AO/macro mask, wear mask. Provide a mobile 2K set and a 4K source set. Avoid glossy wet grass; use broad, soft highlights.

## Lighting and photographed-diorama staging

- Build under a soft warm key from upper-left, cool sky fill, and gentle rim separation. Test with contact shadows at feet, goal pipes, sticks and ball.
- Bevel all hero edges so highlights roll across them. Use painted-toy roughness variation rather than uniformly shiny plastic.
- Background must be layered at real depth: goal/players sharp, lake and trees softer, mountains/sky simplest. Keep high-frequency detail away from the scoring area.
- Supply a neutral HDRI/reference lighting setup and a color-script sheet for sunny morning, golden hour and stadium evening.
- Runtime will use subtle camera orbit and impact pushes. Frame extra geometry beyond portrait safe crop so movement never reveals an empty edge.
- Depth of field should be restrained: gameplay subjects and ball remain crisp. If native mobile DOF is unavailable or too expensive, the far-background and foreground groups need pre-softened texture/geometry variants for an optical-looking fallback.

## Environment and personality props

- Pinebrook wooden field sign, lake/sailboat, benches, fence modules, rocks, flowers, bottle, gear bags, flags and hand-painted sportsmanship banners.
- Animated details: flag breeze, water shimmer geometry, sailboat drift, tree sway, crowd loop, floating pollen/dust. Keep each independently toggleable for performance tiers.
- Goal celebration dressing: bench reaction sockets, crowd focus sockets, confetti origin points, camera-interest sockets.

## Camera and composition markers

Add empty transforms for `camera_gameplay`, `camera_aim`, `camera_release`, `camera_goal_left/right`, `camera_save_left/right`, `camera_celebration`, and `camera_results`. Each should include a paired `_target` empty. Compose for portrait with UI-safe headroom and keep the ball/goal readable at all times.

## Delivery checklist

- No missing textures; no Blender-only nodes; no unapplied transforms; no hidden accidental meshes.
- Animation names and event frames match JSON exactly.
- First and last frames of loops match in pose and velocity.
- Socket transforms are visible in a validation render and documented in meters.
- Test female shooter, male goalie, goal and arena together at world origin/goal-line coordinates.
- Test on a real iPhone through RealityKit before marking final.

