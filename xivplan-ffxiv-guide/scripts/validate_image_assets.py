#!/usr/bin/env python3
"""Validate PNG assets before embedding them into XivPlan specs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image


class AssetError(ValueError):
    """Image asset does not meet guide-asset requirements."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def alpha_stats(image: Image.Image) -> tuple[bool, int, float, bool]:
    has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    histogram = alpha.histogram()
    total = sum(histogram)
    transparent = sum(histogram[:16])
    opaque = sum(histogram[221:])
    subject_ratio = opaque / max(total, 1)
    corners = [alpha.getpixel((0, 0)), alpha.getpixel((rgba.width - 1, 0)), alpha.getpixel((0, rgba.height - 1)), alpha.getpixel((rgba.width - 1, rgba.height - 1))]
    transparent_corners = all(value < 16 for value in corners)
    return has_alpha, transparent, subject_ratio, transparent_corners


def validate_png(path: Path, min_size: int, max_size: int, require_alpha: bool) -> dict[str, Any]:
    if not path.exists():
        raise AssetError(f"missing asset: {path}")
    if path.suffix.lower() != ".png":
        raise AssetError(f"asset must be PNG: {path}")
    with Image.open(path) as image:
        width, height = image.size
        has_alpha, transparent_pixels, subject_ratio, transparent_corners = alpha_stats(image)
    if width < min_size or height < min_size:
        raise AssetError(f"{path}: image is too small ({width}x{height}); minimum is {min_size}px")
    if width > max_size or height > max_size:
        raise AssetError(f"{path}: image is too large ({width}x{height}); maximum is {max_size}px")
    if require_alpha and not has_alpha:
        raise AssetError(f"{path}: image must have an alpha channel")
    if require_alpha and not transparent_corners:
        raise AssetError(f"{path}: corners must be transparent for clean XivPlan placement")
    if require_alpha and subject_ratio < 0.02:
        raise AssetError(f"{path}: subject coverage is too low; asset may be blank")
    if require_alpha and subject_ratio > 0.85:
        raise AssetError(f"{path}: subject coverage is too high; transparent padding may be missing")
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "has_alpha": has_alpha,
        "transparent_pixels": transparent_pixels,
        "subject_ratio": round(subject_ratio, 4),
        "transparent_corners": transparent_corners,
    }


def iter_manifest_assets(manifest_path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    assets = manifest.get("enemy_assets")
    if assets is None:
        assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise AssetError("manifest.assets or manifest.enemy_assets must be a list")
    items: list[dict[str, Any]] = []
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise AssetError(f"assets[{index}] must be an object")
        asset_path = asset.get("path")
        fallback = asset.get("fallback")
        if isinstance(asset_path, str) and asset_path:
            items.append({"path": (manifest_path.parent / asset_path).resolve(), "asset": asset})
            continue
        if manifest.get("enemy_assets") is not None and isinstance(fallback, str) and fallback:
            items.append(
                {
                    "fallback": fallback,
                    "asset": asset,
                    "status": "fallback",
                    "path": None,
                }
            )
            continue
        raise AssetError(f"assets[{index}].path must be a non-empty string or enemy fallback must be set")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNG assets for image2/XivPlan guide usage.")
    parser.add_argument("paths", nargs="+", type=Path, help="PNG files or asset manifest JSON files")
    parser.add_argument("--min-size", type=int, default=32, help="Minimum width and height in pixels")
    parser.add_argument("--max-size", type=int, default=1024, help="Maximum width and height in pixels")
    parser.add_argument("--no-alpha-required", action="store_true", help="Allow opaque PNGs")
    parser.add_argument("--json-out", type=Path, help="Optional JSON validation report path")
    args = parser.parse_args()

    report: list[dict[str, Any]] = []
    try:
        manifest_fallbacks: list[dict[str, Any]] = []
        paths: list[Path] = []
        for input_path in args.paths:
            if input_path.suffix.lower() == ".json":
                for item in iter_manifest_assets(input_path, read_json(input_path)):
                    if item.get("path") is None:
                        asset = item.get("asset", {})
                        manifest_fallbacks.append(
                            {
                                "enemy_id": asset.get("enemy_id") or asset.get("asset_id") or asset.get("name"),
                                "name": asset.get("name"),
                                "kind": asset.get("kind"),
                                "fallback": item.get("fallback"),
                                "status": "fallback",
                            }
                        )
                    else:
                        paths.append(item["path"])
            else:
                paths.append(input_path)
        for path in paths:
            report.append(validate_png(path.resolve(), args.min_size, args.max_size, not args.no_alpha_required))
        report.extend(manifest_fallbacks)
    except (OSError, json.JSONDecodeError, AssetError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps({"assets": report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(report)} asset(s)")
    for item in report:
        if item.get("status") == "fallback":
            print(f"- {item.get('enemy_id') or item.get('name')}: fallback={item.get('fallback')}")
        else:
            print(f"- {item['path']} {item['width']}x{item['height']} alpha={item['has_alpha']} subject={item['subject_ratio']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
