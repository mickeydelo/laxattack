import SwiftUI
import RealityKit

struct ContentView: View {
    @State private var session = GameSession()
    @State private var gameScene = PocketLaxScene()
    @State private var aimSample: ShotControlSample?

    var body: some View {
        ZStack {
            RealityView { content in
                content.camera = .virtual
                gameScene.build(in: &content, session: session)
            }
            .ignoresSafeArea()
            .contentShape(Rectangle())

            GameHUD(
                score: session.score,
                bestScore: session.bestScore,
                combo: session.combo,
                shotsRemaining: session.shotsRemaining,
                goals: session.goals,
                accuracy: session.accuracy,
                feedback: session.feedback,
                goalieLevel: session.difficultyLevel,
                aimPower: aimSample?.normalizedPower ?? 0,
                selectedShotType: session.selectedShotType,
                canSelectShot: !session.isAwaitingResult,
                isQuickStickChallenge: session.isQuickStickChallenge,
                isRoundComplete: session.isRoundComplete,
                onSelectShotType: { type in
                    session.selectShotType(type)
                    gameScene.setShotType(type)
                },
                quickStickPhase: { date in
                    session.quickStickPhase(at: date)
                },
                onQuickStick: { date in
                    gameScene.shootQuickStick(
                        quality: session.quickStickQuality(at: date),
                        session: session
                    )
                },
                onPlayAgain: {
                    session.startNewRound()
                    gameScene.prepareForNewRound()
                }
            )
        }
        .contentShape(Rectangle())
        .gesture(shotGesture)
        .onDisappear {
            gameScene.stop()
        }
    }

    private var shotGesture: some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard !session.isAwaitingResult, !session.isRoundComplete else { return }
                let sample = ShotControlModel.sample(
                    translation: value.translation,
                    velocity: value.velocity
                )
                aimSample = sample
                gameScene.updateAim(using: sample, shotType: session.selectedShotType)
            }
            .onEnded { value in
                let sample = ShotControlModel.sample(
                    translation: value.translation,
                    velocity: value.velocity
                )
                gameScene.hideAimGuide()
                aimSample = nil
                guard value.translation.height < -24 else { return }
                gameScene.shoot(
                    using: sample,
                    shotType: session.selectedShotType,
                    session: session
                )
            }
    }
}

struct GameHUD: View {
    let score: Int
    let bestScore: Int
    let combo: Int
    let shotsRemaining: Int
    let goals: Int
    let accuracy: Double
    let feedback: ShotFeedback
    let goalieLevel: Int
    let aimPower: Double
    let selectedShotType: ShotType
    let canSelectShot: Bool
    let isQuickStickChallenge: Bool
    let isRoundComplete: Bool
    let onSelectShotType: (ShotType) -> Void
    let quickStickPhase: (Date) -> Double
    let onQuickStick: (Date) -> Void
    let onPlayAgain: () -> Void

    var body: some View {
        VStack(spacing: 10) {
            GameHeader(score: score, bestScore: bestScore)

            HStack {
                ShotCounter(shotsRemaining: shotsRemaining)
                Spacer()
                if goalieLevel > 0 {
                    Text("GOALIE +(goalieLevel)")
                        .font(.caption.bold())
                        .foregroundStyle(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(.blue.opacity(0.75), in: Capsule())
                }
            }

            ShotCallout(feedback: feedback, combo: combo)

            Spacer()

            if isRoundComplete {
                RoundCompleteCard(
                    score: score,
                    goals: goals,
                    accuracy: accuracy,
                    onPlayAgain: onPlayAgain
                )
            } else if isQuickStickChallenge {
                QuickStickMeter(
                    phase: quickStickPhase,
                    onQuickStick: onQuickStick
                )
            } else {
                ShotTypePicker(
                    selection: selectedShotType,
                    isEnabled: canSelectShot,
                    onSelect: onSelectShotType
                )
                AimPrompt(power: aimPower, shotType: selectedShotType)
            }
        }
        .padding(.horizontal, 18)
        .padding(.top, 10)
        .padding(.bottom, 28)
    }
}

struct ShotTypePicker: View {
    let selection: ShotType
    let isEnabled: Bool
    let onSelect: (ShotType) -> Void

    var body: some View {
        HStack(spacing: 8) {
            ForEach(ShotType.selectableCases) { type in
                Button {
                    onSelect(type)
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: type.symbolName)
                            .font(.headline.bold())
                        Text(type.title)
                            .font(.caption2.bold())
                    }
                    .foregroundStyle(selection == type ? .black : .white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 9)
                    .background(
                        selection == type ? .yellow : .black.opacity(0.62),
                        in: RoundedRectangle(cornerRadius: 14)
                    )
                }
                .buttonStyle(.plain)
                .disabled(!isEnabled)
            }
        }
        .opacity(isEnabled ? 1 : 0.55)
    }
}

