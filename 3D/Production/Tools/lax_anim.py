# Lax Attack animation system: clip timeline, baking (body + face + pocket + fingers), baked secondary springs.
# Poses are authored in the 1.5 m design space (see lax_pose); apply_pose scales them by the rig's body_scale.
KEYED = [("pelvis", "location"), ("pelvis", "rotation_euler"), ("spine", "rotation_euler"), ("chest", "rotation_euler"),
         ("neck", "rotation_euler"), ("head", "rotation_euler"), ("ik_foot_L", "location"), ("ik_foot_R", "location"),
         ("stick", "location"), ("stick", "rotation_quaternion"),
         ("hair_01", "rotation_euler"), ("hair_02", "rotation_euler"), ("hair_03", "rotation_euler"),
         ("hem_F", "rotation_euler"), ("hem_B", "rotation_euler"), ("pocket_01", "location"), ("pocket_02", "location"),
         ("fingers_L", "rotation_euler"), ("fingers_R", "rotation_euler"),
         ("lid_L", "rotation_euler"), ("lid_R", "rotation_euler"), ("jaw", "rotation_euler"), ("brow_L", "location"), ("brow_R", "location"),
         ("brow_L", "rotation_euler"), ("brow_R", "rotation_euler"), ("mouth_L", "location"), ("mouth_R", "location"),
         ("eye_L", "rotation_euler"), ("eye_R", "rotation_euler")]
GOALIE_EXTRA = [("chest_pad", "rotation_euler"), ("throat_guard", "rotation_euler")]

class Clip:
    def __init__(self, name, start, length, loop, fn, contact=None, release=None, transition=0.12, notes="", blinks=()):
        self.name, self.start, self.length, self.loop, self.fn = name, start, length, loop, fn
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
            poses = secondary(poses, c.loop)
            prev_q = None
            for f, p in enumerate(poses):
                apply_pose(arm, p, family, blink=any(abs(f - b) <= 1 for b in c.blinks))
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

def manifest(asset, clips, fps=30, perspective="shooter", extra=None):
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
        m["clips"].append(d)
    if extra:
        m.update(extra)
    return m
