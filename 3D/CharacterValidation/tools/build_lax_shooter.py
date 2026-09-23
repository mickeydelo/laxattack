# Lax Attack - graybox character validation build script
# Builds lax_shooter (mesh, rig, sockets, 4 clips) inside Blender 5.2.
# Authoring space: Blender Z-up, character faces -Y, character's right = -X.
# Export (see export step): USD Y-up, forward=Z  ->  Blender -Y maps to USD -Z.
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

REPO = os.path.expanduser("~/Developer/laxattack")
OUT = os.path.join(REPO, "3D", "CharacterValidation")
os.makedirs(OUT, exist_ok=True)
FPS = 30
RIG = "lax_shooter_rig"
REPORT = {}

# ------------------------------------------------------------------ reset
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions,
             bpy.data.cameras, bpy.data.lights, bpy.data.curves):
    for d in list(coll):
        coll.remove(d)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
scene.name = "LaxAttackCharacters"
us = scene.unit_settings
us.system = "METRIC"
us.scale_length = 1.0
us.length_unit = "METERS"
scene.render.fps = FPS
scene.render.fps_base = 1.0

col = bpy.data.collections.new("lax_shooter")
scene.collection.children.link(col)
pcol = bpy.data.collections.new("preview_not_exported")
scene.collection.children.link(pcol)

# ------------------------------------------------------------------ materials
def make_mat(name, rgb, rough=0.65):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        outn = nt.nodes.get("Material Output") or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], outn.inputs[0])
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return m

M_JERSEY = make_mat("M_Jersey", (0.80, 0.10, 0.06))
M_NAVY = make_mat("M_Navy", (0.012, 0.03, 0.14))
M_SKIN = make_mat("M_Skin", (0.66, 0.37, 0.21))
M_DARK = make_mat("M_Dark", (0.012, 0.012, 0.018), 0.5)
M_WHITE = make_mat("M_White", (0.85, 0.85, 0.83), 0.55)
MATS = [M_JERSEY, M_NAVY, M_SKIN, M_DARK, M_WHITE]

# ------------------------------------------------------------------ mesh helpers
def new_bm():
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    return bm

def prim_box(size, M=None, bevel=0.35, segs=2):
    bm = new_bm()
    M = M or Matrix.Identity(4)
    S = Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M @ S, calc_uvs=True)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                        offset=min(size) * bevel * 0.5, offset_type="OFFSET",
                        segments=segs, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm

def prim_sphere(center, radii, u=20, v=12):
    bm = new_bm()
    M = Matrix.Translation(center) @ Matrix.Diagonal((radii[0], radii[1], radii[2], 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0, matrix=M, calc_uvs=True)
    return bm

def prim_cyl(p0, p1, r0, r1=None, segs=14):
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    M = Matrix.Translation((p0 + p1) / 2) @ rot
    bm = new_bm()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r0,
                          radius2=r0 if r1 is None else r1, depth=d.length, matrix=M, calc_uvs=True)
    return bm

