# Lax Attack production core: palette, shared materials, mesh builders, scene/render/git helpers.
# Blender authoring space: Z-up, characters face -Y, character right = -X, 1 unit = 1 m (game scale).
import bpy, bmesh, math, os, json, subprocess, random
from mathutils import Vector, Matrix, Euler, Quaternion

V = Vector
REPO = os.path.expanduser("~/Developer/laxattack")
PROD = os.path.join(REPO, "3D", "Production")
FPS = 30

# ------------------------------------------------------------------ palette (linear RGB, roughness, metallic, coat)
# Values are the runtime values: they export to UsdPreviewSurface unchanged.
MATS = {
    # skin tones (diverse complexion set)
    "skin_light":  ((0.80, 0.52, 0.38), 0.55, 0.0, 0.0),
    "skin_tan":    ((0.62, 0.36, 0.22), 0.55, 0.0, 0.0),
    "skin_brown":  ((0.36, 0.18, 0.09), 0.52, 0.0, 0.0),
    "skin_deep":   ((0.17, 0.08, 0.04), 0.50, 0.0, 0.0),
    "blush":       ((0.85, 0.30, 0.25), 0.70, 0.0, 0.0),
    # hair (sculpted vinyl, slight sheen)
    "hair_auburn": ((0.30, 0.09, 0.03), 0.42, 0.0, 0.0),
    "hair_dark":   ((0.035, 0.022, 0.018), 0.40, 0.0, 0.0),
    "hair_blond":  ((0.72, 0.45, 0.16), 0.42, 0.0, 0.0),
    # face paint
    "eye_white":   ((0.90, 0.90, 0.88), 0.30, 0.0, 0.0),
    "iris_brown":  ((0.16, 0.06, 0.02), 0.25, 0.0, 0.0),
    "iris_blue":   ((0.03, 0.18, 0.45), 0.25, 0.0, 0.0),
    "iris_green":  ((0.05, 0.25, 0.10), 0.25, 0.0, 0.0),
    "pupil":       ((0.008, 0.008, 0.012), 0.20, 0.0, 0.0),
    "mouth":       ((0.22, 0.03, 0.03), 0.55, 0.0, 0.0),
    # team kit: blue/white identity
    "kit_blue":    ((0.02, 0.16, 0.62), 0.72, 0.0, 0.0),
    "kit_navy":    ((0.010, 0.030, 0.13), 0.75, 0.0, 0.0),
    "kit_white":   ((0.86, 0.87, 0.88), 0.72, 0.0, 0.0),
    "accent_coral":((0.95, 0.28, 0.14), 0.60, 0.0, 0.0),
    "accent_gold": ((1.00, 0.62, 0.05), 0.45, 0.0, 0.0),
    "accent_teal": ((0.00, 0.45, 0.45), 0.60, 0.0, 0.0),
    # molded plastic / rubber / painted metal
    "plastic_blue":  ((0.02, 0.18, 0.70), 0.28, 0.0, 0.25),
    "plastic_white": ((0.88, 0.89, 0.90), 0.30, 0.0, 0.25),
    "plastic_dark":  ((0.02, 0.022, 0.03), 0.35, 0.0, 0.0),
    "rubber_dark":   ((0.025, 0.025, 0.03), 0.85, 0.0, 0.0),
    "metal_red":     ((0.75, 0.035, 0.02), 0.32, 0.35, 0.3),
    "metal_silver":  ((0.70, 0.72, 0.74), 0.30, 0.85, 0.0),
    "cord_white":    ((0.85, 0.84, 0.80), 0.85, 0.0, 0.0),
    "cord_navy":     ((0.02, 0.05, 0.18), 0.80, 0.0, 0.0),
    "ball_yellow":   ((1.00, 0.72, 0.02), 0.55, 0.0, 0.0),
    # environment
    "turf_a":      ((0.10, 0.36, 0.06), 0.88, 0.0, 0.0),
    "turf_b":      ((0.075, 0.28, 0.045), 0.88, 0.0, 0.0),
    "line_white":  ((0.90, 0.90, 0.86), 0.80, 0.0, 0.0),
    "soil":        ((0.28, 0.15, 0.07), 0.90, 0.0, 0.0),
    "wood":        ((0.45, 0.22, 0.09), 0.62, 0.0, 0.0),
    "wood_dark":   ((0.20, 0.09, 0.04), 0.65, 0.0, 0.0),
    "rock":        ((0.42, 0.40, 0.36), 0.78, 0.0, 0.0),
    "rock_warm":   ((0.52, 0.42, 0.32), 0.78, 0.0, 0.0),
    "foliage_a":   ((0.08, 0.30, 0.07), 0.75, 0.0, 0.0),
    "foliage_b":   ((0.16, 0.42, 0.08), 0.75, 0.0, 0.0),
    "pine":        ((0.02, 0.16, 0.08), 0.75, 0.0, 0.0),
    "bark":        ((0.22, 0.11, 0.05), 0.85, 0.0, 0.0),
    "water":       ((0.02, 0.32, 0.42), 0.12, 0.0, 0.0),
    "water_shallow": ((0.10, 0.55, 0.52), 0.15, 0.0, 0.0),
    "sand":        ((0.75, 0.58, 0.36), 0.90, 0.0, 0.0),
    "mountain":    ((0.20, 0.30, 0.42), 0.90, 0.0, 0.0),
    "mountain_far":((0.38, 0.50, 0.66), 0.95, 0.0, 0.0),
    "snow":        ((0.85, 0.88, 0.92), 0.85, 0.0, 0.0),
    "cloud":       ((0.95, 0.94, 0.92), 0.95, 0.0, 0.0),
    "sign_paint":  ((0.92, 0.88, 0.76), 0.65, 0.0, 0.0),
    "clay":        ((0.62, 0.60, 0.57), 0.55, 0.0, 0.0),  # neutral lineup override
    # --- v2 (reference key art): vinyl-toy teams, golden turf, toy eyes
    "hair_brown":  ((0.13, 0.055, 0.025), 0.40, 0.0, 0.0),
    "eye_dark":    ((0.018, 0.012, 0.010), 0.12, 0.0, 0.3),
    "kit_red":     ((0.62, 0.05, 0.04), 0.62, 0.0, 0.0),
    "kit_cream":   ((0.86, 0.80, 0.68), 0.66, 0.0, 0.0),
    "helmet_red":  ((0.66, 0.05, 0.035), 0.22, 0.0, 0.6),
    "helmet_navy": ((0.012, 0.035, 0.085), 0.22, 0.0, 0.6),
    "helmet_cream":((0.86, 0.80, 0.68), 0.25, 0.0, 0.5),
    "helmet_teal": ((0.0, 0.33, 0.42), 0.25, 0.0, 0.5),
    "cage_light":  ((0.75, 0.73, 0.68), 0.35, 0.3, 0.0),
    "glove_brown": ((0.16, 0.07, 0.03), 0.55, 0.0, 0.0),
    "glove_dark":  ((0.03, 0.03, 0.035), 0.55, 0.0, 0.0),
    "goal_orange": ((0.88, 0.16, 0.025), 0.30, 0.2, 0.4),
    "leaf_a":      ((0.10, 0.34, 0.05), 0.70, 0.0, 0.0),
    "leaf_b":      ((0.20, 0.48, 0.07), 0.70, 0.0, 0.0),
    "leaf_c":      ((0.05, 0.22, 0.04), 0.72, 0.0, 0.0),
    "lake_blue":   ((0.02, 0.22, 0.45), 0.10, 0.0, 0.0),
    "ball":        ((0.88, 0.86, 0.80), 0.45, 0.0, 0.2),
}

