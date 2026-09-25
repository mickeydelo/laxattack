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
        n = int(18 + 60 * (r[0] / (0.36 * h)) ** 2)
        for d in _fib(n):
            if d.z < -0.55:
                continue
            p = V(c) + V((d.x * r[0], d.y * r[1], d.z * r[2])); rs = h * rnd.uniform(0.075, 0.105)
            m = "leaf_light_v9" if d.z > 0.35 else ("leaf_mid_v9" if d.z > -0.2 else "leaf_dark_v9")
            B.add(ellipsoid(tuple(p), (rs, rs, rs * 0.92), 10, 7), m)
    o = B.build(C); o.location = loc; o.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    return o

def pine_forest(C, seed=21):
    rnd = random.Random(seed); B = Builder("v9_pine_forest")
    for row, (y0, hmin, hmax) in enumerate(((-77.0, 7.0, 10.0), (-81.5, 8.0, 12.0), (-86.0, 9.0, 13.5), (-91.0, 10.0, 15.0), (-96.0, 11.0, 16.0))):
        x = -75.0 + rnd.uniform(0, 1.5)
        while x < 75.0:
            h = rnd.uniform(hmin, hmax) * 0.62; y = y0 + rnd.uniform(-1.4, 1.4); z0 = -0.45 + 0.6 * row
            B.add(sweep([(x, y, z0), (x, y, z0 + 0.25 * h)], [0.07 * h, 0.05 * h], 6, 1.0), "bark_v9")
            for i in range(4):
                t = i / 4; zb = z0 + h * (0.14 + 0.62 * t); rb = h * (0.24 - 0.15 * t)
                B.add(loft([(zb, rb, rb, x, y), (zb + 0.06 * h, rb * 0.92, rb * 0.92, x, y), (zb + h * (0.30 - 0.06 * t), 0.02, 0.02, x, y)], 10, "flat", "pole"),
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
    while n < 420:
        x, y = rnd.uniform(-6.6, 6.6), rnd.uniform(-12.0, 5.5)
        if (abs(x) < 1.1 and -5.2 < y < 2.5) or (abs(x) < 2.6 and -7.2 < y < -4.2):
            continue
        s = rnd.uniform(0.12, 0.24); n += 1
        for k in range(9):
            a = rnd.uniform(0, 6.28); lean = rnd.uniform(0.15, 0.45)
            tip = (x + math.cos(a) * lean * s, y + math.sin(a) * lean * s, s * rnd.uniform(0.8, 1.25))
            B.add(sweep([(x, y, 0), (x + (tip[0] - x) * 0.4, y + (tip[1] - y) * 0.4, tip[2] * 0.5), tip], [s * 0.15, s * 0.09, 0.004], 5, 0.5),
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
