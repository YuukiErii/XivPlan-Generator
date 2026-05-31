#!/usr/bin/env python3
"""Assemble a guide package from guide.json into Markdown, DOCX, and PDF."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    from build_docx import build_docx_from_guide
    from build_pdf import build_pdf_from_guide
except ImportError:  # pragma: no cover - supports package-style imports.
    from .build_docx import build_docx_from_guide
    from .build_pdf import build_pdf_from_guide


class GuideError(ValueError):
    """guide.json cannot be assembled into a guide package."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.strip().lower(), flags=re.UNICODE)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "guide"


def ensure_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise GuideError(f"{field} must be a list")
    return value


def validate_guide(guide: Any) -> dict[str, Any]:
    if not isinstance(guide, dict):
        raise GuideError("guide root must be an object")
    for field in ("title", "summary"):
        if not isinstance(guide.get(field), str) or not guide[field].strip():
            raise GuideError(f"{field} must be a non-empty string")
    for field in ("figures", "role_assignments", "common_mistakes", "unknowns", "consistency_checks"):
        ensure_list(guide.get(field), field)
    return guide


def copy_optional_file(source: Path | None, target: Path) -> str | None:
    if source is None:
        return None
    if not source.exists():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target.name


def normalize_figure_images(guide: dict[str, Any], guide_path: Path, output_dir: Path, strict_images: bool) -> None:
    images_dir = output_dir / "images"
    for index, figure in enumerate(ensure_list(guide.get("figures"), "figures"), start=1):
        if not isinstance(figure, dict):
            raise GuideError(f"figures[{index - 1}] must be an object")
        figure.setdefault("step", index)
        figure.setdefault("title", f"图 {index}")
        figure.setdefault("caption", figure.get("title", f"图 {index}"))
        image = figure.get("image")
        if not image:
            continue
        source = (guide_path.parent / str(image)).resolve()
        if not source.exists():
            message = f"figure {index} image does not exist: {source}"
            if strict_images:
                raise GuideError(message)
            figure["missing_image"] = str(source)
            continue
        filename = f"step_{index:02d}_{slugify(str(figure.get('title', index)))}{source.suffix.lower() or '.png'}"
        images_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, images_dir / filename)
        figure["image"] = f"images/{filename}"


def copy_sources(guide: dict[str, Any], guide_path: Path, output_dir: Path) -> None:
    scene = guide.get("scene")
    spec = guide.get("spec")
    if scene:
        copy_optional_file((guide_path.parent / str(scene)).resolve(), output_dir / "scene.xivplan")
    if spec:
        copy_optional_file((guide_path.parent / str(spec)).resolve(), output_dir / "spec.json")


def line_items(items: list[Any]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)


def render_role_table(assignments: list[Any]) -> str:
    if not assignments:
        return "| 职能 | 位置 | 任务 |\n|---|---|---|\n| 全员 | 按图示 | 按攻略正文处理 |"
    rows = ["| 职能 | 位置 | 任务 |", "|---|---|---|"]
    for item in assignments:
        if not isinstance(item, dict):
            raise GuideError("role_assignments entries must be objects")
        rows.append(f"| {item.get('role', '')} | {item.get('position', '')} | {item.get('task', '')} |")
    return "\n".join(rows)


def render_short_markdown(guide: dict[str, Any]) -> str:
    callouts = ensure_list(guide.get("short_callout"), "short_callout")
    assignments = ensure_list(guide.get("role_assignments"), "role_assignments")
    mnemonic = guide.get("mnemonic", "无")
    return "\n\n".join(
        [
            f"# {guide['title']} 队内速记",
            line_items(callouts),
            "## 职能分工\n\n" + render_role_table(assignments),
            f"## 口诀\n\n> {mnemonic}",
        ]
    )


def render_full_markdown(guide: dict[str, Any]) -> str:
    sections: list[str] = [
        f"# {guide['title']}",
        "## 一句话概括\n\n" + guide["summary"],
    ]
    if guide.get("recommended_solution"):
        sections.append("## 推荐解法\n\n" + str(guide["recommended_solution"]))

    figures = ensure_list(guide.get("figures"), "figures")
    for index, figure in enumerate(figures, start=1):
        title = figure.get("title", f"图 {index}")
        section = [f"## 图 {index}：{title}"]
        image = figure.get("image")
        if image:
            section.append(f"![图 {index}]({image})")
        elif figure.get("missing_image"):
            section.append(f"> 图片未找到：`{figure['missing_image']}`")
        guide_text = figure.get("guide_text") or figure.get("caption")
        if guide_text:
            section.append(str(guide_text))
        sections.append("\n\n".join(section))

    flow = ensure_list(guide.get("flow"), "flow")
    if flow:
        sections.append("## 详细处理流程\n\n" + "\n".join(f"{idx}. {item}" for idx, item in enumerate(flow, start=1)))
    sections.append("## 职能分工\n\n" + render_role_table(ensure_list(guide.get("role_assignments"), "role_assignments")))
    sections.append("## 常见失误\n\n" + line_items(ensure_list(guide.get("common_mistakes"), "common_mistakes")))
    sections.append("## 队内速记版\n\n" + line_items(ensure_list(guide.get("short_callout"), "short_callout")))
    sections.append(f"## 口诀\n\n> {guide.get('mnemonic', '无')}")
    checks = ensure_list(guide.get("consistency_checks"), "consistency_checks")
    sections.append("## 图文一致性检查\n\n" + line_items(checks))
    unknowns = ensure_list(guide.get("unknowns"), "unknowns")
    sections.append("## 需要确认的点\n\n" + line_items(unknowns if unknowns else ["无"]))
    return "\n\n".join(sections)


def assemble_guide(guide_path: Path, output_dir: Path, short_only: bool = False, strict_images: bool = False) -> dict[str, Path]:
    guide = validate_guide(read_json(guide_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    normalize_figure_images(guide, guide_path, output_dir, strict_images)
    copy_sources(guide, guide_path, output_dir)
    shutil.copy2(guide_path, output_dir / "guide.json")

    markdown = render_short_markdown(guide) if short_only else render_full_markdown(guide)
    markdown_path = output_dir / "guide.md"
    write_text(markdown_path, markdown)
    if not short_only:
        write_text(output_dir / "short-guide.md", render_short_markdown(guide))

    docx_path = output_dir / "guide.docx"
    pdf_path = output_dir / "guide.pdf"
    build_docx_from_guide(guide, docx_path, base_dir=output_dir, short_only=short_only)
    build_pdf_from_guide(guide, pdf_path, base_dir=output_dir, short_only=short_only)
    return {"markdown": markdown_path, "docx": docx_path, "pdf": pdf_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble guide.md, guide.docx, and guide.pdf from guide.json.")
    parser.add_argument("guide", type=Path, help="Path to guide.json")
    parser.add_argument("-o", "--output-dir", type=Path, required=True, help="Output guide package directory")
    parser.add_argument("--short-only", action="store_true", help="Write only the team-callout version to guide.md/docx/pdf")
    parser.add_argument("--strict-images", action="store_true", help="Fail when a figure image is missing")
    args = parser.parse_args()

    try:
        outputs = assemble_guide(args.guide, args.output_dir, args.short_only, args.strict_images)
    except (OSError, json.JSONDecodeError, GuideError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output_dir}")
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
