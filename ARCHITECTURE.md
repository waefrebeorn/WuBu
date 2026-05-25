# WuBu Architecture — P2P Distributed Inference Network

## Overview

A distributed inference network where consumer-grade GPUs (6-8GB VRAM) collectively serve Qwen 3.6-35B A3B via bittorrent-style shard distribution. Participants earn RTC tokens for seeding model shards and providing inference compute.

## Target Hardware

| Device | VRAM | Compute | Quant Target | Est. Gen |
|--------|------|---------|-------------|----------|
| Steam Deck (custom kernel) | ~7GB shared | 8 RDNA2 CUs | ~4bpw | 8-15 t/s |
| RTX 4050-4070 Ada89 | 6-8GB GDDR6 | Ada tensor cores | ~4bpw | 30-50 t/s |
| RTX 4080-4090 Ada89 | 12-24GB | Full tensor | ~3.5bpw | 50-80 t/s |

## Kernel Layer (bytropix)

### Multi-Token Prediction (MTP) Speculative Decode

Vanilla autoregressive decode is bandwidth-bound — at 4bpw you get ~20t/s on Ada89. MTP speculative decoding predicts N future tokens in parallel and verifies them in one forward pass, achieving effective 2-3× speedup.

**Design:**
- Draft model: lightweight 2-layer predictor (200M params) — uses the same hidden states
- Verify: full model forward pass on the draft sequence
- Accept: number of accepted tokens = first mismatch position
- Target: 50t/s effective = ~15t/s base × 3.3× MTP acceptance rate

**Files:** `src/kernels/`
- `mtp_draft.cu` — Draft predictor kernel (shared memory optimized)
- `mtp_verify.cu` — Batched verification kernel
- `quant_4bpw.cu` — Group-wise 4-bit quantization ops
- `tensor_core_sgemm.cu` — Ada tensor core matmul for small batch sizes (1-4)

### Quantization Strategy

Qwen 3.6-35B A3 at 4bpw = 35B × 0.5 bytes = ~17.5GB → too large for 8GB.
But A3B MoE means only 3.6B active params per token forward pass:
- 3.6B × 0.5 bytes = ~1.8GB active weights
- ~4GB total with KV cache + activations
- **Fits in 6-8GB at 4bpw**

The router + shared embeddings stay in VRAM. Only the active experts per token need to be loaded.

## P2P Layer

### Model Shard Distribution

Each model checkpoint is split into fixed-size shards (64MB). Shards are distributed via a DHT overlay (libtorrent/Mainline DHT). Nodes maintain a shard inventory and seed shards they hold.

**Key design decisions:**
- **No central tracker** — pure DHT with magnet links
- **Shard verification** — each shard has a signed merkle root from the model publisher
- **Rarest-first seeding** — nodes prioritize seeding shards with the fewest peers
- **Locality-aware** — nodes prefer shards from geographically close peers (latency <50ms)

**Protocol:**
1. Node joins DHT with its hardware capability fingerprint
2. Node requests model manifest (signed JSON with shard merkle tree)
3. Node downloads shards in rarest-first order, verifying each against merkle root
4. Once complete, node switches to seeding mode

## RTC Layer (RustChain)

### Proof-of-Seeding

A node proves it seeded a shard for N consecutive blocks by submitting a hash of (shard_id + block_height + node_pubkey) to the RustChain network. The RustChain validator set verifies:

1. The node was reachable for queries during those blocks
2. The shard hash matches the model manifest
3. No double-claim on the same shard-block range

Reward: RTC tokens per shard per block-seeded

### Proof-of-Inference

A client submits a signed inference request to a node. The node performs the forward pass and returns:
- The output tokens
- A commitment hash over (input_hash, output_hash, requested_layers, timestamp)
- The merkle proof showing which expert shards were used

The commitment is submitted to RustChain as a proof-of-compute. If challenged, the node must reveal the actual activations (which can be verified by recomputing a random layer subset).

Reward: RTC tokens per verified inference

## Deploy Layer

### Steam Deck Target

- Custom kernel with unified memory pool optimization
- ROCm/HIP translation layer for RDNA2 CUs
- Power-constrained: target 15W TDP for sustained inference
- Cooling: active fan profile tuned for GPU compute (not gaming)

### Ada89 Target

- Target TensorRT-LLM or custom CUDA kernels
- CUDA graphs for minimal launch overhead
- FP16 accumulation, 4-bit weights
- Batch size 1-4 (inference, not training)

## Network Topology

```
                    ┌─────────────┐
                    │  DHT Root   │
                    │ (no tracker)│
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
    ┌────▼────┐      ┌────▼────┐       ┌─────▼─────┐
    │Steam Deck│      │Ada89#1  │       │ Ada89#2   │
    │ (seeder) │      │ (seeder)│       │ (compute) │
    └──────────┘      └─────────┘       └───────────┘
         │                 │                  │
         │           ┌─────▼──────┐           │
         │           │ Inference  │           │
         │           │ Request    │           │
         │           │ via Socket │           │
         │           └────────────┘           │
         │                                    │
    ┌────▼────────────────────────────────────▼────┐
    │            RustChain Validator Set            │
    │       (tracks proofs + distributes RTC)       │
    └───────────────────────────────────────────────┘
```

## Speed Budget

| Operation | Budget | Notes |
|-----------|--------|-------|
| Weight load (3.6B @ 4bpw) | ~1.8ms | 800MB/s PCIe 4.0 x16 |
| Tensor core matmul | ~0.3ms per layer | Ada89 INT4 tensor core |
| MTP draft (2-layer) | ~0.5ms | Shared-memory optimized |
| MTP verify (6 tokens) | ~1.8ms | Batched |
| **Total per token** | **~4.4ms** | ~227t/s base, ~50t/s effective with 4.5× MTP |
| **Memory budget** | **~5.2GB** | 1.8GB weights + 2GB KV cache + 1.4GB activations |

*Note: These are rough budget estimates. Actual numbers depend on kernel optimization quality and Ada89 tensor core utilization.*

## Files

```
src/
├── kernels/
│   ├── mtp_draft.cu
│   ├── mtp_verify.cu
│   ├── quant_4bpw.cu
│   └── tensor_core_sgemm.cu
├── p2p/
│   ├── dht.rs                 — Mainline DHT overlay
│   ├── shard_swarm.rs         — Bittorrent swarm management
│   ├── shard_verify.rs        — Merkle tree verification
│   └── peer_discovery.rs      — Hardware fingerprint + location
├── rtc/
│   ├── proof_of_seeding.rs    — Seeding proof submission
│   ├── proof_of_inference.rs  — Compute proof submission
│   ├── reward_distributor.rs  — RTC token distribution
│   └── validator_client.rs    — RustChain client
└── deploy/
    ├── steamdeck_build.sh
    ├── steamdeck_kernel.patch
    ├── ada89_container.Dockerfile
    └── entrypoint.sh
```
