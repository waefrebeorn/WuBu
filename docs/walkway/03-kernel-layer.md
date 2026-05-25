# Walkway 03 — Kernel Layer

**Date:** 2026-05-25

## Phase 1 Priority

Build the custom CUDA kernels against Ada89's tensor cores. This is the riskiest component — need to prove 50t/s is achievable before building the P2P layer.

## Quantized Matmul: INT4 Tensor Core

Ada89 supports INT4 tensor core operations with 1:2 throughput ratio vs FP16 (2 INT4 ops per cycle vs 1 FP16). Strategy:

```cuda
// Input: fp16, Weights: int4, Output: fp16
// Tensor core does: D = A * B + C
// A = fp16 activation, B = int4 weight (packed 2-per-i32)
// Accumulate in fp16, dequant on the fly

// Per 32-weight group: scale = fp16, zero = int4
// Actual weight = (packed_int4 - zero) * scale
```

**Files:** `src/kernels/quant_4bpw.cu`, `src/kernels/tensor_core_sgemm.cu`

### Implementation plan:
1. Write naive INT4 matmul (no tensor cores, reference)
2. Verify against FP16 reference (cosine similarity >0.999)
3. Add tensor core path using `nvcuda::wmma` for m16n16k16
4. Optimize: bank conflict free shared memory layout
5. Benchmark: measure t/s at batch=1,2,4

## MTP Speculative Decode

Multi-token prediction from the Qwen 3 paper. The draft module shares the model's hidden states.

### Architecture:
- Base model: Qwen 3.6-35B A3B (30 layers, MoE)
- Draft: 2-layer transformer (shared embeddings, 8 attention heads)
- Draft parameters: ~200M (0.6% of full model)
- Draft cost: ~0.5ms per forward pass
- MTP depth: 6 future tokens predicted in parallel (6 independent draft heads)

### Implementation plan:
1. Extract draft modules from Qwen 3 architecture (shared embedding + head)
2. Write draft forward kernel (shared memory, low batch size)
3. Write batched verification kernel (full model forward on draft sequence)
4. Implement acceptance logic (greedy: first position where argmax differs)
5. Benchmark acceptance rate on ShareGPT dataset samples

## Quantization Flow

1. Load Qwen 3.6-35B A3B in FP16 (~70GB)
2. Quantize weights to 4bpw: group-wise with 32-group size
3. Store: FP16 scales + INT4 packed weights
4. Load on Ada89: ~1.8GB active weights + ~2GB KV cache + ~1.4GB activations
5. Inference: dequantize on-the-fly during tensor core matmul

**bytropix references:**
- `THEORY/math_viz/symplectic_optimizer.md` — quantization-aware training applications
- `.hermes/vault/optimizers/Q_PID_controller.md` — PID control for quant noise management
