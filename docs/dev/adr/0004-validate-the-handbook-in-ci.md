# 0004. Validate the handbook against the code in CI

- **Status:** accepted
- **Date:** 2026-08-10
- **Deciders:** repository maintainer (local fork)
- **Follows:** [ADR-0003](0003-publish-handbook-to-github-pages.md), which added `--strict` builds
  for the published site

## Context and problem statement

The handbook makes hundreds of concrete claims about the code: seven CodeTour walkthroughs anchored
by regex on function signatures, several hundred references to files and packages, and a Vietnamese tree
that is supposed to mirror the English one section for section.

Every one of those claims is true at the moment it is written and decays silently afterwards. A
rename in `core/` does not fail any test; it just leaves a tour step pointing at the wrong function,
and the reader who finds it stops trusting the rest of the handbook.

An audit found this happening in practice. `debug.metrics` was documented in ten places after the
method had been removed from geth, *eth/68* was named as the wire protocol when the implemented
versions are 69–72, and a state-test example pointed at a `tests/testdata/` directory that does not
exist. None of it was caught by the site build, because none of it is a broken link.

`mkdocs build --strict` only validates links between rendered pages. The failure mode here is
different: prose that still renders perfectly while being wrong.

## Considered options

- **Review discipline** — ask contributors to update the handbook when they move code. This is the
  status quo, and the audit shows what it produces.
- **Drop the precise references** — write prose that names packages but never functions or files.
  Cheaper to maintain, and much less useful; the precision is most of the value.
- **A checker script wired into CI** — encode the claims as assertions and fail the build.

## Decision

`docs/dev/check.py`, dependency-free Python, run in CI before the site build. Four checks:

1. **Tours** — valid JSON, every step's file exists, every step's `pattern` still matches, and no
   step is anchored by line number instead of a pattern.
2. **Code paths** — every file or package path written in backticks resolves.
3. **Links** — every relative Markdown link resolves in a plain checkout (the GitHub view, which
   the site build never sees).
4. **Mirror** — `vi/` and `en/` contain the same files, and each pair has the same number of `##`
   sections.

The docs workflow's path filter now includes `**.go`, so the check runs on the pull request that
changes the code rather than on the next documentation edit.

The site build covers what the script cannot. MkDocs logs two failure modes at INFO, where
`--strict` cannot see them: a page that exists but is absent from the nav, and a link to a heading
anchor that no longer exists. `mkdocs.yml` raises `validation.nav.omitted_files`,
`validation.nav.not_found`, `validation.links.anchors` and `validation.links.unrecognized_links` to
`warn`, which `--strict` turns into build failures.

## Consequences

- Good: a refactor that moves a documented function fails CI with the exact tour step and pattern
  named, on the PR that caused it.
- Good: no dependencies — it runs before the Python toolchain is installed and can be run locally
  in seconds.
- Bad: the docs workflow now triggers on Go changes, so it rebuilds and redeploys the site more
  often than the content strictly requires. The build takes seconds; the alternative is a second
  workflow duplicating the checkout.
- Bad: the mirror check compares section *counts*, not meaning. A translation can still drift in
  content while passing. Structural drift is the part worth automating; semantic drift stays a
  review question.
- Neutral: new tours must use `pattern`, never `line`. The checker enforces it, which is the point.
