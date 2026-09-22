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

## Roadmap

1. Prove the shot: goal/save/miss outcomes, fast reset, five-shot rounds, scoring, combo, basic goalie, feedback.
2. Prove lacrosse: visible stick/pocket, release types, bounce shots, quick sticks, first dodge-to-shot sequence.
3. Prove character: one polished shooter, one goalie, authored animation set, one final-quality arena slice.
4. Prove retention: Daily Shot, challenge progression, small cosmetic set, onboarding.
5. Prove competition: leaderboards, ghost shootouts, replays, weekly ladder.
6. Expand toward compact Pocket Sixes play with passing, defense, transition, and teammates.

## Current Implementation

- `MyApp/ContentView.swift` contains the prototype.
- RealityView uses a virtual fixed camera.
- Green field and goal use primitive RealityKit geometry.
- White ball begins kinematic, becomes dynamic on an upward swipe, receives an impulse, and resets after each resolved shot.
- Swipe vertical distance controls power; horizontal distance controls lateral direction.
- A retained RealityKit collision subscription detects the invisible goal trigger, goalie saves, and pipe contacts.
- A scene-update subscription moves a placeholder goalie laterally.
- Five-shot rounds track score, consecutive-goal combo, remaining shots, feedback, round completion, and replay.
- Current scoring awards `100 × combo` for each consecutive goal; saves and misses reset the combo.
- Each completed shot records normalized horizontal input, power, outcome, points, combo, and whether it contacted a pipe; this is the seed for later replay and ghost systems.
- Pipe-and-in goals currently award a 75-point bonus.
- iOS haptics distinguish release, goal, save, pipe, and miss.
- The moving goalie is now a readable primitive character silhouette assembled from a helmet, face, torso, legs, and stick, with one kinematic collision body.
- The SwiftUI HUD is split into `GameHUD` and `StatCard`, while `GameSession` owns observable round state and `PocketLaxScene` owns RealityKit entities, physics, subscriptions, and reset tasks.
- iPhone portrait orientation is configured in build settings.
- iOS deployment target is 26.0 so the installed iOS 26.5 simulator can run the project.

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

- Tune shot velocity, goalie size/speed, camera framing, trigger placement, and reset timing through hands-on play.
- Add distinct placeholder audio and haptics for release, pipe, save, goal, and miss.
- Add shot result data that can later support accuracy bonuses and deterministic replays.
- Replace the block goalie with the first readable primitive character silhouette before starting authored character assets.

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
