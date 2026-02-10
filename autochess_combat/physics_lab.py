from __future__ import annotations

from dataclasses import dataclass, field
import math
import random


@dataclass(slots=True)
class PhysicsBody:
    body_id: int
    team: str
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    mass: float
    color: str
    power: float = 1.0
    role: str = "dealer"
    forward_dir: float = 0.0
    max_hp: float = 100.0
    hp: float = 100.0
    stagger_timer: float = 0.0
    last_damage: float = 0.0
    ability_cooldown: float = 0.0

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError("radius must be > 0")
        if self.mass <= 0:
            raise ValueError("mass must be > 0")
        if self.power <= 0:
            raise ValueError("power must be > 0")
        if self.max_hp <= 0:
            raise ValueError("max_hp must be > 0")
        if self.hp < 0:
            raise ValueError("hp must be >= 0")
        if self.stagger_timer < 0:
            raise ValueError("stagger_timer must be >= 0")
        if self.ability_cooldown < 0:
            raise ValueError("ability_cooldown must be >= 0")
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        self.role = self._normalize_role(self.role)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @staticmethod
    def _normalize_role(raw: str) -> str:
        role = str(raw).strip().lower()
        allowed = {"tank", "dealer", "healer", "ranged_dealer", "ranged_healer"}
        if role not in allowed:
            return "dealer"
        return role


@dataclass(slots=True)
class PhysicsTuning:
    gravity: float = 900.0
    approach_force: float = 1150.0
    restitution: float = 0.68
    wall_restitution: float = 0.55
    linear_damping: float = 0.16
    friction: float = 0.20
    wall_friction: float = 0.08
    ground_friction: float = 0.30
    ground_snap_speed: float = 42.0
    collision_boost: float = 1.0
    solver_passes: int = 3
    position_correction: float = 0.80
    mass_power_impact_scale: float = 120.0
    power_ratio_exponent: float = 0.50
    impact_speed_cap: float = 1400.0
    min_recoil_speed: float = 45.0
    recoil_scale: float = 0.62
    min_launch_speed: float = 90.0
    launch_scale: float = 0.45
    launch_height_scale: float = 1.0
    max_launch_speed: float = 820.0
    damage_base: float = 1.5
    damage_scale: float = 0.028
    stagger_base: float = 0.06
    stagger_scale: float = 0.0012
    max_stagger: float = 1.20
    stagger_drive_multiplier: float = 0.0
    ranged_attack_cooldown: float = 1.00
    ranged_attack_range: float = 520.0
    ranged_knockback_force: float = 240.0
    ranged_damage: float = 5.5
    healer_cooldown: float = 1.20
    healer_range: float = 360.0
    healer_amount: float = 10.0

    def validate(self) -> None:
        if self.restitution < 0:
            raise ValueError("restitution must be >= 0")
        if self.wall_restitution < 0:
            raise ValueError("wall_restitution must be >= 0")
        if self.linear_damping < 0:
            raise ValueError("linear_damping must be >= 0")
        if self.friction < 0:
            raise ValueError("friction must be >= 0")
        if self.wall_friction < 0:
            raise ValueError("wall_friction must be >= 0")
        if self.ground_friction < 0:
            raise ValueError("ground_friction must be >= 0")
        if self.ground_snap_speed < 0:
            raise ValueError("ground_snap_speed must be >= 0")
        if self.collision_boost <= 0:
            raise ValueError("collision_boost must be > 0")
        if self.solver_passes <= 0:
            raise ValueError("solver_passes must be > 0")
        if not 0 <= self.position_correction <= 1:
            raise ValueError("position_correction must be in [0, 1]")
        if self.mass_power_impact_scale <= 0:
            raise ValueError("mass_power_impact_scale must be > 0")
        if self.power_ratio_exponent < 0:
            raise ValueError("power_ratio_exponent must be >= 0")
        if self.impact_speed_cap <= 0:
            raise ValueError("impact_speed_cap must be > 0")
        if self.min_recoil_speed < 0:
            raise ValueError("min_recoil_speed must be >= 0")
        if self.recoil_scale < 0:
            raise ValueError("recoil_scale must be >= 0")
        if self.min_launch_speed < 0:
            raise ValueError("min_launch_speed must be >= 0")
        if self.launch_scale < 0:
            raise ValueError("launch_scale must be >= 0")
        if self.launch_height_scale <= 0:
            raise ValueError("launch_height_scale must be > 0")
        if self.max_launch_speed <= 0:
            raise ValueError("max_launch_speed must be > 0")
        if self.damage_base < 0:
            raise ValueError("damage_base must be >= 0")
        if self.damage_scale < 0:
            raise ValueError("damage_scale must be >= 0")
        if self.stagger_base < 0:
            raise ValueError("stagger_base must be >= 0")
        if self.stagger_scale < 0:
            raise ValueError("stagger_scale must be >= 0")
        if self.max_stagger < 0:
            raise ValueError("max_stagger must be >= 0")
        if self.stagger_drive_multiplier < 0:
            raise ValueError("stagger_drive_multiplier must be >= 0")
        if self.ranged_attack_cooldown <= 0:
            raise ValueError("ranged_attack_cooldown must be > 0")
        if self.ranged_attack_range <= 0:
            raise ValueError("ranged_attack_range must be > 0")
        if self.ranged_knockback_force < 0:
            raise ValueError("ranged_knockback_force must be >= 0")
        if self.ranged_damage < 0:
            raise ValueError("ranged_damage must be >= 0")
        if self.healer_cooldown <= 0:
            raise ValueError("healer_cooldown must be > 0")
        if self.healer_range <= 0:
            raise ValueError("healer_range must be > 0")
        if self.healer_amount < 0:
            raise ValueError("healer_amount must be >= 0")


