#!/usr/bin/env python3
"""Run the full guide pipeline for a generic mechanic Markdown file."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from assemble_guide import assemble_guide
from audit_visual_density import audit_scene
from build_spec_from_solution import build_spec
from build_xivplan_scene import build_scene, write_json
from export_xivplan_steps import export_steps
from parse_mechanic_request import parse_text, render_unknowns, write_outputs
from plan_solution_candidates import plan_bundle
from run_ultimate_yokai_star_dance_pipeline import run_pipeline as run_ultimate_pipeline
from score_solution_candidates import render_markdown as render_score_markdown
from score_solution_candidates import score_bundle
from search_mechanic_knowledge import render_markdown as render_knowledge_markdown
from search_mechanic_knowledge import search as search_knowledge
from validate_guide_package import validate_package
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_ROOT = ROOT / "artifacts" / "full-guide-pipeline"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", cleaned).strip("-") or "guide"


def case_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "parsed": output_dir / "parsed-ir",
        "knowledge": output_dir / "knowledge-matches",
        "solution": output_dir / "solution-candidates",
        "spec": output_dir / "generated-specs",
        "xivplan": output_dir / "generated-xivplan",
        "guide": output_dir / "guide-package",
        "quality": output_dir / "quality-report",
    }


def ensure_output_available(output_dir: Path, force: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError(f"output directory already exists and is not empty: {output_dir}; use --force or choose --output-dir")
    if output_dir.exists() and force:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def guide_for(
    encounter_name: str,
    phase: str,
    version: str,
    input_path: Path,
    bundle: dict[str, Any],
    scores: dict[str, Any],
    manifest: dict[str, Any],
    spec: dict[str, Any],
    unknowns: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_id = scores.get("recommended_candidate")
    candidates = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    candidate = candidates.get(candidate_id, {})
    steps = spec["steps"]
    unknown_text = [item.get("question") or item.get("text") for item in unknowns if item.get("question") or item.get("text")]
    return {
        "title": f"{encounter_name} {phase} {version}",
        "summary": f"由 `{input_path}` 自动生成的机制攻略草案。未确认信息保留在未知点列表中。",
        "recommended_solution": f"{candidate.get('name', candidate_id)}：{candidate.get('summary', '')}",
        "scene": "scene.xivplan",
        "spec": "spec.json",
        "figures": [
            {
                "step": item["step"],
                "title": steps[item["step"] - 1]["title"],
                "image": item["image"],
                "caption": f"图 {item['step']}：{steps[item['step'] - 1]['title']}",
                "guide_text": steps[item["step"] - 1]["guide_text"],
            }
            for item in manifest["steps"]
        ],
        "flow": [step["guide_text"] for step in steps],
        "role_assignments": [
            {"role": "MT/ST", "position": "按图示坦克位", "task": "处理坦克职责、塔或复位。"},
            {"role": "H1/H2", "position": "按图示治疗位", "task": "保证治疗覆盖，读条窗口少移动。"},
            {"role": "D1/D2", "position": "近战内圈或斜角", "task": "优先保 uptime 并按图处理机制。"},
            {"role": "D3/D4", "position": "外圈或读条锚定位", "task": "D3 机动补位，D4 尽量少动。"},
        ],
        "common_mistakes": [
            "把未确认规则写成确定结论。",
            "图中路线与短 call 不一致。",
            "判定后没有按图示复位。",
        ],
        "short_callout": [
            "先观察，再预站。",
            "按推荐候选固定职责处理。",
            "未知点按风险列表确认。",
        ],
        "mnemonic": "观察、预站、判定、移动、结算、复位。",
        "consistency_checks": [
            "IR、知识检索、候选评分、spec、scene、PNG 和攻略包均已生成。",
            "质量门检查 scene、manifest、图片、DOCX/PDF、职责表和 unknowns。",
            "攻略正文保持草案措辞，不把 unknown 写成事实。",
        ],
        "unknowns": unknown_text,
    }


def copy_for_quality(spec_path: Path, scene_path: Path, manifest_path: Path, guide_package: Path, case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(spec_path, case_dir / "spec.json")
    shutil.copy2(scene_path, case_dir / "scene.xivplan")
    shutil.copy2(manifest_path, case_dir / "manifest.json")
    package_target = case_dir / "guide-package"
    if package_target.exists():
        shutil.rmtree(package_target)
    shutil.copytree(guide_package, package_target)
    source_images = scene_path.parent / "images"
    if source_images.exists():
        image_target = case_dir / "images"
        if image_target.exists():
            shutil.rmtree(image_target)
        shutil.copytree(source_images, image_target)


def run_quality(case_dir: Path, quality_dir: Path) -> dict[str, Any]:
    scene_path = case_dir / "scene.xivplan"
    scene = read_json(scene_path)
    scene_errors, type_counts, object_count = validate_scene(scene)
    package_errors, package_stats = validate_package(case_dir)
    density = audit_scene(scene_path)
    errors = scene_errors + package_errors + ([] if density["ok"] else ["visual density audit recommends review"])
    result = {
        "ok": not errors,
        "errors": errors,
        "scene": {
            "path": str(scene_path),
            "steps": len(scene.get("steps", [])),
            "objects": object_count,
            "types": dict(sorted(type_counts.items())),
        },
        "package": package_stats,
        "density": density,
    }
    write_json_file(quality_dir / "quality-results.json", result)
    lines = [
        "# Full Guide Pipeline Quality Report",
        "",
        f"- status: {'PASS' if result['ok'] else 'FAIL'}",
        f"- steps: {result['scene']['steps']}",
        f"- objects: {result['scene']['objects']}",
        f"- avg objects / step: {density.get('avg_objects_per_step')}",
        f"- notes: {density.get('summary', '')}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    write_text(quality_dir / "quality-report.md", "\n".join(lines))
    return result


def run_generic_pipeline(
    input_path: Path,
    encounter_name: str,
    phase: str,
    version: str,
    output_dir: Path,
    force: bool,
) -> dict[str, Any]:
    ensure_output_available(output_dir, force)
    paths = case_paths(output_dir)
    input_text = read_text(input_path)

    parsed = parse_text(input_text, encounter_name, phase, version, "user-input")
    write_outputs(parsed, paths["parsed"], input_text, input_path)

    knowledge = search_knowledge(input_text, topn=6)
    write_json_file(paths["knowledge"] / "knowledge-search.json", knowledge)
    write_text(paths["knowledge"] / "knowledge-search.md", render_knowledge_markdown(knowledge))

    bundle = plan_bundle(parsed["mechanic_ir"], parsed["timeline_ir"], knowledge, {"strategy_context": "prog"})
    write_json_file(paths["solution"] / "solution-candidates.json", bundle)
    scores = score_bundle(bundle)
    write_json_file(paths["solution"] / "solution-scores.json", scores)
    write_text(paths["solution"] / "solution-report.md", render_score_markdown(scores))
    write_text(paths["solution"] / "unknowns.md", render_unknowns(parsed["unknowns"]))

    risks = ["# Risk And Unknowns", ""]
    if parsed["unknowns"]:
        risks.extend(f"- `{item['id']}` {item['question']}" for item in parsed["unknowns"])
    else:
        risks.append("- 暂无显式未知点；仍需实战确认范围、判定和复位节奏。")
    write_text(paths["solution"] / "risks-and-assumptions.md", "\n".join(risks))

    spec = build_spec(bundle, scores, None)
    spec_path = paths["spec"] / "spec.json"
    scene_path = paths["xivplan"] / "scene.xivplan"
    write_json(spec_path, spec)
    scene = build_scene(spec)
    write_json(scene_path, scene)
    errors, _, _ = validate_scene(scene)
    if errors:
        raise RuntimeError(f"generated scene invalid: {errors}")

    manifest = export_steps(scene_path, paths["xivplan"], scale_factor=1)
    guide = guide_for(encounter_name, phase, version, input_path, bundle, scores, manifest, spec, parsed["unknowns"])
    guide_source = paths["xivplan"] / "guide.json"
    write_json(guide_source, guide)
    outputs = assemble_guide(guide_source, paths["guide"], strict_images=True)

    quality_case = paths["quality"] / "case"
    copy_for_quality(spec_path, scene_path, paths["xivplan"] / "manifest.json", paths["guide"], quality_case)
    quality = run_quality(quality_case, paths["quality"])

    summary = {
        "input": str(input_path),
        "encounter_name": encounter_name,
        "phase": phase,
        "version": version,
        "recommended_candidate": scores.get("recommended_candidate"),
        "unknowns": len(parsed["unknowns"]),
        "quality_ok": quality["ok"],
        "output_dir": str(output_dir),
        "guide_markdown": str(outputs["markdown"]),
        "guide_docx": str(outputs["docx"]),
        "guide_pdf": str(outputs["pdf"]),
    }
    write_json_file(output_dir / "pipeline-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run parse -> analogy -> solution planning -> XivPlan -> guide package -> quality gate.")
    parser.add_argument("input", nargs="?", type=Path, help="Mechanic notes Markdown file")
    parser.add_argument("--encounter-name", default="Encounter", help="Encounter name for the guide title and IR")
    parser.add_argument("--phase", default="P1", help="Phase label")
    parser.add_argument("--version", default="v0.1-draft", help="Version label")
    parser.add_argument("--output-dir", type=Path, help="Output directory for generic mode")
    parser.add_argument("--force", action="store_true", help="Overwrite the selected output directory/version")
    parser.add_argument("--ultimate-yokai-star-dance", action="store_true", help="Use the versioned Ultimate Yokai Star Dance workspace")
    parser.add_argument("--previous-version", help="Previous version label for Ultimate Yokai Star Dance change-log entries")
    args = parser.parse_args()

    try:
        if args.ultimate_yokai_star_dance:
            if args.input is None:
                input_path = ROOT / "artifacts" / "ultimate-yokai-star-dance" / "raw-notes" / "p1-draft-notes.md"
            else:
                input_path = args.input
            summary = run_ultimate_pipeline(input_path, args.version, args.previous_version, args.force)
        else:
            if args.input is None:
                print("ERROR: generic mode requires an input Markdown file", file=sys.stderr)
                return 2
            output_dir = args.output_dir or DEFAULT_OUT_ROOT / slugify(f"{args.encounter_name}-{args.phase}-{args.version}")
            summary = run_generic_pipeline(args.input, args.encounter_name, args.phase, args.version, output_dir, args.force)
    except Exception as exc:  # noqa: BLE001 - CLI should report concise failures.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"version: {summary['version']}")
    print(f"recommended: {summary['recommended_candidate']}")
    print(f"unknowns: {summary['unknowns']}")
    print(f"quality: {'PASS' if summary['quality_ok'] else 'FAIL'}")
    print(f"output: {summary.get('output_dir') or summary.get('outputs', {}).get('guide', '')}")
    return 0 if summary["quality_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
