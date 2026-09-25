# Lax Attack environment kit: diorama field, goal + net, foliage, rocks, props, lake, mountains, clouds, signs.
# Blender space (Z-up). Game layout: shooter (0.72, 1.72, 0) facing -Y; goal line y = -5.7; goal faces +Y.
GOAL_W, GOAL_H, GOAL_D, PIPE_R = 2.0, 2.0, 2.1, 0.045
GOAL_Y = -5.7

def field_platform(collection, x0=-7.0, x1=7.0, y0=-13.0, y1=6.0, skirt=0.45, stripe=1.6, turf=("turf_a", "turf_b")):
    """Rounded diorama slab: mowed stripes on top, soil cross-section skirt, white markings."""
    B = Builder("field_platform")
    W, L = x1 - x0, y1 - y0
    B.add(superellipsoid((W, L, skirt), 0.12, 0.06, 64, 8, ((x0 + x1) / 2, (y0 + y1) / 2, -skirt / 2 - 0.004)), "soil")
    B.add(superellipsoid((W - 0.2, L - 0.2, 0.05), 0.12, 0.06, 64, 4, ((x0 + x1) / 2, (y0 + y1) / 2, -0.026)), turf[0])
    n = int(L / stripe) + 1
    for i in range(1, n, 2):   # mowing stripes: flat darker bands laid on the base turf (no gaps)
        ya = y0 + 0.1 + i * stripe; yb = min(y1 - 0.1, ya + stripe)
        if yb - ya < 0.05:
            continue
        verts = [(x0 + 0.12, ya, 0.0), (x1 - 0.12, ya, 0.0), (x1 - 0.12, yb, 0.0), (x0 + 0.12, yb, 0.0)]
        B.add((verts, [(0, 1, 2, 3)]), turf[1], smooth=False)
    ob = B.build(collection)
    return ob

def field_markings(collection, crease_r=2.2):
    B = Builder("field_markings")
    z = 0.004
    def strip(p0, p1, w=0.06):
        p0, p1 = V(p0), V(p1); d = (p1 - p0); L = d.length; ang = math.atan2(d.y, d.x)
        g = superellipsoid((L, w, 0.01), 0.2, 0.2, 12, 4, (0, 0, 0))
        return xform(g, Matrix.Translation(((p0 + p1) / 2).to_tuple()[:2] + (z,)) @ Matrix.Rotation(ang, 4, "Z"))
    ring = [(math.cos(2 * math.pi * i / 64) * crease_r, GOAL_Y + math.sin(2 * math.pi * i / 64) * crease_r, z) for i in range(65)]
    B.add(sweep(ring, [0.04] * 65, 6, 0.25, cap0=False, cap1=False), "line_white")
    B.add(strip((-GOAL_W / 2, GOAL_Y), (GOAL_W / 2, GOAL_Y), 0.07), "line_white")
    # shooting arc (restraining / 8-m style arc, stylized)
    arc = [(math.cos(math.radians(a)) * 6.4, GOAL_Y + math.sin(math.radians(a)) * 6.4, z) for a in range(30, 151, 4)]
    B.add(sweep(arc, [0.04] * len(arc), 6, 0.25), "line_white")
    for sx in (-1, 1):
        B.add(strip((6.3 * sx, -12.5), (6.3 * sx, 5.5), 0.07), "line_white")
    # small hash marks + center spot
    for a in range(40, 141, 20):
        p = V((math.cos(math.radians(a)) * 6.4, GOAL_Y + math.sin(math.radians(a)) * 6.4, z))
        q = p + (p - V((0, GOAL_Y, z))).normalized() * 0.35
        B.add(strip(p, q, 0.06), "line_white")
    return B.build(collection)

