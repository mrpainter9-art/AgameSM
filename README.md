# AgameSM

Python prototype workspace for collision-physics visualization.

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
