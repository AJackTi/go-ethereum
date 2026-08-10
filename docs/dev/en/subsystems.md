# The other subsystems

> **Language:** English (canonical) · [Tiếng Việt](../vi/subsystems.md)
> Parts of the repository that the six core flows do not pass through. Each one is optional, each
> one surprises somebody, and none of them are covered anywhere else in this handbook.

## GraphQL

A second query interface next to JSON-RPC, on the same HTTP port, at `/graphql`.

```shell
geth --http --graphql --graphql.corsdomain '*' --graphql.vhosts localhost
```

- `graphql/schema.go` — the schema, as a Go string. This *is* the API contract.
- `graphql/graphql.go` — resolvers, which call the same `ethapi.Backend` the RPC layer uses.
- `graphql/service.go` — `New(stack, backend, filterSystem, cors, vhosts)`, registered from
  `cmd/geth/config.go` when the flag is on.
- `graphql/graphiql.go` — the in-browser explorer.

Adding a field means touching the schema and the matching resolver. It reads from the same backend
as `internal/ethapi`, so a new capability usually lands there first and is exposed here second.

---

## ethstats — reporting to a dashboard

```shell
geth --ethstats <nodename>:<secret>@<host>:<port>
```

`ethstats/ethstats.go` opens a WebSocket to a stats server and streams node state: head block,
peer count, transaction pool size, whether the node is syncing. `New(node, backend, engine, url)`
wires it up; the `loop` function subscribes to chain-head, new-transaction and new-payload events
and pushes reports.

Outbound only, and entirely optional — it exists to feed the public network dashboards. Do not
confuse it with `--metrics`, which is your own Prometheus data (see
[Run a node](run-a-node.md)).

---

## filtermaps — the log index

`eth_getLogs` used to mean scanning every block's bloom filter. `core/filtermaps` replaces that
with a purpose-built index.

- `core/filtermaps/filtermaps.go` — `NewFilterMaps(db, chainView, historyCutoff, finalBlock, params, config)`,
  constructed in `eth/backend.go`.
- `core/filtermaps/indexer.go` — builds and maintains the index in the background; it follows the
  chain head and rewinds on reorgs.
- `core/filtermaps/checkpoints_*.json` — per-network checkpoints so a fresh node does not have to
  index from genesis.
- `eth/filters/` — the RPC surface on top (`eth_getLogs`, `eth_subscribe`).

Practical consequence: after a fresh sync, log queries can be slow or incomplete until indexing
catches up. `--history.logs` controls how far back the index goes.

---

## signer — what is left of Clef

The standalone `clef` binary is no longer in this repository. Three packages remain, and they are
used by other things:

- `signer/core/apitypes` — EIP-712 typed-data structures, used wherever structured data is signed.
- `signer/fourbyte` — a database of function selectors (`4byte.json`) plus argument validation;
  this is what `cmd/abidump` uses to decode calldata.
- `signer/storage` — AES-GCM encrypted key/value storage.

If you are looking for account management inside geth, that is `accounts/` — see
[Using geth from your own code](using-geth.md).

---

## Binary trie conversion

Groundwork for moving state from the Merkle Patricia Trie to a binary trie.

```shell
geth bintrie convert --datadir <dir> [--delete-source] [--memory-limit <MB>]
```

- `trie/bintrie` — the binary trie itself.
- `trie/transitiontrie` — reads across both structures while a conversion is in flight.
- `core/overlay` — the overlay layer that makes a partially converted state usable.
- `cmd/geth/bintrie_convert.go` — the command.

Experimental. Do not run it on a datadir you care about.

---

## Era files and history pruning

Chain history is packaged into era files, which makes it movable and prunable.

```shell
geth download-era ...        # fetch history files
geth import-history ...      # load them into a datadir
geth export-history ...      # write them out
geth prune-history           # drop pre-merge history from an existing datadir
```

- `internal/era` — the format: `e2store`, indexes, readers and writers.
- `core/history` — the retention policy behind `--history.chain all|postmerge|postprague`.
- `cmd/era` — inspect and verify era files outside a node ([Tools](tools.md)).

This is the machinery behind "my node does not need 20 years of history".

---

## OpenTelemetry tracing

Distributed tracing for RPC handling, separate from `--metrics` and from `debug_trace*` (which
traces EVM execution, not the process).

```shell
geth --rpc.telemetry --rpc.telemetry.endpoint <otlp-endpoint> \
     --rpc.telemetry.username <u> --rpc.telemetry.password <p> \
     --rpc.telemetry.instance-id <id>
```

- `internal/telemetry` — span helpers built on `go.opentelemetry.io/otel`.
- `internal/telemetry/tracesetup` — exporter wiring.
- `node.Config.OpenTelemetry` — endpoint and `SampleRatio` (default 1.0).

Useful when you need to know where wall-clock time inside a request actually went.

---

## Beacon-side packages

geth is an execution client, but it carries consensus-side code for light clients:

- `beacon/types` — beacon headers, SSZ structures.
- `beacon/light` — light client sync committees and proofs.
- `beacon/blsync` — follows the beacon chain without a full consensus client, and can drive an
  execution node's Engine API. `cmd/blsync` is the standalone binary.
- `beacon/engine` — the Engine API payload types shared with `eth/catalyst`.
- `beacon/merkle`, `beacon/params` — supporting primitives.

For a validating node you still need a real consensus client — see [Run a node](run-a-node.md).

---

## Smaller corners worth knowing

| Package | What it is |
| --- | --- |
| `event` | The internal pub/sub used by `ChainHeadEvent`, `NewTxsEvent` and friends |
| `metrics` | The metrics registry, plus InfluxDB and Prometheus exporters |
| `internal/jsre` | The JavaScript runtime behind `geth console` |
| `internal/web3ext` | Console bindings — a new RPC method needs an entry here |
| `internal/flags` | Flag categories and the help output layout |
| `common/prque`, `common/lru`, `common/mclock` | Priority queue, caches, and a mockable clock used all over |
| `internal/reexec`, `internal/cmdtest` | Harness for testing the binaries end to end |

---

## Related

- [Architecture](architecture.md) — the packages the six core flows do pass through.
- [Tools](tools.md) — the binaries that drive several of the subsystems above.
- [Run a node](run-a-node.md) — the operational flags referenced here.
