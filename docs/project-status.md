# XivPlan Generator Project Status

Updated: 2026-06-04

This is the single control document for repo-level requirements, roadmap state,
visual-upgrade progress, acceptance evidence, and next work. It replaces the
older separate roadmap, visual-upgrade plan, work-record, first-round audit, and
requirements snapshot files. Detailed historical prose remains available in git
history.

## Product Goal

Build a Codex skill and local toolchain that can turn FFXIV mechanic notes into
beautiful, importable XivPlan diagrams plus Chinese guide text.

The original requirements are preserved here in compact form:

- Understand common FFXIV mechanic patterns such as stack, spread, gaze,
  knockback, towers, tethers, debuffs, limit-cut ordering, and role positions.
- Recognize representative Savage and Ultimate mechanics from 4.x onward,
  including "similar to X" analogy requests.
- Recommend practical solutions that reduce caster movement, reduce memory load,
  and preserve melee uptime when possible.
- Match the visual and information-density standard of local KING X
  `Strats_limited` `.xivplan` files.
- Support custom local PNG assets for guide-specific icons such as O8S skulls or
  M6S animals when built-in XivPlan resources are insufficient.
- Use the adjacent local XivPlan app when app-side behavior needs to change.

## Public Layout

Use this layout as the current naming and placement rule:

| Area | Role |
|---|---|
| `xivplan-ffxiv-guide/` | Codex skill package. |
| `xivplan-ffxiv-guide/scripts/` | Scene generation, validation, audit, and pipeline utilities. |
| `xivplan-ffxiv-guide/references/` | Stable mechanic, arena, schema, style, and workflow references. |
| `xivplan-ffxiv-guide/assets/` | Source fixtures, specs, curated examples, prompts, sample images, and progression notes. |
| `docs/project-status.md` | This consolidated repo-level control document. |
| `docs/case-studies/` | Durable case-specific notes that should remain readable outside `artifacts/`. |
| `artifacts/` | Ignored local runtime outputs, reports, generated guides, packages, and QA evidence. |

Generated outputs stay under `artifacts/` and should not be committed unless a
future task explicitly promotes a small, durable artifact into `docs/` or
`xivplan-ffxiv-guide/assets/`.

## Current Status

The repo has working coverage for:

- natural-language mechanic parsing into mechanic IR;
- similar-mechanic retrieval and analogy reports;
- solution planning and scoring;
- XivPlan scene spec generation;
- importable `.xivplan` generation;
- visual quality auditing and visual regression;
- arena preset routing, including FRU, Eden-light, O8S fallback, tile, default,
  and UDM / Ultimate Yokai Star Dance phase-specific arenas;
- Boss/add identity contracts with target rings, labels, radius, and fallback or
  sourced icons;
- status-assignment overlays for buff/debuff-driven mechanics;
- XivPlan-only default pipeline output, with full guide packages behind
  `--full-package`.

Current validated default behavior:

- User-facing generation defaults to `.xivplan` plus parse, candidate, spec, and
  quality evidence.
- Step PNG, SVG, Markdown, DOCX, and PDF output is generated only when
  `--full-package` is explicitly requested or when regression QA asks for it.
- `artifacts/` is ignored; only `artifacts/README.md` is tracked.

## Roadmap Status

### Foundation

| Phase | Status | Notes |
|---|---|---|
| Phase 0 | Complete | Requirements and local sample baseline established. |
| Phase 1 | Complete | Local PNG/image workflow and portable scene assets supported. |
| Phase 2 | Complete | Step export and guide-package assembly path exists for QA/release. |
| Phase 3 | Complete | Encounter knowledge cards cover representative Ultimate and Savage mechanics. |
| Phase 4 | Complete | Solution candidate scoring supports practical strategy choices. |
| Phase 5 | Complete | Scene spec generation produces richer XivPlan object language. |
| Phase 6 | Complete | Guide assembly supports Markdown / DOCX / PDF when requested. |
| Phase 7 | Complete | Image asset workflow supports custom icons and manifests. |
| Phase 8 | Complete | End-to-end cases generate specs, scenes, images, manifests, and guide packages. |
| Phase 9 | Complete | Quality gates and visual audits are integrated. |
| Phase 10 | Complete | Natural-language parser preserves categories, timeline order, and unknowns. |
| Phase 11 | Complete | Mechanic knowledge search supports analogy migration. |
| Phase 12 | Complete | Planning v2 supports candidate generation and risk reporting. |
| Phase 13 | Complete | Ultimate Yokai Star Dance progression workspace exists. |
| Phase 14 | Complete | Skill documentation and one-command entrypoints are integrated. |

