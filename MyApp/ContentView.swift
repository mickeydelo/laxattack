import SwiftUI
import RealityKit
import Observation

#if os(iOS)
import UIKit
#endif

struct ContentView: View {
    @State private var session = GameSession()
    @State private var gameScene = PocketLaxScene()

    var body: some View {
        ZStack {
            RealityView { content in
                content.camera = .virtual
                gameScene.build(in: &content, session: session)
            }
            .ignoresSafeArea()
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 20)
                    .onEnded { value in
                        guard value.translation.height < -20 else { return }
                        gameScene.shoot(using: value.translation, session: session)
                    }
            )

            GameHUD(
                score: session.score,
                combo: session.combo,
                shotsRemaining: session.shotsRemaining,
                feedback: session.feedback,
                isRoundComplete: session.isRoundComplete,
                onPlayAgain: {
                    session.startNewRound()
                    gameScene.prepareForNewRound()
                }
            )
        }
        .onDisappear {
            gameScene.stop()
        }
    }
}

struct GameHUD: View {
    let score: Int
    let combo: Int
    let shotsRemaining: Int
    let feedback: ShotFeedback
    let isRoundComplete: Bool
    let onPlayAgain: () -> Void

    var body: some View {
        VStack {
            HStack(alignment: .top) {
                StatCard(title: "SHOTS", value: shotsRemaining)
                Spacer()
                StatCard(title: "SCORE", value: score)
            }

            Text(feedback.title)
                .font(.title.bold())
                .foregroundStyle(feedback.color)
                .shadow(color: .black.opacity(0.65), radius: 3, y: 2)
                .padding(.top, 8)

            if combo > 1 {
                Text("×(combo) COMBO")
                    .font(.headline.bold())
                    .foregroundStyle(.yellow)
                    .shadow(color: .black.opacity(0.65), radius: 2, y: 1)
            }

            Spacer()

            if isRoundComplete {
                VStack(spacing: 12) {
                    Text("ROUND COMPLETE")
                        .font(.headline.bold())
                    Text(score, format: .number)
                        .font(.largeTitle.bold())
                    Button("PLAY AGAIN", action: onPlayAgain)
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 28)
                .padding(.vertical, 20)
                .background(.black.opacity(0.72), in: RoundedRectangle(cornerRadius: 24))
                .padding(.bottom, 36)
            } else {
                Text("SWIPE UP TO SHOOT")
                    .font(.subheadline.bold())
                    .foregroundStyle(.white)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 10)
                    .background(.black.opacity(0.55), in: Capsule())
                    .padding(.bottom, 28)
            }
        }
        .padding(.horizontal, 18)
        .padding(.top, 12)
        .allowsHitTesting(isRoundComplete)
    }
}

struct StatCard: View {
    let title: LocalizedStringResource
    let value: Int

    var body: some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.caption.bold())
                .foregroundStyle(.white.opacity(0.8))
            Text(value, format: .number)
                .font(.title.bold())
                .foregroundStyle(.white)
        }
        .frame(minWidth: 86)
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(.black.opacity(0.6), in: RoundedRectangle(cornerRadius: 18))
    }
}

struct ShotInput: Equatable, Sendable {
    let horizontal: Float
    let power: Float
}

enum ShotOutcome: Equatable, Sendable {
    case goal
    case save
    case miss
}

struct ShotResult: Equatable, Sendable {
    let input: ShotInput
    let outcome: ShotOutcome
    let points: Int
    let combo: Int
    let hitPipe: Bool
}

enum ShotFeedback: Equatable {
    case ready
    case shooting
    case goal
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
        case .goal:
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
    private(set) var combo = 0
    private(set) var shotsRemaining = 5
    private(set) var feedback: ShotFeedback = .ready
    private(set) var isAwaitingResult = false
    private(set) var shotHistory: [ShotResult] = []

    private var pendingInput: ShotInput?
    private var pendingHitPipe = false

    var isRoundComplete: Bool {
        shotsRemaining == 0 && !isAwaitingResult
    }

    func beginShot(input: ShotInput) -> Bool {
        guard shotsRemaining > 0, !isAwaitingResult else { return false }
        shotsRemaining -= 1
        isAwaitingResult = true
        pendingInput = input
        pendingHitPipe = false
        feedback = .shooting
        return true
    }

    func registerGoal() -> Bool {
        guard isAwaitingResult else { return false }
        combo += 1
        let points = 100 * combo + (pendingHitPipe ? 75 : 0)
        score += points
        feedback = .goal
        finishShot(outcome: .goal, points: points)
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

    func registerMiss() -> Bool {
        guard isAwaitingResult else { return false }
        combo = 0
        feedback = .miss
        finishShot(outcome: .miss, points: 0)
        return true
    }

    func startNewRound() {
        score = 0
        combo = 0
        shotsRemaining = 5
        feedback = .ready
        isAwaitingResult = false
        shotHistory = []
        pendingInput = nil
        pendingHitPipe = false
    }

    func prepareNextShot() {
        guard !isRoundComplete else { return }
        feedback = .ready
    }

    private func finishShot(outcome: ShotOutcome, points: Int) {
        guard let pendingInput else { return }
        shotHistory.append(
            ShotResult(
                input: pendingInput,
                outcome: outcome,
                points: points,
                combo: combo,
                hitPipe: pendingHitPipe
            )
        )
        self.pendingInput = nil
        isAwaitingResult = false
    }
}

@MainActor
final class PocketLaxScene {
    private let ballStart = SIMD3<Float>(0, 0.18, 1.5)

