# Lax Attack Blender-side validation for rigged characters (run after bake_clips).
def validate_character(arm, clips, meshes, stick_meta, required_sockets, required_clips, tri_budget=(25000, 45000)):
    sc = bpy.context.scene; ad = arm.data; rep = {"errors": [], "warnings": []}
    E = rep["errors"].append; W = rep["warnings"].append
    rep["unit_scale"] = sc.unit_settings.scale_length; rep["fps"] = sc.render.fps
    if sc.unit_settings.scale_length != 1.0 or sc.unit_settings.system != "METRIC":
        E("scene units are not metric 1.0")
    for o in [arm] + meshes:
        if o.matrix_world != Matrix.Identity(4):
            E("non-identity object transform: " + o.name)
    names = [c.name for c in clips]
    rep["missing_clips"] = [c for c in required_clips if c not in names]
    for c in rep["missing_clips"]:
        E("missing clip " + c)
    socks = {o.name for o in bpy.data.objects if o.parent == arm and o.type == "EMPTY"}
    rep["missing_sockets"] = [s for s in required_sockets if s not in socks]
    for s in rep["missing_sockets"]:
        E("missing socket " + s)
    tris = sum(len(p.vertices) - 2 for o in meshes for p in o.data.polygons); rep["tris"] = tris
    if not tri_budget[0] <= tris <= tri_budget[1]:
        W("triangles %d outside target %s" % (tris, tri_budget))
    mats = {m.name for o in meshes for m in o.data.materials}; rep["materials"] = len(mats)
    for o in meshes:
        if not any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers):
            E("mesh not bound to armature: " + o.name)
        if len(o.vertex_groups) == 0:
            E("mesh has no weights: " + o.name)
    missing_tex = [i.filepath for i in bpy.data.images if i.source == "FILE" and not os.path.exists(bpy.path.abspath(i.filepath))]
    rep["missing_textures"] = missing_tex
    for t in missing_tex:
        E("missing texture " + t)
    # per-clip motion checks
    bs = arm.get("body_scale", 1.0); hk = arm.get("head_k", 1.0)
    helmet_r = 0.27 * hk * 1.13 * 0.98; glove_r = 0.075
    root_rest = ad.bones["root"].matrix_local
    stats = {}
    dg = bpy.context.evaluated_depsgraph_get
    for c in clips:
        s = dict(hand_err=0.0, foot_err=0.0, ankle_z_min=9.0, glove_helmet_clear=9.0, shaft_helmet_clear=9.0, root_dev=0.0,
                 ball_pocket_err=0.0)
        for f in range(c.start, c.end + 1):
            sc.frame_set(f)
            e = arm.evaluated_get(dg()).pose.bones
            for sd in ("L", "R"):
                s["hand_err"] = max(s["hand_err"], (e["forearm_" + sd].tail - e["ik_hand_" + sd].head).length)
                s["foot_err"] = max(s["foot_err"], (e["shin_" + sd].tail - e["ik_foot_" + sd].head).length)
                s["ankle_z_min"] = min(s["ankle_z_min"], e["foot_" + sd].head.z)
            hc = e["head"].matrix @ V((0, 0.27 * hk * 0.85, 0))   # helmet centre along the head bone
            for sd in ("L", "R"):
                s["glove_helmet_clear"] = min(s["glove_helmet_clear"], (e["forearm_" + sd].tail - hc).length - helmet_r - glove_r)
            Ms = e["stick"].matrix
            for i in range(0, 13):
                y = stick_meta["shaft"][0] + i * (stick_meta["y1"] - stick_meta["shaft"][0]) / 12
                s["shaft_helmet_clear"] = min(s["shaft_helmet_clear"], (Ms @ V((0, y, 0)) - hc).length - helmet_r - 0.02)
            s["root_dev"] = max(s["root_dev"], max(abs(a - b) for ra, rb in zip(e["root"].matrix, root_rest) for a, b in zip(ra, rb)))
        stats[c.name] = {k: round(v, 4) for k, v in s.items()}
        if s["hand_err"] > 0.01:
            W("%s: hand IK error %.3f" % (c.name, s["hand_err"]))
        if s["root_dev"] > 1e-5:
            E("%s: root moved" % c.name)
        if s["ankle_z_min"] < 0.05 * bs:
            W("%s: ankle below field level" % c.name)
    rep["clip_stats"] = stats
    seams = {}
    for c in clips:
        if not c.loop:
            continue
        sc.frame_set(c.start); a = {b.name: b.matrix.copy() for b in arm.evaluated_get(dg()).pose.bones}
        sc.frame_set(c.end); b = {k.name: k.matrix.copy() for k in arm.evaluated_get(dg()).pose.bones}
        seams[c.name] = round(max(max(abs(x - y) for ra, rb in zip(a[k], b[k]) for x, y in zip(ra, rb)) for k in a), 5)
        if seams[c.name] > 0.01:
            W("%s loop seam %.4f" % (c.name, seams[c.name]))
    rep["loop_seams"] = seams
    # ball / pocket clearance (static, stick space)
    rep["ball_pocket"] = {"ball_r": stick_meta["ball_r"], "pocket_depth": stick_meta["depth"],
                          "ball_centre_above_bag": round(stick_meta["pocket_center"][2] - stick_meta["ball_contact"][2], 4),
                          "head_inner_half_width": round(stick_meta["W"] * 0.93 * (0.30 + 0.70 * 0.42 ** 0.55), 4)}
    if rep["ball_pocket"]["head_inner_half_width"] < stick_meta["ball_r"]:
        E("ball wider than pocket")
    sc.frame_set(0)
    return rep
