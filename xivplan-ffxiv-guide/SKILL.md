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

## One-Command Guide Pipeline

When the user provides a new mechanic flow Markdown and wants a complete guide package, prefer the full pipeline entrypoint:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py input.md `
  --encounter-name "Encounter" `
  --phase P1 `
  --version v0.1-draft `
  --output-dir artifacts\full-guide-pipeline\my-case
```

This runs natural-language parsing, similar-mechanic search, candidate planning and scoring, spec generation, `.xivplan` generation, step PNG export, Markdown / DOCX / PDF guide assembly, and the quality gate. Use `--force` only when intentionally rerunning the same output folder.

## New Encounter Notes Workflow

For fresh-fight information:

1. Write or update the source Markdown first. It should include timeline notes, screenshot descriptions, oral calls, and explicit unknowns.
2. Run `scripts/run_full_guide_pipeline.py` with `--encounter-name`, `--phase`, `--version`, and `--output-dir`.
3. Inspect `parsed-ir/unknowns.md`, `knowledge-matches/knowledge-search.md`, `solution-candidates/solution-report.md`, and `quality-report/quality-report.md`.
4. Keep guide wording draft-scoped until observed rules are confirmed.

## Similar-Mechanic Rewrite Workflow

When the input says "类似 XXXX 机制":

1. Run the full pipeline when an artifact is needed, or run `scripts/search_mechanic_knowledge.py` for a quick analogy report.
2. If the user asks for adaptation details, run `scripts/adapt_similar_mechanic.py`.
3. In the answer and artifacts, separate transferable principles from positions or timings that must not be copied.
4. Feed the analogy result into candidate planning; old-fight positions are evidence, not final assignments.

## Ultimate Yokai Star Dance Workflow

For 绝妖星乱舞 / Ultimate Yokai Star Dance progression, use the dedicated versioned workspace:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  artifacts\ultimate-yokai-star-dance\raw-notes\p1-draft-notes.md `
  --ultimate-yokai-star-dance `
  --version v0.1-draft
```

For observed updates, create or edit a new raw notes file, then use a new version label:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  artifacts\ultimate-yokai-star-dance\raw-notes\p1-observed-notes.md `
  --ultimate-yokai-star-dance `
  --version v0.2-observed `
  --previous-version v0.1-draft
```

The shortcut preserves previous outputs, writes per-version folders under `artifacts/ultimate-yokai-star-dance/`, and appends `change-log.md`. Use `--force` only for an intentional same-version rerun.

## Quality And Release Workflow

Before handoff or release:

1. Confirm the pipeline produced `.xivplan`, exported PNGs, Markdown, DOCX, PDF, candidate report, analogy report, and unknown/risk files.
2. Confirm `quality-report.md` says `PASS`.
3. For progression versions, confirm `change-log.md` lists new confirmations, disproved assumptions, and remaining unknowns.
4. Never publish `v0.x` output as final public strategy unless the user explicitly says the information is verified.

## References

Load only the reference needed for the task:

- `references/style-and-terms.md`: CN terms, role defaults, direction/marker conventions, and writing style.
- `references/mechanic-taxonomy.md`: base mechanic categories, required inputs, combined shapes, and unknowns checklist.
- `references/positioning-patterns.md`: reusable clocks, light parties, pairs, towers, priorities, relative-north, bait, tether, timeline, and tile layouts.
- `references/mechanic-aliases.md`: CN/EN/common shorthand alias map for similar-mechanic lookup.
- `references/encounters/index.md`: analogy lookup index for TEA, DSR, TOP, FRU, Omega, Eden, Pandaemonium, and Arcadion mechanic cards.
- `references/encounters/coverage-audit.md`: floor-by-floor Savage coverage boundary and live-tier refresh notes.
- `references/xivplan-scene-format.md`: local XivPlan JSON schema, object fields, coordinates, and file handling.
- `references/xivplan-style-guide.md`: KING X golden-sample visual baseline, diagram sizes, colors, layering, and step decomposition.
- `references/image-asset-workflow.md`: image2 / local PNG asset generation, validation, manifest placement, and data-URL injection workflow.
- `references/solution-optimization.md`: candidate comparison rules for safety, movement, melee uptime, memory cost, and diagram clarity.
- `references/solution-candidate-format.md`: executable candidate-bundle JSON format and Phase 4 scoring command.
- `references/future-ultimate-workflow.md`: version policy and iteration rules for new ultimate progression work.
- `references/guide-json-format.md`: Phase 6 guide package schema and commands for Markdown / DOCX / PDF assembly.
- `references/guide-output-templates.md`: full guide, XivPlan instruction, short callout, and consistency-check templates.
- `references/examples.md`: tower, spread/stack, knockback, and tether examples for style calibration.

