# Arena Notes

Blender 5.2.2 LTS.
- Source: `3D/Production/Arena/LaxAttack_Arena.blend`, built by `Tools/style_validation.py` (`build_scene`, characters and
  goal removed).
- Export: `3D/Production/Exports/lax_arena_environment.usdz` (static, root identity at field level, ~4.7 MB with packed turf
  textures).

## Layers
1. **Foreground:** corner hedges, post with bottle, rock, bag, balls. Bottom corners only, clear of the swipe centre.
2. **Field:** 14 x 19 m slab with a 0.45 m soil skirt, textured turf with mow stripes, crease (r 2.2), goal line, shooting arc
   and sidelines. Goal line centre at game z = -5.7. The goal is the separate `lax_goal.usdz`.
3. **Arena edge:** post-and-rail fence, bench.
4. **Spectators:** bleacher and signs (PINEBROOK FIELD, GOOD PLAYERS / BRIGHTER DAYS). Crowd figures come in a later crowd
   pass.
5. **Scenic:** hedge row behind the goal, broadleaf trees and two pines at the sides, lake with sailboats.
6. **Distance:** forested far shore, faint far mountains.
7. **Sky:** clouds. The sky gradient itself is a RealityKit IBL/background task; see VISUAL_STYLE_BIBLE §6.

## Performance
- 44 meshes, 30 materials, 90716 tris, 2 textures (turf 1024^2).
- This is heavier than the final target. Merge by material, and give the far shore, mountains and clouds lower detail or a
  backdrop card, before shipping.

## Next action for the Xcode agent
1. Add the USDZ at the scene origin, where its field level equals the gameplay ground.
2. Keep gameplay collision on existing primitives.
3. Remove the procedural field, trees and signs once it looks right.
4. Try the reference camera from VISUAL_STYLE_BIBLE §7.
