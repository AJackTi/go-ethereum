# Glossary

> **Language:** English (canonical) · [Tiếng Việt](../vi/glossary.md)
> Words that block a newcomer, with the place in this repo where each one becomes concrete.
> Vietnamese is given for reading comprehension — in code and commit messages, keep the English term.

## The two clients

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **Execution layer (EL)** | tầng thực thi | Runs transactions and keeps account state. This repo. | everything here |
| **Consensus layer (CL)** | tầng đồng thuận | Chooses the canonical chain, runs validators, decides finality. A separate program. | talks in via `eth/catalyst` |
| **Engine API** | — | The private, JWT-authenticated API the CL drives the EL with. | `eth/catalyst/api.go` |
| **JWT secret** | khóa JWT | 32 bytes shared by EL and CL so nobody else can drive your node. | `<datadir>/geth/jwtsecret` |
| **Payload** | — | A candidate block passed between CL and EL. | `beacon/engine/types.go` |
| **Fork choice** | chọn nhánh | The rule deciding which branch is canonical. Post-merge the CL owns it. | `forkchoiceUpdated` |

## Chain data

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **Block** | khối | Header plus body (transactions, withdrawals). | `core/types/block.go` |
| **Header** | tiêu đề khối | The block's summary and commitments, including the state root. | `core/types/block.go` |
| **Receipt** | biên nhận | Result of one transaction: status, gas used, logs. | `core/types/receipt.go` |
| **Log / event** | nhật ký sự kiện | Data emitted by a contract, searchable by topic. | `core/types/log.go` |
| **Reorg** | tổ chức lại chuỗi | Switching the head to a different branch; some blocks stop being canonical. | `core/blockchain.go` |
| **Finality** | tính chung cuộc | The point past which a block cannot be reverted without extreme cost. | decided by the CL |
| **Genesis** | khối khởi thủy | Block 0 and the chain configuration baked into it. | `core/genesis.go` |
| **Fork** | đợt nâng cấp giao thức | A scheduled protocol change (Cancun, Prague, Osaka…). | `params/forks/forks.go` |
| **EIP** | — | Ethereum Improvement Proposal: the specification a fork implements. | `core/vm/eips.go` |

## Execution

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **EVM** | máy ảo Ethereum | The stack machine that runs contract bytecode. | `core/vm/interpreter.go` |
| **Opcode** | mã lệnh | One instruction of the EVM. | `core/vm/opcodes.go` |
| **Gas** | — | Meter for computation; also the fee unit. Not a currency. | `core/vm/gas_table.go` |
| **Base fee** | phí cơ bản | Per-block fee that is burned; adjusts with demand (EIP-1559). | `consensus/misc/eip1559` |
| **Priority fee / tip** | phí ưu tiên | Extra paid to the block proposer to be included sooner. | `miner/worker.go` |
| **Precompile** | hợp đồng dựng sẵn | A "contract" implemented natively for speed (hashes, curves). | `core/vm/contracts.go` |
| **Revert** | hoàn tác | Abort a call and undo its state changes; gas is still spent. | `core/state/journal.go` |
| **State transition** | chuyển trạng thái | Applying a block to state and producing the next state. | `core/state_processor.go` |
| **Nonce** | — | Per-account counter that orders transactions and blocks replay. | `core/types/tx_legacy.go` |
| **Blob** | — | Large data attached to a transaction, priced separately (EIP-4844). | `core/types/tx_blob.go` |

