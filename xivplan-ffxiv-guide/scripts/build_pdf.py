#!/usr/bin/env python3
"""Build an A4 PDF guide from guide.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
BODY_FONT = "STSong-Light"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def register_fonts() -> None:
    try:
        registerFont(UnicodeCIDFont(BODY_FONT))
    except Exception:
        pass


def wrap_text(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    for raw_line in str(text).splitlines() or [""]:
        raw_line = raw_line.strip()
        if not raw_line:
            lines.append("")
            continue
        current = ""
        for char in raw_line:
            current += char
            if len(current) >= max_chars:
                lines.append(current)
                current = ""
        if current:
            lines.append(current)
    return lines


class PdfWriter:
    def __init__(self, output_path: Path) -> None:
        register_fonts()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.canvas = canvas.Canvas(str(output_path), pagesize=A4)
        self.y = PAGE_HEIGHT - MARGIN

    def ensure_space(self, height: float) -> None:
        if self.y - height < MARGIN:
            self.canvas.showPage()
            self.y = PAGE_HEIGHT - MARGIN

    def text(self, text: str, size: int = 11, leading: float | None = None, bullet: bool = False) -> None:
        leading = leading or size * 1.45
        max_chars = 42 if size <= 11 else 30
        for line in wrap_text(text, max_chars):
            self.ensure_space(leading)
            self.canvas.setFont(BODY_FONT, size)
            prefix = "• " if bullet and line else ""
            self.canvas.drawString(MARGIN, self.y, prefix + line)
            self.y -= leading
        self.y -= 2

    def heading(self, text: str, level: int) -> None:
        size = 20 if level == 1 else 15
        self.ensure_space(size * 2)
        self.canvas.setFont(BODY_FONT, size)
        self.canvas.drawString(MARGIN, self.y, text)
        self.y -= size * 1.8

    def image(self, image_path: Path, caption: str) -> None:
        if not image_path.exists():
            self.text(f"图片未找到：{image_path}", 10)
            return
        try:
            with Image.open(image_path) as image:
                width, height = image.size
        except Exception:
            self.text(f"图片无法读取：{image_path}", 10)
            return
        max_width = PAGE_WIDTH - MARGIN * 2
        max_height = 115 * mm
        scale = min(max_width / width, max_height / height, 1.0)
        draw_width = width * scale
        draw_height = height * scale
        self.ensure_space(draw_height + 24)
        x = (PAGE_WIDTH - draw_width) / 2
        self.canvas.drawImage(str(image_path), x, self.y - draw_height, draw_width, draw_height, preserveAspectRatio=True, mask="auto")
        self.y -= draw_height + 6
        self.canvas.setFont(BODY_FONT, 9)
        self.canvas.drawCentredString(PAGE_WIDTH / 2, self.y, caption)
        self.y -= 18

    def save(self) -> None:
        self.canvas.save()


def add_role_table(writer: PdfWriter, assignments: list[Any]) -> None:
    if not assignments:
        writer.text("全员 | 按图示 | 按攻略正文处理", 10)
        return
    writer.text("职能 | 位置 | 任务", 10)
    for item in assignments:
        writer.text(f"{item.get('role', '')} | {item.get('position', '')} | {item.get('task', '')}", 10)


def add_short_callout(writer: PdfWriter, guide: dict[str, Any]) -> None:
    writer.heading(f"{guide['title']} 队内速记", 1)
    for item in guide.get("short_callout", []) or ["无"]:
        writer.text(str(item), bullet=True)
    writer.heading("职能分工", 2)
    add_role_table(writer, guide.get("role_assignments", []))
    writer.heading("口诀", 2)
    writer.text(str(guide.get("mnemonic", "无")))


def build_pdf_from_guide(guide: dict[str, Any], output_path: Path, base_dir: Path | None = None, short_only: bool = False) -> None:
    base_dir = base_dir or output_path.parent
    writer = PdfWriter(output_path)
    if short_only:
        add_short_callout(writer, guide)
        writer.save()
        return

    writer.heading(guide["title"], 1)
    writer.heading("一句话概括", 2)
    writer.text(guide["summary"])
    if guide.get("recommended_solution"):
        writer.heading("推荐解法", 2)
        writer.text(str(guide["recommended_solution"]))

    for index, figure in enumerate(guide.get("figures", []), start=1):
        title = figure.get("title", f"图 {index}")
        writer.heading(f"图 {index}：{title}", 2)
        image = figure.get("image")
        if image:
            writer.image(base_dir / image, figure.get("caption", title))
        writer.text(str(figure.get("guide_text") or figure.get("caption") or ""))

    flow = guide.get("flow", [])
    if flow:
        writer.heading("详细处理流程", 2)
        for idx, item in enumerate(flow, start=1):
            writer.text(f"{idx}. {item}")

    writer.heading("职能分工", 2)
    add_role_table(writer, guide.get("role_assignments", []))
    writer.heading("常见失误", 2)
    for item in guide.get("common_mistakes", []) or ["无"]:
        writer.text(str(item), bullet=True)
    writer.heading("队内速记版", 2)
    for item in guide.get("short_callout", []) or ["无"]:
        writer.text(str(item), bullet=True)
    writer.heading("口诀", 2)
    writer.text(str(guide.get("mnemonic", "无")))
    writer.heading("图文一致性检查", 2)
    for item in guide.get("consistency_checks", []) or ["无"]:
        writer.text(str(item), bullet=True)
    writer.heading("需要确认的点", 2)
    for item in guide.get("unknowns", []) or ["无"]:
        writer.text(str(item), bullet=True)
    writer.save()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build guide.pdf from guide.json.")
    parser.add_argument("guide", type=Path, help="Path to guide.json")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output PDF path")
    parser.add_argument("--short-only", action="store_true", help="Render only the team-callout version")
    args = parser.parse_args()
    try:
        build_pdf_from_guide(read_json(args.guide), args.output, base_dir=args.guide.parent, short_only=args.short_only)
    except Exception as exc:  # noqa: BLE001 - CLI should surface PDF errors clearly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
