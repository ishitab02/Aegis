# AEGIS Protocol - Devpost Submission

> Copy-paste ready content for Chainlink Convergence Hackathon Devpost submission.

---

## Project Name

```
AEGIS Protocol
```

---

## Tagline (140 characters max)

```
AI-powered DeFi security: 3 sentinel agents detect threats in seconds, trigger circuit breakers automatically, and investigate with forensics.
```

**Alternative taglines:**
- `The immune system for DeFi — AI sentinels that detect exploits in seconds and protect funds automatically.`
- `Stop DeFi hacks in real-time: AI threat detection + Chainlink-verified consensus + automatic circuit breakers.`

---

## Short Description (300 words)

DeFi protocols lost over $3 billion to exploits in 2024. The pattern repeats: attack begins, funds drain, community notices on Twitter 30 minutes later, security teams investigate for hours. By then, funds are bridged, mixed, and unrecoverable.

**AEGIS Protocol changes this.** We built an autonomous security infrastructure that detects threats in seconds — not hours — and automatically protects funds.

### How It Works

Three AI sentinel agents continuously monitor a DeFi protocol:

1. **Liquidity Sentinel** — Watches TVL (Total Value Locked). If funds drain faster than normal (>10% in one cycle), it raises an alarm.
2. **Oracle Sentinel** — Compares on-chain prices against Chainlink Data Feeds. Price manipulation? Detected instantly.
3. **Governance Sentinel** — Analyzes proposals for malicious patterns like ownership transfers or disabled security.

Each sentinel independently assigns a threat level: NONE, LOW, MEDIUM, HIGH, or CRITICAL.

When **2 of 3 sentinels** agree on a HIGH/CRITICAL threat, the system reaches consensus and triggers an on-chain **Circuit Breaker** — pausing the protocol before funds can be drained.

After the protocol is paused, **ChainSherlock** (our forensic AI) traces the attack, classifies the vulnerability, and generates a detailed report.

### Built on Chainlink

AEGIS uses **5 Chainlink services**:
- **CRE** — Orchestrates detection workflows every 30 seconds
- **Data Feeds** — Price truth for oracle manipulation detection
- **Automation** — Keeps sentinels running 24/7
- **VRF** — Fair tie-breaker selection when sentinels disagree
- **CCIP** — Cross-chain alert propagation

### Why This Matters

- **30-second detection** vs. 30-minute human response
- **Automatic protection** — no human intervention needed
- **Verifiable consensus** — not "trust me" centralized monitoring
- **Real-time forensics** — know what happened immediately

AEGIS is the immune system DeFi has been waiting for.

---

## Long Description (Full Writeup)

### The $3 Billion Problem

In 2024, DeFi protocols lost over $3 billion to exploits. Euler Finance: $197M. Ronin Bridge: $625M. Wormhole: $326M. The list goes on.

Every major hack follows the same devastating pattern:

```
Block N      → Attack begins
Block N+5    → Funds drained (2-5 minutes)
+30 minutes  → Community notices on Twitter
+2 hours     → Security team investigates
+24 hours    → Post-mortem published
             → Funds: UNRECOVERABLE
```

The problem isn't detection algorithms. The problem is **time**. By the time humans notice, analyze, and respond, the attacker has already bridged and mixed the stolen funds.

DeFi protocols need an autonomous immune system — one that watches 24/7, detects threats in seconds, and responds automatically.

### Introducing AEGIS Protocol

AEGIS (AI-Enhanced Guardian Intelligence System) is an autonomous security infrastructure for DeFi. It combines real-time threat detection, consensus-driven circuit breaking, and AI-powered forensic analysis.

#### The SentinelSwarm

Three specialized AI agents continuously monitor a protected protocol:

**1. Liquidity Sentinel**
- Monitors TVL (Total Value Locked) in real-time
- Detects abnormal fund outflows (flash loans, rapid withdrawals)
- Thresholds: 5% drop → MEDIUM, 10% → HIGH, 20% → CRITICAL

**2. Oracle Sentinel**
- Compares protocol's internal prices against Chainlink Data Feeds
- Detects price manipulation attacks
- Thresholds: 2% deviation → HIGH, 5% → CRITICAL

**3. Governance Sentinel**
- Analyzes governance proposals for malicious patterns
- Flags suspicious function calls (transferOwnership, upgradeTo, etc.)
- Detects unusually short voting periods

Each sentinel independently votes on threat level. When 2 of 3 agree on HIGH or CRITICAL, the Consensus Coordinator triggers action.

