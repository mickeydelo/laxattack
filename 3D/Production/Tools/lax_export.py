# Lax Attack runtime export: Blender USD export + pxr post-process (identity root at field level, axis conversion on the
# rig/content child prim), optional 180-degree yaw for assets that must face +Z (goalie), USDZ packaging, verification.
def export_asset(objects, root_name, content_name, out_usdz, fps=30, end_frame=0, face_plus_z=False, manifest=None,
                 sockets=(), animated=True, tmp="/tmp/laxattack_export", bake=True, content_axis=False):
    from pxr import Usd, UsdGeom, UsdSkel, Sdf, Gf, Kind, UsdUtils
    import shutil
    os.makedirs(tmp, exist_ok=True)
    raw = os.path.join(tmp, root_name + ".usdc"); fixed = os.path.join(tmp, root_name + "_fixed.usdc")
    sc = bpy.context.scene; sc.render.fps, sc.render.fps_base = fps, 1.0
    if getattr(bpy.context, "object", None) and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objects:
        o.hide_set(False); o.hide_render = False; o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.context.view_layer.update()                 # never read stale matrix_world (arena origin-stacking bug)
    if bake:
        objects = merge_skinned(objects)            # one skinned mesh per rig: no multi-mesh skin merge in RealityKit
        bake_axes(objects, content_name, face_plus_z)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    want = dict(filepath=raw, selected_objects_only=True, export_animation=animated, export_armatures=True,
                only_deform_bones=True, export_materials=True, generate_preview_surface=True, export_textures=True,
                overwrite_textures=True, relative_paths=True, export_uvmaps=True, export_normals=True, export_mesh_colors=False,
                convert_orientation=False,
                export_lights=False, export_cameras=False, export_shapekeys=False, author_blender_name=False,
                export_custom_properties=False, root_prim_path="/" + root_name, evaluation_mode="RENDER")
    props = {p.identifier for p in bpy.ops.wm.usd_export.get_rna_type().properties}
    args = {k: v for k, v in want.items() if k in props}
    sc.frame_start, sc.frame_end = 0, max(end_frame, 0)
    bpy.ops.wm.usd_export(**args)
    st = Usd.Stage.Open(raw)
    root = st.GetPrimAtPath("/" + root_name); content = st.GetPrimAtPath("/%s/%s" % (root_name, content_name))
    assert root and content, "unexpected hierarchy: %s" % [str(p.GetPath()) for p in st.Traverse()][:12]
    for prim in (root, content):
        UsdGeom.Xformable(prim).ClearXformOpOrder()
        for a in list(prim.GetAttributes()):
            if a.GetName().startswith("xformOp:"):
                prim.RemoveProperty(a.GetName())
    # axis conversion is baked into geometry + skeleton rest pose (bake_axes): every prim stays identity.
    # Transform-animated assets (ambient) keep local pivots instead: the conversion sits on the content prim only.
    if content_axis:
        UsdGeom.Xformable(content).AddRotateXYZOp().Set(Gf.Vec3f(90, 0, 180))
    st.SetDefaultPrim(root); Usd.ModelAPI(root).SetKind(Kind.Tokens.component)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(st, 1.0)
    st.SetTimeCodesPerSecond(fps); st.SetFramesPerSecond(fps); st.SetStartTimeCode(0); st.SetEndTimeCode(max(end_frame, 0))
    meta = {"facing": "+Z" if face_plus_z else "-Z", "up": "+Y", "origin": "field level"}
    if manifest:
        meta["clipManifest"] = json.dumps(manifest)
    root.SetCustomDataByKey("laxattack", meta)
    pad_influences(st, 4)                           # uniform 4 influences on every skinned mesh
    st.GetRootLayer().Export(fixed)
    # copy textures next to the fixed layer so the packager finds them
    for d in ("textures",):
        src = os.path.join(tmp, d)
        if os.path.isdir(src):
            pass
    rep = verify_usd(fixed, root_name, sockets, end_frame, animated)
    if os.path.exists(out_usdz):
        os.remove(out_usdz)
    os.makedirs(os.path.dirname(out_usdz), exist_ok=True)
    ok = False
    try:
        ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(fixed), out_usdz); rep["packager"] = "ARKit"
    except Exception as ex:
        rep["arkit_err"] = repr(ex)[:200]
    if not ok or not os.path.exists(out_usdz):
        ok = UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(fixed), out_usdz); rep["packager"] = "generic"
    rep["usdz_bytes"] = os.path.getsize(out_usdz) if os.path.exists(out_usdz) else 0
    z = Usd.Stage.Open(out_usdz)
    rep["usdz_open"] = bool(z and z.GetDefaultPrim())
    rep["objects"] = [o.name for o in objects]
    return rep

