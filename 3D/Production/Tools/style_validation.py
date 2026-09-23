# Lax Attack art-direction checkpoint scene. Run inside Blender with lax_core/lax_figure/lax_pose/lax_env loaded
# into the same namespace (see load_libs). Builds a gameplay diorama at the origin and a catalog lineup stage at x=+60.
import bpy, os, math
OUT = os.path.join(PROD, "Previews", "StyleValidation")
BLEND = os.path.join(PROD, "StyleValidation", "LaxAttackStyleValidation.blend")

SPECTATORS = [
    dict(name="fan_a", family="field", skin="skin_light", hair="hair_blond", iris="eye_dark", eye_style="toy", body_scale=0.82, head_k=1.15, head_c=(0, 0, 1.195),
         head_r=(0.262, 0.248, 0.268), jaw_taper=0.2, cranium=0.07, eye_az=19, eye_el=-5, eye_size=(0.05, 0.062), lash=True,
         freckles=False, brow_w=0.01, mouth_w=0.046, mouth_el=-28, hair_style="ponytail", headgear="cap", cap_mat="kit_blue",
         kit="accent_gold", kit_trim="kit_white", bottom="shorts", bottom_mat="kit_navy", sock="kit_white", sock_stripe="kit_white",
         shoe="kit_white", shoe_accent="accent_coral", glove=None, glove_cuff=None, glove_size=(0.1, 0.1, 0.1), number=""),
    dict(name="fan_b", family="field", skin="skin_deep", hair="hair_dark", iris="eye_dark", eye_style="toy", body_scale=0.82, head_k=1.15, head_c=(0, 0, 1.19),
         head_r=(0.27, 0.25, 0.26), jaw_taper=0.12, cranium=0.05, eye_az=20, eye_el=-3, eye_size=(0.048, 0.056), lash=False,
         freckles=False, brow_w=0.014, mouth_w=0.052, hair_style="short", headgear="none", kit="kit_white", kit_trim="kit_blue",
         bottom="shorts", bottom_mat="accent_teal", sock="kit_white", sock_stripe="kit_blue", shoe="plastic_dark",
         shoe_accent="kit_white", glove=None, glove_cuff=None, glove_size=(0.1, 0.1, 0.1), number=""),
]

def pose_spectator(arm, mode):
    pbs = arm.pose.bones
    for n in ("forearm_L", "forearm_R", "shin_L", "shin_R", "foot_L", "foot_R"):
        for c in pbs[n].constraints:
            c.mute = True
    def aim(bn, target):
        b = arm.data.bones[bn]; R = b.matrix_local.to_3x3()
        q = (R @ V((0, 1, 0))).rotation_difference(V(target).normalized())
        loc = (R.inverted() @ q.to_matrix() @ R).to_quaternion()
        pbs[bn].rotation_mode = "QUATERNION"; pbs[bn].rotation_quaternion = loc
        return loc
    fv = FACE["big_smile" if mode != "seated" else "smile"]
    if mode in ("cheer", "seated_cheer"):
        aim("upperarm_L", (0.45, -0.15, 0.88)); aim("upperarm_R", (-0.45, -0.15, 0.88))
    else:
        aim("upperarm_L", (0.35, -0.2, -0.9)); aim("upperarm_R", (-0.35, -0.2, -0.9))
    if mode.startswith("seated"):
        for sd in ("L", "R"):
            q = aim("thigh_" + sd, (0, -1, -0.08))
            pbs["shin_" + sd].rotation_mode = "QUATERNION"; pbs["shin_" + sd].rotation_quaternion = q.inverted()
    apply_face(arm, "big_smile" if "cheer" in mode else "smile")

