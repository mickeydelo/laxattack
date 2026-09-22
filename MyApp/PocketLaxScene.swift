import SwiftUI
import RealityKit

private enum BurstKind {
    case goal
    case save
    case pipe
}

private struct BurstParticle {
    let entity: ModelEntity
    let kind: BurstKind
    var velocity: SIMD3<Float> = .zero
    var life: Float = 0
    var maximumLife: Float = 0.7
}

@MainActor
final class PocketLaxScene {
    private let ballStart = SIMD3<Float>(0, 0.18, 1.45)

    private var ball: ModelEntity?
    private var camera: Entity?
    private var goalie: Entity?
    private var shooter: Entity?
    private var shooterStick: Entity?
    private var shooterTorso: ModelEntity?
    private var shooterHead: ModelEntity?
    private var shooterEyes: [ModelEntity] = []
    private var goalieTorso: ModelEntity?
    private var goalieHead: ModelEntity?
    private var goalieEyes: [ModelEntity] = []
    private var goalNet: Entity?
    private var aimDots: [ModelEntity] = []
    private var targetMarkers: [ModelEntity] = []
    private var ballTrail: [ModelEntity] = []
    private var trailHistory: [SIMD3<Float>] = []
    private var burstParticles: [BurstParticle] = []

    private let feedbackPlayer = GameFeedbackPlayer()
    private var subscriptions: [EventSubscription] = []
    private var shotTask: Task<Void, Never>?

    private var elapsedTime: TimeInterval = 0
    private var isAiming = false
    private var aimPower: Float = 0
    private var aimDirection: Float = 0
    private var releaseTime: Float = 0
    private var celebrationTime: Float = 0
    private var disappointmentTime: Float = 0
    private var goalieReactionTime: Float = 0
    private var goalieReactionDirection: Float = 0
    private var goalieSlumpTime: Float = 0
    private var netPulseTime: Float = 0
    private var cameraKickTime: Float = 0
    private var impactShakeTime: Float = 0
    private var selectedShotType: ShotType = .overhand
    private var activeShotType: ShotType?
    private var activeCurveDirection: Float = 0
    private var isBuilt = false

