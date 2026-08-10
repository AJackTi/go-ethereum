# 0003. Publish the handbook to GitHub Pages from this repository

- **Status:** accepted
- **Date:** 2026-08-10
- **Deciders:** repository maintainer (local fork)
- **Follows:** [ADR-0002](0002-offline-first-bilingual-dev-docs.md), which kept a static-site
  generator as a deliberate later addition

## Context and problem statement

The handbook works from a checkout, which was the point. But sharing a link is easier than
sharing instructions to clone a 1 GB repository, and reading Markdown on GitHub gives no search,
no language switcher, and no navigation between the two language trees.

The constraint from ADR-0002 still holds: whatever we add must not make the offline, tool-free
reading path worse, and must not turn a build artifact into the source of truth.

## Considered options

- **A separate documentation repository** — small and fast to clone, but the docs would drift from
  the code they describe, and a change to a package would no longer travel with its documentation
  update in one commit.
- **Docusaurus in this repository** — the strongest i18n story, but adds a Node/React toolchain and
  does not produce a bundle that works from `file://`.
- **Material for MkDocs in this repository** — reads the existing Markdown almost unchanged, has a
  built-in `offline` plugin, and `mkdocs-static-i18n` covers the `en/` + `vi/` folder layout the
  handbook already uses.

## Decision

Material for MkDocs in this repository, deployed to GitHub Pages by GitHub Actions.

- `mkdocs.yml` at the repo root, `docs_dir: docs/dev`, output to a git-ignored `site/`.
- `mkdocs-static-i18n` in `folder` mode: English serves from `/`, Vietnamese from `/vi/`, and the
  language switcher is the theme's, not hand-rolled links.
- Builds run with `--strict`, so a broken internal link fails a pull request instead of shipping a
  404.
- Every CI run also produces `OFFLINE=true` output as a downloadable artifact — the same site,
  openable from `file://` with search intact.
- Two things are handled by a build hook rather than by duplicating content: the repo-root
  `ARCHITECTURE.md` is copied into the docs tree (git-ignored), and checkout-only links
  (`.tours/`, `AGENTS.md`, cross-language links) are rewritten for the web.

## Consequences

- Good: a shareable URL with real search and a language switcher, from the same files, with no new
  source of truth.
- Good: `--strict` in CI makes link rot a build failure rather than a reader's problem.
- Good: the offline requirement survives — both the raw Markdown and the offline bundle stay
  usable with no network.
- Bad: a Python toolchain is now required to *publish* (not to read), and Material for MkDocs has
  announced that MkDocs 2.0 will break the plugin system. Mitigation: versions are pinned with
  upper bounds in `docs/dev/requirements.txt`.
- Bad: links now have two audiences (GitHub and the site). Mitigation: the rewrite list lives in
  one file, `docs/dev/_hooks.py`, and the strict build catches mistakes.
- Neutral: Pages must be enabled by hand once — Actions allowed on the fork, Pages source set to
  GitHub Actions.
