import SwiftUI
import RealityKit

struct ContentView: View {
    @State private var flow = AppFlow()
    @State private var progress = PlayerProgress()
    @AppStorage("reducedMotion") private var reducedMotion = false

    var body: some View {
        ZStack {
            switch flow.destination {
            case .home:
                HomeScreen(
                    dailyRun: .dailyShot(),
                    bestScore: progress.bestScore,
                    dailyBest: progress.dailyBest,
                    onQuickShoot: { flow.start(.quickShoot()) },
                    onTimeAttack: { flow.start(.timeAttack()) },
                    onDailyShot: { flow.start(.dailyShot()) },
                    onChallenges: { flow.isShowingChallenges = true },
                    onSettings: { flow.isShowingSettings = true }
                )
                .transition(.opacity.combined(with: .scale(scale: 0.98)))
            case .gameplay:
                if let run = flow.currentRun {
                    GameplayScreen(
                        run: run,
                        progress: progress,
                        onHome: { flow.returnHome() },
                        onSettings: { flow.isShowingSettings = true }
                    )
                    .transition(.opacity)
                }
            }
        }
        .animation(reducedMotion ? nil : .smooth(duration: 0.28), value: flow.destination)
        .sheet(isPresented: settingsBinding) {
            SettingsScreen()
                .presentationDetents([.medium])
        }
        .sheet(isPresented: challengesBinding) {
            ChallengeSelectionScreen(completedIDs: progress.completedChallengeIDs) { challenge in
                flow.start(.challenge(challenge))
            }
            .presentationDetents([.large])
        }
    }

    private var settingsBinding: Binding<Bool> {
        Binding(
            get: { flow.isShowingSettings },
            set: { flow.isShowingSettings = $0 }
        )
    }

    private var challengesBinding: Binding<Bool> {
        Binding(
            get: { flow.isShowingChallenges },
            set: { flow.isShowingChallenges = $0 }
        )
    }
}

struct GameplayScreen: View {
    let run: GameRun
    let progress: PlayerProgress
    let onHome: () -> Void
    let onSettings: () -> Void

    @State private var session = GameSession()
    @State private var gameScene = PocketLaxScene()
    @State private var aimSample: ShotControlSample?
    @State private var dodgeDirection: Float = 0
    @State private var isPaused = false
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false

