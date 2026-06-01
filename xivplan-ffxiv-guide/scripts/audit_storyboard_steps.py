#!/usr/bin/env python3
"""Audit Phase F storyboard step coverage and metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "purpose",
    "guide_text",
    "checks",
    "visual_focus",
    "required_roles",
    "reset_state",
    "storyboard_phase",
    "teaching_question",
    "why_this_frame_exists",
    "changed_objects_only",
)
REQUIRED_PHASES = ("observation", "movement", "resolve", "reset")
V3_REQUIRED_COVERAGE = ("observation", "assignment", "movement", "resolve", "reset", "next_read")
PHASE_BUCKETS = {
    "observe": "observation",
    "observe_signal": "observation",
    "assign_roles": "assignment",
    "assignment": "assignment",
    "preposition": "assignment",
    "first_move": "movement",
    "second_move": "movement",
    "between_resolves": "movement",
    "move": "movement",
    "first_resolve": "resolve",
    "second_resolve": "resolve",
    "resolve": "resolve",
    "reset": "reset",
    "next_read_setup": "next_read",
}
ACTION_HINTS = ("移动", "散开", "分摊", "入塔", "拉线", "击退", "复位", "判定", "观察", "读取", "确认", "move", "resolve", "reset")


def read_scene(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_phase_f_scene(scene: dict[str, Any]) -> bool:
    metadata = scene.get("metadata")
    if not isinstance(metadata, dict):
        return False
    return metadata.get("source") == "build_spec_from_solution.py" or metadata.get("storyboard_generator") in {
        "phase-f-v2",
        "phase-l-semantic-long-flow",
        "phase-o-v3",
        "phase-o-teaching-long-flow",
    }


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def normalized_phase(step: dict[str, Any]) -> str:
    phase = step.get("storyboard_phase")
    if isinstance(phase, str) and phase:
        return PHASE_BUCKETS.get(phase, phase)
    text = " ".join(str(step.get(key, "")) for key in ("title", "purpose", "guide_text")).lower()
    if any(token in text for token in ("observe", "观察", "读取", "确认")):
        return "observation"
    if any(token in text for token in ("move", "移动", "路线", "入塔", "拉线", "击退")):
        return "movement"
    if any(token in text for token in ("resolve", "判定", "结算", "散开", "分摊", "塔")):
        return "resolve"
    if any(token in text for token in ("reset", "复位", "回中", "下一")):
        return "reset"
    return "unknown"


def raw_phase(step: dict[str, Any]) -> str:
    phase = step.get("storyboard_phase")
    return str(phase) if isinstance(phase, str) and phase else "unknown"


def teaching_question_count(value: Any) -> int:
    if isinstance(value, list):
        return len([item for item in value if has_value(item)])
    if not isinstance(value, str) or not value.strip():
        return 0
    text = value.strip()
    question_marks = text.count("?") + text.count("？")
    if question_marks > 1:
        return question_marks
    return 1


def action_hint_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for hint in ACTION_HINTS if hint in lowered)


def audit_step(step: dict[str, Any], step_index: int) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for field in REQUIRED_FIELDS:
        value = step.get(field)
        if field == "checks":
            if not isinstance(value, list) or not value:
                issues.append({"severity": "severe", "kind": "missing_or_empty_field", "field": field})
        elif field == "required_roles":
            if not isinstance(value, list) or not value:
                issues.append({"severity": "severe", "kind": "missing_or_empty_field", "field": field})
        elif not has_value(value):
            issues.append({"severity": "severe", "kind": "missing_or_empty_field", "field": field})

    question_count = teaching_question_count(step.get("teaching_question"))
    if question_count != 1:
        issues.append({"severity": "severe", "kind": "teaching_question_not_single", "field": "teaching_question", "count": question_count})

    guide_text = str(step.get("guide_text", ""))
    has_flow = any(
        isinstance(obj, dict) and obj.get("type") in {"arrow", "tether"}
        for obj in step.get("objects", [])
        if isinstance(step.get("objects"), list)
    )
    if action_hint_count(guide_text) >= 4 and not has_flow and raw_phase(step) not in {"observe_signal", "assign_roles"}:
        issues.append(
            {
                "severity": "review",
                "kind": "possibly_overloaded_guide_text",
                "field": "guide_text",
                "suggestion": "Split observation, assignment, movement, and resolution into adjacent frames.",
            }
        )

    return {
        "step": step_index,
        "title": step.get("title", f"Step {step_index}"),
        "phase": normalized_phase(step),
        "raw_phase": raw_phase(step),
        "issues": issues,
        "severe_items": sum(1 for issue in issues if issue["severity"] == "severe"),
    }


def audit_scene(path: Path, required: bool | None = None) -> dict[str, Any]:
    scene = read_scene(path)
    steps = scene.get("steps", [])
    if not isinstance(steps, list):
        raise ValueError("scene.steps must be a list")

    applicable = is_phase_f_scene(scene) if required is None else required
    if not applicable:
        return {
            "path": str(path),
            "applicable": False,
            "ok": True,
            "steps": len(steps),
            "phases": [],
            "severe_items": 0,
            "issues": [],
            "per_step": [],
        }

    per_step = [audit_step(step, index) for index, step in enumerate(steps, start=1) if isinstance(step, dict)]
    phases = sorted({item["phase"] for item in per_step})
    raw_phases = sorted({item["raw_phase"] for item in per_step})
    issues: list[dict[str, Any]] = []
    metadata = scene.get("metadata") if isinstance(scene.get("metadata"), dict) else {}
    generator = str(metadata.get("storyboard_generator", ""))
    if generator in {"phase-o-teaching-long-flow"}:
        min_steps, max_steps = 14, 20
    elif generator in {"phase-o-v3"}:
        min_steps, max_steps = 6, 16
    else:
        min_steps, max_steps = 6, 14
    if not min_steps <= len(per_step) <= max_steps:
        issues.append({"severity": "severe", "kind": "step_count_out_of_range", "steps": len(per_step), "expected": f"{min_steps}..{max_steps}"})
    required = V3_REQUIRED_COVERAGE if generator in {"phase-o-v3", "phase-o-teaching-long-flow"} else REQUIRED_PHASES
    coverage = set(phases)
    if "next_read" in coverage:
        coverage.add("reset")
    missing_phases = [phase for phase in required if phase not in coverage]
    if missing_phases:
        issues.append({"severity": "severe", "kind": "missing_storyboard_phases", "missing": missing_phases})

    severe = sum(item["severe_items"] for item in per_step) + sum(1 for issue in issues if issue["severity"] == "severe")
    return {
        "path": str(path),
        "applicable": True,
        "ok": severe == 0,
        "steps": len(per_step),
        "phases": phases,
        "raw_phases": raw_phases,
        "severe_items": severe,
        "issues": issues,
        "per_step": per_step,
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Storyboard Step Audit",
        "",
        "| Scene | Status | Applicable | Steps | Phases | Severe |",
        "|---|---|---:|---:|---|---:|",
    ]
    for result in results:
        lines.append(
            "| {scene} | {status} | {applicable} | {steps} | {phases} | {severe} |".format(
                scene=Path(result["path"]).name,
                status="PASS" if result["ok"] else "FAIL",
                applicable="yes" if result["applicable"] else "no",
                steps=result["steps"],
                phases=", ".join(result["phases"]) or "n/a",
                severe=result["severe_items"],
            )
        )
    lines.extend(["", "## Issues", ""])
    for result in results:
        for issue in result.get("issues", []):
            lines.append(f"- {Path(result['path']).name}: [{issue['severity']}] {issue['kind']} {json.dumps(issue, ensure_ascii=False)}")
        for step in result.get("per_step", []):
            for issue in step.get("issues", []):
                lines.append(
                    "- {scene} step {step}: [{severity}] {kind} field={field}".format(
                        scene=Path(result["path"]).name,
                        step=step["step"],
                        severity=issue["severity"],
                        kind=issue["kind"],
                        field=issue.get("field", ""),
                    )
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Phase F storyboard step metadata and coverage.")
    parser.add_argument("paths", type=Path, nargs="+", help="One or more .xivplan files")
    parser.add_argument("--required", action="store_true", help="Require storyboard checks even without Phase F metadata")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    parser.add_argument("--markdown-out", type=Path, help="Optional Markdown report path")
    args = parser.parse_args()

    try:
        required = True if args.required else None
        results = [audit_scene(path, required=required) for path in args.paths]
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(results), encoding="utf-8")

    for result in results:
        print(
            "{path}: {status} applicable={applicable} steps={steps} phases={phases} severe={severe}".format(
                path=result["path"],
                status="PASS" if result["ok"] else "FAIL",
                applicable="yes" if result["applicable"] else "no",
                steps=result["steps"],
                phases=",".join(result["phases"]) or "n/a",
                severe=result["severe_items"],
            )
        )
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
