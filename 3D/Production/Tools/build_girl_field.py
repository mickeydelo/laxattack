# Lax Attack Phase 2: production girl field hero, exported as lax_shooter (keeps the graybox contract).
# Run inside Blender with lax_core, lax_figure, lax_pose, lax_anim, lax_export, lax_validate loaded in one namespace.
GF_DIR = os.path.join(PROD, "Characters", "GirlField")
EXP = os.path.join(PROD, "Exports")
REQUIRED_CLIPS = ["idle", "cradle", "aim_overhand", "aim_bounce", "aim_sidearm", "split_dodge_left", "split_dodge_right",
                  "release_overhand", "release_bounce", "release_sidearm", "quick_stick_catch", "quick_stick_release",
                  "celebrate", "disappointed"]
REQUIRED_SOCKETS = ["stick_socket", "helmet_socket", "effect_socket", "pocket_socket", "left_hand_socket", "right_hand_socket",
                    "eyes_socket", "camera_focus_socket", "chest_socket"]

GB = finalize(P(BASE_FIELD, G=(-0.27, -0.26, 0.82), D=(-0.60, 0.05, 0.80), F=(0.55, -0.83, 0.10), face="neutral"))
def K(**kw):
    return P(GB, **kw)

def rotY(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Y")

def looped_stick(swing, roll, g_off):
    D0 = V(GB["D"]).normalized(); F0 = orth(GB["F"], D0)
    R = rotY(swing); D = R @ D0; F = R @ F0
    F = Matrix.Rotation(math.radians(roll), 3, D) @ F
    return dict(G=tuple(V(GB["G"]) + V(g_off)), D=tuple(D), F=tuple(F))

def idle_pose(t, N=48):
    ph = 2 * math.pi * t / N; s = math.sin(ph); b = 0.5 - 0.5 * math.cos(ph)
    p = K(pelvis_off=(0.006 * s, 0, -0.035 - 0.012 * b), spine_rot=(6 + 1.5 * b, -4, 0), chest_rot=(4 + 2.0 * b, -4 + 2 * s, 0),
          head_rot=(-6 + 2.5 * s, 8 + 5 * s, 3 * s), eye=(3 * s, 0), pocket=0.004 + 0.002 * b)
    p.update(looped_stick(3 * s, 6 * s, (0.004 * s, 0, -0.004 * b)))
    return finalize(p)

def cradle_pose(t, N=28):
    ph = 2 * math.pi * t / N; s = math.sin(ph); s2 = math.sin(2 * ph); b2 = 0.5 - 0.5 * math.cos(2 * ph)
    p = K(pelvis_off=(0.014 * s, 0, -0.04 - 0.02 * b2), pelvis_rot=(2 * b2, -6 - 3 * s, 2 * s), spine_rot=(6 + 2 * b2, -4, 2.5 * s),
          chest_rot=(4, -4 + 9 * s, -1.5 * s), head_rot=(-6 + 1.5 * s2, 8 - 7 * s, -1.0 * s), face="focused",
          pocket=0.008 + 0.006 * math.sin(ph - 1.1))   # ball lags the cradle sweep
    p.update(looped_stick(16 * s, 55 * s, (-0.012 * s, -0.014 * s, 0.014 * b2)))
    return finalize(p)

def aim_loop(base, N=30):
    def fn(t):
        ph = 2 * math.pi * t / N; s = math.sin(ph); b = 0.5 - 0.5 * math.cos(ph)
        p = dict(base)
        p["pelvis_off"] = (base["pelvis_off"][0], base["pelvis_off"][1], base["pelvis_off"][2] - 0.006 * b)
        p["G"] = tuple(V(base["G"]) + V((0.006 * s, 0, 0.008 * b)))
        p["head_rot"] = (base["head_rot"][0], base["head_rot"][1] + 2 * s, base["head_rot"][2])
        p["pocket"] = base["pocket"] + 0.002 * s
        return finalize(p)
    return fn

AIM_O = finalize(K(pelvis_off=(-0.008, 0.02, -0.06), pelvis_rot=(-2, -14, -2), spine_rot=(-1, -11, -2), chest_rot=(-3, -13, 0),
                   neck_rot=(-2, 12, 0), head_rot=(-4, 18, 2), G=(-0.28, 0.06, 0.98), D=(-0.32, 0.62, 0.72), F=(0.0, -0.55, 0.84),
                   face="focused", pocket=0.008))
AIM_B = finalize(K(pelvis_off=(-0.005, 0.02, -0.08), pelvis_rot=(2, -12, -2), spine_rot=(4, -10, -2), chest_rot=(4, -12, 0),
                   neck_rot=(2, 12, 0), head_rot=(4, 16, 2), G=(-0.29, 0.04, 0.94), D=(-0.40, 0.58, 0.71), F=(0.05, -0.62, 0.78),
                   face="focused", pocket=0.008))
AIM_S = finalize(K(pelvis_off=(-0.02, 0.03, -0.09), pelvis_rot=(3, -22, -4), spine_rot=(4, -16, -6), chest_rot=(2, -16, -4),
                   neck_rot=(-2, 18, 4), head_rot=(-4, 24, 6), G=(-0.32, 0.06, 0.74), D=(-0.86, 0.42, 0.30), F=(0.1, -0.30, 0.95),
                   face="determined", pocket=0.008))

def keys_fn(keys):
    ks = prep_keys(keys)
    return lambda t: sample_keys(ks, t)

REL_O = [
    (0, K(face="focused"), "io"),
    (3, K(pelvis_off=(0, -0.01, -0.05), spine_rot=(9, -4, 0), chest_rot=(7, -4, 0), G=(-0.23, -0.27, 0.86), D=(-0.55, 0.0, 0.83),
          face="focused"), "io"),
    (9, K(pelvis_off=(-0.01, 0.03, -0.07), pelvis_rot=(-2, -18, -3), spine_rot=(-2, -14, -3), chest_rot=(-4, -16, 0),
          neck_rot=(-2, 14, 0), head_rot=(-4, 22, 2), G=(-0.29, 0.10, 1.02), D=(-0.30, 0.70, 0.65), F=(0.0, -0.55, 0.84),
          face="strain", pocket=0.012), "io"),
    (11, K(pelvis_off=(-0.012, 0.035, -0.078), pelvis_rot=(-2, -20, -3), spine_rot=(-3, -15, -3), chest_rot=(-5, -18, 0),
           neck_rot=(-2, 16, 0), head_rot=(-4, 24, 2), G=(-0.31, 0.13, 1.03), D=(-0.30, 0.74, 0.60), F=(0.0, -0.55, 0.84),
           face="strain", pocket=0.014), "io"),
    (14, K(pelvis_off=(0.005, -0.03, -0.035), pelvis_rot=(2, 8, 2), spine_rot=(5, 8, 2), chest_rot=(6, 10, 0), neck_rot=(-6, -10, 0),
           head_rot=(-6, -12, 0), G=(-0.33, -0.20, 1.10), D=(-0.25, -0.45, 0.86), F=(0.0, -0.85, -0.45), face="determined",
           pocket=-0.010), "in"),
    (18, K(pelvis_off=(0.01, -0.05, -0.085), pelvis_rot=(5, 14, 3), spine_rot=(8, 12, 3), chest_rot=(6, 14, 0), neck_rot=(-6, -14, 0),
           head_rot=(-8, -18, 0), G=(0.02, -0.37, 0.66), D=(0.65, -0.35, -0.67), F=None, face="determined", pocket=0.004), "out"),
    (23, K(pelvis_off=(0.005, -0.035, -0.06), pelvis_rot=(3, 9, 2), spine_rot=(6, 7, 2), chest_rot=(5, 8, 0), neck_rot=(-5, -10, 0),
           head_rot=(-6, -12, 0), G=(-0.01, -0.38, 0.68), D=(0.55, -0.40, -0.73), F=None, face="smile"), "io"),
    (28, K(pelvis_off=(0.0, -0.015, -0.045), pelvis_rot=(1, 0, 1), spine_rot=(6, -1, 1), chest_rot=(4, -2, 0), neck_rot=(-4, 0, 0),
           head_rot=(-6, 2, 0), G=(-0.18, -0.32, 0.86), D=(-0.10, -0.75, 0.65), F=(0.55, -0.55, -0.6), face="smile"), "io"),
    (33, K(), "io"),
]
CEL_F = (0.3, -0.95, 0.0)
CEL = [
    (0, K(), "io"),
    (5, K(pelvis_off=(0, -0.01, -0.10), pelvis_rot=(4, -10, 0), spine_rot=(10, -4, 0), chest_rot=(8, -4, 0), neck_rot=(-6, 6, 0),
          head_rot=(-8, 10, 0), G=(-0.22, -0.30, 0.74), D=(-0.75, 0.0, 0.66), face="smile"), "io"),
    (9, K(pelvis_off=(0, 0, 0.14), pelvis_rot=(-4, -6, -2), spine_rot=(-6, -4, -2), chest_rot=(-8, -4, 0), neck_rot=(-6, 6, 0),
          head_rot=(-14, 8, 0), G=(-0.30, -0.10, 1.14), D=(-0.35, 0.05, 0.94), F=CEL_F, face="big_smile"), "in"),
    (12, K(pelvis_off=(0, 0, 0.18), pelvis_rot=(-4, -6, -5), spine_rot=(-6, -4, -4), chest_rot=(-8, -4, -2), neck_rot=(-6, 6, 0),
           head_rot=(-16, 8, 4), G=(-0.30, -0.08, 1.18), D=(-0.25, 0.05, 0.97), F=CEL_F, face="big_smile"), "out"),
    (16, K(pelvis_off=(0, 0, -0.01), pelvis_rot=(0, -6, -2), spine_rot=(-2, -4, -1), chest_rot=(-4, -4, 0), neck_rot=(-5, 6, 0),
           head_rot=(-10, 8, 2), G=(-0.30, -0.12, 1.08), D=(-0.35, 0.05, 0.94), F=CEL_F, face="big_smile"), "in"),
    (19, K(pelvis_off=(0, -0.01, -0.10), pelvis_rot=(5, -8, 0), spine_rot=(10, -4, 0), chest_rot=(6, -4, 0), neck_rot=(-4, 6, 0),
           head_rot=(-6, 8, 0), G=(-0.30, -0.16, 0.98), D=(-0.40, 0.0, 0.92), F=CEL_F, face="big_smile"), "out"),
    (23, K(pelvis_off=(0, 0, -0.025), pelvis_rot=(-2, -8, -4), spine_rot=(-4, -4, -3), chest_rot=(-8, -4, 0), neck_rot=(-6, 6, 0),
           head_rot=(-12, 8, 3), G=(-0.30, -0.10, 1.14), D=(-0.25, 0.05, 0.97), F=CEL_F, face="big_smile"), "io"),
    (26, K(pelvis_off=(0, 0, -0.05), pelvis_rot=(0, -8, -2), spine_rot=(2, -4, -1), chest_rot=(-3, -4, 0), neck_rot=(-5, 6, 0),
           head_rot=(-9, 8, 2), G=(-0.30, -0.14, 1.04), D=(-0.35, 0.0, 0.94), F=CEL_F, face="big_smile"), "io"),
    (29, K(pelvis_off=(0, 0, -0.03), pelvis_rot=(-2, -8, -3), spine_rot=(-3, -4, -2), chest_rot=(-7, -4, 0), neck_rot=(-6, 6, 0),
           head_rot=(-11, 8, 3), G=(-0.30, -0.10, 1.12), D=(-0.28, 0.05, 0.96), F=CEL_F, face="smile"), "io"),
    (36, K(face="smile"), "io"),
]
REL_B = [
    (0, AIM_B, "io"),
    (4, K(pelvis_off=(-0.012, 0.035, -0.09), pelvis_rot=(0, -20, -3), spine_rot=(0, -15, -3), chest_rot=(-2, -18, 0), neck_rot=(0, 16, 0),
          head_rot=(2, 22, 2), G=(-0.30, 0.12, 1.0), D=(-0.30, 0.72, 0.62), F=(0, -0.55, 0.84), face="strain", pocket=0.012), "io"),
    (10, K(pelvis_off=(-0.014, 0.04, -0.095), pelvis_rot=(0, -22, -3), spine_rot=(0, -16, -3), chest_rot=(-2, -20, 0), neck_rot=(0, 18, 0),
           head_rot=(2, 24, 2), G=(-0.32, 0.14, 1.01), D=(-0.30, 0.75, 0.59), F=(0, -0.55, 0.84), face="strain", pocket=0.014), "io"),
    (14, K(pelvis_off=(0.005, -0.035, -0.06), pelvis_rot=(6, 8, 2), spine_rot=(10, 8, 2), chest_rot=(10, 10, 0), neck_rot=(0, -10, 0),
           head_rot=(6, -12, 0), G=(-0.33, -0.24, 0.98), D=(-0.22, -0.62, 0.75), F=(0, -0.6, -0.8), face="determined", pocket=-0.010), "in"),
    (18, K(pelvis_off=(0.01, -0.06, -0.10), pelvis_rot=(10, 14, 3), spine_rot=(14, 12, 3), chest_rot=(10, 14, 0), neck_rot=(-2, -14, 0),
           head_rot=(2, -16, 0), G=(0.03, -0.38, 0.58), D=(0.55, -0.50, -0.67), F=None, pocket=0.004), "out"),
    (24, K(pelvis_off=(0.005, -0.04, -0.07), pelvis_rot=(6, 9, 2), spine_rot=(9, 7, 2), chest_rot=(6, 8, 0), head_rot=(-2, -10, 0),
           G=(-0.02, -0.38, 0.62), D=(0.50, -0.45, -0.74), F=None, face="smile"), "io"),
    (29, K(pelvis_off=(0.0, -0.015, -0.045), G=(-0.18, -0.32, 0.84), D=(-0.10, -0.75, 0.65), F=(0.55, -0.55, -0.6), face="smile"), "io"),
    (33, K(), "io"),
]
REL_S = [
    (0, AIM_S, "io"),
    (4, K(pelvis_off=(-0.025, 0.04, -0.10), pelvis_rot=(3, -30, -5), spine_rot=(4, -22, -6), chest_rot=(2, -22, -4), neck_rot=(-2, 24, 4),
          head_rot=(-4, 30, 6), G=(-0.32, 0.14, 0.74), D=(-0.80, 0.55, 0.25), F=(0.15, -0.25, 0.95), face="strain", pocket=0.012), "io"),
    (9, K(pelvis_off=(-0.01, 0.0, -0.10), pelvis_rot=(3, -8, -3), spine_rot=(4, -6, -4), chest_rot=(2, -6, -2), neck_rot=(-2, 8, 2),
          head_rot=(-4, 12, 4), G=(-0.32, -0.10, 0.76), D=(-0.95, 0.15, 0.25), F=(0.2, -0.95, 0.1), face="strain", pocket=0.014), "in"),
    (13, K(pelvis_off=(0.01, -0.03, -0.09), pelvis_rot=(2, 10, 0), spine_rot=(3, 10, 0), chest_rot=(2, 12, 0), neck_rot=(-2, -10, 0),
           head_rot=(-4, -12, 0), G=(-0.22, -0.30, 0.78), D=(-0.70, -0.62, 0.30), F=(0.62, -0.72, 0.1), face="determined", pocket=-0.010), "in"),
    (18, K(pelvis_off=(0.02, -0.04, -0.08), pelvis_rot=(2, 22, 2), spine_rot=(3, 18, 2), chest_rot=(2, 20, 0), neck_rot=(-2, -18, 0),
           head_rot=(-4, -18, 0), G=(0.10, -0.33, 0.80), D=(0.80, -0.50, 0.30), F=None, pocket=0.004), "out"),
    (24, K(pelvis_off=(0.012, -0.03, -0.07), pelvis_rot=(2, 14, 1), spine_rot=(4, 12, 1), chest_rot=(3, 12, 0), head_rot=(-4, -10, 0),
           G=(0.04, -0.34, 0.80), D=(0.70, -0.60, 0.36), F=None, face="smile"), "io"),
    (29, K(pelvis_off=(0.0, -0.015, -0.045), G=(-0.18, -0.32, 0.84), D=(-0.30, -0.60, 0.74), F=(0.55, -0.55, -0.6), face="smile"), "io"),
    (33, K(), "io"),
]
QS = K(pelvis_off=(0, -0.01, -0.05), pelvis_rot=(2, -4, 0), spine_rot=(4, -2, 0), chest_rot=(2, -2, 0), neck_rot=(-4, 4, 0),
       head_rot=(-8, 4, 0), G=(-0.26, -0.32, 1.04), D=(-0.22, -0.30, 0.93), F=(0.05, -0.95, 0.28), face="focused", pocket=0.004)
QS_READY = P(QS, pocket=0.006)
QSC = [
    (0, K(), "io"),
    (4, QS, "out"),
    (6, P(QS, G=(-0.26, -0.34, 1.05), pocket=0.008), "out"),                                          # CONTACT
    (9, P(QS, G=(-0.26, -0.26, 1.00), D=(-0.22, -0.15, 0.96), F=None, pocket=0.018, face="strain"), "out"),   # give + compression
    (13, P(QS, G=(-0.26, -0.30, 1.03), D=(-0.22, -0.26, 0.94), F=None, pocket=0.004), "io"),
    (18, QS_READY, "io"),
]
QSR = [
    (0, QS_READY, "io"),
    (3, P(QS, G=(-0.26, -0.28, 1.03), D=(-0.22, -0.20, 0.95), F=None, pocket=0.010, face="determined"), "io"),
    (5, P(QS, G=(-0.26, -0.36, 1.02), D=(-0.20, -0.72, 0.66), F=(0, -0.55, -0.83), pocket=-0.010, face="determined"), "in"),  # RELEASE
    (9, P(QS, G=(-0.22, -0.38, 0.92), D=(-0.05, -0.95, 0.30), F=None, pocket=0.0, face="smile"), "out"),
    (16, K(face="smile"), "io"),
]
def dodge(sign):
    """Split dodge in place (root stays put; runtime translates the root ~0.6 m between local frames 6 and 16).
    sign +1 = shooter's left (+X in Blender, -X in game), -1 = shooter's right."""
    sx = sign
    carry = dict(G=(0.02, -0.30, 0.92), D=(0.15, -0.10, 0.98), F=(0.1, -0.99, 0)) if sign > 0 else \
            dict(G=(-0.36, -0.22, 0.94), D=(-0.55, -0.10, 0.83), F=(0.4, -0.9, 0.1))
    return [
        (0, K(), "io"),
        (4, K(pelvis_off=(-0.06 * sx, 0, -0.09), pelvis_rot=(4, -10 * sx, 6 * sx), spine_rot=(6, -4 * sx, 4 * sx), chest_rot=(4, -6 * sx, 2 * sx),
              head_rot=(-6, 4 * sx, -4 * sx), footL=(-0.02 * sx if sx < 0 else 0, 0, 0), footR=(-0.06 * sx if sx > 0 else 0.0, 0.0, 0),
              G=(-0.26, -0.20, 0.84), D=(-0.62, 0.05, 0.78), face="determined"), "io"),
        (9, K(pelvis_off=(0.10 * sx, -0.04, -0.06), pelvis_rot=(2, 12 * sx, -8 * sx), spine_rot=(4, 10 * sx, -6 * sx), chest_rot=(2, 14 * sx, -4 * sx),
              neck_rot=(-2, -8 * sx, 0), head_rot=(-6, -8 * sx, 6 * sx), footL=(0.14 * sx, -0.04, 0.05) if sx > 0 else (-0.02, 0.0, 0.0),
              footR=(0.02 * sx, 0.02, 0) if sx > 0 else (-0.14, -0.04, 0.05), face="determined", **carry), "out"),
        (14, K(pelvis_off=(0.12 * sx, -0.04, -0.10), pelvis_rot=(4, 10 * sx, -4 * sx), spine_rot=(6, 8 * sx, -3 * sx), chest_rot=(4, 10 * sx, -2 * sx),
               head_rot=(-6, -6 * sx, 3 * sx), footL=(0.16 * sx, -0.05, 0) if sx > 0 else (-0.08, 0.0, 0), footR=(0.08 * sx, 0.0, 0) if sx > 0 else (-0.16, -0.05, 0),
               face="determined", **carry), "io"),
        (19, K(pelvis_off=(0.04 * sx, -0.02, -0.06), pelvis_rot=(2, 3 * sx, -1 * sx), footL=(0.04 * sx, -0.02, 0) if sx > 0 else (-0.02, 0, 0),
               footR=(0.02 * sx, 0, 0) if sx > 0 else (-0.04, -0.02, 0), G=(-0.20, -0.26, 0.88), D=(-0.45, 0.0, 0.89), F=(0.5, -0.86, 0.1),
               face="smirk"), "io"),
        (24, K(face="smile"), "io"),
    ]
SLUMP = K(pelvis_off=(0, 0.01, -0.06), pelvis_rot=(4, -4, 0), spine_rot=(7, -2, 0), chest_rot=(6, -2, 0), neck_rot=(5, 0, 0),
          head_rot=(9, 4, 0), G=(-0.20, -0.22, 0.79), D=(-0.35, -0.25, -0.90), F=(0.3, -0.9, 0.3), face="disappointed", eye=(0, -8))
DISAP = [
    (0, K(), "io"), (10, SLUMP, "io"),
    (20, P(SLUMP, pelvis_off=(0, 0.01, -0.04), chest_rot=(6, -2, 0), head_rot=(6, 4, 0), G=(-0.20, -0.22, 0.76)), "io"),
    (30, P(SLUMP, head_rot=(11, -4, 0)), "io"), (40, P(SLUMP, head_rot=(10, 2, 0)), "io"),
]
NEAR = [
    (0, K(), "io"),
    (5, K(pelvis_off=(0, 0.02, -0.03), chest_rot=(-10, -2, 0), neck_rot=(-8, 0, 0), head_rot=(-16, 6, 0), G=(-0.28, -0.14, 1.08),
          D=(-0.30, 0.25, 0.92), F=(0.4, -0.9, 0.1), face="surprise"), "out"),
    (12, K(pelvis_off=(0, 0.02, -0.035), chest_rot=(-8, -2, 0), neck_rot=(-8, 0, 0), head_rot=(-14, 4, 0), G=(-0.28, -0.15, 1.07),
           D=(-0.30, 0.22, 0.93), F=(0.4, -0.9, 0.1), face="surprise"), "io"),
    (20, P(SLUMP, G=(-0.22, -0.24, 0.80), D=(-0.5, -0.2, -0.84)), "io"),
    (30, K(), "io"),
]
PIPE = [
    (0, K(), "io"),
    (3, K(pelvis_off=(0, 0.0, -0.07), chest_rot=(8, -4, 0), head_rot=(6, 4, -6), face="strain", eye=(0, 4)), "out"),
    (8, K(pelvis_off=(0, 0.0, -0.065), chest_rot=(7, -4, 0), head_rot=(4, 10, -4), face="strain"), "io"),
    (14, K(pelvis_off=(0, 0.0, -0.05), head_rot=(0, 16, 0), face="surprise"), "io"),
    (18, K(head_rot=(0, -6, 0), face="disappointed"), "io"),
    (24, K(), "io"),
]
SAVE = [
    (0, K(), "io"), (6, P(SLUMP, head_rot=(6, 4, 0), G=(-0.21, -0.24, 0.80), D=(-0.5, -0.1, -0.86)), "io"),
    (10, P(SLUMP, head_rot=(6, 16, 0), G=(-0.21, -0.24, 0.80), D=(-0.5, -0.1, -0.86)), "io"),
    (16, P(SLUMP, head_rot=(6, -12, 0), G=(-0.21, -0.24, 0.80), D=(-0.5, -0.1, -0.86)), "io"),
    (22, P(SLUMP, head_rot=(6, 8, 0), G=(-0.21, -0.24, 0.80), D=(-0.5, -0.1, -0.86)), "io"),
    (30, K(), "io"),
]
def run_pose(t, N=20):
    ph = 2 * math.pi * t / N; c = math.cos(ph); s = math.sin(ph)
    p = K(pelvis_off=(0, -0.02, -0.05 + 0.015 * math.cos(2 * ph)), pelvis_rot=(6, 6 * c, 0), spine_rot=(12, -3, 0), chest_rot=(6, -6 * c, 0),
          head_rot=(-12, 4, 0), footL=(0, -0.16 * c, 0.07 * max(0.0, s)), footR=(0, 0.16 * c, 0.07 * max(0.0, -s)), face="determined",
          pocket=0.008 + 0.004 * math.sin(2 * ph))
    p.update(looped_stick(6 * s, 20 * s, (0.0, -0.02, 0.06)))
    return finalize(p)

CLIPS = [
    Clip("idle", 0, 48, True, idle_pose, blinks=(30,), notes="breathing/look loop; blink at local 30"),
    Clip("cradle", 60, 28, True, cradle_pose, notes="continuous cradle; pocket lags the sweep"),
    Clip("release_overhand", 100, 33, False, keys_fn(REL_O), release=14, notes="graybox timing preserved: ball leaves pocket_socket at 14/30 s"),
    Clip("celebrate", 150, 36, False, keys_fn(CEL), notes="jump with stick skyward (pelvis motion only)"),
    Clip("aim_overhand", 200, 30, True, aim_loop(AIM_O), notes="loaded overhand hold for aiming; blends into release_overhand"),
    Clip("aim_bounce", 240, 30, True, aim_loop(AIM_B), blinks=(20,), notes="bounce-shot aim; first frame of release_bounce"),
    Clip("aim_sidearm", 280, 30, True, aim_loop(AIM_S), notes="sidearm aim; first frame of release_sidearm"),
    Clip("split_dodge_left", 320, 24, False, keys_fn(dodge(+1)), notes="in place; runtime moves root toward shooter-left (game -X) between local 6 and 16"),
    Clip("split_dodge_right", 350, 24, False, keys_fn(dodge(-1)), notes="in place; runtime moves root toward shooter-right (game +X) between local 6 and 16"),
    Clip("release_bounce", 380, 33, False, keys_fn(REL_B), release=14, notes="starts from aim_bounce; downward release"),
    Clip("release_sidearm", 420, 33, False, keys_fn(REL_S), release=13, notes="starts from aim_sidearm; horizontal whip"),
    Clip("quick_stick_catch", 460, 18, False, keys_fn(QSC), contact=6, notes="ball meets pocket at local 6; ends in quick-stick ready pose"),
    Clip("quick_stick_release", 490, 16, False, keys_fn(QSR), release=5, notes="starts from quick-stick ready pose; redirect release at local 5"),
    Clip("disappointed", 520, 40, False, keys_fn(DISAP), notes="ends slumped (stick head resting on turf); blend to idle"),
    Clip("near_miss_reaction", 570, 30, False, keys_fn(NEAR), notes="extra"),
    Clip("pipe_reaction", 610, 24, False, keys_fn(PIPE), notes="extra"),
    Clip("save_reaction", 645, 30, False, keys_fn(SAVE), notes="extra"),
    Clip("run_loop", 685, 20, True, run_pose, notes="extra; in place"),
]

def build_girl(export=True):
    reset_scene("LaxAttack_GirlField")
    C = coll("lax_shooter")
    arm = build_skeleton(GIRL_FIELD, C, "lax_shooter_rig")
    parts = build_character(GIRL_FIELD, C, arm)
    stick, meta = build_stick("attack", C, arm, name="lax_shooter_stick", frame_mat="helmet_cream", pocket_mat="cord_navy")
    socks = add_character_sockets(GIRL_FIELD, arm, C, meta)
    ad = arm.data; ad.pose_position = "REST"; bpy.context.view_layer.update()
    Ms = ad.bones["stick"].matrix_local.copy()
    socks["ball_contact_socket"] = add_socket("ball_contact_socket", arm, "pocket_01", Ms @ Matrix.Translation(meta["ball_contact"]), C, 0.03)
    ad.pose_position = "POSE"
    meshes = atlas_character(arm, list(parts.values()) + [stick], "lax_shooter", GF_DIR) if "atlas_character" in globals() else list(parts.values()) + [stick]
    cal = [GB, AIM_O, AIM_S, prep_keys(REL_O)[4][1], prep_keys(CEL)[3][1], QS]
    poles = calibrate_poles(arm, cal, "field")
    bake_clips(arm, CLIPS, "field")
    rep = {"poles": poles, "validation": validate_character(arm, CLIPS, meshes, meta, REQUIRED_SOCKETS, REQUIRED_CLIPS)}
    os.makedirs(GF_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(GF_DIR, "LaxAttack_GirlField.blend"), compress=True)
    man = manifest("lax_shooter", CLIPS, body_scale=GIRL_FIELD.get("body_scale", 1.0), extra={
        "required_sockets": REQUIRED_SOCKETS, "extra_sockets": ["ball_contact_socket"],
        "legacy_ranges_unchanged": {"idle": [0, 48], "cradle": [60, 88], "release_overhand": [100, 133], "celebrate": [150, 186]},
        "ball_visual_radius_recommended_m": BALL_R, "stick_axes_blender": "shaft +Y, pocket open face +Z, origin = top-hand grip"})
    if export:
        objs = [arm] + meshes + list(socks.values())
        rep["export"] = export_asset(objs, "lax_shooter", "lax_shooter_rig", os.path.join(EXP, "lax_shooter.usdz"), 30, CLIPS[-1].end,
                                     False, man, REQUIRED_SOCKETS + ["ball_contact_socket"])
        rep["lods"] = export_lods(rep["export"], "lax_shooter", "lax_shooter_rig", os.path.join(EXP, "lax_shooter.usdz"), (0.6, 0.3), 30, CLIPS[-1].end, man)
        with open(os.path.join(EXP, "lax_shooter_clips.json"), "w") as fh:
            json.dump(man, fh, indent=2)
    return rep, arm, meta
