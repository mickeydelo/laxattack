# v9 lookdev turnaround renderer (front / right side / back, studio backdrop, stick prop)
def v9_studio(sc, C):
    w = bpy.data.worlds.new("studio"); w.use_nodes = True; sc.world = w
    bg = w.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value = (0.96, 0.94, 0.90, 1); bg.inputs["Strength"].default_value = 0.75
    obj_from_geo("floor", superellipsoid((12, 12, 0.1), 0.1, 0.1, 16, 4, (0, 0, -0.05)), "kit_cream_v9", C)
    for n, loc, en, size, col in (("key", (-2.2, -2.6, 3.2), 420, 2.5, (1.0, 0.95, 0.88)), ("fill", (2.6, -2.0, 1.6), 140, 3.0, (0.92, 0.95, 1.0)),
                                  ("rim", (0.5, 3.0, 2.6), 320, 2.0, (1.0, 0.97, 0.92))):
        ld = bpy.data.lights.new(n, "AREA"); ld.energy = en; ld.size = size; ld.color = col
        lo = bpy.data.objects.new(n, ld); C.objects.link(lo); lo.location = loc
        lo.rotation_euler = (V((0, 0, 0.6)) - V(loc)).to_track_quat("-Z", "Y").to_euler()

def v9_turnaround(spec, look, name, tag="v9", res=(620, 820)):
    reset_scene("v9_" + name); sc = bpy.context.scene; C = coll(name)
    arm = build_skeleton(spec, C, name + "_rig")
    build_character_v9(spec, C, arm, look)
    st, meta = build_stick("goalie" if look == "goalie" else "attack", C, None, name=name + "_stick_prop",
                           frame_mat="goggle_white" if look == "player" else "cage_white", pocket_mat="cage_white")
    st.rotation_euler = (0, 0, math.radians(-80)); st.location = (-0.45, -0.75, 0.025)
    L = coll("Lookdev"); v9_studio(sc, L)
    setup_eevee(64, res); sc.render.use_stamp = False; sc.view_settings.exposure = -0.2
    tiles = []
    for view, loc in (("front", (0.0, -4.4, 0.95)), ("side", (-4.4, 0.0, 0.95)), ("back", (0.0, 4.4, 0.95))):
        cam = make_camera("cam_" + view, loc, (0, 0, 0.64), L, lens=58, portrait=True)
        tiles.append(render_to("/tmp/laxprev/%s_%s_%s.png" % (tag, name, view), cam))
    out = os.path.join(PROD, "Previews", "V9", "v9_%s_turnaround.png" % name)
    contact_sheet(tiles, out, 3)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROD, "Previews", "V9", "v9_%s_lookdev.blend" % name), compress=True)
    return out
