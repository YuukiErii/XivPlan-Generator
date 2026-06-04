# Visual Quality Checklist

Run this before final handoff, alongside `scripts/audit_visual_quality.py`.

## Context

- [ ] Every normal step has MT, ST, H1, H2, D1, D2, D3, D4.
- [ ] Every normal step has a Boss, enemy, add, or explicit mechanic source.
- [ ] Every normal step has arena context or a justified `partial_observation`.
- [ ] A/B/C/D or equivalent waymarks are stable when orientation matters.

## Storyboard

- [ ] The scene covers observation / signal reading.
- [ ] The scene covers assignment.
- [ ] The scene covers movement or prepositioning.
- [ ] The scene covers resolution / damage / responsibility check.
- [ ] The scene covers reset or next-read setup.
- [ ] Each step has exactly one `teaching_question`.
- [ ] Each step explains why the frame exists and what changed from the previous step.

## In-Scene Teaching

- [ ] Generated complex scenes declare `annotation_contract.require_in_scene_teaching: true`.
- [ ] Every normal step has a rendered `page_title` derived from its `teaching_question`.
- [ ] Every normal step has at least three non-title callouts with `labelRole` such as `axis`, `priority`, `mechanic`, or `footer`.
- [ ] Axis and priority callouts are present when branch, waymark, or role-order judgment matters.
- [ ] Callouts stay under 38 characters and mostly fit the 4-14 character scan range.
- [ ] Complex O8S/Yokai-like scenes reach 10-14 steps and either `140+` text objects or `900+` in-scene text characters.

## Enemy Identity

- [ ] Every Boss/add/clone/source has a non-empty name or display name.
- [ ] Every enemy has a visible target ring and radius / target-ring radius.
- [ ] Every enemy has a dedicated icon or an explicit fallback icon.
- [ ] Known Bosses have a Huiji/wiki/search report or user/screenshot source before a dedicated icon is accepted.
- [ ] Dedicated Boss icon manifests include `source_url`, `source_page_title`, `visual_traits`, `icon_brief`, `generated_icon_path`, and `license_note`.
- [ ] Dedicated Boss icons are original simplified guide art, not copied wiki/game images.
- [ ] Enemy asset manifest entries match the generated `.xivplan` data URLs or clearly record fallback status.
- [ ] Same-name adds are disambiguated by direction or index.
- [ ] Enemy labels do not have severe obstruction from text, arrows, players, or high-opacity mechanics.
- [ ] Facing is visible or encoded when cleaves, body checks, or relative directions matter.

## Party Identity

- [ ] Every normal non-cluster frame has eight unique roles: MT, ST, H1, H2, D1, D2, D3, D4.
- [ ] `mechanic_flow` frames use official numbered role icons: `/actor/tank1.png`, `/actor/tank2.png`, `/actor/healer1.png`, `/actor/healer2.png`, `/actor/dps1.png` through `/actor/dps4.png`.
- [ ] `flow_example` frames use official XivPlan `/actor/<JOB>.png` job icons plus nearby role labels.
- [ ] `flow_example` default jobs match the Phase R/S comp, with MT=/actor/DRK.png, ST=/actor/PLD.png, H1=/actor/AST.png, H2=/actor/SCH.png, D1=/actor/SAM.png, D2=/actor/DRG.png, D3=/actor/BRD.png, D4=/actor/PCT.png, or are intentionally overridden by the user/static.
- [ ] No default party icon is an abstract `job:*` token or text-only abbreviation badge.
- [ ] Cluster/stack `flow_example` frames keep job icons readable when role labels are hidden.
- [ ] Party icons remain readable in exported PNG contact sheets.

## Labels

- [ ] No severe text-to-text collision remains.
- [ ] Labels do not cover players, Boss/enemy anchors, towers, stacks, or key AoE boundaries.
- [ ] Labels do not cover arrowheads.
- [ ] Long explanations are in `guide_text` or Markdown, not crammed into the arena.
- [ ] Moved labels have leader lines or clear anchors.

## Flow

