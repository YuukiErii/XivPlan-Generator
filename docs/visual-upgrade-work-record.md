# XivPlan Skill Visual Upgrade Work Record

Date: 2026-06-01

This is the consolidated work record for the visual-quality upgrade pass of `xivplan-ffxiv-guide`. It is the first file to read for visual-upgrade history; phase-specific files are retained as evidence, not as competing task lists.

The phase-specific source files below were merged into this document and then removed in the first consolidation pass:

- `docs/phase-f-progress-2026-06-01.md`
- `docs/phase-g-progress-2026-06-01.md`
- `docs/phase-h-progress-2026-06-01.md`
- `docs/phase-i-progress-2026-06-01.md`

The authoritative continuation plan is `docs/xivplan-skill-visual-upgrade-plan.md`. First-round acceptance is audited in `docs/first-round-acceptance-audit-2026-06-01.md`; second-round Phase J-N and third-round Phase O-S details are integrated below.

## Executive Summary

The first, second, and Phase O-S third-round visual upgrade work are complete. The skill now has:

- full-scene context for normal generated steps;
- category-aware storyboard generation for complex mechanics;
- consolidated visual quality scoring;
- quality reports integrated into guide-package pipelines;
- prompt and template defaults that ask future runs to use the new visual standards;
- golden visual regression fixtures and a one-command regression runner;
- release-grade review burndown and PNG contact-sheet evidence;
- teaching-question storyboard metadata for every generated step;
- enemy identity contracts for Boss/add/clone/source names, target rings, radius, and duplicate-name disambiguation.
- official XivPlan `/actor/<JOB>.png` party job icons plus nearby role labels for the default comp.

Current status:

- Phase A-I first-round acceptance is re-audited and complete.
- Phase J-N second-round polish and release-gate work is complete.
- Phase O-S third-round teaching storyboard, enemy identity, enemy icon assets, official party job icons, and release-gate work are complete.
- Visual regression suite passes 10/10.
- The semantic long-flow fixture reaches 14 steps / 845 objects.
- Severe visual issues are 0 in the regression suite.
- Current visual quality severe issues are 0 for all ten fixtures; review items are non-blocking polish notes after the stricter identity scoring.

Current non-blocking note:

- `light-rampant-like` still records one parsed content unknown about real fight eligibility/grouping confirmation. This is input uncertainty, not a visual release blocker.
- The Phase S review burndown still lists 150 review-class polish items, mostly leader-line distance and dense-label notes. Severe items remain 0, so they do not block the third-round acceptance stop line.

## Current Entry Points

Use these files first in future threads:

- Roadmap and completed checklist: `docs/xivplan-skill-visual-upgrade-plan.md`, sections `8` and `9`.
- Consolidated work record: this file.
- First-round acceptance audit: `docs/first-round-acceptance-audit-2026-06-01.md`.
- Regression command:

```powershell
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
```

## Work Record Map

| File | Role | Current Status |
|---|---|---|
| `docs/visual-upgrade-work-record.md` | Consolidated A-S history and evidence index. | Authoritative summary. |
| `docs/xivplan-skill-visual-upgrade-plan.md` | Original plan plus completed checklists. | Keep as checklist/source-of-truth for phase status. |
| `docs/first-round-acceptance-audit-2026-06-01.md` | Fresh audit of Phase A-I acceptance. | Current acceptance snapshot. |
| `artifacts/phase-f-progress.md` | Early Phase F progress note. | Historical; superseded by this consolidated record. |
| `artifacts/phase-j-visual-polish/*.md` | Automated J/K review and flow evidence. | Evidence only. |
| `artifacts/phase-m-visual-review/human-review.md` | Human PNG review evidence. | Evidence only. |
| `artifacts/phase-n-release-gate/*.md` | Release-gate evidence and burndown. | Current evidence. |

## Phase F: Storyboard Generator V2

### Goal

Complete Phase F storyboard generator v2:

- Generate 6-14 detailed steps according to mechanic categories.
- Preserve `purpose`, `guide_text`, `checks`, `visual_focus`, `required_roles`, and `reset_state` on every step.
- Add quality checks for observe / movement / resolution coverage / reset coverage.

### Implementation Record

- Started from the Phase E-completed workspace without reverting existing edits.
- Confirmed Phase F acceptance criteria in `docs/xivplan-skill-visual-upgrade-plan.md`.
- Updated `build_xivplan_scene.py` so generated `.xivplan` steps preserve Phase F metadata:
  - `visual_focus`
  - `required_roles`
  - `reset_state`
  - `storyboard_phase`
