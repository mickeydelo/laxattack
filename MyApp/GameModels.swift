import SwiftUI
import Observation

#if os(iOS)
import UIKit
#endif

struct ShotInput: Equatable, Sendable {
    let horizontal: Float
    let power: Float
}

enum ShotOutcome: Equatable, Sendable {
    case goal
    case save
    case miss
}

enum GoalStyle: Equatable, Sendable {
    case standard
    case topCorner
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
    case bounceGoal
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
        case .bounceGoal:
            "BOUNCE GOAL!"
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
        case .goal, .topCorner, .bounceGoal:
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

    func registerGoal(style: GoalStyle) -> Bool {
        guard isAwaitingResult else { return false }
        combo += 1

        let pipeBonus = pendingHitPipe ? 75 : 0
        let bounceBonus = pendingBounced ? 75 : 0
        let placementBonus = style == .topCorner ? 100 : 0
        let points = 100 * combo + pipeBonus + bounceBonus + placementBonus

        score += points
        if pendingBounced {
            feedback = .bounceGoal
        } else if style == .topCorner {
            feedback = .topCorner
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
    func playRelease() {
        #if os(iOS)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred(intensity: 0.75)
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