# Textured materials (image textures are packed into USDZ). name -> (image file, roughness, planar UV scale m^-1)
TEX_MATS = {}
UV_PLANAR = {}
BUILD_XF = None   # optional hook set by the figure builder: f(co, weights) -> co (proportion transform)

def mat(name):
    m = bpy.data.materials.get("M_" + name)
    if m:
        return m
    if name in TEX_MATS:
        e = TEX_MATS[name]
        return mat_tex(name, e[0], e[1], *(list(e[2:4]) + [None, None])[:2])
    rgb, rough, metal, coat = MATS[name]
    m = bpy.data.materials.new("M_" + name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        o = nt.nodes.get("Material Output") or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k in ("Coat Weight", "Coat"):
        if k in b.inputs:
            b.inputs[k].default_value = coat
            break
    if "Coat Roughness" in b.inputs:
        b.inputs["Coat Roughness"].default_value = 0.2
    m.diffuse_color = (*rgb, 1)
    m.roughness = rough
    return m

# ------------------------------------------------------------------ geometry builders -> (verts, faces)
def _ring(cx, cy, z, rx, ry, seg, sq=2.0, rot=0.0):
    pts = []
    for i in range(seg):
        t = 2 * math.pi * i / seg + rot
        c, s = math.cos(t), math.sin(t)
        e = 2.0 / sq
        x = rx * math.copysign(abs(c) ** e, c)
        y = ry * math.copysign(abs(s) ** e, s)
        pts.append((cx + x, cy + y, z))
    return pts

def loft(rings, seg=16, cap0="pole", cap1="pole", sq=2.0):
    """rings: list of (z, rx, ry[, cx, cy[, sq]]) bottom->top. caps: 'pole' (rounded), 'flat', None."""
    verts, faces = [], []
    for r in rings:
        z, rx, ry = r[0], r[1], r[2]
        cx = r[3] if len(r) > 3 else 0.0
        cy = r[4] if len(r) > 4 else 0.0
        s = r[5] if len(r) > 5 else sq
        verts += _ring(cx, cy, z, rx, ry, seg, s)
    n = len(rings)
    for k in range(n - 1):
        for i in range(seg):
            a = k * seg + i; b = k * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    def cap(k, up):
        r = rings[k]; z = r[0]
        cx = r[3] if len(r) > 3 else 0.0; cy = r[4] if len(r) > 4 else 0.0
        verts.append((cx, cy, z)); c = len(verts) - 1
        for i in range(seg):
            a = k * seg + i; b = k * seg + (i + 1) % seg
            faces.append((a, c, b) if not up else (a, b, c))
    if cap0:
        cap(0, False)
    if cap1:
        cap(n - 1, True)
    return verts, faces

def superellipsoid(size, e1=0.5, e2=0.5, useg=24, vseg=16, center=(0, 0, 0)):
    """Rounded-box toy form. size = full extents; e<1 boxier, e=1 ellipsoid."""
    a, b, c = size[0] / 2, size[1] / 2, size[2] / 2
    f = lambda w, m: math.copysign(abs(w) ** m, w)
    verts, faces = [], []
    for j in range(1, vseg):
        phi = -math.pi / 2 + math.pi * j / vseg
        for i in range(useg):
            th = -math.pi + 2 * math.pi * i / useg
            x = a * f(math.cos(phi), e1) * f(math.cos(th), e2)
            y = b * f(math.cos(phi), e1) * f(math.sin(th), e2)
            z = c * f(math.sin(phi), e1)
            verts.append((center[0] + x, center[1] + y, center[2] + z))
    verts.append((center[0], center[1], center[2] - c)); bot = len(verts) - 1
    verts.append((center[0], center[1], center[2] + c)); top = len(verts) - 1
    rows = vseg - 1
    for j in range(rows - 1):
        for i in range(useg):
            p = j * useg + i; q = j * useg + (i + 1) % useg
            faces.append((p, q, q + useg, p + useg))
    for i in range(useg):
        faces.append((bot, (i + 1) % useg, i))
        o = (rows - 1) * useg
        faces.append((o + i, o + (i + 1) % useg, top))
    return verts, faces

def ellipsoid(center, radii, useg=20, vseg=12):
    return superellipsoid((radii[0] * 2, radii[1] * 2, radii[2] * 2), 1.0, 1.0, useg, vseg, center)

def sweep(points, radii, seg=10, flat=1.0, cap0=True, cap1=True, up=(0, 0, 1), twist=0.0):
    """Tube along a polyline with parallel-transport frames. radii per point (0 -> pointed tip)."""
    P = [V(p) for p in points]
    n = len(P)
    T = []
    for i in range(n):
        d = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])
        T.append(d.normalized())
    u = V(up)
    if abs(u.dot(T[0])) > 0.95:
        u = V((1, 0, 0))
    N = (u - u.dot(T[0]) * T[0]).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            N = (N - N.dot(T[i]) * T[i]).normalized()
        B = T[i].cross(N)
        frames.append((N.copy(), B))
    verts, faces = [], []
    for i in range(n):
        Ni, Bi = frames[i]
        r = radii[i]
        for k in range(seg):
            t = 2 * math.pi * k / seg + twist * i / max(1, n - 1)
            verts.append(tuple(P[i] + Ni * (math.cos(t) * r) + Bi * (math.sin(t) * r * flat)))
    for i in range(n - 1):
        for k in range(seg):
            a = i * seg + k; b = i * seg + (k + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    if cap0:
        verts.append(tuple(P[0] - T[0] * radii[0] * 0.6)); c = len(verts) - 1
        for k in range(seg):
            faces.append((c, (k + 1) % seg, k))
    if cap1:
        verts.append(tuple(P[-1] + T[-1] * radii[-1] * 0.6)); c = len(verts) - 1
        o = (n - 1) * seg
        for k in range(seg):
            faces.append((o + k, o + (k + 1) % seg, c))
    return verts, faces

def bezier_pts(p0, p1, p2, p3, n=10):
    p0, p1, p2, p3 = V(p0), V(p1), V(p2), V(p3)
    out = []
    for i in range(n):
        t = i / (n - 1); s = 1 - t
        out.append(tuple(p0 * s ** 3 + p1 * 3 * s * s * t + p2 * 3 * s * t * t + p3 * t ** 3))
    return out

def torus(center, R, r, useg=24, vseg=8, axis="Z"):
    verts, faces = [], []
    for i in range(useg):
        a = 2 * math.pi * i / useg
        for j in range(vseg):
            b = 2 * math.pi * j / vseg
            x = (R + r * math.cos(b)) * math.cos(a); y = (R + r * math.cos(b)) * math.sin(a); z = r * math.sin(b)
            p = V((x, y, z))
            if axis == "X":
                p = V((z, x, y))
            elif axis == "Y":
                p = V((x, z, y))
            verts.append(tuple(V(center) + p))
    for i in range(useg):
        for j in range(vseg):
            a = i * vseg + j; b = ((i + 1) % useg) * vseg + j
            c = ((i + 1) % useg) * vseg + (j + 1) % vseg; d = i * vseg + (j + 1) % vseg
            faces.append((a, b, c, d))
    return verts, faces

def xform(geo, M):
    v, f = geo
    M = M if isinstance(M, Matrix) else Matrix(M)
    return [tuple(M @ V(p)) for p in v], f

def deform(geo, fn):
    v, f = geo
    return [tuple(fn(V(p))) for p in v], f

def merge(*geos):
    verts, faces = [], []
    for v, f in geos:
        o = len(verts); verts += list(v); faces += [tuple(i + o for i in fc) for fc in f]
    return verts, faces

def hull_rock(seed, size, n=18, bevel=0.18):
    rnd = random.Random(seed)
    bm = bmesh.new()
    for i in range(n):
        th = rnd.uniform(0, 2 * math.pi); ph = math.acos(rnd.uniform(-0.6, 1.0))
        r = rnd.uniform(0.75, 1.0)
        bm.verts.new((size[0] * r * math.sin(ph) * math.cos(th), size[1] * r * math.sin(ph) * math.sin(th),
                      size[2] * (r * math.cos(ph) * 0.5 + 0.5)))
    bmesh.ops.convex_hull(bm, input=list(bm.verts))
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(6), verts=list(bm.verts), edges=list(bm.edges))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(size) * bevel, offset_type="OFFSET", segments=3,
                    profile=0.5, affect="EDGES", clamp_overlap=True)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    verts = [tuple(v.co) for v in bm.verts]
    bm.verts.index_update()
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, faces

