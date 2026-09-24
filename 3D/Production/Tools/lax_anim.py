# Lax Attack animation system: clip timeline, baking (body + face + pocket + fingers), baked secondary springs.
# Poses are authored in the 1.5 m design space (see lax_pose); apply_pose scales them by the rig's body_scale.
KEYED = [("pelvis", "location"), ("pelvis", "rotation_euler"), ("spine", "rotation_euler"), ("chest", "rotation_euler"),
         ("neck", "rotation_euler"), ("head", "rotation_euler"), ("ik_foot_L", "location"), ("ik_foot_R", "location"), ("ik_foot_L", "rotation_euler"), ("ik_foot_R", "rotation_euler"), ("ik_hand_L", "location"), ("ik_hand_R", "location"),
         ("stick", "location"), ("stick", "rotation_quaternion"),
         ("hair_01", "rotation_euler"), ("hair_02", "rotation_euler"), ("hair_03", "rotation_euler"),
         ("hem_F", "rotation_euler"), ("hem_B", "rotation_euler"), ("pocket_01", "location"), ("pocket_02", "location"),
         ("fingers_L", "rotation_euler"), ("fingers_R", "rotation_euler"),
         ("lid_L", "rotation_euler"), ("lid_R", "rotation_euler"), ("jaw", "rotation_euler"), ("brow_L", "location"), ("brow_R", "location"),
         ("brow_L", "rotation_euler"), ("brow_R", "rotation_euler"), ("mouth_L", "location"), ("mouth_R", "location"),
         ("eye_L", "rotation_euler"), ("eye_R", "rotation_euler")]
GOALIE_EXTRA = [("chest_pad", "rotation_euler"), ("throat_guard", "rotation_euler")]

class Clip:
    def __init__(self, name, start, length, loop, fn, contact=None, release=None, transition=0.12, notes="", blinks=(), meta=None):
        self.name, self.start, self.length, self.loop, self.fn = name, start, length, loop, fn
        self.meta = meta or {}
        self.contact, self.release, self.transition, self.notes, self.blinks = contact, release, transition, notes, blinks
    @property
    def end(self):
        return self.start + self.length

def spring_series(u, loop, omega=16.0, zeta=0.32, fps=30):
    """Damped spring following input signal u (list). Returns lagged response. Loops are pre-rolled 3 cycles."""
    dt = 1.0 / fps; n = len(u)
    seq = (u[:-1] * 3 + u) if loop and n > 2 else u
    x, v = seq[0], 0.0; out = []
    for target in seq:
        for _ in range(4):   # substeps
            a = -omega * omega * (x - target) - 2 * zeta * omega * v
            v += a * dt / 4; x += v * dt / 4
        out.append(x)
    return out[-n:]

def secondary(poses, loop):
    """Bake hair/hem lag from pelvis + chest motion (design units -> degrees)."""
    pz = [p["pelvis_off"][2] for p in poses]; px = [p["pelvis_off"][0] for p in poses]
    yaw = [p["pelvis_rot"][1] + p["spine_rot"][1] + p["chest_rot"][1] for p in poses]
    pitch = [p["chest_rot"][0] + p["spine_rot"][0] for p in poses]
    # hair: vertical bounce -> pitch lag; lateral/yaw -> roll lag
    hp_in = [z * -260.0 + a * 0.4 for z, a in zip(pz, pitch)]
    hr_in = [x * 220.0 + y * 0.35 for x, y in zip(px, yaw)]
    hp = spring_series(hp_in, loop); hr = spring_series(hr_in, loop, 13.0, 0.28)
    hem_in = [z * -150.0 for z in pz]; hem = spring_series(hem_in, loop, 20.0, 0.4)
    for i, p in enumerate(poses):
        p["hair"] = (hp[i] - hp_in[i] * 0.6, hr[i] - hr_in[i] * 0.6, 0)
        p["hem"] = (hem[i] - hem_in[i] * 0.5, -(hem[i] - hem_in[i] * 0.5))
    return poses

CALM = ("idle", "cradle", "aim_", "goalie_ready", "goalie_scan", "crowd_idle", "crowd_watch", "crowd_anticipate", "run_loop")