def goal_geo(detail=1.0):
    """Returns (frame_parts, net_cords, net_meta) in goal space: mouth plane y=0, net toward -Y, x right-left, z up."""
    hw = GOAL_W / 2 + PIPE_R; h = GOAL_H + PIPE_R; d = GOAL_D; r = PIPE_R
    frame = []
    frame.append(sweep([(-hw, 0, 0), (-hw, 0, h), (hw, 0, h), (hw, 0, 0)], [r] * 4, 16, 1.0))
    for sx in (-1, 1):  # posts' rounded corner caps
        frame.append(ellipsoid((hw * sx, 0, h), (r * 1.05,) * 3, 16, 10))
        frame.append(sweep([(hw * sx, 0, r * 0.8), (0.35 * sx, -d, r * 0.8)], [r * 0.8] * 2, 12, 1.0))
        frame.append(superellipsoid((0.16, 0.16, 0.05), 0.4, 0.4, 16, 6, (hw * sx, 0, 0.025)))
    frame.append(sweep([(-0.35, -d, r * 0.8), (0.35, -d, r * 0.8)], [r * 0.8] * 2, 12, 1.0))
    # net: pyramid-ish: mouth rectangle -> rear bar on ground; side, top, back faces as cord grids
    rim_mouth = lambda u, v: V((-GOAL_W / 2 + GOAL_W * u, -0.02, GOAL_H * v))
    def net_pt(u, v, w):  # u across 0..1, v up 0..1, w depth 0..1 (0 mouth, 1 rear)
        m = rim_mouth(u, v)
        rear = V(((-0.35 + 0.7 * u), -d, 0.03 + 0.05 * v))
        sag = 0.10 * math.sin(math.pi * w) * (1 - abs(2 * u - 1) * 0.5)
        return m.lerp(rear, w) + V((0, 0, -sag))
    cords = []; rad = 0.012 if detail <= 1.0 else 0.0095
    N = int(12 * detail)
    def line(pts):
        cords.append(sweep(pts, [rad] * len(pts), 5, 1.0, cap0=False, cap1=False))
    for k in range(1, N):  # lines from mouth rim to rear across top (u varies), sides (v varies)
        t = k / N
        line([tuple(net_pt(t, 1.0, w / 8)) for w in range(9)])
        line([tuple(net_pt(0.0, t, w / 8)) for w in range(9)])
        line([tuple(net_pt(1.0, t, w / 8)) for w in range(9)])
    NR = int(8 * detail)
    for j in range(1, NR):  # rings at constant depth
        w = j / NR
        ringpts = [tuple(net_pt(0.0, v / 6, w)) for v in range(0, 7)] + [tuple(net_pt(u / 8, 1.0, w)) for u in range(1, 8)] + [tuple(net_pt(1.0, v / 6, w)) for v in range(6, -1, -1)]
        line(ringpts)
    meta = dict(mouth_w=GOAL_W, mouth_h=GOAL_H, depth=d, pipe_r=r)
    return frame, cords, meta, net_pt

def build_goal(collection, loc=(0, GOAL_Y, 0), name="goal", pipe_mat="goal_orange"):
    frame, cords, meta, net_pt = goal_geo()
    Bf = Builder(name + "_frame")
    for g in frame:
        Bf.add(g, pipe_mat)
    of = Bf.build(collection); of.location = loc
    Bn = Builder(name + "_net")
    for g in cords:
        Bn.add(g, "cord_white")
    on = Bn.build(collection); on.location = loc
    return of, on

def pine(seed, h=3.0, collection=None, tiers=4, loc=(0, 0, 0), name=None, mat_="pine"):
    rnd = random.Random(seed)
    B = Builder(name or "pine_%d" % seed)
    B.add(sweep([(0, 0, 0), (0, 0, h * 0.35)], [h * 0.06, h * 0.045], 8, 1.0), "bark")
    for i in range(tiers):
        t = i / tiers
        zb = h * (0.18 + 0.72 * t); top = zb + h * (0.36 - 0.08 * t)
        rb = h * (0.34 - 0.22 * t) * rnd.uniform(0.92, 1.05)
        def scallop(q, rb=rb, zb=zb):
            a = math.atan2(q.y, q.x); rr = math.hypot(q.x, q.y)
            k = 1 + 0.10 * math.sin(7 * a + i)
            droop = -0.08 * h * (rr / rb) ** 3
            return V((q.x * k, q.y * k, q.z + droop))
        g = loft([(zb, rb * 0.4, rb * 0.4), (zb - 0.02 * h, rb, rb), (zb + 0.03 * h, rb * 0.95, rb * 0.95),
                  (zb + (top - zb) * 0.55, rb * 0.42, rb * 0.42), (top, 0.02, 0.02)], 21, "flat", "pole")
        B.add(deform(g, scallop), mat_)
    ob = B.build(collection); ob.location = loc
    ob.rotation_euler.z = rnd.uniform(0, 6.28)
    return ob

