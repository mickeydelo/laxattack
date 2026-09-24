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

def roll_dodge(sign, grip=None):
    """In-place roll dodge: plant, drop the shoulder, full pivot (feet follow), burst out. sign +1 = toward shooter-left."""
    def fn(t):
        u = t / 30.0; turn = -360.0 * sign * (u * u * (3 - 2 * u)) if 0.15 < u < 0.85 else (0.0 if u <= 0.15 else -360.0 * sign)
        if 0.15 < u < 0.85:
            w = (u - 0.15) / 0.7; turn = -360.0 * sign * (w * w * (3 - 2 * w))
        dip = math.sin(math.pi * min(1.0, u / 0.85)) * 0.07
        lead = -28.0 * sign * math.sin(math.pi * min(1.0, u / 0.85))      # shoulders lead the turn, then settle back to 0
        return dict(pelvis_off=(0.05 * sign * math.sin(math.pi * u), -0.02, -0.04 - dip), pelvis_rot=(8 * math.sin(math.pi * u), turn, 0),
                    spine_rot=(10 * math.sin(math.pi * u), lead * 0.6, 0), chest_rot=(6, lead * 0.4, 0), head_rot=(-8, -lead * 0.5, 0), feet_yaw=turn,
                    G=grip or ((-0.10, -0.12, 0.94) if sign > 0 else (-0.20, -0.10, 0.96)), D=(0.0, 0.25, 0.97), F=(0.2, -0.98, 0), face="determined", pocket=0.012)
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
    align_dodges()
    names = {c.name for c in CLIPS}
    CLIPS.extend([c for c in continuity_clips() if c.name not in names])
    gnames = {c.name for c in BG_CLIPS}
    BG_CLIPS.extend([c for c in goalie_idles() if c.name not in gnames])
    add_meta()


# ======================= gameplay continuity (Codex round cb53020+) =======================
def _bump(a, b, t):
    return math.sin(math.pi * min(1.0, max(0.0, (t - a) / (b - a))))

def mirror_field(p):
    """Left-handed mirror: body mirrored across X, stick mirrored, hands swap roles on the shaft (hand -> 1-hand)."""
    q = {k: v for k, v in p.items() if not k.startswith("_")}
    for k in ("pelvis_rot", "spine_rot", "chest_rot", "neck_rot", "head_rot"):
        a = p[k]; q[k] = (a[0], -a[1], -a[2])
    q["pelvis_off"] = (-p["pelvis_off"][0], p["pelvis_off"][1], p["pelvis_off"][2])
    fl, fr = p["footL"], p["footR"]; q["footL"] = (-fr[0], fr[1], fr[2]); q["footR"] = (-fl[0], fl[1], fl[2])
    for k in ("G", "D", "F"):
        v = p[k]; q[k] = (-v[0], v[1], v[2])
    q["eye"] = (-p["eye"][0], p["eye"][1]); q["hand"] = 1.0 - p.get("hand", 0.0); q["feet_yaw"] = -p.get("feet_yaw", 0.0)
    h = p.get("hair", (0, 0, 0)); q["hair"] = (h[0], -h[1], h[2]) if len(h) == 3 else h
    return q

def _mirror_fn(f0):
    return lambda t: finalize(mirror_field(f0(t)))

def _clip(name):
    return next(c for c in CLIPS if c.name == name)

