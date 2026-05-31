# Guide JSON Format

`guide.json` is the Phase 6 bridge between XivPlan scene generation and shareable guide packages. It keeps image captions, guide prose, role assignments, short callouts, and source file pointers in one structured file.

Minimal shape:

```json
{
  "title": "四塔分摊散开",
  "summary": "先按四塔职责处理，再斜角散开，最后回中分摊。",
  "recommended_solution": "固定八方，DPS 斜角，T/H 内圈，降低换位和记忆成本。",
  "scene": "../generated-xivplan/phase5-multistep-style.xivplan",
  "spec": "../../xivplan-ffxiv-guide/assets/specs/phase5-multistep-style.spec.json",
  "figures": [
    {
      "step": 1,
      "title": "初始站位",
      "image": "images/step_01.png",
      "caption": "图 1：初始站位",
      "guide_text": "Boss 中央固定，八人按常规八方预站。"
    }
  ],
  "flow": [
    "机制开始前按八方预站。",
    "四塔出现后按固定职责踩塔。",
    "DPS 去斜角散开，T/H 留内圈。",
    "散开判定后全员回中分摊并复位。"
  ],
  "role_assignments": [
    { "role": "MT", "position": "北塔/北内圈", "task": "踩北塔，散开后回中分摊。" }
  ],
  "common_mistakes": ["踩塔后过早回中导致散开重叠。"],
  "short_callout": ["四塔：MT/H1 北，ST/H2 南，D2/D4 东，D1/D3 西。"],
  "mnemonic": "先塔，后散，最后回中。",
  "consistency_checks": ["四座塔均为 2 人塔。"],
  "unknowns": []
}
```

## Fields

| Field | Required | Notes |
|---|---|---|
| `title` | yes | Guide title and package title. |
| `summary` | yes | One- or two-sentence core rule. |
| `recommended_solution` | no | Strategy choice and tradeoffs. |
| `scene` | no | Relative path to the source `.xivplan`; copied to `scene.xivplan` if present. |
| `spec` | no | Relative path to the source spec; copied to `spec.json` if present. |
| `figures` | no | Ordered figure list. `image` paths are relative to `guide.json`. |
| `flow` | no | Detailed ordered handling flow. |
| `role_assignments` | no | Objects with `role`, `position`, and `task`. |
| `common_mistakes` | no | List of common failure modes. |
| `short_callout` | no | List of lines for the team-callout version. |
| `mnemonic` | no | Short phrase or callout. |
| `consistency_checks` | no | Validated visual/text checks. |
| `unknowns` | no | Explicit unresolved assumptions; use an empty list when none remain. |

## Assembly

Generate a complete package:

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\assemble_guide.py xivplan-ffxiv-guide\assets\sample-guides\phase5-multistep-guide.json -o artifacts\guide-packages\phase5-multistep-guide
```

Outputs:

```text
guide.json
guide.md
short-guide.md
guide.docx
guide.pdf
scene.xivplan
spec.json
images/
```

Short-callout only:

```powershell
& $py xivplan-ffxiv-guide\scripts\assemble_guide.py xivplan-ffxiv-guide\assets\sample-guides\phase5-multistep-guide.json -o artifacts\guide-packages\phase5-short --short-only
```
