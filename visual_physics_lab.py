from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import math
from pathlib import Path
import time
import tkinter as tk
from tkinter import messagebox, ttk

from autochess_combat import PhysicsTuning
from autochess_combat.battle_sim import (
    default_ball_classes,
    run_random_profile_sweep_from_settings_payload,
    run_profile_sweep_from_settings_payload,
    sweep_result_to_html,
    sweep_result_to_json_dict,
    sweep_result_to_markdown,
)
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
CUSTOM_BALLS_TEMPLATE: dict[str, object] = {
    "invincible_teams": [],
    "balls": [
        {
            "team": "left",
            "role": "tank",
            "radius": 24,
            "mass": 0.9,
            "power": 1.1,
            "hp": 110,
            "vx": 280,
        },
        {
            "team": "left",
            "role": "ranged_healer",
            "radius": 36,
            "mass": 1.8,
            "power": 1.6,
            "hp": 160,
            "vx": 180,
        },
        {
            "team": "right",
            "role": "dealer",
            "radius": 30,
            "mass": 1.3,
            "power": 1.7,
            "hp": 120,
            "vx": -240,
        },
        {
            "team": "right",
            "role": "ranged_dealer",
            "radius": 42,
            "mass": 2.4,
            "power": 2.2,
            "hp": 210,
            "vx": -140,
        },
    ],
}


@dataclass
class RingEffect:
    x: float
    y: float
    start_radius: float
    end_radius: float
    color: str
    ttl: float
    duration: float
    width: float


@dataclass
class FloatingTextEffect:
    x: float
    y: float
    text: str
    color: str
    ttl: float
    duration: float
    rise_speed: float
    drift_speed: float
    font_size: int


@dataclass
class HpBarAnimState:
    display_ratio: float
    chip_ratio: float
    pulse_ttl: float = 0.0
    pulse_duration: float = 0.0
    pulse_color: str = "#4ad06f"


@dataclass
class DeathParticleEffect:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: str
    ttl: float
    duration: float


