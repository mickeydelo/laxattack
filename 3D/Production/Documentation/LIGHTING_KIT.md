# Lighting Kit (RealityKit)

Files are in `3D/Production/Exports/Lighting/`.

| File | Format | Purpose |
|---|---|---|
| `lax_env_pinebrook_1k.exr` | OpenEXR, 1024x512 equirectangular, 16-bit half, ZIP, linear | Image-based light: warm sky gradient, green turf bounce, lake band |
| `lax_grade_warm_miniature_32.cube` | Adobe .cube 3D LUT, 32^3, domain 0–1 | Colour grade (Resolve / Metal post-process) |
| `lax_grade_warm_miniature_32_strip.png` | 1024x32 PNG strip (32 tiles of 32x32; tile = blue slice, x = red, y = green), non-colour | Same LUT for a Metal texture lookup |
| `lax_grade_before_after.png` | Preview | Left: ungraded runtime-camera frame; right: graded |

## Environment map orientation and intensity
- The equirect centre (u = 0.5) looks along **gameplay forward (game −Z)**; the image top is +Y.
- If RealityKit's equirect convention differs on device, rotate the IBL entity 180° about Y. Verify with the sky gradient: the
  warm band is the horizon.
- The sun is **not** baked into the map. Use it as fill only (suggested `intensityExponent` about 0–0.5) and apply it to every
  entity via `ImageBasedLightReceiverComponent`.

## Key and fill lights
- **Key:** directional light, colour (1.0, 0.84, 0.62).
  - Travels along game-space (0.42, −0.66, 0.62), i.e. from high behind-left of the goal toward the camera and right.
  - Soft shadows, depth bias tuned so feet contact reads.
  - Suggested 2500–3500 lux equivalent; tune on device.
- **Fill:** gentle cool fill from the lake side (game −Z), colour (0.80, 0.88, 1.0), about 15–25% of the key. No harsh black
  shadows.
- **Contact:** add `GroundingShadowComponent` to characters, sticks, ball, goal and spectators. Do not use baked circular
  shadow cards.

## Colour grade
- Gentle S-curve, +12% saturation, warm highlights, slightly lifted warm shadows.
- Intended strength 1.0; 0.6–0.8 if it clashes with UI colours.
- Apply after tone mapping, in display space.