def _seed(s):
    return sum((i + 1) * ord(ch) for i, ch in enumerate(s))

def auto_blinks(c):
    """Blink every ~2-3.5 s (deterministic per clip), never within 4 frames of a release/contact event or a loop seam."""
    if c.length < 36:
        return ()
    avoid = [x for x in (c.release, c.contact) if x is not None]
    rnd = random.Random(_seed(c.name)); f = 14 + rnd.randint(0, 22); out = []
    while f < c.length - 5:
        if all(abs(f - a) > 4 for a in avoid):
            out.append(f)
        f += 60 + rnd.randint(0, 45)
    return tuple(out)

def eye_darts(poses, c):
    """Small saccades (hold, quick 2-frame move, hold). Loops start and end on the authored gaze."""
    rnd = random.Random(_seed(c.name) + 7); n = len(poses); keys = [(0, (0.0, 0.0))]; f = 10 + rnd.randint(0, 12)
    while f < n - 8:
        keys.append((f, (rnd.uniform(-4, 4), rnd.uniform(-2.5, 2.5)))); f += 18 + rnd.randint(0, 20)
    keys.append((max(n - 6, keys[-1][0] + 2), (0.0, 0.0)))
    out = []
    for k, p in enumerate(poses):
        v = keys[0][1]
        for f0, val in keys:
            if k >= f0:
                u = min(1.0, (k - f0) / 2.0); v = tuple(a + (b - a) * u for a, b in zip(v, val)) if u < 1 else val
        q = dict(p); q["eye"] = (p["eye"][0] + v[0], p["eye"][1] + v[1]); out.append(q)
    return out

def stick_lag(poses, loop, release=None):
    """Hands drive the shaft; the head lags slightly (spring on the shaft direction). The ball rolls laterally in the pocket
    against angular velocity and compresses with acceleration. Release clips only lag after the release frame (timing kept)."""
    n = len(poses); D = [V(p["D"]).normalized() for p in poses]
    comps = [spring_series([d[i] for d in D], loop, 18.0, 0.6) for i in range(3)]
    lat_in, dep_in = [], []
    for k in range(n):
        a = D[(k - 1) % n] if (loop or k > 0) else D[k]; b = D[(k + 1) % n] if (loop or k < n - 1) else D[k]
        X = D[k].cross(V(poses[k]["F"])).normalized()
        lat_in.append(max(-0.012, min(0.012, -(b - a).dot(X) * 0.9)))
        dep_in.append(min(0.008, (b - 2 * D[k] + a).length * 3.0))
    lat = spring_series(lat_in, loop, 14.0, 0.45); dep = spring_series(dep_in, loop, 16.0, 0.5)
    # continuity: every clip's first frame is the exact authored pose (loops subtract their frame-0 offset, which keeps them
    # periodic); one-shot clips also ease the layer out over their last frames so the next clip starts cleanly
    off0 = (V((comps[0][0], comps[1][0], comps[2][0])) - D[0]) if loop else V((0, 0, 0))
    lat0 = lat[0] if loop else 0.0; dep0 = dep[0] if loop else 0.0
    out = []
    for k, p in enumerate(poses):
        w = 1.0 if release is None else smoothstep(release + 1, release + 5, k)
        if not loop:
            w *= smoothstep(0, 3, k) * (1 - smoothstep(n - 7, n - 1, k))
        lag = V((comps[0][k], comps[1][k], comps[2][k]))
        Dn = (D[k] + ((lag - D[k]) - off0) * 0.5 * w).normalized()
        q = dict(p); q["D"] = tuple(Dn); q["F"] = tuple(orth(p["F"], Dn))
        q["pocket_x"] = (lat[k] - lat0) * w
        q["pocket"] = p["pocket"] + (dep[k] - dep0) * w
        out.append(q)
    return out

