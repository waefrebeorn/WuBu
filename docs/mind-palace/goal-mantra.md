# WuBu P2P Inference Network — Goal & Mantra

**P0:** A P2P inference network where consumer GPUs pool compute via bittorrent + RTC tokens.

Qwen 3.6-35B A3B at 4bpw on Steam Deck + Ada89 (6-8GB). 50t/s gen via MTP speculative decode. 400t/s read.
P2P shard distribution via bittorrent DHT. Incentives via RustChain RTC tokens (proof-of-seeding, proof-of-inference).

## Phases

```
Phase 1 ─ Kernel Layer     Custom CUDA quant + MTP decode in bytropix
Phase 2 ─ P2P Layer        Mainline DHT + libtorrent shard distribution
Phase 3 ─ RTC Layer        Proof-of-Seeding + Proof-of-Inference on RustChain
Phase 4 ─ Deploy Layer     Hermes containers → Steam Deck + Ada89 targets
Phase 5 ─ Network          Open beta: >2 nodes in P2P inference cluster
```

## Cross-Repo Architecture

| Repo | Role | What WuBu needs from it |
|------|------|------------------------|
| **bytropix** | Kernels | INT4 tensor core matmul, MTP speculative decode, quant ops |
| **RustChain** | Tokens | Proof-of-Seeding, Proof-of-Inference, escrow, reward distribution |
| **Hermes** | Inference | Model serving, container build, multi-platform deployment |
| **WuBu** (this) | Design + Build Plan | Walkway, architecture, nothing to ship |

## Status

Kernel layer: 🔲 Not started (design complete in walkway 03)
P2P layer:    🔲 Not started (design complete in walkway 04)
RTC layer:    🔲 Not started (design complete in walkway 05)
Deploy layer: 🔲 Not started (design complete in walkway 06)
Network:      🔲 Not started

## Hard Rules

- No centralized infrastructure — pure P2P or nothing
- Every speed claim verified on target hardware (not simulated)
- No delegation for kernel development (bytropix work done in Hermes sessions)
- All code MIT licensed
- Phase 1 must pass all verification criteria before Phase 2 starts