- [ ] Main movement uses `arrowStyle: "movement"`.
- [ ] Preposition, micro, knockback, bait, forbidden, and reset routes use their semantic styles.
- [ ] Routes use waypoints/path/polyline/curve when a straight arrow would cross mechanics.
- [ ] Arrowheads do not obscure players, Boss, markers, or text.
- [ ] Dangerous-zone crossings are either avoided or explicitly marked as intentional.

## Phase V Mechanic Semantics

- [ ] Generated complex scenes declare `mechanic_semantics_contract`.
- [ ] Every movement/reset route has a source, target, intent, `resolveIndex`, and boolean `snapToTarget`.
- [ ] Legal endpoint snaps name the target role, marker, object, or zone; undeclared arrowhead obstruction remains severe.
- [ ] Every critical AoE has `damagePattern.kind`, `label`, `source`, `targets`, `resolveIndex`, `resolveTiming`, and `aoeIntent`.
- [ ] `aoeIntent` distinguishes current damage from `safe`, `bait_history`, `future_resolve`, and `reference_only`.
- [ ] Every resolve frame has real semantic geometry, not only generic circles and arrows.
- [ ] FRU and O8S release fixtures report `range_semantics_score=100.0` and `arrow_semantics_score=100.0`.

## Phase W Arena And Product Gate

- [ ] `scripts/scan_xivplan_assets.py` was run when encounter-specific backgrounds matter.
- [ ] FRU/Fatebreaker P1 diagrams use `/arena/e11.svg` unless the user explicitly requests another background.
- [ ] UDM / 绝妖 diagrams use phase-specific `udm-p1` / `udm-p2` / `udm-p3` local backgrounds when phase context is known.
- [ ] O8S/Omega/妖星乱舞 fallback scenes record `sourceReason: "no built-in O8S arena asset found; fallback to default-circle with explicit axis overlays"`.
- [ ] Fallback arena scenes include visible `arenaOverlays` for radial ticks and AC/BD axes, plus waymarks and Boss target rings.
- [ ] `export_xivplan_steps.py` contact-sheet PNGs show the actual raster background when available, or an explicit arena overlay/fallback note when it is not.
- [ ] Final human review covers text, Boss identity/icon, arrows, ranges, background, waymarks, and flow completeness.

## Output Mode

- [ ] Default user-facing generation produced only `.xivplan` plus parse/solution/quality evidence.
- [ ] Step PNGs, SVGs, Markdown, DOCX, or PDF were generated only because a full-package or release/regression QA command explicitly requested them.

## Phase X Status Assignments

- [ ] Buff/debuff or status-driven scenes declare `status_assignment_contract`.
- [ ] `statusAssignments` binds every critical status to a concrete `MT/ST/H1/H2/D1/D2/D3/D4` role.
- [ ] Every assigned role has a readable upper-left `statusOverlay` icon on the party icon in every visible step.
- [ ] Status overlays preserve `statusRole`, `statusName`, `decisionGroup`, `anchorRole`, and `anchorPartyId`.
- [ ] Fallback status badges record `assetStatus: "fallback"`, `assetFallback: "status-icon-fallback"`, and a concrete `fallbackReason`.
- [ ] `status_assignment_score` is `100.0` for status-driven release fixtures.

## Layering And Aesthetics

- [ ] Large AoE and safe/danger regions sit below players and text.
- [ ] Player icons and any visible role labels remain readable at normal export scale.
- [ ] Opacity does not bury towers, stacks, role markers, or safe spots.
- [ ] Color semantics are stable: danger, safety, movement, and role groups do not contradict each other.
- [ ] Dense long-flow scenes are split into enough steps instead of forcing all logic into one frame.

## Gate Result

- Command:

```bash
python xivplan-ffxiv-guide/scripts/audit_visual_quality.py path/to/scene.xivplan --json-out artifacts/visual-quality-results.json --markdown-out artifacts/visual-quality-report.md
```

- [ ] `status` is `PASS` or `REVIEW`.
- [ ] `severe_items` is 0.
- [ ] Review items are either fixed or listed for manual polish with step/object pointers.
