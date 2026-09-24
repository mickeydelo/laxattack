# Lax Attack animation library expansion (appended after the legacy ranges; charm-first, procedural where it saves effort).
def _steps(sched, t, blend=2.0):
    """Piecewise-constant values with quick blends (eye darts, glances)."""
    v = sched[0][1]
    for f0, val in sched:
        if t >= f0:
            prev = v; v = val; u = min(1.0, (t - f0) / blend)
            v = tuple(a + (b - a) * u for a, b in zip(prev, val)) if u < 1 else val
    return v

def _dyn(base, fn):
    return lambda t: finalize(P(base, **fn(t)))

def _roll_stick(D, F, deg):
    return tuple(Matrix.Rotation(math.radians(deg), 3, V(D).normalized()) @ V(orth(F, D)))

# ---------------- shooter
def idle_variant(N, bob, bobc, sway, look, stick_dz, face, darts, fidget, blinks):
    def fn(t):
        ph = 2 * math.pi * t / N; b = 0.5 - 0.5 * math.cos(bobc * ph)
        G = tuple(V(GB["G"]) + V((0.006 * math.sin(ph), 0, stick_dz - 0.006 * b)))
        return dict(pelvis_off=(sway * math.sin(ph), 0, -0.035 - bob * b), spine_rot=(6 + 1.5 * b, -4, 0),
                    chest_rot=(4 + 2 * b, -4 + 2 * math.sin(ph), 0), head_rot=(-6 + 2 * math.sin(2 * ph), 8 + look * math.sin(ph), 3 * math.sin(ph)),
                    G=G, F=_roll_stick(GB["D"], GB["F"], fidget * math.sin(3 * ph)), face=face, eye=_steps(darts, t), pocket=0.004 + 0.003 * b)
    return fn

def roll_dodge(sign):
    """In-place roll dodge: plant, drop the shoulder, full pivot (feet follow), burst out. sign +1 = toward shooter-left."""
    def fn(t):
        u = t / 30.0; turn = -360.0 * sign * (u * u * (3 - 2 * u)) if 0.15 < u < 0.85 else (0.0 if u <= 0.15 else -360.0 * sign)
        if 0.15 < u < 0.85:
            w = (u - 0.15) / 0.7; turn = -360.0 * sign * (w * w * (3 - 2 * w))
        dip = math.sin(math.pi * min(1.0, u / 0.85)) * 0.07
        return dict(pelvis_off=(0.05 * sign * math.sin(math.pi * u), -0.02, -0.04 - dip), pelvis_rot=(8 * math.sin(math.pi * u), turn * 0.34, 0),
                    spine_rot=(10 * math.sin(math.pi * u), turn * 0.33, 0), chest_rot=(6, turn * 0.33, 0), head_rot=(-8, 0, 0), feet_yaw=turn,
                    G=(-0.10 if sign > 0 else -0.25, -0.12, 0.94), D=(0.0, 0.25, 0.97), F=(0.2, -0.98, 0), face="determined", pocket=0.012)
    return fn

def face_dodge(sign):
    across = dict(G=(0.02, -0.34, 1.02), D=(0.25, -0.2, 0.95), F=(0.2, -0.98, 0)) if sign > 0 else dict(G=(-0.40, -0.30, 1.0), D=(-0.6, -0.1, 0.8), F=(0.5, -0.86, 0))
    duck = K(pelvis_off=(0.03 * sign, -0.02, -0.09), pelvis_rot=(6, 8 * sign, -4 * sign), chest_rot=(8, 10 * sign, 0), head_rot=(4, -6 * sign, 6 * sign),
             face="determined", pocket=0.012, **across)
    return [(0, K(), "io"), (5, duck, "out"), (11, P(duck, pelvis_off=(0.05 * sign, -0.03, -0.08)), "io"), (18, K(face="smirk"), "io"), (24, K(face="smile"), "io")]

def twirl(t, N=40, spins=2.0):
    u = t / N; ang = 360 * spins * min(1.0, max(0.0, (u - 0.15) / 0.6)) ** 0.8
    up = dict(G=(-0.28, -0.14, 1.10), D=(-0.2, 0.05, 0.98))
    b = math.sin(math.pi * u)
    return dict(pelvis_off=(0, 0, -0.03 + 0.05 * b), chest_rot=(-6 * b, -4, 0), head_rot=(-12 * b, 8, 0), F=_roll_stick(up["D"], (0.3, -0.95, 0), ang),
                face="big_smile" if 0.1 < u < 0.9 else "smile", **up)

