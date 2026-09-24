# Lax Attack figurine library: parametric toy-figure characters, shared skeleton families, bone-driven face,
# attack/goalie sticks with deformable pockets. Requires lax_core in the same namespace.
# Space: Blender Z-up, faces -Y, character LEFT = +X (sx=+1), RIGHT = -X (sx=-1).

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ specs
GIRL_FIELD = dict(   # women's field kit (reference photo): goggles, headband + ponytail, jersey, kilt, bare hands. Home red/cream #10
    name="girl_field", family="field", skin="skin_light", hair="hair_brown", iris="eye_dark", eye_style="toy",
    head_c=(0.0, 0.0, 1.195), head_r=(0.262, 0.248, 0.268), jaw_taper=0.16, cranium=0.05,
    eye_az=22.0, eye_el=-8.0, eye_size=(0.043, 0.055), lash=True, freckles=False, brow_w=0.008,
    mouth_w=0.036, mouth_el=-31.0, hair_style="ponytail", pony_el=30.0, pony_len=1.0, headgear="goggles",
    kit="kit_red", kit_trim="kit_cream", number_mat="kit_cream", bottom="kilt", bottom_mat="kit_red",
    sock="kit_white", sock_stripe="kit_white", shoe="kit_white", shoe_accent="kit_red",
    glove="kit_white", glove_cuff="kit_red", glove_size=(0.125, 0.11, 0.13), shoe_k=1.28,   # thin women's gloves
    number="10", stance=0.0, body_scale=0.82, head_k=1.15,
)
BOY_GOALIE = dict(   # v2: away team navy/teal
    name="boy_goalie", family="goalie", skin="skin_tan", hair="hair_dark", iris="eye_dark", eye_style="toy",
    head_c=(0.0, 0.0, 1.19), head_r=(0.268, 0.25, 0.262), jaw_taper=0.10, cranium=0.04,
    eye_az=22.0, eye_el=-7.0, eye_size=(0.043, 0.053), lash=False, freckles=False, brow_w=0.011,
    mouth_w=0.040, mouth_el=-30.0, hair_style="short", headgear="helmet", helmet_mat="helmet_navy",
    stripe_mat="helmet_teal", cage_mat="cage_light", kit="kit_navy", kit_trim="accent_teal", number_mat="kit_white",
    bottom="shorts", bottom_mat="kit_navy", bottom_trim="accent_teal", sock="kit_white", sock_stripe="accent_teal",
    shoe="kit_white", shoe_accent="accent_teal", glove="glove_dark", glove_cuff="glove_dark", glove_size=(0.20, 0.18, 0.21),
    shoe_k=1.28, number="3", stance=0.08, chest_protector=True, protector_mat="kit_navy", protector_accent="accent_teal",
    body_scale=0.84, head_k=1.15,
)

SH_X, SH_Z = 0.19, 0.875
UPPER, FORE = 0.23, 0.26
ARM_A = math.radians(52)
HIP_X = 0.085
GRIP_SPREAD = 0.22

# ------------------------------------------------------------------ proportions (v2)
# Figures are designed in a 1.5 m "design space" and transformed at build time: body segments scale uniformly about the
# ground (body_scale), everything driven by head bones scales up about the neck top (head_k). Sticks are never scaled.
HEAD_BONES = {"head", "jaw", "eye_L", "eye_R", "lid_L", "lid_R", "brow_L", "brow_R", "mouth_L", "mouth_R",
              "hair_01", "hair_02", "hair_03", "throat_guard"}
STICK_BONES = {"stick", "pocket_01", "pocket_02", "ik_hand_L", "ik_hand_R"}
NECK_TOP = V((0.0, 0.0, 0.965))

def prop_xf(s):
    bs = s.get("body_scale", 1.0); hk = s.get("head_k", 1.0)
    N2 = NECK_TOP * bs
    return (lambda p: V(p) * bs), (lambda p: N2 + (V(p) - NECK_TOP) * hk)

def set_proportions(s):
    body, head = prop_xf(s)
    def xf(p, w):
        if not w:
            return p
        b = max(w, key=w.get)
        if b in STICK_BONES:
            return p
        return head(p) if b in HEAD_BONES else body(p)
    globals()["BUILD_XF"] = xf

def clear_proportions():
    globals()["BUILD_XF"] = None
BALL_R = 0.08   # recommended runtime visual ball radius (runtime currently renders 0.12)

# ------------------------------------------------------------------ head surface model
class Head:
    def __init__(self, s):
        self.c = V(s["head_c"]); self.r = V(s["head_r"]); self.jt = s["jaw_taper"]; self.cr = s["cranium"]
    def shape(self, q):
        rz = self.r.z; z = q.z / rz
        if z > 0:
            q = V((q.x * (1 + 0.03 * z), q.y * (1 + 0.03 * z), q.z * (1 + self.cr * z)))
        else:
            t = -z
            q = V((q.x * (1 - self.jt * t * t), q.y * (1 - 0.10 * t * t), q.z))
        if q.y < 0:
            q.y *= 0.94
        return q
    def dirv(self, az, el):
        a, e = math.radians(az), math.radians(el)
        return V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    def point(self, az, el, scale=1.0):
        d = self.dirv(az, el)
        return self.c + self.shape(V((d.x * self.r.x, d.y * self.r.y, d.z * self.r.z))) * scale
    def frame(self, az, el, scale=1.0):
        p = self.point(az, el, scale)
        tx = (self.point(az + 0.5, el, scale) - self.point(az - 0.5, el, scale)).normalized()
        tu = (self.point(az, el + 0.5, scale) - self.point(az, el - 0.5, scale)).normalized()
        n = tx.cross(tu).normalized()  # outward
        tu = n.cross(tx).normalized()  # up
        return p, tx, n, tu
    def place(self, geo, az, el, off=0.0, scale=1.0, roll=0.0):
        """geo in local (x=tangent toward +az, y=outward normal, z=up tangent)."""
        p, tx, n, tu = self.frame(az, el, scale)
        if roll:
            R = Matrix.Rotation(math.radians(roll), 3, n)
            tx = R @ tx; tu = R @ tu
        M = Matrix((tx, n, tu)).transposed()
        v, f = geo
        return [tuple(p + n * off + M @ V(q)) for q in v], f
    def mesh(self, useg=44, vseg=30, scale=1.0):
        geo = ellipsoid((0, 0, 0), (1, 1, 1), useg, vseg)
        return deform(geo, lambda q: self.c + self.shape(V((q.x * self.r.x, q.y * self.r.y, q.z * self.r.z))) * scale)
    def shell_line(self, scale, line, thickness, useg=64, vseg=18):
        """Solidified cap over the head from a smooth lower edge line(az) up to the crown (hair / helmet)."""
        bm = bmesh.new(); grid = {}
        for j in range(vseg + 1):
            for i in range(useg):
                az = -180 + 360 * i / useg
                l0 = line(az); t = j / vseg
                el = l0 + (89.9 - l0) * (1 - (1 - t) ** 1.4)
                grid[(i, j)] = bm.verts.new(tuple(self.point(az, el, scale)))
        for j in range(vseg):
            for i in range(useg):
                q = [grid[(i, j)], grid[((i + 1) % useg, j)], grid[((i + 1) % useg, j + 1)], grid[(i, j + 1)]]
                bm.faces.new(q)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-4)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=list(bm.edges))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        f0 = max(bm.faces, key=lambda f: f.calc_center_median().z)
        if (f0.calc_center_median() - self.c).dot(f0.normal) < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=thickness)
        verts = [tuple(v.co) for v in bm.verts]; bm.verts.index_update()
        faces = [tuple(v.index for v in f.verts) for f in bm.faces]
        bm.free()
        return verts, faces
    def shell(self, scale, keep, thickness, useg=48, vseg=32):
        """Solidified partial shell over the head (hair cap / helmet). keep(az, el) -> bool per face centroid."""
        bm = bmesh.new()
        grid = {}
        for j in range(vseg + 1):
            el = -90 + 180 * j / vseg
            for i in range(useg):
                az = -180 + 360 * i / useg
                grid[(i, j)] = bm.verts.new(tuple(self.point(az, el, scale)))
        for j in range(vseg):
            for i in range(useg):
                az = -180 + 360 * (i + 0.5) / useg; el = -90 + 180 * (j + 0.5) / vseg
                if keep(az, el):
                    q = [grid[(i, j)], grid[((i + 1) % useg, j)], grid[((i + 1) % useg, j + 1)], grid[(i, j + 1)]]
                    if len(set(q)) == 4:
                        try:
                            bm.faces.new(q)
                        except ValueError:
                            pass
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
        for v in [v for v in bm.verts if not v.link_faces]:
            bm.verts.remove(v)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        # make normals point outward from the head center
        if bm.faces:
            f0 = max(bm.faces, key=lambda f: f.calc_center_median().z)
            if (f0.calc_center_median() - self.c).dot(f0.normal) < 0:
                bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        res = bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=thickness)
        verts = [tuple(v.co) for v in bm.verts]; bm.verts.index_update()
        faces = [tuple(v.index for v in f.verts) for f in bm.faces]
        bm.free()
        return verts, faces

