# Walkway 07 — Verify

**Date:** 2026-05-25

## How to Prove This Works

Each phase has concrete verification criteria. No claim counts until measured.

## Phase 1: Kernel Layer

```
Criteria                          | Target               | Verification Method
----------------------------------|----------------------|--------------------
INT4 matmul precision             | cos-sim >0.995 vs FP16 | Compare output distributions on 1000 random inputs
INT4 matmul speed                 | >200 t/s at batch=1   | nvcc benchmark, report t/s
MTP acceptance rate               | >50%                  | Run on ShareGPT 500-samples dataset
MTP effective speedup             | >2.5×                  | Compare t/s with/without MTP at batch=1
Peak VRAM usage                   | <7GB                  | nvidia-smi peak during 4K context generation
```

## Phase 2: P2P Layer

```
Criteria                          | Target               | Verification Method
----------------------------------|----------------------|--------------------
DHT peer discovery                | 2+ peers found       | Run 2 nodes on same network, log peer count
Shard download                    | Complete 1 shard     | Download shard, verify merkle hash
Shard seeding                     | Seed for 5 minutes   | Start second node, verify it gets shard from first node
Inference request/response        | Correct output       | End-to-end: client → compute node → output matches local
```

## Phase 3: RTC Layer

```
Criteria                          | Target               | Verification Method
----------------------------------|----------------------|--------------------
Seeding proof submission          | Accepted by validator| Submit proof, check RustChain block for inclusion
Inference proof submission        | Accepted by validator| Same as above
Challenge-response                | Honest node wins     | Simulate challenge, verify honest node keeps stake
Escrow release                    | Released after window| Check RTC balance change after challenge window expiry
```

## Phase 4: Deploy Layer

```
Criteria                          | Target               | Verification Method
----------------------------------|----------------------|--------------------
Ada89 container builds            | Docker build passes  | `docker build -t wubu-ada89 .`
Ada89 decoder runs                | 50t/s generate       | `docker run --gpus all wubu-ada89 --benchmark`
Steam Deck container builds       | Docker build passes  | `DOCKER_DEFAULT_PLATFORM=linux/arm64 docker build ...`
Steam Deck decoder runs           | 8t/s generate        | Same
Memory stays under limit          | <6.5GB Ada89, <6GB SD| nvidia-smi / radeontop during sustained inference
```

## Phase 5: Network

```
Criteria                          | Target               | Verification Method
----------------------------------|----------------------|--------------------
2+ nodes form a P2P swarm         | All nodes see peers  | P2P status endpoint
All shards reachable across swarm | 100% shard coverage  | Each node reports shard inventory
Inference request routed to node  | Correct output       | Client request → swarm → compute node → response
RTC rewarded for seeding          | Balance increases    | Check RTC wallet after seeding period
RTC rewarded for compute          | Balance increases    | Check RTC wallet after inference
Network survives node disconnects | Re-shards on rejoin  | Drop node, rejoin, verify shard integrity
```

## Benchmark Script

```bash
#!/bin/bash
# Quick verification suite

echo "=== WuBu Verification Suite ==="
echo "Phase 1: Kernel"
./bench_kernels --output phase1_results.json
python3 verify_phase1.py phase1_results.json

echo "Phase 2: P2P"
./p2p_test --nodes 2 --duration 120
python3 verify_phase2.py p2p_test_log.json

echo "Phase 3: RTC"
./rtc_test --submit-seed-proof --submit-inference-proof
python3 verify_phase3.py rtc_test_log.json

echo "Phase 4: Deploy"
docker build -t wubu-test -f deploy/ada89_container.Dockerfile .
docker run --gpus all wubu-test --benchmark
echo "=== Done ==="
```