def blob_cluster(seed, center, size, n=5, mats=("foliage_a", "foliage_b"), useg=18, vseg=10):
    rnd = random.Random(seed); out = []
    for i in range(n):
        off = V((rnd.uniform(-1, 1) * size[0] * 0.45, rnd.uniform(-1, 1) * size[1] * 0.45, rnd.uniform(-0.2, 1) * size[2] * 0.35))
        r = V((size[0] * rnd.uniform(0.35, 0.5), size[1] * rnd.uniform(0.35, 0.5), size[2] * rnd.uniform(0.32, 0.42)))
        g = ellipsoid(V(center) + off, r, useg, vseg)
        def bumpy(q, c=V(center) + off, r=r, ph=rnd.uniform(0, 6)):
            d = q - c
            a = math.atan2(d.y, d.x); e = d.z / max(r.z, 1e-3)
            k = 1 + 0.07 * math.sin(5 * a + ph) * math.cos(3 * e) + 0.05 * math.sin(11 * a + 2 * ph) * math.cos(6 * e + ph)
            d = V((d.x * k, d.y * k, d.z * (0.85 if d.z < 0 else 1.0)))
            return c + d
        out.append((deform(g, bumpy), mats[i % len(mats)]))
    return out

def deciduous(seed, h=3.2, collection=None, loc=(0, 0, 0), name=None, mats=("leaf_a", "leaf_b", "leaf_c"), n=8):
    rnd = random.Random(seed)
    B = Builder(name or "tree_%d" % seed)
    B.add(sweep([(0, 0, 0), (0.02 * h, 0, h * 0.35), (0, 0.03 * h, h * 0.55)], [h * 0.07, h * 0.05, h * 0.035], 9, 1.0), "bark")
    for sx in (-1, 1):
        B.add(sweep([(0.01 * h, 0, h * 0.38), (0.14 * h * sx, 0.02 * h, h * 0.55)], [h * 0.03, h * 0.015], 7, 1.0), "bark")
    for g, m in blob_cluster(seed, (0, 0, h * 0.66), (h * 0.78, h * 0.70, h * 0.56), n, mats, 20, 12):
        B.add(g, m)
    ob = B.build(collection); ob.location = loc
    return ob

def bush(seed, s=0.6, collection=None, loc=(0, 0, 0), mats=("leaf_a", "leaf_b", "leaf_c")):
    B = Builder("bush_%d" % seed)
    for g, m in blob_cluster(seed, (0, 0, s * 0.32), (s, s * 0.9, s * 0.7), 5, mats, 14, 8):
        B.add(g, m)
    ob = B.build(collection); ob.location = loc
    return ob

def rock(seed, size=(0.5, 0.4, 0.35), collection=None, loc=(0, 0, 0), m="rock"):
    ob = obj_from_geo("rock_%d" % seed, hull_rock(seed, size), m, collection, loc)
    ob.rotation_euler.z = seed * 1.3
    return ob

def grass_tuft(seed, collection=None, loc=(0, 0, 0), s=0.25):
    rnd = random.Random(seed); B = Builder("grass_%d" % seed)
    for i in range(6):
        a = rnd.uniform(0, 6.28); lean = rnd.uniform(0.1, 0.35)
        tip = (math.cos(a) * lean * s, math.sin(a) * lean * s, s * rnd.uniform(0.7, 1.1))
        B.add(sweep([(0, 0, 0), (tip[0] * 0.4, tip[1] * 0.4, tip[2] * 0.55), tip], [s * 0.07, s * 0.05, 0.002], 5, 0.45), "foliage_b" if i % 2 else "foliage_a")
    ob = B.build(collection); ob.location = loc
    return ob

