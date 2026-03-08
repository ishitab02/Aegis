# AEGIS Protocol - Chainlink Integration

## Summary

AEGIS Protocol integrates 5 Chainlink services to create a trustless, verifiable security monitoring system for DeFi protocols:

| Service | Purpose | Status | Evidence |
|---------|---------|--------|----------|
| CRE | Workflow orchestration with BFT consensus | Simulation Passed | [threatDetection/main.ts](#1-cre-chainlink-runtime-environment) |
| Data Feeds | Real-time ETH/USD price verification | Live | [Price Read](#2-chainlink-data-feeds) |
| Automation | Cron-triggered detection cycles | Configured | [Cron Trigger](#3-chainlink-automation) |
| VRF v2.5 | Fair tie-breaker selection | TX Confirmed | [VRF Consumer](#4-chainlink-vrf-v25) |
| CCIP | Cross-chain alert propagation | TX Confirmed | [CCIP Alert](#5-chainlink-ccip) |

---

## Deployed Contracts (Base Sepolia)

| Contract | Address | Purpose |
|----------|---------|---------|
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | Emergency pause controller |
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` | AI sentinel registration |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` | On-chain threat reports |
| VRFConsumer | `0x51bAC1448E5beC0E78B0408473296039A207255e` | VRF v2.5 tie-breaker |
| TestVault | `0xB85d57374c18902855FA85d6C36080737Fb7509c` | Demo protected protocol |

---

## 1. CRE (Chainlink Runtime Environment)

Code Location: [`packages/cre-workflows/src/workflows/threatDetection/main.ts`](../packages/cre-workflows/src/workflows/threatDetection/main.ts)

### What It Does
CRE orchestrates the entire threat detection cycle with Byzantine Fault Tolerant (BFT) consensus:

```
Every 30 seconds:
┌─────────────────────────────────────────────────────────────┐
│  1. Read TVL from MockProtocol (EVM Read)                   │
│  2. Read ETH/USD from Chainlink Data Feed                   │
│  3. Call AI Agent API for threat detection (HTTP)           │
│  4. If CRITICAL → Trigger CircuitBreaker (EVM Write)        │
│  5. Submit ThreatReport on-chain (EVM Write)                │
└─────────────────────────────────────────────────────────────┘
```

### Key Code Snippet

```typescript
// packages/cre-workflows/src/workflows/threatDetection/main.ts:72-93

runtime.log("Step 2: Reading Chainlink ETH/USD...");
const priceCallData = encodeFunctionData({
  abi: chainlinkAggregatorAbi,
  functionName: "latestRoundData",
});
const priceResult = evmClient
  .callContract(runtime, {
    call: encodeCallMsg({
      from: zeroAddress,
      to: evm.chainlinkFeeds.ethUsd as Address,  // Data Feed address
      data: priceCallData,
    }),
  })
  .result();
const [, answer, , updatedAt] = decodeFunctionResult({
  abi: chainlinkAggregatorAbi,
  functionName: "latestRoundData",
  data: bytesToHex(priceResult.data) as `0x${string}`,
}) as [bigint, bigint, bigint, bigint, bigint];
const ethPrice = Number(answer) / 1e8;
runtime.log(`  ETH/USD: $${ethPrice.toFixed(2)}`);
```

### Simulation Output

```
[SIMULATION] Simulator Initialized
[SIMULATION] Running trigger trigger=cron-trigger@1.0.0

[USER LOG] AEGIS: Cron-triggered detection cycle starting...
[USER LOG] Step 1: Reading on-chain TVL...
[USER LOG] TVL: 0 wei
[USER LOG] Step 2: Reading Chainlink ETH/USD...
[USER LOG] ETH/USD: $1965.14
[USER LOG] Step 3: Calling AI agent detection API...
[USER LOG] Consensus: NONE (0.67) - reached: true
[USER LOG] Step 4: Threat level NONE - alert only, no circuit breaker.
[USER LOG] Step 5: Submitting ThreatReport on-chain...
[USER LOG] ThreatReport submitted! TX: 0x000...
```

---

## 2. Chainlink Data Feeds

Code Location: [`packages/cre-workflows/src/workflows/threatDetection/main.ts:72-93`](../packages/cre-workflows/src/workflows/threatDetection/main.ts)

### Configuration

| Parameter | Value |
|-----------|-------|
| Feed | ETH/USD |
| Address (Base Sepolia) | `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1` |
| Purpose | Price anomaly detection, oracle attack prevention |

### How AEGIS Uses Data Feeds

The Oracle Sentinel compares on-chain prices against Chainlink's verified ETH/USD feed to detect:
- Flash loan attacks manipulating AMM prices
- Oracle manipulation attempts
- Stale price data (potential oracle failure)

```typescript
// If price deviation > 5% from Chainlink feed → FLAG as anomaly
const deviation = Math.abs(ammPrice - chainlinkPrice) / chainlinkPrice;
if (deviation > 0.05) {
  return { threat_level: "HIGH", reason: "Price deviation from Chainlink feed" };
}
```

---

## 3. Chainlink Automation

Code Location: [`packages/cre-workflows/src/workflows/threatDetection/main.ts:243-246`](../packages/cre-workflows/src/workflows/threatDetection/main.ts)

### Configuration

```typescript
const initWorkflow = (config: Config) => {
  const cronCap = new cre.capabilities.CronCapability();

  // Production: every 30 seconds
  return [cre.handler(cronCap.trigger({ schedule: config.schedule }), onCronTrigger)];
};
```

| Parameter | Value |
|-----------|-------|
| Schedule (Testing) | `0 */1 * * * *` (every minute) |
| Schedule (Production) | `*/30 * * * * *` (every 30 seconds) |
| Purpose | Automated threat detection cycles |

---

## 4. Chainlink VRF v2.5

Code Location: [`packages/contracts/src/vrf/AegisVRFConsumer.sol`](../packages/contracts/src/vrf/AegisVRFConsumer.sol)

### Purpose
When AI sentinels have a split vote (e.g., 1 says HIGH, 1 says CRITICAL), VRF provides verifiable randomness for fair, weighted selection.

### Contract Code

```solidity
// packages/contracts/src/vrf/AegisVRFConsumer.sol:93-123

function requestTieBreaker(uint256[] calldata sentinelIds)
    external
    onlyOwner
    returns (uint256 requestId, uint256 tieBreakerId)
{
    if (sentinelIds.length < 2) revert InvalidSentinelCount();

    tieBreakerId = ++s_tieBreakCounter;

    // Request randomness using VRF v2.5
    requestId = s_vrfCoordinator.requestRandomWords(
        VRFV2PlusClient.RandomWordsRequest({
            keyHash: i_keyHash,
            subId: s_subscriptionId,
            requestConfirmations: s_requestConfirmations,
            callbackGasLimit: s_callbackGasLimit,
            numWords: 1,
            extraArgs: VRFV2PlusClient._argsToBytes(
                VRFV2PlusClient.ExtraArgsV1({nativePayment: false})
            )
        })
    );

    emit RandomnessRequested(requestId, tieBreakerId, sentinelIds);
}
```

### VRF Configuration (Base Sepolia)

| Parameter | Value |
|-----------|-------|
| VRF Coordinator | `0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE` |
| LINK Token | `0xE4aB69C077896252FAFBD49EFD26B5D171A32410` |
| Key Hash (500 gwei) | `0x9e9e46732b32662b9adc6f3abdf6c5e926a666d174a4d6b8e39c4cca76a38897` |
| Subscription ID | `11253994545520594848914204579213158096888562024819407235781468224794237415058` |

### Verified Transactions

| Action | Transaction Hash | BaseScan |
|--------|------------------|----------|
| Deploy VRFConsumer | Foundry Script | [View](https://sepolia.basescan.org/address/0x51bAC1448E5beC0E78B0408473296039A207255e) |
| Create Subscription | `0x10001a8a7bf79cf30394c325e2140c3655f64abafb76dc9f3a488aff0c4329dd` | [View](https://sepolia.basescan.org/tx/0x10001a8a7bf79cf30394c325e2140c3655f64abafb76dc9f3a488aff0c4329dd) |
| Add Consumer | `0x732ef996f6135ef905425063c7986e60e445e02dd70144fb604f8679b8f60a49` | [View](https://sepolia.basescan.org/tx/0x732ef996f6135ef905425063c7986e60e445e02dd70144fb604f8679b8f60a49) |
| Fund Subscription | `0x874d56d6b44f3f33d3451098bc468cbafec7f7473334cfdde3515afd2b5017ef` | [View](https://sepolia.basescan.org/tx/0x874d56d6b44f3f33d3451098bc468cbafec7f7473334cfdde3515afd2b5017ef) |
| Request Randomness | `0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff` | [View](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |

---

## 5. Chainlink CCIP

Code Location:
- Solidity: [`packages/contracts/src/ccip/AlertReceiver.sol`](../packages/contracts/src/ccip/AlertReceiver.sol)
- TypeScript: [`scripts/test-ccip-alert.ts`](../scripts/test-ccip-alert.ts)
- CRE Workflow: [`packages/cre-workflows/src/workflows/ccipAlert/main.ts`](../packages/cre-workflows/src/workflows/ccipAlert/main.ts)

### Purpose
When a CRITICAL threat is detected and CircuitBreaker triggers, CCIP propagates the alert cross-chain to notify protocols deployed on other networks.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CircuitBreaker.triggerBreaker() on Base Sepolia            │
│                         │                                    │
│                         ▼ emits CircuitBreakerTriggered      │
│              ┌──────────────────────┐                        │
│              │  CRE Log Trigger     │                        │
│              └──────────┬───────────┘                        │
│                         │                                    │
│                         ▼                                    │
│              ccipAlert workflow builds message               │
│                         │                                    │
│                         ▼                                    │
│              CCIP Router.ccipSend()                          │
│                         │                                    │
│              ┌──────────┴───────────┐                        │
│              │  Chainlink CCIP DON  │                        │
│              │  relays message      │                        │
│              └──────────┬───────────┘                        │
│                         │                                    │
│                         ▼                                    │
│              AlertReceiver.ccipReceive() on Arbitrum Sepolia │
│              emits AlertReceived event                       │
└─────────────────────────────────────────────────────────────┘
```

### AlertReceiver Contract

```solidity
// packages/contracts/src/ccip/AlertReceiver.sol:87-125

function ccipReceive(Any2EVMMessage calldata message) external {
    if (msg.sender != ccipRouter) revert OnlyCCIPRouter(msg.sender, ccipRouter);
    if (alerts[message.messageId].receivedAt != 0) revert AlertAlreadyProcessed(message.messageId);

    // Decode AEGIS alert payload
    (
        string memory alertType,
        address protocol,
        bytes32 threatId,
        uint8 threatLevel,
        uint256 alertTimestamp,
        string memory description
    ) = abi.decode(message.data, (string, address, bytes32, uint8, uint256, string));

    // Store alert
    alerts[message.messageId] = Alert({
        messageId: message.messageId,
        sourceChainSelector: message.sourceChainSelector,
        senderAddress: abi.decode(message.sender, (address)),
        alertType: alertType,
        protocol: protocol,
        threatId: threatId,
        threatLevel: threatLevel,
        alertTimestamp: alertTimestamp,
        description: description,
        receivedAt: block.timestamp
    });

    emit AlertReceived(
        message.messageId, message.sourceChainSelector, senderAddress,
        alertType, protocol, threatLevel, description
    );
}
```

### Verified CCIP Transaction

| Field | Value |
|-------|-------|
| Source Chain | Base Sepolia (Chain ID: 84532) |
| Destination Chain | Arbitrum Sepolia (Selector: `3478487238524512106`) |
| CCIP Router (Base Sepolia) | `0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93` |
| Transaction Hash | `0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303` |
| CCIP Message ID | `0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238` |
| Gas Used | 154,611 |
| CCIP Fee Paid | 0.000062504478615902 ETH (~$0.16) |

### Links

| Resource | URL |
|----------|-----|
| CCIP Explorer | https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238 |
| Source TX (Base Sepolia) | https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303 |

### Alert Payload Sent

```json
{
  "alertType": "AEGIS_THREAT_ALERT",
  "protocol": "0x11887863b89F1bE23A650909135ffaCFab666803",
  "threatLevel": 4,
  "threatId": "0xbfb900a91113a4f29abff8c01e8b5084e0b171744e62dca7396493d4bc7de1d9",
  "timestamp": "2026-03-06T16:30:05.000Z",
  "description": "Flash loan attack detected — TVL dropped 25% in 30 seconds. AEGIS circuit breaker activated."
}
```

---

## CRE Workflows Summary

```
packages/cre-workflows/
├── project.yaml              # CRE project settings (RPCs, DON)
├── secrets.yaml              # Secret mappings (AGENT_API_URL)
└── src/workflows/
    ├── threatDetection/      # Main detection workflow (CRE + Data Feeds + Automation)
    │   ├── main.ts           # Cron: TVL + price → detect → circuit breaker
    │   ├── config.json       # Contract addresses + thresholds
    │   └── workflow.yaml
    ├── ccipAlert/            # Cross-chain alerting (CRE + CCIP)
    │   ├── main.ts           # Log trigger → CCIP message to dest chain
    │   └── workflow.yaml
    ├── vrfTieBreaker/        # VRF-based tie-breaking (CRE + VRF)
    │   ├── main.ts           # VRF randomness for weighted selection
    │   └── workflow.yaml
    ├── forensicAnalysis/     # Forensic analysis workflow
    │   ├── main.ts           # Log trigger: analyze exploits
    │   └── workflow.yaml
    └── healthCheck/          # System health workflow
        ├── main.ts           # 5min cron: API + sentinel liveness
        └── workflow.yaml
```

---

## How to Run

### Local Simulation

```bash
# Prerequisites
cd packages/cre-workflows
pnpm install

# Start Python Agent API (required for HTTP calls)
cd ../agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000

# Run CRE simulation (in another terminal)
cd packages/cre-workflows
cre workflow simulate src/workflows/threatDetection -T local-simulation --non-interactive --trigger-index 0
```

### Test CCIP Manually

```bash
# Dry run (fee estimate only)
npx tsx scripts/test-ccip-alert.ts

# Send real CCIP message
npx tsx scripts/test-ccip-alert.ts --send
```

### Full Demo

```bash
bash scripts/run-demo.sh
# Opens dashboard at http://localhost:5173/demo
```

---

## Why CRE Is Central

AEGIS uses CRE as the central orchestration layer because:

1. Verifiable Execution: All detection runs through CRE's BFT consensus
2. Trustless On-Chain Actions: Circuit breaker triggers are consensus-verified
3. Signed Reports: ThreatReports are signed by the DON
4. Multi-Capability Workflow: Combines HTTP, EVM Read, EVM Write, Data Feeds in one atomic execution
