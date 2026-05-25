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

## Status (2026-05-25)

**RustChain mining:** ✅ Miner running 6hr+ on WSL (1e-09x VM weight). C symplectic loop built. WSL Bridge with 8-source Windows entropy reader built. Enhanced miner orchestrator tested.

**BATTLESHIP progress:** 123/400 cells vaulted. 64 PRs submitted. Waves 7-8 complete (F20-F44 Form fixes + T7-T9 test coverage). 19 PRs jaxint-approved.

**Polymarket trading:** $747M paper PnL, 73.8% WR (2569W/910L), 4 assets (BTC/ETH/SOL/XRP), running on 5-min cron.

**Walkway:** 01-prestige through 07-verify complete. All design docs written.

| Component | Status | Location |
|-----------|--------|----------|
| Custom CUDA kernels (bytropix) | ✅ Mature | `THEORY/math_viz/`, `.hermes/vault/optimizers/` |
| RTC token + mining | ✅ Live | RustChain fork at `~/rustchain/` |
| RustChain P2P consensus | ✅ Live | RustChain validator set |
| Model engines (Hermes) | ✅ Live | Hermes serving infra |
| Inference tests on Ada-class | 🔲 Not started | — |
| MTP speculative decode | 🔲 Not started | — |
| Bittorrent DHT for shards | 🔲 Not started | — |
| RTC proof-of-seeding | 🔲 Not started | — |
| RTC proof-of-inference | 🔲 Not started | — |

## Hard Rules

- No centralized infrastructure — pure P2P or nothing
- Every speed claim verified on target hardware (not simulated)
- No delegation for kernel development (bytropix work done in Hermes sessions)
- All code MIT licensed
- Phase 1 must pass all verification criteria before Phase 2 starts
- White-hat only — ETHICS.md filed at ~/rustchain/ETHICS.md
- Zero delegation — delegate_task banned for all purposes
