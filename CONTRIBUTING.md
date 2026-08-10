# Contributing

> **Language / Ngôn ngữ:** English · [Tiếng Việt](docs/dev/vi/start-here.md)

New here? Two links do most of the work:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — the code map: four layers, an entry point per question,
  what every package does, and the six flows everything else hangs off.
- **[docs/dev/](docs/dev/README.md)** — the developer handbook, in English and Vietnamese:
  [getting started](docs/dev/en/getting-started.md) · [I want to change X](docs/dev/en/start-here.md) ·
  [learning path](docs/dev/en/learning-path.md) · [testing and debugging](docs/dev/en/debugging.md) ·
  [running a node](docs/dev/en/run-a-node.md) · [glossary](docs/dev/en/glossary.md)

There are also guided, click-through walkthroughs of the seven main flows in [`.tours/`](.tours)
(VS Code + the CodeTour extension, works offline).

---

## Before you open a pull request

Run all of these; they are the same checks CI runs. Cheapest first — do not run the test suite
while the build is broken.

```shell
gofmt -w <changed files>
goimports -w <changed files>

make all                              # every binary under cmd/ still builds

go run ./build/ci.go test -short      # fast loop while iterating
go run ./build/ci.go test             # full suite, including the execution-spec tests
go run ./build/ci.go lint
go run ./build/ci.go check_generate   # gen_*.go files must be regenerated, not hand-edited
```

If `check_generate` fails: `make devtools`, then `go generate ./...` in the affected package, and
commit the regenerated files.

The full rules — including "keep changes minimal" and "do not add dependencies unless the task
requires it" — are in [AGENTS.md](AGENTS.md).

## If you changed documentation

```shell
python3 docs/dev/check.py             # tour anchors, code references, links, en/vi mirror
```

This runs in CI on every pull request that touches Go code or the handbook. It has no
dependencies. The website build (`mkdocs build --strict`, see
[docs/dev/README.md](docs/dev/README.md)) is a separate check that covers the rendered site.

## Writing the pull request

Three paragraphs is usually right:

1. **The problem** — what is wrong today, with a reproduction if it is a bug.
2. **The approach** — what you changed and, if there was a choice, why this one.
3. **The verification** — how you know it works: the tests you added, the numbers you measured.

Keep unrelated cleanups out of the diff. If you find something else worth fixing, that is a second
pull request.

## Upstream

This repository is a fork. Changes intended for everyone belong upstream at
[ethereum/go-ethereum](https://github.com/ethereum/go-ethereum), which has its own review process
and Discord.