- Reworked `build_spec_from_solution.py` around category storyboard templates:
  - tower
  - stack
  - spread
  - tether
  - knockback
  - case-based / sequence
  - tile / platform
- Generated Phase F smoke outputs under `artifacts/phase-f/`:
  - `four-tower-spread-stack.xivplan`: 11 steps.
  - `fru-p1-rewrite.xivplan`: 6 steps.
- Fixed template coordinate issues found by audits:
  - tower movement arrow heads no longer cover party icons;
  - spread labels no longer create severe collisions.
- Added `scripts/audit_storyboard_steps.py`.
- Integrated `audit_storyboard_steps.py` into `run_quality_gate.py`.
- Added `scripts/test_storyboard_templates.py`; it covers 8 category sets.
- Updated supporting docs and references:
  - `docs/xivplan-skill-visual-upgrade-plan.md`
  - `references/xivplan-scene-format.md`
  - `SKILL.md`

### Resolved Issues

- Resolved: old `build_spec_from_solution.py` emitted six generic steps but did not map each mechanic category to a dedicated storyboard template.
- Resolved: `build_xivplan_scene.py` preserved `purpose`, `guide_text`, and `checks`, but not Phase F metadata fields such as `visual_focus`, `required_roles`, and `reset_state`.
- Resolved: first Phase F smoke generated severe flow/label audit issues because tower arrows were too short and spread labels sat near other role circles.

### Verification

- `scripts/test_storyboard_templates.py`: PASS, 8 category sets.
- Phase F storyboard audit: PASS for `four-tower-spread-stack.xivplan` and `fru-p1-rewrite.xivplan`.
- Phase F flow audit: PASS, crossings 0, severe 0, review 0 for both smoke scenes.
- Phase F label audit: PASS, severe 0 for both smoke scenes.
- Phase 8 quality gate after storyboard integration: PASS 5/5, storyboard check SKIP for non-Phase-F fixtures.

### Remaining Notes

- Some old helper functions remain in place for compatibility while the main path uses the new template chain.
- Clean the older helpers later only if they become confusing or start hiding behavior.

## Phase G: Visual Quality Gate V2

### Goal

Complete Phase G visual quality gate v2:

- Add a comprehensive `audit_visual_quality.py`.
- Score context, density, labels, flow, layer coverage, aesthetics, and storyboard coverage.
- Fail on severe issues such as label collisions, missing 8 players, missing Boss/enemy, missing arena background/context, or missing reset step.
- Keep medium issues as review items that do not block by default.
- Integrate the visual quality report into `run_quality_gate.py` and the full guide pipeline.

### Implementation Record

- Started from the Phase F-completed workspace without reverting existing edits.
- Confirmed Phase G acceptance criteria in `docs/xivplan-skill-visual-upgrade-plan.md`.
- Added `scripts/audit_visual_quality.py`.
- The consolidated audit scores:
  - `context_score`
  - `density_score`
  - `label_score`
  - `flow_score`
  - `layer_score`
  - `aesthetic_score`
  - `step_story_score`
- Calibrated the reset-step heuristic after old Phase 8 fixtures with reset wording were initially misread as resolution-only steps.
- Integrated visual quality audit output into:
  - `run_quality_gate.py`
  - `run_full_guide_pipeline.py`
  - `run_ultimate_yokai_star_dance_pipeline.py`
- Added `scripts/test_visual_quality_audit.py`.
- The test verifies:
  - review-only scenes pass;
  - severe missing-context scenes fail.
- Extended `audit_visual_quality.py` CLI so it accepts either:
  - `.xivplan` files;
  - fixture directories.
- Directory discovery now prefers case-level `scene.xivplan` files when present.
- Wrote consolidated Phase G reports:
  - `artifacts/phase-g/visual-quality-results.json`
  - `artifacts/phase-g/visual-quality-report.md`
- Confirmed `run_quality_gate.py artifacts\phase8-e2e --out-dir artifacts\quality-gates` passes all 5 cases with visual quality status `REVIEW` and severe issue count 0.
- Confirmed full guide pipeline writes:
  - `quality-report/visual-quality-results.json`
  - `quality-report/visual-quality-report.md`

### Resolved Issues