def export_lods(rep, root_name, content_name, out_usdz, ratios, fps=30, end_frame=0, manifest=None, animated=True, protect=True, keep=()):
    """Decimated LODs of an already-exported (baked) asset: <name>_lod1.usdz, _lod2.usdz ..."""
    res = {}; objs = [bpy.data.objects[n] for n in rep["objects"] if n in bpy.data.objects]; prev = 1.0
    seen = set()                                    # LODs reference 1024 copies of any larger texture
    for o in objs:
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            if not (m and m.node_tree):
                continue
            for nd in m.node_tree.nodes:
                im = getattr(nd, "image", None)
                if im is None or im.name in seen or im.size[0] <= 1024:
                    continue
                seen.add(im.name); fp = bpy.path.abspath(im.filepath); root_, ext = os.path.splitext(fp)
                if "_1k" in root_:
                    continue
                im.scale(1024, 1024); new = root_ + "_1k" + ext; im.filepath_raw = new
                im.file_format = "JPEG" if ext.lower() in (".jpg", ".jpeg") else "PNG"; im.save(); im.filepath = new
    for i, r in enumerate(ratios, 1):
        hb = globals().get("HEAD_BONES", set()) if protect else set()
        for o in objs:
            if o.type == "MESH" and len(o.data.polygons) > 60 and not any(o.name.startswith(k) for k in keep):
                m = o.modifiers.new("lod", "DECIMATE"); m.ratio = r / prev
                idx = {vg.index for vg in o.vertex_groups if vg.name in hb}
                if idx:                                   # never decimate the head/face (eyes, mouth, lids, hair, headgear)
                    prot = o.vertex_groups.get("lod_protect") or o.vertex_groups.new(name="lod_protect")
                    ids = [v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in idx) > 0.3]
                    prot.add(ids, 1.0, "REPLACE"); m.vertex_group = "lod_protect"; m.invert_vertex_group = True
                bpy.context.view_layer.objects.active = o
                while o.modifiers.find("lod") > 0:
                    bpy.ops.object.modifier_move_up(modifier="lod")
                bpy.ops.object.modifier_apply(modifier="lod")
        prev = r
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs if o.type == "MESH")
        path = out_usdz.replace(".usdz", "_lod%d.usdz" % i)
        e = export_asset(objs, root_name, content_name, path, fps, end_frame, False, manifest, (), animated, bake=False)
        res["lod%d" % i] = {"tris": tris, "kb": e["usdz_bytes"] // 1024, "root_identity": e["root_identity"]}
    return res

def merge_skinned(objects):
    arms = [o for o in objects if o.type == "ARMATURE"]
    out = list(objects)
    for a in arms:
        sk = [o for o in objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == a for m in o.modifiers)]
        if len(sk) < 2:
            continue
        for x in bpy.context.selected_objects:
            x.select_set(False)
        for o in sk:
            o.select_set(True)
        bpy.context.view_layer.objects.active = sk[0]
        bpy.ops.object.join()
        sk[0].name = a.name.replace("_rig", "") + "_body"; sk[0].data.name = sk[0].name
        out = [o for o in out if o not in sk[1:] and o.name in bpy.data.objects]
    return out

def pad_influences(st, n):
    from pxr import UsdSkel, UsdGeom, Vt
    for p in st.Traverse():
        if not p.IsA(UsdGeom.Mesh):
            continue
        b = UsdSkel.BindingAPI(p); ji = b.GetJointIndicesPrimvar(); jw = b.GetJointWeightsPrimvar()
        if not ji or not ji.HasValue():
            continue
        k = ji.GetElementSize(); I = list(ji.Get()); W = list(jw.Get())
        if k == n:
            continue
        nv = len(I) // k; I2, W2 = [], []
        for v in range(nv):
            ii = I[v * k:(v + 1) * k]; ww = W[v * k:(v + 1) * k]
            pairs = sorted(zip(ww, ii), reverse=True)[:n]; tot = sum(w for w, _ in pairs) or 1.0
            pairs += [(0.0, pairs[0][1] if pairs else 0)] * (n - len(pairs))
            I2 += [i for _, i in pairs]; W2 += [w / tot for w, _ in pairs]
        ji.Set(Vt.IntArray(I2)); ji.SetElementSize(n); jw.Set(Vt.FloatArray(W2)); jw.SetElementSize(n)

