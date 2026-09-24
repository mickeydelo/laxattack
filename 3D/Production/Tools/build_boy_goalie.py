# Lax Attack Phase 3: boy goalie hero (lax_goalie.usdz, faces +Z) + goalie stick asset.
# LEFT/RIGHT = SHOOTER'S PERSPECTIVE. goalie_*_left moves toward the shooter's left = game -X = the goalie's own right
# = Blender -X in the canonical (-Y facing) build. Export adds rotateY(180) so the goalie faces +Z (toward the shooter).
BG_DIR = os.path.join(PROD, "Characters", "BoyGoalie")
GOALIE_CLIPS = ["goalie_ready", "goalie_shuffle_left", "goalie_shuffle_right", "goalie_read_left", "goalie_read_right",
                "goalie_save_left", "goalie_save_right", "goalie_goal_against"]

GK = finalize(P(BASE_GOALIE, G=(-0.20, -0.28, 0.90), D=(-0.12, -0.10, 0.99), F=(0.05, -1.0, 0.1), face="focused"))
def Q(**kw):
    return P(GK, **kw)

def mirror(p):
    """Mirror a goalie pose across X (shooter-left <-> shooter-right). Stick is re-authored separately where needed."""
    q = dict(p)
    for k in ("pelvis_rot", "spine_rot", "chest_rot", "neck_rot", "head_rot"):
        a = p[k]; q[k] = (a[0], -a[1], -a[2])
    q["pelvis_off"] = (-p["pelvis_off"][0], p["pelvis_off"][1], p["pelvis_off"][2])
    fl, fr = p["footL"], p["footR"]
    q["footL"] = (-fr[0], fr[1], fr[2]); q["footR"] = (-fl[0], fl[1], fl[2])
    q["eye"] = (-p["eye"][0], p["eye"][1])
    return q

def ready_pose(t, N=40):
    ph = 2 * math.pi * t / N; s = math.sin(ph); b = 0.5 - 0.5 * math.cos(2 * ph)
    p = Q(pelvis_off=(0.004 * s, 0, -0.085 - 0.018 * b), spine_rot=(6 + 1.5 * b, 0, 0), head_rot=(-8 + 1.5 * b, 3 * s, 0),
          G=tuple(V(GK["G"]) + V((0.006 * s, 0, -0.01 * b))), eye=(4 * s, 0), pocket=0.002)
    return finalize(p)

SHUFFLE_L = 0.22   # design-space step per cycle (world = L * body_scale)

def _ss(a, b, t):
    return smoothstep(a, b, t)

def shuffle_root(t, sign, N=20, L=SHUFFLE_L):
    """Root displacement Swift should apply (design units, Blender X): smoothstep from push to settle."""
    k = N / 20.0
    return -sign * L * _ss(3 * k, 15 * k, t)

def shuffle(sign, N=20, L=SHUFFLE_L):
    """Goalie shuffle toward shooter-left (sign +1 -> Blender -X / game -X) or right (-1).
    Beats (N=20): 0-3 ready/load, 3 PUSH (trailing foot), 3-9 lead foot travels, 9 lead PLANT, 10-15 trail recovers, 15 trail plant,
    15-20 balanced SETTLE. Feet are authored in root space against shuffle_root(), so when Swift moves the root by
    travel_meters along that curve the planted foot stays exactly still (no skating). Hips lead; shoulders stay level."""
    k = N / 20.0
    def fn(t):
        R = shuffle_root(t, sign, N, L)
        lead_w = -sign * L * _ss(3 * k, 9 * k, t); lead_z = 0.05 * math.sin(math.pi * min(1.0, max(0.0, (t - 3 * k) / (6 * k))))
        trail_w = -sign * L * _ss(8 * k, 14 * k, t); trail_z = 0.035 * math.sin(math.pi * min(1.0, max(0.0, (t - 8 * k) / (6 * k))))
        push0 = math.sin(math.pi * min(1.0, max(0.0, (t - 2 * k) / (5 * k))))
        hips_w = 0.5 * (lead_w + trail_w) - sign * 0.025 * push0          # hips stay between the feet, leaning into the step
        lead = (lead_w - R, 0.0, lead_z); trail = (trail_w - R, 0.0, trail_z)
        fr, fl = (lead, trail) if sign > 0 else (trail, lead)
        push = math.sin(math.pi * min(1.0, max(0.0, (t - 2 * k) / (5 * k))))
        roll = 4.0 * sign * push
        p = Q(pelvis_off=(hips_w - R, 0.0, -0.115 - 0.02 * push), pelvis_rot=(10, 0, roll), spine_rot=(6, 0, -roll * 0.6), chest_rot=(2, 0, -roll * 0.4),
              footR=fr, footL=fl, head_rot=(-8, 3 * sign, 0), eye=(10 * sign, 0), face="determined",
              G=tuple(V(GK["G"]) + V((-0.02 * sign * push, 0, 0.01 * push))))
        return finalize(p)
    return fn

