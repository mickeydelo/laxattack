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
