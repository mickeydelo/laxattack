# Whimsy Layer: critters, confetti, flowers (v8, 2026-09-24)

These are small living-world touches that make Pinebrook feel inhabited. Every layer is independently toggleable for
performance tiers. They use transform animation only (local pivots, identity root, axis conversion on the content prim), like
`lax_arena_ambient`.

## `lax_arena_life.usdz` + `lax_arena_life_clips.json`
Place it at the scene origin with the arena. 35 meshes, about 4k tris, 1 palette material, about 0.4 MB.

| Clip | Frames | Notes |
|---|---|---|
| `life_loop` | 0–480 (16 s, loop) | Two songbirds on the fence behind the goal hop, peck and tilt their heads; three butterflies flutter over the hedges; a duck glides around the lake and dips its head; 16 lake glints twinkle |
| `birds_startle` | 490–610 | Both birds flutter up about 1.4 m, circle and land back on their perch. Butterflies and the duck are startled too (they move faster). Starts and ends exactly on the `life_loop` frame-0 pose |

- **Use:** loop `life_loop`. On a goal or crowd roar, play `birds_startle` once, then return to `life_loop` from frame 0.
- **Validation** (packaged USDZ): loop seam 0.000 m; startle start/end vs loop rest 0.000 m; no mesh near the origin in any
  sampled frame.
- **Birds** perch on the fence top rail at game (−2.3, 1.09, −12.55) and (3.3, 1.09, −12.55).

## `lax_fx_confetti.usdz` + `lax_fx_confetti_clips.json`
A confetti cannon for celebrations: 90 paper pieces in the team palette, 1 material, about 0.3 MB.

| Clip | Frames | Notes |
|---|---|---|
| `confetti_burst` | 0–105 | Pops from the asset origin, peaks about 2 m, flutters down (paper terminal velocity), and all 90 pieces land flat on the turf |

- **Use:** place at a goal side (for example game (±1.9, 0, −5.4)) or at the crowd.
- Play on a goal; hide the entity about 2 s after the clip ends.
- Spawn two mirrored cannons for big moments.

## Flower beds (in `lax_arena_pinebrook*.usdz`)
- **Toy flower clumps** (white, gold, pink, lilac, coral petals; leaf stems) sit along the fence base, by the benches and near
  the bleachers, in the `near_field` group as `flowers_00..15`.
- **Larger foreground clumps** (`flowers_fg_00..02`) sit in the camera's lower corners, in `foreground_framing`, with
  pre-softened copies in `foreground_framing_soft`.
- The arena still uses 4 materials (flowers use the palette).

Preview: `Previews/RoundTrip/whimsy_life_confetti_flowers.png`.
