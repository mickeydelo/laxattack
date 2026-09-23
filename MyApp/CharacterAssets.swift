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
    case disappointed
    case goalieReady = "goalie_ready"
    case goalieShuffleLeft = "goalie_shuffle_left"
    case goalieShuffleRight = "goalie_shuffle_right"
    case goalieReadLeft = "goalie_read_left"
    case goalieReadRight = "goalie_read_right"
    case goalieSaveLeft = "goalie_save_left"
    case goalieSaveRight = "goalie_save_right"
    case goalieGoalAgainst = "goalie_goal_against"
}

struct CharacterAssetValidationReport: Sendable {
    let missingSockets: [String]
    let missingAnimations: [String]

    var isValid: Bool {
        missingSockets.isEmpty && missingAnimations.isEmpty
    }
}

private struct CharacterClipDefinition {
    let state: CharacterPerformanceState
    let startFrame: Int
    let endFrame: Int
    let loops: Bool
}

@MainActor
final class CharacterAnimationDriver {
    let entity: Entity
    private var currentState: CharacterPerformanceState?

    init(entity: Entity) {
        self.entity = entity
    }

    func transition(to state: CharacterPerformanceState, duration: TimeInterval = 0.12) {
        guard state != currentState,
              let library = entity.components[AnimationLibraryComponent.self],
              let animation = library.animations[state.rawValue] else { return }

        currentState = state
        entity.playAnimation(animation, transitionDuration: duration)
    }
}

@MainActor
enum CharacterAssetContract {
    static let framesPerSecond = 30.0
    static let overhandReleaseDelay = 14.0 / framesPerSecond
    static let shooterAssetName = "lax_shooter"
    static let goalieAssetName = "lax_goalie"

    static let requiredSockets = [
        "stick_socket",
        "helmet_socket",
        "effect_socket"
    ]

    static func requiredAnimations(for role: CharacterRole) -> [CharacterPerformanceState] {
        switch role {
        case .shooter:
            [
                .idle,
                .cradle,
                .aimOverhand,
                .aimBounce,
                .aimSidearm,
                .splitDodgeLeft,
                .splitDodgeRight,
                .releaseOverhand,
                .releaseBounce,
                .releaseSidearm,
                .quickStickCatch,
                .quickStickRelease,
                .celebrate,
                .disappointed
            ]
        case .goalie:
            [
                .goalieReady,
                .goalieShuffleLeft,
                .goalieShuffleRight,
                .goalieReadLeft,
                .goalieReadRight,
                .goalieSaveLeft,
                .goalieSaveRight,
                .goalieGoalAgainst
            ]
        }
    }

    static func validate(_ entity: Entity, role: CharacterRole) -> CharacterAssetValidationReport {
        let missingSockets = requiredSockets.filter {
            entity.findEntity(named: $0) == nil
        }

        let animationNames: Set<String>
        if let library = entity.components[AnimationLibraryComponent.self] {
            animationNames = Set(library.animations.map(\.key))
        } else {
            animationNames = []
        }
        let missingAnimations = requiredAnimations(for: role)
            .map(\.rawValue)
            .filter { !animationNames.contains($0) }

        return CharacterAssetValidationReport(
            missingSockets: missingSockets,
            missingAnimations: missingAnimations
        )
    }

    static func load(named name: String) async throws -> Entity {
        try await Entity(named: name, in: .main)
    }

    static func prepareShooter(_ entity: Entity) throws -> CharacterAnimationDriver {
        guard let source = firstAnimation(in: entity) else {
            throw CharacterAssetError.missingSourceAnimation
        }

        let clips = [
            CharacterClipDefinition(state: .idle, startFrame: 0, endFrame: 48, loops: true),
            CharacterClipDefinition(state: .cradle, startFrame: 60, endFrame: 88, loops: true),
            CharacterClipDefinition(state: .releaseOverhand, startFrame: 100, endFrame: 133, loops: false),
            CharacterClipDefinition(state: .celebrate, startFrame: 150, endFrame: 186, loops: false)
        ]

        var animations: [String: AnimationResource] = [:]
        for clip in clips {
            let view = AnimationView(
                source: source.definition,
                name: clip.state.rawValue,
                repeatMode: clip.loops ? .repeat : .none,
                trimStart: Double(clip.startFrame) / framesPerSecond,
                trimEnd: Double(clip.endFrame) / framesPerSecond
            )
            animations[clip.state.rawValue] = try AnimationResource.generate(with: view)
        }

        entity.components.set(AnimationLibraryComponent(animations: animations))
        return CharacterAnimationDriver(entity: entity)
    }

    private static func firstAnimation(in entity: Entity) -> AnimationResource? {
        if let animation = entity.availableAnimations.first {
            return animation
        }
        for child in entity.children {
            if let animation = firstAnimation(in: child) {
                return animation
            }
        }
        return nil
    }
}

enum CharacterAssetError: Error {
    case missingSourceAnimation
}