def bake_axes(objects, content_name, face_plus_z):
    """Bake the Blender->RealityKit axis change (and optional +Z facing) into mesh data, bone rest poses and socket
    transforms, so the exported USD has identity transforms on every prim (fixes combined skinned-mesh bind issues)."""
    R = Euler((math.radians(90), 0, math.radians(180)), "XYZ").to_matrix().to_4x4()
    if face_plus_z:
        R = R @ Matrix.Rotation(math.pi, 4, "Z")
    arms = [o for o in objects if o.type == "ARMATURE"]
    for a in arms:
        a.data.pose_position = "REST"
    bpy.context.view_layer.update()
    emp = {o: o.matrix_world.copy() for o in objects if o.type == "EMPTY" and o.name != content_name
           and not any(c.parent == o for c in objects)}   # group empties stay identity
    meshes = [o for o in objects if o.type == "MESH"]; parents = {}
    for o in meshes:
        mw = o.matrix_world.copy(); parents[o] = o.parent
        o.parent = None; o.matrix_world = Matrix.Identity(4)
        o.data.transform(R @ mw); o.data.update()
    for a in arms:
        for x in bpy.context.selected_objects:
            x.select_set(False)
        bpy.context.view_layer.objects.active = a; a.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        ebs = a.data.edit_bones   # exact rigid re-orientation (keeps roll): set full matrices, parents first
        old = {eb.name: (eb.matrix.copy(), eb.length) for eb in ebs}
        order = []
        def walk(b):
            order.append(b.name)
            for ch in b.children:
                walk(ch)
        for b in [b for b in ebs if b.parent is None]:
            walk(b)
        for n in order:
            M, L = old[n]; eb = ebs[n]
            eb.matrix = R @ M; eb.length = L
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in meshes:
        if parents[o] is not None:
            o.parent = parents[o]; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for o, mw in emp.items():
        o.matrix_world = R @ mw
    for a in arms:
        a.data.pose_position = "POSE"
    bpy.context.view_layer.update()

def verify_usd(path, root_name, sockets, end_frame, animated):
    from pxr import Usd, UsdGeom, UsdSkel, Gf, UsdShade
    import shutil
    st = Usd.Stage.Open(path); rep = {}
    rep["defaultPrim"] = str(st.GetDefaultPrim().GetPath())
    rep["upAxis"] = str(UsdGeom.GetStageUpAxis(st)); rep["metersPerUnit"] = UsdGeom.GetStageMetersPerUnit(st)
    rep["root_identity"] = UsdGeom.Xformable(st.GetPrimAtPath("/" + root_name)).GetLocalTransformation() == Gf.Matrix4d(1)
    xc = UsdGeom.XformCache(0); found = {}
    for s in sockets:
        ps = [p for p in st.Traverse() if p.GetName() == s]
        found[s] = [round(v, 3) for v in xc.GetLocalToWorldTransform(ps[0]).ExtractTranslation()] if ps else None
    rep["sockets"] = found; rep["missing_sockets"] = [s for s, v in found.items() if v is None]
    rep["skel_animations"] = len([p for p in st.Traverse() if p.IsA(UsdSkel.Animation)])
    rep["meshes"] = len([p for p in st.Traverse() if p.IsA(UsdGeom.Mesh)])
    rep["materials"] = len([p for p in st.Traverse() if p.IsA(UsdShade.Material)])
    rep["time"] = [st.GetStartTimeCode(), st.GetEndTimeCode(), st.GetTimeCodesPerSecond()]
    tex = []
    for p in st.Traverse():
        if p.GetTypeName() == "Shader":
            a = p.GetAttribute("inputs:file")
            if a and a.Get():
                tex.append(str(a.Get().path))
    rep["textures"] = sorted(set(tex))
    if animated:
        tmpb = path.replace(".usdc", "_bake.usdc"); shutil.copy(path, tmpb)
        bs = Usd.Stage.Open(tmpb); UsdSkel.BakeSkinning(bs.Traverse()); bs.GetRootLayer().Save()
        bs = Usd.Stage.Open(tmpb); ymin = 9.0; ymax = -9.0; frames = sorted(set([0, end_frame // 2, end_frame] + list(range(0, end_frame + 1, 15))))
        for f in frames:
            c = UsdGeom.XformCache(f)
            for p in bs.Traverse():
                if p.IsA(UsdGeom.Mesh):
                    M = c.GetLocalToWorldTransform(p); pts = UsdGeom.Mesh(p).GetPointsAttr().Get(f)
                    if pts is None:
                        continue
                    for i in range(0, len(pts), 7):
                        y = M.Transform(Gf.Vec3d(*pts[i]))[1]; ymin = min(ymin, y); ymax = max(ymax, y)
        rep["baked_y_range"] = [round(ymin, 3), round(ymax, 3)]
    return rep
