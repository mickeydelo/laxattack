import SwiftUI
import Observation

enum AppDestination: Equatable {
    case home
    case gameplay
}

enum PlayMode: String, Equatable, Sendable {
    case quickShoot
    case dailyShot
    case challenge
}

enum ChallengeTarget: Equatable, Sendable {
    case score(Int)
    case goals(Int)
    case topCorners(Int)
    case bounceGoals(Int)
    case fiveHoleGoals(Int)
    case dodgeGoals(Int)
}

struct ChallengeDefinition: Identifiable, Equatable, Sendable {
    let id: String
    let title: LocalizedStringResource
    let objective: LocalizedStringResource
    let symbolName: String
    let target: ChallengeTarget
    let recommendedShot: ShotType?
    let medalScores: [Int]

    static let catalog: [ChallengeDefinition] = [
        ChallengeDefinition(
            id: "score_attack",
            title: "SCORE ATTACK",
            objective: "Score 1,200 points in five shots.",
            symbolName: "star.circle.fill",
            target: .score(1_200),
            recommendedShot: nil,
            medalScores: [700, 1_200, 1_900]
        ),
        ChallengeDefinition(
            id: "top_shelf",
            title: "TOP SHELF",
            objective: "Pick two top corners.",
            symbolName: "scope",
            target: .topCorners(2),
            recommendedShot: .overhand,
            medalScores: [1, 2, 3]
        ),
        ChallengeDefinition(
            id: "bounce_house",
            title: "BOUNCE HOUSE",
            objective: "Score two bounce goals.",
            symbolName: "arrow.down.right",
            target: .bounceGoals(2),
            recommendedShot: .bounce,
            medalScores: [1, 2, 3]
        ),
        ChallengeDefinition(
            id: "five_hole",
            title: "FIVE HOLE",
            objective: "Beat the goalie five-hole twice.",
            symbolName: "figure.lacrosse",
            target: .fiveHoleGoals(2),
            recommendedShot: .overhand,
            medalScores: [1, 2, 3]
        ),
        ChallengeDefinition(
            id: "ankle_breaker",
            title: "ANKLE BREAKER",
            objective: "Score twice after a split dodge.",
            symbolName: "arrow.left.and.right",
            target: .dodgeGoals(2),
            recommendedShot: .sidearm,
            medalScores: [1, 2, 3]
        ),
        ChallengeDefinition(
            id: "finisher",
            title: "FINISHER",
            objective: "Score four goals in five shots.",
            symbolName: "flame.fill",
            target: .goals(4),
            recommendedShot: nil,
            medalScores: [2, 4, 5]
        )
    ]

    func progress(for session: GameSession) -> ChallengeProgress {
        let value: Int
        let targetValue: Int

        switch target {
        case .score(let target):
            value = session.score
            targetValue = target
        case .goals(let target):
            value = session.goals
            targetValue = target
        case .topCorners(let target):
            value = session.shotHistory.count {
                $0.outcome == .goal && $0.goalStyle == .topCorner
            }
            targetValue = target
        case .bounceGoals(let target):
            value = session.shotHistory.count {
                $0.outcome == .goal && $0.bounced
            }
            targetValue = target
        case .fiveHoleGoals(let target):
            value = session.shotHistory.count {
                $0.outcome == .goal && $0.goalStyle == .fiveHole
            }
            targetValue = target
        case .dodgeGoals(let target):
            value = session.shotHistory.count {
                $0.outcome == .goal && abs($0.input.dodgeDirection) > 0.5
            }
            targetValue = target
        }

        let medals = medalScores.enumerated().reduce(into: 0) { result, entry in
            if value >= entry.element {
                result = entry.offset + 1
            }
        }
        return ChallengeProgress(value: value, target: targetValue, medals: medals)
    }
}

struct ChallengeProgress: Equatable, Sendable {
    let value: Int
    let target: Int
    let medals: Int

    var fraction: Double {
        guard target > 0 else { return 0 }
        return min(1, Double(value) / Double(target))
    }

    var isComplete: Bool {
        value >= target
    }
}

struct GameRun: Identifiable, Equatable, Sendable {
    let id: String
    let mode: PlayMode
    let title: LocalizedStringResource
    let objective: LocalizedStringResource
    let seed: Int
    let shots: Int
    let challenge: ChallengeDefinition?

    static func quickShoot() -> GameRun {
        GameRun(
            id: "quick",
            mode: .quickShoot,
            title: "QUICK SHOOT",
            objective: "Five shots. Score big and build your streak.",
            seed: 0,
            shots: 5,
            challenge: nil
        )
    }

    static func dailyShot(date: Date = .now, calendar: Calendar = .current) -> GameRun {
        let year = calendar.component(.year, from: date)
        let day = calendar.ordinality(of: .day, in: .year, for: date) ?? 0
        let seed = year * 1_000 + day

        return GameRun(
            id: "daily-\(seed)",
            mode: .dailyShot,
            title: "DAILY SHOT",
            objective: "Everyone gets the same five-shot goalie pattern.",
            seed: seed,
            shots: 5,
            challenge: nil
        )
    }

    static func challenge(_ challenge: ChallengeDefinition) -> GameRun {
        GameRun(
            id: challenge.id,
            mode: .challenge,
            title: challenge.title,
            objective: challenge.objective,
            seed: stableSeed(for: challenge.id),
            shots: 5,
            challenge: challenge
        )
    }

    private static func stableSeed(for value: String) -> Int {
        value.utf8.reduce(17) { partial, byte in
            (partial &* 31 &+ Int(byte)) & 0x7fff_ffff
        }
    }
}

struct RunRecord: Identifiable, Equatable, Sendable {
    let id: UUID
    let runID: String
    let mode: PlayMode
    let seed: Int
    let score: Int
    let completedAt: Date
    let shots: [ShotResult]

    init(run: GameRun, session: GameSession, completedAt: Date = .now) {
        id = UUID()
        runID = run.id
        mode = run.mode
        seed = run.seed
        score = session.score
        self.completedAt = completedAt
        shots = session.shotHistory
    }
}

@MainActor
@Observable
final class AppFlow {
    private(set) var destination: AppDestination = .home
    private(set) var currentRun: GameRun?
    var isPaused = false
    var isShowingSettings = false
    var isShowingChallenges = false

    func start(_ run: GameRun) {
        currentRun = run
        isPaused = false
        isShowingChallenges = false
        destination = .gameplay
    }

    func returnHome() {
        isPaused = false
        destination = .home
        currentRun = nil
    }
}

@MainActor
@Observable
final class PlayerProgress {
    private(set) var bestScore: Int
    private(set) var dailyBest: Int
    private(set) var completedChallengeIDs: Set<String>
    private(set) var lastRun: RunRecord?

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        bestScore = defaults.integer(forKey: "playerBestScore")
        dailyBest = defaults.integer(forKey: "dailyBestScore")
        completedChallengeIDs = Set(defaults.stringArray(forKey: "completedChallengeIDs") ?? [])
        lastRun = nil
    }

    func record(run: GameRun, session: GameSession) {
        lastRun = RunRecord(run: run, session: session)
        if session.score > bestScore {
            bestScore = session.score
            defaults.set(bestScore, forKey: "playerBestScore")
        }

        if run.mode == .dailyShot, session.score > dailyBest {
            dailyBest = session.score
            defaults.set(dailyBest, forKey: "dailyBestScore")
        }

        if let challenge = run.challenge,
           challenge.progress(for: session).isComplete {
            completedChallengeIDs.insert(challenge.id)
            defaults.set(completedChallengeIDs.sorted(), forKey: "completedChallengeIDs")
        }
    }
}
