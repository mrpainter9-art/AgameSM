"""Ball 클래스 시스템 사용 예제"""

from autochess_combat.battle_sim import (
    BallClass,
    default_ball_classes,
    ball_class_to_profile,
)
from autochess_combat.physics_lab import (
    PhysicsTuning,
    PhysicsBasics,
    CollisionSettings,
    DamageSettings,
    LaunchSettings,
)


def example_1_basic_ball_classes():
    """예제 1: 기본 Ball 클래스 사용"""
    print("=== 예제 1: 기본 Ball 클래스 ===\n")

    classes = default_ball_classes()
    for ball_class in classes:
        print(f"클래스: {ball_class.name}")
        print(f"  역할: {ball_class.role}")
        print(f"  설명: {ball_class.description}")
        print(f"  기본 스탯:")
        print(f"    반지름: {ball_class.base_radius}")
        print(f"    질량: {ball_class.base_mass}")
        print(f"    파워: {ball_class.base_power}")
        print(f"    체력: {ball_class.base_hp}")
        print(f"    속도: {ball_class.base_speed}")
        print()


def example_2_custom_ball_class():
    """예제 2: 커스텀 Ball 클래스 생성"""
    print("=== 예제 2: 커스텀 Ball 클래스 ===\n")

    custom_class = BallClass(
        name="어쌔신",
        role="dealer",
        description="빠른 속도와 높은 공격력을 가진 암살자",
        base_radius=22.0,
        base_mass=0.6,
        base_power=1.5,
        base_hp=60.0,
        base_speed=320.0,
        ability_cooldown=0.0,
    )

    print(f"커스텀 클래스: {custom_class.name}")
    print(f"  역할: {custom_class.role}")
    print(f"  설명: {custom_class.description}")
    print(f"  기본 스탯: 반지름={custom_class.base_radius}, 질량={custom_class.base_mass}")
    print()


def example_3_categorized_physics():
    """예제 3: 카테고리별 물리 설정"""
    print("=== 예제 3: 카테고리별 물리 설정 ===\n")

    # 카테고리별로 설정 생성
    physics = PhysicsBasics(gravity=1200.0, approach_force=800.0)
    collision = CollisionSettings(restitution=0.5, wall_restitution=0.4, collision_boost=1.2)
    damage = DamageSettings(damage_base=2.0, damage_scale=0.035)
    launch = LaunchSettings(
        min_launch_speed=150.0,
        launch_scale=0.5,
        launch_height_scale=1.2,
        max_launch_speed=900.0,
    )

    # 카테고리별 설정으로 전체 튜닝 생성
    tuning = PhysicsTuning.from_categories(
        physics=physics, collision=collision, damage=damage, launch=launch
    )

    print("물리 설정이 생성되었습니다:")
    print(f"  중력: {tuning.gravity}")
    print(f"  접근력: {tuning.approach_force}")
    print(f"  반발력: {tuning.restitution}")
    print(f"  데미지 기본값: {tuning.damage_base}")
    print(f"  최소 런치 속도: {tuning.min_launch_speed}")
    print()


def example_4_extract_categories():
    """예제 4: 기존 설정에서 카테고리 추출"""
    print("=== 예제 4: 카테고리 추출 ===\n")

    # 기본 설정 생성
    tuning = PhysicsTuning()

    # 카테고리별로 추출
    physics = tuning.to_physics_basics()
    collision = tuning.to_collision_settings()
    damage = tuning.to_damage_settings()

    print("기본 물리:")
    print(f"  중력: {physics.gravity}")
    print(f"  접근력: {physics.approach_force}")
    print()

    print("충돌 설정:")
    print(f"  반발력: {collision.restitution}")
    print(f"  벽 반발력: {collision.wall_restitution}")
    print(f"  충돌 부스트: {collision.collision_boost}")
    print()

    print("데미지 설정:")
    print(f"  기본 데미지: {damage.damage_base}")
    print(f"  데미지 스케일: {damage.damage_scale}")
    print()


def example_5_ball_class_to_profile():
    """예제 5: BallClass를 BallProfile로 변환"""
    print("=== 예제 5: BallClass → BallProfile 변환 ===\n")

    classes = default_ball_classes()
    dealer = classes[0]  # 딜러

    # BallClass를 BallProfile로 변환
    profile = ball_class_to_profile(dealer, scale_modifier=1.2)

    print(f"Ball 클래스: {dealer.name}")
    print(f"  기본 반지름: {dealer.base_radius}")
    print()

    print(f"변환된 프로필: {profile.name}")
    print(f"  반지름 스케일: {profile.radius_scale:.2f}")
    print(f"  질량 스케일: {profile.mass_scale:.2f}")
    print(f"  파워 스케일: {profile.power_scale:.2f}")
    print(f"  체력 스케일: {profile.hp_scale:.2f}")
    print(f"  속도 스케일: {profile.speed_scale:.2f}")
    print()


if __name__ == "__main__":
    example_1_basic_ball_classes()
    example_2_custom_ball_class()
    example_3_categorized_physics()
    example_4_extract_categories()
    example_5_ball_class_to_profile()

    print("=== 모든 예제 완료 ===")
