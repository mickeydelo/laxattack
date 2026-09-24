# Export Notes

Blender 5.2.2 LTS. Tool: `3D/Production/Tools/lax_export.py` (`export_asset`), generalized from the graybox exporter.

## Settings
Blender USD export options:
- `convert_orientation=True`, forward Z, up Y, `root_prim_path=/<asset>`.
- Selected objects only, `only_deform_bones=True`, UsdPreviewSurface materials, UVs and normals.
- No shape keys, lights or cameras.
- `evaluation_mode=RENDER`, so IK is baked into joint transforms.

pxr post-process:
- The asset root (`/lax_shooter`) keeps an **identity** transform at field level.
- The axis conversion `rotateXYZ(90, 0, 180)` sits on the rig child prim (`/lax_shooter/lax_shooter_rig`).
- Assets that must face +Z (goalie) get an extra `rotateY(180)` on the same child, so the root stays identity.
- `defaultPrim`, kind=component, upAxis Y, metersPerUnit 1, timeCodesPerSecond 30.
- The clip manifest is stored in root customData (`laxattack.clipManifest`) and as JSON beside the USDZ.

Packaging: `UsdUtils.CreateNewARKitUsdzPackage`.

## Verification (run on every export)
Re-opens the stage and checks:
- defaultPrim, up axis and units, and root identity.
- Socket presence and world positions.
- UsdSkel animation count and time range.
- Texture references.
- A `UsdSkel.BakeSkinning` pass over the whole timeline to measure the skinned mesh Y range (field-level check).

## Runtime exports (3D/Production/Exports/)
| File | Result |
|---|---|
| lax_shooter.usdz (2.03 MB) | root identity ✓, Y-up ✓, m ✓, 7/7 sockets ✓, 1 SkelAnimation ✓, time 0–705 @30 ✓, baked Y −0.002…1.606 ✓, 9 meshes, 17 materials, no textures |
| lax_shooter_clips.json | 18 clips with release/contact frames |
| lax_stick_attack.usdz (176 KB) | root identity ✓, 4/4 sockets ✓ (grip (0,0,0), pocket (0,0.025,0.431), ball_contact (0,−0.061,0.431), effect (0,0,0.66)), time 0–214 ✓, 3,744 tris, 5 materials |
| lax_stick_attack_clips.json | 9 pocket clips |
| lax_goalie.usdz (1.87 MB) | faces +Z ✓, root identity ✓, 7/7 sockets ✓, 1 SkelAnimation ✓, time 0–556 @30 ✓, baked Y 0.000…1.685 ✓, 36,164 tris, 17 materials |
| lax_goalie_clips.json | 15 clips (8 required + 7 extra), contact frames, shooter-perspective convention |
| lax_stick_goalie.usdz (176 KB) | root identity ✓, 4/4 sockets ✓, 9 pocket clips, 3,744 tris |
| lax_goal.usdz (296 KB) | mouth faces +Z ✓, root identity ✓, frame + skinned net ✓, 7/7 sockets/references ✓, time 0–295 ✓, 5,208 tris |
| lax_goal_clips.json | 8 net clips, hierarchy, dimensions |

## Validation tool
`lax_validate.validate_character` checks:
- Metric units and fps.
- Identity object transforms.
- Required clips and sockets.
- Triangle budget and material count.
- Mesh/armature binding and weights.
- Missing textures.

It also checks, per clip: hand-IK error, foot-IK error, ankle height, a glove/helmet sphere-clearance estimate, a shaft/helmet
clearance estimate, root motion, loop seams, and static ball/pocket clearance.


## Update: identity-transform export (Codex brief P0, bind fix)
`export_asset` now bakes the axis change into the asset before exporting. It rotates mesh data, sets every bone's rest matrix
exactly (parents first, roll preserved) and re-places sockets. Assets that face +Z get an extra 180° in the same bake.

- The USD is written with `convert_orientation=False`.
- **Every prim is identity** (root, rig, meshes), which removes the combined skinned-mesh bind-transform issue seen in
  RealityKit.
- Validated: bone positions match the pre-bake poses exactly (0.0 m) on sampled frames; baked skin ranges are unchanged.
- Weights are capped at **4 joint influences** per vertex (normalized) in `Builder`.
- `lax_arena_environment.usdz` is replaced by **`lax_arena_pinebrook.usdz`**.


## Update: RealityKit round-trip fixes (Codex feedback)
- **One skinned mesh per rig.** `merge_skinned` joins all character parts into `<asset>_body`, keeping material subsets, so
  RealityKit never has to merge several skinned meshes into one render component.
- **Uniform 4 influences** on every skinned mesh (`pad_influences`), weights renormalized.
- **Rest frame shows open eyes and a closed smile** even if animation playback fails. Lids are authored open and blinks rotate
  them down; the mouth cover is authored closed.
- **Round-trip check:** the packaged `lax_shooter.usdz` is re-imported into a clean Blender scene and rendered from the
  runtime camera (`Previews/RoundTrip/lax_shooter_usdz_roundtrip.png`).
  - Parts are coherent, the stick is in the hands, eyes are open, and clips play.
  - This does **not** replace the on-device RealityKit screenshot.
- **Arena:** depsgraph update before reading world matrices fixes the origin-stacked meshes. `export_lods` writes decimated
  `_lod1`/`_lod2` files.


## v4 update
- **Transform-animated assets** (`lax_arena_ambient`) export with `bake=False, content_axis=True`: local pivots are kept, the
  axis conversion sits on the content prim only, and the root stays identity.
- **LOD face protection:** decimation skips vertices weighted to head/face bones.
- **Round-trip validation** reopens the packaged USDZ. The Blender importer skips an identity root, so the checks compose a
  converter parent rather than overwriting the file's transforms.