@dataclass(slots=True)
class PhysicsWorld:
    width: float
    height: float
    bodies: list[PhysicsBody]
    tuning: PhysicsTuning = field(default_factory=PhysicsTuning)
    time_elapsed: float = 0.0
    total_collisions: int = 0
    last_step_collisions: int = 0
    active_contacts: set[tuple[int, int]] = field(default_factory=set)
    invincible_teams: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("world size must be > 0")
        self.tuning.validate()
        self.set_invincible_teams(self.invincible_teams)

    def set_tuning(self, tuning: PhysicsTuning) -> None:
        tuning.validate()
        self.tuning = tuning

    def set_invincible_teams(self, teams: set[str] | list[str] | tuple[str, ...]) -> None:
        normalized = set()
        for team in teams:
            team_name = str(team).strip().lower()
            if team_name:
                normalized.add(team_name)
        self.invincible_teams = normalized

    def is_team_invincible(self, team: str) -> bool:
        return team.strip().lower() in self.invincible_teams

    def add_random_impulse(self, *, magnitude: float = 420.0, seed: int | None = None) -> None:
        if magnitude <= 0:
            raise ValueError("magnitude must be > 0")
        rng = random.Random(seed)
        for body in self.bodies:
            if not body.is_alive:
                continue
            body.vx += rng.uniform(-magnitude, magnitude) / body.mass
            body.vy += rng.uniform(-magnitude, magnitude) / body.mass

    def max_speed(self) -> float:
        alive = [body for body in self.bodies if body.is_alive]
        if not alive:
            return 0.0
        return max(math.hypot(body.vx, body.vy) for body in alive)

    def step(self, dt: float) -> None:
        if dt <= 0:
            raise ValueError("dt must be > 0")

        damping = max(0.0, 1.0 - (self.tuning.linear_damping * dt))

        for body in self.bodies:
            body.last_damage = 0.0
            if not body.is_alive:
                body.vx = 0.0
                body.vy = 0.0
                body.stagger_timer = 0.0
                body.ability_cooldown = 0.0
                continue
            if body.stagger_timer > 0:
                body.stagger_timer = max(0.0, body.stagger_timer - dt)
            if body.ability_cooldown > 0:
                body.ability_cooldown = max(0.0, body.ability_cooldown - dt)

            on_ground = self._is_grounded(body)
            drive_force = 0.0
            if body.is_alive:
                drive_force = self.tuning.approach_force * body.power
                if body.stagger_timer > 0:
                    drive_force *= self.tuning.stagger_drive_multiplier

            ax = (body.forward_dir * drive_force) / body.mass
            ay = self.tuning.gravity
            if on_ground and body.vy >= 0:
                ay = 0.0
                body.vy = 0.0

            body.vx += ax * dt
            body.vy += ay * dt
            body.vx *= damping
            body.vy *= damping

            if on_ground:
                body.vx *= max(0.0, 1.0 - (self.tuning.ground_friction * dt))

            body.x += body.vx * dt
            body.y += body.vy * dt

            self._resolve_wall_collision(body)

        collision_count = 0
        current_contacts: set[tuple[int, int]] = set()
        impact_pairs: set[tuple[int, int]] = set()
        for _ in range(self.tuning.solver_passes):
            collision_count += self._resolve_body_collisions(current_contacts, impact_pairs)

        self._apply_role_actions()

        self.active_contacts = current_contacts
        self.last_step_collisions = collision_count
        self.total_collisions += collision_count
        self.time_elapsed += dt

    def _is_grounded(self, body: PhysicsBody) -> bool:
        ground_y = self.height - body.radius
        return body.y >= (ground_y - 1e-6) and abs(body.vy) <= self.tuning.ground_snap_speed

    def _resolve_wall_collision(self, body: PhysicsBody) -> None:
        r = body.radius
        wr = self.tuning.wall_restitution
        wf = max(0.0, 1.0 - self.tuning.wall_friction)

        if body.x - r < 0:
            body.x = r
            if body.vx < 0:
                body.vx = -body.vx * wr
                body.vy *= wf
        elif body.x + r > self.width:
            body.x = self.width - r
            if body.vx > 0:
                body.vx = -body.vx * wr
                body.vy *= wf

        if body.y - r < 0:
            body.y = r
            if body.vy < 0:
                body.vy = -body.vy * wr
                body.vx *= wf
        elif body.y + r > self.height:
            body.y = self.height - r
            if body.vy > self.tuning.ground_snap_speed:
                body.vy = -body.vy * wr
            else:
                body.vy = 0.0
            body.vx *= max(0.0, 1.0 - self.tuning.ground_friction)

    def _resolve_body_collisions(
        self,
        current_contacts: set[tuple[int, int]],
        impact_pairs: set[tuple[int, int]],
    ) -> int:
        collisions = 0
        count = len(self.bodies)

        for i in range(count):
            a = self.bodies[i]
            if not a.is_alive:
                continue
            for j in range(i + 1, count):
                b = self.bodies[j]
                if not b.is_alive:
                    continue
                if a.team == b.team:
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                radii = a.radius + b.radius
                distance_sq = dx * dx + dy * dy
                if distance_sq >= radii * radii:
                    continue

                pair = (min(a.body_id, b.body_id), max(a.body_id, b.body_id))
                current_contacts.add(pair)

                if distance_sq <= 1e-12:
                    nx = 1.0 if (a.body_id + b.body_id) % 2 == 0 else -1.0
                    ny = 0.0
                    distance = radii
                else:
                    distance = math.sqrt(distance_sq)
                    nx = dx / distance
                    ny = dy / distance

                inv_mass_a = 1.0 / a.mass
                inv_mass_b = 1.0 / b.mass
                inv_mass_sum = inv_mass_a + inv_mass_b

                penetration = radii - distance
                correction = (penetration / inv_mass_sum) * self.tuning.position_correction
                a.x -= nx * correction * inv_mass_a
                a.y -= ny * correction * inv_mass_a
                b.x += nx * correction * inv_mass_b
                b.y += ny * correction * inv_mass_b

                rel_vx = b.vx - a.vx
                rel_vy = b.vy - a.vy
                rel_normal_speed = (rel_vx * nx) + (rel_vy * ny)

                if rel_normal_speed < 0:
                    power_a = max(1e-6, a.power)
                    power_b = max(1e-6, b.power)
                    effective_inv_mass_a = inv_mass_a / power_a
                    effective_inv_mass_b = inv_mass_b / power_b
                    effective_inv_mass_sum = effective_inv_mass_a + effective_inv_mass_b

                    impulse = -(1.0 + self.tuning.restitution) * rel_normal_speed
                    impulse /= effective_inv_mass_sum
                    impulse *= self.tuning.collision_boost

                    impulse_x = impulse * nx
                    impulse_y = impulse * ny
                    a.vx -= impulse_x * effective_inv_mass_a
                    a.vy -= impulse_y * effective_inv_mass_a
                    b.vx += impulse_x * effective_inv_mass_b
                    b.vy += impulse_y * effective_inv_mass_b

                    tangent_x = rel_vx - (rel_normal_speed * nx)
                    tangent_y = rel_vy - (rel_normal_speed * ny)
                    tangent_mag = math.hypot(tangent_x, tangent_y)
                    if tangent_mag > 1e-9:
                        tangent_x /= tangent_mag
                        tangent_y /= tangent_mag
                        friction_impulse = -((rel_vx * tangent_x) + (rel_vy * tangent_y))
                        friction_impulse /= effective_inv_mass_sum
                        friction_limit = abs(impulse) * self.tuning.friction
                        friction_impulse = max(-friction_limit, min(friction_impulse, friction_limit))

                        fx = friction_impulse * tangent_x
                        fy = friction_impulse * tangent_y
                        a.vx -= fx * effective_inv_mass_a
                        a.vy -= fy * effective_inv_mass_a
                        b.vx += fx * effective_inv_mass_b
                        b.vy += fy * effective_inv_mass_b

                if (
                    pair not in self.active_contacts
                    and pair not in impact_pairs
                    and rel_normal_speed < 0
                ):
                    self._apply_impact_effects(a, b, nx)
                    impact_pairs.add(pair)

                collisions += 1

        return collisions

    def _incoming_strength(self, attacker: PhysicsBody, defender: PhysicsBody) -> float:
        power_ratio = max(1e-6, attacker.power) / max(1e-6, defender.power)
        mass_ratio = attacker.mass / max(1e-6, defender.mass)
        scaled = self.tuning.mass_power_impact_scale * mass_ratio
        scaled *= power_ratio ** self.tuning.power_ratio_exponent
        return min(self.tuning.impact_speed_cap, scaled)

    def _apply_impact_effects(
        self,
        a: PhysicsBody,
        b: PhysicsBody,
        nx: float,
    ) -> None:
        incoming_a = self._incoming_strength(b, a)
        incoming_b = self._incoming_strength(a, b)

        recoil_a = self.tuning.min_recoil_speed + (incoming_a * self.tuning.recoil_scale)
        recoil_b = self.tuning.min_recoil_speed + (incoming_b * self.tuning.recoil_scale)

        launch_a = min(
            self.tuning.max_launch_speed,
            (
                self.tuning.min_launch_speed + (incoming_a * self.tuning.launch_scale)
            )
            * self.tuning.launch_height_scale,
        )
        launch_b = min(
            self.tuning.max_launch_speed,
            (
                self.tuning.min_launch_speed + (incoming_b * self.tuning.launch_scale)
            )
            * self.tuning.launch_height_scale,
        )

        a.vx -= nx * (recoil_a / a.mass)
        b.vx += nx * (recoil_b / b.mass)
        a.vy -= launch_a / a.mass
        b.vy -= launch_b / b.mass

        damage_a = self.tuning.damage_base + (incoming_a * self.tuning.damage_scale)
        damage_b = self.tuning.damage_base + (incoming_b * self.tuning.damage_scale)
        if self.is_team_invincible(a.team):
            damage_a = 0.0
        else:
            a.hp = max(0.0, a.hp - damage_a)
        if self.is_team_invincible(b.team):
            damage_b = 0.0
        else:
            b.hp = max(0.0, b.hp - damage_b)
        a.last_damage = damage_a
        b.last_damage = damage_b

        stagger_a = min(
            self.tuning.max_stagger,
            self.tuning.stagger_base + (incoming_a * self.tuning.stagger_scale),
        )
        stagger_b = min(
            self.tuning.max_stagger,
            self.tuning.stagger_base + (incoming_b * self.tuning.stagger_scale),
        )
        a.stagger_timer = max(a.stagger_timer, stagger_a)
        b.stagger_timer = max(b.stagger_timer, stagger_b)

    def _closest_enemy(self, actor: PhysicsBody, max_range: float) -> PhysicsBody | None:
        closest: PhysicsBody | None = None
        closest_dist_sq = max_range * max_range
        for other in self.bodies:
            if not other.is_alive or other.team == actor.team:
                continue
            dx = other.x - actor.x
            dy = other.y - actor.y
            dist_sq = (dx * dx) + (dy * dy)
            if dist_sq <= closest_dist_sq:
                closest_dist_sq = dist_sq
                closest = other
        return closest

    def _weakest_ally(self, actor: PhysicsBody, max_range: float) -> PhysicsBody | None:
        weakest: PhysicsBody | None = None
        weakest_ratio = 1.1
        max_range_sq = max_range * max_range
        for other in self.bodies:
            if not other.is_alive or other.team != actor.team:
                continue
            dx = other.x - actor.x
            dy = other.y - actor.y
            if (dx * dx) + (dy * dy) > max_range_sq:
                continue
            if other.max_hp <= 0:
                continue
            hp_ratio = other.hp / other.max_hp
            if hp_ratio < weakest_ratio and other.hp < other.max_hp:
                weakest_ratio = hp_ratio
                weakest = other
        return weakest

    def _apply_ranged_knockback(
        self,
        actor: PhysicsBody,
        target: PhysicsBody,
        *,
        force: float,
        damage: float,
    ) -> None:
        if not target.is_alive:
            return
        dx = target.x - actor.x
        dy = target.y - actor.y
        distance = math.hypot(dx, dy)
        if distance <= 1e-9:
            nx = actor.forward_dir if abs(actor.forward_dir) > 1e-6 else 1.0
            ny = 0.0
        else:
            nx = dx / distance
            ny = dy / distance

        target.vx += nx * (force / max(1e-6, target.mass))
        target.vy += (ny * 0.12 - 0.18) * (force / max(1e-6, target.mass))
        target.stagger_timer = max(
            target.stagger_timer,
            min(self.tuning.max_stagger, self.tuning.stagger_base + 0.12),
        )

        if damage > 0 and not self.is_team_invincible(target.team):
            scaled_damage = damage * max(0.6, actor.power)
            target.hp = max(0.0, target.hp - scaled_damage)
            target.last_damage = max(target.last_damage, scaled_damage)

    def _apply_role_actions(self) -> None:
        for actor in self.bodies:
            if not actor.is_alive:
                continue
            if actor.ability_cooldown > 0:
                continue

            role = actor.role
            if role == "ranged_dealer":
                target = self._closest_enemy(actor, self.tuning.ranged_attack_range)
                if target is None:
                    continue
                self._apply_ranged_knockback(
                    actor,
                    target,
                    force=self.tuning.ranged_knockback_force,
                    damage=self.tuning.ranged_damage,
                )
                actor.ability_cooldown = self.tuning.ranged_attack_cooldown
            elif role == "healer":
                target = self._weakest_ally(actor, self.tuning.healer_range * 0.7)
                if target is None:
                    continue
                heal = self.tuning.healer_amount * 0.8
                target.hp = min(target.max_hp, target.hp + heal)
                actor.ability_cooldown = self.tuning.healer_cooldown
            elif role == "ranged_healer":
                acted = False
                heal_target = self._weakest_ally(actor, self.tuning.healer_range)
                if heal_target is not None:
                    heal = self.tuning.healer_amount * 1.1
                    heal_target.hp = min(heal_target.max_hp, heal_target.hp + heal)
                    acted = True
                push_target = self._closest_enemy(actor, self.tuning.ranged_attack_range * 0.9)
                if push_target is not None:
                    self._apply_ranged_knockback(
                        actor,
                        push_target,
                        force=self.tuning.ranged_knockback_force * 0.58,
                        damage=0.0,
                    )
                    acted = True
                if acted:
                    actor.ability_cooldown = self.tuning.healer_cooldown


