from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import html
import itertools
import json
import math
from pathlib import Path
import random
from typing import Any

from .physics_lab import PhysicsBody, PhysicsTuning, PhysicsWorld


DEFAULT_SETTINGS_PATH = Path("visual_physics_lab_settings.json")
DEFAULT_WORLD_WIDTH = 1460.0
DEFAULT_WORLD_HEIGHT = 520.0


@dataclass(frozen=True, slots=True)
class BallClass:
    """Ball의 기본 클래스 (역할별 RPG 스탯)"""
    name: str
    role: str
    description: str
    # RPG 스탯 (1~20 정수, 기준=10)
    base_str: int = 10   # STR: 물리 공격력 → power = STR/10
    base_dex: int = 10   # DEX: 이동속도/공격속도 → speed = DEX*25
    base_int: int = 10   # INT: 마법/원거리 공격력 → ranged_damage
    base_vit: int = 10   # VIT: 체력/크기/질량 → mass=VIT/10, radius=28*sqrt(VIT/10), hp=VIT*10
    base_wis: int = 10   # WIS: 치유량/힐 사거리 → healer cooldown = 12/WIS


@dataclass(frozen=True, slots=True)
class BallProfile:
    """Ball의 프로필 (스케일 배율) - 기존 호환성 유지"""
    name: str
    radius_scale: float
    mass_scale: float
    power_scale: float
    hp_scale: float
    speed_scale: float

    @classmethod
    def from_ball_class(cls, ball_class: BallClass, scale: float = 1.0) -> "BallProfile":
        """BallClass로부터 BallProfile 생성"""
        return cls(
            name=ball_class.name,
            radius_scale=scale,
            mass_scale=scale,
            power_scale=scale,
            hp_scale=scale,
            speed_scale=scale,
        )


@dataclass(slots=True)
class RunMetrics:
    duration: float
    fight_end_time: float
    collisions_per_second: float
    damage_per_second: float
    damage_per_collision: float
    air_ratio: float
    lead_changes: int
    collision_bursts: int
    peak_speed: float
    left_remaining_hp: float
    right_remaining_hp: float
    winner: str
    time_to_first_collision: float | None


@dataclass(slots=True)
class ScenarioSummary:
    scenario_name: str
    left_profile: BallProfile
    right_profile: BallProfile
    run_count: int
    score: float
    win_rate_left: float
    avg_duration: float
    avg_fight_end_time: float
    avg_collisions_per_second: float
    avg_damage_per_second: float
    avg_damage_per_collision: float
    avg_air_ratio: float
    avg_lead_changes: float
    avg_collision_bursts: float
    avg_peak_speed: float


@dataclass(slots=True)
class SweepResult:
    settings_path: str
    seeds: int
    duration: float
    dt: float
    scenario_count: int
    top_scenarios: list[ScenarioSummary]
    all_scenarios: list[ScenarioSummary]
    recommendations: list[str]


def default_ball_classes() -> list[BallClass]:
    """기본 Ball 클래스 정의 (딜러, 탱커, 힐러, 원거리 딜러)"""
    return [
        BallClass(
            name="딜러",
            role="dealer",
            description="근접 공격에 특화된 공격형 유닛",
            base_str=12, base_dex=10, base_int=6, base_vit=10, base_wis=4,
        ),
        BallClass(
            name="탱커",
            role="tank",
            description="높은 체력과 질량으로 전선을 유지하는 방어형 유닛",
            base_str=8, base_dex=7, base_int=4, base_vit=18, base_wis=4,
        ),
        BallClass(
            name="힐러",
            role="healer",
            description="아군을 치료하는 지원형 유닛",
            base_str=4, base_dex=8, base_int=5, base_vit=8, base_wis=12,
        ),
        BallClass(
            name="원거리 딜러",
            role="ranged_dealer",
            description="원거리에서 적을 공격하는 유닛",
            base_str=6, base_dex=9, base_int=10, base_vit=7, base_wis=4,
        ),
    ]


def default_profiles() -> list[BallProfile]:
    """기본 프로필 (기존 호환성 유지용)"""
    return [
        BallProfile("balanced", 1.00, 1.00, 1.00, 1.00, 1.00),
        BallProfile("duelist", 0.90, 0.95, 1.15, 1.00, 1.30),
        BallProfile("striker", 0.95, 0.88, 1.28, 0.88, 1.18),
        BallProfile("bruiser", 1.10, 1.38, 1.14, 1.42, 0.82),
        BallProfile("berserker", 1.00, 0.84, 1.46, 0.74, 1.12),
        BallProfile("juggernaut", 1.20, 1.72, 1.08, 1.84, 0.72),
    ]


