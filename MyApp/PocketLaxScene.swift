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

private struct ScenePerformanceProfile {
    let ambientEnvironmentEnabled: Bool
    let supportLOD: String
    let fanCount: Int

    static var current: ScenePerformanceProfile {
        let memory = ProcessInfo.processInfo.physicalMemory
        if memory < 5_000_000_000 {
            return ScenePerformanceProfile(
                ambientEnvironmentEnabled: false,
                supportLOD: "_lod2",
                fanCount: 2
            )
        }
        return ScenePerformanceProfile(
            // The current ambient export places animated tree trunks across the lake.
            // Keep the authored softened arena layers until Blender ships a corrected pass.
            ambientEnvironmentEnabled: false,
            supportLOD: "_lod1",
            fanCount: 3
        )
    }
}

@MainActor
final class PocketLaxScene {
    private static let physicsVersion = 1
    private static let useProductionShooter = true
    private let ballStart = SIMD3<Float>(0, 0.18, 1.45)
    private let quickStickCatch = SIMD3<Float>(-0.38, 1.16, 1.82)
    private let goalieBaseHeight: Float = 0.625
    private let goalLineZ: Float = -5.7
    private let shooterBaseX: Float = -0.25
    private let performanceProfile = ScenePerformanceProfile.current

    private var ball: ModelEntity?
    private var arenaRoot: Entity?
    private var proceduralEnvironment: Entity?
    private var camera: Entity?
    private var cameraRestPosition = SIMD3<Float>(-0.25, 4.8, 8.55)
    private var cameraRestTarget = SIMD3<Float>(-0.1, 0.58, -3.3)
    private var cameraPosition = SIMD3<Float>(-0.25, 4.8, 8.55)
    private var cameraTarget = SIMD3<Float>(-0.1, 0.58, -3.3)
    private var goalie: Entity?
    private var shooter: Entity?
    private var shooterStick: Entity?
    private var shooterTorso: ModelEntity?
    private var shooterHead: ModelEntity?
    private var shooterEyes: [ModelEntity] = []
    private var shooterArms: [ModelEntity] = []
    private var shooterLegs: [ModelEntity] = []
    private var shooterPonytail: Entity?
    private var shooterAnimationDriver: CharacterAnimationDriver?
    private var goalieAnimationDriver: CharacterAnimationDriver?
    private var goalAnimationDriver: TimelineAnimationDriver?
    private var ambientArenaDriver: TimelineAnimationDriver?
    private var ambientAnimationDrivers: [TimelineAnimationDriver] = []
    private var crowdAnimationDrivers: [TimelineAnimationDriver] = []
    private var goalieTorso: ModelEntity?
    private var goalieHead: ModelEntity?
    private var goalieEyes: [ModelEntity] = []
    private var goalieLegs: [ModelEntity] = []
    private var goalieStick: Entity?
    private var goalNet: Entity?
    private var aimDots: [ModelEntity] = []
    private var targetMarkers: [ModelEntity] = []
    private var calledShotTarget: Entity?
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
    private var goalieReadTime: Float = 0
    private var goalieReadDirection: Float = 0
    private var goalieReadStrength: Float = 0
    private var goalieShuffleDirection: Float = 1
    private var goalieCommitState: CharacterPerformanceState?
    private var goalieReactionState: CharacterPerformanceState = .goalieReady
    private var shooterReactionState: CharacterPerformanceState?
    private var shooterReactionTime: Float = 0
    private var netPulseTime: Float = 0
    private var netImpactOffset = SIMD2<Float>.zero
    private var cameraKickTime: Float = 0
    private var impactShakeTime: Float = 0
    private var resultCameraTime: Float = 0
    private var resultCameraFocus = SIMD3<Float>(0, 1, -5.4)
    private var calledShotHitTime: Float = 0
    private var ambientGustTime: Float = 0
    private var crowdReactionTime: Float = 0
    private var selectedShotType: ShotType = .overhand
    private var activeShotType: ShotType?
    private var activeCurveDirection: Float = 0
    private var activePerfectRelease = false
    private var isQuickStickSetup = false
    private var isBallLaunched = false
    private var quickStickPhase: Float = 0
    private var pendingDodgeDirection: Float = 0
    private var activeDodgeDirection: Float = 0
    private var isBuilt = false
    private(set) var shooterPerformanceState: CharacterPerformanceState = .idle
    private(set) var goaliePerformanceState: CharacterPerformanceState = .goalieReady

