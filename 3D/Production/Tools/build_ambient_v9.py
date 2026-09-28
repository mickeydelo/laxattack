# v9.7 ambient choreography: trees / shore trees sway, boats drift+bob, clouds drift. One seamless root timeline.
AMB_N = 340                      # 11.33 s @ 30 fps (matches the v8 ambient loop length)
AMB_KEYS = ("v9_tree_", "v9_shore_tree_", "v9_clouds", "v9_boat", "v9_flowers_")

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
    groups = {}
    for gname in ("ambient_trees", "ambient_shore_trees", "ambient_boat", "ambient_clouds", "ambient_fence_flowers", "ambient_foreground_flowers", "ambient_bushes"):
        e = bpy.data.objects.new(gname, None); C.objects.link(e); e.parent = content; groups[gname] = e
    objs = sorted([o for o in bpy.data.objects if o.name.startswith(AMB_KEYS) and o.type == "MESH"], key=lambda o: o.name)
    rnd = random.Random(97); pivots = []; meshes = []
    def rebase(o, base):                           # bake the object's world matrix, then move the mesh so `base` is its local origin
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4); o.data.transform(Matrix.Translation(-V(base)))
    def add_pivot(name, grp, base):
        piv = bpy.data.objects.new("amb_piv_" + name, None); C.objects.link(piv); piv.parent = groups[grp]; piv.location = base; piv.rotation_mode = "XYZ"
        pivots.append(piv); return piv
    def attach(o, piv):
        for cl in list(o.users_collection):
            cl.objects.unlink(o)
        C.objects.link(o); o.parent = piv; o.matrix_parent_inverse.identity(); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1); meshes.append(o)
    def split_crown(o):                            # trunk + base foliage (static) vs crown (sways); islands classified by centroid height
        import bmesh as _bm
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        zs = [v.co.z for v in o.data.vertices]; z0, z1 = min(zs), max(zs); zc = z0 + 0.42 * (z1 - z0)
        bm = _bm.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); seen = set(); crown_faces = []
        for v in bm.verts:
            if v.index in seen: continue
            stack = [v]; isl = []
            while stack:
                x = stack.pop()
                if x.index in seen: continue
                seen.add(x.index); isl.append(x); stack += [e.other_vert(x) for e in x.link_edges]
            if sum(q.co.z for q in isl) / len(isl) > zc:
                for q in isl:
                    crown_faces += [f for f in q.link_faces]
        cf = set(crown_faces)
        crown_me = o.data.copy(); crown = bpy.data.objects.new(o.name + "_crown", crown_me); bpy.context.scene.collection.objects.link(crown)
        b1 = _bm.new(); b1.from_mesh(o.data); b1.faces.ensure_lookup_table()
        _bm.ops.delete(b1, geom=[f for f in b1.faces if f.index in {x.index for x in cf}], context="FACES"); b1.to_mesh(o.data); b1.free()
        b2 = _bm.new(); b2.from_mesh(crown_me); b2.faces.ensure_lookup_table()
        _bm.ops.delete(b2, geom=[f for f in b2.faces if f.index not in {x.index for x in cf}], context="FACES"); b2.to_mesh(crown_me); b2.free(); bm.free()
        czs = [v.co.z for v in crown_me.vertices] or [zc]
        xs = [v.co.x for v in o.data.vertices] or [0]; ys = [v.co.y for v in o.data.vertices] or [0]
        return o, crown, V((sum(xs) / len(xs), sum(ys) / len(ys), min(czs)))
    for o in objs:
        n = o.name
        if n.startswith(("v9_tree_", "v9_shore_tree_")):
            grp = "ambient_trees" if n.startswith("v9_tree_") else "ambient_shore_trees"
            trunk, crown, cbase = split_crown(o)
            for cl in list(trunk.users_collection):
                cl.objects.unlink(trunk)
            C.objects.link(trunk); trunk.parent = groups[grp]; trunk.matrix_parent_inverse.identity(); meshes.append(trunk)      # planted, static
            rebase(crown, cbase); piv = add_pivot(crown.name, grp, cbase); attach(crown, piv)
            amp = math.radians(rnd.uniform(0.5, 1.1)); cx, cy = rnd.choice((1, 2)), rnd.choice((2, 3)); px, py = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
            for f in range(0, AMB_N + 1, 4):
                piv.location = cbase; piv.rotation_euler = (amp * _cyc(f, cx, px), amp * 0.7 * _cyc(f, cy, py), 0)
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
        elif n.startswith("v9_boat"):
            o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
            xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]; zs = [v.co.z for v in o.data.vertices]
            base = V((sum(xs) / len(xs), sum(ys) / len(ys), min(zs))); rebase(o, base); piv = add_pivot(n, "ambient_boat", base); attach(o, piv); ph = rnd.uniform(0, 6.28)
            for f in range(0, AMB_N + 1, 4):
                piv.location = (base.x + 0.9 * _cyc(f, 1, ph), base.y + 0.25 * _cyc(f, 1, ph + 1.3), base.z + 0.035 * _cyc(f, 3, ph + 0.4))    # the only vertical bob
                piv.rotation_euler = (math.radians(2.2) * _cyc(f, 2, ph + 0.9), math.radians(1.4) * _cyc(f, 3, ph), math.radians(3.0) * _cyc(f, 1, ph + 2.0))
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
        elif n.startswith("v9_clouds"):
            o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4); piv = add_pivot(n, "ambient_clouds", V((0, 0, 0))); attach(o, piv)
            for f in range(0, AMB_N + 1, 4):
                piv.location = (1.6 * _cyc(f, 1, 0.0), 0, 0); piv.rotation_euler = (0, 0, 0)          # horizontal drift only
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
        elif n.startswith("v9_flowers_"):
            grp = "ambient_foreground_flowers" if "corner" in n else "ambient_fence_flowers"
            o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
            xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]; zs = [v.co.z for v in o.data.vertices]
            base = V(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))       # planted base line
            rebase(o, base); piv = add_pivot(n, grp, base); attach(o, piv)
            amp = math.radians(rnd.uniform(0.8, 1.3)); cx = rnd.choice((2, 3)); px = rnd.uniform(0, 6.28)
            for f in range(0, AMB_N + 1, 4):                     # bend about the base line only (X axis): no vertical lift of the clumps
                piv.location = base; piv.rotation_euler = (amp * _cyc(f, cx, px), 0, 0)
                piv.keyframe_insert("location", frame=f); piv.keyframe_insert("rotation_euler", frame=f)
    objs = meshes
    sc.frame_start = 0; sc.frame_end = AMB_N
    sc.timeline_markers.new("ambient_v9_loop", frame=0)
    clips = [Clip("ambient_v9_loop", 0, AMB_N, True, None, notes="seamless 11.33 s; planted: tree crowns sway about the trunk top, flowers bend about their base line, only the boat bobs; groups ambient_trees/_shore_trees/_boat/_clouds/_fence_flowers/_foreground_flowers/_bushes")]
    man = manifest("lax_arena_ambient_v9", clips, perspective="none", extra={
        "usage": "Load with lax_arena_pinebrook_v9*. Play root.availableAnimations[0] (global scene animation) looped. Replaces the static v9 trees, shore trees, clouds and boats that were removed from the arena.",
        "objects": [o.name for o in objs], "groups": ["ambient_trees", "ambient_shore_trees", "ambient_boat", "ambient_clouds", "ambient_fence_flowers", "ambient_foreground_flowers", "ambient_bushes"], "group_toggle": "disable a group entity to drop its motion and geometry (e.g. ambient_fence_flowers / ambient_foreground_flowers on low tier)"})
    if "palette_materials" in globals():
        palette_materials(objs, "ambient_v9", os.path.join(PROD, "Arena", "Textures"))
    rep = {"objects": len(objs), "tris": sum(tri_count(o) for o in objs)}
    if export:
        path = os.path.join(EXP, "lax_arena_ambient_v9.usdz")
        e = export_asset([content] + list(groups.values()) + pivots + objs, "lax_arena_ambient_v9", "lax_arena_ambient_v9_content", path, 30, AMB_N, False, man, (), True, bake=False, content_axis=True)
        with open(os.path.join(EXP, "lax_arena_ambient_v9_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
        rep["export"] = {k: e.get(k) for k in ("usdz_bytes", "materials")}
    return rep