def wooden_sign(text, collection=None, loc=(0, 0, 0), w=1.3, h=0.55, post_h=0.9, rot=0.0, text_size=0.17, name="sign"):
    B = Builder(name)
    for sx in (-1, 1):
        B.add(superellipsoid((0.08, 0.08, post_h + h * 0.6), 0.3, 0.3, 10, 6, (sx * w * 0.38, 0, (post_h + h * 0.6) / 2)), "wood_dark")
    B.add(superellipsoid((w, 0.07, h), 0.25, 0.25, 24, 8, (0, 0, post_h + h / 2)), "wood")
    B.add(superellipsoid((w * 0.9, 0.02, h * 0.78), 0.2, 0.2, 24, 6, (0, -0.036, post_h + h / 2)), "sign_paint")
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        tv = text_mesh(name + "_t%d" % i, ln, text_size, collection, 0.012)
        zc = post_h + h / 2 + (len(lines) - 1) * text_size * 0.55 - i * text_size * 1.1
        B.add(xform(tv, Matrix.Translation((0, -0.05, zc)) @ Matrix.Rotation(math.radians(90), 4, "X")), "kit_navy")
    ob = B.build(collection); ob.location = loc; ob.rotation_euler.z = rot
    return ob

def board_wall(collection, x0, x1, y, h=0.55, name="boards", accent="kit_blue", rot=0.0):
    B = Builder(name); L = x1 - x0; n = max(1, int(L / 1.6))
    for i in range(n):
        xa = x0 + i * L / n; xb = xa + L / n
        B.add(superellipsoid((L / n - 0.06, 0.12, h), 0.25, 0.3, 16, 8, ((xa + xb) / 2, y, h / 2)), accent if i % 2 == 0 else "kit_white")
        B.add(superellipsoid((0.1, 0.16, h + 0.06), 0.3, 0.3, 8, 6, (xa, y, (h + 0.06) / 2)), "wood")
    B.add(superellipsoid((L, 0.18, 0.06), 0.3, 0.3, 32, 4, ((x0 + x1) / 2, y, h + 0.03)), "wood")
    ob = B.build(collection); ob.rotation_euler.z = rot
    return ob

def bench(collection, loc, L=2.0, rot=0.0):
    B = Builder("bench")
    B.add(superellipsoid((L, 0.34, 0.07), 0.25, 0.3, 20, 6, (0, 0, 0.42)), "wood")
    B.add(superellipsoid((L, 0.06, 0.26), 0.25, 0.3, 20, 6, (0, 0.17, 0.68)), "kit_blue")
    for sx in (-1, 1):
        B.add(superellipsoid((0.08, 0.3, 0.42), 0.3, 0.3, 8, 6, (sx * L * 0.42, 0, 0.21)), "metal_silver")
    ob = B.build(collection); ob.location = loc; ob.rotation_euler.z = rot
    return ob

def bleacher(collection, loc, L=4.0, rows=3, rot=0.0):
    B = Builder("bleacher")
    for i in range(rows):
        B.add(superellipsoid((L, 0.45, 0.08), 0.25, 0.3, 24, 6, (0, i * 0.45, 0.42 + i * 0.36)), "wood")
        B.add(superellipsoid((L, 0.05, 0.36), 0.25, 0.3, 24, 6, (0, i * 0.45 - 0.2, 0.22 + i * 0.36)), "kit_white" if i % 2 else "kit_blue")
    for sx in (-1, 0, 1):
        B.add(sweep([(sx * L * 0.46, -0.2, 0), (sx * L * 0.46, (rows - 1) * 0.45 + 0.2, 0.42 + (rows - 1) * 0.36)], [0.04, 0.04], 8, 1.0), "metal_silver")
    ob = B.build(collection); ob.location = loc; ob.rotation_euler.z = rot
    return ob

def lake(collection, center, size, seed=3):
    rnd = random.Random(seed); B = Builder("lake")
    def blob(r):
        return [(center[0] + size[0] / 2 * r * (1 + 0.08 * math.sin(3 * a + seed)) * math.cos(a),
                 center[1] + size[1] / 2 * r * (1 + 0.08 * math.cos(2 * a)) * math.sin(a)) for a in [2 * math.pi * i / 48 for i in range(48)]]
    def disc(r, z, m, th):
        pts = blob(r); verts = [(x, y, z) for x, y in pts] + [(x, y, z - th) for x, y in pts] + [(center[0], center[1], z), (center[0], center[1], z - th)]
        n = len(pts); f = []
        for i in range(n):
            j = (i + 1) % n
            f += [(i, j, 2 * n), (n + j, n + i, 2 * n + 1), (i, n + i, n + j, j)]
        B.add((verts, f), m, smooth=False)
    disc(1.08, 0.0, "sand", 0.3); disc(1.0, 0.012, "water_shallow", 0.05); disc(0.86, 0.02, "water", 0.05)
    ob = B.build(collection)
    return ob

