# Architecture

> **Language / Ngôn ngữ:** English (canonical) · [Tiếng Việt](docs/dev/vi/architecture.md)
> **Scope:** a code map for people who need to change this repo. Not a protocol spec.
> **Rule:** names of functions and packages are authoritative; line numbers are not. Find things with `grep -n "func (bc \*BlockChain) InsertChain" core/blockchain.go`.

go-ethereum (`geth`) is one process that runs an Ethereum **execution layer** client. Since the Merge it does not choose the canonical chain — a consensus client drives it over the Engine API. Everything else in this repo exists to execute blocks, store state, talk to peers, and answer queries.

---

## Bird's eye view

```
            consensus client (Prysm, Lighthouse, ...)
                        |  Engine API over authrpc:8551 (JWT)
                        v
+-------------------------------------------------------------+
| cmd/geth            CLI flags -> config -> node              |
+-------------------------------------------------------------+
| node.Node           datadir, chaindb, p2p.Server,            |
|                     http/ws/ipc/authrpc, lifecycle registry  |
+-------------------------------------------------------------+
| eth.Ethereum        BlockChain | TxPool | handler+downloader |
| (a Lifecycle)       miner | filters | api backends           |
+-------------------------------------------------------------+
| storage             StateDB -> trie -> triedb -> rawdb       |
|                     -> ethdb/pebble + freezer (ancients)     |
+-------------------------------------------------------------+
```

Four layers. When lost, ask: *which layer is this request in?*

---

## Entry points — start reading here

| Question | File | Function |
| --- | --- | --- |
| How does the process boot? | `cmd/geth/main.go` | `geth()` -> `startNode()` |
| What gets wired into the node? | `eth/backend.go` | `New()` |
| What owns the process? | `node/node.go` | `New()`, `Start()` |
| How is a block imported? | `core/blockchain.go` | `insertChain()` |
| Where does state change? | `core/state_processor.go` | `Process()` |
| Where do opcodes run? | `core/vm/interpreter.go` | `EVM.Run()` |
| How does the CL drive us? | `eth/catalyst/api.go` | `forkchoiceUpdated()`, `newPayload()` |
| How are blocks built? | `miner/payload_building.go` | `buildPayload()` |
| How does sync start? | `eth/downloader/beaconsync.go` | `BeaconSync()` |
| Where do bytes hit disk? | `core/rawdb/schema.go` | key prefixes + `accessors_*.go` |
| Where are RPC methods defined? | `internal/ethapi/api.go` | + `eth/backend.go APIs()` |
| Which fork enables which EIP? | `params/config.go` | `Rules()`, `params/forks/forks.go` |

---

## Code map

### Process lifecycle
- **`cmd/geth`** — CLI entry, subcommands (`init`, `import`, `db`, `snapshot`, `account`, `console`).
- **`cmd/utils`** — every flag lives here; flags become `ethconfig.Config`.
- **`node`** — process container: datadir, database, `p2p.Server`, RPC stacks, start/stop ordering, JWT for the Engine API.
- **`eth`** + **`eth/ethconfig`** — the Ethereum backend. `eth/backend.go New()` assembles almost everything; read it once end to end.

### Chain core
- **`core`** — block import (`blockchain.go`), state transition (`state_processor.go`, `state_transition.go`), validation (`block_validator.go`), genesis, reorgs, tx indexing.
- **`core/types`** — on-chain data: header, block, five transaction types, receipt, log, withdrawal, block access list.
- **`core/txpool`** — thin router (`txpool.go`) over subpools: `legacypool` (nonce-ordered), `blobpool` (disk-backed blobs).
- **`params`** / **`params/forks`** — protocol constants and the fork schedule (Frontier -> Bogota).
- **`consensus`** — the `Engine` interface; `consensus/beacon` is the post-Merge wrapper. `clique`/`ethash` are legacy.
- **`core/forkid`** — lets peers reject each other across forks.

### EVM and state
- **`core/vm`** — the machine: `interpreter.go` (opcode loop), `jump_table.go`, `instructions.go`, `gas_table.go`, `eips.go` (per-fork behaviour), `contracts.go` (precompiles).
- **`core/state`** — `StateDB`: revertible state over the trie, with `journal.go` for undo, `snapshot/` for flat reads, `trie_prefetcher.go` for parallel warm-up.
- **`core/tracing`**, **`eth/tracers`** — execution hooks and the tracers behind `debug_trace*`.

### Storage
- **`trie`** — Merkle Patricia Trie: nodes, hashing, proofs, `stacktrie.go` for sequential building during sync.
- **`triedb`** — node storage with two schemes: `hashdb` (keyed by hash, ref-counted) and `pathdb` (keyed by path, diff layers + state history, rollback capable — the default).
- **`core/rawdb`** — the database key schema plus every accessor; also owns the freezer.
- **`ethdb`** — minimal KV interface; backends `pebble` (default), `leveldb`, `memorydb`, `remotedb`.

### Networking
- **`p2p`** — peers, dialing, RLPx encryption, discovery v4/v5, ENR/enode, DNS discovery.
- **`eth/protocols/eth`** — the `eth/68` wire protocol: headers, bodies, receipts, transaction announcements.
- **`eth/protocols/snap`** — range-based state download, the basis of snap sync.
- **`eth/downloader`** — bulk sync (skeleton + backfill). **`eth/fetcher`** — single announced blocks/txs while synced.

