#!/usr/bin/env python3
"""Validate a generated FFXIV guide package against its Phase 8 manifest."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any


REQUIRED_ROLES = {"MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"}
GROUP_EXPANSIONS = {
    "MT/ST": {"MT", "ST"},
    "T/H": {"MT", "ST", "H1", "H2"},
    "TH": {"MT", "ST", "H1", "H2"},
    "H1/H2": {"H1", "H2"},
    "D1-D4": {"D1", "D2", "D3", "D4"},
    "DPS": {"D1", "D2", "D3", "D4"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as file:
            header = file.read(24)
    except OSError:
        return None
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return struct.unpack(">II", header[16:24])


def resolve_case_dir(path: Path) -> tuple[Path, Path]:
    path = path.resolve()
    if path.name == "guide-package":
        return path.parent, path
    package = path / "guide-package"
    if package.exists():
        return path, package
    return path, path


def covered_roles(assignments: list[Any]) -> set[str]:
    covered: set[str] = set()
    for item in assignments:
        if not isinstance(item, dict):
            continue
        role_text = str(item.get("role", ""))
        for group, roles in GROUP_EXPANSIONS.items():
            if group in role_text:
                covered.update(roles)
        for role in REQUIRED_ROLES:
            if role in role_text:
                covered.add(role)
    return covered


def validate_package(path: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    case_dir, package_dir = resolve_case_dir(path)
    guide_json = package_dir / "guide.json"
    manifest_path = case_dir / "manifest.json"

    required_files = {
        "guide.json": guide_json,
        "guide.md": package_dir / "guide.md",
        "guide.docx": package_dir / "guide.docx",
        "guide.pdf": package_dir / "guide.pdf",
    }
    for label, required_path in required_files.items():
        if not required_path.exists():
            fail(errors, f"{label} is missing at {required_path}")
        elif required_path.stat().st_size == 0:
            fail(errors, f"{label} is empty at {required_path}")
    if not manifest_path.exists():
        fail(errors, f"manifest.json is missing at {manifest_path}")

    if errors:
        return errors, {"case_dir": str(case_dir), "package_dir": str(package_dir)}

    try:
        guide = read_json(guide_json)
        manifest = read_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"failed to read package JSON: {exc}"], {"case_dir": str(case_dir), "package_dir": str(package_dir)}

    figures = guide.get("figures")
    manifest_steps = manifest.get("steps")
    if not isinstance(figures, list):
        fail(errors, "guide.json figures must be a list")
        figures = []
    if not isinstance(manifest_steps, list):
        fail(errors, "manifest.json steps must be a list")
        manifest_steps = []
    if len(figures) != len(manifest_steps):
        fail(errors, f"figure count {len(figures)} does not match manifest step count {len(manifest_steps)}")

    checked_images: list[dict[str, Any]] = []
    for index, manifest_step in enumerate(manifest_steps, start=1):
        if not isinstance(manifest_step, dict):
            fail(errors, f"manifest steps[{index - 1}] must be an object")
            continue
        expected_step = manifest_step.get("step")
        if expected_step != index:
            fail(errors, f"manifest step {index} has step={expected_step!r}")
        image_rel = manifest_step.get("image")
        if not isinstance(image_rel, str) or not image_rel:
            fail(errors, f"manifest step {index} is missing image")
            continue
        image_path = case_dir / image_rel
        if not image_path.exists():
            fail(errors, f"manifest step {index} image is missing: {image_path}")
            continue
        if image_path.stat().st_size == 0:
            fail(errors, f"manifest step {index} image is empty: {image_path}")
            continue
        size = png_size(image_path)
        if size is None:
            fail(errors, f"manifest step {index} image is not a valid PNG: {image_path}")
            continue
        width, height = size
        if width < 500 or height < 500:
            fail(errors, f"manifest step {index} image is too small: {width}x{height}")
        checked_images.append({"step": index, "image": str(image_path), "width": width, "height": height})

        if index <= len(figures) and isinstance(figures[index - 1], dict):
            figure = figures[index - 1]
            if figure.get("step") != index:
                fail(errors, f"guide figure {index} has step={figure.get('step')!r}")
            if figure.get("image") != image_rel:
                fail(errors, f"guide figure {index} image does not match manifest: {figure.get('image')!r} != {image_rel!r}")

    unknowns = guide.get("unknowns")
    if not isinstance(unknowns, list):
        fail(errors, "guide.json unknowns must exist and be a list")

    role_assignments = guide.get("role_assignments")
    if not isinstance(role_assignments, list):
        fail(errors, "guide.json role_assignments must be a list")
        role_assignments = []
    missing_roles = sorted(REQUIRED_ROLES - covered_roles(role_assignments))
    if missing_roles:
        fail(errors, "role_assignments do not cover: " + ", ".join(missing_roles))

    stats = {
        "case_dir": str(case_dir),
        "package_dir": str(package_dir),
        "figures": len(figures),
        "manifest_steps": len(manifest_steps),
        "checked_images": checked_images,
        "unknowns": len(unknowns) if isinstance(unknowns, list) else None,
        "covered_roles": sorted(covered_roles(role_assignments)),
    }
    return errors, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate guide package files, figures, images, roles, and unknowns.")
    parser.add_argument("path", type=Path, help="Case directory or guide-package directory")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    errors, stats = validate_package(args.path)
    result = {"ok": not errors, "errors": errors, "stats": stats}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    print(f"figures: {stats['figures']}")
    print(f"images: {len(stats['checked_images'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