    func build(in content: inout RealityViewCameraContent, session: GameSession) {
        guard !isBuilt else { return }
        isBuilt = true

        let root = Entity()
        root.name = "Lax Attack Arena"

        addBackdrop(to: root)
        addField(to: root)
        addArenaDetails(to: root)
        addGoal(to: root)
        addGoalSensor(to: root)
        addGoalie(to: root)
        addShooter(to: root)
        addAimGuide(to: root)
        addTargetMarkers(to: root)
        addBallTrail(to: root)
        addBurstEffects(to: root)
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
            content.subscribe(to: SceneEvents.Update.self) { [weak self, weak session] event in
                guard let self, let session else { return }
                self.update(deltaTime: event.deltaTime, session: session)
            }
        )
    }

    func setShotType(_ type: ShotType) {
        selectedShotType = type
    }

    func updateAim(using sample: ShotControlSample, shotType: ShotType) {
        isAiming = true
        selectedShotType = shotType
        aimPower += (sample.power - aimPower) * 0.35
        aimDirection += (sample.direction - aimDirection) * 0.35

        let velocity = shotVelocity(sample: sample, type: shotType)
        for (index, dot) in aimDots.enumerated() {
            let time = Float(index + 1) * 0.115
            let gravity = SIMD3<Float>(0, -4.9 * time * time, 0)
            let curve = shotType == .sidearm
                ? SIMD3<Float>(sample.direction * 0.48 * time * time, 0, 0)
                : .zero
            dot.position = ballStart + velocity * time + gravity + curve
            dot.isEnabled = dot.position.y > 0.05 && dot.position.z > -5.4
        }
    }

    func hideAimGuide() {
        isAiming = false
        for dot in aimDots {
            dot.isEnabled = false
        }
    }

    func shoot(
        using sample: ShotControlSample,
        shotType: ShotType,
        session: GameSession
    ) {
        guard let ball else { return }

        let input = ShotInput(
            horizontal: sample.direction,
            power: sample.power,
            releaseSpeed: sample.releaseSpeed,
            type: shotType
        )
        guard session.beginShot(input: input) else { return }

        shotTask?.cancel()
        feedbackPlayer.playRelease(type: shotType)

        aimPower = sample.power
        aimDirection = sample.direction
        releaseTime = 0.62
        selectedShotType = shotType
        activeShotType = shotType
        activeCurveDirection = abs(sample.direction) > 0.12 ? sample.direction : 1
        cameraKickTime = 0.34

        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .dynamic
        ball.components.set(body)

        let velocity = shotVelocity(sample: sample, type: shotType)
        ball.applyLinearImpulse(velocity * body.massProperties.mass, relativeTo: nil)

        shotTask = Task { @MainActor [weak self, weak session] in
            try? await Task.sleep(for: .seconds(2.5))
            guard !Task.isCancelled, let self, let session else { return }

            if session.registerMiss() {
                self.disappointmentTime = 0.7
                self.feedbackPlayer.playMiss()
                await self.resetAfterResult(session: session, delay: .seconds(0.5))
            }
        }
    }

    func prepareForNewRound() {
        shotTask?.cancel()
        celebrationTime = 0
        disappointmentTime = 0
        goalieReactionTime = 0
        goalieSlumpTime = 0
        selectedShotType = .overhand
        resetBall()
    }

    func stop() {
        shotTask?.cancel()
        subscriptions.removeAll()
    }

    private func shotVelocity(sample: ShotControlSample, type: ShotType) -> SIMD3<Float> {
        switch type {
        case .overhand:
            return [
                sample.direction * 2.25,
                2.5 + sample.power * 1.18,
                -(8.8 + sample.power * 1.92)
            ]
        case .bounce:
            return [
                sample.direction * 2.15,
                0.22 + sample.power * 0.22,
                -(9.2 + sample.power * 1.65)
            ]
        case .sidearm:
            return [
                sample.direction * 1.7,
                1.7 + sample.power * 0.72,
                -(9.5 + sample.power * 1.78)
            ]
        }
    }

    private func handleCollision(_ event: CollisionEvents.Began, session: GameSession) {
        let names = Set([event.entityA.name, event.entityB.name])
        guard names.contains("Ball") else { return }

        if names.contains("Goal Sensor") {
            let style = goalStyle(for: ball?.position ?? .zero)
            if session.registerGoal(style: style) {
                celebrationTime = 1
                goalieSlumpTime = 0.8
                netPulseTime = 0.45
                impactShakeTime = 0.42
                emitBurst(.goal, at: ball?.position ?? [0, 1, -4.7])
                feedbackPlayer.playGoal()
                scheduleReset(session: session)
            }
        } else if names.contains("Goalie"), session.registerSave() {
            let ballX = ball?.position.x ?? 0
            let goalieX = goalie?.position.x ?? 0
            goalieReactionDirection = ballX >= goalieX ? 1 : -1
            goalieReactionTime = 0.75
            impactShakeTime = 0.25
            disappointmentTime = 0.65
            emitBurst(.save, at: ball?.position ?? [0, 0.8, -4.3])
            feedbackPlayer.playSave()
            scheduleReset(session: session)
        } else if names.contains("Goal Pipe") {
            session.registerPipe()
            impactShakeTime = 0.32
            emitBurst(.pipe, at: ball?.position ?? [0, 1, -4.5])
            feedbackPlayer.playPipe()
        } else if names.contains("Field") {
            session.registerBounce()
        }
    }

    private func goalStyle(for position: SIMD3<Float>) -> GoalStyle {
        let isHigh = position.y > 1.35
        let isWide = abs(position.x) > 0.48
        if isHigh && isWide { return .topCorner }
        if position.y < 0.62 && abs(position.x) > 0.55 { return .lowCorner }
        if position.y < 0.58 && abs(position.x) < 0.28 { return .fiveHole }
        return .standard
    }

    private func scheduleReset(session: GameSession) {
        shotTask?.cancel()
        shotTask = Task { @MainActor [weak self, weak session] in
            guard let self, let session else { return }
            await self.resetAfterResult(session: session, delay: .seconds(0.82))
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
        activeShotType = nil
        activeCurveDirection = 0
        trailHistory.removeAll(keepingCapacity: true)
        for trail in ballTrail {
            trail.isEnabled = false
        }
    }

    private func update(deltaTime: TimeInterval, session: GameSession) {
        elapsedTime += deltaTime
        updateGoalie(deltaTime: Float(deltaTime), level: session.difficultyLevel)
        updateShooter(deltaTime: Float(deltaTime))
        updateCharacterEyes()
        updateBallTrail(isActive: session.isAwaitingResult)
        updateBurstEffects(deltaTime: Float(deltaTime))
        updateGoalNet(deltaTime: Float(deltaTime))
        updateTargetMarkers()
        updateShotPhysics(deltaTime: Float(deltaTime), isActive: session.isAwaitingResult)
        updateCamera(deltaTime: Float(deltaTime))
    }

    private func updateGoalie(deltaTime: Float, level: Int) {
        guard let goalie else { return }

        let speed = 1.15 + Float(level) * 0.2
        let amplitude = 0.45 + Float(level) * 0.06
        let readyBounce = sin(Float(elapsedTime) * 4.6) * 0.018
        var x = sin(Float(elapsedTime) * speed) * amplitude
        var rootY = readyBounce
        var roll: Float = 0
        var squash = SIMD3<Float>(1, 1, 1)

        if goalieReactionTime > 0 {
            goalieReactionTime = max(0, goalieReactionTime - deltaTime)
            let progress = min(1, 1 - goalieReactionTime / 0.75)
            let attack = sin(progress * .pi)
            let recoil = sin(progress * .pi * 2) * (1 - progress)
            x += goalieReactionDirection * attack * 0.34
            rootY += attack * 0.12
            roll = -goalieReactionDirection * (attack * 0.46 + recoil * 0.08)
            squash = [1 + attack * 0.12, 1 - attack * 0.08, 1]
        } else if goalieSlumpTime > 0 {
            goalieSlumpTime = max(0, goalieSlumpTime - deltaTime)
            let progress = min(1, 1 - goalieSlumpTime / 0.8)
            let slump = sin(progress * .pi)
            rootY -= slump * 0.1
            roll = sin(progress * .pi) * 0.14
            squash = [1.06, 0.91, 1]
        }

        goalie.position.x = x
        goalie.position.y = rootY
        goalie.orientation = simd_quatf(angle: roll, axis: [0, 0, 1])
        goalieTorso?.scale = squash
        goalieHead?.orientation = simd_quatf(
            angle: -roll * 0.35,
            axis: [0, 0, 1]
        )
    }

    private func updateShooter(deltaTime: Float) {
        guard let shooter, let shooterStick else { return }

        let idleBob = sin(Float(elapsedTime) * 2.4) * 0.012
        var rootY = idleBob
        var rootZ: Float = 1.72
        var rootRoll: Float = 0
        var stickAngle: Float = -0.28
        var torsoScale = SIMD3<Float>(1, 1, 1)
        var headTilt: Float = 0

        if isAiming {
            let normalizedPower = max(0, min(1, (aimPower - 0.65) / 1.55))
            rootY -= normalizedPower * 0.035
            rootZ += normalizedPower * 0.055
            rootRoll = -aimDirection * 0.1
            let shotWindup: Float
            switch selectedShotType {
            case .overhand: shotWindup = -0.36 - normalizedPower * 0.58
            case .bounce: shotWindup = -0.18 - normalizedPower * 0.42
            case .sidearm: shotWindup = -1.02 - normalizedPower * 0.24
            }
            stickAngle = shotWindup + aimDirection * 0.14
            torsoScale = [1 + normalizedPower * 0.06, 1 - normalizedPower * 0.055, 1]
            headTilt = aimDirection * 0.05
        } else if releaseTime > 0 {
            releaseTime = max(0, releaseTime - deltaTime)
            let progress = min(1, 1 - releaseTime / 0.62)
            let attack = sin(min(progress / 0.62, 1) * .pi * 0.5)
            let settle = progress > 0.62
                ? sin((progress - 0.62) / 0.38 * .pi) * (1 - progress)
                : 0
            rootY += attack * 0.045
            rootZ -= attack * 0.17
            rootRoll = aimDirection * attack * 0.2 - aimDirection * settle * 0.08
            switch selectedShotType {
            case .overhand:
                stickAngle = -0.94 + attack * 1.72 - settle * 0.24
            case .bounce:
                stickAngle = -0.62 + attack * 1.38 - settle * 0.18
            case .sidearm:
                stickAngle = -1.18 + attack * 2.15 - settle * 0.3
                rootRoll += activeCurveDirection * attack * 0.12
            }
            torsoScale = [1 - attack * 0.08, 1 + attack * 0.11, 1]
            headTilt = -aimDirection * attack * 0.09
        } else if celebrationTime > 0 {
            celebrationTime = max(0, celebrationTime - deltaTime)
            let progress = 1 - celebrationTime
            let jump = abs(sin(progress * .pi * 2))
            rootY += jump * 0.18
            rootRoll = sin(progress * .pi * 2) * 0.12
            stickAngle = 0.85
            torsoScale = [1 - jump * 0.07, 1 + jump * 0.1, 1]
        } else if disappointmentTime > 0 {
            disappointmentTime = max(0, disappointmentTime - deltaTime)
            let progress = 1 - disappointmentTime / 0.7
            let slump = sin(progress * .pi)
            rootY -= slump * 0.05
            rootRoll = slump * -0.1
            stickAngle = -0.05
            torsoScale = [1.05, 0.93, 1]
            headTilt = -0.12
        }

        shooter.position.y = rootY
        shooter.position.z = rootZ
        shooter.orientation = simd_quatf(angle: rootRoll, axis: [0, 0, 1])
        shooterStick.orientation = simd_quatf(angle: stickAngle, axis: [0, 0, 1])
        shooterTorso?.scale = torsoScale
        shooterHead?.orientation = simd_quatf(angle: headTilt, axis: [0, 1, 0])
    }

    private func updateCharacterEyes() {
        guard let ball else { return }

        let blink = sin(Float(elapsedTime) * 1.85) > 0.985
        let shooterLook = max(-0.018, min(0.018, ball.position.x * 0.012))
        for eye in shooterEyes {
            let restingX: Float = eye.position.x < 0 ? -0.09 : 0.09
            eye.position.x += (restingX + shooterLook - eye.position.x) * 0.08
            eye.scale.y = blink ? 0.15 : 1
        }

        let goalieX = goalie?.position.x ?? 0
        let goalieLook = max(-0.022, min(0.022, (ball.position.x - goalieX) * 0.018))
        for eye in goalieEyes {
            let restingX: Float = eye.position.x < 0 ? -0.065 : 0.065
            eye.position.x += (restingX + goalieLook - eye.position.x) * 0.1
            eye.scale.y = blink ? 0.15 : 1
        }
    }

    private func updateShotPhysics(deltaTime: Float, isActive: Bool) {
        guard isActive, activeShotType == .sidearm, let ball else { return }
        guard var motion = ball.components[PhysicsMotionComponent.self] else { return }

        let progress = max(0, min(1, (-ball.position.z - 0.5) / 5.2))
        let lateCurve = progress * progress
        motion.linearVelocity.x += activeCurveDirection * lateCurve * 1.35 * deltaTime
        motion.angularVelocity = [0, 0, -activeCurveDirection * 18]
        ball.components.set(motion)
    }

    private func updateCamera(deltaTime: Float) {
        guard let camera else { return }

        cameraKickTime = max(0, cameraKickTime - deltaTime)
        impactShakeTime = max(0, impactShakeTime - deltaTime)

        let kickProgress = cameraKickTime / 0.34
        let kick = sin((1 - kickProgress) * .pi) * kickProgress
        let shakeProgress = impactShakeTime / 0.42
        let shake = sin(Float(elapsedTime) * 54) * shakeProgress * 0.035
        let from = SIMD3<Float>(
            shake,
            2.9 + abs(shake) * 0.5,
            6.1 - kick * 0.16
        )
        camera.look(
            at: [shake * 0.25, 0.95, -3.85],
            from: from,
            relativeTo: camera.parent
        )
    }

    private func addBallTrail(to root: Entity) {
        let material = SimpleMaterial(
            color: .init(red: 0.82, green: 0.95, blue: 1, alpha: 1),
            isMetallic: false
        )
        for index in 0..<9 {
            let radius = 0.066 - Float(index) * 0.0048
            let particle = ModelEntity(
                mesh: .generateSphere(radius: radius),
                materials: [material]
            )
            particle.isEnabled = false
            ballTrail.append(particle)
            root.addChild(particle)
        }
    }

    private func updateBallTrail(isActive: Bool) {
        guard isActive, let ball else {
            for particle in ballTrail {
                particle.isEnabled = false
            }
            return
        }

        if let last = trailHistory.last {
            if simd_distance(last, ball.position) > 0.075 {
                trailHistory.append(ball.position)
            }
        } else {
            trailHistory.append(ball.position)
        }
        if trailHistory.count > ballTrail.count {
            trailHistory.removeFirst(trailHistory.count - ballTrail.count)
        }

        for (index, particle) in ballTrail.enumerated() {
            let historyIndex = trailHistory.count - 1 - index
            guard historyIndex >= 0 else {
                particle.isEnabled = false
                continue
            }
            particle.position = trailHistory[historyIndex]
            particle.scale = .one * (1 - Float(index) * 0.07)
            particle.isEnabled = true
        }
    }

    private func addBurstEffects(to root: Entity) {
        let materials: [(BurstKind, SimpleMaterial)] = [
            (.goal, SimpleMaterial(color: .systemYellow, isMetallic: false)),
            (.save, SimpleMaterial(color: .systemCyan, isMetallic: false)),
            (.pipe, SimpleMaterial(color: .systemOrange, isMetallic: false))
        ]
        for (kind, material) in materials {
            for _ in 0..<10 {
                let particle = ModelEntity(
                    mesh: .generateSphere(radius: 0.055),
                    materials: [material]
                )
                particle.isEnabled = false
                root.addChild(particle)
                burstParticles.append(BurstParticle(entity: particle, kind: kind))
            }
        }
    }

    private func emitBurst(_ kind: BurstKind, at position: SIMD3<Float>) {
        let indices = burstParticles.indices.filter {
            burstParticles[$0].kind == kind && burstParticles[$0].life <= 0
        }
        for (order, index) in indices.prefix(10).enumerated() {
            let angle = Float(order) / 10 * .pi * 2
            let vertical = 0.65 + Float(order % 3) * 0.18
            burstParticles[index].entity.position = position
            burstParticles[index].entity.scale = .one
            burstParticles[index].entity.isEnabled = true
            burstParticles[index].velocity = [
                cos(angle) * 1.25,
                vertical,
                sin(angle) * 0.72
            ]
            burstParticles[index].life = 0.72
            burstParticles[index].maximumLife = 0.72
        }
    }

    private func updateBurstEffects(deltaTime: Float) {
        for index in burstParticles.indices where burstParticles[index].life > 0 {
            burstParticles[index].life = max(0, burstParticles[index].life - deltaTime)
            burstParticles[index].velocity.y -= 2.2 * deltaTime
            burstParticles[index].entity.position += burstParticles[index].velocity * deltaTime
            let scale = max(0.05, burstParticles[index].life / burstParticles[index].maximumLife)
            burstParticles[index].entity.scale = .one * scale
            if burstParticles[index].life == 0 {
                burstParticles[index].entity.isEnabled = false
            }
        }
    }

    private func updateGoalNet(deltaTime: Float) {
        guard let goalNet else { return }

        if netPulseTime > 0 {
            netPulseTime = max(0, netPulseTime - deltaTime)
            let progress = 1 - netPulseTime / 0.45
            let pulse = sin(progress * .pi) * 0.08
            goalNet.scale = [1 + pulse, 1 + pulse, 1]
        } else {
            goalNet.scale = .one
        }
    }

    private func updateTargetMarkers() {
        for (index, marker) in targetMarkers.enumerated() {
            let phase = Float(elapsedTime) * 2.2 + Float(index) * 0.8
            let pulse = 0.9 + sin(phase) * 0.1
            marker.scale = [pulse, pulse, 0.18]
        }
    }

    private func addBackdrop(to root: Entity) {
        let sky = SimpleMaterial(
            color: .init(red: 0.35, green: 0.67, blue: 0.96, alpha: 1),
            isMetallic: false
        )
        addDecorativeBox(
            size: [16, 8, 0.12],
            position: [0, 3.2, -8.2],
            material: sky,
            to: root
        )

        let hillMaterial = SimpleMaterial(
            color: .init(red: 0.16, green: 0.35, blue: 0.28, alpha: 1),
            isMetallic: false
        )
        for (x, scale): (Float, Float) in [(-4.5, 1.6), (-2.4, 1.2), (2.5, 1.4), (4.6, 1.8)] {
            let hill = ModelEntity(
                mesh: .generateSphere(radius: scale),
                materials: [hillMaterial]
            )
            hill.position = [x, 0.7, -7.9]
            hill.scale.y = 1.35
            root.addChild(hill)
        }

        let cloudMaterial = SimpleMaterial(color: .white, isMetallic: false)
        for x: Float in [-3.2, 0.5, 3.6] {
            let cloud = Entity()
            cloud.position = [x, 4.4 + abs(x) * 0.05, -8]
            for offset: SIMD3<Float> in [[-0.35, 0, 0], [0, 0.12, 0], [0.38, 0, 0]] {
                let puff = ModelEntity(
                    mesh: .generateSphere(radius: 0.42),
                    materials: [cloudMaterial]
                )
                puff.position = offset
                cloud.addChild(puff)
            }
            root.addChild(cloud)
        }
    }

    private func addField(to root: Entity) {
        let fieldSize = SIMD3<Float>(7, 0.1, 14)
        let shape = ShapeResource.generateBox(size: fieldSize)
        let turf = SimpleMaterial(
            color: .init(red: 0.16, green: 0.53, blue: 0.2, alpha: 1),
            isMetallic: false
        )
        let field = ModelEntity(
            mesh: .generateBox(size: fieldSize, cornerRadius: 0.08),
            materials: [turf]
        )
        field.name = "Field"
        field.position = [0, -0.05, -1]
        field.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        field.components.set(
            PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .static)
        )
        root.addChild(field)

        let white = SimpleMaterial(color: .white, isMetallic: false)
        for x: Float in [-2.7, 2.7] {
            addDecorativeBox(
                size: [0.035, 0.012, 11.8],
                position: [x, 0.012, -1],
                material: white,
                to: root
            )
        }

        for z: Float in [-5.9, 4.9] {
            addDecorativeBox(
                size: [5.4, 0.012, 0.035],
                position: [0, 0.012, z],
                material: white,
                to: root
            )
        }

        addDecorativeBox(
            size: [5.4, 0.012, 0.025],
            position: [0, 0.012, -0.6],
            material: white,
            to: root
        )
        addDecorativeBox(
            size: [2.6, 0.015, 0.045],
            position: [0, 0.014, -4.25],
            material: white,
            to: root
        )
    }

    private func addArenaDetails(to root: Entity) {
        let wood = SimpleMaterial(
            color: .init(red: 0.34, green: 0.16, blue: 0.07, alpha: 1),
            isMetallic: false
        )
        for x: Float in [-3.25, 3.25] {
            addDecorativeBox(
                size: [0.32, 0.65, 11.5],
                position: [x, 0.32, -1.2],
                material: wood,
                to: root
            )
        }

        let darkGreen = SimpleMaterial(
            color: .init(red: 0.05, green: 0.24, blue: 0.12, alpha: 1),
            isMetallic: false
        )
        let trunk = SimpleMaterial(
            color: .init(red: 0.3, green: 0.14, blue: 0.05, alpha: 1),
            isMetallic: false
        )

        for x: Float in [-3.8, -2.9, 2.9, 3.8] {
            let tree = Entity()
            tree.position = [x, 0, -6.9]

            let trunkModel = ModelEntity(
                mesh: .generateBox(size: [0.16, 0.9, 0.16], cornerRadius: 0.04),
                materials: [trunk]
            )
            trunkModel.position.y = 0.45
            tree.addChild(trunkModel)

            for (height, radius): (Float, Float) in [(0.9, 0.55), (1.35, 0.42), (1.7, 0.28)] {
                let crown = ModelEntity(
                    mesh: .generateSphere(radius: radius),
                    materials: [darkGreen]
                )
                crown.position.y = height
                crown.scale.y = 1.25
                tree.addChild(crown)
            }
            root.addChild(tree)
        }
    }

    private func addGoal(to root: Entity) {
        let pipeMaterial = SimpleMaterial(
            color: .init(red: 0.92, green: 0.16, blue: 0.12, alpha: 1),
            isMetallic: false
        )
        let netMaterial = SimpleMaterial(color: .white, isMetallic: false)

        addGoalBar(size: [0.1, 2, 0.1], position: [-1, 1, -4.5], material: pipeMaterial, to: root)
        addGoalBar(size: [0.1, 2, 0.1], position: [1, 1, -4.5], material: pipeMaterial, to: root)
        addGoalBar(size: [2.1, 0.1, 0.1], position: [0, 2, -4.5], material: pipeMaterial, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [-1, 0.03, -5.1], material: pipeMaterial, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [1, 0.03, -5.1], material: pipeMaterial, to: root)
        addGoalBar(size: [2.1, 0.06, 0.06], position: [0, 0.03, -5.7], material: pipeMaterial, to: root)

        let net = Entity()
        net.position = [0, 1, -5.67]

        for x: Float in [-0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75] {
            let line = ModelEntity(
                mesh: .generateBox(size: [0.018, 1.65, 0.018]),
                materials: [netMaterial]
            )
            line.position.x = x
            net.addChild(line)
        }

        for y: Float in [-0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75] {
            let line = ModelEntity(
                mesh: .generateBox(size: [1.8, 0.018, 0.018]),
                materials: [netMaterial]
            )
            line.position.y = y
            net.addChild(line)
        }

        goalNet = net
        root.addChild(net)
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
        goalie.position = [0, 0.625, -4.25]

        let navy = SimpleMaterial(
            color: .init(red: 0.05, green: 0.2, blue: 0.55, alpha: 1),
            isMetallic: false
        )
        let white = SimpleMaterial(color: .white, isMetallic: false)
        let skin = SimpleMaterial(
            color: .init(red: 0.78, green: 0.55, blue: 0.38, alpha: 1),
            isMetallic: false
        )
        let dark = SimpleMaterial(
            color: .init(red: 0.04, green: 0.06, blue: 0.1, alpha: 1),
            isMetallic: false
        )

        let torso = ModelEntity(
            mesh: .generateBox(size: [0.44, 0.5, 0.22], cornerRadius: 0.11),
            materials: [navy]
        )
        torso.position = [0, -0.005, 0]
        goalieTorso = torso
        goalie.addChild(torso)

        let helmet = ModelEntity(
            mesh: .generateSphere(radius: 0.23),
            materials: [white]
        )
        helmet.position = [0, 0.4, 0]
        goalieHead = helmet
        goalie.addChild(helmet)

        let face = ModelEntity(
            mesh: .generateSphere(radius: 0.16),
            materials: [skin]
        )
        face.position = [0, 0.38, 0.14]
        goalie.addChild(face)

        for x: Float in [-0.13, 0.13] {
            let eye = ModelEntity(
                mesh: .generateSphere(radius: 0.027),
                materials: [dark]
            )
            eye.position = [x, 0.41, 0.29]
            goalieEyes.append(eye)
            goalie.addChild(eye)

            let leg = ModelEntity(
                mesh: .generateBox(size: [0.15, 0.38, 0.17], cornerRadius: 0.06),
                materials: [navy]
            )
            leg.position = [x, -0.375, 0]
            goalie.addChild(leg)
        }

        let stick = makeStick(
            shaftMaterial: white,
            headMaterial: white,
            scale: 0.85
        )
        stick.position = [0.38, -0.02, 0.08]
        stick.orientation = simd_quatf(angle: -0.3, axis: [0, 0, 1])
        goalie.addChild(stick)

        let collisionSize = SIMD3<Float>(0.68, 1.25, 0.3)
        let shape = ShapeResource.generateBox(size: collisionSize)
        goalie.components.set(
            CollisionComponent(shapes: [shape], mode: .colliding)
        )
        goalie.components.set(
            PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .kinematic)
        )

        self.goalie = goalie
        root.addChild(goalie)
    }

    private func addShooter(to root: Entity) {
        let shooter = Entity()
        shooter.position = [-0.72, 0, 1.72]

        let jersey = SimpleMaterial(color: .white, isMetallic: false)
        let navy = SimpleMaterial(
            color: .init(red: 0.04, green: 0.18, blue: 0.5, alpha: 1),
            isMetallic: false
        )
        let skin = SimpleMaterial(
            color: .init(red: 0.82, green: 0.6, blue: 0.42, alpha: 1),
            isMetallic: false
        )
        let hair = SimpleMaterial(
            color: .init(red: 0.2, green: 0.08, blue: 0.03, alpha: 1),
            isMetallic: false
        )
        let dark = SimpleMaterial(
            color: .init(red: 0.03, green: 0.04, blue: 0.07, alpha: 1),
            isMetallic: false
        )

        let torso = ModelEntity(
            mesh: .generateBox(size: [0.5, 0.56, 0.25], cornerRadius: 0.13),
            materials: [jersey]
        )
        torso.position = [0, 0.65, 0]
        shooterTorso = torso
        shooter.addChild(torso)

        let shorts = ModelEntity(
            mesh: .generateBox(size: [0.46, 0.22, 0.25], cornerRadius: 0.06),
            materials: [navy]
        )
        shorts.position = [0, 0.35, 0]
        shooter.addChild(shorts)

        for x: Float in [-0.14, 0.14] {
            let leg = ModelEntity(
                mesh: .generateBox(size: [0.14, 0.38, 0.16], cornerRadius: 0.06),
                materials: [skin]
            )
            leg.position = [x, 0.13, 0]
            shooter.addChild(leg)

            let eye = ModelEntity(
                mesh: .generateSphere(radius: 0.03),
                materials: [dark]
            )
            eye.position = [x * 0.65, 1.08, 0.25]
            shooterEyes.append(eye)
            shooter.addChild(eye)
        }

        let head = ModelEntity(
            mesh: .generateSphere(radius: 0.23),
            materials: [skin]
        )
        head.position = [0, 1.05, 0.02]
        shooterHead = head
        shooter.addChild(head)

        let hairCap = ModelEntity(
            mesh: .generateSphere(radius: 0.235),
            materials: [hair]
        )
        hairCap.position = [0, 1.12, -0.04]
        hairCap.scale.y = 0.65
        shooter.addChild(hairCap)

        let stick = makeStick(
            shaftMaterial: navy,
            headMaterial: jersey,
            scale: 1
        )
        stick.position = [0.34, 0.7, 0.12]
        shooter.addChild(stick)

        self.shooter = shooter
        shooterStick = stick
        root.addChild(shooter)
    }

    private func makeStick(
        shaftMaterial: SimpleMaterial,
        headMaterial: SimpleMaterial,
        scale: Float
    ) -> Entity {
        let stick = Entity()

        let shaft = ModelEntity(
            mesh: .generateBox(size: [0.055, 1.05, 0.055], cornerRadius: 0.018),
            materials: [shaftMaterial]
        )
        shaft.position.y = -0.2
        stick.addChild(shaft)

        let head = ModelEntity(
            mesh: .generateBox(size: [0.34, 0.42, 0.07], cornerRadius: 0.1),
            materials: [headMaterial]
        )
        head.position.y = 0.47
        stick.addChild(head)

        let pocket = ModelEntity(
            mesh: .generateBox(size: [0.24, 0.3, 0.025], cornerRadius: 0.07),
            materials: [SimpleMaterial(color: .white, isMetallic: false)]
        )
        pocket.position = [0, 0.47, 0.05]
        stick.addChild(pocket)

        stick.scale = .one * scale
        return stick
    }

    private func addAimGuide(to root: Entity) {
        let guideMaterial = SimpleMaterial(
            color: .init(red: 1, green: 0.82, blue: 0.12, alpha: 1),
            isMetallic: false
        )

        for index in 0..<12 {
            let radius: Float = index < 4 ? 0.045 : 0.032
            let dot = ModelEntity(
                mesh: .generateSphere(radius: radius),
                materials: [guideMaterial]
            )
            dot.isEnabled = false
            aimDots.append(dot)
            root.addChild(dot)
        }
    }

    private func addTargetMarkers(to root: Entity) {
        let material = SimpleMaterial(
            color: .init(red: 1, green: 0.78, blue: 0.08, alpha: 0.72),
            isMetallic: false
        )
        let positions: [SIMD3<Float>] = [
            [-0.72, 1.67, -4.82],
            [0.72, 1.67, -4.82],
            [-0.72, 0.38, -4.82],
            [0, 0.38, -4.82],
            [0.72, 0.38, -4.82]
        ]

        for position in positions {
            let marker = ModelEntity(
                mesh: .generateSphere(radius: 0.105),
                materials: [material]
            )
            marker.position = position
            marker.scale.z = 0.18
            targetMarkers.append(marker)
            root.addChild(marker)
        }
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
        var component = PerspectiveCameraComponent()
        component.fieldOfViewInDegrees = 52
        camera.components.set(component)
        camera.look(
            at: [0, 0.95, -3.85],
            from: [0, 2.9, 6.1],
            relativeTo: root
        )
        self.camera = camera
        root.addChild(camera)
    }

    private func addLighting(to root: Entity) {
        let light = Entity()
        light.components.set(
            DirectionalLightComponent(color: .white, intensity: 3_200)
        )
        light.look(at: [0, 0, -2], from: [-3, 7, 4], relativeTo: root)
        root.addChild(light)
    }

    private func addDecorativeBox(
        size: SIMD3<Float>,
        position: SIMD3<Float>,
        material: SimpleMaterial,
        to root: Entity
    ) {
        let model = ModelEntity(
            mesh: .generateBox(size: size, cornerRadius: min(size.x, size.z) * 0.08),
            materials: [material]
        )
        model.position = position
        root.addChild(model)
    }
}
