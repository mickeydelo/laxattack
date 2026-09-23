# Lax Attack: ambient arena life (lax_arena_ambient.usdz): swaying trees/hedges, fluttering pennants, bobbing sailboats, drifting clouds.
# Separate from the static arena so it can be toggled per performance tier. Positions match build_scene / build_arena.
TREES = [(4.2, -15.0, 4.6), (6.8, -16.5, 5.4), (9.5, -14.2, 4.8), (-7.6, -15.2, 5.0), (-9.8, -17.0, 5.6), (11.8, -17.5, 5.0), (-12.5, -14.6, 4.6)]
PINES = [(13.5, -15.5, 5.8), (-14.0, -18.5, 6.2)]
HEDGE_X = (-2.4, -1.3, -0.2, 0.9, 2.0, 3.1, -3.5, -5.2, 5.4)
FLAGS = [((6.8, -12.4), "kit_red"), ((-6.8, -12.4), "accent_teal"), ((6.8, -4.0), "accent_gold"), ((-6.8, -4.0), "kit_red")]
BOATS = [((-5.5, -31.5), 1.5), ((8.5, -37.0), 1.1)]
CLOUDS = [(-13, -70, 14.5, 4.0), (9, -78, 17.5, 4.6), (-1, -95, 23, 3.6), (21, -92, 13, 3.2), (-24, -88, 20, 4.2)]
N_LOOP = 240

def _bake(ob):
    bpy.context.view_layer.update()
    ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix.Identity(4)

def _skin(ob, arm, fn):
    _bake(ob)
    for v in ob.data.vertices:
        for b, w in fn(v.co).items():
            if w > 1e-4:
                vg = ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)
                vg.add([v.index], w, "REPLACE")
    ob.parent = arm; ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob

