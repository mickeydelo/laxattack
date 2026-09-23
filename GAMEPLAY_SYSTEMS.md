# Lax Attack Gameplay Systems

Read this with `PROJECT_MEMORY.md` before changing menus, modes, scoring, progression, replay, or multiplayer.

## Current playable shell

- `AppFlow` owns the current destination and presentation state.
- `GameRun` describes a Quick Shoot, Daily Shot, or Challenge session without changing RealityKit gameplay code.
- `GameSession` owns the live five-shot round, scoring, combo, shot selection, and complete `ShotResult` history.
- `RunRecord` snapshots the run ID, mode, deterministic seed, final score, completion date, and shot history for future ghost replay and validation.
- `PlayerProgress` persists the overall best score, Daily Shot best, and cleared challenge IDs in `UserDefaults`.
- Daily Shot derives a stable seed from the local calendar year and ordinal day. The seed offsets the goalie's movement pattern.

## Modes

- **Quick Shoot:** unrestricted five-shot score chase.
- **Daily Shot:** one seeded goalie pattern shared by the date; local daily best is persisted.
- **Challenges:** six definitions evaluated from the same authoritative `ShotResult` records.

Current challenges cover total score, top corners, bounce goals, five-hole goals, split-dodge goals, and total goals. Challenge definitions remain data rather than separate gameplay screens.

## UX

- Home screen exposes Play, Daily Shot, Challenges, best score, and Settings.
- First run presents a three-step playable-control introduction.
- Gameplay includes pause, restart, settings, home, live challenge progress, tailored results, and medals.
- Haptics can be disabled and Reduce Motion suppresses the primary screen transition.

## Competition path

Do not begin live multiplayer first. Build in this order:

1. Serialize `RunRecord` and its versioned `ShotInput` values.
2. Re-simulate recorded shots against the matching physics and seed version.
3. Add local ghost playback and replay inspection.
4. Add Game Center Daily Shot leaderboards.
5. Add shareable asynchronous friend challenges.
6. Evaluate live play only after deterministic replay and validation are reliable.

## Guardrails

- Challenge rules read `ShotResult`; do not infer results from UI feedback text.
- Preserve `physicsVersion` and the run seed in competitive records.
- Cosmetics must not alter competitive shot physics.
- Keep mode navigation in SwiftUI and simulation ownership in `PocketLaxScene`.
- Keep challenge definitions data-driven and stably identified.