    func build(in content: inout RealityViewCameraContent, session: GameSession) {
        guard !isBuilt else { return }
        isBuilt = true

        let root = Entity()
        root.name = "Lax Attack Arena"
        arenaRoot = root

        let environment = Entity()
        environment.name = "Procedural Environment"
        proceduralEnvironment = environment
        root.addChild(environment)
        addSkyBackdrop(to: root)
        addBackdrop(to: environment)
        addField(to: root)
        addArenaDetails(to: environment)
        addGoal(to: root)
        addGoalSensor(to: root)
        addGoalie(to: root)
        addShooter(to: root)
        addAimGuide(to: root)
        addCalledShotTarget(to: root)
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

    func installAuthoredShooter() async {
        await installProductionAssets()
    }

    private func installProductionAssets() async {
        guard let arenaRoot else { return }

        await installArena(in: arenaRoot)
        await installArenaAmbient(in: arenaRoot)
        await installSupportCast(in: arenaRoot)
        await installGoal(in: arenaRoot)
        await installGoalie(in: arenaRoot)
        await installShooter(in: arenaRoot)
    }

    private func installShooter(in arenaRoot: Entity) async {
        guard Self.useProductionShooter, shooterAnimationDriver == nil else { return }

        do {
            let importedShooter = try await CharacterAssetContract.load(
                named: CharacterAssetContract.shooterAssetName
            )
            let driver = try CharacterAssetContract.prepareCharacter(
                importedShooter,
                manifestName: "lax_shooter_clips"
            )
            let socketReport = CharacterAssetContract.validate(importedShooter, role: .shooter)
            guard socketReport.missingSockets.isEmpty else {
                print("Authored shooter missing sockets: \(socketReport.missingSockets.joined(separator: ", "))")
                return
            }

            shooter?.removeFromParent()
            shooterTorso = nil
            shooterHead = nil
            shooterEyes.removeAll()
            shooterArms.removeAll()
            shooterLegs.removeAll()

            importedShooter.position = [shooterBaseX, 0, 1.72]
            arenaRoot.addChild(importedShooter)
            shooter = importedShooter
            shooterStick = importedShooter.findEntity(named: "stick_socket")
            shooterAnimationDriver = driver
            driver.transition(to: .idle, duration: 0)

            if !socketReport.isValid {
                print("Shooter contract warning — sockets: \(socketReport.missingSockets), clips: \(socketReport.missingAnimations)")
            }
        } catch {
            print("Using procedural shooter because lax_shooter failed to load: \(error)")
        }
    }

    private func installGoalie(in arenaRoot: Entity) async {
        guard goalieAnimationDriver == nil else { return }
        do {
            let importedGoalie = try await CharacterAssetContract.load(named: CharacterAssetContract.goalieAssetName)
            let driver = try CharacterAssetContract.prepareCharacter(
                importedGoalie,
                manifestName: "lax_goalie_clips"
            )
            let report = CharacterAssetContract.validate(importedGoalie, role: .goalie)
            guard report.missingSockets.isEmpty else {
                print("Authored goalie missing sockets: \(report.missingSockets)")
                return
            }

            goalie?.removeFromParent()
            goalieTorso = nil
            goalieHead = nil
            goalieEyes.removeAll()
            goalieLegs.removeAll()
            goalieStick = nil

            let controller = Entity()
            controller.name = "Goalie Controller"
            controller.position = [0, 0, goalLineZ + 0.5]
            importedGoalie.name = "Goalie Visual"
            controller.addChild(importedGoalie)

            let hitbox = Entity()
            hitbox.name = "Goalie"
            hitbox.position = [0, 0.625, 0]
            let shape = ShapeResource.generateBox(size: [0.68, 1.25, 0.3])
            hitbox.components.set(CollisionComponent(shapes: [shape], mode: .colliding))
            hitbox.components.set(PhysicsBodyComponent(shapes: [shape], density: 1_000, mode: .kinematic))
            controller.addChild(hitbox)

            arenaRoot.addChild(controller)
            goalie = controller
            goalieAnimationDriver = driver
            driver.transition(to: .goalieReady, duration: 0)
        } catch {
            print("Using procedural goalie because lax_goalie failed to load: \(error)")
        }
    }

    private func installGoal(in arenaRoot: Entity) async {
        guard goalAnimationDriver == nil else { return }
        do {
            let importedGoal = try await CharacterAssetContract.load(named: CharacterAssetContract.goalAssetName)
            let driver = try CharacterAssetContract.prepareTimeline(importedGoal, manifestName: "lax_goal_clips")
            importedGoal.position = [0, 0, goalLineZ]
            goalNet?.removeFromParent()
            goalNet = importedGoal
            hideModels(named: "Goal Pipe", under: arenaRoot)
            arenaRoot.addChild(importedGoal)
            goalAnimationDriver = driver
            driver.transition(to: "net_idle", duration: 0)
        } catch {
            print("Using procedural goal because lax_goal failed to load: \(error)")
        }
    }

    private func installArena(in arenaRoot: Entity) async {
        guard proceduralEnvironment?.isEnabled != false else { return }
        do {
            let importedArena = try await CharacterAssetContract.load(named: CharacterAssetContract.arenaAssetName)
            importedArena.name = "Production Arena"
            setGroup(named: "far_background", enabled: false, under: importedArena)
            setGroup(named: "far_background_soft", enabled: true, under: importedArena)
            setGroup(named: "foreground_framing", enabled: false, under: importedArena)
            setGroup(named: "foreground_framing_soft", enabled: true, under: importedArena)
            setGroup(named: "collision_only", enabled: false, under: importedArena)
            // The current mobile export contains sailboat masts without readable hulls/sails,
            // which look like tree trunks planted in the lake from the gameplay camera.
            setGroup(named: "sailboat", enabled: false, under: importedArena)
            setGroup(named: "sailboat_001", enabled: false, under: importedArena)
            arenaRoot.addChild(importedArena)
            adoptAuthoredCameraMarkers(from: importedArena, relativeTo: arenaRoot)
            proceduralEnvironment?.isEnabled = false
            arenaRoot.findEntity(named: "Field")?.components.remove(ModelComponent.self)
        } catch {
            print("Using procedural arena because lax_arena_pinebrook failed to load: \(error)")
        }
    }

    private func installArenaAmbient(in arenaRoot: Entity) async {
        guard performanceProfile.ambientEnvironmentEnabled, ambientArenaDriver == nil else { return }
        do {
            let ambient = try await CharacterAssetContract.load(named: CharacterAssetContract.arenaAmbientAssetName)
            let driver = try CharacterAssetContract.prepareTimeline(
                ambient,
                manifestName: "lax_arena_ambient_clips"
            )
            ambient.name = "Arena Ambient Life"
            arenaRoot.addChild(ambient)
            arenaRoot.findEntity(named: "Production Arena")
                .flatMap { $0.findEntity(named: "midground_trees") }?
                .isEnabled = false
            driver.transition(to: "ambient_loop", duration: 0)
            ambientArenaDriver = driver
        } catch {
            print("Skipping optional arena ambient animation: \(error)")
        }
    }

    private func hideModels(named name: String, under entity: Entity) {
        if entity.name == name { entity.components.remove(ModelComponent.self) }
        for child in entity.children { hideModels(named: name, under: child) }
    }

    private func setGroup(named name: String, enabled: Bool, under entity: Entity) {
        entity.findEntity(named: name)?.isEnabled = enabled
    }

    private func adoptAuthoredCameraMarkers(from arena: Entity, relativeTo root: Entity) {
        guard let marker = arena.findEntity(named: "camera_gameplay") else { return }
        cameraRestPosition = marker.position(relativeTo: root)
        if let target = arena.findEntity(named: "camera_gameplay_target") {
            cameraRestTarget = target.position(relativeTo: root)
        }
        cameraPosition = cameraRestPosition
        cameraTarget = cameraRestTarget
    }

    private func installSupportCast(in arenaRoot: Entity) async {
        guard ambientAnimationDrivers.isEmpty else { return }

        let fanPositions: [SIMD3<Float>] = [
            [-3.1, 0.55, -6.85],
            [3.15, 0.55, -6.9],
            [3.85, 0.55, -6.65]
        ]
        for (assetName, position) in zip(
            CharacterAssetContract.fanAssetNames.prefix(performanceProfile.fanCount),
            fanPositions
        ) {
            await installAmbientCharacter(
                named: "\(assetName)\(performanceProfile.supportLOD)",
                manifestName: "\(assetName)_clips",
                clipName: "crowd_idle",
                position: position,
                yaw: .pi,
                in: arenaRoot
            )
        }

        await installAmbientCharacter(
            named: "\(CharacterAssetContract.homeTeammateAssetName)\(performanceProfile.supportLOD)",
            manifestName: "lax_team_home_7_clips",
            clipName: "idle_relaxed",
            position: [-2.8, 0, -1.7],
            yaw: -.pi / 2,
            in: arenaRoot
        )
        await installAmbientCharacter(
            named: "\(CharacterAssetContract.awayTeammateAssetName)\(performanceProfile.supportLOD)",
            manifestName: "lax_team_away_5_clips",
            clipName: "idle_competitive",
            position: [2.8, 0, -3.3],
            yaw: .pi / 2,
            in: arenaRoot
        )
    }

    private func installAmbientCharacter(
        named assetName: String,
        manifestName: String,
        clipName: String,
        position: SIMD3<Float>,
        yaw: Float,
        in arenaRoot: Entity
    ) async {
        do {
            let entity = try await CharacterAssetContract.load(named: assetName)
            let driver = try CharacterAssetContract.prepareTimeline(entity, manifestName: manifestName)
            entity.position = position
            entity.orientation = simd_quatf(angle: yaw, axis: [0, 1, 0])
            arenaRoot.addChild(entity)
            driver.transition(to: clipName, duration: 0)
            ambientAnimationDrivers.append(driver)
            if clipName == "crowd_idle" {
                crowdAnimationDrivers.append(driver)
            }
        } catch {
            print("Skipping optional ambient asset \(assetName): \(error)")
        }
    }

    func setShotType(_ type: ShotType) {
        selectedShotType = type
    }

    func updateDodge(direction: Float) {
        pendingDodgeDirection = max(-1, min(1, direction))
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
            dot.position = (ball?.position ?? ballStart) + velocity * time + gravity + curve
            dot.isEnabled = dot.position.y > 0.05 && dot.position.z > goalLineZ + 0.25
        }
    }

