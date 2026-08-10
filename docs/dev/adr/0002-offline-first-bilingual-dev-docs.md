# 0002. Offline-first, bilingual developer documentation

- **Status:** accepted
- **Date:** 2026-08-10
- **Deciders:** repository maintainer (local fork)

## Context and problem statement

Two hard requirements shaped this handbook:

1. **It must work with no internet and no AI agent.** Onboarding cannot depend on a hosted docs
   site, a search service, or a model being available.
2. **It must serve two languages, Vietnamese and English**, without the two drifting apart into
   contradicting answers.

The repository already had `AGENTS.md` (rules for committing) and `README.md` (how to build), but
nothing that answered "where do I start reading?" or "I want to change X, which file?".

## Considered options

- **A hosted docs site** (Docusaurus, Read the Docs) with i18n plugins — good multilingual support,
  but the reading experience assumes a browser and a build step, and violates requirement 1 unless
  built and shipped as static files.
- **MkDocs Material with the `offline` plugin** — produces a static site that works from `file://`
  with working search. Good, but requires a Python toolchain to rebuild, and the source of truth
  becomes a build artifact.
- **Plain Markdown in the repo, plus CodeTour for guided walkthroughs** — no build step, readable
  in any editor or `less`, versioned with the code it describes.

## Decision

Plain Markdown in the working tree, organised by [Diátaxis](https://diataxis.fr/), plus CodeTour
JSON for in-editor walkthroughs:

- `ARCHITECTURE.md` at the repo root — the code map (the widely used convention; it is the first
  place both humans and tools look).
- `docs/dev/{en,vi}/` — mirrored trees, ISO 639-1 directory names, identical filenames and heading
  structure. English is canonical; Vietnamese is a translation.
- `docs/dev/adr/` — decisions, English only.
- `.tours/*.{en,vi}.tour` — CodeTour walkthroughs, one file per language.
- Offline API reference is delegated to the Go toolchain (`go doc`, or `pkgsite` locally).

CodeTour steps anchor with `pattern` (a regex over the file) rather than `line`, so a refactor
that shifts line numbers does not silently point the tour at the wrong code.

MkDocs Material with the `offline` plugin stays available as a later addition: it can render these
same Markdown files into a searchable static site without changing the source of truth.

## Consequences

- Good: zero dependencies to *read*. `git clone` and you have the docs; no network, no model, no
  build.
- Good: docs live in the same commit as the code they describe, so review catches drift.
- Good: the language split is mechanical — a reviewer can see at a glance whether `vi/` mirrors
  `en/`.
- Bad: every content change is double work, and translations will lag. Mitigation: English wins on
  conflict, and untranslated sections are marked `> TODO(vi): chưa dịch` rather than silently
  diverging.
- Bad: no full-text search across the handbook beyond `grep`. Accepted; `grep -rn` over a handful
  of Markdown files is fast enough.
- Neutral: CodeTour requires a one-time extension install and only works in VS Code. The Markdown
  files stand alone without it.
