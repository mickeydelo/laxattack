# Arena Notes — Pinebrook

Export: `3D/Production/Exports/lax_arena_pinebrook.usdz` (static; identity root at field level; turf textures packed).
Source: `3D/Production/Arena/LaxAttack_Arena.blend`.
Contents: 45 meshes, 31 materials, 90764 tris.

## Groups (child Xforms of `/lax_arena_pinebrook/lax_arena_content`)
| Group | Contents |
|---|---|
| gameplay | field slab, textured turf and mow stripes, markings |
| near_field | fence, bench, bleacher, signs, hedge row |
| midground | broadleaf trees, pines, lake, sailboats, meadow |
| far_background | far shore, mountains, clouds |
| foreground_framing | corner hedges, post with bottle, rock, tuft, bag, balls |
| shadow_only | empty (reserved) |
| collision_only | `collision_ground` box; hide it at runtime |
| camera_markers | see below |

## Camera markers
Each camera has a paired `_target` empty, in game coordinates:
- `camera_gameplay`, `camera_aim`, `camera_release`
- `camera_goal_left`, `camera_goal_right`
- `camera_save_left`, `camera_save_right`
- `camera_celebration`, `camera_results`

Left/right follow the shooter's perspective.

## Not yet done (brief items)
- Full PBR turf set (normal, roughness, AO/macro, wear masks).
- Worn crease and goal-mouth masks, and hero grass tufts.
- Pre-softened far-background and foreground DOF fallback variants.
- 50% / 20% LODs.
- Animated flags, water and trees.
