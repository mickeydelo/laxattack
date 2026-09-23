# Pocket Lax Project Memory

Read this file before making project changes. Update it after each meaningful discovery, decision, implementation milestone, or validation result so future agents can continue without reconstructing context.

## Product North Star

Pocket Lax is a portrait iPhone 3D arcade lacrosse game: immediate swipe-based play, real lacrosse identity, charming stylized characters, authored animation, compact competitive sessions, and console-quality presentation. The long-term bar is a polished Nintendo-like arcade sports experience, but development must proceed through small playable milestones.

## Current Scope

- Swift, SwiftUI, and RealityKit in Xcode 27.
- Portrait iPhone experience.
- Placeholder geometry is intentional until the shot loop is proven.
- Avoid menus, economies, customization, networking, and broad architecture until their milestone begins.
- Keep gameplay deterministic enough to support future replays, ghost competition, and score validation.

## Product Pillars

1. **One more shot:** instant restart, short rounds, clear outcomes, score chasing.
2. **Uniquely lacrosse:** the pocket, cradling, release angles, bounce shots, quick sticks, dodges, crease play, goalie reads, and wall ball.
3. **Character through motion:** readable anticipation, impact, recovery, reactions, and celebrations.
4. **Skill before stats:** competitive outcomes should primarily reflect timing, aim, deception, and shot choice.
5. **Playable milestones:** every phase ends in a build that is fun on its own.

## Visual North Star

- The supplied Pocket Lax concepts are the quality and emotional benchmark, not literal production art to copy.
- Target a premium miniature sports diorama with charming stylized athletes, tactile equipment, layered scenic depth, bold readable HUD cards, and coordinated animation/VFX feedback.
- Final character quality requires Blender-authored models, shared production rigs, facial shapes, equipment sockets, and authored clips imported as USDZ. Procedural geometry remains gameplay scaffolding.
- Keep the goal, goalie, ball path, shot choice, and result readable before adding decorative density.

## Roadmap

1. Prove the shot: goal/save/miss outcomes, fast reset, five-shot rounds, scoring, combo, basic goalie, feedback.
2. Prove lacrosse: visible stick/pocket, release types, bounce shots, quick sticks, first dodge-to-shot sequence.
3. Prove character: one polished shooter, one goalie, authored animation set, one final-quality arena slice.
4. Prove retention: Daily Shot, challenge progression, small cosmetic set, onboarding.
5. Prove competition: leaderboards, ghost shootouts, replays, weekly ladder.
6. Expand toward compact Pocket Sixes play with passing, defense, transition, and teammates.

## Current Implementation