def shuffle_meta(sign, N=20, L=SHUFFLE_L):
    k = N / 20.0
    return {"push_frame": int(round(3 * k)), "plant_frame": int(round(9 * k)), "trail_plant_frame": int(round(14 * k)), "settle_frame": int(round(15 * k)), "travel_meters": L,
            "movement_direction": "shooter_left" if sign > 0 else "shooter_right",
            "root_motion_curve": {"type": "smoothstep", "start_local_frame": int(round(3 * k)), "end_local_frame": int(round(15 * k)),
                                  "axis": "game -X" if sign > 0 else "game +X"}}

READ_L = finalize(Q(pelvis_off=(-0.06, -0.01, -0.11), pelvis_rot=(9, 6, 4), spine_rot=(7, 4, 3), chest_rot=(2, 4, 2),
                    head_rot=(-6, 10, 0), footR=(-0.03, 0, 0), G=(-0.26, -0.30, 0.90), D=(-0.30, -0.12, 0.95), F=(0.1, -1, 0.1),
                    eye=(14, 0), face="focused", pocket=0.002))
SAVE_L = finalize(Q(pelvis_off=(-0.22, -0.05, -0.15), pelvis_rot=(8, 10, 12), spine_rot=(6, 8, 8), chest_rot=(2, 8, 4),
                    neck_rot=(-4, 8, -4), head_rot=(-6, 12, -6), footR=(-0.22, -0.05, 0), footL=(-0.06, 0.0, 0.03),
                    G=(-0.42, -0.30, 0.86), D=(-0.55, -0.15, 0.82), F=(0.1, -1.0, 0.0), eye=(16, 0), face="strain", pocket=0.02))
SAVE_HL = P(SAVE_L, pelvis_off=(-0.18, -0.05, -0.06), G=(-0.36, -0.28, 1.08), D=(-0.36, -0.10, 0.93), eye=(14, 8))
SAVE_LL = P(SAVE_L, pelvis_off=(-0.20, -0.06, -0.22), pelvis_rot=(14, 8, 10), spine_rot=(12, 6, 6), G=(-0.26, -0.34, 0.98),
            D=(-0.40, -0.60, -0.69), F=(0.1, -0.75, 0.65), eye=(14, -10))   # stick head just reaches the turf

def stick_right(p, G, D, F):
    return P(p, G=G, D=D, F=F)

def save_keys(peak, mirror_side=False, contact=7, gx_right=None):
    """Explosive lateral save: read -> push -> CONTACT (local `contact`) -> overshoot -> recover to ready."""
    rd = READ_L if not mirror_side else mirror(READ_L)
    pk = peak if not mirror_side else mirror(peak)
    if mirror_side:   # stick crosses to the shooter's right (Blender +X)
        gx, gy, gz = peak["G"]; dx, dy, dz = peak["D"]
        gxr = gx_right if gx_right is not None else 0.12 + (-gx - 0.42) * 0.8
        pk = P(pk, G=(gxr, gy - 0.04, gz), D=(-dx, dy, dz), F=(-0.1, -1.0, peak["F"][2]))
        rd = P(rd, G=(-0.12, -0.32, 0.90), D=(0.20, -0.12, 0.97), F=(-0.1, -1, 0.1))
    over = P(pk, pelvis_off=(pk["pelvis_off"][0] * 1.08, pk["pelvis_off"][1], pk["pelvis_off"][2] - 0.02),
             G=tuple(V(pk["G"]) + V((0.03 if not mirror_side else -0.03, 0.02, -0.02))), pocket=0.028)
    return [(0, rd, "io"), (3, P(rd, pelvis_off=(rd["pelvis_off"][0] * 1.4, -0.01, -0.13)), "in"),
            (contact, pk, "out"), (contact + 4, over, "io"), (contact + 12, P(pk, face="determined", pocket=0.01), "io"),
            (contact + 23, GK, "io")]