def continuity_clips():
    out = []; cur = [1570]
    def add(name, length, loop, fn, contact=None, release=None, notes="", meta=None):
        out.append(Clip(name, cur[0], length, loop, fn, contact, release, notes=notes, meta=meta or {})); cur[0] += length + 10
    CR = cradle_pose(0); CL = finalize(mirror_field(CR))
    for src in ("cradle", "aim_overhand", "aim_bounce", "aim_sidearm", "release_overhand", "release_bounce", "release_sidearm",
                "quick_stick_catch", "quick_stick_release"):
        c = _clip(src)
        add(src + "_L", c.length, c.loop, _mirror_fn(c.fn), c.contact, c.release, notes="left-handed (left hand on top) mirror of " + src)
    MID = K(G=(0.0, -0.30, 0.97), D=(0.0, -0.10, 0.99), F=(0.0, -0.99, -0.10), hand=0.5, face="focused", head_rot=(-2, 0, 0))
    sw = [(0, CR, "io"), (4, P(MID, G=(-0.16, -0.30, 0.95), D=(-0.35, -0.08, 0.93), F=(0.3, -0.95, 0), hand=0.18), "in"), (8, MID, "lin"),
          (12, P(MID, G=(0.16, -0.30, 0.95), D=(0.35, -0.08, 0.93), F=(-0.3, -0.95, 0), hand=0.82), "out"), (16, CL, "io")]
    f_sw = keys_fn(sw)
    add("switch_R_to_L", 16, False, f_sw, contact=8, notes="stick sweeps across the face; hands meet mid-shaft at contact (8) and regrip left-on-top")
    add("switch_L_to_R", 16, False, _mirror_fn(f_sw), contact=8, notes="mirror: left-on-top -> right-on-top")
    Ld = 0.30
    DS = [(0, CR, "io"),
          (4, K(pelvis_off=(0, 0, -0.08), pelvis_rot=(6, 4, -4), chest_rot=(8, 6, 0), G=(-0.30, -0.24, 0.96), D=(-0.45, -0.05, 0.89), F=(0.5, -0.85, 0.1), face="determined"), "in"),
          (6, K(pelvis_off=(0, 0, -0.10), pelvis_rot=(8, -4, 6), chest_rot=(10, -6, 4), G=(-0.24, -0.28, 1.00), D=(-0.30, -0.10, 0.95), F=(0.5, -0.85, 0.1), face="determined"), "out"),
          (10, K(pelvis_off=(0, 0, -0.09), pelvis_rot=(6, -8, 8), chest_rot=(8, -10, 6), G=(0.0, -0.32, 0.98), D=(0.0, -0.12, 0.99), F=(0, -0.99, 0.1), hand=0.5, face="determined"), "lin"),
          (16, K(pelvis_off=(0, 0, -0.07), pelvis_rot=(8, 10, 6), chest_rot=(6, 12, 2), G=(0.24, -0.26, 0.90), D=(0.45, -0.05, 0.89), F=(-0.5, -0.85, 0.1), hand=1.0, face="determined"), "out"),
          (24, CL, "io")]
    f_ds = keys_fn(DS)
    def dodge_switch(t, f_ds=f_ds):
        R = Ld * smoothstep(6, 16, t)                      # Swift root curve (Blender +X = shooter-left)
        lead = Ld * smoothstep(8, 14, t); push = Ld * smoothstep(12, 17, t)
        p = dict(f_ds(t))
        p["footL"] = (lead - R, 0.0, 0.05 * _bump(8, 14, t)); p["footR"] = (push - R, 0.0, 0.04 * _bump(12, 17, t))
        po = p["pelvis_off"]; p["pelvis_off"] = (0.5 * (lead + push) - R + 0.03 * _bump(4, 12, t), po[1], po[2])
        return finalize(p)
    dmeta = lambda d: {"dodge_commit_frame": 6, "switch_contact_frame": 10, "travel_meters": Ld, "movement_direction": d,
                       "root_motion_curve": {"type": "smoothstep", "start_local_frame": 6, "end_local_frame": 16, "axis": "game -X" if d == "shooter_left" else "game +X"}}
    add("split_dodge_left_switch", 24, False, dodge_switch, notes="split dodge toward shooter-left with R->L hand switch; planted feet vs root curve", meta=dmeta("shooter_left"))
    add("split_dodge_right_switch", 24, False, _mirror_fn(dodge_switch), notes="split dodge toward shooter-right with L->R hand switch", meta=dmeta("shooter_right"))
    # cancellations / recoveries: from each aim stance and each dodge commit back to the cradle of the current hand
    def strip(p):
        return finalize({k: v for k, v in p.items() if not k.startswith("_")})
    for a in ("aim_overhand", "aim_bounce", "aim_sidearm", "aim_overhand_L", "aim_bounce_L", "aim_sidearm_L"):
        src = next(c for c in CLIPS + out if c.name == a); pa = strip(src.fn(0)); dst = CL if a.endswith("_L") else CR
        add(a + "_cancel", 8, False, keys_fn([(0, pa, "io"), (8, dst, "io")]), notes="aim stance -> cradle (same hand)")
    for d, cf in (("split_dodge_left", 6), ("split_dodge_right", 6), ("roll_dodge_left", 8), ("roll_dodge_right", 8), ("face_dodge_left", 5),
                  ("face_dodge_right", 5), ("split_dodge_left_switch", 6), ("split_dodge_right_switch", 6)):
        src = next(c for c in CLIPS + out if c.name == d); pa = strip(src.fn(cf)); pa["feet_yaw"] = 0.0 if abs(pa.get("feet_yaw", 0)) > 180 else pa.get("feet_yaw", 0.0)
        pa["footL"] = (0, 0, 0); pa["footR"] = (0, 0, 0); pa = finalize(pa)
        dst = CL if pa.get("hand", 0) > 0.5 else CR
        add(d + "_cancel", 10, False, keys_fn([(0, pa, "io"), (10, dst, "io")]), notes="cancel from the dodge commit pose -> cradle (current hand)")
    for a in ("aim_overhand", "aim_bounce", "aim_sidearm", "aim_overhand_L", "aim_bounce_L", "aim_sidearm_L"):
        src = next(c for c in CLIPS + out if c.name == a); pa = strip(src.fn(0)); st_ = CL if a.endswith("_L") else CR
        add("cradle_to_" + a, 8, False, keys_fn([(0, st_, "io"), (8, pa, "io")]), notes="cradle -> aim stance bridge (same hand)")
    for r_ in ("release_overhand", "release_bounce", "release_sidearm", "quick_stick_release",
               "release_overhand_L", "release_bounce_L", "release_sidearm_L", "quick_stick_release_L"):
        src = next(c for c in CLIPS + out if c.name == r_); pe = strip(src.fn(src.length)); dst = CL if r_.endswith("_L") else CR
        add(r_ + "_recover", 10, False, keys_fn([(0, pe, "io"), (10, dst, "io")]), notes="follow-through -> cradle (same hand)")
    return out