- The user-facing app display name is **Lax Attack**. Internal Xcode target and Swift type names remain `MyApp` to avoid an unnecessary project-wide rename.
- The implementation is split into focused files: `ContentView.swift` for SwiftUI composition and HUD, `GameModels.swift` for round/shot state and feedback, `PocketLaxScene.swift` for RealityKit entities, animation, physics, and collision events, and `CharacterAssets.swift` for the production USDZ contract.
- RealityView uses a virtual fixed camera.
- The runtime now installs the production lakeside diorama (`lax_arena_environment.usdz`) and disables the procedural scenery after a successful load. Primitive field, goal, and goalie entities remain only as collision/fallback scaffolding.
- White ball begins kinematic, becomes dynamic on an upward swipe, receives an impulse, and resets after each resolved shot.
- Swipe travel and release velocity jointly control power; horizontal travel plus a small velocity contribution controls lateral direction. Values are clamped for consistency, and very short swipes are rejected.
- Dragging before release displays a live dotted 3D ballistic trajectory and a HUD power meter.
- A retained RealityKit collision subscription detects the invisible goal trigger, goalie saves, and pipe contacts.
- The scene-update subscription drives procedural character and environment performance every frame.
- The primitive shooter has an expressive face, uniform, legs, and lacrosse stick/pocket. It procedurally idles, aims, winds up, releases, celebrates, and reacts to misses/saves.
- The primitive goalie has an expressive face, helmet, uniform, legs, and stick/pocket. It patrols laterally, increases speed/amplitude as combo difficulty rises, reacts directionally to saves, and slumps after goals.
- The authored goal replaces the visible procedural cage. Its 8 manifest-driven net clips select center/high/low/heavy reactions from ball impact position and speed, while simple invisible pipe and goal-sensor colliders remain authoritative.
- Five-shot rounds track score, consecutive-goal combo, remaining shots, feedback, round completion, and replay.
- Current scoring awards `100 × combo` for each consecutive goal; saves and misses reset the combo.
- Each completed shot records normalized horizontal input, power, outcome, points, combo, and whether it contacted a pipe; this is the seed for later replay and ghost systems.
- Pipe-and-in goals currently award a 75-point bonus.
- Physics contact with the named field marks a shot as a bounce shot; bounce-and-in earns 75 bonus points and is persisted in `ShotResult`.
- Goal entry above 1.35 meters and wider than 0.48 meters from center is classified as a top-corner finish and earns 100 bonus points.
- Shot bonuses stack with the base combo score, so a skilled shot can combine combo, pipe, bounce, and placement bonuses.
- Players can select Overhand, Bounce, or Sidearm before each shot. Each release has a distinct trajectory, procedural wind-up/follow-through, and haptic signature; the selected type is stored in `ShotInput` for replay/competition work.
- Overhand is the fast high-release precision shot. Bounce launches shallow to contact turf before the cage. Sidearm launches flatter, spins, and develops late lateral curve in flight.
- Five pulsing goal markers communicate top-corner, low-corner, and five-hole scoring windows. Top corner adds 100 points, low corner adds 75, five-hole adds 125, and a sidearm goal adds 50.
- The virtual camera adds a restrained forward kick on release and short shake on goal/save/pipe impact.
- The third attempt in each five-shot round becomes a Quick Stick timing challenge. A pass travels into the visible stick pocket on the same 1.6-second clock as the HUD timing lane; tapping near center increases speed and accuracy and reduces the goalie's read.
- Quick-stick timing quality is persisted in `ShotInput`, and quick-stick goals earn a 150-point release bonus.
- The goalie now commits progressively toward the indicated release direction, scaling its read strength with combo difficulty; well-timed quick sticks partially defeat that anticipation.
- A lateral-first drag followed by the upward release registers a split dodge. The procedural shooter plants and shifts with independent arm/leg motion, the goalie initially commits opposite the eventual shot, the dodge direction is persisted, and a dodge goal adds 100 points.
- Three consecutive goals activate `On Fire` for the following attempt. The state gives the ball a gold material, changes the trail to orange, displays a HUD flame badge, persists with the shot record, and awards 200 bonus points if converted; a miss/save resets the combo and ends the opportunity.
- Ball contact physics now vary by release: bounce shots use higher restitution and lower friction, sidearm shots use controlled lateral force for late curve, and every release applies a distinct angular impulse.
- Goal net response is localized from the ball's entry position rather than only uniformly scaling; shooter arms/legs and goalie legs/stick now articulate procedurally during cradles, dodges, releases, shuffles, and saves.
- Goal feedback distinguishes standard goals, top-corner finishes, and bounce goals.
- iOS haptics distinguish release, goal, save, pipe, and miss.
- The moving goalie is now a readable primitive character silhouette assembled from a helmet, face, torso, legs, and stick, with one kinematic collision body.
- The goalie procedural animation is applied above a fixed 0.625-meter base height. Never assign its animated local offset directly to world Y or the body will be buried beneath the field.
- The placeholder goal now includes a visible primitive mesh grid and field-level goal line for clearer depth and cage readability.
- The SwiftUI HUD is composed from small section views, while `GameSession` owns observable round state and `PocketLaxScene` owns RealityKit entities, physics, subscriptions, and reset tasks.
- The upgraded HUD includes Lax Attack branding, current/best score, five visual shot indicators, goalie difficulty, animated shot callouts, combo, live power, goals, accuracy, and replay.
- iPhone portrait orientation is configured in build settings.
- iOS deployment target is 26.0 so the installed iOS 26.5 simulator can run the project.
- Every release now snapshots the goalie's X position and `physicsVersion` in `ShotInput`, alongside aim, power, timing, dodge, release type, and On Fire state. This is the minimum deterministic record for future replay/ghost migration.
- Shooter and goalie procedural logic emit explicit `CharacterPerformanceState` values. Production assets must provide the exact named clips and sockets validated by `CharacterAssetContract`; see `ART_PIPELINE.md`.
- Production animation clips are decoded from bundled JSON manifests rather than duplicated as hardcoded Swift ranges. The shooter exposes 18 clips, the goalie 15, and the net 8. Overhand, bounce, sidearm, and quick-stick launches use each clip's authored release time.
- The current production shooter is the women’s field player: goggles, headband/ponytail, jersey, kilt, and no helmet. The boy goalie uses its field-level USDZ origin and a separate invisible kinematic hitbox so the visual is no longer buried by the old procedural 0.625 m offset.
- The visible ball radius is 0.08 m for the authored stick pockets; its 0.12 m physics collider remains forgiving. The gameplay camera uses the art-team reference framing at 50° vertical FOV.
- The idle shot HUD now teaches the split-dodge gesture with the concise cue “SIDEWAYS, THEN UP,” making the first deception mechanic discoverable without a menu.

