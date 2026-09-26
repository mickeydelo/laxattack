
import Foundation
import RealityKit
import Metal
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers
struct Ent: Decodable { let file: String; let pos: [Float]; let yaw: Float?; let frame: Double?; let ground: Bool? }
struct Shot: Decodable { let out: String; let w: Int; let h: Int; let cam: [Float]; let target: [Float]; let vfov: Float; let sun_from: [Float]?; let hide: [String]?; let entities: [Ent] }
struct Cfg: Decodable { let exports: String; let ibl_exponent: Float; let sun_lux: Float; let shots: [Shot] }
@MainActor func renderShot(_ cfg: Cfg, _ s: Shot, _ env: EnvironmentResource?, _ dev: MTLDevice) throws {
    let renderer = try RealityRenderer(); let root = Entity()
    for e in s.entities {
        let ent = try Entity.load(contentsOf: URL(fileURLWithPath: cfg.exports + "/" + e.file))
        ent.position = SIMD3<Float>(e.pos[0], e.pos[1], e.pos[2])
        ent.orientation = simd_quatf(angle: (e.yaw ?? 0) * .pi / 180, axis: [0, 1, 0])
        if let f = e.frame, f >= 0, let a = ent.availableAnimations.first { let c = ent.playAnimation(a, transitionDuration: 0, startsPaused: true); c.time = f / 30.0 }
        if e.ground ?? false { func walk(_ x: Entity) { if x.components.has(ModelComponent.self) { x.components.set(GroundingShadowComponent(castsShadow: true)) }; x.children.forEach(walk) }; walk(ent) }
        if let hide = s.hide { func walk(_ x: Entity) { if hide.contains(x.name) { x.isEnabled = false }; x.children.forEach(walk) }; walk(ent) }
        root.addChild(ent)
    }
    renderer.entities.append(root)
    if let env = env { renderer.lighting.resource = env; renderer.lighting.intensityExponent = cfg.ibl_exponent }
    let sun = DirectionalLight(); sun.light.intensity = cfg.sun_lux; sun.light.color = .init(red: 1.0, green: 0.84, blue: 0.62, alpha: 1)
    sun.shadow = DirectionalLightComponent.Shadow(maximumDistance: 25, depthBias: 2)
    let sf = s.sun_from ?? [-4.2, 6.6, 6.2]; sun.look(at: [0, 0, 0], from: SIMD3<Float>(sf[0], sf[1], sf[2]), relativeTo: nil); root.addChild(sun)
    let cam = PerspectiveCamera(); cam.camera.fieldOfViewInDegrees = s.vfov
    cam.look(at: SIMD3<Float>(s.target[0], s.target[1], s.target[2]), from: SIMD3<Float>(s.cam[0], s.cam[1], s.cam[2]), relativeTo: nil)
    root.addChild(cam); renderer.activeCamera = cam
    let td = MTLTextureDescriptor.texture2DDescriptor(pixelFormat: .bgra8Unorm_srgb, width: s.w, height: s.h, mipmapped: false)
    td.usage = [.renderTarget, .shaderRead, .shaderWrite]; td.storageMode = .shared
    let tex = dev.makeTexture(descriptor: td)!; let output = try RealityRenderer.CameraOutput(.singleProjection(colorTexture: tex))
    var done = false
    for i in 0..<4 { try renderer.updateAndRender(deltaTime: i == 0 ? 0.0 : 0.001, cameraOutput: output, onComplete: { _ in if i == 3 { done = true } }) }
    let limit = Date().addingTimeInterval(20); while !done && Date() < limit { RunLoop.main.run(until: Date().addingTimeInterval(0.05)) }
    var bytes = [UInt8](repeating: 0, count: s.w * s.h * 4)
    tex.getBytes(&bytes, bytesPerRow: s.w * 4, from: MTLRegionMake2D(0, 0, s.w, s.h), mipmapLevel: 0)
    let ctx = CGContext(data: &bytes, width: s.w, height: s.h, bitsPerComponent: 8, bytesPerRow: s.w * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                        bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    let dst = CGImageDestinationCreateWithURL(URL(fileURLWithPath: s.out) as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dst, ctx.makeImage()!, nil); CGImageDestinationFinalize(dst); print("OK \(s.out)")
}
@main struct Main { @MainActor static func main() {
    do { let cfg = try JSONDecoder().decode(Cfg.self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
        var env: EnvironmentResource? = nil
        let exr = URL(fileURLWithPath: cfg.exports + "/Lighting/lax_env_pinebrook_1k.exr")
        if let src = CGImageSourceCreateWithURL(exr as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) { env = try EnvironmentResource(equirectangular: img) }
        let dev = MTLCreateSystemDefaultDevice()!
        for s in cfg.shots { do { try renderShot(cfg, s, env, dev) } catch { print("ERROR \(s.out) \(error)") } }
    } catch { print("ERROR \(error)") } } }
