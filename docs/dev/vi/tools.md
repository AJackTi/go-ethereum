# Công cụ trong `cmd/`

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/tools.md)
> Có mười hai binary trong `cmd/` (thư mục thứ mười ba, `cmd/utils`, là thư viện). `make all` build
> hết vào `build/bin/`. Phần lớn là cách quan sát hệ thống từ bên ngoài — đúng thứ bạn cần khi debug.

```shell
make all              # tất cả công cụ
make geth             # chỉ node
go run ./cmd/evm ...  # hoặc chạy thẳng, không cần cài
```

---

## geth

Bản thân node, cộng khoảng bốn mươi lệnh phụ. Những lệnh đáng biết:

| Lệnh | Dùng để |
| --- | --- |
| `geth --dev` | chain dùng xong bỏ, tài khoản có tiền, block tức thì |
| `geth attach <ipc>` | console JavaScript tới node đang chạy |
| `geth init <genesis.json>` | khởi tạo datadir từ genesis tùy chỉnh |
| `geth dumpgenesis` | in genesis của một mạng đã biết |
| `geth import` / `export` | chuyển block ra/vào dưới dạng RLP |
| `geth import-history` / `export-history` | như trên, dùng file era |
| `geth prune-history` | bỏ lịch sử trước Merge khỏi datadir đang có |
| `geth download-era` | tải file lịch sử era |
| `geth db inspect` | đĩa đi đâu, theo từng loại dữ liệu |
| `geth db stats` / `compact` | sức khỏe database và nén |
| `geth db get` / `put` / `delete` | truy cập khóa thô — nguy hiểm nhưng hữu ích |
| `geth db inspect-history` | state history của pathdb |
| `geth snapshot verify-state` | đối chiếu snapshot state với trie |
| `geth snapshot prune-state` | cắt tỉa state lịch sử (hashdb) |
| `geth snapshot dump` / `traverse-state` | đi bộ trên state để kiểm toán |
| `geth removedb` | xóa dữ liệu chain, giữ keystore |
| `geth dumpconfig` | in config hiệu lực dưới dạng TOML |
| `geth account new` / `list` / `import` | quản lý keystore |

`geth dumpconfig` bị đánh giá thấp: nó cho thấy chính xác các flag của bạn quy về giá trị gì, giải
quyết gọn phần lớn câu hỏi "cái này có bật thật không?".

---

## evm — EVM không cần node

```shell
go run ./cmd/evm run --debug --code 6001600101      # chạy bytecode, in từng bước
go run ./cmd/evm statetest <fixture.json>           # chạy một state test theo spec
go run ./cmd/evm bench <file>                       # benchmark bytecode
go run ./cmd/evm fuzz / cross-check                 # fuzz và đối chiếu khác biệt
```

Không database, không mạng, không chain. Khi bug nằm trong interpreter thì đây là cách tái hiện
nhanh nhất. Flag hữu ích: `--dump` (state sau khi chạy), `--statdump` (đếm opcode),
`--trace.format`, `--trace.nomemory`.

---

## devp2p — chọc vào mạng từ bên ngoài

```shell
go run ./cmd/devp2p discv4 ping <enode>        # node đó còn sống không?
go run ./cmd/devp2p discv4 resolve <enode>     # tra một node trong DHT
go run ./cmd/devp2p discv4 crawl <file>        # quét DHT thành một tập node
go run ./cmd/devp2p discv5 ...                 # cùng họ, giao thức v5
go run ./cmd/devp2p rlpx eth-test ...          # kiểm tra tuân thủ protocol với node local
go run ./cmd/devp2p dns ...                    # dựng và công bố danh sách node qua DNS
```

Bộ `eth-test` là phép kiểm chuẩn khi bạn đổi bất cứ thứ gì trong `eth/protocols/eth`.

---

## abigen — sinh binding Go từ ABI

```shell
./build/bin/abigen --abi Token.abi --bin Token.bin --pkg token --type Token --out token.go
```

Sinh ra method Go có kiểu cho contract. Ví dụ sử dụng nằm ở
[Dùng geth từ code của bạn](using-geth.md). Commit file sinh ra, giống cách geth commit các file
`gen_*.go` của chính nó.