    var body: some View {
        ZStack {
            RealityView { content in
                content.camera = .virtual
                gameScene.build(in: &content, session: session)
                await gameScene.installAuthoredShooter()
            }
            .ignoresSafeArea()
            .contentShape(Rectangle())

            GameHUD(
                score: session.score,
                bestScore: max(progress.bestScore, session.bestScore),
                combo: session.combo,
                shotsRemaining: session.shotsRemaining,
                stopsRemaining: session.stopsRemaining,
                maximumStops: session.maximumStops,
                secondsRemaining: session.secondsRemaining,
                goals: session.goals,
                accuracy: session.accuracy,
                feedback: session.feedback,
                goalieLevel: session.difficultyLevel,
                hotZone: session.activeHotZone,
                isClutchShot: session.isClutchShot,
                isOnFire: session.isOnFire,
                aimPower: aimSample?.normalizedPower ?? 0,
                dodgeDirection: dodgeDirection,
                run: run,
                challengeProgress: run.challenge?.progress(for: session),
                selectedShotType: session.selectedShotType,
                canSelectShot: !session.isAwaitingResult,
                isQuickStickChallenge: session.isQuickStickChallenge,
                isRoundComplete: session.isRoundComplete,
                totalShots: session.totalShots,
                onPause: { isPaused = true },
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
                    startRun()
                    gameScene.prepareForNewRound()
                },
                onHome: onHome
            )

            if isPaused {
                PauseOverlay(
                    onResume: { isPaused = false },
                    onRestart: {
                        startRun()
                        gameScene.prepareForNewRound()
                        isPaused = false
                    },
                    onSettings: onSettings,
                    onHome: onHome
                )
            } else if !hasCompletedOnboarding {
                OnboardingOverlay {
                    hasCompletedOnboarding = true
                }
            }
        }
        .contentShape(Rectangle())
        .gesture(shotGesture, isEnabled: !isPaused && hasCompletedOnboarding)
        .task(id: run.id) {
            startRun()
            while !Task.isCancelled && !session.isRoundComplete {
                try? await Task.sleep(for: .milliseconds(100))
                if !isPaused && hasCompletedOnboarding {
                    session.advanceClock(by: 0.1)
                }
            }
        }
        .onChange(of: session.isRoundComplete) { _, isComplete in
            if isComplete {
                progress.record(run: run, session: session)
            }
        }
        .onDisappear {
            gameScene.stop()
        }
    }

    private func startRun() {
        session.startNewRound(
            rule: run.rule,
            seed: run.seed,
            preferredShot: run.challenge?.recommendedShot
        )
        gameScene.setShotType(session.selectedShotType)
    }

    private var shotGesture: some Gesture {
        DragGesture(minimumDistance: 12)
            .onChanged { value in
                guard !session.isAwaitingResult, !session.isRoundComplete else { return }
                if dodgeDirection == 0,
                   abs(value.translation.width) > 55,
                   abs(value.translation.height) < 75 {
                    dodgeDirection = value.translation.width < 0 ? -1 : 1
                    gameScene.updateDodge(direction: dodgeDirection)
                }
                let sample = shotSample(
                    translation: value.translation,
                    velocity: value.velocity,
                    dodgeDirection: dodgeDirection
                )
                aimSample = sample
                gameScene.updateAim(using: sample, shotType: session.selectedShotType)
            }
            .onEnded { value in
                let committedDodge = dodgeDirection
                let sample = shotSample(
                    translation: value.translation,
                    velocity: value.velocity,
                    dodgeDirection: committedDodge
                )
                gameScene.hideAimGuide()
                aimSample = nil
                dodgeDirection = 0
                guard value.translation.height < -24 else { return }
                gameScene.shoot(
                    using: sample,
                    shotType: session.selectedShotType,
                    dodgeDirection: committedDodge,
                    session: session
                )
            }
    }

    private func shotSample(
        translation: CGSize,
        velocity: CGSize,
        dodgeDirection: Float
    ) -> ShotControlSample {
        var shotTranslation = translation
        if abs(dodgeDirection) > 0.5 {
            // The first lateral movement sells the split dodge; only movement beyond
            // that plant should steer the shot itself.
            shotTranslation.width -= CGFloat(dodgeDirection) * 55
        }
        return ShotControlModel.sample(translation: shotTranslation, velocity: velocity)
    }
}

struct GameHUD: View {
    let score: Int
    let bestScore: Int
    let combo: Int
    let shotsRemaining: Int
    let stopsRemaining: Int
    let maximumStops: Int
    let secondsRemaining: Double
    let goals: Int
    let accuracy: Double
    let feedback: ShotFeedback
    let goalieLevel: Int
    let hotZone: HotZone
    let isClutchShot: Bool
    let isOnFire: Bool
    let aimPower: Double
    let dodgeDirection: Float
    let run: GameRun
    let challengeProgress: ChallengeProgress?
    let selectedShotType: ShotType
    let canSelectShot: Bool
    let isQuickStickChallenge: Bool
    let isRoundComplete: Bool
    let totalShots: Int
    let onPause: () -> Void
    let onSelectShotType: (ShotType) -> Void
    let quickStickPhase: (Date) -> Double
    let onQuickStick: (Date) -> Void
    let onPlayAgain: () -> Void
    let onHome: () -> Void