# ------------------------------------------------------------------ mesh assembly
class Builder:
    """Accumulates parts (geo, material, bone/weights) into one mesh object."""
    def __init__(self, name):
        self.name = name; self.parts = []
    def add(self, geo, material, bone=None, weights=None, smooth=True):
        # weights: optional callable(vertex_co) -> {bone: w}
        self.parts.append((geo, material, bone, weights, smooth))
        return self
    def build(self, collection, arm=None, parent=None):
        verts, faces, fmat, fsm, vw = [], [], [], [], []
        mats = []
        for (v, f), m, bone, wfn, sm in self.parts:
            if m not in mats:
                mats.append(m)
            o = len(verts); verts += list(v)
            for p in v:
                if wfn is not None:
                    vw.append(wfn(V(p)))
                elif bone is not None:
                    vw.append({bone: 1.0})
                else:
                    vw.append({})
            for fc in f:
                faces.append(tuple(i + o for i in fc)); fmat.append(mats.index(m)); fsm.append(sm)
        vw = [dict(sorted(w.items(), key=lambda kv: -kv[1])[:4]) if len(w) > 4 else w for w in vw]   # <=4 influences
        vw = [({k: x / (sum(w.values()) or 1.0) for k, x in w.items()} if w else w) for w in vw]
        xf = globals().get("BUILD_XF")
        if xf is not None:
            verts = [tuple(xf(V(p), w)) for p, w in zip(verts, vw)]
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(verts, [], faces)
        me.validate(clean_customdata=False)
        for m in mats:
            me.materials.append(mat(m))
        for i, p in enumerate(me.polygons):
            p.material_index = fmat[i]; p.use_smooth = fsm[i]
        if any(m in UV_PLANAR for m in mats):
            uv = me.uv_layers.new(name="UVMap")
            for poly in me.polygons:
                k = UV_PLANAR.get(mats[poly.material_index], 1.0)
                for li in poly.loop_indices:
                    co = me.vertices[me.loops[li].vertex_index].co
                    uv.data[li].uv = (co.x * k, co.y * k)
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        if arm is not None:
            groups = {}
            for i, w in enumerate(vw):
                for b, x in w.items():
                    if x > 1e-4:
                        groups.setdefault(b, []).append((i, x))
            for b, lst in groups.items():
                vg = ob.vertex_groups.new(name=b)
                for i, x in lst:
                    vg.add([i], x, "REPLACE")
            ob.parent = arm
            ob.modifiers.new("Armature", "ARMATURE").object = arm
        elif parent is not None:
            ob.parent = parent
        return ob

