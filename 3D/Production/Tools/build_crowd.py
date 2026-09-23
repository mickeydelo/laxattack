# Lax Attack crowd modules: seated fans on the shared field skeleton (no stick mesh; the invisible stick frame places the hands).
CROWD_DIR = os.path.join(PROD, "Crowd")
FAN_C = dict(SPECTATORS[1], name="fan_c", skin="skin_tan", hair="hair_auburn", jaw_taper=0.18, cranium=0.07, lash=True, brow_w=0.008,
             mouth_w=0.036, mouth_el=-30, hair_style="ponytail", pony_el=30.0, headgear="none", kit="accent_coral", kit_trim="kit_white",
             bottom="shorts", bottom_mat="kit_navy", body_scale=0.70, head_k=1.25)
SEAT = finalize(P(BASE_FIELD, pelvis_off=(0, 0.02, -0.24), pelvis_rot=(0, 0, 0), spine_rot=(4, 0, 0), chest_rot=(2, 0, 0), neck_rot=(0, 0, 0),
                  head_rot=(-4, 0, 0), footL=(0.02, -0.20, 0), footR=(-0.02, -0.20, 0), G=(-0.11, -0.24, 0.50), D=(-1, 0, 0), F=(0, -1, 0), face="smile"))
def S(**kw):
    return finalize(P(SEAT, **kw))
def fan_loop(N, fn):
    return lambda t: fn(t, 2 * math.pi * t / N)
UP = dict(G=(-0.11, -0.10, 1.18), D=(-1, 0, 0), F=(0, -1, 0))
FAN_CLIPS = [
    Clip("crowd_idle", 0, 48, True, fan_loop(48, lambda t, ph: S(pelvis_off=(0, 0.02, -0.24 - 0.006 * (0.5 - 0.5 * math.cos(ph))), head_rot=(-4, 6 * math.sin(ph), 0),
         eye=(5 * math.sin(ph + 1), 0))), blinks=(20,), notes="seated breathing, small look-around"),
    Clip("crowd_watch_left", 55, 48, True, fan_loop(48, lambda t, ph: S(head_rot=(-4, 26 + 3 * math.sin(ph), 0), chest_rot=(2, 6, 0), eye=(-14, 0))), notes="fan's own left"),
    Clip("crowd_watch_right", 110, 48, True, fan_loop(48, lambda t, ph: S(head_rot=(-4, -26 + 3 * math.sin(ph), 0), chest_rot=(2, -6, 0), eye=(14, 0))), notes="fan's own right"),
    Clip("crowd_anticipate", 165, 48, True, fan_loop(48, lambda t, ph: S(spine_rot=(12, 0, 0), chest_rot=(8, 0, 0), head_rot=(-12, 0, 0), G=(-0.11, -0.28, 0.82),
         pelvis_off=(0, 0.0, -0.24 - 0.008 * abs(math.sin(2 * ph))), face="focused")), notes="leaning in, hands clasped"),
    Clip("crowd_goal_cheer", 220, 48, False, keys_fn([(0, SEAT, "io"), (6, S(pelvis_off=(0, 0.0, -0.16), face="surprise"), "out"),
         (12, S(pelvis_off=(0, -0.04, -0.04), footL=(0.02, -0.06, 0), footR=(-0.02, -0.06, 0), face="big_smile", **UP), "in"),
         (18, S(pelvis_off=(0, -0.04, 0.04), footL=(0.02, -0.06, 0.05), footR=(-0.02, -0.06, 0.05), face="big_smile", **UP), "out"),
         (24, S(pelvis_off=(0, -0.04, -0.05), footL=(0.02, -0.06, 0), footR=(-0.02, -0.06, 0), face="big_smile", **UP), "in"),
         (30, S(pelvis_off=(0, -0.04, 0.03), footL=(0.02, -0.06, 0.04), footR=(-0.02, -0.06, 0.04), face="big_smile", **UP), "out"),
         (40, S(face="big_smile"), "io"), (48, S(face="smile"), "io")]), notes="pops up from the seat, arms overhead, bounces, sits"),
    Clip("crowd_save_cheer", 275, 36, False, keys_fn([(0, SEAT, "io"), (8, S(face="big_smile", **UP), "out"), (14, S(face="big_smile", G=(-0.11, -0.10, 1.05)), "in"),
         (20, S(face="big_smile", **UP), "out"), (36, SEAT, "io")]), notes="seated arms-up clap"),
    Clip("crowd_pipe_groan", 320, 40, False, keys_fn([(0, SEAT, "io"), (5, S(chest_rot=(-8, 0, 0), head_rot=(-14, 0, 0), G=(-0.11, -0.08, 1.10), face="surprise"), "out"),
         (20, S(chest_rot=(-6, 0, 0), head_rot=(-10, 0, 0), G=(-0.11, -0.08, 1.08), face="disappointed"), "io"), (40, SEAT, "io")]), notes="hands on head"),
    Clip("crowd_near_miss", 370, 40, False, keys_fn([(0, SEAT, "io"), (6, S(spine_rot=(14, 0, 0), head_rot=(-12, 0, 0), G=(-0.11, -0.28, 0.80), face="focused"), "io"),
         (12, S(chest_rot=(-10, 0, 0), head_rot=(-16, 0, 0), G=(-0.11, -0.14, 1.02), face="surprise"), "out"),
         (26, S(spine_rot=(10, 0, 0), chest_rot=(8, 0, 0), head_rot=(10, 0, 0), face="disappointed"), "io"), (40, SEAT, "io")]), notes="lean in, 'ooh!', slump"),
    Clip("crowd_streak_hype", 420, 24, True, fan_loop(24, lambda t, ph: S(G=(-0.11, -0.16, 0.95 + 0.14 * max(0.0, math.sin(2 * ph))), pelvis_off=(0, 0.02, -0.24 + 0.02 * max(0.0, math.sin(2 * ph))),
         head_rot=(-8, 0, 4 * math.sin(ph)), face="big_smile")), notes="arm pumps"),
    Clip("crowd_final_shot", 450, 48, True, fan_loop(48, lambda t, ph: S(spine_rot=(14, 0, 3 * math.sin(ph)), chest_rot=(8, 0, 0), head_rot=(-12, 0, 0), G=(-0.11, -0.28, 0.86),
         face="strain")), notes="biting-nails intensity"),
    Clip("crowd_gasp", 505, 30, False, keys_fn([(0, SEAT, "io"), (4, S(chest_rot=(-8, 0, 0), head_rot=(-10, 0, 0), G=(-0.11, -0.25, 0.98), face="surprise"), "out"),
         (16, S(chest_rot=(-6, 0, 0), G=(-0.11, -0.25, 0.96), face="surprise"), "io"), (30, SEAT, "io")]), notes="hands to cheeks"),
    Clip("crowd_wave", 540, 48, True, fan_loop(48, lambda t, ph: S(G=(-0.11 + 0.12 * math.sin(ph), -0.10, 1.16), chest_rot=(-4, 0, 6 * math.sin(ph)),
         head_rot=(-10, 0, -6 * math.sin(ph)), face="big_smile")), notes="arms-up sway"),
]

