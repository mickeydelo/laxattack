# Lax Attack Phase 7: boy field hero (lax_boy_field) + girl goalie (lax_girl_goalie). Reuse the shared rigs/clip libraries
# with character-specific personality layers so each hero moves differently.
BOY_FIELD = dict(GIRL_FIELD, name="boy_field", skin="skin_brown", hair="hair_dark", jaw_taper=0.10, cranium=0.04,
                 eye_az=21.0, eye_el=-7.0, eye_size=(0.042, 0.052), lash=False, brow_w=0.012, mouth_w=0.042, mouth_el=-30.0,
                 hair_style="short", number="22", glove="glove_dark", glove_cuff="glove_dark", body_scale=0.84)
GIRL_GOALIE = dict(BOY_GOALIE, name="girl_goalie", skin="skin_deep", hair="hair_dark", jaw_taper=0.16, cranium=0.05,
                   eye_az=22.0, eye_el=-8.0, eye_size=(0.044, 0.056), lash=True, brow_w=0.008, mouth_w=0.036, mouth_el=-31.0,
                   hair_style="ponytail_helmet", pony_el=-22.0, pony_len=0.72, number="30", body_scale=0.82)

def personality(fn, kind, period=24.0):
    """Additive personality layer on top of a shared clip."""
    def g(t):
        p = dict(fn(t)); ph = 2 * math.pi * t / period   # whole cycles per loop keep seams clean
        if kind == "boy":      # confident swagger: chest up, head bob, wider cradle, smirks
            p["chest_rot"] = (p["chest_rot"][0] - 3, p["chest_rot"][1], p["chest_rot"][2] + 2 * math.sin(ph))
            p["head_rot"] = (p["head_rot"][0] - 2 + 2.5 * math.sin(2 * ph), p["head_rot"][1], p["head_rot"][2] - 3)
            p["pelvis_off"] = (p["pelvis_off"][0] + 0.008 * math.sin(ph), p["pelvis_off"][1], p["pelvis_off"][2])
            if p.get("face") in ("smile", "neutral"):
                p["face"] = "smirk"
        else:                  # goalie with bounce: springier knees, big celebrations
            p["pelvis_off"] = (p["pelvis_off"][0], p["pelvis_off"][1], p["pelvis_off"][2] - 0.012 * abs(math.sin(ph)))
            p["head_rot"] = (p["head_rot"][0], p["head_rot"][1] + 3 * math.sin(ph), p["head_rot"][2])
            if p.get("face") == "smile":
                p["face"] = "big_smile"
        return finalize(p)
    return g

def build_variant(spec, asset, clips_src, family, kind, required, stick_kind, frame_mat, pocket_mat, face_plus_z, cal):
    reset_scene("LaxAttack_" + spec["name"])
    C = coll(asset)
    arm = build_skeleton(spec, C, asset + "_rig")
    parts = build_character(spec, C, arm)
    stick, meta = build_stick(stick_kind, C, arm, name=asset + "_stick", frame_mat=frame_mat, pocket_mat=pocket_mat)
    socks = add_character_sockets(spec, arm, C, meta)
    ad = arm.data; ad.pose_position = "REST"; bpy.context.view_layer.update()
    Ms = ad.bones["stick"].matrix_local.copy()
    socks["ball_contact_socket"] = add_socket("ball_contact_socket", arm, "pocket_01", Ms @ Matrix.Translation(meta["ball_contact"]), C, 0.03)
    ad.pose_position = "POSE"
    clips = [Clip(c.name, c.start, c.length, c.loop, personality(c.fn, kind, float(c.length) if c.loop else 24.0), c.contact, c.release, c.transition, c.notes, c.blinks) for c in clips_src]
    calibrate_poles(arm, cal, family)
    bake_clips(arm, clips, family, GOALIE_EXTRA if family == "goalie" else ())
    meshes = list(parts.values()) + [stick]
    rep = {"validation": validate_character(arm, clips, meshes, meta, REQUIRED_SOCKETS, required)}
    d = os.path.join(PROD, "Characters", "BoyField" if kind == "boy" else "GirlGoalie"); os.makedirs(d, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(d, "LaxAttack_" + spec["name"] + ".blend"), compress=True)
    man = manifest(asset, clips, perspective="goalie" if family == "goalie" else "shooter", extra={
        "shares_timeline_with": "lax_goalie" if family == "goalie" else "lax_shooter",
        "note": "same clip names and frame ranges as the shared-family hero; personality layer changes the motion, not the timing"})
    rep["export"] = export_asset([arm] + meshes + list(socks.values()), asset, asset + "_rig", os.path.join(EXP, asset + ".usdz"),
                                 30, clips[-1].end, face_plus_z, man, REQUIRED_SOCKETS + ["ball_contact_socket"])
    with open(os.path.join(EXP, asset + "_clips.json"), "w") as fh:
        json.dump(man, fh, indent=2)
    return rep

def build_phase7():
    r1 = build_variant(BOY_FIELD, "lax_boy_field", CLIPS, "field", "boy", REQUIRED_CLIPS, "attack", "plastic_white", "cord_navy", False,
                       [GB, AIM_O, AIM_S, QS])
    r2 = build_variant(GIRL_GOALIE, "lax_girl_goalie", BG_CLIPS, "goalie", "girl_goalie", GOALIE_CLIPS, "goalie", "helmet_teal", "cord_white", True,
                       [GK, READ_L, SAVE_L, SAVE_HL, mirror(SAVE_L)])
    return r1, r2
