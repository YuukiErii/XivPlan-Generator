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
        density_errors = [] if density["ok"] else ["visual density audit recommends review"]
    except Exception as exc:  # noqa: BLE001 - keep batch quality gate running across cases.
        density = {"ok": False, "error": str(exc)}
        density_errors = [f"visual density audit failed: {exc}"]

    errors = scene_errors + package_errors + density_errors
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
        "| Case | Status | Steps | Objects | Avg Objects / Step | Missing Layers | Notes |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for result in results:
        density = result.get("density", {})
        missing_layers = ", ".join(density.get("missing_layers", [])) or "none"
        notes = "; ".join(result["errors"]) if result["errors"] else density.get("summary", "")
        lines.append(
            "| {case} | {status} | {steps} | {objects} | {avg} | {missing} | {notes} |".format(
                case=result["slug"],
                status="PASS" if result["ok"] else "FAIL",
                steps=result["scene"]["steps"],
                objects=result["scene"]["objects"],
                avg=density.get("avg_objects_per_step", "n/a"),
                missing=missing_layers,
                notes=notes.replace("|", "\\|"),
            )
        )
    lines.extend(["", "## Checked Surface", ""])
    lines.extend(
        [
            "- `.xivplan` structure, data URLs, step titles, guide text, arena bounds, party overlap, and party count.",
            "- `manifest.json`, step PNG files, figure ordering, image dimensions, Markdown, DOCX, PDF, role assignments, and `unknowns`.",
            "- visual density, object counts, key layer coverage, and single-step focus.",
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
