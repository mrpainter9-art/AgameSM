from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk

from autochess_combat import PhysicsTuning, create_duel_world
from autochess_combat.physics_lab import PhysicsBody, PhysicsWorld


class PhysicsLabApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AgameSM Duel Physics Lab")

        self.canvas_width = 1460
        self.canvas_height = 520
        self.fixed_dt = 1.0 / 120.0
        self.accumulator = 0.0
        self.last_frame_time = time.perf_counter()
        self.paused = False
        self.status_message = "Simulation started."

        self.vars: dict[str, tk.Variable] = {
            "left_radius": tk.DoubleVar(value=32.0),
            "left_mass": tk.DoubleVar(value=1.0),
            "left_power": tk.DoubleVar(value=1.0),
            "left_hp": tk.DoubleVar(value=100.0),
            "left_speed": tk.DoubleVar(value=260.0),
            "right_radius": tk.DoubleVar(value=32.0),
            "right_mass": tk.DoubleVar(value=1.4),
            "right_power": tk.DoubleVar(value=1.8),
            "right_hp": tk.DoubleVar(value=100.0),
            "right_speed": tk.DoubleVar(value=210.0),
            "side_margin": tk.DoubleVar(value=120.0),
            "gravity": tk.DoubleVar(value=900.0),
            "approach_force": tk.DoubleVar(value=1150.0),
            "restitution": tk.DoubleVar(value=0.68),
            "wall_restitution": tk.DoubleVar(value=0.55),
            "linear_damping": tk.DoubleVar(value=0.16),
            "friction": tk.DoubleVar(value=0.20),
            "wall_friction": tk.DoubleVar(value=0.08),
            "ground_friction": tk.DoubleVar(value=0.30),
            "ground_snap_speed": tk.DoubleVar(value=42.0),
            "collision_boost": tk.DoubleVar(value=1.00),
            "solver_passes": tk.IntVar(value=3),
            "position_correction": tk.DoubleVar(value=0.80),
            "power_ratio_exponent": tk.DoubleVar(value=0.50),
            "impact_speed_cap": tk.DoubleVar(value=1400.0),
            "min_recoil_speed": tk.DoubleVar(value=45.0),
            "recoil_scale": tk.DoubleVar(value=0.62),
            "min_launch_speed": tk.DoubleVar(value=90.0),
            "launch_scale": tk.DoubleVar(value=0.45),
            "max_launch_speed": tk.DoubleVar(value=820.0),
            "damage_base": tk.DoubleVar(value=1.50),
            "damage_scale": tk.DoubleVar(value=0.028),
            "stagger_base": tk.DoubleVar(value=0.06),
            "stagger_scale": tk.DoubleVar(value=0.0012),
            "max_stagger": tk.DoubleVar(value=1.20),
            "stagger_drive_multiplier": tk.DoubleVar(value=0.0),
        }

        self.status_var = tk.StringVar(value="")
        self.world = self._create_world()
        self._build_ui()
        self._bind_keys()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#0f141c",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        controls = ttk.Frame(container, padding=(12, 4, 0, 4))
        controls.grid(row=0, column=1, sticky="ns")

        row = 0
        ttk.Label(controls, text="Left Ball", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        row += 1
        for key, label in [
            ("left_radius", "Radius"),
            ("left_mass", "Mass"),
            ("left_power", "Power"),
            ("left_hp", "HP"),
            ("left_speed", "Initial Speed"),
        ]:
            row = self._add_field(controls, row, key, label)

        ttk.Label(controls, text="Right Ball", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(10, 6)
        )
        row += 1
        for key, label in [
            ("right_radius", "Radius"),
            ("right_mass", "Mass"),
            ("right_power", "Power"),
            ("right_hp", "HP"),
            ("right_speed", "Initial Speed"),
        ]:
            row = self._add_field(controls, row, key, label)

        ttk.Label(controls, text="Motion / Contact", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(10, 6)
        )
        row += 1
        for key, label in [
            ("side_margin", "Side Margin"),
            ("gravity", "Gravity"),
            ("approach_force", "Approach Force"),
            ("restitution", "Restitution"),
            ("wall_restitution", "Wall Restitution"),
            ("linear_damping", "Linear Damping"),
            ("friction", "Collision Friction"),
            ("wall_friction", "Wall Friction"),
            ("ground_friction", "Ground Friction"),
            ("ground_snap_speed", "Ground Snap Speed"),
            ("collision_boost", "Collision Boost"),
            ("solver_passes", "Solver Passes"),
            ("position_correction", "Position Correction"),
        ]:
            row = self._add_field(controls, row, key, label)

        ttk.Label(controls, text="Impact / Damage / Stagger", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(10, 6)
        )
        row += 1
        for key, label in [
            ("power_ratio_exponent", "Power Ratio Exp"),
            ("impact_speed_cap", "Impact Speed Cap"),
            ("min_recoil_speed", "Min Recoil Speed"),
            ("recoil_scale", "Recoil Scale"),
            ("min_launch_speed", "Min Launch Speed"),
            ("launch_scale", "Launch Scale"),
            ("max_launch_speed", "Max Launch Speed"),
            ("damage_base", "Damage Base"),
            ("damage_scale", "Damage Scale"),
            ("stagger_base", "Stagger Base"),
            ("stagger_scale", "Stagger Scale"),
            ("max_stagger", "Max Stagger"),
            ("stagger_drive_multiplier", "Stagger Drive Mult"),
        ]:
            row = self._add_field(controls, row, key, label)

        ttk.Button(controls, text="Apply (No Respawn)", command=self.apply_no_respawn).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 4)
        )
        row += 1
        ttk.Button(controls, text="Apply + Respawn", command=self.apply_and_respawn).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Random Kick", command=self.random_kick).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Pause / Resume (Space)", command=self.toggle_pause).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Step 1 Tick", command=self.step_once).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=4
        )
        row += 1

        ttk.Label(
            controls,
            text="Keys: Space pause, R respawn, K random kick, Enter apply+respawn",
            wraplength=300,
            justify="left",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 6))
        row += 1
        ttk.Label(controls, textvariable=self.status_var, wraplength=300, justify="left").grid(
            row=row, column=0, columnspan=2, sticky="w"
        )

    def _add_field(self, parent: ttk.Frame, row: int, key: str, label: str) -> int:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Entry(parent, textvariable=self.vars[key], width=13).grid(row=row, column=1, sticky="ew", pady=2)
        return row + 1

    def _bind_keys(self) -> None:
        self.root.bind("<space>", lambda _: self.toggle_pause())
        self.root.bind("<Return>", lambda _: self.apply_and_respawn())
        self.root.bind("r", lambda _: self.apply_and_respawn())
        self.root.bind("k", lambda _: self.random_kick())

    def _build_tuning(self) -> PhysicsTuning:
        return PhysicsTuning(
            gravity=float(self.vars["gravity"].get()),
            approach_force=float(self.vars["approach_force"].get()),
            restitution=float(self.vars["restitution"].get()),
            wall_restitution=float(self.vars["wall_restitution"].get()),
            linear_damping=float(self.vars["linear_damping"].get()),
            friction=float(self.vars["friction"].get()),
            wall_friction=float(self.vars["wall_friction"].get()),
            ground_friction=float(self.vars["ground_friction"].get()),
            ground_snap_speed=float(self.vars["ground_snap_speed"].get()),
            collision_boost=float(self.vars["collision_boost"].get()),
            solver_passes=int(self.vars["solver_passes"].get()),
            position_correction=float(self.vars["position_correction"].get()),
            power_ratio_exponent=float(self.vars["power_ratio_exponent"].get()),
            impact_speed_cap=float(self.vars["impact_speed_cap"].get()),
            min_recoil_speed=float(self.vars["min_recoil_speed"].get()),
            recoil_scale=float(self.vars["recoil_scale"].get()),
            min_launch_speed=float(self.vars["min_launch_speed"].get()),
            launch_scale=float(self.vars["launch_scale"].get()),
            max_launch_speed=float(self.vars["max_launch_speed"].get()),
            damage_base=float(self.vars["damage_base"].get()),
            damage_scale=float(self.vars["damage_scale"].get()),
            stagger_base=float(self.vars["stagger_base"].get()),
            stagger_scale=float(self.vars["stagger_scale"].get()),
            max_stagger=float(self.vars["max_stagger"].get()),
            stagger_drive_multiplier=float(self.vars["stagger_drive_multiplier"].get()),
        )

    def _create_world(self) -> PhysicsWorld:
        tuning = self._build_tuning()
        return create_duel_world(
            width=self.canvas_width,
            height=self.canvas_height,
            left_radius=float(self.vars["left_radius"].get()),
            right_radius=float(self.vars["right_radius"].get()),
            left_mass=float(self.vars["left_mass"].get()),
            right_mass=float(self.vars["right_mass"].get()),
            left_power=float(self.vars["left_power"].get()),
            right_power=float(self.vars["right_power"].get()),
            left_hp=float(self.vars["left_hp"].get()),
            right_hp=float(self.vars["right_hp"].get()),
            left_initial_speed=float(self.vars["left_speed"].get()),
            right_initial_speed=float(self.vars["right_speed"].get()),
            side_margin=float(self.vars["side_margin"].get()),
            tuning=tuning,
        )

    def apply_no_respawn(self) -> None:
        try:
            self.world.set_tuning(self._build_tuning())
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_message = "Applied tuning without respawn."
        self._refresh_status()

    def apply_and_respawn(self) -> None:
        try:
            self.world = self._create_world()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_message = "Applied values and respawned both balls on ground."
        self._refresh_status()

    def random_kick(self) -> None:
        self.world.add_random_impulse(magnitude=460.0)
        self.status_message = "Applied random impulse."
        self._refresh_status()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.status_message = "Paused." if self.paused else "Running."
        self._refresh_status()

    def step_once(self) -> None:
        self.world.step(self.fixed_dt)
        self._draw_world()
        self.status_message = "Advanced one physics tick."
        self._refresh_status()

    def _find_body(self, team: str) -> PhysicsBody | None:
        for body in self.world.bodies:
            if body.team == team:
                return body
        return None

    def _refresh_status(self) -> None:
        left = self._find_body("left")
        right = self._find_body("right")
        left_speed = 0.0 if left is None else (left.vx * left.vx + left.vy * left.vy) ** 0.5
        right_speed = 0.0 if right is None else (right.vx * right.vx + right.vy * right.vy) ** 0.5
        left_hp = 0.0 if left is None else left.hp
        right_hp = 0.0 if right is None else right.hp
        left_stagger = 0.0 if left is None else left.stagger_timer
        right_stagger = 0.0 if right is None else right.stagger_timer
        live = (
            f"time={self.world.time_elapsed:6.2f}s | "
            f"L hp={left_hp:6.1f} stg={left_stagger:4.2f} spd={left_speed:7.2f} | "
            f"R hp={right_hp:6.1f} stg={right_stagger:4.2f} spd={right_speed:7.2f} | "
            f"step_collisions={self.world.last_step_collisions:2d}"
        )
        self.status_var.set(f"{self.status_message}\n{live}")

    def _draw_world(self) -> None:
        self.canvas.delete("all")

        self.canvas.create_rectangle(
            0,
            0,
            self.canvas_width,
            self.canvas_height,
            fill="#121923",
            outline="",
        )

        ground_y = self.canvas_height - 1
        self.canvas.create_rectangle(
            0,
            self.canvas_height - 28,
            self.canvas_width,
            self.canvas_height,
            fill="#1f2b3a",
            outline="",
        )
        self.canvas.create_line(
            0,
            ground_y,
            self.canvas_width,
            ground_y,
            fill="#6a7f95",
            width=2,
        )
        self.canvas.create_line(
            self.canvas_width * 0.5,
            0,
            self.canvas_width * 0.5,
            self.canvas_height,
            fill="#243041",
            dash=(6, 6),
        )

        for body in self.world.bodies:
            r = body.radius
            fill = body.color if body.is_alive else "#777777"
            self.canvas.create_oval(
                body.x - r,
                body.y - r,
                body.x + r,
                body.y + r,
                fill=fill,
                outline="#0a0a0a",
                width=2,
            )
            self.canvas.create_line(
                body.x,
                body.y,
                body.x - body.vx * 0.08,
                body.y - body.vy * 0.08,
                fill="#f6f7f9",
                width=1,
            )
            self.canvas.create_text(
                body.x,
                body.y - r - 28,
                text=f"{body.team} HP={body.hp:5.1f}/{body.max_hp:5.1f}",
                fill="#dce6f2",
                font=("Consolas", 10),
            )
            self.canvas.create_text(
                body.x,
                body.y - r - 14,
                text=f"P={body.power:.2f} STG={body.stagger_timer:.2f} DMG={body.last_damage:.2f}",
                fill="#dce6f2",
                font=("Consolas", 10),
            )

        self.canvas.create_text(
            14,
            14,
            anchor="nw",
            fill="#dce6f2",
            font=("Consolas", 11),
            text=(
                f"time {self.world.time_elapsed:6.2f}s   "
                f"max_speed {self.world.max_speed():7.2f}   "
                f"collisions {self.world.last_step_collisions:2d}"
            ),
        )

    def run(self) -> None:
        self._refresh_status()
        self._tick()
        self.root.mainloop()

    def _tick(self) -> None:
        now = time.perf_counter()
        frame_dt = min(0.1, now - self.last_frame_time)
        self.last_frame_time = now

        if not self.paused:
            self.accumulator += frame_dt
            while self.accumulator >= self.fixed_dt:
                self.world.step(self.fixed_dt)
                self.accumulator -= self.fixed_dt

        self._draw_world()
        self._refresh_status()
        self.root.after(16, self._tick)


def main() -> None:
    root = tk.Tk()
    app = PhysicsLabApp(root)
    app.run()


if __name__ == "__main__":
    main()
