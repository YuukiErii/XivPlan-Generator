#!/usr/bin/env python3
"""Run the versioned Ultimate Yokai Star Dance progression pipeline."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from assemble_guide import assemble_guide
from audit_visual_density import audit_scene
from build_spec_from_solution import build_spec
from build_xivplan_scene import build_scene, write_json
from export_xivplan_steps import export_steps
from parse_mechanic_request import parse_text, render_unknowns, write_outputs
from plan_solution_candidates import plan_bundle
from score_solution_candidates import render_markdown as render_score_markdown
from score_solution_candidates import score_bundle
from search_mechanic_knowledge import render_markdown as render_knowledge_markdown
from search_mechanic_knowledge import search as search_knowledge
from validate_guide_package import validate_package
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "artifacts" / "ultimate-yokai-star-dance"
DEFAULT_NOTES = WORKSPACE / "raw-notes" / "p1-draft-notes.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def version_paths(version: str) -> dict[str, Path]:
    return {
        "parsed": WORKSPACE / "parsed-ir" / version,
        "knowledge": WORKSPACE / "knowledge-matches" / version,
        "solution": WORKSPACE / "solution-candidates" / version,
        "spec": WORKSPACE / "generated-specs" / version,
        "xivplan": WORKSPACE / "generated-xivplan" / version,
        "guide": WORKSPACE / "guide-packages" / version,
        "quality": WORKSPACE / "quality-reports" / version,
    }


def ensure_version_available(paths: dict[str, Path], force: bool) -> None:
    existing = [path for path in paths.values() if path.exists() and any(path.iterdir())]
    if existing and not force:
        labels = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"version outputs already exist; use a new --version or --force:\n{labels}")
    if force:
        for path in paths.values():
            if path.exists():
                shutil.rmtree(path)


def extract_section(notes: str, heading: str) -> list[str]:
    lines = notes.splitlines()
    items: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line[3:].strip() == heading
            continue
        if active and line.strip().startswith("-"):
            item = line.strip().lstrip("-").strip()
            if item and item != "暂无。":
                items.append(item)
    return items


def changed_unknowns(current_unknowns: list[dict[str, Any]], previous_quality: Path | None) -> list[str]:
    if not previous_quality or not previous_quality.exists():
        return []
    return [item.get("question", item.get("text", "")) for item in current_unknowns if item.get("severity") == "blocking"]


def guide_for(
    version: str,
    notes_path: Path,
    bundle: dict[str, Any],
    scores: dict[str, Any],
    manifest: dict[str, Any],
    spec: dict[str, Any],
    unknowns: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_id = scores.get("recommended_candidate")
    by_id = {candidate.get("id"): candidate for candidate in bundle.get("candidates", [])}
    candidate = by_id.get(candidate_id, {})
    steps = spec["steps"]
    unknown_text = [item.get("question") or item.get("text") for item in unknowns if item.get("question") or item.get("text")]
    return {
        "title": f"绝妖星乱舞 P1 {version}",
        "summary": "开荒草案。所有未确认规则都保留在未知点和风险列表中。",
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
            {"role": "MT/ST", "position": "南北或内圈坦克位", "task": "处理塔、死刑或复位职责。"},
            {"role": "H1/H2", "position": "东西或内圈治疗位", "task": "保持治疗覆盖，读条窗口少移动。"},
            {"role": "D1/D2", "position": "近战内圈或斜角", "task": "优先保 uptime，按图处理散开/塔。"},
            {"role": "D3/D4", "position": "外圈或读条锚定位", "task": "D3 机动补位，D4 尽量少动。"},
        ],
        "common_mistakes": [
            "把当前开荒假设当作最终打法。",
            "补充信息后只改图，不更新 raw notes。",
            "未记录推翻假设，导致队内使用旧 call。",
        ],
        "short_callout": [
            f"{version} 草案，先按图处理。",
            "未知点按风险列表确认。",
            "每轮判定后复位再看下一读条。",
        ],
        "mnemonic": "先记版本，再看未知；先观察，后移动。",
        "consistency_checks": [
            f"source notes: {notes_path}",
            "candidate report, analogy report, spec, scene, PNG, Markdown, DOCX, and PDF generated.",
            "unknowns preserved; guide wording remains draft-scoped.",
        ],
        "unknowns": unknown_text,
    }


def run_quality(case_dir: Path, quality_dir: Path) -> dict[str, Any]:
    scene_path = case_dir / "scene.xivplan"
    scene = read_json(scene_path)
    scene_errors, type_counts, object_count = validate_scene(scene)
    package_errors, package_stats = validate_package(case_dir)
    density = audit_scene(scene_path)
    density_errors = [] if density["ok"] else ["visual density audit recommends review"]
    errors = scene_errors + package_errors + density_errors
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
    json_write(quality_dir / "quality-results.json", result)
    lines = [
        f"# Ultimate Yokai Star Dance Quality Report",
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


def copy_for_quality(spec_path: Path, scene_path: Path, manifest_path: Path, guide_package: Path, case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(spec_path, case_dir / "spec.json")
    shutil.copy2(scene_path, case_dir / "scene.xivplan")
    shutil.copy2(manifest_path, case_dir / "manifest.json")
    target_package = case_dir / "guide-package"
    if target_package.exists():
        shutil.rmtree(target_package)
    shutil.copytree(guide_package, target_package)
    images = scene_path.parent / "images"
    if images.exists():
        target_images = case_dir / "images"
        if target_images.exists():
            shutil.rmtree(target_images)
        shutil.copytree(images, target_images)


def append_change_log(
    version: str,
    previous_version: str | None,
    notes_path: Path,
    notes_text: str,
    unknowns: list[dict[str, Any]],
    paths: dict[str, Path],
    quality: dict[str, Any],
) -> None:
    log_path = WORKSPACE / "change-log.md"
    if not log_path.exists():
        write_text(log_path, "# Ultimate Yokai Star Dance Change Log\n")
    confirmations = extract_section(notes_text, "新增确认") or ["未显式填写；见 raw notes。"]
    disproved = extract_section(notes_text, "推翻假设") or ["未显式填写。"]
    pending = extract_section(notes_text, "仍待确认") or [item.get("question", item.get("text", "")) for item in unknowns] or ["暂无阻塞未知点。"]
    entry = [
        "",
        f"## `{version}`",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- source_notes: `{notes_path}`",
        f"- previous_version: `{previous_version or 'none'}`",
        f"- quality: {'PASS' if quality.get('ok') else 'FAIL'}",
        "- 新增确认：",
        *[f"  - {item}" for item in confirmations],
        "- 推翻假设：",
        *[f"  - {item}" for item in disproved],
        "- 仍待确认：",
        *[f"  - {item}" for item in pending],
        "- outputs:",
        f"  - parsed_ir: `{paths['parsed']}`",
        f"  - knowledge_matches: `{paths['knowledge']}`",
        f"  - solution_candidates: `{paths['solution']}`",
        f"  - generated_spec: `{paths['spec']}`",
        f"  - generated_xivplan: `{paths['xivplan']}`",
        f"  - guide_package: `{paths['guide']}`",
        f"  - quality_report: `{paths['quality'] / 'quality-report.md'}`",
    ]
    with log_path.open("a", encoding="utf-8") as file:
        file.write("\n".join(entry) + "\n")


def run_pipeline(notes_path: Path, version: str, previous_version: str | None, force: bool) -> dict[str, Any]:
    paths = version_paths(version)
    ensure_version_available(paths, force)
    notes_text = read_text(notes_path)

    parsed = parse_text(notes_text, "Ultimate Yokai Star Dance", "P1", version, "raw-notes")
    write_outputs(parsed, paths["parsed"], notes_text, notes_path)

    knowledge = search_knowledge(notes_text, topn=6)
    json_write(paths["knowledge"] / "knowledge-search.json", knowledge)
    write_text(paths["knowledge"] / "knowledge-search.md", render_knowledge_markdown(knowledge))

    bundle = plan_bundle(parsed["mechanic_ir"], parsed["timeline_ir"], knowledge, {"strategy_context": "prog"})
    json_write(paths["solution"] / "solution-candidates.json", bundle)
    scores = score_bundle(bundle)
    json_write(paths["solution"] / "solution-scores.json", scores)
    write_text(paths["solution"] / "solution-report.md", render_score_markdown(scores))

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
    guide = guide_for(version, notes_path, bundle, scores, manifest, spec, parsed["unknowns"])
    guide_source = paths["xivplan"] / "guide.json"
    write_json(guide_source, guide)
    guide_outputs = assemble_guide(guide_source, paths["guide"], strict_images=True)

    write_text(paths["solution"] / "unknowns.md", render_unknowns(parsed["unknowns"]))
    risk_lines = ["# Risk And Unknowns", ""]
    if parsed["unknowns"]:
        for item in parsed["unknowns"]:
            risk_lines.append(f"- `{item['id']}` {item['question']}")
    else:
        risk_lines.append("- 暂无阻塞未知点；仍需实战验证范围、判定和复位节奏。")
    write_text(paths["solution"] / "risks-and-assumptions.md", "\n".join(risk_lines))

    quality_case = paths["quality"] / "case"
    copy_for_quality(spec_path, scene_path, paths["xivplan"] / "manifest.json", paths["guide"], quality_case)
    quality = run_quality(quality_case, paths["quality"])
    append_change_log(version, previous_version, notes_path, notes_text, parsed["unknowns"], paths, quality)

    summary = {
        "version": version,
        "notes": str(notes_path),
        "recommended_candidate": scores.get("recommended_candidate"),
        "unknowns": len(parsed["unknowns"]),
        "quality_ok": quality["ok"],
        "outputs": {key: str(value) for key, value in paths.items()},
        "guide_markdown": str(guide_outputs["markdown"]),
        "guide_docx": str(guide_outputs["docx"]),
        "guide_pdf": str(guide_outputs["pdf"]),
    }
    json_write(paths["quality"] / "pipeline-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a versioned Ultimate Yokai Star Dance guide package from raw notes.")
    parser.add_argument("--notes", type=Path, default=DEFAULT_NOTES, help="Raw notes Markdown file")
    parser.add_argument("--version", default="v0.1-draft", help="Version label such as v0.1-draft or v0.2-observed")
    parser.add_argument("--previous-version", help="Previous version label for change-log context")
    parser.add_argument("--force", action="store_true", help="Overwrite outputs for this version")
    args = parser.parse_args()
    try:
        summary = run_pipeline(args.notes, args.version, args.previous_version, args.force)
    except Exception as exc:  # noqa: BLE001 - CLI should report a concise failure.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"version: {summary['version']}")
    print(f"recommended: {summary['recommended_candidate']}")
    print(f"unknowns: {summary['unknowns']}")
    print(f"quality: {'PASS' if summary['quality_ok'] else 'FAIL'}")
    print(f"guide: {summary['guide_markdown']}")
    return 0 if summary["quality_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
