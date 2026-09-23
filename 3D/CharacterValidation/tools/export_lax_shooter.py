# Lax Attack - lax_shooter USD/USDZ export (run inside Blender 5.2 with LaxAttackCharacters.blend open)
# 1) Blender USD export (Y-up, forward Z) of the lax_shooter collection
# 2) pxr post-process: identity asset root /lax_shooter at field level, axis conversion moved to the rig prim,
#    defaultPrim/kind/clip manifest metadata
# 3) USDZ package + JSON clip manifest
import bpy, os, json, shutil
from pxr import Usd, UsdGeom, UsdSkel, Sdf, Gf, Kind, UsdUtils

REPO = os.path.expanduser("~/Developer/laxattack")
OUT = os.path.join(REPO, "3D", "CharacterValidation")
TMP = "/tmp/laxattack_export"
os.makedirs(TMP, exist_ok=True)
RAW = os.path.join(TMP, "lax_shooter.usdc")
FIXED = os.path.join(TMP, "lax_shooter_fixed.usdc")
USDZ = os.path.join(OUT, "lax_shooter.usdz")
FPS = 30
CLIPS = {  # name: (start, end) on the shared timeline, inclusive
    "idle": (0, 48, True), "cradle": (60, 88, True),
    "release_overhand": (100, 133, False), "celebrate": (150, 186, False)}
RELEASE_FRAME = 114

scene = bpy.context.scene
scene.frame_start, scene.frame_end = 0, 186
scene.render.fps, scene.render.fps_base = FPS, 1.0
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.collections["lax_shooter"].objects:
    o.hide_set(False); o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["lax_shooter_rig"]

want = dict(filepath=RAW, selected_objects_only=True, export_animation=True, export_armatures=True,
            only_deform_bones=True, export_materials=True, generate_preview_surface=True,
            export_uvmaps=True, export_normals=True, export_mesh_colors=False,
            convert_orientation=True, export_global_forward_selection="Z", export_global_up_selection="Y",
            export_lights=False, export_cameras=False, export_shapekeys=False,
            author_blender_name=False, export_custom_properties=False,
            root_prim_path="/lax_shooter", evaluation_mode="RENDER")
props = {p.identifier for p in bpy.ops.wm.usd_export.get_rna_type().properties}
args = {k: v for k, v in want.items() if k in props}
skipped = sorted(set(want) - set(args))
bpy.ops.wm.usd_export(**args)

# ---------------------------------------------------------------- post-process
stage = Usd.Stage.Open(RAW)
root = stage.GetPrimAtPath("/lax_shooter")
rig = stage.GetPrimAtPath("/lax_shooter/lax_shooter_rig")
assert root and rig, "unexpected hierarchy"
rx = UsdGeom.Xformable(root)
rx.ClearXformOpOrder()
for a in list(root.GetAttributes()):
    if a.GetName().startswith("xformOp:"):
        root.RemoveProperty(a.GetName())
gx = UsdGeom.Xformable(rig)
gx.ClearXformOpOrder()
for a in list(rig.GetAttributes()):
    if a.GetName().startswith("xformOp:"):
        rig.RemoveProperty(a.GetName())
gx.AddRotateXYZOp().Set(Gf.Vec3f(90, 0, 180))  # Blender Z-up/-Y-forward -> USD Y-up/-Z-forward
stage.SetDefaultPrim(root)
Usd.ModelAPI(root).SetKind(Kind.Tokens.component)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
stage.SetTimeCodesPerSecond(FPS); stage.SetFramesPerSecond(FPS)
stage.SetStartTimeCode(0); stage.SetEndTimeCode(186)
manifest = {"fps": FPS, "release_overhand_ball_release_frame": RELEASE_FRAME,
            "clips": {n: {"start": s, "end": e, "loop": lp} for n, (s, e, lp) in CLIPS.items()}}
root.SetCustomDataByKey("laxattack", {"clipManifest": json.dumps(manifest), "facing": "-Z", "up": "+Y",
                                      "origin": "field level between feet"})
stage.GetRootLayer().Export(FIXED)

