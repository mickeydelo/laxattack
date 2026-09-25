# v8.1 contingency: convert a transform-animated asset into ONE skinned mesh + ONE skeleton (+ one SkelAnimation).
# Every animated object becomes a bone whose rest pose = its frame-0 world matrix; meshes bind rigidly to the nearest animated
# ancestor-or-self. Each frame, bone poses reproduce the original world matrices exactly.
def skin_transform_asset(blend, asset, src_json, frames, out_name):
    reset_scene("skin_" + out_name); sc = bpy.context.scene
    for lib in list(bpy.data.libraries):
        bpy.data.libraries.remove(lib)
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(("amb_", "life_", "fx_confetti"))]
    for o in dst.objects:
        if o is not None:
            sc.collection.objects.link(o)
    bpy.context.view_layer.update()
    objs = [o for o in dst.objects if o is not None]
    animated = {o for o in objs if o.animation_data and o.animation_data.action}
    def owner(o):
        x = o
        while x is not None:
            if x in animated:
                return x
            x = x.parent
        return None
    owners = sorted(animated, key=lambda o: o.name)
    def anc(o):
        x = o.parent
        while x is not None and x not in animated:
            x = x.parent
        return x
    W = {o: [] for o in owners}; M0 = {}
    meshes = [o for o in objs if o.type == "MESH"]
    for f in range(frames + 1):
        sc.frame_set(f)
        for o in owners:
            W[o].append(o.matrix_world.copy())
        if f == 0:
            for m in meshes:
                M0[m] = m.matrix_world.copy()
    rig = bpy.data.armatures.new(out_name + "_rig"); arm = bpy.data.objects.new(out_name + "_rig", rig); sc.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    arm.select_set(True); bpy.ops.object.mode_set(mode="EDIT")
    rb = rig.edit_bones.new("root"); rb.head = (0, 0, 0); rb.tail = (0, 0.1, 0)
    order = []
    def depth(o):
        d = 0; x = anc(o)
        while x is not None:
            d += 1; x = anc(x)
        return d
    for o in sorted(owners, key=depth):
        eb = rig.edit_bones.new(o.name); eb.head = (0, 0, 0); eb.tail = (0, 0.1, 0)
        Mn = W[o][0].normalized() if hasattr(W[o][0], "normalized") else W[o][0]
        eb.matrix = Mn; eb.length = 0.1
        p = anc(o); eb.parent = rig.edit_bones[p.name] if p is not None else rb
        order.append(o)
    bpy.ops.object.mode_set(mode="OBJECT")
    new_meshes = []
    for m in meshes:
        me = m.data.copy(); me.transform(M0[m])
        nm = bpy.data.objects.new(m.name + "_sk", me); sc.collection.objects.link(nm)
        ow = owner(m); vg = nm.vertex_groups.new(name=ow.name if ow is not None else "root")
        vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
        nm.parent = arm; nm.modifiers.new("Armature", "ARMATURE").object = arm
        new_meshes.append(nm)
    anc_n = {o.name: (anc(o).name if anc(o) is not None else None) for o in order}
    order_n = [o.name for o in order]; Wn = {o.name: W[o] for o in order}
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    Bn = {n: Wn[n][0] for n in order_n}
    for f in range(frames + 1):
        for n in order_n:
            pn = anc_n[n]; pb = arm.pose.bones[n]
            if pn is None:
                loc = Bn[n].inverted() @ Wn[n][f]
            else:
                loc = (Bn[pn].inverted() @ Bn[n]).inverted() @ (Wn[pn][f].inverted() @ Wn[n][f])
            pb.matrix_basis = loc
            pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
    ad = arm.animation_data
    if ad and ad.action and hasattr(ad.action, "fcurves"):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    sc.frame_start = 0; sc.frame_end = frames
    err = 0.0
    for f in sorted({0, frames // 3, frames // 2, frames}):
        sc.frame_set(f)
        for n in order_n:
            Mb = arm.matrix_world @ arm.pose.bones[n].matrix
            err = max(err, (Mb.translation - Wn[n][f].translation).length)
    man = json.load(open(src_json)); man["asset"] = out_name
    man["fallback_of"] = asset; man["animation_mode"] = "skinned: one mesh, one skeleton, one SkelAnimation (contingency; same clip ranges)"
    tris = sum(tri_count(o) for o in new_meshes)
    path = os.path.join(EXP, out_name + ".usdz")
    e = export_asset([arm] + new_meshes, out_name, out_name + "_rig", path, 30, frames, False, man, (), True)
    json.dump(man, open(os.path.join(EXP, out_name + "_clips.json"), "w"), indent=2)
    return {"joints": len(order) + 1, "bone_error_m": round(err, 6), "tris": tris, "kb": e["usdz_bytes"] // 1024, "meshes": e["meshes"],
            "materials": e["materials"], "root_identity": e["root_identity"], "skel_anims": e["skel_animations"], "time": e["time"]}
