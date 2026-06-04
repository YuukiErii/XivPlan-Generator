# XivPlan Generator

Codex skill and local tooling for turning FFXIV mechanic descriptions into XivPlan diagrams and Chinese guide drafts.

## Contents

- `xivplan-ffxiv-guide/`: Codex skill package.
- `xivplan-ffxiv-guide/scripts/`: XivPlan scene generation and validation utilities.
- `xivplan-ffxiv-guide/assets/specs/`: compact mechanic specs used to generate `.xivplan` examples.
- `xivplan-ffxiv-guide/assets/image-assets/`: transparent PNG assets and placement manifests for image2/local PNG workflows.
- `xivplan-ffxiv-guide/assets/image-prompts/`: prompt templates for generated guide assets.
- `xivplan-ffxiv-guide/assets/examples/generated-xivplan/`: curated lightweight `.xivplan` examples for smoke testing and guide fixtures.
- `xivplan-ffxiv-guide/assets/sample-guides/`: `guide.json` examples and lightweight image fixtures.
- `xivplan-ffxiv-guide/assets/optimization/`: multi-candidate fixtures for strategy scoring.
- `xivplan-ffxiv-guide/assets/progression-notes/`: source notes for versioned progression workflows.
- `xivplan-ffxiv-guide/assets/parser-fixtures/`: natural-language mechanic notes for parser regression tests.
- `xivplan-ffxiv-guide/assets/knowledge-fixtures/`: similar-mechanic retrieval fixtures.
- `xivplan-ffxiv-guide/assets/visual-regression-fixtures/`: Phase I golden, Phase S identity, Phase U annotation, Phase V route/range semantic, and Phase X status-assignment visual regression inputs.
- `artifacts/generated-xivplan/`: local generated `.xivplan` outputs.
- `artifacts/guide-packages/`: generated Markdown / DOCX / PDF guide package smoke outputs.
- `artifacts/solution-scores/`: lightweight JSON and Markdown strategy-score reports.
- `artifacts/parsed-mechanics/`: generated mechanic IR, timeline IR, category, unknown, and parse-report outputs.
- `artifacts/knowledge-search/`: generated knowledge-search JSON/Markdown and similarity reports.
- `artifacts/full-guide-pipeline/`: one-command guide package outputs.
- `artifacts/ultimate-yokai-star-dance/`: local generated Ultimate Yokai Star Dance progression outputs.
- `docs/project-status.md`: consolidated requirements, roadmap status, visual-upgrade work record, acceptance evidence, and next-step checklist.
- `docs/case-studies/ultimate-yokai-star-dance/`: persistent notes and historical change-log snapshots for the Ultimate Yokai Star Dance workflow.

Generated runtime outputs under `artifacts/` are ignored by default. Source
fixtures and durable notes live under `xivplan-ffxiv-guide/assets/` and `docs/`.

## Validate

Use the bundled Codex Python on this Windows machine if `python` is not on PATH.

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py xivplan-ffxiv-guide\assets\specs\tower-cardinals.spec.json -o artifacts\generated-xivplan\tower-cardinals.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\generated-xivplan\tower-cardinals.xivplan
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py xivplan-ffxiv-guide\assets\specs\phase5-multistep-style.spec.json -o artifacts\generated-xivplan\phase5-multistep-style.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\generated-xivplan\phase5-multistep-style.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_mechanic_knowledge.py
& $py xivplan-ffxiv-guide\scripts\test_solution_optimizer.py
```

## One-Command XivPlan Generation

Generate an importable `.xivplan` from one mechanic Markdown file:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py input.md `
  --encounter-name "Encounter" `
  --phase P1 `
  --version v0.1-draft `
  --output-dir artifacts\full-guide-pipeline\my-case
```

By default the command writes parsed IR, knowledge matches, solution candidates, a scored recommendation, scene spec, `.xivplan`, and a quality report. It does not export step PNGs, SVGs, Markdown, DOCX, or PDF. If rerunning the same output directory intentionally, add `--force`. Use `--full-package` only when release/regression QA explicitly needs step PNGs and Markdown / DOCX / PDF guide files.

Generate Ultimate Yokai Star Dance progression `.xivplan` output:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  xivplan-ffxiv-guide\assets\progression-notes\ultimate-yokai-star-dance\raw-notes\p1-draft-notes.md `
  --ultimate-yokai-star-dance `
  --version v0.1-draft
