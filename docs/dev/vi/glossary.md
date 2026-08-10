# Thuật ngữ

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/glossary.md)
> Những từ chặn chân người mới, kèm nơi trong repo này khiến chúng trở nên cụ thể.
> Phần tiếng Việt để hiểu nghĩa — trong code và commit message, giữ nguyên thuật ngữ tiếng Anh.

## Hai client

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **Execution layer (EL)** | tầng thực thi | Chạy transaction và giữ state tài khoản. Chính repo này. | toàn bộ ở đây |
| **Consensus layer (CL)** | tầng đồng thuận | Chọn chain chuẩn, chạy validator, quyết định finality. Chương trình riêng. | gọi vào qua `eth/catalyst` |
| **Engine API** | — | API riêng, xác thực JWT, để CL điều khiển EL. | `eth/catalyst/api.go` |
| **JWT secret** | khóa JWT | 32 byte dùng chung giữa EL và CL để không ai khác điều khiển được node. | `<datadir>/geth/jwtsecret` |
| **Payload** | — | Một block ứng viên truyền qua lại giữa CL và EL. | `beacon/engine/types.go` |
| **Fork choice** | chọn nhánh | Luật quyết định nhánh nào là chuẩn. Sau Merge, CL nắm quyền này. | `forkchoiceUpdated` |

## Dữ liệu chain

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **Block** | khối | Header cộng body (transaction, withdrawal). | `core/types/block.go` |
| **Header** | tiêu đề khối | Phần tóm tắt và các cam kết của block, gồm cả state root. | `core/types/block.go` |
| **Receipt** | biên nhận | Kết quả một transaction: status, gas đã dùng, log. | `core/types/receipt.go` |
| **Log / event** | nhật ký sự kiện | Dữ liệu contract phát ra, tìm được theo topic. | `core/types/log.go` |
| **Reorg** | tổ chức lại chuỗi | Chuyển head sang nhánh khác; một số block thôi là chuẩn. | `core/blockchain.go` |
| **Finality** | tính chung cuộc | Mốc mà sau đó block không thể bị đảo nếu không trả giá cực lớn. | do CL quyết |
| **Genesis** | khối khởi thủy | Block 0 và cấu hình chain gắn trong đó. | `core/genesis.go` |
| **Fork** | đợt nâng cấp giao thức | Một thay đổi giao thức theo lịch (Cancun, Prague, Osaka…). | `params/forks/forks.go` |
| **EIP** | — | Ethereum Improvement Proposal: đặc tả mà một fork cài đặt. | `core/vm/eips.go` |

## Thực thi

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **EVM** | máy ảo Ethereum | Máy stack chạy bytecode của contract. | `core/vm/interpreter.go` |
| **Opcode** | mã lệnh | Một chỉ thị của EVM. | `core/vm/opcodes.go` |
| **Gas** | — | Đồng hồ đo tính toán; cũng là đơn vị phí. Không phải tiền tệ. | `core/vm/gas_table.go` |
| **Base fee** | phí cơ bản | Phí theo block bị đốt; tự điều chỉnh theo nhu cầu (EIP-1559). | `consensus/misc/eip1559` |
| **Priority fee / tip** | phí ưu tiên | Trả thêm cho người đề xuất block để được vào sớm. | `miner/worker.go` |
| **Precompile** | hợp đồng dựng sẵn | "Contract" cài đặt native cho nhanh (hash, đường cong). | `core/vm/contracts.go` |
| **Revert** | hoàn tác | Hủy một call và undo thay đổi state; gas vẫn mất. | `core/state/journal.go` |
| **State transition** | chuyển trạng thái | Áp một block lên state để ra state kế tiếp. | `core/state_processor.go` |
| **Nonce** | — | Bộ đếm mỗi tài khoản, định thứ tự tx và chặn replay. | `core/types/tx_legacy.go` |
| **Blob** | — | Dữ liệu lớn đính kèm transaction, tính giá riêng (EIP-4844). | `core/types/tx_blob.go` |

