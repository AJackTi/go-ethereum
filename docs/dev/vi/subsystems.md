# Các hệ thống con còn lại

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/subsystems.md)
> Những phần của repo mà sáu luồng chính không đi qua. Mỗi cái đều tùy chọn, mỗi cái đều làm ai đó
> bất ngờ, và không cái nào được nhắc ở chỗ khác trong sổ tay này.

## GraphQL

Một giao diện truy vấn thứ hai bên cạnh JSON-RPC, cùng cổng HTTP, ở đường dẫn `/graphql`.

```shell
geth --http --graphql --graphql.corsdomain '*' --graphql.vhosts localhost
```

- `graphql/schema.go` — schema, dưới dạng chuỗi Go. Đây **chính là** hợp đồng API.
- `graphql/graphql.go` — resolver, gọi đúng `ethapi.Backend` mà tầng RPC dùng.
- `graphql/service.go` — `New(stack, backend, filterSystem, cors, vhosts)`, được đăng ký từ
  `cmd/geth/config.go` khi bật cờ.
- `graphql/graphiql.go` — trình khám phá chạy trong trình duyệt.

Thêm một trường nghĩa là sửa schema và resolver tương ứng. Nó đọc từ cùng backend với
`internal/ethapi`, nên năng lực mới thường xuất hiện ở đó trước, rồi mới lộ ra đây.

---

## ethstats — báo cáo lên dashboard

```shell
geth --ethstats <nodename>:<secret>@<host>:<port>
```

`ethstats/ethstats.go` mở WebSocket tới một stats server và đẩy liên tục trạng thái node: head
block, số peer, kích thước transaction pool, đang sync hay không. `New(node, backend, engine, url)`
đấu nối; hàm `loop` đăng ký các sự kiện chain-head, transaction mới và payload mới rồi gửi báo cáo.

Chỉ đi ra ngoài, và hoàn toàn tùy chọn — nó sinh ra để nuôi các dashboard công khai của mạng. Đừng
nhầm với `--metrics`, thứ là dữ liệu Prometheus của riêng bạn (xem [Vận hành node](run-a-node.md)).

---

## filtermaps — chỉ mục log

`eth_getLogs` ngày trước nghĩa là quét bloom filter của từng block. `core/filtermaps` thay việc đó
bằng một chỉ mục chuyên dụng.

- `core/filtermaps/filtermaps.go` — `NewFilterMaps(db, chainView, historyCutoff, finalBlock, params, config)`,
  được dựng trong `eth/backend.go`.
- `core/filtermaps/indexer.go` — dựng và duy trì chỉ mục ở nền; nó bám head và tua ngược khi reorg.
- `core/filtermaps/checkpoints_*.json` — checkpoint theo từng mạng để node mới không phải index lại
  từ genesis.
- `eth/filters/` — bề mặt RPC nằm trên (`eth_getLogs`, `eth_subscribe`).

Hệ quả thực tế: sau khi sync xong, truy vấn log có thể chậm hoặc thiếu cho tới khi index đuổi kịp.
`--history.logs` quyết định index lùi về bao xa.

---

## signer — phần còn lại của Clef

Binary `clef` độc lập không còn trong repo này. Ba package còn lại, và chúng vẫn được dùng:

- `signer/core/apitypes` — cấu trúc typed-data theo EIP-712, dùng ở mọi nơi ký dữ liệu có cấu trúc.
- `signer/fourbyte` — cơ sở dữ liệu selector hàm (`4byte.json`) cộng phần kiểm tra tham số; đây là
  thứ `cmd/abidump` dùng để giải mã calldata.
- `signer/storage` — kho key/value mã hóa AES-GCM.

Nếu bạn tìm phần quản lý tài khoản bên trong geth thì đó là `accounts/` — xem
[Dùng geth từ code của bạn](using-geth.md).

---

## Chuyển đổi sang binary trie

Nền móng cho việc chuyển state từ Merkle Patricia Trie sang binary trie.