    func hideAimGuide() {
        isAiming = false
        pendingDodgeDirection = 0
        for dot in aimDots {
            dot.isEnabled = false
        }
    }

    func shoot(
        using sample: ShotControlSample,
        shotType: ShotType,
        timingQuality: Float? = nil,
        dodgeDirection: Float = 0,
        session: GameSession
    ) {
        guard ball != nil else { return }

        let input = ShotInput(
            horizontal: sample.direction,
            power: sample.power,
            releaseSpeed: sample.releaseSpeed,
            type: shotType,
            timingQuality: timingQuality,
            dodgeDirection: dodgeDirection,
            wasOnFire: session.isOnFire,
            goaliePositionAtRelease: goalie?.position.x ?? 0,
            physicsVersion: Self.physicsVersion
        )
        guard session.beginShot(input: input) else { return }

        shotTask?.cancel()
        aimPower = sample.power
        aimDirection = sample.direction
        releaseTime = shooterAnimationDriver != nil ? 1.1 : 0.62
        selectedShotType = shotType
        activeShotType = shotType
        isBallLaunched = false
        activeCurveDirection = abs(sample.direction) > 0.12 ? sample.direction : 1
        activeDodgeDirection = dodgeDirection
        pendingDodgeDirection = 0
        activePerfectRelease = input.isPerfectRelease
        setBallAppearance(isOnFire: input.wasOnFire, isPerfectRelease: input.isPerfectRelease)
        goalieReadTime = shotType == .bounce ? 0.48 : 0.72
        goalieReadDirection = abs(dodgeDirection) > 0.5 ? -dodgeDirection : sample.direction
        let timingDeception = 1 - (timingQuality ?? 0)
        goalieReadStrength = 0.1 + Float(session.difficultyLevel) * 0.055
        if shotType == .quickStick {
            goalieReadStrength *= 0.35 + timingDeception * 0.65
        } else if abs(dodgeDirection) > 0.5 {
            goalieReadStrength += 0.16
        }

        let velocity = shotVelocity(sample: sample, type: shotType)
        let releaseState: CharacterPerformanceState
        switch shotType {
        case .overhand: releaseState = .releaseOverhand
        case .bounce: releaseState = .releaseBounce
        case .sidearm: releaseState = .releaseSidearm
        case .quickStick: releaseState = .quickStickRelease
        }
        let launchDelay = shooterAnimationDriver?.releaseDelay(for: releaseState) ?? 0

        shotTask = Task { @MainActor [weak self, weak session] in
            if launchDelay > 0 {
                try? await Task.sleep(for: .seconds(launchDelay))
            }
            guard !Task.isCancelled, let self else { return }
            self.launchBall(velocity: velocity, sample: sample, shotType: shotType)

            try? await Task.sleep(for: .seconds(2.5))
            guard !Task.isCancelled, let session else { return }

            if session.registerMiss() {
                self.disappointmentTime = 0.7
                self.shooterReactionState = .nearMissReaction
                self.shooterReactionTime = 0.8
                self.feedbackPlayer.playMiss()
                await self.resetAfterResult(session: session, delay: .seconds(0.5))
            }
        }
    }

    private func launchBall(
        velocity: SIMD3<Float>,
        sample: ShotControlSample,
        shotType: ShotType
    ) {
        guard let ball else { return }

        feedbackPlayer.playRelease(type: shotType)
        if activePerfectRelease {
            feedbackPlayer.playPerfectRelease()
        }
        cameraKickTime = 0.34

        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .dynamic
        switch shotType {
        case .bounce:
            body.material = .generate(
                staticFriction: 0.38,
                dynamicFriction: 0.28,
                restitution: 0.68
            )
        case .sidearm:
            body.material = .generate(
                staticFriction: 0.42,
                dynamicFriction: 0.34,
                restitution: 0.42
            )
        case .overhand, .quickStick:
            body.material = .generate(
                staticFriction: 0.5,
                dynamicFriction: 0.4,
                restitution: 0.34
            )
        }
        ball.components.set(body)
        isBallLaunched = true
        ball.applyLinearImpulse(velocity * body.massProperties.mass, relativeTo: nil)

        let spinAxis: SIMD3<Float>
        switch shotType {
        case .overhand: spinAxis = [12, sample.direction * 4, 0]
        case .bounce: spinAxis = [22, 0, sample.direction * 3]
        case .sidearm: spinAxis = [4, activeCurveDirection * 18, -activeCurveDirection * 8]
        case .quickStick: spinAxis = [15, sample.direction * 6, 0]
        }
        ball.applyAngularImpulse(spinAxis * body.massProperties.mass, relativeTo: nil)
    }

