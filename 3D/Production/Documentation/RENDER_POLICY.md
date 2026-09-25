# Render Policy (`Exports/lax_render_policy.json`, schema v1)

Swift should read rendering behaviour from this file instead of inferring it from entity names. Names are stable.

## Resolution order
Later entries override earlier ones:
1. `defaults`
2. `assets.<asset>` (and its `groups.<group>` for the arena)
3. `entity_patterns` (glob match on entity name)
4. `tier_<tier>` overrides
5. `modes.<mode>` show/hide

## Fields
| Field | Meaning |
|---|---|
| `visible` | Default visibility |
| `always_hidden` | Never show, in any mode |
| `pair` | Name of the sharp/soft counterpart |
| `ibl` | Receives the shared image-based light |
| `unlit` | Render without lighting (sky gradient) |
| `cast_shadow` / `receive_shadow` | Shadow participation |
| `tier` | Lowest tier that loads it (`all`, `mid+`) |
| `optional` | May be skipped entirely |
| `animated` | Has a timeline |
| `exclude_from_post` | Skip future post effects |
| `visible_when` | Visibility condition |
| `markers_only` | Transforms only, never rendered |

## Rules encoded
- **Sharp/soft pairs:** `exclusive_pairs` + `pair_rule`. Exactly one of each pair is visible.
  - `modes.dof_fallback`, the current RealityView path: soft groups visible, sharp hidden.
  - `modes.native_dof`: the reverse, focused on `gameplay_focus_center` (9.6 m, f/2.8 full-frame equivalent, 38.6 mm).
- **Unlit sky:** `sky_backdrop` has no image-based light, no shadows, and is unlit.
- **Shadow-free objects:** clouds, lake glints, far shore and mountains cast no shadows.
- **Hidden groups:** `collision_only` is always hidden; `camera_markers` and `crowd_markers` are marker-only.
- **`ambient_twins`:** visible only when `lax_arena_ambient` is not loaded.
- **Grounding shadows:** only on characters, fans, sticks, ball and goal.
- **Confetti:** image-based light on; shadows off on the low tier; hide 2 s after `confetti_burst`.
- **Animated assets:** play the root entity's `global scene animation` (index 0) only, sliced by the JSON ranges. This was
  verified with RealityKit on macOS; the descendants also expose "default subtree animation" and should be ignored.
