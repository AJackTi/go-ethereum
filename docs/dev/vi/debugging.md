# Test và debug

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/debugging.md)
> Cách chứng minh thay đổi của bạn chạy đúng, và cách tìm ra vì sao nó không chạy. Mọi câu lệnh ở
> đây chạy được ngay trên repo này, không cần dịch vụ bên ngoài.

## Chọn công cụ theo triệu chứng

| Triệu chứng | Dùng cái này |
| --- | --- |
| "Thay đổi của tôi có làm hỏng gì không?" | `go run ./build/ci.go test -short`, rồi chạy đủ |
| "Thay đổi EVM có đúng đặc tả không?" | `tests/` (execution-spec fixtures) và `cmd/evm statetest` |
| "Block này thực sự làm gì?" | `debug.traceBlockByNumber`, `debug_traceTransaction` |
| "Vì sao block bị từ chối?" | `debug.getBadBlocks`, rồi đọc ngược từ `ValidateState` |
| "Vì sao chậm / ăn RAM?" | `--pprof` + `go tool pprof`, `debug.metrics` |
| "Luồng thực thi đi đâu?" | Breakpoint `dlv`, hoặc một dòng `log.Info` tạm |
| "Trên đĩa đang có gì?" | `geth db inspect`, `geth db get`, `debug.dbGet` |

---

## 1. Test

```shell
# một package, chi tiết
go test ./core/... -run TestStateProcessorErrors -v

# race detector — bắt buộc với mọi thứ đụng goroutine
go test ./eth/... -race

# runner của dự án: linter, kiểm tra code sinh tự động và bộ spec
go run ./build/ci.go test -short      # vòng lặp nhanh khi đang code
go run ./build/ci.go test             # đầy đủ; chạy trước mọi commit
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```

`-short` bỏ qua các tổ hợp chậm của `tests/` (bộ fixture execution-spec chính thức của Ethereum).
Mọi thay đổi ảnh hưởng hành vi consensus đều phải được kiểm bằng lần chạy đầy đủ — đó chính là bộ
test quyết định node của bạn có đồng thuận với mạng hay không.

### Dựng chain ngay trong test

Đừng dùng mạng thật để tái hiện một bug về chain. `core/chain_makers.go` sinh block ngay trong tiến
trình:

```go
gspec := &core.Genesis{Config: params.TestChainConfig, Alloc: types.GenesisAlloc{addr: {Balance: big.NewInt(1e18)}}}
db, blocks, _ := core.GenerateChainWithGenesis(gspec, engine, 10, func(i int, b *core.BlockGen) {
    b.AddTx(tx)
})
chain, _ := core.NewBlockChain(db, gspec, engine, nil)
if _, err := chain.InsertChain(blocks); err != nil { t.Fatal(err) }
```

Với test ở tầng ứng dụng — thứ mà bình thường phải gọi tới một endpoint RPC — hãy dùng
`ethclient/simulated`: một node đầy đủ ngay trong binary test, không cổng, không datadir.

### Fuzzing

`tests/fuzzers/` chứa các target (RLP, bn256, bls12381, range proof, tx fetcher). Chạy như Go bình
thường:

```shell
go test ./tests/fuzzers/rangeproof/... -fuzz Fuzz -fuzztime 60s
```

---

## 2. Debug một node đang chạy

### Log

```shell
geth --verbosity 5                        # 1 error … 3 info (mặc định) … 5 trace
geth --vmodule 'core/*=5,p2p=4'           # chỉ ồn ở chỗ bạn đang làm
```

Cả hai đổi được lúc đang chạy từ console — tiện với node bạn không muốn restart:

```javascript
debug.verbosity(5)
debug.vmodule("eth/downloader=5")
```

### Namespace `debug`

Attach bằng `geth attach <datadir>/geth.ipc`, rồi:

```javascript
debug.traceBlockByNumber(1234, {tracer: "callTracer"})   // mọi call frame trong block
debug.traceTransaction("0x…", {tracer: "prestateTracer"})// state mà một tx đụng tới
debug.getBadBlocks()                                     // các block node này từ chối, kèm lý do
debug.storageRangeAt(blockHash, txIndex, contract, "0x0", 10)
debug.dumpBlock(1234)                                    // dump toàn bộ state tại một block
debug.intermediateRoots(blockHash)                       // state root sau từng tx — tìm đúng tx bị lệch
debug.stacks()                                           // dump goroutine khi node treo
debug.memStats()
debug.setHead("0x100")                                   // tua ngược chain (phá dữ liệu, chỉ dùng khi dev)
```