Use `assets/templates/*.md` as copyable output templates when creating reusable artifacts for the user. Use `assets/examples/tower-four-card-example.xivplan` as a minimal valid scene example when a concrete `.xivplan` reference is useful.

For concrete diagram files, create a compact mechanic spec JSON and run `scripts/build_xivplan_scene.py` to generate a `.xivplan` draft. Sample specs live in `assets/specs/`.

## Analogy Lookup

When the user says a mechanic is "类似某副本某机制":

1. Run or follow `scripts/search_mechanic_knowledge.py` to expand aliases and search `references/mechanic-taxonomy.md`, `references/positioning-patterns.md`, and `references/encounters/**/*.md`.
2. Run or follow `scripts/adapt_similar_mechanic.py` to write a `similarity-report.md` when a repo-local artifact is useful.
3. State the matched principle, reusable positioning pattern, and unresolved inputs.
4. Keep `可迁移部分` separate from `不应照搬`; do not copy an old encounter's exact positions into a remix without checking the changed rules.
5. Use the user's macro, raidplan, or static convention as the source of truth for concrete assignments.

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

## Solution Optimization

For a complex mechanic with real tradeoffs:

1. Load `references/solution-optimization.md` and `references/solution-candidate-format.md`.
2. Propose at least two safe candidates, such as a stable baseline and a caster-movement optimization.
3. Encode the candidates as a JSON bundle with explicit safety checks, per-role movements, memory features, tolerance margins, communication cost, and diagram complexity.
4. Run `scripts/score_solution_candidates.py`.
5. Never recommend a candidate that fails `safety_gate`, even if its movement cost is lower.
6. Report the recommended strategy, its reasons, its tradeoffs, and any unresolved fight-specific assumptions before drawing the final XivPlan scene.

## XivPlan Rules

When generating object-level instructions:

- Prefer stable role labels: MT, ST, H1, H2, D1, D2, D3, D4.
- Default eight-way role positions are MT north, ST south, H1 west, H2 east, D1 northwest, D2 northeast, D3 southwest, D4 southeast; override with user/team preferences.
- Use `A/B/C/D` for cardinal markers by default: A north, B east, C south, D west; use `1/2/3/4` for intercards when needed.
- In concrete `.xivplan` JSON, prefer these object types:
  - `party` for players, `enemy` for boss/adds, `marker` for A/B/C/D/1/2/3/4, `tower` for towers, `stack` for stacks, `circle`/`rect`/`line`/`cone`/`donut`/`arc`/`polygon`/`starburst` for AoEs and safe zones, `image`/`icon` for embedded assets, `arrow` for movement, `tether` for links, `text` for labels.
  - For multi-step specs, use `style: "king-x-fru"`, `arena.preset`, `markerPresets`, `guide_text`, and `inherit`/`updates`/`remove` to keep repeated objects stable while showing only the change in each figure.
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

To assemble exported images and prose into a shareable guide package, create `guide.json` and run:

```bash
python xivplan-ffxiv-guide/scripts/assemble_guide.py xivplan-ffxiv-guide/assets/sample-guides/phase5-multistep-guide.json -o artifacts/guide-packages/phase5-multistep-guide
```

Use `--short-only` when the user only wants the team-callout version.

When a mechanic needs a special image2/local PNG asset:

1. Draft the prompt from `assets/image-prompts/ffxiv-mechanic-icon.prompt.md`.
2. Save the final transparent PNG under an asset folder.
3. Validate it with `scripts/validate_image_assets.py`.
4. Write an asset manifest and inject it into the scene spec with `scripts/inject_image_assets.py`.
5. Build and validate the `.xivplan` normally.

## Quality Gate

Before finalizing, verify:

- Every figure has a purpose and explains what changed from the previous figure.
- Every role knows where to stand, when to move, and where to reset.
- Direction words and XivPlan coordinates agree.
- Stack/spread/tower/tether mechanics state exact participants or a labeled assumption.
- The short version does not contradict the full version.
- Uncertain fight facts are not presented as confirmed.

For generated Phase 8-style guide packages, run the automated gate:

```bash
python xivplan-ffxiv-guide/scripts/run_quality_gate.py artifacts/phase8-e2e
```

For a single package, use `scripts/validate_guide_package.py` on the case directory and `scripts/audit_visual_density.py` on the `.xivplan` file.

## Mechanic IR Parsing

When the user provides new fight notes, timeline notes, or an incomplete opener draft, parse the notes before proposing detailed diagrams:

```bash
python xivplan-ffxiv-guide/scripts/parse_mechanic_request.py input.md -o artifacts/parsed-mechanics/my-case --encounter-name "Encounter" --phase P1
```

Use the generated `mechanic-ir.json`, `timeline-ir.json`, `candidate-categories.json`, `unknowns.md`, and `parse-report.md` as the source of truth for the next steps. Do not hide uncertainty: if the parser emits unknowns, carry them into the guide or ask for confirmation before drawing final assignments.
