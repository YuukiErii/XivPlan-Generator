#!/usr/bin/env python3
"""Parse natural-language FFXIV mechanic notes into Phase 10 IR files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_ROLES = ["MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"]
TIME_RE = re.compile(r"(?:(P\d+|p\d+|门神|本体)\s*)?(\d{1,2}:\d{2})")
STEP_RE = re.compile(r"^\s*(?:[-*]|\d+[.)、]|Step\s*\d+[:：]?)\s*", re.IGNORECASE)
PHASE_RE = re.compile(r"\b(P\d+|p\d+)\b|第([一二三四五六七八九十\d]+)阶段|门神|本体")


CATEGORY_RULES: list[dict[str, Any]] = [
    {"category": "light-rampant-like", "terms": ["Light Rampant", "光之暴走", "光暴", "光球"], "confidence": 0.82},
    {"category": "hello-world-like", "terms": ["Hello World", "你好世界", "传毒", "补丁"], "confidence": 0.82},
    {"category": "limit-cut-like", "terms": ["Limit Cut", "麻将", "1-8", "1到8", "编号", "顺序处理"], "confidence": 0.82},
    {"category": "tower", "terms": ["塔", "踩塔", "四塔", "二塔", "塔位"], "confidence": 0.86},
    {"category": "stack", "terms": ["分摊", "双分摊", "四人分摊", "八人分摊", "集合"], "confidence": 0.84},
    {"category": "spread", "terms": ["散开", "八方", "近远散开", "时钟位"], "confidence": 0.84},
    {"category": "tether", "terms": ["连线", "拉线", "传线", "线不能交叉", "不交叉"], "confidence": 0.84},
    {"category": "knockback", "terms": ["击退", "防击退", "拉入", "推到"], "confidence": 0.82},
    {"category": "cleave", "terms": ["顺劈", "扇形", "左右刀", "前后刀", "Boss 转向", "转向"], "confidence": 0.78},
    {"category": "in-out", "terms": ["月环", "钢铁", "靠近", "远离", "内外", "外内"], "confidence": 0.8},
    {"category": "line-shape", "terms": ["直线", "十字", "X字", "地火", "射线", "Exaflare", "火龙卷"], "confidence": 0.78},
    {"category": "gaze", "terms": ["背对", "看向", "眼睛", "视线"], "confidence": 0.78},
    {"category": "debuff", "terms": ["颜色", "数字", "倒计时", "正负极", "易伤", "点名"], "confidence": 0.74},
    {"category": "bait", "terms": ["诱导", "最近", "最远", "放地板", "引导"], "confidence": 0.76},
    {"category": "tankbuster", "terms": ["死刑", "换T", "换 T", "双T", "无敌"], "confidence": 0.82},
    {"category": "raidwide", "terms": ["全屏", "AOE", "AoE", "团血", "转场伤害"], "confidence": 0.76},
    {"category": "rotation", "terms": ["顺时针", "逆时针", "旋转", "转场"], "confidence": 0.74},
    {"category": "clone-memory", "terms": ["分身", "镜像", "延迟", "记忆"], "confidence": 0.74},
    {"category": "tile-platform", "terms": ["地板", "平台", "桥", "格子", "落脚点"], "confidence": 0.74},
    {"category": "sequence", "terms": ["运动会", "多轮", "依次", "按顺序", "流程"], "confidence": 0.7},
]

ARENA_PRESET_RULES = [
    {
        "preset": "fru-p1",
        "source": "user-specified",
        "terms": ["fru p1", "fru-p1", "fatebreaker", "e11", "/arena/e11.svg", "雷火剑", "雷火", "死刑", "cyclonic break"],
        "reason": "FRU P1 / Fatebreaker context uses the Eden Promise background.",
    },
    {
        "preset": "eden-light",
        "source": "user-specified",
        "terms": ["light rampant", "light-rampant", "shiva", "e8", "/arena/e8.svg", "光之暴走", "光暴", "冰镜"],
        "reason": "Shiva / Light Rampant-like context uses the Eden Shiva-style background.",
    },
    {
        "preset": "tile-square",
        "source": "user-specified",
        "terms": ["tile square", "tile-square", "square arena", "grid arena", "方形场地", "格子场地", "平台场地", "地板"],
        "reason": "Tile or platform mechanics need a square grid background.",
    },
    {
        "preset": "udm-p1",
        "source": "user-specified",
        "terms": ["udm p1", "udm-p1", "udm phase1", "udm-phase1", "绝妖 p1", "绝妖第一阶段", "绝妖一阶段", "/arena/udm-phase1.png"],
        "reason": "UDM P1 gold references use `/arena/udm-phase1.png`.",
    },
    {
        "preset": "udm-p2",
        "source": "user-specified",
        "terms": ["udm p2", "udm-p2", "udm phase2", "udm-phase2", "绝妖 p2", "绝妖第二阶段", "绝妖二阶段", "/arena/udm-phase2.png"],
        "reason": "UDM P2 gold references use `/arena/udm-phase2.png`.",
    },
    {
        "preset": "udm-p3",
        "source": "user-specified",
        "terms": ["udm p3", "udm-p3", "udm phase3", "udm-phase3", "绝妖 p3", "绝妖第三阶段", "绝妖三阶段", "/arena/udm-phase3.png"],
        "reason": "UDM P3 diagrams should use the local phase-three UDM arena when available.",
    },
    {
        "preset": "ultimate-yokai-star-dance",
        "source": "user-specified",
        "terms": ["ultimate yokai star dance", "yokai star dance", "绝妖星乱舞", "udm", "绝妖"],
        "reason": "Ultimate Yokai Star Dance context uses the phase-specific local UDM arena asset when available.",
    },
    {
        "preset": "omega-o8s",
        "source": "user-specified",
        "terms": ["o8s", "omega", "sigmascape", "kefka", "凯夫卡", "妖星乱舞"],
        "reason": "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays",
    },
    {
        "preset": "default-circle",
        "source": "user-specified",
        "terms": ["default circle", "default-circle", "圆形场地", "普通圆形"],
        "reason": "User requested the default circular arena.",
    },
]

CORE_REQUIRED_INPUTS = {
    "tower": [("target_count", "请确认塔数量、每塔人数、可踩塔角色。")],
    "stack": [("target_count", "请确认分摊人数、分摊目标和易伤规则。")],
    "spread": [("target_count", "请确认点名人数、散开半径和固定/随机规则。")],
    "tether": [("targeting_rule", "请确认连线端点、长度条件、是否可交叉或传线。")],
    "knockback": [("positioning", "请确认击退源、距离、防击退是否合法和落点。")],
    "cleave": [("positioning", "请确认顺劈来源、面向锁定时机和安全侧。")],
    "in-out": [("order", "请确认钢铁/月环顺序和安全半径。")],
    "limit-cut-like": [("order", "请确认编号赋予、处理顺序和等待区。")],
    "hello-world-like": [("order", "请确认 debuff 家族、持续时间和传递规则。")],
    "light-rampant-like": [("eligibility", "请确认光球/塔/连线玩家分组和判定顺序。")],
}

UNCERTAIN_TERMS = ["暂不确定", "不确定", "未知", "待确认", "待验证", "可能", "猜测", "疑似", "TBD", "?"]
POSITION_PATTERNS = [
    r"T/H\s*[^，。；;\n]*",
    r"DPS\s*[^，。；;\n]*",
    r"近战[^，。；;\n]*",
    r"远程[^，。；;\n]*",
    r"治疗[^，。；;\n]*",
    r"坦克[^，。；;\n]*",
    r"东西[^，。；;\n]*",
    r"南北[^，。；;\n]*",
    r"斜角[^，。；;\n]*",
    r"正点[^，。；;\n]*",
    r"回中[^，。；;\n]*",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_phase(value: str | None, fallback: str) -> str:
    if value:
        return value.upper() if value.lower().startswith("p") else value
    return fallback or "unknown"


def detect_phase(text: str, fallback: str = "unknown") -> str:
    match = PHASE_RE.search(text)
    if not match:
        return fallback
    if match.group(1):
        return match.group(1).upper()
    if "门神" in match.group(0):
        return "门神"
    if "本体" in match.group(0):
        return "本体"
    return f"第{match.group(2)}阶段"


def strip_markdown_noise(line: str) -> str:
    line = STEP_RE.sub("", line.strip())
    return line.strip(" \t#")


def split_events(text: str, default_phase: str) -> list[dict[str, Any]]:
    raw_lines = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        raw_lines.append(strip_markdown_noise(line))
    chunks: list[str] = []
    for line in raw_lines:
        if not line or line.startswith("```"):
            continue
        if line.startswith("#"):
            continue
        parts = [part.strip() for part in re.split(r"[；;]\s*", line) if part.strip()]
        chunks.extend(parts or [line])

    events: list[dict[str, Any]] = []
    current_phase = default_phase
    pending_time: str | None = None
    for chunk in chunks:
        phase_in_chunk = detect_phase(chunk, current_phase)
        current_phase = phase_in_chunk
        matches = list(TIME_RE.finditer(chunk))
        if matches:
            for index, match in enumerate(matches):
                start = match.end()
                end = matches[index + 1].start() if index + 1 < len(matches) else len(chunk)
                description = chunk[start:end].strip(" ，。:：")
                time = match.group(2)
                phase = normalize_phase(match.group(1), current_phase)
                current_phase = phase
                if description:
                    events.append({"time": time, "phase": phase, "description": description})
                else:
                    pending_time = time
        else:
            if pending_time:
                events.append({"time": pending_time, "phase": current_phase, "description": chunk})
                pending_time = None
            elif chunk:
                events.append({"time": None, "phase": phase_in_chunk, "description": chunk})

    if not events and text.strip():
        events.append({"time": None, "phase": default_phase, "description": text.strip()})
    return events


def matched_categories(text: str) -> list[dict[str, Any]]:
    lowered = text.lower()
    matches: list[dict[str, Any]] = []
    for rule in CATEGORY_RULES:
        terms = [term for term in rule["terms"] if term.lower() in lowered]
        if terms:
            matches.append({"category": rule["category"], "confidence": rule["confidence"], "matched_terms": terms})
    if len(matches) > 1:
        matches.append({"category": "sequence", "confidence": 0.68, "matched_terms": ["combined mechanic"]})
    dedup: dict[str, dict[str, Any]] = {}
    for match in matches:
        existing = dedup.get(match["category"])
        if existing:
            existing["matched_terms"] = sorted(set(existing["matched_terms"] + match["matched_terms"]))
            existing["confidence"] = max(existing["confidence"], match["confidence"])
        else:
            dedup[match["category"]] = match
    return sorted(dedup.values(), key=lambda item: item["confidence"], reverse=True)


def udm_preset_for_phase(phase: str, text: str = "") -> str:
    haystack = f"{phase} {text}".lower()
    if any(term in haystack for term in ("p3", "phase 3", "phase3", "第三阶段", "三阶段")):
        return "udm-p3"
    if any(term in haystack for term in ("p2", "phase 2", "phase2", "第二阶段", "二阶段")):
        return "udm-p2"
    return "udm-p1"


def udm_arena_reason(preset: str) -> str:
    reasons = {
        "udm-p1": "Ultimate Yokai Star Dance / UDM P1 uses `/arena/udm-phase1.png` from the local gold references.",
        "udm-p2": "Ultimate Yokai Star Dance / UDM P2 uses `/arena/udm-phase2.png` from the local gold references.",
        "udm-p3": "Ultimate Yokai Star Dance / UDM P3 uses the local phase-three UDM arena reference.",
    }
    return reasons.get(preset, reasons["udm-p1"])


def choose_arena_preset(
    text: str,
    encounter_name: str,
    phase: str,
    candidate_categories: list[dict[str, Any]],
) -> dict[str, str]:
    haystack = text.lower()
    for rule in ARENA_PRESET_RULES:
        if any(term.lower() in haystack for term in rule["terms"]):
            preset = rule["preset"]
            reason = rule["reason"]
            if preset == "ultimate-yokai-star-dance":
                preset = udm_preset_for_phase(phase, haystack)
                reason = udm_arena_reason(preset)
            return {
                "preset": preset,
                "source": rule["source"],
                "reason": reason,
            }

    encounter_phase = f"{encounter_name} {phase}".lower()
    if "fru" in encounter_phase and ("p1" in encounter_phase or "phase 1" in encounter_phase):
        return {
            "preset": "fru-p1",
            "source": "mechanic-inferred",
            "reason": "Encounter and phase indicate FRU P1.",
        }
    if any(term in encounter_phase for term in ("ultimate yokai", "yokai star", "udm", "绝妖")):
        preset = udm_preset_for_phase(phase, encounter_phase)
        return {
            "preset": preset,
            "source": "mechanic-inferred",
            "reason": udm_arena_reason(preset),
        }
    if any(term in encounter_phase for term in ("o8s", "omega", "kefka", "sigmascape")):
        return {
            "preset": "omega-o8s",
            "source": "mechanic-inferred",
            "reason": "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays",
        }

    categories = {item["category"] for item in candidate_categories}
    if "light-rampant-like" in categories:
        return {
            "preset": "eden-light",
            "source": "mechanic-inferred",
            "reason": "Detected a Light Rampant-like mechanic.",
        }
    if "tile-platform" in categories:
        return {
            "preset": "tile-square",
            "source": "mechanic-inferred",
            "reason": "Detected tile or platform arena mechanics.",
        }

    return {
        "preset": "default-circle",
        "source": "default-fallback",
        "reason": "No explicit arena instruction or strong encounter/category signal was found.",
    }


def extract_participants(text: str) -> list[str]:
    participants: list[str] = []
    patterns = {
        "T/H": r"\bT/H\b|坦克|治疗",
        "DPS": r"\bDPS\b|近战|远程",
        "MT": r"\bMT\b",
        "ST": r"\bST\b",
        "H1": r"\bH1\b",
        "H2": r"\bH2\b",
        "D1": r"\bD1\b",
        "D2": r"\bD2\b",
        "D3": r"\bD3\b",
        "D4": r"\bD4\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            participants.append(label)
    return participants or ["unknown"]


def extract_positioning(text: str) -> list[str]:
    requirements: list[str] = []
    for pattern in POSITION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(0).strip(" ，。；;")
            if value and value not in requirements:
                requirements.append(value)
    return requirements


def targeting_rule(text: str, categories: list[str]) -> str:
    if any(term in text for term in ("固定", "固定站位", "固定职责")):
        return "fixed"
    if any(term in text for term in ("T/H", "DPS", "坦克", "治疗", "近战", "远程")):
        return "role-based"
    if any(term in text for term in ("颜色", "数字", "倒计时", "点名")):
        return "debuff-based"
    if any(category in categories for category in ("limit-cut-like",)):
        return "number-based"
    if any(term in text for term in ("随机", "随机点名")):
        return "random"
    if any(term in text for term in UNCERTAIN_TERMS):
        return "source-unclear"
    return "unknown"


def party_constraints(text: str) -> dict[str, Any]:
    constraints = {
        "roles": DEFAULT_ROLES,
        "melee_uptime": "not-specified",
        "caster_movement": "not-specified",
        "custom_positions": [],
        "notes": [],
    }
    if "近战" in text and any(term in text for term in ("不离", "打到", "uptime", "少动")):
        constraints["melee_uptime"] = "prefer"
        constraints["notes"].append("近战尽量保 uptime")
    if any(term in text for term in ("读条", "法系", "黑魔", "召唤", "赤魔")) and any(term in text for term in ("少动", "不动", "移动")):
        constraints["caster_movement"] = "minimize"
        constraints["notes"].append("读条职业移动需要最小化")
    for keyword in ("固定队", "野队", "宏", "自定义"):
        if keyword in text:
            constraints["notes"].append(keyword)
    return constraints


def add_unknown(
    unknowns: list[dict[str, Any]],
    scope: str,
    kind: str,
    text: str,
    question: str,
    severity: str = "important",
) -> str:
    existing = next((item for item in unknowns if item["scope"] == scope and item["kind"] == kind and item["text"] == text), None)
    if existing:
        return existing["id"]
    unknown_id = f"u{len(unknowns) + 1:03d}"
    unknowns.append(
        {
            "id": unknown_id,
            "scope": scope,
            "kind": kind,
            "text": text,
            "question": question,
            "severity": severity,
        }
    )
    return unknown_id


def explicit_unknowns(text: str, scope: str, unknowns: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    clauses = [part.strip() for part in re.split(r"[，。；;\n]", text) if part.strip()]
    for clause in clauses:
        if any(term in clause for term in UNCERTAIN_TERMS):
            kind = "targeting_rule" if "点名" in clause else "other"
            refs.append(
                add_unknown(
                    unknowns,
                    scope,
                    kind,
                    clause,
                    "请补充或验证这条机制信息。",
                    "blocking" if kind == "targeting_rule" else "important",
                )
            )
    return refs


def missing_input_unknowns(categories: list[str], text: str, scope: str, unknowns: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for category in categories:
        for kind, question in CORE_REQUIRED_INPUTS.get(category, []):
            if kind == "target_count" and re.search(r"\d|一|二|两|三|四|五|六|七|八|双", text):
                continue
            if kind == "order" and any(term in text for term in ("先", "后", "顺序", "依次", "1-8", "1到8")):
                continue
            if kind == "positioning" and extract_positioning(text):
                continue
            if kind == "targeting_rule" and targeting_rule(text, categories) not in {"unknown", "source-unclear"}:
                continue
            refs.append(add_unknown(unknowns, scope, kind, f"{category} missing {kind}", question, "important"))
    return refs


def movement_window(text: str) -> str:
    if any(term in text for term in ("预站", "提前", "先去")):
        return "preposition"
    if any(term in text for term in ("读条", "判定前", "期间")):
        return "during_cast"
    if any(term in text for term in ("判定后", "结束后", "回中", "复位")):
        return "after_resolution"
    return "unknown"


def reset_window(text: str) -> str:
    if any(term in text for term in ("回中", "复位", "回原位")):
        return "explicit"
    if any(term in text for term in ("后散开", "后集合", "下一")):
        return "implicit"
    return "unknown"


def short_name(text: str, categories: list[str]) -> str:
    cleaned = re.sub(r"^[，。:：\s]+", "", text)
    chunks = [part.strip() for part in re.split(r"[，。]", cleaned) if part.strip()]
    if chunks:
        return chunks[0][:24]
    return categories[0] if categories else "unclassified"


def parse_text(
    text: str,
    encounter_name: str = "unknown",
    phase: str = "unknown",
    version: str = "v0.1-draft",
    source: str = "user-input",
) -> dict[str, Any]:
    events_raw = split_events(text, phase)
    unknowns: list[dict[str, Any]] = []
    mechanics: list[dict[str, Any]] = []
    timeline_events: list[dict[str, Any]] = []
    category_events: dict[str, dict[str, Any]] = {}

    for index, raw in enumerate(events_raw, start=1):
        event_id = f"e{index:03d}"
        event_text = raw["description"]
        category_matches = matched_categories(event_text)
        categories = [item["category"] for item in category_matches] or ["unclassified"]
        unknown_refs = explicit_unknowns(event_text, event_id, unknowns)
        unknown_refs.extend(missing_input_unknowns(categories, event_text, event_id, unknowns))

        mechanic_id = f"m{index:03d}"
        mechanic = {
            "id": mechanic_id,
            "name": short_name(event_text, categories),
            "source_text": event_text,
            "primary_category": categories[0],
            "categories": categories,
            "participants": extract_participants(event_text),
            "targeting_rule": targeting_rule(event_text, categories),
            "positioning_requirements": extract_positioning(event_text),
            "failure_conditions": failure_conditions(categories, unknown_refs),
            "timeline_event_ids": [event_id],
            "confidence": "medium" if category_matches else "low",
            "unknown_refs": sorted(set(unknown_refs)),
        }
        mechanics.append(mechanic)
        timeline_events.append(
            {
                "id": event_id,
                "time": raw["time"],
                "phase": raw["phase"],
                "cast": None,
                "description": event_text,
                "mechanic_ids": [mechanic_id],
                "categories": categories,
                "movement_window": movement_window(event_text),
                "reset_window": reset_window(event_text),
                "unknown_refs": sorted(set(unknown_refs)),
            }
        )
        for match in category_matches:
            entry = category_events.setdefault(
                match["category"],
                {"category": match["category"], "confidence": 0.0, "matched_terms": set(), "timeline_event_ids": []},
            )
            entry["confidence"] = max(entry["confidence"], match["confidence"])
            entry["matched_terms"].update(match["matched_terms"])
            entry["timeline_event_ids"].append(event_id)

    candidate_categories = [
        {
            "category": entry["category"],
            "confidence": round(entry["confidence"], 2),
            "matched_terms": sorted(entry["matched_terms"]),
            "timeline_event_ids": sorted(set(entry["timeline_event_ids"])),
        }
        for entry in category_events.values()
    ]
    candidate_categories.sort(key=lambda item: item["confidence"], reverse=True)

    context_phase = phase if phase != "unknown" else (timeline_events[0]["phase"] if timeline_events else "unknown")
    arena_selection = choose_arena_preset(text, encounter_name, context_phase, candidate_categories)
    mechanic_ir = {
        "schema_version": "mechanic-ir/v0.1",
        "encounter_context": {
            "encounter_name": encounter_name,
            "phase": context_phase,
            "version": version,
            "source": source,
            "confidence": "draft" if unknowns else "medium",
        },
        "arena_selection": arena_selection,
        "party_constraints": party_constraints(text),
        "mechanics": mechanics,
        "candidate_categories": candidate_categories,
        "unknowns": unknowns,
    }
    timeline_ir = {
        "schema_version": "timeline-ir/v0.1",
        "encounter_context": mechanic_ir["encounter_context"],
        "arena_selection": arena_selection,
        "events": timeline_events,
    }
    return {
        "mechanic_ir": mechanic_ir,
        "timeline_ir": timeline_ir,
        "candidate_categories": candidate_categories,
        "unknowns": unknowns,
    }


def failure_conditions(categories: list[str], unknown_refs: list[str]) -> list[str]:
    failures: list[str] = []
    if "tower" in categories:
        failures.append("塔人数、资格或分组错误会导致漏踩/抢塔")
    if "stack" in categories:
        failures.append("分摊人数或易伤规则不明会导致减员")
    if "spread" in categories:
        failures.append("散开半径或点名人数不明会导致重叠")
    if "tether" in categories:
        failures.append("连线路径交叉或长度不足可能导致失败")
    if "knockback" in categories:
        failures.append("击退距离或落点错误会导致出界")
    if "cleave" in categories:
        failures.append("面向或安全侧判断错误会导致顺劈命中")
    if unknown_refs:
        failures.append("存在未确认信息，不能把草案当作最终打法")
    return failures or ["未分类机制需要人工复核"]


def render_unknowns(unknowns: list[dict[str, Any]]) -> str:
    lines = ["# Unknowns", ""]
    if not unknowns:
        lines.append("- 无显式未知点；仍建议按实战录像/宏确认。")
        return "\n".join(lines) + "\n"
    for item in unknowns:
        lines.extend(
            [
                f"## {item['id']} {item['kind']}",
                "",
                f"- scope: `{item['scope']}`",
                f"- severity: `{item['severity']}`",
                f"- text: {item['text']}",
                f"- question: {item['question']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_report(parsed: dict[str, Any], input_path: Path | None) -> str:
    mechanic_ir = parsed["mechanic_ir"]
    timeline_ir = parsed["timeline_ir"]
    lines = [
        "# Mechanic Parse Report",
        "",
        f"- input: `{input_path}`" if input_path else "- input: inline text",
        f"- encounter: {mechanic_ir['encounter_context']['encounter_name']}",
        f"- phase: {mechanic_ir['encounter_context']['phase']}",
        f"- mechanics: {len(mechanic_ir['mechanics'])}",
        f"- timeline events: {len(timeline_ir['events'])}",
        f"- unknowns: {len(mechanic_ir['unknowns'])}",
        f"- arena: {mechanic_ir.get('arena_selection', {}).get('preset', 'unknown')} ({mechanic_ir.get('arena_selection', {}).get('source', 'unknown')})",
        "",
        "## Timeline",
        "",
        "| Event | Time | Phase | Categories | Description |",
        "|---|---|---|---|---|",
    ]
    for event in timeline_ir["events"]:
        lines.append(
            "| {id} | {time} | {phase} | {cats} | {desc} |".format(
                id=event["id"],
                time=event["time"] or "-",
                phase=event["phase"],
                cats=", ".join(event["categories"]),
                desc=event["description"].replace("|", "\\|"),
            )
        )
    lines.extend(["", "## Candidate Categories", ""])
    if parsed["candidate_categories"]:
        for item in parsed["candidate_categories"]:
            terms = ", ".join(item["matched_terms"])
            lines.append(f"- `{item['category']}` confidence={item['confidence']} terms={terms}")
    else:
        lines.append("- none")
    lines.extend(["", "## Unknown Summary", ""])
    if mechanic_ir["unknowns"]:
        for item in mechanic_ir["unknowns"]:
            lines.append(f"- `{item['id']}` {item['kind']}: {item['question']}")
    else:
        lines.append("- 无显式未知点。")
    return "\n".join(lines) + "\n"


def write_outputs(parsed: dict[str, Any], output_dir: Path, input_text: str, input_path: Path | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "input.md").write_text(input_text.rstrip() + "\n", encoding="utf-8")
    write_json(output_dir / "mechanic-ir.json", parsed["mechanic_ir"])
    write_json(output_dir / "timeline-ir.json", parsed["timeline_ir"])
    write_json(output_dir / "candidate-categories.json", parsed["candidate_categories"])
    (output_dir / "unknowns.md").write_text(render_unknowns(parsed["unknowns"]), encoding="utf-8")
    (output_dir / "parse-report.md").write_text(render_report(parsed, input_path), encoding="utf-8")


def slug_from_path(path: Path) -> str:
    name = path.name
    for suffix in (".input.md", ".md", ".txt"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse FFXIV mechanic notes into mechanic/timeline IR.")
    parser.add_argument("input", type=Path, help="Input Markdown/text file")
    parser.add_argument("-o", "--output-dir", type=Path, help="Output directory")
    parser.add_argument("--encounter-name", default="unknown", help="Encounter name")
    parser.add_argument("--phase", default="unknown", help="Default phase label")
    parser.add_argument("--version", default="v0.1-draft", help="IR version label")
    parser.add_argument("--source", default="user-input", help="Input source label")
    args = parser.parse_args()

    try:
        text = read_text(args.input)
        output_dir = args.output_dir or Path("artifacts") / "parsed-mechanics" / slug_from_path(args.input)
        parsed = parse_text(text, args.encounter_name, args.phase, args.version, args.source)
        write_outputs(parsed, output_dir, text, args.input)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {output_dir}")
    print(f"mechanics: {len(parsed['mechanic_ir']['mechanics'])}")
    print(f"timeline events: {len(parsed['timeline_ir']['events'])}")
    print(f"unknowns: {len(parsed['unknowns'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
