# Lax Attack v9 environment (Phase C): matches the gameplay concept art (bubbly trees, pine forest, rocky shore, bright lake,
# flowering fence bushes, tufty grass, puffy clouds). Reuses the v8 field/turf/lines/fence/goal/lake basin/signs/foreground.
def _lin3(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
for _k, (_c, _r) in {"leaf_light_v9": ((0.60, 0.80, 0.25), 0.55), "leaf_mid_v9": ((0.36, 0.64, 0.17), 0.6), "leaf_dark_v9": ((0.17, 0.40, 0.10), 0.7),
                     "pine_dark_v9": ((0.10, 0.28, 0.15), 0.7), "pine_mid_v9": ((0.18, 0.42, 0.20), 0.65), "bark_v9": ((0.48, 0.30, 0.16), 0.8),
                     "rock_v9": ((0.70, 0.62, 0.50), 0.8), "rock_dark_v9": ((0.50, 0.45, 0.38), 0.85), "water_v9": ((0.12, 0.45, 0.88), 0.08),
                     "cloud_v9": ((0.99, 0.99, 1.0), 0.9), "flower_yellow_v9": ((1.0, 0.84, 0.18), 0.5), "flower_white_v9": ((0.98, 0.97, 0.92), 0.5),
                     "bush_v9": ((0.30, 0.56, 0.15), 0.65), "tuft_v9": ((0.40, 0.72, 0.18), 0.6), "tuft_tip_v9": ((0.72, 0.86, 0.26), 0.6),
                     "sky_blue_v9": ((0.36, 0.62, 0.95), 1.0)}.items():
    MATS[_k] = (_lin3(_c), _r, 0.0, 0.0)

def _fib(n):
    g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(max(0.0, 1 - z * z)); t = g * i
        yield V((math.cos(t) * r, math.sin(t) * r, z))

def popcorn_tree(C, name, loc, h, seed):
    rnd = random.Random(seed); B = Builder(name)
    B.add(sweep([(0, 0, 0), (0.01 * h, 0, 0.3 * h), (0, 0.02 * h, 0.58 * h)], [0.085 * h, 0.06 * h, 0.045 * h], 12, 1.0), "bark_v9")
    for sx in (1, -1):
        B.add(sweep([(0.0, 0, 0.42 * h), (0.16 * h * sx, 0.03 * h, 0.62 * h)], [0.03 * h, 0.018 * h], 8, 1.0), "bark_v9")
    subs = [((0, 0, 0.70 * h), (0.36 * h, 0.34 * h, 0.27 * h))]
    for k in range(4):
        a = rnd.uniform(0, 6.28) + k * 1.57
        subs.append(((math.cos(a) * 0.26 * h, math.sin(a) * 0.22 * h, rnd.uniform(0.52, 0.86) * h), (0.24 * h, 0.23 * h, 0.2 * h)))
    for c, r in subs:
        B.add(ellipsoid(c, (r[0] * 0.9, r[1] * 0.9, r[2] * 0.9), 14, 9), "leaf_dark_v9")
        n = int(10 + 30 * (r[0] / (0.36 * h)) ** 2)
        for d in _fib(n):
            if d.z < -0.55:
                continue
            p = V(c) + V((d.x * r[0], d.y * r[1], d.z * r[2])); rs = h * rnd.uniform(0.095, 0.13)
            m = "leaf_light_v9" if d.z > 0.35 else ("leaf_mid_v9" if d.z > -0.2 else "leaf_dark_v9")
            B.add(ellipsoid(tuple(p), (rs, rs, rs * 0.92), 7, 5), m)
    o = B.build(C); o.location = loc; o.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    return o

def pine_forest(C, seed=21):
    rnd = random.Random(seed); B = Builder("v9_pine_forest")
    for row, (y0, hmin, hmax) in enumerate(((-77.0, 7.0, 10.0), (-82.0, 8.0, 12.5), (-87.5, 9.5, 14.0), (-93.0, 10.5, 16.0))):
        x = -75.0 + rnd.uniform(0, 1.5)
        while x < 75.0:
            h = rnd.uniform(hmin, hmax) * 0.62; y = y0 + rnd.uniform(-1.4, 1.4); z0 = -0.45 + 0.6 * row
            B.add(sweep([(x, y, z0), (x, y, z0 + 0.25 * h)], [0.07 * h, 0.05 * h], 6, 1.0), "bark_v9")
            for i in range(4):
                t = i / 4; zb = z0 + h * (0.14 + 0.62 * t); rb = h * (0.24 - 0.15 * t)
                B.add(loft([(zb, rb, rb, x, y), (zb + 0.06 * h, rb * 0.92, rb * 0.92, x, y), (zb + h * (0.30 - 0.06 * t), 0.02, 0.02, x, y)], 7, "flat", "pole"),
                      "pine_dark_v9" if (i + row) % 2 == 0 else "pine_mid_v9")
            x += rnd.uniform(1.0, 1.7)
    return B.build(C)

def shore_rocks(C, seed=5):
    rnd = random.Random(seed); B = Builder("v9_shore_rocks")
    for y0, n, smin, smax in ((-75.0, 90, 0.8, 2.4), (-21.2, 36, 0.3, 0.8)):
        for i in range(n):
            x = (-70 if y0 < -50 else -46) + (140 if y0 < -50 else 92) * (i + rnd.uniform(0, 0.8)) / n; y = y0 + rnd.uniform(-1.0, 1.0); s = rnd.uniform(smin, smax)
            g = ellipsoid((x, y, -0.45 + 0.25 * s), (s, s * rnd.uniform(0.7, 1.0), s * rnd.uniform(0.45, 0.7)), 12, 8)
            B.add(g, "rock_v9" if i % 3 else "rock_dark_v9")
    return B.build(C)

def fence_bushes(C, seed=9, y=-13.0):
    rnd = random.Random(seed); B = Builder("v9_fence_bushes")
    x = -7.2
    while x < 7.3:
        for k in range(rnd.randint(3, 5)):
            r = rnd.uniform(0.22, 0.36); c = (x + rnd.uniform(-0.25, 0.25), y + rnd.uniform(-0.2, 0.25), r * 0.8)
            B.add(ellipsoid(c, (r, r * 0.9, r * 0.85), 12, 8), "bush_v9")
            for f in range(rnd.randint(2, 5)):
                a = rnd.uniform(0, 6.28); e = rnd.uniform(0.2, 1.1)
                fp = (c[0] + math.cos(a) * math.cos(e) * r, c[1] + math.sin(a) * math.cos(e) * r * 0.9, c[2] + math.sin(e) * r * 0.85)
                B.add(ellipsoid(fp, (0.035, 0.035, 0.02), 6, 4), "flower_yellow_v9" if f % 3 else "flower_white_v9")
        x += rnd.uniform(0.55, 0.8)
    return B.build(C)

def field_tufts(C, seed=13):
    rnd = random.Random(seed); B = Builder("v9_field_tufts"); n = 0
    while n < 260:
        x, y = rnd.uniform(-6.6, 6.6), rnd.uniform(-12.0, 5.5)
        if (abs(x) < 1.1 and -5.2 < y < 2.5) or (abs(x) < 2.6 and -7.2 < y < -4.2):
            continue
        s = rnd.uniform(0.12, 0.24); n += 1
        for k in range(9):
            a = rnd.uniform(0, 6.28); lean = rnd.uniform(0.15, 0.45)
            tip = (x + math.cos(a) * lean * s, y + math.sin(a) * lean * s, s * rnd.uniform(0.8, 1.25))
            B.add(sweep([(x, y, 0), (x + (tip[0] - x) * 0.4, y + (tip[1] - y) * 0.4, tip[2] * 0.5), tip], [s * 0.15, s * 0.09, 0.004], 4, 0.5),
                  "tuft_tip_v9" if k % 3 == 0 else "tuft_v9")
    return B.build(C)

def puffy_clouds(C, seed=3):
    rnd = random.Random(seed); B = Builder("v9_clouds")
    for (x, y, z, s) in ((-26, -95, 22, 4.5), (-6, -120, 28, 6.0), (18, -100, 24, 5.0), (38, -130, 30, 6.5), (-44, -125, 27, 5.5), (4, -85, 19, 3.6)):
        for k in range(11):
            r = s * rnd.uniform(0.45, 0.8); c = (x + rnd.uniform(-1.6, 1.6) * s, y + rnd.uniform(-0.4, 0.4) * s, z + rnd.uniform(0.0, 0.7) * s)
            B.add(deform(ellipsoid(c, (r, r * 0.8, r * 0.75), 14, 9), lambda q, z0=z - 0.2 * s: V((q.x, q.y, max(q.z, z0)))), "cloud_v9")
    return B.build(C)

def leafy_bush(B, c, r, seed):
    rnd = random.Random(seed)
    B.add(ellipsoid(c, (r * 0.85, r * 0.8, r * 0.7), 12, 8), "leaf_dark_v9")
    for d in _fib(int(30 * (r / 0.5) ** 2) + 12):
        if d.z < -0.3:
            continue
        p = V(c) + V((d.x * r, d.y * r * 0.9, d.z * r * 0.8)); rs = r * rnd.uniform(0.2, 0.28)
        B.add(ellipsoid(tuple(p), (rs, rs, rs * 0.9), 10, 7), "leaf_light_v9" if d.z > 0.35 else "leaf_mid_v9")

def build_env_v9(Dio):
    """Call after build_scene(): removes v8 scenery and adds the v9 concept scenery."""
    for o in [o for o in bpy.data.objects if o.name.startswith(("tree_", "pine_", "cloud_", "far_shore", "mountains", "sailboat", "bush_6", "twin_", "collision"))
              or o.name.endswith("_soft")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("lake"):
            for i, m in enumerate(o.data.materials):
                o.data.materials[i] = mat("water_v9")
    out = []
    for i, (x, y, h) in enumerate(((-7.6, -15.2, 5.6), (-10.4, -17.2, 6.4), (-5.4, -17.8, 5.0), (7.2, -15.0, 5.8), (10.2, -17.0, 6.6),
                                   (13.2, -14.4, 5.4), (-13.4, -13.8, 5.6), (4.6, -18.4, 4.8), (-7.4, -9.0, 6.2), (7.6, -9.6, 6.0))):
        out.append(popcorn_tree(Dio, "v9_tree_%02d" % i, (x, y, -0.45 if abs(x) > 7 else 0.0), h, 100 + i))
    out += [pine_forest(Dio), shore_rocks(Dio), fence_bushes(Dio), field_tufts(Dio), puffy_clouds(Dio)]
    lake = obj_from_geo("v9_lake", superellipsoid((95, 30, 0.06), 0.25, 0.25, 48, 4, (0, -48.5, -0.44)), "water_v9", Dio); out.append(lake)
    for o in [o for o in bpy.data.objects if o.name.startswith(("bush_8", "rock_4"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    Bf = Builder("v9_foreground_bushes")
    for k, (x, y, r) in enumerate(((1.7, 4.2, 0.55), (-1.6, 4.5, 0.6), (2.4, 5.3, 0.7), (-2.3, 5.6, 0.75), (0.1, 6.4, 0.6))):
        leafy_bush(Bf, (x, y, r * 0.55), r, 400 + k)
    out.append(Bf.build(Dio))
    out += list(build_goal(Dio))
    B = Builder("v9_boat")
    for g, m in boat_parts(1.7):
        B.add(g, m)
    b = B.build(Dio); b.location = (5.5, -30.0, -0.43); b.rotation_euler = (0, 0, math.radians(78)); out.append(b)
    return out


def carpet_tufts(C, seed=17, n=1400):
    """Dense small tufts for a lush lawn read (keeps the ball corridor and crease clear)."""
    rnd = random.Random(seed); B = Builder("v9_carpet_tufts"); k = 0
    while k < n:
        x, y = rnd.uniform(-6.8, 6.8), rnd.uniform(-12.2, 7.5)
        if (abs(x) < 0.9 and -5.2 < y < 2.2) or (math.hypot(x, y + 5.7) < 2.3):
            continue
        s = rnd.uniform(0.05, 0.10); k += 1
        for j in range(4):
            a_ = rnd.uniform(0, 6.28); tip = (x + math.cos(a_) * 0.3 * s, y + math.sin(a_) * 0.3 * s, s * rnd.uniform(0.8, 1.2))
            B.add(sweep([(x, y, 0), tip], [s * 0.16, 0.003], 4, 0.5), "tuft_tip_v9" if j == 0 else "tuft_v9")
    return B.build(C)

def split_rail_fence(C, y=-12.55, x0=-14.0, x1=14.0):
    B = Builder("v9_fence"); x = x0
    while x <= x1 + 1e-3:
        B.add(superellipsoid((0.075, 0.075, 0.58), 0.25, 0.35, 10, 6, (x, y, 0.56)), "bark_v9")
        B.add(superellipsoid((0.085, 0.085, 0.04), 0.3, 0.4, 10, 4, (x, y, 1.15)), "bark_v9")
        x += 2.2
    for z in (0.52, 0.92):
        B.add(superellipsoid(((x1 - x0) / 2 + 0.1, 0.05, 0.065), 0.25, 0.3, 40, 6, ((x0 + x1) / 2, y + 0.07, z)), "bark_v9")
    return B.build(C)

def rock_stacks(C, seed=8, y0=-75.0):
    rnd = random.Random(seed); B = Builder("v9_rock_stacks"); x = -72.0
    while x < 72.0:
        for k in range(rnd.randint(2, 4)):
            s = rnd.uniform(0.5, 1.4); c = (x + rnd.uniform(-1.0, 1.0), y0 + rnd.uniform(-1.2, 1.0), -0.45 + s * rnd.uniform(0.2, 0.5) + k * 0.15)
            B.add(ellipsoid(c, (s * rnd.uniform(1.0, 1.5), s * rnd.uniform(0.7, 1.0), s * rnd.uniform(0.55, 0.8)), 12, 8), rnd.choice(("rock_v9", "rock_v9", "rock_dark_v9")))
        x += rnd.uniform(1.6, 2.6)
    return B.build(C)

def build_v9_gameplay_scene(cam_preset="behind_shooter"):
    """Full v9 lookdev scene: v8 arena base + v9 scenery + v9 characters + concept lighting. Returns the camera."""
    G_ = globals()
    G_["palette_materials"] = lambda *a, **k: {}
    build_arena(False)
    for o in [o for o in bpy.data.objects if o.type == "EMPTY" and o.name in ("camera_markers", "crowd_markers")]:
        for c in list(o.children):
            bpy.data.objects.remove(c, do_unlink=True)
    Dio = bpy.data.collections["Diorama"]
    build_env_v9(Dio)
    for o in [o for o in bpy.data.objects if o.name.startswith(("field_fence", "v9_shore_rocks"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    carpet_tufts(Dio); split_rail_fence(Dio); rock_stacks(Dio)
    for o in [o for o in bpy.data.objects if o.name == "v9_clouds"]:
        bpy.data.objects.remove(o, do_unlink=True)
    Bc = Builder("v9_clouds"); rnd = random.Random(4)
    for (x, y, z, s) in ((-46, -165, 19, 5.0), (-12, -180, 23, 6.0), (22, -170, 20, 5.5), (56, -185, 24, 6.5), (-80, -180, 22, 5.5), (6, -155, 17, 3.6), (84, -175, 20, 5.0)):
        for k in range(12):
            r = s * rnd.uniform(0.45, 0.8); c = (x + rnd.uniform(-1.8, 1.8) * s, y + rnd.uniform(-0.3, 0.3) * s, z + rnd.uniform(0, 0.8) * s)
            Bc.add(deform(ellipsoid(c, (r, r * 0.7, r * 0.72), 14, 9), lambda q, z0=z - 0.1 * s: V((q.x, q.y, max(q.z, z0)))), "cloud_v9")
    Bc.build(Dio)
    for i, (x, y, h) in enumerate(((-12.5, -19.6, 3.4), (-9.6, -20.2, 2.9), (-6.8, -19.8, 3.0), (7.0, -20.1, 2.8), (9.8, -19.6, 3.5), (12.8, -20.3, 3.0))):
        popcorn_tree(Dio, "v9_shore_tree_%02d" % i, (x, y, -0.45), h, 300 + i)
    Bs = Builder("v9_shore_bushes")
    for k in [k_ for k_ in range(18) if abs(-14 + 28 * k_ / 17.0) > 4.5]:
        leafy_bush(Bs, (-14 + 28 * k / 17.0 + random.Random(k).uniform(-0.5, 0.5), -19.0 + random.Random(k + 50).uniform(-0.6, 0.4), -0.2), 0.55, 700 + k)
    Bs.build(Dio)
    C = coll("v9_chars")
    sh = build_skeleton(PLAYER_V9, C, "v9_shooter_rig"); build_character_v9(PLAYER_V9, C, sh, "player")
    build_stick("attack", C, sh, name="v9_shooter_stick", frame_mat="goggle_white", pocket_mat="cage_white")
    calibrate_poles(sh, [GB, AIM_O, AIM_S, QS], "field"); apply_pose(sh, finalize(cradle_pose(0)), "field"); sh.location = (0.72, 1.72, 0.0)
    gk = build_skeleton(GOALIE_V9, C, "v9_goalie_rig"); build_character_v9(GOALIE_V9, C, gk, "goalie")
    build_stick("goalie", C, gk, name="v9_goalie_stick", frame_mat="cage_white", pocket_mat="cage_white")
    calibrate_poles(gk, [GK, READ_L, SAVE_L, SAVE_HL, mirror(SAVE_L)], "goalie"); apply_pose(gk, GK, "goalie")
    gk.location = (0.0, -4.95, 0.0); gk.rotation_euler = (0, 0, math.pi)
    bpy.context.view_layer.update()
    pk = sh.matrix_world @ sh.pose.bones["pocket_01"].head
    ball = obj_from_geo("v9_ball", ellipsoid((0, 0, 0), (0.065, 0.065, 0.065), 20, 14), "goggle_white", C); ball.location = pk + V((0, 0.0, 0.05))
    sc = bpy.context.scene; L = coll("Lookdev"); setup_world()
    for n_ in sc.world.node_tree.nodes:                 # deeper concept-blue sky gradient
        if n_.type == "VALTORGB":
            els = n_.color_ramp.elements
            els[0].color = tuple(_lin3((0.70, 0.84, 0.98))) + (1.0,)
            els[-1].color = tuple(_lin3((0.20, 0.47, 0.92))) + (1.0,)
    sun = bpy.data.lights.new("v9_sun", "SUN"); sun.energy = 5.2; sun.color = (1.0, 0.88, 0.70); sun.angle = math.radians(4.0)
    so = bpy.data.objects.new("v9_sun", sun); L.objects.link(so); so.rotation_euler = (V((0, 0, 0)) - V((-7, 9, 11))).to_track_quat("-Z", "Y").to_euler()
    fill = bpy.data.lights.new("v9_fill", "SUN"); fill.energy = 0.9; fill.color = (0.75, 0.85, 1.0)
    fo = bpy.data.objects.new("v9_fill", fill); L.objects.link(fo); fo.rotation_euler = (V((0, 0, 0)) - V((8, -6, 6))).to_track_quat("-Z", "Y").to_euler()
    setup_eevee(48, (585, 1268)); sc.render.use_stamp = False
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0.25
    try:                                   # soft bloom (compositor API differs between Blender versions; optional)
        if hasattr(sc, "compositing_node_group"):
            ng = bpy.data.node_groups.new("v9_comp", "CompositorNodeTree")
            ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            rl = ng.nodes.new("CompositorNodeRLayers"); gl = ng.nodes.new("CompositorNodeGlare"); go = ng.nodes.new("NodeGroupOutput")
            sc.compositing_node_group = ng
        else:
            sc.use_nodes = True; nt = sc.node_tree
            for n in list(nt.nodes):
                nt.nodes.remove(n)
            ng = nt; rl = nt.nodes.new("CompositorNodeRLayers"); gl = nt.nodes.new("CompositorNodeGlare"); go = nt.nodes.new("CompositorNodeComposite")
        for k_, v_ in (("glare_type", "FOG_GLOW"), ("threshold", 0.8), ("size", 7), ("mix", -0.6)):
            if hasattr(gl, k_):
                setattr(gl, k_, v_)
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs["Image"], go.inputs[0])
    except Exception as e:
        print("bloom skipped:", e)
    presets = {"behind_shooter": ((0.45, 6.9, 2.95), (0.15, -5.5, 0.75), 44, 8.9, None),
               "menu_hero": ((0.9, 4.9, 1.0), (-0.3, -3.0, 0.8), 50, 2.8, ((0.15, 2.3, 0.0), math.radians(165)))}
    loc, tgt, fov, fd, shx = presets[cam_preset]
    if shx is not None:                                   # menu: shooter turned toward camera in the foreground
        sh.location = shx[0]; sh.rotation_euler = (0, 0, shx[1])
        bpy.context.view_layer.update(); ball.location = sh.matrix_world @ sh.pose.bones["pocket_01"].head + V((0, 0, 0.05))
    cam = make_camera("cam_" + cam_preset, loc, tgt, L, vfov_deg=fov)
    return cam, fd


def build_env_v9_export(Dio):
    """Game export version of the v9 scenery (no characters, lighter leaf balls / tufts)."""
    for o in [o for o in bpy.data.objects if o.name.startswith(("twin_",))]:
        bpy.data.objects.remove(o, do_unlink=True)
    build_env_v9(Dio)
    for o in [o for o in bpy.data.objects if o.name.startswith(("goal_frame", "goal_net"))]:      # the goal is its own game asset
        bpy.data.objects.remove(o, do_unlink=True)
    for o in [o for o in bpy.data.objects if o.name.startswith(("field_fence", "v9_shore_rocks", "v9_clouds"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    carpet_tufts(Dio, n=500); split_rail_fence(Dio); rock_stacks(Dio)
    Bc = Builder("v9_clouds"); rnd = random.Random(4)
    for (x, y, z, s) in ((-46, -165, 19, 5.0), (-12, -180, 23, 6.0), (22, -170, 20, 5.5), (56, -185, 24, 6.5), (-80, -180, 22, 5.5), (6, -155, 17, 3.6), (84, -175, 20, 5.0)):
        for k in range(10):
            r = s * rnd.uniform(0.45, 0.8); c = (x + rnd.uniform(-1.8, 1.8) * s, y + rnd.uniform(-0.3, 0.3) * s, z + rnd.uniform(0, 0.8) * s)
            Bc.add(deform(ellipsoid(c, (r, r * 0.7, r * 0.72), 10, 7), lambda q, z0=z - 0.1 * s: V((q.x, q.y, max(q.z, z0)))), "cloud_v9")
    Bc.build(Dio)
    for i, (x, y, h) in enumerate(((-12.5, -19.6, 3.4), (-9.6, -20.2, 2.9), (-6.8, -19.8, 3.0), (7.0, -20.1, 2.8), (9.8, -19.6, 3.5), (12.8, -20.3, 3.0))):
        popcorn_tree(Dio, "v9_shore_tree_%02d" % i, (x, y, -0.45), h, 300 + i)
    Bs = Builder("v9_shore_bushes")
    for k in [k_ for k_ in range(18) if abs(-14 + 28 * k_ / 17.0) > 4.5]:
        leafy_bush(Bs, (-14 + 28 * k / 17.0 + random.Random(k).uniform(-0.5, 0.5), -19.0 + random.Random(k + 50).uniform(-0.6, 0.4), -0.2), 0.55, 700 + k)
    Bs.build(Dio)
