# Deliverables

Thumbnails and wireframe/polycount renders: `3D/Production/Previews/Deliverables/` (`<asset>_thumbnail.png`, `<asset>_wireframe.png`, `deliverables_sheet.png`).
Round-trip: `Previews/RoundTrip/lax_shooter_usdz_roundtrip.png` (packaged USDZ re-imported and rendered from the runtime camera). **The on-device RealityKit screenshot must come from the Xcode side.**

| Asset | LOD0 tris | LOD1 | LOD2 | Materials | Textures |
|---|---|---|---|---|---|
| lax_shooter | 26344 | 15806 | 7903 | 19 | none (flat UsdPreviewSurface colours) |
| lax_goalie | 35764 | 21458 | 10729 | 18 | none (flat UsdPreviewSurface colours) |
| lax_boy_field | 33792 | 20275 | 10136 | 19 | none (flat UsdPreviewSurface colours) |
| lax_girl_goalie | 37688 | 22612 | 11306 | 18 | none (flat UsdPreviewSurface colours) |
| lax_team_home_7 | 25816 | 15488 | 7744 | 19 | none (flat UsdPreviewSurface colours) |
| lax_team_away_5 | 33128 | 19875 | 9936 | 19 | none (flat UsdPreviewSurface colours) |
| lax_fan_a | 22148 | 5536 | 2214 | 14 | none (flat UsdPreviewSurface colours) |
| lax_fan_b | 18420 | 4604 | 1841 | 13 | none (flat UsdPreviewSurface colours) |
| lax_fan_c | 19872 | 4968 | 1987 | 14 | none (flat UsdPreviewSurface colours) |
| lax_goal | 5208 | — | — | 3 | none (flat UsdPreviewSurface colours) |
| lax_arena_pinebrook | 117720 | 72244 | 29073 | 50 | field_albedo.jpg (2048, sRGB), field_normal.png (2048, linear), field_roughness.jpg (2048, linear), turf_albedo.png (1024), sky_gradient.png |
| lax_stick_attack / lax_stick_goalie | 3,744 each | — | — | 5 | none |

LOD files sit next to each LOD0 export as `<asset>_lod1.usdz` / `<asset>_lod2.usdz`, with the same clips, sockets, identity root and facing.
Characters are one skinned mesh with uniform 4 influences. Bind poses were verified by the USDZ round-trip import.