## State and storage

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **State** | trạng thái | Balances, nonces, code and storage of every account. | `core/state/statedb.go` |
| **State root** | gốc trạng thái | One hash committing to the entire state. Mismatch = invalid block. | `StateDB.Commit` |
| **Trie (MPT)** | cây Merkle Patricia | The structure that turns state into that one hash. | `trie/trie.go` |
| **Node (trie node)** | nút cây | One vertex of the trie — the unit actually stored. | `trie/node.go` |
| **hashdb / pathdb** | — | Two trie storage schemes: keyed by node hash, or by path (default, prunable, rollback-capable). | `triedb/` |
| **Pruning** | cắt tỉa | Dropping state that no longer needs to be kept. | `triedb/pathdb` |
| **Archive node** | node lưu trữ | Keeps state at every historical block. Much larger. | `--gcmode archive` |
| **Freezer / ancients** | kho lạnh | Append-only files holding old blocks, outside the KV database. | `core/rawdb/freezer.go` |
| **Snapshot** | ảnh chụp trạng thái | Flat copy of state for fast reads without walking the trie. | `core/state/snapshot/` |
| **Witness** | bằng chứng trạng thái | The minimal state proof needed to execute a block statelessly. | `core/stateless/` |

## Networking and sync

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **devp2p** | — | Ethereum's peer-to-peer stack (discovery + RLPx transport). | `p2p/` |
| **Peer** | nút ngang hàng | Another node you are connected to. | `p2p/peer.go` |
| **Bootnode** | nút khởi điểm | A well-known node used to find your first peers. | `params/bootnodes.go` |
| **enode / ENR** | — | A node's address and its signed record of capabilities. | `p2p/enode`, `p2p/enr` |
| **forkid** | — | Fork fingerprint exchanged at handshake so incompatible peers disconnect. | `core/forkid/` |
| **eth/68** | — | The wire protocol for blocks, transactions and receipts. | `eth/protocols/eth` |
| **snap** | — | Protocol for downloading state by range instead of node by node. | `eth/protocols/snap` |
| **Snap sync** | đồng bộ nhanh | Download recent state directly, then follow the chain. The default. | `--syncmode snap` |
| **Full sync** | đồng bộ đầy đủ | Re-execute every block from genesis. Slow, maximally verified. | `--syncmode full` |
| **Pivot** | điểm neo | The block whose state snap sync downloads before switching to normal execution. | `eth/downloader` |
| **Heal** | vá trạng thái | The phase repairing state that changed while it was being downloaded. | `eth/protocols/snap/sync.go` |
| **Skeleton** | khung header | The header chain filled backwards from the CL-provided head. | `eth/downloader/skeleton.go` |

## Transactions and block production

| Term | Tiếng Việt | What it means | In the code |
| --- | --- | --- | --- |
| **Transaction pool (mempool)** | bể giao dịch | Buffer of transactions not yet in a block. | `core/txpool/` |
| **Pending vs queued** | chờ xử lý / xếp hàng | Executable now vs blocked by a nonce gap. | `legacypool/` |
| **Block building** | dựng block | Assembling a payload when the CL asks for one. | `miner/payload_building.go` |
| **Proposer** | người đề xuất khối | The validator whose turn it is to publish a block. | CL side |
| **MEV** | — | Value extractable by choosing transaction order or inclusion. | `miner/worker.go` ordering |
| **Access list** | danh sách truy cập | Pre-declared addresses/slots that make gas cheaper and predictable. | `core/types/tx_access_list.go` |

## Repository vocabulary

| Term | Tiếng Việt | What it means | Where |
| --- | --- | --- | --- |
| **Lifecycle** | vòng đời dịch vụ | Anything the node starts and stops as a unit. | `node/lifecycle.go` |
| **Backend** | — | The interface an API layer needs from the node. | `internal/ethapi/backend.go` |
| **RLP** | — | Ethereum's serialization format for everything on the wire and on disk. | `rlp/` |
| **ADR** | hồ sơ quyết định | A record of one architectural decision and its reasons. | [`adr/`](../adr/index.md) |
| **CodeTour** | — | Guided click-through walkthrough stored as JSON in the repo. | `.tours/` |

---

Missing a word? It probably has a definition next to its type in `core/types/` or its interface in
the package that owns it. `go doc ./core/types` is faster than searching the internet.
