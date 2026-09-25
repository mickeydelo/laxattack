# Lax Attack v9 look (Phase A): matches the approved turnaround concepts (female #10 field player, female #2 goalie).
# Body/kit come from the existing builder (colours per concept); head, face, hair and headgear are rebuilt here.
# Bone names are unchanged so every animation clip still works.
def _lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
_SRGB = {   # concept colours (sRGB) -> linear shader values
    "skin_v9": ((0.97, 0.79, 0.64), 0.36, 0.25), "hair_v9": ((0.40, 0.22, 0.12), 0.30, 0.35), "eye_v9": ((0.16, 0.09, 0.05), 0.08, 0.6),
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
            dip = (0.013 * math.exp(-(az / 5.0) ** 2) * smoothstep(el0 + 1, el0 + 8, el) * (1 - smoothstep(78, 89, el))) if part else 0.0
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
    ew, eh = 0.036, 0.054
    for side, sx in (("L", 1), ("R", -1)):
        az, el = 23.0 * sx, -7.0
        F.add(H.place(ellipsoid((0, 0, 0), (ew, 0.005, eh), 26, 16), az, el, -0.001), "eye_v9", "eye_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.0125, 0.0025, 0.016), 12, 8), az + 3.2, el + 4.6, 0.0035), "eye_hi_v9", "eye_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.0055, 0.0025, 0.0055), 8, 5), az - 3.4, el - 6.0, 0.0035), "eye_hi_v9", "eye_" + side)
        dA = math.degrees(ew / H.r.x) * 1.3 + 2; dE = math.degrees(eh / H.r.z) + 2
        lo = math.degrees(eh / H.r.z) * 2 + 4
        F.add(surface_patch(H, az - dA, az + dA, el - dE + lo, el + dE + lo, 0.0042), s["skin"], "lid_" + side)
        bpts = [H.point(az + dx * sx, el + 19.5 + 1.2 - 0.03 * dx * dx) for dx in (-7, -2, 3, 8)]
        bpts = [tuple(V(q) + (V(q) - H.c).normalized() * 0.0035) for q in bpts]
        F.add(sweep(bpts, [0.0035, 0.0052, 0.005, 0.003], 8, 0.5), "brow_v9", "brow_" + side)
        F.add(H.place(ellipsoid((0, 0, 0), (0.036, 0.004, 0.022), 14, 6), 37 * sx, -21.0, -0.0015), "blush_v9", "head")
    mw = 0.030; mel = -26.0
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
    bnd = lambda az: _interp([(0, 34), (20, 30), (42, 18), (70, 9), (92, -2), (112, -20), (150, -36), (180, -42)], az)
    cap, rim = hair_cap(H, bnd, base=1.05, grooves=28, depth=0.022, part=True, back_bulge=0.035)
    Hb.add(cap, "hair_v9", "head"); Hb.add(sweep(rim, [0.012] * len(rim), 8, 1.0, cap0=False, cap1=False), "hair_v9", "head")
    for sx in (1, -1):   # face-framing locks in front of the ears
        pts = [H.point(64 * sx, 12, 1.055), H.point(70 * sx, -8, 1.06), H.point(70 * sx, -26, 1.055), H.point(66 * sx, -38, 1.05)]
        Hb.add(sweep(pts, [0.024, 0.022, 0.016, 0.005], 10, 0.55), "hair_v9", "head")
    c = V(H.point(138, -24, 1.16)); n = (c - H.c).normalized()
    for off, r in (((0, 0, 0), 0.085), ((0.035, 0.03, -0.055), 0.066), ((-0.03, 0.045, -0.05), 0.060), ((0.02, 0.06, 0.03), 0.058), ((0.0, 0.02, -0.10), 0.052)):
        cc = c + V(off)
        Hb.add(lobe(tuple(cc), (r, r * 0.95, r * 0.9), tuple((cc - H.c).normalized()), ridges=8, depth=0.10), "hair_v9", "head")
    tie_c = V(H.point(138, -20, 1.07))
    Hb.add(torus(tuple(tie_c), 0.05, 0.014, 20, 8, "Y"), "tie_cream", "head")

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
    G.add(sweep(strap, [0.017] * len(strap), 6, 2.6), "strap_dark", "head")
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
    SH = 1.125
    useg, vseg = 96, 22; verts, faces = [], []
    azs = [-180 + 360.0 * i / useg for i in range(useg)]
    for j in range(vseg + 1):
        for az in azs:
            el0 = bnd(az); t = j / vseg; el = el0 + (89.0 - el0) * (t ** 0.85)
            verts.append(H.point(az, el, SH + 0.025 * smoothstep(100, 180, abs(az)) * (1 - t)))
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
    def band(az_c, el0, el1, w=9.0, nu=6, nv=16):          # raised strip hugging the shell, edges tapered into it
        verts, faces = [], []
        for j in range(nv + 1):
            el = el0 + (el1 - el0) * j / nv
            for i in range(nu + 1):
                u = -1 + 2 * i / nu
                verts.append(H.point(az_c + u * w, el, SH + 0.004 + 0.016 * (1 - abs(u) ** 4)))
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i; faces.append((a, a + 1, a + nu + 2, a + nu + 1))
        return verts, faces
    G.add(band(0, 24, 88), "helmet_cyan", "head"); G.add(band(180, 88, -26), "helmet_cyan", "head")
    # vents: dark elongated insets following the surface
    for az, el in ((28, 62), (-28, 62), (40, 42), (-40, 42), (58, 60), (-58, 60), (112, 52), (-112, 52), (138, 30), (-138, 30), (92, 40), (-92, 40), (150, 58), (-150, 58)):
        G.add(_oriented(H, az, el, (0.030, 0.006, 0.014), (SH - 1.0) * H.r.z + 0.004), "helmet_vent", "head")
    for sx in (1, -1):
        G.add(_oriented(H, 70 * sx, 6, (0.028, 0.012, 0.050), (SH - 1.0) * H.r.z + 0.010), "helmet_cyan", "head")
        G.add(_oriented(H, 62 * sx, -12, (0.017, 0.012, 0.017), (SH - 1.0) * H.r.z + 0.022), "cage_white", "head")
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
    for k in ("face", "hair", "headgear"):
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

PLAYER_V9 = dict(GIRL_FIELD, name="v9_player", skin="skin_v9", hair="hair_v9", iris="eye_v9", kit="kit_cream_v9", kit_trim="kit_red_v9",
                 number="10", number_mat="kit_red_v9", bottom="shorts", bottom_mat="kit_red_v9", bottom_trim="kit_cream_v9",
                 sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_red_v9", glove=None, glove_cuff=None, limb_k=1.28, hand_k=1.25, shoe_k=1.45)
GOALIE_V9 = dict(BOY_GOALIE, name="v9_goalie", skin="skin_v9", hair="hair_v9", iris="eye_v9", kit="kit_navy_v9", kit_trim="kit_cyan_v9",
                 number="2", number_mat="sock_white_v9", bottom="shorts", bottom_mat="kit_navy_v9", bottom_trim="kit_cyan_v9",
                 sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_navy_v9",
                 glove="kit_navy_v9", glove_cuff="sock_white_v9", body_scale=0.82, limb_k=1.28, shoe_k=1.45)
