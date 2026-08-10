# Vận hành node

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/run-a-node.md)
> Triển khai geth trên mạng thật: cần bao nhiêu tài nguyên, mở cổng nào, ghép với cái gì, và hỏng
> ở đâu. Mọi giá trị mặc định ở đây lấy từ `node/defaults.go`, `cmd/utils/flags.go` và
> `eth/ethconfig/config.go`.

## 1. Chốt bốn thứ trước

| Quyết định | Flag | Lựa chọn | Cứ chọn cái này nếu chưa rõ |
| --- | --- | --- | --- |
| Mạng | `--mainnet` / `--sepolia` / `--holesky` / `--hoodi` | — | `--sepolia` khi đang học |
| Chế độ sync | `--syncmode` | `snap`, `full` | `snap` (mặc định) |
| Scheme lưu state | `--state.scheme` | `path`, `hash` | `path` — tự cắt tỉa khi chạy |
| Lịch sử giữ lại | `--gcmode`, `--history.chain` | `full`/`archive`, `all`/`postmerge`/`postprague` | `full` — archive nặng gấp nhiều lần |

Ước lượng đĩa: node testnet vài chục GB; mainnet với `snap` + `path` là vài trăm GB và còn tăng.
Archive là một cấp độ khác hẳn. Đặt datadir trên **SSD hoặc NVMe** — tải là đọc ngẫu nhiên, ổ đĩa
quay sẽ không bao giờ đuổi kịp.

RAM: `--cache` mặc định 4096 MB. Máy chạy mainnet nên có tối thiểu 16 GB.

---

## 2. Bạn cần thêm một consensus client

geth chạy một mình sẽ đứng ở block 0 dù đã có peer: không ai nói cho nó biết chain nào là chuẩn.
Ghép với một trong Prysm, Lighthouse, Teku, Nimbus, Lodestar — dự án riêng, không nằm trong repo này.

Chúng nói chuyện qua **Engine API** ở `localhost:8551`, xác thực bằng một JWT secret 32 byte dùng
chung. geth tự ghi ra `<datadir>/geth/jwtsecret` ở lần chạy đầu nếu bạn không cung cấp
(`node/node.go`, hàm `ObtainJWTSecret`), và cả hai chương trình phải đọc cùng một file.

```
   consensus client  ──engine_forkchoiceUpdated / newPayload──▶  geth :8551 (JWT)
        ▲                                                              │
        │  beacon p2p :9000                                            │  eth p2p :30303
        ▼                                                              ▼
   mạng beacon                                                 mạng execution
```

---

## 3. Câu lệnh thật, giải thích từng flag

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

- `--http.api` — **bắt buộc nếu muốn dùng được gì đó**; HTTP mặc định chỉ phục vụ `net,web3`.
  Tuyệt đối không đưa `admin`, `personal`, `debug` ra interface công khai.
- `--authrpc.*` — Engine API. Ở đó chỉ phục vụ `eth` và `engine`, và mặc định chỉ cho localhost.
  Cổng này dành cho consensus client của bạn, không cho ai khác.
- `--maxpeers` — mặc định 50. Giảm để tiết kiệm băng thông, nhưng đừng dưới ~25 kẻo sync ì ạch.
- `--verbosity` — 3 là info, 4 debug, 5 trace. Mức 5 rất ồn; chỉ bật từng đợt ngắn.

Sau đó chạy consensus client trỏ vào `http://localhost:8551` với đúng file JWT đó.

---

## 4. Cổng và tường lửa

| Cổng | Giao thức | Ai kết nối | Mức mở |
| --- | --- | --- | --- |
| 30303 | TCP **và** UDP | các node Ethereum khác | **mở ra internet** |
| 8551 | TCP | consensus client của bạn | chỉ localhost |
| 8545 / 8546 | TCP | ứng dụng của bạn | localhost, hoặc sau proxy có xác thực |
| 6060 | TCP | bạn | chỉ localhost — metrics và pprof |

Nếu 30303 bị chặn, node vẫn sync được nhưng chậm, chỉ dùng kết nối đi ra — không nhận được peer đi
vào. Mọi cổng còn lại phải đóng.

!!! danger "Mở 8545 ra internet là dâng tài sản"
    Một cổng RPC truy cập được từ internet cho phép người lạ rút sạch tài khoản đang unlock, spam
    truy vấn tốn kém, và đọc dữ liệu `admin`. Bind vào `127.0.0.1`, đừng để key trên node, và nếu
    thật sự cần truy cập từ xa thì đặt reverse proxy có xác thực phía trước.

---

## 5. Chạy như một service

`geth` là tiến trình foreground thuần — cố ý không có chế độ daemon. Để init system giám sát nó.
Repo không kèm unit file; đây là bản tối thiểu chạy được:

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
TimeoutStopSec=600          # geth cần thời gian flush state khi tắt — đừng rút ngắn
LimitNOFILE=65536           # peer cộng file database vượt xa giới hạn mặc định
StateDirectory=geth