def obj_from_geo(name, geo, material, collection, loc=(0, 0, 0), smooth=True):
    b = Builder(name); b.add(geo, material, smooth=smooth)
    ob = b.build(collection); ob.location = loc
    return ob

def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

# ------------------------------------------------------------------ scene helpers
def reset_scene(name):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.actions, bpy.data.cameras,
                 bpy.data.lights, bpy.data.curves, bpy.data.images, bpy.data.worlds, bpy.data.texts):
        for d in list(coll):
            coll.remove(d)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    sc = bpy.context.scene
    sc.name = name
    sc.timeline_markers.clear()
    us = sc.unit_settings; us.system = "METRIC"; us.scale_length = 1.0; us.length_unit = "METERS"
    sc.render.fps = FPS; sc.render.fps_base = 1.0
    return sc

def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c

def text_mesh(name, body, size, collection, extrude=0.01, material="line_white", align="CENTER"):
    cu = bpy.data.curves.new(name + "_curve", "FONT")
    cu.body = body; cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = "CENTER"
    cu.bevel_depth = extrude * 0.3; cu.bevel_resolution = 1; cu.resolution_u = 3
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True); bpy.data.curves.remove(cu)
    v = [tuple(x.co) for x in me.vertices]; f = [tuple(p.vertices) for p in me.polygons]
    bpy.data.meshes.remove(me)
    return v, f

