# Lax Attack: standalone attack stick with deformable pocket rig and pocket clips (lax_stick_attack.usdz).
# Stick space (Blender): shaft +Y, pocket open face +Z, origin = top-hand grip. In USD: shaft +Z, pocket face +Y.
STICK_DIR = os.path.join(PROD, "Equipment", "AttackStick")

def _damped(t, amp, freq, decay):
    return amp * math.exp(-decay * t) * math.sin(2 * math.pi * freq * t)

def _keys(pts, t):   # piecewise smooth interpolation through (frame, value) points
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f0 <= t <= f1:
            u = (t - f0) / (f1 - f0); u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return pts[-1][1]

POCKET_CLIPS = [  # name, start, length, loop, fn(t) -> (depth1, depth2, lateral, pitch_deg, roll_deg), contact, release, notes
    ("pocket_idle", 0, 30, True, lambda t: (0.004 + 0.002 * math.sin(2 * math.pi * t / 30), 0.002, 0.0, 0.0, 0.0), None, None,
     "resting ball weight"),
    ("pocket_cradle_left", 40, 20, True, lambda t: (0.008, 0.003, 0.012 * math.sin(2 * math.pi * t / 20 - 1.1), 0.0, 0.0), None, None,
     "ball rolls toward stick-left (USD +X side of the head) with lag"),
    ("pocket_cradle_right", 70, 20, True, lambda t: (0.008, 0.003, -0.012 * math.sin(2 * math.pi * t / 20 - 1.1), 0.0, 0.0), None, None,
     "mirror of pocket_cradle_left"),
    ("pocket_catch_soft", 100, 15, False, lambda t: (_keys([(0, 0.0), (4, 0.018), (9, -0.004), (15, 0.006)], t), 0.4 * _keys([(0, 0.0), (4, 0.018), (9, -0.004), (15, 0.006)], t), 0.0, _damped(t / 30, 2.0, 5, 6), 0.0), 2, None,
     "ball arrives at local 2; compression peak at 4"),
    ("pocket_catch_hard", 120, 18, False, lambda t: (_keys([(0, 0.0), (3, 0.030), (8, -0.008), (12, 0.010), (18, 0.006)], t), 0.4 * _keys([(0, 0.0), (3, 0.030), (8, -0.008), (12, 0.010), (18, 0.006)], t), 0.0, _damped(t / 30, 5.0, 6, 5), 0.0), 1, None,
     "hard catch: deep compression, overshoot, settle"),
    ("pocket_load", 145, 12, False, lambda t: (_keys([(0, 0.006), (12, 0.016)], t), _keys([(0, 0.003), (12, 0.008)], t), 0.0, 0.0, 0.0), None, None,
     "ball presses back into the pocket during wind-up"),
    ("pocket_release", 160, 8, False, lambda t: (_keys([(0, 0.016), (3, -0.012), (8, 0.0)], t), _keys([(0, 0.008), (3, -0.010), (8, 0.0)], t), 0.0, 0.0, 0.0), None, 3,
     "sharp forward snap; ball exits at local 3"),
    ("pocket_recoil", 170, 15, False, lambda t: (_keys([(0, -0.012), (5, 0.008), (10, -0.004), (15, 0.0)], t), 0.5 * _keys([(0, -0.012), (5, 0.008), (10, -0.004), (15, 0.0)], t), 0.0, _damped(t / 30, 3.0, 4, 4), 0.0), None, None,
     "empty pocket rebounds after the ball leaves"),
    ("pocket_pipe_vibration", 190, 24, False, lambda t: (0.004 + _damped(t / 30, 0.006, 7, 3), 0.002, 0.0, _damped(t / 30, 4.0, 7, 3), _damped(t / 30, 2.0, 9, 3.5)), 0, None,
     "whole-stick buzz after hitting the pipe (rotation about the grip)"),
]

