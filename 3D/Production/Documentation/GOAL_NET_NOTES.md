# Goal and Net Notes

Blender 5.2.2 LTS.
- Source: `3D/Production/Goal/LaxAttack_Goal.blend`, rebuilt by `3D/Production/Tools/build_goal.py`.
- Runtime export: `3D/Production/Exports/lax_goal.usdz` (296 KB).
- Manifest: `lax_goal_clips.json`.

## Dimensions and facing
- Mouth 2.0 × 2.0 m inside the pipes; pipe radius 0.045 m; net depth 2.1 m to a 0.7 m rear ground bar.
- Pipes: painted orange (`goal_orange`). Net: 12 mm white cord.
- The mouth plane is at asset z = 0 and faces **+Z** (toward the shooter). The net extends toward −Z. The root is identity at
  field level.
- Place the asset so its origin sits on the goal line centre. The current scene uses z ≈ −5.7.

## Hierarchy (USD)
```
/lax_goal                       identity, kind=component
  /lax_goal_rig                 skeleton (axis conversion lives here)
    lax_goal_frame              static mesh (1,168 tris)
    lax_goal_net                skinned mesh (4,040 tris), bones goal_root + net_00..net_22
    goal_sensor_socket          (0, 1.0, -0.05)   mouth centre, just behind the goal line
    net_collision_reference     (0, 0.9, -0.88)   empty; its scale = half-extents (1.0, 0.88, 0.9) of a simple box over the net
    net_impact_center           (0, 0.43, -1.16)
    net_impact_high_left        (-0.39, 0.74, -1.16)   shooter-left = game -X
    net_impact_high_right       (0.39, 0.74, -1.16)
    net_impact_low_left         (-0.39, 0.18, -1.16)
    net_impact_low_right        (0.39, 0.18, -1.16)
```
Positions are in asset space (game axes). Impact regions use the **shooter's perspective**.

## Net rig
- 9 net bones on a 3 × 3 grid at 62% depth.
- Cord vertices blend the bones with Gaussian falloff (0.55 m).
- A pin factor keeps the mouth rim (and, partly, the rear bar) on the static `goal_root`, so the **front mouth never moves**.

## Clips (30 fps, one timeline)
| Clip | Start–End | Loop | Impact frame |
|---|---|---|---|
| net_idle | 0–60 | yes | — |
| net_impact_center | 70–94 | no | 70 |
| net_impact_high_left | 100–124 | no | 100 |
| net_impact_high_right | 130–154 | no | 130 |
| net_impact_low_left | 160–184 | no | 160 |
| net_impact_low_right | 190–214 | no | 190 |
| net_impact_heavy | 220–256 | no | 220 |
| net_settle | 265–295 | no | — |

Each impact has five parts:
- Fast displacement: a 0.025 s rise.
- Directional pocketing: the net is pushed away from the shooter, with sag only in the upper net.
- Overshoot: a damped cosine.
- Travelling ripple: each bone is delayed by its distance at about 7 m/s.
- Damped settle.

`net_impact_heavy` uses 1.45× the amplitude, a wider reach and a slower decay.

## Collision recommendations
- Do **not** use the visible net or frame as collision.
- Frame: three capsules (posts r 0.045, crossbar r 0.045) plus the rear bar.
- Goal detection: a thin trigger box behind the mouth centred on `goal_sensor_socket` (2.0 × 2.0 × 0.1 m).
- Net stop volume: a box from `net_collision_reference` (scale = half-extents), or two sloped planes.
- Reaction choice: pick the nearest `net_impact_*` socket to the ball's impact point. Use `net_impact_heavy` above your
  speed threshold, and `net_settle` if a reaction is interrupted.

## Performance
5,208 tris, 2 materials, no textures, 10 joints.

## Known issues
- **Subtle regional impacts:** the corner impacts read clearly only from behind or the side. From the gameplay camera, the
  heavy impact is the obvious one. Amplitudes (0.50–0.55 m peak bone push, 0.80 heavy) should be tuned on device.
- **Below-turf cords:** some cords near the rear ground bar dip up to 6 cm below field level at peak sag. This is hidden by
  turf at gameplay distance.
- **Runtime net:** the current procedural net in `PocketLaxScene` sits at `(0, 1, -5.67)`. Replacing it with this asset is a
  Swift change.

## Next action for the Xcode agent
1. Load `lax_goal.usdz` at the goal-line centre.
2. Slice clips from the manifest.
3. Keep the existing collision primitives.
4. Trigger the `net_impact_*` clip closest to the ball's impact point.


## Update (2026-09-23): impacts readable from the gameplay camera
- Each impact region now billows **sideways and down** as well as back, plus a travelling whole-net tremor. Center,
  high-left/right and low-left/right are distinguishable from the shooter-facing view.
- Amplitudes: 0.70–0.75 regional, 1.05 heavy (bone push).
- Downward travel is clamped by bone height, and turf-level cords are pinned to the static root, so no cord crosses the turf (baked Y min -0.035 m).
- The mouth rim stays pinned. Every clip ends exactly at rest; `net_idle` is enveloped to rest at its loop boundary.
- Playblast: `Previews/Playblasts/lax_goal_net_clips.mp4`.