def body_save():
    hit = Q(pelvis_off=(0, 0.05, -0.08), pelvis_rot=(2, 0, 0), spine_rot=(-4, 0, 0), chest_rot=(-10, 0, 0), head_rot=(-4, 0, 0),
            G=(-0.20, -0.26, 0.90), face="strain", pocket=0.0)
    return [(0, GK, "io"), (3, Q(pelvis_off=(0, -0.02, -0.10), chest_rot=(6, 0, 0)), "in"), (5, hit, "out"),
            (10, P(hit, pelvis_off=(0, 0.06, -0.10), chest_rot=(-14, 0, 0)), "io"), (16, Q(face="determined"), "io"), (24, GK, "io")]

def five_hole():
    shut = Q(pelvis_off=(0, -0.03, -0.18), pelvis_rot=(14, 0, 0), spine_rot=(10, 0, 0), footL=(-0.07, 0, 0), footR=(0.07, 0, 0),
             G=(-0.10, -0.34, 1.02), D=(0.05, -0.60, -0.80), F=(0, -0.80, 0.60), eye=(0, -12), face="strain")
    return [(0, GK, "io"), (3, P(shut, pelvis_off=(0, -0.02, -0.12)), "in"), (5, shut, "out"), (12, P(shut, face="determined"), "io"),
            (20, GK, "io")]

def goal_against():
    look = Q(pelvis_off=(0, 0.0, -0.06), pelvis_rot=(4, 12, 0), chest_rot=(0, 18, 0), neck_rot=(-4, 30, 0), head_rot=(-6, 40, 0),
             G=(-0.21, -0.24, 0.86), eye=(-10, 0), face="surprise")
    slump = Q(pelvis_off=(0, 0.01, -0.05), pelvis_rot=(4, 0, 0), spine_rot=(7, 0, 0), chest_rot=(6, 0, 0), neck_rot=(5, 0, 0),
              head_rot=(9, 0, 0), G=(-0.22, -0.26, 0.78), D=(-0.30, -0.25, 0.92), eye=(0, -8), face="disappointed")
    return [(0, GK, "io"), (6, look, "out"), (16, P(look, face="disappointed"), "io"), (26, slump, "io"),
            (36, P(slump, head_rot=(10, -6, 0)), "io"), (45, P(slump, head_rot=(9, 3, 0)), "io")]

def celebrate():
    up = Q(pelvis_off=(0, 0, 0.10), pelvis_rot=(-4, 0, 0), spine_rot=(-4, 0, 0), chest_rot=(-8, 0, 0), head_rot=(-14, 0, 0),
           G=(-0.26, -0.12, 1.12), D=(-0.25, 0.05, 0.97), F=(0.3, -0.95, 0), face="big_smile")
    down = P(up, pelvis_off=(0, 0, -0.12), G=(-0.26, -0.16, 1.00), face="big_smile")
    return [(0, GK, "io"), (5, P(down, pelvis_off=(0, 0, -0.14)), "io"), (10, up, "in"), (13, P(up, pelvis_off=(0, 0, 0.14)), "out"),
            (18, down, "in"), (23, up, "io"), (29, down, "io"), (36, Q(face="smile"), "io")]