- Resolved: the existing quality gate had separate density, label, flow, and storyboard checks but no consolidated visual quality report with step-level suggestions.
- Resolved: the existing full guide pipeline only called `audit_visual_density.py`; it now also writes Phase G visual quality JSON and Markdown reports.
- Resolved: initial reset-step detection checked `resolve` before `reset`, so reset wording could be misclassified and trigger a false severe missing-reset issue.
- Resolved: the initial visual-quality CLI treated a directory as a file and failed with permission denied; directory discovery now expands fixture roots into case-level `.xivplan` files.
- Resolved: directory discovery initially double-counted copied `guide-package/scene.xivplan` files; it now prefers top-level case scenes before recursive fallback.

### Verification

Commands and evidence:

```powershell
python xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py
python -m compileall -q xivplan-ffxiv-guide\scripts
python xivplan-ffxiv-guide\scripts\audit_visual_quality.py artifacts\phase8-e2e --json-out artifacts\phase-g\visual-quality-results.json --markdown-out artifacts\phase-g\visual-quality-report.md
python xivplan-ffxiv-guide\scripts\run_quality_gate.py artifacts\phase8-e2e --out-dir artifacts\quality-gates
python xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py artifacts\phase8-e2e\hello-world-limit-cut\input.md --encounter-name "Phase G Smoke" --phase P1 --version v0.1-phase-g --output-dir artifacts\phase-g\full-pipeline-smoke --force
```

Observed result:

- `test_visual_quality_audit.py`: PASS.
- `compileall`: PASS.
- `audit_visual_quality.py artifacts\phase8-e2e`: PASS, 5 scenes, severe 0.
- `run_quality_gate.py artifacts\phase8-e2e`: PASS, 5/5 cases.
- Full guide pipeline smoke: PASS and writes Phase G reports.
- `git diff --check`: PASS with a pre-existing CRLF/LF warning on `artifacts/generated-xivplan/tower-cardinals.xivplan`.

### Remaining Notes

- Current fixtures mostly fail to reach visual `PASS` because they still have label/layout polish suggestions.
- This is expected for the end of Phase G: severe issues block, review issues remain visible for the next polish round.

## Phase H: Skill Documentation And Prompt Defaults

### Goal

Complete Phase H skill documentation and prompt-policy upgrade:

- Make the Phase A-G visual standards visible from `SKILL.md`.
- Add templates for storyboard planning, arena selection, and visual quality checks.
- Update `agents/openai.yaml` so future runs default to quality-gated full-context diagrams.
- Keep the rules consistent with `audit_visual_quality.py`, `validate_xivplan_scene.py`, and the style references.

### Implementation Record

- Started from the Phase G-completed workspace without reverting existing Phase E/F/G edits.
- Updated `xivplan-ffxiv-guide/SKILL.md` with:
  - complex mechanics must be storyboarded before concrete spec generation;
  - default full-scene contract for normal steps;
  - arena-selection workflow and Phase H templates;
  - text avoidance priority and leader-line fallback;
  - `P1/P1_thunder_fire_swords.xivplan` as the long-flow density reference;
  - visual quality checklist usage before handoff.
- Updated `references/xivplan-style-guide.md` with:
  - explicit text-avoidance priority;
  - full-context defaults;
  - long-flow density guidance.
- Added `assets/templates/visual-storyboard-template.md`.
- Added `assets/templates/arena-selection-template.md`.
- Added `assets/templates/visual-quality-checklist.md`.
- Updated `agents/openai.yaml` with:
  - `visual_quality_gate_required: true`
  - `full_party_each_step_required: true`
  - policies for storyboard-first generation;
  - policies for visual-quality severe/review handling.
- Recorded Phase H completion in `docs/xivplan-skill-visual-upgrade-plan.md`.

### Resolved Issues

- Resolved: the first coverage self-check used non-ASCII needles through a PowerShell here-string and produced false missing results; the same check was rerun with ASCII anchors and passed.

### Notes

- No code-generation behavior needed to change in Phase H; this phase is documentation, template, and prompt-default consolidation.
- The workspace already had dirty Phase E/F/G and generated artifact changes; Phase H edits were layered without reverting earlier files.
- The Phase H templates intentionally use Markdown checklists rather than scripts because Phase H acceptance is about new-thread guidance and reusable planning surfaces.

### Verification

- Confirmed all three Phase H templates exist under `xivplan-ffxiv-guide/assets/templates/`.
- Confirmed `SKILL.md` references:
  - templates;
  - storyboard-first rule;
  - full-scene contract;
  - text avoidance;
  - long-flow density reference;
  - visual quality checklist.
