# AEGIS Protocol

> The Immune System for DeFi

AI-powered threat detection. Chainlink-verified consensus. Instant automated response.

---

## Hackathon Submission

Chainlink Convergence Hackathon | Feb 6 - Mar 8, 2026 | Track: Risk & Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CRE Workflow with blockchain + AI agent | ✅ | [threatDetection/main.ts](packages/cre-workflows/src/workflows/threatDetection/main.ts) |
| Successful CRE simulation | ✅ | [CRE_DEPLOYMENT.md](docs/CRE_DEPLOYMENT.md) |
| 5 Chainlink services | ✅ | CRE + Data Feeds + Automation + VRF + CCIP |
| On-chain proof (CCIP) | ✅ | [TX 0x6339...](https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303) |
| On-chain proof (VRF) | ✅ | [TX 0x761c...](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |

---

## The Problem

In 2024, DeFi protocols lost $3 billion to exploits. The pattern is always the same:

```
Attack begins (Block N)
    ↓
Funds drained (2-5 minutes)
    ↓
Community notices on Twitter (30-60 minutes)
    ↓
Security team investigates (2-6 hours)
    ↓
Funds: UNRECOVERABLE
```

The problem isn't detection algorithms. The problem is TIME.

---

## The Solution

AEGIS (AI-Enhanced Guardian Intelligence System) detects threats in 30 seconds and responds automatically.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AEGIS PROTOCOL                              │
│                                                                     │
│     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│     │  LIQUIDITY  │   │   ORACLE    │   │ GOVERNANCE  │           │
│     │  SENTINEL   │   │  SENTINEL   │   │  SENTINEL   │           │
│     │             │   │             │   │             │           │
│     │  Monitors   │   │  Compares   │   │  Analyzes   │           │
│     │  TVL drops  │   │  prices to  │   │  proposals  │           │
│     │  & outflows │   │  Chainlink  │   │  for threats│           │
│     └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│            │                 │                 │                   │
│            └─────────────────┼─────────────────┘                   │
│                              ▼                                     │
│               ┌──────────────────────────────┐                     │
│               │   CONSENSUS COORDINATOR      │                     │
│               │   (2/3 majority required)    │                     │
│               └──────────────┬───────────────┘                     │
│                              │                                     │
│        ┌─────────────────────┼─────────────────────┐               │
│        ▼                     ▼                     ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   CIRCUIT    │    │   TELEGRAM   │    │   CHAIN      │         │
│  │   BREAKER    │    │    ALERT     │    │   SHERLOCK   │         │
│  │  (pause tx)  │    │ (notify ops) │    │  (forensics) │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

How it works:

1. Three AI sentinels monitor a protocol in real-time
2. Each sentinel votes on threat level: NONE → LOW → MEDIUM → HIGH → CRITICAL
3. When 2 of 3 agree on HIGH/CRITICAL → consensus reached
4. Circuit Breaker triggers automatically → protocol pauses
5. ChainSherlock traces the attack and generates a forensic report

---

## Chainlink Services (5 Total = +4 Bonus Points)

| Service | Purpose | On-Chain Proof |
|---------|---------|----------------|
| CRE | Workflow orchestration | Simulation passed ([docs](docs/CRE_DEPLOYMENT.md)) |
| Data Feeds | ETH/USD price verification | Used in every detection cycle |
| Automation | 30-second monitoring cycles | Cron trigger in CRE workflow |
| VRF | Fair tie-breaker selection | [BaseScan TX](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |
| CCIP | Cross-chain alerts | [CCIP Explorer](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238) |

### All Files Using Chainlink (Required for Submission)

CRE Workflows (`packages/cre-workflows/`):
- [`src/workflows/threatDetection/main.ts`](packages/cre-workflows/src/workflows/threatDetection/main.ts) — Main detection workflow (Cron trigger → HTTP → EVM Read/Write)
- [`src/workflows/forensicAnalysis/main.ts`](packages/cre-workflows/src/workflows/forensicAnalysis/main.ts) — Forensic analysis workflow
- [`src/workflows/healthCheck/main.ts`](packages/cre-workflows/src/workflows/healthCheck/main.ts) — System health monitoring
- [`src/workflows/ccipAlert/main.ts`](packages/cre-workflows/src/workflows/ccipAlert/main.ts) — Cross-chain alert propagation via CCIP
- [`src/workflows/vrfTieBreaker/main.ts`](packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts) — VRF-based consensus tie-breaker
- [`src/types/abis.ts`](packages/cre-workflows/src/types/abis.ts) — CCIP Router, VRF Coordinator, Data Feed ABIs
- [`project.yaml`](packages/cre-workflows/project.yaml) — CRE project configuration

Data Feeds (`packages/agents-py/`):
- [`aegis/blockchain/chainlink_feeds.py`](packages/agents-py/aegis/blockchain/chainlink_feeds.py) — ETH/USD, USDC/USD price reads
- [`aegis/config.py`](packages/agents-py/aegis/config.py) — Chainlink feed addresses (Base, Ethereum, multi-chain)

Smart Contracts (`packages/contracts/`):
- [`src/vrf/AegisVRFConsumer.sol`](packages/contracts/src/vrf/AegisVRFConsumer.sol) — VRF v2.5 consumer contract
- [`src/ccip/AlertReceiver.sol`](packages/contracts/src/ccip/AlertReceiver.sol) — CCIP message receiver
- [`script/DeployVRFConsumer.s.sol`](packages/contracts/script/DeployVRFConsumer.s.sol) — VRF deployment script
- [`script/DeployCCIPReceiver.s.sol`](packages/contracts/script/DeployCCIPReceiver.s.sol) — CCIP receiver deployment

---

## Deployed Smart Contracts (Base Sepolia)

| Contract | Address | Verified |
|----------|---------|----------|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` | Yes |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | Yes |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` | Yes |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` | Yes |
| TestVault | `0xB85d57374c18902855FA85d6C36080737Fb7509c` | Yes |
| AegisVRFConsumer | `0x51bAC1448E5beC0E78B0408473296039A207255e` | Yes |

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/aegis-protocol/aegis.git
cd aegis
pnpm install
```

### 2. Set Up Python Environment

```bash
cd packages/agents-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### 3. Configure Environment

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY
```

### 4. Run All Services

```bash
bash scripts/run-demo.sh
```

### 5. Open Dashboard

Navigate to http://localhost:5173

---

## Demo: Simulate an Attack

### Option 1: Visual Exploit Simulator (Recommended)

Run the production-ready exploit simulator with ASCII art, progress bars, and real-time sentinel responses:

```bash
# Classic reentrancy attack (The DAO style)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=reentrancy

# Euler Finance flash loan exploit ($197M)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=euler

# Oracle manipulation attack (Mango Markets style)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=oracle

# Malicious governance attack (Beanstalk style)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=governance

# Bridge exploit (Ronin style)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=bridge

# Curve pool imbalance attack
pnpm exec tsx scripts/simulate-exploit.ts --scenario=curve

# Run ALL scenarios sequentially
pnpm exec tsx scripts/simulate-exploit.ts --all

# Enable REAL on-chain circuit breaker (requires DEPLOYER_PRIVATE_KEY)
pnpm exec tsx scripts/simulate-exploit.ts --scenario=euler --live
```

Supported Protocols: MockProtocol, Aave V3, Uniswap V3, Compound V3, Curve 3pool, Balancer V2, Stargate Bridge, Euler Finance

### Option 2: Direct API Call

```bash
# Simulate a reentrancy attack (25% TVL drop + 6% price deviation)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25,"simulate_price_deviation_percent":6}'
```

### Option 3: Interactive Euler Replay (Frontend)

Navigate to http://localhost:5173/demo for a step-by-step visualization of the Euler Finance hack.

Expected result:
- Liquidity Sentinel → CRITICAL
- Oracle Sentinel → CRITICAL
- Consensus reached (2/3) → Circuit Breaker triggers
- Dashboard goes red → Protocol paused

---

## Deployed Contracts (Base Sepolia)

| Contract | Address | Explorer |
|----------|---------|----------|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` | [View](https://sepolia.basescan.org/address/0xd34FC1ee378F342EFb92C0D334362B9E577b489f) |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | [View](https://sepolia.basescan.org/address/0xa0eE49660252B353830ADe5de0Ca9385647F85b5) |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` | [View](https://sepolia.basescan.org/address/0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499) |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` | [View](https://sepolia.basescan.org/address/0x7970433B694f7fa6f8D511c7B20110ECd28db100) |
| MockProtocol | `0x11887863b89F1bE23A650909135ffaCFab666803` | [View](https://sepolia.basescan.org/address/0x11887863b89F1bE23A650909135ffaCFab666803) |

---

## Project Structure

```
packages/
├── contracts/       # Solidity smart contracts (Foundry)
│   └── src/
│       ├── core/    # SentinelRegistry, CircuitBreaker, ThreatReport
│       └── mocks/   # MockProtocol for testing
│
├── agents-py/       # Python AI agents (CrewAI + FastAPI)
│   └── aegis/
│       ├── sentinels/     # Liquidity, Oracle, Governance sentinels
│       ├── sherlock/      # Forensic analysis engine
│       ├── coordinator/   # Consensus logic
│       └── api/           # FastAPI server (port 8000)
│
├── api/             # TypeScript gateway (Hono, port 3000)
│   └── src/
│       ├── routes/  # REST endpoints
│       └── services/# Agent proxy, Telegram notifications
│
├── cre-workflows/   # Chainlink CRE workflows
│   └── src/workflows/
│       ├── threatDetection/   # Main detection loop
│       ├── ccipAlert/         # Cross-chain alerts
│       └── vrfTieBreaker/     # VRF-based consensus
│
└── frontend/        # React dashboard (Vite + Tailwind)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Smart Contracts | Solidity 0.8.24, Foundry, OpenZeppelin |
| AI Agents | Python 3.12, CrewAI, Anthropic Claude |
| Agent API | FastAPI, Pydantic v2, web3.py |
| Gateway API | Hono, ethers.js v6, SQLite |
| Frontend | React 18, Vite, TailwindCSS |
| Blockchain | Base Sepolia, Chainlink (CRE, Data Feeds, VRF, CCIP, Automation) |

---

## Tests

```bash
# Smart contract tests (21 passing)
cd packages/contracts && forge test

# Python agent tests (147 passing)
cd packages/agents-py && python -m pytest tests/ -v
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health check |
| `/api/v1/sentinel/aggregate` | GET | All sentinel assessments + consensus |
| `/api/v1/sentinel/detect` | POST | Trigger detection cycle |
| `/api/v1/alerts` | GET | List threat alerts |
| `/api/v1/forensics` | GET/POST | Forensic reports |

Full API documentation: http://localhost:3000/api/v1/docs

---

## Documentation

- [CRE Deployment](docs/CRE_DEPLOYMENT.md) — CRE workflow simulation & deployment status
- [Demo Guide](docs/DEMO_GUIDE.md) — Step-by-step demo instructions
- [Video Script](docs/VIDEO_SCRIPT.md) — 4-minute demo video script
- [Demo Runbook](docs/DEMO_RUNBOOK.md) — Commands for video recording
- [VRF Test Results](docs/VRF_TEST_RESULTS.md) — VRF integration proof
- [CCIP Test Results](docs/CCIP_TEST_RESULTS.md) — CCIP integration proof
- [Forensics Demo](docs/FORENSICS_DEMO.md) — ChainSherlock Euler hack analysis
- [Judge Cheatsheet](docs/JUDGE_CHEATSHEET.md) — One-pager for hackathon judges
- [Judge Q&A](docs/JUDGE_QA.md) — Anticipated questions and answers
- [CLAUDE.md](CLAUDE.md) — Technical reference for contributors

---

## Why AEGIS?

| Without AEGIS | With AEGIS |
|---------------|------------|
| Attack detected: 30+ min | Attack detected: 30 sec |
| Response: Manual | Response: Automatic |
| Funds lost: Millions | Funds lost: Zero |

---

## License

MIT

---

## Hackathon Submission Details

Event: Chainlink Convergence Hackathon (February 6 - March 8, 2026)

Track: Risk & Compliance ($6,000 prize)

### Requirements Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| CRE Workflow as orchestration layer | ✅ | 5 workflows in [`packages/cre-workflows/`](packages/cre-workflows/) |
| Integrates blockchain + AI agent | ✅ | EVM Read/Write + Python AI agents via HTTP |
| Successful CRE simulation | ✅ | `cre workflow simulate` passed ([docs](docs/CRE_DEPLOYMENT.md)) |
| 3-5 min video | ✅ | [Video script](docs/VIDEO_SCRIPT.md) |
| Public source code | ✅ | This repository |
| README links to Chainlink files | ✅ | See [Chainlink Integration](#all-files-using-chainlink-required-for-submission) above |

### On-Chain Proof of Chainlink Services

| Service | Transaction/Proof | Explorer Link |
|---------|-------------------|---------------|
| CCIP | Alert sent Base → Arbitrum | [TX 0x6339...](https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303) |
| CCIP | Message delivered | [CCIP Explorer](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238) |
| VRF | Randomness requested | [TX 0x761c...](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |
| Data Feeds | ETH/USD: $1965.14 | Live in every detection cycle |
| CRE | Workflow simulated | [Simulation output](docs/CRE_DEPLOYMENT.md) |
| Automation | Cron trigger | 30-second intervals in CRE workflow |

### Chainlink Services Used (5 = +4 Bonus Points)

1. CRE — Workflow orchestration, consensus verification
2. Data Feeds — Real-time ETH/USD price for oracle manipulation detection
3. Automation — Scheduled 30-second monitoring cycles
4. VRF — Verifiable random tie-breaker when sentinels disagree
5. CCIP — Cross-chain alert propagation (Base → Arbitrum)

---

## Chainlink Documentation References

This project uses the following Chainlink services. Official documentation links for each:

| Service | Documentation | How AEGIS Uses It |
|---------|---------------|-------------------|
| Chainlink Runtime Environment (CRE) | [CRE Docs](https://docs.chain.link/cre) | Orchestrates threat detection workflows, connects AI agents to on-chain actions |
| Data Feeds | [Data Feeds Docs](https://docs.chain.link/data-feeds) | ETH/USD price verification for oracle manipulation detection ([Base Sepolia Feeds](https://docs.chain.link/data-feeds/price-feeds/addresses?network=base&page=1)) |
| Automation | [Automation Docs](https://docs.chain.link/chainlink-automation) | Cron-triggered 30-second monitoring cycles via CRE |
| VRF v2.5 | [VRF Docs](https://docs.chain.link/vrf) | Verifiable random tie-breaker when sentinel votes are split ([Base Sepolia VRF](https://docs.chain.link/vrf/v2-5/supported-networks#base-sepolia-testnet)) |
| CCIP | [CCIP Docs](https://docs.chain.link/ccip) | Cross-chain alert propagation from Base to other chains ([CCIP Directory](https://docs.chain.link/ccip/directory/testnet)) |

### CRE Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CRE WORKFLOW: threatDetection                     │
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐             │
│  │  CRON    │───▶│  HTTP FETCH  │───▶│  AI AGENTS    │             │
│  │ (30 sec) │    │ (Price Data) │    │ (Python API)  │             │
│  └──────────┘    └──────────────┘    └───────┬───────┘             │
│                                              │                       │
│                                              ▼                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    CONSENSUS CHECK                            │   │
│  │           (2/3 sentinels agree on threat level)               │   │
│  └──────────────────────────────┬───────────────────────────────┘   │
│                                 │                                    │
│               ┌─────────────────┼─────────────────┐                 │
│               ▼                 ▼                 ▼                 │
│        ┌────────────┐   ┌────────────┐   ┌────────────┐            │
│        │ EVM WRITE  │   │   CCIP     │   │   VRF      │            │
│        │ (Circuit   │   │ (Cross-    │   │ (Tie-      │            │
│        │  Breaker)  │   │  chain)    │   │  breaker)  │            │
│        └────────────┘   └────────────┘   └────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Chainlink Contract Addresses Used (Base Sepolia)

| Contract | Address | Purpose |
|----------|---------|---------|
| ETH/USD Data Feed | `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1` | Price oracle for manipulation detection |
| VRF Coordinator | `0xDA3b641D438362C440Ac5458c57e00a712b66700` | VRF v2.5 on Base Sepolia |
| CCIP Router | `0xD3b06cEbF099CE7DA4AcCf578aaebFDBd6e88a93` | Cross-chain messaging |
| LINK Token | `0xE4aB69C077896252FAFBD49EFD26B5D171A32410` | Payment for Chainlink services |