## Environment Discoveries

- The available iPhone simulators are iOS 26.5; the original template target of iOS 27.0 made them incompatible.
- Xcode's automated Device Interaction service currently requires an iOS 27+ simulator, so normal Xcode Run works but automated screenshot/touch inspection does not.
- The app successfully launched on the iPhone 17 Pro simulator.
- RealityKit emits simulator asset-library warnings for built-in render resources; the process remains running and these have not indicated an app crash.
- In the Xcode 27 SDK, `RealityView` camera mode is set inside its make closure with `content.camera = .virtual`.
- Static `PhysicsBodyComponent(shapes:density:mode:)` requires an explicit density argument in this SDK.
- RealityKit trigger volumes should use `CollisionComponent` mode `.trigger` and must not also have a physics body.
- Retain `EventSubscription` values created by `RealityView` content subscriptions.

## Immediate Build Target

- Perform hands-on tuning of shot velocity, trajectory prediction, camera framing, character scale, goalie speed, collision bounds, and reset timing.
- Add authored audio assets for pocket movement, release snap, bounce, pipe, save, net impact, crowd, and UI.
- Add a first quick-stick challenge that uses timing rather than free aiming.
- Tune the three release profiles through hands-on device play, especially bounce restitution and sidearm late curve.
- Build `lax_goalie.usdz` and the shooter's remaining contract clips. The first shooter is now integrated and validates successfully at runtime.

## Guardrails

- Do not imitate the supplied concept images literally; use them only as a quality and emotional reference.
- Do not introduce pay-to-win equipment.
- Do not start full-team AI or real-time multiplayer before the solo shot loop and replay data are proven.
- Prefer an `@Observable`, main-actor session model for shared SwiftUI gameplay state.
- Keep RealityKit entity/physics responsibilities separate from SwiftUI HUD state without building a general-purpose engine.

## Update Log

