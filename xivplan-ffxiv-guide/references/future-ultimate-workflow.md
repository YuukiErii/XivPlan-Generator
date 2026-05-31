# Future Ultimate Workflow

This reference defines the short-progression workflow for a new ultimate fight such as Ultimate Yokai Star Dance.

## Version Labels

| Version | Meaning | Required Discipline |
|---|---|---|
| `v0.1-draft` | Based on spoken notes, first pulls, screenshots, or placeholder planning. | Preserve assumptions and unknowns. Do not publish as a final strategy. |
| `v0.2-observed` | Adds observed targeting rules or resolution order. | Record what changed from v0.1 and keep both versions. |
| `v0.3-stabilized` | Standing positions and movement routes are stable for the group. | Remaining unknowns should be non-blocking. |
| `v1.0-release` | Public guide package. | Wording must separate confirmed mechanics from optional variants. |

## Iteration Rules

- Update raw notes first. Generated artifacts are derived from notes, not edited as the source of truth.
- Generate each version into its own folder. Do not overwrite older version outputs during progression.
- Every version must list:
  - new confirmations,
  - disproved assumptions,
  - still-pending unknowns.
- Knowledge matches are analogies only. Do not copy old-fight positions unless the new mechanic confirms them.
- Guides may recommend a conservative solution, but the text must not present unconfirmed targeting as fact.

## Output Surface

Each generated version should include:

- parsed mechanic and timeline IR,
- local knowledge analogy report,
- candidate solution JSON and Markdown comparison,
- generated scene spec and `.xivplan`,
- exported step PNGs,
- Markdown, DOCX, and PDF guide package,
- risk / unknown list,
- quality gate report.
