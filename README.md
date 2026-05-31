# XivPlan Generator

Codex skill and local tooling for turning FFXIV mechanic descriptions into XivPlan diagrams and Chinese guide drafts.

## Contents

- `xivplan-ffxiv-guide/`: Codex skill package.
- `xivplan-ffxiv-guide/scripts/`: XivPlan scene generation and validation utilities.
- `xivplan-ffxiv-guide/assets/specs/`: compact mechanic specs used to generate `.xivplan` examples.
- `artifacts/generated-xivplan/`: lightweight generated `.xivplan` examples for smoke testing.
- `ff14-xivplan-guide-skill-plan.md`: full implementation roadmap.
- `project-requirements.md`: original requirements snapshot.

## Validate

Use the bundled Codex Python on this Windows machine if `python` is not on PATH.

```powershell
$py = "C:\Users\Mahiru\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py xivplan-ffxiv-guide\scripts\build_xivplan_scene.py xivplan-ffxiv-guide\assets\specs\tower-cardinals.spec.json -o artifacts\generated-xivplan\tower-cardinals.xivplan
& $py xivplan-ffxiv-guide\scripts\validate_xivplan_scene.py artifacts\generated-xivplan\tower-cardinals.xivplan
```

The local XivPlan application source is expected beside this repository at `..\XivPlan`; it is not vendored here.