def dock(collection, loc, L=3.0, rot=0.0):
    B = Builder("dock")
    for i in range(int(L / 0.3)):
        B.add(superellipsoid((1.0, 0.26, 0.06), 0.3, 0.3, 10, 4, (0, i * 0.3, 0.25)), "wood" if i % 2 else "wood_dark")
    for sx in (-1, 1):
        for k in range(3):
            B.add(sweep([(sx * 0.45, k * L / 2.2, -0.2), (sx * 0.45, k * L / 2.2, 0.35)], [0.05, 0.05], 8, 1.0), "wood_dark")
    ob = B.build(collection); ob.location = loc; ob.rotation_euler.z = rot
    return ob

def sailboat(collection, loc, s=1.0):
    B = Builder("sailboat")
    B.add(superellipsoid((0.5 * s, 1.4 * s, 0.25 * s), 0.6, 0.35, 18, 8, (0, 0, 0.1 * s)), "kit_white")
    B.add(sweep([(0, 0, 0.2 * s), (0, 0, 1.6 * s)], [0.02 * s, 0.02 * s], 6, 1.0), "wood_dark")
    B.add(([(0, 0.05 * s, 0.3 * s), (0, 0.05 * s, 1.55 * s), (0, 0.75 * s, 0.35 * s)], [(0, 1, 2)]), "accent_coral", smooth=False)
    B.add(([(0, -0.05 * s, 0.35 * s), (0, -0.05 * s, 1.3 * s), (0, -0.6 * s, 0.35 * s)], [(0, 2, 1)]), "kit_white", smooth=False)
    ob = B.build(collection); ob.location = loc
    return ob

def mountain_range(collection, y, x0, x1, h, seed, m="mountain", snow=True, depth=6.0, name="mountains"):
    rnd = random.Random(seed); B = Builder(name)
    x = x0
    while x < x1:
        w = rnd.uniform(0.8, 1.4) * h * 1.6; hh = h * rnd.uniform(0.7, 1.15)
        g = loft([(0, w / 2, depth / 2), (hh * 0.55, w * 0.28, depth * 0.3), (hh * 0.85, w * 0.1, depth * 0.1), (hh, 0.05, 0.05)], 12, "flat", "pole")
        g = deform(g, lambda q, xx=x, yy=y: V((q.x + xx, q.y + yy, q.z)))
        B.add(g, m, smooth=True)
        if snow:
            sg = loft([(hh * 0.70, w * 0.19, depth * 0.205), (hh * 0.85, w * 0.105, depth * 0.105), (hh * 1.01, 0.06, 0.06)], 12, "flat", "pole")
            B.add(deform(sg, lambda q, xx=x, yy=y: V((q.x + xx, q.y + yy - 0.01, q.z + 0.01))), "snow")
        x += w * 0.55
    return B.build(collection)

def cloud(seed, collection, loc, s=1.0):
    B = Builder("cloud_%d" % seed)
    for g, m in blob_cluster(seed, (0, 0, 0), (3.0 * s, 1.2 * s, 1.1 * s), 6, ("cloud",), 16, 10):
        B.add(deform(g, lambda q: V((q.x, q.y, max(q.z, -0.18 * s)))), m)
    ob = B.build(collection); ob.location = loc
    return ob

def props_bag(collection, loc, rot=0.0):
    B = Builder("equipment_bag")
    B.add(superellipsoid((0.75, 0.34, 0.32), 0.45, 0.6, 20, 10, (0, 0, 0.16)), "kit_navy")
    B.add(sweep([(-0.25, 0, 0.3), (0, 0, 0.44), (0.25, 0, 0.3)], [0.025] * 3, 6, 1.0), "rubber_dark")
    B.add(superellipsoid((0.5, 0.345, 0.07), 0.3, 0.3, 16, 4, (0, 0, 0.18)), "kit_white")
    ob = B.build(collection); ob.location = loc; ob.rotation_euler.z = rot
    return ob