JUMP = lambda z, **kw: K(pelvis_off=(0, 0, z), face="big_smile", **kw)
SHOOTER_LIB = [
    Clip("idle_relaxed", 720, 72, True, _dyn(GB, idle_variant(72, 0.008, 1, 0.004, 12, -0.03, "smile", [(0, (0, 0)), (14, (10, 2)), (30, (-8, 0)), (50, (4, -4)), (64, (0, 0))], 4, ())),
         blinks=(22, 57), notes="loose, happy look-around"),
    Clip("idle_competitive", 800, 48, True, _dyn(GB, idle_variant(48, 0.02, 2, 0.006, 3, 0.03, "determined", [(0, (0, 0)), (20, (3, 0)), (34, (0, 0))], 8, ())),
         blinks=(30,), notes="toe bounce, eyes locked on goal"),
    Clip("idle_nervous", 860, 60, True, _dyn(GB, idle_variant(60, 0.01, 2, 0.02, 6, 0.0, "focused", [(0, (0, 0)), (8, (9, 3)), (16, (-9, 2)), (26, (6, -2)), (38, (-5, 3)), (50, (0, 0))], 18, ())),
         blinks=(12, 33, 47), notes="weight shifts, darting eyes, stick fidget"),
    Clip("roll_dodge_left", 930, 30, False, _dyn(GB, roll_dodge(+1)), notes="in place; 360 pivot with planted-foot turn; root may slide toward shooter-left"),
    Clip("roll_dodge_right", 970, 30, False, _dyn(GB, roll_dodge(-1)), notes="in place; mirror"),
    Clip("face_dodge_left", 1010, 24, False, keys_fn(face_dodge(+1)), notes="stick swept across the face to shooter-left and back"),
    Clip("face_dodge_right", 1045, 24, False, keys_fn(face_dodge(-1)), notes="mirror"),
    Clip("celebrate_fist_pump", 1080, 30, False, keys_fn([(0, K(), "io"), (6, K(pelvis_off=(0, 0, -0.08), chest_rot=(10, 0, 0), face="smile"), "out"),
         (10, K(pelvis_off=(0, 0, -0.02), chest_rot=(-8, -10, 0), head_rot=(-14, 10, 0), G=(-0.30, -0.18, 1.10), D=(-0.3, 0.1, 0.95), face="big_smile"), "in"),
         (14, K(pelvis_off=(0, 0, -0.07), chest_rot=(6, -6, 0), G=(-0.26, -0.24, 0.86), face="big_smile"), "out"),
         (18, K(pelvis_off=(0, 0, -0.02), chest_rot=(-8, -10, 0), G=(-0.30, -0.18, 1.10), D=(-0.3, 0.1, 0.95), face="big_smile"), "in"), (30, K(face="smile"), "io")]),
         notes="double pump; short"),
    Clip("celebrate_stick_twirl", 1120, 40, False, _dyn(GB, twirl), notes="two stick twirls overhead"),
    Clip("celebrate_jump_tuck", 1170, 30, False, keys_fn([(0, K(), "io"), (6, JUMP(-0.10, chest_rot=(10, 0, 0)), "out"), (11, JUMP(0.18, footL=(0, 0.04, 0.08), footR=(0, 0.04, 0.08), G=(-0.3, -0.12, 1.14), D=(-0.3, 0.05, 0.95)), "out"),
         (15, JUMP(0.14, footL=(0, 0.02, 0.05), footR=(0, 0.02, 0.05), G=(-0.3, -0.12, 1.14), D=(-0.3, 0.05, 0.95)), "in"), (19, JUMP(-0.09, chest_rot=(8, 0, 0)), "out"), (30, K(face="smile"), "io")]),
         notes="big tuck jump (pelvis motion only)"),
    Clip("celebrate_knee_slide", 1210, 40, False, keys_fn([(0, K(), "io"), (6, K(pelvis_off=(0, -0.04, -0.12), chest_rot=(12, 0, 0), face="big_smile"), "in"),
         (14, K(pelvis_off=(0, 0.02, -0.26), pelvis_rot=(-14, 0, 0), spine_rot=(-10, 0, 0), chest_rot=(-10, 0, 0), head_rot=(-16, 0, 0), footL=(0, 0.10, 0), footR=(0, 0.14, 0),
               G=(-0.24, -0.06, 1.02), D=(-0.2, 0.2, 0.96), face="big_smile"), "out"),
         (28, K(pelvis_off=(0, 0.02, -0.25), pelvis_rot=(-12, 0, 0), spine_rot=(-8, 0, 0), chest_rot=(-8, 0, 0), head_rot=(-14, 0, 0), footL=(0, 0.10, 0), footR=(0, 0.14, 0),
               G=(-0.24, -0.06, 1.02), D=(-0.2, 0.2, 0.96), face="big_smile"), "io"), (40, K(face="smile"), "io")]),
         notes="in-place knee drop + lean back, stick skyward; runtime may add a short forward slide"),
    Clip("celebrate_point", 1260, 24, False, keys_fn([(0, K(), "io"), (6, K(pelvis_rot=(0, 16, 0), chest_rot=(0, 14, 0), head_rot=(-6, 14, 0), G=(0.05, -0.32, 0.98), D=(0.95, -0.2, 0.2), F=(0, -0.3, 0.95), face="big_smile", eye=(-10, 0)), "out"),
         (16, K(pelvis_rot=(0, 16, 0), chest_rot=(0, 14, 0), head_rot=(-8, 16, 0), G=(0.06, -0.33, 0.99), D=(0.95, -0.2, 0.2), F=(0, -0.3, 0.95), face="smirk", eye=(-10, 0)), "io"), (24, K(face="smile"), "io")]),
         notes="stick points to a teammate (toward shooter-left)"),
    Clip("celebrate_restrained", 1295, 30, False, keys_fn([(0, K(), "io"), (8, K(head_rot=(4, 8, 0), face="smile"), "io"), (14, K(head_rot=(-8, 8, 0), face="smile"), "io"),
         (20, K(G=(-0.26, -0.28, 0.80), face="smirk"), "io"), (30, K(face="smile"), "io")]), notes="cool nod and smile"),
    Clip("celebrate_clutch", 1335, 54, False, lambda t: (keys_fn(CEL)(t) if t <= 30 else _dyn(GB, twirl)(t - 14)) if t < 50 else K(face="smile"),
         notes="huge win: jump celebration flowing into a stick twirl"),
    Clip("weak_miss", 1400, 24, False, keys_fn([(0, K(), "io"), (6, K(pelvis_off=(0, 0, -0.05), chest_rot=(6, 0, 0), head_rot=(8, 6, 8), face="disappointed"), "out"),
         (12, K(pelvis_off=(0, 0, -0.03), chest_rot=(2, 0, 0), head_rot=(2, 6, -6), G=(-0.25, -0.26, 0.86), face="disappointed"), "io"), (24, K(), "io")]),
         notes="little shoulder shrug, never a tantrum"),
    Clip("goal_glance_back", 1435, 30, False, keys_fn([(0, K(), "io"), (8, K(pelvis_rot=(0, -10, 0), chest_rot=(0, -20, 0), neck_rot=(0, -20, 0), head_rot=(-8, -30, 0), eye=(-12, 0), face="big_smile"), "out"),
         (20, K(pelvis_rot=(0, -8, 0), chest_rot=(0, -16, 0), neck_rot=(0, -16, 0), head_rot=(-6, -26, 0), eye=(-12, 0), face="smirk"), "io"), (30, K(face="smile"), "io")]),
         notes="grin back over the shoulder"),
    Clip("run_start", 1475, 16, False, lambda t: finalize(lerp_pose(K(), run_pose(t * 20.0 / 16.0), min(1.0, t / 8.0))), notes="blend into run_loop"),
    Clip("run_stop", 1500, 18, False, keys_fn([(0, run_pose(0), "io"), (6, K(pelvis_off=(0, 0.03, -0.09), pelvis_rot=(-6, 0, 0), footL=(0, -0.10, 0), face="determined"), "out"),
         (11, K(pelvis_off=(0, 0.0, -0.05), pelvis_rot=(4, 0, 0)), "io"), (18, K(), "io")]), notes="plant and settle"),
    Clip("stumble_recover", 1528, 30, False, keys_fn([(0, K(), "io"), (4, K(pelvis_off=(0, -0.05, -0.08), pelvis_rot=(16, 0, 6), chest_rot=(12, 0, 0), footR=(0, -0.12, 0.05), face="surprise"), "out"),
         (10, K(pelvis_off=(0.02, -0.04, -0.11), pelvis_rot=(10, 0, -6), footR=(0.0, -0.14, 0), footL=(0, 0.04, 0.04), G=(-0.34, -0.26, 0.92), face="strain"), "io"),
         (18, K(pelvis_off=(0, -0.01, -0.06), face="smile"), "io"), (30, K(face="smile"), "io")]), notes="trip, windmill, laugh it off"),
]