def build_ambient(export=True):
    reset_scene("LaxAttack_Ambient")
    C = coll("lax_arena_ambient")
    ad = bpy.data.armatures.new("lax_arena_ambient_rig"); arm = bpy.data.objects.new("lax_arena_ambient_rig", ad); C.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = ad.edit_bones.new("amb_root"); root.head = (0, 0, -0.45); root.tail = (0, 0, 0.5)
    def bone(n, h, t):
        b = ad.edit_bones.new(n); b.head = h; b.tail = t; b.parent = root; return b
    for i, (x, y, h) in enumerate(TREES + PINES):
        bone("tree_%d" % i, (x, y, -0.45), (x, y, h * 0.6))
    for i, x in enumerate(HEDGE_X):
        bone("hedge_%d" % i, (x, -13.3, -0.45), (x, -13.3, 0.6))
    for i, ((x, y), m) in enumerate(FLAGS):
        prev = None
        for k in range(3):
            b = bone("flag_%d_%d" % (i, k), (x, y + 0.02, 1.95 - 0.0), (x, y + 0.02, 1.95))
            b.head = (x - 0.25 * k * (1 if x < 0 else -1), y, 1.95); b.tail = (x - 0.25 * (k + 1) * (1 if x < 0 else -1), y, 1.95)
            if prev:
                b.parent = prev; b.use_connect = True
            prev = b
    for i, ((x, y), s) in enumerate(BOATS):
        bone("boat_%d" % i, (x, y, -0.40), (x, y, 0.6))
    for i, (x, y, z, s) in enumerate(CLOUDS):
        bone("cloud_%d" % i, (x, y, z), (x, y, z + 1.0))
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    objs = []
    for i, (x, y, h) in enumerate(TREES):
        o = deciduous(40 + i, h, C, loc=(x, y, -0.45), n=11)
        objs.append(_skin(o, arm, lambda co, i=i, h=h: {"tree_%d" % i: smoothstep(0.25 * h, 0.95 * h, co.z + 0.45), "amb_root": 1 - smoothstep(0.25 * h, 0.95 * h, co.z + 0.45)}))
    for j, (x, y, h) in enumerate(PINES):
        i = len(TREES) + j; o = pine(10 + j, h, C, loc=(x, y, -0.45))
        objs.append(_skin(o, arm, lambda co, i=i, h=h: {"tree_%d" % i: smoothstep(0.2 * h, 1.0 * h, co.z + 0.45), "amb_root": 1 - smoothstep(0.2 * h, 1.0 * h, co.z + 0.45)}))
    for i, x in enumerate(HEDGE_X):
        o = bush(60 + i, 1.0 + 0.25 * (i % 3), C, loc=(x, -13.3 - 0.3 * (i % 2), -0.45))
        objs.append(_skin(o, arm, lambda co, i=i: {"hedge_%d" % i: smoothstep(-0.4, 0.8, co.z), "amb_root": 1 - smoothstep(-0.4, 0.8, co.z)}))
    for i, ((x, y), m) in enumerate(FLAGS):
        sgn = 1 if x < 0 else -1; B = Builder("flag_%d" % i)
        B.add(sweep([(x, y, 0), (x, y, 2.05)], [0.035, 0.03], 8, 1.0), "wood_dark")
        B.add(ellipsoid((x, y, 2.07), (0.05, 0.05, 0.05), 10, 6), "accent_gold")
        verts = [(x, y, 1.95 + 0.16), (x, y, 1.95 - 0.16), (x + sgn * 0.75, y, 1.95)]
        pen = merge(([verts[0], verts[1], verts[2]], [(0, 1, 2)]), ([verts[0], verts[2], verts[1]], [(0, 1, 2)]))
        B.add(pen, m, smooth=False)
        o = B.build(C)
        def fw(co, i=i, x=x, sgn=sgn):
            d = abs(co.x - x)
            if co.z < 1.7 or d < 0.01:
                return {"amb_root": 1.0}
            k = min(2, int(d / 0.25)); return {"flag_%d_%d" % (i, k): 1.0}
        objs.append(_skin(o, arm, fw))
    for i, ((x, y), s) in enumerate(BOATS):
        o = sailboat(C, (x, y, -0.40), s)
        objs.append(_skin(o, arm, lambda co, i=i: {"boat_%d" % i: 1.0}))
    for i, (x, y, z, s) in enumerate(CLOUDS):
        o = cloud(90 + i, C, (x, y, z), s)
        objs.append(_skin(o, arm, lambda co, i=i: {"cloud_%d" % i: 1.0}))
    # ---- clips: integer cycles over the loop so it is seamless
    def loop_pose(t, gust=0.0):
        w = 2 * math.pi * t / N_LOOP; P_ = {}
        for i, (x, y, h) in enumerate(TREES + PINES):
            a = (2.2 + 3.0 * gust) * math.sin(4 * w + x * 0.35) + 0.8 * math.sin(9 * w + y)
            P_["tree_%d" % i] = ("rot", (math.radians(a * 0.4), 0, math.radians(a)))
        for i, x in enumerate(HEDGE_X):
            P_["hedge_%d" % i] = ("rot", (0, 0, math.radians((2.5 + 3 * gust) * math.sin(6 * w + x))))
        for i in range(len(FLAGS)):
            for k in range(3):
                P_["flag_%d_%d" % (i, k)] = ("rot", (math.radians((10 + 8 * gust) * math.sin(16 * w - k * 1.1 + i)), 0, math.radians((14 + 10 * gust) * math.sin(12 * w - k * 0.9 + i))))
        for i, ((x, y), s) in enumerate(BOATS):
            P_["boat_%d" % i] = ("both", (0.9 * math.sin(w + i), 0.06 * math.sin(6 * w + i), 0.0),
                                 (math.radians(3 * math.sin(5 * w + i)), math.radians(2 * math.sin(3 * w + i)), 0))
        for i, (x, y, z, s) in enumerate(CLOUDS):
            P_["cloud_%d" % i] = ("loc", (1.6 * math.sin(w + i * 1.3), 0.3 * math.sin(2 * w + i), 0.0))
        return P_
    prefs = bpy.context.preferences.edit; old = prefs.keyframe_new_interpolation_type; prefs.keyframe_new_interpolation_type = "LINEAR"
    anim = arm.animation_data_create(); clips = []
    specs = [("ambient_loop", 0, N_LOOP, True, 0.0, "seamless 8 s breeze: trees/hedges sway, pennants flutter, boats bob and drift, clouds glide"),
             ("ambient_gust", 250, 90, False, 1.0, "stronger gust (blend in/out from ambient_loop; returns to the loop's frame-0 pose)")]
    try:
        for name, start, L, loop, gust, notes in specs:
            act = bpy.data.actions.new(name); act.use_fake_user = True; anim.action = act
            for f in range(L + 1):
                gg = gust * math.sin(math.pi * f / L) if not loop else 0.0
                for bn, (kind, a, *b) in loop_pose(f if loop else f * N_LOOP / L * 0.25, gg).items():
                    pb = arm.pose.bones[bn]
                    M3 = arm.data.bones[bn].matrix_local.to_3x3().inverted()
                    if kind in ("loc", "both"):
                        pb.location = M3 @ V(a); pb.keyframe_insert("location", frame=f, group=bn)
                    if kind in ("rot", "both"):
                        pb.rotation_euler = a if kind == "rot" else b[0]; pb.keyframe_insert("rotation_euler", frame=f, group=bn)
            anim.action = None
            clips.append(Clip(name, start, L, loop, None, notes=notes))
    finally:
        prefs.keyframe_new_interpolation_type = old
    tr = anim.nla_tracks.new(); tr.name = "clips"
    for i, c in enumerate(clips):
        act = bpy.data.actions[c.name]; st = tr.strips.new(c.name, c.start, act)
        if hasattr(st, "action_slot") and st.action_slot is None and len(act.slots):
            st.action_slot = act.slots[0]
        st.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD"
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
    sc = bpy.context.scene; sc.frame_end = clips[-1].end
    for c in clips:
        sc.timeline_markers.new(c.name, frame=c.start)
    tris = sum(tri_count(o) for o in objs)
    d = os.path.join(PROD, "Arena"); bpy.ops.wm.save_as_mainfile(filepath=os.path.join(d, "LaxAttack_Ambient.blend"), compress=True)
    man = manifest("lax_arena_ambient", clips, perspective="none", extra={
        "usage": "place at the scene origin with lax_arena_pinebrook; hide the static arena group 'midground_trees' while this asset is shown",
        "contents": ["7 broadleaf trees + 2 pines (sway)", "9 hedges behind the goal (sway)", "4 pennant flags on the fence (flutter)",
                     "2 sailboats (bob, roll, drift)", "5 clouds (glide)"], "tris": tris})
    rep = {"tris": tris}
    if export:
        path = os.path.join(EXP, "lax_arena_ambient.usdz")
        e = export_asset([arm] + objs, "lax_arena_ambient", "lax_arena_ambient_rig", path, 30, clips[-1].end, False, man, ())
        rep.update(y=e["baked_y_range"], kb=e["usdz_bytes"] // 1024, meshes=e["meshes"], root=e["root_identity"])
        with open(os.path.join(EXP, "lax_arena_ambient_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep
