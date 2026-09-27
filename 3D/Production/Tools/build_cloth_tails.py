# v9.7: cloth-ready stick tails for RealityKit ClothBodyComponent (iOS 27). Stick-socket space, ribbons, pin data.
import json as _json
EXP = os.path.join(PROD, "Exports")

def _ribbon(pts, width, segs=8):
    """Densify a tail polyline and build a double-sided ribbon (2 verts per station). Returns (verts, faces, pin_vertex_indices)."""
    P = [V(p) for p in pts]; dense = []
    for i in range(segs + 1):
        t = i / segs * (len(P) - 1); k = min(int(t), len(P) - 2); f = t - k
        dense.append(P[k].lerp(P[k + 1], f))
    verts, faces = [], []
    for i, c in enumerate(dense):
        d = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
        side = d.cross(V((0, 0, 1))); side = side.normalized() if side.length > 1e-6 else V((1, 0, 0))
        w = width * (1.0 - 0.55 * i / segs)
        verts += [tuple(c - side * w / 2), tuple(c + side * w / 2)]
    for i in range(segs):
        a = 2 * i; faces += [(a, a + 2, a + 3, a + 1), (a, a + 1, a + 3, a + 2)]
    return verts, faces, [0, 1]

def build_cloth_tails(export=True):
    reset_scene("LaxAttack_StickTails"); C = coll("tails")
    out = {"schema": "lax_stick_tails_cloth", "version": 1, "space": "stick-socket space (same axes as the character's stick_socket / stick joint: +Y along the shaft toward the head, +Z = pocket open face, origin = top-hand grip, metres). Attach as a child of the entity/transform that follows the stick joint (the same system used for the ball), identity local transform.",
           "runtime": {"ClothSimulationComponent": "one per character (or one shared root)", "ClothBodyComponent": "one per tail prim; simulation mesh = the ribbon itself",
                       "pinning": "set each tail's pin_vertices to kinematic so the knot follows the stick; all other vertices dynamic",
                       "suggested_material": {"mass_per_vertex_g": 0.3, "stretch": "high/inextensible", "bend": "low", "damping": "medium-high (strings settle within ~0.4 s)", "gravity_scale": 1.0},
                       "fallback": "the character USDZs still contain baked tails (skinned lag via pocket joints). If cloth tails are adopted, request the no-baked-tail character exports (STICK_TAILS_NONE) to avoid doubled strings."},
           "colours_by_character": {"lax_shooter (Rae)": "cord_tan_v9 #BC9161", "lax_team_home_7 (Mina)": "kit_purple_v9 #A87DE0", "lax_goalie (Kit)": "cord_cream #F5EBD9", "lax_girl_goalie (#30)": "cord_cream #F5EBD9"},
           "assets": {}}
    for kind in ("attack", "goalie"):
        g = stick_geo(kind, "womens"); objs = []; tails = []
        for i, (geo, root, ln, pb, pts) in enumerate(g["tails"]):
            v, f, pins = _ribbon(pts, 0.010 if i < 2 else 0.008)
            o = obj_from_geo("%s_tail_%02d" % (kind, i), (v, f), "cord_tan_v9", C); objs.append(o)
            tails.append({"prim": o.name, "kind": "throat" if i < 2 else "sidewall", "length_m": round(ln, 3), "vertices": len(v), "pin_vertices": pins,
                          "root_stick_space": [round(x, 4) for x in root]})
        name = "lax_stick_tails_womens_%s" % kind
        if export:
            for o in bpy.data.objects:
                try:
                    o.select_set(False)
                except Exception:
                    pass
            for o in objs: o.select_set(True)
            path = os.path.join(EXP, name + ".usdz")
            kw = dict(filepath=path, selected_objects_only=True, export_materials=True, generate_preview_surface=True, export_animation=False)
            try:
                bpy.ops.wm.usd_export(convert_orientation=False, **kw)
            except TypeError:
                bpy.ops.wm.usd_export(**kw)
        out["assets"][name + ".usdz"] = {"stick_kind": kind, "tails": tails}
        for o in objs:
            me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)
    with open(os.path.join(EXP, "lax_stick_tails_cloth.json"), "w") as fh:
        _json.dump(out, fh, indent=2)
    return out
