# Sổ tay lập trình viên go-ethereum

Bản đồ cho người phải **đọc và sửa** codebase này — không phải đặc tả giao thức, cũng không phải
hướng dẫn vận hành node.

Tất cả ở đây là Markdown thường nằm trong repo. Website chỉ là tiện ích; cây mã mới là nguồn sự
thật. Không cần internet, không cần AI agent để dùng bất cứ phần nào.

---

## Bắt đầu từ đâu?

**Chưa từng build geth?** Bắt đầu ở [Bắt đầu từ số không](getting-started.md) — một giờ từ terminal
trắng tới một node gửi transaction được. Mọi thứ bên dưới giả định bạn đã qua bước đó.

<div class="grid cards" markdown>

- :material-rocket-launch: **[Bắt đầu từ số không](getting-started.md)**

    Chuẩn bị máy, `make geth`, một chain `--dev` dùng xong bỏ, transaction đầu tiên, và những lỗi
    ai cũng gặp trong giờ đầu.

- :material-map: **[Kiến trúc](architecture.md)**

    Bản đồ mã nguồn. Bốn lớp, điểm vào theo từng câu hỏi, mỗi package làm gì, sáu luồng quan trọng.

- :material-wrench: **[Tôi muốn sửa X](start-here.md)**

    Mục lục theo công việc: file mở đầu tiên, những chỗ khác bị chạm theo, và cách tự chứng minh
    là chạy đúng.

- :material-school: **[Lộ trình học](learning-path.md)**

    Tám tuần từ `make geth` tới pull request đầu tiên, kèm bài tập và checkpoint tự trả lời được.

- :material-server-network: **[Vận hành node](run-a-node.md)**

    Tài nguyên cần bao nhiêu, chế độ sync, ghép với consensus client, cổng, systemd, Docker, giám
    sát và bảo trì.

- :material-bug: **[Test và debug](debugging.md)**

    Triệu chứng nào dùng công cụ nào: bộ test, tracer, pprof, delve, và cách đọc một block bị từ chối.

- :material-code-braces: **[Dùng geth từ code của bạn](using-geth.md)**

    `ethclient`, binding `abigen`, một chain thật ngay trong test, subscription — xây *trên* geth
    thay vì sửa geth.

- :material-puzzle: **[Các hệ thống con còn lại](subsystems.md)**

    GraphQL, ethstats, chỉ mục log, file era, telemetry, chuyển đổi binary trie — những phần sáu
    luồng chính không đi qua.

- :material-toolbox: **[Công cụ](tools.md)**

    Mười hai binary trong `cmd/`: `evm`, `devp2p`, `abigen`, `rlpdump`, `era`, `workload` và phần
    còn lại.

- :material-translate: **[Thuật ngữ](glossary.md)**

    Mọi từ chặn chân người mới, Anh và Việt, mỗi từ trỏ tới đoạn code khiến nó thành cụ thể.

- :material-file-document-multiple: **[Quyết định](../adr/index.md)**

    Vì sao sổ tay và bộ công cụ này được dựng như vậy — mỗi quyết định một hồ sơ.

</div>

---

## Tour có hướng dẫn ngay trong editor

Bảy walkthrough click-through nằm sẵn trong repo tại
[`.tours/`](https://github.com/AJackTi/go-ethereum/tree/master/.tours):

| Tour | Đi qua cái gì |
| --- | --- |
| **01 · Khởi động node** | Dòng lệnh → config → `node.Node` → `eth.Ethereum` → các service chạy |
| **02 · Nhập block** | `engine_newPayload` → `InsertChain` → EVM → kiểm state root → byte trên đĩa |
| **03 · Vòng đời transaction** | RPC hoặc peer → txpool → gossip → miner → block → pool reset |
| **04 · Đồng bộ** | head từ CL → skeleton → fetcher song song → range snap → heal |
| **05 · Một request RPC** | transport → định tuyến → reflection → `ethapi` → backend → state lịch sử |
| **06 · Lưu trữ state** | `SSTORE` → journal → trie → tầng triedb → rawdb → pebble và freezer |
| **07 · Cài đặt một EIP** | lịch fork → `Rules` → `eips.go` → jump table → gas → spec test |

Cài extension VS Code `vsls-contrib.codetour` một lần, mở panel CodeTour, chọn tour. Sau khi cài
xong nó chạy hoàn toàn offline — không service, không model.

Mỗi bước neo bằng regex trên chữ ký hàm, không dùng số dòng, nên refactor không âm thầm trỏ tour
vào nhầm chỗ.

---

## Sổ tay này tổ chức thế nào

Bốn loại tài liệu, cố ý tách riêng ([Diátaxis](https://diataxis.fr/)):

| Loại | Trả lời | Ở đâu |
| --- | --- | --- |
| Tutorial | "Dạy tôi codebase này" | Lộ trình học, `.tours/` |
| How-to | "Tôi cần sửa X" | Tôi muốn sửa X |
| Reference | "Y nằm ở đâu?" | Kiến trúc, `go doc` |
| Explanation | "Vì sao lại dựng như vậy?" | Quyết định, mục bất biến |

Trộn chúng vào nhau là lỗi thường gặp: một tutorial kèm lý thuyết thì không giúp được ai.

---

## Dùng offline

```shell
# đọc thẳng từ checkout — không cần cài gì
$EDITOR ARCHITECTURE.md docs/dev/vi/start-here.md

# tài liệu API mọi package, không cần mạng
go doc ./core/vm
go doc ./core/vm EVM.Run

# hoặc trải nghiệm y hệt pkg.go.dev, chạy tại máy
go install golang.org/x/pkgsite/cmd/pkgsite@latest
pkgsite -http :8080
```

Muốn website này trên máy không có mạng? Build bản đóng gói rồi copy đi:

```shell
OFFLINE=true mkdocs build     # site/ mở trực tiếp bằng file://
```

Hoặc khỏi build luôn: mỗi lần CI chạy đều đính kèm đúng bản đóng gói đó dưới tên artifact
`handbook-offline`. Mở lần chạy mới nhất ở
[Actions → docs](https://github.com/AJackTi/go-ethereum/actions/workflows/docs.yml), tải về, giải
nén, mở `index.html` — đầy đủ website, có cả tìm kiếm, không cần server và không cần mạng.

---

## Quy tắc ngôn ngữ

Tiếng Anh là bản gốc; tiếng Việt mirror 1:1, cùng heading, cùng thứ tự. Khi hai bên lệch nhau,
tiếng Anh thắng. Code, định danh và câu lệnh không bao giờ dịch.
