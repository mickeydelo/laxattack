# Lax Attack pose model (shared by field + goalie families). Generalized from the graybox build.
# A pose = body rotations + pelvis offset + foot offsets + stick frame (G grip, D shaft dir, F pocket face) + face.
STANCE = {"field": {"L": V((0.035, -0.03, 0)), "R": V((-0.035, 0.045, 0))},
          "goalie": {"L": V((0.13, -0.01, 0)), "R": V((-0.13, -0.01, 0))}}

BASE_FIELD = dict(pelvis_off=(0, 0, -0.035), pelvis_rot=(0, -6, 0), spine_rot=(6, -4, 0), chest_rot=(4, -4, 0),
                  neck_rot=(-4, 4, 0), head_rot=(-6, 8, 0), footL=(0, 0, 0), footR=(0, 0, 0),
                  G=(-0.24, -0.25, 0.86), D=(-0.60, 0.05, 0.80), F=(0.55, -0.83, 0.10),
                  hair=(0, 0, 0), hem=(0, 0), face="neutral", eye=(0, 0), pocket=0.0, fingers=0.0, feet_yaw=0.0)
BASE_GOALIE = dict(pelvis_off=(0, 0, -0.085), pelvis_rot=(8, 0, 0), spine_rot=(6, 0, 0), chest_rot=(2, 0, 0),
                   neck_rot=(-6, 0, 0), head_rot=(-8, 0, 0), footL=(0, 0, 0), footR=(0, 0, 0),
                   G=(-0.21, -0.30, 0.98), D=(-0.10, -0.12, 0.99), F=(0.0, -1.0, 0.1),
                   hair=(0, 0, 0), hem=(0, 0), face="focused", eye=(0, 0), pocket=0.0, fingers=0.0, feet_yaw=0.0)

def P(base, **kw):
    p = {k: (tuple(v) if isinstance(v, (tuple, list)) else v) for k, v in base.items()}
    for k, v in kw.items():
        p[k] = None if v is None else (tuple(v) if isinstance(v, (tuple, list)) else v)
    return p

def orth(f, d):
    d = V(d).normalized(); f = V(f); f = f - f.dot(d) * d
    return f.normalized()

def finalize(p):
    p["D"] = tuple(V(p["D"]).normalized()); p["F"] = tuple(orth(p["F"], p["D"]))
    return p

def vslerp(a, b, t):
    a = V(a).normalized(); b = V(b).normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    if d > 0.9995:
        return a.lerp(b, t).normalized()
    ang = math.acos(d); s = math.sin(ang)
    return (a * math.sin((1 - t) * ang) + b * math.sin(t * ang)) / s

def lerp_pose(p, q, t):
    r = {}
    for k in p:
        if k in ("D", "F"):
            continue
        a, b = p[k], q[k]
        if isinstance(a, str):
            r[k] = a if t < 0.5 else b
        elif isinstance(a, tuple):
            r[k] = tuple(x + (y - x) * t for x, y in zip(a, b))
        else:
            r[k] = a + (b - a) * t
    r["D"] = tuple(vslerp(p["D"], q["D"], t)); r["F"] = tuple(orth(vslerp(p["F"], q["F"], t), r["D"]))
    # face blends numerically between presets
    r["_face_a"], r["_face_b"], r["_face_t"] = p.get("face"), q.get("face"), t
    return r

EASE = {"io": lambda t: t * t * (3 - 2 * t), "in": lambda t: t * t, "out": lambda t: 1 - (1 - t) ** 2,
        "lin": lambda t: t, "snap": lambda t: t ** 3, "back": lambda t: 1 - (1 - t) ** 2 * (1 - 2.2 * t) if t < 1 else 1}

def prep_keys(keys):
    out = []; prev = None
    for f, p, e in keys:
        p = dict(p); p["D"] = tuple(V(p["D"]).normalized())
        if p["F"] is None:
            p["F"] = tuple(V(prev["D"]).rotation_difference(V(p["D"])) @ V(prev["F"]))
        p = finalize(p); out.append((f, p, e)); prev = p
    return out

def sample_keys(keys, f):
    for (f0, p0, _), (f1, p1, e) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            return lerp_pose(p0, p1, EASE[e]((f - f0) / (f1 - f0)))
    return keys[-1][1]

def face_values(p):
    a = FACE[p.get("_face_a") or p["face"]]; b = FACE[p.get("_face_b") or p["face"]]; t = p.get("_face_t", 0.0)
    L = lambda x, y: x + (y - x) * t
    return dict(lid=L(a["lid"], b["lid"]), jaw=L(a["jaw"], b["jaw"]),
                mouth=(L(a["mouth"][0], b["mouth"][0]), L(a["mouth"][1], b["mouth"][1])),
                brow=(L(a["brow"][0], b["brow"][0]), L(a["brow"][1], b["brow"][1])),
                asym=a.get("asym") if t < 0.5 else b.get("asym"))

