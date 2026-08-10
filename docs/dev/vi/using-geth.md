# Dùng geth từ code của bạn

> **Ngôn ngữ:** Tiếng Việt · [English (bản gốc)](../en/using-geth.md)
> Nhóm đối tượng còn lại: bạn không sửa geth, bạn xây trên nó. Mọi thứ ở đây đều nằm sẵn trong repo
> này — không cần SDK bên thứ ba.

## Import package nào?

| Bạn muốn | Package |
| --- | --- |
| Nói chuyện với node qua RPC | `ethclient` |
| Dùng phần RPC riêng của geth | `ethclient/gethclient` |
| Chạy một chain ngay trong test | `ethclient/simulated` |
| Gọi contract bằng method Go có kiểu | `accounts/abi/bind` + `cmd/abigen` |
| Encode/decode ABI thủ công | `accounts/abi` |
| Làm việc với address, hash, hex | `common`, `common/hexutil` |
| Dựng hoặc parse transaction | `core/types` |
| Ký, băm, sinh khóa | `crypto` |

```shell
go get github.com/ethereum/go-ethereum
```

---

## 1. Đọc chain

```go
client, err := ethclient.Dial("http://localhost:8545")
if err != nil { log.Fatal(err) }
defer client.Close()

ctx := context.Background()
head, err := client.HeaderByNumber(ctx, nil)          // nil = latest
bal, err := client.BalanceAt(ctx, addr, nil)          // nil = latest
nonce, err := client.PendingNonceAt(ctx, addr)
code, err := client.CodeAt(ctx, contract, nil)
```