# ------------------------------------------------------------------ look-dev: lighting / world / camera
def setup_world(top=(0.22, 0.46, 0.95), horizon=(1.0, 0.86, 0.66), strength=0.8):
    w = bpy.data.worlds.new("LaxSky"); bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    # world Generated Z is the view-direction Z in [-1, 1]: horizon at 0, zenith at 1
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*horizon, 1)
    ramp.color_ramp.elements[1].position = 0.32; ramp.color_ramp.elements[1].color = (*top, 1)
    mid = ramp.color_ramp.elements.new(0.08); mid.color = (0.52, 0.68, 0.93, 1)
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w

def setup_lights(collection, sun_energy=6.6, sun_angle_deg=8.0, sun_dir=(-0.42, 0.62, -0.66)):
    # Golden-hour key (v2): warm sun from behind-left of the goal (screen upper-left), shadows fall toward the camera/right.
    # Cool rim (area) for separation, no fill light: the warm sky gradient provides fill.
    sd = bpy.data.lights.new("key_sun", "SUN"); sd.energy = sun_energy; sd.angle = math.radians(sun_angle_deg)
    sd.color = (1.0, 0.84, 0.62)
    sun = bpy.data.objects.new("key_sun", sd); collection.objects.link(sun)
    sun.rotation_euler = V(sun_dir).normalized().to_track_quat("-Z", "Y").to_euler()
    rd = bpy.data.lights.new("rim_area", "AREA"); rd.energy = 900; rd.size = 6; rd.color = (0.80, 0.88, 1.0)
    rim = bpy.data.objects.new("rim_area", rd); collection.objects.link(rim)
    rim.location = (3.5, -9.0, 5.0)
    rim.rotation_euler = (V((0, -2, 0.8)) - rim.location).to_track_quat("-Z", "Y").to_euler()
    return sun, rim