### Consensus layer and block production
- **`eth/catalyst`** — Engine API: `forkchoiceUpdated`, `getPayload`, `newPayload`; plus the simulated beacon behind `--dev`.
- **`miner`** — builds payloads on demand and keeps improving them until the CL collects.
- **`beacon/*`** — consensus-side types, light client, blsync.

### API surface
- **`rpc`** — geth's own JSON-RPC library (server, client, subscriptions, transports).
- **`internal/ethapi`** — the real implementation of the `eth` namespace, argument defaulting, `eth_simulateV1`.
- **`ethclient`**, **`graphql`**, **`ethstats`** — outward-facing clients and endpoints.
- **`eth/filters`**, **`core/filtermaps`** — log queries and the log index.

### Foundation and tools
- **`rlp`**, **`common`**, **`crypto`** — encoding, `Address`/`Hash`/hexutil, hashing and signatures.
- **`accounts`**, **`signer`** — keystore, hardware wallets, ABI, Clef.
- **`cmd/*`** — 12 more tools: `evm`, `devp2p`, `abigen`, `rlpdump`, `era`, `workload`, ...
- **`tests`** — the official execution-spec test suite. **`internal/build`** + `build/ci.go` — the CI pipeline you must run locally.

---

## The six flows worth knowing

Everything you will ever change sits on one of these paths.

1. **CL <-> EL loop** — `eth/catalyst/api.go`: `forkchoiceUpdated` (with `payloadAttributes` = "build me a block") -> `getPayload` -> `newPayload`.
2. **Block import** — `InsertChain` -> `insertChain` -> header/body verify -> `StateProcessor.Process` -> per-tx `ApplyTransactionWithEVM` -> `EVM.Run` -> `ValidateState` -> `writeBlockAndSetHead` -> `StateDB.Commit` -> `triedb.Update` -> `rawdb`.
3. **State storage** — `StateDB` (RAM, revertible) -> `trie` (hashing) -> `triedb` (hashdb | pathdb) -> `rawdb` schema -> pebble + freezer.
4. **Transaction lifecycle** — RPC or peer -> `TxPool.Add` -> subpool -> broadcast to peers **and** `Pending()` to the miner -> block -> `ChainHeadEvent` resets the pool.
5. **Sync** — CL head -> `BeaconSync` -> `skeleton.Sync` fills headers backwards -> concurrent fetchers for bodies/receipts; with `--syncmode snap`, `snap` downloads state by range, then heals.
6. **RPC request** — transport -> `rpc/handler.go` routing -> `internal/ethapi` -> `ethapi.Backend` -> `eth/api_backend.go` -> chain/state/txpool.

Each flow has a guided in-editor walkthrough: see [`.tours/`](.tours) (VS Code + the CodeTour extension, fully offline).

---

## Invariants and rules of thumb

- **Consensus behaviour must be fork-gated.** Any change to execution semantics goes behind a fork flag in `params/config.go`; see `core/vm/eips.go` for the pattern. Ungated changes corrupt replay of history.
- **`StateDB` is revertible, `triedb` is not.** Anything that must survive a failed call belongs above the `Commit` boundary.
- **Interfaces are the seams.** `consensus.Engine`, `txpool.SubPool`, `ethapi.Backend`, `ethdb.KeyValueStore`, `trie` readers. Read the interface, then one implementation.
- **Generated files are checked.** Files starting with `// Code generated` (`gen_*.go`) must be regenerated (`make devtools`, then `go generate`) or CI fails on `check_generate`.
- **Adding an RPC method touches four places:** the method in `internal/ethapi/api.go` (or `eth/api_*.go`), the `Backend` interface, `eth/api_backend.go`, and `internal/web3ext/web3ext.go` for the console.
- **Keep diffs minimal.** See `AGENTS.md`: no drive-by refactors, no new dependencies unless the task requires them.

---

## Build, run, test

```shell
make geth                              # build
make all                               # build every cmd/ tool
go run ./build/ci.go test -short       # fast loop while coding
go run ./build/ci.go test              # full suite, required before commit
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```

Run a node you can poke at:

```shell
./build/bin/geth --dev --http --http.api eth,net,web3,debug   # instant private chain
./build/bin/geth attach                                       # JS console
```

Full pre-commit checklist: `AGENTS.md`.

---

## Where to go next

- Never built geth before: [`docs/dev/en/getting-started.md`](docs/dev/en/getting-started.md)
- Task-oriented index ("I want to change X, where do I start?"): [`docs/dev/en/start-here.md`](docs/dev/en/start-here.md)
- Structured learning path: [`docs/dev/en/learning-path.md`](docs/dev/en/learning-path.md)
- Deploying and operating a node: [`docs/dev/en/run-a-node.md`](docs/dev/en/run-a-node.md)
- Tests, tracers, profiling, delve: [`docs/dev/en/debugging.md`](docs/dev/en/debugging.md)
- Terminology (EN ↔ VI): [`docs/dev/en/glossary.md`](docs/dev/en/glossary.md)
- In-editor guided tours: [`.tours/`](.tours)
- Decisions and their reasons: [`docs/dev/adr/`](docs/dev/adr)
- Offline API reference: `go doc ./core/vm` or `pkgsite -http :8080` (see `docs/dev/README.md`)
