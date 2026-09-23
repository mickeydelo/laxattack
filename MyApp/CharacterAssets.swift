import Foundation
import RealityKit

enum CharacterRole: String, Sendable {
    case shooter
    case goalie
}

enum CharacterPerformanceState: String, CaseIterable, Sendable {
    case idle
    case cradle
    case aimOverhand = "aim_overhand"
    case aimBounce = "aim_bounce"
    case aimSidearm = "aim_sidearm"
    case splitDodgeLeft = "split_dodge_left"
    case splitDodgeRight = "split_dodge_right"
    case releaseOverhand = "release_overhand"
    case releaseBounce = "release_bounce"
    case releaseSidearm = "release_sidearm"
    case quickStickCatch = "quick_stick_catch"
    case quickStickRelease = "quick_stick_release"
    case celebrate
    case celebrateFistPump = "celebrate_fist_pump"
    case celebrateStickTwirl = "celebrate_stick_twirl"
    case celebrateJumpTuck = "celebrate_jump_tuck"
    case celebrateKneeSlide = "celebrate_knee_slide"
    case celebratePoint = "celebrate_point"
    case celebrateRestrained = "celebrate_restrained"
    case celebrateClutch = "celebrate_clutch"
    case disappointed
    case nearMissReaction = "near_miss_reaction"
    case pipeReaction = "pipe_reaction"
    case saveReaction = "save_reaction"
    case runLoop = "run_loop"
    case goalieReady = "goalie_ready"
    case goalieShuffleLeft = "goalie_shuffle_left"
    case goalieShuffleRight = "goalie_shuffle_right"
    case goalieReadLeft = "goalie_read_left"
    case goalieReadRight = "goalie_read_right"
    case goalieSaveLeft = "goalie_save_left"
    case goalieSaveRight = "goalie_save_right"
    case goalieGoalAgainst = "goalie_goal_against"
    case goalieSaveHighLeft = "goalie_save_high_left"
    case goalieSaveHighRight = "goalie_save_high_right"
    case goalieSaveLowLeft = "goalie_save_low_left"
    case goalieSaveLowRight = "goalie_save_low_right"
    case goalieFiveHoleClose = "goalie_five_hole_close"
    case goalieBodySave = "goalie_body_save"
    case goalieCelebrate = "goalie_celebrate"
    case goalieBigClutchSave = "goalie_big_clutch_save"
}

struct CharacterAssetValidationReport: Sendable {
    let missingSockets: [String]
    let missingAnimations: [String]

    var isValid: Bool { missingSockets.isEmpty && missingAnimations.isEmpty }
}

struct AnimationClipManifest: Decodable, Sendable {
    struct Clip: Decodable, Sendable {
        let name: String
        let start: Int
        let end: Int
        let loop: Bool
        let transitionSeconds: Double
        let releaseSecondsAfterStart: Double?
        let contactLocalFrame: Int?

        enum CodingKeys: String, CodingKey {
            case name, start, end, loop
            case transitionSeconds = "transition_seconds"
            case releaseSecondsAfterStart = "release_seconds_after_start"
            case contactLocalFrame = "contact_local_frame"
        }
    }

    let asset: String
    let fps: Double
    let clips: [Clip]

    func clip(named name: String) -> Clip? {
        clips.first { $0.name == name }
    }

    static func load(named name: String) throws -> AnimationClipManifest {
        guard let url = Bundle.main.url(forResource: name, withExtension: "json") else {
            throw CharacterAssetError.missingManifest(name)
        }
        return try JSONDecoder().decode(AnimationClipManifest.self, from: Data(contentsOf: url))
    }
}

@MainActor
final class TimelineAnimationDriver {
    let entity: Entity
    let manifest: AnimationClipManifest
    private var currentClip: String?

    init(entity: Entity, manifest: AnimationClipManifest) {
        self.entity = entity
        self.manifest = manifest
    }

    func transition(to clipName: String, duration: TimeInterval? = nil, restart: Bool = false) {
        guard (restart || clipName != currentClip),
              let library = entity.components[AnimationLibraryComponent.self],
              let animation = library.animations[clipName] else { return }

        currentClip = clipName
        let transition = duration ?? manifest.clip(named: clipName)?.transitionSeconds ?? 0.12
        entity.playAnimation(animation, transitionDuration: transition)
    }
}

