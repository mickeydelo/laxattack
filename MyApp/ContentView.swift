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
    @State private var isCancellingShot = false
    @State private var isPaused = false
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    @AppStorage("careerShots") private var careerShots = 0
    @AppStorage("hasSeenSplitDodgeHint") private var hasSeenSplitDodgeHint = false

    var body: some View {
        ZStack {
            RealityView { content in
                content.camera = .virtual
                content.renderingEffects.depthOfField = .enabled
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
                bestCombo: session.bestCombo,
                accuracy: session.accuracy,
                feedback: session.feedback,
                goalieLevel: session.difficultyLevel,
                hotZone: session.activeHotZone,
                isClutchShot: session.isClutchShot,
                isOnFire: session.isOnFire,
                aimPower: aimSample?.normalizedPower ?? 0,
                dodgeDirection: dodgeDirection,
                isCancellingShot: isCancellingShot,
                showsSplitDodgeHint: careerShots >= 3 && !hasSeenSplitDodgeHint,
                run: run,
                challengeProgress: run.challenge?.progress(for: session),
                selectedShotType: session.selectedShotType,
                availableShotTypes: availableShotTypes,
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
        .onChange(of: session.shotHistory.count) { oldValue, newValue in
            if newValue > oldValue {
                careerShots += newValue - oldValue
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
                let shouldCancel = value.translation.height > 34
                if shouldCancel != isCancellingShot {
                    withAnimation(.smooth(duration: 0.2)) {
                        isCancellingShot = shouldCancel
                    }
                }
                if shouldCancel {
                    aimSample = nil
                    dodgeDirection = 0
                    gameScene.hideAimGuide()
                    return
                }
                if dodgeDirection == 0,
                   abs(value.translation.width) > 55,
                   abs(value.translation.height) < 75 {
                    dodgeDirection = value.translation.width < 0 ? -1 : 1
                    hasSeenSplitDodgeHint = true
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
                let cancelled = isCancellingShot || value.translation.height > 34
                let committedDodge = dodgeDirection
                let sample = shotSample(
                    translation: value.translation,
                    velocity: value.velocity,
                    dodgeDirection: committedDodge
                )
                gameScene.hideAimGuide()
                aimSample = nil
                dodgeDirection = 0
                withAnimation(.smooth(duration: 0.18)) {
                    isCancellingShot = false
                }
                guard !cancelled else { return }
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

    private var availableShotTypes: [ShotType] {
        if careerShots < 3 { return [.overhand] }
        if careerShots < 8 { return [.overhand, .bounce] }
        return ShotType.selectableCases
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
    let bestCombo: Int
    let accuracy: Double
    let feedback: ShotFeedback
    let goalieLevel: Int
    let hotZone: HotZone
    let isClutchShot: Bool
    let isOnFire: Bool
    let aimPower: Double
    let dodgeDirection: Float
    let isCancellingShot: Bool
    let showsSplitDodgeHint: Bool
    let run: GameRun
    let challengeProgress: ChallengeProgress?
    let selectedShotType: ShotType
    let availableShotTypes: [ShotType]
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
        VStack(spacing: 8) {
            GameHeader(
                score: score,
                bestScore: bestScore,
                onPause: onPause
            )

            HStack(alignment: .center) {
                RunStatusBadge(
                    rule: run.rule,
                    shotsRemaining: shotsRemaining,
                    totalShots: totalShots,
                    stopsRemaining: stopsRemaining,
                    maximumStops: maximumStops,
                    secondsRemaining: secondsRemaining
                )
                Spacer()
                MomentumBadge(
                    combo: combo,
                    goalieLevel: goalieLevel,
                    isOnFire: isOnFire,
                    isClutchShot: isClutchShot
                )
            }

            TargetDirective(hotZone: hotZone)

            ShotCallout(feedback: feedback)

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
                    bestCombo: bestCombo,
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
                    availableTypes: availableShotTypes,
                    isEnabled: canSelectShot,
                    onSelect: onSelectShotType
                )
                AimPrompt(
                    power: aimPower,
                    shotType: selectedShotType,
                    dodgeDirection: dodgeDirection,
                    isCancellingShot: isCancellingShot,
                    showsSplitDodgeHint: showsSplitDodgeHint
                )
            }
        }
        .padding(.horizontal, 16)
        .padding(.top, 8)
        .padding(.bottom, 18)
    }
}

struct ShotTypePicker: View {
    let selection: ShotType
    let availableTypes: [ShotType]
    let isEnabled: Bool
    let onSelect: (ShotType) -> Void

    var body: some View {
        HStack(spacing: 7) {
            ForEach(availableTypes) { type in
                Button {
                    onSelect(type)
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: type.symbolName)
                            .font(.subheadline.bold())
                        Text(type.title)
                            .font(.system(size: 11, weight: .black, design: .rounded))
                            .lineLimit(1)
                    }
                    .foregroundStyle(selection == type ? PocketLaxStyle.ink : .white.opacity(0.88))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 11)
                    .background(
                        selection == type ? PocketLaxStyle.gold : PocketLaxStyle.ink.opacity(0.76),
                        in: Capsule()
                    )
                    .overlay { Capsule().stroke(.white.opacity(selection == type ? 0.5 : 0.14), lineWidth: 1) }
                    .shadow(color: selection == type ? PocketLaxStyle.gold.opacity(0.28) : .clear, radius: 8, y: 4)
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
    let onPause: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Button(action: onPause) {
                Image(systemName: "pause.fill")
                    .font(.system(size: 10, weight: .black))
                    .foregroundStyle(.white.opacity(0.88))
                    .frame(width: 30, height: 30)
                    .background(PocketLaxStyle.ink.opacity(0.7), in: Circle())
                    .overlay { Circle().stroke(.white.opacity(0.15), lineWidth: 1) }
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Pause")

            Spacer()

            HStack(spacing: 11) {
                HeaderStat(title: "SCORE", value: score)
                Divider().overlay(.white.opacity(0.2)).frame(height: 24)
                HeaderStat(title: "BEST", value: bestScore)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(PocketLaxStyle.ink.opacity(0.82), in: RoundedRectangle(cornerRadius: 16))
            .overlay { RoundedRectangle(cornerRadius: 16).stroke(.white.opacity(0.13), lineWidth: 1) }
        }
    }
}

struct HeaderStat: View {
    let title: LocalizedStringResource
    let value: Int

    var body: some View {
        VStack(spacing: 1) {
            Text(title).font(.system(size: 9, weight: .bold, design: .rounded)).foregroundStyle(.white.opacity(0.62))
            Text(value, format: .number)
                .font(.system(size: 19, weight: .black, design: .rounded))
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
                        .foregroundStyle(index < stopsRemaining ? PocketLaxStyle.sky : .white.opacity(0.24))
                }
            }
            .font(.subheadline.bold())
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background(PocketLaxStyle.ink.opacity(0.8), in: Capsule())
            .overlay { Capsule().stroke(.white.opacity(0.14), lineWidth: 1) }
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

    var body: some View {
        Text(feedback.title)
            .font(.system(size: 22, weight: .black, design: .rounded))
            .foregroundStyle(feedback.color)
            .shadow(color: .black.opacity(0.55), radius: 3, y: 2)
            .id(feedback)
            .transition(.scale(scale: 0.9).combined(with: .opacity))
        .animation(.bouncy(duration: 0.35), value: feedback)
    }
}

struct TargetDirective: View {
    let hotZone: HotZone

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "scope")
                .font(.system(size: 14, weight: .black))
                .foregroundStyle(PocketLaxStyle.sky)
                .frame(width: 30, height: 30)
                .background(PocketLaxStyle.sky.opacity(0.13), in: Circle())

            VStack(alignment: .leading, spacing: 0) {
                Text(hotZone.title)
                    .font(.system(size: 13, weight: .black, design: .rounded))
                    .foregroundStyle(.white)
                Text(hotZone.shotHint)
                    .font(.system(size: 9, weight: .bold, design: .rounded))
                    .tracking(0.7)
                    .foregroundStyle(.white.opacity(0.58))
            }

            Spacer(minLength: 10)

            Text("+200")
                .font(.system(size: 13, weight: .black, design: .rounded))
                .foregroundStyle(PocketLaxStyle.gold)
        }
        .padding(.leading, 7)
        .padding(.trailing, 12)
        .padding(.vertical, 6)
        .frame(maxWidth: 240)
        .background(PocketLaxStyle.ink.opacity(0.84), in: RoundedRectangle(cornerRadius: 17))
        .overlay(alignment: .leading) {
            Capsule()
                .fill(PocketLaxStyle.sky)
                .frame(width: 3, height: 28)
                .offset(x: -1)
        }
        .overlay { RoundedRectangle(cornerRadius: 17).stroke(.white.opacity(0.12), lineWidth: 1) }
    }
}

struct MomentumBadge: View {
    let combo: Int
    let goalieLevel: Int
    let isOnFire: Bool
    let isClutchShot: Bool

    var body: some View {
        HStack(spacing: 7) {
            Image(systemName: symbolName)
                .font(.system(size: 11, weight: .black))
                .foregroundStyle(accent)

            if combo > 1 || isOnFire || isClutchShot {
                if combo > 1 {
                    Text("×\(combo)")
                        .font(.system(size: 17, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                        .contentTransition(.numericText())
                }
                Text(label)
                    .font(.system(size: 9, weight: .black, design: .rounded))
                    .tracking(0.8)
                    .foregroundStyle(.white.opacity(0.6))
            } else {
                Text("LEVEL \(goalieLevel)")
                    .font(.system(size: 10, weight: .black, design: .rounded))
                    .tracking(0.8)
                    .foregroundStyle(.white.opacity(0.72))
            }
        }
        .padding(.horizontal, 11)
        .frame(height: 34)
        .background(PocketLaxStyle.ink.opacity(0.82), in: Capsule())
        .overlay { Capsule().stroke(accent.opacity(0.38), lineWidth: 1) }
        .shadow(color: accent.opacity(isOnFire || isClutchShot ? 0.3 : 0), radius: 8)
        .animation(.bouncy(duration: 0.3), value: combo)
    }

    private var symbolName: String {
        if isClutchShot { return "bolt.fill" }
        if isOnFire { return "flame.fill" }
        return "gauge.with.dots.needle.67percent"
    }

    private var label: LocalizedStringResource {
        if isClutchShot { return "CLUTCH" }
        if isOnFire { return "HOT STREAK" }
        return "STREAK"
    }

    private var accent: Color {
        if isClutchShot { return .purple }
        if isOnFire { return PocketLaxStyle.gold }
        return PocketLaxStyle.sky
    }
}

struct AimPrompt: View {
    let power: Double
    let shotType: ShotType
    let dodgeDirection: Float
    let isCancellingShot: Bool
    let showsSplitDodgeHint: Bool

    var body: some View {
        VStack(spacing: 7) {
            if isCancellingShot {
                Label("RELEASE TO CANCEL", systemImage: "xmark")
                    .font(.system(size: 12, weight: .black, design: .rounded))
                    .tracking(0.8)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 15)
                    .padding(.vertical, 9)
                    .background(PocketLaxStyle.ink.opacity(0.92), in: Capsule())
                    .overlay { Capsule().stroke(.white.opacity(0.2), lineWidth: 1) }
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
            if dodgeDirection != 0 {
                Label("SPLIT DODGE", systemImage: "figure.lacrosse")
                    .font(.caption.bold())
                    .foregroundStyle(.yellow)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 7)
                    .background(.black.opacity(0.68), in: Capsule())
            }
            if showsSplitDodgeHint && dodgeDirection == 0 && !isCancellingShot && power == 0 {
                Label("SIDEWAYS, THEN UP", systemImage: "arrow.left.and.right")
                    .font(.system(size: 10, weight: .bold, design: .rounded))
                    .tracking(0.7)
                    .foregroundStyle(.white.opacity(0.8))
                    .transition(.opacity)
            }
            if power > 0 {
                ProgressView(value: power)
                    .tint(power > 0.82 ? .orange : .cyan)
                    .frame(width: 180)
                    .scaleEffect(y: 1.8)
            }

            if !isCancellingShot {
                Label(
                power > 0 ? shotType.releasePrompt : "FLICK TO SHOOT",
                systemImage: power > 0 ? "arrow.up" : "hand.draw.fill"
                )
                .font(.system(size: 13, weight: .black, design: .rounded))
                .tracking(0.7)
                .foregroundStyle(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 9)
                .background(PocketLaxStyle.ink.opacity(0.84), in: Capsule())
                .overlay { Capsule().stroke(.white.opacity(0.16), lineWidth: 1) }
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }

        }
    }
}

private enum PocketLaxStyle {
    static let ink = Color(red: 0.055, green: 0.12, blue: 0.16)
    static let sky = Color(red: 0.25, green: 0.84, blue: 1)
    static let gold = Color(red: 1, green: 0.78, blue: 0.08)
}

struct RoundCompleteCard: View {
    let score: Int
    let goals: Int
    let bestCombo: Int
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
                    Text(bestCombo, format: .number)
                        .font(.title2.bold())
                    Text("BEST COMBO")
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
                ShareLink(
                    item: "I scored \(score) points with \(goals) goals in Lax Attack!",
                    subject: Text("Lax Attack score")
                ) {
                    Label("SHARE", systemImage: "square.and.arrow.up")
                }
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

            ScrollView(showsIndicators: false) {
                VStack(spacing: 14) {
                    HomeHeader(bestScore: bestScore, onSettings: onSettings)
                        .padding(.bottom, 138)

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
                .padding(.horizontal, 16)
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
                colors: [Color(red: 0.30, green: 0.78, blue: 0.98), Color(red: 0.16, green: 0.63, blue: 0.86), Color(red: 0.16, green: 0.53, blue: 0.28)],
                startPoint: .top,
                endPoint: .bottom
            )

            HStack(spacing: -38) {
                ForEach(0..<3, id: \.self) { _ in
                    Circle().fill(.white.opacity(0.78)).frame(width: 118, height: 72)
                }
            }
            .blur(radius: 8)
            .offset(x: 70, y: -300)

            RoundedRectangle(cornerRadius: 80)
                .fill(Color(red: 0.20, green: 0.65, blue: 0.28))
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
            ZStack {
                Image(systemName: "mountain.2.fill")
                    .resizable()
                    .scaledToFit()
                    .foregroundStyle(Color.indigo.opacity(0.3))
                    .frame(width: 430)
                    .offset(y: 86)
                Image(systemName: "tree.fill")
                    .font(.system(size: 112))
                    .foregroundStyle(Color(red: 0.08, green: 0.38, blue: 0.22))
                    .offset(x: -145, y: 178)
                Image(systemName: "tree.fill")
                    .font(.system(size: 92))
                    .foregroundStyle(Color(red: 0.09, green: 0.44, blue: 0.24))
                    .offset(x: 150, y: 195)
            }
        }
    }
}

struct HomeHeader: View {
    let bestScore: Int
    let onSettings: () -> Void

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: -3) {
                Text("LAX ATTACK")
                    .foregroundStyle(.white)
                Text("POCKET-SIZED. GAME-DAY BIG.")
                    .font(.system(size: 9, weight: .black, design: .rounded))
                    .foregroundStyle(PocketLaxStyle.gold)
            }
            .font(.system(size: 27, weight: .black, design: .rounded))
            .tracking(0.8)
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
            .background(PocketLaxStyle.ink.opacity(0.8), in: RoundedRectangle(cornerRadius: 17))
            .overlay { RoundedRectangle(cornerRadius: 17).stroke(.white.opacity(0.16), lineWidth: 1) }

            Button(action: onSettings) {
                Image(systemName: "gearshape.fill")
                    .font(.title2.bold())
                    .foregroundStyle(.white)
                    .frame(width: 50, height: 50)
                    .background(PocketLaxStyle.ink.opacity(0.8), in: Circle())
                    .overlay { Circle().stroke(.white.opacity(0.16), lineWidth: 1) }
            }
            .buttonStyle(.plain)
        }
        .padding(.top, 44)
    }
}

