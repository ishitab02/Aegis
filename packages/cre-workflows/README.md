# AEGIS CRE Workflows

> Chainlink Runtime Environment (CRE) workflows for the AEGIS Protocol — autonomous threat detection, forensic analysis, cross-chain alerting, and VRF tie-breaking.

## Workflows

| Workflow | Trigger | Description | Chainlink Services |
|----------|---------|-------------|--------------------|
| **Threat Detection** | Cron (every 60s) | Reads protocol TVL + ETH/USD price, calls AI agents, triggers CircuitBreaker on CRITICAL consensus | CRE, Data Feeds, Automation |
| **Forensic Analysis** | Log (`CircuitBreakerTriggered`) | Calls ChainSherlock for attack classification, stores report on-chain | CRE |
| **Health Check** | Cron (every 5 min) | Verifies agent API, sentinel liveness, and data feed freshness | CRE, Data Feeds |
| **CCIP Alert** | Log (`CircuitBreakerTriggered`) | Propagates threat alerts cross-chain via CCIP | CRE, CCIP |
| **VRF Tie-Breaker** | Cron (keep-alive) | Resolves split sentinel votes using verifiable randomness | CRE, VRF |

## Chainlink Services Used (5 total = +4 bonus)

1. **CRE** — Workflow orchestration with BFT consensus verification
2. **Data Feeds** — ETH/USD price verification for oracle sentinel (Base Sepolia: `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1`)
3. **Automation** — Cron-triggered detection cycles (every 60 seconds)
4. **VRF** — Fair tie-breaker selection when sentinels disagree (Coordinator: `0xd691f04bc0c9a24Edb78af9E005Cf85768F694C9`)
5. **CCIP** — Cross-chain alert propagation (Router: `0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93`)

## Prerequisites

```bash
# Install CRE CLI
curl -sSL https://cre.chain.link/install.sh | bash

# Install dependencies
cd packages/cre-workflows
pnpm install
```

## Project Structure

```
cre-workflows/
├── project.yaml                # Global settings (RPCs, DON)
├── secrets.yaml                # Secret mappings
├── src/
│   ├── types/
│   │   ├── index.ts            # Config schema (Zod) + all types
│   │   └── abis.ts             # Contract ABIs (viem parseAbi)
│   └── workflows/
│       ├── threatDetection/
│       │   ├── main.ts         # Cron → TVL + price → AI detect → CircuitBreaker
│       │   ├── config.json     # Runtime config (addresses, thresholds)
│       │   └── workflow.yaml
│       ├── forensicAnalysis/
│       │   ├── main.ts         # Log trigger → ChainSherlock → report on-chain
│       │   └── workflow.yaml
│       ├── healthCheck/
│       │   ├── main.ts         # 5-min cron → API health + sentinel liveness
│       │   └── workflow.yaml
│       ├── ccipAlert/
│       │   ├── main.ts         # Log trigger → CCIP cross-chain message
│       │   └── workflow.yaml
│       └── vrfTieBreaker/
│           ├── main.ts         # VRF randomness → weighted vote selection
│           └── workflow.yaml
├── tsconfig.json
└── package.json
```

## Configuration

All workflows share `threatDetection/config.json` for deployed contract addresses:

```jsonc
{
  "schedule": "0 */1 * * * *",       // Cron schedule (every 60s)
  "agentApiUrl": "http://localhost:8000",
  "evm": {
    "chainId": 84532,                // Base Sepolia
    "rpcUrl": "https://sepolia.base.org",
    "circuitBreakerAddress": "0xa0eE49660252B353830ADe5de0Ca9385647F85b5",
    "threatReportAddress": "0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499",
    "sentinelRegistryAddress": "0xd34FC1ee378F342EFb92C0D334362B9E577b489f",
    "mockProtocolAddress": "0x11887863b89F1bE23A650909135ffaCFab666803",
    "dataFeeds": {
      "ethUsd": "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1"
    },
    // Optional — set to enable CCIP and VRF features
    "ccipRouter": "0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93",
    "linkToken": "0xE4aB69C077896252FAFBD49EFD26B5D171A32410",
    "vrfCoordinator": "0xd691f04bc0c9a24Edb78af9E005Cf85768F694C9"
  }
}
```

## Environment Variables

```bash
# Required
AGENT_API_URL=http://localhost:8000    # Python agent API

# For deployment
DEPLOYER_PRIVATE_KEY=...               # Key with DEFAULT_ADMIN_ROLE on contracts
CRE_WORKFLOW_ADDRESS=...               # Address of deployed CRE workflow (for role grants)

# Chainlink (Base Sepolia)
BASE_SEPOLIA_RPC=https://sepolia.base.org
```

Secrets are mapped via `secrets.yaml`:
```yaml
secrets:
  AGENT_API_URL:
    env: "AGENT_API_URL"
```

## Running Workflows

### Simulate Locally

```bash
# Simulate threat detection workflow
cre workflow simulate threatDetection

# Simulate with broadcast (sends real transactions)
cre workflow simulate threatDetection --broadcast

# Simulate forensic analysis (requires a CircuitBreakerTriggered event)
cre workflow simulate forensicAnalysis

# Simulate health check
cre workflow simulate healthCheck
```

### Deploy to Chainlink Network

```bash
# Deploy all workflows
cre workflow deploy --network base-sepolia

# Deploy specific workflow
cre workflow deploy threatDetection --network base-sepolia
```

### Integration Setup

Before deploying workflows, run the Foundry integration script to set up permissions:

```bash
cd packages/contracts

# Register MockProtocol + grant CRE_WORKFLOW_ROLE + register sentinels
CRE_WORKFLOW_ADDRESS=0x... forge script script/IntegrateProtocol.s.sol:IntegrateProtocol \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast

# Verify configuration
forge script script/IntegrateProtocol.s.sol:ConfigureCircuitBreaker \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY
```

## Workflow Details

### Threat Detection (30-second cycle)

```
Cron (60s) → Read MockProtocol TVL (EVM Read)
           → Read ETH/USD price (Data Feeds)
           → POST /api/v1/detect (AI Agents — 3 sentinels + consensus)
           → If CRITICAL → triggerBreaker() (EVM Write)
           → Submit ThreatReport on-chain (EVM Write)
```

### CCIP Alert (event-triggered)

```
CircuitBreakerTriggered event → Decode threat details
                               → Check LINK balance
                               → Estimate CCIP fee
                               → Approve LINK spend
                               → ccipSend() to destination chain
```

### VRF Tie-Breaker (on-demand)

```
Split vote detected → Request VRF randomness
                    → Fetch sentinel votes from /api/v1/sentinel/aggregate
                    → Weight by reputation (Liquidity=95, Oracle=90, Governance=85)
                    → Select winner using VRF random word
                    → Return resolved consensus
```

## Testing

```bash
# Type-check all workflows
npx tsc --noEmit

# Run workflow tests
pnpm test

# Simulate individual workflows
cre workflow simulate threatDetection
cre workflow simulate healthCheck
```

## Deployed Contracts (Base Sepolia)

| Contract | Address |
|----------|---------|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` |
| MockProtocol | `0x11887863b89F1bE23A650909135ffaCFab666803` |