@MainActor
final class CharacterAnimationDriver {
    let timeline: TimelineAnimationDriver

    var entity: Entity { timeline.entity }
    var manifest: AnimationClipManifest { timeline.manifest }

    init(timeline: TimelineAnimationDriver) {
        self.timeline = timeline
    }

    func transition(to state: CharacterPerformanceState, duration: TimeInterval? = nil, restart: Bool = false) {
        timeline.transition(to: state.rawValue, duration: duration, restart: restart)
    }

    func releaseDelay(for state: CharacterPerformanceState) -> TimeInterval {
        manifest.clip(named: state.rawValue)?.releaseSecondsAfterStart ?? 0
    }
}

@MainActor
enum CharacterAssetContract {
    static let shooterAssetName = "lax_shooter"
    static let goalieAssetName = "lax_goalie"
    static let goalAssetName = "lax_goal"
    static let arenaAssetName = "lax_arena_pinebrook"
    static let homeTeammateAssetName = "lax_team_home_7"
    static let awayTeammateAssetName = "lax_team_away_5"
    static let fanAssetNames = ["lax_fan_a", "lax_fan_b", "lax_fan_c"]

    static let requiredSockets = [
        "stick_socket",
        "helmet_socket",
        "effect_socket",
        "pocket_socket",
        "left_hand_socket",
        "right_hand_socket"
    ]

    static func requiredAnimations(for role: CharacterRole) -> [CharacterPerformanceState] {
        switch role {
        case .shooter:
            return [.idle, .cradle, .aimOverhand, .aimBounce, .aimSidearm,
                    .splitDodgeLeft, .splitDodgeRight, .releaseOverhand,
                    .releaseBounce, .releaseSidearm, .quickStickCatch,
                    .quickStickRelease, .celebrate, .disappointed]
        case .goalie:
            return [.goalieReady, .goalieShuffleLeft, .goalieShuffleRight,
                    .goalieReadLeft, .goalieReadRight, .goalieSaveLeft,
                    .goalieSaveRight, .goalieGoalAgainst]
        }
    }

    static func validate(_ entity: Entity, role: CharacterRole) -> CharacterAssetValidationReport {
        let missingSockets = requiredSockets.filter { entity.findEntity(named: $0) == nil }
        let names = Set(entity.components[AnimationLibraryComponent.self]?.animations.map(\.key) ?? [])
        let missingAnimations = requiredAnimations(for: role).map(\.rawValue).filter { !names.contains($0) }
        return CharacterAssetValidationReport(missingSockets: missingSockets, missingAnimations: missingAnimations)
    }

    static func load(named name: String) async throws -> Entity {
        try await Entity(named: name, in: .main)
    }

    static func prepareCharacter(_ entity: Entity, manifestName: String) throws -> CharacterAnimationDriver {
        CharacterAnimationDriver(timeline: try prepareTimeline(entity, manifestName: manifestName))
    }

    static func prepareTimeline(_ entity: Entity, manifestName: String) throws -> TimelineAnimationDriver {
        guard let source = firstAnimation(in: entity) else {
            throw CharacterAssetError.missingSourceAnimation
        }
        let manifest = try AnimationClipManifest.load(named: manifestName)
        var animations: [String: AnimationResource] = [:]
        for clip in manifest.clips {
            let view = AnimationView(
                source: source.definition,
                name: clip.name,
                repeatMode: clip.loop ? .repeat : .none,
                trimStart: Double(clip.start) / manifest.fps,
                trimEnd: Double(clip.end) / manifest.fps
            )
            animations[clip.name] = try AnimationResource.generate(with: view)
        }
        entity.components.set(AnimationLibraryComponent(animations: animations))
        return TimelineAnimationDriver(entity: entity, manifest: manifest)
    }

    private static func firstAnimation(in entity: Entity) -> AnimationResource? {
        if let animation = entity.availableAnimations.first { return animation }
        for child in entity.children {
            if let animation = firstAnimation(in: child) { return animation }
        }
        return nil
    }
}

enum CharacterAssetError: Error {
    case missingSourceAnimation
    case missingManifest(String)
}