def build_character_full(spec, coll_, fam, base, loc, rotz=0.0, face=None, stick=True, **pose_kw):
    arm = build_skeleton(spec, coll_, spec["name"] + "_rig")
    parts = build_character(spec, coll_, arm)
    st = meta = None
    if stick:
        st, meta = build_stick("attack" if fam == "field" else "goalie", coll_, arm, name=spec["name"] + "_stick")
    p = finalize(P(base, face=face or base["face"], **pose_kw))
    if stick:
        calibrate_poles(arm, [p], fam); apply_pose(arm, p, fam)
    arm.location = loc; arm.rotation_euler.z = rotz
    return arm, parts, st, meta

def add_ball_in_pocket(arm, meta, coll_):
    b = obj_from_geo("ball", ball_geo(), "ball", coll_)
    b.parent = arm; b.parent_type = "BONE"; b.parent_bone = "pocket_01"
    bpy.context.view_layer.update()
    arm.data.pose_position = "REST"; bpy.context.view_layer.update()
    Mw = arm.matrix_world @ arm.data.bones["stick"].matrix_local @ Matrix.Translation(meta["pocket_center"])
    b.matrix_world = Mw
    arm.data.pose_position = "POSE"; bpy.context.view_layer.update()
    return b

def setup_textures():
    tdir = os.path.join(PROD, "Arena", "Textures")
    a = os.path.join(tdir, "turf_albedo.png"); b = os.path.join(tdir, "turf_albedo_mow.png")
    if not os.path.exists(a):
        make_turf_texture(a, (0.13, 0.40, 0.07), 1024, 5)
    if not os.path.exists(b):
        make_turf_texture(b, (0.10, 0.32, 0.055), 1024, 6)
    TEX_MATS["turf_tex"] = (a, 0.9); TEX_MATS["turf_tex_mow"] = (b, 0.9)
    UV_PLANAR["turf_tex"] = 0.35; UV_PLANAR["turf_tex_mow"] = 0.35

