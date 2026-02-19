# 주요 변경사항

## 1. Ball 클래스 시스템 도입

### 새로운 `BallClass`
게임 역할별 기본 성능치를 명확하게 정의하는 클래스 기반 시스템을 추가했습니다.

**4가지 기본 클래스:**

| 클래스 | 역할 | 반지름 | 질량 | 파워 | 체력 | 속도 |
|--------|------|--------|------|------|------|------|
| 딜러 | dealer | 28.0 | 1.0 | 1.2 | 100.0 | 250.0 |
| 탱커 | tank | 38.0 | 1.8 | 0.8 | 180.0 | 180.0 |
| 힐러 | healer | 26.0 | 0.8 | 0.6 | 80.0 | 220.0 |
| 원거리 딜러 | ranged_dealer | 24.0 | 0.7 | 1.0 | 70.0 | 200.0 |

**특징:**
- 실제 수치 기반으로 명확한 밸런싱
- 각 클래스의 역할과 설명 포함
- 커스텀 클래스 생성 가능

**사용 예제:**
```python
from autochess_combat.battle_sim import default_ball_classes

classes = default_ball_classes()
dealer = classes[0]  # 딜러 클래스

print(f"{dealer.name}: 파워={dealer.base_power}, 체력={dealer.base_hp}")
# 출력: 딜러: 파워=1.2, 체력=100.0
```

## 2. 직관적인 물리 설정 시스템

### 카테고리별 설정 클래스
40개 이상의 물리 파라미터를 **11개 직관적 카테고리**로 그룹화했습니다.

**카테고리 목록:**

1. **PhysicsBasics** (기본 물리)
   - `gravity`: 중력
   - `approach_force`: 접근력

2. **CollisionSettings** (충돌 반발)
   - `restitution`: 반발력
   - `wall_restitution`: 벽 반발력
   - `collision_boost`: 충돌 부스트

3. **FrictionSettings** (마찰)
   - `linear_damping`: 선형 감쇠
   - `friction`: 마찰
   - `wall_friction`: 벽 마찰
   - `ground_friction`: 지면 마찰

4. **SolverSettings** (충돌 해결)
   - `solver_passes`: 해결 패스 수
   - `position_correction`: 위치 보정
   - `ground_snap_speed`: 지면 스냅 속도

5. **ImpactSettings** (충돌 강도)
   - `mass_power_impact_scale`: 질량·파워 영향 스케일
   - `power_ratio_exponent`: 파워 비율 지수
   - `impact_speed_cap`: 임팩트 속도 상한

6. **RecoilSettings** (밀려남)
   - `min_recoil_speed`: 최소 밀려남 속도
   - `recoil_scale`: 밀려남 스케일

7. **LaunchSettings** (튕겨올림)
   - `min_launch_speed`: 최소 런치 속도
   - `launch_scale`: 런치 스케일
   - `launch_height_scale`: 런치 높이 배율
   - `max_launch_speed`: 최대 런치 속도

8. **DamageSettings** (데미지)
   - `damage_base`: 기본 데미지
   - `damage_scale`: 데미지 스케일

9. **StaggerSettings** (경직)
   - `stagger_base`: 기본 경직 시간
   - `stagger_scale`: 경직 스케일
   - `max_stagger`: 최대 경직
   - `stagger_drive_multiplier`: 경직 중 이동 배율

10. **RangedAttackSettings** (원거리 공격)
    - `ranged_attack_cooldown`: 쿨다운
    - `ranged_attack_range`: 사거리
    - `ranged_knockback_force`: 넉백 강도
    - `ranged_damage`: 데미지

11. **HealingSettings** (힐링)
    - `healer_cooldown`: 쿨다운
    - `healer_range`: 범위
    - `healer_amount`: 회복량

**사용 예제:**

```python
from autochess_combat.physics_lab import (
    PhysicsTuning,
    PhysicsBasics,
    CollisionSettings,
    DamageSettings,
)

# 카테고리별로 설정
physics = PhysicsBasics(gravity=1200.0, approach_force=800.0)
collision = CollisionSettings(restitution=0.5, collision_boost=1.2)
damage = DamageSettings(damage_base=2.0, damage_scale=0.035)

# 전체 설정 생성
tuning = PhysicsTuning.from_categories(
    physics=physics,
    collision=collision,
    damage=damage,
    # 나머지는 기본값 사용
)
```

**카테고리 추출:**
```python
# 기존 설정에서 카테고리별로 추출
tuning = PhysicsTuning()
physics = tuning.to_physics_basics()
damage = tuning.to_damage_settings()

print(f"중력: {physics.gravity}")
print(f"기본 데미지: {damage.damage_base}")
```

## 3. 기존 코드와의 호환성

### 완벽한 하위 호환성 유지
- `BallProfile` 클래스는 그대로 유지
- `default_profiles()` 함수 정상 작동
- 기존 `PhysicsTuning` 사용법 변경 없음
- 모든 기존 테스트 통과 (18/18)

### 변환 함수 제공
```python
from autochess_combat.battle_sim import ball_class_to_profile

# BallClass를 BallProfile로 변환
dealer = default_ball_classes()[0]
profile = ball_class_to_profile(dealer, scale_modifier=1.2)
```

## 4. 파일 변경 내역

### 수정된 파일
- `autochess_combat/physics_lab.py`: 카테고리별 설정 클래스 추가
- `autochess_combat/battle_sim.py`: BallClass 추가, BallProfile 유지
- `README.md`: 새로운 기능 문서화

### 새로운 파일
- `ball_class_example.py`: 사용 예제 (5가지 패턴)
- `CHANGES.md`: 변경사항 문서 (본 파일)

## 5. 마이그레이션 가이드

### 기존 코드는 수정 불필요
기존 코드는 그대로 작동합니다. 새로운 기능은 선택적으로 사용할 수 있습니다.

### 새 시스템 사용 권장
더 직관적인 설정을 원한다면:

**Before:**
```python
# 모든 파라미터를 한 번에 설정
tuning = PhysicsTuning(
    gravity=1200.0,
    approach_force=800.0,
    restitution=0.5,
    wall_restitution=0.4,
    linear_damping=0.16,
    # ... 30개 이상의 파라미터
)
```

**After:**
```python
# 카테고리별로 그룹화하여 설정
physics = PhysicsBasics(gravity=1200.0, approach_force=800.0)
collision = CollisionSettings(restitution=0.5, wall_restitution=0.4)

tuning = PhysicsTuning.from_categories(physics=physics, collision=collision)
```

## 6. 다음 단계

### 제안사항
1. Ball 클래스 기반 프리셋 추가
2. UI에 카테고리별 설정 탭 추가
3. 클래스별 밸런스 테스트 자동화
4. 비주얼 에디터에서 BallClass 직접 편집 기능

### 피드백 환영
새로운 시스템에 대한 피드백이나 개선 제안은 언제든지 환영합니다!