    func shootQuickStick(quality: Double, session: GameSession) {
        guard session.isQuickStickChallenge else { return }

        let clampedQuality = Float(max(0, min(1, quality)))
        let goalieX = goalie?.position.x ?? 0
        let placement: Float = goalieX >= 0 ? -0.58 : 0.58
        let timingError = (1 - clampedQuality) * sin(Float(elapsedTime) * 9) * 0.32
        let sample = ShotControlSample(
            direction: max(-1, min(1, placement + timingError)),
            power: 1.15 + clampedQuality * 1.05,
            releaseSpeed: 1_100 + clampedQuality * 1_000
        )
        ball?.position = quickStickCatch
        shoot(
            using: sample,
            shotType: .quickStick,
            timingQuality: clampedQuality,
            dodgeDirection: 0,
            session: session
        )
    }

    func prepareForNewRound() {
        shotTask?.cancel()
        celebrationTime = 0
        disappointmentTime = 0
        goalieReactionTime = 0
        goalieSlumpTime = 0
        goalieReadTime = 0
        resultCameraTime = 0
        goalieCommitState = nil
        shooterReactionState = nil
        shooterReactionTime = 0
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
                2.7 + sample.power * 1.28,
                -(8.45 + sample.power * 1.72)
            ]
        case .bounce:
            return [
                sample.direction * 2.15,
                -0.62 + sample.power * 0.12,
                -(10.15 + sample.power * 1.85)
            ]
        case .sidearm:
            return [
                sample.direction * 1.7,
                1.9 + sample.power * 0.66,
                -(10.35 + sample.power * 1.95)
            ]
        case .quickStick:
            return [
                sample.direction * 1.8,
                2.15 + sample.power * 0.72,
                -(10.4 + sample.power * 2.05)
            ]
        }
    }

    private func handleCollision(_ event: CollisionEvents.Began, session: GameSession) {
        let names = Set([event.entityA.name, event.entityB.name])
        guard names.contains("Ball") else { return }

        if names.contains("Goal Sensor") {
            let style = goalStyle(for: ball?.position ?? .zero)
            let resolvedShotType = activeShotType ?? selectedShotType
            let hitHotZone = session.activeHotZone.contains(ball?.position ?? .zero)
                && session.activeHotZone.accepts(resolvedShotType)
            if session.registerGoal(style: style, hitHotZone: hitHotZone) {
                calledShotHitTime = hitHotZone ? 0.72 : 0
                celebrationTime = 1
                let celebrations: [CharacterPerformanceState] = [
                    .celebrateFistPump,
                    .celebrateStickTwirl,
                    .celebrateJumpTuck,
                    .celebratePoint,
                    .celebrateRestrained
                ]
                let wasClutch = session.shotHistory.last?.wasClutch == true
                shooterReactionState = wasClutch
                    ? .celebrateClutch
                    : celebrations[session.goals % celebrations.count]
                shooterReactionTime = wasClutch ? 1.8 : 1.25
                goalieSlumpTime = 0.8
                netPulseTime = 0.45
                netImpactOffset = [ball?.position.x ?? 0, (ball?.position.y ?? 1) - 1]
                playNetImpact(at: ball?.position ?? .zero)
                beginImpactMoment(at: ball?.position ?? [0, 1, goalLineZ])
                impactShakeTime = 0.42
                emitBurst(.goal, at: ball?.position ?? [0, 1, -4.7])
                feedbackPlayer.playGoal()
                playCrowdReaction("crowd_goal_cheer", duration: 1.6)
                if session.combo >= 3 || hitHotZone {
                    playAmbientGust()
                }
                scheduleReset(session: session)
            }
        } else if names.contains("Goalie"), session.registerSave() {
            let ballX = ball?.position.x ?? 0
            let goalieX = goalie?.position.x ?? 0
            goalieReactionDirection = ballX >= goalieX ? 1 : -1
            goalieReactionTime = 0.75
            goalieReactionState = goalieSaveState(for: ball?.position ?? .zero)
            beginImpactMoment(at: ball?.position ?? [0, 0.8, goalLineZ + 0.5])
            impactShakeTime = 0.25
            disappointmentTime = 0.65
            shooterReactionState = .saveReaction
            shooterReactionTime = 0.72
            emitBurst(.save, at: ball?.position ?? [0, 0.8, -4.3])
            feedbackPlayer.playSave()
            playCrowdReaction("crowd_save_cheer", duration: 1.3)
            scheduleReset(session: session)
        } else if names.contains("Goal Pipe") {
            session.registerPipe()
            impactShakeTime = 0.32
            emitBurst(.pipe, at: ball?.position ?? [0, 1, -4.5])
            feedbackPlayer.playPipe()
            playCrowdReaction("crowd_pipe_groan", duration: 1.1)
            shooterReactionState = .pipeReaction
            shooterReactionTime = 0.64
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
        isBallLaunched = false
        activeCurveDirection = 0
        activePerfectRelease = false
        activeDodgeDirection = 0
        pendingDodgeDirection = 0
        isQuickStickSetup = false
        goalieCommitState = nil
        shooterReactionState = nil
        shooterReactionTime = 0
        resultCameraTime = 0
        calledShotHitTime = 0
        trailHistory.removeAll(keepingCapacity: true)
        for trail in ballTrail {
            trail.isEnabled = false
        }
        setBallAppearance(isOnFire: false, isPerfectRelease: false)
    }

    private func update(deltaTime: TimeInterval, session: GameSession) {
        elapsedTime += deltaTime
        if ambientGustTime > 0 {
            ambientGustTime = max(0, ambientGustTime - Float(deltaTime))
            if ambientGustTime == 0 {
                ambientArenaDriver?.transition(to: "ambient_loop", duration: 0.3)
            }
        }
        if crowdReactionTime > 0 {
            crowdReactionTime = max(0, crowdReactionTime - Float(deltaTime))
            if crowdReactionTime == 0 {
                for driver in crowdAnimationDrivers {
                    driver.transition(to: "crowd_idle", duration: 0.2)
                }
            }
        }
        updateQuickStickSetup(session: session)
        updatePerformanceStates()
        updateGoalie(
            deltaTime: Float(deltaTime),
            level: session.difficultyLevel,
            seed: session.runSeed
        )
        updateShooter(deltaTime: Float(deltaTime))
        updateAuthoredBallPocket()
        updateCharacterEyes()
        updateBallTrail(isActive: session.isAwaitingResult)
        updateBurstEffects(deltaTime: Float(deltaTime))
        updateGoalNet(deltaTime: Float(deltaTime))
        updateCalledShotTarget(deltaTime: Float(deltaTime), session: session)
        updateShotPhysics(deltaTime: Float(deltaTime), isActive: session.isAwaitingResult)
        updateCamera(deltaTime: Float(deltaTime))
    }

    private func updateAuthoredBallPocket() {
        guard shooterAnimationDriver != nil,
              !isBallLaunched,
              !isQuickStickSetup,
              let ball,
              let pocket = shooter?.findEntity(named: "pocket_socket"),
              let parent = ball.parent else { return }

        var pocketPosition = pocket.position(relativeTo: parent)
        let cradlePhase = Float(elapsedTime) * 5.4
        let cradleAmount: Float = isAiming ? 0.008 : 0.022
        pocketPosition.x += sin(cradlePhase) * cradleAmount
        pocketPosition.y += abs(cos(cradlePhase)) * cradleAmount * 0.45
        pocketPosition.z += cos(cradlePhase) * cradleAmount * 0.22
        ball.setPosition(pocketPosition, relativeTo: parent)
    }

    private func updateGoalie(deltaTime: Float, level: Int, seed: Int) {
        guard let goalie else { return }

        let speed = 1.15 + Float(level) * 0.2
        let amplitude = 0.45 + Float(level) * 0.06
        let seedPhase = Float(seed % 997) / 997 * .pi * 2
        let travel = Float(elapsedTime) * speed + seedPhase
        let stepNumber = Int(floor(travel / .pi))
        let stepPhase = (travel.truncatingRemainder(dividingBy: .pi)) / .pi
        let stepStart: Float = stepNumber.isMultiple(of: 2) ? -amplitude : amplitude
        let stepEnd = -stepStart
        let movingPhase = max(0, min(1, (stepPhase - 0.22) / 0.56))
        let plantedProgress = movingPhase * movingPhase * (3 - 2 * movingPhase)
        var x = stepStart + (stepEnd - stepStart) * plantedProgress
        var rootY = sin(plantedProgress * .pi) * 0.025
        goalieShuffleDirection = stepEnd > stepStart ? 1 : -1
        var roll: Float = 0
        var squash = SIMD3<Float>(1, 1, 1)

        if goalieReadTime > 0 {
            goalieReadTime = max(0, goalieReadTime - deltaTime)
            let readProgress = 1 - goalieReadTime / (selectedShotType == .bounce ? 0.48 : 0.72)
            let committedRead = readProgress * readProgress
            x += goalieReadDirection * committedRead * goalieReadStrength
            roll -= goalieReadDirection * committedRead * 0.08
        }

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
        goalie.position.y = goalieAnimationDriver == nil ? goalieBaseHeight + rootY : rootY
        goalie.orientation = simd_quatf(angle: roll, axis: [0, 0, 1])
        goalieTorso?.scale = squash
        goalieHead?.orientation = simd_quatf(
            angle: -roll * 0.35,
            axis: [0, 0, 1]
        )
        let shuffle = cos(Float(elapsedTime) * speed) * 0.16
        for (index, leg) in goalieLegs.enumerated() {
            let side: Float = index == 0 ? -1 : 1
            leg.orientation = simd_quatf(angle: side * shuffle - roll * 0.25, axis: [0, 0, 1])
        }
        goalieStick?.orientation = simd_quatf(
            angle: -0.3 - roll * 0.85,
            axis: [0, 0, 1]
        )
    }

    private func updatePerformanceStates() {
        if shooterReactionTime > 0, let shooterReactionState {
            shooterPerformanceState = shooterReactionState
        } else if celebrationTime > 0 {
            shooterPerformanceState = .celebrate
        } else if disappointmentTime > 0 {
            shooterPerformanceState = .disappointed
        } else if releaseTime > 0 {
            switch selectedShotType {
            case .overhand: shooterPerformanceState = .releaseOverhand
            case .bounce: shooterPerformanceState = .releaseBounce
            case .sidearm: shooterPerformanceState = .releaseSidearm
            case .quickStick: shooterPerformanceState = .quickStickRelease
            }
        } else if isQuickStickSetup {
            shooterPerformanceState = .quickStickCatch
        } else if pendingDodgeDirection < -0.5 {
            shooterPerformanceState = .splitDodgeLeft
        } else if pendingDodgeDirection > 0.5 {
            shooterPerformanceState = .splitDodgeRight
        } else if isAiming {
            switch selectedShotType {
            case .overhand: shooterPerformanceState = .aimOverhand
            case .bounce: shooterPerformanceState = .aimBounce
            case .sidearm: shooterPerformanceState = .aimSidearm
            case .quickStick: shooterPerformanceState = .quickStickCatch
            }
        } else {
            shooterPerformanceState = .cradle
        }

        if goalieSlumpTime > 0 {
            goaliePerformanceState = .goalieGoalAgainst
        } else if goalieReactionTime > 0 {
            goaliePerformanceState = goalieReactionState
        } else if let goalieCommitState {
            goaliePerformanceState = goalieCommitState
        } else if goalieReadTime > 0 {
            goaliePerformanceState = goalieReadDirection < 0
                ? .goalieReadLeft
                : .goalieReadRight
        } else {
            goaliePerformanceState = goalieShuffleDirection < 0
                ? .goalieShuffleLeft
                : .goalieShuffleRight
        }

        shooterAnimationDriver?.transition(to: shooterPerformanceState)
        goalieAnimationDriver?.transition(to: goaliePerformanceState)
    }

    private func updateShooter(deltaTime: Float) {
        guard let shooter else { return }
        shooterReactionTime = max(0, shooterReactionTime - deltaTime)
        if shooterReactionTime == 0 {
            shooterReactionState = nil
        }
        if shooterAnimationDriver != nil {
            if releaseTime > 0 {
                releaseTime = max(0, releaseTime - deltaTime)
            } else if celebrationTime > 0 {
                celebrationTime = max(0, celebrationTime - deltaTime)
            } else if disappointmentTime > 0 {
                disappointmentTime = max(0, disappointmentTime - deltaTime)
            }
            let dodge = abs(pendingDodgeDirection) > 0.5
                ? pendingDodgeDirection * 0.32
                : activeDodgeDirection * min(releaseTime / 1.1, 1) * 0.32
            shooter.position = [shooterBaseX + dodge, 0, 1.72]
            shooter.orientation = simd_quatf(angle: 0, axis: [0, 1, 0])
            return
        }
        guard let shooterStick else { return }

        let idleBob = sin(Float(elapsedTime) * 2.4) * 0.012
        var rootY = idleBob
        var rootX = shooterBaseX
        var rootZ: Float = 1.72
        var rootRoll: Float = 0
        var stickAngle: Float = -0.28 + sin(Float(elapsedTime) * 3.6) * 0.055
        var torsoScale = SIMD3<Float>(1, 1, 1)
        var headTilt: Float = 0

        if isQuickStickSetup {
            let pocketPulse = sin(quickStickPhase * .pi)
            rootY -= pocketPulse * 0.025
            rootZ += pocketPulse * 0.035
            rootRoll = -0.08 + pocketPulse * 0.06
            stickAngle = -0.72 + pocketPulse * 0.38
            torsoScale = [1.04, 0.96, 1]
            headTilt = 0.08
        } else if isAiming {
            let normalizedPower = max(0, min(1, (aimPower - 0.65) / 1.55))
            rootY -= normalizedPower * 0.035
            rootZ += normalizedPower * 0.055
            rootRoll = -aimDirection * 0.1
            let shotWindup: Float
            switch selectedShotType {
            case .overhand: shotWindup = -0.36 - normalizedPower * 0.58
            case .bounce: shotWindup = -0.18 - normalizedPower * 0.42
            case .sidearm: shotWindup = -1.02 - normalizedPower * 0.24
            case .quickStick: shotWindup = -0.72
            }
            stickAngle = shotWindup + aimDirection * 0.14
            torsoScale = [1 + normalizedPower * 0.06, 1 - normalizedPower * 0.055, 1]
            headTilt = aimDirection * 0.05
            if abs(pendingDodgeDirection) > 0.5 {
                let dodgePulse = 0.72 + sin(Float(elapsedTime) * 10) * 0.08
                rootX += pendingDodgeDirection * dodgePulse * 0.34
                rootRoll -= pendingDodgeDirection * 0.2
                stickAngle += pendingDodgeDirection * 0.16
                torsoScale = [1.08, 0.93, 1]
            }
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
            case .quickStick:
                stickAngle = -0.48 + attack * 1.35 - settle * 0.18
                rootZ -= attack * 0.08
            }
            torsoScale = [1 - attack * 0.08, 1 + attack * 0.11, 1]
            headTilt = -aimDirection * attack * 0.09
            if abs(activeDodgeDirection) > 0.5 {
                let plant = sin(progress * .pi)
                rootX += activeDodgeDirection * (1 - progress) * 0.3
                rootRoll += activeDodgeDirection * plant * 0.18
            }
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

        shooter.position.x = rootX
        shooter.position.y = rootY
        shooter.position.z = rootZ
        shooter.orientation = simd_quatf(angle: rootRoll, axis: [0, 0, 1])
        shooterStick.orientation = simd_quatf(angle: stickAngle, axis: [0, 0, 1])
        shooterTorso?.scale = torsoScale
        shooterHead?.orientation = simd_quatf(angle: headTilt, axis: [0, 1, 0])
        shooterPonytail?.orientation = simd_quatf(
            angle: -rootRoll * 1.5 + sin(Float(elapsedTime) * 3.2) * 0.035,
            axis: [0, 0, 1]
        )
        let dodgeStride = pendingDodgeDirection * 0.32 + activeDodgeDirection * 0.2
        for (index, leg) in shooterLegs.enumerated() {
            let side: Float = index == 0 ? -1 : 1
            leg.orientation = simd_quatf(
                angle: side * dodgeStride + rootRoll * 0.25,
                axis: [0, 0, 1]
            )
        }
        for (index, arm) in shooterArms.enumerated() {
            let side: Float = index == 0 ? -1 : 1
            arm.orientation = simd_quatf(
                angle: stickAngle * 0.28 + side * 0.12,
                axis: [0, 0, 1]
            )
        }
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

    private func updateQuickStickSetup(session: GameSession) {
        guard session.isQuickStickChallenge, let ball else {
            isQuickStickSetup = false
            return
        }

        isQuickStickSetup = true
        selectedShotType = .quickStick
        quickStickPhase = Float(session.quickStickPhase())

        if quickStickPhase <= 0.5 {
            let rawProgress = quickStickPhase / 0.5
            let progress = rawProgress * rawProgress * (3 - 2 * rawProgress)
            let start = SIMD3<Float>(-2.15, 0.82, 1.34)
            var position = simd_mix(start, quickStickCatch, SIMD3<Float>(repeating: progress))
            position.y += sin(progress * .pi) * 0.16
            ball.position = position
        } else {
            let cradle = sin((quickStickPhase - 0.5) * .pi * 4) * 0.035
            ball.position = quickStickCatch + [cradle, abs(cradle) * 0.4, 0]
        }
    }

    private func updateShotPhysics(deltaTime _: Float, isActive: Bool) {
        guard isActive, let ball else { return }

        if goalieCommitState == nil, ball.position.z < goalLineZ + 2.6 {
            goalieCommitState = goalieSaveState(for: ball.position)
        }

        guard activeShotType == .sidearm else { return }

        let progress = max(0, min(1, (-ball.position.z - 0.5) / 5.2))
        let lateCurve = progress * progress
        let curveForce = SIMD3<Float>(activeCurveDirection * lateCurve * 0.62, 0, 0)
        ball.addForce(curveForce, relativeTo: nil)
    }

    private func goalieSaveState(for position: SIMD3<Float>) -> CharacterPerformanceState {
        let goalieX = goalie?.position.x ?? 0
        let isLeft = position.x < goalieX
        if position.y > 1.28 {
            return isLeft ? .goalieSaveHighLeft : .goalieSaveHighRight
        }
        if position.y < 0.5, abs(position.x) < 0.3 {
            return .goalieFiveHoleClose
        }
        if position.y < 0.62 {
            return isLeft ? .goalieSaveLowLeft : .goalieSaveLowRight
        }
        if abs(position.x - goalieX) < 0.25 {
            return .goalieBodySave
        }
        return isLeft ? .goalieSaveLeft : .goalieSaveRight
    }

    private func updateCamera(deltaTime: Float) {
        guard let camera else { return }

        cameraKickTime = max(0, cameraKickTime - deltaTime)
        impactShakeTime = max(0, impactShakeTime - deltaTime)
        resultCameraTime = max(0, resultCameraTime - deltaTime)

        let kickProgress = cameraKickTime / 0.34
        let kick = sin((1 - kickProgress) * .pi) * kickProgress
        let shakeProgress = impactShakeTime / 0.42
        let shake = sin(Float(elapsedTime) * 54) * shakeProgress * 0.035
        // A restrained orbit keeps the diorama visibly three-dimensional without
        // moving the target out from under the player's thumb.
        let idleOrbit = sin(Float(elapsedTime) * 0.22) * 0.11
        let baseFrom = cameraRestPosition + SIMD3<Float>(
            idleOrbit + shake,
            abs(shake) * 0.5,
            -kick * 0.16
        )
        let resultProgress = 1 - resultCameraTime / 0.8
        let resultBlend = resultCameraTime > 0 ? sin(resultProgress * .pi) : 0
        let resultFrom = SIMD3<Float>(
            resultCameraFocus.x * 0.16,
            3.15,
            3.75
        )
        let desiredPosition = simd_mix(baseFrom, resultFrom, SIMD3<Float>(repeating: resultBlend * 0.72))
        let baseTarget = cameraRestTarget + SIMD3<Float>(shake * 0.25, 0, 0)
        let resultTarget = SIMD3<Float>(
            resultCameraFocus.x * 0.35,
            max(0.55, resultCameraFocus.y * 0.72),
            goalLineZ - 0.05
        )
        var desiredTarget = simd_mix(baseTarget, resultTarget, SIMD3<Float>(repeating: resultBlend))
        if isBallLaunched, let ball {
            let trackedBall = ball.position(relativeTo: camera.parent)
            desiredTarget.x += trackedBall.x * 0.12
            desiredTarget.y += max(0, trackedBall.y - 0.8) * 0.055
        }

        // Frame-rate-independent exponential damping avoids a robotic camera snap.
        let positionBlend = 1 - exp(-deltaTime * 5.2)
        let targetBlend = 1 - exp(-deltaTime * 7.5)
        cameraPosition = simd_mix(cameraPosition, desiredPosition, SIMD3<Float>(repeating: positionBlend))
        cameraTarget = simd_mix(cameraTarget, desiredTarget, SIMD3<Float>(repeating: targetBlend))
        camera.look(
            at: cameraTarget,
            from: cameraPosition,
            relativeTo: camera.parent
        )
    }

    private func beginImpactMoment(at position: SIMD3<Float>) {
        resultCameraFocus = position
        resultCameraTime = 0.8

        guard let ball else { return }
        var body = ball.components[PhysicsBodyComponent.self] ?? PhysicsBodyComponent()
        body.mode = .kinematic
        ball.components.set(body)
        ball.components.set(PhysicsMotionComponent())
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

    private func setBallAppearance(isOnFire: Bool, isPerfectRelease: Bool) {
        let ballColor: UIColor = isOnFire
            ? .systemYellow
            : (isPerfectRelease ? .systemCyan : .white)
        let trailColor: UIColor = isOnFire
            ? .systemOrange
            : (isPerfectRelease ? .systemCyan : UIColor(
                red: 0.82,
                green: 0.95,
                blue: 1,
                alpha: 1
            ))
        if let ball, var model = ball.components[ModelComponent.self] {
            model.materials = [SimpleMaterial(color: ballColor, isMetallic: isOnFire)]
            ball.components.set(model)
        }
        for particle in ballTrail {
            guard var model = particle.components[ModelComponent.self] else { continue }
            model.materials = [SimpleMaterial(color: trailColor, isMetallic: false)]
            particle.components.set(model)
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

        if goalAnimationDriver != nil {
            netPulseTime = max(0, netPulseTime - deltaTime)
            if netPulseTime == 0 {
                goalAnimationDriver?.transition(to: "net_idle", duration: 0.2)
            }
            return
        }

        if netPulseTime > 0 {
            netPulseTime = max(0, netPulseTime - deltaTime)
            let progress = 1 - netPulseTime / 0.45
            let pulse = sin(progress * .pi) * 0.08
            goalNet.scale = [1 + pulse, 1 + pulse, 1]
            goalNet.position.x = netImpactOffset.x * pulse * 0.7
            goalNet.position.y = 1 + netImpactOffset.y * pulse * 0.45
            goalNet.orientation = simd_quatf(
                angle: -netImpactOffset.x * pulse * 0.08,
                axis: [0, 1, 0]
            )
        } else {
            goalNet.scale = .one
            goalNet.position = [0, 1, -5.67]
            goalNet.orientation = .init()
        }
    }

    private func playNetImpact(at position: SIMD3<Float>) {
        guard let driver = goalAnimationDriver else { return }
        let motion: PhysicsMotionComponent? = ball?.components[PhysicsMotionComponent.self]
        let speed = simd_length(motion?.linearVelocity ?? .zero)
        let clip: String
        if speed > 11.8 {
            clip = "net_impact_heavy"
        } else if position.y > 1.15 {
            clip = position.x < 0 ? "net_impact_high_left" : "net_impact_high_right"
        } else if abs(position.x) > 0.32 {
            clip = position.x < 0 ? "net_impact_low_left" : "net_impact_low_right"
        } else {
            clip = "net_impact_center"
        }
        driver.transition(to: clip, duration: 0.04, restart: true)
    }

    private func updateTargetMarkers() {
        for (index, marker) in targetMarkers.enumerated() {
            let phase = Float(elapsedTime) * 2.2 + Float(index) * 0.8
            let pulse = 0.9 + sin(phase) * 0.1
            marker.scale = [pulse, pulse, 0.18]
        }
    }

    private func addCalledShotTarget(to root: Entity) {
        let target = Entity()
        target.name = "Called Shot Target"

        let cyan = SimpleMaterial(color: .systemCyan, isMetallic: false)
        let white = SimpleMaterial(color: .white, isMetallic: false)
        for index in 0..<12 {
            let angle = Float(index) / 12 * .pi * 2
            let dot = ModelEntity(
                mesh: .generateSphere(radius: index.isMultiple(of: 3) ? 0.036 : 0.026),
                materials: [index.isMultiple(of: 2) ? cyan : white]
            )
            dot.position = [cos(angle) * 0.2, sin(angle) * 0.2, 0]
            target.addChild(dot)
        }

        calledShotTarget = target
        root.addChild(target)
    }

    private func updateCalledShotTarget(deltaTime: Float, session: GameSession) {
        guard let target = calledShotTarget else { return }
        calledShotHitTime = max(0, calledShotHitTime - deltaTime)
        target.position = session.activeHotZone.targetPosition
        let pulse = 1 + sin(Float(elapsedTime) * 4.4) * 0.09
        target.scale = .one * pulse
        target.orientation = simd_quatf(
            angle: Float(elapsedTime) * 0.28,
            axis: [0, 0, 1]
        )
        target.isEnabled = !session.isRoundComplete && calledShotHitTime == 0
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

    private func addSkyBackdrop(to root: Entity) {
        let sky = SimpleMaterial(
            color: .init(red: 0.38, green: 0.7, blue: 0.96, alpha: 1),
            isMetallic: false
        )
        addDecorativeBox(
            size: [400, 120, 0.2],
            position: [0, 28, -171],
            material: sky,
            to: root
        )
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

        addGoalBar(size: [0.1, 2, 0.1], position: [-1, 1, goalLineZ], material: pipeMaterial, to: root)
        addGoalBar(size: [0.1, 2, 0.1], position: [1, 1, goalLineZ], material: pipeMaterial, to: root)
        addGoalBar(size: [2.1, 0.1, 0.1], position: [0, 2, goalLineZ], material: pipeMaterial, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [-1, 0.03, goalLineZ - 0.6], material: pipeMaterial, to: root)
        addGoalBar(size: [0.06, 0.06, 1.2], position: [1, 0.03, goalLineZ - 0.6], material: pipeMaterial, to: root)
        addGoalBar(size: [2.1, 0.06, 0.06], position: [0, 0.03, goalLineZ - 1.2], material: pipeMaterial, to: root)

        let net = Entity()
        net.position = [0, 1, goalLineZ - 1.17]

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
        sensor.position = [0, 1, goalLineZ - 0.12]
        let shape = ShapeResource.generateBox(size: [1.78, 1.75, 0.2])
        sensor.components.set(
            CollisionComponent(shapes: [shape], mode: .trigger)
        )
        root.addChild(sensor)
    }

    private func addGoalie(to root: Entity) {
        let goalie = Entity()
        goalie.name = "Goalie"
        goalie.position = [0, 0.625, goalLineZ + 0.5]

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
        helmet.name = "helmet_socket"
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
            goalieLegs.append(leg)
            goalie.addChild(leg)
        }

        let stick = makeStick(
            shaftMaterial: white,
            headMaterial: white,
            scale: 0.85
        )
        stick.name = "stick_socket"
        stick.position = [0.38, -0.02, 0.08]
        stick.orientation = simd_quatf(angle: -0.3, axis: [0, 0, 1])
        goalieStick = stick
        goalie.addChild(stick)

        let effectSocket = Entity()
        effectSocket.name = "effect_socket"
        effectSocket.position = [0, 0.35, 0.18]
        goalie.addChild(effectSocket)

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
        shooter.name = "shooter_root"
        shooter.position = [shooterBaseX, 0, 1.72]

        let jersey = SimpleMaterial(
            color: .init(red: 0.96, green: 0.91, blue: 0.78, alpha: 1),
            isMetallic: false
        )
        let homeRed = SimpleMaterial(
            color: .init(red: 0.78, green: 0.12, blue: 0.1, alpha: 1),
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

        let skirt = ModelEntity(
            mesh: .generateBox(size: [0.5, 0.24, 0.28], cornerRadius: 0.075),
            materials: [homeRed]
        )
        skirt.position = [0, 0.36, 0]
        skirt.scale.x = 1.08
        shooter.addChild(skirt)

        for x: Float in [-0.14, 0.14] {
            let leg = ModelEntity(
                mesh: .generateBox(size: [0.14, 0.38, 0.16], cornerRadius: 0.06),
                materials: [skin]
            )
            leg.position = [x, 0.13, 0]
            shooterLegs.append(leg)
            shooter.addChild(leg)

            let eye = ModelEntity(
                mesh: .generateSphere(radius: 0.03),
                materials: [dark]
            )
            eye.position = [x * 0.65, 1.08, 0.25]
            shooterEyes.append(eye)
            shooter.addChild(eye)
        }

        for x: Float in [-0.31, 0.31] {
            let arm = ModelEntity(
                mesh: .generateBox(size: [0.12, 0.42, 0.13], cornerRadius: 0.055),
                materials: [skin]
            )
            arm.position = [x, 0.67, 0.03]
            arm.orientation = simd_quatf(angle: x < 0 ? -0.18 : 0.18, axis: [0, 0, 1])
            shooterArms.append(arm)
            shooter.addChild(arm)
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

        let headband = ModelEntity(
            mesh: .generateBox(size: [0.43, 0.055, 0.08], cornerRadius: 0.025),
            materials: [homeRed]
        )
        headband.position = [0, 1.15, 0.18]
        shooter.addChild(headband)

        let ponytail = Entity()
        ponytail.position = [0, 1.05, 0.22]
        for (index, radius): (Int, Float) in [(0, 0.15), (1, 0.13), (2, 0.1)] {
            let segment = ModelEntity(
                mesh: .generateSphere(radius: radius),
                materials: [hair]
            )
            segment.position = [0, -Float(index) * 0.16, Float(index) * 0.045]
            segment.scale = [0.82, 1, 0.82]
            ponytail.addChild(segment)
        }
        shooterPonytail = ponytail
        shooter.addChild(ponytail)

        let stick = makeStick(
            shaftMaterial: homeRed,
            headMaterial: jersey,
            scale: 1
        )
        stick.name = "stick_socket"
        stick.position = [0.34, 0.7, 0.12]
        shooter.addChild(stick)

        let helmetSocket = Entity()
        helmetSocket.name = "helmet_socket"
        helmetSocket.position = [0, 1.05, 0]
        shooter.addChild(helmetSocket)

        let effectSocket = Entity()
        effectSocket.name = "effect_socket"
        effectSocket.position = [0, 0.85, 0.12]
        shooter.addChild(effectSocket)

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
            [-0.72, 1.67, goalLineZ - 0.12],
            [0.72, 1.67, goalLineZ - 0.12],
            [-0.72, 0.38, goalLineZ - 0.12],
            [0, 0.38, goalLineZ - 0.12],
            [0.72, 0.38, goalLineZ - 0.12]
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
        let visibleRadius: Float = 0.08
        let collisionRadius: Float = 0.12
        let shape = ShapeResource.generateSphere(radius: collisionRadius)
        let ball = ModelEntity(
            mesh: .generateSphere(radius: visibleRadius),
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
        component.fieldOfViewInDegrees = 50
        camera.components.set(component)
        cameraPosition = cameraRestPosition
        cameraTarget = cameraRestTarget
        camera.look(
            at: cameraTarget,
            from: cameraPosition,
            relativeTo: root
        )
        self.camera = camera
        root.addChild(camera)
    }

    private func playAmbientGust() {
        ambientGustTime = 3
        ambientArenaDriver?.transition(to: "ambient_gust", duration: 0.18, restart: true)
    }

    private func playCrowdReaction(_ clipName: String, duration: Float) {
        crowdReactionTime = duration
        for driver in crowdAnimationDrivers {
            driver.transition(to: clipName, duration: 0.08, restart: true)
        }
    }

    private func addLighting(to root: Entity) {
        let light = Entity()
        light.components.set(
            DirectionalLightComponent(
                color: UIColor(red: 1, green: 0.82, blue: 0.66, alpha: 1),
                intensity: 4_800
            )
        )
        light.components.set(DirectionalLightComponent.Shadow(maximumDistance: 20, depthBias: 1.4))
        // A raking key produces readable character/cage silhouettes instead of
        // the dark circular footprint created by a near-overhead light.
        light.look(at: [0, 0, -2], from: [-7, 8, 7], relativeTo: root)
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