`--v2` sinh binding kiểu mới; không có cờ đó thì ra API v1 (`bind.NewKeyedTransactorWithChainID`,
`bind.WaitMined`) — chính là API các ví dụ trong sổ tay này dùng.

---

## rlpdump và abidump — đọc byte

```shell
go run ./cmd/rlpdump <hex>          # cấu trúc RLP, đọc được bằng mắt
go run ./cmd/rlpdump -reverse       # chiều ngược lại
go run ./cmd/abidump <hexdata>      # giải mã calldata theo các ABI đã biết
```

`rlpdump` là cách nhanh nhất trả lời "trong đống byte này thực ra có gì" khi debug protocol hoặc
nội dung database.

---

## ethkey — thao tác file khóa không cần node

```shell
go run ./cmd/ethkey generate                       # tạo file khóa mới
go run ./cmd/ethkey inspect <file>                 # xem address và public key
go run ./cmd/ethkey changepassword <file>          # mã hóa lại bằng mật khẩu mới
go run ./cmd/ethkey signmessage <file> <message>
go run ./cmd/ethkey verifymessage <addr> <sig> <message>
```

Làm việc trực tiếp trên file keystore. Đừng trỏ nó vào keystore mà một node đang chạy sở hữu.

---

## era — file lịch sử

```shell
go run ./cmd/era block --dir <dir> --network <name>
go run ./cmd/era info   --dir <dir>
go run ./cmd/era verify --dir <dir>
```

File era là cách đóng gói chuẩn cho các đoạn lịch sử chain — định dạng đứng sau
`geth import-history`, `export-history` và `download-era`. Verify là cách kiểm tra một kho lịch sử
trước khi import.

---

## workload — RPC dưới tải

```shell
go run ./cmd/workload filtergen  <rpc-url>    # sinh tập truy vấn log filter
go run ./cmd/workload historygen <rpc-url>    # sinh truy vấn lịch sử
go run ./cmd/workload test       <rpc-url>    # chạy bộ đã sinh lên một node
go run ./cmd/workload filterfuzz <rpc-url>    # fuzz API filter
```

Công cụ cho câu hỏi "sau thay đổi của tôi, `eth_getLogs` còn nhanh không?" — nó tạo ra tập truy vấn
lặp lại được, không phải một benchmark ngẫu hứng.

---

## blsync — light client cho beacon

Một beacon-chain light syncer độc lập (`beacon/light`, `beacon/blsync`). Nó bám chain consensus mà
không cần chạy consensus client đầy đủ, và có thể điều khiển Engine API của một execution node.
Hợp để thử nghiệm; không thay thế được một CL thật trên node có validator.

---

## fetchpayload và keeper — thực thi stateless

```shell
go run ./cmd/fetchpayload -rpc http://localhost:8545 <block>
```

`fetchpayload` kéo một block cùng execution witness của nó từ node qua RPC rồi ghi ra payload
RLP/JSON.

`keeper` tiêu thụ đúng payload đó: nó thực thi block **stateless** từ witness và đối chiếu state
root cùng receipt root tính được với header — được viết để chạy như một zkvm guest (xem
`cmd/keeper/README.md`). Lưu ý nó là một **Go module riêng** (`cmd/keeper/go.mod`), build qua
`build/ci.go` với build tag riêng, nên hãy dùng `make all` chứ đừng `go run`.

Hai cái ghép lại chính là cửa vào thực tế của `core/stateless`.

---

## Không có trong repo này

**Clef**, trình ký độc lập, không còn command ở đây nữa; thư viện nền của nó vẫn nằm trong
[`signer/`](https://github.com/AJackTi/go-ethereum/tree/master/signer). Các consensus client
(Prysm, Lighthouse, Teku, Nimbus, Lodestar) là dự án riêng — xem [Vận hành node](run-a-node.md).

---

## Liên quan

- [Test và debug](debugging.md) — triệu chứng nào dùng công cụ nào.
- [Dùng geth từ code của bạn](using-geth.md) — phía thư viện.
- `go run ./cmd/<tool> --help` — đầy đủ flag, offline, luôn đúng hiện trạng.
