# WuBu P2P Inference Network — State

**Date:** 2026-05-25  
**Status:** Design Phase (walkway complete, mining live, BATTLESHIP active)

## What Exists

- Walkway documents: 01-prestige through 07-verify ✅
- Architecture document: Full cross-repo design ✅
- Target hardware identified: Steam Deck + Ada89 (6-8GB) ✅
- **RustChain miner**: Running PID 41550, epoch 173, 6hr+ uptime ✅
- **C symplectic loop**: tools/symplectic_miner_loop (16584 bytes C binary) ✅
- **WSL Bridge**: Python + PowerShell entropy reader (8 source, CV=11% vs WSL <1%) ✅
- **Enhanced miner**: tools/enhanced_miner.py — orchestrator ✅
- **ETHICS.md**: White-hat disclosure policy filed ✅
- **BATTLESHIP**: 123/400 vaulted, 64 PRs, 19 jaxint-approved ✅
- **Polymarket trading**: $747M paper PnL, 73.8% WR, running on 5-min cron ✅

## What's Blocked

- Phase 1 (kernel) won't start until bytropix CUDA kernel development session spins up
- Phase 2 (P2P) can't start until INT4 matmul + MTP acceptance rate proven on target
- Phase 3 (RTC) can't start until RustChain fork integration planned
- Phase 4 (Deploy) can't start until Hermes container strategy decided
- **Miner stuck at 1e-09x weight** — WSL VM detection server-side, need bare metal for 0.8x

## Active Questions

1. MTP acceptance rate for Qwen 3.6-35B A3B — unknown, must benchmark
2. Ada89 INT4 tensor core throughput at batch=1 — unknown, must benchmark
3. RustChain block time vs inference proof intervals — need RTC config
4. Steam Deck unified memory pool performance — unknown
5. Bittorrent library choice: `mainline` (Rust) vs `libtorrent` (C++) for DHT

## Next Action

1. Continue BATTLESHIP — next T-row test gaps (T10 bridge_api, T6 beacon_x402)
2. Submit bounty claims for 19 approved PRs
3. When user signals Phase 1 start: begin CUDA kernel work in bytropix repo