#### The Consensus Mechanism

We use a 2/3 majority consensus rule. This prevents false positives from a single malfunctioning sentinel while ensuring real threats get caught by at least two independent detectors.

When consensus is reached:
1. **Circuit Breaker** triggers — protocol pauses on-chain
2. **Telegram alert** fires — operators notified instantly
3. **ChainSherlock** activates — forensic analysis begins

#### ChainSherlock: AI Forensics

After a threat is detected, ChainSherlock traces the suspicious transaction:
- Builds a transaction graph of all internal calls
- Identifies known attacker addresses, mixers, CEX wallets
- Classifies the attack type (reentrancy, flash loan, oracle manipulation)
- Generates a structured forensic report

### Chainlink Integration (5 Services)

AEGIS is deeply integrated with Chainlink's infrastructure:

**1. CRE (Chainlink Runtime Environment)**
- Orchestrates the entire detection → response pipeline
- Runs workflows every 30 seconds
- Provides BFT consensus verification for critical actions
- Code: `packages/cre-workflows/src/workflows/threatDetection/main.ts`

**2. Data Feeds**
- Source of truth for price verification
- ETH/USD feed on Base Sepolia: `0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1`
- Oracle Sentinel compares protocol prices against these feeds
- Code: `packages/agents-py/aegis/blockchain/chainlink_feeds.py`

**3. Automation**
- Cron-based triggers for scheduled monitoring
- Keeps sentinels running 24/7 without manual intervention
- Code: Cron trigger configuration in CRE workflows

**4. VRF (Verifiable Random Function)**
- Fair tie-breaker selection when sentinels are split 1-1-1
- Provably random, tamper-proof selection
- Code: `packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts`

**5. CCIP (Cross-Chain Interoperability Protocol)**
- Propagates alerts across chains
- If Base is attacked, Ethereum and Arbitrum deployments get notified
- Code: `packages/cre-workflows/src/workflows/ccipAlert/main.ts`

### Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AEGIS PROTOCOL                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CHAINLINK CRE WORKFLOW (30s cron)                             │
│        │                                                       │
│        ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  SENTINELSWARM                           │   │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐           │   │
│  │   │LIQUIDITY │   │ ORACLE   │   │GOVERNANCE│           │   │
│  │   │ SENTINEL │   │ SENTINEL │   │ SENTINEL │           │   │
│  │   └────┬─────┘   └────┬─────┘   └────┬─────┘           │   │
│  │        └──────────────┼──────────────┘                 │   │
│  │                       ▼                                 │   │
│  │              CONSENSUS (2/3 vote)                       │   │
│  └───────────────────────┼─────────────────────────────────┘   │
│                          ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ CIRCUIT BREAKER │ TELEGRAM ALERT │ CHAINSHERLOCK FORENSICS│ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  SMART CONTRACTS (Base Sepolia)                                │
│  ├── SentinelRegistry.sol — Agent registration                 │
│  ├── CircuitBreaker.sol — Emergency pause                      │
│  ├── ThreatReport.sol — On-chain reports                       │
│  └── ReputationTracker.sol — Sentinel accuracy                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Smart Contracts

Deployed on Base Sepolia:

