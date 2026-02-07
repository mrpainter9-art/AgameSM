from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class UnitSpec:
    """Static unit data used to spawn a fighter into battle."""

    name: str
    hp: int
    attack: int
    armor: int = 0
    attack_speed: float = 1.0

    def __post_init__(self) -> None:
        if self.hp <= 0:
            raise ValueError("hp must be > 0")
        if self.attack < 0:
            raise ValueError("attack must be >= 0")
        if self.attack_speed <= 0:
            raise ValueError("attack_speed must be > 0")


@dataclass(slots=True)
class Fighter:
    unit: UnitSpec
    team: str
    slot: int
    hp: int = field(init=False)
    next_attack_time: float = field(default=0.0)

    def __post_init__(self) -> None:
        self.hp = self.unit.hp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def speed_interval(self) -> float:
        return 1.0 / self.unit.attack_speed

    @property
    def label(self) -> str:
        return f"{self.team}:{self.unit.name}[{self.slot}]"


@dataclass(frozen=True, slots=True)
class Survivor:
    team: str
    name: str
    slot: int
    hp: int


@dataclass(frozen=True, slots=True)
class BattleResult:
    winner: str | None
    time_elapsed: float
    actions: int
    survivors: tuple[Survivor, ...]
    log: tuple[str, ...]


def _alive_fighters(fighters: Iterable[Fighter]) -> list[Fighter]:
    return [fighter for fighter in fighters if fighter.is_alive]


def _pick_target(enemies: list[Fighter]) -> Fighter:
    # Frontline first: smaller slot index is considered closer to frontline.
    return min(enemies, key=lambda fighter: (fighter.slot, fighter.hp, fighter.unit.name))


def _compute_damage(attacker: Fighter, defender: Fighter) -> int:
    return max(1, attacker.unit.attack - defender.unit.armor)


def simulate_battle(
    team_a: list[UnitSpec],
    team_b: list[UnitSpec],
    *,
    team_a_name: str = "A",
    team_b_name: str = "B",
    max_actions: int = 500,
    max_time: float = 180.0,
) -> BattleResult:
    """
    Run an auto-battler style basic combat simulation.

    Mechanics:
    - Every alive unit repeatedly performs a normal attack.
    - Attack interval = 1 / attack_speed.
    - Targets the enemy in the smallest slot index first.
    - Damage = max(1, attack - armor).
    - Battle ends when one team is fully dead, or safety limits are reached.
    """
    if not team_a or not team_b:
        raise ValueError("both teams must have at least one unit")
    if max_actions <= 0:
        raise ValueError("max_actions must be > 0")
    if max_time <= 0:
        raise ValueError("max_time must be > 0")

    fighters: list[Fighter] = []
    for idx, unit in enumerate(team_a):
        fighters.append(Fighter(unit=unit, team=team_a_name, slot=idx))
    for idx, unit in enumerate(team_b):
        fighters.append(Fighter(unit=unit, team=team_b_name, slot=idx))

    log: list[str] = []
    current_time = 0.0
    actions = 0

    while actions < max_actions and current_time <= max_time:
        alive_a = [fighter for fighter in fighters if fighter.team == team_a_name and fighter.is_alive]
        alive_b = [fighter for fighter in fighters if fighter.team == team_b_name and fighter.is_alive]

        if not alive_a or not alive_b:
            break

        next_time = min(fighter.next_attack_time for fighter in _alive_fighters(fighters))
        current_time = next_time

        ready = sorted(
            (
                fighter
                for fighter in fighters
                if fighter.is_alive and abs(fighter.next_attack_time - next_time) < 1e-9
            ),
            key=lambda fighter: (fighter.team, fighter.slot, fighter.unit.name),
        )

        for attacker in ready:
            if not attacker.is_alive:
                # If attacker was killed by a previous action at the same timestamp.
                continue

            enemies = [
                fighter
                for fighter in fighters
                if fighter.team != attacker.team and fighter.is_alive
            ]
            if not enemies:
                break

            target = _pick_target(enemies)
            damage = _compute_damage(attacker, target)
            target.hp = max(0, target.hp - damage)
            actions += 1

            log.append(
                f"{current_time:06.2f}s {attacker.label} -> {target.label} "
                f"for {damage} (target hp: {target.hp})"
            )

            if target.hp == 0:
                log.append(f"{current_time:06.2f}s {target.label} defeated")

            attacker.next_attack_time = current_time + attacker.speed_interval

            if actions >= max_actions:
                break

    alive_a = [fighter for fighter in fighters if fighter.team == team_a_name and fighter.is_alive]
    alive_b = [fighter for fighter in fighters if fighter.team == team_b_name and fighter.is_alive]

    winner: str | None
    if alive_a and not alive_b:
        winner = team_a_name
    elif alive_b and not alive_a:
        winner = team_b_name
    else:
        winner = None

    survivors = tuple(
        Survivor(team=fighter.team, name=fighter.unit.name, slot=fighter.slot, hp=fighter.hp)
        for fighter in sorted(_alive_fighters(fighters), key=lambda f: (f.team, f.slot))
    )

    return BattleResult(
        winner=winner,
        time_elapsed=current_time,
        actions=actions,
        survivors=survivors,
        log=tuple(log),
    )
