# Based on gpt-fast: https://github.com/pytorch-labs/gpt-fast/blob/095b2229ee3a40e379c11f05b94bd6923db63b4b/model.py
import torch
import torch.nn as nn
from torch.nn import functional as F

from ..config import BackboneConfig, InferenceParams # Adjusted for relative import


def precompute_freqs_cis(seq_len: int, n_elem: int, base: float = 10000) -> torch.Tensor:
    freqs = 1.0 / (base ** (torch.arange(0, n_elem, 2)[: (n_elem // 2)].float() / n_elem))
    t = torch.arange(seq_len, device=freqs.device)
    freqs = torch.outer(t, freqs)
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)
    cache = torch.stack([freqs_cis.real, freqs_cis.imag], dim=-1)
    return cache


def apply_rotary_emb(x: torch.Tensor, freqs_cis: torch.Tensor) -> torch.Tensor:
    xshaped = x.float().reshape(*x.shape[:-1], -1, 2)
    freqs_cis = freqs_cis.view(-1, xshaped.size(1), 1, xshaped.size(3), 2)
    x_out2 = torch.stack(
        [
            xshaped[..., 0] * freqs_cis[..., 0] - xshaped[..., 1] * freqs_cis[..., 1],
            xshaped[..., 1] * freqs_cis[..., 0] + xshaped[..., 0] * freqs_cis[..., 1],
        ],
        -1,
    )

    x_out2 = x_out2.flatten(3)
    return x_out2.type_as(x)


def _update_kv_cache(
    k: torch.Tensor, v: torch.Tensor, inference_params: InferenceParams, layer_idx: int
) -> torch.Tensor:
    """k/v: (batch_size, seqlen, nheads, head_dim) or (batch_size, 1, nheads, head_dim)"""
    assert layer_idx in inference_params.key_value_memory_dict
    kv_cache, _ = inference_params.key_value_memory_dict[layer_idx]
    # Adjust key and value for inference
    batch_start = inference_params.batch_size_offset
    batch_end = batch_start + k.shape[0]
    sequence_start = inference_params.seqlen_offset
    sequence_end = sequence_start + k.shape[1]
    assert batch_end <= kv_cache.shape[0]
    assert sequence_end <= kv_cache.shape[1]
    assert kv_cache is not None
    kv_cache[batch_start:batch_end, sequence_start:sequence_end, 0, ...] = k
    kv_cache[batch_start:batch_end, sequence_start:sequence_end, 1, ...] = v
    return kv_cache[batch_start:batch_end, :sequence_end, ...]


class TorchZonosBackbone(nn.Module):
    supported_architectures = ["transformer"]
    freqs_cis: torch.Tensor

    def __init__(self, config: BackboneConfig):
        assert not config.ssm_cfg, "This backbone implementation only supports the Transformer model."
        super().__init__()
        self.config = config

        self.layers = nn.ModuleList(TransformerBlock(config, i) for i in range(config.n_layer))
        self.norm_f = nn.LayerNorm(config.d_model, eps=config.norm_epsilon)

    def allocate_inference_cache(self, batch_size: int, max_seqlen: int, dtype: torch.dtype = torch.bfloat16):
        head_dim = self.config.d_model // self.config.attn_cfg["num_heads"]

        module_device = self.norm_f.weight.device

        # Compute freqs_cis on CPU then move to target device if not already there or on correct device
        if not hasattr(self, 'freqs_cis') or self.freqs_cis.device != module_device or self.freqs_cis.shape[0] < 16384:
            cpu_freqs_cis = precompute_freqs_cis(16384, head_dim)
            self.freqs_cis = cpu_freqs_cis.to(module_device)

        return {
            # Pass module_device to sub-layer cache allocation
            i: layer.allocate_inference_cache(batch_size, max_seqlen, dtype=dtype, device=module_device)
            for i, layer in enumerate(self.layers)
        }

    def forward(self, hidden_states: torch.Tensor, inference_params: InferenceParams) -> torch.Tensor:
        current_device = hidden_states.device
        current_seq_len = hidden_states.shape[1]
        start_pos = inference_params.seqlen_offset
        if not hasattr(self, 'freqs_cis'):
            # This should not happen if allocate_inference_cache was called
            raise RuntimeError("freqs_cis not initialized. Call allocate_inference_cache first.")

        # RoPE positions are relative to the start of the sequence segment
        # Ensure positions are created on the same device as self.freqs_cis for indexing
        positions = torch.arange(start_pos, start_pos + current_seq_len, device=self.freqs_cis.device)

        # Slice self.freqs_cis to get frequencies for the current range of positions
        # freqs_cis_for_layer will have shape [current_seq_len, num_rope_features, 2]
        freqs_cis_for_layer = self.freqs_cis[positions]

        # Ensure freqs_cis_for_layer is on the same device as hidden_states
        # (self.freqs_cis should already be on current_device via allocate_inference_cache logic)
        freqs_cis_for_layer = freqs_cis_for_layer.to(current_device)

        for i, layer in enumerate(self.layers):
            hidden_states = layer(hidden_states, inference_params, freqs_cis_for_layer)
        return self.norm_f(hidden_states)


class TransformerBlock(nn.Module):
    def __init__(self, config: BackboneConfig, layer_idx: int) -> None:
        super().__init__()
        self.config = config

        self.norm = nn.LayerNorm(config.d_model, eps=config.norm_epsilon)
        self.mixer = Attention(config, layer_idx)
        self.norm2 = nn.LayerNorm(config.d_model, eps=config.norm_epsilon)
        self.mlp = FeedForward(config)

        self.num_heads_kv = config.attn_cfg["num_heads_kv"]
        self.head_dim = config.d_model // config.attn_cfg["num_heads"]

    def allocate_inference_cache(self, batch_size: int, max_seqlen: int, dtype: torch.dtype = torch.bfloat16, device: torch.device = None): # Add device param
        return torch.empty(batch_size, max_seqlen, 2, self.num_heads_kv, self.head_dim, dtype=dtype, device=device), None # Use device

    def forward(self, x: torch.Tensor, inference_params: InferenceParams, freqs_cis: torch.Tensor) -> torch.Tensor:
        x = x + self.mixer(self.norm(x), inference_params, freqs_cis)
        x = x + self.mlp(self.norm2(x))
        return x


class Attention(nn.Module):
    def __init__(self, config: BackboneConfig, layer_idx: int):
        super().__init__()
        self.num_heads = config.attn_cfg["num_heads"]
        self.num_heads_kv = config.attn_cfg["num_heads_kv"]
        self.head_dim = config.d_model // self.num_heads
        self.layer_idx = layer_idx

        total_head_dim = (self.num_heads + 2 * self.num_heads_kv) * self.head_dim
        self.in_proj = nn.Linear(config.d_model, total_head_dim, bias=False)
        self.out_proj = nn.Linear(self.num_heads * self.head_dim, config.d_model, bias=False)

    def forward(self, x: torch.Tensor, inference_params: InferenceParams, freqs_cis: torch.Tensor) -> torch.Tensor:
        batch_size, seqlen, _ = x.shape

        q_size = self.num_heads * self.head_dim
        kv_size = self.num_heads_kv * self.head_dim
        q, k, v = self.in_proj(x).split([q_size, kv_size, kv_size], dim=-1)

        q = q.view(batch_size, seqlen, self.num_heads, self.head_dim)
        k = k.view(batch_size, seqlen, self.num_heads_kv, self.head_dim)
        v = v.view(batch_size, seqlen, self.num_heads_kv, self.head_dim)

        q = apply_rotary_emb(q, freqs_cis)
        k = apply_rotary_emb(k, freqs_cis)

        kv = _update_kv_cache(k, v, inference_params, self.layer_idx)
        k_retrieved, v_retrieved = kv.unbind(dim=-3)

        # GQA: Repeat K and V heads if num_heads_kv < num_heads
        if self.num_heads_kv < self.num_heads:
            if self.num_heads % self.num_heads_kv != 0:
                raise ValueError(f"num_heads ({self.num_heads}) must be divisible by num_heads_kv ({self.num_heads_kv}) for GQA.")
            repeats = self.num_heads // self.num_heads_kv
            k_retrieved = torch.repeat_interleave(k_retrieved, repeats, dim=2) # dim 2 is head dim before transpose
            v_retrieved = torch.repeat_interleave(v_retrieved, repeats, dim=2)

        # Ensure q matches k/v dtype.
        # If model is bfloat16, q, k_retrieved are already bfloat16. If model is float32, they are float32.
        # This cast handles potential inconsistencies or if q was float() from RoPE.
        q = q.to(k_retrieved.dtype)

        q_final, k_final, v_final = map(lambda x: x.transpose(1, 2), (q, k_retrieved, v_retrieved))

        # Remove enable_gqa=True as it's not supported / needed in PyTorch 2.7.1
        y = F.scaled_dot_product_attention(q_final, k_final, v_final, is_causal=seqlen > 1)

        y = y.transpose(1, 2).contiguous().view(batch_size, seqlen, q_size)

        # Cast y to out_proj.weight.dtype before projection.
        # If model is .to(bfloat16), out_proj.weight is bfloat16. SDPA output y (from bfloat16 inputs) is bfloat16.
        # This ensures consistency if dtypes somehow diverge or if model is float32.
        y = self.out_proj(y.to(self.out_proj.weight.dtype))
        return y


class FeedForward(nn.Module):
    def __init__(self, config: BackboneConfig) -> None:
        super().__init__()
        self.fc1 = nn.Linear(config.d_model, 2 * config.attn_mlp_d_intermediate, bias=False)
        self.fc2 = nn.Linear(config.attn_mlp_d_intermediate, config.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y, gate = self.fc1(x).chunk(2, dim=-1)
        return self.fc2(y * F.silu(gate))

