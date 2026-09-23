# Lax Attack art-direction checkpoint scene. Run inside Blender with lax_core/lax_figure/lax_pose/lax_env loaded
# into the same namespace (see load_libs). Builds a gameplay diorama at the origin and a catalog lineup stage at x=+60.
import bpy, os, math
OUT = os.path.join(PROD, "Previews", "StyleValidation")
BLEND = os.path.join(PROD, "StyleValidation", "LaxAttackStyleValidation.blend")

SPECTATORS = [
    dict(name="fan_a", family="field", skin="skin_light", hair="hair_blond", iris="iris_blue", head_c=(0, 0, 1.195),
         head_r=(0.262, 0.248, 0.268), jaw_taper=0.2, cranium=0.07, eye_az=19, eye_el=-5, eye_size=(0.05, 0.062), lash=True,
         freckles=False, brow_w=0.01, mouth_w=0.046, mouth_el=-28, hair_style="ponytail", headgear="cap", cap_mat="kit_blue",
         kit="accent_gold", kit_trim="kit_white", bottom="shorts", bottom_mat="kit_navy", sock="kit_white", sock_stripe="kit_white",
         shoe="kit_white", shoe_accent="accent_coral", glove=None, glove_cuff=None, glove_size=(0.1, 0.1, 0.1), number=""),
    dict(name="fan_b", family="field", skin="skin_deep", hair="hair_dark", iris="iris_brown", head_c=(0, 0, 1.19),
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
    b = obj_from_geo("ball", ball_geo(), "ball_yellow", coll_)
    b.parent = arm; b.parent_type = "BONE"; b.parent_bone = "pocket_01"
    bpy.context.view_layer.update()
    arm.data.pose_position = "REST"; bpy.context.view_layer.update()
    Mw = arm.matrix_world @ arm.data.bones["stick"].matrix_local @ Matrix.Translation(meta["pocket_center"])
    b.matrix_world = Mw
    arm.data.pose_position = "POSE"; bpy.context.view_layer.update()
    return b

def build_scene():
    reset_scene("LaxStyleValidation")
    D = coll("Diorama"); Ch = coll("Characters", D); En = coll("Environment", D); Cr = coll("Crowd", D); Fg = coll("Foreground", D)
    Lk = coll("Lookdev")
    setup_world(); setup_lights(Lk); setup_eevee(64, (720, 1560))
    # --- playable field (layer 2) + edge (layer 3)
    field_platform(En); field_markings(En)
    build_goal(En)
    board_wall(En, -6.6, -2.4, -12.2, name="boards_back_R"); board_wall(En, 2.4, 6.6, -12.2, name="boards_back_L")
    board_wall(En, -12.0, 3.5, 6.75, name="boards_side_R", rot=math.radians(90))
    bench(En, (-5.9, -1.5, 0), 2.2, math.radians(90))
    # --- characters
    girl, gparts, gst, gmeta = build_character_full(GIRL_FIELD, Ch, "field", BASE_FIELD, (0.72, 1.72, 0), face="focused")
    add_ball_in_pocket(girl, gmeta, Ch)
    goalie, _, _, _ = build_character_full(BOY_GOALIE, Ch, "goalie", BASE_GOALIE, (0.0, -4.95, 0), rotz=math.pi, face="determined")
    # --- spectator layer (4)
    bleacher(Cr, (-4.3, -13.6, 0), 3.4, 3); bleacher(Cr, (4.3, -13.6, 0), 3.4, 3)
    fa, *_ = build_character_full(SPECTATORS[0], Cr, "field", BASE_FIELD, (-4.9, -13.6 + 0.45, 0.30), stick=False)
    pose_spectator(fa, "seated_cheer")
    fb, *_ = build_character_full(SPECTATORS[1], Cr, "field", BASE_FIELD, (4.0, -13.6 + 0.9, 0.66), stick=False)
    pose_spectator(fb, "seated_cheer")
    banner(Cr, (-3.6, -12.9, 0.4), "LAX LIFE", 1.5, 0.45, "kit_blue")
    wooden_sign("SMALL SHOTS\nBIG PLAYS", Cr, (3.2, -12.9, 0.0), 1.5, 0.62, 0.55, 0.0, 0.15, "sign_slogan")
    # --- scenic middle distance (5): meadow, woods, lake, dock
    obj_from_geo("meadow", superellipsoid((140, 110, 1.0), 0.15, 0.1, 48, 6, (0, -62, -0.95)), "foliage_a", En)
    for i, (x, y, h) in enumerate(((-7.8, -15.5, 4.2), (-9.5, -18.0, 5.0), (-6.5, -19.0, 3.6), (8.2, -16.0, 4.6), (9.8, -19.5, 5.2),
                                   (6.6, -18.6, 3.8), (-12, -22, 5.5), (12.5, -23, 5.8), (-4.8, -24.5, 3.0), (5.2, -25, 3.2))):
        pine(10 + i, h, En, loc=(x, y, -0.45))
    for i, (x, y, h) in enumerate(((-5.2, -17.0, 3.0), (5.8, -17.2, 3.2), (-10.8, -14.0, 3.6), (10.6, -13.6, 3.4))):
        deciduous(40 + i, h, En, loc=(x, y, -0.45))
    for i, x in enumerate((-2.0, -0.6, 0.9, 2.3)):
        bush(60 + i, 0.9, En, loc=(x, -14.8, -0.45))
    lake(En, (0, -42, -0.45), (60, 26))
    dock(En, (-6, -31.5, -0.45), 3.6, math.radians(8)); sailboat(En, (7, -44, -0.40), 1.3); sailboat(En, (-11, -50, -0.40), 1.0)
    for i in range(14):
        x = -34 + i * 5.2
        pine(80 + i, 6.5 + (i * 37 % 5), En, tiers=3, loc=(x, -58 - (i % 3) * 2.5, -0.45))
    # --- distant background (6) + sky (7)
    mountain_range(En, -95, -80, 80, 22, 7, "mountain", True, 16, "mountains_near")
    mountain_range(En, -130, -110, 110, 30, 9, "mountain_far", True, 20, "mountains_far")
    for i, (x, y, z, s) in enumerate(((-13, -70, 13.5, 4.0), (9, -78, 16.5, 4.6), (-1, -95, 22, 3.6), (21, -92, 12, 3.2), (-24, -88, 19, 4.2))):
        cloud(90 + i, En, (x, y, z), s)
    # --- foreground framing (1)
    rock(1, (0.55, 0.45, 0.42), Fg, (-1.55, 3.3, 0)); rock(2, (0.35, 0.3, 0.25), Fg, (-1.2, 3.9, 0))
    rock(3, (0.5, 0.42, 0.36), Fg, (1.7, 3.5, 0), "rock_warm")
    for i, (x, y) in enumerate(((-1.35, 3.0), (1.45, 3.1), (-1.8, 3.8), (1.95, 3.9), (1.1, 4.2))):
        grass_tuft(20 + i, Fg, (x, y, 0), 0.32)
    props_bag(Fg, (2.2, 2.5, 0), 0.5); props_bottle(Fg, (1.75, 2.35, 0)); props_bottle(Fg, (1.85, 2.2, 0), "accent_coral")
    props_balls(Fg, [(-1.9, 2.4), (-1.75, 2.6), (2.5, 3.2)])
    fence(Fg, -3.2, -2.1, 4.6)
    # runtime-frustum framing (bottom-right corner of the portrait frame; clear of shooter, HUD, ball path)
    rock(4, (0.34, 0.3, 0.26), Fg, (-0.66, 2.62, 0), "rock_warm"); grass_tuft(30, Fg, (-0.55, 2.45, 0), 0.26)
    grass_tuft(31, Fg, (-0.86, 2.9, 0), 0.3); props_balls(Fg, [(-0.42, 2.8)])
    # --- cameras
    cams = {}
    cams["game"] = make_camera("cam_runtime", game_to_blender((0, 2.9, 6.1)), game_to_blender((0, 0.95, -3.85)), Lk, vfov_deg=52)
    cams["p34"] = make_camera("cam_three_quarter", (-0.35, 7.2, 3.6), (0.3, -3.6, 0.7), Lk, vfov_deg=44)
    cams["goal"] = make_camera("cam_goal", (1.9, -1.2, 1.55), (0.0, -6.0, 0.95), Lk, lens=45, portrait=False)
    cams["env"] = make_camera("cam_env", (0.0, 3.5, 5.5), (0.0, -40.0, 3.0), Lk, vfov_deg=58)
    focus = bpy.data.objects.new("dof_focus", None); Lk.objects.link(focus); focus.location = (0.3, -0.6, 0.9)
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
    obj_from_geo("lineup_ball", ball_geo(meta["pocket_center"]), "ball_yellow", L).parent = st
    # goal pipe + net section
    frame, cords, gm, net_pt = goal_geo(0.7)
    B = Builder("goal_section")
    for gg in frame[:1]:
        B.add(gg, "metal_red")
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
