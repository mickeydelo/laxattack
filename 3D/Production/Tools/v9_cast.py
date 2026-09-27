# v9.7 supporting cast: boy field #22, girl goalie #30, fans A/B/C. Built on each asset's ORIGINAL spec so rigs/contracts are preserved.
MATS.update({k: (_lin(c), r, 0.0, co) for k, (c, r, co) in {
    "helmet_cream_v9": ((0.97, 0.93, 0.85), 0.24, 0.4), "skin_v9_mid": ((0.86, 0.62, 0.44), 0.36, 0.25),
    "hair_v9_auburn": ((0.55, 0.27, 0.14), 0.35, 0.3), "knit_teal_v9": ((0.10, 0.45, 0.52), 0.85, 0.0)}.items()})

def v9_hair_short(s, H, Hb):
    bnd = lambda az: _interp([(0, 32), (20, 27), (45, 16), (75, 8), (100, -8), (140, -28), (180, -34)], az)
    cap, rim = hair_cap(H, bnd, base=1.05, grooves=20, depth=0.030, part=True, back_bulge=0.03, pole=H.point(180, -10, 1.1))
    Hb.add(cap, s["hair"], "head"); Hb.add(sweep(rim, [0.011] * len(rim), 8, 1.0, cap0=False, cap1=False), s["hair"], "head")

def v9_hair_pigtails(s, H, Hb):
    v9_hair_short(s, H, Hb)
    tie = s.get("hair_tie", "tie_cream")
    for sx in (1, -1):
        root = V(H.point(98 * sx, 6, 1.10))
        pts = [tuple(root), tuple(root + V((0.05 * sx, 0.01, -0.05))), tuple(root + V((0.08 * sx, 0.02, -0.14))), tuple(root + V((0.07 * sx, 0.02, -0.22)))]
        Hb.add(sweep(pts, [0.050, 0.052, 0.040, 0.008], 12, 0.5), s["hair"], "head")
        Hb.add(torus(tuple(root + V((0.012 * sx, 0.0, -0.012))), 0.042, 0.013, 18, 8, "X"), tie, "head")

def v9_cap(s, H, G):
    mat = s.get("cap_mat", "kit_navy_v9"); brim = s.get("cap_brim", mat)
    bnd = lambda az: _interp([(0, 20), (60, 14), (100, 6), (180, 2)], az)
    shell, rim = hair_cap(H, bnd, base=1.12, grooves=6, depth=0.004, part=False, back_bulge=0.0)
    G.add(shell, mat, "head"); G.add(sweep(rim, [0.012] * len(rim), 8, 1.0, cap0=False, cap1=False), mat, "head")
    p, tx, n, tu = H.frame(0, 18)
    G.add(xform(superellipsoid((0.16, 0.13, 0.012), 0.35, 0.8, 18, 6, (0, 0, 0)),
                Matrix.Translation(tuple(V(p) + V(n) * 0.10 - V(tu) * 0.01)) @ Matrix.Rotation(-0.25, 4, "X")), brim, "head")
    G.add(ellipsoid(tuple(H.point(0, 90, 1.135)), (0.022, 0.022, 0.012), 10, 6), brim, "head")

def v9_beanie(s, H, G):
    mat = s.get("beanie_mat", "knit_teal_v9"); pom = s.get("beanie_pom", "kit_gold_v9")
    bnd = lambda az: _interp([(0, 22), (90, 12), (180, 4)], az)
    shell, rim = hair_cap(H, bnd, base=1.11, grooves=28, depth=0.010, part=False, back_bulge=0.02)
    G.add(shell, mat, "head")
    cuff = [H.point(az, bnd(az) + 3, 1.13) for az in range(-180, 181, 6)]
    G.add(sweep(cuff, [0.026] * len(cuff), 10, 1.0, cap0=False, cap1=False), mat, "head")
    curl_cluster(G, H.point(0, 90, 1.24), 0.055, pom, 40, 0.016, 77)

_V9FACE = dict(v9=True, iris="eye_v9", eye_size=(0.0267, 0.0397), eye_az=25.0, eye_el=-11.0, lid_park_deg=55.0, head_r=(0.285, 0.258, 0.27),
               limb_k=1.4, hand_k=1.35, torso_k=1.18, shoe_k=1.45, lash=False, freckles=False)
