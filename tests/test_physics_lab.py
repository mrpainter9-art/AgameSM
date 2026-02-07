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

        for _ in range(300):
            world.step(0.01)

        self.assertLess(right.vx, 0.0)

    def test_create_clash_world_spawns_expected_count(self) -> None:
        world = create_clash_world(player_count=5, monster_count=7, seed=42)
        self.assertEqual(12, len(world.bodies))
        self.assertTrue(any(body.team == "player" for body in world.bodies))
        self.assertTrue(any(body.team == "monster" for body in world.bodies))


if __name__ == "__main__":
    unittest.main()
