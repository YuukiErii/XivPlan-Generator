# Artifacts

This directory is the default runtime output root for the guide-generation scripts.

Generated contents under `artifacts/` are intentionally ignored by Git except
for this README:

- exported step PNGs,
- generated Markdown / DOCX / PDF guide packages,
- quality-gate case copies,
- smoke-test outputs,
- versioned pipeline reports,
- local skill ZIP packages.

Source-like fixtures and persistent notes live outside this runtime directory:

- `xivplan-ffxiv-guide/assets/examples/generated-xivplan/`: curated lightweight
  `.xivplan` examples.
- `xivplan-ffxiv-guide/assets/progression-notes/ultimate-yokai-star-dance/`:
  source notes for the Ultimate Yokai Star Dance progression workflow.
- `docs/case-studies/ultimate-yokai-star-dance/`: persistent case-study notes
  and historical change-log snapshots.

Run the documented scripts in `README.md` to regenerate local derived artifacts.