def build_scene():
    reset_scene("LaxStyleValidation")
    setup_textures()
    D = coll("Diorama"); Ch = coll("Characters", D); En = coll("Environment", D); Cr = coll("Crowd", D); Fg = coll("Foreground", D)
    Lk = coll("Lookdev")
    setup_world(); setup_lights(Lk); setup_eevee(64, (720, 1560))
    # --- playable field (layer 2) + arena edge (layer 3)
    field_platform(En, turf=("turf_tex", "turf_tex_mow")); field_markings(En)
    build_goal(En)
    rail_fence(En, [(6.8, 5.0), (6.8, -12.4), (-6.8, -12.4), (-6.8, 5.0)], name="field_fence")
    bench(En, (-6.0, -1.5, 0), 2.2, math.radians(90))
    # --- characters
    girl, gparts, gst, gmeta = build_character_full(GIRL_FIELD, Ch, "field", BASE_FIELD, (0.72, 1.72, 0), face="focused")
    add_ball_in_pocket(girl, gmeta, Ch)
    goalie, _, _, _ = build_character_full(BOY_GOALIE, Ch, "goalie", BASE_GOALIE, (0.0, -4.95, 0), rotz=math.pi, face="determined")
    # --- spectator layer (4): small bleacher off the right corner, behind the fence
    bleacher(Cr, (-5.2, -14.4, -0.45), 3.4, 3)
    fb, *_ = build_character_full(SPECTATORS[1], Cr, "field", BASE_FIELD, (-5.6, -14.4 + 0.9, 0.21), stick=False)
    pose_spectator(fb, "seated_cheer")
    fa, *_ = build_character_full(SPECTATORS[0], Cr, "field", BASE_FIELD, (-4.4, -14.4 + 0.45, -0.15), stick=False)
    pose_spectator(fa, "seated_cheer")
    wooden_sign("PINEBROOK\nFIELD", Cr, (4.2, -12.95, 0.0), 1.9, 0.9, 0.6, 0.0, 0.26, "sign_field")
    wooden_sign("GOOD PLAYERS\nBRIGHTER DAYS", Cr, (-3.3, -12.95, 0.0), 1.6, 0.7, 0.45, 0.0, 0.15, "sign_slogan")
    # --- scenic middle distance (5): hedges, broadleaf woods, lakeside
    obj_from_geo("meadow", superellipsoid((160, 60, 1.0), 0.15, 0.1, 48, 6, (0, -8, -0.95)), "turf_tex", En)
    for i, x in enumerate((-2.4, -1.3, -0.2, 0.9, 2.0, 3.1, -3.5, -5.2, 5.4)):
        bush(60 + i, 1.0 + 0.25 * (i % 3), En, loc=(x, -13.3 - 0.3 * (i % 2), -0.45))
    for i, (x, y, h) in enumerate(((4.2, -15.0, 4.6), (6.8, -16.5, 5.4), (9.5, -14.2, 4.8), (-7.6, -15.2, 5.0), (-9.8, -17.0, 5.6),
                                   (11.8, -17.5, 5.0), (-12.5, -14.6, 4.6))):
        deciduous(40 + i, h, En, loc=(x, y, -0.45), n=11)
    for i, (x, y, h) in enumerate(((13.5, -15.5, 5.8), (-14.0, -18.5, 6.2))):
        pine(10 + i, h, En, loc=(x, y, -0.45))
    lake(En, (0, -31, -0.45), (90, 22))
    sailboat(En, (-5.5, -31.5, -0.40), 1.5); sailboat(En, (8.5, -37, -0.40), 1.1)
    far_shore(En, -46, -70, 70, 21, 7.0)
    # --- distant background (6) + sky (7)
    mountain_range(En, -150, -130, 130, 30, 9, "mountain_far", True, 20, "mountains_far")
    for i, (x, y, z, s) in enumerate(((-13, -70, 14.5, 4.0), (9, -78, 17.5, 4.6), (-1, -95, 23, 3.6), (21, -92, 13, 3.2), (-24, -88, 20, 4.2))):
        cloud(90 + i, En, (x, y, z), s)
    # --- foreground framing (1): soft corner hedges + a post with a water bottle (bottom corners, clear of the swipe zone centre)
    bush(80, 1.1, Fg, loc=(1.35, 2.95, 0)); bush(81, 0.9, Fg, loc=(-1.25, 3.05, 0))
    fp = Builder("fg_post"); fp.add(superellipsoid((0.16, 0.16, 0.9), 0.35, 0.35, 8, 6, (0, 0, 0.45)), "wood"); fp.build(Fg).location = (-0.98, 2.75, 0)
    props_bottle(Fg, (-0.98, 2.75, 0.9), "accent_teal")
    rock(4, (0.34, 0.3, 0.26), Fg, (1.05, 2.55, 0), "rock_warm"); grass_tuft(30, Fg, (0.8, 2.4, 0), 0.26)
    props_bag(Fg, (2.2, 2.5, 0), 0.5); props_balls(Fg, [(-1.9, 2.4), (2.5, 3.2)])
    # --- cameras
    cams = {}
    cams["game"] = make_camera("cam_runtime", game_to_blender((0, 2.9, 6.1)), game_to_blender((0, 0.95, -3.85)), Lk, vfov_deg=52)
    cams["ref"] = make_camera("cam_reference", (0.3, 7.0, 4.3), (0.15, -3.5, 0.4), Lk, vfov_deg=50)
    cams["p34"] = make_camera("cam_three_quarter", (-0.35, 7.2, 3.6), (0.3, -3.6, 0.7), Lk, vfov_deg=44)
    cams["goal"] = make_camera("cam_goal", (1.9, -1.2, 1.55), (0.0, -6.0, 0.95), Lk, lens=45, portrait=False)
    cams["env"] = make_camera("cam_env", (0.0, 3.5, 5.5), (0.0, -40.0, 3.0), Lk, vfov_deg=58)
    focus = bpy.data.objects.new("dof_focus", None); Lk.objects.link(focus); focus.location = (0.3, -1.2, 0.9)
    return dict(girl=girl, goalie=goalie, cams=cams, focus=focus)