# ---------------- goalie
def gk_dyn(fn):
    return lambda t: finalize(P(GK, **fn(t)))
GOALIE_LIB = [
    Clip("goalie_scan", 570, 48, True, gk_dyn(lambda t: dict(head_rot=(-8, 24 * math.sin(2 * math.pi * t / 48), 0), eye=(18 * math.sin(2 * math.pi * t / 48 + 0.4), 0),
         pelvis_off=(0, 0, -0.085 - 0.01 * abs(math.sin(2 * math.pi * t / 24)))) ), blinks=(18,), notes="watchful sweep"),
    Clip("goalie_tap_pipes", 628, 40, False, keys_fn([(0, GK, "io"), (8, Q(G=(-0.42, -0.14, 0.94), D=(-0.6, 0.3, 0.74), pelvis_rot=(8, 14, 0), head_rot=(-6, 18, 0)), "in"),
         (11, Q(G=(-0.44, -0.12, 0.92), D=(-0.62, 0.34, 0.70), pelvis_rot=(8, 14, 0), head_rot=(-6, 18, 0)), "out"),
         (22, Q(G=(0.04, -0.16, 0.94), D=(0.6, 0.3, 0.74), F=(-0.1, -1, 0), pelvis_rot=(8, -14, 0), head_rot=(-6, -18, 0)), "in"),
         (25, Q(G=(0.06, -0.14, 0.92), D=(0.62, 0.34, 0.70), F=(-0.1, -1, 0), pelvis_rot=(8, -14, 0), head_rot=(-6, -18, 0)), "out"), (40, GK, "io")]),
         contact=11, notes="taps both pipes (contacts local 11 and 25): ritual"),
    Clip("goalie_reset_gloves", 678, 36, False, keys_fn([(0, GK, "io"), (8, Q(G=(-0.12, -0.30, 0.86), D=(-0.05, -0.1, 0.99), head_rot=(6, 0, 0), eye=(0, -10), face="neutral"), "io"),
         (16, Q(G=(-0.10, -0.28, 0.84), D=(-0.02, -0.1, 0.99), fingers=20, head_rot=(8, 0, 0), eye=(0, -10), face="neutral"), "io"),
         (26, Q(G=(-0.14, -0.30, 0.88), D=(-0.05, -0.1, 0.99), face="determined"), "io"), (36, GK, "io")]), notes="adjusts gloves, re-sets"),
    Clip("goalie_crossover_left", 724, 20, True, shuffle(+1, 20, 0.34), meta=shuffle_meta(+1, 20, 0.34), notes="long recovery step toward shooter-left; same beats as the shuffle"),
    Clip("goalie_crossover_right", 754, 20, True, shuffle(-1, 20, 0.34), meta=shuffle_meta(-1, 20, 0.34), notes="mirror"),
    Clip("goalie_read_high", 784, 18, False, keys_fn([(0, GK, "io"), (8, Q(pelvis_off=(0, -0.01, -0.06), G=(-0.22, -0.30, 1.02), head_rot=(-12, 0, 0), eye=(0, 10)), "out"),
         (18, Q(pelvis_off=(0, -0.01, -0.05), G=(-0.22, -0.30, 1.04), head_rot=(-12, 0, 0), eye=(0, 10)), "io")]), notes="chains into high saves"),
    Clip("goalie_read_low", 812, 18, False, keys_fn([(0, GK, "io"), (8, Q(pelvis_off=(0, -0.02, -0.14), pelvis_rot=(12, 0, 0), G=(-0.22, -0.32, 0.92), eye=(0, -10)), "out"),
         (18, Q(pelvis_off=(0, -0.02, -0.15), pelvis_rot=(12, 0, 0), G=(-0.22, -0.32, 0.92), eye=(0, -10)), "io")]), notes="chains into low saves / five-hole"),
    Clip("goalie_kick_save_left", 840, 30, False, keys_fn([(0, GK, "io"), (4, Q(pelvis_off=(-0.05, 0, -0.11)), "in"),
         (7, Q(pelvis_off=(-0.10, 0, -0.09), pelvis_rot=(6, 6, 14), footR=(-0.24, -0.06, 0.16), G=(-0.30, -0.30, 0.86), D=(-0.35, -0.1, 0.93), face="strain", eye=(14, -10)), "out"),
         (11, Q(pelvis_off=(-0.11, 0, -0.10), pelvis_rot=(6, 6, 16), footR=(-0.26, -0.07, 0.12), face="strain"), "io"), (30, GK, "io")]), contact=7, notes="leg kick save low"),
    Clip("goalie_kick_save_right", 880, 30, False, keys_fn([(0, GK, "io"), (4, Q(pelvis_off=(0.05, 0, -0.11)), "in"),
         (7, Q(pelvis_off=(0.10, 0, -0.09), pelvis_rot=(6, -6, -14), footL=(0.24, -0.06, 0.16), G=(-0.12, -0.30, 0.86), face="strain", eye=(-14, -10)), "out"),
         (11, Q(pelvis_off=(0.11, 0, -0.10), pelvis_rot=(6, -6, -16), footL=(0.26, -0.07, 0.12), face="strain"), "io"), (30, GK, "io")]), contact=7, notes="mirror"),
    Clip("goalie_doorstep_stuff", 920, 30, False, keys_fn([(0, GK, "io"), (4, Q(pelvis_off=(0, -0.06, -0.12), chest_rot=(8, 0, 0)), "in"),
         (6, Q(pelvis_off=(0, -0.09, -0.16), pelvis_rot=(12, 0, 0), chest_rot=(12, 0, 0), G=(-0.12, -0.36, 1.00), D=(0.02, -0.55, -0.83), F=(0, -0.83, 0.55), face="strain"), "out"),
         (12, Q(pelvis_off=(0, -0.08, -0.15), G=(-0.12, -0.35, 1.0), D=(0.02, -0.55, -0.83), F=(0, -0.83, 0.55), face="determined"), "io"), (30, GK, "io")]), contact=6, notes="point-blank stuff"),
    Clip("goalie_desperation_dive_left", 960, 36, False, keys_fn(save_keys(P(SAVE_L, pelvis_off=(-0.32, -0.06, -0.24), pelvis_rot=(10, 12, 22), spine_rot=(8, 8, 14),
         footR=(-0.30, -0.06, 0), footL=(-0.02, 0.02, 0.10), G=(-0.52, -0.30, 0.90), D=(-0.8, -0.1, 0.58), face="strain"), contact=9)), contact=9, notes="full stretch, slower recovery"),
    Clip("goalie_desperation_dive_right", 1006, 36, False, keys_fn(save_keys(P(SAVE_L, pelvis_off=(-0.32, -0.06, -0.24), pelvis_rot=(10, 12, 22), spine_rot=(8, 8, 14),
         footR=(-0.30, -0.06, 0), footL=(-0.02, 0.02, 0.10), G=(-0.52, -0.30, 0.90), D=(-0.8, -0.1, 0.58), face="strain"), True, 9, gx_right=0.16)), contact=9, notes="mirror"),
    Clip("goalie_trail_stick_recovery", 1052, 30, False, keys_fn([(0, P(SAVE_L, face="determined"), "io"), (10, Q(pelvis_off=(-0.10, 0, -0.10), G=(-0.30, -0.22, 0.80), D=(-0.5, 0.4, 0.76)), "io"),
         (20, Q(G=(-0.22, -0.28, 0.88)), "io"), (30, GK, "io")]), notes="stick sweeps back through, reset to ready"),
    Clip("goalie_frustrated_tap", 1092, 30, False, keys_fn([(0, GK, "io"), (6, Q(G=(-0.22, -0.30, 1.02), D=(-0.3, -0.45, -0.84), F=(0, -0.84, 0.45), head_rot=(8, 0, 0), face="disappointed"), "io"),
         (9, Q(G=(-0.22, -0.30, 1.00), D=(-0.3, -0.45, -0.84), F=(0, -0.84, 0.45), head_rot=(10, 8, 0), face="disappointed"), "out"),
         (14, Q(G=(-0.22, -0.30, 1.02), D=(-0.3, -0.45, -0.84), F=(0, -0.84, 0.45), head_rot=(10, -8, 0), face="disappointed"), "in"),
         (17, Q(G=(-0.22, -0.30, 1.00), D=(-0.3, -0.45, -0.84), F=(0, -0.84, 0.45), head_rot=(9, 0, 0), face="disappointed"), "out"), (30, GK, "io")]),
         notes="two stick taps on the turf, head shake (never mean)"),
    Clip("goalie_shrug", 1132, 24, False, keys_fn([(0, GK, "io"), (8, Q(pelvis_off=(0, 0, -0.06), chest_rot=(-4, 0, 0), head_rot=(-4, 0, 8), G=(-0.24, -0.26, 0.96), face="smirk"), "out"),
         (14, Q(pelvis_off=(0, 0, -0.07), head_rot=(-4, 0, 8), face="smirk"), "io"), (24, GK, "io")]), notes="good-natured shrug"),
    Clip("goalie_reset", 1166, 30, False, keys_fn([(0, Q(face="disappointed"), "io"), (10, Q(pelvis_off=(0, 0, -0.04), chest_rot=(-6, 0, 0), head_rot=(-10, 0, 0), face="neutral"), "io"),
         (20, Q(pelvis_off=(0, 0, -0.11), face="determined"), "out"), (30, GK, "io")]), notes="deep breath, bounce back into set"),
    Clip("goalie_stick_raise", 1206, 30, False, keys_fn([(0, GK, "io"), (8, Q(pelvis_off=(0, 0, -0.03), G=(-0.26, -0.12, 1.12), D=(-0.25, 0.05, 0.97), F=(0.3, -0.95, 0), head_rot=(-14, 0, 0), face="big_smile"), "out"),
         (20, Q(pelvis_off=(0, 0, -0.03), G=(-0.26, -0.12, 1.14), D=(-0.25, 0.05, 0.97), F=(0.3, -0.95, 0), head_rot=(-14, 0, 0), face="big_smile"), "io"), (30, GK, "io")]), notes="save celebration"),
    Clip("goalie_helmet_nod", 1246, 24, False, keys_fn([(0, GK, "io"), (6, Q(head_rot=(6, 0, 0), face="smirk"), "io"), (11, Q(head_rot=(-12, 0, 0), face="smirk"), "io"),
         (16, Q(head_rot=(4, 0, 0), face="smile"), "io"), (24, GK, "io")]), notes="cool nod"),
    Clip("goalie_small_dance", 1280, 48, False, gk_dyn(lambda t: dict(pelvis_off=(0.03 * math.sin(2 * math.pi * t / 16), 0, -0.07 - 0.02 * abs(math.sin(2 * math.pi * t / 16))),
         pelvis_rot=(4, 10 * math.sin(2 * math.pi * t / 16), 0), head_rot=(-6, -8 * math.sin(2 * math.pi * t / 16), 6 * math.sin(2 * math.pi * t / 8)),
         G=(-0.24, -0.18, 1.04), D=(-0.2, 0.05, 0.98), F=(0.3, -0.95, 0), face="big_smile" if 4 < t < 44 else "smile")), notes="happy sway"),
    Clip("goalie_big_clutch_save", 1338, 60, False, lambda t: keys_fn(save_keys(SAVE_HL))(t) if t <= 30 else keys_fn(celebrate())(min(36, (t - 30) * 1.2)),
         contact=7, notes="high save flowing into celebration"),
]

def extend_libraries():
    names = {c.name for c in CLIPS}
    CLIPS.extend([c for c in SHOOTER_LIB if c.name not in names])
    gnames = {c.name for c in BG_CLIPS}
    BG_CLIPS.extend([c for c in GOALIE_LIB if c.name not in gnames])