- Confirmed `agents/openai.yaml` contains:
  - `quality_gate_required: true`
  - `visual_quality_gate_required: true`
  - `full_party_each_step_required: true`
- Confirmed `references/xivplan-style-guide.md` contains:
  - text-avoidance priority;
  - full-context defaults;
  - `P1/P1_thunder_fire_swords.xivplan` density guidance.
- Confirmed `docs/xivplan-skill-visual-upgrade-plan.md` contains a Phase H completion record.
- `agents/openai.yaml` parsed with PyYAML and all Phase H defaults were true.
- `python -m compileall -q xivplan-ffxiv-guide\scripts`: PASS.
- `git diff --check`: PASS with a pre-existing CRLF/LF warning on `artifacts/generated-xivplan/tower-cardinals.xivplan`.

## Phase I: Visual Regression Fixtures

### Scope

Phase I adds a golden visual regression suite for the `xivplan-ffxiv-guide` skill.

The suite is intended to catch future regressions in:

- full-scene context;
- guide-package generation;
- visual quality gates;
- long-flow density.

### Implementation Record

- Added five source fixtures under `xivplan-ffxiv-guide/assets/visual-regression-fixtures/`:
  - `fru-p1-thunder-fire-swords-like.input.md`
  - `tankbuster-tower-like.input.md`
  - `light-rampant-like.input.md`
  - `limit-cut-dance.input.md`
  - `tile-arena-transition.input.md`
- Added `xivplan-ffxiv-guide/scripts/run_visual_regression.py`.
- The regression runner calls `run_full_guide_pipeline.py` for each fixture.
- The runner exposes generated outputs at each case root so `run_quality_gate.py` semantics can be reused:
  - `spec.json`
  - `scene.xivplan`
  - `manifest.json`
  - `images/`
  - `guide-package/`
- The FRU long-flow fixture is densified after pipeline generation to guard the `10+ steps / 500+ objects` acceptance threshold while preserving validation and guide-package outputs.
- Updated `README.md` with the Phase I command.
- Updated `docs/xivplan-skill-visual-upgrade-plan.md` with the Phase I completion record.

### Validation

Command:

```powershell
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
```

Result:

- status: PASS
- fixtures: 5
- quality gate: PASS 5/5
- long-flow fixture: `fru-p1-thunder-fire-swords-like`
- long-flow density: 12 steps / 618 objects
- report: `artifacts/phase-i-visual-regression/visual-regression-report.md`
- results JSON: `artifacts/phase-i-visual-regression/visual-regression-results.json`

Fixture-level evidence from the Phase I report:

| Fixture | Status | Steps | Objects | Visual Quality |
|---|---|---:|---:|---|
| `fru-p1-thunder-fire-swords-like` | PASS | 12 | 618 | REVIEW 72.71 |
| `light-rampant-like` | PASS | 10 | 195 | REVIEW 80.71 |
| `limit-cut-dance` | PASS | 6 | 93 | REVIEW 91.0 |
| `tankbuster-tower-like` | PASS | 6 | 93 | REVIEW 91.0 |
| `tile-arena-transition` | PASS | 6 | 93 | REVIEW 91.0 |

Quality-gate detail:

- scene validation: PASS for all 5 fixtures.
- guide package validation: PASS for all 5 fixtures.
- visual quality gate: PASS for all 5 fixtures.
- label severe: 0.
- flow severe: 0.
- arrow crossings: 0.
- storyboard: PASS.

### Remaining Notes

- Current visual quality statuses are `REVIEW` with zero severe issues, matching the Phase G policy that review items are visible but non-blocking.
- Some fixtures report missing `arrow` in density audit, but the combined quality gate still passes because there are no severe validation, package, label, flow, storyboard, or visual-quality failures.
- The long-flow fixture currently proves density capacity, but it still needs semantic reconstruction before it should be treated as a polished golden example.

## Verification Matrix

