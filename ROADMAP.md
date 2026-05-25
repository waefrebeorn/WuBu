# WuBu — ROADMAP

## Phase 1: Kernel Layer (bytropix)

- [ ] INT4 group-wise quantization (4bpw, 32-group)
- [ ] Tensor core INT4 matmul (Ada89 sm_89)
- [ ] MTP speculative decode draft model (2-layer)
- [ ] MTP speculative decode verification kernel
- [ ] CUDA graphs for full inference pipeline
- [ ] **Verify:** 50t/s on Ada89 6-8GB, cos-sim >0.995 vs FP16

## Phase 2: P2P Layer

- [ ] Mainline DHT custom extension (model_manifest, node_profile)
- [ ] Shard split + merkle tree (64MB shards)
- [ ] Rarest-first download scheduler
- [ ] Prioritized seeding (under-replicated shards first)
- [ ] Inference request/response protocol
- [ ] **Verify:** 2+ nodes share shards on LAN

## Phase 3: RTC Layer (RustChain)

- [ ] Proof-of-Seeding type (RustChain enrollment/submission)
- [ ] Proof-of-Inference type with challenge-response
- [ ] Escrow account system for inference fees
- [ ] Reward distribution at block boundaries
- [ ] Validator verification logic
- [ ] **Verify:** Submit proof, see RTC in wallet

## Phase 4: Deploy Layer

- [ ] Ada89 container (CUDA 12.8, sm_89)
- [ ] Steam Deck custom kernel + ROCm/HIP build
- [ ] Auto-detection: hardware capabilities → config
- [ ] CUDA graph caching (compile once, reuse across restarts)
- [ ] **Verify:** Both targets run benchmark at target t/s

## Phase 5: Network

- [ ] 2+ seeders in swarm
- [ ] Inference routing across nodes
- [ ] RTC rewards flowing
- [ ] Graceful node disconnect/rejoin
- [ ] **Verify:** End-to-end: client → swarm → compute → response → reward