BOY_FIELD_V9 = dict(BOY_FIELD, name="lax_boy_field_v9", **_V9FACE, v9_look="player", skin="skin_v9_mid", hair="hair_v9", v9_hair="helmet_curls",
                    v9_headgear="helmet", helmet_shell="helmet_cream_v9", helmet_stripe="kit_red_v9", number="22", kit="kit_cream_v9", kit_trim="kit_red_v9",
                    number_mat="kit_red_v9", bottom="shorts_v9", bottom_mat="kit_red_v9", bottom_trim="kit_cream_v9", glove="kit_red_v9", glove_cuff="kit_cream_v9",
                    sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_red_v9", sole="kit_red_v9",
                    front_number_size=0.16, front_number_x=-0.07, front_number_z=0.66, stick_frame="stick_cream_v9", stick_pocket="cord_tan_v9",
                    stick_bag="cord_tan_dark_v9", stick_shaft="metal_silver_v9", stick_strings="cord_tan_v9", stick_grip="grip_dark_v9")
GIRL_GOALIE_V9 = dict(GIRL_GOALIE, name="lax_girl_goalie_v9", **_V9FACE, v9_look="goalie", skin="skin_v9_deep", hair="hair_v9_dark", v9_hair="helmet_bun",
                      v9_headgear="helmet", helmet_shell="helmet_navy_v9", helmet_stripe="kit_gold_v9", goalie_pads=True, chest_protector=False, number="30",
                      kit="kit_navy_v9", kit_trim="kit_gold_v9", number_mat="sock_white_v9", bottom="shorts_v9", bottom_mat="kit_navy_v9", bottom_trim="kit_gold_v9",
                      glove="kit_navy_v9", glove_cuff="kit_gold_v9", sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", shoe_accent="kit_navy_v9",
                      sole="kit_gold_v9", stick_frame="stick_cream_v9", stick_pocket="cord_cream", stick_bag="cord_cream_dark", stick_shaft="metal_silver_v9",
                      stick_strings="cord_cream", stick_grip="kit_navy_v9")
_FANK = dict(bottom="shorts_v9", sock="sock_white_v9", sock_stripe="sock_white_v9", shoe="cleat_white_v9", number="")
FAN_A_V9 = dict(SPECTATORS[0], name="lax_fan_a_v9", **_V9FACE, **_FANK, v9_look="player", skin="skin_v9", hair="hair_v9", v9_hair="pigtails", v9_headgear="none",
                hair_tie="kit_red_v9", kit="kit_red_v9", kit_trim="kit_cream_v9", bottom_mat="kit_navy_v9", bottom_trim="kit_cream_v9", shoe_accent="kit_red_v9", sole="kit_red_v9")
FAN_B_V9 = dict(SPECTATORS[1], name="lax_fan_b_v9", **_V9FACE, **_FANK, v9_look="player", skin="skin_v9_deep", hair="hair_v9_dark", v9_hair="short",
                v9_headgear="cap", cap_mat="kit_navy_v9", cap_brim="kit_cyan_v9", kit="kit_navy_v9", kit_trim="kit_cyan_v9", bottom_mat="kit_cream_v9",
                bottom_trim="kit_cyan_v9", shoe_accent="kit_navy_v9", sole="kit_cyan_v9")
FAN_C_V9 = dict(FAN_C, name="lax_fan_c_v9", **_V9FACE, **_FANK, v9_look="player", skin="skin_v9_mid", hair="hair_v9_auburn", v9_hair="short",
                v9_headgear="beanie", beanie_mat="knit_teal_v9", beanie_pom="kit_gold_v9", kit="kit_gold_v9", kit_trim="kit_teal_v9", bottom_mat="kit_teal_v9",
                bottom_trim="kit_gold_v9", shoe_accent="kit_teal_v9", sole="kit_gold_v9")
FAN_C_V9["body_scale"] = FAN_C["body_scale"]; FAN_C_V9["head_k"] = FAN_C["head_k"]
