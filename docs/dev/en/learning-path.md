# Learning path: eight weeks to a first pull request

> **Language:** English (canonical) · [Tiếng Việt](../vi/learning-path.md)
> A tutorial. For task lookup use [`start-here.md`](start-here.md); for the map use
> [`ARCHITECTURE.md`](../../../ARCHITECTURE.md).

Each week has a goal, what to read, what to *do*, and a checkpoint you can answer alone.
The doing matters more than the reading — anything you only read is gone in a week.

---

## Week 1 — Run a node and watch it live (~8h)

- **Read:** `README.md`, `cmd/geth/main.go`, `cmd/geth/config.go`, `node/node.go`.
- **Do:** `make geth`; run `geth --sepolia --syncmode snap --http`; `geth attach` and call
  `eth.syncing`, `admin.peers`, `txpool.status`; then `geth --dev --http` for an instant
  private chain.
- **Write down:** the list of lifecycles registered at startup (add a log line in
  `node.Node.RegisterLifecycle`).
- **Checkpoint:** explain why `--dev` needs no consensus client
  (hint: `eth/catalyst/simulated_beacon.go`).

## Week 2 — Data types and RLP (~8h)

- **Read:** `core/types/block.go`, `transaction.go`, the five `tx_*.go` files, `receipt.go`,
  `rlp/encode.go`, `rlp/decode.go`.
- **Do:** decode a real block with `go run ./cmd/rlpdump`; write a test that round-trips one
  transaction of each type.
- **Write down:** a table of what each transaction type adds and which fork enabled it
  (cross-check `params/config.go`).
- **Checkpoint:** compute a transaction hash from raw bytes and match it against an explorer.

## Week 3 — The EVM (~10h)

- **Read:** `core/vm/interpreter.go` (`EVM.Run`), `jump_table.go`, `instructions.go`,
  `gas_table.go`, `contracts.go`, `evm.go` (`Call`).
- **Do:** `go run ./cmd/evm run --debug --code 6001600101` and follow the stack; run a state test
  with `go run ./cmd/evm statetest`; on a scratch branch, add a fake opcode to see fork gating work.
- **Write down:** what happens across a nested `CALL` — the 63/64 gas rule, the state snapshot,
  the depth limit.
- **Checkpoint:** point at the exact code where `REVERT` undoes state
  (hint: `core/state/journal.go`).

## Week 4 — State transition and block import (~10h)

- **Read:** `core/state_processor.go`, `core/state_transition.go`, `core/blockchain.go`
  (`insertChain`), `core/block_validator.go`, `core/state/statedb.go`.
- **Do:** use `core/chain_makers.go` in a test to generate ten blocks and `InsertChain` them;
  corrupt a state root on purpose and read the failure; run `debug_traceBlock` on your block.
- **Write down:** the exact order — pre-execution system calls, transactions, post-execution
  requests, validation, write.
- **Checkpoint:** describe what happens when the parent of an imported block is on another branch.

## Week 5 — Trie and storage (~10h)

- **Read:** `trie/trie.go`, `trie/hasher.go`, `trie/stacktrie.go`, `triedb/database.go`,
  `triedb/pathdb/difflayer.go`, `core/rawdb/schema.go`.
- **Do:** build a small trie in a test and print the root after each insert; run
  `geth db inspect` on a real datadir; read a proof through `trie/proof.go`.
- **Write down:** your own diagram of one `SetState` becoming bytes on disk.
- **Checkpoint:** explain why `pathdb` can roll back and `hashdb` cannot.

## Week 6 — Networking and sync (~9h)

- **Read:** `p2p/server.go`, `eth/protocols/eth/handshake.go`, `handlers.go`, `eth/handler.go`,
  `eth/downloader/beaconsync.go`, `eth/protocols/snap/sync.go`.
- **Do:** ping a bootnode with `go run ./cmd/devp2p`; run with `--verbosity 5` and read the
  handshake; watch one full snap sync on Sepolia.
- **Write down:** why two nodes on the same network can still refuse each other (`core/forkid`).
- **Checkpoint:** list the message order from TCP connect to the first block header.

## Week 7 — Engine API, miner, txpool (~8h)

- **Read:** `eth/catalyst/api.go`, `miner/payload_building.go`, `miner/worker.go`,
  `core/txpool/txpool.go`, `core/txpool/legacypool/legacypool.go`, `core/txpool/blobpool/blobpool.go`.
- **Do:** on `--dev`, send transactions with `ethclient` and log the full
  forkchoiceUpdated -> getPayload -> newPayload cycle; inspect `txpool_content` with a nonce gap
  to see the queued lane.
- **Write down:** what decides transaction order inside a block.
- **Checkpoint:** explain why calling `getPayload` later yields a better block.

## Week 8 — Contribute for real (~8h)

- **Read:** `AGENTS.md`, `build/ci.go`, `tests/state_test.go`, and the git history of the package
  you care about.
- **Do:** run the full `go run ./build/ci.go test` once to learn how long it takes; find a small
  gap (a missing test, a confusing error message) and fix it; run the whole pre-commit checklist.
- **Write down:** a three-paragraph PR description — problem, approach, how you verified it.
- **Checkpoint:** `lint`, `check_generate` and the full test suite all pass before you open the PR.

---

## If you only have one weekend

Week 1 (run it) + week 4 (block import) + the `.tours/` walkthrough. That is enough context to
read most PRs in this repo.