def align_dodges():
    """Existing dodges ease in from / out to the exact cradle pose (roll dodges keep their full turn)."""
    CR = {k: v for k, v in cradle_pose(0).items() if not k.startswith("_")}
    for c in CLIPS:
        if c.name not in ("split_dodge_left", "split_dodge_right", "roll_dodge_left", "roll_dodge_right", "face_dodge_left", "face_dodge_right") or getattr(c, "_aligned", False):
            continue
        f0, L = c.fn, c.length
        def fn(t, f0=f0, L=L):
            p = finalize({k: v for k, v in f0(t).items() if not k.startswith("_")})
            a = smoothstep(0, 5, t); b = smoothstep(L - 7, L, t)
            if a < 1:
                p = finalize({k: v for k, v in lerp_pose(CR, p, a).items() if not k.startswith("_")} | {"face": p["face"]})
            if b > 0:
                e = dict(CR); e["feet_yaw"] = round(p.get("feet_yaw", 0.0) / 360.0) * 360.0
                pr = e["pelvis_rot"]; e["pelvis_rot"] = (pr[0], pr[1] + round(p["pelvis_rot"][1] / 360.0) * 360.0, pr[2])   # full turns stay full turns
                p = finalize({k: v for k, v in lerp_pose(p, e, b).items() if not k.startswith("_")} | {"face": p["face"] if b < 0.5 else CR["face"]})
            return p
        c.fn = fn; c._aligned = True
    for rel, aim in (("release_overhand", "aim_overhand"), ("release_bounce", "aim_bounce"), ("release_sidearm", "aim_sidearm")):
        c = next(x for x in CLIPS if x.name == rel)
        if getattr(c, "_aligned", False):
            continue
        a0 = finalize({k: v for k, v in next(x for x in CLIPS if x.name == aim).fn(0).items() if not k.startswith("_")})
        f0 = c.fn
        def fn(t, f0=f0, a0=a0):
            p = finalize({k: v for k, v in f0(t).items() if not k.startswith("_")})
            w = smoothstep(0, 3, t)
            return p if w >= 1 else finalize({k: v for k, v in lerp_pose(a0, p, w).items() if not k.startswith("_")} | {"face": p["face"]})
        c.fn = fn; c._aligned = True