```

Generate the next observed version and append the change log:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  xivplan-ffxiv-guide\assets\progression-notes\ultimate-yokai-star-dance\raw-notes\p1-observed-notes.md `
  --ultimate-yokai-star-dance `
  --version v0.2-observed `
  --previous-version v0.1-draft
```

Quality reports are written under the selected output directory or under `artifacts\ultimate-yokai-star-dance\quality-reports\<version>\`.

Compare and explain strategy candidates:

```powershell
& $py xivplan-ffxiv-guide\scripts\score_solution_candidates.py xivplan-ffxiv-guide\assets\optimization\spread-stack-candidates.json --json-out artifacts\solution-scores\spread-stack-scores.json --markdown-out artifacts\solution-scores\spread-stack-report.md
```

Assemble a guide package:

```powershell
& $py xivplan-ffxiv-guide\scripts\assemble_guide.py xivplan-ffxiv-guide\assets\sample-guides\phase5-multistep-guide.json -o artifacts\guide-packages\phase5-multistep-guide --strict-images
& $py xivplan-ffxiv-guide\scripts\assemble_guide.py xivplan-ffxiv-guide\assets\sample-guides\phase5-multistep-guide.json -o artifacts\guide-packages\phase5-short --short-only --strict-images
```

Validate and inject image2/local PNG assets:

```powershell
& $py xivplan-ffxiv-guide\scripts\validate_image_assets.py xivplan-ffxiv-guide\assets\image-assets\sample-asset-manifest.json --json-out artifacts\image-asset-reports\sample-asset-validation.json
& $py xivplan-ffxiv-guide\scripts\inject_image_assets.py xivplan-ffxiv-guide\assets\specs\image-asset-base.spec.json xivplan-ffxiv-guide\assets\image-assets\sample-asset-manifest.json -o artifacts\generated-specs\image-asset-injected.spec.json --replace
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py artifacts\generated-specs\image-asset-injected.spec.json -o artifacts\generated-xivplan\image-asset-injected.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\generated-xivplan\image-asset-injected.xivplan
```

Validate and inject enemy icon manifests:

```powershell
& $py xivplan-ffxiv-guide\scripts\validate_image_assets.py artifacts\phase-q\enemy-assets.json --json-out artifacts\phase-q\enemy-asset-validation.json
& $py xivplan-ffxiv-guide\scripts\inject_enemy_assets.py artifacts\phase-q\spec.json artifacts\phase-q\enemy-assets.json -o artifacts\phase-q\spec.enemy-assets.json
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py artifacts\phase-q\spec.enemy-assets.json -o artifacts\phase-q\scene.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\phase-q\scene.xivplan
```

Run Phase 8 end-to-end fixtures:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_phase8_e2e.py
```

This writes five complete case packages under `artifacts\phase8-e2e\`, including input text, recommended solution notes, `spec.json`, `scene.xivplan`, step PNG exports, `manifest.json`, and Markdown / DOCX / PDF guide packages.

Run the Phase 9 quality gate over those generated packages:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_quality_gate.py artifacts\phase8-e2e
```

This checks `.xivplan` structure, embedded image data URLs, step titles and guide text, object bounds, player overlap, manifest / figure alignment, PNG dimensions, Markdown / DOCX / PDF outputs, role coverage, `unknowns`, and visual density. It writes `artifacts\quality-gates\phase9-quality-report.md` and `artifacts\quality-gates\phase9-quality-results.json`.

Run the visual regression suite:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
```

This runs the golden visual fixtures plus Phase O/P/Q/R/S/U/V/W/X checks, writes top-level case surfaces for quality gating, and produces `artifacts\phase-i-visual-regression\visual-regression-report.md`. The suite now expects 12/12 fixtures: the long FRU-style fixtures guard 14+ teaching steps and 500+ objects; enemy fixtures check target rings, readable names, duplicate add disambiguation, and fallback/dedicated enemy icons; party fixtures check both guide-section modes, with main mechanism scenes using numbered role icons and `flow_example` fixtures preserving official XivPlan job icons plus stack-frame role-label omission; the Yokai/O8S fixture checks Phase U page-title density and Phase V judgment geometry; the status-driven fixture checks Phase X per-player buff/debuff overlays.

Run the Phase S third-round release gate:

```powershell
& $py -m compileall -q xivplan-ffxiv-guide\scripts
& $py xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py
& $py xivplan-ffxiv-guide\scripts\test_storyboard_templates.py
& $py xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
& $py xivplan-ffxiv-guide\scripts\summarize_visual_reviews.py `
  artifacts\phase-i-visual-regression\visual-regression-results.json `
  --json-out artifacts\phase-s-release-gate\review-burndown.json `
  --markdown-out artifacts\phase-s-release-gate\review-burndown.md
& $py xivplan-ffxiv-guide\scripts\build_contact_sheets.py `
  --input-dir artifacts\phase-i-visual-regression `
  --output-dir artifacts\phase-s-release-gate\contact-sheets
& $py xivplan-ffxiv-guide\scripts\build_identity_crop_sheets.py `
  --input-dir artifacts\phase-i-visual-regression `
  --output-dir artifacts\phase-s-release-gate\identity-crop-sheets
```

