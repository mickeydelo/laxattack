# Lax Attack ambient life v2: transform hierarchy (no skinning). Every animated object keeps a LOCAL pivot:
#   tree:   amb_tree_NN (trunk base) -> trunk mesh ; amb_tree_NN_canopy (pivot on the trunk) -> canopy mesh
#   hedge:  amb_hedge_NN (base) -> mesh     flag: amb_flag_NN (pole base) -> pole ; _seg1.._seg3 chain -> pennant
#   boat:   amb_boat_NN (waterline) -> hull/mast/sails      cloud: amb_cloud_NN -> mesh
# The static arena builds identical "ambient_twins" from the same geometry functions (make_twins).
TREES = [(4.2, -15.0, 4.6), (6.8, -16.5, 5.4), (9.5, -14.2, 4.8), (-7.6, -15.2, 5.0), (-9.8, -17.0, 5.6), (11.8, -17.5, 5.0), (-12.5, -14.6, 4.6)]
PINES = [(13.5, -15.5, 5.8), (-14.0, -18.5, 6.2)]
HEDGES = [(x, -13.3 - 0.3 * (i % 2), 1.0 + 0.25 * (i % 3)) for i, x in enumerate((-2.4, -1.3, -0.2, 0.9, 2.0, 3.1, -3.5, -5.2, 5.4))]
FLAGS = [((6.95, -12.55), "kit_red"), ((-6.95, -12.55), "accent_teal"), ((6.95, -4.0), "accent_gold"), ((-6.95, -4.0), "kit_red")]
BOATS = [((-5.0, -26.0), 1.6, 0.0), ((8.0, -30.0), 1.25, 2.1)]
CLOUDS = [(-13, -70, 14.5, 4.0), (9, -78, 17.5, 4.6), (-1, -95, 23, 3.6), (21, -92, 13, 3.2), (-24, -88, 20, 4.2)]
GROUND_Z = -0.45; WATER_Z = -0.43; N_LOOP = 240; GUST0, GUST_N = 250, 90

def _blob(c, r, seed, useg=14, vseg=9):
    rnd = random.Random(seed); ph = rnd.uniform(0, 6)
    def f(q):
        d = q - V(c); a = math.atan2(d.y, d.x); e = d.z / max(r[2], 1e-3)
        k = 1 + 0.08 * math.sin(5 * a + ph) * math.cos(3 * e) + 0.05 * math.sin(9 * a + 2 * ph) * math.cos(5 * e)
        return V(c) + V((d.x * k, d.y * k, d.z * (0.85 if d.z < 0 else 1.0) * k))
    return deform(ellipsoid(c, r, useg, vseg), f)

