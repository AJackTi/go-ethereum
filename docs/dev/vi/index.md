# Sổ tay lập trình viên go-ethereum

Bản đồ cho người phải **đọc và sửa** codebase này — không phải đặc tả giao thức, cũng không phải
hướng dẫn vận hành node.

Tất cả ở đây là Markdown thường nằm trong repo. Website chỉ là tiện ích; cây mã mới là nguồn sự
thật. Không cần internet, không cần AI agent để dùng bất cứ phần nào.

---

## Bắt đầu từ đâu?

<div class="grid cards" markdown>

- :material-map: **[Kiến trúc](architecture.md)**

    Bản đồ mã nguồn. Bốn lớp, điểm vào theo từng câu hỏi, mỗi package làm gì, sáu luồng quan
    trọng. Đọc cái này trước.

- :material-wrench: **[Tôi muốn sửa X](start-here.md)**

    Mục lục theo công việc: file mở đầu tiên, những chỗ khác bị chạm theo, và cách tự chứng minh
    là chạy đúng.

- :material-school: **[Lộ trình học](learning-path.md)**

    Tám tuần từ `make geth` tới pull request đầu tiên, kèm bài tập và checkpoint tự trả lời được.

- :material-file-document-multiple: **[Quyết định](../adr/index.md)**

    Vì sao sổ tay và bộ công cụ này được dựng như vậy — mỗi quyết định một hồ sơ.

</div>

---

## Tour có hướng dẫn ngay trong editor

Hai walkthrough click-through nằm sẵn trong repo tại
[`.tours/`](https://github.com/AJackTi/go-ethereum/tree/master/.tours):

| Tour | Đi qua cái gì |
| --- | --- |
| **01 · Khởi động node** | Dòng lệnh → config → `node.Node` → `eth.Ethereum` → các service chạy |
| **02 · Nhập block** | `engine_newPayload` → `InsertChain` → EVM → kiểm state root → byte trên đĩa |

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

---

## Quy tắc ngôn ngữ

Tiếng Anh là bản gốc; tiếng Việt mirror 1:1, cùng heading, cùng thứ tự. Khi hai bên lệch nhau,
tiếng Anh thắng. Code, định danh và câu lệnh không bao giờ dịch.