def create_duel_world(
    *,
    width: float = 1400.0,
    height: float = 520.0,
    left_radius: float = 32.0,
    right_radius: float = 32.0,
    left_mass: float = 1.0,
    right_mass: float = 1.2,
    left_power: float = 1.0,
    right_power: float = 1.6,
    left_hp: float = 100.0,
    right_hp: float = 100.0,
    left_initial_speed: float = 260.0,
    right_initial_speed: float = 210.0,
    balls_per_side: int = 1,
    side_margin: float = 120.0,
    left_invincible: bool = False,
    right_invincible: bool = False,
    tuning: PhysicsTuning | None = None,
) -> PhysicsWorld:
    if width <= 0 or height <= 0:
        raise ValueError("world size must be > 0")
    if side_margin < 0:
        raise ValueError("side_margin must be >= 0")
    if balls_per_side <= 0:
        raise ValueError("balls_per_side must be > 0")

    left_spacing = left_radius * 2.3
    right_spacing = right_radius * 2.3
    left_start_x = side_margin + left_radius
    right_start_x = width - side_margin - right_radius

    bodies: list[PhysicsBody] = []
    for idx in range(balls_per_side):
        left_x = min(width - left_radius, max(left_radius, left_start_x + (idx * left_spacing)))
        right_x = min(
            width - right_radius,
            max(right_radius, right_start_x - (idx * right_spacing)),
        )

        bodies.append(
            PhysicsBody(
                body_id=len(bodies),
                team="left",
                x=left_x,
                y=height - left_radius,
                vx=abs(left_initial_speed),
                vy=0.0,
                radius=left_radius,
                mass=left_mass,
                color="#4aa3ff",
                power=left_power,
                forward_dir=1.0,
                max_hp=max(1.0, left_hp),
                hp=max(0.0, left_hp),
            )
        )
        bodies.append(
            PhysicsBody(
                body_id=len(bodies),
                team="right",
                x=right_x,
                y=height - right_radius,
                vx=-abs(right_initial_speed),
                vy=0.0,
                radius=right_radius,
                mass=right_mass,
                color="#f26b5e",
                power=right_power,
                forward_dir=-1.0,
                max_hp=max(1.0, right_hp),
                hp=max(0.0, right_hp),
            )
        )

    return PhysicsWorld(
        width=width,
        height=height,
        bodies=bodies,
        tuning=tuning or PhysicsTuning(),
        invincible_teams={
            team
            for team, is_enabled in (("left", left_invincible), ("right", right_invincible))
            if is_enabled
        },
    )