def bake_clips(arm, clips, family="field", extra_channels=()):
    pbs = arm.pose.bones
    keyed = [(n, pth) for n, pth in KEYED + list(extra_channels) if n in pbs]
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type; prefs.keyframe_new_interpolation_type = "LINEAR"
    ad = arm.animation_data_create()
    try:
        for c in clips:
            act = bpy.data.actions.new(c.name); act.use_fake_user = True; ad.action = act
            poses = [c.fn(f) for f in range(0, c.length + 1)]
            blinks = c.blinks or auto_blinks(c)
            per = (c.length / max(1, round(c.length / 48.0))) if c.loop else 48.0     # breathing: whole cycles per loop
            for k, p in enumerate(poses):
                bth = math.sin(2 * math.pi * k / per) if c.loop else \
                    math.sin(2 * math.pi * k / 48.0) * smoothstep(0, 6, k) * (1 - smoothstep(c.length - 6, c.length, k))   # 0 at both ends
                p["chest_rot"] = (p["chest_rot"][0] + 1.3 * bth, p["chest_rot"][1], p["chest_rot"][2])
                p["spine_rot"] = (p["spine_rot"][0] + 0.5 * bth, p["spine_rot"][1], p["spine_rot"][2])
                p["head_rot"] = (p["head_rot"][0] - 0.9 * bth, p["head_rot"][1], p["head_rot"][2])
            if c.name.startswith(CALM):
                poses = eye_darts(poses, c)
            poses = secondary(poses, c.loop)
            if family == "field" and (c.name in ("run_loop",) or c.name.startswith(("idle", "cradle", "aim_", "release_", "quick_stick", "switch_", "split_dodge", "face_dodge"))):
                poses = stick_lag(poses, c.loop, c.release)
            prev_q = None
            for f, p in enumerate(poses):
                apply_pose(arm, p, family, blink=any(abs(f - b) <= 1 for b in blinks))
                q = pbs["stick"].rotation_quaternion.copy()
                if prev_q is not None and q.dot(prev_q) < 0:
                    q.negate(); pbs["stick"].rotation_quaternion = q
                prev_q = q
                for n, pth in keyed:
                    pbs[n].keyframe_insert(pth, frame=f, group=n)
            ad.action = None
    finally:
        prefs.keyframe_new_interpolation_type = old
    track = ad.nla_tracks.new(); track.name = "clips"
    for i, c in enumerate(clips):
        act = bpy.data.actions[c.name]
        st = track.strips.new(c.name, c.start, act)
        if hasattr(st, "action_slot") and st.action_slot is None and len(act.slots):
            st.action_slot = act.slots[0]
        st.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD"
    ad.action = None
    for b in pbs:
        b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.scale = (1, 1, 1)
    sc = bpy.context.scene
    sc.frame_start = 0; sc.frame_end = clips[-1].end
    sc.timeline_markers.clear()
    for c in clips:
        sc.timeline_markers.new(c.name + "_start", frame=c.start)
        if c.release is not None:
            sc.timeline_markers.new(c.name + "_RELEASE", frame=c.start + c.release)
        if c.contact is not None:
            sc.timeline_markers.new(c.name + "_CONTACT", frame=c.start + c.contact)

def manifest(asset, clips, fps=30, perspective="shooter", extra=None, body_scale=1.0):
    m = {"asset": asset, "fps": fps, "timeline_end": clips[-1].end,
         "left_right_convention": {"shooter": "left/right are the shooter's own left/right (shooter faces -Z; shooter-left = -X in game space)",
                                   "goalie": "left/right are from the SHOOTER's perspective (goalie faces +Z); goalie_save_left = shooter's left = game -X",
                                   "none": "n/a"}[perspective],
         "clips": []}
    for c in clips:
        d = {"name": c.name, "start": c.start, "end": c.end, "loop": c.loop, "transition_seconds": c.transition}
        if c.release is not None:
            d["release_frame"] = c.start + c.release; d["release_local_frame"] = c.release
            d["release_seconds_after_start"] = round(c.release / fps, 4)
        if c.contact is not None:
            d["contact_frame"] = c.start + c.contact; d["contact_local_frame"] = c.contact
        if c.notes:
            d["notes"] = c.notes
        for k, v in getattr(c, "meta", {}).items():
            d[k] = round(v * body_scale, 4) if k == "travel_meters" else v
        m["clips"].append(d)
    if extra:
        m.update(extra)
    return m
