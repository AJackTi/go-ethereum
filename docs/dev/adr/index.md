# Architecture decision records

Why things are the way they are. One file per decision, [MADR minimal](https://adr.github.io/madr/)
format. English only — these are records, not teaching material.

A decision earns a record when it is hard to reverse, constrains future work, or will look wrong
to someone who does not know the context. Everything else belongs in a commit message.

| # | Decision | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | accepted | 2026-08-10 |
| [0002](0002-offline-first-bilingual-dev-docs.md) | Offline-first, bilingual developer documentation | accepted | 2026-08-10 |
| [0003](0003-publish-handbook-to-github-pages.md) | Publish the handbook to GitHub Pages from this repository | accepted | 2026-08-10 |
| [0004](0004-validate-the-handbook-in-ci.md) | Validate the handbook against the code in CI | accepted | 2026-08-10 |

New record: copy [`0000-template.md`](0000-template.md), take the next number, never reuse one.
To change an accepted decision, write a new record and mark the old one *superseded* — the trail
is the value.