## State và lưu trữ

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **State** | trạng thái | Số dư, nonce, code và storage của mọi tài khoản. | `core/state/statedb.go` |
| **State root** | gốc trạng thái | Một hash cam kết cho toàn bộ state. Lệch = block không hợp lệ. | `StateDB.Commit` |
| **Trie (MPT)** | cây Merkle Patricia | Cấu trúc biến state thành đúng một hash đó. | `trie/trie.go` |
| **Node (trie node)** | nút cây | Một đỉnh của trie — đơn vị thực sự được lưu. | `trie/node.go` |
| **hashdb / pathdb** | — | Hai scheme lưu trie: khóa theo hash node, hoặc theo path (mặc định, cắt tỉa và rollback được). | `triedb/` |
| **Pruning** | cắt tỉa | Bỏ đi state không cần giữ nữa. | `triedb/pathdb` |
| **Archive node** | node lưu trữ | Giữ state ở mọi block lịch sử. Nặng hơn nhiều. | `--gcmode archive` |
| **Freezer / ancients** | kho lạnh | File chỉ ghi thêm, chứa block cũ, nằm ngoài database KV. | `core/rawdb/freezer.go` |
| **Snapshot** | ảnh chụp trạng thái | Bản sao phẳng của state để đọc nhanh, không phải đi bộ trên trie. | `core/state/snapshot/` |
| **Witness** | bằng chứng trạng thái | Chứng minh state tối thiểu đủ để thực thi block kiểu stateless. | `core/stateless/` |

## Mạng và đồng bộ

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **devp2p** | — | Bộ giao thức ngang hàng của Ethereum (discovery + vận chuyển RLPx). | `p2p/` |
| **Peer** | nút ngang hàng | Một node khác mà bạn đang kết nối tới. | `p2p/peer.go` |
| **Bootnode** | nút khởi điểm | Node đã biết trước, dùng để tìm những peer đầu tiên. | `params/bootnodes.go` |
| **enode / ENR** | — | Địa chỉ của một node và bản ghi có chữ ký về năng lực của nó. | `p2p/enode`, `p2p/enr` |
| **forkid** | — | Dấu vân tay fork trao đổi lúc handshake để peer không tương thích tự ngắt. | `core/forkid/` |
| **eth/68** | — | Wire protocol cho block, transaction và receipt. | `eth/protocols/eth` |
| **snap** | — | Giao thức tải state theo range thay vì từng node một. | `eth/protocols/snap` |
| **Snap sync** | đồng bộ nhanh | Tải thẳng state gần đây rồi bám theo chain. Mặc định. | `--syncmode snap` |
| **Full sync** | đồng bộ đầy đủ | Chạy lại mọi block từ genesis. Chậm, kiểm chứng tối đa. | `--syncmode full` |
| **Pivot** | điểm neo | Block mà snap sync tải state của nó trước khi chuyển sang thực thi bình thường. | `eth/downloader` |
| **Heal** | vá trạng thái | Pha sửa lại phần state đã đổi trong lúc đang tải. | `eth/protocols/snap/sync.go` |
| **Skeleton** | khung header | Chuỗi header điền lùi dần từ head do CL cung cấp. | `eth/downloader/skeleton.go` |

## Transaction và dựng block

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Trong code |
| --- | --- | --- | --- |
| **Transaction pool (mempool)** | bể giao dịch | Bộ đệm transaction chưa vào block. | `core/txpool/` |
| **Pending vs queued** | chờ xử lý / xếp hàng | Thực thi được ngay, so với đang kẹt vì thiếu nonce. | `legacypool/` |
| **Block building** | dựng block | Ráp payload khi CL yêu cầu. | `miner/payload_building.go` |
| **Proposer** | người đề xuất khối | Validator tới lượt công bố block. | phía CL |
| **MEV** | — | Giá trị moi ra được nhờ chọn thứ tự hoặc chọn đưa tx vào. | thứ tự trong `miner/worker.go` |
| **Access list** | danh sách truy cập | Khai báo trước địa chỉ/slot để gas rẻ và dễ đoán hơn. | `core/types/tx_access_list.go` |

## Từ vựng riêng của repo

| Thuật ngữ | Nghĩa tiếng Việt | Là gì | Ở đâu |
| --- | --- | --- | --- |
| **Lifecycle** | vòng đời dịch vụ | Thứ mà node start và stop như một khối. | `node/lifecycle.go` |
| **Backend** | — | Interface mà tầng API cần node cung cấp. | `internal/ethapi/backend.go` |
| **RLP** | — | Định dạng tuần tự hóa của Ethereum, dùng cả trên dây lẫn trên đĩa. | `rlp/` |
| **ADR** | hồ sơ quyết định | Bản ghi một quyết định kiến trúc và lý do của nó. | [`adr/`](../adr/index.md) |
| **CodeTour** | — | Walkthrough click-through lưu dạng JSON trong repo. | `.tours/` |

---

Thiếu từ nào? Nó gần như chắc chắn có định nghĩa ngay cạnh kiểu dữ liệu của nó trong `core/types/`
hoặc trong interface của package sở hữu nó. `go doc ./core/types` nhanh hơn tìm trên mạng.