def create_clash_world(
    *,
    width: float = 960.0,
    height: float = 620.0,
    player_count: int = 8,
    monster_count: int = 8,
    radius: float = 16.0,
    player_mass: float = 1.0,
    monster_mass: float = 1.2,
    spawn_jitter: float = 120.0,
    seed: int = 7,
    tuning: PhysicsTuning | None = None,
) -> PhysicsWorld:
    if player_count <= 0 or monster_count <= 0:
        raise ValueError("player_count and monster_count must be > 0")
    if radius <= 0:
        raise ValueError("radius must be > 0")
    if player_mass <= 0 or monster_mass <= 0:
        raise ValueError("mass must be > 0")
    if spawn_jitter < 0:
        raise ValueError("spawn_jitter must be >= 0")

    rng = random.Random(seed)
    bodies: list[PhysicsBody] = []

    bodies.extend(
        _spawn_team(
            team="player",
            count=player_count,
            anchor_x=width * 0.22,
            anchor_y=height * 0.22,
            toward_center=1.0,
            radius=radius,
            mass=player_mass,
            color="#4aa3ff",
            spawn_jitter=spawn_jitter,
            rng=rng,
            next_id=len(bodies),
            world_width=width,
            world_height=height,
        )
    )
    bodies.extend(
        _spawn_team(
            team="monster",
            count=monster_count,
            anchor_x=width * 0.78,
            anchor_y=height * 0.22,
            toward_center=-1.0,
            radius=radius,
            mass=monster_mass,
            color="#f26b5e",
            spawn_jitter=spawn_jitter,
            rng=rng,
            next_id=len(bodies),
            world_width=width,
            world_height=height,
        )
    )

    return PhysicsWorld(width=width, height=height, bodies=bodies, tuning=tuning or PhysicsTuning())