def props_bottle(collection, loc, m="accent_teal"):
    B = Builder("bottle")
    B.add(loft([(0, 0.045, 0.045), (0.2, 0.047, 0.047), (0.23, 0.03, 0.03)], 14, "flat", None), m)
    B.add(loft([(0.23, 0.028, 0.028), (0.27, 0.025, 0.025)], 12, None, "flat"), "plastic_white")
    ob = B.build(collection); ob.location = loc
    return ob

def props_balls(collection, pts, r=None):
    r = BALL_R if r is None else r
    B = Builder("balls")
    for p in pts:
        B.add(ball_geo((p[0], p[1], r), r), "ball")
    return B.build(collection)

def fence(collection, x0, x1, y, h=0.7, rot=0.0):
    B = Builder("fence"); n = int((x1 - x0) / 0.9) + 1
    for i in range(n):
        x = x0 + i * (x1 - x0) / (n - 1)
        B.add(superellipsoid((0.09, 0.09, h), 0.35, 0.35, 8, 6, (x, y, h / 2)), "wood")
    for z in (h * 0.45, h * 0.85):
        B.add(superellipsoid((x1 - x0, 0.05, 0.07), 0.3, 0.3, 24, 4, ((x0 + x1) / 2, y + 0.05, z)), "wood_dark")
    ob = B.build(collection); ob.rotation_euler.z = rot
    return ob

def rail_fence(collection, pts, h=0.8, spacing=1.6, name="rail_fence"):
    """Rustic post-and-rail fence along a polyline (Blender XY)."""
    B = Builder(name)
    P = [V((x, y, 0)) for x, y in pts]
    for a, b in zip(P, P[1:]):
        d = b - a; n = max(1, int(d.length / spacing))
        for i in range(n + 1):
            q = a + d * (i / n)
            B.add(superellipsoid((0.13, 0.13, h + 0.08), 0.35, 0.35, 8, 6, (q.x, q.y, (h + 0.08) / 2)), "wood_dark" if i % 2 else "wood")
        for z in (h * 0.5, h * 0.9):
            B.add(sweep([(a.x, a.y, z), (b.x, b.y, z)], [0.045, 0.045], 8, 0.7), "wood")
    return B.build(collection)

def shore_rocks(collection, x0, x1, y, seed=11, n=18):
    rnd = random.Random(seed); B = Builder("shore_rocks")
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rnd.uniform(0, 0.8)) / n
        sz = (rnd.uniform(0.6, 1.4), rnd.uniform(0.5, 1.0), rnd.uniform(0.35, 0.8))
        v, f = hull_rock(seed * 100 + i, sz)
        B.add(([(p[0] + x, p[1] + y + rnd.uniform(-0.6, 0.6), p[2] - 0.5) for p in v], f), "rock_warm" if i % 3 else "rock")
    return B.build(collection)

def far_shore(collection, y, x0, x1, seed=21, h=6.0, name="far_shore"):
    """Forested far shore: overlapping canopy blobs on a low bank (cheap, reads as distant woods)."""
    rnd = random.Random(seed); B = Builder(name)
    B.add(superellipsoid((x1 - x0, 8.0, 1.2), 0.3, 0.3, 32, 6, ((x0 + x1) / 2, y, -0.3)), "leaf_c")
    x = x0
    while x < x1:
        s = rnd.uniform(0.7, 1.3) * h
        for g, m in blob_cluster(rnd.randint(0, 9999), (x, y + rnd.uniform(-2, 2), s * 0.35), (s * 1.3, s, s * 0.9), 3, ("leaf_c", "leaf_a", "pine"), 12, 8):
            B.add(g, m)
        x += s * 0.9
    return B.build(collection)

def banner(collection, loc, text, w=1.6, h=0.5, m="kit_blue"):
    B = Builder("banner")
    for sx in (-1, 1):
        B.add(sweep([(sx * w / 2, 0, 0), (sx * w / 2, 0, 1.3 + h)], [0.025, 0.025], 6, 1.0), "metal_silver")
    B.add(superellipsoid((w, 0.02, h), 0.15, 0.15, 20, 4, (0, 0, 1.3 + h / 2)), m)
    tv = text_mesh("banner_t", text, h * 0.42, collection, 0.008)
    B.add(xform(tv, Matrix.Translation((0, -0.02, 1.3 + h / 2)) @ Matrix.Rotation(math.radians(90), 4, "X")), "kit_white")
    ob = B.build(collection); ob.location = loc
    return ob
