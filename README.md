# AgameSM

Python prototype workspace for collision-physics visualization.

## 1) Visual Duel Physics Lab

Run interactive 2-ball duel simulator:

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
- balls per side
- left radius
- left mass
- left power
- left hp
- left initial speed
- left invincible
- right radius
- right mass
- right power
- right hp
- right initial speed
- right invincible
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

Controls:
- `Space`: pause/resume
- `R`: apply values and respawn
- `K`: random impulse kick
- `Enter`: apply values and respawn

## 2) Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

If `python` command is not available in your shell:

```powershell
C:\Users\9nain\AppData\Local\Programs\Python\Python312\python.exe visual_physics_lab.py
C:\Users\9nain\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover -s tests -p "test_*.py" -v
```
