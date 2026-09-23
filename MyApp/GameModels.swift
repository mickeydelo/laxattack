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
        Double(min(max((power - 0.65) / 1.55, 0), 1))
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

        let travelPower = smoothStep(min(upwardTravel / 240, 1))
        let speedPower = smoothStep(min(upwardSpeed / 2_000, 1))
        let power = clamp(0.72 + travelPower * 1.02 + speedPower * 0.38, 0.72, 2.08)

        // End-position carries most of the aim. Velocity adds only a small amount,
        // preventing a tiny wrist hook at release from throwing the shot wide.
        let travelAim = lateralTravel / 178
        let speedAim = lateralSpeed / 4_800
        let rawDirection = clamp(travelAim + speedAim * 0.08, -1, 1)
        let direction = abs(rawDirection) < 0.055
            ? 0
            : rawDirection * (0.76 + abs(rawDirection) * 0.24)

        return ShotControlSample(
            direction: direction,
            power: power,
            releaseSpeed: upwardSpeed
        )
    }

    private static func clamp(_ value: Float, _ minimum: Float, _ maximum: Float) -> Float {
        min(max(value, minimum), maximum)
    }

    private static func smoothStep(_ value: Float) -> Float {
        value * value * (3 - 2 * value)
    }
}

struct ShotInput: Equatable, Sendable {
    let horizontal: Float
    let power: Float
    let releaseSpeed: Float
    let type: ShotType
    let timingQuality: Float?
    let dodgeDirection: Float
    let wasOnFire: Bool
    let goaliePositionAtRelease: Float
    let physicsVersion: Int

    var releaseQuality: Float {
        if type == .quickStick {
            return timingQuality ?? 0
        }
        let speedScore = max(0, 1 - abs(releaseSpeed - 1_500) / 900)
        let controlScore = max(0, 1 - abs(power - 1.65) / 0.85)
        return min(1, speedScore * 0.72 + controlScore * 0.28)
    }

    var isPerfectRelease: Bool {
        releaseQuality >= 0.82
    }
}

enum ShotType: String, CaseIterable, Equatable, Sendable, Identifiable {
    case overhand
    case bounce
    case sidearm
    case quickStick

    var id: Self { self }

    static let selectableCases: [ShotType] = [.overhand, .bounce, .sidearm]

    var title: String {
        switch self {
        case .overhand: "OVERHAND"
        case .bounce: "BOUNCE"
        case .sidearm: "SIDEARM"
        case .quickStick: "QUICK STICK"
        }
    }

    var symbolName: String {
        switch self {
        case .overhand: "arrow.up.forward"
        case .bounce: "arrow.down.right"
        case .sidearm: "arrow.turn.up.right"
        case .quickStick: "bolt.fill"
        }
    }

