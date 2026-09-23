# Lax Attack Phase 4: goal cage + animated net (lax_goal.usdz). Mouth faces the shooter (Blender +Y = game +Z).
# Net impact regions use the SHOOTER's perspective: *_left = shooter-left = game -X = Blender +X.
GOAL_DIR = os.path.join(PROD, "Goal")
NET_U = (0.2, 0.5, 0.8); NET_V = (0.3, 0.62, 0.95); NET_W = 0.62   # bone grid on the net (u across, v up, w depth)

def build_goal_asset(export=True):
    reset_scene("LaxAttack_Goal")
    C = coll("lax_goal")
    frame_parts, cords, gmeta, net_pt = goal_geo()
    ad = bpy.data.armatures.new("lax_goal_rig"); arm = bpy.data.objects.new("lax_goal_rig", ad); C.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    r = ad.edit_bones.new("goal_root"); r.head = (0, 0, 0); r.tail = (0, 0, 0.3)
    bones = {}
    for i, u in enumerate(NET_U):
        for j, v in enumerate(NET_V):
            n = "net_%d%d" % (i, j); p = net_pt(u, v, NET_W)
            b = ad.edit_bones.new(n); b.head = p; b.tail = p + V((0, -0.15, 0)); b.parent = r; b.roll = 0
            bones[n] = V(p)
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    # frame: static, parented to the rig object (not skinned)
    Bf = Builder("lax_goal_frame")
    for gg in frame_parts:
        Bf.add(gg, "goal_orange")
    frame = Bf.build(C, parent=arm)
    # net: skinned to the bone grid, mouth rim pinned to goal_root
    def net_w(p):
        w = min(1.0, max(0.0, -p.y / gmeta["depth"]))
        pin = smoothstep(0.05, 0.35, w) * (1 - 0.35 * smoothstep(0.85, 1.0, w))   # rim and rear bar stay firmer
        ws = {}
        for n, q in bones.items():
            d = (p - q).length
            ws[n] = math.exp(-(d / 0.55) ** 2)
        tot = sum(ws.values()) or 1.0
        out = {n: pin * x / tot for n, x in ws.items()}
        out["goal_root"] = 1.0 - pin
        return out
    Bn = Builder("lax_goal_net")
    for gg in cords:
        Bn.add(gg, "cord_white", weights=net_w)
    net = Bn.build(C, arm)
    # sockets / references (static, parented to the rig object)
    def empty(name, loc, size=0.1, scale=(1, 1, 1), kind="ARROWS"):
        e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
        C.objects.link(e); e.parent = arm; e.location = loc; e.scale = scale
        return e
    H = gmeta["mouth_h"]; Wd = gmeta["mouth_w"]; Dp = gmeta["depth"]
    socks = {"goal_sensor_socket": empty("goal_sensor_socket", (0, -0.05, H / 2)),
             "net_collision_reference": empty("net_collision_reference", (0, -Dp * 0.42, H * 0.45), 0.5, (Wd / 2, Dp * 0.42, H * 0.45), "CUBE")}
    impacts = {"net_impact_center": (0.5, 0.55), "net_impact_high_left": (0.8, 0.85), "net_impact_high_right": (0.2, 0.85),
               "net_impact_low_left": (0.8, 0.25), "net_impact_low_right": (0.2, 0.25)}
    for n, (u, v) in impacts.items():
        socks[n] = empty(n, tuple(net_pt(u, v, 0.55)), 0.12)
    # ---- net clips
    def impact_fn(u0, v0, amp, heavy=False):
        c0 = net_pt(u0, v0, NET_W)
        def fn(bone, t):   # t in frames since impact
            q = bones[bone]; d = (q - c0).length
            reach = math.exp(-(d / (0.9 if heavy else 0.65)) ** 2)
            delay = d / 7.0 * 30.0                 # travelling ripple, ~7 m/s
            tt = (t - delay) / 30.0
            if tt <= 0:
                return (0.0, 0.0, 0.0)
            env = (1 - math.exp(-tt / 0.025)) * math.exp(-tt * (3.2 if heavy else 4.2))
            osc = math.cos(2 * math.pi * (2.6 if heavy else 3.2) * tt)
            k = amp * reach * env * osc
            return (0.0, -k, -0.35 * abs(k) * min(1.0, q.z / 0.9))   # pocket back (away from shooter); sag only up high
        return fn
    def idle_fn(bone, t):
        q = bones[bone]; ph = 2 * math.pi * t / 60.0
        return (0.0, 0.012 * math.sin(ph + q.x * 2.0 + q.z), 0.006 * math.sin(ph * 2 + q.x))
    def settle_fn(bone, t):
        tt = t / 30.0; q = bones[bone]
        k = 0.18 * math.exp(-tt * 4.0) * math.cos(2 * math.pi * 2.4 * tt + q.x)
        return (0.0, -k, -0.3 * abs(k) * min(1.0, q.z / 0.9))
    specs = [("net_idle", 0, 60, True, idle_fn, None, "gentle breeze sway (loop)"),
             ("net_impact_center", 70, 24, False, impact_fn(0.5, 0.55, 0.55), 0, "shot into the middle"),
             ("net_impact_high_left", 100, 24, False, impact_fn(0.8, 0.85, 0.55), 0, "shooter-left top corner"),
             ("net_impact_high_right", 130, 24, False, impact_fn(0.2, 0.85, 0.55), 0, "shooter-right top corner"),
             ("net_impact_low_left", 160, 24, False, impact_fn(0.8, 0.25, 0.50), 0, "shooter-left bottom corner"),
             ("net_impact_low_right", 190, 24, False, impact_fn(0.2, 0.25, 0.50), 0, "shooter-right bottom corner"),
             ("net_impact_heavy", 220, 36, False, impact_fn(0.5, 0.55, 0.80, True), 0, "hard shot: deeper pocketing, wider ripple"),
             ("net_settle", 265, 30, False, settle_fn, None, "generic damped settle from a displaced state")]
    prefs = bpy.context.preferences.edit; old = prefs.keyframe_new_interpolation_type; prefs.keyframe_new_interpolation_type = "LINEAR"
    anim = arm.animation_data_create(); clips = []
    try:
        for name, start, length, loop, fn, contact, notes in specs:
            act = bpy.data.actions.new(name); act.use_fake_user = True; anim.action = act
            for f in range(length + 1):
                x = f / length   # envelopes guarantee an exact return to the rest pose
                env = (0.5 - 0.5 * math.cos(2 * math.pi * x)) if loop else (1.0 - smoothstep(0.72, 1.0, x))
                for bn in bones:
                    arm.pose.bones[bn].location = arm.data.bones[bn].matrix_local.to_3x3().inverted() @ (V(fn(bn, f)) * env)
                    arm.pose.bones[bn].keyframe_insert("location", frame=f, group=bn)
            anim.action = None
            clips.append(Clip(name, start, length, loop, None, contact=contact, notes=notes))
    finally:
        prefs.keyframe_new_interpolation_type = old
    tr = anim.nla_tracks.new(); tr.name = "clips"
    for i, c in enumerate(clips):
        act = bpy.data.actions[c.name]; st = tr.strips.new(c.name, c.start, act)
        if hasattr(st, "action_slot") and st.action_slot is None and len(act.slots):
            st.action_slot = act.slots[0]
        st.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD"
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
    bpy.context.scene.frame_end = clips[-1].end
    os.makedirs(GOAL_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(GOAL_DIR, "LaxAttack_Goal.blend"), compress=True)
    man = manifest("lax_goal", clips, perspective="none", extra={
        "left_right_convention": "impact regions use the SHOOTER's perspective: *_left = shooter-left = game -X",
        "hierarchy": ["lax_goal/lax_goal_rig/lax_goal_frame", "lax_goal/lax_goal_rig/lax_goal_net (skinned)"] + ["lax_goal/lax_goal_rig/" + s for s in socks],
        "mouth_m": [Wd, H], "depth_m": Dp, "pipe_radius_m": gmeta["pipe_r"],
        "goal_line": "mouth plane is at asset z = 0; the net extends toward -Z (away from the shooter)",
        "net_collision_reference": "empty whose scale gives the half-extents of a simple box covering the net volume",
        "tris": {"frame": tri_count(frame), "net": tri_count(net)}})
    rep = {"tris": man["tris"], "materials": len(frame.data.materials) + len(net.data.materials)}
    if export:
        rep["export"] = export_asset([arm, frame, net] + list(socks.values()), "lax_goal", "lax_goal_rig", os.path.join(EXP, "lax_goal.usdz"),
                                     30, clips[-1].end, False, man, list(socks.keys()))
        with open(os.path.join(EXP, "lax_goal_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep, arm, net, clips
