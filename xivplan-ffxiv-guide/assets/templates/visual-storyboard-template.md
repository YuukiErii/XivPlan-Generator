# Visual Storyboard Template

Use this before writing a complex XivPlan spec. Keep each step focused on one visual question.

## Mechanic

- Encounter / phase:
- Mechanic name:
- Source notes:
- Known assumptions:
- Unknowns to carry into guide text:

## Scene Contract

```json
{
  "require_full_party_each_step": true,
  "require_enemy_each_step": true,
  "require_waymarks_each_step": true,
  "allow_partial_observation": false
}
```

Use `partial_observation: true` only for a local evidence frame, asset preview, or screenshot-derived crop. Explain the reason in `guide_text`.

## Arena

- Preset:
- Selection source: `user-specified` / `mechanic-inferred` / `default-fallback`
- Source reason:
- Waymarks:
- Initial Boss/enemy anchor:
- Initial party layout:

## Step Plan

| Step | `storyboard_phase` | `teaching_question` | Purpose | `why_this_frame_exists` | `changed_objects_only` | Visual focus | Required roles | Mechanic objects | Movement / flow | Reset state | Checks |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | observe_signal |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 2 | assign_roles |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 3 | preposition |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 4 | first_move |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 5 | first_resolve |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 6 | reset |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |
| 7 | next_read_setup |  |  |  |  |  | MT/ST/H1/H2/D1/D2/D3/D4 |  |  |  |  |

Add rows until the mechanic has enough frames. Simple mechanics usually use 3-5 steps, medium mechanics 6-10, complex mechanics 10-16, and long teaching flows 12-20 when each frame answers a distinct teaching question.

## Label Plan

| Label | Anchor object | Placement | Avoids | Leader line | Full explanation location |
|---|---|---|---|---|---|
|  |  | auto / fixed | party, enemy, mechanic, arrow, text | yes / no | guide_text / Markdown |

## Flow Plan

| Route | Actor(s) | `arrowStyle` | Start | Waypoints | End | Danger crossing allowed? | Notes |
|---|---|---|---|---|---|---|---|
|  |  | movement / preposition / micro / knockback / bait / forbidden / reset |  |  |  | false |  |

## Acceptance Notes

- Every normal step keeps 8 players, Boss/enemy anchor, arena context, and stable waymarks.
- Each step has exactly one primary `teaching_question`, plus `purpose`, `guide_text`, `checks`, `visual_focus`, `required_roles`, `storyboard_phase`, `reset_state`, `why_this_frame_exists`, and `changed_objects_only`.
- Severe label collisions, severe arrow obstruction, missing reset coverage, missing party context, missing Boss, or missing arena context must be fixed before handoff.
