#!/usr/bin/env python3
"""Run Phase 8 end-to-end fixtures for complex FFXIV guide generation."""

from __future__ import annotations

import base64
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from assemble_guide import assemble_guide
from build_xivplan_scene import build_scene, write_json
from export_xivplan_steps import export_steps
from validate_xivplan_scene import validate_scene


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "phase8-e2e"
SAMPLE_IMAGE = ROOT / "xivplan-ffxiv-guide" / "assets" / "image-assets" / "samples" / "m6s-animal-icon-256.png"


def party_ring(distance: int = 108) -> list[dict[str, Any]]:
    return [
        {"kind": "party", "role": "MT", "pos": "N", "distance": distance},
        {"kind": "party", "role": "ST", "pos": "S", "distance": distance},
        {"kind": "party", "role": "H1", "pos": "W", "distance": distance},
        {"kind": "party", "role": "H2", "pos": "E", "distance": distance},
        {"kind": "party", "role": "D1", "pos": "NW", "distance": distance + 15},
        {"kind": "party", "role": "D2", "pos": "NE", "distance": distance + 15},
        {"kind": "party", "role": "D3", "pos": "SW", "distance": distance + 15},
        {"kind": "party", "role": "D4", "pos": "SE", "distance": distance + 15},
    ]


def asset_data_url() -> str:
    return "data:image/png;base64," + base64.b64encode(SAMPLE_IMAGE.read_bytes()).decode("ascii")


def case_spread_stack() -> dict[str, Any]:
    return {
        "slug": "four-tower-spread-stack",
        "input": "四塔 + 分摊散开：T/H 负责南北塔，DPS 负责东西塔，塔后 DPS 斜角散开，最后回中八人分摊。",
        "solution": "固定职责比临场按点名换位更稳定：塔位按职能拆组，散开只让 DPS 外扩，读条职业留内圈，最后全员回中。",
        "spec": {
            "name": "Phase 8：四塔分摊散开",
            "style": "king-x-fru",
            "arena": {"preset": "fru-p2"},
            "markerPresets": "all-waymarks",
            "steps": [
                {
                    "title": "1 初始八方",
                    "purpose": "固定预站和标点。",
                    "guide_text": "Boss 中央固定，T/H 十字、DPS 斜角预站。",
                    "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}] + party_ring(),
                },
                {
                    "title": "2 四塔职责",
                    "purpose": "四座二人塔按固定职能处理。",
                    "guide_text": "MT/H1 北塔，ST/H2 南塔，D2/D4 东塔，D1/D3 西塔。",
                    "inherit": True,
                    "objects": [
                        {"kind": "tower", "key": "tn", "pos": "N", "distance": 205, "count": 2, "label": "MT/H1"},
                        {"kind": "tower", "key": "te", "pos": "E", "distance": 205, "count": 2, "label": "D2/D4"},
                        {"kind": "tower", "key": "ts", "pos": "S", "distance": 205, "count": 2, "label": "ST/H2"},
                        {"kind": "tower", "key": "tw", "pos": "W", "distance": 205, "count": 2, "label": "D1/D3"},
                    ],
                },
                {
                    "title": "3 DPS 斜角散开",
                    "purpose": "塔后散开，T/H 保持内圈。",
                    "guide_text": "DPS 去四个斜角，T/H 在内圈等待回中窗口。",
                    "inherit": True,
                    "remove": ["tn", "te", "ts", "tw"],
                    "updates": {
                        "MT": {"pos": "N", "distance": 70},
                        "ST": {"pos": "S", "distance": 70},
                        "H1": {"pos": "W", "distance": 70},
                        "H2": {"pos": "E", "distance": 70},
                        "D1": {"pos": "NW", "distance": 215},
                        "D2": {"pos": "NE", "distance": 215},
                        "D3": {"pos": "SW", "distance": 215},
                        "D4": {"pos": "SE", "distance": 215},
                    },
                    "objects": [
                        {"kind": "circle", "key": "d1", "pos": "NW", "distance": 215, "radius": 50, "label": "D1"},
                        {"kind": "circle", "key": "d2", "pos": "NE", "distance": 215, "radius": 50, "label": "D2"},
                        {"kind": "circle", "key": "d3", "pos": "SW", "distance": 215, "radius": 50, "label": "D3"},
                        {"kind": "circle", "key": "d4", "pos": "SE", "distance": 215, "radius": 50, "label": "D4"},
                    ],
                },
                {
                    "title": "4 回中分摊",
                    "purpose": "散开后统一回中。",
                    "guide_text": "散开判定后全员回中吃八人分摊并复位。",
                    "inherit": True,
                    "remove": ["d1", "d2", "d3", "d4"],
                    "objects": [{"kind": "stack", "key": "stack", "pos": "center", "radius": 76, "count": 8, "label": "八人分摊"}],
                },
            ],
        },
    }