- 2026-09-22: Created shared memory file and recorded the prototype, product plan, environment constraints, and immediate Phase 1 target.
- 2026-09-22: Implemented the Phase 1 five-shot loop with goal/save/pipe/miss detection, score, combo, moving placeholder goalie, fast resets, round-complete replay, and a compact HUD. The project built successfully and launched on the iPhone 17 Pro simulator with the process remaining running.
- 2026-09-22: Added deterministic shot-result records, pipe-and-in bonus scoring, distinct iOS haptics, and a primitive multi-part goalie silhouette. Corrected child geometry positions relative to the goalie's centered collision parent. The updated project builds successfully.
- 2026-09-22: Changed the generated bundle display name to **Lax Attack** while preserving internal target names. The project builds successfully afterward.
- 2026-09-22: Added bounce-shot tracking, top-corner classification, stackable skill bonuses, richer goal callouts, a primitive goal net, and a goal-line marking. The updated build compiled and launched successfully on the iPhone 17 Pro simulator.
- 2026-09-22: Completed the first large vertical-slice upgrade. Split the project into focused HUD/model/scene files; added a live 3D trajectory guide, procedural shooter performance, reactive difficulty-scaling goalie, pulsing net, richer miniature outdoor arena, improved camera framing, best score, shot indicators, live power, accuracy, and animated round presentation. The project compiled and launched successfully on the iPhone 17 Pro simulator.
- 2026-09-22: Added the first lacrosse decision layer: selectable Overhand/Bounce/Sidearm releases with distinct physics, previews, poses, spin/curve, haptics, and recorded shot type. Added pulsing placement targets, low-corner/five-hole scoring, placement callouts, and restrained camera kick/impact shake. The project built and launched successfully on the iPhone 17 Pro simulator with no crash/fatal/assertion output.
- 2026-09-23: Added a synchronized Quick Stick timing challenge on the third shot, an incoming pass that reaches the procedural pocket, timing-dependent velocity/placement, a 150-point quick-stick bonus, persisted timing quality, quick-stick animation staging, and direction-aware goalie anticipation. Expanded the art pipeline and memory with the supplied concept's diorama/material/feedback quality principles. The project built and launched successfully with no crash/fatal/assertion output.
- 2026-09-23: Added split-dodge gesture recognition and wrong-footed goalie reads, a 100-point dodge finish, release-specific restitution/friction/spin, force-driven sidearm curve, localized net deformation, and additional procedural limb articulation. Added an `On Fire` three-goal streak state with gold/orange visual treatment and a 200-point conversion bonus. The project built and launched successfully with no crash/fatal/assertion output.
- 2026-09-23: Fixed the goalie body being buried below the turf by preserving its 0.625-meter world-space base height during procedural animation. Added explicit shooter/goalie performance states, production socket names, USDZ loading and validation, versioned release snapshots with goalie position, and an in-game split-dodge hint. Documented the exact Blender-to-RealityKit acceptance contract; the project built successfully after these changes.
- 2026-09-23: Delivered the first graybox character-validation asset in `3D/CharacterValidation/`: `LaxAttackCharacters.blend` (Blender 5.2.2 LTS), `lax_shooter.usdz`, `lax_shooter_clips.json`, `ASSET_NOTES.md`, rebuild/export scripts, and a contact sheet. The 1.52 m right-handed shooter faces -Z with +X right, origin at field level, identity root, `stick_socket`/`helmet_socket`/`effect_socket` (plus optional `pocket_socket`), and 4 clips on one 30 fps timeline: idle 0-48, cradle 60-88 (both loop), release_overhand 100-133 with ball release at frame 114, celebrate 150-186. USDZ has no AnimationLibraryComponent, so the runtime must slice clips by frame range. No Swift code was changed.
- 2026-09-23: Integrated `lax_shooter.usdz` into the app bundle and replaced the procedural shooter when loading succeeds. RealityKit now slices the baked timeline with `AnimationView`, creates a four-clip `AnimationLibraryComponent`, validates all attachment sockets, drives clips from `CharacterPerformanceState`, keeps the ball in the animated `pocket_socket` until release, and delays overhand launch by exactly 14/30 seconds to match Blender timeline frame 114. Runtime inspection measured bounds from ground level to 1.522 m, found all four sockets, and found the four expected clips. The app built and launched successfully; remaining missing clips are expected for the graybox sprint.
- 2026-09-23: On branch `gameplay-shell-daily-challenges`, added the first complete non-asset game shell: home, Quick Shoot, deterministic Daily Shot, six data-driven lacrosse challenges, live objective progress, medal results, first-run onboarding, pause/restart/home, haptic and reduced-motion settings, persistent bests/clears, and replay-ready `RunRecord` snapshots. Daily seeds now influence the goalie pattern. See `GAMEPLAY_SYSTEMS.md`. The branch builds, launches, and renders successfully on iPhone 17 Pro / iOS 26.5.