    var body: some View {
        VStack(spacing: 10) {
            GameHeader(
                score: score,
                bestScore: bestScore,
                modeTitle: run.title,
                onPause: onPause
            )

            HStack {
                RunStatusBadge(
                    rule: run.rule,
                    shotsRemaining: shotsRemaining,
                    totalShots: totalShots,
                    stopsRemaining: stopsRemaining,
                    maximumStops: maximumStops,
                    secondsRemaining: secondsRemaining
                )
                Spacer()
                if isClutchShot {
                    Label("CLUTCH ×2", systemImage: "bolt.fill")
                        .font(.caption.bold())
                        .foregroundStyle(.yellow)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(.purple.opacity(0.82), in: Capsule())
                } else if isOnFire {
                    Label("ON FIRE", systemImage: "flame.fill")
                        .font(.caption.bold())
                        .foregroundStyle(.yellow)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(.orange.opacity(0.82), in: Capsule())
                }
                if goalieLevel > 0 {
                    Label("PRESSURE \(goalieLevel)", systemImage: "gauge.with.dots.needle.67percent")
                        .font(.caption.bold())
                        .foregroundStyle(goalieLevel >= 3 ? .yellow : .white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 7)
                        .background(
                            (goalieLevel >= 3 ? Color.red : Color.blue).opacity(0.78),
                            in: Capsule()
                        )
                }
            }

            ShotCallout(feedback: feedback, combo: combo)

            HStack(spacing: 4) {
                Image(systemName: "scope")
                Text("CALL:")
                Text(hotZone.title)
                Text("+200")
                    .foregroundStyle(.yellow)
            }
            .font(.caption.bold())
            .foregroundStyle(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(.black.opacity(0.58), in: Capsule())

            if let challenge = run.challenge, let challengeProgress {
                ChallengeProgressCard(
                    objective: challenge.objective,
                    progress: challengeProgress
                )
            } else if run.mode == .dailyShot {
                ModeObjectiveCard(symbolName: "calendar", text: run.objective)
            }

            Spacer()

            if isRoundComplete {
                RoundCompleteCard(
                    score: score,
                    goals: goals,
                    accuracy: accuracy,
                    run: run,
                    challengeProgress: challengeProgress,
                    onPlayAgain: onPlayAgain,
                    onHome: onHome
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
                AimPrompt(
                    power: aimPower,
                    shotType: selectedShotType,
                    dodgeDirection: dodgeDirection
                )
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
    let modeTitle: LocalizedStringResource
    let onPause: () -> Void

    var body: some View {
        HStack(alignment: .top) {
            HStack(spacing: 9) {
                Button(action: onPause) {
                    Image(systemName: "pause.fill")
                        .font(.headline.bold())
                        .foregroundStyle(.white)
                        .frame(width: 38, height: 38)
                        .background(.black.opacity(0.62), in: RoundedRectangle(cornerRadius: 13))
                }
                .buttonStyle(.plain)

                VStack(alignment: .leading, spacing: 0) {
                    Text("LAX ATTACK")
                        .foregroundStyle(.cyan)
                    Text(modeTitle)
                        .font(.caption2.bold())
                        .foregroundStyle(.white.opacity(0.78))
                }
            }
            .font(.headline.bold())
            .tracking(1.5)

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
    let totalShots: Int

    var body: some View {
        HStack(spacing: 6) {
            ForEach(0..<totalShots, id: \.self) { index in
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

struct RunStatusBadge: View {
    let rule: RunRule
    let shotsRemaining: Int
    let totalShots: Int
    let stopsRemaining: Int
    let maximumStops: Int
    let secondsRemaining: Double

    var body: some View {
        switch rule {
        case .survival:
            HStack(spacing: 6) {
                ForEach(0..<maximumStops, id: \.self) { index in
                    Image(systemName: index < stopsRemaining ? "shield.fill" : "shield")
                        .foregroundStyle(index < stopsRemaining ? .cyan : .white.opacity(0.28))
                }
            }
            .font(.subheadline.bold())
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background(.black.opacity(0.5), in: Capsule())
        case .timed:
            Label {
                Text(Int(ceil(secondsRemaining)), format: .number)
                    .monospacedDigit()
                    .contentTransition(.numericText())
            } icon: {
                Image(systemName: "timer")
            }
            .font(.headline.bold())
            .foregroundStyle(secondsRemaining <= 10 ? .yellow : .white)
            .padding(.horizontal, 13)
            .padding(.vertical, 8)
            .background(.black.opacity(0.56), in: Capsule())
        case .shotLimit:
            ShotCounter(shotsRemaining: shotsRemaining, totalShots: totalShots)
        }
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
                Text("×\(combo) COMBO")
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
    let dodgeDirection: Float

    var body: some View {
        VStack(spacing: 8) {
            if dodgeDirection != 0 {
                Label("SPLIT DODGE", systemImage: "figure.lacrosse")
                    .font(.caption.bold())
                    .foregroundStyle(.yellow)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(.black.opacity(0.68), in: Capsule())
            }
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
    let run: GameRun
    let challengeProgress: ChallengeProgress?
    let onPlayAgain: () -> Void
    let onHome: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text(run.mode == .dailyShot ? "DAILY COMPLETE" : "ROUND COMPLETE")
                .font(.headline.bold())
                .foregroundStyle(.cyan)

            if let challengeProgress {
                MedalRow(earned: challengeProgress.medals)
                Text(challengeProgress.isComplete ? "CHALLENGE CLEARED" : "KEEP FIRING")
                    .font(.caption.bold())
                    .foregroundStyle(challengeProgress.isComplete ? .yellow : .white.opacity(0.72))
            }

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

            HStack {
                Button("HOME", action: onHome)
                    .buttonStyle(.bordered)
                Button("PLAY AGAIN", action: onPlayAgain)
                    .buttonStyle(.borderedProminent)
            }
            .controlSize(.large)
        }
        .padding(.horizontal, 30)
        .padding(.vertical, 22)
        .background(.black.opacity(0.78), in: RoundedRectangle(cornerRadius: 26))
    }
}

struct HomeScreen: View {
    let dailyRun: GameRun
    let bestScore: Int
    let dailyBest: Int
    let onQuickShoot: () -> Void
    let onTimeAttack: () -> Void
    let onDailyShot: () -> Void
    let onChallenges: () -> Void
    let onSettings: () -> Void

    var body: some View {
        ZStack {
            HomeDioramaBackground()

            ScrollView {
                VStack(spacing: 18) {
                    HomeHeader(bestScore: bestScore, onSettings: onSettings)
                        .padding(.bottom, 118)

                    HomeHeroCard(onPlay: onQuickShoot)

                    HStack(spacing: 12) {
                        HomeModeButton(
                            title: "60 SECOND RUSH",
                            subtitle: "Beat the clock.",
                            symbolName: "timer",
                            color: .purple,
                            action: onTimeAttack
                        )
                        HomeModeButton(
                            title: "DAILY SHOT",
                            subtitle: "Same setup. One score.",
                            symbolName: "calendar",
                            color: .blue,
                            action: onDailyShot
                        )
                    }

                    HomeModeButton(
                        title: "CHALLENGES",
                        subtitle: "Master your stick.",
                        symbolName: "trophy.fill",
                        color: .orange,
                        action: onChallenges
                    )

                    VStack(spacing: 3) {
                        Text(dailyRun.objective)
                        Text("DAILY BEST: \(dailyBest)")
                            .monospacedDigit()
                    }
                    .font(.caption.bold())
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white.opacity(0.8))
                    .padding(.horizontal, 24)
                }
                .padding(.horizontal, 18)
                .padding(.top, 12)
                .padding(.bottom, 28)
                .containerRelativeFrame(.horizontal)
            }
        }
    }
}

struct HomeDioramaBackground: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.cyan.opacity(0.75), Color.blue.opacity(0.48), Color.green.opacity(0.7)],
                startPoint: .top,
                endPoint: .bottom
            )

            Circle()
                .fill(.white.opacity(0.72))
                .frame(width: 190, height: 74)
                .blur(radius: 14)
                .offset(x: 80, y: -290)

            RoundedRectangle(cornerRadius: 80)
                .fill(Color.green.opacity(0.88))
                .frame(width: 470, height: 440)
                .rotationEffect(.degrees(-4))
                .offset(y: 235)
                .overlay {
                    RoundedRectangle(cornerRadius: 80)
                        .stroke(.white.opacity(0.42), lineWidth: 3)
                        .frame(width: 330, height: 250)
                        .offset(y: 240)
                }
        }
        .ignoresSafeArea()
        .overlay(alignment: .top) {
            Image(systemName: "mountain.2.fill")
                .resizable()
                .scaledToFit()
                .foregroundStyle(.indigo.opacity(0.36))
                .frame(width: 390)
                .offset(y: 95)
        }
    }
}

struct HomeHeader: View {
    let bestScore: Int
    let onSettings: () -> Void

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 0) {
                Text("LAX")
                    .foregroundStyle(.white)
                Text("ATTACK")
                    .foregroundStyle(.cyan)
            }
            .font(.largeTitle.bold())
            .tracking(1.5)
            .shadow(color: .black.opacity(0.35), radius: 3, y: 2)

            Spacer()

            VStack(spacing: 0) {
                Text("BEST")
                    .font(.caption2.bold())
                    .foregroundStyle(.white.opacity(0.68))
                Text(bestScore, format: .number)
                    .font(.headline.bold())
                    .foregroundStyle(.white)
            }
            .padding(.horizontal, 12)
            .frame(height: 50)
            .background(.black.opacity(0.52), in: RoundedRectangle(cornerRadius: 17))

            Button(action: onSettings) {
                Image(systemName: "gearshape.fill")
                    .font(.title2.bold())
                    .foregroundStyle(.white)
                    .frame(width: 50, height: 50)
                    .background(.black.opacity(0.52), in: RoundedRectangle(cornerRadius: 17))
            }
            .buttonStyle(.plain)
        }
        .padding(.top, 44)
    }
}

struct HomeHeroCard: View {
    let onPlay: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            VStack(spacing: 3) {
                Text("SMALL SHOTS. BIG PLAYS.")
                    .font(.title2.bold())
                    .foregroundStyle(.white)
                Text("Keep scoring. Three stops end the run.")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.white.opacity(0.78))
            }

            Button(action: onPlay) {
                Label("PLAY", systemImage: "play.fill")
                    .font(.title.bold())
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .background(
                        LinearGradient(colors: [.green, .mint], startPoint: .top, endPoint: .bottom),
                        in: RoundedRectangle(cornerRadius: 24)
                    )
                    .shadow(color: .green.opacity(0.45), radius: 10, y: 7)
            }
            .buttonStyle(.plain)
        }
        .padding(18)
        .background(.black.opacity(0.58), in: RoundedRectangle(cornerRadius: 28))
    }
}

