# Bắt đầu ở đây: tôi muốn sửa X

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/start-here.md)
> Đây là mục lục theo công việc. Bản đồ toàn repo xem [`ARCHITECTURE.md`](../../../ARCHITECTURE.md)
> hoặc bản tiếng Việt [`architecture.md`](architecture.md).

Tìm việc của bạn bên dưới. Mỗi mục cho biết: file mở đầu tiên, những chỗ khác thường bị chạm theo,
và cách tự chứng minh là chạy đúng. Luôn xác nhận tên hàm bằng `grep -n` trước khi sửa — bảng này
là bản đồ, không phải thực địa.

---

## 1. Thêm vào bề mặt API

### Thêm một JSON-RPC method mới
1. **Mở trước:** `internal/ethapi/api.go` (namespace `eth`) hoặc `eth/api_debug.go` / `eth/api_admin.go`.
2. **Chạm theo:** interface `Backend` trong `internal/ethapi/backend.go`; cài đặt của nó ở
   `eth/api_backend.go`; `internal/web3ext/web3ext.go` để console JS biết method.
3. **Kiểm chứng:** `geth --dev --http --http.api eth,debug`, rồi `curl` method đó; viết test cạnh package.
4. **Coi chừng:** mọi implementation của `Backend` đều phải compile, gồm cả backend trong test và
   `ethclient/simulated`.

### Đổi dữ liệu một RPC trả về
1. **Mở trước:** các helper marshal trong `internal/ethapi/api.go` (`RPCMarshalBlock`, ...).
2. **Chạm theo:** `ethclient/` nếu client Go có parse trường đó; `graphql/` nếu có expose.
3. **Coi chừng:** đổi tên trường là breaking change với người dùng. Thêm mới, đánh dấu deprecated,
   rồi mới xóa.

---

## 2. Thay đổi giao thức và consensus

### Cài đặt một EIP đổi hành vi EVM
1. **Mở trước:** `core/vm/eips.go` — chép theo mẫu của EIP mới nhất.
2. **Chạm theo:** `params/config.go` (cờ fork + `Rules`), `params/forks/forks.go`,
   `core/vm/jump_table.go` (opcode mới/đổi), `core/vm/gas_table.go` hoặc `gascosts.go`,
   `params/protocol_params.go` cho hằng số.
3. **Kiểm chứng:** `go test ./core/vm/...`, rồi bộ spec: `go run ./build/ci.go test`
   (chạy `tests/` với fixture chính thức).
4. **Coi chừng:** **bắt buộc** gate theo fork. Không gate thì mọi node chạy lại lịch sử sẽ tính ra
   state root khác.

### Đổi chi phí gas
Cùng đường như trên. Gas nằm ở ba nơi tùy opcode: `gas_table.go` (động), `jump_table.go` (hằng),
`operations_acl.go` (có access list, sau Berlin).

### Thêm một loại transaction mới
1. **Mở trước:** `core/types/transaction.go` — interface `TxData`.
2. **Chạm theo:** file mới `core/types/tx_*.go`; `transaction_marshalling.go`;
   `transaction_signing.go`; `core/txpool/validation.go` và đúng subpool;
   `internal/ethapi/transaction_args.go`; sinh lại RLP (`gen_*.go` bằng `go generate`).
3. **Kiểm chứng:** test encode/decode khứ hồi, rồi gửi loại tx mới trên chain `--dev`.

---

## 3. Lưu trữ và hiệu năng

### Đổi thứ được ghi xuống đĩa
1. **Mở trước:** `core/rawdb/schema.go` — các prefix khóa.
2. **Chạm theo:** `core/rawdb/accessors_*.go` tương ứng; phần tính dung lượng của `geth db inspect`
   trong `cmd/geth/dbcmd.go`.
3. **Coi chừng:** đụng prefix sẽ hỏng dữ liệu âm thầm. Kiểm tra prefix mới chưa ai dùng, và quyết
   định database cũ gặp code mới thì xử lý ra sao.

### Làm việc ở tầng trie / state
1. **Mở trước:** `triedb/database.go`, rồi `triedb/pathdb/` (scheme mặc định) hoặc `triedb/hashdb/`.
2. **Chạm theo:** `core/state/statedb.go` nếu thay đổi lộ ra phía trên ranh giới commit; `trie/`
   nếu đụng encoding hoặc hashing node.