`nil` nghĩa là *latest* ở mọi chỗ block number là tùy chọn. Truyền block cũ vào một node có pruning
sẽ buộc node chạy lại state — xem [tour 05](https://github.com/AJackTi/go-ethereum/tree/master/.tours);
hãy chờ đợi nó chậm hoặc lỗi hẳn.

---

## 2. Gửi transaction

```go
chainID, _ := client.ChainID(ctx)
nonce, _ := client.PendingNonceAt(ctx, from)
tip, _ := client.SuggestGasTipCap(ctx)
head, _ := client.HeaderByNumber(ctx, nil)

tx := types.NewTx(&types.DynamicFeeTx{
    ChainID:   chainID,
    Nonce:     nonce,
    GasTipCap: tip,
    GasFeeCap: new(big.Int).Add(tip, new(big.Int).Mul(head.BaseFee, big.NewInt(2))),
    Gas:       21000,
    To:        &to,
    Value:     big.NewInt(1e18),
})

signed, err := types.SignTx(tx, types.LatestSignerForChainID(chainID), privKey)
err = client.SendTransaction(ctx, signed)
```

Ba chỗ hay sai:

- **`GasFeeCap` phải chịu được base fee tăng.** Base fee có thể tăng 12,5% mỗi block; đặt trần đúng
  bằng giá trị hiện tại thì transaction mắc kẹt.
- **`SendTransaction` trả về nil nghĩa là *đã vào pool*,** không phải đã lên block. Chờ receipt bằng
  `bind.WaitMined` hoặc poll `TransactionReceipt`.
- **Nonce là việc của bạn.** Hai transaction dựng từ cùng một `PendingNonceAt` sát nhau sẽ đụng
  nhau; nếu gửi liên tục thì tự giữ bộ đếm.

---

## 3. Binding contract có kiểu bằng abigen

```shell
make all                                   # build ./build/bin/abigen
solc --abi --bin Token.sol -o build/

./build/bin/abigen \
  --abi build/Token.abi \
  --bin build/Token.bin \
  --pkg token \
  --type Token \
  --out token/token.go
```

```go
tok, err := token.NewToken(contractAddr, client)
supply, err := tok.TotalSupply(&bind.CallOpts{Context: ctx})   // đọc: không tốn gas

auth, err := bind.NewKeyedTransactorWithChainID(privKey, chainID)
tx, err := tok.Transfer(auth, to, amount)                      // ghi: ký và gửi
receipt, err := bind.WaitMined(ctx, client, tx)
```

`CallOpts` là đọc (`eth_call`, miễn phí, không đổi state). `TransactOpts` ký và phát đi. Lẫn lộn hai
cái này là lỗi phổ biến nhất khi dùng binding.

Sinh lại binding mỗi khi contract đổi và commit file sinh ra — đúng quy ước geth dùng cho các file
`gen_*.go` của chính nó.

---

## 4. Một chain thật ngay trong test

Không cổng, không datadir, không docker — một execution node đầy đủ trong binary test:

```go
func TestTransfer(t *testing.T) {
    key, _ := crypto.GenerateKey()
    addr := crypto.PubkeyToAddress(key.PublicKey)

    backend := simulated.NewBackend(types.GenesisAlloc{
        addr: {Balance: big.NewInt(9e18)},
    })
    defer backend.Close()

    client := backend.Client()          // cùng interface với ethclient
    // ... dựng, ký và gửi transaction ...
    backend.Commit()                    // đào block theo yêu cầu

    receipt, err := client.TransactionReceipt(context.Background(), tx.Hash())
    if err != nil || receipt.Status != types.ReceiptStatusSuccessful {
        t.Fatalf("transfer failed: %v", err)
    }
}
```

`backend.Commit()` chính là điểm mấu chốt: block xuất hiện đúng lúc bạn nói, khiến test tất định
theo cách một testnet thật không bao giờ làm được.

---

## 5. Subscription

Subscription cần WebSocket hoặc IPC — HTTP thuần không đẩy dữ liệu được:

```go
client, _ := ethclient.Dial("ws://localhost:8546")

heads := make(chan *types.Header)
sub, err := client.SubscribeNewHead(ctx, heads)

logs := make(chan types.Log)
sub2, err := client.SubscribeFilterLogs(ctx, ethereum.FilterQuery{
    Addresses: []common.Address{contract},
}, logs)

for {
    select {
    case err := <-sub.Err():   // luôn xử lý: kết nối sẽ rớt
        return err
    case h := <-heads:
        fmt.Println("new head", h.Number)
    }
}
```

Đừng bao giờ bỏ qua `sub.Err()`. WebSocket rớt thì im lặng, chương trình của bạn đơn giản là ngừng
nhận sự kiện trong khi vẫn trông có vẻ khỏe mạnh.

---

## 6. Phần riêng của geth

`ethclient` bám API chuẩn. Thứ gì chỉ geth mới có thì nằm ở `gethclient`:

```go
gc := gethclient.New(rpcClient)
proof, err := gc.GetProof(ctx, account, keys, blockNum)      // eth_getProof
al, gas, vmErr, err := gc.CreateAccessList(ctx, msg)         // eth_createAccessList
err = gc.SetHead(ctx, big.NewInt(1000))                      // debug_setHead — chỉ khi dev
```

Với thứ hoàn toàn không có wrapper, dùng thẳng RPC client thô:

```go
rpcClient, _ := rpc.Dial("http://localhost:8545")
var result json.RawMessage
err := rpcClient.CallContext(ctx, &result, "debug_traceTransaction", txHash, map[string]any{
    "tracer": "callTracer",
})
```

---

## 7. Chạy trên một node dùng xong bỏ

Để thử nghiệm thủ công, `--dev` ăn đứt testnet công khai: block tức thì, tài khoản có sẵn tiền,
không phải sync.

```shell
geth --dev --http --http.api eth,net,web3,debug,txpool --ws --datadir /tmp/geth-dev
```

Chi tiết và các lỗi giờ đầu nằm ở [Bắt đầu từ số không](getting-started.md); còn node phải sống sót
qua reboot thì xem [Vận hành node](run-a-node.md).

---

## Liên quan

- [Công cụ](tools.md) — `abigen`, `abidump`, `rlpdump` và phần còn lại của `cmd/`.
- [Test và debug](debugging.md) — tracer và profiling khi lời gọi của bạn cư xử lạ.
- `go doc ./ethclient` — danh sách method đầy đủ, offline.
