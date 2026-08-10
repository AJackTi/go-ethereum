# Run a node

> **Language:** English (canonical) · [Tiếng Việt](../vi/run-a-node.md)
> Deploying geth on a real network: what to size, what to open, what to pair it with, and what
> breaks. Defaults quoted here come from `node/defaults.go`, `cmd/utils/flags.go` and
> `eth/ethconfig/config.go`.

## 1. Decide four things first

| Decision | Flag | Options | Pick this unless you know better |
| --- | --- | --- | --- |
| Network | `--mainnet` / `--sepolia` / `--holesky` / `--hoodi` | — | `--sepolia` while learning |
| Sync mode | `--syncmode` | `snap`, `full` | `snap` (the default) |
| State scheme | `--state.scheme` | `path`, `hash` | `path` — prunes as it goes |
| History kept | `--gcmode`, `--history.chain` | `full`/`archive`, `all`/`postmerge`/`postprague` | `full` — archive is many times larger |

Rough disk: a testnet node is tens of GB; mainnet with `snap` + `path` is hundreds of GB and grows.
Archive is a different order of magnitude. Put the datadir on **SSD or NVMe** — the workload is
random reads, and a spinning disk will never catch up.

Memory: `--cache` defaults to 4096 MB. Give the machine at least 16 GB for mainnet.

---

## 2. You need a consensus client too

geth alone will sit at block 0 with peers connected and never advance: nothing is telling it which
chain is canonical. Pair it with one of Prysm, Lighthouse, Teku, Nimbus or Lodestar — separate
projects, not in this repo.

They talk over the **Engine API** on `localhost:8551`, authenticated by a shared 32-byte JWT
secret. geth writes one to `<datadir>/geth/jwtsecret` on first start if you do not supply one
(`node/node.go`, `ObtainJWTSecret`), and both programs must read the same file.

```
   consensus client  ──engine_forkchoiceUpdated / newPayload──▶  geth :8551 (JWT)
        ▲                                                              │
        │  beacon p2p :9000                                            │  eth p2p :30303
        ▼                                                              ▼
   beacon network                                            execution network
```

---

## 3. A real command, flag by flag

```shell
geth \
  --sepolia \
  --datadir /var/lib/geth \
  --syncmode snap \
  --state.scheme path \
  --http --http.addr 127.0.0.1 --http.port 8545 --http.api eth,net,web3 \
  --authrpc.addr 127.0.0.1 --authrpc.port 8551 \
  --authrpc.jwtsecret /var/lib/geth/jwtsecret \
  --port 30303 \
  --maxpeers 50 \
  --cache 8192 \
  --metrics --pprof --pprof.addr 127.0.0.1 \
  --verbosity 3
```

- `--http.api` — **required to expose anything useful**; HTTP serves only `net,web3` by default.
  Never include `admin`, `personal` or `debug` on a public interface.
- `--authrpc.*` — the Engine API. Only `eth` and `engine` are served there, and only to localhost
  by default. This port is for your consensus client, nobody else.
- `--maxpeers` — default 50. Lower it to save bandwidth, but not below ~25 or sync suffers.
- `--verbosity` — 3 is info, 4 debug, 5 trace. Level 5 is very loud; use it in bursts.

Then start the consensus client pointing at `http://localhost:8551` with the same JWT file.

---

## 4. Ports and firewall

| Port | Protocol | Who connects | Exposure |
| --- | --- | --- | --- |
| 30303 | TCP **and** UDP | other Ethereum nodes | **open to the internet** |
| 8551 | TCP | your consensus client | localhost only |
| 8545 / 8546 | TCP | your applications | localhost, or behind a proxy with auth |
| 6060 | TCP | you | localhost only — metrics and pprof |

If 30303 is closed you will still sync, slowly, using only outbound connections — you just never
receive inbound peers. Everything else must stay closed.

!!! danger "An open 8545 is a giveaway"
    An RPC port reachable from the internet lets anyone drain accounts the node has unlocked, spam
    expensive queries, and read `admin` data. Bind to `127.0.0.1`, keep keys off the node, and put
    a reverse proxy with authentication in front if remote access is genuinely needed.

---

## 5. Run it as a service

`geth` is a plain foreground process — no daemon mode, on purpose. Let the init system supervise
it. The repo ships no unit file; this is a working minimal one:

```ini
# /etc/systemd/system/geth.service
[Unit]
Description=go-ethereum execution client
After=network-online.target
Wants=network-online.target

[Service]
User=geth
Group=geth
Type=simple
ExecStart=/usr/local/bin/geth --sepolia --datadir /var/lib/geth \
    --http --http.addr 127.0.0.1 --http.api eth,net,web3 \
    --authrpc.jwtsecret /var/lib/geth/jwtsecret \
    --metrics --pprof --pprof.addr 127.0.0.1
Restart=always
RestartSec=5
TimeoutStopSec=600          # geth needs time to flush state on shutdown — do not shorten
LimitNOFILE=65536           # peers plus database files exhaust the default limit
StateDirectory=geth

[Install]
WantedBy=multi-user.target
```