### Visual Upgrade

| Phase | Status | Outcome |
|---|---|---|
| A-I | Complete | First-round scene baselines, arena selection, context preservation, label layout, arrows, storyboard v2, quality gate v2, docs, and golden fixtures. |
| J-N | Complete | Review burndown, label/flow polish, long-flow reconstruction, PNG human review, release gate. |
| O-S | Complete | Teaching storyboard metadata, enemy identity contract, enemy icon workflow, party/job icon routing, third-round release gate. |
| T | Complete | Gold-reference comparison and strict-vs-gold audit separation. |
| U | Complete | In-scene page titles, priority labels, axis labels, callouts, and footer teaching text. |
| V | Complete | Route/range semantics, resolve timing, damage intent, and hard gate scoring. |
| W | Complete | Arena/resource gate, O8S fallback overlays, UDM/Yokai arena discovery, and contact-sheet readiness. |
| X | Complete | Buff/debuff ownership overlays and status assignment scoring. |
| Y | Complete | UDM P1-P3 gold-reference absorption and XivPlan-only default output mode. |

## Phase Y Summary

Phase Y is the current latest completed phase.

Implemented:

- UDM P1/P2/P3 gold references were profiled from local `.xivplan` and
  `.xivplancn` folders under `C:\Users\Mahiru\Desktop\FFXIV\KING X\UDM`.
- `references/encounters/ultimates/udm.md` records phase-specific arena routing,
  density baselines, lightweight object language, and output policy.
- `udm-p1`, `udm-p2`, `udm-p3`, and `udm-p4` arena presets were added.
- Parser routing now resolves `绝妖星乱舞` / UDM before generic `妖星乱舞` /
  O8S fallback.
- `run_full_guide_pipeline.py` and
  `run_ultimate_yokai_star_dance_pipeline.py` default to XivPlan-only output.
- `run_visual_regression.py` explicitly requests `--full-package` so QA still
  gets contact sheets and rendered evidence.

Gold-reference profile:

- 10 scenes, 84 steps, 1972 objects, median 23 objects per step.
- Common backgrounds include `/arena/udm-phase1.png`,
  `/arena/udm-phase2.png`, remote Kefka floor images, and `/arena/udm-p4.png`.
- Generated UDM scenes should target roughly 20-30 meaningful objects per normal
  step without copying large embedded PNG data URLs from the reference files.

## Validation Commands

Use bundled Python on this machine:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m compileall -q xivplan-ffxiv-guide\scripts
& $py xivplan-ffxiv-guide\scripts\test_visual_quality_audit.py
& $py xivplan-ffxiv-guide\scripts\test_storyboard_templates.py
& $py xivplan-ffxiv-guide\scripts\test_mechanic_parser.py
& $py xivplan-ffxiv-guide\scripts\test_arena_selection.py
& $py xivplan-ffxiv-guide\scripts\test_solution_optimizer.py
& $py xivplan-ffxiv-guide\scripts\run_visual_regression.py --force
```

Latest verified evidence from the cleanup pass:

- `compileall`: PASS.
- Visual quality audit test: PASS.
- Storyboard template test: PASS.
- Mechanic parser test: PASS.
- Arena selection test: PASS.
- Solution optimizer test: PASS.
- Ultimate Yokai smoke: PASS, `mode: xivplan-only`.
- Visual regression: PASS, `12/12 cases`.
- Visual review summary: `review_items=347`, `severe_items=0`.
- `git diff --check`: PASS.

## Open Follow-Ups

These are non-blocking polish items, not release blockers:

- Some fixtures still carry review-class dense-label or leader-line notes, but
  severe issues are 0.
- `light-rampant-like` keeps one content unknown about real fight eligibility or
  grouping confirmation; this is input uncertainty rather than visual failure.
- Exact official status icon sourcing can replace deterministic fallback badges
  when a future asset task needs it.
- Concrete UDM phase work should keep using
  `references/encounters/ultimates/udm.md` and local gold folders as the style
  source of truth.

## Maintenance Rule

Future repo-level updates should modify this file instead of creating new
one-off roadmap, work-record, audit, or requirements markdown files. Create a
new document only when it is a durable case study, a stable reference card, or a
user-facing guide artifact.
