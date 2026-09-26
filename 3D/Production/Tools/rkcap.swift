
import Foundation
import RealityKit
import Metal
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

struct Placement { let file: String; let pos: SIMD3<Float>; let yawDeg: Float; let frame: Double }

@MainActor func loadPlaced(_ dir: String, _ p: Placement, grounding: Bool) throws -> Entity {
    let e = try Entity.load(contentsOf: URL(fileURLWithPath: dir + "/" + p.file))
    e.position = p.pos
    e.orientation = simd_quatf(angle: p.yawDeg * .pi / 180, axis: [0, 1, 0])
    if let a = e.availableAnimations.first, p.frame >= 0 {
        let c = e.playAnimation(a, transitionDuration: 0, startsPaused: true)
        c.time = p.frame / 30.0
    }
    if grounding {
        func walk(_ x: Entity) { if x.components.has(ModelComponent.self) { x.components.set(GroundingShadowComponent(castsShadow: true)) }; x.children.forEach(walk) }
        walk(e)
    }
    return e
}

@MainActor func hide(_ root: Entity, names: [String]) {
    func walk(_ x: Entity) { if names.contains(x.name) { x.isEnabled = false }; x.children.forEach(walk) }
    walk(root)
}

@MainActor func render(_ args: [String]) throws {
    // args: exportsDir outPNG width height camX camY camZ tgtX tgtY tgtZ vfov iblExp sunLux mode(scene|face_goalie|face_shooter|save) frameShooter frameGoalie
    let dir = args[0], out = args[1]
    let W = Int(args[2])!, H = Int(args[3])!
    let camPos = SIMD3<Float>(Float(args[4])!, Float(args[5])!, Float(args[6])!)
    let tgt = SIMD3<Float>(Float(args[7])!, Float(args[8])!, Float(args[9])!)
    let vfov = Float(args[10])!, iblExp = Float(args[11])!, sunLux = Float(args[12])!
    let mode = args[13]; let fS = Double(args[14])!, fG = Double(args[15])!
    let renderer = try RealityRenderer()
    let root = Entity()
    if mode.hasPrefix("scene") || mode.hasPrefix("save") || mode.hasPrefix("shore") {
        let arena = try loadPlaced(dir, Placement(file: "lax_arena_pinebrook_v9_lod1.usdz", pos: [0, 0, 0], yawDeg: 0, frame: -1), grounding: false)
        hide(arena, names: ["collision_only", "far_background", "foreground_framing", "camera_markers", "crowd_markers", "shadow_only"])
        root.addChild(arena)
        root.addChild(try loadPlaced(dir, Placement(file: "lax_goal.usdz", pos: [0, 0, -5.7], yawDeg: 0, frame: 0), grounding: true))
    }
    root.addChild(try loadPlaced(dir, Placement(file: "lax_shooter.usdz", pos: [-0.72, 0, 1.72], yawDeg: 0, frame: fS), grounding: true))
    root.addChild(try loadPlaced(dir, Placement(file: "lax_goalie.usdz", pos: [0, 0, -4.95], yawDeg: 0, frame: fG), grounding: true))
    renderer.entities.append(root)
    // image-based light from the kit EXR
    let exr = URL(fileURLWithPath: dir + "/Lighting/lax_env_pinebrook_1k.exr")
    if let src = CGImageSourceCreateWithURL(exr as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) {
        renderer.lighting.resource = try EnvironmentResource(equirectangular: img)
        renderer.lighting.intensityExponent = iblExp
    }
    let sun = DirectionalLight()
    sun.light.intensity = sunLux
    sun.light.color = .init(red: 1.0, green: 0.84, blue: 0.62, alpha: 1)
    sun.shadow = DirectionalLightComponent.Shadow(maximumDistance: 25, depthBias: 2)
    sun.look(at: [0, 0, 0], from: mode.hasSuffix("_front") ? [-4.2, 6.6, -6.2] : [-4.2, 6.6, 6.2], relativeTo: nil)
    root.addChild(sun)
    let cam = PerspectiveCamera()
    cam.camera.fieldOfViewInDegrees = vfov
    cam.look(at: tgt, from: camPos, relativeTo: nil)
    root.addChild(cam)
    renderer.activeCamera = cam
    let dev = MTLCreateSystemDefaultDevice()!
    let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm_srgb, width: W, height: H, mipmapped: false)
    td.usage = [.renderTarget, .shaderRead, .shaderWrite]; td.storageMode = .shared
    let tex = dev.makeTexture(descriptor: td)!
    let output = try RealityRenderer.CameraOutput(.singleProjection(colorTexture: tex))
    var done = false
    for i in 0..<4 {
        try renderer.updateAndRender(deltaTime: i == 0 ? 0.0 : 0.001, cameraOutput: output, onComplete: { _ in if i == 3 { done = true } })
    }
    let limit = Date().addingTimeInterval(20)
    while !done && Date() < limit { RunLoop.main.run(until: Date().addingTimeInterval(0.05)) }
    var bytes = [UInt8](repeating: 0, count: W * H * 4)
    tex.getBytes(&bytes, bytesPerRow: W * 4, from: MTLRegionMake2D(0, 0, W, H), mipmapLevel: 0)
    let cs = CGColorSpace(name: CGColorSpace.sRGB)!
    let ctx = CGContext(data: &bytes, width: W, height: H, bitsPerComponent: 8, bytesPerRow: W * 4, space: cs,
                        bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    let cg = ctx.makeImage()!
    let dst = CGImageDestinationCreateWithURL(URL(fileURLWithPath: out) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dst, cg, nil); CGImageDestinationFinalize(dst)
    print("OK \(out) done=\(done)")
}

@main struct Main {
    @MainActor static func main() {
        do { try render(Array(CommandLine.arguments.dropFirst())) } catch { print("ERROR \(error)") }
    }
}