def prim_head_frame(n=28, thick=0.009, hd=0.022):
    # Teardrop lacrosse head frame in stick space (X lateral, Y along shaft, Z pocket face)
    bm = new_bm()
    def outline(t):
        c = math.cos(t); s = math.sin(t)
        return Vector((0.095 * s * (0.45 + 0.55 * ((1 + c) / 2) ** 0.6), 0.37 + 0.12 * c))
    pts = [outline(2 * math.pi * i / n) for i in range(n)]
    ring = []
    for i in range(n):
        tan = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        nrm = Vector((-tan.y, tan.x))
        o = pts[i] + nrm * thick; q = pts[i] - nrm * thick
        ring.append([bm.verts.new((o.x, o.y, hd)), bm.verts.new((o.x, o.y, -hd)),
                     bm.verts.new((q.x, q.y, hd)), bm.verts.new((q.x, q.y, -hd))])
    for i in range(n):
        a = ring[i]; b = ring[(i + 1) % n]
        bm.faces.new((a[0], b[0], b[1], a[1]))
        bm.faces.new((a[2], a[3], b[3], b[2]))
        bm.faces.new((a[0], a[2], b[2], b[0]))
        bm.faces.new((a[1], b[1], b[3], a[3]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

class MeshBuilder:
    def __init__(self):
        self.verts = []; self.faces = []; self.fmat = []; self.fsmooth = []; self.fuv = []; self.vgroup = []
    def add(self, bm, mat, group, smooth=True, xform=None):
        if xform is not None:
            bmesh.ops.transform(bm, matrix=xform, verts=list(bm.verts))
        uvl = bm.loops.layers.uv.active
        bm.verts.index_update()
        base = len(self.verts)
        for v in bm.verts:
            self.verts.append(tuple(v.co)); self.vgroup.append(group)
        for f in bm.faces:
            self.faces.append(tuple(base + v.index for v in f.verts))
            self.fmat.append(MATS.index(mat)); self.fsmooth.append(smooth)
            self.fuv.append([tuple(l[uvl].uv) if uvl else (0.0, 0.0) for l in f.loops])
        bm.free()
    def build(self, name, arm):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        for m in MATS:
            me.materials.append(m)
        for i, p in enumerate(me.polygons):
            p.material_index = self.fmat[i]; p.use_smooth = self.fsmooth[i]
        uv = me.uv_layers.new(name="UVMap")
        for i, p in enumerate(me.polygons):
            for k, li in enumerate(p.loop_indices):
                uv.data[li].uv = self.fuv[i][k]
        me.update()
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        groups = {}
        for i, g in enumerate(self.vgroup):
            groups.setdefault(g, []).append(i)
        for g, idx in groups.items():
            ob.vertex_groups.new(name=g).add(idx, 1.0, "REPLACE")
        ob.parent = arm
        ob.modifiers.new("Armature", "ARMATURE").object = arm
        # drop unused material slots to keep the export lean
        used = sorted(set(self.fmat))
        return ob, used

# ------------------------------------------------------------------ armature
SH = 0.18            # shoulder half-width
UPPER = 0.23; FORE = 0.26   # forearm bone ends at the glove centre
A = math.radians(50) # A-pose arm angle below horizontal
GRIP_SPREAD = 0.28   # top-hand to bottom-hand distance along the shaft

arm_data = bpy.data.armatures.new(RIG)
arm = bpy.data.objects.new(RIG, arm_data)
col.objects.link(arm)
arm.show_in_front = True
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones

def bone(name, head, tail, parent=None, deform=True, connect=False, align_z=None):
    b = eb.new(name); b.head = head; b.tail = tail
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    b.use_deform = deform
    if align_z is not None:
        b.align_roll(Vector(align_z))
    return b

bone("root", (0, 0, 0), (0, 0, 0.2))
bone("pelvis", (0, 0, 0.53), (0, 0, 0.64), "root")
bone("spine", (0, 0, 0.64), (0, 0, 0.78), "pelvis", connect=True)
bone("chest", (0, 0, 0.78), (0, 0, 0.97), "spine", connect=True)
bone("neck", (0, 0, 0.97), (0, 0, 1.03), "chest", connect=True)
bone("head", (0, 0, 1.03), (0, 0, 1.43), "neck", connect=True)
REST = {}
for s, sx in (("L", 1.0), ("R", -1.0)):
    sh = Vector((SH * sx, 0, 0.92))
    el = sh + Vector((UPPER * math.cos(A) * sx, 0.02, -UPPER * math.sin(A)))
    gl = el + Vector((FORE * math.cos(A) * sx, -0.04, -FORE * math.sin(A)))
    hd = gl + (gl - el).normalized() * 0.06
    REST[s] = dict(shoulder=sh, elbow=el, glove=gl)
    bone("clavicle_" + s, (0.03 * sx, 0, 0.90), sh, "chest")
    bone("upperarm_" + s, sh, el, "clavicle_" + s, connect=True)
    bone("forearm_" + s, el, gl, "upperarm_" + s, connect=True)
    bone("hand_" + s, gl, hd, "forearm_" + s, connect=True)
    bone("thigh_" + s, (0.09 * sx, 0, 0.50), (0.09 * sx, -0.025, 0.29), "pelvis")
    bone("shin_" + s, (0.09 * sx, -0.025, 0.29), (0.09 * sx, 0, 0.08), "thigh_" + s, connect=True)
    bone("foot_" + s, (0.09 * sx, 0, 0.08), (0.09 * sx, -0.12, 0.03), "shin_" + s, connect=True)
    bone("ik_foot_" + s, (0.09 * sx, 0, 0.08), (0.09 * sx, -0.12, 0.03), "root", deform=False)
    bone("pole_knee_" + s, (0.13 * sx, -0.7, 0.30), (0.13 * sx, -0.7, 0.36), "root", deform=False)
    bone("pole_elbow_" + s, (0.55 * sx, 0.40, 0.62), (0.55 * sx, 0.40, 0.68), "chest", deform=False)
g0 = REST["R"]["glove"]
bone("stick", g0, g0 + Vector((0, 0, 0.22)), "root", align_z=(0, -1, 0))
bone("ik_hand_R", g0, g0 + Vector((0, 0, 0.05)), "stick", deform=False)
bone("ik_hand_L", g0 + Vector((0, 0, -GRIP_SPREAD)), g0 + Vector((0, 0, -GRIP_SPREAD + 0.05)), "stick", deform=False)
bpy.ops.object.mode_set(mode="OBJECT")
M_STICK = arm_data.bones["stick"].matrix_local.copy()

# ------------------------------------------------------------------ body mesh
B = MeshBuilder()
B.add(prim_box((0.36, 0.25, 0.20), Matrix.Translation((0, 0, 0.55))), M_NAVY, "pelvis", False)
B.add(prim_box((0.38, 0.26, 0.16), Matrix.Translation((0, 0, 0.70))), M_JERSEY, "spine", False)
B.add(prim_box((0.42, 0.28, 0.24), Matrix.Translation((0, 0, 0.86))), M_JERSEY, "chest", False)
B.add(prim_cyl((0, 0, 0.97), (0, 0, 1.0), 0.075), M_NAVY, "chest")
B.add(prim_cyl((0, 0, 0.97), (0, 0, 1.06), 0.055), M_SKIN, "neck")
B.add(prim_sphere((0, 0, 1.23), (0.25, 0.25, 0.25), 28, 16), M_SKIN, "head")
B.add(prim_sphere((0, 0.035, 1.26), (0.262, 0.262, 0.262), 28, 16), M_DARK, "head")
for sx in (1, -1):
    B.add(prim_sphere((0.085 * sx, -0.232, 1.21), (0.036, 0.021, 0.050), 16, 10), M_DARK, "head")
    B.add(prim_sphere((0.072 * sx, -0.255, 1.235), (0.013, 0.013, 0.013), 10, 6), M_WHITE, "head")
    B.add(prim_sphere((0.245 * sx, 0.0, 1.21), (0.025, 0.04, 0.05), 12, 8), M_SKIN, "head")
B.add(prim_sphere((0, -0.215, 1.10), (0.028, 0.008, 0.012), 12, 6), M_DARK, "head")
for s in ("L", "R"):
    r = REST[s]; sh, el, gl = r["shoulder"], r["elbow"], r["glove"]
    fdir = (gl - el).normalized()
    B.add(prim_sphere(sh, (0.066, 0.066, 0.066)), M_JERSEY, "upperarm_" + s)
    B.add(prim_cyl(sh, el, 0.054), M_JERSEY, "upperarm_" + s)
    B.add(prim_sphere(el, (0.05, 0.05, 0.05)), M_SKIN, "forearm_" + s)
    B.add(prim_cyl(el, gl - fdir * 0.05, 0.046), M_SKIN, "forearm_" + s)
    B.add(prim_cyl(gl - fdir * 0.11, gl - fdir * 0.05, 0.064), M_NAVY, "forearm_" + s)
    grot = Vector((0, 0, 1)).rotation_difference(fdir).to_matrix().to_4x4()
    B.add(prim_box((0.13, 0.13, 0.13), Matrix.Translation(gl) @ grot, 0.45, 3), M_JERSEY, "hand_" + s, False)
    sx = 1 if s == "L" else -1
    hip = Vector((0.09 * sx, 0, 0.50)); knee = Vector((0.09 * sx, -0.025, 0.29)); ank = Vector((0.09 * sx, 0, 0.08))
    B.add(prim_cyl(hip + Vector((0, 0, 0.03)), hip + Vector((0, 0, -0.09)), 0.082), M_NAVY, "thigh_" + s)
    B.add(prim_cyl(hip, knee, 0.062), M_SKIN, "thigh_" + s)
    B.add(prim_sphere(knee, (0.062, 0.062, 0.062)), M_SKIN, "shin_" + s)
    B.add(prim_cyl(knee, ank, 0.058), M_WHITE, "shin_" + s)
    B.add(prim_box((0.13, 0.21, 0.085), Matrix.Translation((0.09 * sx, -0.035, 0.0425)), 0.5, 2), M_DARK, "foot_" + s, False)
body, _ = B.build("lax_shooter_body", arm)

# ------------------------------------------------------------------ stick mesh (built in stick space)
S = MeshBuilder()
S.add(prim_cyl((0, -0.50, 0), (0, 0.24, 0), 0.016, segs=10), M_DARK, "stick", xform=M_STICK)
S.add(prim_cyl((0, -0.515, 0), (0, -0.48, 0), 0.021, segs=10), M_DARK, "stick", xform=M_STICK)
S.add(prim_cyl((0, 0.22, 0), (0, 0.265, 0), 0.02, 0.014, segs=10), M_WHITE, "stick", xform=M_STICK)
S.add(prim_head_frame(), M_WHITE, "stick", False, xform=M_STICK)
S.add(prim_sphere((0, 0.365, -0.012), (0.072, 0.105, 0.028), 16, 8), M_NAVY, "stick", xform=M_STICK)
stick_mesh, _ = S.build("lax_shooter_stick", arm)

# ------------------------------------------------------------------ sockets (empties)
C_MAT = Euler((math.radians(90), 0, math.radians(180)), "XYZ").to_matrix().to_4x4()  # = export axis conversion; makes socket frame identity (Y-up, -Z forward) in USD root space
arm_data.pose_position = "REST"
bpy.context.view_layer.update()
def socket(name, bone_name, world, size=0.08):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "ARROWS"; e.empty_display_size = size
    col.objects.link(e)
    e.parent = arm; e.parent_type = "BONE"; e.parent_bone = bone_name
    bpy.context.view_layer.update()
    e.matrix_world = world
    return e
socket("stick_socket", "stick", M_STICK.copy())
socket("pocket_socket", "stick", M_STICK @ Matrix.Translation((0, 0.365, 0)), 0.05)
socket("helmet_socket", "head", Matrix.Translation((0, 0, 1.23)) @ C_MAT, 0.15)
socket("effect_socket", "chest", Matrix.Translation((0, -0.17, 0.86)) @ C_MAT, 0.1)
bpy.context.view_layer.update()
arm_data.pose_position = "POSE"

# ------------------------------------------------------------------ constraints
pbs = arm.pose.bones
for s in ("L", "R"):
    c = pbs["forearm_" + s].constraints.new("IK")
    c.target = arm; c.subtarget = "ik_hand_" + s
    c.pole_target = arm; c.pole_subtarget = "pole_elbow_" + s
    c.chain_count = 2; c.use_tail = True; c.use_stretch = False; c.iterations = 500
    c = pbs["shin_" + s].constraints.new("IK")
    c.target = arm; c.subtarget = "ik_foot_" + s
    c.pole_target = arm; c.pole_subtarget = "pole_knee_" + s
    c.chain_count = 2; c.use_tail = True; c.use_stretch = False; c.iterations = 500
    c = pbs["foot_" + s].constraints.new("COPY_ROTATION")
    c.target = arm; c.subtarget = "ik_foot_" + s
for n in ("pelvis", "spine", "chest", "neck", "head"):
    pbs[n].rotation_mode = "XYZ"
pbs["stick"].rotation_mode = "QUATERNION"

# ------------------------------------------------------------------ pose model
STANCE = {"L": Vector((0.035, -0.03, 0)), "R": Vector((-0.035, 0.045, 0))}
V = Vector
def rotY(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Y")
def orth(f, d):
    d = V(d).normalized(); f = V(f); f = f - f.dot(d) * d
    return f.normalized()

BASE = dict(pelvis_off=(0, 0, -0.035), pelvis_rot=(0, -6, 0), spine_rot=(6, -4, 0), chest_rot=(4, -4, 0),
            neck_rot=(-4, 4, 0), head_rot=(-6, 8, 0), footL=(0, 0, 0), footR=(0, 0, 0),
            G=(-0.23, -0.24, 0.87), D=(-0.60, 0.05, 0.80), F=(0.55, -0.83, 0.10))

def P(**kw):
    p = {k: tuple(v) for k, v in BASE.items()}
    for k, v in kw.items():
        p[k] = None if v is None else tuple(v)
    return p

def finalize(p):
    p["D"] = tuple(V(p["D"]).normalized())
    p["F"] = tuple(orth(p["F"], p["D"]))
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
        r[k] = tuple(V(p[k]).lerp(V(q[k]), t))
    r["D"] = tuple(vslerp(p["D"], q["D"], t))
    r["F"] = tuple(orth(vslerp(p["F"], q["F"], t), r["D"]))
    return r

EASE = {"io": lambda t: t * t * (3 - 2 * t), "in": lambda t: t * t,
        "out": lambda t: 1 - (1 - t) ** 2, "lin": lambda t: t}

def prep_keys(keys):
    out = []
    prev = None
    for f, p, e in keys:
        p = dict(p)
        p["D"] = tuple(V(p["D"]).normalized())
        if p["F"] is None:  # carry pocket roll along with the shaft sweep
            p["F"] = tuple(V(prev["D"]).rotation_difference(V(p["D"])) @ V(prev["F"]))
        p = finalize(p)
        out.append((f, p, e)); prev = p
    return out

def sample_keys(keys, f):
    for (f0, p0, _), (f1, p1, e) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            return lerp_pose(p0, p1, EASE[e]((f - f0) / (f1 - f0)))
    return keys[-1][1]

def looped_stick(t_deg_swing, roll_deg, g_off):
    D0 = V(BASE["D"]).normalized(); F0 = orth(BASE["F"], D0)
    R = rotY(t_deg_swing)
    D = R @ D0; F = R @ F0
    F = Matrix.Rotation(math.radians(roll_deg), 3, D) @ F
    return dict(G=tuple(V(BASE["G"]) + V(g_off)), D=tuple(D), F=tuple(F))

# ---- idle: 48-frame breathing / look loop
def idle_pose(t, N=48):
    ph = 2 * math.pi * t / N; s = math.sin(ph); b = 0.5 - 0.5 * math.cos(ph)
    p = P(pelvis_off=(0.006 * s, 0, -0.035 - 0.012 * b), spine_rot=(6 + 1.5 * b, -4, 0),
          chest_rot=(4 + 2.0 * b, -4 + 2 * s, 0), head_rot=(-6 + 2.5 * s, 8 + 5 * s, 3 * s))
    p.update(looped_stick(3 * s, 6 * s, (0.004 * s, 0, -0.004 * b)))
    return finalize(p)

# ---- cradle: 28-frame continuous cradle loop (stick head sweeps ear -> face, wrist roll)
def cradle_pose(t, N=28):
    ph = 2 * math.pi * t / N; s = math.sin(ph); s2 = math.sin(2 * ph); b2 = 0.5 - 0.5 * math.cos(2 * ph)
    p = P(pelvis_off=(0.012 * s, 0, -0.035 - 0.014 * b2), pelvis_rot=(0, -6, 1.5 * s),
          spine_rot=(6, -4, 2 * s), chest_rot=(4, -4 + 6 * s, 0), head_rot=(-6 + 2 * s2, 8 - 5 * s, -1.5 * s))
    p.update(looped_stick(13 * s, 45 * s, (-0.01 * s, -0.012 * s, 0.012 * b2)))
    return finalize(p)

# ---- release_overhand: pose-to-pose, 33 frames, ball release at local frame 14
RELEASE_LOCAL = 14
REL_KEYS = prep_keys([
    (0, P(), "io"),
    (3, P(pelvis_off=(0, -0.01, -0.05), spine_rot=(9, -4, 0), chest_rot=(7, -4, 0),
          G=(-0.23, -0.27, 0.86), D=(-0.55, 0.0, 0.83)), "io"),                                  # counter-dip
    (9, P(pelvis_off=(-0.01, 0.03, -0.07), pelvis_rot=(-2, -18, -3), spine_rot=(-2, -14, -3),
          chest_rot=(-4, -16, 0), neck_rot=(-2, 14, 0), head_rot=(-4, 22, 2),
          G=(-0.25, 0.10, 1.02), D=(-0.30, 0.70, 0.65), F=(0.0, -0.55, 0.84)), "io"),            # loaded
    (11, P(pelvis_off=(-0.012, 0.035, -0.078), pelvis_rot=(-2, -20, -3), spine_rot=(-3, -15, -3),
           chest_rot=(-5, -18, 0), neck_rot=(-2, 16, 0), head_rot=(-4, 24, 2),
           G=(-0.28, 0.13, 1.03), D=(-0.30, 0.74, 0.60), F=(0.0, -0.55, 0.84)), "io"),           # moving hold
    (14, P(pelvis_off=(0.005, -0.03, -0.035), pelvis_rot=(2, 8, 2), spine_rot=(5, 8, 2),
           chest_rot=(6, 10, 0), neck_rot=(-6, -10, 0), head_rot=(-6, -12, 0),
           G=(-0.33, -0.20, 1.10), D=(-0.25, -0.45, 0.86), F=(0.0, -0.85, -0.45)), "in"),        # RELEASE
    (18, P(pelvis_off=(0.01, -0.05, -0.085), pelvis_rot=(5, 14, 3), spine_rot=(8, 12, 3),
           chest_rot=(6, 14, 0), neck_rot=(-6, -14, 0), head_rot=(-8, -18, 0),
           G=(0.02, -0.37, 0.66), D=(0.65, -0.35, -0.67), F=None), "out"),                        # follow-through overshoot
    (23, P(pelvis_off=(0.005, -0.035, -0.06), pelvis_rot=(3, 9, 2), spine_rot=(6, 7, 2),
           chest_rot=(5, 8, 0), neck_rot=(-5, -10, 0), head_rot=(-6, -12, 0),
           G=(-0.01, -0.38, 0.68), D=(0.55, -0.40, -0.73), F=None), "io"),                          # settle back
    (28, P(pelvis_off=(0.0, -0.015, -0.045), pelvis_rot=(1, 0, 1), spine_rot=(6, -1, 1),
           chest_rot=(4, -2, 0), neck_rot=(-4, 0, 0), head_rot=(-6, 2, 0),
           G=(-0.18, -0.32, 0.86), D=(-0.10, -0.75, 0.65), F=(0.55, -0.55, -0.6)), "io"),        # recover
    (33, P(), "io"),
])

# ---- celebrate: 36 frames, crouch -> jump with stick skyward -> land squash -> pumps -> settle
CEL_F = (0.3, -0.95, 0.0)
CEL_KEYS = prep_keys([
    (0, P(), "io"),
    (5, P(pelvis_off=(0, -0.01, -0.10), pelvis_rot=(4, -10, 0), spine_rot=(10, -4, 0), chest_rot=(8, -4, 0),
          neck_rot=(-6, 6, 0), head_rot=(-8, 10, 0), G=(-0.22, -0.30, 0.74), D=(-0.75, 0.0, 0.66)), "io"),
    (9, P(pelvis_off=(0, 0, 0.14), pelvis_rot=(-4, -6, -2), spine_rot=(-6, -4, -2), chest_rot=(-8, -4, 0),
          neck_rot=(-6, 6, 0), head_rot=(-14, 8, 0), G=(-0.30, -0.10, 1.14), D=(-0.35, 0.05, 0.94), F=CEL_F), "in"),
    (12, P(pelvis_off=(0, 0, 0.18), pelvis_rot=(-4, -6, -5), spine_rot=(-6, -4, -4), chest_rot=(-8, -4, -2),
           neck_rot=(-6, 6, 0), head_rot=(-16, 8, 4), G=(-0.30, -0.08, 1.18), D=(-0.25, 0.05, 0.97), F=CEL_F), "out"),
    (16, P(pelvis_off=(0, 0, -0.01), pelvis_rot=(0, -6, -2), spine_rot=(-2, -4, -1), chest_rot=(-4, -4, 0),
           neck_rot=(-5, 6, 0), head_rot=(-10, 8, 2), G=(-0.30, -0.12, 1.08), D=(-0.35, 0.05, 0.94), F=CEL_F), "in"),
    (19, P(pelvis_off=(0, -0.01, -0.10), pelvis_rot=(5, -8, 0), spine_rot=(10, -4, 0), chest_rot=(6, -4, 0),
           neck_rot=(-4, 6, 0), head_rot=(-6, 8, 0), G=(-0.26, -0.16, 0.98), D=(-0.40, 0.0, 0.92), F=CEL_F), "out"),
    (23, P(pelvis_off=(0, 0, -0.025), pelvis_rot=(-2, -8, -4), spine_rot=(-4, -4, -3), chest_rot=(-8, -4, 0),
           neck_rot=(-6, 6, 0), head_rot=(-12, 8, 3), G=(-0.30, -0.10, 1.14), D=(-0.25, 0.05, 0.97), F=CEL_F), "io"),
    (26, P(pelvis_off=(0, 0, -0.05), pelvis_rot=(0, -8, -2), spine_rot=(2, -4, -1), chest_rot=(-3, -4, 0),
           neck_rot=(-5, 6, 0), head_rot=(-9, 8, 2), G=(-0.30, -0.14, 1.04), D=(-0.35, 0.0, 0.94), F=CEL_F), "io"),
    (29, P(pelvis_off=(0, 0, -0.03), pelvis_rot=(-2, -8, -3), spine_rot=(-3, -4, -2), chest_rot=(-7, -4, 0),
           neck_rot=(-6, 6, 0), head_rot=(-11, 8, 3), G=(-0.30, -0.10, 1.12), D=(-0.28, 0.05, 0.96), F=CEL_F), "io"),
    (36, P(), "io"),
])

CLIPS = [  # name, timeline start, local length (frames), loop, pose fn
    ("idle", 0, 48, True, idle_pose),
    ("cradle", 60, 28, True, cradle_pose),
    ("release_overhand", 100, 33, False, lambda t: sample_keys(REL_KEYS, t)),
    ("celebrate", 150, 36, False, lambda t: sample_keys(CEL_KEYS, t)),
]

# ------------------------------------------------------------------ pose application
def set_loc_world(pb, delta):
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ V(delta)

def apply_pose(p):
    for n in ("pelvis", "spine", "chest", "neck", "head"):
        pbs[n].rotation_euler = Euler([math.radians(a) for a in p[n + "_rot"]], "XYZ")
    set_loc_world(pbs["pelvis"], p["pelvis_off"])
    lift = max(0.0, p["pelvis_off"][2] + 0.012)  # feet leave the turf only when the pelvis rises (jump)
    set_loc_world(pbs["ik_foot_L"], STANCE["L"] + V(p["footL"]) + V((0, 0, lift)))
    set_loc_world(pbs["ik_foot_R"], STANCE["R"] + V(p["footR"]) + V((0, 0, lift)))
    yaw = p["pelvis_rot"][1] + p["spine_rot"][1] + p["chest_rot"][1]
    Rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    G = V(p["pelvis_off"]) + Rz @ V(p["G"])
    D = (Rz @ V(p["D"])).normalized()
    F = orth(Rz @ V(p["F"]), D)
    X = D.cross(F)
    pbs["stick"].matrix = Matrix(((X.x, D.x, F.x, G.x), (X.y, D.y, F.y, G.y), (X.z, D.z, F.z, G.z), (0, 0, 0, 1)))
    pbs["stick"].scale = (1, 1, 1)

# ------------------------------------------------------------------ IK pole calibration
def evaluated():
    dg = bpy.context.evaluated_depsgraph_get()
    return arm.evaluated_get(dg).pose.bones

def calibrate(owner, mid, pole, poses):
    con = pbs[owner].constraints["IK"]
    def cost(a):
        con.pole_angle = math.radians(a)
        tot = 0.0
        for p in poses:
            apply_pose(p); arm.update_tag(); bpy.context.view_layer.update()
            e = evaluated(); tot += (e[mid].tail - e[pole].head).length
        return tot
    best = min(range(-180, 180, 15), key=cost)
    best = min(range(best - 14, best + 15, 2), key=cost)
    con.pole_angle = math.radians(best)
    return best

cal_poses = [finalize(P()), REL_KEYS[2][1], REL_KEYS[4][1], CEL_KEYS[3][1]]
REPORT["pole_angles"] = {
    "elbow_R": calibrate("forearm_R", "upperarm_R", "pole_elbow_R", cal_poses),
    "elbow_L": calibrate("forearm_L", "upperarm_L", "pole_elbow_L", cal_poses),
    "knee_R": calibrate("shin_R", "thigh_R", "pole_knee_R", cal_poses[:1]),
    "knee_L": calibrate("shin_L", "thigh_L", "pole_knee_L", cal_poses[:1]),
}

# ------------------------------------------------------------------ keyframing
KEYED = [("pelvis", "location"), ("pelvis", "rotation_euler"), ("spine", "rotation_euler"),
         ("chest", "rotation_euler"), ("neck", "rotation_euler"), ("head", "rotation_euler"),
         ("ik_foot_L", "location"), ("ik_foot_R", "location"),
         ("stick", "location"), ("stick", "rotation_quaternion")]
prefs = bpy.context.preferences.edit
old_interp = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = "LINEAR"
ad = arm.animation_data_create()
try:
    for name, start, length, loop, fn in CLIPS:
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        ad.action = act
        prev_q = None
        for f in range(0, length + 1):
            apply_pose(fn(f))
            q = pbs["stick"].rotation_quaternion.copy()
            if prev_q is not None and q.dot(prev_q) < 0:
                q.negate(); pbs["stick"].rotation_quaternion = q
            prev_q = q
            for n, path in KEYED:
                pbs[n].keyframe_insert(path, frame=f, group=n)
        ad.action = None
finally:
    prefs.keyframe_new_interpolation_type = old_interp

# NLA: lay the clips on one timeline for the combined USD export
track = ad.nla_tracks.new()
track.name = "lax_shooter_clips"
for i, (name, start, length, loop, fn) in enumerate(CLIPS):
    act = bpy.data.actions[name]
    st = track.strips.new(name, start, act)
    if hasattr(st, "action_slot") and st.action_slot is None and len(act.slots):
        st.action_slot = act.slots[0]
    st.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD"
ad.action = None
for n in ("pelvis", "spine", "chest", "neck", "head", "stick", "ik_foot_L", "ik_foot_R"):
    pbs[n].location = (0, 0, 0); pbs[n].rotation_euler = (0, 0, 0); pbs[n].rotation_quaternion = (1, 0, 0, 0)

scene.frame_start = 0
scene.frame_end = CLIPS[-1][1] + CLIPS[-1][2]
scene.timeline_markers.clear()
for name, start, length, loop, fn in CLIPS:
    scene.timeline_markers.new(name + "_start", frame=start)
    scene.timeline_markers.new(name + "_end", frame=start + length)
scene.timeline_markers.new("release_overhand_BALL_RELEASE", frame=CLIPS[2][1] + RELEASE_LOCAL)

# ------------------------------------------------------------------ validation
def clip_of(f):
    for name, start, length, loop, fn in CLIPS:
        if start <= f <= start + length:
            return name
    return None

stats = {}
root_rest = arm_data.bones["root"].matrix_local
prev_stick = None
for f in range(scene.frame_start, scene.frame_end + 1):
    c = clip_of(f)
    if c is None:
        continue
    scene.frame_set(f)
    e = evaluated()
    st = stats.setdefault(c, dict(hand_err=0.0, foot_err=0.0, ankle_z_min=9.0, ankle_z_max=-9.0,
                                  glove_head_clear=9.0, shaft_head_clear=9.0, root_dev=0.0,
                                  stick_step_deg=0.0, pelvis_z_min=9.0, pelvis_z_max=-9.0))
    for s in ("L", "R"):
        st["hand_err"] = max(st["hand_err"], (e["forearm_" + s].tail - e["ik_hand_" + s].head).length)
        st["foot_err"] = max(st["foot_err"], (e["shin_" + s].tail - e["ik_foot_" + s].head).length)
        z = e["foot_" + s].head.z
        st["ankle_z_min"] = min(st["ankle_z_min"], z); st["ankle_z_max"] = max(st["ankle_z_max"], z)
    hc = e["head"].matrix @ V((0, 0.20, 0))
    for s in ("L", "R"):
        st["glove_head_clear"] = min(st["glove_head_clear"], (e["forearm_" + s].tail - hc).length - 0.25 - 0.065)
    Ms = e["stick"].matrix
    for i in range(0, 21):
        y = -0.5 + i * 0.049
        st["shaft_head_clear"] = min(st["shaft_head_clear"], (Ms @ V((0, y, 0)) - hc).length - 0.262 - 0.016)
    head_pt = Ms @ V((0, 0.37, 0))
    st["shaft_head_clear"] = min(st["shaft_head_clear"], (head_pt - hc).length - 0.262 - 0.10)
    st["root_dev"] = max(st["root_dev"], max(abs(a - b) for ra, rb in zip(e["root"].matrix, root_rest) for a, b in zip(ra, rb)))
    pz = e["pelvis"].head.z
    st["pelvis_z_min"] = min(st["pelvis_z_min"], pz); st["pelvis_z_max"] = max(st["pelvis_z_max"], pz)
    q = Ms.to_quaternion()
    if prev_stick is not None and prev_stick[0] == c:
        a = q.rotation_difference(prev_stick[1]).angle
        st["stick_step_deg"] = max(st["stick_step_deg"], math.degrees(min(a, 2 * math.pi - a)))
    prev_stick = (c, q)
for c in stats:
    stats[c] = {k: round(v, 4) for k, v in stats[c].items()}
REPORT["clip_stats"] = stats

# loop seam check: first vs last frame of looping clips (evaluated bone matrices)
seams = {}
for name, start, length, loop, fn in CLIPS:
    scene.frame_set(start); a = {b.name: b.matrix.copy() for b in evaluated()}
    scene.frame_set(start + length); b = {bb.name: bb.matrix.copy() for bb in evaluated()}
    seams[name] = round(max(max(abs(x - y) for ra, rb in zip(a[k], b[k]) for x, y in zip(ra, rb)) for k in a), 6)
REPORT["first_vs_last_frame_max_delta"] = seams

scene.frame_set(0)
zs = [v.co.z for v in body.data.vertices]
REPORT["rest_height_m"] = round(max(zs) - min(zs), 4)
REPORT["rest_min_z"] = round(min(zs), 4)
REPORT["tris"] = sum(len(p.vertices) - 2 for m in (body.data, stick_mesh.data) for p in m.polygons)
REPORT["bones_deform"] = [b.name for b in arm_data.bones if b.use_deform]
REPORT["timeline"] = {n: [s, s + l] for n, s, l, lp, fn in CLIPS}
REPORT["release_frame"] = CLIPS[2][1] + RELEASE_LOCAL