```shell
sudo systemctl daemon-reload && sudo systemctl enable --now geth
journalctl -fu geth
```

!!! warning "Never `kill -9` a syncing node"
    A hard kill during a state flush can leave the database needing a long repair on next start.
    `systemctl stop` and wait; that is what `TimeoutStopSec` is for.

### Docker

The repo builds its own image ([`Dockerfile`](https://github.com/AJackTi/go-ethereum/blob/master/Dockerfile),
exposes 8545, 8546, 30303/tcp and 30303/udp):

```shell
docker build -t geth .
docker run -d --name geth \
  -p 30303:30303 -p 30303:30303/udp \
  -p 127.0.0.1:8545:8545 \
  -v /var/lib/geth:/root/.ethereum \
  geth --sepolia --http --http.addr 0.0.0.0 --http.api eth,net,web3
```

`--http.addr 0.0.0.0` inside the container is safe **only** because the host mapping is pinned to
`127.0.0.1:8545`. Get that backwards and you have published your RPC to the internet.

---

## 6. Is it healthy?

```shell
geth attach /var/lib/geth/geth.ipc
```

```javascript
eth.syncing            // false = synced; otherwise currentBlock vs highestBlock
eth.blockNumber        // should climb every ~12s once synced
admin.peers.length     // 0 for more than a few minutes is a networking problem
admin.nodeInfo.protocols.eth
txpool.status
```

Throughput and internals come from the metrics endpoint, not the console:

```shell
curl -s localhost:6060/debug/metrics/prometheus | grep '^chain_'   # head, inserts, execution
curl -s localhost:6060/debug/metrics | head                        # same data as expvar JSON
```

!!! note "`--metrics` alone opens no port"
    `--metrics` turns collection on. To *reach* it you need either `--pprof` (metrics are served on
    the pprof server, `127.0.0.1:6060` by default) or `--metrics.addr` (a standalone metrics
    server). Point Prometheus and Grafana at that endpoint; `/debug/pprof` on the same port is for
    investigation only.

Reading the logs: `Imported new potential chain segment` means you are following the chain.
`Syncing: chain download in progress` with a rising percentage is normal early on. Repeated
`Post-merge network, but no beacon client seen` means the consensus client is not talking to you.

---

## 7. Maintenance

```shell
geth db inspect --datadir /var/lib/geth        # where the disk went, by category
geth db stats  --datadir /var/lib/geth
geth removedb  --datadir /var/lib/geth         # nuke chain data, keep the keystore
```

Keeping the disk in check (all on `state.scheme=path`):

- `--history.state 90000` — blocks of state history retained; `0` keeps everything.
- `--history.transactions` — the transaction index; `0` indexes the whole chain.
- `--history.chain postmerge` — drop pre-merge bodies and receipts entirely.
- `geth prune-history` — apply chain-history pruning to an existing datadir.

**Upgrading:** stop the service, replace the binary, start it again. Read the release notes first —
a change of `state.scheme` or database format needs a resync, and downgrades are not supported.

**Backups:** the chain is public data; you can always resync. The one irreplaceable thing is
`<datadir>/keystore` (and your JWT file, which is trivially regenerated). Never copy a live
database directory — stop the node first, or you will copy a torn state.

---

## 8. When it goes wrong

| Symptom | Likely cause and fix |
| --- | --- |
| `eth.blockNumber` stuck at 0, peers connected | No consensus client, or wrong/mismatched JWT. Check both logs for `engine_forkchoiceUpdated`. |
| `admin.peers.length` is 0 | 30303 blocked, or a `forkid` mismatch (wrong network flag). Check `--bootnodes` and the firewall. |
| `Failed to register the Ethereum service` | Datadir written by another `--state.scheme` or a newer geth. Resync or match the setting. |
| Sync percentage crawls near the end | Normal for snap sync: the heal phase repairs state that moved while downloading. |
| Disk fills up | `geth db inspect`, then history flags above; archive mode is not fixable by pruning. |
| Node stops during shutdown for minutes | Flushing state. Let it finish. |
| RPC times out under load | `--cache` too low, disk too slow, or a heavy `eth_getLogs` range. Check the metrics endpoint. |

---

## Related

- [Getting started](getting-started.md) — build it and run `--dev` first.
- [Testing and debugging](debugging.md) — pprof, tracers and reading a bad-block report.
- [Architecture](architecture.md) — what each flag is actually configuring.