def set_loc_world(pb, delta):
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ V(delta)

def apply_pose(arm, p, family="field", blink=None):
    pbs = arm.pose.bones
    for n in ("pelvis", "spine", "chest", "neck", "head"):
        pbs[n].rotation_euler = Euler([math.radians(a) for a in p[n + "_rot"]], "XYZ")
    bs = arm.get("body_scale", 1.0)
    set_loc_world(pbs["pelvis"], V(p["pelvis_off"]) * bs)
    base_z = BASE_GOALIE["pelvis_off"][2] if family == "goalie" else BASE_FIELD["pelvis_off"][2]
    lift = max(0.0, p["pelvis_off"][2] - base_z - 0.05) if family == "field" else max(0.0, p["pelvis_off"][2] - base_z - 0.10)
    st = STANCE[family]
    fy = math.radians(p.get("feet_yaw", 0.0)); Rf = Matrix.Rotation(fy, 3, "Z")   # feet follow body turns (roll dodges)
    for sd in ("L", "R"):
        rest = pbs["ik_foot_" + sd].bone.head_local.copy(); rest.z = 0.0
        tgt = Rf @ (rest + (st[sd] + V(p["foot" + sd]) + V((0, 0, lift))) * bs) - rest
        set_loc_world(pbs["ik_foot_" + sd], tgt)
        pbs["ik_foot_" + sd].rotation_euler = (0, 0, fy)
    yaw = p["pelvis_rot"][1] + p["spine_rot"][1] + p["chest_rot"][1]   # bone-local Y of the up-pointing spine = world yaw
    Rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    G = (V(p["pelvis_off"]) + Rz @ V(p["G"])) * bs
    D = (Rz @ V(p["D"])).normalized(); F = orth(Rz @ V(p["F"]), D); X = D.cross(F)
    pbs["stick"].matrix = Matrix(((X.x, D.x, F.x, G.x), (X.y, D.y, F.y, G.y), (X.z, D.z, F.z, G.z), (0, 0, 0, 1)))
    pbs["stick"].scale = (1, 1, 1)
    # secondary + face
    h = p["hair"]
    for i, n in enumerate(("hair_01", "hair_02", "hair_03")):
        pbs[n].rotation_euler = Euler((math.radians(h[0] * (0.5 + 0.5 * i)), 0, math.radians(h[1] * (0.5 + 0.5 * i))), "XYZ")
    pbs["hem_F"].rotation_euler = Euler((math.radians(p["hem"][0]), 0, 0), "XYZ")
    pbs["hem_B"].rotation_euler = Euler((math.radians(p["hem"][1]), 0, 0), "XYZ")
    pbs["pocket_01"].location = (0, 0, -p["pocket"])
    pbs["pocket_02"].location = (0, 0, -p["pocket"] * 0.4)
    for s in ("L", "R"):
        pbs["fingers_" + s].rotation_euler = Euler((math.radians(p["fingers"]), 0, 0), "XYZ")
    fv = face_values(p)
    for side, sx in (("L", 1), ("R", -1)):
        lid = 1.0 if blink else fv["lid"]
        pbs["lid_" + side].rotation_euler = lid_rot(arm, lid)
        pbs["brow_" + side].location = (0, 0, fv["brow"][0])
        pbs["brow_" + side].rotation_euler = (0, math.radians(fv["brow"][1] * -sx), 0)
        k = 1.0 if not fv["asym"] or side == "L" else 0.0
        pbs["mouth_" + side].location = (-fv["mouth"][1] * sx * k, 0, fv["mouth"][0] * k)
        ex, ez = p["eye"]
        pbs["eye_" + side].rotation_euler = (math.radians(ez), 0, math.radians(-ex))
    pbs["jaw"].rotation_euler = jaw_rot(arm, fv["jaw"])

def calibrate_poles(arm, poses, family):
    def evaluated():
        return arm.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones
    out = {}
    for owner, mid, pole, use in (("forearm_R", "upperarm_R", "pole_elbow_R", poses), ("forearm_L", "upperarm_L", "pole_elbow_L", poses),
                                  ("shin_R", "thigh_R", "pole_knee_R", poses[:1]), ("shin_L", "thigh_L", "pole_knee_L", poses[:1])):
        con = arm.pose.bones[owner].constraints["IK"]
        def cost(a):
            con.pole_angle = math.radians(a); tot = 0.0
            for p in use:
                apply_pose(arm, p, family); bpy.context.view_layer.update()
                e = evaluated(); tot += (e[mid].tail - e[pole].head).length
            return tot
        best = min(range(-180, 180, 15), key=cost)
        best = min(range(best - 14, best + 15, 2), key=cost)
        con.pole_angle = math.radians(best); out[owner] = best
    return out