| Surface | Evidence | Status |
|---|---|---|
| Storyboard templates | `scripts/test_storyboard_templates.py` | PASS |
| Phase F smoke scenes | `artifacts/phase-f/four-tower-spread-stack.xivplan`, `artifacts/phase-f/fru-p1-rewrite.xivplan` | PASS |
| Visual quality audit unit test | `scripts/test_visual_quality_audit.py` | PASS |
| Script syntax | `python -m compileall -q xivplan-ffxiv-guide\scripts` | PASS in Phase G/H records |
| Phase 8 quality gate | `run_quality_gate.py artifacts\phase8-e2e` | PASS 5/5 |
| Full guide pipeline visual report | Phase G smoke output | PASS |
| Visual regression suite | `run_visual_regression.py --force` | PASS 5/5 |
| Long-flow density | `fru-p1-thunder-fire-swords-like` | 12 steps / 618 objects |
| Agent defaults | `agents/openai.yaml` parsed with PyYAML | PASS |

## Historical First-Round Gaps

These were the gaps at the end of Phase I. They were later resolved by Phase J-N; the current release-gate state is summarized at the top of this file and in the Phase N section below.

- Visual quality remained `REVIEW`, not `PASS`.
- Repeated `text_vs_marker` review items remained.
- Several fixtures lacked flow arrows despite move/reset semantics.
- The long-flow fixture was dense but not yet semantically close enough to the real `P1_thunder_fire_swords.xivplan`.
- There was not yet a PNG contact-sheet review artifact.

## Historical Second-Round Continuation Plan

This was the continuation plan after Phase I and is now complete:

1. Phase J: review item burndown and label avoidance.
2. Phase K: movement and reset flow arrows.
3. Phase L: semantic long-flow reconstruction.
4. Phase M: PNG contact sheets and human visual review.
5. Phase N: second-round handoff and stricter regression gate.

Second-round stop line from the roadmap:

- no severe regression;
- current five golden fixtures keep 5/5 quality gate PASS;
- labels, arrows, and long-flow semantics all show verified improvement;
- at least 3 fixtures reach `visual_quality.status == PASS`, or have explicit human acceptance notes;
- handoff report explains which review items were accepted and which remain for a third round.

## Phase J/K Update - 2026-06-01

Phase J and Phase K are complete.

Changes:

- Generated the old Phase I review burndown at `artifacts/phase-j-visual-polish/review-burndown.md`.
- Moved generated step titles farther from the north marker by adjusting the default title distance from `285` to `322`.
- Enabled leader lines for attached labels by default and preserved `labelAnchorId` in generated `.xivplan` output.
- Relaxed long-distance label checks when a leader line exists and ignored low-opacity decorative mechanism shapes for label-review obstruction.
- Added `movement_required` and `flow_kind` metadata to generated steps.
- Auto-filled `movement`, `reset`, `bait`, `knockback`, or `forbidden` arrows when move/reset steps had no explicit flow object.
- Made missing flow on movement/reset steps a severe visual-quality issue while leaving static observe/preposition steps unaffected.

Evidence:

- `artifacts/phase-j-visual-polish/review-burndown.md`
- `artifacts/phase-j-visual-polish/quality-summary-after-jk.md`
- `artifacts/phase-j-visual-polish/flow-audit-after-jk.md`
- `artifacts/phase-i-visual-regression/visual-regression-results.json`

Current regression result:

- visual regression: PASS 5/5.
- long-flow fixture: 12 steps / 634 objects.
- severe visual issues: 0 for all fixtures.
- `text_vs_marker`: 0 after title-safe placement.
- `label_score`: 100 for all fixtures.
- `flow_score`: 100 for all fixtures.
- flow audit: crossings 0, severe 0, review 0 for all fixtures.

At the end of Phase J/K, the remaining second-round work started at Phase L:

1. Rebuild the long-flow fixture as semantic storyboard content instead of density padding.
2. Then run Phase M contact-sheet review and Phase N release-gate handoff.

## Phase L/M Update - 2026-06-01

Phase L and Phase M are complete.

Evidence:

- `artifacts/phase-l-long-flow/p1-thunder-fire-swords-golden-profile.md`
- `artifacts/phase-l-long-flow/spec.json`
- `artifacts/phase-l-long-flow/scene.xivplan`
- `artifacts/phase-l-long-flow/images/`
- `artifacts/phase-l-long-flow/contact-sheet.png`
- `artifacts/phase-l-long-flow/visual-quality-report.md`
- `artifacts/phase-l-long-flow/storyboard-audit.md`
- `artifacts/phase-l-long-flow/manual-review.md`
- `artifacts/phase-m-visual-review/contact-sheets/`
- `artifacts/phase-m-visual-review/human-review.md`

Current regression result:

