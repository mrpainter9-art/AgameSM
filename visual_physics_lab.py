from __future__ import annotations

import json
from pathlib import Path
import time
import tkinter as tk
from tkinter import messagebox, ttk

from autochess_combat import PhysicsTuning, create_duel_world
from autochess_combat.physics_lab import PhysicsBody, PhysicsWorld


FIELD_HELP_KO: dict[str, str] = {
    "balls_per_side": "좌/우 팀당 생성할 볼 개수. 기본 3.",
    "left_radius": "왼쪽 공 반지름(px). 값이 커질수록 충돌 범위가 넓어집니다.",
    "left_mass": "왼쪽 공 질량. 클수록 같은 힘에서 덜 밀리고, 반동/발사 속도 변화가 줄어듭니다.",
    "left_power": "왼쪽 공 파워. 클수록 충돌 시 상대에게 주는 반동/피해/경직 영향이 커집니다.",
    "left_hp": "왼쪽 공 최대 체력(리스폰 시 적용).",
    "left_speed": "왼쪽 공 시작 수평 속도(px/s).",
    "left_invincible": "왼쪽 팀 무적 모드. 켜면 HP가 줄지 않습니다.",
    "right_radius": "오른쪽 공 반지름(px).",
    "right_mass": "오른쪽 공 질량.",
    "right_power": "오른쪽 공 파워.",
    "right_hp": "오른쪽 공 최대 체력(리스폰 시 적용).",
    "right_speed": "오른쪽 공 시작 수평 속도(px/s).",
    "right_invincible": "오른쪽 팀 무적 모드. 켜면 HP가 줄지 않습니다.",
    "side_margin": "양쪽 벽에서 스폰되는 여백 거리(px).",
    "gravity": "중력 가속도(px/s^2). 높일수록 더 빨리 떨어져 낮게 뜹니다.",
    "approach_force": "정면 방향으로 밀어주는 추진력. 경직이 끝난 뒤 다시 돌진하는 속도에 영향.",
    "restitution": "공-공 충돌 탄성 계수. 높을수록 더 튕깁니다.",
    "wall_restitution": "벽/바닥 반발 계수.",
    "linear_damping": "공기저항(속도 감쇠). 높을수록 전체 속도가 빨리 줄어듭니다.",
    "friction": "공-공 충돌 시 접선 마찰.",
    "wall_friction": "벽 충돌 시 접선 마찰.",
    "ground_friction": "바닥에서 미끄러질 때 감속 마찰.",
    "ground_snap_speed": "이 속도 이하로 바닥에 닿으면 y속도를 0으로 스냅합니다.",
    "collision_boost": "충돌 임펄스 전체 배율. 충돌 반응을 강하게/약하게 만듭니다.",
    "solver_passes": "충돌 해석 반복 횟수. 높을수록 안정적이지만 계산량이 늘어납니다.",
    "position_correction": "겹침 보정 강도(0~1).",
    "mass_power_impact_scale": "질량+파워 기반 충돌 영향량의 전체 배율.",
    "power_ratio_exponent": "파워 비율이 충돌 영향량에 반영되는 정도.",
    "impact_speed_cap": "충돌 영향량 상한(과도한 값 제한).",
    "min_recoil_speed": "충돌 시 최소 수평 반동량.",
    "recoil_scale": "충돌 강도에 따른 수평 반동 증가율.",
    "min_launch_speed": "충돌 시 최소 수직 발사량(위로 튀는 기본값).",
    "launch_scale": "충돌 강도에 따른 수직 발사 증가율.",
    "launch_height_scale": (
        "충돌 후 튀어오르는 높이 배율. 1.0 기본, 2.0이면 더 높게 뜹니다 "
        "(최종 발사량은 Max Launch Speed 상한 적용)."
    ),
    "max_launch_speed": "수직 발사량 상한.",
    "damage_base": "충돌 시 기본 피해량.",
    "damage_scale": "충돌 강도에 따른 피해 증가율.",
    "stagger_base": "충돌 시 기본 경직 시간(초).",
    "stagger_scale": "충돌 강도에 따른 경직 증가율.",
    "max_stagger": "경직 시간 상한(초).",
    "stagger_drive_multiplier": "경직 중 이동 추진력 배율(0이면 경직 중 거의 정지).",
}

SETTINGS_FILE_NAME = "visual_physics_lab_settings.json"
SETTINGS_VERSION = 1


