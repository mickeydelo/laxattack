# v9.7 ambient choreography: trees / shore trees sway, boats drift+bob, clouds drift. One seamless root timeline.
AMB_N = 340                      # 11.33 s @ 30 fps (matches the v8 ambient loop length)
AMB_KEYS = ("v9_tree_", "v9_shore_tree_", "v9_clouds", "v9_boat")

def _cyc(f, cycles, phase):
    return math.sin(2 * math.pi * (cycles * f / AMB_N) + phase)

def build_ambient_v9(export=True):
    reset_scene("LaxAttack_Ambient_v9"); sc = bpy.context.scene
    Dio = coll("v9_ambient_src")
    build_env_v9_export(Dio)
    bpy.context.view_layer.update()
    keep_mw = {o.name: o.matrix_world.copy() for o in bpy.data.objects if o.name.startswith(AMB_KEYS)}   # before parents (e.g. the lake) are deleted
    for o in list(bpy.data.objects):
        if not o.name.startswith(AMB_KEYS) and o.type != "CAMERA":
            bpy.data.objects.remove(o, do_unlink=True)
    for n, mw in keep_mw.items():
        o = bpy.data.objects.get(n)
        if o:
            o.parent = None; o.matrix_world = mw
    C = coll("lax_arena_ambient_v9")
    content = bpy.data.objects.new("lax_arena_ambient_v9_content", None); C.objects.link(content)
    objs = sorted([o for o in bpy.data.objects if o.name.startswith(AMB_KEYS) and o.type == "MESH"], key=lambda o: o.name)
    rnd = random.Random(97); pivots = []
    for o in objs:
        for cl in list(o.users_collection):
            cl.objects.unlink(o)
        C.objects.link(o)
        piv = bpy.data.objects.new("amb_piv_" + o.name, None); C.objects.link(piv); piv.parent = content
        piv.matrix_world = o.matrix_world.copy(); bpy.context.view_layer.update()
        o.parent = piv; o.matrix_parent_inverse.identity(); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        pivots.append(piv)
        piv.rotation_mode = "XYZ"; base_loc = piv.location.copy(); base_rot = piv.rotation_euler.copy()
        if o.name.startswith(("v9_tree_", "v9_shore_tree_")):
            amp = math.radians(rnd.uniform(0.6, 1.3)); cx, cy = rnd.choice((1, 2)), rnd.choice((2, 3)); px, py = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
            for f in range(0, AMB_N + 1, 4):
                piv.location = base_loc
                piv.rotation_euler = (base_rot.x + amp * _cyc(f, cx, px), base_rot.y + amp * 0.7 * _cyc(f, cy, py), base_rot.z)
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
        elif o.name.startswith("v9_boat"):
            ph = rnd.uniform(0, 6.28)
            for f in range(0, AMB_N + 1, 4):
                piv.location = (base_loc.x + 0.9 * _cyc(f, 1, ph), base_loc.y + 0.25 * _cyc(f, 1, ph + 1.3), base_loc.z + 0.035 * _cyc(f, 3, ph + 0.4))
                piv.rotation_euler = (base_rot.x + math.radians(2.2) * _cyc(f, 2, ph + 0.9), base_rot.y + math.radians(1.4) * _cyc(f, 3, ph), base_rot.z + math.radians(3.0) * _cyc(f, 1, ph + 2.0))
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
        elif o.name.startswith("v9_clouds"):
            for f in range(0, AMB_N + 1, 4):
                piv.location = (base_loc.x + 1.6 * _cyc(f, 1, 0.0), base_loc.y, base_loc.z + 0.25 * _cyc(f, 1, 1.4))
                piv.rotation_euler = base_rot
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
    sc.frame_start = 0; sc.frame_end = AMB_N
    sc.timeline_markers.new("ambient_v9_loop", frame=0)
    clips = [Clip("ambient_v9_loop", 0, AMB_N, True, None, notes="seamless 11.33 s: tree sway (per-tree phase/amplitude, 0.6-1.3 deg), boats drift/bob/roll, clouds drift; no synchronised motion")]
    man = manifest("lax_arena_ambient_v9", clips, perspective="none", extra={
        "usage": "Load with lax_arena_pinebrook_v9*. Play root.availableAnimations[0] (global scene animation) looped. Replaces the static v9 trees, shore trees, clouds and boats that were removed from the arena.",
        "objects": [o.name for o in objs]})
    if "palette_materials" in globals():
        palette_materials(objs, "ambient_v9", os.path.join(PROD, "Arena", "Textures"))
    rep = {"objects": len(objs), "tris": sum(tri_count(o) for o in objs)}
    if export:
        path = os.path.join(EXP, "lax_arena_ambient_v9.usdz")
        e = export_asset([content] + pivots + objs, "lax_arena_ambient_v9", "lax_arena_ambient_v9_content", path, 30, AMB_N, False, man, (), True, bake=False, content_axis=True)
        with open(os.path.join(EXP, "lax_arena_ambient_v9_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
        rep["export"] = {k: e.get(k) for k in ("usdz_bytes", "materials")}
    return rep