def build_lineup(x0=60.0):
    L = coll("Lineup"); Lk = bpy.data.collections["Lookdev"]
    obj_from_geo("lineup_sweep", superellipsoid((16, 8, 0.2), 0.2, 0.2, 32, 8, (x0, -1.0, -0.1)), "sign_paint", L)
    obj_from_geo("lineup_back", superellipsoid((16, 0.2, 7), 0.2, 0.2, 32, 8, (x0, 3.0, 3.4)), "sign_paint", L)
    g, *_ = build_character_full(dict(GIRL_FIELD, name="girl_field_lineup"), L, "field", BASE_FIELD, (x0 - 2.7, 0.6, 0), face="smile")
    k, *_ = build_character_full(dict(BOY_GOALIE, name="boy_goalie_lineup"), L, "goalie", BASE_GOALIE, (x0 - 4.5, 0.6, 0), face="smile")
    f, *_ = build_character_full(dict(SPECTATORS[0], name="fan_lineup"), L, "field", BASE_FIELD, (x0 - 1.0, 0.8, 0), stick=False)
    pose_spectator(f, "cheer")
    st, meta = build_stick("attack", L, None, name="attack_stick_lineup")
    st.location = (x0 + 0.3, -1.7, 0.12); st.rotation_euler = (math.radians(12), 0, math.radians(-58))
    obj_from_geo("lineup_ball", ball_geo(meta["pocket_center"]), "ball", L).parent = st
    # goal pipe + net section
    frame, cords, gm, net_pt = goal_geo(0.7)
    B = Builder("goal_section")
    for gg in frame[:1]:
        B.add(gg, "goal_orange")
    for gg in cords:
        B.add(gg, "cord_white")
    sec = B.build(L); sec.location = (x0 + 1.2, 1.4, 0); sec.scale = (0.6, 0.6, 0.6); sec.rotation_euler.z = math.radians(200)
    turf = Builder("turf_tile")
    turf.add(superellipsoid((0.9, 0.9, 0.18), 0.15, 0.1, 24, 6, (0, 0, 0.09)), "soil")
    turf.add(superellipsoid((0.86, 0.43, 0.04), 0.2, 0.1, 16, 4, (0, -0.215, 0.19)), "turf_a")
    turf.add(superellipsoid((0.86, 0.43, 0.04), 0.2, 0.1, 16, 4, (0, 0.215, 0.19)), "turf_b")
    turf.add(superellipsoid((0.86, 0.05, 0.012), 0.2, 0.1, 16, 4, (0, 0.0, 0.215)), "line_white")
    t = turf.build(L); t.location = (x0 - 2.3, -1.9, 0)
    rock(5, (0.5, 0.4, 0.38), L, (x0 - 1.0, -1.9, 0))
    pine(7, 2.2, L, loc=(x0 + 3.1, 0.9, 0)); deciduous(8, 2.3, L, loc=(x0 + 4.9, 1.0, 0))
    wooden_sign("BOUNCE IT!", L, (x0 + 2.6, -1.7, 0), 1.1, 0.42, 0.45, 0.0, 0.14, "sign_lineup")
    lk = lake(L, (x0 - 4.2, -1.9, 0.3), (1.6, 1.1))
    c = cloud(3, L, (x0 + 1.9, 1.2, 3.4), 0.42)
    cam = make_camera("cam_lineup", (x0 + 0.1, -13.5, 3.6), (x0 + 0.1, 0, 0.95), Lk, lens=40, portrait=False)
    cc = make_camera("cam_char_close", (x0 - 3.6, -3.3, 1.35), (x0 - 3.6, 0.6, 0.85), Lk, lens=50, portrait=False)
    cc.data.sensor_fit = "HORIZONTAL"
    cb = make_camera("cam_char_bust", (x0 - 3.6, -2.0, 1.28), (x0 - 3.6, 0.6, 1.12), Lk, lens=50, portrait=False)
    cb.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_fit = "HORIZONTAL"
    return cam

def lineup_override(on):
    vl = bpy.context.view_layer
    vl.material_override = mat("clay") if on else None