struct HomeHeroCard: View {
    let onPlay: () -> Void

    var body: some View {
        VStack(spacing: 13) {
            Text("SURVIVAL")
                .font(.system(size: 13, weight: .black, design: .rounded))
                .tracking(2)
                .foregroundStyle(PocketLaxStyle.gold)
            Text("Own the crease.")
                .font(.system(size: 27, weight: .black, design: .rounded))
                .foregroundStyle(.white)
            Text("Score until the goalie stops you three times.")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.white.opacity(0.72))

            Button(action: onPlay) {
                Label("PLAY NOW", systemImage: "play.fill")
                    .font(.system(size: 22, weight: .black, design: .rounded))
                    .foregroundStyle(PocketLaxStyle.ink)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .background(
                        LinearGradient(colors: [PocketLaxStyle.gold, Color.orange], startPoint: .top, endPoint: .bottom),
                        in: RoundedRectangle(cornerRadius: 24)
                    )
                    .overlay { RoundedRectangle(cornerRadius: 24).stroke(.white.opacity(0.55), lineWidth: 2) }
                    .shadow(color: .black.opacity(0.3), radius: 0, y: 6)
            }
            .buttonStyle(.plain)
        }
        .padding(18)
        .background(
            LinearGradient(colors: [PocketLaxStyle.ink.opacity(0.94), Color(red: 0.12, green: 0.27, blue: 0.25).opacity(0.94)], startPoint: .topLeading, endPoint: .bottomTrailing),
            in: RoundedRectangle(cornerRadius: 28)
        )
        .overlay { RoundedRectangle(cornerRadius: 28).stroke(.white.opacity(0.18), lineWidth: 1) }
        .shadow(color: .black.opacity(0.28), radius: 18, y: 10)
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
            HStack(spacing: 11) {
                Image(systemName: symbolName)
                    .font(.title2.bold())
                    .frame(width: 34)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 13, weight: .black, design: .rounded))
                Text(subtitle)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.white.opacity(0.75))
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(.caption.bold())
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity, minHeight: 64)
            .padding(.horizontal, 14)
            .background(
                LinearGradient(colors: [color.opacity(0.96), color.opacity(0.72)], startPoint: .topLeading, endPoint: .bottomTrailing),
                in: RoundedRectangle(cornerRadius: 19)
            )
            .overlay { RoundedRectangle(cornerRadius: 19).stroke(.white.opacity(0.24), lineWidth: 1) }
            .shadow(color: .black.opacity(0.22), radius: 0, y: 4)
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

    var body: some View {
        Color.black.opacity(0.58)
            .ignoresSafeArea()
            .overlay {
                VStack(spacing: 16) {
                    Image(systemName: "hand.draw.fill")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundStyle(.yellow)
                    Text("FLICK TO SHOOT")
                        .font(.title.bold())
                        .foregroundStyle(.white)
                    Text("Swipe up toward the spot you want to hit.")
                        .font(.body.weight(.semibold))
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.white.opacity(0.78))

                    Button("LET'S PLAY", action: onComplete)
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
