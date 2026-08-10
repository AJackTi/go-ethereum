# Tools in `cmd/`

> **Language:** English (canonical) · [Tiếng Việt](../vi/tools.md)
> Thirteen binaries live in `cmd/`. `make all` builds them into `build/bin/`. Most are ways to
> observe the system from outside, which is exactly what you want while debugging.

```shell
make all              # every tool
make geth             # just the node
go run ./cmd/evm ...  # or run one without installing
```

---

## geth

The node itself, plus roughly forty subcommands. The ones worth knowing:

| Command | Use |
| --- | --- |
| `geth --dev` | throwaway chain, funded account, instant blocks |
| `geth attach <ipc>` | JavaScript console against a running node |
| `geth init <genesis.json>` | initialise a datadir from a custom genesis |
| `geth dumpgenesis` | print the genesis of a known network |
| `geth import` / `export` | move blocks in and out as RLP |
| `geth import-history` / `export-history` | the same, using era files |
| `geth prune-history` | drop pre-merge history from an existing datadir |
| `geth download-era` | fetch era history files |
| `geth db inspect` | where the disk went, by data category |
| `geth db stats` / `compact` | database health and compaction |
| `geth db get` / `put` / `delete` | raw key access — dangerous, useful |
| `geth db inspect-history` | pathdb state history |
| `geth snapshot verify-state` | verify the state snapshot against the trie |
| `geth snapshot prune-state` | prune historical state (hashdb) |
| `geth snapshot dump` / `traverse-state` | walk state for auditing |
| `geth removedb` | delete chain data, keep the keystore |
| `geth dumpconfig` | print the effective config as TOML |
| `geth account new` / `list` / `import` | keystore management |

`geth dumpconfig` is underrated: it shows exactly what your flags resolved to, which settles most
"is this actually on?" questions in one command.

---

## evm — the EVM without a node

```shell
go run ./cmd/evm run --debug --code 6001600101      # execute bytecode, print every step
go run ./cmd/evm statetest <fixture.json>           # run an execution-spec state test
go run ./cmd/evm bench <file>                       # benchmark bytecode
go run ./cmd/evm fuzz / cross-check                 # fuzzing and differential checks
```

No database, no network, no chain. When a bug is inside the interpreter this is the fastest
reproduction you will get. Useful flags: `--dump` (state after), `--statdump` (opcode counts),
`--trace.format`, `--trace.nomemory`.

---

## devp2p — the network, poked from outside

```shell
go run ./cmd/devp2p discv4 ping <enode>        # is that node alive?
go run ./cmd/devp2p discv4 resolve <enode>     # look a node up in the DHT
go run ./cmd/devp2p discv4 crawl <file>        # walk the DHT into a node set
go run ./cmd/devp2p discv5 ...                 # same family, protocol v5
go run ./cmd/devp2p rlpx eth-test ...          # protocol conformance against a local node
go run ./cmd/devp2p dns ...                    # build and publish DNS node lists
```

The `eth-test` suite is the reference check when you change anything in `eth/protocols/eth`.

---

## abigen — Go bindings from an ABI

```shell
./build/bin/abigen --abi Token.abi --bin Token.bin --pkg token --type Token --out token.go
```

Generates typed Go methods for a contract. Usage examples are in
[Using geth from your own code](using-geth.md). Commit the generated file, like geth commits its
own `gen_*.go`.

---

## rlpdump and abidump — reading bytes

```shell
go run ./cmd/rlpdump <hex>          # RLP structure, human readable
go run ./cmd/rlpdump -reverse       # the other direction
go run ./cmd/abidump <hexdata>      # decode transaction calldata against known ABIs
```

`rlpdump` is the fastest way to answer "what is actually in this blob" when debugging protocol or
database content.

---

## ethkey — key files without a node

```shell
go run ./cmd/ethkey generate           # new key file
go run ./cmd/ethkey inspect <file>     # address and public key
go run ./cmd/ethkey signmessage <file> <message>
```

Operates directly on keystore files. Never point it at a keystore a running node owns.

---

## era — history files

```shell
go run ./cmd/era block --dir <dir> --network <name>
go run ./cmd/era info   --dir <dir>
go run ./cmd/era verify --dir <dir>
```

Era files are the standard packaging for historical chain segments — the format behind
`geth import-history`, `export-history` and `download-era`. Verifying them is how you check a
history archive before importing it.

---

## workload — RPC under load

```shell
go run ./cmd/workload filtergen  <rpc-url>    # generate a log-filter query set
go run ./cmd/workload historygen <rpc-url>    # generate history queries
go run ./cmd/workload test       <rpc-url>    # run the generated suite against a node
go run ./cmd/workload filterfuzz <rpc-url>    # fuzz the filter API
```

The tool for "is `eth_getLogs` still fast after my change?" — it produces a repeatable query set
rather than an ad-hoc benchmark.

---

## blsync — beacon light client

A standalone beacon-chain light syncer (`beacon/light`, `beacon/blsync`). It follows the consensus
chain without running a full consensus client, and can drive an execution node's Engine API. Useful
for experiments; not a substitute for a real CL on a validating node.

---

## fetchpayload and keeper — stateless execution

```shell
go run ./cmd/fetchpayload -rpc http://localhost:8545 <block>
```

`fetchpayload` pulls a block plus its execution witness from a node over RPC and writes an
RLP/JSON payload. `keeper` consumes exactly that payload: it executes the block **statelessly**
from the witness and checks the computed state and receipt roots against the header — it is built
to run as a zkvm guest (see `cmd/keeper/README.md`).

Together they are the practical entry point to `core/stateless`.

---

## Not in this repo

**Clef**, the standalone signer, no longer has a command here; the library it was built on remains
under [`signer/`](https://github.com/AJackTi/go-ethereum/tree/master/signer). Consensus clients
(Prysm, Lighthouse, Teku, Nimbus, Lodestar) are separate projects — see
[Run a node](run-a-node.md).

---

## Related

- [Testing and debugging](debugging.md) — which tool for which symptom.
- [Using geth from your own code](using-geth.md) — the library side.
- `go run ./cmd/<tool> --help` — every flag, offline, always current.
