"""Small auto-battler combat prototype package."""

from .core import BattleResult, UnitSpec, simulate_battle
from .physics_lab import (
    PhysicsBody,
    PhysicsTuning,
    PhysicsWorld,
    create_clash_world,
    create_duel_world,
)

__all__ = [
    "UnitSpec",
    "BattleResult",
    "simulate_battle",
    "PhysicsBody",
    "PhysicsTuning",
    "PhysicsWorld",
    "create_clash_world",
    "create_duel_world",
]