def tree_parts(seed, h, kind="broadleaf"):
    """Local geometry (origin = trunk base). Returns trunk parts, canopy parts (relative to pivot), pivot height."""
    rnd = random.Random(seed)
    if kind == "pine":
        pz = h * 0.30
        trunk = [(sweep([(0, 0, 0), (0, 0, h * 0.35)], [h * 0.06, h * 0.045], 8, 1.0), "bark")]
        can = []
        for i in range(4):
            t = i / 4; zb = h * (0.18 + 0.72 * t) - pz; top = zb + h * (0.36 - 0.08 * t); rb = h * (0.34 - 0.22 * t) * rnd.uniform(0.92, 1.05)
            def sc(q, rb=rb, i=i):
                a = math.atan2(q.y, q.x); rr = math.hypot(q.x, q.y); k = 1 + 0.10 * math.sin(7 * a + i)
                return V((q.x * k, q.y * k, q.z - 0.08 * h * (rr / rb) ** 3))
            g = loft([(zb, rb * 0.4, rb * 0.4), (zb - 0.02 * h, rb, rb), (zb + 0.03 * h, rb * 0.95, rb * 0.95), (zb + (top - zb) * 0.55, rb * 0.42, rb * 0.42), (top, 0.02, 0.02)], 21, "flat", "pole")
            can.append((deform(g, sc), "pine" if i % 2 == 0 else "leaf_c"))
        return trunk, can, pz
    pz = h * 0.42
    trunk = [(sweep([(0, 0, 0), (0.02 * h, 0, h * 0.35), (0, 0.03 * h, h * 0.55)], [h * 0.07, h * 0.05, h * 0.035], 9, 1.0), "bark")]
    for sx in (-1, 1):
        trunk.append((sweep([(0.01 * h, 0, h * 0.38), (0.14 * h * sx, 0.02 * h, h * 0.55)], [h * 0.03, h * 0.015], 7, 1.0), "bark"))
    can = []; cz = h * 0.68 - pz; R = (h * 0.40, h * 0.36, h * 0.28)
    for i in range(20):      # leaf clusters on a shell + a few inner: dark interior, sunlit top/outer tips
        u = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(-0.55, 1.0); inner = i >= 16
        s = 0.55 if inner else 1.0
        c = (math.cos(u) * math.sqrt(1 - v * v) * R[0] * s, math.sin(u) * math.sqrt(1 - v * v) * R[1] * s, cz + v * R[2] * s)
        r = h * rnd.uniform(0.13, 0.19); m = "leaf_c" if (inner or v < -0.2) else ("leaf_b" if v > 0.35 else "leaf_a")
        can.append((_blob(c, (r, r * 0.95, r * 0.85), seed * 31 + i), m))
    return trunk, can, pz

def hedge_parts(seed, s):
    rnd = random.Random(seed); out = []
    for i in range(6):
        c = (rnd.uniform(-0.45, 0.45) * s, rnd.uniform(-0.3, 0.3) * s, s * rnd.uniform(0.28, 0.45))
        r = s * rnd.uniform(0.30, 0.42)
        out.append((_blob(c, (r, r * 0.9, r * 0.8), seed * 17 + i, 12, 8), ("leaf_c", "leaf_a", "leaf_b")[i % 3]))
    return out

def _prism(tri, th):
    """Closed thin prism from a triangle (y = thickness axis): visible from both sides, outward normals."""
    a, b, c = [V(p) for p in tri]; o = V((0, th / 2, 0))
    v = [tuple(a - o), tuple(b - o), tuple(c - o), tuple(a + o), tuple(b + o), tuple(c + o)]
    f = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return v, f

def boat_parts(s):
    """Complete toy sailboat: closed hull (seated ~30% below the waterline), deck stripe, mast, two double-sided sails, pennant."""
    parts = [(superellipsoid((0.95 * s, 2.7 * s, 0.55 * s), 0.55, 0.35, 24, 10, (0, 0, 0.12 * s)), "kit_red"),
             (superellipsoid((0.80 * s, 2.3 * s, 0.10 * s), 0.3, 0.3, 20, 4, (0, 0, 0.40 * s)), "wood"),
             (superellipsoid((0.97 * s, 2.72 * s, 0.09 * s), 0.5, 0.35, 24, 4, (0, 0, 0.30 * s)), "kit_white"),
             (sweep([(0, 0.15 * s, 0.4 * s), (0, 0.15 * s, 3.5 * s)], [0.05 * s, 0.04 * s], 8, 1.0), "wood_dark"),
             (_prism([(0, 0.25 * s, 0.6 * s), (0, 0.25 * s, 3.4 * s), (0, 1.9 * s, 0.6 * s)], 0.05 * s), "kit_white"),
             (_prism([(0, 0.05 * s, 0.7 * s), (0, 0.05 * s, 3.0 * s), (0, -1.6 * s, 0.7 * s)], 0.05 * s), "accent_coral"),
             (_prism([(0, 0.15 * s, 3.55 * s), (0, 0.15 * s, 3.35 * s), (0, -0.35 * s, 3.45 * s)], 0.03 * s), "accent_gold")]
    return [(xform(g, Matrix.Rotation(math.radians(90), 4, "Z")), m) if False else (g, m) for g, m in parts]

