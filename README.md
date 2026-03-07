# AEGIS Protocol

> **The Immune System for DeFi**

AI-powered threat detection. Chainlink-verified consensus. Instant automated response.
---

## The Problem

In 2024, DeFi protocols lost **$3 billion** to exploits. The pattern is always the same:

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

**The problem isn't detection algorithms. The problem is TIME.**

---

## The Solution

AEGIS (AI-Enhanced Guardian Intelligence System) detects threats in **30 seconds** and responds **automatically**.

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

**How it works:**

1. **Three AI sentinels** monitor a protocol in real-time
2. Each sentinel votes on threat level: NONE → LOW → MEDIUM → HIGH → CRITICAL
3. When **2 of 3** agree on HIGH/CRITICAL → **consensus reached**
4. **Circuit Breaker** triggers automatically → protocol pauses
5. **ChainSherlock** traces the attack and generates a forensic report

---

## Chainlink Services (5 Total)

| Service | Purpose | Code |
|---------|---------|------|
| **CRE** | Workflow orchestration, consensus verification | [`threatDetection/main.ts`](packages/cre-workflows/src/workflows/threatDetection/main.ts) |
| **Data Feeds** | Price truth for oracle manipulation detection | [`chainlink_feeds.py`](packages/agents-py/aegis/blockchain/chainlink_feeds.py) |
| **Automation** | Scheduled 30-second detection cycles | Cron triggers in CRE workflows |
| **VRF** | Fair tie-breaker when sentinels disagree | [`vrfTieBreaker/main.ts`](packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts) |
| **CCIP** | Cross-chain alert propagation | [`ccipAlert/main.ts`](packages/cre-workflows/src/workflows/ccipAlert/main.ts) |

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

Navigate to **http://localhost:5173**

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

**Supported Protocols**: MockProtocol, Aave V3, Uniswap V3, Compound V3, Curve 3pool, Balancer V2, Stargate Bridge, Euler Finance

### Option 2: Direct API Call

```bash
# Simulate a reentrancy attack (25% TVL drop + 6% price deviation)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25,"simulate_price_deviation_percent":6}'
```

### Option 3: Interactive Euler Replay (Frontend)

Navigate to **http://localhost:5173/demo** for a step-by-step visualization of the Euler Finance hack.

**Expected result:**
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

# Python agent tests (96 passing)
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

- [Deployment Guide](docs/DEPLOYMENT.md) — Deploy to Vercel + Railway
- [Demo Guide](docs/DEMO_GUIDE.md) — Step-by-step demo instructions
- [Video Script](docs/VIDEO_SCRIPT.md) — 3-minute demo video script
- [Devpost](docs/DEVPOST.md) — Hackathon submission content
- [Judge Q&A](docs/JUDGE_QA.md) — Anticipated questions and answers
- [CLAUDE.md](CLAUDE.md) — Technical reference for contributors

---

## Why AEGIS?

| Without AEGIS | With AEGIS |
|---------------|------------|
| Attack detected: 30+ min | Attack detected: **30 sec** |
| Response: Manual | Response: **Automatic** |
| Funds lost: Millions | Funds lost: **Zero** |

---

## License

MIT

---

## Hackathon

**Chainlink Convergence Hackathon** — February 6 to March 8, 2026

**Track**: Risk & Compliance

**Chainlink Services**: CRE, Data Feeds, Automation, VRF, CCIP (5 total = +4 bonus)