def _spawn_team(
    *,
    team: str,
    count: int,
    anchor_x: float,
    anchor_y: float,
    toward_center: float,
    radius: float,
    mass: float,
    color: str,
    spawn_jitter: float,
    rng: random.Random,
    next_id: int,
    world_width: float,
    world_height: float,
) -> list[PhysicsBody]:
    rows = max(1, min(6, math.ceil(math.sqrt(count))))
    spacing = radius * 2.4
    spawned: list[PhysicsBody] = []

    for idx in range(count):
        row = idx % rows
        col = idx // rows

        x = anchor_x - (col * spacing * toward_center)
        y = anchor_y + ((row - (rows - 1) * 0.5) * spacing)

        x += rng.uniform(-radius * 0.15, radius * 0.15)
        y += rng.uniform(-radius * 0.15, radius * 0.15)
        x = min(world_width - radius, max(radius, x))
        y = min(world_height - radius, max(radius, y))

        vx = toward_center * (95.0 + rng.uniform(-spawn_jitter, spawn_jitter) * 0.35)
        vy = rng.uniform(-spawn_jitter, spawn_jitter) * 0.22

        spawned.append(
            PhysicsBody(
                body_id=next_id + idx,
                team=team,
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                radius=radius,
                mass=mass,
                color=color,
                power=1.0,
                forward_dir=toward_center,
                max_hp=100.0,
                hp=100.0,
            )
        )

    return spawned
