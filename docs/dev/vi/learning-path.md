# Lộ trình học: tám tuần tới pull request đầu tiên

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/learning-path.md)
> Đây là tutorial. Tra theo công việc dùng [`start-here.md`](start-here.md); bản đồ repo dùng
> [`architecture.md`](architecture.md).

Mỗi tuần có mục tiêu, phần cần đọc, phần phải *làm*, và một checkpoint bạn tự trả lời được.
Phần làm quan trọng hơn phần đọc — thứ chỉ đọc thì một tuần sau quên sạch.

---

## Tuần 1 — Chạy node và nhìn nó sống (~8h)

- **Đọc:** `README.md`, `cmd/geth/main.go`, `cmd/geth/config.go`, `node/node.go`.
- **Làm:** `make geth`; chạy `geth --sepolia --syncmode snap --http`; `geth attach` rồi gọi
  `eth.syncing`, `admin.peers`, `debug.metrics(false)`; sau đó `geth --dev --http` để có chain riêng
  tức thì.
- **Ghi lại:** danh sách lifecycle được đăng ký lúc khởi động (thêm một dòng log trong
  `node.Node.RegisterLifecycle`).
- **Checkpoint:** giải thích vì sao `--dev` không cần consensus client
  (gợi ý: `eth/catalyst/simulated_beacon.go`).

## Tuần 2 — Kiểu dữ liệu và RLP (~8h)

- **Đọc:** `core/types/block.go`, `transaction.go`, năm file `tx_*.go`, `receipt.go`,
  `rlp/encode.go`, `rlp/decode.go`.
- **Làm:** giải mã một block thật bằng `go run ./cmd/rlpdump`; viết test encode/decode khứ hồi cho
  mỗi loại transaction.
- **Ghi lại:** bảng mỗi loại tx thêm trường gì và bật ở fork nào (đối chiếu `params/config.go`).
- **Checkpoint:** tự tính hash một transaction từ byte thô và khớp với explorer.

## Tuần 3 — EVM (~10h)

- **Đọc:** `core/vm/interpreter.go` (`EVM.Run`), `jump_table.go`, `instructions.go`,
  `gas_table.go`, `contracts.go`, `evm.go` (`Call`).
- **Làm:** `go run ./cmd/evm run --debug --code 6001600101` rồi theo dõi stack; chạy một state test
  bằng `go run ./cmd/evm statetest`; trên nhánh nháp, thêm một opcode giả để thấy fork gating hoạt động.
- **Ghi lại:** chuyện gì xảy ra khi `CALL` lồng nhau — luật gas 63/64, snapshot state, giới hạn depth.
- **Checkpoint:** chỉ đúng dòng code nơi `REVERT` hoàn tác state (gợi ý: `core/state/journal.go`).

## Tuần 4 — State transition và nhập block (~10h)

- **Đọc:** `core/state_processor.go`, `core/state_transition.go`, `core/blockchain.go`
  (`insertChain`), `core/block_validator.go`, `core/state/statedb.go`.
- **Làm:** dùng `core/chain_makers.go` trong test để sinh 10 block rồi `InsertChain`; cố tình sửa
  sai một state root và đọc lỗi; chạy `debug_traceBlock` trên block vừa tạo.
- **Ghi lại:** thứ tự chính xác — system call trước thực thi, các transaction, requests sau thực thi,
  xác thực, ghi.
- **Checkpoint:** mô tả chuyện gì xảy ra khi block nhập vào có cha thuộc nhánh khác.

## Tuần 5 — Trie và lưu trữ (~10h)

- **Đọc:** `trie/trie.go`, `trie/hasher.go`, `trie/stacktrie.go`, `triedb/database.go`,
  `triedb/pathdb/difflayer.go`, `core/rawdb/schema.go`.
- **Làm:** dựng một trie nhỏ trong test và in root sau mỗi lần insert; chạy `geth db inspect` trên
  datadir thật; đọc một proof qua `trie/proof.go`.
- **Ghi lại:** sơ đồ của riêng bạn: một `SetState` thành byte trên đĩa thế nào.
- **Checkpoint:** giải thích vì sao `pathdb` rollback được còn `hashdb` thì không.

## Tuần 6 — Mạng và sync (~9h)

- **Đọc:** `p2p/server.go`, `eth/protocols/eth/handshake.go`, `handlers.go`, `eth/handler.go`,
  `eth/downloader/beaconsync.go`, `eth/protocols/snap/sync.go`.
- **Làm:** ping một bootnode bằng `go run ./cmd/devp2p`; chạy với `--verbosity 5` và đọc handshake;
  theo dõi trọn một lần snap sync trên Sepolia.
- **Ghi lại:** vì sao hai node cùng mạng vẫn có thể từ chối nhau (`core/forkid`).
- **Checkpoint:** kể thứ tự message từ lúc mở TCP tới header block đầu tiên.

## Tuần 7 — Engine API, miner, txpool (~8h)

- **Đọc:** `eth/catalyst/api.go`, `miner/payload_building.go`, `miner/worker.go`,
  `core/txpool/txpool.go`, `legacypool/legacypool.go`, `blobpool/blobpool.go`.
- **Làm:** trên `--dev`, gửi tx bằng `ethclient` và log trọn chu kỳ
  forkchoiceUpdated -> getPayload -> newPayload; soi `txpool_content` khi có nonce nhảy cóc để thấy
  hàng queued.
- **Ghi lại:** cái gì quyết định thứ tự transaction trong block.
- **Checkpoint:** giải thích vì sao gọi `getPayload` muộn hơn thì được block tốt hơn.

## Tuần 8 — Đóng góp thật (~8h)

- **Đọc:** `AGENTS.md`, `build/ci.go`, `tests/state_test.go`, và lịch sử git của package bạn quan tâm.
- **Làm:** chạy đủ `go run ./build/ci.go test` một lần để biết mất bao lâu; tìm một chỗ thiếu (test
  còn thiếu, thông báo lỗi khó hiểu) và sửa; chạy trọn checklist trước commit.
- **Ghi lại:** mô tả PR ba đoạn — vấn đề, cách làm, cách kiểm chứng.
- **Checkpoint:** `lint`, `check_generate` và full test đều sạch trước khi mở PR.

---

## Nếu chỉ có một cuối tuần

Tuần 1 (chạy được) + tuần 4 (nhập block) + đi hết `.tours/`. Bấy nhiêu đủ để đọc hiểu phần lớn PR
trong repo này.
