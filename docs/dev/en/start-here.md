# Start here: I want to change X

> **Language:** English (canonical) · [Tiếng Việt](../vi/start-here.md)
> A how-to index. For the map of the whole repo see [`ARCHITECTURE.md`](../../../ARCHITECTURE.md).

Find your task below. Each row gives the first file to open, the other places the change usually
touches, and how to prove it works. Verify every function name with `grep -n` before editing —
this table is a map, not the territory.

---

## 1. Adding to the API surface

### Add a new JSON-RPC method
1. **Open first:** `internal/ethapi/api.go` (namespace `eth`) or `eth/api_debug.go` / `eth/api_admin.go`.
2. **Also touch:** the `Backend` interface in `internal/ethapi/backend.go`; its implementation in
   `eth/api_backend.go`; `internal/web3ext/web3ext.go` so the JS console knows the method.
3. **Verify:** `geth --dev --http --http.api eth,debug`, then `curl` the method; add a test next to
   the package.
4. **Watch out:** every `Backend` implementation must compile, including test backends and
   `ethclient/simulated`.

### Change what an existing RPC returns
1. **Open first:** the marshalling helpers in `internal/ethapi/api.go` (`RPCMarshalBlock`, etc.).
2. **Also touch:** `ethclient/` if the Go client parses the field; `graphql/` if exposed there.
3. **Watch out:** field renames are breaking changes for users. Add, deprecate, then remove.

---

## 2. Protocol and consensus changes

### Implement an EIP that changes EVM behaviour
1. **Open first:** `core/vm/eips.go` — copy the pattern of the most recent EIP.
2. **Also touch:** `params/config.go` (fork flag + `Rules`), `params/forks/forks.go`,
   `core/vm/jump_table.go` (new/changed opcodes), `core/vm/gas_table.go` or `gascosts.go`,
   `params/protocol_params.go` for constants.
3. **Verify:** `go test ./core/vm/...`, then the spec suite: `go run ./build/ci.go test`
   (runs `tests/` against the official fixtures).
4. **Watch out:** the change **must** be fork-gated. Ungated, every node replaying history
   computes a different state root.

### Change gas costs
Same path as above. Gas lives in three places depending on the opcode: `gas_table.go` (dynamic),
`jump_table.go` (constant), `operations_acl.go` (access-list-aware, post-Berlin).

### Add a new transaction type
1. **Open first:** `core/types/transaction.go` — the `TxData` interface.
2. **Also touch:** a new `core/types/tx_*.go`; `transaction_marshalling.go`; `transaction_signing.go`;
   `core/txpool/validation.go` and the right subpool; `internal/ethapi/transaction_args.go`;
   RLP generation (`gen_*.go` via `go generate`).
3. **Verify:** round-trip encode/decode tests, then a `--dev` chain sending the new type.

---

## 3. Storage and performance

### Change what is stored on disk
1. **Open first:** `core/rawdb/schema.go` — the key prefixes.
2. **Also touch:** the matching `core/rawdb/accessors_*.go`; `geth db inspect` accounting in
   `cmd/geth/dbcmd.go`.
3. **Watch out:** prefix collisions silently corrupt data. Check that your new prefix is unused,
   and decide what an old database does when it meets the new code.

### Work on the trie / state layer
1. **Open first:** `triedb/database.go`, then `triedb/pathdb/` (default scheme) or `triedb/hashdb/`.
2. **Also touch:** `core/state/statedb.go` if the change is visible above the commit boundary;
   `trie/` for node encoding or hashing.
3. **Verify:** `go test ./trie/... ./triedb/...`; benchmark with `go test -bench . -benchmem`.

### Chase a performance regression
1. **Measure first:** `geth --pprof`, then `go tool pprof http://localhost:6060/debug/pprof/profile`.
2. **Usual suspects:** `core/state/trie_prefetcher.go`, `triedb/pathdb/buffer.go`,
   `core/blockchain.go` write path, `eth/protocols/snap` during sync.
3. **Verify:** report before/after numbers in the PR; `debug.metrics(false).chain` shows import speed.

---

## 4. Networking

### Change or add a wire protocol message
1. **Open first:** `eth/protocols/eth/protocol.go` (message codes) or `eth/protocols/snap/protocol.go`.
2. **Also touch:** `handlers.go` (serve it), `peer.go` (send it), `handler.go` in `eth/`,
   `dispatcher.go` if it is request/response.
3. **Verify:** `go run ./cmd/devp2p rlpx eth-test ...` against a local node.
4. **Watch out:** protocol changes need a version bump and backwards compatibility with older peers.

### Debug peering problems
`geth --verbosity 5` shows handshakes. `admin.peers` in the console shows who is connected.
Mismatched `core/forkid` values are the most common reason two nodes refuse each other.

---

## 5. Block production and the transaction pool

### Change how transactions are selected into a block
1. **Open first:** `miner/worker.go` -> `fillTransactions`.
2. **Also touch:** `core/txpool/txorder/` for ordering, `core/txpool/txpool.go` `Pending()` filter.
3. **Verify:** `--dev` chain, send competing transactions, inspect the produced block.

### Change transaction acceptance rules
1. **Open first:** `core/txpool/validation.go` (shared checks).
2. **Also touch:** `legacypool/legacypool.go` or `blobpool/blobpool.go` for pool-specific limits.
3. **Watch out:** stricter rules can strand transactions already in the pool across a restart.

---

## 6. Engine API / consensus client integration

1. **Open first:** `eth/catalyst/api.go`.
2. **Also touch:** `beacon/engine/types.go` for payload structs; `miner/payload_building.go` if
   building changes; `eth/catalyst/simulated_beacon.go` to keep `--dev` working.
3. **Verify:** `--dev` exercises the whole loop locally; the method versions must follow the
   Engine API spec exactly.

---

## 7. When you have no idea where to start

Run this ladder, in order:

1. **Reproduce it.** `geth --dev` or a `core/chain_makers.go` test is faster than a real network.
2. **Grep for the user-visible string.** Error text, RPC method name, log message, flag name.
   `grep -rn "insufficient funds" --include="*.go"`.
3. **Follow the call upward.** Find the function, then grep for its name to find callers.
4. **Read the test.** `*_test.go` next to the package shows the intended usage.
5. **Read the history.** `git log -p --follow <file>` — most confusing code is scar tissue from a
   past bug, and the commit message says which one.
6. **Take a tour.** `.tours/` walks the main flows step by step in the editor.

---

## Before you commit

Full checklist in [`AGENTS.md`](../../../AGENTS.md). Short version, in this order:

```shell
gofmt -w <files> && goimports -w <files>
make all
go run ./build/ci.go test -short      # while iterating
go run ./build/ci.go test             # before commit — full suite
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```