`debug.intermediateRoots` là cách nhanh nhất khoanh vùng một consensus bug: so với client khác, chỉ
số đầu tiên lệch nhau chính là transaction gây vỡ.

!!! warning
    `debug` là công cụ nội bộ. Đừng bao giờ mở nó qua `--http.api` công khai.

### Profiling

```shell
geth --pprof --pprof.addr 127.0.0.1 --pprof.port 6060 --metrics
```

```shell
go tool pprof -http=: http://localhost:6060/debug/pprof/profile?seconds=30   # CPU
go tool pprof -http=: http://localhost:6060/debug/pprof/heap                 # bộ nhớ
curl -s localhost:6060/debug/pprof/goroutine?debug=2 | head -50              # goroutine kẹt
curl -s localhost:6060/debug/metrics/prometheus | grep chain_               # tốc độ nhập block
```

Profile block và mutex mặc định tắt; chỉ bật khi đang đo:

```javascript
debug.setBlockProfileRate(1)
debug.setMutexProfileFraction(1)
```

---

## 3. Làm việc ở tầng EVM

```shell
# chạy bytecode thô và xem stack
go run ./cmd/evm run --debug --code 6001600101

# chạy một fixture state test
go run ./cmd/evm statetest tests/testdata/GeneralStateTests/…/foo.json

# đọc RLP bằng mắt
go run ./cmd/rlpdump <hex>
```

`cmd/evm` không dựng node, không database, không mạng — khi bug nằm trong interpreter thì cách này
nhanh gấp trăm lần tái hiện trên chain.

---

## 4. Chạy từng bước bằng debugger

```shell
go install github.com/go-delve/delve/cmd/dlv@latest

dlv test ./core -- -test.run TestStateProcessorErrors     # bước qua một test
dlv exec ./build/bin/geth -- --dev --http                 # bước qua node đang chạy
(dlv) break core/state_processor.go:67
(dlv) continue
(dlv) print block.NumberU64()
```

Extension Go của VS Code làm y hệt qua giao diện; lệnh delve ở trên chính là thứ nó chạy bên dưới.

---

## 5. Đọc một block bị từ chối

Thứ tự kiểm tra, khớp với đường nhập block trong
[tour 02](https://github.com/AJackTi/go-ethereum/tree/master/.tours):

1. **`debug.getBadBlocks()`** — geth giữ lại block bị từ chối kèm lỗi xác thực.
2. **Kiểm tra nào fail?** Lệch state root nghĩa là thực thi bị phân kỳ; lỗi body hoặc header nghĩa
   là block đã sai từ trước khi chạy.
3. **`debug.intermediateRoots(hash)`** — tìm transaction đầu tiên có post-state root khác.
4. **`debug.traceTransaction`** trên transaction đó với `callTracer`, rồi `prestateTracer`.
5. **Tái hiện trong test** bằng `chain_makers`, rồi sửa với test đó làm thước đo.

Các sự cố consensus trong lịch sử được ghi lại ở
[`docs/postmortems/`](https://github.com/AJackTi/go-ethereum/tree/master/docs/postmortems) — đáng
đọc một lần để thấy người ta chẩn đoán kiểu này ngoài đời ra sao.

---

## 6. Soi database

```shell
geth db inspect      --datadir <dir>     # dung lượng theo từng loại dữ liệu
geth db stats        --datadir <dir>
geth db get          --datadir <dir> <hex-key>
geth db inspect-history --datadir <dir>  # state history của pathdb
geth snapshot verify-state --datadir <dir>
```

Prefix khóa định nghĩa trong `core/rawdb/schema.go`; mọi accessor đọc/ghi chúng nằm ngay cạnh, trong
các file `accessors_*.go`.

---

## Liên quan

- [Tôi muốn sửa X](start-here.md) — nơi thực hiện thay đổi mà bạn đang test.
- [Vận hành node](run-a-node.md) — các flag ở đây đặt trong bối cảnh vận hành.
- [Kiến trúc](architecture.md) — luồng mà từng công cụ đang soi.
