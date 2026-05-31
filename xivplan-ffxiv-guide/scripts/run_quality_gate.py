#!/usr/bin/env python3
"""Run Phase 9 quality gates across generated Phase 8 guide cases."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from audit_visual_density import audit_scene
from audit_label_layout import audit_scene as audit_label_scene
from audit_flow_lines import audit_scene as audit_flow_scene
from audit_storyboard_steps import audit_scene as audit_storyboard_scene
from audit_visual_quality import audit_scene as audit_visual_quality_scene
from validate_guide_package import validate_package
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "artifacts" / "quality-gates"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_cases(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "scene.xivplan").exists() and (path / "guide-package").exists()
    )


def case_result(case_dir: Path) -> dict[str, Any]:
    scene_path = case_dir / "scene.xivplan"
    scene = read_json(scene_path)
    scene_errors, type_counts, object_count = validate_scene(scene)
    package_errors, package_stats = validate_package(case_dir)
    try:
        density = audit_scene(scene_path)
        density_errors = []
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        density = {"ok": False, "error": str(exc)}
        density_errors = [f"visual density audit failed: {exc}"]
    try:
        label_layout = audit_label_scene(scene_path)
        label_errors = [] if label_layout["ok"] else ["label layout audit found severe collisions"]
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        label_layout = {"ok": False, "error": str(exc)}
        label_errors = [f"label layout audit failed: {exc}"]
    try:
        flow_lines = audit_flow_scene(scene_path)
        flow_errors = [] if flow_lines["ok"] else ["flow line audit found severe issues"]
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        flow_lines = {"ok": False, "error": str(exc)}
        flow_errors = [f"flow line audit failed: {exc}"]
    try:
        storyboard = audit_storyboard_scene(scene_path)
        storyboard_errors = [] if storyboard["ok"] else ["storyboard audit found severe issues"]
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        storyboard = {"ok": False, "error": str(exc)}
        storyboard_errors = [f"storyboard audit failed: {exc}"]
    try:
        visual_quality = audit_visual_quality_scene(scene_path)
        visual_quality_errors = [] if visual_quality["ok"] else ["visual quality audit found severe issues"]
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        visual_quality = {"ok": False, "error": str(exc)}
        visual_quality_errors = [f"visual quality audit failed: {exc}"]

    errors = scene_errors + package_errors + density_errors + label_errors + flow_errors + storyboard_errors + visual_quality_errors
    return {
        "slug": case_dir.name,
        "ok": not errors,
        "errors": errors,
        "scene": {
            "path": str(scene_path),
            "steps": len(scene.get("steps", [])) if isinstance(scene, dict) else 0,
            "objects": object_count,
            "types": dict(sorted(type_counts.items())),
        },
        "package": package_stats,
        "density": density,
        "label_layout": label_layout,
        "flow_lines": flow_lines,
        "storyboard": storyboard,
        "visual_quality": visual_quality,
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts: Counter[str] = Counter()
    for result in results:
        type_counts.update(result.get("scene", {}).get("types", {}))
    return {
        "ok": all(result["ok"] for result in results),
        "cases": len(results),
        "passed": sum(1 for result in results if result["ok"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "types": dict(sorted(type_counts.items())),
    }


def render_markdown(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [
        "# Phase 9 Quality Gate Report",
        "",
        "## Summary",
        "",
        f"- status: {'PASS' if summary['ok'] else 'FAIL'}",
        f"- cases: {summary['cases']}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        "",
        "## Cases",
        "",
        "| Case | Status | Steps | Objects | Avg Objects / Step | Missing Layers | Label Severe | Flow Severe | Crossings | Storyboard | Visual Quality | Notes |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---|---|---|",
    ]
    for result in results:
        density = result.get("density", {})
        label_layout = result.get("label_layout", {})
        flow_lines = result.get("flow_lines", {})
        storyboard = result.get("storyboard", {})
        visual_quality = result.get("visual_quality", {})
        missing_layers = ", ".join(density.get("missing_layers", [])) or "none"
        notes = "; ".join(result["errors"]) if result["errors"] else f"{visual_quality.get('status', 'UNKNOWN')} score={visual_quality.get('overall_score', 'n/a')}"
        lines.append(
            "| {case} | {status} | {steps} | {objects} | {avg} | {missing} | {labels} | {flow} | {crossings} | {storyboard} | {visual_quality} | {notes} |".format(
                case=result["slug"],
                status="PASS" if result["ok"] else "FAIL",
                steps=result["scene"]["steps"],
                objects=result["scene"]["objects"],
                avg=density.get("avg_objects_per_step", "n/a"),
                missing=missing_layers,
                labels=label_layout.get("severe_collisions", "n/a"),
                flow=flow_lines.get("severe_items", "n/a"),
                crossings=flow_lines.get("crossings", "n/a"),
                storyboard="SKIP" if storyboard.get("applicable") is False else ("PASS" if storyboard.get("ok") else "FAIL"),
                visual_quality=f"{visual_quality.get('status', 'n/a')} {visual_quality.get('overall_score', 'n/a')}",
                notes=notes.replace("|", "\\|"),
            )
        )
    lines.extend(["", "## Checked Surface", ""])
    lines.extend(
        [
            "- `.xivplan` structure, data URLs, step titles, guide text, arena bounds, party overlap, and party count.",
            "- `manifest.json`, step PNG files, figure ordering, image dimensions, Markdown, DOCX, PDF, role assignments, and `unknowns`.",
            "- visual density, object counts, key layer coverage, and single-step focus.",
            "- label layout, text collisions, text over party/Boss/marker/mechanic zones, and label review items.",
            "- flow lines, arrow crossings, arrow-head obstruction, and movement through danger-zone review items.",
            "- Phase F storyboard coverage, required step metadata, and observe / movement / resolution / reset phase coverage when the scene is generated by `build_spec_from_solution.py`.",
            "- Phase G visual quality score across context, density, labels, flow, layers, aesthetics, and step story. Severe issues fail; review issues are reported but do not block.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 9 quality gates over Phase 8 e2e cases.")
    parser.add_argument("phase8_root", type=Path, help="Directory containing Phase 8 case folders")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="Directory for quality gate reports")
    args = parser.parse_args()

    try:
        cases = discover_cases(args.phase8_root)
    except OSError as exc:
        print(f"ERROR: cannot list {args.phase8_root}: {exc}", file=sys.stderr)
        return 2
    if not cases:
        print(f"ERROR: no Phase 8 cases found under {args.phase8_root}", file=sys.stderr)
        return 2

    results = [case_result(case_dir) for case_dir in cases]
    summary = aggregate(results)
    payload = {"summary": summary, "results": results}

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "phase9-quality-results.json"
    markdown_path = args.out_dir / "phase9-quality-report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(summary, results), encoding="utf-8")

    print(f"Wrote {markdown_path}")
    print(f"Wrote {json_path}")
    print(f"status: {'PASS' if summary['ok'] else 'FAIL'} ({summary['passed']}/{summary['cases']} cases)")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
