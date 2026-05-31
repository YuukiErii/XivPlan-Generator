# Solution Candidate Format

## Purpose

Use `scripts/score_solution_candidates.py` after decomposing a mechanic and before generating the final XivPlan scene. Codex still proposes the candidate strategies; the script makes the comparison reproducible and rejects unsafe candidates before soft scoring.

The optimizer is intentionally separate from `build_xivplan_scene.py`. Phase 4 compares strategy shapes. Phase 5 turns the selected strategy into a richer multi-step scene spec.

## Command

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\score_solution_candidates.py `
  xivplan-ffxiv-guide\assets\optimization\spread-stack-candidates.json `
  --json-out artifacts\solution-scores\spread-stack-scores.json `
  --markdown-out artifacts\solution-scores\spread-stack-report.md
```

Phase 12 can now generate and score candidates from parsed IR:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\plan_solution_candidates.py `
  --mechanic-ir artifacts\parsed-mechanics\four-tower-spread-stack\mechanic-ir.json `
  --timeline-ir artifacts\parsed-mechanics\four-tower-spread-stack\timeline-ir.json `
  -o artifacts\solution-planning\four-tower-spread-stack\solution-candidates.json
& $py xivplan-ffxiv-guide\scripts\score_solution_candidates.py `
  artifacts\solution-planning\four-tower-spread-stack\solution-candidates.json `
  --json-out artifacts\solution-planning\four-tower-spread-stack\solution-scores.json `
  --markdown-out artifacts\solution-planning\four-tower-spread-stack\solution-report.md
& $py xivplan-ffxiv-guide\scripts\build_spec_from_solution.py `
  artifacts\solution-planning\four-tower-spread-stack\solution-candidates.json `
  --scores artifacts\solution-planning\four-tower-spread-stack\solution-scores.json `
  -o artifacts\solution-planning\four-tower-spread-stack\spec.json
```

For the full Phase 12 acceptance batch:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_phase12_planning.py
& $py xivplan-ffxiv-guide\scripts\run_quality_gate.py artifacts\solution-planning --out-dir artifacts\solution-planning\quality-gates
```

## Bundle Shape

```json
{
  "mechanic": "Mechanic name",
  "description": "What is being compared",
  "boss": {
    "pos": [0, 0],
    "uptime_radius": 125,
    "targetable_duration": 12
  },
  "party": {
    "MT": { "job": "DRK", "tags": ["tank", "uptime"] },
    "D4": { "job": "BLM", "tags": ["caster"] }
  },
  "constraints": {
    "forbid_route_crossing": true
  },
  "budgets": {
    "movement": 32,
    "caster_movement": 12
  },
  "candidates": []
}
```

Use all eight default roles: `MT`, `ST`, `H1`, `H2`, `D1`, `D2`, `D3`, `D4`.

## Candidate Shape

```json
{
  "id": "fixed-clocks",
  "name": "候选 A：固定八方",
  "summary": "Why this strategy exists",
  "tradeoffs": ["Known sacrifice"],
  "safety_checks": [
    { "name": "spread_clearance", "passed": true, "details": "..." }
  ],
  "movements": [
    {
      "role": "D4",
      "from": [55, -55],
      "to": [125, -125],
      "timing": "preposition",
      "duration": 1.0,
      "hold": 0.0,
      "beat": "spread",
      "boss_targetable": true
    }
  ],
  "complexity": {},
  "tolerance": {},
  "communication": {},
  "diagram": {},
  "fight_specific_fit": 5
}
```

## Hard Safety Gate

`safety_gate` must pass before a candidate can be recommended. Use `safety_checks` for mechanic-specific facts:

- all eight players assigned
- tower soak counts match
- stack counts match
- spread clearance is sufficient
- tether endpoint rules are legal
- safe and danger zones do not conflict
- timeline ordering is legal

The optimizer also checks:

- all default roles exist in the party
- movement roles exist
- positions are valid
- routes in the same `beat` do not cross when `forbid_route_crossing` is true

## Movement Model

Each movement has:

- `timing`: `downtime`, `free`, `preposition`, `resolution`, or `cast`
- `duration`: travel time used by uptime estimation
- `hold`: optional time held at the destination
- `boss_targetable`: set false during forced downtime
- `forced`: reduces the soft movement penalty, but does not erase actual uptime loss
- `beat`: groups routes for crossing detection
- `route_check`: set false only when two drawn arrows are intentionally not simultaneous paths

General weighted movement cost is a diagnostic field. The recommendation score uses the dedicated caster-movement component so total weights remain stable.

## Complexity Features

`complexity` controls the `/20` memory score:

| Field | Meaning |
|---|---|
| `live_sorts` | runtime player sorting decisions |
| `role_swaps` | adjacent-beat responsibility changes |
| `exceptions` | rules that override the main pattern |
| `simultaneous_attributes` | properties read at the same time |
| `pattern_reuse` | repeated movement template bonus |
| `fixed_assignments` | stable role assignment bonus |
| `stable_meanings` | stable color, number, or marker meaning bonus |

## Tolerance And Communication Features

`tolerance` controls the `/15` tolerance score:

- `min_margin`
- `crossing_routes`
- `simultaneous_swaps`
- `last_second_adjustments`

`communication` controls the `/10` communication score:

- `callout_words`
- `priority_rules`
- `exception_rules`
- `macro_lines`

## Diagram Features

`diagram` controls the `/10` diagram-clarity score:

- `steps`
- `arrows`
- `crossing_arrows`
- `labels`
- `branches`
- `max_objects_per_step`

## Score Shape

```text
solution_score =
  safety_gate
  + caster_movement_score    / 20
  + melee_uptime_score       / 20
  + memory_score             / 20
  + tolerance_score          / 15
  + communication_score      / 10
  + diagram_clarity_score    / 10
  + fight_specific_fit_score / 5
```

Unsafe candidates keep diagnostic component scores but receive `solution_score: null` and cannot win.

Phase 12 reports also include `details.phase12` with timeline movement distance, cast-window movement distance, reset movement distance, declared safe-area ratio, tower players, and stack players.
