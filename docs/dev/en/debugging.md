# Testing and debugging

> **Language:** English (canonical) · [Tiếng Việt](../vi/debugging.md)
> How to prove a change works, and how to find out why it does not. Every command here runs
> against this repo with no external service.

## Pick the tool by symptom

| Symptom | Reach for |
| --- | --- |
| "Does my change break anything?" | `go run ./build/ci.go test -short`, then the full suite |
| "Is my EVM change correct per spec?" | `tests/` (execution-spec fixtures) and `cmd/evm statetest` |
| "What does this block actually do?" | `debug.traceBlockByNumber`, `debug_traceTransaction` |
| "Why is this block rejected?" | `debug.getBadBlocks`, then read backwards from `ValidateState` |
| "Why is it slow / eating RAM?" | `--pprof` + `go tool pprof`, the `/debug/metrics` endpoint |
| "Where does execution actually go?" | `dlv` breakpoints, or a temporary `log.Info` |
| "What is on disk?" | `geth db inspect`, `geth db get`, `debug.dbGet` |

---

## 1. Tests

```shell
# one package, verbose
go test ./core/... -run TestStateProcessorErrors -v

# race detector — required for anything touching goroutines
go test ./eth/... -race

# the project runner: linters, generated-code check and the spec suite
go run ./build/ci.go test -short      # fast loop while coding
go run ./build/ci.go test             # everything; run before every commit
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```

`-short` skips the slow permutations of `tests/` (the official Ethereum execution-spec fixtures,
downloaded on demand into `tests/spec-tests/`).
Anything that changes consensus behaviour must be validated by the full run — that is the suite
that decides whether your node agrees with the network.

### Build a chain inside a test

Do not reach for a real network to reproduce a chain bug. `core/chain_makers.go` generates blocks
in-process:

```go
gspec := &core.Genesis{Config: params.TestChainConfig, Alloc: types.GenesisAlloc{addr: {Balance: big.NewInt(1e18)}}}
db, blocks, _ := core.GenerateChainWithGenesis(gspec, engine, 10, func(i int, b *core.BlockGen) {
    b.AddTx(tx)
})
chain, _ := core.NewBlockChain(db, gspec, engine, nil)
if _, err := chain.InsertChain(blocks); err != nil { t.Fatal(err) }
```

For application-level tests — anything that would otherwise dial an RPC endpoint — use
`ethclient/simulated`: a full node in your test binary, no ports, no datadir.

### Fuzzing

`tests/fuzzers/` holds the targets (RLP, bn256, bls12381, range proofs, the tx fetcher). Run one
the normal Go way:

```shell
go test ./tests/fuzzers/rangeproof/... -fuzz Fuzz -fuzztime 60s
```

---

## 2. Debugging a running node

### Logs

```shell
geth --verbosity 5                        # 1 error … 3 info (default) … 5 trace
geth --vmodule 'core/*=5,p2p=4'           # loud only where you are working
```

Both are changeable at runtime from the console — useful on a node you do not want to restart:

```javascript
debug.verbosity(5)
debug.vmodule("eth/downloader=5")
```

### The `debug` namespace

Attach with `geth attach <datadir>/geth.ipc`, then:

```javascript
debug.traceBlockByNumber(1234, {tracer: "callTracer"})   // every call frame in a block
debug.traceTransaction("0x…", {tracer: "prestateTracer"})// state a tx touched
debug.getBadBlocks()                                     // blocks this node rejected, with the reason
debug.storageRangeAt(blockHash, txIndex, contract, "0x0", 10)
debug.dumpBlock(1234)                                    // full state dump at a block
debug.intermediateRoots(blockHash)                       // state root after each tx — finds the exact tx that diverges
debug.stacks()                                           // goroutine dump when the node is wedged
debug.memStats()
debug.setHead("0x100")                                   // rewind the chain (destructive, dev only)
```

`debug.intermediateRoots` is the fastest way to localise a consensus bug: compare against another
client and the first mismatching index is the transaction that broke.

!!! warning
    `debug` is a local tool. Never expose it over a public `--http.api`.

### Profiling

```shell
geth --pprof --pprof.addr 127.0.0.1 --pprof.port 6060 --metrics
```

```shell
go tool pprof -http=: http://localhost:6060/debug/pprof/profile?seconds=30   # CPU
go tool pprof -http=: http://localhost:6060/debug/pprof/heap                 # memory
curl -s localhost:6060/debug/pprof/goroutine?debug=2 | head -50              # stuck goroutines
curl -s localhost:6060/debug/metrics/prometheus | grep '^chain_'            # import speed
```

Block and mutex profiles are off by default; turn them on only while measuring:

```javascript
debug.setBlockProfileRate(1)
debug.setMutexProfileFraction(1)
```

---

## 3. EVM-level work

```shell
# run raw bytecode and watch the stack
go run ./cmd/evm run --debug --code 6001600101

# execute a state test fixture
# fixtures are not in the repo: `go run ./build/ci.go test` downloads them into
# tests/spec-tests/ (git-ignored)
go run ./cmd/evm statetest tests/spec-tests/fixtures/state_tests/<…>.json

# decode RLP by eye
go run ./cmd/rlpdump <hex>
```

`cmd/evm` boots no node, no database and no network — when a bug is inside the interpreter this is
a hundred times faster than reproducing it on a chain.

---

## 4. Stepping through with a debugger

```shell
go install github.com/go-delve/delve/cmd/dlv@latest

dlv test ./core -- -test.run TestStateProcessorErrors     # step through a test
dlv exec ./build/bin/geth -- --dev --http                 # step through a running node
(dlv) break core/state_processor.go:67
(dlv) continue
(dlv) print block.NumberU64()
```

VS Code's Go extension does the same through the UI; the delve invocation above is what it runs.

---

## 5. Reading a rejected block

The order to check, matching the import path in [tour 02](https://github.com/AJackTi/go-ethereum/tree/master/.tours):

1. **`debug.getBadBlocks()`** — geth keeps rejected blocks with the validation error attached.
2. **Which check failed?** A state-root mismatch means execution diverged; a body or header error
   means the block was malformed before execution ever ran.
3. **`debug.intermediateRoots(hash)`** — find the first transaction whose post-state root differs.
4. **`debug.traceTransaction`** on that transaction with `callTracer`, then `prestateTracer`.
5. **Reproduce it in a test** with `chain_makers`, then fix with the test as your check.

Historic consensus failures are written up in
[`docs/postmortems/`](https://github.com/AJackTi/go-ethereum/tree/master/docs/postmortems) — worth
reading once to see how these are diagnosed in practice.

---

## 6. Inspecting the database

```shell
geth db inspect      --datadir <dir>     # size per data category
geth db stats        --datadir <dir>
geth db get          --datadir <dir> <hex-key>
geth db inspect-history --datadir <dir>  # pathdb state history
geth snapshot verify-state --datadir <dir>
```

Key prefixes are defined in `core/rawdb/schema.go`; every accessor that reads or writes them sits
in the neighbouring `accessors_*.go`.

---

## Related

- [I want to change X](start-here.md) — where to make the change you are testing.
- [Run a node](run-a-node.md) — the flags referenced here in their operational context.
- [Architecture](architecture.md) — the flow each tool inspects.
