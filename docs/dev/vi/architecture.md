# Kiến trúc

> **Ngôn ngữ / Language:** Tiếng Việt · [English (bản gốc)](../../../ARCHITECTURE.md)
> **Phạm vi:** bản đồ mã nguồn cho người cần sửa repo này. Không phải đặc tả giao thức.
> **Quy tắc:** tên hàm và tên package mới là chuẩn, số dòng thì không. Tìm bằng
> `grep -n "func (bc \*BlockChain) InsertChain" core/blockchain.go`.

go-ethereum (`geth`) là một tiến trình chạy client **execution layer** của Ethereum. Sau Merge,
geth không tự chọn chain chuẩn — consensus client điều khiển nó qua Engine API. Mọi thứ còn lại
trong repo tồn tại để: thực thi block, lưu state, nói chuyện với peer, và trả lời truy vấn.

---

## Nhìn từ trên cao

```
            consensus client (Prysm, Lighthouse, ...)
                        |  Engine API qua authrpc:8551 (JWT)
                        v
+-------------------------------------------------------------+
| cmd/geth            CLI flags -> config -> node              |
+-------------------------------------------------------------+
| node.Node           datadir, chaindb, p2p.Server,            |
|                     http/ws/ipc/authrpc, lifecycle registry  |
+-------------------------------------------------------------+
| eth.Ethereum        BlockChain | TxPool | handler+downloader |
| (một Lifecycle)     miner | filters | api backends           |
+-------------------------------------------------------------+
| lưu trữ             StateDB -> trie -> triedb -> rawdb       |
|                     -> ethdb/pebble + freezer (ancients)     |
+-------------------------------------------------------------+
```

Bốn lớp. Khi lạc đường, hỏi: *request này đang ở lớp nào?*

---

## Điểm vào — bắt đầu đọc ở đây

| Câu hỏi | File | Hàm |
| --- | --- | --- |
| Tiến trình khởi động thế nào? | `cmd/geth/main.go` | `geth()` -> `startNode()` |
| Node được ráp từ những gì? | `eth/backend.go` | `New()` |
| Ai sở hữu tiến trình? | `node/node.go` | `New()`, `Start()` |
| Một block được nhập ra sao? | `core/blockchain.go` | `insertChain()` |
| State đổi ở đâu? | `core/state_processor.go` | `Process()` |
| Opcode chạy ở đâu? | `core/vm/interpreter.go` | `EVM.Run()` |
| CL điều khiển ta thế nào? | `eth/catalyst/api.go` | `forkchoiceUpdated()`, `newPayload()` |
| Block được dựng ra sao? | `miner/payload_building.go` | `buildPayload()` |
| Sync bắt đầu từ đâu? | `eth/downloader/beaconsync.go` | `BeaconSync()` |
| Byte nằm ở đâu trên đĩa? | `core/rawdb/schema.go` | prefix khóa + `accessors_*.go` |
| RPC method khai báo ở đâu? | `internal/ethapi/api.go` | + `eth/backend.go APIs()` |
| Fork nào bật EIP nào? | `params/config.go` | `Rules()`, `params/forks/forks.go` |

---

## Bản đồ mã nguồn

### Vòng đời tiến trình
- **`cmd/geth`** — điểm vào CLI, lệnh phụ (`init`, `import`, `db`, `snapshot`, `account`, `console`).
- **`cmd/utils`** — mọi flag nằm ở đây; flag trở thành `ethconfig.Config`.
- **`node`** — container tiến trình: datadir, database, `p2p.Server`, các RPC stack, thứ tự
  start/stop, JWT cho Engine API.
- **`eth`** + **`eth/ethconfig`** — backend Ethereum. `eth/backend.go New()` ráp gần như mọi thứ;
  nên đọc trọn một lần từ đầu tới cuối.

### Lõi chain
- **`core`** — nhập block (`blockchain.go`), state transition (`state_processor.go`,
  `state_transition.go`), xác thực (`block_validator.go`), genesis, reorg, index tx.
- **`core/types`** — dữ liệu on-chain: header, block, năm loại transaction, receipt, log,
  withdrawal, block access list.