```shell
geth bintrie convert --datadir <dir> [--delete-source] [--memory-limit <MB>]
```

- `trie/bintrie` — bản thân binary trie.
- `trie/transitiontrie` — đọc xuyên cả hai cấu trúc trong lúc đang chuyển đổi.
- `core/overlay` — lớp overlay khiến state chuyển đổi dở dang vẫn dùng được.
- `cmd/geth/bintrie_convert.go` — câu lệnh.

Thử nghiệm. Đừng chạy trên datadir mà bạn còn cần.

---

## File era và cắt lịch sử

Lịch sử chain được đóng gói thành file era, nhờ vậy nó di chuyển và cắt tỉa được.

```shell
geth download-era ...        # tải file lịch sử
geth import-history ...      # nạp vào một datadir
geth export-history ...      # xuất ra
geth prune-history           # bỏ lịch sử trước Merge khỏi datadir đang có
```

- `internal/era` — định dạng: `e2store`, chỉ mục, reader và writer.
- `core/history` — chính sách giữ lịch sử đứng sau `--history.chain all|postmerge|postprague`.
- `cmd/era` — soi và verify file era ngoài node ([Công cụ](tools.md)).

Đây là bộ máy đứng sau câu "node của tôi không cần 20 năm lịch sử".

---

## Tracing OpenTelemetry

Tracing phân tán cho việc xử lý RPC, tách biệt với `--metrics` và với `debug_trace*` (cái đó trace
thực thi EVM, không phải tiến trình).

```shell
geth --rpc.telemetry --rpc.telemetry.endpoint <otlp-endpoint> \
     --rpc.telemetry.username <u> --rpc.telemetry.password <p> \
     --rpc.telemetry.instance-id <id>
```

- `internal/telemetry` — helper span dựng trên `go.opentelemetry.io/otel`.
- `internal/telemetry/tracesetup` — đấu nối exporter.
- `node.Config.OpenTelemetry` — endpoint và `SampleRatio` (mặc định 1.0).

Hữu ích khi bạn cần biết thời gian thực trong một request đã đi đâu.

---

## Các package phía beacon

geth là execution client, nhưng vẫn mang theo code phía consensus dành cho light client:

- `beacon/types` — header beacon, cấu trúc SSZ.
- `beacon/light` — sync committee và proof cho light client.
- `beacon/blsync` — bám beacon chain mà không cần consensus client đầy đủ, và có thể điều khiển
  Engine API của một execution node. `cmd/blsync` là binary độc lập.
- `beacon/engine` — kiểu payload của Engine API, dùng chung với `eth/catalyst`.
- `beacon/merkle`, `beacon/params` — các primitive hỗ trợ.

Với node có validator, bạn vẫn cần consensus client thật — xem [Vận hành node](run-a-node.md).

---

## Vài góc nhỏ đáng biết

| Package | Là gì |
| --- | --- |
| `event` | Pub/sub nội bộ dùng cho `ChainHeadEvent`, `NewTxsEvent` và các sự kiện khác |
| `metrics` | Registry metrics, kèm exporter InfluxDB và Prometheus |
| `internal/jsre` | Runtime JavaScript đứng sau `geth console` |
| `internal/web3ext` | Binding cho console — RPC method mới cần một mục ở đây |
| `internal/flags` | Phân loại flag và cách bố trí phần help |
| `common/prque`, `common/lru`, `common/mclock` | Hàng đợi ưu tiên, cache, và đồng hồ giả lập được, dùng khắp nơi |
| `internal/reexec`, `internal/cmdtest` | Bộ khung test các binary từ đầu tới cuối |

---

## Liên quan

- [Kiến trúc](architecture.md) — các package mà sáu luồng chính có đi qua.
- [Công cụ](tools.md) — các binary điều khiển vài hệ thống con ở trên.
- [Vận hành node](run-a-node.md) — các flag vận hành được nhắc ở đây.
