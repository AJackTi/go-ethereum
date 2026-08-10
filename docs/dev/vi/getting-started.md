# Bắt đầu từ số không

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/getting-started.md)
> Dành cho người chưa từng build geth và chưa rõ execution client là gì. Một giờ, từ tay trắng tới
> một node đang chạy và nói chuyện được.

## geth thực chất là gì

Một node Ethereum ngày nay gồm **hai chương trình**:

| | Execution layer (repo này) | Consensus layer (chương trình riêng) |
| --- | --- | --- |
| Làm gì | chạy transaction, giữ state tài khoản, phục vụ RPC `eth_*` | chọn chain chuẩn, quản validator, quyết định finality |
| Phần mềm | geth, Nethermind, Besu, Erigon, Reth | Prysm, Lighthouse, Teku, Nimbus, Lodestar |
| Nói chuyện qua | — | Engine API ở `localhost:8551`, xác thực bằng file JWT |

geth một mình **không thể bám mainnet** — không có gì nói cho nó biết chain nào là chuẩn. Vì vậy
bước 4 dưới đây chạy một consensus layer giả, và [Vận hành node](run-a-node.md) mới ghép geth với
một CL thật.

Từ ngữ bạn sẽ gặp trong giờ đầu tiên được gom ở [bảng thuật ngữ](glossary.md).

---

## 1. Chuẩn bị

- **Go 1.24 trở lên** — bản trong `go.mod` mới là chuẩn: `grep '^go ' go.mod`.
- **Một C compiler** — macOS: `xcode-select --install`; Debian/Ubuntu: `build-essential`.
  Cần vì một phần code mật mã viết bằng C.
- **git**, và khoảng 2 GB đĩa trống cho bản build và một chain dev.

```shell
go version     # go1.24.x trở lên
cc --version   # C compiler nào cũng được
```

Biết Go thì tốt nhưng không bắt buộc để bắt đầu đọc. [Go tour](https://go.dev/tour/) đủ dùng trong
một buổi chiều; geth viết Go rất chuẩn mực, không màu mè.

---

## 2. Build

```shell
git clone https://github.com/AJackTi/go-ethereum
cd go-ethereum
make geth                 # lần đầu ~2-5 phút
./build/bin/geth version
```

`make all` build mọi công cụ trong `cmd/` (`evm`, `devp2p`, `abigen`, `rlpdump`, ...). Chưa cần vội.

!!! tip "Nếu build lỗi"
    Gần như luôn là Go quá cũ hoặc thiếu C compiler. Đọc dòng lỗi **đầu tiên**, đừng đọc dòng cuối.

---

## 3. Chạy một chain dùng xong bỏ

`--dev` cho bạn một chain proof-of-authority riêng, có sẵn tài khoản đầy tiền, block ra tức thì.
Không sync, không peer, không cần consensus client, và xóa datadir là mất sạch. Tuần đầu tiên nên
sống ở đây.

```shell
./build/bin/geth --dev --http --http.api eth,net,web3,debug,txpool \
    --datadir /tmp/geth-dev
```

Hai thứ đáng để ý trong log: geth in ra tài khoản developer đã nạp sẵn tiền, và block chỉ được tạo
khi có transaction cần đưa vào (`--dev.period 2` thì đào đều mỗi 2 giây).

Mở terminal thứ hai:

```shell
./build/bin/geth attach /tmp/geth-dev/geth.ipc
```

```javascript
eth.blockNumber                                   // 0 — chưa có gì xảy ra
eth.accounts                                      // tài khoản dev có sẵn tiền
eth.getBalance(eth.accounts[0])                   // một số rất lớn

// gửi tiền tới địa chỉ bất kỳ rồi xem block xuất hiện
eth.sendTransaction({from: eth.accounts[0], to: "0x0000000000000000000000000000000000000042", value: web3.toWei(1, "ether")})
eth.blockNumber                                   // 1
eth.getBlock(1)                                   // block đầu tiên của bạn, đầy đủ
txpool.status                                     // transaction pending / queued
```

Bạn vừa chạy trọn con đường được mô tả trong
[tour 02 — nhập block](https://github.com/AJackTi/go-ethereum/tree/master/.tours).

!!! warning "`--http.api` không phải tùy chọn cho vui"
    HTTP server mặc định chỉ mở `net` và `web3`. Nếu `eth_blockNumber` báo "method not found" thì
    bạn quên liệt kê namespace.

---

## 4. Nói chuyện qua HTTP

Console chỉ là tiện ích; mọi client đều nói JSON-RPC thuần:

```shell
curl -s localhost:8545 -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}'
```

Cùng lời gọi đó từ Go, dùng client có sẵn trong repo:

```go
client, err := ethclient.Dial("http://localhost:8545")
n, err := client.BlockNumber(context.Background())
```

Với test thì thậm chí không cần node đang chạy — `ethclient/simulated` cho bạn một chain ngay trong
tiến trình. Xem [Test và debug](debugging.md).

---

## 5. Giờ đầu tiên với code

Làm theo thứ tự, mỗi việc 10-15 phút.

1. **Đi tour 01** (khởi động node) trong VS Code — cài `vsls-contrib.codetour`, mở panel CodeTour.
   Nó đi đúng con đường bạn vừa chạy.
2. **Đọc [bản đồ mã](architecture.md)** tới hết mục "Sáu luồng đáng biết" rồi dừng.
3. **Cố tình phá một thứ.** Thêm `log.Info("hello from insertChain")` ở đầu hàm `insertChain` trong
   `core/blockchain.go`, chạy `make geth`, chạy lại `--dev`, gửi một transaction. Nhìn thấy dòng log
   của chính mình in ra đáng giá hơn một giờ đọc nữa.
4. **Tìm bằng grep, đừng tìm bằng trí nhớ:**
   ```shell
   grep -rn "func (bc \*BlockChain) InsertChain" core/blockchain.go
   go doc ./core/vm EVM.Run
   ```

---

## 6. Đi tiếp

| Bạn muốn | Vào đây |
| --- | --- |
| Chạy node trên mạng thật | [Vận hành node](run-a-node.md) |
| Học codebase tử tế | [Lộ trình học](learning-path.md) — tám tuần, có bài tập |
| Sửa một thứ cụ thể | [Tôi muốn sửa X](start-here.md) |
| Hiểu bố cục | [Kiến trúc](architecture.md) |
| Tra một từ | [Thuật ngữ](glossary.md) |

---

## Lỗi giờ đầu, giải mã

| Bạn thấy | Nghĩa là gì |
| --- | --- |
| `Fatal: Failed to register the Ethereum service` | Thường do datadir được tạo bởi `--state.scheme` khác, hoặc bản geth không tương thích. Với chain dev thì cứ xóa datadir. |
| `the method eth_blockNumber does not exist/is not available` | Chưa truyền namespace vào `--http.api`. |
| `Post "http://localhost:8545": connection refused` | geth chưa chạy, hoặc thiếu `--http`. |
| `Fatal: Error starting protocol stack: listen tcp :30303: bind: address already in use` | Đang có geth khác chạy. Dùng `--port 30304` hoặc tắt nó đi. |
| Console mở được nhưng `eth.accounts` rỗng | Bạn không ở chế độ `--dev`; node thường không có tài khoản nào cho tới khi bạn tạo. |
| Node chạy, `eth.blockNumber` đứng ở 0, `admin.peers` rỗng | Bình thường trên mạng thật khi chưa có consensus client. Đó là [trang tiếp theo](run-a-node.md). |