- **`core/txpool`** — router mỏng (`txpool.go`) trên các subpool: `legacypool` (theo nonce),
  `blobpool` (blob lưu trên đĩa).
- **`params`** / **`params/forks`** — hằng số giao thức và lịch fork (Frontier -> Bogota).
- **`consensus`** — interface `Engine`; `consensus/beacon` là lớp bọc hậu Merge. `clique`/`ethash`
  là legacy.
- **`core/forkid`** — cho phép peer từ chối nhau khi khác fork.

### EVM và state
- **`core/vm`** — máy ảo: `interpreter.go` (vòng lặp opcode), `jump_table.go`, `instructions.go`,
  `gas_table.go`, `eips.go` (hành vi theo fork), `contracts.go` (precompile).
- **`core/state`** — `StateDB`: state revert được nằm trên trie, `journal.go` để hoàn tác,
  `snapshot/` cho đọc phẳng, `trie_prefetcher.go` nạp trước song song.
- **`core/tracing`**, **`eth/tracers`** — hook quan sát thực thi và các tracer sau `debug_trace*`.

### Lưu trữ
- **`trie`** — Merkle Patricia Trie: node, hashing, proof, `stacktrie.go` để dựng tuần tự khi sync.
- **`triedb`** — lưu node theo hai scheme: `hashdb` (khóa theo hash, đếm tham chiếu) và `pathdb`
  (khóa theo path, diff layer + state history, rollback được — mặc định hiện nay).
- **`core/rawdb`** — sơ đồ khóa database và mọi accessor; cũng sở hữu freezer.
- **`ethdb`** — interface KV tối giản; backend `pebble` (mặc định), `leveldb`, `memorydb`, `remotedb`.

### Mạng
- **`p2p`** — peer, dial, mã hóa RLPx, discovery v4/v5, ENR/enode, DNS discovery.
- **`eth/protocols/eth`** — wire protocol `eth/68`: header, body, receipt, loan tin transaction.
- **`eth/protocols/snap`** — tải state theo range, nền tảng của snap sync.
- **`eth/downloader`** — sync khối lượng lớn (skeleton + backfill). **`eth/fetcher`** — block/tx lẻ
  được loan tin khi đã đồng bộ.

### Consensus layer và sản xuất block
- **`eth/catalyst`** — Engine API: `forkchoiceUpdated`, `getPayload`, `newPayload`; kèm beacon giả
  lập sau cờ `--dev`.
- **`miner`** — dựng payload theo yêu cầu và cải thiện dần cho tới khi CL đến lấy.
- **`beacon/*`** — kiểu dữ liệu phía consensus, light client, blsync.

### Bề mặt API
- **`rpc`** — thư viện JSON-RPC riêng của geth (server, client, subscription, các transport).
- **`internal/ethapi`** — cài đặt thật của namespace `eth`, điền tham số mặc định, `eth_simulateV1`.
- **`ethclient`**, **`graphql`**, **`ethstats`** — client và endpoint hướng ra ngoài.
- **`eth/filters`**, **`core/filtermaps`** — truy vấn log và chỉ mục log.

### Nền tảng và công cụ
- **`rlp`**, **`common`**, **`crypto`** — mã hóa, `Address`/`Hash`/hexutil, băm và chữ ký.
- **`accounts`**, **`signer`** — keystore, ví cứng, ABI, Clef.
- **`cmd/*`** — 12 công cụ khác: `evm`, `devp2p`, `abigen`, `rlpdump`, `era`, `workload`, ...
- **`tests`** — bộ execution-spec test chính thức. **`internal/build`** + `build/ci.go` — pipeline CI
  bạn phải chạy được ở máy mình.

---

## Sáu luồng đáng biết

Mọi thứ bạn sẽ sửa đều nằm trên một trong sáu đường này.

1. **Vòng lặp CL <-> EL** — `eth/catalyst/api.go`: `forkchoiceUpdated` (kèm `payloadAttributes`
   nghĩa là "dựng block cho tôi") -> `getPayload` -> `newPayload`.