struct HomeModeButton: View {
    let title: LocalizedStringResource
    let subtitle: LocalizedStringResource
    let symbolName: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 7) {
                Image(systemName: symbolName)
                    .font(.title.bold())
                Text(title)
                    .font(.subheadline.bold())
                Text(subtitle)
                    .font(.caption2.weight(.semibold))
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white.opacity(0.75))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity, minHeight: 108)
            .padding(.horizontal, 10)
            .background(color.opacity(0.88), in: RoundedRectangle(cornerRadius: 22))
        }
        .buttonStyle(.plain)
    }
}

struct ChallengeSelectionScreen: View {
    let completedIDs: Set<String>
    let onSelect: (ChallengeDefinition) -> Void

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(ChallengeDefinition.catalog) { challenge in
                        ChallengeRow(
                            title: challenge.title,
                            objective: challenge.objective,
                            symbolName: challenge.symbolName,
                            isComplete: completedIDs.contains(challenge.id),
                            action: { onSelect(challenge) }
                        )
                    }
                }
                .padding(18)
            }
            .background(Color(red: 0.05, green: 0.12, blue: 0.19))
            .navigationTitle("CHALLENGES")
            .toolbarColorScheme(.dark, for: .navigationBar)
            .toolbarBackground(Color(red: 0.05, green: 0.12, blue: 0.19), for: .navigationBar)
        }
    }
}

