#!/usr/bin/env python3
"""Validate the Phase 3 encounter knowledge-card structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REFERENCE_DIR = Path(__file__).resolve().parents[1] / "references"
ENCOUNTER_DIR = REFERENCE_DIR / "encounters"
ENCOUNTER_FILES = [
    ENCOUNTER_DIR / "ultimates" / "ucob.md",
    ENCOUNTER_DIR / "ultimates" / "uwu.md",
    ENCOUNTER_DIR / "ultimates" / "tea.md",
    ENCOUNTER_DIR / "ultimates" / "dsr.md",
    ENCOUNTER_DIR / "ultimates" / "top.md",
    ENCOUNTER_DIR / "ultimates" / "fru.md",
    ENCOUNTER_DIR / "savage" / "omega.md",
    ENCOUNTER_DIR / "savage" / "eden.md",
    ENCOUNTER_DIR / "savage" / "pandaemonium.md",
    ENCOUNTER_DIR / "savage" / "arcadion.md",
]
REQUIRED_FILES = [
    REFERENCE_DIR / "mechanic-taxonomy.md",
    REFERENCE_DIR / "positioning-patterns.md",
    ENCOUNTER_DIR / "index.md",
    ENCOUNTER_DIR / "coverage-audit.md",
    *ENCOUNTER_FILES,
]
FLOOR_SERIES = {
    ENCOUNTER_DIR / "savage" / "omega.md": [f"O{floor}S" for floor in range(1, 13)],
    ENCOUNTER_DIR / "savage" / "eden.md": [f"E{floor}S" for floor in range(1, 13)],
    ENCOUNTER_DIR / "savage" / "pandaemonium.md": [f"P{floor}S" for floor in range(1, 13)],
    ENCOUNTER_DIR / "savage" / "arcadion.md": [f"M{floor}S" for floor in range(1, 13)],
}
REQUIRED_FIELDS = [
    "副本",
    "阶段",
    "常见别名",
    "机制类别",
    "原理",
    "默认解法",
    "常见优化",
    "常见失误",
    "可类比机制",
    "可迁移部分",
    "不应照搬",
    "XivPlan 图示拆分",
    "需要确认的信息",
    "参考来源",
    "置信度",
]
ENTRY_HEADING = re.compile(r"^## (?!Scope$|Sources$|Usage Notes$)(.+)$", re.MULTILINE)
LOCAL_LINK = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)(?:#[^)]+)?\)")


def validate_card_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    matches = list(ENTRY_HEADING.finditer(text))
    if not matches:
        return [f"{path}: no mechanic cards found"]

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        missing = [field for field in REQUIRED_FIELDS if f"- {field}：" not in block]
        if missing:
            errors.append(f"{path}: {match.group(1)} missing {', '.join(missing)}")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.is_file():
            errors.append(f"missing required file: {path}")

    if not errors:
        for path in ENCOUNTER_FILES:
            errors.extend(validate_card_file(path))
        for path, floors in FLOOR_SERIES.items():
            text = path.read_text(encoding="utf-8")
            missing_floors = [
                floor
                for floor in floors
                if not re.search(rf"^- 副本：.* / {re.escape(floor)}(?:\s|$)", text, re.MULTILINE)
            ]
            if missing_floors:
                errors.append(f"{path}: missing floor coverage {', '.join(missing_floors)}")
        for link_source in [ENCOUNTER_DIR / "index.md", ENCOUNTER_DIR / "coverage-audit.md"]:
            text = link_source.read_text(encoding="utf-8")
            for link in LOCAL_LINK.findall(text):
                if not (link_source.parent / link).is_file():
                    errors.append(f"{link_source}: broken local link {link}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    card_count = 0
    for path in ENCOUNTER_FILES:
        card_count += len(ENTRY_HEADING.findall(path.read_text(encoding="utf-8")))
    print(f"OK: {len(REQUIRED_FILES)} files, {card_count} mechanic cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
