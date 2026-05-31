---
name: xivplan-ffxiv-guide
description: Create Chinese FFXIV/FF14 raid guide content from XivPlan diagrams, .xivplan files, screenshots, or written mechanic descriptions. Use when converting mechanics into XivPlan drawing instructions, writing complete or short Chinese guide text, localizing English/Japanese strategies for CN players, generating role/position/tower/spread/stack/knockback/tether diagrams, or checking consistency between XivPlan visuals and guide text.
---

# FFXIV XivPlan Guide

## Core Workflow

Use Simplified Chinese by default. Produce practical raid-guide output that a CN static or pickup group can execute.

1. Triage the input:
   - Written mechanic description: decompose the mechanic, then draft XivPlan drawing instructions and guide text.
   - XivPlan screenshot or described diagram: identify visible objects, directions, roles, and sequence before writing.
   - `.xivplan` file: treat it as JSON, inspect `arena`, `steps`, and `objects`; use `scripts/validate_xivplan_scene.py` after edits.
   - EN/JP strategy text: localize into CN FF14 terms and mark uncertain translations or missing mechanics.
2. Build a diagram plan before prose:
   - Name each figure by purpose, not only by order.
   - Define arena, direction markers, boss/enemy placement, player positions, AoE objects, arrows/pathing, text labels, and layer order.
   - Use XivPlan scene coordinates when concrete files are needed: center is `(0,0)`, `x` positive east, `y` positive north.
3. Write the guide:
   - Keep mechanics, role assignments, movement timing, and reset points separate.
   - Always include a full version and a short team-callout version unless the user asks for one format only.
   - Do not invent boss mechanics. If information is missing, make a clearly labeled assumption and add "需要确认的点".
4. Run a consistency pass:
   - Check direction, role, player count, stack/spread/tower responsibility, arrow direction, tether endpoints, and reset wording.
   - If a contradiction is found, report the issue and provide a corrected version.

## References

Load only the reference needed for the task:

- `references/style-and-terms.md`: CN terms, role defaults, direction/marker conventions, and writing style.
- `references/xivplan-scene-format.md`: local XivPlan JSON schema, object fields, coordinates, and file handling.
- `references/guide-output-templates.md`: full guide, XivPlan instruction, short callout, and consistency-check templates.
- `references/examples.md`: tower, spread/stack, knockback, and tether examples for style calibration.

Use `assets/templates/*.md` as copyable output templates when creating reusable artifacts for the user. Use `assets/examples/tower-four-card-example.xivplan` as a minimal valid scene example when a concrete `.xivplan` reference is useful.

For concrete diagram files, create a compact mechanic spec JSON and run `scripts/build_xivplan_scene.py` to generate a `.xivplan` draft. Sample specs live in `assets/specs/`.

## Default Output

For a complete guide request, output:

1. `机制名`
2. `一句话概括`
3. `XivPlan 绘图指令`
4. `正式攻略文案`
5. `职能分工`
6. `常见失误`
7. `队内速记版`
8. `口诀`
9. `图文一致性检查`
10. `需要确认的点` if any assumptions remain

For a short-callout request, output only the minimum actionable rules, role assignments, and mnemonic.

## XivPlan Rules

When generating object-level instructions:

- Prefer stable role labels: MT, ST, H1, H2, D1, D2, D3, D4.
- Default eight-way role positions are MT north, ST south, H1 west, H2 east, D1 northwest, D2 northeast, D3 southwest, D4 southeast; override with user/team preferences.
- Use `A/B/C/D` for cardinal markers by default: A north, B east, C south, D west; use `1/2/3/4` for intercards when needed.
- In concrete `.xivplan` JSON, prefer these object types:
  - `party` for players, `enemy` for boss/adds, `tower` for towers, `stack` for stacks, `circle` for spread or danger circles, `line`/`cone`/`donut`/`arc` for AoEs, `arrow` for movement, `tether` for links, `text` for labels.
- Keep scene-wide object IDs unique across all steps.
- Validate generated or edited `.xivplan` JSON with:

```bash
python scripts/validate_xivplan_scene.py path/to/file.xivplan
```

If the local Windows `python` alias is broken, use the bundled Codex Python executable.

When asked to create a `.xivplan` file from a mechanic, use:

```bash
python xivplan-ffxiv-guide/scripts/build_xivplan_scene.py xivplan-ffxiv-guide/assets/specs/tower-cardinals.spec.json -o artifacts/generated-xivplan/tower-cardinals.xivplan
python xivplan-ffxiv-guide/scripts/validate_xivplan_scene.py artifacts/generated-xivplan/tower-cardinals.xivplan
```

For new mechanics, first draft a spec JSON with `name`, `arena`, `steps`, and object entries such as `boss`, `party`, `tower`, `stack`, `circle`, `safe_circle`, `knockback`, `arrow`, `tether`, and `label`.

## Quality Gate

Before finalizing, verify:

- Every figure has a purpose and explains what changed from the previous figure.
- Every role knows where to stand, when to move, and where to reset.
- Direction words and XivPlan coordinates agree.
- Stack/spread/tower/tether mechanics state exact participants or a labeled assumption.
- The short version does not contradict the full version.
- Uncertain fight facts are not presented as confirmed.
