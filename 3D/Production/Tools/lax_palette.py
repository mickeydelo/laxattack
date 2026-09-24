# Palette atlas: collapse flat-colour materials into one shared material (colour + roughness swatches). Big draw-call saving.
import numpy as np
PAL_N = 16          # 16 x 16 swatches, 8 px each -> 128 px textures (nearest-safe: UVs sit at swatch centres)

def palette_materials(meshes, name, out_dir, keep=("turf_field", "turf_tex", "turf_tex_mow", "sky_grad")):
    mats = []
    for o in meshes:
        for m in o.data.materials:
            if m and m.name.replace("M_", "") not in keep and m not in mats:
                mats.append(m)
    if not mats:
        return {}
    px = 8; res = PAL_N * px
    col = np.ones((res, res, 4), np.float32); rough = np.ones((res, res, 4), np.float32)
    slot = {}
    for i, m in enumerate(mats[:PAL_N * PAL_N]):
        b = m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
        c = tuple(b.inputs["Base Color"].default_value) if b else (0.8, 0.8, 0.8, 1); r = b.inputs["Roughness"].default_value if b else 0.6
        gx, gy = i % PAL_N, i // PAL_N
        col[gy * px:(gy + 1) * px, gx * px:(gx + 1) * px, :3] = c[:3]; rough[gy * px:(gy + 1) * px, gx * px:(gx + 1) * px, :3] = r
        slot[m.name] = ((gx + 0.5) / PAL_N, (gy + 0.5) / PAL_N)
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for k, arr, cs in (("color", col, "sRGB"), ("rough", rough, "Non-Color")):
        im = bpy.data.images.new("%s_palette_%s" % (name, k), res, res, alpha=False, float_buffer=False); im.colorspace_settings.name = cs
        if k == "color":                                  # shader colours are linear; an sRGB byte texture needs encoded values
            arr = arr.copy(); lin = arr[..., :3]
            arr[..., :3] = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0, 1), 1 / 2.4) - 0.055)
        im.pixels = arr.ravel(); p = os.path.join(out_dir, "%s_palette_%s.png" % (name, k)); im.filepath_raw = p; im.file_format = "PNG"; im.save(); paths[k] = p
    pm = bpy.data.materials.new("M_%s_palette" % name); pm.use_nodes = True; nt = pm.node_tree; b = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexImage"); tc.image = bpy.data.images.load(paths["color"]); tc.interpolation = "Closest"
    nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
    tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = bpy.data.images.load(paths["rough"]); tr.image.colorspace_settings.name = "Non-Color"; tr.interpolation = "Closest"
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(tr.outputs["Color"], sep.inputs["Color"]); nt.links.new(sep.outputs["Red"], b.inputs["Roughness"])
    for o in meshes:
        me = o.data; names = [m.name if m else "" for m in me.materials]
        if not any(n in slot for n in names):
            continue
        uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
        keep_idx = {}
        for pi, poly in enumerate(me.polygons):
            n = names[poly.material_index] if poly.material_index < len(names) else ""
            if n in slot:
                u, v = slot[n]
                for li in poly.loop_indices:
                    uv.data[li].uv = (u, v)
        # rebuild slots: palette first, keep textured slots after it
        kept = [m for m in me.materials if m and m.name not in slot]
        remap = {}
        for pi, poly in enumerate(me.polygons):
            n = names[poly.material_index] if poly.material_index < len(names) else ""
            remap[pi] = 0 if n in slot else 1 + [k.name for k in kept].index(n)
        me.materials.clear(); me.materials.append(pm)
        for k in kept:
            me.materials.append(k)
        for pi, poly in enumerate(me.polygons):
            poly.material_index = remap[pi]
    return {"palette_materials": len(slot), "files": paths}
