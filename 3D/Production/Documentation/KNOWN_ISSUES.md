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
- **Reach misses:** hand IK misses by up to 4.9 cm in `roll_dodge_right` and `celebrate_knee_slide` (boy field, teammates).
  Tune these key poses after on-device review.
- **Arena file size:** the arena USDZ is about 16 MB (2048 PBR field set). A 1024 mobile variant can be produced if needed; the
  4K source set is not generated yet.
- **Crowd LOD0** is heavier than the brief's hero-spectator target (18–22k vs 8–15k); use `_lod1` for heroes if needed.
- **RealityKit screenshots:** still required from the Xcode side (Blender round-trip renders are provided).