- 2026-09-23: Art-direction checkpoint v1 committed (superseded the same day by Mickey's reference key art; v2 follows). `3D/Production/Documentation/VISUAL_STYLE_BIBLE.md` is now the binding look (toy-figurine proportions with ~38% heads, rigid toy segments, bone-driven painted faces, roughness-spread material language, warm key + cool rim + sky-gradient fill, restrained f/1.4 DOF). Scene `3D/Production/StyleValidation/LaxAttackStyleValidation.blend`, renders in `3D/Production/Previews/StyleValidation/`, shared builders in `3D/Production/Tools/` (lax_core, lax_figure, lax_pose, lax_env, style_validation). Discoveries: the runtime ball renders at 0.12 m radius, larger than a believable stick head, so production pockets are sized for a 0.08 m visual ball (recommend the visual sphere shrink to 0.08 m; the collider may stay 0.12 m). The runtime camera (vFOV 52°) is narrow horizontally (~25°): framing props must sit near the view axis. Goalie stays facing +Z per ART_PIPELINE. New shooter clips will be appended after frame 186 because `prepareShooter()` hardcodes the four graybox ranges.

- 2026-09-23: Art direction v2 committed, aligned to Mickey's reference key art (vinyl-toy figures with ~45% head+helmet, glossy striped helmets on every player, dark glossy toy eyes, home red/cream vs away navy/teal, orange goal, white ball, golden-hour light, textured turf, broadleaf woods, post-and-rail fence, lakeside with sailboats, stronger but gameplay-safe DOF). Figures now use a build-time proportion transform (body_scale ~0.82, head_k 1.15) so pose data and sticks stay compatible. Recommended gameplay camera to match the key art: from (-0.3, 4.3, 7.0) to (-0.15, 0.4, -3.5), vFOV 50 (Swift decision). The key art shows 5v5 players; the game is 1v1, so extra players remain a gameplay decision. See VISUAL_STYLE_BIBLE.md v2.

- 2026-09-23: Phase 1 production foundations committed: shared skeleton families and bone-driven face (`lax_figure.py`), pose model (`lax_pose.py`), clip/bake/secondary-spring system (`lax_anim.py`), generalized USD/USDZ exporter with goalie +Z option and pxr verification (`lax_export.py`), and Blender-side validator (`lax_validate.py`). Docs: CHARACTER_NOTES.md, EXPORT_NOTES.md.

- 2026-09-23: Phase 2 girl field hero committed. `3D/Production/Exports/lax_shooter.usdz` replaces the graybox look while keeping name, facing, identity root, and the four legacy ranges (idle 0-48, cradle 60-88, release_overhand 100-133 with release 114, celebrate 150-186). New clips appended: aim_overhand 200-230, aim_bounce 240-270, aim_sidearm 280-310, split_dodge_left 320-344, split_dodge_right 350-374, release_bounce 380-413 (release 394), release_sidearm 420-453 (release 433), quick_stick_catch 460-478 (contact 466), quick_stick_release 490-506 (release 495), disappointed 520-560, extras near_miss 570-600, pipe 610-634, save 645-675, run_loop 685-705. Sockets: 6 required + ball_contact_socket; pocket_socket is now the resting ball centre for a 0.08 m ball. 34,972 tris, 17 materials. Standalone `lax_stick_attack.usdz` with 9 pocket clips. Manifests beside each USDZ. Swift must add the new ranges (contract change). Phase 1 commit 3ef396d.

- 2026-09-23: Phase 3 boy goalie committed: `3D/Production/Exports/lax_goalie.usdz` faces +Z (rotateY 180 on the rig prim, identity root at field level), 15 clips on one 30 fps timeline: goalie_ready 0-40, shuffle_left 50-70, shuffle_right 80-100, read_left 110-128, read_right 135-153, save_left 160-190 (contact 167), save_right 200-230 (contact 207), goal_against 240-285, plus high/low left/right saves, five_hole_close, body_save, celebrate. Left/right are from the SHOOTER's perspective (save_left = game -X). Asset origin is at field level, so the runtime must drop the procedural 0.625 m base height. Also `lax_stick_goalie.usdz` with 9 pocket clips.

- 2026-09-23: Phase 4 goal committed: `3D/Production/Exports/lax_goal.usdz` (mouth 2.0x2.0 m facing +Z, net depth 2.1 m, identity root on the goal line), static frame + net skinned to a 3x3 bone grid with a pinned mouth rim, sockets goal_sensor_socket, net_collision_reference (scale = box half-extents), net_impact_center/high_left/high_right/low_left/low_right (shooter perspective). Clips: net_idle 0-60, impacts center 70-94, high_left 100-124, high_right 130-154, low_left 160-184, low_right 190-214, heavy 220-256, settle 265-295. See GOAL_NET_NOTES.md.

- 2026-09-23: Phase 7 committed: `lax_boy_field.usdz` (shares lax_shooter clip ranges, swagger personality layer) and `lax_girl_goalie.usdz` (faces +Z, shares lax_goalie clip ranges, bouncy personality layer), manifests beside each.

- 2026-09-23: Phase 5 committed: `lax_arena_environment.usdz` static diorama (90716 tris, 30 materials, packed turf textures), goal/characters excluded. Crowd (Phase 6) and full validation (Phase 8) not yet done.

- 2026-09-23: Girl shooter switched to the women's field kit (goggles, headband + ponytail, jersey, kilt, bare hands) per Mickey's reference; clip timeline and sockets unchanged. Boy field keeps the men's helmet kit; goalies keep helmets.
- 2026-09-23: Rebased the gameplay-shell branch onto Blender main `d81762e` and recopied the corrected women’s-field-kit shooter. Integrated the production shooter, boy goalie, animated goal/net, and lakeside arena. Runtime animation libraries are generated from the three bundled JSON manifests; all shooter/goalie required sockets and clips validated with no omissions (18 shooter clips, 15 goalie clips, 8 net clips). Goal/net reactions are impact-directed, all four shot releases are frame-synchronized, the goalie visual is field-level with a separate collider, and the visible ball is pocket-correct at 0.08 m. Xcode build and normal simulator launch succeeded. Automated screenshots remain blocked because device interaction requires iOS 27 while the installed simulator is iOS 26.5; RealityKit also does not render in the SwiftUI canvas snapshot, so eyelid/mouth joint-scale playback still requires hands-on simulator/device inspection.
- 2026-09-23: Runtime arena inspection found an export defect after the first production screenshot showed a giant green occluder: `tree_*`, `bush_*`, `pine_*`, and `cloud_*` meshes all have geometry baked around game origin instead of their authored placements. Field platform/markings, fence, signs, bleacher, lake, meadow, far shore, and mountains retain valid transforms. Swift now quarantines the malformed mesh prefixes at load so they cannot cover the camera, field, characters, or goal. Blender must re-export the arena with those object/world transforms preserved; remove the quarantine after validating corrected bounds.
- 2026-09-23: A second runtime screenshot exposed more origin-stacked foreground props (`sign_slogan`, `fg_post`, `bottle`, `equipment_bag`, `rock_4`) and confirmed that RealityKit does not visibly play the joint-scale eyelid channels: the production goalie appears eyes-closed. Those props are now quarantined too. Added `3D/Production/Documentation/RUNTIME_INTEGRATION_FEEDBACK.md` as the binding Blender correction/animation-quality handoff, including rotation/translation facial controls and an acceptance gate.
- 2026-09-23: Refined authored performance playback. The goalie now commits before contact and selects standard, high, low, five-hole, or body-save clips from live ball position; this lets the authored contact frame meet the ball instead of playing after collision. Shooter near-miss, pipe, and save reactions now persist instead of being overwritten by the base state machine. Removed ball-like yellow target spheres from the cage. Smoothed swipe power/aim response, reduced velocity-spike steering, added a center dead zone, and separated the first 55 points of split-dodge travel from shot aim so a dodge does not force every finish into the same corner.
- 2026-09-23: Third runtime screenshot showed the women's shooter combined skin rendering with separated parts (large white jersey/equipment form and a vertically stretched/misplaced shaft) despite plausible aggregate bounds. This cannot be selectively hidden because RealityKit exposes one combined `lax_shooter_rig` model. The production shooter is temporarily gated by `useProductionShooter = false`, restoring the clean procedural shooter until Blender corrects bind/inverse-bind transforms. The issue and exact re-export checks are in `RUNTIME_INTEGRATION_FEEDBACK.md`.
- 2026-09-23: Added a fast result-cinematic layer: goals and saves freeze the resolved ball at contact, preserve net/goalie reaction readability, and run a restrained 0.8-second camera push toward the impact before returning to the gameplay camera. This is the recommended form of “bullet time” for the short-loop game—impact emphasis without slowing every flight or delaying the next shot.
- 2026-09-23: Added the first recommended retention hooks without adding controls. Perfect Release scores a controlled snap using release speed plus power control, activates at quality ≥0.82 (roughly 1350–1650 pt/s near ideal power), adds 125 points on a goal, colors the ball/trail cyan, triggers a second crisp haptic beat, and displays `PERFECT RELEASE!`. The idle HUD teaches the bonus. Pressure Ladder now advances after every consecutive goal up to level 5 (previously only every two goals to level 3), making goalie patrol and reads progressively harder; the HUD displays an escalating PRESSURE badge. Also fixed previously literal goalie/combo interpolation strings in the HUD.
- 2026-09-23: Added deterministic Called Shot hot zones without adding input. Every attempt selects top-left, top-right, low-left, low-right, or five-hole from the run seed and shot index. A pulsing 12-dot cyan/white ring marks the target in real 3D goal space but has no collision or steering influence. Actual ball entry is checked against an elliptical region; a conversion adds 200 points, records `hitHotZone` in `ShotResult`, displays `CALLED SHOT!`, and hides the ring during the result impact before the next deterministic zone appears. HUD names the current call and bonus. Validation confirmed seed 42 produces a repeatable low-left → top-right opening sequence and stacks called-shot/perfect/top-corner bonuses correctly.
- 2026-09-23: Added final-ball Clutch Shot drama without a new control. Before the last attempt, the HUD replaces the On Fire badge with `CLUTCH ×2`; converting doubles the entire earned shot value after all combo, placement, release, dodge, heat, perfect, pipe, bounce, and called-shot bonuses. The result displays `CLUTCH ×2!` and persists `wasClutch` in `ShotResult` for replay/ghost parity. A one-shot validation produced 450 points from a 225-point perfect release and recorded the clutch flag.
- 2026-09-23: Updated the temporary procedural shooter to default visually as the women's field athlete while the broken production bind export remains gated: centred her from x −0.72 to −0.25, changed to cream/red jersey and kilt, red stick, red headband, and a segmented brown ponytail with procedural secondary sway tied to body roll. Added a large blue sky backing plane behind the production mountains to eliminate the black void exposed when malformed arena foliage/cloud meshes are quarantined. The intended default remains the authored female `lax_shooter.usdz`; set `useProductionShooter = true` only after the corrected packaged USDZ passes `RUNTIME_INTEGRATION_FEEDBACK.md`.

- 2026-09-23: Codex brief P0 pass: all exports re-baked with identity transforms on every prim (skinned bind fix), max 4 joint influences, faces moved to rotation-driven lid/mouth covers (no joint scale), new eyes/camera_focus/chest sockets, women's gloves, net clips return exactly to rest, arena re-exported as lax_arena_pinebrook.usdz with named groups and camera markers.

- 2026-09-23: Blender round-trip fixes for Codex feedback (branch gameplay-shell-daily-challenges): single merged skinned mesh per character, uniform 4 influences, open-eyes/closed-mouth rest frame, arena origin-stacking fixed (stale matrix_world) with automated 4 m origin test. Arena v3: unique 2048 PBR field (mow bands, macro variation, worn crease/goal-mouth/shooting spot), hero tufts, foreground frame, pre-softened far_background_soft/foreground_framing_soft DOF fallback groups, sky backdrop, LOD1/LOD2 arena exports.

- 2026-09-23: Expanded animation library (shooter 37 clips: idle_relaxed/competitive/nervous, roll/face dodges, 7 celebrations, weak_miss, glance-back, run start/stop, stumble; goalie 35 clips: scan, pipe taps, glove reset, crossovers, read high/low, kick saves, doorstep stuff, desperation dives, trail-stick recovery, frustrated tap, shrug, reset, stick raise, helmet nod, dance, clutch save) on all heroes; LOD1/LOD2 for every character; crowd modules lax_fan_a/b/c (12 seated clips, hero/midground/distant tiers); teammates lax_team_home_7 and lax_team_away_5; thumbnail + wireframe deliverables and DELIVERABLES.md.

- 2026-09-23: H.264 playblasts for shooter, goalie and net (Previews/Playblasts). Net impacts strengthened so all five regions read from the shooter-facing camera (sideways/down billow + travelling tremor), low cords clamped off the turf, exact rest return kept.

- 2026-09-23: Ambient life asset `lax_arena_ambient.usdz` (swaying trees/hedges, fluttering pennants, bobbing/drifting sailboats, gliding clouds; ambient_loop 0-240 seamless, ambient_gust 250-340); static arena gains group midground_trees (hide when ambient shown); `lax_arena_pinebrook_mobile.usdz` 1024 textures (~8 MB); fan hero tiers 10-12k tris; knee-slide reach fixed, roll_dodge_right ~2.5 cm.

# 2026-09-22: Competitive feel and art direction

- Product name is **Lax Attack**. The runtime remains SwiftUI + RealityKit in portrait orientation.
- The shot control model now combines swipe travel and release velocity, clamps both aim and power, previews the physical trajectory, and rejects short accidental swipes.
- Procedural characters now use staged anticipation, release, follow-through, recovery, squash/stretch, eye tracking, blinking, goalie reactions, and result poses.
- Gameplay feedback includes a pooled spatial ball trail and distinct goal/save/pipe burst colors. Keep effects pooled to avoid per-shot allocation.
- The professional art decision is Blender for character/equipment modeling, rigging, skinning, and authored clips; RealityKit remains the game engine. Unity is unnecessary unless the whole runtime changes.
- See `ART_PIPELINE.md` for scale, rig, naming, animation, mobile budget, and USDZ integration conventions.
- Reference principles from Nintendo sports titles: readable aiming/trajectory information, expressive timing, approachable direct input, and character identity. Do not copy characters, art, UI, or animations.
# 2026-09-23 — Diorama production brief and camera polish

- Added `3D/Production/Documentation/BLENDER_PRODUCTION_BRIEF.md` as the authoritative Blender handoff: asset inventory, RealityKit export contract, animation list, sockets/events, LOD/texture budgets, grass layers, lighting, depth staging, secondary motion, crowd/environment props, and camera markers.
- Camera motion now uses frame-rate-independent exponential damping, restrained idle orbit, subtle ball tracking, and smoothed result pushes. The goal remains stable for aiming while the arena reads more clearly as a three-dimensional miniature.
- The mockup look should be built as a layered system: tileable PBR turf + macro/wear masks + sparse hero tufts + intentionally out-of-focus foreground framing. Full-field blade geometry is explicitly avoided for mobile performance.
# 2026-09-23 — Survival and timed core loop

- The main Play button now starts `SURVIVAL`: the run is unlimited until the goalie earns three stops. A miss also counts as a stop because the defending team has won the possession; goals keep the run alive.
- Added `60 SECOND RUSH`, a continuous score attack with a pause-aware 60-second clock.
- Daily Shot and authored challenges intentionally retain their deterministic five-shot format.
- Introduced `RunRule` (`survival`, `timed`, `shotLimit`) so HUD and session completion derive from one rule rather than scattered mode checks.
- Quick-stick opportunities now recur during longer runs instead of being hardcoded to shot three of a five-shot round.
- Replaced the shot dots with contextual survival shields or a live timer as appropriate.
- Removed the persistent perfect-release and split-dodge instruction block. The only always-visible control instruction is the swipe prompt; advanced mechanics should be surfaced progressively and briefly.
# 2026-09-23 — Production art refresh `a0a716f`

- Rebasing target: Blender `main` commit `a0a716f44bec405f3b2333ebc00ba3a0f398641c`.
- Mirrored every USDZ and JSON in `3D/Production/Exports/` into the app resource folder, including all character/arena LODs, fans, teammates, sticks, goalie variants, shooter, goal, and manifests.
- Replaced `lax_arena_environment.usdz` with `lax_arena_pinebrook.usdz` and changed `CharacterAssetContract.arenaAssetName` accordingly.
- Re-enabled the production shooter after the corrected one-mesh/identity-transform bind export.
- Removed the obsolete arena mesh quarantine. Runtime now shows `far_background_soft` and `foreground_framing_soft`, hides their sharp counterparts, and hides `collision_only` as the mobile diorama-depth fallback.
- Added three animated crowd modules behind the goal plus home/away sideline teammates, driven from their production manifests.
- Added the expanded shooter celebration states and rotates goal celebrations, with the clutch clip reserved for clutch goals.
- Clean Xcode build and launch. Runtime console contained no asset fallback, missing socket, optional asset skip, failure, error, or warning messages.
- Screenshot automation remains blocked by the simulator service/runtime mismatch; visual placement still requires a human/device screenshot pass.
