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
- The miniature arena uses primitive RealityKit geometry for turf, markings, side boards, sky, hills, clouds, trees, goal, red pipes, and netting.
- White ball begins kinematic, becomes dynamic on an upward swipe, receives an impulse, and resets after each resolved shot.
- Swipe travel and release velocity jointly control power; horizontal travel plus a small velocity contribution controls lateral direction. Values are clamped for consistency, and very short swipes are rejected.
- Dragging before release displays a live dotted 3D ballistic trajectory and a HUD power meter.
- A retained RealityKit collision subscription detects the invisible goal trigger, goalie saves, and pipe contacts.
- The scene-update subscription drives procedural character and environment performance every frame.
- The primitive shooter has an expressive face, uniform, legs, and lacrosse stick/pocket. It procedurally idles, aims, winds up, releases, celebrates, and reacts to misses/saves.
- The primitive goalie has an expressive face, helmet, uniform, legs, and stick/pocket. It patrols laterally, increases speed/amplitude as combo difficulty rises, reacts directionally to saves, and slumps after goals.
- The goal net pulses after a score.
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
- Import the graybox `3D/CharacterValidation/lax_shooter.usdz` (delivered; see its `ASSET_NOTES.md`): slice its single timeline into `idle`/`cradle`/`release_overhand`/`celebrate` in `AnimationLibraryComponent`, pass `CharacterAssetContract` socket validation, and align the authored ball-release frame (timeline 114, 0.467 s into `release_overhand`) with `shoot()`. `lax_goalie.usdz` is not built yet.

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

# 2026-09-22: Competitive feel and art direction

- Product name is **Lax Attack**. The runtime remains SwiftUI + RealityKit in portrait orientation.
- The shot control model now combines swipe travel and release velocity, clamps both aim and power, previews the physical trajectory, and rejects short accidental swipes.
- Procedural characters now use staged anticipation, release, follow-through, recovery, squash/stretch, eye tracking, blinking, goalie reactions, and result poses.
- Gameplay feedback includes a pooled spatial ball trail and distinct goal/save/pipe burst colors. Keep effects pooled to avoid per-shot allocation.
- The professional art decision is Blender for character/equipment modeling, rigging, skinning, and authored clips; RealityKit remains the game engine. Unity is unnecessary unless the whole runtime changes.
- See `ART_PIPELINE.md` for scale, rig, naming, animation, mobile budget, and USDZ integration conventions.
- Reference principles from Nintendo sports titles: readable aiming/trajectory information, expressive timing, approachable direct input, and character identity. Do not copy characters, art, UI, or animations.
