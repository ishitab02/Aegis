# AEGIS Protocol

**AI-Enhanced Guardian Intelligence System** — Real-time DeFi threat detection, consensus-driven circuit breaking, and AI-powered forensic analysis.

Built for the [Chainlink Convergence Hackathon](https://convergence.chainlink.com) using **5 Chainlink services**: CRE, Data Feeds, Automation, VRF, and CCIP.

---

## How It Works

Three AI sentinel agents continuously monitor a DeFi protocol:

| Sentinel | Watches For | Example Trigger |
|---|---|---|
| **Liquidity Sentinel** | Abnormal TVL drops | >10% TVL drain in one cycle |
| **Oracle Sentinel** | Price feed deviations | Chainlink vs market price divergence |
| **Governance Sentinel** | Malicious proposals | Suspicious function signatures |

When **2 of 3 sentinels** agree on a HIGH/CRITICAL threat, the system automatically triggers an on-chain **Circuit Breaker** to pause the protocol and protect funds. A forensic AI agent (**ChainSherlock**) then traces and classifies the attack.

## Architecture

```
Chainlink CRE Workflow (30s cron)
        │
        ▼
Python FastAPI + CrewAI Agents (port 8000)
        │
        ▼
TypeScript Hono API (port 3000)
        │
        ▼
React Dashboard (port 5173)
```

## Deployed Contracts (Base Sepolia)

| Contract | Address |
|---|---|
| SentinelRegistry | [`0xd34FC1ee378F342EFb92C0D334362B9E577b489f`](https://sepolia.basescan.org/address/0xd34FC1ee378F342EFb92C0D334362B9E577b489f) |
| CircuitBreaker | [`0xa0eE49660252B353830ADe5de0Ca9385647F85b5`](https://sepolia.basescan.org/address/0xa0eE49660252B353830ADe5de0Ca9385647F85b5) |
| ThreatReport | [`0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499`](https://sepolia.basescan.org/address/0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499) |
| ReputationTracker | [`0x7970433B694f7fa6f8D511c7B20110ECd28db100`](https://sepolia.basescan.org/address/0x7970433B694f7fa6f8D511c7B20110ECd28db100) |
| MockProtocol | [`0x11887863b89F1bE23A650909135ffaCFab666803`](https://sepolia.basescan.org/address/0x11887863b89F1bE23A650909135ffaCFab666803) |

## Getting Started

### Prerequisites

- Node.js >= 20, pnpm >= 9
- Python >= 3.11
- Foundry (forge, cast)
- An [Anthropic API key](https://console.anthropic.com)

### Step 1: Install Dependencies

```bash
# Clone the repo
git clone https://github.com/your-org/aegis-protocol.git
cd aegis-protocol

# Install Node dependencies
pnpm install

# Set up Python virtual environment
cd packages/agents-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Fill in your `.env` with:
- `DEPLOYER_PRIVATE_KEY` — wallet private key (funded with Base Sepolia ETH)
- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- Contract addresses (already filled if using the deployed contracts above)

### Step 3: Deploy Contracts (optional — already deployed)

If you need to redeploy:

```bash
cd packages/contracts
forge script script/Deploy.s.sol:DeployAegis \
  --fork-url https://sepolia.base.org \
  --private-key 0x$DEPLOYER_PRIVATE_KEY \
  --broadcast --verify
```

Update `.env` with the 5 deployed addresses from the output.

### Step 4: Run All Services

```bash
bash scripts/run-demo.sh
```

Or start each service individually:

```bash
# Terminal 1 — Python Agent API
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2 — TypeScript API
cd packages/api
npx tsx src/index.ts

# Terminal 3 — Frontend Dashboard
cd packages/frontend
pnpm dev
```

### Step 5: Open the Dashboard

Navigate to **http://localhost:5173**

The dashboard auto-triggers a detection scan on first load. Click **"Run Scan"** to trigger additional scans manually.

## Demo: Simulating an Attack

```bash
npx tsx scripts/simulate-exploit.ts
```

This simulates a reentrancy attack:
1. Rapid fund drainage from MockProtocol (25% TVL drop)
2. Liquidity Sentinel → CRITICAL, Oracle Sentinel → HIGH
3. Consensus reached (2/3) → Circuit Breaker triggers
4. Protocol paused, funds protected
5. ChainSherlock generates forensic report

## Project Structure

```
packages/
├── contracts/       # Solidity smart contracts (Foundry)
├── agents-py/       # Python AI agents (CrewAI + FastAPI)
├── api/             # TypeScript API gateway (Hono)
├── cre-workflows/   # Chainlink CRE workflow definitions
└── frontend/        # React dashboard (Vite + Tailwind)
scripts/
├── run-demo.sh      # Start all services
└── simulate-exploit.ts  # Attack simulation
```

## Tech Stack

| Layer | Technology |
|---|---|
| Smart Contracts | Solidity, Foundry, OpenZeppelin |
| AI Agents | Python, CrewAI, Anthropic Claude |
| Agent API | FastAPI, Pydantic, web3.py |
| Gateway API | Hono, ethers.js v6, x402 |
| Frontend | React, Vite, Tailwind CSS, React Query |
| Blockchain | Base Sepolia, Chainlink (CRE, Data Feeds, Automation, VRF, CCIP) |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | GET | System health check |
| `/api/v1/sentinel/aggregate` | GET | All sentinel assessments + consensus |
| `/api/v1/sentinel/{id}` | GET | Individual sentinel status |
| `/api/v1/sentinel/detect` | POST | Trigger full detection cycle |
| `/api/v1/forensics` | GET | List forensic reports |
| `/api/v1/forensics` | POST | Run forensic analysis (x402 gated) |

## License

MIT



```
What AEGIS Protocol Actually Does
AEGIS (AI-Enhanced Guardian Intelligence System) is a real-time DeFi security system that protects blockchain protocols from exploits like the ones that drained hundreds of millions from Euler Finance, Ronin Bridge, etc.

The Problem
DeFi protocols get hacked. By the time anyone notices, funds are already gone. There's no automated "immune system" watching for attacks in real time.

How AEGIS Works
3 AI Sentinel Agents constantly monitor a protocol, each watching for different attack signals:

Liquidity Sentinel — Watches the protocol's TVL (Total Value Locked). If funds start draining abnormally fast (>10% drop), it raises an alarm.

Oracle Sentinel — Compares Chainlink price feeds against market data. If prices diverge (a sign of oracle manipulation), it flags it.

Governance Sentinel — Analyzes governance proposals for suspicious patterns (e.g., proposals that try to change fund withdrawal logic or disable security checks).

Each sentinel independently assigns a threat level: NONE → LOW → MEDIUM → HIGH → CRITICAL.

The Consensus Mechanism
The 3 sentinels then vote. If 2 out of 3 agree the threat is HIGH or CRITICAL, the system reaches consensus and takes action — specifically, it triggers an on-chain Circuit Breaker smart contract that pauses the protocol, freezing all funds before the attacker can drain them.

ChainSherlock (Forensics)
After the protocol is paused, a forensic AI agent called ChainSherlock traces the suspicious transactions, classifies the attack type (reentrancy, flash loan, oracle manipulation, etc.), and generates a detailed report stored on-chain.

The Architecture (How Services Connect)

Chainlink CRE Workflow (every 30s)
        │
        ▼
Python FastAPI (port 8000) ← CrewAI orchestrates 3 sentinel agents
        │
        ▼
TypeScript API (port 3000) ← Proxies data, adds x402 payment gate
        │
        ▼
React Dashboard (port 5173) ← Polls every 5s, shows live threat status
The Chainlink CRE workflow is the orchestrator — it triggers detection cycles on a schedule, reads on-chain data (TVL, price feeds), calls the AI agents, and if the threat is critical, writes back to the blockchain to pause the protocol.

What Judges See in the Demo
Dashboard is green — "All Clear", protocol has 100 ETH locked
We simulate a reentrancy attack (rapid fund drainage)
Liquidity Sentinel goes CRITICAL, Oracle Sentinel goes HIGH
Consensus reached: 2/3 sentinels agree → Circuit Breaker fires
Dashboard goes red, protocol is paused, funds are safe
ChainSherlock produces a forensic report explaining the attack
After cooldown, protocol resumes
Why Chainlink
The project uses 5 Chainlink services (the hackathon requirement):

CRE — Orchestrates the entire detection → response pipeline
Data Feeds — ETH/USD price data for oracle manipulation detection
Automation — Cron-based triggers for periodic monitoring
VRF — Randomized tie-breaker when sentinels disagree 1-1-1
CCIP — Cross-chain alerts (e.g., notify Ethereum mainnet of a Base exploit)
In short: AEGIS is an AI-powered immune system for DeFi that detects attacks in real time, automatically pauses protocols to protect funds, and then forensically explains what happened.
```