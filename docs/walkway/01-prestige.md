# Walkway 01 — Prestige

**Date:** 2026-05-25

## Why This Project Exists

Consumer inference is hitting a wall: models grow faster than VRAM. Qwen 3.6-35B A3B at 4bpw fits in 8GB but deploying it to thousands of users requires distribution infrastructure that costs money. Centralized CDNs are expensive. Centralized inference clusters are expensive.

**The bet:** A P2P inference network where participants earn tokens for seeding model shards and providing compute can bootstrap without upfront capital. The incentive alignment is:
- Users want fast, private inference on their own hardware
- Seeders want token rewards for idle bandwidth
- Compute providers want token rewards for idle GPU cycles

## What Already Exists

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

## The Namespace

- **bytropix** = kernels, optimizers, math proofs
- **RustChain** = tokens, mining, consensus
- **Hermes** = inference engine, deployment
- **WuBu** (this repo) = P2P network design, build plan, walkway

## Risk

Hardware targeting is ambitious. Steam Deck's RDNA2 CUs are not Ada tensor cores. Custom kernel for unified memory on Steam Deck requires low-level DRM work. Ada89 tensor core quant ops need careful throughput tuning.

Mitigation: start with the highest-value target (Ada89, 6-8GB) which has the largest userbase and best toolchain support. Steam Deck is Phase 4.