def setup_eevee(samples=64, res=(720, 1560)):
    sc = bpy.context.scene
    r = sc.render
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            r.engine = eng; break
        except TypeError:
            pass
    ee = sc.eevee
    for attr, val in (("taa_render_samples", samples), ("use_shadows", True), ("use_raytracing", True),
                      ("shadow_ray_count", 2), ("shadow_step_count", 8), ("use_gtao", True),
                      ("gtao_distance", 0.6), ("fast_gi_distance", 0.6)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:
                pass
    r.resolution_x, r.resolution_y = res; r.resolution_percentage = 100
    r.film_transparent = False
    vs = sc.view_settings
    vs.view_transform = "AgX"
    try:
        vs.look = "AgX - Punchy"
    except Exception:
        try:
            vs.look = "Punchy"
        except Exception:
            pass
    vs.exposure = 0.35; vs.gamma = 1.0
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = "IMAGE"      # playblasts switch scenes to video output
    vs = bpy.context.scene.view_settings            # always restore the style-bible look (env-map renders switch to Standard)
    try:
        vs.view_transform = "AgX"; vs.look = "AgX - Punchy"
    except Exception:
        pass
    vs.exposure = 0.35
    r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"

def make_camera(name, loc, target, collection, vfov_deg=None, lens=None, portrait=True):
    cd = bpy.data.cameras.new(name)
    if vfov_deg is not None:
        cd.sensor_fit = "VERTICAL"; cd.lens_unit = "FOV"; cd.angle = math.radians(vfov_deg)
    elif lens is not None:
        cd.lens = lens; cd.sensor_fit = "VERTICAL" if portrait else "AUTO"
    cd.clip_start = 0.05; cd.clip_end = 500
    ob = bpy.data.objects.new(name, cd); collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob

def game_to_blender(p):
    """RealityKit/USD game coords (x, y-up, z) -> Blender authoring coords."""
    return (-p[0], p[2], p[1])

def render_to(path, camera=None, res=None, dof=None):
    sc = bpy.context.scene
    if camera is not None:
        sc.camera = camera
    if res is not None:
        sc.render.resolution_x, sc.render.resolution_y = res
    cam = sc.camera.data
    if dof is None:
        cam.dof.use_dof = False
    else:
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = dof.get("fstop", 2.8)
        if "focus_object" in dof:
            cam.dof.focus_object = dof["focus_object"]
        else:
            cam.dof.focus_object = None; cam.dof.focus_distance = dof["distance"]
        cam.dof.aperture_blades = 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path

def contact_sheet(paths, out, cols, tile=None, bg=0.08, pad=6, labels=None):
    import numpy as np
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p, check_existing=False)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        bpy.data.images.remove(im)
        if tile is not None and (w, h) != tuple(tile):
            ys = (np.arange(tile[1]) * h / tile[1]).astype(int); xs = (np.arange(tile[0]) * w / tile[0]).astype(int)
            a = a[ys][:, xs]
        imgs.append(a)
    th, tw = imgs[0].shape[:2]
    rows = (len(imgs) + cols - 1) // cols
    H = rows * th + (rows + 1) * pad; W = cols * tw + (cols + 1) * pad
    sheet = np.full((H, W, 4), bg, dtype=np.float32); sheet[..., 3] = 1
    for i, a in enumerate(imgs):
        r, c = divmod(i, cols)
        y0 = H - (r + 1) * (th + pad); x0 = pad + c * (tw + pad)  # pixels are bottom-up
        sheet[y0:y0 + th, x0:x0 + tw] = a[:th, :tw]
    im = bpy.data.images.new("sheet_tmp", W, H, alpha=True)
    im.pixels = sheet.ravel()
    im.filepath_raw = out; im.file_format = "PNG"; im.save()
    bpy.data.images.remove(im)
    return out