def goalie_idles():
    out = []
    taps = [(0, GK, "io"), (6, Q(G=(-0.42, -0.14, 0.94), D=(-0.6, 0.3, 0.74), pelvis_rot=(8, 14, 0), head_rot=(-6, 18, 0)), "in"),
            (9, Q(G=(-0.44, -0.12, 0.92), D=(-0.62, 0.34, 0.70), pelvis_rot=(8, 14, 0), head_rot=(-6, 18, 0)), "out"),
            (14, Q(pelvis_off=(0, 0, -0.11), head_rot=(-8, 0, 0)), "io"),
            (22, Q(G=(0.04, -0.16, 0.94), D=(0.6, 0.3, 0.74), F=(-0.1, -1, 0), pelvis_rot=(8, -14, 0), head_rot=(-6, -18, 0)), "in"),
            (25, Q(G=(0.06, -0.14, 0.92), D=(0.62, 0.34, 0.70), F=(-0.1, -1, 0), pelvis_rot=(8, -14, 0), head_rot=(-6, -18, 0)), "out"),
            (30, Q(pelvis_off=(0, 0, -0.11), head_rot=(-8, 0, 0)), "io"), (38, Q(head_rot=(0, 0, 0), face="determined"), "io"), (48, GK, "io")]
    out.append(Clip("goalie_center_taps", 1410, 48, False, keys_fn(taps), contact=9, notes="waiting routine: tap left pipe, re-centre, tap right pipe, nod",
                    meta={"pipe_tap_frames": [9, 25], "recommended_use": "between shots while the shooter resets"}))
    def spin(t):
        u = t / 40.0; D0 = (-0.10, -0.12, 0.99)
        p = Q(G=(-0.20, -0.30, 0.92), D=D0, F=_roll_stick(D0, (0.05, -1.0, 0.1), 720 * smoothstep(4, 30, t)),
              head_rot=(-4, 9 * math.sin(2 * math.pi * 3 * u) * (1 - u), 0), pelvis_off=(0, 0, -0.07 - 0.012 * math.sin(2 * math.pi * 2 * u)),
              face="disappointed" if u < 0.55 else "determined")
        p = finalize(p)
        return finalize({k: v for k, v in lerp_pose(p, GK, smoothstep(32, 40, t)).items() if not k.startswith("_")} | {"face": p["face"] if t < 36 else "focused"})
    out.append(Clip("goalie_stick_spin", 1468, 40, False, spin, notes="after a goal against: spins the stick twice in his hands, shakes it off, re-sets",
                    meta={"recommended_use": "after goalie_goal_against or a missed save"}))
    def lively(t):
        ph = 2 * math.pi * t / 48; b = 0.5 - 0.5 * math.cos(2 * ph)
        return finalize(P(GK, pelvis_off=(0.006 * math.sin(ph), 0, -0.09 - 0.022 * b), G=tuple(V(GK["G"]) + V((0.01 * math.sin(ph), 0, -0.012 * b))),
                          F=_roll_stick(GK["D"], GK["F"], 12 * math.sin(2 * ph)), head_rot=(-8, 7 * math.sin(ph), 0), eye=(6 * math.sin(ph + 0.5), 0)))
    out.append(Clip("goalie_ready_lively", 1518, 48, True, lively, blinks=(20,), notes="livelier ready loop: bounce, stick waggle, tracking head"))
    return out

def add_meta():
    for c in CLIPS:
        m = c.meta; hl = "left" if c.name.endswith("_L") or "_L_" in c.name else "right"
        m.setdefault("recommended_blend_in_s", 0.08 if c.name.startswith(("release_", "quick_stick_release")) else 0.12)
        m.setdefault("recommended_blend_out_s", 0.15)
        if c.name.startswith(("cradle", "aim_")) and not c.name.endswith("_cancel"):
            m["handedness"] = hl
        if c.name.startswith("aim_") and not c.name.endswith("_cancel"):
            kind = c.name.split("_")[1]; m["compatible_releases"] = ["release_%s%s" % (kind, "_L" if hl == "left" else "")]
        if c.name.startswith(("release_", "quick_stick_release")) and c.release is not None:
            m["handedness"] = hl; m["ideal_release_window"] = [max(0, c.release - 2), c.release + 1]; m["recovery_frame"] = min(c.length, c.release + 9)
        if c.name.startswith("quick_stick_catch") and c.contact is not None:
            m["handedness"] = hl; m["contact_window"] = [max(0, c.contact - 1), c.contact + 1]; m["recovery_frame"] = min(c.length, c.contact + 8)
        if c.name.startswith("switch_"):
            m["switch_contact_frame"] = 8; m["recovery_frame"] = 12
            m["handedness_start"], m["handedness_end"] = ("right", "left") if "R_to_L" in c.name else ("left", "right")
        if c.name in ("split_dodge_left", "split_dodge_right", "roll_dodge_left", "roll_dodge_right", "face_dodge_left", "face_dodge_right"):
            cf = {"split": 6, "roll": 8, "face": 5}[c.name.split("_")[0]]
            m["dodge_commit_frame"] = cf; m["recovery_frame"] = cf + 10; m["handedness_start"] = m["handedness_end"] = "right"
            m["movement_direction"] = "shooter_left" if c.name.endswith("left") else "shooter_right"
        if c.name.endswith("_switch") and c.name.startswith("split_dodge"):
            m["recovery_frame"] = 18
            m["handedness_start"], m["handedness_end"] = ("right", "left") if "left" in c.name else ("left", "right")
        if c.name.endswith("_recover") or c.name.startswith("cradle_to_"):
            m["recovery_frame"] = c.length; m["handedness"] = hl
        if c.name.endswith("_cancel"):
            m["recovery_frame"] = c.length; m["cancel_of"] = c.name[:-7]