def case_light_rampant() -> dict[str, Any]:
    return {
        "slug": "light-rampant-like",
        "input": "类似 Light Rampant：四名光球、四名塔，连线不能交叉，先外圈诱导，再按东西南北塔处理。",
        "solution": "推荐十字塔 + 斜角光球。光球组只沿外圈顺时针移动半格，塔组内圈就近踩塔，降低连线交叉和记忆成本。",
        "spec": {
            "name": "Phase 8：Light Rampant 类机制",
            "style": "king-x-fru",
            "arena": {"preset": "eden-light"},
            "markerPresets": "all-waymarks",
            "steps": [
                {"title": "1 分组预站", "purpose": "光球组斜角，塔组正点。", "guide_text": "DPS 斜角拿光球，T/H 正点准备塔。", "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}] + party_ring(120)},
                {
                    "title": "2 光球与连线",
                    "purpose": "显示光球组外圈和不可交叉连线。",
                    "guide_text": "DPS 带光球沿外圈同向移动，避免横穿中心。",
                    "inherit": True,
                    "objects": [
                        {"kind": "circle", "key": "orb1", "pos": "NW", "distance": 230, "radius": 32, "color": "#d7f8ff", "label": "光"},
                        {"kind": "circle", "key": "orb2", "pos": "NE", "distance": 230, "radius": 32, "color": "#d7f8ff", "label": "光"},
                        {"kind": "circle", "key": "orb3", "pos": "SW", "distance": 230, "radius": 32, "color": "#d7f8ff", "label": "光"},
                        {"kind": "circle", "key": "orb4", "pos": "SE", "distance": 230, "radius": 32, "color": "#d7f8ff", "label": "光"},
                        {"kind": "arrow", "key": "orb-route-n", "from": "NW", "to": "N", "distance": 220, "arrowStyle": "movement", "endGap": 44},
                        {"kind": "arrow", "key": "orb-route-e", "from": "NE", "to": "E", "distance": 220, "arrowStyle": "movement", "endGap": 44},
                        {"kind": "arrow", "key": "orb-route-s", "from": "SE", "to": "S", "distance": 220, "arrowStyle": "movement", "endGap": 44},
                        {"kind": "arrow", "key": "orb-route-w", "from": "SW", "to": "W", "distance": 220, "arrowStyle": "movement", "endGap": 44},
                    ],
                },
                {
                    "title": "3 正点四塔",
                    "purpose": "塔组就近踩塔。",
                    "guide_text": "T/H 处理正点塔，DPS 外圈等待光球判定。",
                    "inherit": True,
                    "remove": ["orb-route-n", "orb-route-e", "orb-route-s", "orb-route-w"],
                    "objects": [
                        {"kind": "tower", "key": "tower-n", "pos": "N", "distance": 175, "count": 1, "label": "MT"},
                        {"kind": "tower", "key": "tower-e", "pos": "E", "distance": 175, "count": 1, "label": "H2"},
                        {"kind": "tower", "key": "tower-s", "pos": "S", "distance": 175, "count": 1, "label": "ST"},
                        {"kind": "tower", "key": "tower-w", "pos": "W", "distance": 175, "count": 1, "label": "H1"},
                        {"kind": "donut", "pos": "center", "innerRadius": 95, "radius": 270, "color": "#d13438", "opacity": 18},
                    ],
                },
                {
                    "title": "4 回中复位",
                    "purpose": "判定后统一回中。",
                    "guide_text": "光球和塔都判定后，所有人回中准备下一轮。",
                    "inherit": True,
                    "remove": ["tower-n", "tower-e", "tower-s", "tower-w", "orb1", "orb2", "orb3", "orb4"],
                    "objects": [{"kind": "stack", "pos": "center", "radius": 72, "count": 8, "label": "回中"}],
                },
            ],
        },
    }


def case_limit_cut() -> dict[str, Any]:
    return {
        "slug": "hello-world-limit-cut",
        "input": "Hello World / Limit Cut 类：1-8 号顺序处理，奇数去北侧，偶数去南侧，线和地火按顺序诱导。",
        "solution": "用奇偶分层处理：奇数北、偶数南，当前号出列诱导直线和地火，下一号提前半步接位。图上强制分为观察、1-2、3-4、复位四张。",
        "spec": {
            "name": "Phase 8：Hello World / Limit Cut 类机制",
            "style": "king-x-fru",
            "arena": {"preset": "default-circle"},
            "markerPresets": "all-waymarks",
            "steps": [
                {"title": "1 编号观察", "purpose": "八人按编号分奇偶。", "guide_text": "奇数北半场，偶数南半场，先确认自己编号。", "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}] + party_ring(130) + [{"kind": "label", "key": "odd-even-callout", "text": "奇数北 / 偶数南", "pos": [0, 205]}]},
                {
                    "title": "2 1-2 号处理",
                    "purpose": "第一组出列诱导。",
                    "guide_text": "1 号北侧诱导直线，2 号南侧诱导直线，其余按半场避让。",
                    "inherit": True,
                    "objects": [
                        {"kind": "line", "key": "line1", "pos": "N", "distance": 120, "length": 540, "width": 58, "rotation": 90, "opacity": 35},
                        {"kind": "line", "key": "line2", "pos": "S", "distance": 120, "length": 540, "width": 58, "rotation": 90, "opacity": 35},
                        {"kind": "exaflare", "key": "exa1", "pos": "NW", "distance": 190, "rotation": 0, "length": 4},
                        {"kind": "exaflare", "key": "exa2", "pos": "SE", "distance": 190, "rotation": 180, "length": 4},
                    ],
                },
                {
                    "title": "3 3-4 号接位",
                    "purpose": "下一组接替，上一组回避。",
                    "guide_text": "3/4 号接到同侧诱导点，1/2 号沿外圈回队。",
                    "inherit": True,
                    "remove": ["line1", "line2", "exa1", "exa2"],
                    "objects": [
                        {"kind": "line", "key": "line3", "pos": "NE", "distance": 120, "length": 500, "width": 58, "rotation": 45, "opacity": 35},
                        {"kind": "line", "key": "line4", "pos": "SW", "distance": 120, "length": 500, "width": 58, "rotation": 45, "opacity": 35},
                        {"kind": "arrow", "key": "handoff-north", "from": "N", "to": "NE", "distance": 170, "arrowStyle": "movement", "endGap": 48},
                        {"kind": "arrow", "key": "handoff-south", "from": "S", "to": "SW", "distance": 170, "arrowStyle": "movement", "endGap": 48},
                    ],
                },
                {"title": "4 结束复位", "purpose": "顺序处理完成后回到八方。", "guide_text": "后续 5-8 号照同样节奏处理，全部结束后回八方。", "inherit": True, "remove": ["line3", "line4", "handoff-north", "handoff-south"], "objects": [{"kind": "stack", "pos": "center", "radius": 70, "count": 8, "label": "复位"}]},
            ],
        },
    }


def case_fru_rewrite() -> dict[str, Any]:
    return {
        "slug": "fru-p1-rewrite",
        "input": "FRU P1 风格改写：暗光龙诗一段，先观察东西安全，再按近远分散，坦克处理死刑后全员回中。",
        "solution": "沿用 FRU 成品的信息密度：先画观察点，再画安全半场，再画近远散开和坦克死刑。DPS 不穿 Boss，治疗保持中线，坦克死刑单独外拉。",
        "spec": {
            "name": "Phase 8：FRU P1 机制改写",
            "style": "king-x-fru",
            "arena": {"preset": "fru-p1"},
            "markerPresets": "all-waymarks",
            "steps": [
                {"title": "1 观察东西安全", "purpose": "观察分身朝向和安全半场。", "guide_text": "看东西两侧分身，危险半场标红，安全半场提前预站。", "objects": [{"kind": "boss", "key": "boss", "name": "Fatebreaker", "pos": "center"}] + party_ring(110) + [{"kind": "rect", "key": "danger-east", "pos": "E", "distance": 150, "width": 220, "height": 560, "opacity": 28}, {"kind": "polygon", "key": "safe-west", "pos": "W", "distance": 120, "radius": 115, "sides": 4, "color": "#8fd14f", "opacity": 28, "label": "安全", "labelPos": [-212, 88]}]},
                {"title": "2 近远散开", "purpose": "近战内圈、远程外圈。", "guide_text": "近战留 Boss 圈内侧，远程和治疗去外圈，避免穿越危险半场。", "inherit": True, "updates": {"D1": {"pos": "NW", "distance": 85}, "D2": {"pos": "NE", "distance": 85}, "D3": {"pos": "SW", "distance": 210}, "D4": {"pos": "SE", "distance": 210}, "H1": {"pos": "W", "distance": 205}, "H2": {"pos": "E", "distance": 205}}, "objects": [{"kind": "circle", "key": "near-zone", "pos": "NW", "distance": 85, "radius": 42, "label": "近", "labelPos": [-78, 128]}, {"kind": "circle", "key": "far-zone", "pos": "SE", "distance": 210, "radius": 48, "label": "远"}]},
                {"title": "3 双坦死刑外拉", "purpose": "坦克离队处理死刑。", "guide_text": "MT/ST 向南北外拉死刑，其余人保持安全半场，治疗注意覆盖。", "inherit": True, "updates": {"MT": {"pos": "N", "distance": 215}, "ST": {"pos": "S", "distance": 215}}, "objects": [{"kind": "circle", "key": "tb1", "pos": "N", "distance": 205, "radius": 48, "color": "#d13438", "label": "MT", "labelPos": [88, 214]}, {"kind": "circle", "key": "tb2", "pos": "S", "distance": 205, "radius": 48, "color": "#d13438", "label": "ST", "labelPos": [88, -214]}]},
                {"title": "4 回中接下一读条", "purpose": "死刑后复位。", "guide_text": "死刑判定后坦克回中，其余人按原八方复位，准备下一段。", "inherit": True, "remove": ["tb1", "tb2", "danger-east", "safe-west", "near-zone", "far-zone"], "objects": [{"kind": "stack", "pos": "center", "radius": 72, "count": 8, "label": "回中"}]},
            ],
        },
    }


def case_image_asset() -> dict[str, Any]:
    image = asset_data_url()
    return {
        "slug": "image2-animal-asset",
        "input": "需要 image2 特殊素材：M6S 动物点名，四个动物图标出现后按同色去斜角，随后回中分摊。",
        "solution": "将 image2 生成的透明动物 PNG 内嵌为 data URL，保证 `.xivplan` 脱离原图也能显示。图标只作为识别物，不遮挡玩家站位。",
        "spec": {
            "name": "Phase 8：image2 动物素材机制",
            "style": "king-x-fru",
            "arena": {"preset": "default-circle"},
            "markerPresets": "all-waymarks",
            "steps": [
                {"title": "1 动物点名出现", "purpose": "展示本地 PNG / image2 素材内嵌。", "guide_text": "四个动物图标出现在斜角，玩家先按固定八方观察。", "objects": [{"kind": "boss", "key": "boss", "name": "Boss", "pos": "center"}] + party_ring(110) + [{"kind": "image", "key": "animal-nw", "name": "动物", "image": image, "pos": "NW", "distance": 205, "width": 64, "height": 64}, {"kind": "image", "key": "animal-ne", "name": "动物", "image": image, "pos": "NE", "distance": 205, "width": 64, "height": 64}, {"kind": "image", "key": "animal-sw", "name": "动物", "image": image, "pos": "SW", "distance": 205, "width": 64, "height": 64}, {"kind": "image", "key": "animal-se", "name": "动物", "image": image, "pos": "SE", "distance": 205, "width": 64, "height": 64}]},
                {"title": "2 同色斜角集合", "purpose": "按动物图标分组。", "guide_text": "被点名者去对应斜角，未点名者留内圈补位。", "inherit": True, "objects": [{"kind": "tower", "pos": "NW", "distance": 205, "count": 2, "label": "同色"}, {"kind": "tower", "pos": "SE", "distance": 205, "count": 2, "label": "同色"}]},
                {"title": "3 外圈散开判定", "purpose": "动物点名外圈散开。", "guide_text": "点名者在图标旁散开，内圈玩家避开外圈范围。", "inherit": True, "objects": [{"kind": "donut", "pos": "center", "innerRadius": 145, "radius": 275, "opacity": 22}]},
                {"title": "4 回中分摊", "purpose": "判定后回中。", "guide_text": "动物判定结束后全员回中吃分摊，图标素材保留在 .xivplan 内。", "inherit": True, "objects": [{"kind": "stack", "pos": "center", "radius": 74, "count": 8, "label": "八人"}]},
            ],
        },
    }


def guide_for_case(case: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    steps = case["spec"]["steps"]
    return {
        "title": case["spec"]["name"].replace("Phase 8：", ""),
        "summary": case["input"],
        "recommended_solution": case["solution"],
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
            {"role": "MT/ST", "position": "按图示坦克位", "task": "处理坦克职责、死刑或塔位。"},
            {"role": "H1/H2", "position": "按图示治疗位", "task": "优先保证治疗覆盖并参与固定分组。"},
            {"role": "D1-D4", "position": "按图示近远 / 斜角", "task": "处理散开、塔、图标或顺序诱导。"},
        ],
        "common_mistakes": [
            "把观察图和判定图混成同一步，导致移动窗口不清楚。",
            "临场换位时穿过 Boss 或穿过危险半场。",
            "图中箭头方向与口头 call 不一致。"
        ],
        "short_callout": [
            "先看图中观察点，再执行当前 step 的移动。",
            "不穿中心，不交叉线，读条职业优先少动。",
            "每个判定结束都按图示回中或复位。"
        ],
        "mnemonic": "先观察，后移动，判定后复位。",
        "consistency_checks": [
            "输入文本、推荐方案、spec、.xivplan 和攻略正文都已生成。",
            "每个 step 都有对应 PNG，且 manifest 顺序一致。",
            "8 人职责在攻略包中有明确分配。",
        ],
        "unknowns": [],
    }


def write_case(case: dict[str, Any]) -> dict[str, Any]:
    case_dir = ARTIFACT_ROOT / case["slug"]
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "input.md").write_text("# 输入文本\n\n" + case["input"] + "\n\n# 推荐方案\n\n" + case["solution"] + "\n", encoding="utf-8")
    spec_path = case_dir / "spec.json"
    scene_path = case_dir / "scene.xivplan"
    write_json(spec_path, case["spec"])
    scene = build_scene(case["spec"])
    write_json(scene_path, scene)
    errors, counts, object_count = validate_scene(scene)
    if errors:
        raise RuntimeError(f"{case['slug']} invalid scene: {errors}")

    manifest = export_steps(scene_path, case_dir, scale_factor=1)
    guide = guide_for_case(case, manifest)
    guide_path = case_dir / "guide.json"
    write_json(guide_path, guide)
    outputs = assemble_guide(guide_path, case_dir / "guide-package", strict_images=True)

    return {
        "slug": case["slug"],
        "steps": len(scene["steps"]),
        "objects": object_count,
        "types": dict(sorted(counts.items())),
        "paths": {
            "input": str(case_dir / "input.md"),
            "spec": str(spec_path),
            "scene": str(scene_path),
            "manifest": str(case_dir / "manifest.json"),
            "guide_package": str(case_dir / "guide-package"),
            "markdown": str(outputs["markdown"]),
            "docx": str(outputs["docx"]),
            "pdf": str(outputs["pdf"]),
        },
    }


def main() -> int:
    cases = [case_spread_stack(), case_light_rampant(), case_limit_cut(), case_fru_rewrite(), case_image_asset()]
    results = []
    for case in cases:
        results.append(write_case(case))

    report_lines = [
        "# Phase 8 End-to-End 联调报告",
        "",
        "## 验收范围",
        "",
        "- 输入文本",
        "- 推荐方案",
        "- scene spec JSON",
        "- `.xivplan` 生成与结构校验",
        "- 每个 step PNG 导出与 manifest",
        "- Markdown / DOCX / PDF 攻略包生成",
        "",
        "## Case 结果",
        "",
    ]
    for result in results:
        report_lines.extend(
            [
                f"### {result['slug']}",
                "",
                f"- steps: {result['steps']}",
                f"- objects: {result['objects']}",
                f"- object types: `{json.dumps(result['types'], ensure_ascii=False)}`",
                f"- input: `{result['paths']['input']}`",
                f"- spec: `{result['paths']['spec']}`",
                f"- scene: `{result['paths']['scene']}`",
                f"- png manifest: `{result['paths']['manifest']}`",
                f"- guide package: `{result['paths']['guide_package']}`",
                "",
            ]
        )
    report_lines.extend(
        [
            "## XivPlan 打开显示",
            "",
            "这些 case 的 `scene.xivplan` 均为普通 XivPlan scene JSON，并已通过 `validate_xivplan_scene.py` 的结构校验。"
            "本地 XivPlan UI 显示检查记录见 `artifacts/phase8-e2e/xivplan-ui-check.md`。",
            "",
        ]
    )
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_ROOT / "phase8-e2e-report.md").write_text("\n".join(report_lines), encoding="utf-8")
    (ARTIFACT_ROOT / "phase8-e2e-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {ARTIFACT_ROOT / 'phase8-e2e-report.md'}")
    print(f"cases: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
