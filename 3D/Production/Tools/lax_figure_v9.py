# Lax Attack v9 look (Phase A): matches the approved turnaround concepts (female #10 field player, female #2 goalie).
# Body/kit come from the existing builder (colours per concept); head, face, hair and headgear are rebuilt here.
# Bone names are unchanged so every animation clip still works.
def _lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
_SRGB = {   # concept colours (sRGB) -> linear shader values
    "skin_v9": ((0.95, 0.72, 0.55), 0.36, 0.25), "hair_v9": ((0.40, 0.22, 0.12), 0.30, 0.35), "eye_v9": ((0.16, 0.09, 0.05), 0.08, 0.6),
    "eye_hi_v9": ((1.0, 1.0, 1.0), 0.2, 0.0), "brow_v9": ((0.30, 0.16, 0.09), 0.5, 0.0), "mouth_v9": ((0.55, 0.22, 0.18), 0.4, 0.0),
    "blush_v9": ((0.98, 0.66, 0.60), 0.5, 0.0), "goggle_white": ((0.96, 0.94, 0.89), 0.18, 0.4), "strap_dark": ((0.16, 0.16, 0.17), 0.5, 0.0),
    "tie_cream": ((0.97, 0.94, 0.87), 0.3, 0.2), "helmet_navy_v9": ((0.10, 0.17, 0.33), 0.22, 0.5), "helmet_vent": ((0.04, 0.06, 0.12), 0.6, 0.0),
    "helmet_cyan": ((0.13, 0.72, 0.88), 0.22, 0.5), "cage_white": ((0.95, 0.95, 0.93), 0.2, 0.3), "kit_cream_v9": ((0.96, 0.93, 0.86), 0.55, 0.0),
    "kit_red_v9": ((0.86, 0.27, 0.23), 0.45, 0.1), "kit_navy_v9": ((0.10, 0.17, 0.32), 0.45, 0.1), "kit_cyan_v9": ((0.14, 0.72, 0.88), 0.40, 0.1),
    "sock_white_v9": ((0.97, 0.97, 0.96), 0.7, 0.0), "cleat_white_v9": ((0.98, 0.98, 0.97), 0.25, 0.3),
}
V9_MATS = {k: (_lin(c), r, 0.0, co) for k, (c, r, co) in _SRGB.items()}
MATS.update(V9_MATS)

def _interp(table, x):
    x = abs(x)
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0); t = t * t * (3 - 2 * t)
            return y0 + (y1 - y0) * t
    return table[-1][1]

def hair_cap(H, boundary, base=1.045, grooves=30, depth=0.011, part=True, back_bulge=0.03, useg=96, vseg=24):
    verts, faces = [], []
    azs = [-180 + 360.0 * i / useg for i in range(useg)]
    for j in range(vseg + 1):
        for az in azs:
            el0 = boundary(az); t = j / vseg; el = el0 + (89.2 - el0) * (t ** 0.85)
            ridge = (0.5 - 0.5 * math.cos(grooves * math.radians(az))) ** 0.7
            fade = 1.0 - smoothstep(72, 89, el)
            dip = (0.024 * math.exp(-(az / 6.5) ** 2) * smoothstep(el0 + 1, el0 + 8, el) * (1 - smoothstep(78, 89, el))) if part else 0.0
            bulge = back_bulge * smoothstep(80, 180, abs(az)) * math.sin(math.pi * min(1.0, max(0.0, (el + 40) / 110.0)))
            verts.append(H.point(az, el, base + bulge + depth * ridge * fade - dip))
    for j in range(vseg):
        for i in range(useg):
            a = j * useg + i; b = j * useg + (i + 1) % useg
            faces.append((a, b, b + useg, a + useg))
    top = len(verts); verts.append(H.point(0, 90, base))
    for i in range(useg):
        a = vseg * useg + i; b = vseg * useg + (i + 1) % useg; faces.append((a, b, top))
    rim = [H.point(az, boundary(az) + 0.8, base - 0.004) for az in range(-180, 181, 6)]
    return (verts, faces), rim

