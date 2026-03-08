# AEGIS CCIP Cross-Chain Alert Test Results

## Test Date

March 6, 2026


## Transaction Details

| Field | Value |
|---|---|
| Source Chain | Base Sepolia (Chain ID: 84532) |
| Destination Chain | Arbitrum Sepolia (Chain Selector: `3478487238524512106`) |
| CCIP Router (Base Sepolia) | `0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93` |
| Sender Wallet | `0x15896e731c51ecB7BdB1447600DF126ea1d6969A` |
| Receiver (Arbitrum Sepolia) | `0x15896e731c51ecB7BdB1447600DF126ea1d6969A` |
| Transaction Hash | `0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303` |
| Confirmed Block | 38523160 |
| Gas Used | 154,611 |
| CCIP Fee Paid | 0.000062504478615902 ETH (~$0.16) |

---

## CCIP Message

| Field | Value |
|---|---|
| **Message ID** | `0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238` |
| Message Type | Data-only (no token transfer) |
| Gas Limit | 200,000 |
| Fee Token | Native ETH |

---

## Alert Payload

The cross-chain message encodes a full AEGIS threat alert:

| Field | Value |
|---|---|
| Alert Type | `AEGIS_THREAT_ALERT` |
| Monitored Protocol | `0x11887863b89F1bE23A650909135ffaCFab666803` (MockProtocol) |
| Threat Level | `4` (CRITICAL) |
| Threat ID | `0xbfb900a91113a4f29abff8c01e8b5084e0b171744e62dca7396493d4bc7de1d9` |
| Timestamp | 2026-03-06T16:30:05.000Z |
| Description | Flash loan attack detected — TVL dropped 25% in 30 seconds. AEGIS circuit breaker activated. |

## Links

| Resource | URL |
|---|---|
| CCIP Explorer | https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238 |
| Source TX (Base Sepolia) | https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303 |
| Chainlink CCIP Docs | https://docs.chain.link/ccip |

---

## How It Works

```
AEGIS Detection Cycle (every 30s)
          │
          ▼  threat = CRITICAL
  CircuitBreaker.triggerBreaker()
          │
          └──▶ emits CircuitBreakerTriggered event
                        │
                        ▼  (CRE log trigger)
              ccipAlert workflow (main.ts)
                        │
                        ▼
              CCIP Router.ccipSend()
                        │
              ┌─────────┴──────────┐
              │  Chainlink CCIP    │
              │  DON relays msg    │
              └─────────┬──────────┘
                        │
                        ▼
              AlertReceiver on destination chain
              ── emits AlertReceived event
              ── stores threat data on-chain
```

```bash
npx tsx scripts/test-ccip-alert.ts
npx tsx scripts/test-ccip-alert.ts --send
cd packages/contracts
forge script script/DeployCCIPReceiver.s.sol \
  --rpc-url https://sepolia-rollup.arbitrum.io/rpc \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast
npx tsx scripts/test-ccip-alert.ts --send --receiver=<deployed-address>
```