def downscale(src, out, width):
    import numpy as np
    im = bpy.data.images.load(src, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    f = w / width; nh = int(h / f)
    # box filter
    fi = int(round(f))
    if fi >= 2 and abs(f - fi) < 1e-6:
        a = a[:nh * fi, :width * fi].reshape(nh, fi, width, fi, 4).mean(axis=(1, 3))
    else:
        ys = (np.arange(nh) * f).astype(int); xs = (np.arange(width) * f).astype(int); a = a[ys][:, xs]
    o = bpy.data.images.new("ds_tmp", width, nh, alpha=True); o.pixels = a.ravel()
    o.filepath_raw = out; o.file_format = "PNG"; o.save(); bpy.data.images.remove(o)
    return out

# ------------------------------------------------------------------ textures
def make_turf_texture(path, base=(0.13, 0.40, 0.07), size=1024, seed=5):
    """Tiling lush-turf albedo: multi-octave value noise + short blade strokes + light speckle. Linear RGB -> sRGB PNG."""
    import numpy as np
    rng = np.random.default_rng(seed)
    def tile_noise(cells):
        g = rng.random((cells, cells)).astype(np.float32)
        x = np.linspace(0, cells, size, endpoint=False); i0 = np.floor(x).astype(int); f = x - i0
        f = f * f * (3 - 2 * f); i1 = (i0 + 1) % cells
        a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        return a * (1 - f)[:, None] + b * f[:, None]
    n = 0.5 * tile_noise(4) + 0.3 * tile_noise(16) + 0.2 * tile_noise(64)
    blades = np.zeros((size, size), np.float32)
    for _ in range(26000):
        x, y = rng.integers(0, size, 2); L = rng.integers(5, 14); dx = rng.integers(-2, 3)
        v = rng.uniform(-1, 1)
        for t in range(L):
            blades[(y + t) % size, (x + (dx * t) // L) % size] += v * (1 - t / L)
    blades = np.clip(blades, -1.5, 1.5) / 1.5
    speck = (rng.random((size, size)) > 0.9975).astype(np.float32)
    lum = 0.74 + 0.60 * (n - 0.5) + 0.42 * blades + 0.45 * speck
    rgb = np.stack([base[0] * lum * (1 + 0.25 * (n - 0.5)), base[1] * lum, base[2] * lum * (1 - 0.2 * (n - 0.5))], -1)
    rgb = np.clip(rgb, 0, 1)
    srgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)
    img = np.concatenate([srgb, np.ones((size, size, 1), np.float32)], -1)
    im = bpy.data.images.new(os.path.basename(path), size, size, alpha=False)
    im.pixels = img.ravel(); im.filepath_raw = path; im.file_format = "PNG"
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(); bpy.data.images.remove(im)
    return path

def mat_tex(name, path, rough, normal=None, rough_map=None):
    m = bpy.data.materials.new("M_" + name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree; b = nt.nodes.get("Principled BSDF")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if normal:
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(normal, check_existing=True)
        tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if rough_map:
        tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = bpy.data.images.load(rough_map, check_existing=True)
        tr.image.colorspace_settings.name = "Non-Color"
        nt.links.new(tr.outputs["Color"], b.inputs["Roughness"])
    m.diffuse_color = (0.1, 0.35, 0.06, 1)
    return m

# ------------------------------------------------------------------ git helpers
def git(*args, timeout=300):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    r = subprocess.run(["/usr/bin/git", "-C", REPO, *args], capture_output=True, text=True, env=env, timeout=timeout)
    return [r.returncode, r.stdout.strip()[-3000:], r.stderr.strip()[-1500:]]

def scratch_push(paths, branch="scratch-previews"):
    """Push files to a throwaway branch (without touching main's index/worktree) for remote preview."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_INDEX_FILE="/tmp/lax_scratch_index")
    def g(*a, inp=None):
        r = subprocess.run(["/usr/bin/git", "-C", REPO, *a], capture_output=True, text=True, env=env, input=inp)
        return r.stdout.strip(), r.returncode, r.stderr.strip()
    if os.path.exists("/tmp/lax_scratch_index"):
        os.remove("/tmp/lax_scratch_index")
    for p in paths:
        sha, _, _ = g("hash-object", "-w", p)
        g("update-index", "--add", "--cacheinfo", "100644," + sha + "," + os.path.basename(p))
    tree, _, _ = g("write-tree")
    commit, _, _ = g("commit-tree", tree, "-m", "scratch previews (throwaway)")
    out, rc, err = g("push", "-f", "origin", commit + ":refs/heads/" + branch)
    return {"commit": commit, "rc": rc, "err": err[-300:]}

MATS["pocket_bag"] = ((0.10, 0.12, 0.22), 0.9, 0.0, 0.0)   # solid pocket backing