    var releasePrompt: LocalizedStringResource {
        switch self {
        case .overhand: "RELEASE OVERHAND"
        case .bounce: "RELEASE BOUNCE SHOT"
        case .sidearm: "RELEASE SIDEARM"
        case .quickStick: "TAP TO QUICK STICK"
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

enum HotZone: Int, CaseIterable, Equatable, Sendable {
    case topLeft
    case topRight
    case lowLeft
    case lowRight
    case fiveHole

    var title: LocalizedStringResource {
        switch self {
        case .topLeft: "TOP LEFT"
        case .topRight: "TOP RIGHT"
        case .lowLeft: "LOW LEFT"
        case .lowRight: "LOW RIGHT"
        case .fiveHole: "FIVE HOLE"
        }
    }

    var targetPosition: SIMD3<Float> {
        switch self {
        case .topLeft: [-0.68, 1.58, -5.62]
        case .topRight: [0.68, 1.58, -5.62]
        case .lowLeft: [-0.67, 0.5, -5.62]
        case .lowRight: [0.67, 0.5, -5.62]
        case .fiveHole: [0, 0.38, -5.62]
        }
    }

    func contains(_ position: SIMD3<Float>) -> Bool {
        let target = targetPosition
        let horizontalRadius: Float = self == .fiveHole ? 0.3 : 0.38
        let verticalRadius: Float = self == .fiveHole ? 0.26 : 0.34
        let x = (position.x - target.x) / horizontalRadius
        let y = (position.y - target.y) / verticalRadius
        return x * x + y * y <= 1
    }
}

struct ShotResult: Equatable, Sendable {
    let input: ShotInput
    let outcome: ShotOutcome
    let points: Int
    let combo: Int
    let hitPipe: Bool
    let bounced: Bool
    let goalStyle: GoalStyle?
    let hitHotZone: Bool
    let wasClutch: Bool
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
    case quickStickGoal
    case dodgeGoal
    case heatGoal
    case perfectRelease
    case calledShot
    case clutchGoal
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
        case .quickStickGoal:
            "QUICK STICK!"
        case .dodgeGoal:
            "ANKLES BROKEN!"
        case .heatGoal:
            "ON FIRE!"
        case .perfectRelease:
            "PERFECT RELEASE!"
        case .calledShot:
            "CALLED SHOT!"
        case .clutchGoal:
            "CLUTCH ×2!"
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
        case .goal, .topCorner, .lowCorner, .fiveHole, .bounceGoal, .sidearmGoal, .quickStickGoal, .dodgeGoal, .heatGoal, .perfectRelease, .calledShot, .clutchGoal:
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
    private(set) var bestCombo = 0
    private(set) var shotsRemaining = 5
    private(set) var totalShots = 5
    private(set) var stopsRemaining = 3
    private(set) var maximumStops = 3
    private(set) var secondsRemaining: Double = 0
    private(set) var runSeed = 0
    private(set) var feedback: ShotFeedback = .ready
    private(set) var isAwaitingResult = false
    private(set) var shotHistory: [ShotResult] = []
    private(set) var selectedShotType: ShotType = .overhand
    private(set) var quickStickStartedAt: Date?
    private(set) var activeHotZone: HotZone = .topLeft
    private(set) var runRule: RunRule = .shotLimit(5)

    private var pendingInput: ShotInput?
    private var pendingHitPipe = false
    private var pendingBounced = false
    private var pendingClutch = false

    var isRoundComplete: Bool {
        guard !isAwaitingResult else { return false }
        switch runRule {
        case .survival:
            return stopsRemaining == 0
        case .timed:
            return secondsRemaining <= 0
        case .shotLimit:
            return shotsRemaining == 0
        }
    }

    var goals: Int {
        shotHistory.lazy.filter { $0.outcome == .goal }.count
    }

    var accuracy: Double {
        guard !shotHistory.isEmpty else { return 0 }
        return Double(goals) / Double(shotHistory.count)
    }

    var difficultyLevel: Int {
        min(5, max(0, combo))
    }

    var isOnFire: Bool {
        combo >= 3
    }

    var isQuickStickChallenge: Bool {
        quickStickStartedAt != nil && !isAwaitingResult && !isRoundComplete
    }

    var isClutchShot: Bool {
        guard case .shotLimit = runRule else { return false }
        return shotsRemaining == 1 && !isAwaitingResult && !isRoundComplete
    }

    func quickStickPhase(at date: Date = .now) -> Double {
        guard let quickStickStartedAt else { return 0 }
        let elapsed = max(0, date.timeIntervalSince(quickStickStartedAt))
        return elapsed.truncatingRemainder(dividingBy: 1.6) / 1.6
    }

    func quickStickQuality(at date: Date = .now) -> Double {
        let distance = abs(quickStickPhase(at: date) - 0.5)
        return max(0, 1 - distance / 0.28)
    }

    func beginShot(input: ShotInput) -> Bool {
        guard !isRoundComplete, !isAwaitingResult else { return false }
        if case .shotLimit = runRule {
            pendingClutch = shotsRemaining == 1
            shotsRemaining -= 1
        } else {
            pendingClutch = false
        }
        isAwaitingResult = true
        pendingInput = input
        pendingHitPipe = false
        pendingBounced = false
        quickStickStartedAt = nil
        feedback = .shooting
        return true
    }

    func selectShotType(_ type: ShotType) {
        guard !isAwaitingResult, !isRoundComplete else { return }
        selectedShotType = type
    }

    func registerGoal(style: GoalStyle, hitHotZone: Bool) -> Bool {
        guard isAwaitingResult else { return false }
        combo += 1
        bestCombo = max(bestCombo, combo)

        let pipeBonus = pendingHitPipe ? 75 : 0
        let bounceBonus = pendingBounced ? 75 : 0
        let placementBonus: Int
        switch style {
        case .topCorner: placementBonus = 100
        case .lowCorner: placementBonus = 75
        case .fiveHole: placementBonus = 125
        case .standard: placementBonus = 0
        }
        let releaseBonus: Int
        switch pendingInput?.type {
        case .sidearm: releaseBonus = 50
        case .quickStick: releaseBonus = 150
        default: releaseBonus = 0
        }
        let dodgeBonus = abs(pendingInput?.dodgeDirection ?? 0) > 0.5 ? 100 : 0
        let heatBonus = pendingInput?.wasOnFire == true ? 200 : 0
        let perfectBonus = pendingInput?.isPerfectRelease == true ? 125 : 0
        let hotZoneBonus = hitHotZone ? 200 : 0
        let earnedPoints = 100 * combo + pipeBonus + bounceBonus + placementBonus + releaseBonus + dodgeBonus + heatBonus + perfectBonus + hotZoneBonus
        let points = pendingClutch ? earnedPoints * 2 : earnedPoints

        score += points
        if pendingClutch {
            feedback = .clutchGoal
        } else if hitHotZone {
            feedback = .calledShot
        } else if pendingInput?.isPerfectRelease == true {
            feedback = .perfectRelease
        } else if pendingInput?.wasOnFire == true {
            feedback = .heatGoal
        } else if pendingBounced {
            feedback = .bounceGoal
        } else if pendingInput?.type == .quickStick {
            feedback = .quickStickGoal
        } else if abs(pendingInput?.dodgeDirection ?? 0) > 0.5 {
            feedback = .dodgeGoal
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

        finishShot(outcome: .goal, points: points, goalStyle: style, hitHotZone: hitHotZone)
        return true
    }

    func registerSave() -> Bool {
        guard isAwaitingResult else { return false }
        combo = 0
        bestCombo = 0
        feedback = .save
        registerStop()
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
        registerStop()
        finishShot(outcome: .miss, points: 0)
        return true
    }

    func startNewRound(rule: RunRule = .shotLimit(5), seed: Int = 0, preferredShot: ShotType? = nil) {
        bestScore = max(bestScore, score)
        score = 0
        combo = 0
        runRule = rule
        switch rule {
        case .survival(let maxStops):
            maximumStops = max(1, maxStops)
            stopsRemaining = maximumStops
            totalShots = 0
            shotsRemaining = 0
            secondsRemaining = 0
        case .timed(let seconds):
            maximumStops = 0
            stopsRemaining = 0
            totalShots = 0
            shotsRemaining = 0
            secondsRemaining = Double(max(1, seconds))
        case .shotLimit(let shots):
            totalShots = max(1, shots)
            shotsRemaining = totalShots
            maximumStops = 0
            stopsRemaining = 0
            secondsRemaining = 0
        }
        runSeed = seed
        feedback = .ready
        isAwaitingResult = false
        shotHistory = []
        selectedShotType = preferredShot ?? .overhand
        quickStickStartedAt = nil
        pendingInput = nil
        pendingHitPipe = false
        pendingBounced = false
        pendingClutch = false
        chooseNextHotZone()
    }

    func prepareNextShot() {
        guard !isRoundComplete else {
            bestScore = max(bestScore, score)
            return
        }
        feedback = .ready
        if shotHistory.count > 0, shotHistory.count % 5 == 2 {
            quickStickStartedAt = .now
        }
        chooseNextHotZone()
    }

    private func finishShot(
        outcome: ShotOutcome,
        points: Int,
        goalStyle: GoalStyle? = nil,
        hitHotZone: Bool = false
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
                goalStyle: goalStyle,
                hitHotZone: hitHotZone,
                wasClutch: pendingClutch
            )
        )

        self.pendingInput = nil
        isAwaitingResult = false

        if isRoundComplete {
            bestScore = max(bestScore, score)
        }
    }

    private func chooseNextHotZone() {
        let zones = HotZone.allCases
        let seed = UInt(bitPattern: runSeed)
        let sequence = seed &+ UInt(shotHistory.count &* 3)
        activeHotZone = zones[Int(sequence % UInt(zones.count))]
    }

    func advanceClock(by interval: Double) {
        guard case .timed = runRule, !isRoundComplete else { return }
        secondsRemaining = max(0, secondsRemaining - interval)
        if secondsRemaining == 0 {
            quickStickStartedAt = nil
            bestScore = max(bestScore, score)
        }
    }

    private func registerStop() {
        guard case .survival = runRule else { return }
        stopsRemaining = max(0, stopsRemaining - 1)
    }
}

@MainActor
final class GameFeedbackPlayer {
    func playRelease(type: ShotType) {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        switch type {
        case .overhand:
            UIImpactFeedbackGenerator(style: .medium).impactOccurred(intensity: 0.78)
        case .bounce:
            UIImpactFeedbackGenerator(style: .soft).impactOccurred(intensity: 0.62)
        case .sidearm:
            UIImpactFeedbackGenerator(style: .rigid).impactOccurred(intensity: 0.82)
        case .quickStick:
            UIImpactFeedbackGenerator(style: .heavy).impactOccurred(intensity: 0.92)
        }
        #endif
    }

    func playGoal() {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        #endif
    }

    func playPerfectRelease() {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        let generator = UIImpactFeedbackGenerator(style: .rigid)
        generator.prepare()
        generator.impactOccurred(intensity: 0.55)
        #endif
    }

    func playSave() {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        UINotificationFeedbackGenerator().notificationOccurred(.warning)
        #endif
    }

    func playPipe() {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        UIImpactFeedbackGenerator(style: .rigid).impactOccurred(intensity: 1)
        #endif
    }

    func playMiss() {
        #if os(iOS)
        guard isHapticsEnabled else { return }
        UIImpactFeedbackGenerator(style: .light).impactOccurred(intensity: 0.45)
        #endif
    }

    private var isHapticsEnabled: Bool {
        let defaults = UserDefaults.standard
        guard defaults.object(forKey: "hapticsEnabled") != nil else { return true }
        return defaults.bool(forKey: "hapticsEnabled")
    }
}
