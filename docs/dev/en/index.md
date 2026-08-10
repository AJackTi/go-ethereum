# go-ethereum developer handbook

A map for people who have to **read and change** this codebase — not a protocol spec, and not a
user manual for running a node.

Everything here is plain Markdown in the repository. The website is a convenience; the working
tree is the source of truth. No internet and no AI agent is required to use any of it.

---

## Where do I start?

<div class="grid cards" markdown>

- :material-map: **[Architecture](architecture.md)**

    The code map. Four layers, entry points per question, what every package does, the six flows
    that matter. Read this first.

- :material-wrench: **[I want to change X](start-here.md)**

    Task-oriented index: the first file to open, the other places the change touches, and how to
    prove it works.

- :material-school: **[Learning path](learning-path.md)**

    Eight weeks from `make geth` to a first pull request, with exercises and a checkpoint you can
    answer alone.

- :material-file-document-multiple: **[Decisions](../adr/index.md)**

    Why the handbook and its tooling are built this way — one record per decision.

</div>

---

## Guided tours inside the editor

Two click-through walkthroughs ship in the repo under
[`.tours/`](https://github.com/AJackTi/go-ethereum/tree/master/.tours):

| Tour | What it covers |
| --- | --- |
| **01 · Node startup** | Command line → config → `node.Node` → `eth.Ethereum` → running services |
| **02 · Block import** | `engine_newPayload` → `InsertChain` → EVM → state root check → bytes on disk |

Install the VS Code extension `vsls-contrib.codetour` once, open the CodeTour panel, pick a tour.
After the install it works entirely offline — no service, no model.

Steps are anchored by regex on function signatures, not line numbers, so refactors do not silently
point a tour at the wrong code.

---

## How this handbook is organised

Four document types, deliberately kept apart ([Diátaxis](https://diataxis.fr/)):

| Type | Answers | Where |
| --- | --- | --- |
| Tutorial | "Teach me this codebase" | Learning path, `.tours/` |
| How-to | "I need to change X" | I want to change X |
| Reference | "Where is Y?" | Architecture, `go doc` |
| Explanation | "Why is it built this way?" | Decisions, the invariants section |

Mixing them is the usual failure mode: a tutorial that also explains theory helps nobody.

---

## Offline usage

```shell
# read it straight from the checkout — nothing to install
$EDITOR ARCHITECTURE.md docs/dev/en/start-here.md

# API reference for every package, no network
go doc ./core/vm
go doc ./core/vm EVM.Run

# or the full pkg.go.dev experience, served locally
go install golang.org/x/pkgsite/cmd/pkgsite@latest
pkgsite -http :8080
```

Want this website on a machine with no connection? Build the self-contained bundle and copy it:

```shell
OFFLINE=true mkdocs build     # site/ opens straight from file://
```

---

## Language policy

English is canonical; Vietnamese mirrors it 1:1 with the same headings in the same order. If the
two ever disagree, English wins. Code, identifiers and commands are never translated.
