# In-Scene Annotation Style

Phase U changes the default goal from "guide text explains the diagram" to "the diagram carries the key guide sentence itself".

## Contract

Generated complex mechanism scenes should include:

- `annotation_contract.require_in_scene_teaching: true`
- one `page_title` per normal step
- at least three non-title callouts per normal step
- callout labels no longer than 38 characters
- axis and priority labels when the mechanic has any positional branching
- a footer callout when long `guide_text` is preserved outside the diagram

## Label Roles

Use `labelRole` on text objects:

- `page_title`: 8-16 character page title derived from the step `teaching_question`.
- `axis`: arena or waymark language such as `AC/BD 轴线固定` or `南北 T/H 东西 DPS`.
- `priority`: role priority or branch rule such as `T/H 南北优先`.
- `mechanic`: local mechanic read such as `塔人数先确认`.
- `footer`: short action or exception line such as `移动前先读完`.
- `role_badge`: small party or role badges, mostly for `flow_example` scenes.

## Bands

Use `labelBand: "top" | "bottom" | "left" | "right"` with `labelBandIndex` for generated callouts. The builder places these labels in stable outside-arena bands so they can be dense without covering party icons, Boss rings, waymarks, AoE edges, or arrowheads.

Recommended generated slots:

- top left/right for axis and priority
- left/right upper side bands for local mechanic reads
- bottom left/right for action, reset, or exception reminders

## Text Length

- Page title: 8-16 characters when possible.
- Local label: 2-8 characters.
- Explanation band: 8-14 characters by default, never more than 38 characters.
- Long prose stays in `guide_text`, but complex scenes should put at least the critical read, priority, and action sentence into the figure.

## O8S / Yokai-Like Target

For a complex branch mechanic such as O8S / 妖星乱舞:

- target 10-14 steps
- target `140+` text objects or `900+` in-scene text characters
- every normal step should have page title, mechanic read, priority, and action/reset callouts
- branch pages should split different cases instead of mixing every condition into one generic frame