def flag_parts(color):
    pole = [(sweep([(0, 0, 0), (0, 0, 2.05)], [0.035, 0.03], 8, 1.0), "wood_dark"), (ellipsoid((0, 0, 2.07), (0.05, 0.05, 0.05), 10, 6), "accent_gold")]
    segs = []
    for k in range(3):   # pennant segments in local seg space (x along the flag), tapering
        w0 = 0.16 * (1 - k / 3.0); w1 = 0.16 * (1 - (k + 1) / 3.0) + 0.002
        v = [(0, -0.012, w0), (0.26, -0.012, w1), (0.26, -0.012, -w1), (0, -0.012, -w0), (0, 0.012, w0), (0.26, 0.012, w1), (0.26, 0.012, -w1), (0, 0.012, -w0)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        segs.append(((v, f), color))
    return pole, segs

def cloud_parts(seed, s):
    out = []
    for g, m in blob_cluster(seed, (0, 0, 0), (3.0 * s, 1.2 * s, 1.1 * s), 6, ("cloud",), 16, 10):
        out.append((deform(g, lambda q: V((q.x, q.y, max(q.z, -0.18 * s)))), m))
    return out

def _mesh(name, parts, coll_, parent=None):
    B = Builder(name)
    for g, m in parts:
        B.add(g, m)
    ob = B.build(coll_)
    if parent is not None:
        ob.parent = parent; ob.matrix_parent_inverse = Matrix.Identity(4); ob.location = (0, 0, 0)
    return ob

def _empty(name, coll_, parent, loc, rotz=0.0):
    e = bpy.data.objects.new(name, None); coll_.objects.link(e); e.parent = parent
    e.matrix_parent_inverse = Matrix.Identity(4); e.location = loc; e.rotation_euler = (0, 0, rotz)
    return e

def _yaw(seed):
    return random.Random(seed * 7 + 3).uniform(0, 6.28)

def build_hierarchy(C, root):
    """Creates the pivot hierarchy + meshes under root. Returns {kind: [(pivot, extra)]}."""
    H = {"tree": [], "hedge": [], "flag": [], "boat": [], "cloud": []}
    for i, (x, y, h) in enumerate(TREES + PINES):
        kind = "pine" if i >= len(TREES) else "broadleaf"; seed = 40 + i
        trunk, can, pz = tree_parts(seed, h, kind)
        p = _empty("amb_tree_%02d" % i, C, root, (x, y, GROUND_Z), _yaw(seed))
        _mesh("amb_tree_%02d_trunk" % i, trunk, C, p)
        cp = _empty("amb_tree_%02d_canopy" % i, C, p, (0, 0, pz))
        _mesh("amb_tree_%02d_leaves" % i, can, C, cp)
        H["tree"].append((p, cp, x, y, h))
    for i, (x, y, s) in enumerate(HEDGES):
        p = _empty("amb_hedge_%02d" % i, C, root, (x, y, GROUND_Z)); _mesh("amb_hedge_%02d_leaves" % i, hedge_parts(60 + i, s), C, p)
        H["hedge"].append((p, x))
    for i, ((x, y), col) in enumerate(FLAGS):
        pole, segs = flag_parts(col)
        p = _empty("amb_flag_%02d" % i, C, root, (x, y, 0.0), 0.0 if x < 0 else math.pi)
        _mesh("amb_flag_%02d_pole" % i, pole, C, p)
        prev = p; chain = []
        for k, sp in enumerate(segs):
            e = _empty("amb_flag_%02d_seg%d" % (i, k + 1), C, prev, (0.0, 0, 1.95) if k == 0 else (0.26, 0, 0))
            _mesh("amb_flag_%02d_cloth%d" % (i, k + 1), [sp], C, e); chain.append(e); prev = e
        H["flag"].append((p, chain, i))
    for i, ((x, y), s, ph) in enumerate(BOATS):
        p = _empty("amb_boat_%02d" % i, C, root, (x, y, WATER_Z), math.radians(78 if i == 0 else -65))
        _mesh("amb_boat_%02d_hull" % i, boat_parts(s), C, p)
        H["boat"].append((p, x, y, ph))
    for i, (x, y, z, s) in enumerate(CLOUDS):
        p = _empty("amb_cloud_%02d" % i, C, root, (x, y, z)); _mesh("amb_cloud_%02d_puff" % i, cloud_parts(90 + i, s), C, p)
        H["cloud"].append((p, x, y, z))
    return H

def make_twins(C):
    """Static copies (identical rest geometry and placement) for the static arena group 'ambient_twins'."""
    tmp = bpy.data.objects.new("_twin_root", None); C.objects.link(tmp)
    build_hierarchy(C, tmp); bpy.context.view_layer.update()
    meshes = []
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name.startswith("amb_") and o.parent is not None:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
            o.name = o.name.replace("amb_", "twin_"); meshes.append(o)
    for o in [o for o in bpy.data.objects if o.type == "EMPTY" and (o.name.startswith("amb_") or o.name == "_twin_root")]:
        bpy.data.objects.remove(o, do_unlink=True)
    return meshes

def animate(H):
    """Keyframes every pivot for ambient_loop (0..240, seamless) and ambient_gust (250..340)."""
    def pose(t, gust, gx):   # t = loop phase frame, gust envelope function of x
        w = 2 * math.pi * t / N_LOOP; out = {}
        for (p, cp, x, y, h) in H["tree"]:
            r = random.Random(int(x * 10 + y)); ph = r.uniform(0, 6.28); amp = r.uniform(0.75, 1.25); g = gust(x)
            tr = (0.35 * amp + 1.2 * g) * math.sin(2 * w + ph)
            ca = (1.8 * amp + 4.0 * g) * math.sin(2 * w + ph - 0.7) + 0.5 * amp * math.sin(5 * w + ph * 1.3)
            out[p] = ("rot", (math.radians(tr * 0.5), math.radians(tr), p.rotation_euler.z))
            out[cp] = ("rot", (math.radians(ca * 0.45), math.radians(ca), 0.0))
        for (p, x) in H["hedge"]:
            g = gust(x); a = (1.4 + 3.0 * g) * math.sin(3 * w + x)
            out[p] = ("rot", (math.radians(a * 0.4), math.radians(a), 0.0))
        for (p, chain, i) in H["flag"]:
            g = gust(p.location.x)
            for k, e in enumerate(chain):
                out[e] = ("rot", (math.radians((6 + 6 * g) * math.sin(12 * w - k * 1.1 + i)), 0.0,
                                  math.radians((12 + 10 * g) * math.sin(8 * w - k * 0.9 + i) + (8 if k == 0 else 0))))
        for (p, x, y, ph) in H["boat"]:
            out[p] = ("both", (x + 0.8 * math.sin(w + ph), y + 0.25 * math.sin(w * 2 + ph), WATER_Z + 0.035 * math.sin(4 * w + ph)),
                      (math.radians(2.5 * math.sin(3 * w + ph)), math.radians(1.8 * math.sin(2 * w + ph + 1)), p["yaw0"] + math.radians(4 * math.sin(w + ph))))
        for (p, x, y, z) in H["cloud"]:
            out[p] = ("loc", (x + 1.6 * math.sin(w + x * 0.1), y, z + 0.3 * math.sin(2 * w + x)), None)
        return out
    for (p, x, y, ph) in H["boat"]:
        p["yaw0"] = p.rotation_euler.z
    for (p, cp, x, y, h) in H["tree"]:
        p["yaw0"] = p.rotation_euler.z
    P0 = pose(0, lambda x: 0.0, 0)                 # frame 0 == rest pose exactly: swapping in for the static twins never pops
    rest = {ob: (ob.location.copy(), ob.rotation_euler.copy()) for ob in P0}
    def key(frame, poses):
        for ob, (kind, a, *b) in poses.items():
            k0, a0, *b0 = P0[ob]; rl, rr = rest[ob]
            if kind == "rot":
                ob.rotation_euler = tuple(r + x - x0 for r, x, x0 in zip(rr, a, a0)); ob.keyframe_insert("rotation_euler", frame=frame)
            elif kind == "loc":
                ob.location = tuple(r + x - x0 for r, x, x0 in zip(rl, a, a0)); ob.keyframe_insert("location", frame=frame)
            else:
                ob.location = tuple(r + x - x0 for r, x, x0 in zip(rl, a, a0))
                ob.rotation_euler = tuple(r + x - x0 for r, x, x0 in zip(rr, b[0], b0[0]))
                ob.keyframe_insert("location", frame=frame); ob.keyframe_insert("rotation_euler", frame=frame)
    for f in range(N_LOOP + 1):
        key(f, pose(f, lambda x: 0.0, 0))
    for f in range(GUST_N + 1):      # gust: travelling wave across x (left -> right), from and back to the frame-0 pose
        u = f / GUST_N
        def gust(x, u=u):
            d = (x + 15) / 30.0 * 0.35; v = min(1.0, max(0.0, (u - d) / 0.6))
            return math.sin(math.pi * v) ** 2
        key(GUST0 + f, pose(f * (N_LOOP / GUST_N), gust, 0))   # ends on loop phase 240 == frame-0 pose
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if ad and ad.action:
            for fc in (ad.action.fcurves if hasattr(ad.action, "fcurves") else []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"

def build_ambient(export=True):
    reset_scene("LaxAttack_Ambient")
    C = coll("lax_arena_ambient")
    root = bpy.data.objects.new("lax_arena_ambient_content", None); C.objects.link(root)
    H = build_hierarchy(C, root)
    bpy.context.view_layer.update()
    animate(H)
    sc = bpy.context.scene; sc.frame_start = 0; sc.frame_end = GUST0 + GUST_N
    sc.timeline_markers.new("ambient_loop", frame=0); sc.timeline_markers.new("ambient_gust", frame=GUST0)
    objs = [o for o in bpy.data.objects if o.name.startswith(("amb_", "lax_arena_ambient"))]
    tris = sum(tri_count(o) for o in objs if o.type == "MESH")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROD, "Arena", "LaxAttack_Ambient.blend"), compress=True)
    clips = [Clip("ambient_loop", 0, N_LOOP, True, None, notes="seamless 8 s breeze; per-object phase/amplitude variation"),
             Clip("ambient_gust", GUST0, GUST_N, False, None, notes="gust wave travels across the foliage (x -15 -> +15 m); starts/ends on the ambient_loop frame-0 pose")]
    man = manifest("lax_arena_ambient", clips, perspective="none", extra={
        "hierarchy": "transform animation only (no skeleton): each amb_* Xform is a local pivot; meshes are local to their pivot",
        "pivots": {"tree": "amb_tree_NN at the trunk base; amb_tree_NN_canopy on the trunk", "hedge": "amb_hedge_NN at the base",
                   "flag": "amb_flag_NN at the pole base; amb_flag_NN_seg1..3 chain", "boat": "amb_boat_NN at the waterline", "cloud": "amb_cloud_NN"},
        "static_twins": "hide the static arena group 'ambient_twins' while this asset is shown (identical rest placement)",
        "tris": tris})
    rep = {"tris": tris, "objects": len(objs)}
    if export:
        path = os.path.join(EXP, "lax_arena_ambient.usdz")
        e = export_asset(objs, "lax_arena_ambient", "lax_arena_ambient_content", path, 30, GUST0 + GUST_N, False, man, (), True, bake=False, content_axis=True)
        rep.update(kb=e["usdz_bytes"] // 1024, meshes=e["meshes"], y=e["baked_y_range"], root=e["root_identity"])
        with open(os.path.join(EXP, "lax_arena_ambient_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep
