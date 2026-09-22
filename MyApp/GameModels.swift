import SwiftUI
import Observation

#if os(iOS)
import UIKit
#endif

struct ShotControlSample: Equatable, Sendable {
    let direction: Float
    let power: Float
    let releaseSpeed: Float

    var normalizedPower: Double {
        Double((power - 0.65) / 1.55)
    }
}

enum ShotControlModel {
    static func sample(
        translation: CGSize,
        velocity: CGSize
    ) -> ShotControlSample {
        let upwardTravel = max(0, Float(-translation.height))
        let upwardSpeed = max(0, Float(-velocity.height))
        let lateralTravel = Float(translation.width)
        let lateralSpeed = Float(velocity.width)

        let travelPower = min(upwardTravel / 220, 1)
        let speedPower = min(upwardSpeed / 1_800, 1)
        let power = clamp(0.65 + travelPower * 1.1 + speedPower * 0.45, 0.65, 2.2)

        let travelAim = lateralTravel / 115
        let speedAim = lateralSpeed / 3_000
        let direction = clamp(travelAim + speedAim * 0.22, -1, 1)

        return ShotControlSample(
            direction: direction,
            power: power,
            releaseSpeed: upwardSpeed
        )
    }

    private static func clamp(_ value: Float, _ minimum: Float, _ maximum: Float) -> Float {
        min(max(value, minimum), maximum)
    }
}

struct ShotInput: Equatable, Sendable {
    let horizontal: Float
    let power: Float
    let releaseSpeed: Float
    let type: ShotType
}

enum ShotType: String, CaseIterable, Equatable, Sendable, Identifiable {
    case overhand
    case bounce
    case sidearm

    var id: Self { self }

    var title: LocalizedStringResource {
        switch self {
        case .overhand: "OVERHAND"
        case .bounce: "BOUNCE"
        case .sidearm: "SIDEARM"
        }
    }

    var symbolName: String {
        switch self {
        case .overhand: "arrow.up.forward"
        case .bounce: "arrow.down.forward.and.arrow.up"
        case .sidearm: "arrow.turn.up.right"
        }
    }

    var releasePrompt: LocalizedStringResource {
        switch self {
        case .overhand: "RELEASE OVERHAND"
        case .bounce: "RELEASE BOUNCE SHOT"
        case .sidearm: "RELEASE SIDEARM"
        }
    }
}

enum ShotOutcome: Equatable, Sendable {
    case goal
    case save
    case miss
}

enum GoalStyle: Equatable, Sendable {
    case standard
    case topCorner
    case lowCorner
    case fiveHole
}

struct ShotResult: Equatable, Sendable {
    let input: ShotInput
    let outcome: ShotOutcome
    let points: Int
    let combo: Int
    let hitPipe: Bool
    let bounced: Bool
    let goalStyle: GoalStyle?
}

enum ShotFeedback: Equatable {
    case ready
    case shooting
    case goal
    case topCorner
    case lowCorner
    case fiveHole
    case bounceGoal
    case sidearmGoal
    case save
    case pipe
    case miss

    var title: LocalizedStringResource {
        switch self {
        case .ready:
            "READY"
        case .shooting:
            ""
        case .goal:
            "GOAL!"
        case .topCorner:
            "TOP CORNER!"
        case .lowCorner:
            "LOW CORNER!"
        case .fiveHole:
            "FIVE HOLE!"
        case .bounceGoal:
            "BOUNCE GOAL!"
        case .sidearmGoal:
            "SIDEARM RIP!"
        case .save:
            "SAVE!"
        case .pipe:
            "PIPE!"
        case .miss:
            "MISS"
        }
    }

    var color: Color {
        switch self {
        case .goal, .topCorner, .lowCorner, .fiveHole, .bounceGoal, .sidearmGoal:
            .yellow
        case .save:
            .cyan
        case .pipe:
            .orange
        case .miss:
            .white
        case .ready, .shooting:
            .clear
        }
    }
}

@MainActor
@Observable
final class GameSession {
    private(set) var score = 0
    private(set) var bestScore = 0
    private(set) var combo = 0
    private(set) var shotsRemaining = 5
    private(set) var feedback: ShotFeedback = .ready
    private(set) var isAwaitingResult = false
    private(set) var shotHistory: [ShotResult] = []
    private(set) var selectedShotType: ShotType = .overhand

    private var pendingInput: ShotInput?
    private var pendingHitPipe = false
    private var pendingBounced = false

    var isRoundComplete: Bool {
        shotsRemaining == 0 && !isAwaitingResult
    }

    var goals: Int {
        shotHistory.lazy.filter { $0.outcome == .goal }.count
    }

    var accuracy: Double {
        guard !shotHistory.isEmpty else { return 0 }
        return Double(goals) / Double(shotHistory.count)
    }

    var difficultyLevel: Int {
        min(3, max(0, combo / 2))
    }

    func beginShot(input: ShotInput) -> Bool {
        guard shotsRemaining > 0, !isAwaitingResult else { return false }
        shotsRemaining -= 1
        isAwaitingResult = true
        pendingInput = input
        pendingHitPipe = false
        pendingBounced = false
        feedback = .shooting
        return true
    }

    func selectShotType(_ type: ShotType) {
        guard !isAwaitingResult, !isRoundComplete else { return }
        selectedShotType = type
    }

    func registerGoal(style: GoalStyle) -> Bool {
        guard isAwaitingResult else { return false }
        combo += 1

        let pipeBonus = pendingHitPipe ? 75 : 0
        let bounceBonus = pendingBounced ? 75 : 0
        let placementBonus: Int
        switch style {
        case .topCorner: placementBonus = 100
        case .lowCorner: placementBonus = 75
        case .fiveHole: placementBonus = 125
        case .standard: placementBonus = 0
        }
        let releaseBonus = pendingInput?.type == .sidearm ? 50 : 0
        let points = 100 * combo + pipeBonus + bounceBonus + placementBonus + releaseBonus

        score += points
        if pendingBounced {
            feedback = .bounceGoal
        } else if style == .topCorner {
            feedback = .topCorner
        } else if style == .lowCorner {
            feedback = .lowCorner
        } else if style == .fiveHole {
            feedback = .fiveHole
        } else if pendingInput?.type == .sidearm {
            feedback = .sidearmGoal
        } else {
            feedback = .goal
        }

        finishShot(outcome: .goal, points: points, goalStyle: style)
        return true
    }

    func registerSave() -> Bool {
        guard isAwaitingResult else { return false }
        combo = 0
        feedback = .save
        finishShot(outcome: .save, points: 0)
        return true
    }

    func registerPipe() {
        guard isAwaitingResult else { return }
        pendingHitPipe = true
        feedback = .pipe
    }

    func registerBounce() {
        guard isAwaitingResult else { return }
        pendingBounced = true
    }

    func registerMiss() -> Bool {
        guard isAwaitingResult else { return false }
        combo = 0
        feedback = .miss
        finishShot(outcome: .miss, points: 0)
        return true
    }

    func startNewRound() {
        bestScore = max(bestScore, score)
        score = 0
        combo = 0
        shotsRemaining = 5
        feedback = .ready
        isAwaitingResult = false
        shotHistory = []
        selectedShotType = .overhand
        pendingInput = nil
        pendingHitPipe = false
        pendingBounced = false
    }

    func prepareNextShot() {
        guard !isRoundComplete else {
            bestScore = max(bestScore, score)
            return
        }
        feedback = .ready
    }

    private func finishShot(
        outcome: ShotOutcome,
        points: Int,
        goalStyle: GoalStyle? = nil
    ) {
        guard let pendingInput else { return }

        shotHistory.append(
            ShotResult(
                input: pendingInput,
                outcome: outcome,
                points: points,
                combo: combo,
                hitPipe: pendingHitPipe,
                bounced: pendingBounced,
                goalStyle: goalStyle
            )
        )

        self.pendingInput = nil
        isAwaitingResult = false

        if isRoundComplete {
            bestScore = max(bestScore, score)
        }
    }
}

@MainActor
final class GameFeedbackPlayer {
    func playRelease(type: ShotType) {
        #if os(iOS)
        switch type {
        case .overhand:
            UIImpactFeedbackGenerator(style: .medium).impactOccurred(intensity: 0.78)
        case .bounce:
            UIImpactFeedbackGenerator(style: .soft).impactOccurred(intensity: 0.62)
        case .sidearm:
            UIImpactFeedbackGenerator(style: .rigid).impactOccurred(intensity: 0.82)
        }
        #endif
    }

    func playGoal() {
        #if os(iOS)
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
    }

    func playSave() {
        #if os(iOS)
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
        #endif
    }

    func playPipe() {
        #if os(iOS)
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred(intensity: 1)
        #endif
    }

    func playMiss() {
        #if os(iOS)
        UIImpactFeedbackGenerator(style: .light).impactOccurred(intensity: 0.45)
        #endif
    }
}
