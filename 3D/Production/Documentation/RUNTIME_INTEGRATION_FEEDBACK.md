# Runtime Integration Feedback

Last updated: 2026-09-23 after RealityKit integration on iPhone 17 Pro / iOS 26.5.

This document is the handoff from the Swift/RealityKit runtime back to Blender. Treat the items under **Blocking** as the next export target. Do not change asset names, facing, scale, sockets, timeline ranges, or release/contact frames unless the JSON manifests and this document are updated together.

## Blocking export corrections

### Arena transforms

The first runtime export places these meshes around game origin rather than at their authored world positions:

- `tree_*`
- `bush_*`
- `pine_*`
- `cloud_*`
- `sign_slogan`
- `fg_post`
- `bottle`
- `equipment_bag`
- `rock_4`

They occlude the camera, shooter, and goal. Swift temporarily disables these names. `field_platform`, `field_markings`, `field_fence`, `sign_field`, `bleacher`, `lake`, `meadow`, `far_shore`, and `mountains_far` have usable game-space bounds.

Before the next export, apply/evaluate each affected object's world transform into the exported USD hierarchy or preserve its parent transform. Validate by reopening the USDZ and asserting that the affected meshes do not all overlap an origin-centred 4 m cube. Add the gameplay camera to the automated render check even though cameras are not included in the runtime package.

### Face animation

RealityKit on iOS 26.5 does not visibly reproduce the joint-scale face channels. The goalie appears with closed lids in its ready pose, confirming the risk recorded in `KNOWN_ISSUES.md`.

Convert facial animation to transforms RealityKit reliably plays:

- eyelids: rotation and/or translation, never scale;
- jaw/mouth opening: jaw rotation plus mouth-corner translation, never scale;
- preserve the current simple toy-eye and painted-mouth look;
- verify neutral, blink, focused, smile, strain, surprise, and disappointed expressions in a RealityKit-oriented USDZ preview.

The default frame must show open eyes and a closed, pleasant neutral mouth even if animation playback fails entirely.

### Shooter skin/bind transforms

The corrected women's shooter loads as one combined `lax_shooter_rig` render component with plausible aggregate bounds, but its runtime image shows visibly separated parts: a large white jersey/equipment-shaped mesh sits to the shooter's right and the stick shaft stretches vertically through the play space. Because RealityKit exposes the result as one combined skinned render component, Swift cannot quarantine only the broken submesh.

Rebuild and verify the bind pose after applying the women's kit changes:

- apply object transforms before armature binding/export;
- verify every mesh uses the intended armature modifier and inverse bind matrices;
- remove stale vertex groups/modifiers inherited from the helmeted version;
- ensure jersey, kilt, stick shaft/head/pocket, hands, and body occupy the correct pose at frame 0 and during `cradle`;
- reopen the packaged USDZ outside Blender and render frame 0 plus frames 60, 74, and 88 from the runtime camera.

Swift temporarily uses the procedural shooter by setting `useProductionShooter = false`. Re-enable it only after the packaged USDZ passes the runtime-camera check.

## Animation quality pass

Keep the current event frames because gameplay now consumes them directly from JSON.

### Shooter

- Preserve release events: overhand local 14, bounce local 14, sidearm local 13, quick-stick local 5.
- Give each aim loop a seamless breathing hold with visible eye focus and pocket tension, without moving the release pose.
- Strengthen silhouette changes between overhand, bounce, and sidearm at phone scale.
- Polish kilt, ponytail, headband tails, jersey hem, and pocket lag as baked secondary motion. Avoid cloth intersections and high-frequency flutter.
- Make plant foot, hips, chest, hands, stick, pocket snap, head follow-through, and recovery read as one kinetic chain.
- Split dodges remain in place, but poses must tolerate runtime root translation of roughly 0.32 m toward game ±X.
- Add clear reaction silhouettes: near miss follows the ball, pipe hit recoils through the hands/stick, save shows frustration without tantrum, goal celebration feels joyful and brief.
- Confirm `pocket_socket` follows the actual resting ball centre throughout aim and cradle clips and reaches the release position exactly on the event frame.

### Goalie

- Preserve save contacts: standard/high/low local 7, five-hole/body local 5.
- Ready and shuffle loops need open eyes, active stick tracking, weight transfer, and stable feet.
- Read clips must chain into matching save clips without a pop.
- Runtime now selects standard, high, low, five-hole, and body saves from the live ball position before contact. Every variant therefore needs a distinct, readable silhouette and its pocket/contact point aligned to the incoming-ball region.
- The goalie root stays at field level. All jumps/reaches remain pelvis/limb motion; no exported root translation.
- Add convincing save impact: pocket compression first, then shoulders/head recoil, then balanced recovery.
- Goal-against and goalie celebration should return cleanly to `goalie_ready` within a 0.2 s blend.

### Goal net

- Keep the mouth rim pinned and strengthen regional impacts for the gameplay camera.
- Ensure center/high-left/high-right/low-left/low-right are visibly distinct from the shooter-facing view.
- Heavy impact must read immediately without cords crossing the turf or front rim.
- `net_settle` should blend acceptably from any impact clip.

## Model and presentation checks

- Women's field shooter remains goggles/headband/ponytail, jersey, kilt, and no helmet.
- Check stick and hands for intersections in every release, dodge, quick-stick, and reaction key pose.
- Check kilt/legs and ponytail/back intersections over full clips, not only contact sheets.
- Keep the 0.08 m visible-ball contract and 0.12 m forgiving runtime collider.
- Preserve identity asset roots, meters, Y-up, shooter facing −Z, goalie/goal facing +Z.
- Preserve all socket names. Add automated socket-to-mesh distance checks at each release/contact frame.
- Provide one phone-resolution contact sheet per asset using the runtime camera and lighting direction.
- Provide one short H.264 viewport/runtime-camera playblast showing every clip in sequence; still contact sheets do not reveal timing or transition pops.

