# XivPlan Generator

Codex skill and local tooling for turning FFXIV mechanic descriptions into XivPlan diagrams and Chinese guide drafts.

## Contents

- `xivplan-ffxiv-guide/`: Codex skill package.
- `xivplan-ffxiv-guide/scripts/`: XivPlan scene generation and validation utilities.
- `xivplan-ffxiv-guide/assets/specs/`: compact mechanic specs used to generate `.xivplan` examples.
- `xivplan-ffxiv-guide/assets/image-assets/`: transparent PNG assets and placement manifests for image2/local PNG workflows.
- `xivplan-ffxiv-guide/assets/image-prompts/`: prompt templates for generated guide assets.
- `xivplan-ffxiv-guide/assets/sample-guides/`: `guide.json` examples and lightweight image fixtures.
- `xivplan-ffxiv-guide/assets/optimization/`: multi-candidate fixtures for strategy scoring.
- `xivplan-ffxiv-guide/assets/parser-fixtures/`: natural-language mechanic notes for parser regression tests.
- `xivplan-ffxiv-guide/assets/knowledge-fixtures/`: similar-mechanic retrieval fixtures.
- `artifacts/generated-xivplan/`: lightweight generated `.xivplan` examples for smoke testing.
- `artifacts/guide-packages/`: generated Markdown / DOCX / PDF guide package smoke outputs.
- `artifacts/solution-scores/`: lightweight JSON and Markdown strategy-score reports.
- `artifacts/parsed-mechanics/`: generated mechanic IR, timeline IR, category, unknown, and parse-report outputs.
- `artifacts/knowledge-search/`: generated knowledge-search JSON/Markdown and similarity reports.
- `artifacts/full-guide-pipeline/`: one-command guide package outputs.
- `artifacts/ultimate-yokai-star-dance/`: versioned Ultimate Yokai Star Dance progression workspace.
- `docs/roadmap.md`: full implementation roadmap.
- `docs/project-requirements.md`: original requirements snapshot.

Generated runtime outputs under `artifacts/` are ignored by default, except for
small source notes and documentation needed to regenerate them.

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

## One-Command Guide Generation

Generate a complete guide package from one mechanic Markdown file:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py input.md `
  --encounter-name "Encounter" `
  --phase P1 `
  --version v0.1-draft `
  --output-dir artifacts\full-guide-pipeline\my-case
```

The command writes parsed IR, knowledge matches, solution candidates, a scored recommendation, scene spec, `.xivplan`, step PNGs, Markdown / DOCX / PDF guide package, and a quality report. If rerunning the same output directory intentionally, add `--force`.

Generate Ultimate Yokai Star Dance progression output:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  artifacts\ultimate-yokai-star-dance\raw-notes\p1-draft-notes.md `
  --ultimate-yokai-star-dance `
  --version v0.1-draft
```

Generate the next observed version and append the change log:

```powershell
& $py xivplan-ffxiv-guide\scripts\run_full_guide_pipeline.py `
  artifacts\ultimate-yokai-star-dance\raw-notes\p1-observed-notes.md `
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