struct ChallengeRow: View {
    let title: LocalizedStringResource
    let objective: LocalizedStringResource
    let symbolName: String
    let isComplete: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 14) {
                Image(systemName: symbolName)
                    .font(.title2.bold())
                    .foregroundStyle(.yellow)
                    .frame(width: 46, height: 46)
                    .background(.blue.opacity(0.55), in: RoundedRectangle(cornerRadius: 14))

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.headline.bold())
                    Text(objective)
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.7))
                }

                Spacer()
                Image(systemName: isComplete ? "checkmark.seal.fill" : "chevron.right")
                    .foregroundStyle(isComplete ? .green : .white.opacity(0.55))
            }
            .foregroundStyle(.white)
            .padding(14)
            .background(.white.opacity(0.09), in: RoundedRectangle(cornerRadius: 20))
        }
        .buttonStyle(.plain)
    }
}

struct SettingsScreen: View {
    @AppStorage("hapticsEnabled") private var hapticsEnabled = true
    @AppStorage("reducedMotion") private var reducedMotion = false

    var body: some View {
        NavigationStack {
            Form {
                Section("GAME FEEL") {
                    Toggle("Haptics", isOn: $hapticsEnabled)
                    Toggle("Reduce Motion", isOn: $reducedMotion)
                }

                Section("CONTROLS") {
                    LabeledContent("Aim", value: "Swipe direction")
                    LabeledContent("Power", value: "Swipe speed")
                    LabeledContent("Split dodge", value: "Sideways, then up")
                }
            }
            .navigationTitle("SETTINGS")
        }
    }
}

struct OnboardingOverlay: View {
    let onComplete: () -> Void
    @State private var step = 0

