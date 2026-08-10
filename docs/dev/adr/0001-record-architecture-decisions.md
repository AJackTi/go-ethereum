# 0001. Record architecture decisions

- **Status:** accepted
- **Date:** 2026-08-10
- **Deciders:** repository maintainer (local fork)

## Context and problem statement

Code shows *what* the system does. It rarely shows *why* it does it that way. In a codebase this
size, the reasons live in pull request threads, issue comments, and people's heads — all of which
are unavailable when you are reading offline, and all of which decay.

The recurring cost is concrete: someone "cleans up" a workaround that existed for a reason, or
re-litigates a tradeoff that was already settled two years ago.

## Considered options

- **Nothing** — keep relying on git history and PR discussions.
- **A single DECISIONS.md** — one growing file.
- **One Markdown file per decision (ADR)** in `docs/dev/adr/`, MADR minimal format.

## Decision

One Markdown file per decision, MADR minimal format, in `docs/dev/adr/`.

A decision earns an ADR when it (a) is hard to reverse, (b) constrains future work, or (c) will
look wrong to someone who does not know the context. Everything else stays in commit messages.

## Consequences

- Good: the "why" travels with the code and is readable with no network and no tooling.
- Good: a superseded decision stays visible instead of vanishing — the trail is the value.
- Bad: it only works if records get written at decision time. An ADR written three months late is
  a summary, not a record.
- Neutral: numbering must be kept unique by hand.