@dataclass
class DeathFadeState:
    x: float
    y: float
    radius: float
    base_color: str
    ttl: float
    duration: float


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
        self.custom_data_text_widget: tk.Text | None = None
        self.custom_data_text = json.dumps(CUSTOM_BALLS_TEMPLATE, indent=2)
        self.ball_specs: list[dict[str, object]] = []
        self.ball_templates: dict[str, dict[str, object]] = {}
        self.ball_tree: ttk.Treeview | None = None
        self.ball_tree_editor: tk.Widget | None = None
        self.ball_tree_editor_item: str | None = None
        self.ball_tree_editor_column: str | None = None
        self.template_listbox: tk.Listbox | None = None
        self._loading_editor_spec = False
        self._syncing_editor_team = False
        self.ball_editor_vars: dict[str, tk.Variable] = {
            "team": tk.StringVar(value="left"),
            "role": tk.StringVar(value="dealer"),
            "radius": tk.DoubleVar(value=32.0),
            "mass": tk.DoubleVar(value=1.0),
            "power": tk.DoubleVar(value=1.0),
            "hp": tk.DoubleVar(value=100.0),
            "max_hp": tk.DoubleVar(value=100.0),
            "vx": tk.DoubleVar(value=260.0),
            "vy": tk.DoubleVar(value=0.0),
            "forward_dir": tk.DoubleVar(value=1.0),
            "color": tk.StringVar(value="#4aa3ff"),
            "x": tk.StringVar(value=""),
            "y": tk.StringVar(value=""),
        }
        team_var = self.ball_editor_vars["team"]
        if isinstance(team_var, tk.StringVar):
            team_var.trace_add("write", self._on_editor_team_changed)
        self.template_name_var = tk.StringVar(value="")
        self.ball_specs = self._default_ball_specs()
        self.settings_path = Path(__file__).resolve().with_name(SETTINGS_FILE_NAME)
        self._load_settings_from_disk(silent=True)

        self.status_var = tk.StringVar(value="")
        self._ring_effects: list[RingEffect] = []
        self._floating_text_effects: list[FloatingTextEffect] = []
        self._death_particles: list[DeathParticleEffect] = []
        self._prev_hp_by_body_id: dict[int, float] = {}
        self._prev_alive_by_body_id: dict[int, bool] = {}
        self._hp_bar_anim_by_body_id: dict[int, HpBarAnimState] = {}
        self._death_fade_by_body_id: dict[int, DeathFadeState] = {}
        self._vanished_body_ids: set[int] = set()
        self.world = self._create_world()
        self._reset_combat_vfx_state()
        self.battle_over = False
        self.battle_report_text = ""
        self._build_ui()
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=8)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=1)
        container.rowconfigure(1, weight=0)

        self.canvas = tk.Canvas(
            container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#0f141c",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

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
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(controls, text="Simulation", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        row += 1
        ttk.Button(controls, text="Save Settings", command=self.save_settings).grid(
            row=row, column=0, sticky="ew", pady=2
        )
        ttk.Button(controls, text="Load Settings", command=self.load_settings).grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=2
        )
        row += 1
        ttk.Button(controls, text="Run Battle Feel Report", command=self.run_battle_feel_report).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4)
        )
        row += 1
        ttk.Button(
            controls,
            text="Run Random Battle Report",
            command=self.run_random_battle_feel_report,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        row += 1

        ttk.Label(controls, text="Balls", font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(10, 6)
        )
        row += 1
        ball_list_frame = ttk.Frame(controls)
        ball_list_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        ball_list_frame.columnconfigure(0, weight=1)
        self.ball_tree = ttk.Treeview(
            ball_list_frame,
            columns=("idx", "team", "role", "hp", "max_hp", "power", "radius", "mass", "vx"),
            show="headings",
            height=8,
        )
        self.ball_tree.heading("idx", text="#")
        self.ball_tree.heading("team", text="Team")
        self.ball_tree.heading("role", text="Class")
        self.ball_tree.heading("hp", text="HP")
        self.ball_tree.heading("max_hp", text="Max")
        self.ball_tree.heading("power", text="Power")
        self.ball_tree.heading("radius", text="R")
        self.ball_tree.heading("mass", text="M")
        self.ball_tree.heading("vx", text="Vx")
        self.ball_tree.column("idx", width=34, anchor="center")
        self.ball_tree.column("team", width=50, anchor="center")
        self.ball_tree.column("role", width=98, anchor="center")
        self.ball_tree.column("hp", width=50, anchor="center")
        self.ball_tree.column("max_hp", width=50, anchor="center")
        self.ball_tree.column("power", width=54, anchor="center")
        self.ball_tree.column("radius", width=42, anchor="center")
        self.ball_tree.column("mass", width=42, anchor="center")
        self.ball_tree.column("vx", width=52, anchor="center")
        self.ball_tree.grid(row=0, column=0, sticky="ew")
        ball_scroll = ttk.Scrollbar(ball_list_frame, orient="vertical", command=self.ball_tree.yview)
        ball_scroll.grid(row=0, column=1, sticky="ns")
        self.ball_tree.configure(yscrollcommand=ball_scroll.set)
        self.ball_tree.bind("<<TreeviewSelect>>", self._on_ball_tree_select)
        self.ball_tree.bind("<Double-1>", self._on_ball_tree_double_click)
        row += 1
        ttk.Label(
            controls,
            text="Tip: double-click a cell in Balls list to edit directly.",
            justify="left",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        ttk.Button(controls, text="Add Ball", command=self.add_ball_from_editor).grid(
            row=row, column=0, sticky="ew", pady=(4, 2)
        )
        ttk.Button(controls, text="Update Selected", command=self.update_selected_ball).grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=(4, 2)
        )
        row += 1
        ttk.Button(controls, text="Duplicate", command=self.duplicate_selected_ball).grid(
            row=row, column=0, sticky="ew", pady=(0, 6)
        )
        ttk.Button(controls, text="Remove", command=self.remove_selected_ball).grid(
            row=row, column=1, sticky="ew", padx=(6, 0), pady=(0, 6)
        )
        row += 1

        editor = ttk.LabelFrame(controls, text="Ball Editor", padding=(8, 6))
        editor.grid(row=row, column=0, columnspan=2, sticky="ew")
        editor.columnconfigure(1, weight=1, minsize=96)
        editor.columnconfigure(3, weight=1)
        erow = 0

        ttk.Label(editor, text="Team").grid(row=erow, column=0, sticky="w", pady=2)
        ttk.Combobox(
            editor,
            values=("left", "right"),
            state="readonly",
            textvariable=self.ball_editor_vars["team"],
            width=8,
        ).grid(row=erow, column=1, sticky="ew", pady=2, padx=(0, 8))
        ttk.Label(editor, text="Class").grid(row=erow, column=2, sticky="w", pady=2)
        ttk.Combobox(
            editor,
            values=self._role_options(),
            state="readonly",
            textvariable=self.ball_editor_vars["role"],
            width=14,
        ).grid(row=erow, column=3, sticky="ew", pady=2)
        erow += 1
        ttk.Label(editor, text="Color").grid(row=erow, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.ball_editor_vars["color"], width=10).grid(
            row=erow, column=1, sticky="ew", pady=2, padx=(0, 8)
        )
        ttk.Label(editor, text="Preset").grid(row=erow, column=2, sticky="w", pady=2)
        ttk.Label(editor, text="Class quick apply").grid(row=erow, column=3, sticky="w", pady=2)
        erow += 1
        preset_row = ttk.Frame(editor)
        preset_row.grid(row=erow, column=0, columnspan=4, sticky="ew", pady=(0, 4))
        for col in range(3):
            preset_row.columnconfigure(col, weight=1)
        preset_names = ("tank", "dealer", "healer", "ranged_dealer", "ranged_healer")
        for idx, p in enumerate(preset_names):
            ttk.Button(
                preset_row,
                text=p,
                command=lambda name=p: self.apply_class_preset(name),
            ).grid(
                row=(idx // 3),
                column=(idx % 3),
                sticky="ew",
                padx=(0, 4),
                pady=2,
            )
        erow += 1

        for left_key, left_label, right_key, right_label in [
            ("radius", "Radius", "mass", "Mass"),
            ("power", "Power", "hp", "HP"),
            ("max_hp", "Max HP", "vx", "Vx"),
            ("vy", "Vy", "forward_dir", "Forward"),
            ("x", "X (opt)", "y", "Y (opt)"),
        ]:
            ttk.Label(editor, text=left_label).grid(row=erow, column=0, sticky="w", pady=2)
            ttk.Entry(editor, textvariable=self.ball_editor_vars[left_key], width=10).grid(
                row=erow, column=1, sticky="ew", pady=2, padx=(0, 8)
            )
            ttk.Label(editor, text=right_label).grid(row=erow, column=2, sticky="w", pady=2)
            ttk.Entry(editor, textvariable=self.ball_editor_vars[right_key], width=10).grid(
                row=erow, column=3, sticky="ew", pady=2
            )
            erow += 1
        row += 1

        templates = ttk.LabelFrame(controls, text="Templates", padding=(8, 6))
        templates.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        templates.columnconfigure(1, weight=1)
        ttk.Label(templates, text="Name").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(templates, textvariable=self.template_name_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )
        self.template_listbox = tk.Listbox(templates, height=5, exportselection=False)
        self.template_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 6))
        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_selected)
        ttk.Button(templates, text="Save Template", command=self.save_ball_template).grid(
            row=2, column=0, sticky="ew", pady=2
        )
        ttk.Button(templates, text="Delete Template", command=self.delete_ball_template).grid(
            row=2, column=1, sticky="ew", pady=2, padx=(6, 0)
        )
        ttk.Button(templates, text="Apply to Selected Ball", command=self.apply_template_to_selected).grid(
            row=3, column=0, sticky="ew", pady=2
        )
        ttk.Button(templates, text="Apply to All Balls", command=self.apply_template_to_all).grid(
            row=3, column=1, sticky="ew", pady=2, padx=(6, 0)
        )
        row += 1

        ttk.Button(controls, text="Apply Physics Only", command=self.apply_no_respawn).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 4)
        )
        row += 1
        ttk.Button(controls, text="Respawn Balls", command=self.apply_and_respawn).grid(
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

        self.keys_label = ttk.Label(
            controls,
            text="Keys: Space pause, R/Enter respawn, K kick, B report, N random report",
            wraplength=self.controls_wraplength,
            justify="left",
        )
        self.keys_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 6))
        row += 1
        self.status_label = ttk.Label(
            controls,
            textvariable=self.status_var,
            wraplength=self.controls_wraplength,
            justify="left",
        )
        self.status_label.grid(row=row, column=0, columnspan=2, sticky="w")

        env_outer = ttk.LabelFrame(container, text="Environment / Physics", padding=(10, 8))
        env_outer.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self._build_environment_panel(env_outer)

        self._refresh_ball_tree()
        self._refresh_template_list()

    def _build_environment_panel(self, parent: ttk.LabelFrame) -> None:
        """물리 설정을 카테고리별 탭으로 구성"""
        # 상단에 Side Margin 표시
        top_frame = ttk.Frame(parent)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 8))
        ttk.Label(top_frame, text="Side Margin").grid(row=0, column=0, sticky="w", padx=(0, 6))
        margin_entry = ttk.Entry(top_frame, textvariable=self.vars["side_margin"], width=10)
        margin_entry.grid(row=0, column=1, sticky="w")
        self.value_widgets["side_margin"] = margin_entry
        self._bind_field_help(margin_entry, "side_margin")
        self._apply_widget_lock_state("side_margin")

        # 카테고리별 탭 생성
        notebook = ttk.Notebook(parent)
        notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # 카테고리별 필드 정의
        categories = {
            "기본 물리": [
                ("gravity", "중력 (Gravity)"),
                ("approach_force", "접근력 (Approach Force)"),
            ],
            "충돌 반발": [
                ("restitution", "반발력 (Restitution)"),
                ("wall_restitution", "벽 반발력 (Wall Restitution)"),
                ("collision_boost", "충돌 부스트 (Collision Boost)"),
            ],
            "마찰": [
                ("linear_damping", "선형 감쇠 (Linear Damping)"),
                ("friction", "충돌 마찰 (Collision Friction)"),
                ("wall_friction", "벽 마찰 (Wall Friction)"),
                ("ground_friction", "지면 마찰 (Ground Friction)"),
            ],
            "충돌 해결": [
                ("solver_passes", "해결 패스 (Solver Passes)"),
                ("position_correction", "위치 보정 (Position Correction)"),
                ("ground_snap_speed", "지면 스냅 속도 (Ground Snap Speed)"),
            ],
            "충돌 강도": [
                ("mass_power_impact_scale", "질량·파워 스케일"),
                ("power_ratio_exponent", "파워 비율 지수"),
                ("impact_speed_cap", "임팩트 속도 상한"),
            ],
            "밀려남 효과": [
                ("min_recoil_speed", "최소 밀려남 속도"),
                ("recoil_scale", "밀려남 스케일"),
            ],
            "튕겨올림": [
                ("min_launch_speed", "최소 런치 속도"),
                ("launch_scale", "런치 스케일"),
                ("launch_height_scale", "런치 높이 배율"),
                ("max_launch_speed", "최대 런치 속도"),
            ],
            "데미지": [
                ("damage_base", "기본 데미지"),
                ("damage_scale", "데미지 스케일"),
            ],
            "경직": [
                ("stagger_base", "기본 경직 시간"),
                ("stagger_scale", "경직 스케일"),
                ("max_stagger", "최대 경직"),
                ("stagger_drive_multiplier", "경직 중 이동 배율"),
            ],
        }

        # 각 카테고리별 탭 생성
        for category_name, fields in categories.items():
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=category_name)

            # 2열 레이아웃으로 필드 배치
            tab.columnconfigure(1, weight=1)
            tab.columnconfigure(3, weight=1)

            for idx, (key, label) in enumerate(fields):
                row = idx // 2
                col = (idx % 2) * 2

                label_widget = ttk.Label(tab, text=label)
                label_widget.grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)

                entry_widget = ttk.Entry(tab, textvariable=self.vars[key], width=12)
                entry_widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 20), pady=4)

                self.value_widgets[key] = entry_widget
                self._bind_field_help(label_widget, key)
                self._bind_field_help(entry_widget, key)
                self._apply_widget_lock_state(key)

    def _default_ball_specs(self) -> list[dict[str, object]]:
        default_balls: list[dict[str, object]] = []
        raw = CUSTOM_BALLS_TEMPLATE.get("balls", [])
        if isinstance(raw, list):
            for idx, item in enumerate(raw):
                if isinstance(item, dict):
                    default_balls.append(self._normalize_ball_spec(item, idx))
        return default_balls

    def _team_default_color(self, team: str) -> str:
        if team == "left":
            return "#4aa3ff"
        if team == "right":
            return "#f26b5e"
        return "#dce6f2"

    def _normalize_team(self, raw: object, *, fallback: str = "left") -> str:
        team = str(raw).strip().lower()
        if team in {"left", "player", "ally", "blue", "l"}:
            return "left"
        if team in {"right", "monster", "enemy", "red", "r"}:
            return "right"
        return fallback

    def _on_editor_team_changed(self, *_: object) -> None:
        if self._loading_editor_spec or self._syncing_editor_team:
            return

        self._syncing_editor_team = True
        try:
            team_var = self.ball_editor_vars["team"]
            team = self._normalize_team(team_var.get(), fallback="left")
            team_var.set(team)

            own_default = self._team_default_color(team)
            opposite = "right" if team == "left" else "left"
            opposite_default = self._team_default_color(opposite)
            color_var = self.ball_editor_vars["color"]
            color_text = str(color_var.get()).strip().lower()
            if color_text == "" or color_text == opposite_default.lower():
                color_var.set(own_default)

            vx_var = self.ball_editor_vars["vx"]
            try:
                vx_mag = abs(float(vx_var.get()))
            except (TypeError, ValueError, tk.TclError):
                vx_mag = 0.0
            vx_var.set(vx_mag if team == "left" else -vx_mag)

            forward_var = self.ball_editor_vars["forward_dir"]
            try:
                forward_mag = abs(float(forward_var.get()))
            except (TypeError, ValueError, tk.TclError):
                forward_mag = 1.0
            if forward_mag <= 1e-6:
                forward_mag = 1.0
            forward_var.set(forward_mag if team == "left" else -forward_mag)
        finally:
            self._syncing_editor_team = False

    def _role_options(self) -> tuple[str, ...]:
        return ("tank", "dealer", "healer", "ranged_dealer", "ranged_healer")

    def _normalize_role(self, raw: object) -> str:
        role = str(raw).strip().lower()
        if role not in self._role_options():
            return "dealer"
        return role

    def _class_preset_payload(self, preset: str) -> dict[str, object] | None:
        """Ball 클래스 프리셋 가져오기 (default_ball_classes 사용)"""
        # default_ball_classes()에서 정의된 클래스 사용
        ball_classes = default_ball_classes()
        class_map = {ball_class.role: ball_class for ball_class in ball_classes}

        # ranged_healer는 별도 정의 (기본 클래스에 없음)
        if preset == "ranged_healer":
            return {
                "role": "ranged_healer",
                "radius": 26.0,
                "mass": 0.9,
                "power": 1.05,
                "hp": 120.0,
                "max_hp": 120.0,
                "vx": 220.0,
            }

        ball_class = class_map.get(preset)
        if ball_class is None:
            return None

        return {
            "role": ball_class.role,
            "radius": ball_class.base_radius,
            "mass": ball_class.base_mass,
            "power": ball_class.base_power,
            "hp": ball_class.base_hp,
            "max_hp": ball_class.base_hp,
            "vx": ball_class.base_speed,
        }

    def apply_class_preset(self, preset: str) -> None:
        payload = self._class_preset_payload(preset)
        if payload is None:
            return
        for key, value in payload.items():
            if key in self.ball_editor_vars:
                self.ball_editor_vars[key].set(value)
        team = self._normalize_team(self.ball_editor_vars["team"].get(), fallback="left")
        if team == "right":
            vx = abs(float(self.ball_editor_vars["vx"].get()))
            self.ball_editor_vars["vx"].set(-vx)
            self.ball_editor_vars["forward_dir"].set(-1.0)
        else:
            vx = abs(float(self.ball_editor_vars["vx"].get()))
            self.ball_editor_vars["vx"].set(vx)
            self.ball_editor_vars["forward_dir"].set(1.0)

    def _optional_float(self, value: object) -> float | None:
        if value is None:
            return None
        text = str(value).strip()
        if text == "":
            return None
        return float(text)

    def _normalize_ball_spec(self, raw: dict[str, object], idx: int) -> dict[str, object]:
        team = self._normalize_team(
            raw.get("team", "left"),
            fallback=("left" if (idx % 2) == 0 else "right"),
        )
        role = self._normalize_role(raw.get("role", "dealer"))
        radius = float(raw.get("radius", 32.0))
        mass = float(raw.get("mass", 1.0))
        power = float(raw.get("power", 1.0))
        hp = float(raw.get("hp", 100.0))
        max_hp = float(raw.get("max_hp", hp))
        if radius <= 0:
            raise ValueError(f"`balls[{idx}].radius` must be > 0.")
        if mass <= 0:
            raise ValueError(f"`balls[{idx}].mass` must be > 0.")
        if power <= 0:
            raise ValueError(f"`balls[{idx}].power` must be > 0.")
        if max_hp <= 0:
            raise ValueError(f"`balls[{idx}].max_hp` must be > 0.")
        if hp < 0:
            raise ValueError(f"`balls[{idx}].hp` must be >= 0.")
        hp = min(hp, max_hp)
        if "vx" in raw:
            vx = float(raw.get("vx", 0.0))
        elif team == "left":
            vx = abs(float(self.vars["left_speed"].get()))
        elif team == "right":
            vx = -abs(float(self.vars["right_speed"].get()))
        else:
            vx = 0.0
        if team == "left":
            vx = abs(vx)
        elif team == "right":
            vx = -abs(vx)
        vy = float(raw.get("vy", 0.0))
        forward_mag = abs(float(raw.get("forward_dir", 1.0)))
        if forward_mag <= 1e-6:
            forward_mag = 1.0
        forward_dir = forward_mag if team == "left" else -forward_mag
        color = str(raw.get("color", self._team_default_color(team))).strip()
        if not color:
            color = self._team_default_color(team)
        left_default = self._team_default_color("left").lower()
        right_default = self._team_default_color("right").lower()
        color_lower = color.lower()
        if team == "left" and color_lower == right_default:
            color = self._team_default_color("left")
        elif team == "right" and color_lower == left_default:
            color = self._team_default_color("right")
        x = self._optional_float(raw.get("x"))
        y = self._optional_float(raw.get("y"))
        return {
            "team": team,
            "role": role,
            "radius": radius,
            "mass": mass,
            "power": power,
            "hp": hp,
            "max_hp": max_hp,
            "vx": vx,
            "vy": vy,
            "forward_dir": forward_dir,
            "color": color,
            "x": x,
            "y": y,
        }

    def _selected_ball_index(self) -> int | None:
        if self.ball_tree is None:
            return None
        selected = self.ball_tree.selection()
        if not selected:
            return None
        try:
            return int(selected[0])
        except ValueError:
            return None

    def _refresh_ball_tree(self, *, select_index: int | None = None) -> None:
        if self.ball_tree is None:
            return
        self._destroy_ball_tree_editor()
        if select_index is None:
            select_index = self._selected_ball_index()

        for item in self.ball_tree.get_children():
            self.ball_tree.delete(item)

        for idx, spec in enumerate(self.ball_specs):
            hp = float(spec["hp"])
            max_hp = float(spec["max_hp"])
            self.ball_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    idx + 1,
                    str(spec["team"]),
                    str(spec.get("role", "dealer")),
                    f"{hp:.0f}",
                    f"{max_hp:.0f}",
                    f"{float(spec['power']):.2f}",
                    f"{float(spec['radius']):.0f}",
                    f"{float(spec['mass']):.1f}",
                    f"{float(spec['vx']):.0f}",
                ),
            )

        if not self.ball_specs:
            return
        if select_index is None:
            select_index = 0
        select_index = min(max(0, select_index), len(self.ball_specs) - 1)
        self.ball_tree.selection_set(str(select_index))
        self.ball_tree.focus(str(select_index))
        self._load_editor_from_spec(self.ball_specs[select_index])

    def _on_ball_tree_select(self, _: tk.Event) -> None:
        idx = self._selected_ball_index()
        if idx is None or idx >= len(self.ball_specs):
            return
        self._load_editor_from_spec(self.ball_specs[idx])

    def _destroy_ball_tree_editor(self) -> None:
        if self.ball_tree_editor is not None:
            self.ball_tree_editor.destroy()
            self.ball_tree_editor = None
        self.ball_tree_editor_item = None
        self.ball_tree_editor_column = None

    def _on_ball_tree_double_click(self, event: tk.Event) -> None:
        if self.ball_tree is None:
            return
        item = self.ball_tree.identify_row(event.y)
        column = self.ball_tree.identify_column(event.x)
        if not item or not column:
            return
        if column == "#1":
            return
        idx = int(item)
        if idx < 0 or idx >= len(self.ball_specs):
            return

        bbox = self.ball_tree.bbox(item, column)
        if not bbox:
            return
        x, y, width, height = bbox
        values = self.ball_tree.item(item, "values")
        col_index = int(column[1:]) - 1
        if col_index < 0 or col_index >= len(values):
            return
        current_text = str(values[col_index])

        self._destroy_ball_tree_editor()
        if column == "#2":
            editor = ttk.Combobox(
                self.ball_tree,
                values=("left", "right"),
                state="readonly",
            )
            editor.set(current_text)
        elif column == "#3":
            editor = ttk.Combobox(
                self.ball_tree,
                values=self._role_options(),
                state="readonly",
            )
            editor.set(current_text)
        else:
            editor = ttk.Entry(self.ball_tree)
            editor.insert(0, current_text)
            editor.selection_range(0, "end")

        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()
        editor.bind("<Return>", lambda _: self._commit_ball_tree_edit())
        editor.bind("<Escape>", lambda _: self._destroy_ball_tree_editor())
        editor.bind("<FocusOut>", lambda _: self._commit_ball_tree_edit())
        self.ball_tree_editor = editor
        self.ball_tree_editor_item = item
        self.ball_tree_editor_column = column

    def _commit_ball_tree_edit(self) -> None:
        if (
            self.ball_tree is None
            or self.ball_tree_editor is None
            or self.ball_tree_editor_item is None
            or self.ball_tree_editor_column is None
        ):
            return

        item = self.ball_tree_editor_item
        column = self.ball_tree_editor_column
        idx = int(item)
        if idx < 0 or idx >= len(self.ball_specs):
            self._destroy_ball_tree_editor()
            return

        if isinstance(self.ball_tree_editor, ttk.Combobox):
            raw_value = self.ball_tree_editor.get().strip().lower()
        elif isinstance(self.ball_tree_editor, ttk.Entry):
            raw_value = self.ball_tree_editor.get().strip()
        else:
            self._destroy_ball_tree_editor()
            return

        updated = dict(self.ball_specs[idx])
        try:
            if column == "#2":
                if raw_value not in ("left", "right"):
                    raise ValueError("Team must be left or right.")
                updated["team"] = raw_value
                if str(updated.get("color", "")).strip() == "":
                    updated["color"] = self._team_default_color(raw_value)
            elif column == "#3":
                updated["role"] = self._normalize_role(raw_value)
            elif column == "#4":
                updated["hp"] = float(raw_value)
            elif column == "#5":
                updated["max_hp"] = float(raw_value)
            elif column == "#6":
                updated["power"] = float(raw_value)
            elif column == "#7":
                updated["radius"] = float(raw_value)
            elif column == "#8":
                updated["mass"] = float(raw_value)
            elif column == "#9":
                updated["vx"] = float(raw_value)
            else:
                self._destroy_ball_tree_editor()
                return

            normalized = self._normalize_ball_spec(updated, idx)
        except (TypeError, ValueError) as exc:
            self._destroy_ball_tree_editor()
            messagebox.showerror("Ball List Edit Error", str(exc))
            return

        self.ball_specs[idx] = normalized
        self._destroy_ball_tree_editor()
        self._refresh_ball_tree(select_index=idx)
        self.status_message = f"Updated ball #{idx + 1} from list."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def _load_editor_from_spec(self, spec: dict[str, object]) -> None:
        self._loading_editor_spec = True
        try:
            self.ball_editor_vars["team"].set(str(spec["team"]))
            self.ball_editor_vars["role"].set(self._normalize_role(spec.get("role", "dealer")))
            self.ball_editor_vars["radius"].set(float(spec["radius"]))
            self.ball_editor_vars["mass"].set(float(spec["mass"]))
            self.ball_editor_vars["power"].set(float(spec["power"]))
            self.ball_editor_vars["hp"].set(float(spec["hp"]))
            self.ball_editor_vars["max_hp"].set(float(spec["max_hp"]))
            self.ball_editor_vars["vx"].set(float(spec["vx"]))
            self.ball_editor_vars["vy"].set(float(spec["vy"]))
            self.ball_editor_vars["forward_dir"].set(float(spec["forward_dir"]))
            self.ball_editor_vars["color"].set(str(spec["color"]))
            x = spec.get("x")
            y = spec.get("y")
            self.ball_editor_vars["x"].set("" if x is None else f"{float(x):.1f}")
            self.ball_editor_vars["y"].set("" if y is None else f"{float(y):.1f}")
        finally:
            self._loading_editor_spec = False

    def _ball_spec_from_editor(self) -> dict[str, object]:
        raw: dict[str, object] = {
            "team": str(self.ball_editor_vars["team"].get()),
            "role": str(self.ball_editor_vars["role"].get()),
            "radius": self.ball_editor_vars["radius"].get(),
            "mass": self.ball_editor_vars["mass"].get(),
            "power": self.ball_editor_vars["power"].get(),
            "hp": self.ball_editor_vars["hp"].get(),
            "max_hp": self.ball_editor_vars["max_hp"].get(),
            "vx": self.ball_editor_vars["vx"].get(),
            "vy": self.ball_editor_vars["vy"].get(),
            "forward_dir": self.ball_editor_vars["forward_dir"].get(),
            "color": str(self.ball_editor_vars["color"].get()),
            "x": str(self.ball_editor_vars["x"].get()).strip(),
            "y": str(self.ball_editor_vars["y"].get()).strip(),
        }
        try:
            return self._normalize_ball_spec(raw, 0)
        except (tk.TclError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid ball editor value: {exc}") from exc

    def add_ball_from_editor(self) -> None:
        try:
            spec = self._ball_spec_from_editor()
        except ValueError as exc:
            messagebox.showerror("Ball Editor Error", str(exc))
            return
        self.ball_specs.append(spec)
        self._refresh_ball_tree(select_index=len(self.ball_specs) - 1)
        self.status_message = f"Added ball #{len(self.ball_specs)}."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def update_selected_ball(self) -> None:
        idx = self._selected_ball_index()
        if idx is None or idx >= len(self.ball_specs):
            messagebox.showinfo("Select Ball", "Select a ball row to update.")
            return
        try:
            spec = self._ball_spec_from_editor()
        except ValueError as exc:
            messagebox.showerror("Ball Editor Error", str(exc))
            return
        self.ball_specs[idx] = spec
        self._refresh_ball_tree(select_index=idx)
        self.status_message = f"Updated ball #{idx + 1}."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def duplicate_selected_ball(self) -> None:
        idx = self._selected_ball_index()
        if idx is None or idx >= len(self.ball_specs):
            messagebox.showinfo("Select Ball", "Select a ball row to duplicate.")
            return
        clone = dict(self.ball_specs[idx])
        self.ball_specs.insert(idx + 1, clone)
        self._refresh_ball_tree(select_index=idx + 1)
        self.status_message = f"Duplicated ball #{idx + 1}."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def remove_selected_ball(self) -> None:
        idx = self._selected_ball_index()
        if idx is None or idx >= len(self.ball_specs):
            messagebox.showinfo("Select Ball", "Select a ball row to remove.")
            return
        if len(self.ball_specs) == 1:
            messagebox.showerror("Cannot Remove", "At least one ball is required.")
            return
        del self.ball_specs[idx]
        self._refresh_ball_tree(select_index=max(0, idx - 1))
        self.status_message = f"Removed ball #{idx + 1}."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def _template_fields(self) -> tuple[str, ...]:
        return (
            "role",
            "radius",
            "mass",
            "power",
            "hp",
            "max_hp",
            "vx",
            "vy",
            "forward_dir",
            "color",
        )

    def _template_from_editor(self) -> dict[str, object]:
        spec = self._ball_spec_from_editor()
        return {field: spec[field] for field in self._template_fields()}

    def _selected_template_name(self) -> str | None:
        if self.template_listbox is None:
            return None
        selected = self.template_listbox.curselection()
        if not selected:
            return None
        name = self.template_listbox.get(selected[0]).strip()
        return name or None

    def _refresh_template_list(self, *, select_name: str | None = None) -> None:
        if self.template_listbox is None:
            return
        self.template_listbox.delete(0, "end")
        names = sorted(self.ball_templates.keys())
        for name in names:
            self.template_listbox.insert("end", name)
        if not names:
            return
        if select_name is None:
            select_name = names[0]
        if select_name in names:
            idx = names.index(select_name)
            self.template_listbox.selection_set(idx)
            self.template_listbox.activate(idx)
            self.template_name_var.set(select_name)

    def _on_template_selected(self, _: tk.Event) -> None:
        name = self._selected_template_name()
        if name is None:
            return
        self.template_name_var.set(name)
        payload = self.ball_templates.get(name)
        if payload is None:
            return
        for key, value in payload.items():
            if key not in self.ball_editor_vars:
                continue
            self.ball_editor_vars[key].set(value)

    def save_ball_template(self) -> None:
        name = self.template_name_var.get().strip()
        if not name:
            messagebox.showerror("Template Name", "Template name is required.")
            return
        try:
            self.ball_templates[name] = self._template_from_editor()
        except ValueError as exc:
            messagebox.showerror("Template Error", str(exc))
            return
        self._refresh_template_list(select_name=name)
        self.status_message = f"Saved template '{name}'."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def delete_ball_template(self) -> None:
        name = self._selected_template_name() or self.template_name_var.get().strip()
        if not name:
            messagebox.showinfo("Template", "Select a template to delete.")
            return
        if name not in self.ball_templates:
            messagebox.showinfo("Template", f"Template '{name}' not found.")
            return
        del self.ball_templates[name]
        self._refresh_template_list()
        self.status_message = f"Deleted template '{name}'."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def apply_template_to_selected(self) -> None:
        template_name = self._selected_template_name()
        if template_name is None:
            messagebox.showinfo("Template", "Select a template first.")
            return
        idx = self._selected_ball_index()
        if idx is None or idx >= len(self.ball_specs):
            messagebox.showinfo("Select Ball", "Select a ball row to apply template.")
            return
        payload = self.ball_templates.get(template_name)
        if payload is None:
            messagebox.showerror("Template", f"Template '{template_name}' not found.")
            return
        updated = dict(self.ball_specs[idx])
        updated.update(payload)
        self.ball_specs[idx] = self._normalize_ball_spec(updated, idx)
        self._refresh_ball_tree(select_index=idx)
        self.status_message = f"Applied template '{template_name}' to ball #{idx + 1}."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def apply_template_to_all(self) -> None:
        template_name = self._selected_template_name()
        if template_name is None:
            messagebox.showinfo("Template", "Select a template first.")
            return
        payload = self.ball_templates.get(template_name)
        if payload is None:
            messagebox.showerror("Template", f"Template '{template_name}' not found.")
            return
        updated_specs: list[dict[str, object]] = []
        for idx, spec in enumerate(self.ball_specs):
            merged = dict(spec)
            merged.update(payload)
            updated_specs.append(self._normalize_ball_spec(merged, idx))
        self.ball_specs = updated_specs
        self._refresh_ball_tree(select_index=0)
        self.status_message = f"Applied template '{template_name}' to all balls."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

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

    def _get_custom_data_text(self) -> str:
        if self.custom_data_text_widget is not None:
            self.custom_data_text = self.custom_data_text_widget.get("1.0", "end-1c")
        return self.custom_data_text

    def _set_custom_data_text(self, text: str) -> None:
        self.custom_data_text = text
        if self.custom_data_text_widget is None:
            return
        self.custom_data_text_widget.delete("1.0", "end")
        self.custom_data_text_widget.insert("1.0", text)

    def _build_settings_payload(self) -> dict[str, object]:
        return {
            "version": SETTINGS_VERSION,
            "values": {key: self._get_var_value(key) for key in self.vars},
            "locks": {key: bool(lock_var.get()) for key, lock_var in self.lock_vars.items()},
            "ball_specs": self.ball_specs,
            "ball_templates": self.ball_templates,
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

        raw_ball_specs = payload.get("ball_specs")
        if isinstance(raw_ball_specs, list):
            normalized_specs: list[dict[str, object]] = []
            for idx, item in enumerate(raw_ball_specs):
                if not isinstance(item, dict):
                    continue
                try:
                    normalized_specs.append(self._normalize_ball_spec(item, idx))
                except (TypeError, ValueError):
                    continue
            if normalized_specs:
                self.ball_specs = normalized_specs

        raw_templates = payload.get("ball_templates")
        if isinstance(raw_templates, dict):
            normalized_templates: dict[str, dict[str, object]] = {}
            for name, item in raw_templates.items():
                template_name = str(name).strip()
                if not template_name or not isinstance(item, dict):
                    continue
                try:
                    normalized = self._normalize_ball_spec(item, 0)
                except (TypeError, ValueError):
                    continue
                normalized_templates[template_name] = {
                    field: normalized[field] for field in self._template_fields()
                }
            self.ball_templates = normalized_templates

        raw_custom_data = payload.get("custom_data_text")
        if isinstance(raw_custom_data, str) and raw_custom_data.strip():
            self._set_custom_data_text(raw_custom_data)

        self._refresh_ball_tree()
        self._refresh_template_list()

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
        self._reset_combat_vfx_state()
        self.battle_over = False
        self.battle_report_text = ""
        self.paused = False
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

    def _on_custom_text_mousewheel(self, event: tk.Event) -> str:
        if self.custom_data_text_widget is None:
            return "break"
        if event.delta == 0:
            return "break"
        self.custom_data_text_widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _on_custom_text_return(self, event: tk.Event) -> str:
        if self.custom_data_text_widget is None:
            return "break"
        self.custom_data_text_widget.insert("insert", "\n")
        return "break"

    def _bind_keys(self) -> None:
        self.root.bind("<space>", lambda _: self.toggle_pause())
        self.root.bind("<Return>", lambda _: self.apply_and_respawn())
        self.root.bind("r", lambda _: self.apply_and_respawn())
        self.root.bind("k", lambda _: self.random_kick())
        self.root.bind("b", lambda _: self.run_battle_feel_report())
        self.root.bind("n", lambda _: self.run_random_battle_feel_report())

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
        if not self.ball_specs:
            raise ValueError("At least one ball is required.")
        return self._create_world_from_custom_payload(
            {
                "balls": self.ball_specs,
                "invincible_teams": [],
            }
        )

    def _create_world_from_custom_payload(self, payload: object) -> PhysicsWorld:
        if not isinstance(payload, dict):
            raise ValueError("Custom JSON root must be an object.")

        balls_raw = payload.get("balls")
        if not isinstance(balls_raw, list) or len(balls_raw) == 0:
            raise ValueError("`balls` must be a non-empty array.")

        invincible_raw = payload.get("invincible_teams", [])
        invincible_teams: set[str] = set()
        if isinstance(invincible_raw, list):
            for team in invincible_raw:
                team_name = str(team).strip().lower()
                if team_name:
                    invincible_teams.add(team_name)

        side_margin = float(self.vars["side_margin"].get())
        left_speed = abs(float(self.vars["left_speed"].get()))
        right_speed = abs(float(self.vars["right_speed"].get()))
        team_slots: dict[str, int] = defaultdict(int)
        bodies: list[PhysicsBody] = []

        for idx, raw_ball in enumerate(balls_raw):
            if not isinstance(raw_ball, dict):
                raise ValueError(f"`balls[{idx}]` must be an object.")

            team = self._normalize_team(
                raw_ball.get("team", "left"),
                fallback=("left" if (idx % 2) == 0 else "right"),
            )
            role = self._normalize_role(raw_ball.get("role", "dealer"))

            radius = float(raw_ball.get("radius", 32.0))
            mass = float(raw_ball.get("mass", 1.0))
            power = float(raw_ball.get("power", 1.0))
            hp = float(raw_ball.get("hp", 100.0))
            max_hp = float(raw_ball.get("max_hp", hp))
            if radius <= 0:
                raise ValueError(f"`balls[{idx}].radius` must be > 0.")
            if mass <= 0:
                raise ValueError(f"`balls[{idx}].mass` must be > 0.")
            if power <= 0:
                raise ValueError(f"`balls[{idx}].power` must be > 0.")
            if max_hp <= 0:
                raise ValueError(f"`balls[{idx}].max_hp` must be > 0.")
            if hp < 0:
                raise ValueError(f"`balls[{idx}].hp` must be >= 0.")
            hp = min(hp, max_hp)

            default_forward = 1.0 if team == "left" else (-1.0 if team == "right" else 0.0)
            forward_dir = float(raw_ball.get("forward_dir", default_forward))
            if "vx" in raw_ball:
                vx = float(raw_ball["vx"])
            elif team == "left":
                vx = left_speed
            elif team == "right":
                vx = -right_speed
            else:
                vx = 0.0
            if team == "left":
                vx = abs(vx)
            elif team == "right":
                vx = -abs(vx)
            vy = float(raw_ball.get("vy", 0.0))

            forward_mag = abs(float(raw_ball.get("forward_dir", 1.0)))
            if forward_mag <= 1e-6:
                forward_mag = 1.0
            forward_dir = forward_mag if team == "left" else -forward_mag

            slot = team_slots[team]
            team_slots[team] += 1
            spacing = radius * 2.3
            x_raw = raw_ball.get("x")
            if x_raw is not None and str(x_raw).strip() != "":
                x = float(x_raw)
            elif team == "left":
                x = side_margin + radius + (slot * spacing)
            elif team == "right":
                x = self.canvas_width - side_margin - radius - (slot * spacing)
            else:
                x = (self.canvas_width * 0.5) + ((slot - 0.5) * spacing)

            y_raw = raw_ball.get("y")
            if y_raw is not None and str(y_raw).strip() != "":
                y = float(y_raw)
            else:
                y = self.canvas_height - radius

            x = min(self.canvas_width - radius, max(radius, x))
            y = min(self.canvas_height - radius, max(radius, y))
            if team == "left":
                default_color = "#4aa3ff"
            elif team == "right":
                default_color = "#f26b5e"
            else:
                default_color = "#dce6f2"
            color = str(raw_ball.get("color", default_color)).strip()
            if not color:
                color = default_color
            if team == "left" and color.lower() == "#f26b5e":
                color = "#4aa3ff"
            elif team == "right" and color.lower() == "#4aa3ff":
                color = "#f26b5e"

            bodies.append(
                PhysicsBody(
                    body_id=idx,
                    team=team,
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    radius=radius,
                    mass=mass,
                    color=color,
                    power=power,
                    role=role,
                    forward_dir=forward_dir,
                    max_hp=max_hp,
                    hp=hp,
                )
            )

        return PhysicsWorld(
            width=float(self.canvas_width),
            height=float(self.canvas_height),
            bodies=bodies,
            tuning=self._build_tuning(),
            invincible_teams=invincible_teams,
        )

    def fill_custom_data_example(self) -> None:
        self._set_custom_data_text(json.dumps(CUSTOM_BALLS_TEMPLATE, indent=2))
        self.status_message = "Filled custom JSON example."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def apply_custom_data_and_respawn(self) -> None:
        raw = self._get_custom_data_text().strip()
        if not raw:
            messagebox.showerror("Custom Data Error", "Custom JSON is empty.")
            return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror(
                "Custom Data Error",
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
            return

        try:
            self.world = self._create_world_from_custom_payload(payload)
        except (TypeError, ValueError) as exc:
            messagebox.showerror("Custom Data Error", str(exc))
            return

        self._reset_combat_vfx_state()
        self.battle_over = False
        self.battle_report_text = ""
        self.paused = False
        self.status_message = f"Applied custom JSON and respawned {len(self.world.bodies)} balls."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

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
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self.status_message = "Applied environment/physics settings without respawn."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def apply_and_respawn(self) -> None:
        try:
            self.world = self._create_world()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc))
            return
        self._reset_combat_vfx_state()
        self.battle_over = False
        self.battle_report_text = ""
        self.paused = False
        self.status_message = f"Respawned {len(self.ball_specs)} balls from Ball List."
        self._refresh_status()
        self._save_settings_to_disk(silent=True)

    def _timestamped_report_paths(self, report_dir: Path, prefix: str) -> tuple[Path, Path, Path]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return (
            report_dir / f"{prefix}_{stamp}.md",
            report_dir / f"{prefix}_{stamp}.json",
            report_dir / f"{prefix}_{stamp}.html",
        )

    def run_battle_feel_report(self) -> None:
        payload = self._build_settings_payload()
        report_dir = self.settings_path.resolve().parent / "reports"
        report_md_path, report_json_path, report_html_path = self._timestamped_report_paths(
            report_dir,
            "battle_feel_report",
        )

        try:
            self.root.config(cursor="watch")
            self.root.update_idletasks()
            result = run_profile_sweep_from_settings_payload(
                settings_payload=payload,
                settings_label=f"{self.settings_path.name} (lab-live)",
                seeds=6,
                duration=24.0,
                dt=self.fixed_dt,
                top_k=10,
                speed_jitter=12.0,
                width=float(self.canvas_width),
                height=float(self.canvas_height),
            )
        except ValueError as exc:
            messagebox.showerror("Battle Report Error", str(exc))
            return
        finally:
            self.root.config(cursor="")

        report_dir.mkdir(parents=True, exist_ok=True)
        report_md_path.write_text(sweep_result_to_markdown(result), encoding="utf-8")
        report_json_path.write_text(
            json.dumps(sweep_result_to_json_dict(result), indent=2),
            encoding="utf-8",
        )
        report_html_path.write_text(sweep_result_to_html(result), encoding="utf-8")

        best = result.top_scenarios[0] if result.top_scenarios else None
        if best is None:
            self.status_message = "Battle report completed. No scenarios were generated."
        else:
            self.status_message = (
                "Battle report done. "
                f"Best={best.scenario_name} score={best.score:.2f} "
                f"(coll/s={best.avg_collisions_per_second:.2f}, dmg/s={best.avg_damage_per_second:.2f})"
            )
        self._refresh_status()
        messagebox.showinfo(
            "Battle Report",
            f"Saved report files:\n- {report_md_path}\n- {report_json_path}\n- {report_html_path}",
        )

    def run_random_battle_feel_report(self) -> None:
        payload = self._build_settings_payload()
        report_dir = self.settings_path.resolve().parent / "reports"
        report_md_path, report_json_path, report_html_path = self._timestamped_report_paths(
            report_dir,
            "battle_feel_random_report",
        )

        try:
            self.root.config(cursor="watch")
            self.root.update_idletasks()
            result = run_random_profile_sweep_from_settings_payload(
                settings_payload=payload,
                settings_label=f"{self.settings_path.name} (lab-live-random)",
                scenario_count=80,
                profile_seed=2026,
                seeds=4,
                duration=24.0,
                dt=self.fixed_dt,
                top_k=12,
                speed_jitter=14.0,
                width=float(self.canvas_width),
                height=float(self.canvas_height),
            )
        except ValueError as exc:
            messagebox.showerror("Random Battle Report Error", str(exc))
            return
        finally:
            self.root.config(cursor="")

        report_dir.mkdir(parents=True, exist_ok=True)
        report_md_path.write_text(sweep_result_to_markdown(result), encoding="utf-8")
        report_json_path.write_text(
            json.dumps(sweep_result_to_json_dict(result), indent=2),
            encoding="utf-8",
        )
        report_html_path.write_text(sweep_result_to_html(result), encoding="utf-8")

        best = result.top_scenarios[0] if result.top_scenarios else None
        if best is None:
            self.status_message = "Random battle report completed. No scenarios were generated."
        else:
            self.status_message = (
                "Random battle report done. "
                f"Best={best.scenario_name} score={best.score:.2f} "
                f"(coll/s={best.avg_collisions_per_second:.2f}, dmg/s={best.avg_damage_per_second:.2f})"
            )
        self._refresh_status()
        messagebox.showinfo(
            "Random Battle Report",
            f"Saved report files:\n- {report_md_path}\n- {report_json_path}\n- {report_html_path}",
        )

    def _alive_bodies(self) -> list[PhysicsBody]:
        return [body for body in self.world.bodies if body.is_alive]

    def _reset_combat_vfx_state(self) -> None:
        self._ring_effects.clear()
        self._floating_text_effects.clear()
        self._death_particles.clear()
        self._prev_hp_by_body_id = {body.body_id: body.hp for body in self.world.bodies}
        self._prev_alive_by_body_id = {body.body_id: body.is_alive for body in self.world.bodies}
        self._hp_bar_anim_by_body_id = {}
        self._death_fade_by_body_id = {}
        self._vanished_body_ids.clear()
        for body in self.world.bodies:
            ratio = 0.0 if body.max_hp <= 0 else max(0.0, min(1.0, body.hp / body.max_hp))
            self._hp_bar_anim_by_body_id[body.body_id] = HpBarAnimState(
                display_ratio=ratio,
                chip_ratio=ratio,
            )

    def _collect_combat_vfx_events(self) -> None:
        active_ids: set[int] = set()
        for body in self.world.bodies:
            active_ids.add(body.body_id)
            prev_hp = self._prev_hp_by_body_id.get(body.body_id, body.hp)
            prev_alive = self._prev_alive_by_body_id.get(body.body_id, body.is_alive)
            heal_amount = body.hp - prev_hp
            damage_amount = max(0.0, body.last_damage)

            if prev_alive and not body.is_alive:
                self._spawn_death_vfx(body)
            if body.is_alive:
                self._vanished_body_ids.discard(body.body_id)
                if body.body_id in self._death_fade_by_body_id:
                    del self._death_fade_by_body_id[body.body_id]

            if damage_amount >= 0.05:
                self._spawn_damage_vfx(body, damage_amount)
                self._trigger_hp_bar_pulse(body.body_id, color="#ff8f7a", duration=0.22)
            if heal_amount >= 0.05:
                self._spawn_heal_vfx(body, heal_amount)
                self._trigger_hp_bar_pulse(body.body_id, color="#7cf2ad", duration=0.30)

            self._prev_hp_by_body_id[body.body_id] = body.hp
            self._prev_alive_by_body_id[body.body_id] = body.is_alive

        stale_ids = [body_id for body_id in self._prev_hp_by_body_id if body_id not in active_ids]
        for body_id in stale_ids:
            del self._prev_hp_by_body_id[body_id]
        stale_alive_ids = [body_id for body_id in self._prev_alive_by_body_id if body_id not in active_ids]
        for body_id in stale_alive_ids:
            del self._prev_alive_by_body_id[body_id]
        stale_fade_ids = [body_id for body_id in self._death_fade_by_body_id if body_id not in active_ids]
        for body_id in stale_fade_ids:
            del self._death_fade_by_body_id[body_id]
            self._vanished_body_ids.discard(body_id)

    def _spawn_damage_vfx(self, body: PhysicsBody, amount: float) -> None:
        text_offset = ((len(self._floating_text_effects) % 3) - 1) * 7.0
        self._ring_effects.append(
            RingEffect(
                x=body.x,
                y=body.y,
                start_radius=body.radius * 0.55,
                end_radius=body.radius * 1.65,
                color="#ff7c66",
                ttl=0.24,
                duration=0.24,
                width=3.0,
            )
        )
        text_value = f"-{amount:.0f}" if amount >= 10.0 else f"-{amount:.1f}"
        self._floating_text_effects.append(
            FloatingTextEffect(
                x=body.x + text_offset,
                y=body.y - body.radius - 12.0,
                text=text_value,
                color="#ffb3a6",
                ttl=0.55,
                duration=0.55,
                rise_speed=54.0,
                drift_speed=0.0,
                font_size=12,
            )
        )
        self._trim_combat_vfx_buffers()

    def _spawn_heal_vfx(self, body: PhysicsBody, amount: float) -> None:
        text_offset = ((len(self._floating_text_effects) % 3) - 1) * 7.0
        self._ring_effects.append(
            RingEffect(
                x=body.x,
                y=body.y,
                start_radius=body.radius * 0.70,
                end_radius=body.radius * 1.45,
                color="#52e68f",
                ttl=0.34,
                duration=0.34,
                width=2.5,
            )
        )
        text_value = f"+{amount:.0f}" if amount >= 10.0 else f"+{amount:.1f}"
        self._floating_text_effects.append(
            FloatingTextEffect(
                x=body.x + text_offset,
                y=body.y - body.radius - 12.0,
                text=text_value,
                color="#d2ffe1",
                ttl=0.70,
                duration=0.70,
                rise_speed=36.0,
                drift_speed=0.0,
                font_size=11,
            )
        )
        self._trim_combat_vfx_buffers()

    def _spawn_death_vfx(self, body: PhysicsBody) -> None:
        self._ring_effects.append(
            RingEffect(
                x=body.x,
                y=body.y,
                start_radius=body.radius * 0.65,
                end_radius=body.radius * 2.25,
                color="#ffd8ca",
                ttl=0.42,
                duration=0.42,
                width=3.2,
            )
        )
        self._ring_effects.append(
            RingEffect(
                x=body.x,
                y=body.y,
                start_radius=body.radius * 0.25,
                end_radius=body.radius * 1.35,
                color="#ff8e70",
                ttl=0.28,
                duration=0.28,
                width=2.4,
            )
        )
        self._floating_text_effects.append(
            FloatingTextEffect(
                x=body.x,
                y=body.y - body.radius - 10.0,
                text="OUT",
                color="#ffe1d7",
                ttl=0.52,
                duration=0.52,
                rise_speed=32.0,
                drift_speed=0.0,
                font_size=11,
            )
        )
        self._death_fade_by_body_id[body.body_id] = DeathFadeState(
            x=body.x,
            y=body.y,
            radius=body.radius,
            base_color=body.color,
            ttl=0.72,
            duration=0.72,
        )

        particle_count = 14
        for idx in range(particle_count):
            angle = (math.tau * idx) / particle_count
            speed = 82.0 + ((idx % 4) * 14.0)
            self._death_particles.append(
                DeathParticleEffect(
                    x=body.x,
                    y=body.y,
                    vx=math.cos(angle) * speed,
                    vy=(math.sin(angle) * speed) - 35.0,
                    radius=max(1.6, body.radius * (0.12 + (0.02 * (idx % 3)))),
                    color=body.color if idx % 2 == 0 else "#f2f5fa",
                    ttl=0.44 + (0.05 * (idx % 3)),
                    duration=0.44 + (0.05 * (idx % 3)),
                )
            )

        self._trim_combat_vfx_buffers()

    def _trim_combat_vfx_buffers(self) -> None:
        max_rings = 240
        max_texts = 180
        max_death_particles = 520
        if len(self._ring_effects) > max_rings:
            self._ring_effects = self._ring_effects[-max_rings:]
        if len(self._floating_text_effects) > max_texts:
            self._floating_text_effects = self._floating_text_effects[-max_texts:]
        if len(self._death_particles) > max_death_particles:
            self._death_particles = self._death_particles[-max_death_particles:]

    @staticmethod
    def _smooth_follow(current: float, target: float, speed: float, dt: float) -> float:
        if dt <= 0.0:
            return current
        alpha = max(0.0, min(1.0, speed * dt))
        return current + ((target - current) * alpha)

    def _ensure_hp_bar_anim_state(self, body: PhysicsBody) -> HpBarAnimState:
        state = self._hp_bar_anim_by_body_id.get(body.body_id)
        if state is not None:
            return state
        ratio = 0.0 if body.max_hp <= 0 else max(0.0, min(1.0, body.hp / body.max_hp))
        state = HpBarAnimState(display_ratio=ratio, chip_ratio=ratio)
        self._hp_bar_anim_by_body_id[body.body_id] = state
        return state

    def _trigger_hp_bar_pulse(self, body_id: int, *, color: str, duration: float) -> None:
        state = self._hp_bar_anim_by_body_id.get(body_id)
        if state is None:
            return
        if duration >= state.pulse_ttl:
            state.pulse_ttl = duration
            state.pulse_duration = duration
            state.pulse_color = color

    def _update_hp_bar_animation(self, dt: float) -> None:
        if dt <= 0.0:
            return

        active_ids: set[int] = set()
        for body in self.world.bodies:
            active_ids.add(body.body_id)
            state = self._ensure_hp_bar_anim_state(body)
            target = 0.0 if body.max_hp <= 0 else max(0.0, min(1.0, body.hp / body.max_hp))

            display_speed = 16.0 if target < state.display_ratio else 8.0
            chip_speed = 3.8 if target < state.chip_ratio else 11.0

            state.display_ratio = self._smooth_follow(
                state.display_ratio,
                target,
                speed=display_speed,
                dt=dt,
            )
            state.chip_ratio = self._smooth_follow(
                state.chip_ratio,
                target,
                speed=chip_speed,
                dt=dt,
            )
            state.display_ratio = max(0.0, min(1.0, state.display_ratio))
            state.chip_ratio = max(0.0, min(1.0, state.chip_ratio))

            if state.pulse_ttl > 0.0:
                state.pulse_ttl = max(0.0, state.pulse_ttl - dt)

        stale_ids = [body_id for body_id in self._hp_bar_anim_by_body_id if body_id not in active_ids]
        for body_id in stale_ids:
            del self._hp_bar_anim_by_body_id[body_id]

    def _update_combat_vfx(self, dt: float) -> None:
        if dt <= 0.0:
            return

        active_rings: list[RingEffect] = []
        for effect in self._ring_effects:
            effect.ttl = max(0.0, effect.ttl - dt)
            if effect.ttl > 0.0:
                active_rings.append(effect)
        self._ring_effects = active_rings

        active_texts: list[FloatingTextEffect] = []
        for effect in self._floating_text_effects:
            effect.ttl = max(0.0, effect.ttl - dt)
            effect.y -= effect.rise_speed * dt
            effect.x += effect.drift_speed * dt
            if effect.ttl > 0.0:
                active_texts.append(effect)
        self._floating_text_effects = active_texts

        active_particles: list[DeathParticleEffect] = []
        for effect in self._death_particles:
            effect.ttl = max(0.0, effect.ttl - dt)
            effect.x += effect.vx * dt
            effect.y += effect.vy * dt
            effect.vx *= max(0.0, 1.0 - (2.8 * dt))
            effect.vy = (effect.vy * max(0.0, 1.0 - (2.1 * dt))) + (130.0 * dt)
            if effect.ttl > 0.0:
                active_particles.append(effect)
        self._death_particles = active_particles

        finished_fade_ids: list[int] = []
        for body_id, effect in self._death_fade_by_body_id.items():
            effect.ttl = max(0.0, effect.ttl - dt)
            if effect.ttl <= 0.0:
                finished_fade_ids.append(body_id)
        for body_id in finished_fade_ids:
            del self._death_fade_by_body_id[body_id]
            self._vanished_body_ids.add(body_id)

    def _check_battle_end(self) -> None:
        if self.battle_over:
            return
        alive = self._alive_bodies()

        # 한쪽 팀이 전멸했는지 확인
        left_alive = sum(1 for body in self.world.bodies if body.team == "left" and body.is_alive)
        right_alive = sum(1 for body in self.world.bodies if body.team == "right" and body.is_alive)

        # 양쪽 팀이 모두 살아있으면 게임 계속
        if left_alive > 0 and right_alive > 0:
            return

        left_hp = sum(body.hp for body in self.world.bodies if body.team == "left")
        right_hp = sum(body.hp for body in self.world.bodies if body.team == "right")

        # 승자 결정
        if left_alive == 0 and right_alive == 0:
            winner_text = "🤝 무승부 (전멸)"
            winner_team = "무승부"
        elif left_alive > 0:
            winner_text = "🔵 LEFT 팀 승리!"
            winner_team = "LEFT"
        else:
            winner_text = "🔴 RIGHT 팀 승리!"
            winner_team = "RIGHT"

        # 전투 결과 텍스트
        self.battle_report_text = (
            f"{winner_text}\n"
            f"time={self.world.time_elapsed:.2f}s collisions={self.world.total_collisions}\n"
            f"L alive={left_alive} hp={left_hp:.1f} | R alive={right_alive} hp={right_hp:.1f}\n"
            "클릭하면 다시 시작"
        )
        self.battle_over = True
        self.paused = True
        self.status_message = "Battle finished. Click center overlay to respawn."
        self._refresh_status()

        # 팝업 표시
        result_message = (
            f"{winner_text}\n\n"
            f"⏱️ 경과 시간: {self.world.time_elapsed:.2f}초\n"
            f"💥 총 충돌: {self.world.total_collisions}회\n\n"
            f"🔵 LEFT 팀 - 생존: {left_alive}, HP: {left_hp:.1f}\n"
            f"🔴 RIGHT 팀 - 생존: {right_alive}, HP: {right_hp:.1f}"
        )
        messagebox.showinfo("⚔️ 전투 종료", result_message)

    def _on_canvas_click(self, event: tk.Event) -> None:
        if not self.battle_over:
            return
        center_x = self.canvas_width * 0.5
        center_y = self.canvas_height * 0.5
        if abs(event.x - center_x) <= 260 and abs(event.y - center_y) <= 110:
            self.apply_and_respawn()

    def random_kick(self) -> None:
        self.world.add_random_impulse(magnitude=460.0)
        self.status_message = "Applied random impulse."
        self._refresh_status()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.status_message = "Paused." if self.paused else "Running."
        self._refresh_status()

    def step_once(self) -> None:
        if self.battle_over:
            return
        self.world.step(self.fixed_dt)
        self._collect_combat_vfx_events()
        self._update_hp_bar_animation(self.fixed_dt)
        self._check_battle_end()
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

    def _power_emoticon(self, power: float) -> str:
        if power < 1.0:
            return ":-|"
        if power < 1.6:
            return ":-)"
        if power < 2.4:
            return ":-D"
        return ">:-D"

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

    @staticmethod
    def _blend_hex_color(start_hex: str, end_hex: str, t: float) -> str:
        blend = max(0.0, min(1.0, t))
        start = start_hex.lstrip("#")
        end = end_hex.lstrip("#")
        if len(start) != 6 or len(end) != 6:
            return start_hex
        sr = int(start[0:2], 16)
        sg = int(start[2:4], 16)
        sb = int(start[4:6], 16)
        er = int(end[0:2], 16)
        eg = int(end[2:4], 16)
        eb = int(end[4:6], 16)
        rr = int(sr + ((er - sr) * blend))
        rg = int(sg + ((eg - sg) * blend))
        rb = int(sb + ((eb - sb) * blend))
        return f"#{rr:02x}{rg:02x}{rb:02x}"

    def _draw_combat_vfx(self) -> None:
        fade_target = "#121923"
        for effect in self._death_particles:
            life = 0.0 if effect.duration <= 0 else max(0.0, min(1.0, effect.ttl / effect.duration))
            radius = max(0.7, effect.radius * life)
            fill = self._blend_hex_color(effect.color, fade_target, 1.0 - life)
            self.canvas.create_oval(
                effect.x - radius,
                effect.y - radius,
                effect.x + radius,
                effect.y + radius,
                fill=fill,
                outline="",
            )

        for effect in self._ring_effects:
            life = 0.0 if effect.duration <= 0 else max(0.0, min(1.0, effect.ttl / effect.duration))
            progress = 1.0 - life
            radius = effect.start_radius + ((effect.end_radius - effect.start_radius) * progress)
            outline = self._blend_hex_color(effect.color, fade_target, 1.0 - life)
            self.canvas.create_oval(
                effect.x - radius,
                effect.y - radius,
                effect.x + radius,
                effect.y + radius,
                outline=outline,
                width=max(1.0, effect.width * life),
            )

        for effect in self._floating_text_effects:
            life = 0.0 if effect.duration <= 0 else max(0.0, min(1.0, effect.ttl / effect.duration))
            text_color = self._blend_hex_color(effect.color, fade_target, 1.0 - life)
            self.canvas.create_text(
                effect.x,
                effect.y,
                text=effect.text,
                fill=text_color,
                font=("Consolas", max(8, effect.font_size), "bold"),
            )

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
            if not body.is_alive and body.body_id in self._vanished_body_ids:
                continue

            death_fade = self._death_fade_by_body_id.get(body.body_id)
            if body.is_alive:
                draw_x = body.x
                draw_y = body.y
                draw_r = body.radius
                draw_fill = body.color
                draw_outline = "#0a0a0a"
                draw_width = 2.0
                draw_velocity = True
            elif death_fade is not None and death_fade.duration > 0:
                fade_life = max(0.0, min(1.0, death_fade.ttl / death_fade.duration))
                draw_x = death_fade.x
                draw_y = death_fade.y
                draw_r = death_fade.radius * (0.28 + (0.72 * fade_life))
                draw_fill = self._blend_hex_color(death_fade.base_color, "#121923", 1.0 - fade_life)
                draw_outline = self._blend_hex_color("#f4f7fc", "#121923", 1.0 - fade_life)
                draw_width = max(1.0, 2.0 * fade_life)
                draw_velocity = False
            else:
                draw_x = body.x
                draw_y = body.y
                draw_r = body.radius
                draw_fill = "#777777"
                draw_outline = "#0a0a0a"
                draw_width = 1.6
                draw_velocity = False

            self.canvas.create_oval(
                draw_x - draw_r,
                draw_y - draw_r,
                draw_x + draw_r,
                draw_y + draw_r,
                fill=draw_fill,
                outline=draw_outline,
                width=draw_width,
            )
            if draw_velocity:
                self.canvas.create_line(
                    body.x,
                    body.y,
                    body.x - body.vx * 0.08,
                    body.y - body.vy * 0.08,
                    fill="#f6f7f9",
                    width=1,
                )

            if not body.is_alive:
                continue

            hp_anim = self._ensure_hp_bar_anim_state(body)
            display_ratio = hp_anim.display_ratio
            chip_ratio = hp_anim.chip_ratio
            bar_w = max(28.0, draw_r * 2.0)
            bar_h = 7.0
            bar_x0 = draw_x - (bar_w * 0.5)
            bar_y0 = draw_y - draw_r - 24
            self.canvas.create_rectangle(
                bar_x0,
                bar_y0,
                bar_x0 + bar_w,
                bar_y0 + bar_h,
                fill="#2b1f27",
                outline="#111820",
                width=1,
            )
            chip_x1 = bar_x0 + (bar_w * chip_ratio)
            display_x1 = bar_x0 + (bar_w * display_ratio)
            self.canvas.create_rectangle(
                bar_x0,
                bar_y0,
                chip_x1,
                bar_y0 + bar_h,
                fill="#7a3f47",
                outline="",
            )
            self.canvas.create_rectangle(
                bar_x0,
                bar_y0,
                display_x1,
                bar_y0 + bar_h,
                fill="#4ad06f",
                outline="",
            )
            if display_ratio > chip_ratio + 0.002:
                self.canvas.create_rectangle(
                    bar_x0 + (bar_w * chip_ratio),
                    bar_y0,
                    display_x1,
                    bar_y0 + bar_h,
                    fill="#7ef0b0",
                    outline="",
                )
            if hp_anim.pulse_ttl > 0.0 and hp_anim.pulse_duration > 0.0:
                pulse_life = max(0.0, min(1.0, hp_anim.pulse_ttl / hp_anim.pulse_duration))
                pulse_color = self._blend_hex_color(hp_anim.pulse_color, "#121923", 1.0 - pulse_life)
                pulse_expand = 1.0 + (2.5 * (1.0 - pulse_life))
                self.canvas.create_rectangle(
                    bar_x0 - pulse_expand,
                    bar_y0 - pulse_expand,
                    bar_x0 + bar_w + pulse_expand,
                    bar_y0 + bar_h + pulse_expand,
                    outline=pulse_color,
                    width=max(1.0, 1.8 * pulse_life),
                )

            self.canvas.create_text(
                draw_x,
                draw_y - draw_r - 14,
                text=f"HP {body.hp:.0f}/{body.max_hp:.0f}",
                fill="#dce6f2",
                font=("Consolas", 10),
            )

        # 발사체 그리기
        for projectile in self.world.projectiles:
            if not projectile.active:
                continue

            r = projectile.radius
            # 팀 색상 결정
            fill_color = "#4aa3ff" if projectile.owner_team == "left" else "#f26b5e"

            # 발사체 본체
            self.canvas.create_oval(
                projectile.x - r,
                projectile.y - r,
                projectile.x + r,
                projectile.y + r,
                fill=fill_color,
                outline="#ffffff",
                width=2,
            )

            # 발사체 궤적 (꼬리)
            tail_length = 15.0
            tail_x = projectile.x - (projectile.vx / abs(projectile.vx + 1e-9)) * tail_length if projectile.vx != 0 else projectile.x
            tail_y = projectile.y - (projectile.vy / abs(projectile.vy + 1e-9)) * tail_length if projectile.vy != 0 else projectile.y

            self.canvas.create_line(
                projectile.x,
                projectile.y,
                tail_x,
                tail_y,
                fill=fill_color,
                width=3,
                arrow=tk.FIRST,
            )

        self._draw_combat_vfx()

        self.canvas.create_text(
            14,
            14,
            anchor="nw",
            fill="#dce6f2",
            font=("Consolas", 11),
            text=(
                f"time {self.world.time_elapsed:6.2f}s   "
                f"max_speed {self.world.max_speed():7.2f}   "
                f"collisions {self.world.last_step_collisions:2d}   "
                f"projectiles {len(self.world.projectiles):2d}"
            ),
        )

        if self.battle_over:
            panel_w = 520
            panel_h = 180
            x0 = (self.canvas_width - panel_w) * 0.5
            y0 = (self.canvas_height - panel_h) * 0.5
            self.canvas.create_rectangle(
                x0,
                y0,
                x0 + panel_w,
                y0 + panel_h,
                fill="#0f1724",
                outline="#dce6f2",
                width=2,
            )
            self.canvas.create_text(
                self.canvas_width * 0.5,
                self.canvas_height * 0.5,
                text=self.battle_report_text,
                fill="#e6edf3",
                font=("Consolas", 14),
                justify="center",
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

        if not self.paused and not self.battle_over:
            self.accumulator += frame_dt
            while self.accumulator >= self.fixed_dt:
                self.world.step(self.fixed_dt)
                self._collect_combat_vfx_events()
                self.accumulator -= self.fixed_dt
                self._check_battle_end()
                if self.battle_over:
                    break

        self._update_hp_bar_animation(frame_dt)
        self._update_combat_vfx(frame_dt)
        self._draw_world()
        self._refresh_status()
        self.root.after(16, self._tick)


def main() -> None:
    root = tk.Tk()
    app = PhysicsLabApp(root)
    app.run()


if __name__ == "__main__":
    main()
