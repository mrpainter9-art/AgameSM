from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from autochess_combat.battle_sim import (
    DEFAULT_SETTINGS_PATH,
    run_random_profile_sweep,
    run_profile_sweep,
    sweep_result_to_html,
    sweep_result_to_json_dict,
    sweep_result_to_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run headless combat simulations from current visual_physics_lab settings "
            "while keeping environment tuning fixed and sweeping ball-value profiles."
        )
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help="Path to visual physics settings JSON.",
    )
    parser.add_argument(
        "--mode",
        choices=("profiles", "random"),
        default="profiles",
        help="Sweep strategy: fixed profile grid or random profile generation.",
    )
    parser.add_argument("--seeds", type=int, default=6, help="Runs per scenario.")
    parser.add_argument("--duration", type=float, default=24.0, help="Seconds per run.")
    parser.add_argument("--dt", type=float, default=1.0 / 120.0, help="Fixed simulation timestep.")
    parser.add_argument("--top-k", type=int, default=10, help="Top scenario count in output.")
    parser.add_argument(
        "--random-scenarios",
        type=int,
        default=80,
        help="Scenario count when --mode random is used.",
    )
    parser.add_argument(
        "--profile-seed",
        type=int,
        default=2026,
        help="Random profile seed when --mode random is used.",
    )
    parser.add_argument(
        "--speed-jitter",
        type=float,
        default=12.0,
        help="Random speed jitter applied to each ball on spawn.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("reports") / "battle_feel_report",
        help="Output markdown report path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("reports") / "battle_feel_report",
        help="Output JSON summary path.",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=Path("reports") / "battle_feel_report",
        help="Output HTML visual report path.",
    )
    return parser.parse_args()


def _timestamped(path: Path, suffix: str, stamp: str) -> Path:
    stem = path.stem if path.suffix else path.name
    return path.parent / f"{stem}_{stamp}{suffix}"


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.mode == "profiles":
        result = run_profile_sweep(
            settings_path=args.settings,
            seeds=args.seeds,
            duration=args.duration,
            dt=args.dt,
            top_k=args.top_k,
            speed_jitter=args.speed_jitter,
        )
    else:
        result = run_random_profile_sweep(
            settings_path=args.settings,
            scenario_count=args.random_scenarios,
            profile_seed=args.profile_seed,
            seeds=args.seeds,
            duration=args.duration,
            dt=args.dt,
            top_k=args.top_k,
            speed_jitter=args.speed_jitter,
        )
    md_text = sweep_result_to_markdown(result)
    html_text = sweep_result_to_html(result)
    json_text = json.dumps(sweep_result_to_json_dict(result), indent=2)

    output_md = _timestamped(args.output_md, ".md", stamp)
    output_json = _timestamped(args.output_json, ".json", stamp)
    output_html = _timestamped(args.output_html, ".html", stamp)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md_text, encoding="utf-8")
    output_json.write_text(json_text, encoding="utf-8")
    output_html.write_text(html_text, encoding="utf-8")

    top = result.top_scenarios[0] if result.top_scenarios else None
    print(f"mode: {args.mode}")
    print(f"scenarios: {result.scenario_count}")
    print(f"report(md): {output_md}")
    print(f"report(json): {output_json}")
    print(f"report(html): {output_html}")
    if top is not None:
        print(
            "best: "
            f"{top.scenario_name} "
            f"(score={top.score:.2f}, collisions/s={top.avg_collisions_per_second:.2f}, "
            f"damage/s={top.avg_damage_per_second:.2f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
