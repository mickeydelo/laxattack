# lax_shooter — graybox character validation

Validation asset only (graybox, not final art). Purpose: prove scale, facing, sockets, clip timing, and USDZ import against `CharacterAssetContract`.

## Files

| File | What it is |
|---|---|
| `LaxAttackCharacters.blend` | Source scene (rig, IK controls, 4 actions, NLA timeline, markers, preview camera/light) |
| `lax_shooter.usdz` | Runtime asset (ARKit-profile USDZ, all 4 clips on one baked timeline) |
| `lax_shooter_clips.json` | Clip manifest: frame ranges, loop flags, release frame (also stored in `/lax_shooter` customData) |
| `tools/build_lax_shooter.py` | Rebuilds the whole scene from scratch (mesh, rig, sockets, clips, validation) |
| `tools/export_lax_shooter.py` | USD export + post-process + USDZ packaging + verification |
| `previews/lax_shooter_contact_sheet.png` | Workbench renders of key frames (see frame list below) |

## Tool versions

- Blender 5.2.2 LTS (macOS arm64), Python 3.13, bundled OpenUSD (`pxr`).

## Dimensions and facing (USD / RealityKit space)

- Meters, unit scale 1.0, `metersPerUnit = 1`, `upAxis = Y`, 30 fps (`timeCodesPerSecond = 30`).
- Height: 1.52 m in rest pose, ~1.48 m in the athletic ready pose.
- Origin at field level (Y = 0) between the feet. Feet stay at Y = 0 in every clip except the celebrate jump (pelvis carries it; root never moves).
- Faces **−Z**. Character's right side is **+X**. Right-handed shooter (right hand top of stick, left hand bottom); stick carried on +X.
- No object scale or rotation left on any Blender object (all identity). The asset root `/lax_shooter` has an identity transform.
- ~7.75k triangles, 21 joints, 5 flat materials (UsdPreviewSurface, no textures).

## Hierarchy (USD)

```
/lax_shooter                      Xform, defaultPrim, kind=component, identity transform (gameplay root)
  lax_shooter_rig                 SkelRoot, static rotateXYZ(90,0,180) = Blender Z-up -> Y-up conversion
    lax_shooter_rig               Skeleton (21 joints: root, pelvis, spine, chest, neck, head,
                                  clavicle/upperarm/forearm/hand _L/_R, thigh/shin/foot _L/_R, stick)
      Action                      SkelAnimation, frames 0–186 (all clips)
    lax_shooter_body              skinned mesh (rigid 1-joint weights)
    lax_shooter_stick             skinned mesh, bound to `stick` joint
    stick_socket                  Xform, per-frame animated
    helmet_socket                 Xform, per-frame animated
    effect_socket                 Xform, per-frame animated
    pocket_socket                 Xform, per-frame animated (extra, optional)
  _materials                      M_Jersey, M_Navy, M_Skin, M_Dark, M_White
```

In Blender the sockets are empties bone-parented to the rig; the exporter bakes them to per-frame translate/orient samples. None carry scale.

## Sockets

Positions are in `/lax_shooter` space.

| Socket | Follows | Placement | Local axes |
|---|---|---|---|
| `stick_socket` | `stick` joint | Top-hand (right) grip on the shaft. Ready pose ≈ (0.28, 0.84, −0.18) | +Y along shaft toward the stick head, +Z out of the pocket's open face |
| `pocket_socket` | `stick` joint | Pocket center, 0.365 m up the shaft from `stick_socket` | same as `stick_socket` |
| `helmet_socket` | `head` joint | Head center. Rest (0, 1.23, 0); ready pose ≈ (0.01, 1.19, −0.05) | Matches character root in rest pose (+Y up, −Z forward) |
| `effect_socket` | `chest` joint | Front of chest. Rest (0, 0.86, −0.17); ready pose ≈ (0.05, 0.79, −0.19) | Matches character root in rest pose |

