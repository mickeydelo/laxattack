# Known Issues

- **Ball size contract:** the runtime renders the ball at 0.12 m radius. Production pockets fit a 0.08 m visual ball
  (7 mm side clearance). Recommendation: set the visual sphere to 0.08 m (0.06 m would match the key art even better); the
  collider can stay 0.12 m.
- **(Resolved: faces no longer use joint scale.)** Old note: lids and mouth use joint *scale*. UsdSkel exports it, but RealityKit playback of joint
  scale must be confirmed on device. If it fails, lids and mouth will render authored-closed / authored-open. The fallback is
  to swap to rotation-driven lids.
- **Glove/helmet proximity:** the sphere-based clearance estimate reports overlaps up to ~0.27 m in reaction clips because
  the helmet is approximated as a sphere and the face opening is ignored. Visual review of the key-pose sheet shows no
  obvious intersections. A mesh-based check is still to do.
- **Small reach errors:** the bottom hand misses its IK target by 1.6 cm (cradle) and 1.3 cm (celebrate).
- **Materials:** 17 materials on the shooter. Atlasing into one texture set is recommended before shipping.
- **Hand switching:** the rig is right-handed only; split dodges do not switch hands.
- **Dodge root motion:** dodges are in place; Swift must translate the root.
- **Look gaps vs key art:** grass normal map, leaf-clump canopies, lake shoreline and reflective water, helmet size from
  directly behind.
- **Legacy art in the repo:** `07_portrait_three_quarter_dof.png` and `08_portrait_three_quarter_no_dof.png` in
  `Previews/StyleValidation` are v1 renders kept for history.


Phase 1 commit: `3ef396d58503f5e7844da3cee169684900893c22`.

- **Goalie base height:** `PocketLaxScene` lifts the procedural goalie to a 0.625 m base height. The USDZ goalie must be placed
  at y = 0 (feet on the turf).
- **Goalie hands:** the goalie rig is right-hand-top only. Low saves tilt the stick forward instead of flipping hands.
- **Crowd not built:** crowd figures and reaction clips (Phase 6) are not built yet; the arena has bleachers but no crowd.
- **Heavy arena:** the arena is about 90k tris and 30 materials. Optimize before shipping.
- **Brief items still to do:** grass PBR/tufts/masks, DOF fallback layers, LODs, the expanded animation library (idle variants, roll/face dodges, celebrations, goalie extras), crowd, teammates, and RealityKit round-trip screenshots.
- **(Resolved)** `celebrate_knee_slide` reach fixed by a grip search (0.0 cm). `roll_dodge_right` improved to about 2.5 cm.
- **Arena file size:** use `lax_arena_pinebrook_mobile.usdz` (1024 textures, about 8 MB) on device. The 4K source set is not generated yet.
- **(Resolved)** crowd hero tiers are now 10–12k tris.
- **RealityKit screenshots:** still required from the Xcode side (Blender round-trip renders are provided).
- **LOD2 heads:** LOD decimation now protects the head and face (fixes the "C-shaped eyes" in RealityKit), so LOD2 keeps the
  full head. Current LOD2 sizes: 13k (shooter), about 20k (helmeted heroes).
- **Character texture atlases** (painted-vinyl AO, fabric weave, decals) are not built yet; materials are still flat PBR values.
- **IBL orientation** must be confirmed on device (see LIGHTING_KIT.md).
- **Atlas seams:** faint UV seam lines can show on faces in extreme close-ups (tangent-space normal seams). They are not visible
  at gameplay scale.
- **Atlas file sizes:** heroes about 5.3–5.6 MB (LODs about 3.5–3.8 MB), fans about 2 MB.
- **Crowd LODs** decimate faces too; they are only meant for midground and distant use.
- **(Resolved)** the note about flat PBR character materials.
- **(Resolved)** arena material count: the arena now uses 4 materials and the ambient layer uses 1 (shared palette).
- **(Resolved)** `roll_dodge_right` grip miss and its twisted end pose.
- **Continuity playblast preview is dark:** colour management leaked from the environment-map render. Previews only; exports
  are unaffected.
- **Blender USD importer caching:** re-importing a just-exported USDZ in the same session can return stale data. Validation
  now force-reloads USD layers first.
- **Remaining hand-to-grip gaps** of up to 2.4 cm on some variant clips (cradles, kick saves).
- **Preview exposure:** Blender preview renders now use AgX with no look at +0.85 exposure. "AgX - Punchy" measured about 0.7
  stop too dark on the palette scene. Previews only; the runtime look is RealityKit's (see LIGHTING_KIT.md). The v7 continuity
  playblast predates this fix and renders dark.
- **(Fixed 2026-09-24)** `fan_root_offset_below_seat_m` was 0.17 / 0.17 / 0.15 (an estimate), which sank fans about 9 cm into the benches. Measured values are 0.086 / 0.082 / 0.070 m.
