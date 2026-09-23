# Lax Attack 3D Art Pipeline

Lax Attack stays a SwiftUI + RealityKit game. Blender is the recommended authoring tool for hero characters, equipment, rigging, skinning, and authored animation clips. Unity is not required unless the entire runtime is intentionally moved away from RealityKit.

RealityKit owns gameplay, physics, camera, effects, animation state, and input. Blender owns the assets that need an artist's hand.

## Visual target

- Stylized, toy-like proportions with readable silhouettes on an iPhone screen.
- Large heads, expressive eyes, oversized gloves and lacrosse heads, and clear team colors.
- Animation poses should read at game speed before secondary detail is added.
- Lacrosse identity comes from cradling, pocket deformation cues, release styles, goalie stance, crease play, checks, dodges, and stick celebrations.
- Compose each screen like a handcrafted sports diorama: foreground framing, playable middle ground, goal focal point, and softly simplified scenic depth.
- Use tactile material families—painted wood, stitched fabric, molded plastic, rubber, turf, metal pipe, and woven mesh—rather than uniformly colored primitives.
- Keep UI shapes chunky and physical with strong value separation, restrained shadows, and a small set of repeatable color roles.
- Give every important outcome a coordinated response across character pose, camera, particles, sound, haptics, and score presentation.
- Preserve generous negative space around the ball path and goal. Decorative richness must not compete with aiming readability.

## Asset conventions

- Work in meters and apply scale/rotation before export.
- Use Y-up. Place the character origin on the field between the feet.
- Characters face forward consistently; document any export-axis conversion in the Blender source file.
- Name assets and actions predictably: `player_f_01`, `goalie_01`, `stick_attack_01`, `anim_shot_overhand`, and `anim_goalie_save_high_left`.
- Keep stick, head/pocket, helmet, and character as separable meshes where customization is expected.
- Add a `stick_socket` bone or empty at the lead hand and stable attachment points for helmet and accessories.

## Character rig

Use one shared skeleton per body family: root, pelvis, spine, chest, neck, head, eyes, clavicles, upper/lower arms, hands, upper/lower legs, and feet. Add a compact facial rig for blink, look, smile, strain, surprise, and disappointment. Preserve a clean rest pose so RealityKit retargeting and additive animation remain viable.

## First animation set

Player:

- Ready idle, breathing idle, look-around idle, and continuous cradle.
- Aim low/medium/high with a readable anticipation pose.
- Overhand, sidearm, underhand, quick-stick, and bounce-shot releases.
- Split dodge, roll dodge, step-down wind-up, recover, stumble, and reset.
- Goal celebrations, near-miss frustration, pipe reaction, and save reaction.

Goalie:

- Ready stance, shuffle, track ball, and reset.
- Saves high/low to both sides, five-hole close, body save, stick save, and rebound recovery.
- Goal-against reaction, confidence animation, and idle personality beats.

Each action needs anticipation, a sharp readable contact/release pose, follow-through, overshoot, and settle. Favor strong timing and silhouette over motion-capture realism.

## Mobile production targets

Initial working targets, to validate on representative iPhones:

- 25k-40k rendered triangles for the foreground hero character.
- 15k-30k for the goalie; less for background characters.
- One 2048 PBR texture set per hero character, packed where practical.
- Limit transparent layers and material count; use shared materials for uniform variants.
- Add lower-detail variants once multiple characters share a scene.

These are production starting points, not fixed engine limits. Profile before increasing them.

## Export and integration

1. Export one fully rigged test character and its idle/shot clips to USD/USDZ before producing the full cast.
2. Verify scale, facing, materials, skeleton, clip names, attachment sockets, and looping in RealityKit.
3. Load the character as an Entity and drive named clips through RealityKit's animation library or animation graph.
4. Keep collision volumes as simple RealityKit shapes rather than mesh colliders on skinned characters.
5. Only after the vertical slice works, produce variants and customization pieces.

RealityKit supports skeletal resources, animation retargeting, named animation libraries, additive animation processing, and animation graphs. That makes Blender-to-USDZ-to-RealityKit the intended next production step without changing the current engine.

## Production handoff contract

The runtime contract is defined in `MyApp/CharacterAssets.swift`. Treat these names as API: changing one in Blender requires the same change in code.

- Deliver `lax_shooter.usdz` and `lax_goalie.usdz` as the first graybox exports.
- Export in meters, Y-up, with the root at field level. Shooter faces toward negative Z; goalie faces toward positive Z.
- Keep the skinned visual hierarchy free of gameplay collision meshes. RealityKit owns the simple character collider, ball, goal, and field physics.
- Include child transforms named `stick_socket`, `helmet_socket`, and `effect_socket`. Sockets must inherit character motion without scale animation.
- Put named clips in the root entity's `AnimationLibraryComponent`. The app validates the sockets and clip names before an authored character is accepted.
- Use a single material atlas per character for the first vertical slice. Keep eyes/face separate only if expression animation requires it.

Required shooter clips:

`idle`, `cradle`, `aim_overhand`, `aim_bounce`, `aim_sidearm`, `split_dodge_left`, `split_dodge_right`, `release_overhand`, `release_bounce`, `release_sidearm`, `quick_stick_catch`, `quick_stick_release`, `celebrate`, `disappointed`.

Required goalie clips:

`goalie_ready`, `goalie_shuffle_left`, `goalie_shuffle_right`, `goalie_read_left`, `goalie_read_right`, `goalie_save_left`, `goalie_save_right`, `goalie_goal_against`.

Loop `idle`, `cradle`, `goalie_ready`, and both goalie shuffle clips cleanly. All release clips need a clearly documented ball-release frame; both quick-stick clips need a clearly documented pocket-contact frame. Do not animate the world root away from field level. Use hips/pelvis motion for jumps and saves so the gameplay root and collider remain stable.

## First-asset acceptance test

Before producing variants, import one graybox shooter and one graybox goalie and verify:

1. `CharacterAssetContract.load(named:)` loads each bundle resource without conversion or runtime warnings.
2. `CharacterAssetContract.validate(_:role:)` reports no missing sockets or clips.
3. Scale, facing, feet, stick grip, pocket position, and helmet attachment remain correct through every clip.
4. Release and save timing match the existing gameplay state transitions at full game speed.
5. The ball, goal, goalie hit volume, trajectory preview, scoring, and replay record behave identically with procedural visuals hidden.
6. The iPhone portrait build sustains the target frame rate with the arena and both characters visible.

The first production task is therefore a graybox asset-validation sprint, not a full character art pass.
