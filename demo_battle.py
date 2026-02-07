from autochess_combat import UnitSpec, simulate_battle


def main() -> None:
    team_dwarves = [
        UnitSpec(name="Shieldbearer", hp=120, attack=14, armor=5, attack_speed=0.9),
        UnitSpec(name="Axe Fighter", hp=90, attack=22, armor=2, attack_speed=1.2),
        UnitSpec(name="Rifleman", hp=70, attack=26, armor=1, attack_speed=1.4),
    ]
    team_monsters = [
        UnitSpec(name="Goblin", hp=65, attack=18, armor=1, attack_speed=1.3),
        UnitSpec(name="Orc", hp=105, attack=20, armor=3, attack_speed=1.0),
        UnitSpec(name="Troll", hp=140, attack=16, armor=4, attack_speed=0.8),
    ]

    result = simulate_battle(team_dwarves, team_monsters, team_a_name="Dwarves", team_b_name="Monsters")

    print(f"Winner: {result.winner}")
    print(f"Time: {result.time_elapsed:.2f}s")
    print(f"Actions: {result.actions}")
    print("Survivors:")
    for survivor in result.survivors:
        print(f"  - {survivor.team} {survivor.name}[{survivor.slot}] hp={survivor.hp}")

    print("\nBattle log (first 12 lines):")
    for line in result.log[:12]:
        print(line)


if __name__ == "__main__":
    main()
