# Lax Attack: Pinebrook arena v3 (grass recipe, DOF fallback layers, LODs, groups, camera markers).
import numpy as np
FX0, FX1, FY0, FY1 = -6.9, 6.9, -12.9, 5.9      # field top (Blender XY)

def _srgb(a):
    a = np.clip(a, 0, 1); return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)

def _save(path, rgb, lin=True):
    h, w = rgb.shape[:2]
    img = np.concatenate([_srgb(rgb) if lin else np.clip(rgb, 0, 1), np.ones((h, w, 1), np.float32)], -1)
    im = bpy.data.images.new(os.path.basename(path), w, h, alpha=False); im.pixels = img.astype(np.float32).ravel()
    im.filepath_raw = path; im.file_format = "JPEG" if path.endswith(".jpg") else "PNG"
    if path.endswith(".jpg"):
        bpy.context.scene.render.image_settings.quality = 88
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(); bpy.data.images.remove(im)

def make_field_textures(tdir, n=2048, seed=7):
    """Unique field PBR set: albedo (mow bands, macro variation, worn crease / goal mouth / shooting spot), normal, roughness."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32)
    X = FX0 + (xs + 0.5) / n * (FX1 - FX0); Y = FY0 + (ys + 0.5) / n * (FY1 - FY0)   # pixel -> field metres (v up = +Y)
    def smooth_noise(cells):
        g = rng.random((cells + 1, cells + 1)).astype(np.float32)
        u = xs / n * cells; v = ys / n * cells; i0 = u.astype(int); j0 = v.astype(int); fu = u - i0; fv = v - j0
        fu = fu * fu * (3 - 2 * fu); fv = fv * fv * (3 - 2 * fv)
        return (g[j0, i0] * (1 - fu) * (1 - fv) + g[j0, i0 + 1] * fu * (1 - fv) + g[j0 + 1, i0] * (1 - fu) * fv + g[j0 + 1, i0 + 1] * fu * fv)
    macro = 0.55 * smooth_noise(6) + 0.3 * smooth_noise(18) + 0.15 * smooth_noise(60)
    blade = rng.random((n, n)).astype(np.float32)
    k = 9; streak = np.zeros_like(blade)
    for s in range(k):                                  # vertical smear -> blade streaks
        streak += np.roll(blade, s, axis=0) * (1 - s / k)
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    clump = smooth_noise(220)
    mow = np.where((np.floor((Y - FY0) / 1.6) % 2) == 0, 1.0, 0.86).astype(np.float32)
    d_crease = np.abs(np.hypot(X, Y + 5.7) - 2.2)
    worn = np.clip(1 - d_crease / 0.35, 0, 1) * 0.55
    worn = np.maximum(worn, np.clip(1 - np.hypot(X / 1.1, (Y + 5.35) / 0.7), 0, 1) * 0.95)       # goal mouth
    worn = np.maximum(worn, np.clip(1 - np.hypot(X - 0.72, Y - 1.72) / 0.7, 0, 1) * 0.6)          # shooting spot
    worn = np.clip(worn * 1.35 * (0.7 + 0.6 * clump), 0, 1)
    lane = np.clip(1 - np.abs(X) / 1.4, 0, 1) * 0.06                                              # brighter maintained lane
    ax, ay, bx, by = 0.72, 1.72, 0.0, -3.4                                                        # flattened traffic path shooter -> crease
    tt = np.clip(((X - ax) * (bx - ax) + (Y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
    dpath = np.hypot(X - (ax + tt * (bx - ax)), Y - (ay + tt * (by - ay)))
    trafficm = np.clip(1 - dpath / 0.5, 0, 1) * (0.6 + 0.4 * clump)
    streak = streak * (1 - 0.55 * trafficm)
    lane = lane + 0.05 * trafficm
    lum = (0.80 + 0.30 * (macro - 0.5) + 0.12 * streak * 0.5 + 0.10 * (clump - 0.5) + lane) * mow
    grass = np.stack([0.12 * lum * (1 + 0.3 * (macro - 0.5)), 0.40 * lum, 0.065 * lum * (1 - 0.3 * (macro - 0.5))], -1)
    dirt = np.stack([0.30 + 0.05 * streak * 0.2, 0.22 + 0.03 * streak * 0.2, 0.12 + 0.02 * streak * 0.2], -1) * (0.9 + 0.2 * clump[..., None])
    w = np.clip(worn * (0.8 + 0.4 * (streak * 0.15 + 0.5)), 0, 1)[..., None]
    alb = grass * (1 - w) + (grass * 0.35 + dirt * 0.65) * w
    alb *= (0.88 + 0.12 * clump[..., None])            # baked micro AO
    h = 0.6 * streak * 0.2 + 0.4 * (clump - 0.5) - 0.8 * w[..., 0]
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 2.0; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 2.0
    nz = np.ones_like(h); L = np.sqrt(gx * gx + gy * gy + 1)
    nrm = np.stack([(-gx / L) * 0.5 + 0.5, (-gy / L) * 0.5 + 0.5, (nz / L) * 0.5 + 0.5], -1)
    rough = np.repeat((0.86 + 0.06 * w[..., 0] - 0.04 * (streak * 0.1)).clip(0.75, 0.97)[..., None], 3, -1)
    paths = [os.path.join(tdir, f) for f in ("field_albedo.jpg", "field_normal.png", "field_roughness.jpg")]
    _save(paths[0], alb); _save(paths[1], nrm, lin=False); _save(paths[2], rough, lin=False)
    return paths

def field_top(collection, mat_name):
    nx, ny = 56, 76; verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = FX0 + (FX1 - FX0) * i / nx; y = FY0 + (FY1 - FY0) * j / ny
            crown = 0.035 * (1 - ((x / FX1) ** 2)) * (1 - (((y + 3.5) / 9.4) ** 2))   # gently crowned
            verts.append((x, y, max(0.0, crown) * 0.0 + 0.001))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    B = Builder("field_turf"); B.add((verts, faces), mat_name, smooth=False)
    ob = B.build(collection)
    uv = ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            co = ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x - FX0) / (FX1 - FX0), (co.y - FY0) / (FY1 - FY0))
    return ob

def hero_tufts(collection, seed=3):
    """Sparse modeled tufts: crease edge, shooter area, camera foreground; ball corridor (|x|<0.9 between shooter and goal) kept clear."""
    rnd = random.Random(seed); B = Builder("hero_tufts"); pts = []
    for i in range(44):          # hero tufts only near camera_gameplay (bottom of frame + side edges)
        y = rnd.uniform(2.3, 5.4); spread = 0.9 + (y - 2.3) * 0.55
        x = rnd.uniform(-spread, spread)
        if abs(x) < 0.55 and y < 3.0:
            continue
        pts.append((x, y))
    for (x, y) in pts:
        if abs(x) < 0.9 and -5.0 < y < 1.0:
            continue
        s = rnd.uniform(0.10, 0.32); cm = rnd.choice(("leaf_a", "leaf_b", "leaf_b", "grass_dry"))
        for k in range(9):   # fuller, softer clumps with varied scale / lean / colour
            a = rnd.uniform(0, 6.28); lean = rnd.uniform(0.1, 0.4)
            tip = (x + math.cos(a) * lean * s, y + math.sin(a) * lean * s, s * rnd.uniform(0.7, 1.15))
            B.add(sweep([(x, y, 0), (x + (tip[0] - x) * 0.4, y + (tip[1] - y) * 0.4, tip[2] * 0.55), tip], [s * 0.13, s * 0.08, 0.004], 4, 0.5),
                  cm if k % 3 else "leaf_a")
    return B.build(collection)

def haze_material(m, haze=(0.80, 0.84, 0.88), t=0.45, rough=0.95):
    base = m.replace("M_", ""); name = base + "_soft"
    if name not in MATS and base in MATS:
        rgb, r0, me, co = MATS[base]
        MATS[name] = (tuple(c + (h - c) * t for c, h in zip(rgb, haze)), rough, 0.0, 0.0)
    return name if name in MATS else base

def soft_copy(o, group, t, haze):
    c = o.copy(); c.data = o.data.copy(); c.name = o.name + "_soft"; group.users_collection[0].objects.link(c)
    mw = o.matrix_world.copy(); c.parent = group; c.matrix_world = mw
    for i, slot in enumerate(c.data.materials):
        if slot:
            c.data.materials[i] = mat(haze_material(slot.name, haze, t))
    sm = c.modifiers.new("soften", "SMOOTH"); sm.factor = 0.8; sm.iterations = 6
    bpy.context.view_layer.objects.active = c; bpy.ops.object.modifier_apply(modifier="soften")
    return c

def sky_backdrop(collection):
    n = 256; ys = np.linspace(0, 1, n)[:, None, None]
    top = np.array([0.22, 0.46, 0.95]); mid = np.array([0.52, 0.68, 0.93]); hor = np.array([1.0, 0.86, 0.66])
    col = np.where(ys < 0.35, hor + (mid - hor) * (ys / 0.35), mid + (top - mid) * ((ys - 0.35) / 0.65))
    img = np.repeat(col, 4, axis=1).astype(np.float32)
    p = os.path.join(PROD, "Arena", "Textures", "sky_gradient.png"); _save(p, img)
    TEX_MATS["sky_grad"] = (p, 1.0)
    verts, faces = [], []
    R_, H_ = 170.0, 70.0; seg = 24
    for k in range(seg + 1):
        a = math.radians(-80 + 160 * k / seg)
        for z in (-2.0, H_):
            verts.append((math.sin(a) * R_, -math.cos(a) * R_ - 10, z))
    for k in range(seg):
        a = 2 * k; faces.append((a, a + 2, a + 3, a + 1))
    B = Builder("sky_backdrop"); B.add((verts, faces), "sky_grad", smooth=True); ob = B.build(collection)
    uv = ob.data.uv_layers.new(name="UVMap")
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            vi = ob.data.loops[li].vertex_index; uv.data[li].uv = ((vi // 2) / seg, (vi % 2) * 0.999)
    return ob

def flower_clump(seed, s=1.4):
    rnd = random.Random(seed); out = []
    cols = ("kit_white", "accent_gold", "petal_pink", "petal_lilac", "accent_coral")
    for k in range(rnd.randint(5, 9)):
        x, y = rnd.uniform(-0.22, 0.22) * s, rnd.uniform(-0.12, 0.12) * s; h = rnd.uniform(0.10, 0.20) * s
        out.append((sweep([(x, y, 0), (x + rnd.uniform(-0.02, 0.02), y, h)], [0.006 * s, 0.004 * s], 5, 1.0), "leaf_b"))
        out.append((ellipsoid((x + 0.03 * s, y, h * 0.4), (0.03 * s, 0.012 * s, 0.006 * s), 8, 4), "leaf_a"))
        col = rnd.choice(cols); c = V((x, y, h))
        for pi_ in range(5):
            a = 2 * math.pi * pi_ / 5 + rnd.uniform(0, 0.3)
            out.append((ellipsoid(tuple(c + V((math.cos(a) * 0.022 * s, math.sin(a) * 0.022 * s, 0))), (0.02 * s, 0.02 * s, 0.006 * s), 8, 4), col))
        out.append((ellipsoid(tuple(c + V((0, 0, 0.004 * s))), (0.011 * s, 0.011 * s, 0.008 * s), 8, 5), "accent_gold" if col != "accent_gold" else "accent_coral"))
    return out

def flower_beds(Dio):
    """Toy flower clumps: along the fence base, by the bench and signs, and soft foreground clumps near the camera corners."""
    MATS.setdefault("petal_pink", ((0.95, 0.45, 0.62), 0.6, 0.0, 0.0)); MATS.setdefault("petal_lilac", ((0.62, 0.50, 0.92), 0.6, 0.0, 0.0))
    spots = [(x, -12.25 + 0.12 * ((i * 7) % 3 - 1)) for i, x in enumerate((-6.2, -5.1, -4.0, -2.9, -1.7, 1.8, 3.0, 4.1, 5.2, 6.3))]
    spots += [(-6.0, -2.6), (-6.0, -0.4), (6.0, -2.6), (6.0, -0.4), (-4.6, -11.9), (4.6, -11.9)]
    out = []
    for i, (x, y) in enumerate(spots):
        B = Builder("flowers_%02d" % i)
        for g, m in flower_clump(200 + i):
            B.add(g, m)
        o = B.build(Dio); o.location = (x, y, 0.0); out.append(o)
    for i, (x, y, s) in enumerate(((1.55, 3.05, 2.2), (-1.35, 3.25, 2.0), (1.1, 3.6, 1.8))):
        B = Builder("flowers_fg_%02d" % i)
        for g, m in flower_clump(300 + i, s):
            B.add(g, m)
        o = B.build(Dio); o.location = (x, y, 0.0); out.append(o)
    return out

def build_arena(export=True):
    tdir = os.path.join(PROD, "Arena", "Textures")
    fa, fn, fr = make_field_textures(tdir)
    MATS["grass_dry"] = ((0.40, 0.38, 0.10), 0.85, 0.0, 0.0)
    build_scene()
    TEX_MATS["turf_field"] = (fa, 0.88, fn, fr)
    for o in [o for o in bpy.data.objects if o.type in ("ARMATURE", "CAMERA", "LIGHT") or (o.parent and o.parent.type == "ARMATURE")
              or o.name == "dof_focus" or o.name.startswith(("goal_", "tree_", "pine_", "bush_6", "sailboat", "cloud_"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    Dio = bpy.data.collections["Diorama"]
    twins = make_twins(Dio)                                        # static twins of lax_arena_ambient (identical rest placement)
    flower_beds(Dio)
    if globals().get("ARENA_V9"):
        build_env_v9_export(Dio)
    bleacher(Dio, (5.2, -14.4, -0.45), 3.4, 3); bench(Dio, (6.0, -1.5, 0), 2.2, math.radians(-90))
    plat = bpy.data.objects["field_platform"]                   # keep the soil skirt only: drop old flat-colour turf faces
    me = plat.data
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(me)
    kill = [f for f in bm.faces if me.materials[f.material_index].name in ("M_turf_tex", "M_turf_tex_mow", "M_turf_a", "M_turf_b")]
    _bm.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free()
    field_top(Dio, "turf_field")
    hero_tufts(Dio)
    sky_backdrop(Dio)
    bpy.context.view_layer.update()
    root = bpy.data.objects.new("lax_arena_content", None); Dio.objects.link(root)
    groups = {}
    for g in ("gameplay", "near_field", "midground", "ambient_twins", "far_background", "far_background_soft", "foreground_framing",
              "foreground_framing_soft", "shadow_only", "collision_only", "camera_markers"):
        e = bpy.data.objects.new(g, None); Dio.objects.link(e); e.parent = root; groups[g] = e
    fg = {o.name for o in bpy.data.collections["Foreground"].objects}
    def group_of(n):
        if n.startswith(("v9_pine_forest", "v9_rock_stacks", "v9_lake", "v9_clouds", "v9_boat")): return "far_background"
        if n.startswith(("v9_tree", "v9_shore_tree", "v9_shore_bushes")): return "midground"
        if n.startswith(("v9_fence", "v9_field_tufts", "v9_carpet_tufts")): return "near_field"
        if n.startswith("v9_foreground_bushes"): return "foreground_framing"
        if n in fg: return "foreground_framing"
        if n.startswith(("field_platform", "field_markings", "field_turf", "hero_tufts")): return "gameplay"
        if n.startswith("twin_"): return "ambient_twins"   # static twins of lax_arena_ambient: hide when ambient is shown
        if n.startswith("flowers_fg"): return "foreground_framing"
        if n.startswith("flowers"): return "near_field"
        if n.startswith(("field_fence", "bench", "bleacher", "sign_", "banner")): return "near_field"
        if n.startswith(("far_shore", "mountains", "cloud_", "sky_backdrop")): return "far_background"
        return "midground"
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = groups[group_of(o.name)]; o.matrix_world = mw
    bpy.context.view_layer.update()
    soft = []
    for o in meshes:
        g = group_of(o.name)
        if g == "far_background" and not o.name.startswith("sky_"):
            soft.append(soft_copy(o, groups["far_background_soft"], 0.55, (0.72, 0.80, 0.90)))
        elif g == "foreground_framing":
            soft.append(soft_copy(o, groups["foreground_framing_soft"], 0.25, (0.55, 0.62, 0.45)))
    meshes += soft
    col = obj_from_geo("collision_ground", superellipsoid((14, 19, 0.1), 0.05, 0.05, 8, 4, (0, -3.5, -0.05)), "clay", Dio)
    col.parent = groups["collision_only"]; meshes.append(col)
    cams = {"camera_gameplay": ((0.3, 7.0, 4.3), (0.15, -3.5, 0.4)), "camera_aim": ((0.6, 4.2, 2.2), (0.4, -3.0, 0.9)),
            "camera_release": ((0.9, 3.6, 1.8), (0.0, -5.7, 1.0)), "camera_goal_left": ((2.4, -2.0, 1.6), (0.5, -5.7, 1.0)),
            "camera_goal_right": ((-2.4, -2.0, 1.6), (-0.5, -5.7, 1.0)), "camera_save_left": ((1.6, -1.8, 1.3), (0.0, -5.0, 0.9)),
            "camera_save_right": ((-1.6, -1.8, 1.3), (0.0, -5.0, 0.9)), "camera_celebration": ((-0.6, -0.8, 1.4), (0.72, 1.72, 0.9)),
            "camera_results": ((0.0, 9.0, 6.0), (0.0, -4.0, 0.5))}
    marks = []
    for n, (loc, tgt) in cams.items():
        c = bpy.data.objects.new(n, None); Dio.objects.link(c); c.parent = groups["camera_markers"]
        c.matrix_world = Matrix.Translation(loc) @ (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_matrix().to_4x4()
        t = bpy.data.objects.new(n + "_target", None); Dio.objects.link(t); t.parent = groups["camera_markers"]; t.matrix_world = Matrix.Translation(tgt)
        marks += [c, t]
    refs = {"gameplay_focus_center": (0.36, -1.99, 0.9), "foreground_focus_reference": (0.0, 3.0, 0.4), "far_background_focus_reference": (0.0, -31.0, 1.0)}
    for n, loc in refs.items():
        e = bpy.data.objects.new(n, None); Dio.objects.link(e); e.parent = groups["camera_markers"]; e.matrix_world = Matrix.Translation(loc); marks.append(e)
    seat_group = bpy.data.objects.new("crowd_markers", None); Dio.objects.link(seat_group); seat_group.parent = root; groups["crowd_markers"] = seat_group
    seats = []
    for side, bx in (("home", -5.2), ("away", 5.2)):          # home = game +X side, away = game -X side
        n = 0
        for row in range(3):
            for dx in (-0.8, 0.8):
                n += 1; seats.append(("bleacher_%s_seat_%02d" % (side, n), (bx + dx, -14.4 + row * 0.45, -0.45 + 0.42 + row * 0.36 + 0.04), math.pi))
    for side, bx, yaw in (("home", -6.0, math.radians(90)), ("away", 6.0, math.radians(-90))):
        for k, dy in enumerate((-0.7, 0.0, 0.7)):
            seats.append(("sideline_%s_%02d" % (side, k + 1), (bx, -1.5 + dy, 0.46), yaw))
    for n, loc, yaw in seats:
        e = bpy.data.objects.new(n, None); Dio.objects.link(e); e.parent = seat_group
        e.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(yaw, 4, "Z"); marks.append(e)
    rep_markers = {n: {"position_game": [round(-loc[0], 3), round(loc[2], 3), round(loc[1], 3)], "yaw_deg_about_game_Y": round(math.degrees(yaw), 1),
                       "contact": "seat surface (place the fan root = seat - root_offset)"} for n, loc, yaw in seats}
    rep_markers.update({n: {"position_game": [round(-l[0], 3), round(l[2], 3), round(l[1], 3)]} for n, l in refs.items()})
    bpy.context.view_layer.update()
    if "palette_materials" in globals():         # one shared palette material for every flat-colour surface
        palette_materials(meshes, "arena_v9" if globals().get("ARENA_V9") else "arena", os.path.join(PROD, "Arena", "Textures"))
    for o in meshes + marks:                     # unique ASCII names (no .001 nodes)
        if "." in o.name:
            o.name = o.name.replace(".", "_")
    tris = sum(tri_count(o) for o in meshes)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROD, "Arena", "LaxAttack_Arena_v9.blend" if globals().get("ARENA_V9") else "LaxAttack_Arena.blend"), compress=True)
    rep = {"tris": tris, "markers": rep_markers}
    with open(os.path.join(EXP, "lax_arena_pinebrook_markers.json"), "w") as fh:
        json.dump({"asset": "lax_arena_pinebrook", "coordinates": "game space (meters, Y-up, gameplay forward -Z)",
                   "fan_root_offset_below_seat_m": {"lax_fan_a": 0.086, "lax_fan_b": 0.082, "lax_fan_c": 0.07},   # measured seated hip contact
                   "markers": rep_markers}, fh, indent=2)
    if export:
        path = os.path.join(PROD, "Exports", "lax_arena_pinebrook_v9.usdz" if globals().get("ARENA_V9") else "lax_arena_pinebrook.usdz")
        objs = [root] + list(groups.values()) + meshes + marks
        e = export_asset(objs, "lax_arena_pinebrook", "lax_arena_content", path, 30, 0, False, {"asset": "lax_arena_pinebrook"},
                         ["camera_gameplay"], animated=False)
        rep["lod0"] = {"meshes": e["meshes"], "materials": e["materials"], "kb": e["usdz_bytes"] // 1024, "textures": e["textures"], "root": e["root_identity"]}
        rep["check"] = arena_origin_check(path)
        for im in list(bpy.data.images):          # mobile variant: 1024 textures
            fp = bpy.path.abspath(im.filepath)
            if "Arena" in fp and "Textures" in fp and im.size[0] > 1024:
                root_, ext = os.path.splitext(fp); new = root_ + "_1k" + ext
                im.scale(1024, 1024); im.filepath_raw = new; im.save(); im.filepath = new
        em = export_asset(objs, "lax_arena_pinebrook", "lax_arena_content", path.replace(".usdz", "_mobile.usdz"), 30, 0, False,
                          {"asset": "lax_arena_pinebrook", "variant": "mobile 1024 textures"}, ["camera_gameplay"], False, bake=False)
        rep["mobile_kb"] = em["usdz_bytes"] // 1024; rep["mobile_textures"] = em["textures"]
        e["objects"] = [o.name for o in objs if o.name in bpy.data.objects]
        rep["lods"] = export_lods(e, "lax_arena_pinebrook", "lax_arena_content", path, (0.5, 0.2), animated=False)
        rep["check_lod2"] = arena_origin_check(path.replace(".usdz", "_lod2.usdz"))
    return rep

def arena_origin_check(path):
    from pxr import Usd, UsdGeom
    st = Usd.Stage.Open(path); bc = UsdGeom.BBoxCache(0, ["default", "render"]); bad = []; n = 0
    for p in st.Traverse():
        if p.IsA(UsdGeom.Mesh) and not p.GetName().startswith(("field_", "collision", "hero_tufts", "sky_", "meadow", "lake", "far_shore", "mountains")):
            n += 1; c = bc.ComputeWorldBound(p).ComputeAlignedRange().GetMidpoint()
            if abs(c[0]) < 2 and abs(c[2]) < 2 and c[1] < 4:
                bad.append(p.GetName())
    return {"checked": n, "near_origin": bad}
