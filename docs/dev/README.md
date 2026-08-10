# Developer handbook · Sổ tay lập trình viên

Offline-first navigation for this repo. No internet, no AI agent required — everything here is
plain files in the working tree, readable in any editor.

Điều hướng offline cho repo này. Không cần internet, không cần AI agent — tất cả là file thường
trong cây mã, đọc bằng editor nào cũng được.

---

## Start here · Bắt đầu ở đây

| | English | Tiếng Việt |
| --- | --- | --- |
| Never built geth before | [`en/getting-started.md`](en/getting-started.md) | [`vi/getting-started.md`](vi/getting-started.md) |
| Code map — what lives where | [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) | [`vi/architecture.md`](vi/architecture.md) |
| "I want to change X" | [`en/start-here.md`](en/start-here.md) | [`vi/start-here.md`](vi/start-here.md) |
| Learning path, 8 weeks | [`en/learning-path.md`](en/learning-path.md) | [`vi/learning-path.md`](vi/learning-path.md) |
| Deploy and operate a node | [`en/run-a-node.md`](en/run-a-node.md) | [`vi/run-a-node.md`](vi/run-a-node.md) |
| Tests, tracers, pprof, delve | [`en/debugging.md`](en/debugging.md) | [`vi/debugging.md`](vi/debugging.md) |
| Build *on* geth (ethclient, abigen) | [`en/using-geth.md`](en/using-geth.md) | [`vi/using-geth.md`](vi/using-geth.md) |
| The 13 tools in `cmd/` | [`en/tools.md`](en/tools.md) | [`vi/tools.md`](vi/tools.md) |
| Terminology, EN ↔ VI | [`en/glossary.md`](en/glossary.md) | [`vi/glossary.md`](vi/glossary.md) |
| Why things are the way they are | [`adr/`](adr) | [`adr/`](adr) (English only) |
| Guided walkthrough in the editor | [`../../.tours/`](../../.tours) | [`../../.tours/`](../../.tours) |

---

## How this handbook is organised

Four document types, kept separate on purpose ([Diátaxis](https://diataxis.fr/)):

| Type | Answers | Lives in |
| --- | --- | --- |
| **Tutorial** — learning | "Teach me this codebase" | `learning-path.md`, `.tours/` |
| **How-to** — a task | "I need to change X" | `start-here.md` |
| **Reference** — facts | "Where is Y?" | `ARCHITECTURE.md`, `go doc` |
| **Explanation** — why | "Why is it built this way?" | `adr/`, ARCHITECTURE invariants |

Mixing them is the common failure: a tutorial that also explains theory helps nobody.

---

## Language policy · Quy tắc ngôn ngữ

- **English is canonical.** Vietnamese pages are translations that mirror the English structure
  1:1 (same headings, same order). If the two disagree, English wins.
- Directories use ISO 639-1 codes: `en/`, `vi/`. Same filename in both trees.
- Code, identifiers, commands, and technical terms stay in English in both languages —
  translate the prose, never the API.
- Update order: change `en/` first, then `vi/` in the same commit. Anything left untranslated
  gets a line at the top of the section: `> TODO(vi): chưa dịch`.
- ADRs are English-only. They are records of a decision, not teaching material.

---

## The published website

The same Markdown is published at **<https://ajackti.github.io/go-ethereum/>** (Vietnamese at
`/vi/`), built by [`.github/workflows/docs.yml`](../../.github/workflows/docs.yml) on every push
to `master` that touches the handbook. The working tree stays the source of truth — the site is
generated from it, never the other way round.

```shell
python3 -m venv .venv
.venv/bin/pip install -r docs/dev/requirements.txt

.venv/bin/mkdocs serve                          # live preview on http://127.0.0.1:8000
.venv/bin/mkdocs build --strict                 # -> site/
OFFLINE=true .venv/bin/mkdocs build --strict    # -> site/ that works from file://
```

`--strict` fails the build on a broken internal link, so a typo cannot ship a 404. The offline
build is also attached to every CI run as the `handbook-offline` artifact: download, unzip, open
`index.html` — full site, search included, no server and no network.

Two build-time details worth knowing (both handled by [`_hooks.py`](_hooks.py)):

- `docs/dev/en/architecture.md` is **generated** from the repo-root `ARCHITECTURE.md` and is
  git-ignored. Edit the root file.
- Links are written to be correct when browsing the repo on GitHub; the hook rewrites the few
  checkout-only targets (`.tours/`, `AGENTS.md`, cross-language links) when building the site.

Prerequisites in repository settings, once: **Actions → General** must allow workflows (forks
start with them disabled), and **Pages → Source** must be set to *GitHub Actions*.

---

## Offline API reference

Godoc for every package in this repo and its dependencies, without a network:

```shell
go doc ./core/vm                                # one package, in the terminal
go doc ./core/vm EVM.Run                        # one symbol
go install golang.org/x/pkgsite/cmd/pkgsite@latest   # once, needs internet
pkgsite -http :8080                             # then browse http://localhost:8080 offline
```

`go doc` needs nothing but the toolchain. `pkgsite` renders the same pages as pkg.go.dev from
your local module cache.

---

## Guided tours (`.tours/`)

[CodeTour](https://github.com/microsoft/codetour) turns a JSON file into a click-through
walkthrough inside VS Code — offline, no service, no AI.

1. Install the extension `vsls-contrib.codetour` (one-time, needs internet).
2. Open the CodeTour panel in the Explorer sidebar and pick a tour.
3. `Ctrl/Cmd+Right` walks forward; each step jumps to the exact code and explains it.

Tours in this repo are suffixed by language: `*.en.tour`, `*.vi.tour`. Six flows are covered, each
in both languages:

| Tour | Path it walks |
| --- | --- |
| 01 · Node startup | CLI → config → `node.Node` → `eth.Ethereum` → running services |
| 02 · Block import | `engine_newPayload` → `InsertChain` → EVM → state root check → disk |
| 03 · Transaction lifecycle | RPC/peer → txpool → gossip → miner → block → pool reset |
| 04 · Sync | CL head → skeleton → concurrent fetchers → snap ranges → heal |
| 05 · An RPC request | transport → routing → reflection → `ethapi` → backend → state |
| 06 · State storage | `SSTORE` → journal → trie → triedb layers → rawdb → pebble/freezer |

**Steps use `pattern` (a regex), not `line`.** That is deliberate: line numbers rot with every
refactor, regexes on function signatures do not. Keep it that way when you add steps.

To record a new tour: open the CodeTour panel -> `+` -> click through the code -> it writes the
JSON for you. Then swap any `line` fields for `pattern`.

---

## Keeping this honest

The handbook is only useful if it is true. Two habits:

- When a PR moves an entry point or renames a package, update `ARCHITECTURE.md` in the same PR.
- Verify a claim before trusting it: `grep -n "func (bc \*BlockChain) InsertChain" core/blockchain.go`.
  Function names are authoritative; the tables here are a map, not the territory.

If you keep this handbook in a fork and do not want it in upstream diffs, exclude it locally:

```shell
printf 'ARCHITECTURE.md\ndocs/dev/\n.tours/\n' >> .git/info/exclude
```