## Runtime-owned work

Swift owns camera kick/shake, root translation for dodges and goalie crease movement, ball physics/spin/curve, collision, target prediction, clip selection, release timing, haptics, score feedback, and reset cadence. Do not bake world-space ball flight, camera motion, or character root travel into the USDZ clips.

## Acceptance gate for the next export

1. No quarantined arena object overlaps world origin unless intentionally authored there.
2. Neutral frame has open eyes and closed mouth without relying on joint scale.
3. All manifests decode and every named clip slices successfully in RealityKit.
4. Shooter and goalie sockets are present and correctly located at all release/contact frames.
5. No feet below field level in idle/ready; no obvious cloth, hair, hand, helmet, stick, or body intersections.
6. Release/contact poses match the unchanged event frames.
7. Phone-camera playblast demonstrates readable anticipation, action, impact, overshoot, settle, and recovery.

## Gap to `mockup-1.png` / `mockup-2.png`

The reference mockups are now the composition target for the gameplay view. Close the gap in this order:

1. Correct shooter bind pose and face controls; the female shooter must be the default hero.
2. Correct arena transforms so layered foreground foliage, field edge, fence, signs, lake, boats, far trees, and sky all frame the play space without origin overlap.
3. Export a small set of low-cost formation players from the shared hero rigs: two home off-ball players and three field defenders. They need idle/read/reaction/run clips, distinct jersey numbers, and no gameplay collision initially. Do not simply duplicate identical frozen figures.
4. Provide a warm-sun/cool-fill runtime lighting reference and an environment cubemap or documented RealityKit IBL source. The mockup depends on contact shadows, material separation, and reflected sky color.
5. Provide foreground and distant scenic layers separately so Swift can apply restrained depth-of-field or selective blur without softening the shooter→goal gameplay band.
6. Supply phone-resolution framing renders with safe zones for the top score/pause HUD and bottom input prompt. Characters, target trajectory, goalie, and goal must remain readable under those overlays.

The full mockup population is a presentation milestone, not a prerequisite for the one-shooter physics loop. Formation players should be added only after the corrected shooter, goalie, goal, and arena pass the runtime acceptance gate.
# Production brief

The complete forward-looking asset, animation, environment, grass, lighting, LOD, socket, and export request is now maintained in `BLENDER_PRODUCTION_BRIEF.md`. Treat that file as the production checklist and this file as runtime defect feedback from specific deliveries.
# `a0a716f` integration result

- Shooter production loading re-enabled. No load, manifest, or socket fallback appeared in the runtime console.
- Pinebrook replaces the former environment asset. The malformed-mesh quarantine was removed.
- Runtime selects `far_background_soft` and `foreground_framing_soft`, hides the matching sharp groups, and hides `collision_only`.
- Fan A/B/C and both teammate assets load through their manifests and begin ambient idle clips.
- All exported USDZ/JSON files and LOD variants are mirrored into the application resources.
- Project builds and launches cleanly. A visual placement/device screenshot pass is still required because automated simulator capture is unavailable in the current environment.
# Screenshot review and `057d9d1` integration

Observed in the supplied iPhone 17 Pro screenshot before this pass:

- Shooter was too large/cropped at the bottom and the composition was top-heavy.
- A center spectator sat directly behind the goalie/net, reducing goal readability; fans appeared on field level instead of convincingly seated.
- Shooter, goalie, and all three fans appeared to have closed eyes simultaneously. This persists despite the no-joint-scale export and needs an authored rest/clip validation in RealityKit.
- Contact shadows and material separation were too weak, and the top/bottom HUD competed with the play space.

Runtime changes made:

- Uses `lax_arena_pinebrook_mobile.usdz` and the lighter LOD1 support characters, with LOD2/fewer fans below 5 GB physical memory.
- Loads `lax_arena_ambient.usdz`, loops `ambient_loop`, hides `midground_trees`, and triggers `ambient_gust` for called shots and streak moments. Low-memory tier disables it.
- Reads `camera_gameplay` and `camera_gameplay_target` when present; retains a pulled-back portrait fallback.
- Fans moved out of the center goal sightline and use crowd goal/save/pipe reactions.
- Warm directional key now casts shadows. RealityKit's `GroundingShadowComponent` caused a simulator render-pipeline compile failure, so lightweight soft contact-shadow meshes are used for hero subjects instead.
- A full clean build and launch produced no asset fallback, missing socket, manifest, optional asset, or render-pipeline errors.

Still needed from Blender:

1. Validate open eyes in every loop's first/rest frame after USDZ round trip, specifically `idle`, `goalie_ready`, and `crowd_idle`; the supplied screenshot shows all eyes closed.
2. Deliver the referenced environment map in a RealityKit-loadable bundle format and provide its exact resource name. No `.hdr`, `.exr`, or RealityKit environment resource currently exists in `3D/Production`.
3. Deliver the referenced color-grading LUT and exact format/name. No LUT file is currently present.
4. Provide named bleacher seat sockets/transforms for fan placement. `CROWD_NOTES.md` says to place roots on seat tops but does not provide runtime coordinates.
# Device finding: ambient export placement (2026-09-23 7:57 PM)

`lax_arena_ambient.usdz` currently renders animated tree trunks in the lake from the gameplay camera. Runtime has disabled the ambient asset and restored the static softened arena groups. Before re-enabling it, round-trip the packaged USDZ through RealityKit and verify every animated tree/hedge retains the same world-space base position as `midground_trees` in `lax_arena_pinebrook_mobile.usdz`. Please also add named bleacher seat markers so crowd placement does not rely on Swift coordinates.