The Phase S/U/V/W/X gate expects severe visual issues to remain 0, all 12 regression fixtures to pass the quality gate, every normal Boss/add to have a name/target ring/icon or fallback icon, every normal party frame to preserve unique role identity, and the crop sheets to show numbered-role main-flow icons plus `flow_example` job-icon readability in exported PNGs. The Phase U fixture must stay in the 10-14 step range and pass the in-scene annotation text threshold. Phase V additionally requires FRU and O8S semantic profiles to report `range_semantics_score=100.0`, `arrow_semantics_score=100.0`, real resolve geometry, and no undeclared danger crossing. Phase X requires `status_assignment_score=100.0` on the status-driven fixture, with all eight role-bound status overlays visible in every status-assignment frame.

Run the second-round visual release gate:

```powershell
& $py -m compileall -q xivplan-ffxiv-guide\scripts
& $py xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py
& $py xivplan-ffxiv-guide\scripts\test_storyboard_templates.py
& $py xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
& $py xivplan-ffxiv-guide\scripts\summarize_visual_reviews.py `
  artifacts\phase-i-visual-regression\visual-regression-results.json `
  --json-out artifacts\phase-n-release-gate\review-burndown.json `
  --markdown-out artifacts\phase-n-release-gate\review-burndown.md
& $py xivplan-ffxiv-guide\scripts\build_contact_sheets.py `
  --input-dir artifacts\phase-i-visual-regression `
  --output-dir artifacts\phase-n-release-gate\contact-sheets
```

The release gate expects no severe visual issues, no label/title obstruction, no severe movement-arrow issues, all current visual-regression fixtures passing the quality gate, regenerated contact sheets, and a review burndown. Semantic long-flow scenes use the Phase L/O density policy: `phase-l-semantic-long-flow` and `phase-o-teaching-long-flow` fixtures are accepted when they stay in the golden-sample density band, retain observe/move/resolve/reset coverage, and keep severe issues at 0.

For full pipeline outputs, the quality gate is run automatically. To inspect a generated case manually, use the per-version `quality-report.md` plus `scripts\validate_guide_package.py` and `scripts\audit_visual_density.py`.

Parse natural-language mechanic notes into Phase 10 IR:

```powershell
& $py xivplan-ffxiv-guide\scripts\parse_mechanic_request.py xivplan-ffxiv-guide\assets\parser-fixtures\ultimate-yokai-star-dance-p1-draft.input.md --encounter-name "Ultimate Yokai Star Dance" --phase P1 --source fixture
& $py xivplan-ffxiv-guide\scripts\test_mechanic_parser.py
```

The parser writes `artifacts\parsed-mechanics\<case>\mechanic-ir.json`, `timeline-ir.json`, `candidate-categories.json`, `unknowns.md`, and `parse-report.md`.

Search similar mechanics and write an adaptation report:

```powershell
& $py xivplan-ffxiv-guide\scripts\search_mechanic_knowledge.py --input xivplan-ffxiv-guide\assets\knowledge-fixtures\light-rampant-remix.input.md --json-out artifacts\knowledge-search\light-rampant-remix\knowledge-search.json --markdown-out artifacts\knowledge-search\light-rampant-remix\knowledge-search.md
& $py xivplan-ffxiv-guide\scripts\adapt_similar_mechanic.py --input xivplan-ffxiv-guide\assets\knowledge-fixtures\light-rampant-remix.input.md -o artifacts\knowledge-search\light-rampant-remix
& $py xivplan-ffxiv-guide\scripts\test_mechanic_knowledge_search.py
```

The adaptation report separates transferable principles from concrete positions that should not be copied.

The local XivPlan application source is expected beside this repository at `..\XivPlan`; it is not vendored here.
