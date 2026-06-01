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

## Enemy Identity

- [ ] Every Boss/add/clone/source has a non-empty name or display name.
- [ ] Every enemy has a visible target ring and radius / target-ring radius.
- [ ] Every enemy has a dedicated icon or an explicit fallback icon.
- [ ] Enemy asset manifest entries match the generated `.xivplan` data URLs or clearly record fallback status.
- [ ] Same-name adds are disambiguated by direction or index.
- [ ] Enemy labels do not have severe obstruction from text, arrows, players, or high-opacity mechanics.
- [ ] Facing is visible or encoded when cleaves, body checks, or relative directions matter.

## Party Identity

- [ ] Every normal non-cluster frame has eight unique roles: MT, ST, H1, H2, D1, D2, D3, D4.
- [ ] Every party object has an official XivPlan `/actor/<JOB>.png` job icon plus a nearby role label.
- [ ] Default jobs match the Phase R/S comp, with MT=/actor/DRK.png, ST=/actor/PLD.png, H1=/actor/AST.png, H2=/actor/SCH.png, D1=/actor/SAM.png, D2=/actor/DRG.png, D3=/actor/BRD.png, D4=/actor/PCT.png, or are intentionally overridden by the user/static.
- [ ] No default party icon is an abstract `job:*` token, generic role icon, or text-only abbreviation badge.
- [ ] Cluster/stack frames keep job icons readable when role labels are hidden.
- [ ] Job icons remain readable in exported PNG contact sheets.

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

## Layering And Aesthetics

- [ ] Large AoE and safe/danger regions sit below players and text.
- [ ] Player icons and role labels remain readable at normal export scale.
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