def ball_class_to_profile(ball_class: BallClass, scale_modifier: float = 1.0) -> BallProfile:
    """BallClass RPG 스탯을 BallProfile 배율로 변환"""
    # STR=VIT=DEX=10 기준값
    default_radius = 28.0   # VIT=10 → 28*sqrt(1.0)=28
    default_mass = 1.0      # VIT=10 → 10/10=1.0
    default_power = 1.0     # STR=10 → 10/10=1.0
    default_hp = 100.0      # VIT=10 → 10*10=100
    default_speed = 250.0   # DEX=10 → 10*25=250

    derived_radius = 28.0 * math.sqrt(ball_class.base_vit / 10.0)
    derived_mass = ball_class.base_vit / 10.0
    derived_power = ball_class.base_str / 10.0
    derived_hp = float(ball_class.base_vit * 10)
    derived_speed = float(ball_class.base_dex * 25)

    return BallProfile(
        name=ball_class.name,
        radius_scale=(derived_radius / default_radius) * scale_modifier,
        mass_scale=(derived_mass / default_mass) * scale_modifier,
        power_scale=(derived_power / default_power) * scale_modifier,
        hp_scale=(derived_hp / default_hp) * scale_modifier,
        speed_scale=(derived_speed / default_speed) * scale_modifier,
    )


def _random_profile(rng: random.Random, name: str) -> BallProfile:
    return BallProfile(
        name=name,
        radius_scale=rng.uniform(0.80, 1.25),
        mass_scale=rng.uniform(0.72, 1.85),
        power_scale=rng.uniform(0.72, 1.75),
        hp_scale=rng.uniform(0.72, 1.85),
        speed_scale=rng.uniform(0.72, 1.40),
    )


