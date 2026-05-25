# Walkway 05 — RTC Layer

**Date:** 2026-05-25

## Phase 3 Priority

Wire RustChain tokens into the P2P network as incentive layer. RustChain already has symplectic mining, RTC token, and a working validator set.

## Proof-of-Seeding

A node proves it seeded a shard during blocks [N, N+k] by submitting:

```
proof = H(shard_id || start_block || end_block || node_pubkey || nonce)
```

The RustChain validator set challenges by:
1. Requesting the shard from the claimed node
2. Verifying the hash matches the model manifest
3. Checking the node was reachable during the claimed blocks (requires DHT liveness tracking)

### Implementation
- Extend RustChain's existing proof system (`src/proof/`)
- Add `enrollment` type: `SeedShard(manifest_hash, shard_index)`
- Add `submission` type: `SeedProof(complete_proof)`
- Validator verifies via DHT query + hash check

## Proof-of-Inference

A node proves it ran a forward pass for a client. The trust model is optimistic with challenge:

1. Client sends `InferenceRequest` with a commitment `H(input || timestamp)`
2. Node runs inference, returns output + commitment `H(input_hash || output_hash || layers_used || timestamp)`
3. Both commitments posted to RustChain as pending proofs
4. If unchallenged for N blocks, proof is accepted and node earns RTC
5. If challenged, node must reveal random layer subset activations for verification

### Challenge cost
- Challenger must stake RTC tokens (10× the inference reward)
- If challenge succeeds (node cheated), challenger gets node's stake
- If challenge fails (node honest), challenger loses stake

## Reward Distribution

Rewards are distributed at the end of each RustChain block by the validator set:

```rust
fn distribute_rewards(block: Block, pending_proofs: Vec<Proof>) {
    for proof in pending_proofs {
        match proof.proof_type {
            ProofType::Seeding => {
                let reward = SEED_REWARD_PER_SHARD * proof.duration_blocks;
                transfer_rtc(proof.node, reward);
            }
            ProofType::Inference => {
                let reward = INFERENCE_REWARD;
                transfer_rtc(proof.node, reward);
            }
        }
    }
}
```

### Escrow accounts
- Client pays inference fee into an RTC escrow account
- Released to compute node on challenge window expiry
- If node is caught cheating, escrow refunded to client + penalty to client

## Files

`src/rtc/proof_of_seeding.rs` — Seeding proof creation + submission  
`src/rtc/proof_of_inference.rs` — Compute proof creation + submission  
`src/rtc/reward_distributor.rs` — RTC transfer logic  
`src/rtc/validator_client.rs` — RustChain client integration  

## RustChain Fork Changes

The RustChain fork at `~/rustchain/` needs:

1. **New proof types:** Add `SeedShard` and `ComputeInference` to enrollment/submission enums
2. **Validator logic:** Add challenge-response verification for inference proofs
3. **Escrow system:** Hold inference fees during challenge window
4. **Tokenomics config:** Reward rates for seeding vs inference

See `~/rustchain/src/proof/` for the existing proof system.
