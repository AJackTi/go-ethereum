# Using geth from your own code

> **Language:** English (canonical) · [Tiếng Việt](../vi/using-geth.md)
> The other audience: you are not changing geth, you are building on it. Everything here ships in
> this repository — no third-party SDK.

## Which package do I import?

| You want to | Package |
| --- | --- |
| Talk to a node over RPC | `ethclient` |
| Use geth-specific RPC extras | `ethclient/gethclient` |
| Run a chain inside your tests | `ethclient/simulated` |
| Call a contract with typed Go methods | `accounts/abi/bind` + `cmd/abigen` |
| Encode/decode ABI by hand | `accounts/abi` |
| Work with addresses, hashes, hex | `common`, `common/hexutil` |
| Build or parse transactions | `core/types` |
| Sign, hash, derive keys | `crypto` |

```shell
go get github.com/ethereum/go-ethereum
```

---

## 1. Reading the chain

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

`nil` means *latest* everywhere a block number is optional. Passing an old block number against a
pruning node makes the node replay state — see [tour 05](https://github.com/AJackTi/go-ethereum/tree/master/.tours);
expect it to be slow or to fail outright.

---

## 2. Sending a transaction

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

Three things people get wrong:

- **`GasFeeCap` must cover a rising base fee.** The base fee can grow 12.5% per block; a cap equal
  to the current one gets your transaction stranded.
- **`SendTransaction` returning nil means *accepted into the pool*,** not mined. Wait for a receipt
  with `bind.WaitMined` or poll `TransactionReceipt`.
- **Nonces are yours to manage.** Two transactions built from the same `PendingNonceAt` in quick
  succession collide; keep a counter if you send in bursts.

---

## 3. Typed contract bindings with abigen

```shell
make all                                   # builds ./build/bin/abigen
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
supply, err := tok.TotalSupply(&bind.CallOpts{Context: ctx})   // read: no gas

auth, err := bind.NewKeyedTransactorWithChainID(privKey, chainID)
tx, err := tok.Transfer(auth, to, amount)                      // write: signs and sends
receipt, err := bind.WaitMined(ctx, client, tx)
```

`CallOpts` is a read (`eth_call`, free, no state change). `TransactOpts` signs and broadcasts.
Getting the two mixed up is the most common binding mistake.

Regenerate bindings whenever the contract changes and commit the generated file — that is the same
convention geth uses for its own `gen_*.go` files.

---

## 4. A real chain inside your tests

No ports, no datadir, no docker — a full execution node in your test binary:

```go
func TestTransfer(t *testing.T) {
    key, _ := crypto.GenerateKey()
    addr := crypto.PubkeyToAddress(key.PublicKey)

    backend := simulated.NewBackend(types.GenesisAlloc{
        addr: {Balance: big.NewInt(9e18)},
    })
    defer backend.Close()

    client := backend.Client()          // implements the same interface as ethclient
    // ... build, sign and send a transaction ...
    backend.Commit()                    // mine a block on demand

    receipt, err := client.TransactionReceipt(context.Background(), tx.Hash())
    if err != nil || receipt.Status != types.ReceiptStatusSuccessful {
        t.Fatalf("transfer failed: %v", err)
    }
}
```

`backend.Commit()` is the point: blocks appear exactly when you say so, which makes tests
deterministic in a way a live testnet never is.

---

## 5. Subscriptions

Subscriptions need WebSocket or IPC — plain HTTP cannot push:

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
    case err := <-sub.Err():   // always handle this: connections drop
        return err
    case h := <-heads:
        fmt.Println("new head", h.Number)
    }
}
```

Never ignore `sub.Err()`. A dropped WebSocket is silent otherwise, and your program simply stops
receiving events while looking healthy.

---

## 6. geth-specific extras

`ethclient` sticks to the standard API. Anything geth-only lives in `gethclient`:

```go
gc := gethclient.New(rpcClient)
proof, err := gc.GetProof(ctx, account, keys, blockNum)      // eth_getProof
al, gas, vmErr, err := gc.CreateAccessList(ctx, msg)         // eth_createAccessList
err = gc.SetHead(ctx, big.NewInt(1000))                      // debug_setHead — dev only
```

For anything with no wrapper at all, drop to the raw RPC client:

```go
rpcClient, _ := rpc.Dial("http://localhost:8545")
var result json.RawMessage
err := rpcClient.CallContext(ctx, &result, "debug_traceTransaction", txHash, map[string]any{
    "tracer": "callTracer",
})
```

---

## 7. Running against a throwaway node

For manual experiments, `--dev` beats a public testnet: instant blocks, a funded account, no sync.

```shell
geth --dev --http --http.api eth,net,web3,debug,txpool --ws --datadir /tmp/geth-dev
```

Details and the first-hour errors are in [Getting started](getting-started.md); for a node that
must survive a reboot, see [Run a node](run-a-node.md).

---

## Related

- [Tools](tools.md) — `abigen`, `abidump`, `rlpdump` and the rest of `cmd/`.
- [Testing and debugging](debugging.md) — tracers and profiling when your calls misbehave.
- `go doc ./ethclient` — the full method list, offline.