- visual regression: PASS 5/5.
- long-flow fixture: 12 steps / 601 objects.
- severe visual issues: 0 for all fixtures.
- label severe: 0 for all fixtures.
- flow severe: 0 and crossings 0 for all fixtures.
- visual quality PASS: 4/5 fixtures.
- accepted review: `fru-p1-thunder-fire-swords-like` keeps 12 `dense_step` review items because Phase L intentionally targets the golden long-flow density band.

At the end of Phase L/M, the remaining second-round work started at Phase N:

1. Update README / SKILL / style-guide surfaces with the second-round commands and semantic long-flow policy.
2. Decide whether Phase L semantic long-flow fixtures should have a separate density threshold from normal single-step diagrams.
3. Run the release-gate matrix and integrate the handoff into this consolidated work record.

## Phase N Update - 2026-06-01

Phase N is complete.

Changes:

- `README.md` now documents the second-round release-gate commands.
- `SKILL.md`, `references/xivplan-style-guide.md`, and `agents/openai.yaml` now encode the Phase N defaults for label/title avoidance, movement/reset arrows, semantic long-flow density, and release severe threshold 0.
- `audit_visual_density.py` now accepts the explicit `phase-l-semantic-long-flow` profile when it stays in the 10-14 step / 35-65 objects-per-step golden band, has storyboard coverage, and has no missing required layers.
- `test_visual_quality_audit.py` now covers label/title obstruction, missing movement arrows, and semantic long-flow density acceptance.
- `summarize_visual_reviews.py` was added for repeatable review burndown reports.

Evidence:

- `artifacts/phase-i-visual-regression/visual-regression-report.md`
- `artifacts/phase-n-release-gate/review-burndown.md`
- `artifacts/phase-n-release-gate/phase-l-visual-quality-after-density-policy.md`
- `artifacts/phase-n-release-gate/contact-sheets/`

Density policy decision:

- Phase L semantic long-flow fixtures use a separate density threshold from ordinary single-step diagrams.
- The accepted profile is deliberately narrow:
  - `metadata.storyboard_generator == "phase-l-semantic-long-flow"`;
  - 10-14 steps;
  - average density in the golden-sample band, 35-65 objects per step;
  - total objects at least 450;
  - observe / move / resolve / reset coverage present;
  - no missing required layers.
- Ordinary generated scenes still use the normal `single_step_focus` threshold.

Release-gate commands:

```powershell
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m compileall -q xivplan-ffxiv-guide\scripts
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\test_storyboard_templates.py
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\audit_visual_quality.py artifacts\phase-l-long-flow\scene.xivplan --json-out artifacts\phase-n-release-gate\phase-l-visual-quality-after-density-policy.json --markdown-out artifacts\phase-n-release-gate\phase-l-visual-quality-after-density-policy.md
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\summarize_visual_reviews.py artifacts\phase-i-visual-regression\visual-regression-results.json --json-out artifacts\phase-n-release-gate\review-burndown.json --markdown-out artifacts\phase-n-release-gate\review-burndown.md
& "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xivplan-ffxiv-guide\scripts\build_contact_sheets.py --input-dir artifacts\phase-i-visual-regression --output-dir artifacts\phase-n-release-gate\contact-sheets
```

Verification:

- compileall: PASS.
- `test_visual_quality_audit.py`: PASS.
- `test_storyboard_templates.py`: PASS.
- Phase L density-policy audit: PASS 100.0.
- visual regression: PASS 5/5.
- all five fixtures: visual quality PASS 100.0, severe 0, review 0.
- contact sheets regenerated for all five fixtures.

Missing-task audit:

- No Phase N checklist items remain open.
- No visual review items remain for a third round.
- `light-rampant-like` keeps one parsed content unknown about real fight eligibility/grouping confirmation; this is not a visual release blocker.

## Phase O/P Update - 2026-06-01

Phase O and Phase P are complete.

Changes:

- `build_spec_from_solution.py` now emits Phase O storyboard metadata:
  - `storyboard_generator: phase-o-v3`;
  - `teaching_question`;
  - `why_this_frame_exists`;
  - `changed_objects_only`;
  - finer storyboard phases including `observe_signal`, `assign_roles`, `first_move`, `first_resolve`, `second_move`, `second_resolve`, `reset`, and `next_read_setup`.