[Install]
WantedBy=multi-user.target
```

```shell
sudo systemctl daemon-reload && sudo systemctl enable --now geth
journalctl -fu geth
```

!!! warning "Đừng bao giờ `kill -9` một node đang sync"
    Giết cứng giữa lúc đang flush state có thể để lại database phải sửa chữa rất lâu ở lần khởi
    động sau. Dùng `systemctl stop` rồi chờ; `TimeoutStopSec` sinh ra để làm việc đó.

### Docker

Repo tự build image ([`Dockerfile`](https://github.com/AJackTi/go-ethereum/blob/master/Dockerfile),
expose 8545, 8546, 30303/tcp và 30303/udp):

```shell
docker build -t geth .
docker run -d --name geth \
  -p 30303:30303 -p 30303:30303/udp \
  -p 127.0.0.1:8545:8545 \
  -v /var/lib/geth:/root/.ethereum \
  geth --sepolia --http --http.addr 0.0.0.0 --http.api eth,net,web3
```

`--http.addr 0.0.0.0` bên trong container an toàn **chỉ vì** ánh xạ cổng phía host ghim vào
`127.0.0.1:8545`. Làm ngược lại là bạn vừa công khai RPC ra internet.

---

## 6. Node có khỏe không?

```shell
geth attach /var/lib/geth/geth.ipc
```

```javascript
eth.syncing            // false = đã đồng bộ; ngược lại so currentBlock với highestBlock
eth.blockNumber        // phải tăng mỗi ~12s khi đã đồng bộ
admin.peers.length     // bằng 0 quá vài phút là có vấn đề mạng
admin.nodeInfo.protocols.eth
txpool.status
```

Thông lượng và số liệu nội bộ lấy từ endpoint metrics, không phải từ console:

```shell
curl -s localhost:6060/debug/metrics/prometheus | grep '^chain_'   # head, inserts, execution
curl -s localhost:6060/debug/metrics | head                        # cùng dữ liệu, dạng expvar JSON
```

!!! note "`--metrics` một mình không mở cổng nào"
    `--metrics` chỉ bật việc thu thập. Muốn *truy cập* được thì cần thêm `--pprof` (metrics được
    phục vụ trên chính server pprof, mặc định `127.0.0.1:6060`) hoặc `--metrics.addr` (server
    metrics riêng). Cho Prometheus và Grafana trỏ vào endpoint đó; `/debug/pprof` trên cùng cổng chỉ
    dùng khi đang điều tra.

Đọc log: `Imported new potential chain segment` nghĩa là đang bám chain. `Syncing: chain download in
progress` kèm phần trăm tăng dần là bình thường lúc đầu. Lặp lại `Post-merge network, but no beacon
client seen` nghĩa là consensus client không nói chuyện với bạn.

---

## 7. Bảo trì

```shell
geth db inspect --datadir /var/lib/geth        # đĩa đi đâu, theo từng loại dữ liệu
geth db stats  --datadir /var/lib/geth
geth removedb  --datadir /var/lib/geth         # xóa dữ liệu chain, giữ lại keystore
```

Giữ đĩa trong tầm kiểm soát (đều thuộc `state.scheme=path`):

- `--history.state 90000` — số block giữ state history; `0` là giữ tất cả.
- `--history.transactions` — chỉ mục transaction; `0` là index toàn chain.
- `--history.chain postmerge` — bỏ hẳn body và receipt trước Merge.
- `geth prune-history` — áp dụng cắt lịch sử chain lên datadir đang có.

**Nâng cấp:** dừng service, thay binary, chạy lại. Đọc release notes trước — đổi `state.scheme` hay
đổi định dạng database là phải resync, và hạ cấp thì không được hỗ trợ.

**Sao lưu:** dữ liệu chain là dữ liệu công khai, luôn resync lại được. Thứ duy nhất không thay thế
được là `<datadir>/keystore` (và file JWT, cái này sinh lại dễ). Đừng bao giờ copy thư mục database
đang chạy — dừng node trước, nếu không bạn copy phải state dở dang.

---

## 8. Khi hỏng

| Triệu chứng | Nguyên nhân và cách xử lý |
| --- | --- |
| `eth.blockNumber` đứng ở 0 dù có peer | Chưa có consensus client, hoặc JWT sai/lệch nhau. Kiểm tra cả hai log xem có `engine_forkchoiceUpdated` không. |
| `admin.peers.length` bằng 0 | 30303 bị chặn, hoặc lệch `forkid` (sai flag mạng). Kiểm tra `--bootnodes` và tường lửa. |
| `Failed to register the Ethereum service` | Datadir được ghi bởi `--state.scheme` khác hoặc geth mới hơn. Resync hoặc chỉnh cho khớp. |
| Phần trăm sync bò rất chậm ở đoạn cuối | Bình thường với snap sync: pha heal đang vá phần state đã thay đổi trong lúc tải. |
| Đầy đĩa | `geth db inspect`, rồi dùng các flag history ở trên; chế độ archive thì cắt tỉa không cứu được. |
| Node tắt mất mấy phút | Đang flush state. Cứ để nó xong. |
| RPC timeout khi tải nặng | `--cache` quá thấp, đĩa quá chậm, hoặc một truy vấn `eth_getLogs` khoảng quá rộng. Xem endpoint metrics. |

---

## Liên quan

- [Bắt đầu từ số không](getting-started.md) — build và chạy `--dev` trước đã.
- [Test và debug](debugging.md) — pprof, tracer và cách đọc báo cáo bad block.
- [Kiến trúc](architecture.md) — mỗi flag thực chất đang cấu hình cái gì.
