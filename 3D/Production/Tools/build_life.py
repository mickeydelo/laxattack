# Lax Attack whimsy layer: critters + lake glints (lax_arena_life.usdz) and a confetti burst FX (lax_fx_confetti.usdz).
# Transform animation only (local pivots, like lax_arena_ambient). Loop length 480 (16 s) so critters move unhurriedly.
N_LIFE = 480; STARTLE0, STARTLE_N = 490, 120
MATS.setdefault("petal_pink", ((0.95, 0.45, 0.62), 0.6, 0.0, 0.0)); MATS.setdefault("petal_lilac", ((0.62, 0.50, 0.92), 0.6, 0.0, 0.0))
MATS.setdefault("bird_brown", ((0.36, 0.22, 0.13), 0.7, 0.0, 0.0)); MATS.setdefault("eye_black", ((0.02, 0.02, 0.03), 0.25, 0.0, 0.0))
MATS.setdefault("duck_cream", ((0.93, 0.88, 0.76), 0.7, 0.0, 0.0))

def _obj(name, parts, C, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    B = Builder(name)
    for g, m in parts:
        B.add(g, m)
    ob = B.build(C)
    ob.parent = parent; ob.matrix_parent_inverse = Matrix.Identity(4); ob.location = loc; ob.rotation_euler = rot
    return ob

def _piv(name, C, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); C.objects.link(e); e.parent = parent
    e.matrix_parent_inverse = Matrix.Identity(4); e.location = loc; e.rotation_euler = rot
    return e

def bird(C, parent, name, loc, yaw, s=2.2):
    root = _piv(name, C, parent, loc, (0, 0, yaw))
    body = [(ellipsoid((0, 0, 0.07 * s), (0.05 * s, 0.07 * s, 0.055 * s), 14, 9), "bird_brown"),
            (ellipsoid((0, 0.03 * s, 0.062 * s), (0.041 * s, 0.045 * s, 0.042 * s), 12, 8), "accent_coral"),
            (xform(ellipsoid((0, 0, 0), (0.024 * s, 0.05 * s, 0.007 * s), 10, 5), Matrix.Translation((0, -0.08 * s, 0.10 * s)) @ Matrix.Rotation(0.5, 4, "X")), "bird_brown"),
            (sweep([(0.015 * s, 0.01 * s, 0.03 * s), (0.015 * s, 0.012 * s, 0.0)], [0.004 * s, 0.003 * s], 5, 1.0), "accent_gold"),
            (sweep([(-0.015 * s, 0.01 * s, 0.03 * s), (-0.015 * s, 0.012 * s, 0.0)], [0.004 * s, 0.003 * s], 5, 1.0), "accent_gold")]
    _obj(name + "_body", body, C, root)
    hp = _piv(name + "_head", C, root, (0, 0.03 * s, 0.10 * s))
    head = [(ellipsoid((0, 0.015 * s, 0.03 * s), (0.038 * s, 0.038 * s, 0.036 * s), 12, 8), "bird_brown"),
            (ellipsoid((0, 0.058 * s, 0.028 * s), (0.008 * s, 0.022 * s, 0.008 * s), 8, 5), "accent_gold"),
            (ellipsoid((0.024 * s, 0.035 * s, 0.038 * s), (0.007 * s, 0.006 * s, 0.008 * s), 8, 5), "eye_black"),
            (ellipsoid((-0.024 * s, 0.035 * s, 0.038 * s), (0.007 * s, 0.006 * s, 0.008 * s), 8, 5), "eye_black")]
    _obj(name + "_headmesh", head, C, hp)
    wings = []
    for sx in (1, -1):
        wp = _piv(name + ("_wingL" if sx > 0 else "_wingR"), C, root, (0.04 * s * sx, -0.005 * s, 0.10 * s))
        _obj(wp.name + "_mesh", [(ellipsoid((0.01 * s * sx, -0.01 * s, -0.02 * s), (0.013 * s, 0.05 * s, 0.035 * s), 10, 6), "bird_brown")], C, wp)
        wings.append((wp, sx))
    return root, hp, wings

def butterfly(C, parent, name, col, s=2.6):
    root = _piv(name, C, parent)
    _obj(name + "_body", [(ellipsoid((0, 0, 0), (0.006 * s, 0.028 * s, 0.006 * s), 8, 5), "eye_black")], C, root)
    wings = []
    for sx in (1, -1):
        wp = _piv(name + ("_wingL" if sx > 0 else "_wingR"), C, root)
        wv = [(0, 0.02 * s, 0.0), (0.05 * s * sx, 0.035 * s, 0.0), (0.045 * s * sx, -0.01 * s, 0.0), (0.03 * s * sx, -0.035 * s, 0.0), (0, -0.015 * s, 0.0)]
        top = [(x, y, 0.0015) for x, y, z in wv]; bot = [(x, y, -0.0015) for x, y, z in wv]
        n = len(wv); verts = top + bot
        faces = [tuple(range(n)) if sx < 0 else tuple(reversed(range(n))), tuple(range(n, 2 * n)) if sx > 0 else tuple(reversed(range(n, 2 * n)))]
        for i in range(n):
            j = (i + 1) % n; faces.append((i, j, n + j, n + i) if sx > 0 else (i, n + i, n + j, j))
        _obj(wp.name + "_mesh", [((verts, faces), col)], C, wp)
        wings.append((wp, sx))
    return root, wings

def duck(C, parent, name, s=1.7):
    root = _piv(name, C, parent)
    parts = [(ellipsoid((0, 0, 0.05 * s), (0.10 * s, 0.16 * s, 0.075 * s), 14, 9), "duck_cream"),
             (xform(ellipsoid((0, 0, 0), (0.05 * s, 0.07 * s, 0.03 * s), 10, 6), Matrix.Translation((0, -0.15 * s, 0.09 * s)) @ Matrix.Rotation(0.6, 4, "X")), "duck_cream")]
    _obj(name + "_body", parts, C, root)
    hp = _piv(name + "_head", C, root, (0, 0.11 * s, 0.10 * s))
    _obj(name + "_headmesh", [(ellipsoid((0, 0.01 * s, 0.05 * s), (0.05 * s, 0.055 * s, 0.05 * s), 12, 8), "accent_teal"),
                             (ellipsoid((0, 0.065 * s, 0.045 * s), (0.02 * s, 0.035 * s, 0.01 * s), 8, 5), "accent_gold"),
                             (ellipsoid((0.035 * s, 0.03 * s, 0.065 * s), (0.008 * s, 0.007 * s, 0.009 * s), 6, 4), "eye_black"),
                             (ellipsoid((-0.035 * s, 0.03 * s, 0.065 * s), (0.008 * s, 0.007 * s, 0.009 * s), 6, 4), "eye_black")], C, hp)
    return root, hp

def build_life(export=True, fence_top=0.95, fence_y=-12.55):
    reset_scene("LaxAttack_Life"); C = coll("lax_arena_life")
    content = bpy.data.objects.new("lax_arena_life_content", None); C.objects.link(content)
    birds = [bird(C, content, "life_bird_00", (2.3, fence_y, fence_top), math.radians(160)),
             bird(C, content, "life_bird_01", (-3.3, fence_y, fence_top), math.radians(205))]
    flies = [(butterfly(C, content, "life_butterfly_%02d" % i, col), c) for i, (col, c) in
             enumerate((("accent_gold", (-2.0, -12.1, 0.75)), ("kit_white", (1.4, -12.0, 0.9)), ("petal_lilac", (4.2, -12.2, 0.65))))]
    dk = duck(C, content, "life_duck_00")
    glints = []
    rnd = random.Random(11)
    for i in range(16):
        g = _obj("life_glint_%02d" % i, [(ellipsoid((0, 0, 0), (0.16, 0.05, 0.004), 10, 4), "kit_white")], C, content,
                 (rnd.uniform(-12, 12), rnd.uniform(-38, -22), -0.448), (0, 0, rnd.uniform(-0.3, 0.3)))
        glints.append((g, rnd.uniform(0, 1), rnd.uniform(0, 1)))
    bpy.context.view_layer.update()
    rest = {o: (o.location.copy(), o.rotation_euler.copy()) for o in bpy.data.objects if o.name.startswith("life_") and o.type == "EMPTY" or o.name.startswith("life_glint")}
    def keyall(f):
        for o in rest:
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    def env(t, a, b):
        return math.sin(math.pi * min(1.0, max(0.0, (t - a) / (b - a))))
    def pose_reset():
        for o, (l, r) in rest.items():
            o.location = l; o.rotation_euler = r
    def pose_birds(f):
        w = 2 * math.pi * f / N_LIFE
        for bi, (root, hp, wings) in enumerate(birds):
            l, r = rest[root]; ff = (f + bi * 190) % N_LIFE
            hop = sum(env(ff, h, h + 8) for h in (40, 250))
            turn = 22 * math.sin(math.pi * min(1, max(0, (ff - 40) / 210.0)))
            root.location = (l.x, l.y, l.z + 0.07 * hop); root.rotation_euler = (0, 0, r.z + math.radians(turn))
            peck = sum(env(ff, p_, p_ + 7) for p_ in (95, 118, 330, 400))
            tilt = 28 * math.sin(2 * w + bi) * (1 - peck)
            hp.rotation_euler = (math.radians(55 * peck), math.radians(tilt * 0.4), math.radians(tilt))
            for wp, sx in wings:
                wp.rotation_euler = (0, math.radians(-45 * sx * hop * abs(math.sin(f * 1.4))), 0)
    def pose_others(f):
        w = 2 * math.pi * f / N_LIFE
        for fi, ((root, wings), c) in enumerate(flies):
            ph = fi * 2.1
            x = c[0] + 0.7 * math.sin(2 * w + ph); y = c[1] + 0.35 * math.sin(3 * w + ph); z = c[2] + 0.25 * math.sin(5 * w + ph) + 0.03 * math.sin(40 * w)
            dx_ = 1.4 * math.cos(2 * w + ph); dy_ = 1.05 * math.cos(3 * w + ph)
            root.location = (x, y, z); root.rotation_euler = (math.radians(-15), 0, math.atan2(-dx_, dy_))
            for wp, sx in wings:
                wp.rotation_euler = (0, math.radians(-sx * (10 + 62 * (0.5 + 0.5 * math.sin(80 * w + ph)))), 0)
        root, hp = dk
        root.location = (-9.0 + 2.6 * math.sin(w), -27.0 + 1.2 * math.cos(w), -0.43 + 0.012 * math.sin(6 * w))
        root.rotation_euler = (math.radians(1.5 * math.sin(5 * w)), 0, math.atan2(-2.6 * math.cos(w), -1.2 * math.sin(w)))
        dip = sum(env(f % N_LIFE, a, a + 16) for a in (150, 380))
        hp.rotation_euler = (math.radians(70 * dip), 0, math.radians(15 * math.sin(3 * w) * (1 - dip)))
        for g, a, b in glints:
            l, r = rest[g]; tw = max(env((f / N_LIFE + a) % 1.0 * N_LIFE, 0, 14), env((f / N_LIFE + b) % 1.0 * N_LIFE, 200, 212))
            g.location = (l.x, l.y, -0.448 + 0.024 * tw)
    for f in range(N_LIFE + 1):       # --- life_loop (seamless)
        pose_reset(); pose_birds(f); pose_others(f); keyall(f)
    for k in range(STARTLE_N + 1):    # --- birds_startle: birds flutter up, circle, land back; everyone else is startled too (faster)
        f = STARTLE0 + k; u = k / STARTLE_N
        pose_reset(); pose_birds(0); pose_others(k * N_LIFE / STARTLE_N)     # ends exactly on the loop's frame-0 pose
        for bi, (root, hp, wings) in enumerate(birds):
            sg = 1 if bi == 0 else -1
            bl = root.location.copy(); brz = root.rotation_euler.z; h0 = hp.rotation_euler.copy()   # this bird's loop frame-0 pose
            up = math.sin(math.pi * u) ** 0.7; wgt = math.sin(math.pi * u)
            root.location = (bl.x + 0.9 * sg * math.sin(2 * math.pi * u), bl.y + 0.5 * (1 - math.cos(2 * math.pi * u)), bl.z + 1.4 * up)
            root.rotation_euler = (0, 0, brz + 2 * math.pi * u * sg)
            flap = 1.0 if 0.03 < u < 0.95 else 0.0
            for wp, sx in wings:
                wp.rotation_euler = (0, math.radians(-sx * 70 * flap * (0.5 + 0.5 * math.sin(k * 2.2))), 0)
            hp.rotation_euler = (h0.x * (1 - wgt) + math.radians(-10) * wgt, h0.y * (1 - wgt), h0.z * (1 - wgt))
        keyall(f)
    for o in bpy.data.objects:
        ad = o.animation_data
        if ad and ad.action and hasattr(ad.action, "fcurves"):
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    sc = bpy.context.scene; sc.frame_start = 0; sc.frame_end = STARTLE0 + STARTLE_N
    objs = [o for o in bpy.data.objects if o.name.startswith(("life_", "lax_arena_life"))]
    if "palette_materials" in globals():
        palette_materials([o for o in objs if o.type == "MESH"], "life", os.path.join(PROD, "Arena", "Textures"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROD, "Arena", "LaxAttack_Life.blend"), compress=True)
    clips = [Clip("life_loop", 0, N_LIFE, True, None, notes="16 s seamless: birds hop/peck/tilt on the fence, butterflies flutter over the hedges, duck glides and dips, lake glints twinkle"),
             Clip("birds_startle", STARTLE0, STARTLE_N, False, None, notes="both birds flutter up, circle and land back on their perch (use on goal / crowd roar); starts and ends on the loop rest pose")]
    man = manifest("lax_arena_life", clips, perspective="none", extra={"placement": "scene origin, together with lax_arena_pinebrook", "toggleable": True,
                   "critters": ["life_bird_00", "life_bird_01", "life_butterfly_00..02", "life_duck_00", "life_glint_00..15"]})
    rep = {"tris": sum(tri_count(o) for o in objs if o.type == "MESH")}
    if export:
        path = os.path.join(EXP, "lax_arena_life.usdz")
        e = export_asset(objs, "lax_arena_life", "lax_arena_life_content", path, 30, STARTLE0 + STARTLE_N, False, man, (), True, bake=False, content_axis=True)
        rep.update(kb=e["usdz_bytes"] // 1024, meshes=e["meshes"], root=e["root_identity"], y=e["baked_y_range"])
        json.dump(man, open(os.path.join(EXP, "lax_arena_life_clips.json"), "w"), indent=2)
    return rep

def build_confetti(export=True, n=90, frames=105):
    reset_scene("LaxAttack_Confetti"); C = coll("lax_fx_confetti")
    content = bpy.data.objects.new("lax_fx_confetti_content", None); C.objects.link(content)
    rnd = random.Random(5); cols = ("kit_red", "accent_gold", "accent_teal", "kit_white", "accent_coral", "petal_lilac")
    pieces = []
    for i in range(n):
        w_, h_ = rnd.uniform(0.035, 0.055), rnd.uniform(0.02, 0.03)
        v = [(-w_, -h_, -0.002), (w_, -h_, -0.002), (w_, h_, -0.002), (-w_, h_, -0.002), (-w_, -h_, 0.002), (w_, -h_, 0.002), (w_, h_, 0.002), (-w_, h_, 0.002)]
        fcs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        o = _obj("fx_confetti_%02d" % i, [((v, fcs), cols[i % len(cols)])], C, content)
        a = rnd.uniform(0, 2 * math.pi); tilt = math.radians(rnd.uniform(5, 38)); sp = rnd.uniform(4.2, 6.8)
        vel = V((math.cos(a) * math.sin(tilt) * sp, math.sin(a) * math.sin(tilt) * sp, math.cos(tilt) * sp))
        spin = V((rnd.uniform(-14, 14), rnd.uniform(-14, 14), rnd.uniform(-6, 6))); pieces.append([o, V((0, 0, 0.05)), vel, V((0, 0, 0)), spin, rnd.uniform(0, 6), False])
    dt = 1.0 / 30
    for f in range(frames + 1):
        for pc in pieces:
            o, pos, vel, rot, spin, ph, rest = pc
            if f > 0 and not rest:
                vel.z -= 9.8 * dt
                if vel.z < -0.9:
                    vel.z = -0.9                                   # paper flutter terminal velocity
                vel.x *= 0.975; vel.y *= 0.975
                pos += vel * dt + V((0.02 * math.sin(f * 0.35 + ph), 0.02 * math.cos(f * 0.3 + ph), 0))
                rot += spin * dt
                if pos.z <= 0.004 and vel.z < 0:
                    pos.z = 0.004; pc[6] = True; rot.x = 0.0; rot.y = 0.0     # lands flat on the turf
            o.location = pos; o.rotation_euler = rot
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    sc = bpy.context.scene; sc.frame_start = 0; sc.frame_end = frames
    objs = [o for o in bpy.data.objects if o.name.startswith(("fx_confetti", "lax_fx_confetti"))]
    if "palette_materials" in globals():
        palette_materials([o for o in objs if o.type == "MESH"], "confetti", os.path.join(PROD, "FX", "Textures"))
    os.makedirs(os.path.join(PROD, "FX"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROD, "FX", "LaxAttack_Confetti.blend"), compress=True)
    clips = [Clip("confetti_burst", 0, frames, False, None, notes="cannon pop from the origin: pieces rise 1-2.3 m, flutter down and settle flat on the turf by ~frame 90")]
    man = manifest("lax_fx_confetti", clips, perspective="none", extra={"placement": "place at a goal-side or crowd position on a goal; hide ~2 s after the clip ends",
                                                                       "pieces": n})
    rep = {"tris": sum(tri_count(o) for o in objs if o.type == "MESH"), "landed": sum(1 for pc in pieces if pc[6])}
    if export:
        path = os.path.join(EXP, "lax_fx_confetti.usdz")
        e = export_asset(objs, "lax_fx_confetti", "lax_fx_confetti_content", path, 30, frames, False, man, (), True, bake=False, content_axis=True)
        rep.update(kb=e["usdz_bytes"] // 1024, root=e["root_identity"], y=e["baked_y_range"])
        json.dump(man, open(os.path.join(EXP, "lax_fx_confetti_clips.json"), "w"), indent=2)
    return rep
