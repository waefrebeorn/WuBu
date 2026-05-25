# WuBu — P2P Distributed Inference Network

**Target:** Qwen 3.6-35B A3B on Steam Deck + RTX Ada89 (6-8GB VRAM)
**Speed:** 50t/s gen (MTP speculative decode) | 400t/s read
**Distribution:** Bittorrent-style P2P seeding via RTC token incentives

A P2P inference network where constrained hardware nodes pool compute via bittorrent-style model shard distribution, incentivized by RTC tokens. Custom CUDA kernels target Ada89's tensor cores for 50t/s generation with multi-token prediction speculative decoding.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    P2P INFERENCE NETWORK              │
├────────────┬─────────────┬──────────────┬────────────┤
│  KERNELS   │    P2P      │    RTC       │   DEPLOY   │
│  bytropix  │  libtorrent │  RustChain   │  Hermes    │
├────────────┼─────────────┼──────────────┼────────────┤
│ MTP decode │ DHT overlay │ token mining │ Steam Deck │
│ quant ops  │ shard swarm │ compute proof│ Ada89      │
│ custom CUDA│ peer discov │ seeding stake│ containers │
└────────────┴─────────────┴──────────────┴────────────┘
```

## Repo Map

This repo is the **design + build plan**. Actual implementations live in:

| Component | Repo | What's there |
|-----------|------|-------------|
| **Kernels** | [bytropix](https://github.com/waefrebeorn/bytropix) | WuBu DCT/DFT/GAAD, symplectic optimizers, CUDA kernels, `THEORY/papers/` |
| **Tokens** | [RustChain](https://github.com/waefrebeorn/Rustchain) | RTC token, symplectic mining, P2P consensus |
| **Inference** | [hermes-agent](https://github.com/waefrebeorn/hermes-agent) | Model serving, tool system, multi-platform |
| **Design** | This repo (WuBu) | Walkway, architecture, build plan |

## Why This Exists

Consumer GPUs (6-8GB) can run Qwen 3.6-35B A3B at usable speeds — the 3.6B active params fit in 8GB at ~4bpw. The bottleneck is distribution and incentives:

1. **Bittorrent seeding** for model shards — no central CDN, no bandwidth bill
2. **RTC tokens** for proof of inference — seeders earn, compute earners earn
3. **Custom kernels** tuned for Ada89's tensor cores — 50t/s is aggressive but achievable with MTP speculative decode at small batch sizes

## Phases

```
Phase 1 ─ Kernel Layer     Custom CUDA quant + MTP decode kernels
Phase 2 ─ P2P Layer        Bittorrent DHT for model shard distribution
Phase 3 ─ RTC Layer        Proof-of-Seeding + Proof-of-Inference on RustChain
Phase 4 ─ Deploy Layer     Hermes containers targeting Steam Deck + Ada89
Phase 5 ─ Network          Open beta: P2P inference cluster
```

## License

MIT — same as the original WuBu repo.
