# Walkway 06 — Deploy Layer

**Date:** 2026-05-25

## Phase 4 Priority

Package and target specific hardware configurations. The deploy layer wraps kernels + P2P + RTC into a deployable container for each target.

## Ada89 Target (Priority 1)

**Why first:** Largest userbase, best toolchain (CUDA), highest performance potential.

### Container spec
```
FROM nvidia/cuda:12.8-devel-ubuntu24.04
COPY kernels/*.cu /opt/wubu/kernels/
COPY p2p/target/release/wubu-p2p /opt/wubu/bin/
COPY rtc/target/release/wubu-rtc /opt/wubu/bin/
COPY config.yaml /opt/wubu/
ENV NVIDIA_VISIBLE_DEVICES=all
ENV WUBU_QUANT=4bpw
ENV WUBU_BATCH=1
ENV WUBU_MTP_DEPTH=6
```

### Ada89 provisioning
- `nvidia-smi` check for compute capability 8.9+ (Ada89 = sm_89)
- VRAM check: require ≥6GB
- CUDA graph compilation on first run (cache to disk)
- Model shard directory: `~/.cache/wubu/models/`
- DHT port: 6881 (configurable)

### Performance targets
- First token: <5ms (200+ t/s)
- Decode: 50t/s (Ada89 6-8GB)
- Memory: <6.5GB peak

## Steam Deck Target (Priority 2)

**Challenge:** RDNA2 CUs, no CUDA. Need ROCm/HIP translation or Vulkan compute.

### Approach options
1. **ROCm 6.x HIP** — Translates CUDA kernels to HIP for AMD GPUs
2. **Vulkan compute** — Rewrite kernels in GLSL compute shaders
3. **Custom kernel** — Unified memory pool optimization for Steam Deck

### Custom kernel patch
The Steam Deck's 7GB shared memory (CPU+GPU) needs special handling:
- `amdgpu.unified_memory_pool=1` — Enable unified memory
- DRM scheduler tuning for compute (not gaming) workloads
- TDP locked at 15W to prevent thermal throttling
- VRAM reservation: 6GB for GPU, 1GB for system

### Performance expectations
- Quant: 4bpw (same as Ada89)
- Decode: 8-15t/s (RDNA2 limitation)
- Memory: Peak ~6GB within 7GB pool
- No MTP speculative decode (draft model overhead outweighs benefit at low t/s)

## Config File

```yaml
# ~/.config/wubu/config.yaml
model: "Qwen/Qwen3-35B-A3B"
quant: "int4"          # int4, fp8, fp16
batch_size: 1
mtp_depth: 6           # 0 = disabled
p2p:
  dht_port: 6881
  max_peers: 50
  seed_min_hours: 2
  upload_rate_kbps: 10240
rtc:
  wallet: "RTC17c0d21f04f6f65c1a85c0aeb5d4a305d57531096"
  rpc_url: "http://127.0.0.1:8545"
hardware:
  min_vram_gb: 6
  compute_capability: "8.9"  # or "auto-detect"
```

## Docker Deploy

```bash
# Build
docker build -t wubu-ada89 -f deploy/ada89_container.Dockerfile .

# Run (inference only, no P2P seeding)
docker run --gpus all -v ~/.cache/wubu:/opt/wubu/cache wubu-ada89

# Run (P2P seeder)
docker run --gpus all \
  -p 6881:6881/udp \
  -v ~/.cache/wubu:/opt/wubu/cache \
  -e WUBU_MODE=seeder \
  wubu-ada89
```