def load_settings_payload(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("settings root must be object")
    return payload


def extract_tuning_from_settings(settings_payload: dict[str, Any]) -> PhysicsTuning:
    values = settings_payload.get("values", {})
    if not isinstance(values, dict):
        raise ValueError("settings.values must be object")

    tuning_kwargs: dict[str, Any] = {}
    for field in fields(PhysicsTuning):
        if field.name in values:
            tuning_kwargs[field.name] = values[field.name]
    tuning = PhysicsTuning(**tuning_kwargs)
    tuning.validate()
    return tuning


def extract_ball_specs(settings_payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = settings_payload.get("ball_specs")
    if not isinstance(raw, list) or not raw:
        raise ValueError("settings.ball_specs must be a non-empty array")
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"ball_specs[{idx}] must be object")
        out.append(dict(item))
    return out


def _default_speed_for_team(team: str, settings_values: dict[str, Any]) -> float:
    left_speed = abs(float(settings_values.get("left_speed", 260.0)))
    right_speed = abs(float(settings_values.get("right_speed", 210.0)))
    if team == "left":
        return left_speed
    if team == "right":
        return -right_speed
    return 0.0


def _default_forward_for_team(team: str) -> float:
    if team == "left":
        return 1.0
    if team == "right":
        return -1.0
    return 0.0


def _default_color_for_team(team: str) -> str:
    if team == "left":
        return "#4aa3ff"
    if team == "right":
        return "#f26b5e"
    return "#dce6f2"


def _cooldown_from_stats(role: str, dex: int, wis: int) -> float:
    """RPG 스탯(DEX/WIS)으로부터 스킬 쿨다운 파생"""
    if role == "ranged_dealer":
        return 10.0 / max(1, dex)
    if role in ("healer", "ranged_healer"):
        return 12.0 / max(1, wis)
    return 0.0


def _normalize_ball_spec(raw: dict[str, Any], idx: int) -> dict[str, Any]:
    team = str(raw.get("team", "left")).strip().lower()
    if not team:
        raise ValueError(f"ball_specs[{idx}].team must not be empty")

    normalized = dict(raw)
    normalized["team"] = team
    role = str(raw.get("role", "dealer")).strip().lower()
    if role not in {"tank", "dealer", "healer", "ranged_dealer", "ranged_healer"}:
        role = "dealer"
    normalized["role"] = role

    # RPG 스탯 읽기 (1~20, 기준=10)
    str_s = max(1, int(raw.get("str_stat", 10)))
    dex_s = max(1, int(raw.get("dex_stat", 10)))
    int_s = max(1, int(raw.get("int_stat", 10)))
    vit_s = max(1, int(raw.get("vit_stat", 10)))
    wis_s = max(1, int(raw.get("wis_stat", 10)))

    # 물리값 파생
    normalized["power"]    = str_s / 10.0
    normalized["mass"]     = vit_s / 10.0
    normalized["radius"]   = 28.0 * math.sqrt(vit_s / 10.0)
    normalized["max_hp"]   = float(vit_s * 10)
    hp_raw = float(raw.get("hp", vit_s * 10))
    normalized["hp"]       = min(hp_raw, normalized["max_hp"])
    normalized["int_stat"] = float(int_s)
    normalized["wis_stat"] = float(wis_s)

    normalized["forward_dir"] = float(raw.get("forward_dir", _default_forward_for_team(team)))
    normalized["color"] = str(raw.get("color", _default_color_for_team(team)))
    normalized["vy"] = float(raw.get("vy", 0.0))
    normalized["x"] = raw.get("x")
    normalized["y"] = raw.get("y")
    # 쿨다운: DEX/WIS에서 자동 파생 (JSON에서 명시적 지정도 허용)
    normalized["ability_cooldown"] = float(
        raw.get("ability_cooldown", _cooldown_from_stats(role, dex_s, wis_s))
    )
    # vx: DEX에서 파생 (명시적 지정도 허용)
    if "vx" not in raw:
        if team == "left":
            normalized["vx"] = float(dex_s) * 25.0
        elif team == "right":
            normalized["vx"] = -(float(dex_s) * 25.0)
        else:
            normalized["vx"] = 0.0
    return normalized


def _apply_profile(
    spec: dict[str, Any],
    profile: BallProfile,
    settings_values: dict[str, Any],
    rng: random.Random,
    speed_jitter: float,
) -> dict[str, Any]:
    out = dict(spec)
    out["radius"] = max(6.0, float(spec["radius"]) * profile.radius_scale)
    out["mass"] = max(0.2, float(spec["mass"]) * profile.mass_scale)
    out["power"] = max(0.1, float(spec["power"]) * profile.power_scale)
    out["max_hp"] = max(1.0, float(spec["max_hp"]) * profile.hp_scale)
    out["hp"] = min(out["max_hp"], max(0.0, float(spec["hp"]) * profile.hp_scale))

    team = str(spec["team"]).strip().lower()
    base_speed = float(spec.get("vx", _default_speed_for_team(team, settings_values)))
    direction = 1.0 if base_speed >= 0 else -1.0
    scaled_speed = abs(base_speed) * profile.speed_scale
    scaled_speed += rng.uniform(-speed_jitter, speed_jitter)
    out["vx"] = direction * max(8.0, scaled_speed)
    out["vy"] = float(spec.get("vy", 0.0))
    return out


def _build_world_from_specs(
    *,
    width: float,
    height: float,
    side_margin: float,
    settings_values: dict[str, Any],
    tuning: PhysicsTuning,
    specs: list[dict[str, Any]],
    invincible_teams: set[str] | None = None,
) -> PhysicsWorld:
    team_slots: dict[str, int] = {"left": 0, "right": 0}
    bodies: list[PhysicsBody] = []
    for idx, raw in enumerate(specs):
        spec = _normalize_ball_spec(raw, idx)
        team = str(spec["team"])
        radius = float(spec["radius"])
        slot = team_slots.get(team, 0)
        team_slots[team] = slot + 1
        spacing = radius * 2.3

        x_raw = spec.get("x")
        if x_raw is not None and str(x_raw).strip():
            x = float(x_raw)
        elif team == "left":
            x = side_margin + radius + (slot * spacing)
        elif team == "right":
            x = width - side_margin - radius - (slot * spacing)
        else:
            x = (width * 0.5) + ((slot - 0.5) * spacing)

        y_raw = spec.get("y")
        if y_raw is not None and str(y_raw).strip():
            y = float(y_raw)
        else:
            y = height - radius

        x = min(width - radius, max(radius, x))
        y = min(height - radius, max(radius, y))

        raw_vx = float(spec.get("vx", _default_speed_for_team(team, settings_values)))
        bodies.append(
            PhysicsBody(
                body_id=idx,
                team=team,
                x=x,
                y=y,
                vx=raw_vx,
                vy=float(spec.get("vy", 0.0)),
                radius=radius,
                mass=float(spec["mass"]),
                color=str(spec["color"]),
                power=float(spec["power"]),
                role=str(spec.get("role", "dealer")),
                forward_dir=float(spec["forward_dir"]),
                max_hp=float(spec["max_hp"]),
                hp=float(spec["hp"]),
                speed=max(1.0, abs(raw_vx)),
                base_cooldown=float(spec.get("ability_cooldown", 0.0)),
                int_stat=float(spec.get("int_stat", 10.0)),
                wis_stat=float(spec.get("wis_stat", 10.0)),
            )
        )

    return PhysicsWorld(
        width=width,
        height=height,
        bodies=bodies,
        tuning=tuning,
        invincible_teams=invincible_teams or set(),
    )


def _team_hp(world: PhysicsWorld, team: str) -> float:
    return sum(body.hp for body in world.bodies if body.team == team)


def _winner_from_world(world: PhysicsWorld) -> str:
    left_alive = any(body.team == "left" and body.is_alive for body in world.bodies)
    right_alive = any(body.team == "right" and body.is_alive for body in world.bodies)
    if left_alive and not right_alive:
        return "left"
    if right_alive and not left_alive:
        return "right"
    left_hp = _team_hp(world, "left")
    right_hp = _team_hp(world, "right")
    if abs(left_hp - right_hp) < 1e-6:
        return "draw"
    return "left" if left_hp > right_hp else "right"


def _is_grounded(world: PhysicsWorld, body: PhysicsBody) -> bool:
    ground_y = world.height - body.radius
    return body.y >= (ground_y - 1e-6) and abs(body.vy) <= world.tuning.ground_snap_speed


def simulate_run(
    *,
    world: PhysicsWorld,
    duration: float,
    dt: float,
) -> RunMetrics:
    if duration <= 0:
        raise ValueError("duration must be > 0")
    if dt <= 0:
        raise ValueError("dt must be > 0")

    steps = max(1, int(duration / dt))
    time_to_first_collision: float | None = None
    collision_bursts = 0
    peak_speed = world.max_speed()
    airborne_acc = 0.0
    airborne_samples = 0
    lead_changes = 0
    fight_end_time = duration

    initial_left_hp = _team_hp(world, "left")
    initial_right_hp = _team_hp(world, "right")
    prev_lead = 0
    hp_diff_start = initial_left_hp - initial_right_hp
    if hp_diff_start > 1e-6:
        prev_lead = 1
    elif hp_diff_start < -1e-6:
        prev_lead = -1

    for step_idx in range(steps):
        world.step(dt)

        if world.last_step_collisions > 0:
            collision_bursts += 1
            if time_to_first_collision is None:
                time_to_first_collision = (step_idx + 1) * dt

        peak_speed = max(peak_speed, world.max_speed())
        for body in world.bodies:
            if body.is_alive:
                airborne_samples += 1
                if not _is_grounded(world, body):
                    airborne_acc += 1.0

        hp_diff = _team_hp(world, "left") - _team_hp(world, "right")
        lead = 0
        if hp_diff > 1e-6:
            lead = 1
        elif hp_diff < -1e-6:
            lead = -1
        if prev_lead != 0 and lead != 0 and lead != prev_lead:
            lead_changes += 1
        if lead != 0:
            prev_lead = lead

        left_alive = any(body.team == "left" and body.is_alive for body in world.bodies)
        right_alive = any(body.team == "right" and body.is_alive for body in world.bodies)
        if not left_alive or not right_alive:
            fight_end_time = (step_idx + 1) * dt
            break

    final_left_hp = _team_hp(world, "left")
    final_right_hp = _team_hp(world, "right")
    damage_done = (initial_left_hp + initial_right_hp) - (final_left_hp + final_right_hp)
    collisions = max(0, world.total_collisions)
    elapsed = max(dt, world.time_elapsed)

    air_ratio = 0.0
    if airborne_samples > 0:
        air_ratio = airborne_acc / airborne_samples

    return RunMetrics(
        duration=elapsed,
        fight_end_time=fight_end_time,
        collisions_per_second=collisions / elapsed,
        damage_per_second=damage_done / elapsed,
        damage_per_collision=(damage_done / collisions) if collisions > 0 else 0.0,
        air_ratio=air_ratio,
        lead_changes=lead_changes,
        collision_bursts=collision_bursts,
        peak_speed=peak_speed,
        left_remaining_hp=final_left_hp,
        right_remaining_hp=final_right_hp,
        winner=_winner_from_world(world),
        time_to_first_collision=time_to_first_collision,
    )


def _score_metric(value: float, target: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 0.0
    delta = abs(value - target) / tolerance
    return max(0.0, 1.0 - delta)


def score_metrics(metrics: RunMetrics) -> float:
    collision_score = _score_metric(metrics.collisions_per_second, target=2.2, tolerance=1.6)
    damage_score = _score_metric(metrics.damage_per_second, target=22.0, tolerance=16.0)
    air_score = _score_metric(metrics.air_ratio, target=0.26, tolerance=0.18)
    duration_score = _score_metric(metrics.fight_end_time, target=14.0, tolerance=10.0)
    swing_score = _score_metric(float(metrics.lead_changes), target=3.0, tolerance=3.0)
    burst_score = _score_metric(float(metrics.collision_bursts), target=80.0, tolerance=65.0)

    weighted = (
        (collision_score * 0.23)
        + (damage_score * 0.20)
        + (air_score * 0.12)
        + (duration_score * 0.20)
        + (swing_score * 0.15)
        + (burst_score * 0.10)
    )
    return round(weighted * 100.0, 2)


def _aggregate_summaries(
    scenario_name: str,
    left_profile: BallProfile,
    right_profile: BallProfile,
    runs: list[RunMetrics],
) -> ScenarioSummary:
    run_count = len(runs)
    if run_count == 0:
        raise ValueError("runs must not be empty")

    left_wins = sum(1 for run in runs if run.winner == "left")
    avg_score = sum(score_metrics(run) for run in runs) / run_count
    return ScenarioSummary(
        scenario_name=scenario_name,
        left_profile=left_profile,
        right_profile=right_profile,
        run_count=run_count,
        score=round(avg_score, 2),
        win_rate_left=left_wins / run_count,
        avg_duration=sum(run.duration for run in runs) / run_count,
        avg_fight_end_time=sum(run.fight_end_time for run in runs) / run_count,
        avg_collisions_per_second=sum(run.collisions_per_second for run in runs) / run_count,
        avg_damage_per_second=sum(run.damage_per_second for run in runs) / run_count,
        avg_damage_per_collision=sum(run.damage_per_collision for run in runs) / run_count,
        avg_air_ratio=sum(run.air_ratio for run in runs) / run_count,
        avg_lead_changes=sum(float(run.lead_changes) for run in runs) / run_count,
        avg_collision_bursts=sum(float(run.collision_bursts) for run in runs) / run_count,
        avg_peak_speed=sum(run.peak_speed for run in runs) / run_count,
    )


def build_recommendations(
    scenarios: list[ScenarioSummary],
) -> list[str]:
    if not scenarios:
        return ["시뮬레이션 결과가 없어 추천 항목을 계산할 수 없습니다."]

    avg_collision = sum(s.avg_collisions_per_second for s in scenarios) / len(scenarios)
    avg_damage_rate = sum(s.avg_damage_per_second for s in scenarios) / len(scenarios)
    avg_air = sum(s.avg_air_ratio for s in scenarios) / len(scenarios)
    avg_swings = sum(s.avg_lead_changes for s in scenarios) / len(scenarios)

    recs: list[str] = []
    if avg_damage_rate < 0.5:
        recs.append(
            "초당 피해량이 매우 낮습니다. `power_scale >= 1.2` 조합 비중과 낮은 HP 프로필 비중을 늘려 보세요."
        )

    if avg_collision < 1.4:
        recs.append(
            "충돌 빈도가 낮습니다. `speed_scale` 1.10~1.25 구간 샘플을 늘리고 좌/우 `radius_scale` 차이를 0.1 이상 벌린 매치를 추가하세요."
        )
    if avg_damage_rate < 12.0:
        recs.append(
            "전투 템포가 느립니다. `power_scale >= 1.2`와 `hp_scale` 0.8~1.0 조합을 더 섞어 타격감을 올려 보세요."
        )
    if avg_air < 0.12:
        recs.append(
            "체공 비율이 낮아 타격 연출이 평평할 수 있습니다. 경량(질량 0.8x) + 고파워(1.25x) 샘플을 늘려 보세요."
        )
    if avg_swings < 1.0:
        recs.append(
            "역전 구간이 적습니다. `bruiser vs striker`, `juggernaut vs duelist` 같은 극단 조합을 늘려 보세요."
        )

    recs.extend(
        [
            "추가 제안: 충돌 순간 0.03~0.06초 `hit-stop`을 넣으면 임팩트가 더 강하게 느껴집니다.",
            "추가 제안: 연속 충돌 `combo` 수를 추적해 콤보 단계별로 SFX/파티클 강도를 올려 보세요.",
            "추가 제안: 볼별 `poise(경직 저항)` 스탯을 추가해 같은 질량이라도 체감 차이를 만들 수 있습니다.",
        ]
    )
    return recs


def run_profile_sweep_from_settings_payload(
    *,
    settings_payload: dict[str, Any],
    settings_label: str,
    profiles: list[BallProfile] | None = None,
    seeds: int = 6,
    duration: float = 24.0,
    dt: float = 1.0 / 120.0,
    top_k: int = 10,
    speed_jitter: float = 12.0,
    width: float = DEFAULT_WORLD_WIDTH,
    height: float = DEFAULT_WORLD_HEIGHT,
) -> SweepResult:
    if seeds <= 0:
        raise ValueError("seeds must be > 0")
    if top_k <= 0:
        raise ValueError("top_k must be > 0")
    if speed_jitter < 0:
        raise ValueError("speed_jitter must be >= 0")
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be > 0")

    settings_values = settings_payload.get("values", {})
    if not isinstance(settings_values, dict):
        raise ValueError("settings.values must be object")

    tuning = extract_tuning_from_settings(settings_payload)
    base_specs = [
        _normalize_ball_spec(spec, idx)
        for idx, spec in enumerate(extract_ball_specs(settings_payload))
    ]
    side_margin = float(settings_values.get("side_margin", 120.0))

    invincible_raw = settings_payload.get("invincible_teams")
    invincible_teams: set[str] = set()
    if isinstance(invincible_raw, list):
        for team in invincible_raw:
            team_name = str(team).strip().lower()
            if team_name:
                invincible_teams.add(team_name)

    profile_pool = profiles or default_profiles()
    scenarios: list[ScenarioSummary] = []
    for left_profile, right_profile in itertools.product(profile_pool, profile_pool):
        runs: list[RunMetrics] = []
        for seed in range(seeds):
            rng = random.Random(seed)
            shaped_specs: list[dict[str, Any]] = []
            for spec in base_specs:
                team = str(spec["team"]).strip().lower()
                profile = left_profile if team == "left" else right_profile
                shaped_specs.append(
                    _apply_profile(
                        spec=spec,
                        profile=profile,
                        settings_values=settings_values,
                        rng=rng,
                        speed_jitter=speed_jitter,
                    )
                )

            world = _build_world_from_specs(
                width=width,
                height=height,
                side_margin=side_margin,
                settings_values=settings_values,
                tuning=tuning,
                specs=shaped_specs,
                invincible_teams=invincible_teams,
            )
            runs.append(simulate_run(world=world, duration=duration, dt=dt))

        scenario_name = f"L:{left_profile.name} vs R:{right_profile.name}"
        scenarios.append(
            _aggregate_summaries(
                scenario_name=scenario_name,
                left_profile=left_profile,
                right_profile=right_profile,
                runs=runs,
            )
        )

    sorted_scenarios = sorted(scenarios, key=lambda s: s.score, reverse=True)
    top = sorted_scenarios[:top_k]
    return SweepResult(
        settings_path=settings_label,
        seeds=seeds,
        duration=duration,
        dt=dt,
        scenario_count=len(sorted_scenarios),
        top_scenarios=top,
        all_scenarios=sorted_scenarios,
        recommendations=build_recommendations(sorted_scenarios),
    )


def run_profile_sweep(
    *,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    profiles: list[BallProfile] | None = None,
    seeds: int = 6,
    duration: float = 24.0,
    dt: float = 1.0 / 120.0,
    top_k: int = 10,
    speed_jitter: float = 12.0,
    width: float = DEFAULT_WORLD_WIDTH,
    height: float = DEFAULT_WORLD_HEIGHT,
) -> SweepResult:
    payload = load_settings_payload(settings_path)
    return run_profile_sweep_from_settings_payload(
        settings_payload=payload,
        settings_label=str(settings_path),
        profiles=profiles,
        seeds=seeds,
        duration=duration,
        dt=dt,
        top_k=top_k,
        speed_jitter=speed_jitter,
        width=width,
        height=height,
    )


def run_random_profile_sweep_from_settings_payload(
    *,
    settings_payload: dict[str, Any],
    settings_label: str,
    scenario_count: int = 80,
    profile_seed: int = 2026,
    seeds: int = 6,
    duration: float = 24.0,
    dt: float = 1.0 / 120.0,
    top_k: int = 10,
    speed_jitter: float = 12.0,
    width: float = DEFAULT_WORLD_WIDTH,
    height: float = DEFAULT_WORLD_HEIGHT,
) -> SweepResult:
    if scenario_count <= 0:
        raise ValueError("scenario_count must be > 0")
    if seeds <= 0:
        raise ValueError("seeds must be > 0")
    if top_k <= 0:
        raise ValueError("top_k must be > 0")
    if speed_jitter < 0:
        raise ValueError("speed_jitter must be >= 0")
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be > 0")

    settings_values = settings_payload.get("values", {})
    if not isinstance(settings_values, dict):
        raise ValueError("settings.values must be object")

    tuning = extract_tuning_from_settings(settings_payload)
    base_specs = [
        _normalize_ball_spec(spec, idx)
        for idx, spec in enumerate(extract_ball_specs(settings_payload))
    ]
    side_margin = float(settings_values.get("side_margin", 120.0))

    invincible_raw = settings_payload.get("invincible_teams")
    invincible_teams: set[str] = set()
    if isinstance(invincible_raw, list):
        for team in invincible_raw:
            team_name = str(team).strip().lower()
            if team_name:
                invincible_teams.add(team_name)

    profile_rng = random.Random(profile_seed)
    scenarios: list[ScenarioSummary] = []
    for scenario_idx in range(scenario_count):
        left_profile = _random_profile(profile_rng, f"randL-{scenario_idx + 1:03d}")
        right_profile = _random_profile(profile_rng, f"randR-{scenario_idx + 1:03d}")
        runs: list[RunMetrics] = []

        for seed in range(seeds):
            rng = random.Random((profile_seed * 100003) + (scenario_idx * 997) + seed)
            shaped_specs: list[dict[str, Any]] = []
            for spec in base_specs:
                team = str(spec["team"]).strip().lower()
                profile = left_profile if team == "left" else right_profile
                shaped_specs.append(
                    _apply_profile(
                        spec=spec,
                        profile=profile,
                        settings_values=settings_values,
                        rng=rng,
                        speed_jitter=speed_jitter,
                    )
                )

            world = _build_world_from_specs(
                width=width,
                height=height,
                side_margin=side_margin,
                settings_values=settings_values,
                tuning=tuning,
                specs=shaped_specs,
                invincible_teams=invincible_teams,
            )
            runs.append(simulate_run(world=world, duration=duration, dt=dt))

        scenario_name = f"L:{left_profile.name} vs R:{right_profile.name}"
        scenarios.append(
            _aggregate_summaries(
                scenario_name=scenario_name,
                left_profile=left_profile,
                right_profile=right_profile,
                runs=runs,
            )
        )

    sorted_scenarios = sorted(scenarios, key=lambda s: s.score, reverse=True)
    top = sorted_scenarios[:top_k]
    return SweepResult(
        settings_path=settings_label,
        seeds=seeds,
        duration=duration,
        dt=dt,
        scenario_count=len(sorted_scenarios),
        top_scenarios=top,
        all_scenarios=sorted_scenarios,
        recommendations=build_recommendations(sorted_scenarios),
    )


def run_random_profile_sweep(
    *,
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    scenario_count: int = 80,
    profile_seed: int = 2026,
    seeds: int = 6,
    duration: float = 24.0,
    dt: float = 1.0 / 120.0,
    top_k: int = 10,
    speed_jitter: float = 12.0,
    width: float = DEFAULT_WORLD_WIDTH,
    height: float = DEFAULT_WORLD_HEIGHT,
) -> SweepResult:
    payload = load_settings_payload(settings_path)
    return run_random_profile_sweep_from_settings_payload(
        settings_payload=payload,
        settings_label=str(settings_path),
        scenario_count=scenario_count,
        profile_seed=profile_seed,
        seeds=seeds,
        duration=duration,
        dt=dt,
        top_k=top_k,
        speed_jitter=speed_jitter,
        width=width,
        height=height,
    )


def sweep_result_to_markdown(result: SweepResult) -> str:
    lines: list[str] = []
    lines.append("# 전투감 시뮬레이션 리포트")
    lines.append("")
    lines.append(f"- 설정 파일: `{result.settings_path}`")
    lines.append(f"- 시나리오 수: {result.scenario_count}")
    lines.append(f"- 시나리오당 반복(seed): {result.seeds}")
    lines.append(f"- 1회 실행 시간: {result.duration:.2f}s")
    lines.append(f"- 물리 dt: {result.dt:.5f}s")
    lines.append("")
    lines.append("## 상위 시나리오")
    lines.append("")
    lines.append("| 순위 | 시나리오 | 점수 | 좌측 승률 | 충돌/초 | 피해/초 | 체공 비율 | 리드 전환 |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|")
    for idx, s in enumerate(result.top_scenarios, start=1):
        lines.append(
            f"| {idx} | {s.scenario_name} | {s.score:.2f} | {s.win_rate_left:.2%} | "
            f"{s.avg_collisions_per_second:.2f} | {s.avg_damage_per_second:.2f} | "
            f"{s.avg_air_ratio:.2f} | {s.avg_lead_changes:.2f} |"
        )

    lines.append("")
    lines.append("## 개선 제안")
    lines.append("")
    for rec in result.recommendations:
        lines.append(f"- {rec}")

    lines.append("")
    lines.append("## 사용 프로필 배율")
    lines.append("")
    lines.append("| 진영 | 프로필 | 반지름 | 질량 | 파워 | HP | 속도 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    seen: set[str] = set()
    for scenario in result.top_scenarios:
        for side, profile in (("left", scenario.left_profile), ("right", scenario.right_profile)):
            key = f"{side}:{profile.name}"
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"| {side} | {profile.name} | {profile.radius_scale:.2f} | {profile.mass_scale:.2f} | "
                f"{profile.power_scale:.2f} | {profile.hp_scale:.2f} | {profile.speed_scale:.2f} |"
            )

    return "\n".join(lines).strip() + "\n"


def _metric_bar(value: float, cap: float) -> str:
    if cap <= 0:
        width = 0.0
    else:
        width = max(0.0, min(100.0, (value / cap) * 100.0))
    return f'<div class="bar"><span style="width:{width:.1f}%"></span></div>'


def sweep_result_to_html(result: SweepResult) -> str:
    top = result.top_scenarios
    max_score = max((s.score for s in top), default=1.0)
    max_collision = max((s.avg_collisions_per_second for s in top), default=1.0)
    max_damage = max((s.avg_damage_per_second for s in top), default=1.0)
    max_air = max((s.avg_air_ratio for s in top), default=1.0)
    max_lead = max((s.avg_lead_changes for s in top), default=1.0)

    rows: list[str] = []
    for rank, scenario in enumerate(top, start=1):
        rows.append(
            "<tr>"
            f"<td>{rank}</td>"
            f"<td>{html.escape(scenario.scenario_name)}</td>"
            f"<td>{scenario.score:.2f}{_metric_bar(scenario.score, max_score)}</td>"
            f"<td>{scenario.avg_collisions_per_second:.2f}{_metric_bar(scenario.avg_collisions_per_second, max_collision)}</td>"
            f"<td>{scenario.avg_damage_per_second:.2f}{_metric_bar(scenario.avg_damage_per_second, max_damage)}</td>"
            f"<td>{scenario.avg_air_ratio:.2f}{_metric_bar(scenario.avg_air_ratio, max_air)}</td>"
            f"<td>{scenario.avg_lead_changes:.2f}{_metric_bar(scenario.avg_lead_changes, max_lead)}</td>"
            "</tr>"
        )

    rec_items = "".join(f"<li>{html.escape(rec)}</li>" for rec in result.recommendations)
    return (
        "<!doctype html>"
        "<html lang=\"ko\">"
        "<head>"
        "<meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>전투감 리포트</title>"
        "<style>"
        ":root{--bg:#0d1117;--panel:#161b22;--line:#2a3544;--text:#e6edf3;--muted:#94a3b8;--accent:#22c55e;}"
        "body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:radial-gradient(circle at 20% 0%,#1a2330 0,#0d1117 45%);color:var(--text);}"
        ".wrap{max-width:1100px;margin:24px auto;padding:0 16px;}"
        ".card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px;}"
        "h1,h2{margin:0 0 10px 0;}"
        ".meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;}"
        ".meta div{background:#0f1520;border:1px solid var(--line);border-radius:8px;padding:8px 10px;}"
        ".meta b{display:block;color:var(--muted);font-weight:600;font-size:12px;}"
        ".meta span{font-size:15px;}"
        "table{width:100%;border-collapse:collapse;font-size:14px;}"
        "th,td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top;}"
        "th{color:var(--muted);text-align:left;}"
        ".bar{height:6px;background:#1f2937;border-radius:6px;overflow:hidden;margin-top:4px;}"
        ".bar span{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#16a34a);}"
        "ul{margin:0;padding-left:20px;}"
        "</style>"
        "</head>"
        "<body>"
        "<div class=\"wrap\">"
        "<div class=\"card\">"
        "<h1>전투감 시뮬레이션 리포트</h1>"
        "<div class=\"meta\">"
        f"<div><b>설정 파일</b><span>{html.escape(result.settings_path)}</span></div>"
        f"<div><b>시나리오 수</b><span>{result.scenario_count}</span></div>"
        f"<div><b>시나리오당 반복</b><span>{result.seeds}</span></div>"
        f"<div><b>1회 실행 시간</b><span>{result.duration:.2f}s</span></div>"
        f"<div><b>물리 dt</b><span>{result.dt:.5f}s</span></div>"
        "</div>"
        "</div>"
        "<div class=\"card\">"
        "<h2>상위 시나리오</h2>"
        "<table>"
        "<thead><tr>"
        "<th>순위</th><th>시나리오</th><th>점수</th><th>충돌/초</th>"
        "<th>피해/초</th><th>체공 비율</th><th>리드 전환</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        "</div>"
        "<div class=\"card\">"
        "<h2>개선 제안</h2>"
        f"<ul>{rec_items}</ul>"
        "</div>"
        "</div>"
        "</body>"
        "</html>"
    )


def sweep_result_to_json_dict(result: SweepResult) -> dict[str, Any]:
    return {
        "settings_path": result.settings_path,
        "seeds": result.seeds,
        "duration": result.duration,
        "dt": result.dt,
        "scenario_count": result.scenario_count,
        "top_scenarios": [
            {
                **asdict(scenario),
                "left_profile": asdict(scenario.left_profile),
                "right_profile": asdict(scenario.right_profile),
            }
            for scenario in result.top_scenarios
        ],
        "recommendations": list(result.recommendations),
    }
