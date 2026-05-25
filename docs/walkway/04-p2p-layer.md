# Walkway 04 — P2P Layer

**Date:** 2026-05-25

## Phase 2 Priority

Build the P2P distribution layer once kernels are proven. This layer is less risky (well-known bittorrent/DHT techniques) but requires careful integration with the RTC incentive layer.

## DHT Overlay

Use Mainline DHT (Kademlia) with a custom extension for ML model distribution. The standard Mainline DHT handles peer discovery; we add:

### Custom DHT Records
- `model_manifest` — Signed JSON with model name, shard count, merkle root, hardware requirements
- `node_profile` — Hardware fingerprint (GPU model, VRAM, compute capability) + geohash
- `shard_inventory` — Which shards this node currently holds

### Peer Discovery Flow
1. Node hashes model name → DHT key
2. DHT returns nodes storing `model_manifest` for that key
3. Node fetches manifest, validates signature
4. Manifest contains merkle root for shard verification
5. Node queries DHT for peers with specific shard inventory

## Shard Swarm Management

### Download Strategy
- **Rarest-first:** Request shards from peers reporting fewest copy counts
- **Parallelism:** Download up to 4 shards simultaneously from different peers
- **Verification:** Each shard verified against merkle root on completion
- **Prioritization:** First 5 shards downloaded sequentially (need at least one running)

### Seeding Strategy
- **Minimum seed time:** Seed each shard for at least 2 hours after download
- **Priority seeding:** Shards with <3 peers get priority upload bandwidth
- **Rate limiting:** Don't saturate upload for token rewards (see RTC layer)

## Protocol Buffer Messages

```protobuf
message ShardRequest {
    bytes shard_hash = 1;
    uint64 shard_index = 2;
    bytes node_pubkey = 3;
    uint64 timestamp = 4;
    bytes signature = 5;  // Signed by node
}

message ShardResponse {
    bytes shard_hash = 1;
    bytes shard_data = 2;      // Max 64MB
    bytes merkle_proof = 3;    // Proof this shard belongs to manifest tree
    uint64 timestamp = 4;
    bytes signature = 5;       // Signed by respondent
}

message InferenceRequest {
    uint32 model_version = 1;
    bytes input_tokens = 2;
    uint32 max_new_tokens = 3;
    float temperature = 4;
    bytes client_pubkey = 5;
    bytes commitment = 6;      // Hash(input || timestamp)
    uint64 timestamp = 7;
}
```

## Files

`src/p2p/dht.rs` — Mainline DHT custom extension  
`src/p2p/shard_swarm.rs` — Download/seeding management  
`src/p2p/shard_verify.rs` — Merkle tree verification  
`src/p2p/peer_discovery.rs` — Node capability + location discovery  

## Implementation Plan

1. Fork an existing Mainline DHT library (e.g., `mainline` crate in Rust)
2. Add custom DHT record types (`model_manifest`, `node_profile`, `shard_inventory`)
3. Implement shard download with rarest-first scheduling
4. Implement shard verification against merkle root
5. Implement seeding with priority for under-replicated shards
6. Wire up inference request/response protocol
7. Integration test: 2+ nodes sharing shards on LAN