# ------------------------------------------------------------------ skeleton
def rest_layout(s):
    L = {}
    for side, sx in (("L", 1.0), ("R", -1.0)):
        sh = V((SH_X * sx, 0.0, SH_Z))
        el = sh + V((UPPER * math.cos(ARM_A) * sx, 0.02, -UPPER * math.sin(ARM_A)))
        gl = el + V((FORE * math.cos(ARM_A) * sx, -0.04, -FORE * math.sin(ARM_A)))
        L[side] = dict(sh=sh, el=el, gl=gl, fdir=(gl - el).normalized(),
                       hip=V((HIP_X * sx, 0, 0.47)), knee=V((HIP_X * sx, -0.02, 0.27)), ank=V((HIP_X * sx, 0, 0.08)),
                       toe=V((HIP_X * sx, -0.11, 0.035)), tip=V((HIP_X * sx, -0.18, 0.03)))
    return L

def build_skeleton(s, collection, name):
    H = Head(s); L = rest_layout(s)
    ad = bpy.data.armatures.new(name); arm = bpy.data.objects.new(name, ad)
    collection.objects.link(arm); arm.show_in_front = True
    bpy.context.view_layer.objects.active = arm
    for o in bpy.context.selected_objects:
        o.select_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    body, head = prop_xf(s)
    g0d = L["R"]["gl"]; g0shift = body(g0d) - g0d
    def T(n, p):
        if n in HEAD_BONES:
            return head(p)
        if n in STICK_BONES:
            return V(p) + g0shift
        return body(p)
    def bone(n, h, t, parent=None, deform=True, connect=False, roll_z=None):
        b = eb.new(n); b.head = T(n, h); b.tail = T(n, t)
        if parent:
            b.parent = eb[parent]; b.use_connect = connect
        b.use_deform = deform
        if roll_z is not None:
            b.align_roll(V(roll_z))
        return b
    hc = H.c
    bone("root", (0, 0, 0), (0, 0, 0.2))
    bone("pelvis", (0, 0, 0.50), (0, 0, 0.60), "root")
    bone("spine", (0, 0, 0.60), (0, 0, 0.72), "pelvis", connect=True)
    bone("chest", (0, 0, 0.72), (0, 0, 0.90), "spine", connect=True)
    bone("neck", (0, 0, 0.90), (0, 0, 0.965), "chest", connect=True)
    bone("head", (0, 0, 0.965), (0, 0, 1.45), "neck", connect=True)
    # face: jaw (mouth open/close by scale), mouth corners, eyes (aim), lids (blink by scale), brows
    mel = s.get("mouth_el", -27.0)
    mt = H.point(0, mel + 1.0)
    mdir = (H.point(0, mel) - hc).normalized()   # jaw = mouth-cover hinge about the head centre (rotation only, no scale)
    bone("jaw", hc, hc + mdir * 0.1, "head", roll_z=(0, 0, 1))
    for side, sx in (("L", 1), ("R", -1)):
        az = s["eye_az"] * sx
        p, tx, n, tu = H.frame(az, s["eye_el"])
        ctr = p - n * 0.10
        bone("eye_" + side, ctr, ctr + n * 0.04, "head", roll_z=(0, 0, 1))
        top = p + tu * (s["eye_size"][1] + 0.004) + n * 0.004
        bone("lid_" + side, hc, hc + (p - hc).normalized() * 0.1, "head", roll_z=(0, 0, 1))   # lid hinge about head centre
        bp = H.point(az * 1.02, s["eye_el"] + 23.0)
        bone("brow_" + side, bp, bp + H.frame(az, s["eye_el"] + 23.0)[2] * 0.03, "head", roll_z=(0, 0, 1))
        mc = H.point(s["mouth_w"] / 0.25 * 57.3 * 0.95 * sx, mel)
        bone("mouth_" + side, mc, mc + V((0, -0.03, 0)), "head", roll_z=(0, 0, 1))
    for side, sx in (("L", 1.0), ("R", -1.0)):
        r = L[side]
        hd = r["gl"] + r["fdir"] * 0.06
        bone("clavicle_" + side, (0.03 * sx, 0, SH_Z - 0.02), r["sh"], "chest")
        bone("upperarm_" + side, r["sh"], r["el"], "clavicle_" + side, connect=True)
        bone("forearm_" + side, r["el"], r["gl"], "upperarm_" + side, connect=True)
        bone("hand_" + side, r["gl"], hd, "forearm_" + side, connect=True)
        bone("fingers_" + side, hd, hd + r["fdir"] * 0.05, "hand_" + side, connect=True)
        bone("thumb_" + side, r["gl"] + V((0, -0.03, 0.0)), r["gl"] + V((0, -0.07, 0.02)), "hand_" + side)
        bone("thigh_" + side, r["hip"], r["knee"], "pelvis")
        bone("shin_" + side, r["knee"], r["ank"], "thigh_" + side, connect=True)
        bone("foot_" + side, r["ank"], r["toe"], "shin_" + side, connect=True)
        bone("toe_" + side, r["toe"], r["tip"], "foot_" + side, connect=True)
        bone("ik_foot_" + side, r["ank"], r["toe"], "root", deform=False)
        bone("pole_knee_" + side, (0.13 * sx, -0.7, 0.30), (0.13 * sx, -0.7, 0.36), "root", deform=False)
        bone("pole_elbow_" + side, (0.55 * sx, 0.40, 0.62), (0.55 * sx, 0.40, 0.68), "chest", deform=False)
    # secondary chains: hair (ponytail), hem front/back
    p0 = H.point(180, s.get("pony_el", 30)) + V((0, 0.03, 0.02)); k = s.get("pony_len", 1.0)
    bone("hair_01", p0, p0 + V((0, 0.10, -0.02)) * k, "head")
    bone("hair_02", p0 + V((0, 0.10, -0.02)) * k, p0 + V((0, 0.17, -0.16)) * k, "hair_01", connect=True)
    bone("hair_03", p0 + V((0, 0.17, -0.16)) * k, p0 + V((0, 0.16, -0.34)) * k, "hair_02", connect=True)
    bone("hem_F", (0, -0.12, 0.58), (0, -0.14, 0.44), "pelvis")
    bone("hem_B", (0, 0.12, 0.58), (0, 0.14, 0.44), "pelvis")
    if s["family"] == "goalie":
        bone("chest_pad", (0, -0.13, 0.86), (0, -0.14, 0.66), "chest")
        tg = H.point(0, -52, 1.25)
        bone("throat_guard", tg, tg + V((0, -0.02, -0.10)), "head")
    # stick + IK hand targets (stick frame: +Y shaft toward head, +Z pocket open face)
    g0 = L["R"]["gl"]
    bone("stick", g0, g0 + V((0, 0, 0.22)), "root", roll_z=(0, -1, 0))
    bone("pocket_01", g0 + V((0, 0, 0.40)), g0 + V((0, 0, 0.44)), "stick", roll_z=(0, -1, 0))
    bone("pocket_02", g0 + V((0, 0, 0.50)), g0 + V((0, 0, 0.54)), "stick", roll_z=(0, -1, 0))
    bone("ik_hand_R", g0, g0 + V((0, 0, 0.05)), "stick", deform=False)
    bone("ik_hand_L", g0 + V((0, 0, -GRIP_SPREAD)), g0 + V((0, 0, -GRIP_SPREAD + 0.05)), "stick", deform=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    arm["lid_open_deg"] = math.degrees(s["eye_size"][1] / s["head_r"][2]) * 2 + 4; arm["mouth_open_deg"] = 15.0
    arm["body_scale"] = s.get("body_scale", 1.0); arm["head_k"] = s.get("head_k", 1.0); arm["family"] = s["family"]
    pb = arm.pose.bones
    for side in ("L", "R"):
        c = pb["forearm_" + side].constraints.new("IK"); c.target = arm; c.subtarget = "ik_hand_" + side
        c.pole_target = arm; c.pole_subtarget = "pole_elbow_" + side; c.chain_count = 2; c.use_stretch = False
        c.iterations = 500
        c = pb["shin_" + side].constraints.new("IK"); c.target = arm; c.subtarget = "ik_foot_" + side
        c.pole_target = arm; c.pole_subtarget = "pole_knee_" + side; c.chain_count = 2; c.use_stretch = False
        c.iterations = 500
        c = pb["foot_" + side].constraints.new("COPY_ROTATION"); c.target = arm; c.subtarget = "ik_foot_" + side
    for b in pb:
        b.rotation_mode = "QUATERNION" if b.name == "stick" else "XYZ"
    return arm

# ------------------------------------------------------------------ character meshes
def body_weights(p):
    z = p.z
    if z < 0.60:
        w = smoothstep(0.54, 0.64, z); return {"pelvis": 1 - w, "spine": w}
    if z < 0.74:
        w = smoothstep(0.68, 0.78, z); return {"spine": 1 - w, "chest": w}
    return {"chest": 1.0}

def build_character(s, collection, arm):
    set_proportions(s)
    try:
        return _build_character(s, collection, arm)
    finally:
        clear_proportions()

def _build_character(s, collection, arm):
    H = Head(s); L = rest_layout(s)
    parts = {}
    skin, hair, kit, trim = s["skin"], s["hair"], s["kit"], s["kit_trim"]
    # ---- head + face
    B = Builder(s["name"] + "_head")
    B.add(H.mesh(), skin, "head")
    B.add(H.place(ellipsoid((0, 0, 0), (0.028, 0.018, 0.022), 14, 8), 0, -15.0, 0.004), skin, "head")        # nose
    for side, sx in (("L", 1), ("R", -1)):
        B.add(H.place(ellipsoid((0, 0, 0), (0.030, 0.045, 0.052), 12, 8), 86 * sx, -6.0, -0.01), skin, "head")  # ear
    parts["head"] = B.build(collection, arm)
    F = Builder(s["name"] + "_face")
    ew, eh = s["eye_size"]
    for side, sx in (("L", 1), ("R", -1)):
        az, el = s["eye_az"] * sx, s["eye_el"]
        if s.get("eye_style") == "toy":   # vinyl-toy eye: one glossy dark oval + two painted highlights
            F.add(H.place(ellipsoid((0, 0, 0), (ew, 0.006, eh), 22, 12), az, el, -0.003), s["iris"], "eye_" + side)
            F.add(H.place(ellipsoid((0, 0, 0), (0.015, 0.003, 0.017), 10, 6), az + 3.5 * sx, el + 5.0, 0.0035), "eye_white", "eye_" + side)
            F.add(H.place(ellipsoid((0, 0, 0), (0.007, 0.003, 0.007), 8, 5), az - 4.0 * sx, el - 6.0, 0.0035), "eye_white", "eye_" + side)
        else:
            F.add(H.place(ellipsoid((0, 0, 0), (ew, 0.018, eh), 20, 12), az, el, -0.004), "eye_white", "head")
            F.add(H.place(ellipsoid((0, 0, 0), (ew * 0.72, 0.012, eh * 0.78), 18, 10), az - 2.0 * sx, el - 1.5, 0.004), s["iris"], "eye_" + side)
            F.add(H.place(ellipsoid((0, 0, 0), (ew * 0.40, 0.011, eh * 0.45), 14, 8), az - 2.0 * sx, el - 1.8, 0.0075), "pupil", "eye_" + side)
            F.add(H.place(ellipsoid((0, 0, 0), (0.012, 0.009, 0.013), 10, 6), az + 3.0 * sx, el + 6.0, 0.013), "eye_white", "head")
            F.add(H.place(ellipsoid((0, 0, 0), (0.006, 0.006, 0.006), 8, 5), az - 5.5 * sx, el - 7.0, 0.012), "eye_white", "head")
        # lid: authored closed (covers the eye), collapsed to a thin upper lid by lid bone scale in every pose
        p, tx, n, tu = H.frame(az, el)
        top = p + tu * (eh + 0.004) + n * 0.004
        # lid: skin patch hugging the head over the eye (authored closed); lid bone rotates it up onto the forehead to open
        dA = math.degrees(ew / H.r.x) * 1.25 + 2; dE = math.degrees(eh / H.r.z) + 2
        lo = math.degrees(s["eye_size"][1] / s["head_r"][2]) * 2 + 4   # lids AUTHORED OPEN (parked on the forehead): rest frame = open eyes
        F.add(surface_patch(H, az - dA, az + dA, el - dE + lo, el + dE + lo, 0.0050), skin, "lid_" + side)
        # upper lash line (painted)
        pts = [H.point(az + dx * sx, el + 14.2 - 5.0 * (dx / 12.0) ** 2) for dx in (-12, -6, 0, 6, 12)]
        pts = [tuple(V(q) + (V(q) - H.c).normalized() * 0.016) for q in pts]
        rad = [0.004, 0.0055, 0.006, 0.006, 0.005]
        if s["lash"]:
            pts.append(tuple(V(pts[-1]) + V((0.018 * sx, 0.005, 0.012)))); rad.append(0.0015)
        F.add(sweep(pts, rad, 8, 0.6), "pupil", "head")
        # brow
        bpts = [H.point(az + dx * sx, el + 23.0 + (1.2 if abs(dx) < 4 else 0) - 0.02 * dx * dx) for dx in (-9, -3, 3, 9)]
        bpts = [tuple(V(q) + (V(q) - H.c).normalized() * 0.006) for q in bpts]
        bw = s["brow_w"]
        F.add(sweep(bpts, [bw * 0.7, bw, bw, bw * 0.6], 8, 0.55), hair, "brow_" + side)
        # cheek blush
        F.add(H.place(ellipsoid((0, 0, 0), (0.034, 0.005, 0.020), 14, 6), 35 * sx, -19.0, -0.0015), "blush", "head")
        if s["freckles"]:
            for k, (da, de) in enumerate(((-4, 2), (2, -2), (5, 3), (-1, -5))):
                F.add(H.place(ellipsoid((0, 0, 0), (0.005, 0.003, 0.005), 6, 4), (33 + da) * sx, -12.0 + de, 0.001), "mouth", "head")
    # mouth: authored open (D shape with tongue); jaw bone scale collapses it to a smile line
    mw = s["mouth_w"]; mel = s.get("mouth_el", -27.0)
    def mouth_shape(q):
        x = q.x / mw; z = q.z
        z = z * (1.0 if z < 0 else 0.25) + 0.012 * x * x   # flat top with smile curve
        return V((q.x, q.y, z))
    mouth = deform(ellipsoid((0, 0, 0), (mw * 1.12, 0.005, 0.052), 22, 12), mouth_shape)
    def mouth_w(p):
        loc = p - H.point(0, mel)
        wl = smoothstep(0.012, mw * 0.95, loc.x); wr = smoothstep(0.012, mw * 0.95, -loc.x)
        return {"head": max(0.0, 1 - wl - wr), "mouth_L": wl, "mouth_R": wr}
    F.add(H.place(mouth, 0, mel, -0.002), "mouth", weights=mouth_w)
    F.add(H.place(ellipsoid((0, 0, 0), (mw * 0.58, 0.004, 0.018), 12, 6), 0, mel - 6.5, 0.0), "blush", "head")
    # mouth cover: skin patch that leaves only the top smile line visible; jaw bone rotates it down onto the chin to open
    mA = math.degrees(mw * 1.12 / H.r.x) * 1.25 + 2
    F.add(surface_patch(H, -mA, mA, mel - 13.5, mel + 1.8, 0.0045), skin, "jaw")
    parts["face"] = F.build(collection, arm)
    # ---- hair
    Hb = Builder(s["name"] + "_hair")
    if s["hair_style"] == "ponytail":
        Hb.add(H.shell_line(1.045, lambda az: 34 - 78 * smoothstep(45, 168, abs(az)), 0.018), hair, "head")
        for k, (az0, el0, az1, el1) in enumerate(((-6, 76, -34, 30), (8, 78, 22, 29), (24, 70, 48, 22), (-24, 70, -52, 18))):
            pts = [H.point(az0 + (az1 - az0) * t, el0 + (el1 - el0) * (t ** 0.8), 1.06 + 0.02 * math.sin(math.pi * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
            Hb.add(sweep(pts, [0.045, 0.05, 0.045, 0.03, 0.006], 10, 0.45), hair, "head")
        for sx in (1, -1):  # face-framing side locks
            pts = [H.point(58 * sx, 34, 1.06), H.point(70 * sx, 8, 1.07), H.point(72 * sx, -18, 1.06), H.point(62 * sx, -36, 1.05)]
            pts.append(tuple(V(pts[-1]) + V((-0.012 * sx, -0.03, 0.01))))
            Hb.add(sweep(pts, [0.04, 0.045, 0.038, 0.022, 0.005], 10, 0.5), hair, "head")
        # ponytail (skinned to hair chain)
        p0 = H.point(180, 30) + V((0, 0.03, 0.02))
        pts = bezier_pts(p0, p0 + V((0, 0.14, 0.03)), p0 + V((0, 0.22, -0.12)), p0 + V((0, 0.13, -0.36)), 11)
        rad = [0.06, 0.085, 0.10, 0.10, 0.095, 0.085, 0.07, 0.055, 0.04, 0.025, 0.006]
        def pony_w(p):
            d = p.z - p0.z; y = p.y - p0.y
            t = max(0.0, min(1.0, (y * 0.6 - d) / 0.42))
            w1 = 1 - smoothstep(0.0, 0.35, t); w3 = smoothstep(0.45, 0.9, t); w2 = max(0.0, 1 - w1 - w3)
            return {"hair_01": w1, "hair_02": w2, "hair_03": w3}
        Hb.add(sweep(pts, rad, 14, 0.8), hair, weights=pony_w)
        Hb.add(torus(p0 + V((0, 0.035, 0.005)), 0.058, 0.02, 20, 8, "Y"), "accent_coral", "hair_01")
        # headband
        hb = [H.point(a, 38 - 22 * smoothstep(60, 180, abs(a)), 1.055) for a in range(-180, 181, 20)]
        Hb.add(sweep(hb, [0.012] * len(hb), 8, 1.7, cap0=False, cap1=False), "kit_white", "head")
    elif s["hair_style"] == "ponytail_helmet":   # hair shows below the helmet rim at the back + ponytail + side puffs
        Hb.add(H.shell_line(1.04, lambda az: 20 - 70 * smoothstep(40, 165, abs(az)), 0.02), hair, "head")
        for sx in (1, -1):
            for az, el, r in ((122, -40, (0.075, 0.065, 0.07)), (148, -44, (0.07, 0.065, 0.065))):
                Hb.add(ellipsoid(H.point(az * sx, el, 1.02), r, 14, 8), hair, "head")
        p0 = H.point(180, s.get("pony_el", -22)) + V((0, 0.03, 0.02)); k = s.get("pony_len", 1.0)
        pts = bezier_pts(p0, p0 + V((0, 0.14, 0.03)) * k, p0 + V((0, 0.22, -0.12)) * k, p0 + V((0, 0.13, -0.36)) * k, 11)
        rad = [x * (0.8 + 0.2 * k) for x in (0.06, 0.085, 0.10, 0.10, 0.095, 0.085, 0.07, 0.055, 0.04, 0.025, 0.006)]
        def pony_w2(p):
            d = p.z - p0.z; y = p.y - p0.y
            t = max(0.0, min(1.0, (y * 0.6 - d) / (0.42 * k)))
            w1 = 1 - smoothstep(0.0, 0.35, t); w3 = smoothstep(0.45, 0.9, t); w2 = max(0.0, 1 - w1 - w3)
            return {"hair_01": w1, "hair_02": w2, "hair_03": w3}
        Hb.add(sweep(pts, rad, 14, 0.8), hair, weights=pony_w2)
        Hb.add(torus(p0 + V((0, 0.035, 0.005)), 0.055, 0.019, 20, 8, "Y"), s.get("kit_trim", "accent_coral"), "hair_01")
    else:  # short hair tufts visible under a helmet
        Hb.add(H.shell_line(1.03, lambda az: 40 - 52 * smoothstep(60, 120, abs(az)) - 12 * smoothstep(120, 170, abs(az)), 0.02), hair, "head")
        for sx in (1, -1):
            pts = [H.point(80 * sx, 12, 1.03), H.point(84 * sx, -6, 1.05), H.point(80 * sx, -20, 1.03)]
            Hb.add(sweep(pts, [0.03, 0.028, 0.006], 8, 0.6), hair, "head")
    parts["hair"] = Hb.build(collection, arm)
    # ---- headgear
    G = Builder(s["name"] + "_headgear")
    if s["headgear"] == "goggles":
        def gp(az, el, off=0.038):   # offset along the surface normal (radial scaling would drift the frame down)
            p, tx, n, tu = H.frame(az, el)
            return tuple(p + n * off)
        loop = []
        for i in range(24):
            t = 2 * math.pi * i / 24
            c, sn = math.cos(t), math.sin(t)
            az = 44 * math.copysign(abs(c) ** 0.55, c); el = -3.5 + 15.0 * math.copysign(abs(sn) ** 0.55, sn)
            loop.append(gp(az, el))
        loop.append(loop[0])
        G.add(sweep(loop, [0.014] * len(loop), 8, 1.0, cap0=False, cap1=False), "plastic_white", "head")
        G.add(sweep([gp(0, 11.5), gp(0, -3.5, 0.048), gp(0, -18.5)], [0.010, 0.0095, 0.010], 8, 1.0), "plastic_white", "head")
        for sx in (1, -1):
            G.add(sweep([gp(46 * sx, 8, 0.03), gp(46 * sx, -15, 0.03)], [0.018, 0.018], 8, 1.2), "plastic_blue", "head")
        strap = [H.point(a, -3 + 6 * smoothstep(90, 180, abs(a)), 1.085) for a in list(range(45, 181, 15)) + list(range(-180, -44, 15))]
        G.add(sweep(strap, [0.011] * len(strap), 6, 2.2), "kit_navy", "head")
    elif s["headgear"] == "cap":
        G.add(H.shell_line(1.06, lambda az: 26 - 10 * smoothstep(60, 180, abs(az)), 0.02, 48, 10), s.get("cap_mat", "kit_blue"), "head")
        G.add(H.place(superellipsoid((0.30, 0.16, 0.025), 0.5, 0.8, 20, 6, (0, 0.07, 0)), 0, 26, 0.0, 1.06), s.get("cap_mat", "kit_blue"), "head")
        G.add(ellipsoid(H.point(0, 89, 1.08), (0.02, 0.02, 0.012), 8, 5), "kit_white", "head")
    elif s["headgear"] == "helmet":  # helmet with face cage (+ throat guard for goalies)
        hm, sm, cm = s.get("helmet_mat", "plastic_blue"), s.get("stripe_mat", "plastic_white"), s.get("cage_mat", "metal_silver")
        G.add(H.shell_line(1.13, lambda az: 36 - 86 * smoothstep(50, 74, abs(az)) + 20 * smoothstep(112, 142, abs(az)), 0.03, 72, 20), hm, "head")
        ridge = [H.point(0, e, 1.155) for e in range(32, 181, 12)]
        G.add(sweep(ridge, [0.012] * len(ridge), 8, 4.5, up=(0, -1, 0)), sm, "head")
        for sx in (1, -1):
            side = [H.point(22 * sx, e, 1.145) for e in range(40, 150, 12)]
            G.add(sweep(side, [0.006] * len(side), 6, 2.5), sm, "head")
        visor = [H.point(a, 35, 1.19) for a in range(-56, 57, 8)]
        G.add(sweep(visor, [0.02] * len(visor), 8, 2.0), hm, "head")
        for sx in (1, -1):
            G.add(H.place(superellipsoid((0.09, 0.05, 0.10), 0.5, 0.6, 16, 10), 92 * sx, -12, 0.035, 1.12), sm, "head")
            G.add(H.place(ellipsoid((0, 0, 0), (0.02, 0.012, 0.02), 10, 6), 92 * sx, -12, 0.064, 1.12), "rubber_dark", "head")
        cage_r = 1.21
        for el in (30, -36):
            pts = [H.point(a, el, cage_r) for a in range(-58, 59, 8)]
            G.add(sweep(pts, [0.011] * len(pts), 8, 1.0), cm, "head")
        chin = [H.point(a, -54 + 8 * (abs(a) / 58) ** 2, cage_r * 0.97) for a in range(-58, 59, 8)]
        G.add(sweep(chin, [0.013] * len(chin), 8, 1.0), cm, "head")
        for a in (-38, 38, -58, 58):
            pts = [H.point(a, e, cage_r * (0.97 if e < -40 else 1.0)) for e in (30, 5, -36, -52)]
            G.add(sweep(pts, [0.011] * 4, 8, 1.0), cm, "head")
        G.add(H.place(superellipsoid((0.20, 0.05, 0.08), 0.45, 0.6, 18, 10), 0, -58, 0.07, 1.12), sm, "head")
        if s["family"] == "goalie":
            G.add(xform(superellipsoid((0.17, 0.035, 0.11), 0.5, 0.7, 16, 10), Matrix.Translation(H.point(0, -52, 1.25) + V((0, -0.02, -0.07)))), hm, "throat_guard")
    if G.parts:
        parts["headgear"] = G.build(collection, arm)
    # ---- torso / kit
    K = Builder(s["name"] + "_kit")
    torso = loft([(0.50, 0.135, 0.105), (0.56, 0.142, 0.108), (0.64, 0.148, 0.112), (0.72, 0.162, 0.122),
                  (0.80, 0.180, 0.130), (0.855, 0.178, 0.128), (0.895, 0.13, 0.095), (0.915, 0.07, 0.06)], 28, "flat", "flat", 2.3)
    K.add(torso, kit, weights=body_weights)
    K.add(torus((0, -0.005, 0.905), 0.078, 0.014, 22, 8), trim, "chest")
    for sx in (1, -1):
        stripe = [(0.155 * sx, 0.0, 0.54), (0.165 * sx, 0.0, 0.66), (0.183 * sx, 0.0, 0.80)]
        K.add(sweep(stripe, [0.022, 0.024, 0.02], 8, 0.35, up=(1, 0, 0)), trim, weights=body_weights)
    def wrap(geo, sgn, y0):
        def f(q):
            ys = 0.124 * math.sqrt(max(0.0, 1 - (q.x / 0.172) ** 2))
            return V((q.x, sgn * (ys + 0.004) + (q.y - y0), q.z))
        return deform(geo, f)
    num_b = text_mesh("num_b", s["number"] or " ", 0.20, collection, 0.012) if s["number"] else ([], [])
    num_b = xform(num_b, Matrix.Translation((0, 0.128, 0.72)) @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(180), 4, "Y"))
    K.add(wrap(num_b, 1, 0.128), s.get("number_mat", trim), "chest")
    if s["number"] and not s.get("chest_protector"):
        num_f = text_mesh("num_f", s["number"], 0.09, collection, 0.01)
        num_f = xform(num_f, Matrix.Translation((-0.07, -0.133, 0.80)) @ Matrix.Rotation(math.radians(90), 4, "X"))
        K.add(wrap(num_f, -1, -0.133), s.get("number_mat", trim), "chest")
    if s["bottom"] == "kilt":
        def pleat(q):
            t = math.atan2(q.y, q.x); d = max(0.0, 0.60 - q.z) / 0.18
            k = 1 + 0.07 * d * abs(math.sin(5 * t))
            return V((q.x * k, q.y * k, q.z))
        kilt = deform(loft([(0.405, 0.205, 0.172), (0.44, 0.19, 0.160), (0.52, 0.168, 0.135), (0.585, 0.150, 0.118), (0.61, 0.142, 0.112)], 40, None, None, 2.2), pleat)
        def kilt_w(p):
            d = smoothstep(0.58, 0.42, p.z) * 0.7
            return {"pelvis": 1 - d, ("hem_F" if p.y < 0 else "hem_B"): d}
        K.add(kilt, s["bottom_mat"], weights=kilt_w)
        K.add(deform(loft([(0.40, 0.207, 0.174), (0.425, 0.203, 0.170)], 40, None, None, 2.2), pleat), trim, weights=kilt_w)
        K.add(loft([(0.44, 0.15, 0.11), (0.58, 0.14, 0.11)], 24, "flat", None), s["bottom_mat"], "pelvis")
    else:
        shorts = loft([(0.60, 0.145, 0.112), (0.52, 0.17, 0.13), (0.47, 0.19, 0.14)], 32, None, "flat", 2.2)
        K.add(shorts, s["bottom_mat"], "pelvis")
        K.add(superellipsoid((0.30, 0.24, 0.20), 0.6, 0.7, 24, 12, (0, 0.0, 0.445)), s["bottom_mat"], "pelvis")
        for sx in (1, -1):
            leg = loft([(0.36, 0.085, 0.085, HIP_X * sx * 1.12, -0.01), (0.43, 0.095, 0.095, HIP_X * sx * 1.1, -0.005), (0.50, 0.10, 0.10, HIP_X * sx, 0)], 18, "flat", None)
            K.add(leg, s["bottom_mat"], "thigh_L" if sx > 0 else "thigh_R")
            K.add(loft([(0.355, 0.087, 0.087, HIP_X * sx * 1.12, -0.01), (0.375, 0.088, 0.088, HIP_X * sx * 1.12, -0.01)], 18, None, None), s.get("bottom_trim", trim), "thigh_L" if sx > 0 else "thigh_R")
    K.add(loft([(0.90, 0.052, 0.05), (0.99, 0.048, 0.046)], 16, None, None), skin, "neck")
    parts["kit"] = K.build(collection, arm)
    # ---- limbs, gloves, shoes
    A = Builder(s["name"] + "_limbs"); Gl = Builder(s["name"] + "_gloves"); Sh = Builder(s["name"] + "_shoes")
    gs = s["glove_size"]
    for side, sx in (("L", 1.0), ("R", -1.0)):
        r = L[side]; sh, el, gl, fd = r["sh"], r["el"], r["gl"], r["fdir"]
        ud = (el - sh).normalized()
        A.add(ellipsoid(sh, (0.072, 0.07, 0.07), 16, 10), kit, "upperarm_" + side)
        A.add(sweep([sh, sh + ud * 0.12], [0.066, 0.064], 16, 1.0, cap0=False), kit, "upperarm_" + side)
        A.add(sweep([sh + ud * 0.10, sh + ud * 0.125], [0.067, 0.066], 16, 1.0, cap0=False, cap1=False), trim, "upperarm_" + side)
        A.add(sweep([sh + ud * 0.11, el], [0.050, 0.047], 14, 1.0, cap0=False, cap1=False), skin, "upperarm_" + side)
        A.add(ellipsoid(el, (0.049, 0.049, 0.049), 14, 8), skin, "forearm_" + side)
        A.add(sweep([el, gl - fd * (0.06 if s["glove"] else 0.035)], [0.046, 0.041], 14, 1.0, cap0=False, cap1=False), skin, "forearm_" + side)
        M = Matrix.Translation(gl) @ V((0, 0, 1)).rotation_difference(fd).to_matrix().to_4x4()
        if s["glove"] is None:   # bare toy hand (spectators)
            Gl.add(xform(superellipsoid((0.075, 0.06, 0.085), 0.7, 0.8, 14, 8, (0, 0, -0.02)), M), skin, "hand_" + side)
            Gl.add(xform(superellipsoid((0.07, 0.055, 0.06), 0.7, 0.8, 12, 8, (0, 0, 0.04)), M), skin, "fingers_" + side)
            Gl.add(xform(ellipsoid((0, -0.035, 0.0), (0.02, 0.02, 0.03), 8, 6), M), skin, "thumb_" + side)
        else:
          # cuff (flared), palm block, curled finger block, thumb
          Gl.add(xform(loft([(-0.13, 0.058, 0.058), (-0.085, 0.074, 0.072), (-0.05, 0.08, 0.078)], 18, "flat", None), M), s["glove_cuff"], "forearm_" + side)
          Gl.add(xform(superellipsoid((gs[0], gs[1], gs[2] * 0.62), 0.55, 0.6, 22, 14, (0, 0, -0.01)), M), s["glove"], "hand_" + side)
          Gl.add(xform(superellipsoid((gs[0] * 0.96, gs[1] * 1.02, gs[2] * 0.5), 0.6, 0.7, 20, 12, (0, 0.0, 0.07)), M), s["glove"], "fingers_" + side)
          for k in (-1, 0, 1):
              Gl.add(xform(sweep([(gs[0] * 0.28 * k, -gs[1] * 0.52, 0.05), (gs[0] * 0.28 * k, -gs[1] * 0.46, 0.11)], [0.009, 0.009], 6, 1.0), M), s["glove_cuff"], "fingers_" + side)
          Gl.add(xform(superellipsoid((0.05, 0.05, 0.07), 0.7, 0.8, 12, 8, (0.0, -0.06, 0.02)), M), s["glove"], "thumb_" + side)
        # legs
        hip, knee, ank = r["hip"], r["knee"], r["ank"]
        A.add(sweep([hip + V((0, 0, 0.03)), knee], [0.070, 0.058], 16, 1.0), skin, "thigh_" + side)
        A.add(ellipsoid(knee, (0.059, 0.059, 0.059), 14, 8), skin, "shin_" + side)
        kd = (ank - knee).normalized()
        A.add(sweep([knee + kd * 0.035, ank + V((0, 0, 0.01))], [0.060, 0.052], 16, 1.0, cap0=False), s["sock"], "shin_" + side)
        for t in (0.10, 0.22):
            q = knee + kd * (0.035 + t * 0.2)
            A.add(sweep([q, q + kd * 0.018], [0.062, 0.062], 16, 1.0, cap0=False, cap1=False), s["sock_stripe"], "shin_" + side)
        fx = HIP_X * sx
        kS = s.get("shoe_k", 1.0); Ms = Matrix.Translation((fx, -0.02, 0)) @ Matrix.Scale(kS, 4) @ Matrix.Translation((-fx, 0.02, 0))
        Sh.add(xform(superellipsoid((0.135, 0.245, 0.045), 0.4, 0.5, 22, 10, (fx, -0.045, 0.0225)), Ms), "rubber_dark", "foot_" + side)
        Sh.add(xform(superellipsoid((0.125, 0.19, 0.10), 0.6, 0.55, 22, 12, (fx, -0.02, 0.075)), Ms), s["shoe"], "foot_" + side)
        Sh.add(xform(superellipsoid((0.12, 0.10, 0.075), 0.6, 0.6, 18, 10, (fx, -0.115, 0.058)), Ms), s["shoe"], "toe_" + side)
        Sh.add(xform(superellipsoid((0.128, 0.06, 0.05), 0.6, 0.6, 14, 8, (fx, 0.07, 0.09)), Ms), s["shoe_accent"], "foot_" + side)
        Sh.add(xform(sweep([(fx + 0.045 * sx, -0.10, 0.06), (fx + 0.064 * sx, -0.02, 0.085), (fx + 0.064 * sx, 0.05, 0.07)], [0.012, 0.014, 0.01], 6, 0.5, up=(sx, 0, 0)), Ms), s["shoe_accent"], "foot_" + side)
    parts["limbs"] = A.build(collection, arm)
    parts["gloves"] = Gl.build(collection, arm)
    parts["shoes"] = Sh.build(collection, arm)
    if s.get("chest_protector"):
        C = Builder(s["name"] + "_chest_protector")
        pm, pa = s.get("protector_mat", "plastic_white"), s.get("protector_accent", "plastic_blue")
        C.add(superellipsoid((0.40, 0.10, 0.28), 0.45, 0.5, 26, 16, (0, -0.10, 0.765)), pm, "chest_pad")
        for k, z in enumerate((0.84, 0.70)):
            C.add(superellipsoid((0.34 - 0.03 * k, 0.03, 0.025), 0.4, 0.4, 20, 8, (0, -0.152, z)), pa, "chest_pad")
        num_c = text_mesh("num_c", s["number"] or " ", 0.12, collection, 0.012)
        C.add(xform(num_c, Matrix.Translation((0, -0.156, 0.77)) @ Matrix.Rotation(math.radians(90), 4, "X")), s.get("number_mat", "kit_white"), "chest_pad")
        for sx in (1, -1):
            C.add(superellipsoid((0.15, 0.20, 0.08), 0.5, 0.6, 18, 10, (0.16 * sx, -0.01, 0.905)), pm, "chest")
        parts["chest_protector"] = C.build(collection, arm)
    return parts

# ------------------------------------------------------------------ sticks (built in stick-local space, then placed on stick bone)
def stick_geo(kind="attack"):
    """Returns dict of geo lists in stick space: +Y along shaft toward head, +Z pocket open face, origin = top-hand grip."""
    if kind == "attack":   # sized for the recommended 0.08 m visual ball radius
        W, y0, y1, depth, shaft0, shaft1 = 0.128, 0.28, 0.64, 0.068, -0.50, 0.30
    else:
        W, y0, y1, depth, shaft0, shaft1 = 0.185, 0.32, 0.86, 0.10, -0.62, 0.34
    L = y1 - y0
    def outline(t):  # t in [0,1): teardrop, t=0 at scoop top center, going around
        a = 2 * math.pi * t
        c, s = math.cos(a), math.sin(a)
        u = (1 + c) / 2  # 1 at top, 0 at throat
        x = W * s * (0.30 + 0.70 * u ** 0.55)
        y = y0 + L * u
        z = 0.035 * max(0.0, (u - 0.80) / 0.20) ** 2   # scoop curls toward the open face
        return V((x, y, z))
    g = {}
    n = 40
    loop = [outline(i / n) for i in range(n)] + [outline(0)]
    g["frame"] = [sweep(loop, [0.024] * len(loop), 10, 0.42, cap0=False, cap1=False, up=(0, 0, 1))]
    g["frame"].append(sweep([(0, shaft1 - 0.02, 0), (0, y0 + 0.01, 0)], [0.024, 0.018], 10, 1.0))
    g["shaft"] = [sweep([(0, shaft0, 0), (0, shaft1, 0)], [0.019, 0.019], 12, 1.0)]
    g["grip"] = [sweep([(0, shaft0 + 0.012, 0), (0, shaft0 + 0.06, 0)], [0.024, 0.023], 12, 1.0),
                 sweep([(0, -0.04, 0), (0, 0.04, 0)], [0.0215, 0.0215], 12, 1.0, cap0=False, cap1=False)]
    # pocket: bag surface below the frame (toward -Z), woven diamonds with enlarged cord
    def bag(u, v):  # u across [-1,1], v along [0,1]
        o = outline(0.5 - 0.5 * (1 - v) * 0 + 0.0)
        y = y0 + L * v
        half = W * (0.30 + 0.70 * v ** 0.55) * 0.93
        x = half * u
        deep = depth * (1 - u * u) * math.sin(math.pi * min(1.0, v * 1.05)) ** 1.2 * (1.0 - 0.35 * v)
        return V((x, y, -deep))
    cords = []
    for k in range(-5, 6):  # two diagonal families
        for sgn in (1, -1):
            pts = []
            for i in range(13):
                v = i / 12
                u = sgn * (k / 5.0 + (v - 0.5) * 1.2)
                if -1 <= u <= 1 and 0.02 <= v <= 0.97:
                    pts.append(tuple(bag(u, v)))
            if len(pts) >= 3:
                cords.append(sweep(pts, [0.0045] * len(pts), 6, 1.0))
    g["pocket"] = cords
    g["strings"] = []
    for v in (0.80, 0.86):
        pts = [tuple(bag(u / 6.0, v) + V((0, 0, 0.006))) for u in range(-6, 7)]
        g["strings"].append(sweep(pts, [0.006] * len(pts), 6, 1.0))
    vb = 0.42; bottom = bag(0.0, vb)
    g["meta"] = dict(y0=y0, y1=y1, W=W, depth=depth, ball_r=BALL_R,
                     pocket_center=(0.0, bottom.y, bottom.z + BALL_R + 0.006),   # = resting ball center
                     ball_contact=(0.0, bottom.y, bottom.z), shaft=(shaft0, shaft1),
                     grip=(0.0, 0.0, 0.0), effect=(0.0, y1 + 0.02, 0.0))
    return g

def build_stick(kind, collection, arm=None, bone="stick", name=None, frame_mat="plastic_white", pocket_mat="cord_navy"):
    g = stick_geo(kind)
    B = Builder(name or ("stick_" + kind))
    M = arm.data.bones[bone].matrix_local.copy() if arm is not None else Matrix.Identity(4)
    Minv = M.inverted()
    y0 = g["meta"]["y0"]; L = g["meta"]["y1"] - y0; depth = g["meta"]["depth"]
    pc = V(g["meta"]["pocket_center"])
    def pocket_w(p_world):
        p = Minv @ p_world
        d = min(1.0, max(0.0, -p.z / depth))
        v = (p.y - y0) / L
        w2 = d * smoothstep(0.55, 0.8, v); w1 = d * (1 - smoothstep(0.55, 0.8, v))
        return {"stick": max(0.0, 1 - w1 - w2), "pocket_01": w1, "pocket_02": w2}
    for key, m in (("frame", frame_mat), ("shaft", "plastic_dark"), ("grip", "rubber_dark"), ("strings", "kit_white")):
        for geo in g[key]:
            B.add(xform(geo, M), m, bone)
    for geo in g["pocket"]:
        B.add(xform(geo, M), pocket_mat, weights=pocket_w if arm is not None else None)
    ob = B.build(collection, arm)
    return ob, g["meta"]

def ball_geo(center=(0, 0, 0), r=None):
    r = BALL_R if r is None else r
    return ellipsoid(center, (r, r, r), 20, 12)

# ------------------------------------------------------------------ sockets
def add_socket(name, arm, bone, world, collection, size=0.06):
    e = bpy.data.objects.new(name, None); e.empty_display_type = "ARROWS"; e.empty_display_size = size
    collection.objects.link(e)
    e.parent = arm; e.parent_type = "BONE"; e.parent_bone = bone
    bpy.context.view_layer.update()
    e.matrix_world = world
    return e

C_MAT = Euler((math.radians(90), 0, math.radians(180)), "XYZ").to_matrix().to_4x4()

def add_character_sockets(s, arm, collection, stick_meta):
    H = Head(s); body, head = prop_xf(s)
    ad = arm.data
    ad.pose_position = "REST"; bpy.context.view_layer.update()
    Ms = ad.bones["stick"].matrix_local.copy()
    S = {}
    S["stick_socket"] = add_socket("stick_socket", arm, "stick", Ms, collection)
    S["pocket_socket"] = add_socket("pocket_socket", arm, "pocket_01", Ms @ Matrix.Translation(stick_meta["pocket_center"]), collection, 0.04)
    S["helmet_socket"] = add_socket("helmet_socket", arm, "head", Matrix.Translation(head(H.c)) @ C_MAT, collection, 0.12)
    S["eyes_socket"] = add_socket("eyes_socket", arm, "head", Matrix.Translation(head(H.point(0, s["eye_el"], 1.0))) @ C_MAT, collection, 0.05)
    S["camera_focus_socket"] = add_socket("camera_focus_socket", arm, "chest", Matrix.Translation(body((0, 0, 0.95))) @ C_MAT, collection, 0.08)
    S["chest_socket"] = add_socket("chest_socket", arm, "chest", Matrix.Translation(body((0, -0.14, 0.78))) @ C_MAT, collection, 0.06)
    S["effect_socket"] = add_socket("effect_socket", arm, "chest", Matrix.Translation(body((0, -0.15, 0.80))) @ C_MAT, collection, 0.08)
    for side, key in (("L", "left_hand_socket"), ("R", "right_hand_socket")):
        S[key] = add_socket(key, arm, "hand_" + side, ad.bones["hand_" + side].matrix_local.copy(), collection, 0.05)
    ad.pose_position = "POSE"; bpy.context.view_layer.update()
    return S

# ------------------------------------------------------------------ face poses (bone-driven; values per bone)
# lid scale: 1 = closed, 0.1 = open. jaw scale: 1 = open mouth, 0.16 = closed smile line.
FACE = {
    "neutral":     dict(lid=0.10, jaw=0.14, mouth=(0.004, 0.0), brow=(0.0, 0.0), eye=(0, 0)),
    "blink":       dict(lid=1.00, jaw=0.14, mouth=(0.004, 0.0), brow=(-0.006, 0.0), eye=(0, 0)),
    "focused":     dict(lid=0.36, jaw=0.12, mouth=(-0.003, 0.0), brow=(-0.010, 16.0), eye=(0, 0)),
    "determined":  dict(lid=0.22, jaw=0.18, mouth=(-0.008, 0.0), brow=(-0.013, 24.0), eye=(0, 0)),
    "smile":       dict(lid=0.16, jaw=0.34, mouth=(0.013, 0.006), brow=(0.007, -6.0), eye=(0, 0)),
    "big_smile":   dict(lid=0.24, jaw=1.00, mouth=(0.016, 0.009), brow=(0.017, -10.0), eye=(0, 0)),
    "strain":      dict(lid=0.58, jaw=0.50, mouth=(-0.012, 0.010), brow=(-0.016, 28.0), eye=(0, 0)),
    "surprise":    dict(lid=0.02, jaw=0.90, mouth=(-0.004, -0.010), brow=(0.026, -8.0), eye=(0, 0)),
    "disappointed":dict(lid=0.36, jaw=0.24, mouth=(-0.005, -0.002), brow=(0.010, -22.0), eye=(0, -7)),
    "smirk":       dict(lid=0.30, jaw=0.18, mouth=(0.016, 0.0), brow=(0.006, 10.0), eye=(5, 0), asym=True),
}

def lid_rot(arm, lid):     # lid preset value: 0.1 open .. 1.0 closed  ->  hinge rotation (radians), no joint scale
    c = min(1.0, max(0.0, (lid - 0.1) / 0.9))
    return (-math.radians(arm.get("lid_open_deg", 30.0) * c), 0, 0)   # 0 = authored open; closing rotates down

def jaw_rot(arm, jaw):     # jaw preset value: 0.14 closed line .. 1.0 open  ->  cover rotates down
    o = min(1.0, max(0.0, (jaw - 0.14) / 0.86))
    return (-math.radians(arm.get("mouth_open_deg", 15.0) * o), 0, 0)

def surface_patch(H, az0, az1, el0, el1, off, nu=12, nv=10):
    """Skin patch hugging the head; its border tapers flush with the skin so no step or shadow line shows."""
    verts, faces = [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            az = az0 + (az1 - az0) * i / nu; el = el0 + (el1 - el0) * j / nv
            p, tx, n, tu = H.frame(az, el)
            edge = min(i / nu, 1 - i / nu, j / nv, 1 - j / nv)
            o = 0.0004 + (off - 0.0004) * smoothstep(0.0, 0.16, edge)
            verts.append(tuple(p + n * o))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return verts, faces

def apply_face(arm, name, eye_aim=None):
    f = FACE[name]; pb = arm.pose.bones
    for side, sx in (("L", 1), ("R", -1)):
        pb["lid_" + side].rotation_euler = lid_rot(arm, f["lid"])
        du, rot = f["brow"]
        pb["brow_" + side].location = (0, 0, du)
        pb["brow_" + side].rotation_euler = (0, math.radians(rot * -sx), 0)
        mu, mo = f["mouth"]
        k = 1.0 if not f.get("asym") or side == "L" else 0.0
        pb["mouth_" + side].location = (-mo * sx * k, 0, mu * k)
        ex, ez = eye_aim if eye_aim else f["eye"]
        pb["eye_" + side].rotation_euler = (math.radians(ez), 0, math.radians(-ex))
    pb["jaw"].rotation_euler = jaw_rot(arm, f["jaw"])