struct QuickStickMeter: View {
    let phase: (Date) -> Double
    let onQuickStick: (Date) -> Void

    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 30)) { context in
            let currentPhase = phase(context.date)

            Button {
                onQuickStick(context.date)
            } label: {
                VStack(spacing: 9) {
                    HStack {
                        Image(systemName: "bolt.fill")
                        Text("QUICK STICK")
                        Image(systemName: "bolt.fill")
                    }
                    .font(.headline.bold())
                    .foregroundStyle(.yellow)

                    GeometryReader { proxy in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(.black.opacity(0.68))
                            Capsule()
                                .fill(.green.opacity(0.72))
                                .frame(width: proxy.size.width * 0.18)
                                .position(x: proxy.size.width * 0.5, y: proxy.size.height * 0.5)
                            Circle()
                                .fill(.white)
                                .shadow(color: .cyan, radius: 5)
                                .frame(width: 18, height: 18)
                                .offset(x: (proxy.size.width - 18) * currentPhase)
                        }
                    }
                    .frame(height: 20)

                    Text("TAP AS THE PASS HITS THE POCKET")
                        .font(.caption.bold())
                        .foregroundStyle(.white)
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 13)
                .background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 18))
            }
            .buttonStyle(.plain)
        }
    }
}

struct GameHeader: View {
    let score: Int
    let bestScore: Int

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 0) {
                Text("LAX")
                    .foregroundStyle(.white)
                Text("ATTACK")
                    .foregroundStyle(.cyan)
            }
            .font(.headline.bold())
            .tracking(1.5)
            .padding(.horizontal, 14)
            .padding(.vertical, 9)
            .background(.black.opacity(0.62), in: RoundedRectangle(cornerRadius: 16))

            Spacer()

            HStack(spacing: 16) {
                HeaderStat(title: "BEST", value: bestScore)
                HeaderStat(title: "SCORE", value: score)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(.black.opacity(0.62), in: RoundedRectangle(cornerRadius: 16))
        }
    }
}

struct HeaderStat: View {
    let title: LocalizedStringResource
    let value: Int

    var body: some View {
        VStack(spacing: 1) {
            Text(title)
                .font(.caption2.bold())
                .foregroundStyle(.white.opacity(0.72))
            Text(value, format: .number)
                .font(.title3.bold())
                .foregroundStyle(.white)
                .contentTransition(.numericText())
        }
    }
}

struct ShotCounter: View {
    let shotsRemaining: Int

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0..<5, id: \.self) { index in
                Circle()
                    .fill(index < shotsRemaining ? .white : .white.opacity(0.2))
                    .frame(width: 12, height: 12)
                    .overlay {
                        Circle().stroke(.black.opacity(0.25), lineWidth: 1)
                    }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 9)
        .background(.black.opacity(0.45), in: Capsule())
    }
}

struct ShotCallout: View {
    let feedback: ShotFeedback
    let combo: Int

    var body: some View {
        VStack(spacing: 3) {
            Text(feedback.title)
                .font(.title.bold())
                .foregroundStyle(feedback.color)
                .shadow(color: .black.opacity(0.75), radius: 4, y: 2)
                .id(feedback)
                .transition(.scale.combined(with: .opacity))

            if combo > 1 {
                Text("×(combo) COMBO")
                    .font(.headline.bold())
                    .foregroundStyle(.orange)
                    .shadow(color: .black.opacity(0.7), radius: 3, y: 2)
                    .contentTransition(.numericText())
            }
        }
        .animation(.bouncy(duration: 0.35), value: feedback)
    }
}

struct AimPrompt: View {
    let power: Double
    let shotType: ShotType

    var body: some View {
        VStack(spacing: 8) {
            if power > 0 {
                ProgressView(value: power)
                    .tint(power > 0.82 ? .orange : .cyan)
                    .frame(width: 180)
                    .scaleEffect(y: 1.8)
            }

            Text(power > 0 ? shotType.releasePrompt : "SWIPE UP TO SHOOT")
                .font(.subheadline.bold())
                .foregroundStyle(.white)
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .background(.black.opacity(0.58), in: Capsule())
        }
    }
}

struct RoundCompleteCard: View {
    let score: Int
    let goals: Int
    let accuracy: Double
    let onPlayAgain: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text("ROUND COMPLETE")
                .font(.headline.bold())
                .foregroundStyle(.cyan)

            Text(score, format: .number)
                .font(.largeTitle.bold())
                .foregroundStyle(.white)

            HStack(spacing: 24) {
                VStack {
                    Text(goals, format: .number)
                        .font(.title2.bold())
                    Text("GOALS")
                        .font(.caption.bold())
                        .foregroundStyle(.white.opacity(0.7))
                }

                VStack {
                    Text(accuracy, format: .percent.precision(.fractionLength(0)))
                        .font(.title2.bold())
                    Text("ACCURACY")
                        .font(.caption.bold())
                        .foregroundStyle(.white.opacity(0.7))
                }
            }
            .foregroundStyle(.white)

            Button("PLAY AGAIN", action: onPlayAgain)
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
        }
        .padding(.horizontal, 30)
        .padding(.vertical, 22)
        .background(.black.opacity(0.78), in: RoundedRectangle(cornerRadius: 26))
    }
}

#Preview {
    ContentView()
}