    private let lessons: [(symbol: String, title: LocalizedStringResource, detail: LocalizedStringResource)] = [
        ("hand.draw.fill", "FLICK TO SHOOT", "Swipe upward. Direction aims; speed adds power."),
        ("arrow.left.and.right", "SELL THE DODGE", "Move sideways first, then flick up to wrong-foot the goalie."),
        ("figure.lacrosse", "MIX YOUR RELEASE", "Overhand, bounce, and sidearm shots attack different openings.")
    ]

    var body: some View {
        Color.black.opacity(0.58)
            .ignoresSafeArea()
            .overlay {
                let lesson = lessons[step]
                VStack(spacing: 16) {
                    Image(systemName: lesson.symbol)
                        .font(.system(size: 48, weight: .bold))
                        .foregroundStyle(.yellow)
                    Text(lesson.title)
                        .font(.title.bold())
                        .foregroundStyle(.white)
                    Text(lesson.detail)
                        .font(.body.weight(.semibold))
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.white.opacity(0.78))

                    HStack(spacing: 7) {
                        ForEach(lessons.indices, id: \.self) { index in
                            Capsule()
                                .fill(index == step ? .cyan : .white.opacity(0.25))
                                .frame(width: index == step ? 24 : 8, height: 8)
                        }
                    }

                    Button(step == lessons.count - 1 ? "LET'S PLAY" : "NEXT") {
                        if step == lessons.count - 1 {
                            onComplete()
                        } else {
                            step += 1
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                }
                .padding(28)
                .background(.black.opacity(0.82), in: RoundedRectangle(cornerRadius: 28))
                .padding(28)
            }
    }
}

struct PauseOverlay: View {
    let onResume: () -> Void
    let onRestart: () -> Void
    let onSettings: () -> Void
    let onHome: () -> Void

    var body: some View {
        Color.black.opacity(0.62)
            .ignoresSafeArea()
            .overlay {
                VStack(spacing: 12) {
                    Text("PAUSED")
                        .font(.largeTitle.bold())
                        .foregroundStyle(.white)
                    PauseButton(title: "RESUME", symbolName: "play.fill", action: onResume)
                    PauseButton(title: "RESTART", symbolName: "arrow.counterclockwise", action: onRestart)
                    PauseButton(title: "SETTINGS", symbolName: "gearshape.fill", action: onSettings)
                    PauseButton(title: "HOME", symbolName: "house.fill", action: onHome)
                }
                .padding(24)
                .background(.black.opacity(0.82), in: RoundedRectangle(cornerRadius: 28))
                .padding(34)
            }
    }
}

struct PauseButton: View {
    let title: LocalizedStringResource
    let symbolName: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: symbolName)
                .font(.headline.bold())
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
        .controlSize(.large)
    }
}

struct ModeObjectiveCard: View {
    let symbolName: String
    let text: LocalizedStringResource

    var body: some View {
        Label(text, systemImage: symbolName)
            .font(.caption.bold())
            .foregroundStyle(.white)
            .padding(.horizontal, 13)
            .padding(.vertical, 8)
            .background(.blue.opacity(0.76), in: Capsule())
    }
}

struct ChallengeProgressCard: View {
    let objective: LocalizedStringResource
    let progress: ChallengeProgress

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(objective)
                    .lineLimit(1)
                Spacer()
                Text("\(progress.value)/\(progress.target)")
                    .monospacedDigit()
            }
            .font(.caption.bold())
            .foregroundStyle(.white)

            ProgressView(value: progress.fraction)
                .tint(progress.isComplete ? .yellow : .cyan)
        }
        .padding(.horizontal, 13)
        .padding(.vertical, 8)
        .background(.black.opacity(0.58), in: RoundedRectangle(cornerRadius: 13))
    }
}

struct MedalRow: View {
    let earned: Int

    var body: some View {
        HStack(spacing: 9) {
            ForEach(0..<3, id: \.self) { index in
                Image(systemName: index < earned ? "star.circle.fill" : "star.circle")
                    .font(.title2.bold())
                    .foregroundStyle(index < earned ? .yellow : .white.opacity(0.28))
            }
        }
    }
}

#Preview {
    ContentView()
}

#Preview("Gameplay") {
    let _ = UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
    GameplayScreen(
        run: .quickShoot(),
        progress: PlayerProgress(),
        onHome: {},
        onSettings: {}
    )
}

#Preview("Challenges") {
    ChallengeSelectionScreen(completedIDs: ["score_attack", "top_shelf"]) { _ in }
}