class HoverTooltip:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window: tk.Toplevel | None = None
        self.label: tk.Label | None = None

    def show(self, text: str, x: int, y: int) -> None:
        if not text:
            return
        if self.window is None or not self.window.winfo_exists():
            self.window = tk.Toplevel(self.root)
            self.window.withdraw()
            self.window.overrideredirect(True)
            try:
                self.window.attributes("-topmost", True)
            except tk.TclError:
                pass
            self.label = tk.Label(
                self.window,
                text="",
                justify="left",
                bg="#121923",
                fg="#dce6f2",
                relief="solid",
                bd=1,
                font=("Segoe UI", 9),
                padx=8,
                pady=6,
                wraplength=320,
            )
            self.label.pack()

        if self.label is None:
            return
        self.label.configure(text=text)
        self.window.geometry(f"+{x + 14}+{y + 14}")
        self.window.deiconify()
        self.window.lift()

    def hide(self) -> None:
        if self.window is not None and self.window.winfo_exists():
            self.window.withdraw()


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
        self.controls_wraplength = 300
        self.tooltip = HoverTooltip(root)

        self.vars: dict[str, tk.Variable] = {
            "balls_per_side": tk.IntVar(value=3),
            "left_radius": tk.DoubleVar(value=32.0),
            "left_mass": tk.DoubleVar(value=1.0),
            "left_power": tk.DoubleVar(value=1.0),
            "left_hp": tk.DoubleVar(value=100.0),
            "left_speed": tk.DoubleVar(value=260.0),
            "left_invincible": tk.BooleanVar(value=False),
            "right_radius": tk.DoubleVar(value=32.0),
            "right_mass": tk.DoubleVar(value=1.4),
            "right_power": tk.DoubleVar(value=1.8),
            "right_hp": tk.DoubleVar(value=100.0),
            "right_speed": tk.DoubleVar(value=210.0),
            "right_invincible": tk.BooleanVar(value=False),
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
            "mass_power_impact_scale": tk.DoubleVar(value=120.0),
            "power_ratio_exponent": tk.DoubleVar(value=0.50),
            "impact_speed_cap": tk.DoubleVar(value=1400.0),
            "min_recoil_speed": tk.DoubleVar(value=45.0),
            "recoil_scale": tk.DoubleVar(value=0.62),
            "min_launch_speed": tk.DoubleVar(value=90.0),
            "launch_scale": tk.DoubleVar(value=0.45),
            "launch_height_scale": tk.DoubleVar(value=1.0),
            "max_launch_speed": tk.DoubleVar(value=820.0),
            "damage_base": tk.DoubleVar(value=1.50),
            "damage_scale": tk.DoubleVar(value=0.028),
            "stagger_base": tk.DoubleVar(value=0.06),
            "stagger_scale": tk.DoubleVar(value=0.0012),
            "max_stagger": tk.DoubleVar(value=1.20),
            "stagger_drive_multiplier": tk.DoubleVar(value=0.0),
        }
        self.lock_vars: dict[str, tk.BooleanVar] = {
            key: tk.BooleanVar(value=False) for key in self.vars
        }
        self.value_widgets: dict[str, tk.Widget] = {}
        self.settings_path = Path(__file__).resolve().with_name(SETTINGS_FILE_NAME)
        self._load_settings_from_disk(silent=True)

        self.status_var = tk.StringVar(value="")
        self.world = self._create_world()
        self._build_ui()
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        controls_outer = ttk.Frame(container, padding=(12, 4, 0, 4))
        controls_outer.grid(row=0, column=1, sticky="ns")
        controls_outer.rowconfigure(0, weight=1)
        controls_outer.columnconfigure(0, weight=1)

        self.controls_canvas = tk.Canvas(controls_outer, width=340, highlightthickness=0)
        self.controls_canvas.grid(row=0, column=0, sticky="nsew")
        controls_scroll = ttk.Scrollbar(
            controls_outer, orient="vertical", command=self.controls_canvas.yview
        )
        controls_scroll.grid(row=0, column=1, sticky="ns")
        self.controls_canvas.configure(yscrollcommand=controls_scroll.set)

        self.controls_frame = ttk.Frame(self.controls_canvas)
        self.controls_window = self.controls_canvas.create_window(
            (0, 0), window=self.controls_frame, anchor="nw"
        )
        self.controls_frame.bind("<Configure>", self._on_controls_frame_configure)
        self.controls_canvas.bind("<Configure>", self._on_controls_canvas_configure)
        self.controls_canvas.bind("<MouseWheel>", self._on_controls_mousewheel)
        self.controls_frame.bind("<MouseWheel>", self._on_controls_mousewheel)

        controls = self.controls_frame
        controls.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(controls, text="Settings", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )
        row += 1
        ttk.Button(controls, text="Save Settings", command=self.save_settings).grid(
            row=row, column=1, sticky="ew", pady=2
        )
        ttk.Button(controls, text="Load Settings", command=self.load_settings).grid(
            row=row, column=2, sticky="ew", padx=(6, 0), pady=2
        )
        row += 1
        ttk.Button(controls, text="Lock All", command=self.lock_all_fields).grid(
            row=row, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Button(controls, text="Unlock All", command=self.unlock_all_fields).grid(
            row=row, column=2, sticky="ew", padx=(6, 0), pady=(0, 6)
        )
        row += 1

        row = self._add_field(controls, row, "balls_per_side", "Balls Per Side")

        ttk.Label(controls, text="Left Ball", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 6)
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
        row = self._add_toggle(controls, row, "left_invincible", "Invincible")

        ttk.Label(controls, text="Right Ball", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(10, 6)
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
        row = self._add_toggle(controls, row, "right_invincible", "Invincible")

        ttk.Label(controls, text="Motion / Contact", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(10, 6)
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
            row=row, column=0, columnspan=3, sticky="w", pady=(10, 6)
        )
        row += 1
        for key, label in [
            ("power_ratio_exponent", "Power Ratio Exp"),
            ("mass_power_impact_scale", "Mass+Power Scale"),
            ("impact_speed_cap", "Impact Speed Cap"),
            ("min_recoil_speed", "Min Recoil Speed"),
            ("recoil_scale", "Recoil Scale"),
            ("min_launch_speed", "Min Launch Speed"),
            ("launch_scale", "Launch Scale"),
            ("launch_height_scale", "Launch Height Scale"),
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
            row=row, column=0, columnspan=3, sticky="ew", pady=(10, 4)
        )
        row += 1
        ttk.Button(controls, text="Apply + Respawn", command=self.apply_and_respawn).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Random Kick", command=self.random_kick).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Pause / Resume (Space)", command=self.toggle_pause).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=4
        )
        row += 1
        ttk.Button(controls, text="Step 1 Tick", command=self.step_once).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=4
        )
        row += 1

        self.keys_label = ttk.Label(
            controls,
            text="Keys: Space pause, R respawn, K random kick, Enter apply+respawn",
            wraplength=self.controls_wraplength,
            justify="left",
        )
        self.keys_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(10, 6))
        row += 1
        self.status_label = ttk.Label(
            controls,
            textvariable=self.status_var,
            wraplength=self.controls_wraplength,
            justify="left",
        )
        self.status_label.grid(row=row, column=0, columnspan=3, sticky="w")

    def _add_field(self, parent: ttk.Frame, row: int, key: str, label: str) -> int:
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        entry_widget = ttk.Entry(parent, textvariable=self.vars[key], width=13)
        entry_widget.grid(row=row, column=1, sticky="ew", pady=2)
        self.value_widgets[key] = entry_widget
        lock_widget = ttk.Checkbutton(
            parent,
            text="Lock",
            variable=self.lock_vars[key],
            command=lambda field=key: self._on_lock_toggled(field),
        )
        lock_widget.grid(row=row, column=2, sticky="w", padx=(6, 0), pady=2)
        self._bind_field_help(label_widget, key)
        self._bind_field_help(entry_widget, key)
        self._bind_field_help(lock_widget, key)
        self._apply_widget_lock_state(key)
        return row + 1

    def _add_toggle(self, parent: ttk.Frame, row: int, key: str, label: str) -> int:
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        toggle_widget = ttk.Checkbutton(parent, variable=self.vars[key])
        toggle_widget.grid(row=row, column=1, sticky="w", pady=2)
        self.value_widgets[key] = toggle_widget
        lock_widget = ttk.Checkbutton(
            parent,
            text="Lock",
            variable=self.lock_vars[key],
            command=lambda field=key: self._on_lock_toggled(field),
        )
        lock_widget.grid(row=row, column=2, sticky="w", padx=(6, 0), pady=2)
        self._bind_field_help(label_widget, key)
        self._bind_field_help(toggle_widget, key)
        self._bind_field_help(lock_widget, key)
        self._apply_widget_lock_state(key)
        return row + 1

    def _bind_field_help(self, widget: tk.Widget, key: str) -> None:
        widget.bind("<Enter>", lambda event, field=key: self._show_field_help(event, field))
        widget.bind("<Motion>", lambda event, field=key: self._show_field_help(event, field))
        widget.bind("<Leave>", lambda _: self.tooltip.hide())

    def _show_field_help(self, event: tk.Event, key: str) -> None:
        help_text = FIELD_HELP_KO.get(key)
        if help_text is None:
            self.tooltip.hide()
            return
        self.tooltip.show(help_text, event.x_root, event.y_root)

    def _apply_widget_lock_state(self, key: str) -> None:
        widget = self.value_widgets.get(key)
        lock_var = self.lock_vars.get(key)
        if widget is None or lock_var is None:
            return
        if lock_var.get():
            widget.state(["disabled"])
        else:
            widget.state(["!disabled"])

    def _on_lock_toggled(self, key: str) -> None:
        self._apply_widget_lock_state(key)
        self._save_settings_to_disk(silent=True)

    def lock_all_fields(self) -> None:
        for key, lock_var in self.lock_vars.items():
            lock_var.set(True)
            self._apply_widget_lock_state(key)
        self.status_message = "Locked all fields."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def unlock_all_fields(self) -> None:
        for key, lock_var in self.lock_vars.items():
            lock_var.set(False)
            self._apply_widget_lock_state(key)
        self.status_message = "Unlocked all fields."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def _get_var_value(self, key: str) -> int | float | bool:
        var = self.vars[key]
        if isinstance(var, tk.BooleanVar):
            return bool(var.get())
        if isinstance(var, tk.IntVar):
            return int(var.get())
        return float(var.get())

    def _set_var_value(self, key: str, value: int | float | bool) -> None:
        var = self.vars[key]
        if isinstance(var, tk.BooleanVar):
            var.set(bool(value))
            return
        if isinstance(var, tk.IntVar):
            var.set(int(value))
            return
        var.set(float(value))

    def _build_settings_payload(self) -> dict[str, object]:
        return {
            "version": SETTINGS_VERSION,
            "values": {key: self._get_var_value(key) for key in self.vars},
            "locks": {key: bool(lock_var.get()) for key, lock_var in self.lock_vars.items()},
        }

    def _apply_settings_payload(self, payload: dict[str, object]) -> None:
        raw_values = payload.get("values")
        if isinstance(raw_values, dict):
            for key, value in raw_values.items():
                if key not in self.vars:
                    continue
                self._set_var_value(key, value)

        raw_locks = payload.get("locks")
        if isinstance(raw_locks, dict):
            for key, value in raw_locks.items():
                if key not in self.lock_vars:
                    continue
                self.lock_vars[key].set(bool(value))
                self._apply_widget_lock_state(key)

    def _save_settings_to_disk(self, *, silent: bool = False) -> bool:
        payload = self._build_settings_payload()
        try:
            self.settings_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            if not silent:
                messagebox.showerror("Save Failed", f"Could not save settings:\n{exc}")
            return False
        return True

    def _load_settings_from_disk(self, *, silent: bool = False) -> bool:
        if not self.settings_path.exists():
            return False
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            if not silent:
                messagebox.showerror("Load Failed", f"Could not load settings:\n{exc}")
            return False

        if not isinstance(payload, dict):
            if not silent:
                messagebox.showerror("Load Failed", "Settings file format is invalid.")
            return False

        try:
            self._apply_settings_payload(payload)
        except (TypeError, ValueError) as exc:
            if not silent:
                messagebox.showerror("Load Failed", f"Invalid settings value:\n{exc}")
            return False
        return True

    def save_settings(self) -> None:
        if self._save_settings_to_disk():
            self.status_message = f"Saved settings to {self.settings_path.name}."
            self._refresh_status()

    def load_settings(self) -> None:
        if not self._load_settings_from_disk():
            messagebox.showinfo(
                "No Saved Settings",
                f"Settings file not found:\n{self.settings_path}",
            )
            return
        try:
            self.world = self._create_world()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_message = f"Loaded settings from {self.settings_path.name} and respawned."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def _on_canvas_resize(self, event: tk.Event) -> None:
        new_width = max(1, int(event.width))
        new_height = max(1, int(event.height))
        if new_width == self.canvas_width and new_height == self.canvas_height:
            return

        delta_h = new_height - self.canvas_height
        self.canvas_width = new_width
        self.canvas_height = new_height
        self.world.width = float(new_width)
        self.world.height = float(new_height)

        if abs(delta_h) > 1e-6:
            for body in self.world.bodies:
                body.y += delta_h

        for body in self.world.bodies:
            r = body.radius
            body.x = min(self.world.width - r, max(r, body.x))
            body.y = min(self.world.height - r, max(r, body.y))

    def _on_controls_frame_configure(self, _: tk.Event) -> None:
        bbox = self.controls_canvas.bbox("all")
        if bbox is not None:
            self.controls_canvas.configure(scrollregion=bbox)

    def _on_controls_canvas_configure(self, event: tk.Event) -> None:
        self.controls_canvas.itemconfigure(self.controls_window, width=event.width)
        wrap = max(200, event.width - 20)
        if wrap != self.controls_wraplength:
            self.controls_wraplength = wrap
            keys_label = getattr(self, "keys_label", None)
            status_label = getattr(self, "status_label", None)
            if keys_label is not None:
                keys_label.configure(wraplength=wrap)
            if status_label is not None:
                status_label.configure(wraplength=wrap)

    def _on_controls_mousewheel(self, event: tk.Event) -> None:
        if event.delta == 0:
            return
        self.tooltip.hide()
        self.controls_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
            mass_power_impact_scale=float(self.vars["mass_power_impact_scale"].get()),
            power_ratio_exponent=float(self.vars["power_ratio_exponent"].get()),
            impact_speed_cap=float(self.vars["impact_speed_cap"].get()),
            min_recoil_speed=float(self.vars["min_recoil_speed"].get()),
            recoil_scale=float(self.vars["recoil_scale"].get()),
            min_launch_speed=float(self.vars["min_launch_speed"].get()),
            launch_scale=float(self.vars["launch_scale"].get()),
            launch_height_scale=float(self.vars["launch_height_scale"].get()),
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
            balls_per_side=int(self.vars["balls_per_side"].get()),
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
            left_invincible=bool(self.vars["left_invincible"].get()),
            right_invincible=bool(self.vars["right_invincible"].get()),
            tuning=tuning,
        )

    def _selected_invincible_teams(self) -> set[str]:
        teams: set[str] = set()
        if bool(self.vars["left_invincible"].get()):
            teams.add("left")
        if bool(self.vars["right_invincible"].get()):
            teams.add("right")
        return teams

    def apply_no_respawn(self) -> None:
        try:
            self.world.set_tuning(self._build_tuning())
            self.world.set_invincible_teams(self._selected_invincible_teams())
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_message = "Applied tuning/invincible settings without respawn."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def apply_and_respawn(self) -> None:
        try:
            self.world = self._create_world()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        balls_per_side = int(self.vars["balls_per_side"].get())
        self.status_message = f"Applied values and respawned {balls_per_side} balls per side."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

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

    def _team_bodies(self, team: str) -> list[PhysicsBody]:
        return [body for body in self.world.bodies if body.team == team]

    def _team_live_stats(self, team: str) -> tuple[int, int, float, float, float]:
        bodies = self._team_bodies(team)
        if not bodies:
            return 0, 0, 0.0, 0.0, 0.0

        count = len(bodies)
        alive_count = sum(1 for body in bodies if body.is_alive)
        avg_hp = sum(body.hp for body in bodies) / count
        avg_stagger = sum(body.stagger_timer for body in bodies) / count
        avg_speed = (
            sum((body.vx * body.vx + body.vy * body.vy) ** 0.5 for body in bodies) / count
        )
        return count, alive_count, avg_hp, avg_stagger, avg_speed

    def _refresh_status(self) -> None:
        left_count, left_alive, left_hp, left_stagger, left_speed = self._team_live_stats("left")
        right_count, right_alive, right_hp, right_stagger, right_speed = self._team_live_stats("right")
        left_mode = "INV" if self.world.is_team_invincible("left") else "DMG"
        right_mode = "INV" if self.world.is_team_invincible("right") else "DMG"
        live = (
            f"time={self.world.time_elapsed:6.2f}s | "
            f"L {left_alive}/{left_count} {left_mode} hp={left_hp:6.1f} stg={left_stagger:4.2f} spd={left_speed:7.2f} | "
            f"R {right_alive}/{right_count} {right_mode} hp={right_hp:6.1f} stg={right_stagger:4.2f} spd={right_speed:7.2f} | "
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
                text=(
                    f"{body.team} "
                    f"{'INV' if self.world.is_team_invincible(body.team) else 'DMG'} "
                    f"HP={body.hp:5.1f}/{body.max_hp:5.1f}"
                ),
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

    def _on_close(self) -> None:
        self._save_settings_to_disk(silent=True)
        self.root.destroy()

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