# ---------------------------------------------------------------- verify
st = Usd.Stage.Open(FIXED)
rep = {"export_args_skipped": skipped}
rep["defaultPrim"] = str(st.GetDefaultPrim().GetPath())
rep["upAxis"] = UsdGeom.GetStageUpAxis(st); rep["metersPerUnit"] = UsdGeom.GetStageMetersPerUnit(st)
rep["root_local_xform_identity"] = UsdGeom.Xformable(st.GetPrimAtPath("/lax_shooter")).GetLocalTransformation() == Gf.Matrix4d(1)
rep["prims"] = [str(p.GetPath()) for p in st.Traverse()][:60]
cache = UsdGeom.XformCache(0)
for s in ("stick_socket", "helmet_socket", "effect_socket", "pocket_socket"):
    found = [p for p in st.Traverse() if p.GetName() == s]
    if found:
        m = cache.GetLocalToWorldTransform(found[0])
        rep[s] = {"path": str(found[0].GetPath()), "pos": [round(v, 3) for v in m.ExtractTranslation()]}
    else:
        rep[s] = None
anims = [p for p in st.Traverse() if p.IsA(UsdSkel.Animation)]
rep["skel_animations"] = [str(p.GetPath()) for p in anims]
checks = {}
try:
    tmp_bake = os.path.join(TMP, "bake_check.usdc")
    shutil.copy(FIXED, tmp_bake)
    bs = Usd.Stage.Open(tmp_bake)
    UsdSkel.BakeSkinning(bs.Traverse())
    bs.GetRootLayer().Save()
    bs = Usd.Stage.Open(tmp_bake)
    for f in (0, 67, 114, 162):
        xc = UsdGeom.XformCache(f)
        info = {}
        for name in ("lax_shooter_body", "lax_shooter_stick"):
            ps = [p for p in bs.Traverse() if p.GetName() == name and p.IsA(UsdGeom.Mesh)]
            if not ps: continue
            m = UsdGeom.Mesh(ps[0]); M = xc.GetLocalToWorldTransform(ps[0])
            pts = [M.Transform(Gf.Vec3d(*v)) for v in m.GetPointsAttr().Get(f)]
            ys = [v[1] for v in pts]; xs = [v[0] for v in pts]; zs = [v[2] for v in pts]
            info[name] = {"y_min": round(min(ys), 3), "y_max": round(max(ys), 3), "x_mean": round(sum(xs)/len(xs), 3),
                          "z_min": round(min(zs), 3), "z_max": round(max(zs), 3)}
            if name == "lax_shooter_body":
                low = [v for v in pts if v[1] < 0.03]
                info["toe_z_min"] = round(min(v[2] for v in low), 3) if low else None
                info["heel_z_max"] = round(max(v[2] for v in low), 3) if low else None
        checks[f] = info
except Exception as ex:
    checks["error"] = repr(ex)
rep["baked_checks"] = checks

# ---------------------------------------------------------------- package
if os.path.exists(USDZ):
    os.remove(USDZ)
ok = False
try:
    ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(FIXED), USDZ)
    rep["packager"] = "CreateNewARKitUsdzPackage"
except Exception as ex:
    rep["arkit_err"] = repr(ex)
if not ok or not os.path.exists(USDZ):
    ok = UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(FIXED), USDZ)
    rep["packager"] = "CreateNewUsdzPackage"
rep["usdz_ok"] = bool(ok) and os.path.exists(USDZ)
rep["usdz_bytes"] = os.path.getsize(USDZ) if os.path.exists(USDZ) else 0
z = Usd.Stage.Open(USDZ)
rep["usdz_defaultPrim"] = str(z.GetDefaultPrim().GetPath()) if z.GetDefaultPrim() else None
rep["usdz_time"] = [z.GetStartTimeCode(), z.GetEndTimeCode(), z.GetTimeCodesPerSecond()]
with open(os.path.join(OUT, "lax_shooter_clips.json"), "w") as fh:
    json.dump(manifest, fh, indent=2)
REPORT = rep