    private var ball: ModelEntity?
    private var goalie: Entity?
    private let feedbackPlayer = GameFeedbackPlayer()
    private var subscriptions: [EventSubscription] = []
    private var shotTask: Task<Void, Never>?
    private var goalieElapsedTime: TimeInterval = 0
    private var isBuilt = false

    func build(in content: inout RealityViewCameraContent, session: GameSession) {
        guard !isBuilt else { return }
        isBuilt = true

        let root = Entity()
        root.name = "Pocket Lax Scene"

        addField(to: root)
        addGoal(to: root)
        addGoalSensor(to: root)
        addGoalie(to: root)
        addLighting(to: root)
        addCamera(to: root)

        let ball = makeBall()
        self.ball = ball
        root.addChild(ball)
        content.add(root)

        subscriptions.append(
            content.subscribe(to: CollisionEvents.Began.self) { [weak self, weak session] event in
                guard let self, let session else { return }
                self.handleCollision(event, session: session)
            }
        )

        subscriptions.append(
            content.subscribe(to: SceneEvents.Update.self) { [weak self] event in
                self?.updateGoalie(deltaTime: event.deltaTime)
            }
        )
    }

    func shoot(using translation: CGSize, session: GameSession) {
        guard let ball else { return }

        let swipeStrength = min(max(Float(-translation.height) / 140, 0.8), 2.2)
        let sideways = min(max(Float(translation.width) / 140, -1), 1)
        let input = ShotInput(horizontal: sideways, power: swipeStrength)
        guard session.beginShot(input: input) else { return }

        shotTask?.cancel()
        feedbackPlayer.playRelease()

        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .dynamic
        ball.components.set(body)

        let velocity = SIMD3<Float>(
            sideways * 1.4,
            2.0 + swipeStrength * 1.15,
            -(7.3 + swipeStrength * 2.25)
        )
        ball.applyLinearImpulse(velocity * body.massProperties.mass, relativeTo: nil)

        shotTask = Task { @MainActor [weak self, weak session] in
            try? await Task.sleep(for: .seconds(2.5))
            guard !Task.isCancelled, let self, let session else { return }
            if session.registerMiss() {
                self.feedbackPlayer.playMiss()
                await self.resetAfterResult(session: session, delay: .seconds(0.45))
            }
        }
    }

    func prepareForNewRound() {
        shotTask?.cancel()
        resetBall()
    }

    func stop() {
        shotTask?.cancel()
        subscriptions.removeAll()
    }

    private func handleCollision(_ event: CollisionEvents.Began, session: GameSession) {
        let names = Set([event.entityA.name, event.entityB.name])
        guard names.contains("Ball") else { return }

        if names.contains("Goal Sensor"), session.registerGoal() {
            feedbackPlayer.playGoal()
            scheduleReset(session: session)
        } else if names.contains("Goalie"), session.registerSave() {
            feedbackPlayer.playSave()
            scheduleReset(session: session)
        } else if names.contains("Goal Pipe") {
            session.registerPipe()
            feedbackPlayer.playPipe()
        }
    }

    private func scheduleReset(session: GameSession) {
        shotTask?.cancel()
        shotTask = Task { @MainActor [weak self, weak session] in
            guard let self, let session else { return }
            await self.resetAfterResult(session: session, delay: .seconds(0.75))
        }
    }

    private func resetAfterResult(
        session: GameSession,
        delay: Duration
    ) async {
        try? await Task.sleep(for: delay)
        guard !Task.isCancelled else { return }
        resetBall()
        session.prepareNextShot()
    }

    private func resetBall() {
        guard let ball else { return }

        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .kinematic
        ball.components.set(body)
        ball.components.set(PhysicsMotionComponent())
        ball.setPosition(ballStart, relativeTo: ball.parent)
        ball.orientation = .init()
    }

    private func updateGoalie(deltaTime: TimeInterval) {
        goalieElapsedTime += deltaTime
        goalie?.position.x = sin(Float(goalieElapsedTime) * 1.35) * 0.58
    }

    private func addField(to root: Entity) {
        let fieldSize = SIMD3<Float>(8, 0.1, 14)
        let shape = ShapeResource.generateBox(size: fieldSize)
        let field = ModelEntity(
            mesh: .generateBox(size: fieldSize),
            materials: [SimpleMaterial(color: .green, isMetallic: false)]
        )
        field.position = [0, -0.05, -1]
        field.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        field.components.set(
            PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .static)
        )
        root.addChild(field)
    }

