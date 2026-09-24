# Lax Attack painted-vinyl atlases: merge -> UV -> procedural paint detail -> Cycles bake (albedo, AO, roughness, normal) -> 1 material.
import numpy as np
ATLAS_ENABLED = True
FABRIC = ("kit_", "accent_", "glove_")
HAIRS = ("hair_",)

def _join(meshes, name):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = meshes[0]; ob.name = name; ob.data.name = name
    return ob

def _uv(ob, margin=0.004):
    for x in bpy.context.selected_objects:
        x.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    while ob.data.uv_layers:
        ob.data.uv_layers.remove(ob.data.uv_layers[0])
    ob.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=margin, area_weight=0.0, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    except Exception:
        pass
    bpy.ops.object.mode_set(mode="OBJECT")

def _detail(m):
    """Adds painted-toy variation to a flat material (only affects what gets baked)."""
    nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    if b is None or m.get("detailed"):
        return
    base = m.name.replace("M_", ""); c = tuple(b.inputs["Base Color"].default_value); r = b.inputs["Roughness"].default_value
    N = nt.nodes; L = nt.links
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 7.0; nz.inputs["Detail"].default_value = 3.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    clean = base.startswith(("skin", "blush", "eye_", "pupil", "mouth", "iris"))      # face paint + skin stay clean
    mr = N.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.985 if clean else 0.94; mr.inputs["To Max"].default_value = 1.015 if clean else 1.05
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs["Vector"])
    gr = N.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0.1; gr.inputs["From Max"].default_value = 1.5
    gr.inputs["To Min"].default_value = 0.97; gr.inputs["To Max"].default_value = 1.03; L.new(sep.outputs["Z"], gr.inputs["Value"])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(mr.outputs["Result"], mul.inputs[0]); L.new(gr.outputs["Result"], mul.inputs[1])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
    mix.inputs["A"].default_value = c
    L.new(mul.outputs["Value"], mix.inputs["B"]); L.new(mix.outputs["Result"], b.inputs["Base Color"])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 22.0; L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    rr = N.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = max(0.05, r - 0.07); rr.inputs["To Max"].default_value = min(1.0, r + 0.07)
    L.new(nz2.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], b.inputs["Roughness"])
    if base.startswith(FABRIC) or base.startswith(HAIRS):
        w1 = N.new("ShaderNodeTexWave"); w2 = N.new("ShaderNodeTexWave")
        if base.startswith(HAIRS):       # sculpted strand bands
            w1.wave_type = "BANDS"; w1.bands_direction = "Z"; w1.inputs["Scale"].default_value = 18.0; w1.inputs["Distortion"].default_value = 4.0
            L.new(tc.outputs["Object"], w1.inputs["Vector"]); h = w1.outputs["Fac"]; strength = 0.35
        else:                            # fabric weave
            for w, d in ((w1, "X"), (w2, "Y")):
                w.wave_type = "BANDS"; w.bands_direction = d; w.inputs["Scale"].default_value = 160.0; L.new(tc.outputs["Object"], w.inputs["Vector"])
            hm = N.new("ShaderNodeMath"); hm.operation = "MULTIPLY"; L.new(w1.outputs["Fac"], hm.inputs[0]); L.new(w2.outputs["Fac"], hm.inputs[1])
            h = hm.outputs["Value"]; strength = 0.18
        bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = strength; bump.inputs["Distance"].default_value = 0.002
        L.new(h, bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
    m["detailed"] = True

def _bake(ob, kind, img, samples=1):
    for m in ob.data.materials:
        nt = m.node_tree; t = nt.nodes.get("_bake_target") or nt.nodes.new("ShaderNodeTexImage")
        t.name = "_bake_target"; t.image = img; nt.nodes.active = t
    sc = bpy.context.scene; sc.cycles.samples = samples
    for x in bpy.context.selected_objects:
        x.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    kw = dict(type=kind, margin=6, use_clear=True)
    if kind == "DIFFUSE":
        kw["pass_filter"] = {"COLOR"}
    if kind == "NORMAL":
        kw["normal_space"] = "TANGENT"
    bpy.ops.object.bake(**kw)

def atlas_character(arm, meshes, asset, out_dir, res=2048):
    """Merge + unwrap + bake. Returns [merged_mesh] carrying one atlas material (base colour, roughness, normal)."""
    if not ATLAS_ENABLED:
        return meshes
    arm.data.pose_position = "REST"; bpy.context.view_layer.update()
    ob = _join(meshes, asset + "_body"); _uv(ob)
    for m in ob.data.materials:
        _detail(m)
    sc = bpy.context.scene; eng = sc.render.engine; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    tdir = os.path.join(out_dir, "Textures"); os.makedirs(tdir, exist_ok=True)
    imgs = {}
    for k, cs in (("albedo", "sRGB"), ("ao", "Non-Color"), ("rough", "Non-Color"), ("normal", "Non-Color")):
        im = bpy.data.images.new(asset + "_" + k, res, res, alpha=False, float_buffer=False); im.colorspace_settings.name = cs; imgs[k] = im
    _bake(ob, "DIFFUSE", imgs["albedo"]); _bake(ob, "AO", imgs["ao"], 40); _bake(ob, "ROUGHNESS", imgs["rough"]); _bake(ob, "NORMAL", imgs["normal"])
    mask = bpy.data.images.new(asset + "_mask", res, res, alpha=False); mask.colorspace_settings.name = "Non-Color"
    saved = {}
    for m in ob.data.materials:                         # emission mask: 1 where the normal map carries real detail
        b = m.node_tree.nodes.get("Principled BSDF"); base = m.name.replace("M_", "")
        on = 1.0 if base.startswith(FABRIC) or base.startswith(HAIRS) else 0.0
        saved[m] = (tuple(b.inputs["Emission Color"].default_value), b.inputs["Emission Strength"].default_value)
        b.inputs["Emission Color"].default_value = (on, on, on, 1); b.inputs["Emission Strength"].default_value = 1.0
    _bake(ob, "EMIT", mask)
    for m, (c_, s_) in saved.items():
        b = m.node_tree.nodes.get("Principled BSDF"); b.inputs["Emission Color"].default_value = c_; b.inputs["Emission Strength"].default_value = s_
    mk = np.array(mask.pixels[:], np.float32).reshape(res, res, 4)[..., :1]
    nn = np.array(imgs["normal"].pixels[:], np.float32).reshape(res, res, 4)
    nn[..., :3] = nn[..., :3] * mk + np.array([0.5, 0.5, 1.0], np.float32) * (1 - mk)
    imgs["normal"].pixels = nn.ravel(); bpy.data.images.remove(mask)
    sc.render.engine = eng
    a = np.array(imgs["albedo"].pixels[:], np.float32).reshape(res, res, 4); ao = np.array(imgs["ao"].pixels[:], np.float32).reshape(res, res, 4)
    o = ao[..., 0]
    for ax in (0, 1):                                   # separable blur (denoise), radius ~4 px
        o = sum(np.roll(o, s, axis=ax) * w for s, w in zip(range(-4, 5), (1, 2, 4, 6, 8, 6, 4, 2, 1))) / 34.0
    o = np.clip((o - 0.35) / 0.65, 0.0, 1.0)            # interpenetrating toy segments never go black
    a[..., :3] *= (0.87 + 0.13 * o)[..., None]          # gentle baked contact shading in creases (colour stays saturated)
    imgs["albedo"].pixels = a.ravel()
    paths = {}
    sc.render.image_settings.quality = 90
    for k, ext, fmt in (("albedo", "jpg", "JPEG"), ("rough", "jpg", "JPEG"), ("normal", "png", "PNG")):   # mobile-sized atlas files
        im = imgs[k]
        if k == "normal" and res > 1024:
            im.scale(1024, 1024)
        for old in (os.path.join(tdir, "%s_%s.png" % (asset, k)), os.path.join(tdir, "%s_%s.jpg" % (asset, k))):
            if os.path.exists(old):
                os.remove(old)
        p = os.path.join(tdir, "%s_%s.%s" % (asset, k, ext)); im.filepath_raw = p; im.file_format = fmt; im.save(); paths[k] = p
    bpy.data.images.remove(imgs["ao"])
    am = bpy.data.materials.new("M_" + asset + "_atlas"); am.use_nodes = True; nt = am.node_tree; b = nt.nodes.get("Principled BSDF")
    ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = bpy.data.images.load(paths["albedo"]); nt.links.new(ta.outputs["Color"], b.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = bpy.data.images.load(paths["rough"]); tr.image.colorspace_settings.name = "Non-Color"
    sepc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tr.outputs["Color"], sepc.inputs["Color"]); nt.links.new(sepc.outputs["Red"], b.inputs["Roughness"])
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(paths["normal"]); tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    for k_ in ("Coat Weight", "Coat"):
        if k_ in b.inputs:
            b.inputs[k_].default_value = 0.12; break
    ob.data.materials.clear(); ob.data.materials.append(am)
    for p_ in ob.data.polygons:
        p_.material_index = 0
    arm.data.pose_position = "POSE"; bpy.context.view_layer.update()
    return [ob]