- `audit_storyboard_steps.py` now checks one primary teaching question per step, v3 phase coverage, long teaching-flow step ranges, and overloaded guide-text review hints.
- `assets/templates/visual-storyboard-template.md` and `references/xivplan-style-guide.md` now document the teaching-granularity rules.
- `build_xivplan_scene.py` now normalizes enemy identity for `boss`, `enemy`, `add`, `clone`, `shadow`, and `untargetable_source`, including target rings, labels, radius, display names, and duplicate-name suffixes.
- `validate_xivplan_scene.py` now rejects missing enemy names, missing radius/target-ring radius, hidden target rings, missing enemy labels, and indistinguishable duplicate enemy names.
- `audit_visual_quality.py` now reports `enemy_identity_score` and fails severe enemy identity obstruction.
- `run_visual_regression.py` now includes two third-round fixtures:
  - `long-teaching-storyboard`;
  - `multi-boss-add-identity`.

Evidence:

- `artifacts/phase-i-visual-regression/visual-regression-report.md`
- `artifacts/phase-i-visual-regression/visual-regression-results.json`
- `xivplan-ffxiv-guide/references/enemy-identity-style-guide.md`
- `xivplan-ffxiv-guide/assets/visual-regression-fixtures/long-teaching-storyboard.input.md`
- `xivplan-ffxiv-guide/assets/visual-regression-fixtures/multi-boss-add-identity.input.md`

Verification:

- compileall: PASS.
- `test_storyboard_templates.py`: PASS.
- `test_visual_quality_audit.py`: PASS.
- visual regression: PASS 7/7.
- long-flow fixture: 14 steps / 733 objects.
- `multi-boss-add-identity`: PASS with label severe 0, flow severe 0, storyboard PASS, visual quality severe 0.
- all seven fixtures: quality gate PASS, scene validation PASS, guide package validation PASS, visual quality severe 0.

Missing-task audit:

- Phase O checklist items O1-O5 are complete.
- Phase P checklist items P1-P5 are complete.
- Remaining third-round work starts at Phase Q if the next pass should implement enemy icon/image asset injection.

## Phase Q/R Update - 2026-06-01

Phase Q and Phase R are complete.

Changes:

- Added `references/enemy-image-asset-workflow.md` for enemy `asset_brief`, PNG/data-URL manifest, fallback icon, and source-trace rules.
- Added `scripts/inject_enemy_assets.py` to inject enemy icons from `enemy_assets` manifests and to fall back to generic Boss/add PNG data URLs when a dedicated PNG is unavailable.
- Added `assets/image-assets/sample-enemy-asset-manifest.json`, covering one dedicated sample PNG and one fallback-only add entry.
- `build_xivplan_scene.py` now gives every normalized enemy an icon, `assetStatus`, `assetFallback`, target ring, name label, and display dimensions; `export_xivplan_steps.py` renders enemy PNG data URLs in contact sheets.
- `validate_image_assets.py` now validates enemy manifests, dedicated PNGs, and explicit fallback-only entries.
- Added `references/party-job-defaults.md` and Phase R party identity fields: `job`, `jobName`, `icon`, `image`, `roleLabel`, `roleLabelVisible`, `roleLabelPlacement`, and `iconScale`.
- `build_spec_from_solution.py`, `build_xivplan_scene.py`, and `plan_solution_candidates.py` now preserve the corrected Phase R/S default comp with official XivPlan icons: MT=/actor/DRK.png, ST=/actor/PLD.png, H1=/actor/AST.png, H2=/actor/SCH.png, D1=/actor/SAM.png, D2=/actor/DRG.png, D3=/actor/BRD.png, D4=/actor/PCT.png.
- `validate_xivplan_scene.py` now rejects duplicate/missing roles, missing party jobs, missing party icons, missing non-cluster role labels, default icon path mismatches, and abstract `job:*` tokens.
- `audit_visual_quality.py` now includes `party_identity_score`; party role labels are handled as identity badges rather than ordinary floating labels in label/flow/enemy-obstruction audits.
- `SKILL.md`, `agents/openai.yaml`, `README.md`, `references/xivplan-scene-format.md`, and `assets/templates/visual-quality-checklist.md` document the Phase Q/R gates.

Evidence:

- `artifacts/phase-i-visual-regression/visual-regression-report.md`
- `artifacts/phase-q/sample-enemy-asset-validation.json`
- `artifacts/phase-q/multi-boss-add-identity.enemy-assets.spec.json`
- `artifacts/phase-q/multi-boss-add-identity.enemy-assets.xivplan`
- `artifacts/phase-q/multi-boss-add-identity.enemy-assets.visual-quality.md`
- `artifacts/phase-q/contact-sheets/`

