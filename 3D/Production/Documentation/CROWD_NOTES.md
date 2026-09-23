# Crowd Notes

Seated spectator modules on the shared field skeleton. Source: `3D/Production/Tools/build_crowd.py`.

| Module | Look | Hero tris | Midground (_lod1) | Distant (_lod2) |
|---|---|---|---|---|
| lax_fan_a | blonde, blue cap, gold shirt | 22,148 | 5,536 | 2,214 |
| lax_fan_b | deep skin, short hair, white shirt, teal shorts | 18,420 | 4,604 | 1,841 |
| lax_fan_c | child, auburn ponytail, coral shirt | 19,872 | 4,968 | 1,987 |

**Clips** (one timeline, 30 fps, seated): full ranges are in `lax_fan_*_clips.json`.
- `crowd_idle`, `crowd_watch_left`, `crowd_watch_right` (the fan's own left/right), `crowd_anticipate`
- `crowd_goal_cheer` (pops up, arms overhead), `crowd_save_cheer`, `crowd_pipe_groan`, `crowd_near_miss`
- `crowd_streak_hype`, `crowd_final_shot`, `crowd_gasp`, `crowd_wave`

**Usage:**
- Place the root on the bleacher seat top.
- Use `_lod1` for midground rows and `_lod2` for distant rows.
- Offset each instance's clip start by 0–1 s for asynchronous motion.
- Build a 6–10 fan block by repeating the three modules with different offsets and facing jitter.

**Palette:** each module is one palette. Recolour at runtime by material name (`M_accent_gold`, `M_kit_white`, `M_accent_coral`,
`M_kit_navy`, `M_accent_teal`) for more variants.