def build_stick_asset(kind="attack", asset="lax_stick_attack", folder="AttackStick", frame_mat="helmet_cream", pocket_mat="cord_navy", export=True):
    reset_scene("LaxAttack_" + folder)
    C = coll(asset); sdir = os.path.join(PROD, "Equipment", folder)
    ad = bpy.data.armatures.new(asset + "_rig"); arm = bpy.data.objects.new(asset + "_rig", ad); C.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    b = ad.edit_bones.new("stick"); b.head = (0, 0, 0); b.tail = (0, 0.22, 0); b.roll = 0
    g = stick_geo(kind); m = g["meta"]; yb = m["pocket_center"][1]
    for n, y in (("pocket_01", yb), ("pocket_02", yb + 0.10)):
        c = ad.edit_bones.new(n); c.head = (0, y, 0); c.tail = (0, y + 0.04, 0); c.roll = 0; c.parent = ad.edit_bones["stick"]
    bpy.ops.object.mode_set(mode="OBJECT")
    stick, meta = build_stick(kind, C, arm, name=asset + "_mesh", frame_mat=frame_mat, pocket_mat=pocket_mat)
    socks = {}
    socks["grip_socket"] = add_socket("grip_socket", arm, "stick", Matrix.Identity(4), C, 0.05)
    socks["pocket_socket"] = add_socket("pocket_socket", arm, "pocket_01", Matrix.Translation(meta["pocket_center"]), C, 0.04)
    socks["ball_contact_socket"] = add_socket("ball_contact_socket", arm, "pocket_01", Matrix.Translation(meta["ball_contact"]), C, 0.03)
    socks["effect_socket"] = add_socket("effect_socket", arm, "stick", Matrix.Translation(meta["effect"]), C, 0.05)
    pbs = arm.pose.bones
    for pb in pbs:
        pb.rotation_mode = "XYZ"
    prefs = bpy.context.preferences.edit; old = prefs.keyframe_new_interpolation_type; prefs.keyframe_new_interpolation_type = "LINEAR"
    anim = arm.animation_data_create(); clips = []
    try:
        for name, start, length, loop, fn, contact, release, notes in POCKET_CLIPS:
            act = bpy.data.actions.new(name); act.use_fake_user = True; anim.action = act
            for f in range(length + 1):
                d1, d2, lat, pitch, roll = fn(f)
                pbs["pocket_01"].location = (lat, 0, -d1); pbs["pocket_02"].location = (lat * 0.5, 0, -d2)
                pbs["stick"].rotation_euler = (math.radians(pitch), math.radians(roll), 0)
                for n, pth in (("pocket_01", "location"), ("pocket_02", "location"), ("stick", "rotation_euler")):
                    pbs[n].keyframe_insert(pth, frame=f, group=n)
            anim.action = None
            clips.append(Clip(name, start, length, loop, fn, contact=contact, release=release, notes=notes))
    finally:
        prefs.keyframe_new_interpolation_type = old
    tr = anim.nla_tracks.new(); tr.name = "clips"
    for i, c in enumerate(clips):
        act = bpy.data.actions[c.name]; st = tr.strips.new(c.name, c.start, act)
        if hasattr(st, "action_slot") and st.action_slot is None and len(act.slots):
            st.action_slot = act.slots[0]
        st.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD"
    for pb in pbs:
        pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
    bpy.context.scene.frame_end = clips[-1].end
    os.makedirs(sdir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(sdir, "LaxAttack_" + folder + ".blend"), compress=True)
    man = manifest(asset, clips, perspective="none", extra={
        "sockets": list(socks.keys()),
        "axes_usd": "origin = top-hand grip; shaft points +Z; pocket open face points +Y; stick-left = +X",
        "axes_blender": "shaft +Y, pocket face +Z",
        "ball_visual_radius_m": BALL_R, "pocket_depth_m": meta["depth"],
        "ball_clearance_m": round(meta["W"] * 0.93 * (0.30 + 0.70 * 0.42 ** 0.55) - BALL_R, 4), "kind": kind,
        "tris": tri_count(stick)})
    rep = {"tris": tri_count(stick), "materials": len(stick.data.materials), "meta": {k: (list(v) if isinstance(v, tuple) else v) for k, v in meta.items()}}
    if export:
        rep["export"] = export_asset([arm, stick] + list(socks.values()), asset, asset + "_rig",
                                     os.path.join(EXP, asset + ".usdz"), 30, clips[-1].end, False, man, list(socks.keys()))
        with open(os.path.join(EXP, asset + "_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep, arm, stick

def build_attack_stick(export=True):
    return build_stick_asset(export=export)

def build_goalie_stick(export=True):
    return build_stick_asset("goalie", "lax_stick_goalie", "GoalieStick", "helmet_teal", "cord_white", export)