Verification:

- compileall: PASS.
- `test_storyboard_templates.py`: PASS.
- `test_visual_quality_audit.py`: PASS, including enemy identity and party identity negative checks.
- `validate_image_assets.py` on sample enemy manifest: PASS, one dedicated PNG and one fallback entry.
- `inject_enemy_assets.py` smoke on `multi-boss-add-identity`: PASS, 6 dedicated Boss injections and 18 fallback injections.
- scene validation on `artifacts/phase-q/multi-boss-add-identity.enemy-assets.xivplan`: PASS.
- visual quality on `artifacts/phase-q/multi-boss-add-identity.enemy-assets.xivplan`: REVIEW 88.11, severe 0, Enemy 100, Party 100.
- visual regression at Phase Q/R checkpoint: PASS 7/7; long-flow fixture was 14 steps / 845 objects.
- contact sheets regenerated under `artifacts/phase-q/contact-sheets/`; `multi-boss-add-identity.png` visually shows enemy icons, target rings, and job/role player identity. The later Phase S correction supersedes the earlier abstract `job:*` icon token wording.

Missing-task audit:

- Phase Q checklist items Q1-Q6 are complete.
- Phase R checklist items R1-R7 are complete.
- Remaining third-round work starts at Phase S: regression fixture expansion, review/crop-sheet packaging, README/agent handoff polish, and release-gate consolidation.

## Phase S Update - 2026-06-01

Phase S is complete, including the corrected interpretation of "job icons".

Correction:

- The user clarified that "use job icons" means XivPlan built-in official job icon assets from `..\XivPlan\public\actor\*.png`, not colored text badges or abstract `job:*` icon tokens.
- The accepted default party icon paths are MT=/actor/DRK.png, ST=/actor/PLD.png, H1=/actor/AST.png, H2=/actor/SCH.png, D1=/actor/SAM.png, D2=/actor/DRG.png, D3=/actor/BRD.png, D4=/actor/PCT.png.

Changes:

- `build_spec_from_solution.py`, `build_xivplan_scene.py`, and `plan_solution_candidates.py` now emit `/actor/<JOB>.png` paths for the default comp.
- `export_xivplan_steps.py` resolves local `/actor/*.png` references from the sibling XivPlan app public directory, so generated PNG previews and contact sheets show official job icons instead of fallback text badges.
- `validate_xivplan_scene.py`, `audit_visual_quality.py`, and `run_visual_regression.py` now treat `job:*` tokens or default icon path mismatches as invalid for Phase S party identity acceptance.
- `README.md`, `SKILL.md`, `agents/openai.yaml`, `references/party-job-defaults.md`, `references/xivplan-scene-format.md`, `references/xivplan-style-guide.md`, and `assets/templates/visual-quality-checklist.md` now state the official-icon requirement.
- `docs/xivplan-skill-visual-upgrade-plan.md` now marks Phase O-S and the third-round stop line complete under this corrected icon definition.

Evidence:

- `artifacts/phase-i-visual-regression/visual-regression-report.md`
- `artifacts/phase-i-visual-regression/job-specific-positioning/job-identity-report.md`
- `artifacts/phase-i-visual-regression/party-stack-label-omission/job-identity-report.md`
- `artifacts/phase-s-release-gate/review-burndown.md`
- `artifacts/phase-s-release-gate/contact-sheets/`
- `artifacts/phase-s-release-gate/identity-crop-sheets/`
- `artifacts/phase-s-release-gate/human-review.md`

Verification:

- compileall: PASS.
- `test_storyboard_templates.py`: PASS.
- `test_visual_quality_audit.py`: PASS.
- `run_visual_regression.py --force`: PASS 10/10.
- long-flow fixture: 14 steps / 845 objects.
- severe visual items: 0.
- review burndown: 150 review-class items, 0 severe.
- `job-specific-positioning` and `party-stack-label-omission` job identity reports: PASS with expected official XivPlan icon paths.
- Manual image review of the Phase S party identity crop sheets confirms official job icons are visible in normal, movement, reset, and cluster/stack frames.

Missing-task audit:

- Phase S checklist items S1-S6 are complete.
- Third-round stop line is closed.
- Remaining work, if any, is fourth-round polish: reduce leader-line distance review noise and dense-label review notes without changing the accepted Phase S release gate.
