#!/usr/bin/env python3
"""Embed local PNG assets as data URLs into a XivPlan scene spec."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any


class InjectError(ValueError):
    """Asset manifest cannot be injected into the scene spec."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def data_url(path: Path) -> str:
    if not path.exists():
        raise InjectError(f"asset file does not exist: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    if mime_type != "image/png":
        raise InjectError(f"only PNG assets are supported for now: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def ensure_step(spec: dict[str, Any], index: int) -> dict[str, Any]:
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        raise InjectError("spec.steps must be a non-empty list")
    if index < 1 or index > len(steps):
        raise InjectError(f"placement step {index} is outside spec step range 1..{len(steps)}")
    step = steps[index - 1]
    if not isinstance(step, dict):
        raise InjectError(f"spec.steps[{index - 1}] must be an object")
    objects = step.setdefault("objects", [])
    if not isinstance(objects, list):
        raise InjectError(f"spec.steps[{index - 1}].objects must be a list")
    return step


def remove_existing(objects: list[Any], key: str) -> None:
    objects[:] = [obj for obj in objects if not (isinstance(obj, dict) and obj.get("key") == key)]


def inject_manifest(spec: dict[str, Any], manifest: dict[str, Any], manifest_path: Path, replace: bool) -> dict[str, Any]:
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise InjectError("manifest.assets must be a list")
    for asset_index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise InjectError(f"assets[{asset_index}] must be an object")
        asset_id = asset.get("asset_id") or asset.get("name") or f"asset-{asset_index + 1}"
        asset_path_value = asset.get("path")
        if not isinstance(asset_path_value, str) or not asset_path_value:
            raise InjectError(f"assets[{asset_index}].path must be a non-empty string")
        asset_path = (manifest_path.parent / asset_path_value).resolve()
        encoded = data_url(asset_path)
        placements = asset.get("placements")
        if not isinstance(placements, list) or not placements:
            raise InjectError(f"asset {asset_id!r} requires at least one placement")
        for placement_index, placement in enumerate(placements):
            if not isinstance(placement, dict):
                raise InjectError(f"asset {asset_id!r} placement {placement_index} must be an object")
            step_index = int(placement.get("step", 1))
            step = ensure_step(spec, step_index)
            objects = step["objects"]
            key = placement.get("key") or f"{asset_id}-{step_index}-{placement_index + 1}"
            image_object = {
                "kind": placement.get("kind", "image"),
                "key": key,
                "name": placement.get("name", asset.get("name", asset_id)),
                "image": encoded,
                "pos": placement.get("pos", "center"),
                "width": int(placement.get("width", asset.get("width", 72))),
                "height": int(placement.get("height", asset.get("height", 72))),
            }
            for optional_key in (
                "distance",
                "offset",
                "rotation",
                "opacity",
                "label",
                "labelPos",
                "labelDistance",
                "labelOffset",
                "labelFontSize",
            ):
                if optional_key in placement:
                    image_object[optional_key] = placement[optional_key]
            if replace:
                remove_existing(objects, str(key))
            objects.append(image_object)
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject local PNG assets into a XivPlan spec as data URLs.")
    parser.add_argument("spec", type=Path, help="Input compact scene spec JSON")
    parser.add_argument("manifest", type=Path, help="Asset manifest JSON")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output spec JSON")
    parser.add_argument("--replace", action="store_true", help="Replace existing objects with the same placement key")
    args = parser.parse_args()

    try:
        spec = read_json(args.spec)
        manifest = read_json(args.manifest)
        if not isinstance(spec, dict) or not isinstance(manifest, dict):
            raise InjectError("spec and manifest roots must be objects")
        write_json(args.output, inject_manifest(spec, manifest, args.manifest, args.replace))
    except (OSError, json.JSONDecodeError, InjectError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
