import SwiftUI
import RealityKit

@MainActor
final class PocketLaxScene {
    private let ballStart = SIMD3<Float>(0, 0.18, 1.45)

    private var ball: ModelEntity?
    private var goalie: Entity?
    private var shooter: Entity?
    private var shooterStick: Entity?
    private var goalNet: Entity?
    private var aimDots: [ModelEntity] = []

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

    func updateAim(using translation: CGSize) {
        let power = min(max(Float(-translation.height) / 140, 0.8), 2.2)
        let direction = min(max(Float(translation.width) / 140, -1), 1)

        isAiming = true
        aimPower = power
        aimDirection = direction

        let velocity = shotVelocity(power: power, direction: direction)
        for (index, dot) in aimDots.enumerated() {
            let time = Float(index + 1) * 0.115
            let gravity = SIMD3<Float>(0, -4.9 * time * time, 0)
            dot.position = ballStart + velocity * time + gravity
            dot.isEnabled = dot.position.y > 0.05 && dot.position.z > -5.4
        }
    }

    func hideAimGuide() {
        isAiming = false
        for dot in aimDots {
            dot.isEnabled = false
        }
    }

    func shoot(using translation: CGSize, session: GameSession) {
        guard let ball else { return }

        let power = min(max(Float(-translation.height) / 140, 0.8), 2.2)
        let direction = min(max(Float(translation.width) / 140, -1), 1)
        let input = ShotInput(horizontal: direction, power: power)
        guard session.beginShot(input: input) else { return }

        shotTask?.cancel()
        feedbackPlayer.playRelease()

        aimPower = power
        aimDirection = direction
        releaseTime = 0.55

        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .dynamic
        ball.components.set(body)

        let velocity = shotVelocity(power: power, direction: direction)
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
        resetBall()
    }

    func stop() {
        shotTask?.cancel()
        subscriptions.removeAll()
    }

    private func shotVelocity(power: Float, direction: Float) -> SIMD3<Float> {
        SIMD3<Float>(
            direction * 1.55,
            1.9 + power * 1.18,
            -(7.4 + power * 2.3)
        )
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
                feedbackPlayer.playGoal()
                scheduleReset(session: session)
            }
        } else if names.contains("Goalie"), session.registerSave() {
            let ballX = ball?.position.x ?? 0
            let goalieX = goalie?.position.x ?? 0
            goalieReactionDirection = ballX >= goalieX ? 1 : -1
            goalieReactionTime = 0.75
            disappointmentTime = 0.65
            feedbackPlayer.playSave()
            scheduleReset(session: session)
        } else if names.contains("Goal Pipe") {
            session.registerPipe()
            feedbackPlayer.playPipe()
        } else if names.contains("Field") {
            session.registerBounce()
        }
    }

    private func goalStyle(for position: SIMD3<Float>) -> GoalStyle {
        let isHigh = position.y > 1.35
        let isWide = abs(position.x) > 0.48
        return isHigh && isWide ? .topCorner : .standard
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
    }

    private func update(deltaTime: TimeInterval, session: GameSession) {
        elapsedTime += deltaTime
        updateGoalie(deltaTime: Float(deltaTime), level: session.difficultyLevel)
        updateShooter(deltaTime: Float(deltaTime))
        updateGoalNet(deltaTime: Float(deltaTime))
    }

    private func updateGoalie(deltaTime: Float, level: Int) {
        guard let goalie else { return }

        let speed = 1.15 + Float(level) * 0.2
        let amplitude = 0.45 + Float(level) * 0.06
        var x = sin(Float(elapsedTime) * speed) * amplitude
        var roll: Float = 0

        if goalieReactionTime > 0 {
            goalieReactionTime = max(0, goalieReactionTime - deltaTime)
            let progress = 1 - goalieReactionTime / 0.75
            let arc = sin(progress * .pi)
            x += goalieReactionDirection * arc * 0.28
            roll = -goalieReactionDirection * arc * 0.42
        } else if goalieSlumpTime > 0 {
            goalieSlumpTime = max(0, goalieSlumpTime - deltaTime)
            let progress = 1 - goalieSlumpTime / 0.8
            roll = sin(progress * .pi) * 0.14
        }

        goalie.position.x = x
        goalie.orientation = simd_quatf(angle: roll, axis: [0, 0, 1])
    }

    private func updateShooter(deltaTime: Float) {
        guard let shooter, let shooterStick else { return }

        let idleBob = sin(Float(elapsedTime) * 2.4) * 0.012
        var rootY = idleBob
        var rootRoll: Float = 0
        var stickAngle: Float = -0.28

        if isAiming {
            let normalizedPower = (aimPower - 0.8) / 1.4
            rootRoll = -aimDirection * 0.08
            stickAngle = -0.35 - normalizedPower * 0.5 + aimDirection * 0.12
        } else if releaseTime > 0 {
            releaseTime = max(0, releaseTime - deltaTime)
            let progress = 1 - releaseTime / 0.55
            let snap = sin(min(progress, 1) * .pi)
            rootRoll = aimDirection * snap * 0.16
            stickAngle = -0.9 + progress * 1.55
        } else if celebrationTime > 0 {
            celebrationTime = max(0, celebrationTime - deltaTime)
            let progress = 1 - celebrationTime
            rootY += abs(sin(progress * .pi * 2)) * 0.18
            rootRoll = sin(progress * .pi * 2) * 0.12
            stickAngle = 0.85
        } else if disappointmentTime > 0 {
            disappointmentTime = max(0, disappointmentTime - deltaTime)
            let progress = 1 - disappointmentTime / 0.7
            rootRoll = sin(progress * .pi) * -0.1
            stickAngle = -0.05
        }

        shooter.position.y = rootY
        shooter.orientation = simd_quatf(angle: rootRoll, axis: [0, 0, 1])
        shooterStick.orientation = simd_quatf(angle: stickAngle, axis: [0, 0, 1])
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
        goalie.addChild(torso)

        let helmet = ModelEntity(
            mesh: .generateSphere(radius: 0.23),
            materials: [white]
        )
        helmet.position = [0, 0.4, 0]
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
            shooter.addChild(eye)
        }

        let head = ModelEntity(
            mesh: .generateSphere(radius: 0.23),
            materials: [skin]
        )
        head.position = [0, 1.05, 0.02]
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
