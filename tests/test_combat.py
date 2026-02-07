import unittest

from autochess_combat import UnitSpec, simulate_battle


class CombatTests(unittest.TestCase):
    def test_damage_has_minimum_one(self) -> None:
        tank = UnitSpec(name="Tank", hp=20, attack=3, armor=10, attack_speed=1.0)
        weak = UnitSpec(name="Weak", hp=20, attack=1, armor=0, attack_speed=1.0)

        result = simulate_battle([weak], [tank], team_a_name="A", team_b_name="B")

        # Weak should eventually deal damage despite high armor.
        self.assertTrue(any("for 1" in line for line in result.log))

    def test_frontline_targeting(self) -> None:
        striker = UnitSpec(name="Striker", hp=50, attack=10, armor=0, attack_speed=1.0)
        front = UnitSpec(name="Front", hp=30, attack=1, armor=0, attack_speed=0.5)
        back = UnitSpec(name="Back", hp=30, attack=1, armor=0, attack_speed=0.5)

        result = simulate_battle([striker], [front, back], team_a_name="A", team_b_name="B")

        first_attack = next(line for line in result.log if "A:Striker" in line and "for" in line)
        self.assertIn("B:Front[0]", first_attack)

    def test_winner_is_determined(self) -> None:
        strong = UnitSpec(name="Strong", hp=80, attack=25, armor=2, attack_speed=1.2)
        weak = UnitSpec(name="Weak", hp=50, attack=8, armor=1, attack_speed=0.9)

        result = simulate_battle([strong], [weak], team_a_name="Dwarves", team_b_name="Monsters")

        self.assertEqual("Dwarves", result.winner)
        self.assertGreater(len(result.survivors), 0)
        self.assertTrue(all(s.team == "Dwarves" for s in result.survivors))

    def test_simultaneous_actions_skip_dead_attackers(self) -> None:
        glass = UnitSpec(name="Glass", hp=10, attack=10, armor=0, attack_speed=1.0)
        cannon = UnitSpec(name="Cannon", hp=10, attack=15, armor=0, attack_speed=1.0)

        result = simulate_battle([glass], [cannon], team_a_name="A", team_b_name="B")

        # Same start time, deterministic order. If first strike kills target,
        # dead target should not attack in same tick.
        first_tick_attacks = [line for line in result.log if line.startswith("000.00s") and "->" in line]
        self.assertEqual(1, len(first_tick_attacks))


if __name__ == "__main__":
    unittest.main()
