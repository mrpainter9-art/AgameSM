import unittest

from autochess_combat.physics_lab import (
    PhysicsBody,
    PhysicsTuning,
    PhysicsWorld,
    create_clash_world,
    create_duel_world,
)


class PhysicsLabTests(unittest.TestCase):
    def test_duel_world_spawns_on_ground_with_forward_dir(self) -> None:
        world = create_duel_world(
            width=1200.0,
            height=500.0,
            left_radius=30.0,
            right_radius=20.0,
        )
        self.assertEqual(2, len(world.bodies))
        left = next(body for body in world.bodies if body.team == "left")
        right = next(body for body in world.bodies if body.team == "right")

        self.assertEqual(500.0 - 30.0, left.y)
        self.assertEqual(500.0 - 20.0, right.y)
        self.assertEqual(0.0, left.vy)
        self.assertEqual(0.0, right.vy)
        self.assertEqual(1.0, left.forward_dir)
        self.assertEqual(-1.0, right.forward_dir)

    def test_duel_world_can_spawn_three_per_side(self) -> None:
        world = create_duel_world(
            width=1400.0,
            height=500.0,
            left_radius=30.0,
            right_radius=30.0,
            balls_per_side=3,
        )
        left_bodies = [body for body in world.bodies if body.team == "left"]
        right_bodies = [body for body in world.bodies if body.team == "right"]
        self.assertEqual(6, len(world.bodies))
        self.assertEqual(3, len(left_bodies))
        self.assertEqual(3, len(right_bodies))
        self.assertTrue(all(body.y == 500.0 - 30.0 for body in left_bodies))
        self.assertTrue(all(body.y == 500.0 - 30.0 for body in right_bodies))

    def test_collision_launches_both_and_applies_stagger(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            min_launch_speed=120.0,
            launch_scale=0.5,
        )
        left = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=12.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            forward_dir=1.0,
        )
        right = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-12.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=200.0, height=100.0, bodies=[left, right], tuning=tuning)

        world.step(0.01)

        self.assertLess(left.vy, 0.0)
        self.assertLess(right.vy, 0.0)
        self.assertGreater(left.stagger_timer, 0.0)
        self.assertGreater(right.stagger_timer, 0.0)

    def test_strong_ball_also_recoils_but_less(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            min_recoil_speed=30.0,
            recoil_scale=0.7,
        )
        weak = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=10.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=0.7,
            forward_dir=1.0,
        )
        strong = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-10.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=2.2,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=200.0, height=100.0, bodies=[weak, strong], tuning=tuning)

        world.step(0.01)

        self.assertLess(weak.vx, 0.0)
        self.assertGreater(strong.vx, 0.0)
        self.assertGreater(abs(weak.vx), abs(strong.vx))

    def test_mass_and_power_reduce_knockback_and_stagger(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            min_recoil_speed=25.0,
            recoil_scale=0.8,
            stagger_base=0.0,
            stagger_scale=0.004,
        )
        weak_light = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=10.0,
            vy=0.0,
            radius=10.0,
            mass=0.9,
            color="#4aa3ff",
            power=0.7,
            forward_dir=1.0,
        )
        strong_heavy = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-10.0,
            vy=0.0,
            radius=10.0,
            mass=1.8,
            color="#f26b5e",
            power=2.2,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=220.0, height=120.0, bodies=[weak_light, strong_heavy], tuning=tuning)

        world.step(0.01)

        self.assertGreater(abs(weak_light.vx), abs(strong_heavy.vx))
        self.assertGreater(weak_light.stagger_timer, strong_heavy.stagger_timer)

    def test_launch_height_scale_controls_vertical_launch(self) -> None:
        def make_world(tuning: PhysicsTuning) -> PhysicsWorld:
            left = PhysicsBody(
                body_id=0,
                team="left",
                x=40.0,
                y=60.0,
                vx=12.0,
                vy=0.0,
                radius=10.0,
                mass=1.0,
                color="#4aa3ff",
                power=1.0,
                forward_dir=1.0,
            )
            right = PhysicsBody(
                body_id=1,
                team="right",
                x=58.0,
                y=60.0,
                vx=-12.0,
                vy=0.0,
                radius=10.0,
                mass=1.0,
                color="#f26b5e",
                power=1.0,
                forward_dir=-1.0,
            )
            return PhysicsWorld(width=220.0, height=140.0, bodies=[left, right], tuning=tuning)

        base_tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            min_launch_speed=120.0,
            launch_scale=0.0,
            launch_height_scale=1.0,
        )
        higher_tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            min_launch_speed=120.0,
            launch_scale=0.0,
            launch_height_scale=1.8,
        )

        world_base = make_world(base_tuning)
        world_higher = make_world(higher_tuning)

        world_base.step(0.01)
        world_higher.step(0.01)

        self.assertLess(world_base.bodies[0].vy, 0.0)
        self.assertLess(world_higher.bodies[0].vy, world_base.bodies[0].vy)
        self.assertLess(world_higher.bodies[1].vy, world_base.bodies[1].vy)

    def test_power_is_connected_to_damage_and_stagger(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            damage_base=0.0,
            damage_scale=0.05,
            stagger_base=0.0,
            stagger_scale=0.01,
        )
        weak = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=10.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=0.5,
            forward_dir=1.0,
        )
        strong = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-10.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=2.0,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=200.0, height=100.0, bodies=[weak, strong], tuning=tuning)

        world.step(0.01)

        self.assertLess(weak.hp, strong.hp)
        self.assertGreater(weak.stagger_timer, strong.stagger_timer)

    def test_invincible_team_does_not_take_damage(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            damage_base=3.0,
            damage_scale=0.03,
        )
        left = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=12.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            forward_dir=1.0,
        )
        right = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-12.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(
            width=220.0,
            height=120.0,
            bodies=[left, right],
            tuning=tuning,
            invincible_teams={"right"},
        )

        right_hp_before = right.hp
        world.step(0.01)

        self.assertEqual(right_hp_before, right.hp)
        self.assertLess(left.hp, left.max_hp)
        self.assertEqual(0.0, right.last_damage)

    def test_staggered_ball_recoils_then_charges_again(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=240.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
            stagger_base=0.30,
            stagger_scale=0.0,
            stagger_drive_multiplier=0.0,
        )
        left = PhysicsBody(
            body_id=0,
            team="left",
            x=40.0,
            y=50.0,
            vx=20.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            forward_dir=1.0,
        )
        right = PhysicsBody(
            body_id=1,
            team="right",
            x=58.0,
            y=50.0,
            vx=-20.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.8,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=400.0, height=100.0, bodies=[left, right], tuning=tuning)

        world.step(0.01)
        self.assertGreater(right.stagger_timer, 0.0)
        self.assertGreater(right.vx, 0.0)
        recoil_vx = right.vx

        for _ in range(300):
            world.step(0.01)

        self.assertEqual(0.0, right.stagger_timer)
        self.assertLess(right.vx, recoil_vx)
        vx_before = right.vx
        world.step(0.01)
        self.assertLess(right.vx, vx_before)

    def test_create_clash_world_spawns_expected_count(self) -> None:
        world = create_clash_world(player_count=5, monster_count=7, seed=42)
        self.assertEqual(12, len(world.bodies))
        self.assertTrue(any(body.team == "player" for body in world.bodies))
        self.assertTrue(any(body.team == "monster" for body in world.bodies))

    def test_same_side_balls_overlap_without_collision_response(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=1.0,
        )
        left_a = PhysicsBody(
            body_id=0,
            team="left",
            x=50.0,
            y=60.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            forward_dir=1.0,
        )
        left_b = PhysicsBody(
            body_id=1,
            team="left",
            x=54.0,
            y=60.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            forward_dir=1.0,
        )
        right = PhysicsBody(
            body_id=2,
            team="right",
            x=180.0,
            y=60.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=300.0, height=140.0, bodies=[left_a, left_b, right], tuning=tuning)

        world.step(0.01)

        self.assertEqual(0, world.last_step_collisions)
        self.assertAlmostEqual(50.0, left_a.x, places=6)
        self.assertAlmostEqual(54.0, left_b.x, places=6)

    def test_dead_ball_does_not_collide_but_falls(self) -> None:
        tuning = PhysicsTuning(
            gravity=900.0,
            approach_force=300.0,
            restitution=0.3,
            wall_restitution=0.55,
            linear_damping=0.16,
            friction=0.2,
            wall_friction=0.08,
            ground_friction=0.3,
            collision_boost=1.0,
            solver_passes=2,
            position_correction=0.8,
        )
        dead = PhysicsBody(
            body_id=0,
            team="left",
            x=120.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            hp=0.0,
            max_hp=100.0,
            forward_dir=1.0,
        )
        alive = PhysicsBody(
            body_id=1,
            team="right",
            x=131.0,
            y=70.0,
            vx=-10.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            hp=100.0,
            max_hp=100.0,
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=400.0, height=200.0, bodies=[dead, alive], tuning=tuning)
        ground_y = world.height - dead.radius

        world.step(0.02)

        # Dead ball should not cause collisions
        self.assertEqual(0, world.last_step_collisions)
        # Dead ball falls with gravity (y increases toward ground)
        self.assertGreater(dead.y, 70.0)

        # Step until the dead ball reaches the ground
        for _ in range(200):
            world.step(0.02)

        self.assertAlmostEqual(dead.y, ground_y, places=1)
        self.assertEqual(0.0, dead.vx)
        self.assertEqual(0.0, dead.vy)

    def test_ranged_dealer_can_knockback_without_contact(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            ranged_attack_cooldown=0.5,
            ranged_attack_range=300.0,
            ranged_knockback_force=200.0,
            ranged_damage=4.0,
        )
        ranged = PhysicsBody(
            body_id=0,
            team="left",
            x=120.0,
            y=80.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="ranged_dealer",
            forward_dir=1.0,
        )
        target = PhysicsBody(
            body_id=1,
            team="right",
            x=260.0,
            y=80.0,
            vx=0.0,
            vy=0.0,
            radius=12.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=600.0, height=200.0, bodies=[ranged, target], tuning=tuning)

        world.step(0.02)

        self.assertGreater(len(world.projectiles), 0, "발사체가 생성되어야 함")
        self.assertLess(target.hp, target.max_hp, "타겟이 피해를 입어야 함")

    def test_healer_restores_ally_hp(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            healer_cooldown=0.5,
            healer_range=240.0,
            healer_amount=12.0,
        )
        healer = PhysicsBody(
            body_id=0,
            team="left",
            x=100.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="healer",
            forward_dir=1.0,
        )
        ally = PhysicsBody(
            body_id=1,
            team="left",
            x=180.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=80.0,
            forward_dir=1.0,
        )
        enemy = PhysicsBody(
            body_id=2,
            team="right",
            x=420.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        world = PhysicsWorld(width=640.0, height=200.0, bodies=[healer, ally, enemy], tuning=tuning)

        hp_before = ally.hp
        world.step(0.02)

        self.assertGreater(ally.hp, hp_before)

    def test_healer_prioritizes_frontline_ally(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            healer_cooldown=0.5,
            healer_range=220.0,
            healer_amount=10.0,
        )
        healer = PhysicsBody(
            body_id=0,
            team="left",
            x=100.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="healer",
            forward_dir=1.0,
        )
        rear_low_hp = PhysicsBody(
            body_id=1,
            team="left",
            x=150.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=40.0,
            forward_dir=1.0,
        )
        front_ally = PhysicsBody(
            body_id=2,
            team="left",
            x=250.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=95.0,
            forward_dir=1.0,
        )
        enemy = PhysicsBody(
            body_id=3,
            team="right",
            x=500.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        world = PhysicsWorld(
            width=700.0,
            height=220.0,
            bodies=[healer, rear_low_hp, front_ally, enemy],
            tuning=tuning,
        )

        rear_before = rear_low_hp.hp
        front_before = front_ally.hp
        world.step(0.02)

        self.assertGreater(front_ally.hp, front_before)
        self.assertEqual(rear_before, rear_low_hp.hp)

    def test_healer_range_scales_with_power(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=0.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            healer_cooldown=0.5,
            healer_range=120.0,
            healer_amount=10.0,
        )
        low_healer = PhysicsBody(
            body_id=0,
            team="left",
            x=100.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="healer",
            forward_dir=1.0,
            wis_stat=7.0,
        )
        low_target = PhysicsBody(
            body_id=1,
            team="left",
            x=210.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=80.0,
            forward_dir=1.0,
        )
        low_enemy = PhysicsBody(
            body_id=2,
            team="right",
            x=480.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        low_world = PhysicsWorld(
            width=700.0,
            height=220.0,
            bodies=[low_healer, low_target, low_enemy],
            tuning=tuning,
        )

        high_healer = PhysicsBody(
            body_id=10,
            team="left",
            x=100.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="healer",
            forward_dir=1.0,
            wis_stat=14.0,
        )
        high_target = PhysicsBody(
            body_id=11,
            team="left",
            x=210.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=80.0,
            forward_dir=1.0,
        )
        high_enemy = PhysicsBody(
            body_id=12,
            team="right",
            x=480.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        high_world = PhysicsWorld(
            width=700.0,
            height=220.0,
            bodies=[high_healer, high_target, high_enemy],
            tuning=tuning,
        )

        low_before = low_target.hp
        high_before = high_target.hp
        low_world.step(0.02)
        high_world.step(0.02)

        self.assertEqual(low_before, low_target.hp)
        self.assertGreater(high_target.hp, high_before)

    def test_healer_holds_back_when_frontline_ally_is_in_range(self) -> None:
        tuning = PhysicsTuning(
            gravity=0.0,
            approach_force=320.0,
            restitution=0.0,
            wall_restitution=1.0,
            linear_damping=0.0,
            friction=0.0,
            wall_friction=0.0,
            ground_friction=0.0,
            healer_cooldown=0.5,
            healer_range=220.0,
            healer_amount=10.0,
        )
        healer = PhysicsBody(
            body_id=0,
            team="left",
            x=100.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="healer",
            forward_dir=1.0,
        )
        frontline_ally = PhysicsBody(
            body_id=1,
            team="left",
            x=180.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#4aa3ff",
            power=1.0,
            role="dealer",
            max_hp=120.0,
            hp=120.0,
            forward_dir=1.0,
        )
        enemy = PhysicsBody(
            body_id=2,
            team="right",
            x=520.0,
            y=70.0,
            vx=0.0,
            vy=0.0,
            radius=10.0,
            mass=1.0,
            color="#f26b5e",
            power=1.0,
            role="dealer",
            forward_dir=-1.0,
        )
        world = PhysicsWorld(
            width=760.0,
            height=240.0,
            bodies=[healer, frontline_ally, enemy],
            tuning=tuning,
        )

        world.step(0.02)

        self.assertAlmostEqual(0.0, healer.vx, places=6)


if __name__ == "__main__":
    unittest.main()