BG_CLIPS = [
    Clip("goalie_ready", 0, 40, True, ready_pose, blinks=(28,), notes="set position; toe bounce; eyes track"),
    Clip("goalie_shuffle_left", 50, 20, True, shuffle(+1), meta=shuffle_meta(+1),
         notes="one shuffle step per cycle; Swift moves the root travel_meters toward game -X along root_motion_curve (no foot skating)"),
    Clip("goalie_shuffle_right", 80, 20, True, shuffle(-1), meta=shuffle_meta(-1),
         notes="one shuffle step per cycle; Swift moves the root travel_meters toward game +X along root_motion_curve"),
    Clip("goalie_read_left", 110, 18, False, keys_fn([(0, GK, "io"), (4, P(READ_L, footR=(-0.015, 0, 0.03)), "io"), (8, READ_L, "out"),
                                                      (18, P(READ_L, pelvis_off=(-0.07, -0.01, -0.12)), "io")]), meta={"plant_frame": 8, "travel_meters": 0.0},
         notes="anticipation toward shooter-left; ends loaded (chain into goalie_save_left)"),
    Clip("goalie_read_right", 135, 18, False, keys_fn([(0, GK, "io"), (4, mirror(P(READ_L, footR=(-0.015, 0, 0.03), G=(-0.12, -0.32, 0.90), D=(0.2, -0.12, 0.97), F=(-0.1, -1, 0.1))), "io"),
                                                       (8, mirror(P(READ_L, G=(-0.12, -0.32, 0.90), D=(0.2, -0.12, 0.97), F=(-0.1, -1, 0.1))), "out"),
                                                       (18, mirror(P(READ_L, pelvis_off=(-0.07, -0.01, -0.12), G=(-0.12, -0.32, 0.90), D=(0.2, -0.12, 0.97), F=(-0.1, -1, 0.1))), "io")]),
         notes="anticipation toward shooter-right"),
    Clip("goalie_save_left", 160, 30, False, keys_fn(save_keys(SAVE_L)), contact=7, notes="stick save at mid height, shooter-left; contact local 7"),
    Clip("goalie_save_right", 200, 30, False, keys_fn(save_keys(SAVE_L, True)), contact=7, notes="stick save at mid height, shooter-right; contact local 7"),
    Clip("goalie_goal_against", 240, 45, False, keys_fn(goal_against()), notes="looks back at the net, slumps; blend to ready"),
    Clip("goalie_save_high_left", 295, 30, False, keys_fn(save_keys(SAVE_HL)), contact=7, notes="extra"),
    Clip("goalie_save_high_right", 335, 30, False, keys_fn(save_keys(SAVE_HL, True)), contact=7, notes="extra"),
    Clip("goalie_save_low_left", 375, 30, False, keys_fn(save_keys(SAVE_LL)), contact=7, notes="extra; stick head drops to the turf"),
    Clip("goalie_save_low_right", 415, 30, False, keys_fn(save_keys(SAVE_LL, True, gx_right=0.14)), contact=7, notes="extra"),
    Clip("goalie_five_hole_close", 455, 20, False, keys_fn(five_hole()), contact=5, notes="extra; knees + stick close the gap"),
    Clip("goalie_body_save", 485, 24, False, keys_fn(body_save()), contact=5, notes="extra; chest block with recoil"),
    Clip("goalie_celebrate", 520, 36, False, keys_fn(celebrate()), notes="extra; stick pumps"),
]

def build_goalie(export=True):
    reset_scene("LaxAttack_BoyGoalie")
    C = coll("lax_goalie")
    arm = build_skeleton(BOY_GOALIE, C, "lax_goalie_rig")
    parts = build_character(BOY_GOALIE, C, arm)
    stick, meta = build_stick("goalie", C, arm, name="lax_goalie_stick", frame_mat="helmet_teal", pocket_mat="cord_white")
    socks = add_character_sockets(BOY_GOALIE, arm, C, meta)
    ad = arm.data; ad.pose_position = "REST"; bpy.context.view_layer.update()
    Ms = ad.bones["stick"].matrix_local.copy()
    socks["ball_contact_socket"] = add_socket("ball_contact_socket", arm, "pocket_01", Ms @ Matrix.Translation(meta["ball_contact"]), C, 0.03)
    ad.pose_position = "POSE"
    meshes = atlas_character(arm, list(parts.values()) + [stick], "lax_goalie", BG_DIR) if "atlas_character" in globals() else list(parts.values()) + [stick]
    poles = calibrate_poles(arm, [GK, READ_L, SAVE_L, SAVE_HL, mirror(SAVE_L)], "goalie")
    bake_clips(arm, BG_CLIPS, "goalie", GOALIE_EXTRA)
    rep = {"poles": poles, "validation": validate_character(arm, BG_CLIPS, meshes, meta, REQUIRED_SOCKETS, GOALIE_CLIPS)}
    os.makedirs(BG_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BG_DIR, "LaxAttack_BoyGoalie.blend"), compress=True)
    man = manifest("lax_goalie", BG_CLIPS, perspective="goalie", body_scale=BOY_GOALIE.get("body_scale", 1.0), extra={
        "facing": "+Z (toward the shooter); root identity at field level between the feet",
        "required_sockets": REQUIRED_SOCKETS, "extra_sockets": ["ball_contact_socket"],
        "runtime_note": "the procedural goalie used a 0.625 m base height; this asset's origin is at field level (y = 0)"})
    if export:
        objs = [arm] + meshes + list(socks.values())
        rep["export"] = export_asset(objs, "lax_goalie", "lax_goalie_rig", os.path.join(EXP, "lax_goalie.usdz"), 30, BG_CLIPS[-1].end,
                                     True, man, REQUIRED_SOCKETS + ["ball_contact_socket"])
        rep["lods"] = export_lods(rep["export"], "lax_goalie", "lax_goalie_rig", os.path.join(EXP, "lax_goalie.usdz"), (0.6, 0.3), 30, BG_CLIPS[-1].end, man)
        with open(os.path.join(EXP, "lax_goalie_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep, arm, meta
