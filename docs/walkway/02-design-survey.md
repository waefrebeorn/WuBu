# Walkway 02 — Design Survey

**Date:** 2026-05-25

## Model Selection

**Qwen 3.6-35B A3B** — The key spec is 3.6B active params out of 35B total (MoE). At 4bpw:
- Active weights: ~1.8GB
- KV cache (4K context): ~2GB
- Activations + overhead: ~1.4GB
- **Total: ~5.2GB** — fits in 6-8GB with headroom

Alternative candidates:
- DeepSeek V3 (671B MoE, 37B active) — too large for 8GB even at 2bpw
- Llama 4 Maverick (128B MoE, 16B active) — possible at 3bpw but tight
- Qwen 3.6-35B A3B is the sweet spot for 6-8GB VRAM

## Speed Target: 50t/s

50t/s generation with 400t/s read on Ada89. Read speed = first token latency. At 400t/s, first token arrives in ~2.5ms. At 50t/s decode, each subsequent token takes ~20ms.

**How to get there:**
1. **Quantization:** 4bpw weight compression (group-wise, 32-group)
2. **Tensor cores:** INT4 tensor core matmul on Ada89 (1:2 INT4:FP16)
3. **MTP speculative decode:** 6-token draft + verify in one batch
4. **CUDA graphs:** Static launch graph for all layers
5. **Shared memory:** KV cache in shared memory where possible

**MTP acceptance rate target: 3.3×**
- Higher rates require larger draft models → slower draft
- Lower rates harm speedup
- 3.3× = ~6 accepted tokens out of 10 drafted (60% acceptance rate)
- At 15t/s base × 3.3 = 50t/s effective

## Bittorrent Distribution Analysis

Standard bittorrent is designed for immutable files. Model shards are immutable (checkpoint snapshots). Key adaptations:

| Standard BT | Our design |
|------------|-----------|
| Magnet link → metadata → file | Manifest (signed JSON) → shard merkle tree → download |
| Leech/seeder roles | Every node is a seeder for shards it holds |
| Tit-for-tat bandwidth | Token-based incentives override TFT |
| Tracker or DHT | DHT only (no tracker) |
| Piece priority: sequential | Piece priority: rarest-first |

**Shard size: 64MB**
- 35B model at 4bpw = ~17.5GB → ~273 shards
- At 50MB/s download (typical home internet), full model in ~6 minutes
- At 10MB/s upload, seeding all shards for 1 hour = 36GB transferred = seeding proof

## RTC Token Economics

| Action | RTC Reward | Frequency |
|--------|-----------|-----------|
| Seed 1 shard for 1 block | 0.1 RTC | Per block (~5min) |
| Complete inference for client | 0.5 RTC | Per inference |
| Refer a new compute node | 10 RTC | One-time |
| Validate proofs (validator) | 0.05 RTC | Per block |

At $0 RTC price (early stage), rewards are bootstrapping tokens. Value accrues as network grows.

## Related Work

| Project | Similarity | Difference |
|---------|-----------|------------|
| Petals (HuggingFace) | P2P inference | Uses centralized coordinator, no token incentives |
| Bittensor (TAO) | Token-incentivized AI | General subnet, not specific to edge inference |
| Together AI | Distributed inference | Centralized, paid API |
| ExLlamaV2 | Quant + inference engine | Single-node only, no P2P distribution |