| Contract | Address | Purpose |
|----------|---------|---------|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` | ERC-721 registry for sentinel agents |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | Emergency pause controller |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` | Immutable threat report storage |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` | Sentinel accuracy tracking |
| MockProtocol | `0x11887863b89F1bE23A650909135ffaCFab666803` | Demo protocol for testing |

### Test Coverage

- **Smart Contracts**: 21 tests (Foundry)
- **Python Agents**: 96 tests (pytest)
- **All tests passing**

### The Demo

1. Dashboard shows healthy protocol (100 ETH TVL, all sentinels green)
2. Simulate reentrancy attack (25% TVL drop + 6% price deviation)
3. Two sentinels go CRITICAL
4. Consensus reached → Circuit Breaker fires
5. Protocol paused, funds protected
6. ChainSherlock generates forensic report

### Why Risk & Compliance Track?

AEGIS directly addresses the biggest compliance risk in DeFi: protocol exploits. We provide:

- **Real-time risk monitoring** — not periodic audits
- **Automated compliance** — circuit breakers enforce protection
- **Audit trail** — all threats and responses logged on-chain
- **Verifiable execution** — Chainlink CRE ensures tamper-proof workflows

### Business Model (Future)

1. **Protocol Subscriptions** — Monthly fee for AEGIS protection
2. **Forensic Reports** — Pay-per-use via x402 ($1/report)
3. **Insurance Integration** — Reduced premiums for protected protocols

---

## How We Built It

### Tech Stack

| Layer | Technology |
|-------|------------|
| Smart Contracts | Solidity 0.8.24, Foundry, OpenZeppelin |
| AI Agents | Python 3.12, CrewAI, Anthropic Claude |
| Agent API | FastAPI, Pydantic v2, web3.py |
| Gateway API | Hono, ethers.js v6, SQLite |
| Frontend | React 18, Vite, TailwindCSS, React Query |
| Blockchain | Base Sepolia, Chainlink (CRE, Data Feeds, VRF, CCIP, Automation) |

### Development Process

1. **Week 1**: Designed architecture, deployed smart contracts
2. **Week 2**: Built Python AI agents with CrewAI
3. **Week 3**: Integrated CRE workflows, added protocol adapters (Aave, Uniswap)
4. **Week 4**: Built frontend dashboard, added Telegram notifications, testing

### Lines of Code

- Smart Contracts: ~800 lines (Solidity)
- Python Agents: ~2,500 lines
- TypeScript API: ~1,200 lines
- CRE Workflows: ~600 lines
- Frontend: ~1,000 lines

---

## Challenges We Ran Into

### 1. CRE SDK Learning Curve
The Chainlink Runtime Environment was new to us. We spent significant time understanding workflow triggers, capabilities, and consensus requirements. The documentation helped, but hands-on experimentation was essential.

### 2. Consensus Timing
Balancing detection speed vs. false positives was tricky. Too aggressive → false alarms. Too conservative → missed attacks. We settled on a 2/3 majority with configurable thresholds per protocol.

### 3. Real Protocol Data
Connecting to actual DeFi protocols (Aave, Uniswap) required understanding their ABIs, event structures, and data formats. We built protocol adapters with caching to handle this efficiently.

### 4. Multi-Service Orchestration
AEGIS has multiple services (Python API, TypeScript API, CRE workflows, smart contracts). Ensuring they communicate correctly — especially during live demos — required careful coordination.

---

## What We Learned

1. **CRE is powerful** — Being able to orchestrate detection, consensus, and on-chain actions in a verifiable workflow is game-changing for security applications.

2. **Multi-agent AI works** — Having specialized sentinels (liquidity, oracle, governance) each focusing on their domain, then voting on consensus, is more robust than a single "god model."

3. **Speed matters** — The difference between 30-second detection and 30-minute detection is the difference between "funds protected" and "funds gone."

4. **Chainlink services compose well** — Data Feeds for price truth, CRE for orchestration, VRF for fairness, CCIP for cross-chain — they all fit together naturally.

---

## What's Next

### Short Term (Post-Hackathon)
- Deploy CRE workflows to Chainlink mainnet
- Add more protocol adapters (Compound, Curve)
- Production-grade Telegram/Discord/PagerDuty integrations

### Medium Term (3-6 months)
- Protocol onboarding portal with x402 payments
- Multi-chain deployment (Ethereum, Arbitrum, Optimism)
- Machine learning models trained on historical exploit data

### Long Term (6-12 months)
- DAO governance for sentinel upgrades
- Integration with DeFi insurance protocols
- Token economics for sentinel operators

---

## Chainlink Services Used

| Service | How We Use It | Code Location |
|---------|---------------|---------------|
| **CRE** | Orchestrates detection workflows every 30s, triggers circuit breakers with consensus | `packages/cre-workflows/src/workflows/threatDetection/main.ts` |
| **Data Feeds** | Price truth for oracle manipulation detection (ETH/USD) | `packages/agents-py/aegis/blockchain/chainlink_feeds.py` |
| **Automation** | Scheduled monitoring cycles via cron triggers | CRE workflow cron configuration |
| **VRF** | Fair tie-breaker selection when sentinels split 1-1-1 | `packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts` |
| **CCIP** | Cross-chain alert propagation | `packages/cre-workflows/src/workflows/ccipAlert/main.ts` |

**Total: 5 services (+4 bonus points)**

---

## Links

| Resource | URL |
|----------|-----|
| GitHub Repository | `https://github.com/aegis-protocol/aegis` |
| Demo Video | `[YouTube link]` |
| Live Demo | `[if hosted]` |
| Deployed Contracts | Base Sepolia (see addresses above) |

---

## Team

[Add team member information]

---

## Built At

**Chainlink Convergence Hackathon**
February 6 - March 8, 2026

**Track**: Risk & Compliance ($20K prize pool)

---

## License

MIT License