2. **Nhập block** — `InsertChain` -> `insertChain` -> verify header/body -> `StateProcessor.Process`
   -> từng tx `ApplyTransactionWithEVM` -> `EVM.Run` -> `ValidateState` -> `writeBlockAndSetHead`
   -> `StateDB.Commit` -> `triedb.Update` -> `rawdb`.
3. **Lưu state** — `StateDB` (RAM, revert được) -> `trie` (hashing) -> `triedb` (hashdb | pathdb)
   -> sơ đồ khóa `rawdb` -> pebble + freezer.
4. **Vòng đời transaction** — RPC hoặc peer -> `TxPool.Add` -> subpool -> vừa broadcast cho peer
   vừa `Pending()` cho miner -> block -> `ChainHeadEvent` reset pool.
5. **Sync** — head từ CL -> `BeaconSync` -> `skeleton.Sync` điền header lùi dần -> các fetcher song
   song tải body/receipt; với `--syncmode snap`, `snap` tải state theo range rồi vá (heal).
6. **Request RPC** — transport -> định tuyến ở `rpc/handler.go` -> `internal/ethapi` ->
   `ethapi.Backend` -> `eth/api_backend.go` -> chain/state/txpool.

Mỗi luồng có một walkthrough ngay trong editor: xem [`.tours/`](../../../.tours)
(VS Code + extension CodeTour, chạy hoàn toàn offline).

---

## Bất biến và quy tắc ngón tay cái

- **Thay đổi hành vi consensus phải gate theo fork.** Mọi thay đổi ngữ nghĩa thực thi phải nằm sau
  một cờ fork trong `params/config.go`; xem mẫu ở `core/vm/eips.go`. Không gate thì mọi node chạy
  lại lịch sử sẽ ra state root khác.
- **`StateDB` revert được, `triedb` thì không.** Thứ gì phải sống sót qua một call thất bại thì phải
  nằm phía trên ranh giới `Commit`.
- **Interface là đường nối để học.** `consensus.Engine`, `txpool.SubPool`, `ethapi.Backend`,
  `ethdb.KeyValueStore`. Đọc interface trước, rồi một implementation.
- **Code sinh tự động bị CI kiểm.** File mở đầu bằng `// Code generated` (`gen_*.go`) phải được sinh
  lại (`make devtools`, rồi `go generate`), nếu không `check_generate` sẽ đỏ.
- **Thêm một RPC method chạm bốn chỗ:** hàm trong `internal/ethapi/api.go` (hoặc `eth/api_*.go`),
  interface `Backend`, `eth/api_backend.go`, và `internal/web3ext/web3ext.go` cho console.
- **Giữ diff nhỏ.** Xem `AGENTS.md`: không refactor kèm, không thêm dependency nếu task không đòi.

---

## Build, chạy, test

```shell
make geth                              # build
make all                               # build mọi công cụ trong cmd/
go run ./build/ci.go test -short       # vòng lặp nhanh khi đang code
go run ./build/ci.go test              # đầy đủ, bắt buộc trước khi commit
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```

Chạy một node để nghịch:

```shell
./build/bin/geth --dev --http --http.api eth,net,web3,debug   # chain riêng, tức thì
./build/bin/geth attach                                       # console JS
```

Checklist đầy đủ trước commit: `AGENTS.md`.

---

## Đi tiếp

- Chưa từng build geth: [`getting-started.md`](getting-started.md)
- Tra theo công việc ("tôi muốn sửa X, bắt đầu ở đâu?"): [`start-here.md`](start-here.md)
- Lộ trình học có cấu trúc: [`learning-path.md`](learning-path.md)
- Triển khai và vận hành node: [`run-a-node.md`](run-a-node.md)
- Test, tracer, profiling, delve: [`debugging.md`](debugging.md)
- Thuật ngữ (Anh ↔ Việt): [`glossary.md`](glossary.md)
- Walkthrough trong editor: [`.tours/`](../../../.tours)
- Quyết định và lý do: [`../adr/`](../adr)
- Tài liệu API offline: `go doc ./core/vm` hoặc `pkgsite -http :8080` (xem `../README.md`)