Ball spawn/launch should use `pocket_socket` if present (fall back to `stick_socket` + 0.365 m along its +Y).

## Animation clips (one shared timeline, 30 fps)

Blender exports a single `SkelAnimation`. Slice it by these ranges (inclusive). Every clip starts and ends on the same ready pose (first/last frame delta = 0), so clips can be cut and blended freely.

| Clip | Timeline frames | Length | Seconds | Loop |
|---|---|---|---|---|
| `idle` | 0–48 | 48 | 0.0–1.6 s (1.6 s) | yes |
| `cradle` | 60–88 | 28 | 2.0–2.933 s (0.933 s) | yes |
| `release_overhand` | 100–133 | 33 | 3.333–4.433 s (1.1 s) | no |
| `celebrate` | 150–186 | 36 | 5.0–6.2 s (1.2 s) | no |

For looping clips the last frame equals the first; drop the last frame when looping (idle: 0–47, cradle: 60–87).

**Ball release: timeline frame 114 = `release_overhand` local frame 14 = 0.467 s into the clip** (marker `release_overhand_BALL_RELEASE`).

`release_overhand` beats (local frames): counter-dip 3, loaded 9, moving hold 11 (cocked), whip 12–13, **release 14**, overshoot/follow-through 18, settle 23, recover 28, ready 33. After release: 19 frames ≈ 0.63 s (matches `releaseTime = 0.62`).

`celebrate` beats: crouch 5, launch 9, apex 12 (pelvis +0.18 m), touchdown 16, squash 19, stick pumps 23 and 29, settle 36.

Contact sheet frames (left→right, top→bottom): 0, 24 (idle) · 67, 81 (cradle) · 103, 111, 114, 118, 124, 133 (release) · 155, 162, 169, 173, 179, 186 (celebrate).

## Export settings

Blender `wm.usd_export` (see `tools/export_lax_shooter.py`): selected objects only (collection `lax_shooter`), animation on, armatures on, deform bones only, materials + UsdPreviewSurface, UVs, normals, `convert_orientation=True`, up `Y`, forward `Z`, root prim `/lax_shooter`, evaluation mode Render; no lights, cameras, shape keys, Blender names or custom properties.

Post-process with `pxr`: the axis-conversion rotation is moved from `/lax_shooter` to `lax_shooter_rig` so the asset root is identity; set defaultPrim, kind, upAxis, metersPerUnit, 30 fps, time range 0–186, clip manifest in customData. Packaged with `UsdUtils.CreateNewARKitUsdzPackage`.

Verified after export (skinning baked in a scratch copy): feet at Y = 0, toes toward −Z, stick on +X, root transform identity, all sockets present. Rig validation in Blender: root never moves, foot IK error 0, hand-to-grip error ≤ 0.1 mm, no stick/head intersections in the clearance check, loop seams exact.

## Known issues / notes for the Xcode agent

1. **No `AnimationLibraryComponent` in the USDZ.** Blender can't author it. At load time, slice the single animation into named clips using the ranges above (e.g. `AnimationResource` trimmed by time) and store them in `AnimationLibraryComponent` on the root entity so `validate()` finds them.
2. Only 4 of the 14 contract clips exist. `validate()` will still report the other 10 missing (expected for this sprint).
3. Gameplay launches the ball instantly in `shoot()`, but the authored release is 0.467 s in. Either start `release_overhand` at local frame ~11 (cocked pose, 3 frames to release) or delay the launch to the release frame.
4. Facing: the asset faces −Z (toward the goal), so the default camera at +Z sees the shooter's back / over-the-shoulder. The procedural placeholder faces the camera (+Z). Rotate the entity 180° about Y if a camera-facing shooter is wanted.
5. No helmet mesh yet — `helmet_socket` only.
6. Animation is densely baked (every frame, linear); IK controls exist only in the `.blend`.
7. 5 separate materials, not atlased (fine for graybox; atlas for final art).
8. `celebrate` leans the head back strongly at the apex; the jump lifts the feet off the turf (intended).