def lobe(c, r, n_axis, ridges=7, depth=0.08, seg=(18, 12)):
    n = V(n_axis).normalized(); a = n.orthogonal().normalized(); b = n.cross(a)
    def f(q):
        d = q - V(c); ax = d.dot(n); rad = d - n * ax
        th = math.atan2(rad.dot(b), rad.dot(a))
        k = 1.0 + depth * (abs(math.sin(ridges * th * 0.5)) ** 0.6 - 0.5)
        return V(c) + n * ax + rad * k
    return deform(ellipsoid(c, r, seg[0], seg[1]), f)

def v9_face(s, H, F):
    ew, eh = 0.031, 0.046
    for side, sx in (("L", 1), ("R", -1)):
        az, el = 25.0 * sx, -11.0
        F.add(H.place(ellipsoid((0, 0, 0), (ew, 0.005, eh), 26, 16), az, el, -0.001), "eye_v9", "eye_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.011, 0.0025, 0.014), 12, 8), az + 2.8, el + 4.0, 0.0035), "eye_hi_v9", "eye_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.0055, 0.0025, 0.0055), 8, 5), az - 3.4, el - 6.0, 0.0035), "eye_hi_v9", "eye_" + side)
        dA = math.degrees(ew / H.r.x) * 1.3 + 2; dE = math.degrees(eh / H.r.z) + 2
        lo = math.degrees(eh / H.r.z) * 2 + 4
        F.add(surface_patch(H, az - dA, az + dA, el - dE + lo, el + dE + lo, 0.0042), s["skin"], "lid_" + side)
        bpts = [H.point(az + dx * sx, el + 17.5 + 1.2 - 0.03 * dx * dx) for dx in (-7, -2, 3, 8)]
        bpts = [tuple(V(q) + (V(q) - H.c).normalized() * 0.0035) for q in bpts]
        F.add(sweep(bpts, [0.0035, 0.0052, 0.005, 0.003], 8, 0.5), "brow_v9", "brow_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.038, 0.004, 0.023), 14, 6), 38 * sx, -24.0, -0.0015), "blush_v9", "head")
    mw = 0.028; mel = -30.0
    def mouth_shape(q):
        x = q.x / mw; z = q.z
        return V((q.x, q.y, z * (1.0 if z < 0 else 0.25) + 0.010 * x * x))
    mouth = deform(ellipsoid((0, 0, 0), (mw * 1.1, 0.004, 0.040), 22, 12), mouth_shape)
    def mouth_w(p):
        loc = p - H.point(0, mel)
        wl = smoothstep(0.010, mw * 0.95, loc.x); wr = smoothstep(0.010, mw * 0.95, -loc.x)
        return {"head": max(0.0, 1 - wl - wr), "mouth_L": wl, "mouth_R": wr}
    F.add(H.place(mouth, 0, mel, -0.002), "mouth_v9", weights=mouth_w)
    mA = math.degrees(mw * 1.1 / H.r.x) * 1.25 + 2
    F.add(surface_patch(H, -mA, mA, mel - 11.0, mel + 1.4, 0.0038), s["skin"], "jaw")

def v9_hair_player(s, H, Hb):
    bnd = lambda az: _interp([(0, 30), (14, 26), (34, 15), (56, 6), (80, 2), (100, -14), (130, -32), (180, -42)], az)
    cap, rim = hair_cap(H, bnd, base=1.065, grooves=24, depth=0.034, part=True, back_bulge=0.06)
    Hb.add(cap, "hair_v9", "head"); Hb.add(sweep(rim, [0.012] * len(rim), 8, 1.0, cap0=False, cap1=False), "hair_v9", "head")
    for sx in (1, -1):   # swept bangs: from the centre part down and out across the forehead to the temples
        for k_, (e0, a1, e1, rr) in enumerate(((44, 30, 24, 0.034), (40, 42, 14, 0.030))):
            pts = [H.point(3 * sx, e0, 1.07), H.point(14 * sx, e0 - 8, 1.085), H.point(a1 * sx, e1 + 2, 1.085), H.point((a1 + 12) * sx, e1 - 8, 1.07)]
            Hb.add(sweep(pts, [rr, rr * 1.05, rr * 0.8, rr * 0.3], 12, 0.45), "hair_v9", "head")
    for sx in (1, -1):   # flowing locks: in front of the ears and just behind them
        pts = [H.point(60 * sx, 16, 1.06), H.point(68 * sx, -4, 1.07), H.point(70 * sx, -24, 1.065), H.point(66 * sx, -40, 1.055), H.point(62 * sx, -48, 1.05)]
        Hb.add(sweep(pts, [0.030, 0.030, 0.024, 0.014, 0.004], 12, 0.5), "hair_v9", "head")
        pts = [H.point(104 * sx, 4, 1.07), H.point(108 * sx, -20, 1.075), H.point(104 * sx, -40, 1.06)]
        Hb.add(sweep(pts, [0.034, 0.028, 0.006], 12, 0.5), "hair_v9", "head")
    c = V(H.point(152, -22, 1.24)); n = (c - H.c).normalized()
    for off, r in (((0, 0, 0), 0.13), ((0.055, 0.04, -0.08), 0.10), ((-0.05, 0.06, -0.075), 0.094), ((0.03, 0.085, 0.04), 0.088), ((0.0, 0.03, -0.15), 0.078), ((-0.06, 0.025, 0.05), 0.082)):
        cc = c + V(off)
        Hb.add(lobe(tuple(cc), (r, r * 0.95, r * 0.9), tuple((cc - H.c).normalized()), ridges=8, depth=0.10), "hair_v9", "head")
    tie_c = V(H.point(152, -14, 1.11))
    Hb.add(torus(tuple(tie_c), 0.058, 0.016, 20, 8, "Y"), "tie_cream", "head")

def v9_goggles(s, H, G):
    def gp(az, el, off=0.032):
        p, tx, n, tu = H.frame(az, el); return tuple(p + n * off)
    loop = []
    for i in range(48):   # one wide rounded mask frame around both eyes
        t = 2 * math.pi * i / 48; c, sn = math.cos(t), math.sin(t)
        az = 44.0 * math.copysign(abs(c) ** 0.6, c); el = -6.5 + 14.5 * math.copysign(abs(sn) ** 0.75, sn) - 2.5 * (1 - abs(c)) * (sn < 0)
        loop.append(gp(az, el, 0.030 + 0.006 * (1 - abs(c))))
    loop.append(loop[0])
    G.add(sweep(loop, [0.0125] * len(loop), 10, 1.0, cap0=False, cap1=False), "goggle_white", "head")
    G.add(sweep([gp(0, 8.0, 0.036), gp(0, -1.0, 0.040), gp(0, -10.0, 0.038)], [0.0105, 0.010, 0.0105], 8, 1.0), "goggle_white", "head")
    G.add(sweep([gp(-40, 1.5, 0.036), gp(-20, 3.0, 0.040), gp(0, 3.5, 0.041), gp(20, 3.0, 0.040), gp(40, 1.5, 0.036)], [0.0075] * 5, 8, 1.0), "goggle_white", "head")
    for sx in (1, -1):
        G.add(superellipsoid((0.014, 0.024, 0.030), 0.45, 0.45, 10, 6, gp(48 * sx, -4, 0.022)), "goggle_white", "head")
    strap = [H.point(a, -2 + 10 * smoothstep(80, 180, abs(a)), 1.075) for a in list(range(52, 181, 12)) + list(range(-180, -51, 12))]
    G.add(sweep(strap, [0.010] * len(strap), 6, 2.6), "strap_dark", "head")
    G.add(superellipsoid((0.030, 0.012, 0.020), 0.4, 0.4, 10, 5, tuple(H.point(180, 8, 1.11))), "goggle_white", "head")

def v9_hair_goalie(s, H, Hb):
    bnd = lambda az: _interp([(0, 30), (30, 24), (60, 4), (95, -20), (140, -40), (180, -46)], az)
    cap, rim = hair_cap(H, bnd, base=1.04, grooves=26, depth=0.018, part=True, back_bulge=0.02)
    Hb.add(cap, "hair_v9", "head"); Hb.add(sweep(rim, [0.011] * len(rim), 8, 1.0, cap0=False, cap1=False), "hair_v9", "head")
    for sx in (1, -1):
        pts = [H.point(52 * sx, 18, 1.05), H.point(58 * sx, 0, 1.055), H.point(58 * sx, -18, 1.05)]
        Hb.add(sweep(pts, [0.022, 0.02, 0.006], 10, 0.55), "hair_v9", "head")
    c = V(H.point(160, -52, 1.14))
    for off, r in (((0, 0, 0), 0.10), ((0.06, 0.02, 0.02), 0.08), ((-0.06, 0.02, 0.01), 0.078), ((0.03, 0.05, -0.06), 0.07), ((-0.035, 0.05, -0.065), 0.068), ((0, 0.07, 0.03), 0.065)):
        cc = c + V(off)
        Hb.add(lobe(tuple(cc), (r, r * 0.95, r * 0.9), tuple((cc - H.c).normalized()), ridges=8, depth=0.10), "hair_v9", "head")

def _oriented(H, az, el, radii, off, geo=None):
    p, tx, n, tu = H.frame(az, el)
    R = Matrix((tuple(tx), tuple(n), tuple(tu))).transposed().to_4x4()
    return xform(geo or ellipsoid((0, 0, 0), radii, 14, 7), Matrix.Translation(tuple(V(p) + V(n) * off)) @ R)

def v9_helmet(s, H, G):
    bnd = lambda az: _interp([(0, 27), (46, 25), (60, -8), (78, -40), (130, -38), (180, -30)], az)
    SH = 1.10
    def shell_sc(az, el):   # elongated toward the back, slightly flattened crown
        el0 = bnd(az); t = max(0.0, min(1.0, (el - el0) / (89.0 - el0)))
        return SH + 0.06 * smoothstep(80, 180, abs(az)) * (1 - t) ** 0.6 - 0.03 * smoothstep(62, 89, el) + 0.012 * smoothstep(20, 60, abs(az)) * (1 - t)
    useg, vseg = 96, 22; verts, faces = [], []
    azs = [-180 + 360.0 * i / useg for i in range(useg)]
    for j in range(vseg + 1):
        for az in azs:
            el0 = bnd(az); t = j / vseg; el = el0 + (89.0 - el0) * (t ** 0.85)
            verts.append(H.point(az, el, shell_sc(az, el)))
    for j in range(vseg):
        for i in range(useg):
            a = j * useg + i; b = j * useg + (i + 1) % useg; faces.append((a, b, b + useg, a + useg))
    top = len(verts); verts.append(H.point(0, 90, SH))
    for i in range(useg):
        a = vseg * useg + i; b = vseg * useg + (i + 1) % useg; faces.append((a, b, top))
    G.add((verts, faces), "helmet_navy_v9", "head")
    rim = [H.point(az, bnd(az) + 0.5, SH + 0.005) for az in range(-180, 181, 5)]
    G.add(sweep(rim, [0.017] * len(rim), 8, 1.0, cap0=False, cap1=False), "helmet_navy_v9", "head")
    # wide raised cyan centre band (front brow -> crown -> back)
    def band(az_c, el0, el1, w=12.0, nu=8, nv=18):          # raised strip hugging the shell, edges tapered into it
        verts, faces = [], []
        for j in range(nv + 1):
            el = el0 + (el1 - el0) * j / nv
            for i in range(nu + 1):
                u = -1 + 2 * i / nu
                verts.append(H.point(az_c + u * w, el, shell_sc(az_c + u * w, el) + 0.004 + 0.026 * (1 - abs(u) ** 4)))
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i; faces.append((a, a + 1, a + nu + 2, a + nu + 1))
        return verts, faces
    G.add(band(0, 24, 88), "helmet_cyan", "head"); G.add(band(180, 88, -26), "helmet_cyan", "head")
    # vents: dark elongated insets following the surface
    for az, el in ((28, 62), (-28, 62), (40, 42), (-40, 42), (58, 60), (-58, 60), (112, 52), (-112, 52), (138, 30), (-138, 30), (92, 40), (-92, 40), (150, 58), (-150, 58)):
        G.add(_oriented(H, az, el, (0.052, 0.008, 0.021), (shell_sc(az, el) - 1.0) * H.r.z + 0.006), "helmet_vent", "head")
    for sx in (1, -1):
        G.add(_oriented(H, 72 * sx, 4, (0.034, 0.014, 0.062), (shell_sc(72 * sx, 4) - 1.0) * H.r.z + 0.010), "helmet_cyan", "head")
        for k_, el_ in enumerate((18, 0, -18)):
            G.add(_oriented(H, 86 * sx, el_, (0.020, 0.008, 0.010), (shell_sc(86 * sx, el_) - 1.0) * H.r.z + 0.012), "helmet_vent", "head")
        G.add(_oriented(H, 62 * sx, -12, (0.017, 0.012, 0.017), (SH - 1.0) * H.r.z + 0.022), "cage_white", "head")
    lip = [H.point(a, 27.5, shell_sc(a, 27.5) + 0.045) for a in range(-48, 49, 6)]          # front brow lip
    chin = [H.point(a, -50 - 4 * (1 - abs(a) / 50.0), 1.17) for a in range(-50, 51, 5)]      # navy chin guard under the cage
    G.add(sweep(chin, [0.032] * len(chin), 12, 0.6), "helmet_navy_v9", "head")
    for k_ in (-1, 0, 1):
        G.add(_oriented(H, 14 * k_, -52, (0.006, 0.006, 0.014), 0.05), "helmet_vent", "head")
    G.add(sweep(lip, [0.022] * len(lip), 10, 1.0), "helmet_navy_v9", "head")
    def cp(az, el, sc):
        return H.point(az, el, sc)
    bars = [[cp(a, 25, 1.17) for a in range(-54, 55, 6)], [cp(a, -16, 1.23) for a in range(-56, 57, 7)], [cp(a, -37, 1.20) for a in range(-48, 49, 8)]]
    for b in bars:
        G.add(sweep(b, [0.0095] * len(b), 8, 1.0), "cage_white", "head")
    for a in (-56, 56):
        G.add(sweep([cp(a, 25, 1.17), cp(a, 2, 1.21), cp(a, -16, 1.23), cp(a * 0.86, -37, 1.20)], [0.0095] * 4, 8, 1.0), "cage_white", "head")
    for a in (-18, 0, 18):
        G.add(sweep([cp(a, -16, 1.23), cp(a, -27, 1.22), cp(a, -37, 1.20)], [0.0085] * 3, 8, 1.0), "cage_white", "head")

def build_character_v9(s, collection, arm, look):
    """look: 'player' or 'goalie'. Builds the old body/kit, then replaces head/face/hair/headgear with v9 parts."""
    base = dict(s, hair_style="short", headgear="none", lash=False, freckles=False)
    parts = build_character(base, collection, arm)
    for k in ("face", "hair", "headgear") + (("chest_protector",) if look == "goalie" else ()):
        o = parts.pop(k, None)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    set_proportions(s)
    try:
        H = Head(s)
        F = Builder(s["name"] + "_face"); v9_face(s, H, F); parts["face"] = F.build(collection, arm)
        Hb = Builder(s["name"] + "_hair"); (v9_hair_player if look == "player" else v9_hair_goalie)(s, H, Hb); parts["hair"] = Hb.build(collection, arm)
        G = Builder(s["name"] + "_headgear"); (v9_goggles if look == "player" else v9_helmet)(s, H, G); parts["headgear"] = G.build(collection, arm)
    finally:
        clear_proportions()
    set_proportions(s)
    try:
        L = rest_layout(s); Hn = Builder(s["name"] + "_hands_v9"); hk = s.get("hand_k", 1.0); gs = s.get("glove_size", (0.1, 0.1, 0.1))
        for side, sx in (("L", 1.0), ("R", -1.0)):
            r = L[side]; gl, fd = r["gl"], r["fdir"]
            M = Matrix.Translation(gl) @ V((0, 0, 1)).rotation_difference(fd).to_matrix().to_4x4()
            if look == "player":     # chunky toy hand: palm, four fingers, thumb
                Hn.add(xform(superellipsoid((0.058 * hk, 0.042 * hk, 0.056 * hk), 0.7, 0.8, 16, 10, (0, 0, -0.012)), M), s["skin"], "hand_" + side)
                for k_ in range(4):
                    x = (-0.033 + 0.022 * k_) * hk
                    Hn.add(xform(sweep([(x, 0.004, 0.030 * hk), (x * 1.08, -0.004, 0.066 * hk), (x * 1.12, -0.018, 0.090 * hk)],
                                       [0.0125 * hk, 0.0118 * hk, 0.0105 * hk], 10, 0.8), M), s["skin"], "fingers_" + side)
                Hn.add(xform(sweep([(0.0, -0.030 * hk, -0.005), (0.012 * sx * 0 + 0.0, -0.050 * hk, 0.025 * hk), (0.0, -0.058 * hk, 0.048 * hk)],
                                   [0.016 * hk, 0.014 * hk, 0.012 * hk], 10, 0.8), M), s["skin"], "thumb_" + side)
            else:                    # white finger + thumb panels on the goalie gloves
                Hn.add(xform(superellipsoid((gs[0] * 0.86, gs[1] * 0.35, gs[2] * 0.30), 0.6, 0.7, 16, 8, (0, gs[1] * 0.72, 0.075)), M), "sock_white_v9", "fingers_" + side)
                Hn.add(xform(superellipsoid((0.036, 0.03, 0.05), 0.7, 0.8, 12, 8, (0.0, -0.075, 0.025)), M), "sock_white_v9", "thumb_" + side)
        parts["hands_v9"] = Hn.build(collection, arm)
    finally:
        clear_proportions()
    if look == "player" and "gloves" in parts:
        bpy.data.objects.remove(parts.pop("gloves"), do_unlink=True)
    if look == "goalie":        # rounded protector pads under the jersey + front number
        Bp = Builder(s["name"] + "_pads"); tk = s.get("torso_k", 1.0)
        for (x, z, rx, rz) in ((0.078, 0.815, 0.082, 0.062), (-0.078, 0.815, 0.082, 0.062), (0.07, 0.60, 0.078, 0.055), (-0.07, 0.60, 0.078, 0.055)):
            Bp.add(superellipsoid((rx * tk, 0.055, rz), 0.85, 0.85, 20, 12, (x * tk, -0.116 * tk, z)), s["kit"], "chest" if z > 0.72 else "spine")
        for sx in (1, -1):
            Bp.add(superellipsoid((0.075, 0.07, 0.06), 0.55, 0.6, 16, 8, (0.17 * sx * tk, -0.01, 0.86)), s["kit"], "chest")
            Bp.add(sweep([(0.13 * sx * tk, -0.13 * tk, 0.88), (0.19 * sx * tk, -0.06, 0.90)], [0.011, 0.011], 8, 1.0), s["kit_trim"], "chest")
        num = text_mesh("num_front_v9_150", s["number"], 0.15, collection, 0.014)
        Bp.add(xform(num, Matrix.Translation((-0.045, -0.178 * tk, 0.655)) @ Matrix.Rotation(math.radians(90), 4, "X")), s["number_mat"], "chest")
        parts["pads"] = Bp.build(collection, arm)
    if look == "player":
        vs = [o.matrix_world @ v.co for o in parts.values() if o.type == "MESH" for v in o.data.vertices
              if any(m and m.name == "M_kit_cream_v9" for m in o.data.materials)]
        band = [q for q in vs if abs(q.x) < 0.03 and 0.72 < q.z < 0.86]
        if band:
            ztop = max(q.z for q in vs if abs(q.x) < 0.04); yf = min(q.y for q in band)
            neck = [q for q in vs if q.z > ztop - 0.02]
            rx = max(abs(q.x) for q in neck) if neck else 0.07
            Bc = Builder(s["name"] + "_collar")
            ring = [(rx * 0.9 * math.sin(a), yf * 0.55 * math.cos(a) - 0.004 + 0.01, ztop - 0.012) for a in [2 * math.pi * k / 24 for k in range(25)]]
            Bc.add(sweep(ring, [0.011] * len(ring), 8, 1.0, cap0=False, cap1=False), s["kit_trim"], "chest")
            vee = [(-rx * 0.8, yf * 0.8, ztop - 0.02), (-0.03, yf - 0.003, ztop - 0.07), (0.0, yf - 0.006, ztop - 0.10), (0.03, yf - 0.003, ztop - 0.07), (rx * 0.8, yf * 0.8, ztop - 0.02)]
            Bc.add(sweep(vee, [0.013] * 5, 8, 1.0), s["kit_trim"], "chest")
            parts["collar"] = Bc.build(collection, arm)
    return parts

PLAYER_V9 = dict(GIRL_FIELD, name="v9_player", head_r=(0.285, 0.258, 0.27), skin="skin_v9", hair="hair_v9", iris="eye_v9", kit="kit_cream_v9", kit_trim="kit_red_v9",
                 number="10", number_mat="kit_red_v9", bottom="shorts_v9", bottom_mat="kit_red_v9", bottom_trim="kit_cream_v9",
                 sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_red_v9", glove=None, glove_cuff=None, limb_k=1.5, hand_k=1.4, shoe_k=1.5, torso_k=1.22, sole="kit_red_v9", front_number_size=0.17, front_number_x=-0.095, front_number_z=0.68)
GOALIE_V9 = dict(BOY_GOALIE, name="v9_goalie", head_r=(0.285, 0.258, 0.27), skin="skin_v9", hair="hair_v9", iris="eye_v9", kit="kit_navy_v9", kit_trim="kit_cyan_v9",
                 number="2", number_mat="sock_white_v9", bottom="shorts_v9", bottom_mat="kit_navy_v9", bottom_trim="kit_cyan_v9",
                 sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_navy_v9",
                 glove="kit_navy_v9", glove_cuff="sock_white_v9", body_scale=0.82, limb_k=1.5, shoe_k=1.5, torso_k=1.22, sole="kit_cyan_v9", chest_protector=False)


def pose_turnaround(arm, look):
    """Concept stance for lookdev renders only: wide stance, soft knees, arms out and down (arm IK released)."""
    pbs = arm.pose.bones
    for pb in pbs:
        for c in pb.constraints:
            if c.type == "IK" and ("forearm" in pb.name):
                c.mute = True
    bpy.context.view_layer.update()
    for side, sx in (("L", 1), ("R", -1)):
        for bn, d in (("upperarm_" + side, (0.78 * sx, -0.12, -0.62)), ("forearm_" + side, (0.42 * sx, -0.30, -0.86))):
            pb = pbs[bn]; R0 = arm.data.bones[bn].matrix_local.to_3x3()
            q = V(R0.col[1]).rotation_difference(V(d).normalized())
            pb.matrix = Matrix.Translation(pb.head) @ (q.to_matrix() @ R0).to_4x4()
            bpy.context.view_layer.update()
        set_loc_world(pbs["ik_foot_" + side], V((0.07 * sx, -0.01, 0.0)))
    set_loc_world(pbs["pelvis"], V((0, 0.0, -0.012)))
    bpy.context.view_layer.update()
