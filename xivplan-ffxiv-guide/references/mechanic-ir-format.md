# Mechanic IR Format

## Purpose

Phase 10 introduces a traceable intermediate representation for natural-language FFXIV mechanic notes. The IR is intentionally conservative: it records what the input says, identifies likely mechanic categories, and lists missing facts instead of inventing encounter rules.

The parser writes two JSON files:

- `mechanic-ir.json`: encounter context, party constraints, mechanics, category candidates, and unknowns.
- `timeline-ir.json`: ordered timeline events with movement and reset windows.

It also writes `unknowns.md`, `candidate-categories.json`, and `parse-report.md`.

## `mechanic-ir.json`

```json
{
  "schema_version": "mechanic-ir/v0.1",
  "encounter_context": {
    "encounter_name": "Ultimate Yokai Star Dance",
    "phase": "P1",
    "version": "v0.1-draft",
    "source": "user-input",
    "confidence": "draft"
  },
  "party_constraints": {
    "roles": ["MT", "ST", "H1", "H2", "D1", "D2", "D3", "D4"],
    "melee_uptime": "prefer",
    "caster_movement": "minimize",
    "custom_positions": [],
    "notes": []
  },
  "mechanics": [
    {
      "id": "m001",
      "name": "四塔",
      "source_text": "P1 00:18 四塔，T/H 南北，DPS 东西。",
      "primary_category": "tower",
      "categories": ["tower"],
      "participants": ["T/H", "DPS"],
      "targeting_rule": "role-based",
      "positioning_requirements": ["T/H 南北", "DPS 东西"],
      "failure_conditions": ["tower count or assigned players may be wrong if eligibility is unconfirmed"],
      "timeline_event_ids": ["e001"],
      "confidence": "medium",
      "unknown_refs": []
    }
  ],
  "candidate_categories": [
    {
      "category": "tower",
      "confidence": 0.85,
      "matched_terms": ["四塔"],
      "timeline_event_ids": ["e001"]
    }
  ],
  "unknowns": [
    {
      "id": "u001",
      "scope": "e003",
      "kind": "targeting_rule",
      "text": "点名规则暂不确定",
      "question": "请确认点名目标、数量、随机或固定规则。",
      "severity": "blocking"
    }
  ]
}
```

### Required Fields

`encounter_context`

- `encounter_name`: fight, dungeon, or placeholder name.
- `phase`: phase label such as `P1`, `P2`, `门神`, or `unknown`.
- `version`: output version, for example `v0.1-draft`.
- `source`: source label such as `user-input`, `macro`, `log-notes`, or `fixture`.
- `confidence`: `draft`, `partial`, `medium`, or `high`.

`timeline`

Timeline data lives in `timeline-ir.json`, but each mechanic must link to one or more event IDs. Events include:

- `time`: timestamp string such as `00:18`, or `null` when not provided.
- `phase`: phase label active at that event.
- `cast`: cast or mechanic name if a cast was mentioned.
- `description`: original event text.
- `mechanic_ids`: linked mechanics.
- `categories`: detected mechanic categories.
- `movement_window`: `preposition`, `during_cast`, `after_resolution`, or `unknown`.
- `reset_window`: `explicit`, `implicit`, or `unknown`.
- `unknown_refs`: unknown IDs raised by this event.

`mechanics`

- `primary_category`: the main category used for downstream planning.
- `categories`: all matched categories, including combined shapes such as `limit-cut-like`, `hello-world-like`, or `light-rampant-like`.
- `participants`: extracted role groups, target groups, or `unknown`.
- `targeting_rule`: `fixed`, `role-based`, `debuff-based`, `number-based`, `random`, `source-unclear`, or `unknown`.
- `positioning_requirements`: concrete standing, split, direction, or reset requirements from the text.
- `failure_conditions`: conservative risk statements for missing or unsafe rules.
- `unknown_refs`: unknown IDs relevant to this mechanic.

`party_constraints`

- `melee_uptime`: `hard`, `prefer`, or `not-specified`.
- `caster_movement`: `minimize`, `normal`, or `not-specified`.
- `custom_positions`: user/static-specific position rules.
- `notes`: other constraints such as “野队宏优先” or “固定队可换位”.

`unknowns`

Unknowns must be explicit when the input contains uncertainty or when a detected mechanic lacks critical inputs. Use:

- `kind`: `targeting_rule`, `target_count`, `order`, `positioning`, `timing`, `eligibility`, `damage`, `source`, or `other`.
- `severity`: `blocking`, `important`, or `minor`.
- `question`: the next user-facing question or validation item.

## Category Vocabulary

Use core taxonomy names from `mechanic-taxonomy.md` where possible:

- `raidwide`
- `tankbuster`
- `spread`
- `stack`
- `tower`
- `cleave`
- `in-out`
- `line-shape`
- `knockback`
- `gaze`
- `tether`
- `debuff`
- `bait`
- `pass`
- `rotation`
- `clone-memory`
- `sequence`
- `tile-platform`
- `adds-priority`

Combined or analogy categories may be added as suffix labels:

- `limit-cut-like`
- `hello-world-like`
- `light-rampant-like`
- `exaflare-like`

Downstream scripts should treat combined categories as hints and still inspect the core categories.
