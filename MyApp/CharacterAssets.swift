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

@MainActor
enum CharacterAssetContract {
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
}
