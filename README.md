# AgameSM

Python prototype workspace for collision-physics visualization.

## 주요 기능

### Ball 클래스 시스템
게임 역할별로 정의된 4가지 기본 Ball 클래스:
- **딜러** (Dealer): 근접 공격 특화, 균형잡힌 스탯
- **탱커** (Tank): 높은 체력과 질량, 낮은 속도
- **힐러** (Healer): 아군 치료, 낮은 전투력
- **원거리 딜러** (Ranged Dealer): 원거리 공격, 낮은 체력

### 직관적인 물리 설정
물리 파라미터를 11개 카테고리로 그룹화:
1. **기본 물리** (PhysicsBasics): 중력, 접근력
2. **충돌 반발** (CollisionSettings): 반발력, 충돌 부스트
3. **마찰** (FrictionSettings): 각종 마찰 계수
4. **충돌 해결** (SolverSettings): 정밀도 설정
5. **충돌 강도** (ImpactSettings): 임팩트 계산
6. **밀려남** (RecoilSettings): 넉백 효과
7. **튕겨올림** (LaunchSettings): 팝업 효과
8. **데미지** (DamageSettings): 피해량 계산
9. **경직** (StaggerSettings): 스태거 시간
10. **원거리 공격** (RangedAttackSettings): 원거리 능력
11. **힐링** (HealingSettings): 치료 능력

## 1) Visual Duel Physics Lab

Run interactive multi-ball duel simulator:

```powershell
python visual_physics_lab.py
```

Default behavior:
- left and right balls spawn on the ground
- wide horizontal arena
- on collision both balls are launched into a parabolic arc and bounce on ground
- both balls get recoil; stronger ball is also pushed back briefly
- after stagger, each ball re-charges toward its forward direction
- `power` affects recoil/launch plus collision damage and stagger time

What you can tune in real time:
- per-ball setup using `Ball List` + `Ball Editor`
- ball class (`tank`, `dealer`, `healer`, `ranged_dealer`, `ranged_healer`)
- add / update / duplicate / remove balls
- save template from current ball and apply to one/all balls
- gravity
- approach force (how hard units push toward center)
- restitution (bounciness)
- collision friction
- ground friction
- linear damping
- collision boost
- solver passes
- position correction
- mass+power impact scale
- recoil/launch parameters
- launch height scale (multiplier for collision pop-up height)
- damage parameters
- stagger parameters
- save/load settings (`Save Settings`, `Load Settings`)
- auto-persist settings on apply/close (`visual_physics_lab_settings.json`)

Ball template tips:
- pick or edit a ball in `Ball Editor`
- set template name and click `Save Template`
- select template and click `Apply to Selected Ball` or `Apply to All Balls`

Controls:
- `Space`: pause/resume
- `R`: apply values and respawn
- `K`: random impulse kick
- `Enter`: apply values and respawn
- `B`: run battle-feel sweep report from current Lab state
- `N`: run random-combination battle-feel report from current Lab state
- battle end overlay: if all dead or only one survivor remains, click center panel to restart

## 2) Headless Battle Feel Sweep (Auto Report)

Run a non-visual simulation sweep that keeps environment physics values from
`visual_physics_lab_settings.json` and only varies ball-side profiles.

```powershell
python battle_sim_report.py
```

This creates:
- `reports/battle_feel_report_YYYYMMDD_HHMMSS.md`
- `reports/battle_feel_report_YYYYMMDD_HHMMSS.json`
- `reports/battle_feel_report_YYYYMMDD_HHMMSS.html`

Useful options:

```powershell
python battle_sim_report.py --seeds 8 --duration 30 --top-k 12 --speed-jitter 10
python battle_sim_report.py --mode random --random-scenarios 120 --profile-seed 77
```

You can also run the same sweep directly in Lab using `Run Battle Feel Report`
button (or `B` key). It uses current `Environment / Physics` + `Ball List` values.
For random matchups in Lab, use `Run Random Battle Report` (or `N` key).

## 3) Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

If `python` command is not available in your shell:

```powershell
C:\Users\9nain\AppData\Local\Programs\Python\Python312\python.exe visual_physics_lab.py
C:\Users\9nain\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## 4) Ball 클래스 및 물리 설정 사용 예제

### Ball 클래스 사용

```python
from autochess_combat.battle_sim import default_ball_classes, BallClass

# 기본 클래스 가져오기
classes = default_ball_classes()
dealer = classes[0]  # 딜러
tank = classes[1]    # 탱커
healer = classes[2]  # 힐러
ranged = classes[3]  # 원거리 딜러

# 커스텀 클래스 생성
assassin = BallClass(
    name="어쌔신",
    role="dealer",
    description="빠른 속도와 높은 공격력",
    base_radius=22.0,
    base_mass=0.6,
    base_power=1.5,
    base_hp=60.0,
    base_speed=320.0,
)
```

### 카테고리별 물리 설정

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
    damage=damage
)

# 기존 설정에서 카테고리 추출
existing_tuning = PhysicsTuning()
physics_config = existing_tuning.to_physics_basics()
damage_config = existing_tuning.to_damage_settings()
```

### 전체 예제 실행

```powershell
python ball_class_example.py
```

이 예제는 5가지 사용 패턴을 보여줍니다:
1. 기본 Ball 클래스 사용
2. 커스텀 Ball 클래스 생성
3. 카테고리별 물리 설정
4. 기존 설정에서 카테고리 추출
5. BallClass를 BallProfile로 변환