3. **Kiểm chứng:** `go test ./trie/... ./triedb/...`; đo bằng `go test -bench . -benchmem`.

### Truy một vụ tụt hiệu năng
1. **Đo trước:** `geth --pprof`, rồi `go tool pprof http://localhost:6060/debug/pprof/profile`.
2. **Nghi phạm quen thuộc:** `core/state/trie_prefetcher.go`, `triedb/pathdb/buffer.go`, đường ghi
   trong `core/blockchain.go`, `eth/protocols/snap` khi đang sync.
3. **Kiểm chứng:** ghi số liệu trước/sau vào PR; `debug.metrics(false).chain` cho tốc độ nhập block.

---

## 4. Mạng

### Đổi hoặc thêm message của wire protocol
1. **Mở trước:** `eth/protocols/eth/protocol.go` (mã message) hoặc `eth/protocols/snap/protocol.go`.
2. **Chạm theo:** `handlers.go` (phục vụ), `peer.go` (gửi), `eth/handler.go`, và `dispatcher.go`
   nếu là dạng request/response.
3. **Kiểm chứng:** `go run ./cmd/devp2p rlpx eth-test ...` với một node local.
4. **Coi chừng:** đổi protocol cần tăng version và giữ tương thích với peer bản cũ.

### Debug chuyện không kết nối được peer
`geth --verbosity 5` cho thấy handshake. `admin.peers` trong console cho thấy ai đang kết nối.
Lệch `core/forkid` là lý do phổ biến nhất khiến hai node từ chối nhau.

---

## 5. Dựng block và transaction pool

### Đổi cách chọn transaction vào block
1. **Mở trước:** `miner/worker.go` -> `fillTransactions`.
2. **Chạm theo:** `core/txpool/txorder/` cho thứ tự, filter `Pending()` trong `core/txpool/txpool.go`.
3. **Kiểm chứng:** chain `--dev`, gửi các tx cạnh tranh nhau, soi block sinh ra.

### Đổi luật chấp nhận transaction
1. **Mở trước:** `core/txpool/validation.go` (kiểm tra dùng chung).
2. **Chạm theo:** `legacypool/legacypool.go` hoặc `blobpool/blobpool.go` cho giới hạn riêng từng pool.
3. **Coi chừng:** luật chặt hơn có thể làm kẹt các tx đã nằm sẵn trong pool sau khi restart.

---

## 6. Engine API / tích hợp consensus client

1. **Mở trước:** `eth/catalyst/api.go`.
2. **Chạm theo:** `beacon/engine/types.go` cho struct payload; `miner/payload_building.go` nếu đổi
   cách dựng block; `eth/catalyst/simulated_beacon.go` để `--dev` không hỏng.
3. **Kiểm chứng:** `--dev` chạy trọn vòng lặp ngay tại máy; phiên bản method phải bám đúng đặc tả
   Engine API.

---

## 7. Khi hoàn toàn không biết bắt đầu từ đâu

Chạy thang bậc này, đúng thứ tự:

1. **Tái hiện lỗi.** `geth --dev` hoặc một test dùng `core/chain_makers.go` nhanh hơn mạng thật.
2. **Grep chuỗi mà người dùng nhìn thấy.** Nội dung lỗi, tên RPC method, dòng log, tên flag.
   `grep -rn "insufficient funds" --include="*.go"`.
3. **Lần ngược lên trên.** Tìm được hàm rồi thì grep tên hàm đó để ra nơi gọi.
4. **Đọc test.** `*_test.go` cạnh package cho thấy cách dùng đúng.
5. **Đọc lịch sử.** `git log -p --follow <file>` — phần lớn code khó hiểu là vết sẹo của một bug cũ,
   và commit message nói bug nào.
6. **Đi một tour.** `.tours/` dẫn từng bước qua các luồng chính ngay trong editor.

---

## Trước khi commit

Checklist đầy đủ ở [`AGENTS.md`](../../../AGENTS.md). Bản ngắn, đúng thứ tự này:

```shell
gofmt -w <files> && goimports -w <files>
make all
go run ./build/ci.go test -short      # khi đang code
go run ./build/ci.go test             # trước khi commit — đầy đủ
go run ./build/ci.go lint
go run ./build/ci.go check_generate
```
