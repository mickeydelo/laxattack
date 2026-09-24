# Lax Attack lighting kit: warm diorama environment map (EXR) + colour-grading LUT (.cube + 1024x32 strip) + before/after preview.
import numpy as np
KIT_DIR = os.path.join(PROD, "Exports", "Lighting")

def build_env_map(res=(1024, 512)):
    reset_scene("LaxEnv")
    C = coll("env")
    setup_world(); sc = bpy.context.scene
    sd = bpy.data.lights.new("sun_glow", "SUN"); sd.energy = 0.0          # sun comes from the runtime directional light, not the IBL
    obj_from_geo("ground", superellipsoid((400, 400, 1.0), 0.1, 0.1, 16, 4, (0, 0, -0.6)), "turf_a", C)
    obj_from_geo("lake_band", superellipsoid((160, 40, 0.2), 0.2, 0.2, 16, 4, (0, -60, -0.05)), "water", C)
    cd = bpy.data.cameras.new("equirect"); cd.type = "PANO"
    if hasattr(cd, "panorama_type"):
        cd.panorama_type = "EQUIRECTANGULAR"
    else:
        cd.cycles.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("equirect", cd); C.objects.link(cam); cam.location = (0, 0, 1.6)
    cam.rotation_euler = (math.radians(90), 0, 0)      # image centre looks along Blender -Y  (= game -Z, gameplay forward)
    sc.camera = cam
    r = sc.render; r.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    if hasattr(r.image_settings, "media_type"):
        r.image_settings.media_type = "IMAGE"
    r.resolution_x, r.resolution_y = res; r.resolution_percentage = 100
    r.image_settings.file_format = "OPEN_EXR"; r.image_settings.color_depth = "16"; r.image_settings.exr_codec = "ZIP"
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0.0
    os.makedirs(KIT_DIR, exist_ok=True)
    path = os.path.join(KIT_DIR, "lax_env_pinebrook_1k.exr"); r.filepath = path
    bpy.ops.render.render(write_still=True)
    return path

def grade(rgb):
    """Warm miniature grade: gentle S-curve, +12% saturation, warm highlights, slightly lifted warm shadows."""
    x = np.clip(rgb, 0, 1)
    x = x + 0.08 * (x - x * x) * (x - 0.5) * 4 * 0.5                     # soft S-curve
    l = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    x = l + (x - l) * 1.12
    hi = np.clip((l - 0.55) / 0.45, 0, 1); lo = np.clip((0.35 - l) / 0.35, 0, 1)
    x = x + hi * np.array([0.030, 0.012, -0.020]) + lo * np.array([0.018, 0.010, 0.0])
    return np.clip(x, 0, 1)

def build_lut(n=32):
    g = np.linspace(0, 1, n); r_, g_, b_ = np.meshgrid(g, g, g, indexing="ij")
    src = np.stack([r_, g_, b_], -1); out = grade(src)
    cube = os.path.join(KIT_DIR, "lax_grade_warm_miniature_32.cube")
    with open(cube, "w") as fh:
        fh.write('TITLE "Lax Attack warm miniature"\nLUT_3D_SIZE %d\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n' % n)
        for bi in range(n):
            for gi in range(n):
                for ri in range(n):
                    c = out[ri, gi, bi]; fh.write("%.6f %.6f %.6f\n" % (c[0], c[1], c[2]))
    strip = np.zeros((n, n * n, 3), np.float32)          # 1024x32 strip: tile b horizontally, x = r, y = g (row 0 at top)
    for bi in range(n):
        strip[:, bi * n:(bi + 1) * n, :] = np.transpose(out[:, :, bi, :], (1, 0, 2))
    im = bpy.data.images.new("lut_strip", n * n, n, alpha=False)
    im.pixels = np.concatenate([strip[::-1], np.ones((n, n * n, 1), np.float32)], -1).ravel()
    im.colorspace_settings.name = "Non-Color"
    p = os.path.join(KIT_DIR, "lax_grade_warm_miniature_32_strip.png"); im.filepath_raw = p; im.file_format = "PNG"; im.save(); bpy.data.images.remove(im)
    return cube, p

def lut_preview(src_png):
    im = bpy.data.images.load(src_png); w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4); bpy.data.images.remove(im)
    after = a.copy(); after[..., :3] = grade(a[..., :3])        # applied in display (sRGB) space, as a post-process LUT would be
    both = np.concatenate([a, after], 1)
    o = bpy.data.images.new("lut_prev", w * 2, h, alpha=True); o.pixels = both.ravel()
    p = os.path.join(KIT_DIR, "lax_grade_before_after.png"); o.filepath_raw = p; o.file_format = "PNG"; o.save(); bpy.data.images.remove(o)
    return p
