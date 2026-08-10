# Getting started from zero

> **Language:** English (canonical) · [Tiếng Việt](../vi/getting-started.md)
> For someone who has never built geth and is not sure what an execution client is. One hour, from
> nothing to a running node you can talk to.

## What geth actually is

An Ethereum node today is **two programs**:

| | Execution layer (this repo) | Consensus layer (separate program) |
| --- | --- | --- |
| Does | runs transactions, keeps account state, serves `eth_*` RPC | picks the canonical chain, handles validators and finality |
| Software | geth, Nethermind, Besu, Erigon, Reth | Prysm, Lighthouse, Teku, Nimbus, Lodestar |
| They talk over | — | Engine API on `localhost:8551`, authenticated with a JWT file |

geth on its own **cannot follow mainnet** — nothing tells it which chain is canonical. That is why
step 4 below runs a fake consensus layer, and why [Run a node](run-a-node.md) pairs geth with a
real one.

Terms you will hit in the first hour are collected in the [glossary](glossary.md).

---

## 1. Prerequisites

- **Go 1.24 or newer** — the version in `go.mod` is authoritative: `grep '^go ' go.mod`.
- **A C compiler** — `xcode-select --install` on macOS, `build-essential` on Debian/Ubuntu.
  Needed because parts of the crypto code are C.
- **git**, and roughly 2 GB of free disk for the build and a dev chain.

```shell
go version     # go1.24.x or newer
cc --version   # any C compiler
```

Knowing Go helps but is not required to start reading. The [Go tour](https://go.dev/tour/) covers
enough in an afternoon; geth is idiomatic, unflashy Go.

---

## 2. Build it

```shell
git clone https://github.com/AJackTi/go-ethereum
cd go-ethereum
make geth                 # ~2-5 minutes the first time
./build/bin/geth version
```

`make all` builds every tool under `cmd/` (`evm`, `devp2p`, `abigen`, `rlpdump`, ...). You do not
need them yet.

!!! tip "If the build fails"
    Almost always Go too old or no C compiler. Read the first error line, not the last.

---

## 3. Run a throwaway chain

`--dev` gives you a private proof-of-authority chain with a pre-funded account and instant blocks.
No sync, no peers, no consensus client, and everything disappears when you delete the data
directory. This is where you should spend your first week.

```shell
./build/bin/geth --dev --http --http.api eth,net,web3,debug,txpool \
    --datadir /tmp/geth-dev
```

Two things to notice in the log: geth prints the pre-funded developer account, and blocks are only
produced when there is a transaction to include (`--dev.period 2` mines every 2 seconds instead).

Open a second terminal:

```shell
./build/bin/geth attach /tmp/geth-dev/geth.ipc
```

```javascript
eth.blockNumber                                   // 0 — nothing has happened yet
eth.accounts                                      // the pre-funded dev account
eth.getBalance(eth.accounts[0])                   // a very large number

// send value to a random address and watch a block appear
eth.sendTransaction({from: eth.accounts[0], to: "0x0000000000000000000000000000000000000042", value: web3.toWei(1, "ether")})
eth.blockNumber                                   // 1
eth.getBlock(1)                                   // your first block, in full
txpool.status                                     // pending / queued transactions
```

You just executed the entire path documented in
[tour 02 — block import](https://github.com/AJackTi/go-ethereum/tree/master/.tours).

!!! warning "`--http.api` is not optional"
    The HTTP server only exposes `net` and `web3` by default. If `eth_blockNumber` returns
    "method not found", you forgot to list the namespace.

---

## 4. Talk to it over HTTP

The console is a convenience; every client speaks plain JSON-RPC:

```shell
curl -s localhost:8545 -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
```

Same call from Go, using the client that ships in this repo:

```go
client, err := ethclient.Dial("http://localhost:8545")
n, err := client.BlockNumber(context.Background())
```

For tests you do not even need a running node — `ethclient/simulated` gives you an in-process
chain. See [Testing and debugging](debugging.md).

---

## 5. Your first hour in the code

Do these in order; each takes 10-15 minutes.

1. **Take tour 01** (node startup) in VS Code — install `vsls-contrib.codetour`, open the CodeTour
   panel. It walks the path you just ran.
2. **Read the [code map](architecture.md)** as far as "The six flows worth knowing", then stop.
3. **Break something on purpose.** Add `log.Info("hello from insertChain")` at the top of
   `insertChain` in `core/blockchain.go`, `make geth`, rerun `--dev`, send a transaction. Seeing
   your own log line print is worth more than another hour of reading.
4. **Find something by grep, not by memory:**
   ```shell
   grep -rn "func (bc \*BlockChain) InsertChain" core/blockchain.go
   go doc ./core/vm EVM.Run
   ```

---

## 6. Where to go next

| You want to | Go to |
| --- | --- |
| Run a node on a real network | [Run a node](run-a-node.md) |
| Learn the codebase properly | [Learning path](learning-path.md) — eight weeks, with exercises |
| Change something specific | [I want to change X](start-here.md) |
| Understand the layout | [Architecture](architecture.md) |
| Look up a word | [Glossary](glossary.md) |

---

## First-hour errors, decoded

| What you see | What it means |
| --- | --- |
| `Fatal: Failed to register the Ethereum service` | Usually a datadir built by a different `--state.scheme` or an incompatible geth version. For a dev chain, delete the datadir. |
| `the method eth_blockNumber does not exist/is not available` | Namespace not passed to `--http.api`. |
| `Post "http://localhost:8545": connection refused` | geth not running, or `--http` missing. |
| `Fatal: Error starting protocol stack: listen tcp :30303: bind: address already in use` | Another geth is running. Use `--port 30304` or stop it. |
| Console opens but `eth.accounts` is empty | You are not in `--dev`; a normal node has no accounts until you create one. |
| Node runs, `eth.blockNumber` stays 0, `admin.peers` empty | Expected on a real network without a consensus client. That is [the next page](run-a-node.md). |