def build_fan(spec, asset):
    reset_scene("LaxAttack_" + asset)
    C = coll(asset)
    arm = build_skeleton(spec, C, asset + "_rig")
    parts = build_character(spec, C, arm)
    calibrate_poles(arm, [SEAT, S(**UP), S(G=(-0.11, -0.28, 0.82))], "field")
    bake_clips(arm, FAN_CLIPS, "field")
    meshes = list(parts.values())
    os.makedirs(CROWD_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CROWD_DIR, "LaxAttack_" + asset + ".blend"), compress=True)
    man = manifest(asset, FAN_CLIPS, perspective="none", extra={
        "usage": "seated spectator; place the root on the bleacher seat top; offset clip start times per instance for asynchronous motion",
        "tiers": {"hero": asset + ".usdz", "midground": asset + "_lod1.usdz", "distant": asset + "_lod2.usdz"}})
    for o in meshes:                        # hero tier inside the brief's 8-15k spectator target
        m = o.modifiers.new("hero_lod", "DECIMATE"); m.ratio = 0.55
        bpy.context.view_layer.objects.active = o
        while o.modifiers.find("hero_lod") > 0:
            bpy.ops.object.modifier_move_up(modifier="hero_lod")
        bpy.ops.object.modifier_apply(modifier="hero_lod")
    tris = sum(tri_count(o) for o in meshes)
    path = os.path.join(EXP, asset + ".usdz")
    e = export_asset([arm] + meshes, asset, asset + "_rig", path, 30, FAN_CLIPS[-1].end, False, man, ())
    lods = export_lods(e, asset, asset + "_rig", path, (0.45, 0.18), 30, FAN_CLIPS[-1].end, man)
    with open(os.path.join(EXP, asset + "_clips.json"), "w") as fh:
        json.dump(man, fh, indent=2)
    return {"tris": tris, "y": e["baked_y_range"], "lods": {k: v["tris"] for k, v in lods.items()}}