    private func addGoal(to root: Entity) {
        let white = SimpleMaterial(color: .white, isMetallic: false)
        addGoalBar(size: [0.1, 2, 0.1], position: [-1, 1, -4.5], material: white, to: root)
        addGoalBar(size: [0.1, 2, 0.1], position: [1, 1, -4.5], material: white, to: root)
        addGoalBar(size: [2.1, 0.1, 0.1], position: [0, 2, -4.5], material: white, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [-1, 0.03, -5.1], material: white, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [1, 0.03, -5.1], material: white, to: root)
        addGoalBar(size: [2.1, 0.06, 0.06], position: [0, 0.03, -5.7], material: white, to: root)
    }

    private func addGoalBar(
        size: SIMD3<Float>,
        position: SIMD3<Float>,
        material: SimpleMaterial,
        to root: Entity
    ) {
        let shape = ShapeResource.generateBox(size: size)
        let bar = ModelEntity(mesh: .generateBox(size: size), materials: [material])
        bar.name = "Goal Pipe"
        bar.position = position
        bar.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        bar.components.set(
            PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .static)
        )
        root.addChild(bar)
    }

    private func addGoalSensor(to root: Entity) {
        let sensor = Entity()
        sensor.name = "Goal Sensor"
        sensor.position = [0, 1, -4.72]
        let shape = ShapeResource.generateBox(size: [1.78, 1.75, 0.2])
        sensor.components.set(
            CollisionComponent(shapes: [shape], mode: .trigger)
        )
        root.addChild(sensor)
    }

    private func addGoalie(to root: Entity) {
        let goalie = Entity()
        goalie.name = "Goalie"
        goalie.position = [0, 0, -4.25]

        let blue = SimpleMaterial(color: .blue, isMetallic: false)
        let white = SimpleMaterial(color: .white, isMetallic: false)
        let skin = SimpleMaterial(color: .init(red: 0.78, green: 0.55, blue: 0.38, alpha: 1), isMetallic: false)

        let torso = ModelEntity(
            mesh: .generateBox(size: [0.42, 0.5, 0.2], cornerRadius: 0.1),
            materials: [blue]
        )
        torso.position = [0, -0.005, 0]
        goalie.addChild(torso)

        let helmet = ModelEntity(
            mesh: .generateSphere(radius: 0.22),
            materials: [white]
        )
        helmet.position = [0, 0.395, 0]
        goalie.addChild(helmet)

        let face = ModelEntity(
            mesh: .generateSphere(radius: 0.16),
            materials: [skin]
        )
        face.position = [0, 0.375, 0.13]
        goalie.addChild(face)

        for x: Float in [-0.13, 0.13] {
            let leg = ModelEntity(
                mesh: .generateBox(size: [0.14, 0.38, 0.16], cornerRadius: 0.06),
                materials: [blue]
            )
            leg.position = [x, -0.375, 0]
            goalie.addChild(leg)
        }

        let stick = ModelEntity(
            mesh: .generateBox(size: [0.06, 1.05, 0.06], cornerRadius: 0.02),
            materials: [white]
        )
        stick.position = [0.35, -0.005, 0.08]
        stick.orientation = simd_quatf(angle: -0.32, axis: [0, 0, 1])
        goalie.addChild(stick)

        let collisionSize = SIMD3<Float>(0.65, 1.25, 0.28)
        let shape = ShapeResource.generateBox(size: collisionSize)
        goalie.position.y = collisionSize.y / 2
        goalie.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        goalie.components.set(
            PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .kinematic)
        )

        self.goalie = goalie
        root.addChild(goalie)
    }

    private func makeBall() -> ModelEntity {
        let radius: Float = 0.12
        let shape = ShapeResource.generateSphere(radius: radius)
        let ball = ModelEntity(
            mesh: .generateSphere(radius: radius),
            materials: [SimpleMaterial(color: .white, isMetallic: false)]
        )
        ball.name = "Ball"
        ball.position = ballStart
        ball.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        ball.components.set(
            PhysicsBodyComponent(
                shapes: [shape],
                mass: 0.15,
                material: .generate(
                    staticFriction: 0.5,
                    dynamicFriction: 0.4,
                    restitution: 0.35
                ),
                mode: .kinematic
            )
        )
        ball.components.set(PhysicsMotionComponent())
        return ball
    }

    private func addCamera(to root: Entity) {
        let camera = Entity()
        camera.components.set(PerspectiveCameraComponent())
        camera.look(
            at: [0, 0.9, -4.3],
            from: [0, 2.6, 5.8],
            relativeTo: root
        )
        root.addChild(camera)
    }

    private func addLighting(to root: Entity) {
        let light = Entity()
        light.components.set(
            DirectionalLightComponent(color: .white, intensity: 2_500)
        )
        light.look(at: .zero, from: [-3, 6, 4], relativeTo: root)
        root.addChild(light)
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

#Preview {
    ContentView()
}
