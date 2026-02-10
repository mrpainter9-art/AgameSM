from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from autochess_combat.battle_sim import (
    BallProfile,
    default_profiles,
    run_random_profile_sweep_from_settings_payload,
    run_profile_sweep_from_settings_payload,
    run_profile_sweep,
    sweep_result_to_html,
    sweep_result_to_json_dict,
    sweep_result_to_markdown,
)


def _write_settings(path: Path) -> None:
    payload = {
        "version": 1,
        "values": {
            "gravity": 900.0,
            "approach_force": 1150.0,
            "restitution": 0.68,
            "wall_restitution": 0.55,
            "linear_damping": 0.16,
            "friction": 0.2,
            "wall_friction": 0.08,
            "ground_friction": 0.3,
            "ground_snap_speed": 42.0,
            "collision_boost": 1.0,
            "solver_passes": 3,
            "position_correction": 0.8,
            "mass_power_impact_scale": 120.0,
            "power_ratio_exponent": 0.5,
            "impact_speed_cap": 1400.0,
            "min_recoil_speed": 45.0,
            "recoil_scale": 0.62,
            "min_launch_speed": 90.0,
            "launch_scale": 0.45,
            "launch_height_scale": 1.0,
            "max_launch_speed": 820.0,
            "damage_base": 1.5,
            "damage_scale": 0.028,
            "stagger_base": 0.06,
            "stagger_scale": 0.0012,
            "max_stagger": 1.2,
            "stagger_drive_multiplier": 0.0,
            "left_speed": 250.0,
            "right_speed": 220.0,
            "side_margin": 80.0,
        },
        "ball_specs": [
            {
                "team": "left",
                "radius": 28.0,
                "mass": 1.0,
                "power": 1.1,
                "hp": 110.0,
                "max_hp": 110.0,
                "vx": 250.0,
                "vy": 0.0,
                "forward_dir": 1.0,
                "color": "#4aa3ff",
                "x": None,
                "y": None,
            },
            {
                "team": "right",
                "radius": 30.0,
                "mass": 1.2,
                "power": 1.3,
                "hp": 120.0,
                "max_hp": 120.0,
                "vx": -220.0,
                "vy": 0.0,
                "forward_dir": -1.0,
                "color": "#f26b5e",
                "x": None,
                "y": None,
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class BattleSimTests(unittest.TestCase):
    def test_default_profiles_are_available(self) -> None:
        names = [profile.name for profile in default_profiles()]
        self.assertIn("balanced", names)
        self.assertIn("striker", names)
        self.assertIn("juggernaut", names)

    def test_run_profile_sweep_returns_ranked_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            _write_settings(settings_path)
            profiles = [
                BallProfile("balanced", 1.0, 1.0, 1.0, 1.0, 1.0),
                BallProfile("striker", 0.95, 0.88, 1.28, 0.88, 1.18),
            ]
            result = run_profile_sweep(
                settings_path=settings_path,
                profiles=profiles,
                seeds=2,
                duration=1.0,
                dt=0.02,
                top_k=3,
                speed_jitter=5.0,
                width=800.0,
                height=300.0,
            )

            self.assertEqual(4, result.scenario_count)
            self.assertEqual(3, len(result.top_scenarios))
            self.assertGreaterEqual(result.top_scenarios[0].score, result.top_scenarios[-1].score)

            md = sweep_result_to_markdown(result)
            self.assertIn("# 전투감 시뮬레이션 리포트", md)
            self.assertIn("## 상위 시나리오", md)
            html_report = sweep_result_to_html(result)
            self.assertIn("<!doctype html>", html_report.lower())
            self.assertIn("상위 시나리오", html_report)

            json_dict = sweep_result_to_json_dict(result)
            self.assertEqual(4, json_dict["scenario_count"])
            self.assertIn("recommendations", json_dict)

    def test_run_profile_sweep_from_payload_uses_lab_like_data(self) -> None:
        payload = {
            "version": 1,
            "values": {
                "gravity": 900.0,
                "approach_force": 1150.0,
                "restitution": 0.68,
                "wall_restitution": 0.55,
                "linear_damping": 0.16,
                "friction": 0.2,
                "wall_friction": 0.08,
                "ground_friction": 0.3,
                "ground_snap_speed": 42.0,
                "collision_boost": 1.0,
                "solver_passes": 3,
                "position_correction": 0.8,
                "mass_power_impact_scale": 120.0,
                "power_ratio_exponent": 0.5,
                "impact_speed_cap": 1400.0,
                "min_recoil_speed": 45.0,
                "recoil_scale": 0.62,
                "min_launch_speed": 90.0,
                "launch_scale": 0.45,
                "launch_height_scale": 1.0,
                "max_launch_speed": 820.0,
                "damage_base": 1.5,
                "damage_scale": 0.028,
                "stagger_base": 0.06,
                "stagger_scale": 0.0012,
                "max_stagger": 1.2,
                "stagger_drive_multiplier": 0.0,
                "left_speed": 250.0,
                "right_speed": 220.0,
                "side_margin": 80.0,
                "left_invincible": True,
                "right_invincible": True,
            },
            "ball_specs": [
                {
                    "team": "left",
                    "radius": 28.0,
                    "mass": 1.0,
                    "power": 1.1,
                    "hp": 110.0,
                    "max_hp": 110.0,
                    "vx": 250.0,
                    "vy": 0.0,
                    "forward_dir": 1.0,
                    "color": "#4aa3ff",
                    "x": None,
                    "y": None,
                },
                {
                    "team": "right",
                    "radius": 30.0,
                    "mass": 1.2,
                    "power": 1.3,
                    "hp": 120.0,
                    "max_hp": 120.0,
                    "vx": -220.0,
                    "vy": 0.0,
                    "forward_dir": -1.0,
                    "color": "#f26b5e",
                    "x": None,
                    "y": None,
                },
            ],
        }

        result = run_profile_sweep_from_settings_payload(
            settings_payload=payload,
            settings_label="lab-live",
            profiles=[BallProfile("balanced", 1.0, 1.0, 1.0, 1.0, 1.0)],
            seeds=1,
            duration=1.0,
            dt=0.02,
            top_k=1,
            speed_jitter=0.0,
            width=800.0,
            height=300.0,
        )

        self.assertEqual("lab-live", result.settings_path)
        self.assertTrue(
            all("invincible flags" not in message.lower() for message in result.recommendations)
        )

    def test_random_profile_sweep_from_payload(self) -> None:
        payload = {
            "version": 1,
            "values": {
                "gravity": 900.0,
                "approach_force": 1150.0,
                "restitution": 0.68,
                "wall_restitution": 0.55,
                "linear_damping": 0.16,
                "friction": 0.2,
                "wall_friction": 0.08,
                "ground_friction": 0.3,
                "ground_snap_speed": 42.0,
                "collision_boost": 1.0,
                "solver_passes": 3,
                "position_correction": 0.8,
                "mass_power_impact_scale": 120.0,
                "power_ratio_exponent": 0.5,
                "impact_speed_cap": 1400.0,
                "min_recoil_speed": 45.0,
                "recoil_scale": 0.62,
                "min_launch_speed": 90.0,
                "launch_scale": 0.45,
                "launch_height_scale": 1.0,
                "max_launch_speed": 820.0,
                "damage_base": 1.5,
                "damage_scale": 0.028,
                "stagger_base": 0.06,
                "stagger_scale": 0.0012,
                "max_stagger": 1.2,
                "stagger_drive_multiplier": 0.0,
                "left_speed": 250.0,
                "right_speed": 220.0,
                "side_margin": 80.0,
            },
            "ball_specs": [
                {
                    "team": "left",
                    "radius": 28.0,
                    "mass": 1.0,
                    "power": 1.1,
                    "hp": 110.0,
                    "max_hp": 110.0,
                    "vx": 250.0,
                    "vy": 0.0,
                    "forward_dir": 1.0,
                    "color": "#4aa3ff",
                    "x": None,
                    "y": None,
                },
                {
                    "team": "right",
                    "radius": 30.0,
                    "mass": 1.2,
                    "power": 1.3,
                    "hp": 120.0,
                    "max_hp": 120.0,
                    "vx": -220.0,
                    "vy": 0.0,
                    "forward_dir": -1.0,
                    "color": "#f26b5e",
                    "x": None,
                    "y": None,
                },
            ],
        }
        result = run_random_profile_sweep_from_settings_payload(
            settings_payload=payload,
            settings_label="lab-live-random",
            scenario_count=8,
            profile_seed=123,
            seeds=2,
            duration=1.0,
            dt=0.02,
            top_k=5,
            speed_jitter=3.0,
            width=800.0,
            height=300.0,
        )

        self.assertEqual("lab-live-random", result.settings_path)
        self.assertEqual(8, result.scenario_count)
        self.assertEqual(5, len(result.top_scenarios))


if __name__ == "__main__":
    unittest.main()
