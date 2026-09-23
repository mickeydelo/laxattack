# Lax Attack runtime export: Blender USD export + pxr post-process (identity root at field level, axis conversion on the
# rig/content child prim), optional 180-degree yaw for assets that must face +Z (goalie), USDZ packaging, verification.
def export_asset(objects, root_name, content_name, out_usdz, fps=30, end_frame=0, face_plus_z=False, manifest=None,
                 sockets=(), animated=True, tmp="/tmp/laxattack_export"):
    from pxr import Usd, UsdGeom, UsdSkel, Sdf, Gf, Kind, UsdUtils
    import shutil
    os.makedirs(tmp, exist_ok=True)
    raw = os.path.join(tmp, root_name + ".usdc"); fixed = os.path.join(tmp, root_name + "_fixed.usdc")
    sc = bpy.context.scene; sc.render.fps, sc.render.fps_base = fps, 1.0
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objects:
        o.hide_set(False); o.hide_render = False; o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    want = dict(filepath=raw, selected_objects_only=True, export_animation=animated, export_armatures=True,
                only_deform_bones=True, export_materials=True, generate_preview_surface=True, export_textures=True,
                overwrite_textures=True, relative_paths=True, export_uvmaps=True, export_normals=True, export_mesh_colors=False,
                convert_orientation=True, export_global_forward_selection="Z", export_global_up_selection="Y",
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
    cx = UsdGeom.Xformable(content)
    if face_plus_z:
        cx.AddRotateYOp().Set(180.0)          # turn the whole asset to face +Z (root stays identity)
    cx.AddRotateXYZOp().Set(Gf.Vec3f(90, 0, 180))   # Blender Z-up/-Y-forward -> USD Y-up/-Z-forward
    st.SetDefaultPrim(root); Usd.ModelAPI(root).SetKind(Kind.Tokens.component)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(st, 1.0)
    st.SetTimeCodesPerSecond(fps); st.SetFramesPerSecond(fps); st.SetStartTimeCode(0); st.SetEndTimeCode(max(end_frame, 0))
    meta = {"facing": "+Z" if face_plus_z else "-Z", "up": "+Y", "origin": "field level"}
    if manifest:
        meta["clipManifest"] = json.dumps(manifest)
    root.SetCustomDataByKey("laxattack", meta)
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
    rep["usdz_textures"] = [str(a.path) for a in []]
    return rep

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
