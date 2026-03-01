# AEGIS Protocol - Claude Code Reference Guide

> **AEGIS** = AI-Enhanced Guardian Intelligence System

This document is the complete reference for Claude Code (or any AI coding assistant) to understand, navigate, and contribute to the AEGIS Protocol codebase. Read this ENTIRE document before making any changes.

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Solution Architecture](#3-solution-architecture)
4. [Technical Stack](#4-technical-stack)
5. [Repository Structure](#5-repository-structure)
6. [Core Components Deep Dive](#6-core-components-deep-dive)
7. [Chainlink Services Integration](#7-chainlink-services-integration)
8. [Data Flow & Sequences](#8-data-flow--sequences)
9. [Smart Contracts Specification](#9-smart-contracts-specification)
10. [CRE Workflows Specification](#10-cre-workflows-specification)
11. [AI Agent Specification](#11-ai-agent-specification)
12. [x402 Payment Integration](#12-x402-payment-integration)
13. [ERC-8004 Integration](#13-erc-8004-integration)
14. [API Specifications](#14-api-specifications)
15. [Testing Strategy](#15-testing-strategy)
16. [Deployment Guide](#16-deployment-guide)
17. [Environment Variables](#17-environment-variables)
18. [Common Tasks & Commands](#18-common-tasks--commands)
19. [Coding Standards](#19-coding-standards)
20. [Known Issues & TODOs](#20-known-issues--todos)
21. [Resources & References](#21-resources--references)
22. [Production Roadmap](#22-production-roadmap)
23. [Parallel Development Guide (4 Agents)](#23-parallel-development-guide-4-agents)
24. [Self-Updating Progress Protocol](#24-self-updating-progress-protocol)

---

## 1. PROJECT OVERVIEW

### What is AEGIS Protocol?

AEGIS Protocol is an autonomous, AI-powered security infrastructure for DeFi protocols. It combines two integrated systems:

1. **SentinelSwarm**: A network of specialized AI agents that continuously monitor DeFi protocols for anomalies and threats, capable of triggering circuit breakers when consensus is reached.

2. **ChainSherlock**: An AI forensics engine that, when triggered by threat detection, traces attack paths, identifies vulnerabilities, and generates actionable reports in real-time.

### The One-Liner

> "AEGIS is the immune system for DeFi - AI agents that detect threats in seconds and investigate exploits in minutes, not hours."

### Hackathon Context

- **Event**: Chainlink Convergence Hackathon (Feb 6 - Mar 8, 2026)
- **Submission Deadline**: March 8, 2026
- **Track**: Risk & Compliance ($20K dedicated prize) + AI Track
- **Requirements**: Must use CRE (Chainlink Runtime Environment) as orchestration layer
- **Bonus Points**: +4 for using 4+ Chainlink services

### Chainlink Services We Use (5 total = +4 bonus)

| Service | Purpose in AEGIS |
|---------|------------------|
| CRE | Workflow orchestration, consensus verification |
| Data Feeds | Real-time price verification for anomaly detection (ETH/USD) |
| Automation | Scheduled detection cycles every 30 seconds |
| VRF | Fair tie-breaker selection when sentinels disagree |
| CCIP | Cross-chain alert propagation |

---

## 2. PROBLEM STATEMENT

### The $3 Billion Problem

In 2024 alone, DeFi protocols lost over $3 billion to exploits. The pattern is always the same:

```
Attack begins (Block N)
    ↓ 
Funds drained (Block N+1 to N+10) [~2-5 minutes]
    ↓
Community notices on Twitter [~30-60 minutes]
    ↓
Security researchers analyze [~2-6 hours]
    ↓
Post-mortem published [~1-7 days]
    ↓
Funds already mixed/bridged [unrecoverable]
```

### Why Current Solutions Fail

| Solution | Limitation |
|----------|------------|
| Manual monitoring | Humans can't watch 24/7, react in seconds |
| Simple alerts | High false positives, no intelligence |
| Bug bounties | Reactive, not preventive |
| Audits | Point-in-time, can't catch runtime exploits |
| Insurance | Pays after loss, doesn't prevent it |

### What's Needed

1. **Detection in seconds**, not minutes
2. **Automated response** capability (circuit breakers)
3. **Multi-signal analysis** (not just one metric)
4. **Verifiable execution** (not trust-me centralized)
5. **Real-time forensics** when incidents occur

---

## 3. SOLUTION ARCHITECTURE

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AEGIS PROTOCOL                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         ┌─────────────────────┐                             │
│                         │   PROTECTED DEFI    │                             │
│                         │     PROTOCOLS       │                             │
│                         │  (Aave, Compound,   │                             │
│                         │   Uniswap, etc.)    │                             │
│                         └──────────┬──────────┘                             │
│                                    │ monitors                               │
│                                    ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        SENTINELSWARM                                  │  │
│  │                                                                       │  │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │  │
│  │   │  LIQUIDITY  │   │   ORACLE    │   │ GOVERNANCE  │               │  │
│  │   │  SENTINEL   │   │  SENTINEL   │   │  SENTINEL   │               │  │
│  │   │             │   │             │   │             │               │  │
│  │   │ • TVL drops │   │ • Price     │   │ • Malicious │               │  │
│  │   │ • Flash     │   │   deviation │   │   proposals │               │  │
│  │   │   loans     │   │ • Staleness │   │ • Timelock  │               │  │
│  │   │ • Withdraws │   │ • Outliers  │   │   bypass    │               │  │
│  │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘               │  │
│  │          │                 │                 │                       │  │
│  │          └─────────────────┼─────────────────┘                       │  │
│  │                            ↓                                         │  │
│  │              ┌─────────────────────────────┐                         │  │
│  │              │    CONSENSUS COORDINATOR    │                         │  │
│  │              │    (2/3 agreement required) │                         │  │
│  │              └──────────────┬──────────────┘                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ↓ threat detected                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CHAINSHERLOCK                                  │  │
│  │                                                                        │  │
│  │   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │  │
│  │   │ TRANSACTION    │  │ VULNERABILITY  │  │ FUND TRACKING  │         │  │
│  │   │ GRAPH ANALYSIS │→ │ CLASSIFICATION │→ │ & REPORTING    │         │  │
│  │   └────────────────┘  └────────────────┘  └────────────────┘         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ↓                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    CRE WORKFLOW LAYER                                  │  │
│  │                                                                        │  │
│  │   Triggers: Cron (30s) | HTTP | LogTrigger                           │  │
│  │   Capabilities: HTTP | EVM Read | EVM Write | Data Feeds | VRF | CCIP│  │
│  │   Output: Consensus-verified signed reports                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                │                                            │
│                                ↓                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    SMART CONTRACT LAYER                                │  │
│  │                                                                        │  │
│  │   SentinelRegistry.sol │ CircuitBreaker.sol │ ThreatReport.sol        │  │
│  │   ReputationTracker.sol │ AegisPayments.sol                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    x402 PAYMENT LAYER                                  │  │
│  │                                                                        │  │
│  │   Protocol subscriptions │ Premium forensics │ Alert notifications    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| LiquiditySentinel | Monitor TVL, withdrawals, flash loans | CrewAI Agent + Python |
| OracleSentinel | Monitor price feeds, detect manipulation | CrewAI Agent + Chainlink Data Feeds |
| GovernanceSentinel | Monitor proposals, detect malicious governance | CrewAI Agent + Python |
| Consensus Coordinator | Aggregate sentinel signals, enforce 2/3 rule | Python (reach_consensus) |
| ChainSherlock | Forensic analysis and reporting | CrewAI Agent + Anthropic Claude |
| CRE Workflows | Verifiable execution, on-chain actions | Chainlink CRE SDK (TypeScript) |
| Smart Contracts | State management, circuit breakers | Solidity (Foundry) |
| x402 Gateway | Payment processing | Coinbase x402 SDK (Hono middleware) |

---

## 4. TECHNICAL STACK

### Languages & Frameworks

```yaml
Smart Contracts:
  - Solidity ^0.8.24
  - Foundry (forge, cast, anvil)
  - OpenZeppelin Contracts

CRE Workflows:
  - TypeScript 5.x
  - Chainlink CRE SDK
  - Node.js 20+

AI Agents (Python - IMPLEMENTED):
  - Python 3.12+
  - CrewAI (multi-agent orchestration)
  - Anthropic Claude (primary LLM)
  - FastAPI (HTTP API on port 8000)
  - web3.py (on-chain reads)
  - Pydantic v2 (data models)

Backend Services:
  - TypeScript 5.x
  - Express.js or Hono
  - ethers.js v6

Frontend (minimal):
  - React 18
  - Vite
  - TailwindCSS
  - wagmi + viem

Testing:
  - Foundry (forge test) - contracts
  - pytest - Python agents (96 tests passing)
  - Vitest - CRE workflows / TS API
```

### External Dependencies

```yaml
Chainlink:
  - CRE CLI: curl -sSL https://cre.chain.link/install.sh | bash
  - Data Feeds: On-chain price oracles
  - Data Streams: Real-time data via WebSocket
  - CCIP: Cross-chain messaging
  - VRF: Verifiable randomness
  - Automation: Keeper network

Coinbase:
  - x402 SDK: @x402/core, @x402/evm, @x402/fetch
  - Facilitator: https://x402.org/facilitator (Base)

AI/LLM:
  - Anthropic Claude API (primary, via CrewAI)
  - Google Gemini API (backup)
  - OpenAI GPT-4 (backup)

Blockchain:
  - Base Sepolia (primary testnet)
  - Ethereum Sepolia (secondary)
  - Arbitrum Sepolia (CCIP testing)
```

### Network Configuration

```yaml
Base Sepolia:
  Chain ID: 84532
  RPC: https://sepolia.base.org
  Explorer: https://sepolia.basescan.org
  USDC: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
  
Chainlink (Base Sepolia):
  ETH/USD Feed: 0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1
  LINK Token: 0xE4aB69C077896252FAFBD49EFD26B5D171A32410
  VRF Coordinator: [check docs]
  
x402 Facilitator:
  URL: https://x402.org/facilitator
  Network: Base Sepolia (eip155:84532)
```

---

## 5. REPOSITORY STRUCTURE

```
aegis-protocol/
├── README.md                      # Project overview, quick start
├── CLAUDE_CODE.md                 # THIS FILE - AI assistant reference
├── LICENSE                        # MIT License
├── .env.example                   # Environment template
├── .gitignore
│
├── packages/
│   ├── contracts/                 # Solidity smart contracts
│   │   ├── src/
│   │   │   ├── core/
│   │   │   │   ├── SentinelRegistry.sol
│   │   │   │   ├── CircuitBreaker.sol
│   │   │   │   ├── ThreatReport.sol
│   │   │   │   └── ReputationTracker.sol
│   │   │   ├── interfaces/
│   │   │   │   ├── ISentinelRegistry.sol
│   │   │   │   ├── ICircuitBreaker.sol
│   │   │   │   └── IThreatReport.sol
│   │   │   ├── payments/
│   │   │   │   └── AegisPayments.sol
│   │   │   └── mocks/
│   │   │       └── MockProtocol.sol
│   │   ├── test/
│   │   │   ├── SentinelRegistry.t.sol
│   │   │   ├── CircuitBreaker.t.sol
│   │   │   └── Integration.t.sol
│   │   ├── script/
│   │   │   ├── Deploy.s.sol
│   │   │   └── ConfigureCircuitBreaker.s.sol
│   │   ├── foundry.toml
│   │   └── package.json
│   │
│   ├── cre-workflows/             # [IMPLEMENTED] Chainlink CRE workflows
│   │   ├── project.yaml           # Global CRE project settings (RPCs, DON)
│   │   ├── secrets.yaml           # Secret mappings (AGENT_API_URL)
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── index.ts       # Config schema (zod), API response types
│   │   │   │   └── abis.ts        # Contract ABI definitions (viem parseAbi)
│   │   │   └── workflows/
│   │   │       ├── threatDetection/
│   │   │       │   ├── main.ts    # Cron: read TVL + price → detect → circuit breaker
│   │   │       │   ├── config.json # Deployed contract addresses + thresholds
│   │   │       │   └── workflow.yaml
│   │   │       ├── forensicAnalysis/
│   │   │       │   ├── main.ts    # Log trigger: CircuitBreakerTriggered → forensics
│   │   │       │   └── workflow.yaml
│   │   │       ├── healthCheck/
│   │   │       │   ├── main.ts    # 5min cron: API health + sentinel liveness
│   │   │       │   └── workflow.yaml
│   │   │       ├── ccipAlert/         # [NEW] Cross-chain alert propagation
│   │   │       │   ├── main.ts    # Log trigger → CCIP message to dest chain
│   │   │       │   └── workflow.yaml
│   │   │       └── vrfTieBreaker/      # [NEW] VRF-based vote tie-breaking
│   │   │           ├── main.ts    # VRF randomness → weighted sentinel selection
│   │   │           └── workflow.yaml
│   │   ├── tsconfig.json
│   │   └── package.json           # @chainlink/cre-sdk, viem, zod
│   │
│   ├── agents/                    # [LEGACY] TypeScript agent scaffolding (reference only)
│   │   └── ...                    # Replaced by agents-py/
│   │
│   ├── agents-py/                 # [IMPLEMENTED] Python AI Agents (CrewAI + FastAPI)
│   │   ├── pyproject.toml         # Hatchling build, deps: crewai, fastapi, web3, pydantic
│   │   ├── requirements.txt
│   │   ├── aegis/
│   │   │   ├── __init__.py
│   │   │   ├── config.py          # Constants, thresholds, ABIs, env vars
│   │   │   ├── models.py          # Pydantic v2 models (ThreatLevel, ThreatAssessment, etc.)
│   │   │   ├── utils.py           # Helpers (calculate_change_percent, wei_to_ether, etc.)
│   │   │   ├── adapters/          # [NEW] Protocol adapters for real DeFi data
│   │   │   │   ├── __init__.py    # AdapterRegistry, get_adapter(), protocol detection
│   │   │   │   ├── base.py        # BaseProtocolAdapter, TTLCache, TokenBalance, ProtocolEvent
│   │   │   │   ├── aave_v3.py     # AaveV3Adapter — TVL, reserves, Supply/Withdraw events
│   │   │   │   ├── uniswap_v3.py  # UniswapV3Adapter — pools, liquidity, Swap events
│   │   │   │   └── history.py     # [NEW] TVLHistoryStore, SQLiteTVLStore, HistoricalTVLTracker, anomaly detection
│   │   │   ├── sentinels/
│   │   │   │   ├── liquidity_sentinel.py   # monitor_tvl() + CrewAI Agent
│   │   │   │   ├── oracle_sentinel.py      # monitor_price_feeds() + CrewAI Agent
│   │   │   │   └── governance_sentinel.py  # analyze_proposal() + CrewAI Agent
│   │   │   ├── sherlock/
│   │   │   │   ├── __init__.py            # Module exports
│   │   │   │   ├── chain_sherlock.py      # trace_transaction() + CrewAI Agent
│   │   │   │   ├── tracer.py              # [NEW] ForensicTracer, TransactionGraph, known address DB
│   │   │   │   └── prompts.py             # Forensic analysis prompts
│   │   │   ├── coordinator/
│   │   │   │   ├── consensus.py           # reach_consensus() + weighted_consensus()
│   │   │   │   ├── aggregator.py          # SentinelAggregator class
│   │   │   │   └── crew.py               # run_detection_cycle() orchestration
│   │   │   ├── blockchain/
│   │   │   │   ├── web3_client.py         # Cached Web3 provider
│   │   │   │   ├── chainlink_feeds.py     # Chainlink price feed reads
│   │   │   │   └── contracts.py           # On-chain contract interaction
│   │   │   └── api/
│   │   │       ├── server.py              # FastAPI app (port 8000)
│   │   │       └── routes/
│   │   │           ├── detect.py          # POST /api/v1/detect
│   │   │           ├── sentinel.py        # GET /api/v1/sentinel/*
│   │   │           ├── forensics.py       # POST/GET /api/v1/forensics/*
│   │   │           └── health.py          # GET /api/v1/health
│   │   └── tests/
│   │       ├── test_consensus.py          # 7 tests (2/3 majority + weighted)
│   │       ├── test_sentinels.py          # 11 tests (all 3 sentinels)
│   │       ├── test_api.py                # 7 tests (FastAPI endpoints)
│   │       ├── test_adapters.py           # 21 tests (cache, models, adapters, registry, crew)
│   │       ├── test_tracer.py             # [NEW] 26 tests (address ID, graphs, forensic tracer)
│   │       └── test_history.py            # [NEW] 24 tests (TVL snapshots, rolling avg, anomalies)
│   │
│   ├── api/                       # [IMPLEMENTED] TypeScript API (Hono, port 3000)
│   │   ├── src/
│   │   │   ├── index.ts           # Hono server entry point (v1.2.0)
│   │   │   ├── config.ts          # Env vars, contract addresses
│   │   │   ├── db/
│   │   │   │   └── index.ts       # SQLite (better-sqlite3) — alerts, protocols, forensic_reports
│   │   │   ├── routes/
│   │   │   │   ├── sentinel.ts    # GET /aggregate, /:id, POST /detect
│   │   │   │   ├── forensics.ts   # POST /, GET /, GET /:id
│   │   │   │   ├── reports.ts     # GET /protocol (on-chain reads)
│   │   │   │   ├── health.ts      # GET / (aggregated health)
│   │   │   │   ├── alerts.ts      # GET / (paginated), GET /:id, POST / (create + Telegram + SSE broadcast)
│   │   │   │   ├── protocols.ts   # GET /, GET /:addr, POST /, PATCH /:addr, GET /:addr/status
│   │   │   │   ├── ws.ts          # SSE real-time alert stream (/api/v1/ws)
│   │   │   │   └── docs.ts        # OpenAPI 3.1 spec + Swagger UI (/api/v1/docs)
│   │   │   ├── middleware/
│   │   │   │   ├── x402Payment.ts # HTTP 402 payment gate
│   │   │   │   ├── auth.ts        # X-API-Key authentication
│   │   │   │   ├── rateLimit.ts   # Sliding-window IP rate limiter (100 req/min)
│   │   │   │   └── cors.ts
│   │   │   └── services/
│   │   │       ├── agentProxy.ts  # HTTP client to Python FastAPI
│   │   │       ├── contractReader.ts  # ethers.js v6 on-chain reads
│   │   │       └── telegram.ts    # Telegram Bot API notifications
│   │   ├── data/                  # SQLite database (auto-created, gitignored)
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── frontend/                  # [IMPLEMENTED] React dashboard (Vite + Tailwind)
│       ├── src/
│       │   ├── main.tsx           # Entry + React Query provider
│       │   ├── App.tsx            # Main dashboard layout
│       │   ├── index.css          # Tailwind imports
│       │   ├── components/
│       │   │   ├── layout/Header.tsx
│       │   │   ├── dashboard/ThreatDashboard.tsx
│       │   │   ├── dashboard/SystemStatus.tsx
│       │   │   ├── sentinels/SentinelCard.tsx
│       │   │   ├── sentinels/ConsensusView.tsx
│       │   │   ├── protocol/CircuitBreakerStatus.tsx
│       │   │   └── common/ThreatBadge.tsx, Loading.tsx
│       │   ├── hooks/
│       │   │   ├── useSentinels.ts  # Polls /sentinel/aggregate (5s)
│       │   │   └── useHealth.ts     # Polls /health (10s)
│       │   ├── lib/
│       │   │   ├── api.ts           # Fetch wrapper to TS API
│       │   │   └── constants.ts     # Colors, labels
│       │   └── types/index.ts
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── package.json
│
├── scripts/
│   ├── run-demo.sh                # Start all 3 services + open browser
│   └── simulate-exploit.ts        # Simulate reentrancy attack
│
├── demo/
│   └── exploit-scenarios/
│       └── reentrancy-demo.json   # 9-step demo scenario
│
├── turbo.json                     # Turborepo config
├── pnpm-workspace.yaml
└── package.json                   # Root package.json
```

---

## 6. CORE COMPONENTS DEEP DIVE

### 6.1 Liquidity Sentinel

**Purpose**: Monitor protocol liquidity for anomalies indicating potential exploits.

**What It Monitors**:

| Metric | Threshold | Threat Level |
|--------|-----------|--------------|
| TVL drop in 5 min | >= 20% | CRITICAL |
| TVL drop in 5 min | >= 10% | HIGH |
| TVL drop in 5 min | >= 5% | MEDIUM |

**Implementation** (`packages/agents-py/aegis/sentinels/liquidity_sentinel.py`):

```python
def monitor_tvl(
    protocol_address: str,
    current_tvl: int,
    previous_tvl: int | None = None,
) -> ThreatAssessment:
    """Monitor Total Value Locked for anomalies indicating potential exploits.
    Uses the same thresholds as the TypeScript implementation:
    - >= 20% drop -> CRITICAL (confidence 0.95, CIRCUIT_BREAKER)
    - >= 10% drop -> HIGH (confidence 0.9, ALERT)
    - >= 5% drop  -> MEDIUM (confidence 0.8, ALERT)
    """
```

### 6.2 Oracle Sentinel

**Purpose**: Monitor price feeds for manipulation or staleness.

**What It Monitors**:

| Metric | Threshold | Threat Level |
|--------|-----------|--------------|
| Price deviation from Chainlink | > 5% | CRITICAL |
| Price deviation from Chainlink | > 2% | HIGH |
| Feed staleness | > 1 hour | HIGH |
| Feed staleness | > 30 min | MEDIUM |

**Implementation** (`packages/agents-py/aegis/sentinels/oracle_sentinel.py`):

```python
def monitor_price_feeds(
    protocol_price: float,
    chainlink_data: PriceFeedData,
) -> ThreatAssessment:
    """Monitor price feeds for manipulation or staleness.
    Compares protocol's internal price against Chainlink Data Feeds.
    Uses ThreatLevel.severity() for proper enum ordering.
    """
```

### 6.3 Governance Sentinel

**Purpose**: Monitor governance proposals for malicious actions.

**What It Monitors**:

| Metric | Threat Level |
|--------|--------------|
| Suspicious function call (transferOwnership, upgradeTo, etc.) | HIGH |
| Unusually short voting period (< 100 blocks) | HIGH |
| Flash loan voting detected | CRITICAL |

**Implementation** (`packages/agents-py/aegis/sentinels/governance_sentinel.py`):

```python
SUSPICIOUS_SIGNATURES = [
    "transferOwnership(address)", "upgradeTo(address)",
    "upgradeToAndCall(address,bytes)", "setAdmin(address)",
    "grantRole(bytes32,address)", "pause()",
]

def analyze_proposal(proposal: GovernanceProposal) -> ThreatAssessment:
    """Analyze a governance proposal for malicious intent.
    Checks for suspicious function calls and short voting periods.
    """
```

### 6.4 Consensus Coordinator

**Purpose**: Aggregate sentinel assessments and enforce 2/3 consensus rule.

**Implementation** (`packages/agents-py/aegis/coordinator/consensus.py`):

```python
def reach_consensus(votes: list[SentinelVote]) -> ConsensusResult:
    """Reach consensus among sentinel votes using 2/3 majority rule.
    Requires >= 2 votes. Threshold: 2/3 (0.6666...).
    CRITICAL consensus -> CIRCUIT_BREAKER
    HIGH/MEDIUM consensus -> ALERT
    """

def weighted_consensus(votes: list[SentinelVote]) -> ConsensusResult:
    """Weighted consensus considering confidence scores.
    Higher confidence votes carry more weight.
    """
```

### 6.5 ChainSherlock

**Purpose**: Real-time forensic analysis when threats are detected.

**Capabilities**:

1. **Transaction Graph Analysis**: Trace the full call stack of attack transactions
2. **Vulnerability Classification**: Identify the type of exploit (reentrancy, price manipulation, etc.)
3. **Fund Tracking**: Follow where stolen funds move
4. **Report Generation**: Create actionable, structured reports

**Implementation** (`packages/agents-py/aegis/sherlock/chain_sherlock.py`):

```python
def trace_transaction(tx_hash: str) -> TransactionTrace:
    """Trace a transaction using debug_traceTransaction (callTracer).
    Parses internal calls and extracts ERC-20 Transfer events.
    """

def analyze_trace(trace: TransactionTrace, protocol: str) -> ForensicReport:
    """Analyze a transaction trace and generate a forensic report.
    Uses Claude AI to classify the attack type and generate recommendations.
    """
```

### 6.6 FastAPI Agent Server

**Purpose**: HTTP bridge between CRE workflows / TS API and Python agents.

**Endpoints** (port 8000):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/detect` | POST | Run full detection cycle (3 sentinels → consensus) |
| `/api/v1/sentinel/aggregate` | GET | All sentinel assessments + consensus result |
| `/api/v1/sentinel/{id}` | GET | Single sentinel status |
| `/api/v1/forensics` | POST | Run ChainSherlock forensic analysis |
| `/api/v1/forensics/{id}` | GET | Get forensic report |
| `/api/v1/forensics` | GET | List all forensic reports |
| `/api/v1/health` | GET | System health check |

---

## 7. CHAINLINK SERVICES INTEGRATION

### 7.1 CRE (Chainlink Runtime Environment)

**What**: Workflow orchestration layer with BFT consensus verification.

**Our Usage**:
- Execute detection workflows with verifiable outputs
- Trigger circuit breakers with consensus
- Generate signed reports

**Setup**:
```bash
# Install CRE CLI
curl -sSL https://cre.chain.link/install.sh | bash

# Initialize workflow
cre init aegis-threat-detection

# Simulate workflow
cre workflow simulate --broadcast

# Deploy workflow
cre workflow deploy --network base-sepolia
```

**Workflow Structure**:
```typescript
// packages/cre-workflows/src/workflows/threatDetection.workflow.ts

import { 
  Workflow, 
  Trigger, 
  Capability,
  ConsensusConfig 
} from "@chainlink/cre-sdk";

export const threatDetectionWorkflow: Workflow = {
  name: "aegis-threat-detection",
  version: "1.0.0",
  
  triggers: [
    {
      type: "cron",
      schedule: "*/30 * * * * *", // Every 30 seconds
      name: "scheduled-health-check"
    },
    {
      type: "http",
      path: "/detect",
      method: "POST",
      name: "on-demand-detection"
    }
  ],
  
  capabilities: [
    {
      type: "http",
      name: "fetch-sentinel-data",
      config: {
        url: "${SENTINEL_API_URL}/aggregate",
        method: "GET",
        headers: {
          "Authorization": "Bearer ${API_KEY}"
        }
      }
    },
    {
      type: "evm-read",
      name: "read-protocol-state",
      config: {
        chain: "base-sepolia",
        contract: "${PROTOCOL_ADDRESS}",
        method: "getTVL()"
      }
    },
    {
      type: "data-feeds",
      name: "get-eth-price",
      config: {
        feed: "ETH/USD",
        chain: "base-sepolia"
      }
    },
    {
      type: "evm-write",
      name: "trigger-circuit-breaker",
      config: {
        chain: "base-sepolia",
        contract: "${CIRCUIT_BREAKER_ADDRESS}",
        method: "pause(bytes32,uint8)",
        requiresConsensus: true
      }
    }
  ],
  
  consensus: {
    threshold: "2/3",
    timeout: 30000 // 30 seconds
  },
  
  logic: async (context) => {
    // 1. Fetch sentinel data
    const sentinelData = await context.capabilities["fetch-sentinel-data"]();
    
    // 2. Read on-chain state
    const protocolState = await context.capabilities["read-protocol-state"]();
    
    // 3. Get price data
    const ethPrice = await context.capabilities["get-eth-price"]();
    
    // 4. Analyze with AI
    const analysis = await analyzeWithAI({
      sentinelData,
      protocolState,
      ethPrice
    });
    
    // 5. If critical threat, trigger circuit breaker
    if (analysis.threatLevel === "CRITICAL" && analysis.confidence > 0.9) {
      await context.capabilities["trigger-circuit-breaker"](
        analysis.threatId,
        analysis.threatLevel
      );
    }
    
    // 6. Return signed report
    return {
      timestamp: Date.now(),
      threatLevel: analysis.threatLevel,
      confidence: analysis.confidence,
      details: analysis.details,
      actionTaken: analysis.threatLevel === "CRITICAL" ? "CIRCUIT_BREAKER" : "NONE"
    };
  }
};
```

### 7.2 Data Feeds

**What**: Decentralized price oracles.

**Our Usage**:
- Source of truth for price comparison
- Detect price manipulation in protocols
- Calculate USD value of exploits

```typescript
// packages/agents/src/plugins/chainlink-data-feeds/index.ts

import { ethers } from "ethers";

const AGGREGATOR_V3_ABI = [
  "function latestRoundData() view returns (uint80, int256, uint256, uint256, uint80)",
  "function decimals() view returns (uint8)"
];

export async function getChainlinkPrice(
  feedAddress: string,
  provider: ethers.Provider
): Promise<{ price: number; updatedAt: number; decimals: number }> {
  const feed = new ethers.Contract(feedAddress, AGGREGATOR_V3_ABI, provider);
  
  const [, answer, , updatedAt] = await feed.latestRoundData();
  const decimals = await feed.decimals();
  
  return {
    price: Number(answer) / Math.pow(10, decimals),
    updatedAt: Number(updatedAt),
    decimals
  };
}

// Base Sepolia feed addresses
export const FEEDS = {
  "ETH/USD": "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1",
  "BTC/USD": "0x0FB99723Aee6f420beAD13e6bBB79b7E6F034298",
  "LINK/USD": "0xb113F5A928BCfF189C998ab20d753a47F9dE5A61"
};
```

### 7.3 Data Streams

**What**: Real-time data delivery with sub-second latency.

**Our Usage**:
- Detect flash loan attacks in real-time
- Monitor rapid price movements
- High-frequency anomaly detection

### 7.4 Automation (Keepers)

**What**: Decentralized job scheduler.

**Our Usage**:
- Scheduled health checks every 30 seconds
- Deadline enforcement for responses
- Automatic follow-up forensics

### 7.5 VRF (Verifiable Random Function)

**What**: Provably fair random number generation.

**Our Usage**:
- Fair selection of tie-breaker sentinel when 1-1 split
- Random audit selection for sentinel accuracy verification

### 7.6 CCIP (Cross-Chain Interoperability Protocol)

**What**: Secure cross-chain messaging.

**Our Usage**:
- Propagate threat alerts to all chains where protocol is deployed
- Trigger circuit breakers across multiple chains simultaneously
- Cross-chain fund tracking for forensics

---

## 8. DATA FLOW & SEQUENCES

### 8.1 Normal Monitoring Flow (No Threat)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ CRE     │     │Sentinels│     │ Chain   │
│ Cron    │     │  API    │     │         │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     │  trigger      │               │
     │──────────────>│               │
     │               │               │
     │               │  read state   │
     │               │──────────────>│
     │               │               │
     │               │  state data   │
     │               │<──────────────│
     │               │               │
     │  sentinel     │               │
     │  analysis     │               │
     │<──────────────│               │
     │               │               │
     │  threat: NONE │               │
     │  (no action)  │               │
     │               │               │
     ▼               ▼               ▼
```

### 8.2 Threat Detection Flow

```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  CRE    │  │Sentinels│  │Consensus│  │ Circuit │  │Sherlock │
│ Trigger │  │  (3x)   │  │  Coord  │  │ Breaker │  │         │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │            │
     │  analyze   │            │            │            │
     │───────────>│            │            │            │
     │            │            │            │            │
     │  3 votes:  │            │            │            │
     │  CRITICAL, │            │            │            │
     │  CRITICAL, │            │            │            │
     │  HIGH      │            │            │            │
     │<───────────│            │            │            │
     │            │            │            │            │
     │  aggregate │            │            │            │
     │  votes     │            │            │            │
     │───────────────────────>│            │            │
     │            │            │            │            │
     │  consensus:│            │            │            │
     │  CRITICAL  │            │            │            │
     │  (2/3)     │            │            │            │
     │<───────────────────────│            │            │
     │            │            │            │            │
     │  trigger   │            │            │            │
     │  pause()   │            │            │            │
     │──────────────────────────────────>│            │
     │            │            │            │            │
     │            │            │  paused   │            │
     │            │            │<──────────│            │
     │            │            │            │            │
     │  start     │            │            │            │
     │  forensics │            │            │            │
     │─────────────────────────────────────────────────>│
     │            │            │            │            │
     │            │            │            │  analyze  │
     │            │            │            │  attack   │
     │            │            │            │<──────────│
     │            │            │            │            │
     │  forensics │            │            │            │
     │  report    │            │            │            │
     │<─────────────────────────────────────────────────│
     │            │            │            │            │
     ▼            ▼            ▼            ▼            ▼
```

### 8.3 x402 Payment Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │     │  AEGIS  │     │  x402   │     │  Base   │
│         │     │   API   │     │Facilit. │     │  Chain  │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     │  GET /report  │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │  402 Payment  │               │               │
     │  Required     │               │               │
     │  {amount: $1} │               │               │
     │<──────────────│               │               │
     │               │               │               │
     │  Sign EIP-712 │               │               │
     │  payment      │               │               │
     │               │               │               │
     │  GET /report  │               │               │
     │  X-PAYMENT:   │               │               │
     │  {signature}  │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │               │  verify &     │               │
     │               │  settle       │               │
     │               │──────────────>│               │
     │               │               │               │
     │               │               │  transfer     │
     │               │               │  USDC         │
     │               │               │──────────────>│
     │               │               │               │
     │               │  confirmed    │               │
     │               │<──────────────│               │
     │               │               │               │
     │  200 OK       │               │               │
     │  {report}     │               │               │
     │<──────────────│               │               │
     │               │               │               │
     ▼               ▼               ▼               ▼
```

---

## 9. SMART CONTRACTS SPECIFICATION

### 9.1 SentinelRegistry.sol

**Purpose**: Register and manage sentinel agents with ERC-8004 compatibility.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SentinelRegistry
 * @notice Registry for AEGIS sentinel agents, ERC-8004 compatible
 * @dev Each sentinel is represented as an NFT with metadata URI
 */
contract SentinelRegistry is ERC721URIStorage, Ownable {
    
    // ============ State Variables ============
    
    uint256 private _nextTokenId;
    
    // Sentinel type enum
    enum SentinelType { LIQUIDITY, ORACLE, GOVERNANCE, SHERLOCK }
    
    // Sentinel data
    struct Sentinel {
        SentinelType sentinelType;
        address operator;       // Address that operates the sentinel
        bool active;
        uint256 registeredAt;
        uint256 lastActiveAt;
    }
    
    // Mapping from token ID to sentinel data
    mapping(uint256 => Sentinel) public sentinels;
    
    // Mapping from operator to their sentinel IDs
    mapping(address => uint256[]) public operatorSentinels;
    
    // ============ Events ============
    
    event SentinelRegistered(
        uint256 indexed tokenId,
        SentinelType sentinelType,
        address indexed operator,
        string metadataUri
    );
    
    event SentinelDeactivated(uint256 indexed tokenId);
    event SentinelReactivated(uint256 indexed tokenId);
    event SentinelHeartbeat(uint256 indexed tokenId, uint256 timestamp);
    
    // ============ Constructor ============
    
    constructor() ERC721("AEGIS Sentinel", "AEGIS") Ownable(msg.sender) {}
    
    // ============ External Functions ============
    
    /**
     * @notice Register a new sentinel
     * @param sentinelType Type of sentinel (LIQUIDITY, ORACLE, GOVERNANCE, SHERLOCK)
     * @param operator Address that will operate the sentinel
     * @param metadataUri URI to sentinel metadata (ERC-8004 registration file)
     * @return tokenId The ID of the newly registered sentinel
     */
    function registerSentinel(
        SentinelType sentinelType,
        address operator,
        string calldata metadataUri
    ) external onlyOwner returns (uint256 tokenId) {
        tokenId = _nextTokenId++;
        
        _mint(operator, tokenId);
        _setTokenURI(tokenId, metadataUri);
        
        sentinels[tokenId] = Sentinel({
            sentinelType: sentinelType,
            operator: operator,
            active: true,
            registeredAt: block.timestamp,
            lastActiveAt: block.timestamp
        });
        
        operatorSentinels[operator].push(tokenId);
        
        emit SentinelRegistered(tokenId, sentinelType, operator, metadataUri);
    }
    
    /**
     * @notice Record sentinel activity (heartbeat)
     * @param tokenId The sentinel's token ID
     */
    function heartbeat(uint256 tokenId) external {
        require(sentinels[tokenId].operator == msg.sender, "Not operator");
        require(sentinels[tokenId].active, "Sentinel not active");
        
        sentinels[tokenId].lastActiveAt = block.timestamp;
        
        emit SentinelHeartbeat(tokenId, block.timestamp);
    }
    
    /**
     * @notice Deactivate a sentinel
     * @param tokenId The sentinel's token ID
     */
    function deactivate(uint256 tokenId) external onlyOwner {
        require(sentinels[tokenId].active, "Already inactive");
        sentinels[tokenId].active = false;
        emit SentinelDeactivated(tokenId);
    }
    
    /**
     * @notice Get all active sentinels
     * @return Array of active sentinel token IDs
     */
    function getActiveSentinels() external view returns (uint256[] memory) {
        uint256 activeCount = 0;
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (sentinels[i].active) activeCount++;
        }
        
        uint256[] memory active = new uint256[](activeCount);
        uint256 index = 0;
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (sentinels[i].active) {
                active[index++] = i;
            }
        }
        
        return active;
    }
    
    /**
     * @notice Check if sentinel is active and recently alive
     * @param tokenId The sentinel's token ID
     * @param maxInactivity Maximum seconds since last heartbeat
     * @return bool True if sentinel is active and alive
     */
    function isAlive(uint256 tokenId, uint256 maxInactivity) external view returns (bool) {
        Sentinel memory s = sentinels[tokenId];
        return s.active && (block.timestamp - s.lastActiveAt <= maxInactivity);
    }
}
```

### 9.2 CircuitBreaker.sol

**Purpose**: Emergency pause functionality for protected protocols.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title CircuitBreaker
 * @notice Emergency pause controller for DeFi protocols
 * @dev Can be triggered by CRE workflows with consensus verification
 */
contract CircuitBreaker is AccessControl, ReentrancyGuard {
    
    // ============ Roles ============
    
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UNPAUSER_ROLE = keccak256("UNPAUSER_ROLE");
    bytes32 public constant CRE_WORKFLOW_ROLE = keccak256("CRE_WORKFLOW_ROLE");
    
    // ============ State Variables ============
    
    // Threat levels
    enum ThreatLevel { NONE, LOW, MEDIUM, HIGH, CRITICAL }
    
    // Circuit breaker state
    struct BreakerState {
        bool paused;
        ThreatLevel threatLevel;
        bytes32 threatId;
        uint256 pausedAt;
        uint256 cooldownEnds;
        string reason;
    }
    
    // Protocol address => breaker state
    mapping(address => BreakerState) public protocolStates;
    
    // Registered protocols
    address[] public registeredProtocols;
    mapping(address => bool) public isRegistered;
    
    // Configuration
    uint256 public cooldownPeriod = 1 hours;
    uint256 public autoPauseThreshold = 3; // Number of HIGH alerts before auto-pause
    
    // Alert tracking
    mapping(address => uint256) public recentHighAlerts;
    mapping(address => uint256) public lastAlertTimestamp;
    
    // ============ Events ============
    
    event ProtocolRegistered(address indexed protocol);
    event CircuitBreakerTriggered(
        address indexed protocol,
        bytes32 indexed threatId,
        ThreatLevel threatLevel,
        string reason
    );
    event CircuitBreakerReset(address indexed protocol, address indexed resetBy);
    event ThreatAlertRecorded(
        address indexed protocol,
        bytes32 indexed threatId,
        ThreatLevel threatLevel
    );
    
    // ============ Constructor ============
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(UNPAUSER_ROLE, msg.sender);
    }
    
    // ============ External Functions ============
    
    /**
     * @notice Register a protocol for monitoring
     * @param protocol Address of the protocol to protect
     */
    function registerProtocol(address protocol) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(!isRegistered[protocol], "Already registered");
        
        registeredProtocols.push(protocol);
        isRegistered[protocol] = true;
        
        protocolStates[protocol] = BreakerState({
            paused: false,
            threatLevel: ThreatLevel.NONE,
            threatId: bytes32(0),
            pausedAt: 0,
            cooldownEnds: 0,
            reason: ""
        });
        
        emit ProtocolRegistered(protocol);
    }
    
    /**
     * @notice Trigger circuit breaker (called by CRE workflow)
     * @param protocol Address of the protocol to pause
     * @param threatId Unique identifier for the threat
     * @param threatLevel Severity level
     * @param reason Human-readable reason
     */
    function triggerBreaker(
        address protocol,
        bytes32 threatId,
        ThreatLevel threatLevel,
        string calldata reason
    ) external onlyRole(CRE_WORKFLOW_ROLE) nonReentrant {
        require(isRegistered[protocol], "Protocol not registered");
        require(!protocolStates[protocol].paused, "Already paused");
        require(threatLevel >= ThreatLevel.HIGH, "Threat level too low for pause");
        
        protocolStates[protocol] = BreakerState({
            paused: true,
            threatLevel: threatLevel,
            threatId: threatId,
            pausedAt: block.timestamp,
            cooldownEnds: block.timestamp + cooldownPeriod,
            reason: reason
        });
        
        // Call the protocol's pause function if it exists
        _attemptProtocolPause(protocol);
        
        emit CircuitBreakerTriggered(protocol, threatId, threatLevel, reason);
    }
    
    /**
     * @notice Record a threat alert without pausing
     * @param protocol Address of the affected protocol
     * @param threatId Unique identifier for the threat
     * @param threatLevel Severity level
     */
    function recordAlert(
        address protocol,
        bytes32 threatId,
        ThreatLevel threatLevel
    ) external onlyRole(CRE_WORKFLOW_ROLE) {
        require(isRegistered[protocol], "Protocol not registered");
        
        // Reset alert count if last alert was > 1 hour ago
        if (block.timestamp - lastAlertTimestamp[protocol] > 1 hours) {
            recentHighAlerts[protocol] = 0;
        }
        
        // Track HIGH alerts
        if (threatLevel >= ThreatLevel.HIGH) {
            recentHighAlerts[protocol]++;
            lastAlertTimestamp[protocol] = block.timestamp;
            
            // Auto-pause if threshold reached
            if (recentHighAlerts[protocol] >= autoPauseThreshold) {
                _autoPause(protocol, threatId);
            }
        }
        
        emit ThreatAlertRecorded(protocol, threatId, threatLevel);
    }
    
    /**
     * @notice Reset circuit breaker (manual intervention)
     * @param protocol Address of the protocol to unpause
     */
    function resetBreaker(address protocol) external onlyRole(UNPAUSER_ROLE) {
        require(protocolStates[protocol].paused, "Not paused");
        require(
            block.timestamp >= protocolStates[protocol].cooldownEnds,
            "Cooldown not finished"
        );
        
        protocolStates[protocol].paused = false;
        protocolStates[protocol].threatLevel = ThreatLevel.NONE;
        recentHighAlerts[protocol] = 0;
        
        // Call the protocol's unpause function if it exists
        _attemptProtocolUnpause(protocol);
        
        emit CircuitBreakerReset(protocol, msg.sender);
    }
    
    /**
     * @notice Check if a protocol is paused
     * @param protocol Address of the protocol
     * @return bool True if paused
     */
    function isPaused(address protocol) external view returns (bool) {
        return protocolStates[protocol].paused;
    }
    
    /**
     * @notice Get full breaker state for a protocol
     * @param protocol Address of the protocol
     */
    function getBreakerState(address protocol) external view returns (BreakerState memory) {
        return protocolStates[protocol];
    }
    
    // ============ Internal Functions ============
    
    function _autoPause(address protocol, bytes32 threatId) internal {
        if (!protocolStates[protocol].paused) {
            protocolStates[protocol] = BreakerState({
                paused: true,
                threatLevel: ThreatLevel.HIGH,
                threatId: threatId,
                pausedAt: block.timestamp,
                cooldownEnds: block.timestamp + cooldownPeriod,
                reason: "Auto-paused: multiple HIGH alerts"
            });
            
            _attemptProtocolPause(protocol);
            
            emit CircuitBreakerTriggered(
                protocol,
                threatId,
                ThreatLevel.HIGH,
                "Auto-paused: multiple HIGH alerts"
            );
        }
    }
    
    function _attemptProtocolPause(address protocol) internal {
        // Try to call pause() on the protocol
        // This is a best-effort call - protocol must grant us permission
        (bool success,) = protocol.call(abi.encodeWithSignature("pause()"));
        // We don't revert if this fails - the protocol might not have pause()
    }
    
    function _attemptProtocolUnpause(address protocol) internal {
        (bool success,) = protocol.call(abi.encodeWithSignature("unpause()"));
    }
}
```

### 9.3 ThreatReport.sol

**Purpose**: Store consensus-verified threat reports on-chain.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ThreatReport
 * @notice Immutable storage for AEGIS threat reports
 * @dev Reports are submitted by CRE workflows with consensus verification
 */
contract ThreatReport {
    
    // ============ Structs ============
    
    struct Report {
        bytes32 reportId;
        address protocol;
        uint8 threatLevel;      // 0-4 mapping to enum
        uint256 timestamp;
        uint256 blockNumber;
        bytes32 consensusHash;  // Hash of sentinel votes
        string ipfsHash;        // Full report stored on IPFS
        bool actionTaken;       // Was circuit breaker triggered?
    }
    
    struct SentinelVote {
        uint256 sentinelId;
        uint8 threatLevel;
        uint256 confidence;     // Basis points (9500 = 95%)
        bytes signature;
    }
    
    // ============ State Variables ============
    
    // Report ID => Report
    mapping(bytes32 => Report) public reports;
    
    // Report ID => Sentinel votes
    mapping(bytes32 => SentinelVote[]) public reportVotes;
    
    // Protocol => Report IDs
    mapping(address => bytes32[]) public protocolReports;
    
    // All report IDs (for enumeration)
    bytes32[] public allReports;
    
    // Authorized CRE workflow address
    address public creWorkflow;
    
    // ============ Events ============
    
    event ReportSubmitted(
        bytes32 indexed reportId,
        address indexed protocol,
        uint8 threatLevel,
        bool actionTaken
    );
    
    // ============ Constructor ============
    
    constructor(address _creWorkflow) {
        creWorkflow = _creWorkflow;
    }
    
    // ============ External Functions ============
    
    /**
     * @notice Submit a new threat report
     * @param protocol Affected protocol address
     * @param threatLevel Consensus threat level
     * @param consensusHash Hash of all sentinel votes
     * @param ipfsHash IPFS hash of full report
     * @param actionTaken Whether circuit breaker was triggered
     * @param votes Array of sentinel votes
     */
    function submitReport(
        address protocol,
        uint8 threatLevel,
        bytes32 consensusHash,
        string calldata ipfsHash,
        bool actionTaken,
        SentinelVote[] calldata votes
    ) external returns (bytes32 reportId) {
        require(msg.sender == creWorkflow, "Only CRE workflow");
        
        reportId = keccak256(abi.encodePacked(
            protocol,
            block.timestamp,
            block.number,
            consensusHash
        ));
        
        require(reports[reportId].timestamp == 0, "Report exists");
        
        reports[reportId] = Report({
            reportId: reportId,
            protocol: protocol,
            threatLevel: threatLevel,
            timestamp: block.timestamp,
            blockNumber: block.number,
            consensusHash: consensusHash,
            ipfsHash: ipfsHash,
            actionTaken: actionTaken
        });
        
        for (uint i = 0; i < votes.length; i++) {
            reportVotes[reportId].push(votes[i]);
        }
        
        protocolReports[protocol].push(reportId);
        allReports.push(reportId);
        
        emit ReportSubmitted(reportId, protocol, threatLevel, actionTaken);
    }
    
    /**
     * @notice Get reports for a protocol
     * @param protocol Protocol address
     * @param limit Max reports to return
     * @return Array of report IDs
     */
    function getProtocolReports(
        address protocol,
        uint256 limit
    ) external view returns (bytes32[] memory) {
        bytes32[] storage all = protocolReports[protocol];
        uint256 count = limit < all.length ? limit : all.length;
        
        bytes32[] memory result = new bytes32[](count);
        for (uint i = 0; i < count; i++) {
            result[i] = all[all.length - 1 - i]; // Most recent first
        }
        
        return result;
    }
    
    /**
     * @notice Get votes for a report
     * @param reportId Report ID
     */
    function getReportVotes(bytes32 reportId) external view returns (SentinelVote[] memory) {
        return reportVotes[reportId];
    }
}
```

### 9.4 ReputationTracker.sol

**Purpose**: Track sentinel accuracy and reliability over time.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ReputationTracker
 * @notice ERC-8004 compatible reputation tracking for AEGIS sentinels
 */
contract ReputationTracker {
    
    // ============ Structs ============
    
    struct ReputationScore {
        uint256 totalPredictions;
        uint256 correctPredictions;
        uint256 falsePositives;
        uint256 missedThreats;
        uint256 lastUpdated;
    }
    
    struct FeedbackEntry {
        uint256 sentinelId;
        bytes32 reportId;
        bool wasCorrect;
        string feedbackUri;     // IPFS link to detailed feedback
        uint256 timestamp;
    }
    
    // ============ State Variables ============
    
    // Sentinel ID => Reputation
    mapping(uint256 => ReputationScore) public reputations;
    
    // Sentinel ID => Feedback entries
    mapping(uint256 => FeedbackEntry[]) public feedbackHistory;
    
    // Authorized updaters
    mapping(address => bool) public authorizedUpdaters;
    
    address public owner;
    
    // ============ Events ============
    
    event ReputationUpdated(
        uint256 indexed sentinelId,
        bool wasCorrect,
        uint256 newAccuracy
    );
    
    event FeedbackSubmitted(
        uint256 indexed sentinelId,
        bytes32 indexed reportId,
        bool wasCorrect
    );
    
    // ============ Constructor ============
    
    constructor() {
        owner = msg.sender;
        authorizedUpdaters[msg.sender] = true;
    }
    
    // ============ External Functions ============
    
    /**
     * @notice Submit feedback for a sentinel's prediction
     * @param sentinelId The sentinel's token ID
     * @param reportId The report this feedback is for
     * @param wasCorrect Whether the prediction was correct
     * @param feedbackUri IPFS URI to detailed feedback
     */
    function submitFeedback(
        uint256 sentinelId,
        bytes32 reportId,
        bool wasCorrect,
        string calldata feedbackUri
    ) external {
        require(authorizedUpdaters[msg.sender], "Not authorized");
        
        ReputationScore storage rep = reputations[sentinelId];
        
        rep.totalPredictions++;
        if (wasCorrect) {
            rep.correctPredictions++;
        } else {
            rep.falsePositives++;
        }
        rep.lastUpdated = block.timestamp;
        
        feedbackHistory[sentinelId].push(FeedbackEntry({
            sentinelId: sentinelId,
            reportId: reportId,
            wasCorrect: wasCorrect,
            feedbackUri: feedbackUri,
            timestamp: block.timestamp
        }));
        
        emit FeedbackSubmitted(sentinelId, reportId, wasCorrect);
        emit ReputationUpdated(
            sentinelId,
            wasCorrect,
            getAccuracy(sentinelId)
        );
    }
    
    /**
     * @notice Record a missed threat (sentinel didn't detect it)
     * @param sentinelId The sentinel's token ID
     */
    function recordMissedThreat(uint256 sentinelId) external {
        require(authorizedUpdaters[msg.sender], "Not authorized");
        
        reputations[sentinelId].missedThreats++;
        reputations[sentinelId].lastUpdated = block.timestamp;
    }
    
    /**
     * @notice Get accuracy percentage for a sentinel
     * @param sentinelId The sentinel's token ID
     * @return Accuracy in basis points (9500 = 95%)
     */
    function getAccuracy(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];
        
        if (rep.totalPredictions == 0) {
            return 10000; // 100% if no predictions yet
        }
        
        return (rep.correctPredictions * 10000) / rep.totalPredictions;
    }
    
    /**
     * @notice Get reliability score (accounts for missed threats)
     * @param sentinelId The sentinel's token ID
     * @return Reliability in basis points
     */
    function getReliability(uint256 sentinelId) public view returns (uint256) {
        ReputationScore memory rep = reputations[sentinelId];
        
        uint256 totalOpportunities = rep.totalPredictions + rep.missedThreats;
        if (totalOpportunities == 0) {
            return 10000;
        }
        
        return (rep.correctPredictions * 10000) / totalOpportunities;
    }
    
    /**
     * @notice Add an authorized updater
     */
    function addUpdater(address updater) external {
        require(msg.sender == owner, "Only owner");
        authorizedUpdaters[updater] = true;
    }
}
```

---

## 10. CRE WORKFLOWS SPECIFICATION

### 10.1 Threat Detection Workflow

**File**: `packages/cre-workflows/src/workflows/threatDetection.workflow.ts`

**Triggers**:
- Cron: Every 30 seconds
- HTTP: On-demand via POST /detect

**Flow**:
1. Fetch sentinel assessments via HTTP capability
2. Read protocol state via EVM Read
3. Verify prices via Data Feeds
4. Aggregate votes and check consensus
5. If consensus on CRITICAL → trigger circuit breaker
6. Store report via EVM Write
7. Broadcast via CCIP if multi-chain

### 10.2 Forensic Analysis Workflow

**File**: `packages/cre-workflows/src/workflows/forensicAnalysis.workflow.ts`

**Triggers**:
- HTTP: POST /forensics (with x402 payment)
- LogTrigger: CircuitBreakerTriggered event

**Flow**:
1. Accept threat ID and transaction hash
2. Fetch transaction trace via HTTP
3. Analyze with AI for vulnerability classification
4. Track fund movements
5. Generate structured report
6. Store report hash on-chain
7. Upload full report to IPFS

### 10.3 Health Check Workflow

**File**: `packages/cre-workflows/src/workflows/healthCheck.workflow.ts`

**Triggers**:
- Cron: Every 5 minutes

**Flow**:
1. Check all registered sentinels for liveness
2. Verify CRE connectivity
3. Test Data Feeds availability
4. Log health status

---

## 11. AI AGENT SPECIFICATION (Python/CrewAI - IMPLEMENTED)

### 11.1 Agent Architecture

Agents are implemented as **CrewAI Agent** instances with lazy initialization (to avoid requiring LLM API keys at import time). Each sentinel has:
- A **pure Python detection function** (no LLM needed) for threshold-based analysis
- A **CrewAI Agent** (requires LLM at runtime) for AI-enhanced analysis

```python
# packages/agents-py/aegis/sentinels/liquidity_sentinel.py

# Pure detection (no LLM)
def monitor_tvl(protocol_address, current_tvl, previous_tvl) -> ThreatAssessment: ...

# CrewAI Agent (lazy-loaded, requires ANTHROPIC_API_KEY)
def get_liquidity_sentinel() -> Agent:
    return Agent(
        role="Liquidity Sentinel",
        goal="Monitor DeFi protocol liquidity pools for anomalies...",
        backstory="You are the AEGIS Liquidity Sentinel...",
    )
```

### 11.2 Agent Personalities (CrewAI role/goal/backstory)

| Agent | Role | Specialization |
|-------|------|----------------|
| Liquidity Sentinel | Liquidity pool monitor | TVL drops, flash loans, withdrawal patterns |
| Oracle Sentinel | Price feed monitor | Chainlink deviations, feed staleness |
| Governance Sentinel | Proposal analyzer | Suspicious calldata, short voting periods |
| ChainSherlock | Forensic investigator | Transaction tracing, attack classification |

### 11.3 AI Prompts

Forensic analysis prompts are in `packages/agents-py/aegis/sherlock/prompts.py`:

- **FORENSIC_ANALYSIS_PROMPT**: Analyzes transaction traces, classifies attack types
- **REPORT_GENERATION_PROMPT**: Generates structured ForensicReport JSON

### 11.4 Data Models (Pydantic v2)

All models in `packages/agents-py/aegis/models.py`:

```python
class ThreatLevel(str, Enum):       # NONE, LOW, MEDIUM, HIGH, CRITICAL
class SentinelType(str, Enum):      # LIQUIDITY, ORACLE, GOVERNANCE, SHERLOCK
class ActionRecommendation(str, Enum):  # NONE, ALERT, INVESTIGATE, CIRCUIT_BREAKER
class AttackType(str, Enum):        # REENTRANCY, PRICE_MANIPULATION, FLASH_LOAN, etc.

class ThreatAssessment(BaseModel):  # threat_level, confidence, details, indicators
class SentinelVote(BaseModel):      # sentinel_id, threat_level, confidence
class ConsensusResult(BaseModel):   # consensus_reached, final_threat_level, agreement_ratio
class ForensicReport(BaseModel):    # report_id, attack_classification, attack_flow, etc.
```

### 11.5 Test Coverage

96 tests passing (`cd packages/agents-py && python -m pytest tests/ -v`):
- **test_consensus.py** (7): insufficient votes, 2/3 critical, unanimous, split, high alert, 2-sentinel, weighted
- **test_sentinels.py** (11): TVL drops (initial/critical/high/medium/none), oracle deviations (critical/high/stale/none), governance (clean/short)
- **test_api.py** (7): root, health, sentinel aggregate, sentinel by ID, sentinel 404, forensics list, forensics 404
- **test_adapters.py** (21): TTLCache (7), TokenBalance (2), ProtocolEvent (1), ProtocolMetricsSnapshot (1), AdapterRegistry (1), AaveV3Adapter (2), UniswapV3Adapter (2), get_adapter factory (3), crew integration (2)
- **test_tracer.py** (26): address identification (8), graph node/edge (4), TransactionGraph (2), ForensicTracer (3), ArchiveNodeClient (3), analysis detection (2), known addresses DB (4)
- **test_history.py** (24): TVLSnapshot (2), RollingAverage (1), TVLAnomaly (1), TVLHistoryStore (6), SQLiteTVLStore (4), HistoricalTVLTracker (7), factory functions (2), integration (2)

---

## 12. x402 PAYMENT INTEGRATION

### 12.1 Server-Side Middleware

```typescript
// packages/api/src/middleware/x402Payment.ts

import { paymentMiddleware, Network } from "@x402/express";
import { facilitatorUrl } from "@x402/evm";

export const aegisPaymentMiddleware = paymentMiddleware({
  "POST /forensics": {
    price: "$1.00",
    network: Network.BASE_SEPOLIA,
    config: {
      description: "AEGIS forensic analysis report"
    }
  },
  "GET /report/:id/full": {
    price: "$0.50",
    network: Network.BASE_SEPOLIA,
    config: {
      description: "Full threat report with details"
    }
  },
  "POST /subscribe": {
    price: "$100.00",
    network: Network.BASE_SEPOLIA,
    config: {
      description: "Monthly AEGIS monitoring subscription"
    }
  }
}, {
  facilitatorUrl: facilitatorUrl // https://x402.org/facilitator
});
```

### 12.2 Client-Side Payment

```typescript
// Example client using x402
import { wrapFetch } from "@x402/fetch";
import { privateKeyToAccount } from "viem/accounts";

const account = privateKeyToAccount(process.env.PRIVATE_KEY);
const x402Fetch = wrapFetch(fetch, account);

// This automatically handles 402 responses and payment
const response = await x402Fetch("https://aegis.api/forensics", {
  method: "POST",
  body: JSON.stringify({ txHash: "0x..." })
});

const report = await response.json();
```

---

## 13. ERC-8004 INTEGRATION

### 13.1 Agent Registration File

Each sentinel has an ERC-8004 compatible registration file:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "AEGIS Liquidity Sentinel #1",
  "description": "AI agent monitoring DeFi protocol liquidity for anomalies and potential exploits. Part of the AEGIS Protocol security network.",
  "image": "ipfs://QmXXX/liquidity-sentinel.png",
  "endpoints": {
    "a2a": {
      "enabled": true,
      "url": "https://aegis.api/agents/liquidity-1/a2a"
    },
    "mcp": {
      "enabled": false
    }
  },
  "evmChains": [
    {"name": "Base", "chainId": 8453},
    {"name": "Base Sepolia", "chainId": 84532}
  ],
  "capabilities": [
    "tvl_monitoring",
    "flash_loan_detection",
    "withdrawal_analysis"
  ],
  "supportedTrust": [
    "reputation",
    "validation"
  ],
  "pricing": {
    "model": "subscription",
    "currency": "USDC",
    "basePrice": "100.00",
    "period": "monthly"
  }
}
```

### 13.2 Reputation Integration

The ReputationTracker contract implements ERC-8004's Reputation Registry interface, allowing other agents and protocols to query sentinel reliability before trusting their assessments.

---

## 14. API SPECIFICATIONS

### 14.1 Sentinel API

```yaml
# Sentinel Aggregate Endpoint
GET /api/v1/sentinel/aggregate
Response:
  {
    "timestamp": 1706000000,
    "protocol": "0x...",
    "sentinels": [
      {
        "id": 1,
        "type": "LIQUIDITY",
        "assessment": {
          "threatLevel": "NONE",
          "confidence": 0.95,
          "details": "..."
        }
      },
      ...
    ],
    "consensus": {
      "reached": true,
      "threatLevel": "NONE",
      "agreementRatio": 1.0
    }
  }

# Single Sentinel Status
GET /api/v1/sentinel/:id
Response:
  {
    "id": 1,
    "type": "LIQUIDITY",
    "status": "ACTIVE",
    "lastHeartbeat": 1706000000,
    "reputation": {
      "accuracy": 9500,
      "reliability": 9200,
      "totalPredictions": 1000
    }
  }
```

### 14.2 Forensics API

```yaml
# Request Forensic Analysis (x402 gated)
POST /api/v1/forensics
Headers:
  X-PAYMENT: <base64 encoded PaymentPayload>
Body:
  {
    "txHash": "0x...",
    "protocol": "0x...",
    "description": "Optional context"
  }
Response:
  {
    "reportId": "0x...",
    "status": "PROCESSING",
    "estimatedTime": 60
  }

# Get Forensic Report (x402 gated for full)
GET /api/v1/forensics/:reportId
Response:
  {
    "reportId": "0x...",
    "status": "COMPLETE",
    "summary": { ... },
    "fullReportUrl": "/api/v1/forensics/:reportId/full" // Requires payment
  }
```

### 14.3 Health API

```yaml
# System Health
GET /api/v1/health
Response:
  {
    "status": "HEALTHY",
    "sentinels": {
      "active": 3,
      "total": 3
    },
    "cre": {
      "connected": true,
      "lastWorkflow": 1706000000
    },
    "chainlink": {
      "dataFeeds": "AVAILABLE",
      "ccip": "AVAILABLE",
      "vrf": "AVAILABLE"
    }
  }
```

---

## 15. TESTING STRATEGY

### 15.1 Smart Contract Tests

```bash
# Run all contract tests
cd packages/contracts
forge test

# Run with verbosity
forge test -vvv

# Run specific test
forge test --match-test testCircuitBreakerTrigger

# Run with gas report
forge test --gas-report

# Run coverage
forge coverage
```

**Key Test Cases**:
- SentinelRegistry: registration, deactivation, heartbeat
- CircuitBreaker: trigger, reset, cooldown, auto-pause
- ThreatReport: submission, retrieval, vote verification
- ReputationTracker: feedback, accuracy calculation

### 15.2 Agent Tests (Python)

```bash
cd packages/agents-py
source venv/bin/activate

# Run all tests (25 passing)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_consensus.py -v
python -m pytest tests/test_sentinels.py -v
python -m pytest tests/test_api.py -v
```

**Test Coverage**:
- **test_consensus.py** (7): 2/3 majority, unanimous, split, weighted consensus
- **test_sentinels.py** (11): TVL drops, oracle deviations, governance proposals
- **test_api.py** (7): All FastAPI endpoints

### 15.3 CRE Workflow Tests

```bash
# Simulate workflow
cd packages/cre-workflows
cre workflow simulate threatDetection

# Test with broadcast
cre workflow simulate threatDetection --broadcast

# Run integration tests
pnpm test
```

### 15.4 E2E Tests

```bash
# Run full integration test
cd scripts
./run-e2e-test.sh

# This spins up:
# - Local Anvil fork
# - Mock protocol
# - Sentinel agents
# - Simulates exploit
# - Verifies detection and response
```

---

## 16. DEPLOYMENT GUIDE

### 16.1 Prerequisites

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install Node dependencies
pnpm install

# Set up Python virtual environment
cd packages/agents-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..

# Copy environment file
cp .env.example .env
# Fill in: DEPLOYER_PRIVATE_KEY, ANTHROPIC_API_KEY
```

### 16.2 Deploy Contracts

Contracts are deployed to Base Sepolia at:

| Contract | Address |
|---|---|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` |
| MockProtocol | `0x11887863b89F1bE23A650909135ffaCFab666803` |

To redeploy:

```bash
cd packages/contracts
forge script script/Deploy.s.sol:DeployAegis \
  --fork-url https://sepolia.base.org \
  --private-key 0x$DEPLOYER_PRIVATE_KEY \
  --broadcast --verify
```

### 16.3 Start All Services

```bash
bash scripts/run-demo.sh
```

Or start each individually:

```bash
# Terminal 1 — Python Agent API (port 8000)
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2 — TypeScript API (port 3000)
cd packages/api
npx tsx src/index.ts

# Terminal 3 — Frontend Dashboard (port 5173)
cd packages/frontend
pnpm dev
```

### 16.4 Open Dashboard

Navigate to **http://localhost:5173**. The dashboard auto-triggers a scan on first load.

### 16.5 Verification Checklist

- [x] Contracts deployed and verified on Base Sepolia
- [x] All sentinels operational (96 tests passing)
- [x] Frontend connected and displaying data
- [ ] CRE workflows deployed to Chainlink network
- [ ] x402 payments working (test with small amount)
- [ ] CCIP test message sent successfully

---

## 17. ENVIRONMENT VARIABLES

```bash
# Required
DEPLOYER_PRIVATE_KEY=<your-wallet-private-key>
ANTHROPIC_API_KEY=sk-ant-...

# Network
BASE_SEPOLIA_RPC=https://sepolia.base.org

# Deployed Contracts (Base Sepolia — already deployed)
SENTINEL_REGISTRY_ADDRESS=0xd34FC1ee378F342EFb92C0D334362B9E577b489f
CIRCUIT_BREAKER_ADDRESS=0xa0eE49660252B353830ADe5de0Ca9385647F85b5
THREAT_REPORT_ADDRESS=0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499
REPUTATION_TRACKER_ADDRESS=0x7970433B694f7fa6f8D511c7B20110ECd28db100
MOCK_PROTOCOL_ADDRESS=0x11887863b89F1bE23A650909135ffaCFab666803

# Chainlink (Base Sepolia)
CHAINLINK_ETH_USD_FEED=0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1
CHAINLINK_LINK_TOKEN=0xE4aB69C077896252FAFBD49EFD26B5D171A32410

# Services
AGENT_API_URL=http://localhost:8000
AGENT_API_PORT=8000
API_PORT=3000

# Optional
OPENAI_API_KEY=...         # Fallback LLM
ETHERSCAN_API_KEY=...      # Contract verification
BASESCAN_API_KEY=...       # Contract verification
X402_FACILITATOR_URL=https://x402.org/facilitator
AEGIS_PAYMENT_RECEIVER=0x...

# Telegram Notifications (Agent 4)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# API Authentication (Agent 4)
API_KEYS=aegis-dev-key-1,aegis-dev-key-2   # Comma-separated; empty = open access

# Database (Agent 4)
DATABASE_PATH=./data/aegis.db              # SQLite file path (auto-created)

# Rate Limiting (Agent 4)
RATE_LIMIT_MAX=100                         # Max requests per window (default 100)
RATE_LIMIT_WINDOW_MS=60000                 # Window length in ms (default 60000 = 1 min)
```

---

## 18. COMMON TASKS & COMMANDS

### Run All Services

```bash
bash scripts/run-demo.sh
```

### Contract Commands

```bash
cd packages/contracts

forge build                    # Compile contracts
forge test                     # Run tests (21 passing)
forge test -vvv                # Verbose output

# Deploy
forge script script/Deploy.s.sol:DeployAegis \
  --fork-url https://sepolia.base.org \
  --private-key 0x$DEPLOYER_PRIVATE_KEY \
  --broadcast --verify
```

### Python Agent Commands

```bash
cd packages/agents-py
source venv/bin/activate

python -m pytest tests/ -v                          # Run tests (96 passing)
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000  # Start API
curl http://localhost:8000/api/v1/health             # Check health
curl http://localhost:8000/docs                      # OpenAPI docs
```

### TypeScript API Commands

```bash
cd packages/api
npx tsx src/index.ts           # Start API (port 3000)
```

### Frontend Commands

```bash
cd packages/frontend
pnpm dev                       # Start dev server (port 5173)
pnpm build                     # Production build
```

### Demo Commands

```bash
bash scripts/run-demo.sh                  # Start all 3 services
npx tsx scripts/simulate-exploit.ts       # Simulate reentrancy attack
```

---

## 19. CODING STANDARDS

### TypeScript

```typescript
// Use explicit types
const threatLevel: ThreatLevel = "CRITICAL";

// Use interfaces for objects
interface SentinelConfig {
  id: number;
  type: SentinelType;
  endpoint: string;
}

// Use async/await over promises
async function fetchData(): Promise<Data> {
  const response = await fetch(url);
  return response.json();
}

// Use descriptive variable names
const isCircuitBreakerActive = await circuitBreaker.isPaused(protocol);

// Document public functions
/**
 * Analyzes protocol metrics for potential threats
 * @param protocol - The protocol address to analyze
 * @param metrics - Current protocol metrics
 * @returns Threat assessment with confidence score
 */
async function analyzeThreat(
  protocol: Address,
  metrics: ProtocolMetrics
): Promise<ThreatAssessment> {
  // ...
}
```

### Solidity

```solidity
// Use NatSpec comments
/// @notice Triggers the circuit breaker for a protocol
/// @param protocol The protocol address to pause
/// @param threatId Unique identifier for the threat
/// @param threatLevel Severity level (must be HIGH or CRITICAL)
/// @param reason Human-readable explanation
function triggerBreaker(
    address protocol,
    bytes32 threatId,
    ThreatLevel threatLevel,
    string calldata reason
) external;

// Use custom errors over require strings
error NotAuthorized(address caller);
error ProtocolNotRegistered(address protocol);
error ThreatLevelTooLow(ThreatLevel provided, ThreatLevel minimum);

// Use events for important state changes
event CircuitBreakerTriggered(
    address indexed protocol,
    bytes32 indexed threatId,
    ThreatLevel threatLevel,
    string reason
);

// Follow checks-effects-interactions pattern
function withdraw() external {
    // Checks
    require(balances[msg.sender] > 0, "No balance");
    
    // Effects
    uint256 amount = balances[msg.sender];
    balances[msg.sender] = 0;
    
    // Interactions
    (bool success,) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

### Git Commit Messages

```
feat(sentinels): add flash loan detection to LiquiditySentinel
fix(contracts): handle edge case in circuit breaker cooldown
docs(readme): add deployment instructions
test(cre): add workflow simulation tests
refactor(api): extract x402 middleware into separate module
chore(deps): update ethers to v6.10.0
```

---

## 20. KNOWN ISSUES & TODOS

### Known Issues

1. **CRE Cron Minimum Interval**: CRE cron triggers have a minimum interval of 30 seconds. For faster monitoring, consider using log triggers or external schedulers.

2. **x402 Testnet Limitations**: x402 facilitator on testnet may have rate limits. For demos, pre-fund test accounts with USDC.

3. **Data Streams Access**: Data Streams requires separate approval. Fall back to Data Feeds if not available.

4. **CrewAI Agent LLM Initialization**: CrewAI Agent() requires LLM API key at construction time. All agents use lazy-loaded getter functions (e.g. `get_liquidity_sentinel()`) to avoid import-time errors.

### Completed

- [x] Smart contracts (SentinelRegistry, CircuitBreaker, ThreatReport, ReputationTracker, MockProtocol) — 21 tests passing
- [x] Python agents package (`packages/agents-py/`) — CrewAI + FastAPI + web3.py + Pydantic v2 — 96 tests passing
- [x] 3 sentinel detection functions (liquidity, oracle, governance) with exact threshold parity to TS
- [x] Consensus algorithms (reach_consensus + weighted_consensus) with 2/3 majority rule
- [x] ChainSherlock forensic tracing (trace_transaction + analyze_trace)
- [x] FastAPI server with 6 endpoints (detect, sentinel, forensics, health)
- [x] CRE workflows (3 workflows: threatDetection, forensicAnalysis, healthCheck) using @chainlink/cre-sdk
- [x] TypeScript API (`packages/api/`) — Hono + ethers.js + x402 middleware — proxies to Python agents
- [x] Frontend dashboard (`packages/frontend/`) — React + Vite + Tailwind + React Query — 5s polling
- [x] Demo scripts (run-demo.sh, simulate-exploit.ts, reentrancy-demo.json)
- [x] **Agent 4 — SQLite database** (`packages/api/src/db/index.ts`) — WAL-mode better-sqlite3, 3 tables (alerts, protocols, forensic_reports), typed CRUD helpers
- [x] **Agent 4 — Alert routes** (`packages/api/src/routes/alerts.ts`) — GET paginated list, GET by id, POST create with auto Telegram notification on HIGH/CRITICAL
- [x] **Agent 4 — Protocol management routes** (`packages/api/src/routes/protocols.ts`) — GET list, GET by address, POST register, PATCH update, GET /:address/status (live on-chain read)
- [x] **Agent 4 — Telegram notifications** (`packages/api/src/services/telegram.ts`) — Markdown-formatted alerts via Bot API, graceful no-op when unconfigured
- [x] **Agent 4 — API key auth middleware** (`packages/api/src/middleware/auth.ts`) — X-API-Key header check, public route exemptions, disabled when API_KEYS unset
- [x] **Agent 4 — Wired up in index.ts** — DB init on startup, auth middleware, new routes mounted, CORS updated for PATCH + X-API-Key, version 1.1.0
- [x] **Agent 1 — Protocol Adapter Base Class** (`packages/agents-py/aegis/adapters/base.py`) — Abstract base class with TTLCache (60s default), async methods (get_tvl, get_token_balances, get_recent_events), sync wrappers, ProtocolMetricsSnapshot model
- [x] **Agent 1 — Aave V3 Adapter** (`packages/agents-py/aegis/adapters/aave_v3.py`) — Reads TVL from all reserve aTokens, tracks Supply/Withdraw/Borrow/Repay events, get_utilization_rate(), get_large_withdrawals()
- [x] **Agent 1 — Uniswap V3 Adapter** (`packages/agents-py/aegis/adapters/uniswap_v3.py`) — Factory mode (multiple pools) or pool mode, auto-discovers popular pools on Base, tracks Swap/Mint/Burn events, get_large_swaps()
- [x] **Agent 1 — Adapter Registry** (`packages/agents-py/aegis/adapters/__init__.py`) — Auto-detection of protocol type from address, get_adapter(web3, address) factory function, cached adapter instances, KNOWN_PROTOCOLS mapping
- [x] **Agent 1 — Detection Cycle Update** (`packages/agents-py/aegis/coordinator/crew.py`) — Added adapter parameter, auto-detects adapter when not simulating, simulation params take precedence
- [x] **Agent 1 — Adapter Tests** (`packages/agents-py/tests/test_adapters.py`) — 21 tests for TTLCache, TokenBalance, ProtocolEvent, adapters, registry, crew integration
- [x] **Agent 1 Phase 2 — Real Forensics Engine** (`packages/agents-py/aegis/sherlock/tracer.py`) — ForensicTracer with archive node support, transaction graph building, known address identification (CEX, DEX, mixers, attackers), multi-hop fund tracking, reentrancy/flash loan detection
- [x] **Agent 1 Phase 2 — Historical TVL Tracking** (`packages/agents-py/aegis/adapters/history.py`) — TVLHistoryStore (in-memory), SQLiteTVLStore (persistent), HistoricalTVLTracker with rolling averages (1h/24h/7d), anomaly detection (sudden drop, flash drain, below baseline)
- [x] **Agent 1 Phase 2 — Tracer Tests** (`packages/agents-py/tests/test_tracer.py`) — 26 tests for address identification, graph models, forensic tracer, archive node client, analysis detection
- [x] **Agent 1 Phase 2 — History Tests** (`packages/agents-py/tests/test_history.py`) — 24 tests for TVL snapshots, rolling averages, anomaly detection, SQLite persistence — 96 total tests passing
- [x] **Agent 4 — SSE real-time alert streaming** (`packages/api/src/routes/ws.ts`) — Server-Sent Events via hono/streaming, broadcast() on every new alert, 30s heartbeat, subscriber count
- [x] **Agent 4 — Rate limiting middleware** (`packages/api/src/middleware/rateLimit.ts`) — Sliding-window IP-based limiter, 100 req/min default, X-RateLimit-* headers, 429 Retry-After, env-configurable
- [x] **Agent 4 — OpenAPI/Swagger docs** (`packages/api/src/routes/docs.ts`) — Full OpenAPI 3.1 spec (12 paths), Swagger UI at /api/v1/docs, raw spec at /api/v1/openapi
- [x] **Agent 4 — Wired up v1.2.0** (`packages/api/src/index.ts`) — Rate limit middleware, SSE + docs routes, broadcast on alert POST, public path exemptions for /ws and /docs
- [x] **Agent 2 — CCIP Alert workflow** (`packages/cre-workflows/src/workflows/ccipAlert/main.ts`) — Log-triggered cross-chain alert propagation via CCIP Router, LINK approval + fee estimation, encoded threat data message
- [x] **Agent 2 — VRF Tie-Breaker workflow** (`packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts`) — VRF randomness request, weighted sentinel vote selection by reputation, deterministic fallback
- [x] **Agent 2 — IntegrateProtocol.s.sol** (`packages/contracts/script/IntegrateProtocol.s.sol`) — Foundry script: register MockProtocol in CircuitBreaker, grant CRE_WORKFLOW_ROLE, register 3 sentinels, authorize ReputationTracker updater
- [x] **Agent 2 — CRE types extended** (`packages/cre-workflows/src/types/`) — Added CCIP + VRF fields to evmConfigSchema, added ccipRouterAbi + linkTokenAbi + vrfCoordinatorAbi to abis.ts
- [x] **Agent 2 — Config.json fixed** (`packages/cre-workflows/src/workflows/threatDetection/config.json`) — Replaced zero placeholder addresses with real deployed contract addresses
- [x] **Agent 2 — CRE README** (`packages/cre-workflows/README.md`) — Full documentation: 5 workflows, setup, env vars, deployment, integration instructions

### TODOs

- [x] Deploy contracts to Base Sepolia (5 contracts deployed, addresses in .env)
- [x] Install npm dependencies for api, frontend, cre-workflows (`pnpm install`)
- [x] Agent 4 tasks: SQLite DB, alert routes, protocol routes, Telegram, auth middleware, wiring
- [x] Agent 1 Phase 1: Protocol adapters (Aave V3, Uniswap V3), adapter registry, detection cycle update
- [x] Agent 1 Phase 2: Real forensics engine, historical TVL tracking — 96 tests passing
- [x] Implement CCIP cross-chain alerting (show code, explain to judges) — ccipAlert workflow complete
- [x] Add VRF tie-breaker selection (show code, explain to judges) — vrfTieBreaker workflow complete
- [ ] Deploy CRE workflows to Chainlink network
- [ ] Record demo video
- [x] Agent 2 tasks: CRE threat detection config fixed, CCIP alert workflow, VRF tie-breaker, integration script, README — All 5 tasks completed
- [x] Agent 3 tasks: AlertHistory, ThreatFeed, RegisterProtocol, CircuitBreakerCard, ForensicsViewer, routing — All 6 components completed

### Future Enhancements

- Support for additional chains (Arbitrum, Optimism, Polygon)
- Integration with DeFi insurance protocols
- Machine learning model for threat prediction
- DAO governance for sentinel upgrades
- Token economics for sentinel staking

---

## 21. RESOURCES & REFERENCES

### Chainlink Documentation

- CRE Docs: https://docs.chain.link/cre
- CRE Getting Started: https://docs.chain.link/cre/getting-started/overview
- Data Feeds: https://docs.chain.link/data-feeds
- CCIP: https://docs.chain.link/ccip
- VRF: https://docs.chain.link/vrf
- Automation: https://docs.chain.link/chainlink-automation

### x402 Documentation

- x402 Docs: https://docs.cdp.coinbase.com/x402/welcome
- x402 GitHub: https://github.com/coinbase/x402
- x402 Specification: https://github.com/coinbase/x402/blob/main/specs/x402-specification.md

### ERC-8004

- EIP: https://eips.ethereum.org/EIPS/eip-8004
- Awesome ERC-8004: https://github.com/sudeepb02/awesome-erc8004
- Reference Implementation: https://github.com/vistara-apps/erc-8004-example

### CrewAI

- GitHub: https://github.com/crewAIInc/crewAI
- Docs: https://docs.crewai.com

### Example Repos

- x402 CRE Price Alerts: https://github.com/smartcontractkit/x402-cre-price-alerts
- CRE Prediction Market Demo: https://github.com/smartcontractkit/cre-gcp-prediction-market-demo

### Hackathon

- Hackathon Page: https://chain.link/hackathon
- Hackathon FAQ: https://chain.link/hackathon/faq
- LinkLab CRE Masterclass: https://youtube.com/watch?v=r7VKS5L47f0

---

## 22. PRODUCTION ROADMAP

### Current State (Hackathon MVP) — Updated March 1, 2026

| Component | Status | Reality |
|-----------|--------|---------|
| Smart Contracts | ✅ Deployed | On Base Sepolia testnet, 5 contracts deployed |
| AI Agents | ✅ Working | Simulation mode + real adapters (Aave V3, Uniswap V3) |
| Protocol Adapters | ✅ Complete | Base class + Aave V3 + Uniswap V3 + registry + history, 96 tests passing |
| CRE Workflows | ✅ Complete | 5 workflows (threat detection, forensics, health check, CCIP alert, VRF tie-breaker), not deployed yet |
| Circuit Breaker | ✅ Code exists | IntegrateProtocol.s.sol ready for deployment |
| Forensics | ⏳ Stub | Returns mock data, no real tracing |
| Frontend | ✅ Complete | 6 components: AlertHistory, ThreatFeed, RegisterProtocol, CircuitBreakerCard, ReportViewer, routing |
| API + Database | ✅ Complete | SQLite, alerts, protocols, Telegram notifications, API key auth |

### What's Missing for Real-World Use

#### 1. Real Protocol Integration ✅ COMPLETED

Protocol adapters are now implemented:

```
Implemented (Agent 1):
├── Protocol adapters for DeFi protocols
│   ├── ✅ Aave V3 adapter (TVL, borrows, utilization, events)
│   ├── ✅ Uniswap V3 adapter (factory + pool mode, large swaps)
│   ├── Compound adapter (future)
│   └── Generic ERC-4626 vault adapter (future)
├── ✅ TTLCache for efficient polling (60s default)
├── ✅ Adapter registry with auto-detection
└── Historical data storage for trend analysis (in progress via SQLite)
```

#### 2. Protocol Onboarding Flow — Partially Complete

How does a protocol actually use AEGIS?

```
Status:
├── ✅ Registration portal (RegisterProtocol frontend component)
├── Integration SDK (protocol installs circuit breaker hook) — Future
├── ✅ Custom threshold configuration per protocol (alert_threshold, breaker_threshold)
├── ✅ Dashboard for protocol admins (ThreatFeed, AlertHistory, CircuitBreakerCard)
└── ✅ Alert notification setup (Telegram notifications on HIGH/CRITICAL)
```

#### 3. Real Forensics Engine

ChainSherlock currently returns mock data. Needs:

```
├── Archive node access (debug_traceTransaction)
├── Transaction graph builder (trace fund flows)
├── Known attacker address database
├── Integration with Etherscan/Basescan APIs
└── AI analysis with full context (not just stubs)
```

#### 4. Production Infrastructure — Partially Complete

```
Status:
├── ✅ Database (SQLite WAL-mode) — alerts, protocols, forensic_reports tables
├── ✅ Authentication — X-API-Key header, public route exemptions
├── Rate limiting — could be DoS'd (TODO)
├── Multi-chain deployment — only Base Sepolia (TODO)
├── Redundant RPC providers — using public RPCs (TODO)
├── Monitoring & alerting (Datadog/Grafana) — TODO
└── CI/CD pipeline — TODO
```

#### 5. Chainlink Services

| Service | Status | What's Needed |
|---------|--------|---------------|
| CRE | ✅ Code complete (5 workflows) | Deploy to Chainlink network |
| CCIP | ✅ Implemented (ccipAlert workflow) | Fund LINK for fees on testnet |
| VRF | ✅ Implemented (vrfTieBreaker workflow) | Create VRF subscription on testnet |
| Automation | Concept only | Replace cron with Keepers |

### 7-Day Sprint to Submission (Mar 1-8, 2026)

| Day | Date | Focus | Agents |
|-----|------|-------|--------|
| **1** | Mar 1 | ✅ Protocol adapters, frontend, API/DB complete | Done |
| **2** | Mar 2 | CRE threat detection workflow + integration test | Agent 2 |
| **3** | Mar 3 | CCIP cross-chain alerting + VRF tie-breaker | Agent 2 |
| **4** | Mar 4 | Real forensics engine + historical TVL | Agent 1 |
| **5** | Mar 5 | End-to-end testing, bug fixes | All |
| **6** | Mar 6 | Demo video recording, polish UI | Team |
| **7** | Mar 7 | Documentation, README, submission prep | Team |
| **8** | Mar 8 | **SUBMIT** | - |

### Prioritized Roadmap

#### Phase 1: Make It Real ✅ COMPLETE (Mar 1)

1. **Connect to real DeFi protocols** ✅
   - ✅ Aave V3 adapter (TVL, borrows, utilization, events)
   - ✅ Uniswap V3 adapter (factory + pool mode, large swaps)
   - ✅ Adapter registry with auto-detection

2. **Deploy CRE workflows to Chainlink** ⏳ IN PROGRESS
   - Get CRE access from Chainlink team
   - Deploy threatDetection workflow
   - Wire up to trigger real CircuitBreaker

3. **Add database persistence** ✅
   - ✅ SQLite for alerts, protocols, forensic reports
   - ✅ Telegram notifications on HIGH/CRITICAL
   - ✅ API key authentication

#### Phase 2: Protocol Onboarding (2-3 weeks)

4. **Build protocol registration system**
   - Web portal for protocols to sign up
   - x402 subscription payments
   - Custom alert thresholds

5. **Integration SDK**
   - NPM package protocols install
   - Hooks into their pause() function
   - Automatic AEGIS authorization

#### Phase 3: Production Ready (2-3 weeks)

6. **Security hardening**
   - API authentication
   - Rate limiting
   - Audit smart contracts

7. **Multi-chain expansion**
   - Deploy to Ethereum mainnet
   - Deploy to Arbitrum, Optimism
   - CCIP for cross-chain alerts

### How Someone Would Actually Use AEGIS

#### For a DeFi Protocol (Customer):

```
1. Go to aegis.xyz
2. Connect wallet, pay subscription ($100/mo in USDC via x402)
3. Register protocol address
4. Configure thresholds:
   - TVL drop alert: 10%
   - Circuit breaker: 20%
   - Price deviation: 3%
5. Grant AEGIS permission to call pause() on your contracts
6. Set up notifications (Telegram bot, webhook to PagerDuty)
7. View dashboard showing real-time monitoring
```

#### For a Security Researcher:

```
1. Browse public threat feed at aegis.xyz/threats
2. See live alerts across all monitored protocols
3. Pay $1 per forensic report via x402
4. Get detailed attack analysis for incidents
```

#### For Chainlink Integration:

```
1. CRE workflow runs every 30s
2. Reads protocol state via EVM Read capability
3. Calls AEGIS AI agents via HTTP capability
4. If consensus = CRITICAL:
   - Writes to CircuitBreaker via EVM Write
   - Triggers protocol's pause()
   - Sends CCIP message to other chains
5. Stores signed report on-chain via ThreatReport contract
```

### Quick Wins (Can Implement Quickly)

| Task | Effort | Impact | Status |
|------|--------|--------|--------|
| Add real Aave TVL reading | 2-4 hours | High — proves real-world capability | ✅ Done (Agent 1) |
| Persist alerts to SQLite | 2-3 hours | Medium — enables history | ✅ Done (Agent 4) |
| Add Telegram notifications | 2-3 hours | High — real alerting | ✅ Done (Agent 4) |
| Deploy CRE workflow locally | 4-6 hours | High — full Chainlink loop | ⏳ Pending (Agent 2) |

### Simulation Mode (Current)

The current implementation supports simulation parameters for testing:

```bash
# Simulate a reentrancy attack (25% TVL drop + 6% price manipulation)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0x1",
    "simulate_tvl_drop_percent": 25,
    "simulate_price_deviation_percent": 6,
    "simulate_short_voting_period": false
  }'
```

**Simulation Parameters:**

| Parameter | Type | Effect |
|-----------|------|--------|
| `simulate_tvl_drop_percent` | float | Triggers Liquidity Sentinel (20%+ = CRITICAL) |
| `simulate_price_deviation_percent` | float | Triggers Oracle Sentinel (5%+ = CRITICAL) |
| `simulate_short_voting_period` | bool | Triggers Governance Sentinel (HIGH) |

---

## 23. PARALLEL DEVELOPMENT GUIDE (4 AGENTS)

> **FOR AI AGENTS**: If you are Claude Code or Codex, read this section to understand your assigned tasks and boundaries. Do NOT work outside your assigned directories.

### Agent Assignment Overview

| Agent | Role | Directory Ownership | Best At |
|-------|------|---------------------|---------|
| **Claude Code 1** | Detection Engine | `packages/agents-py/` | Complex Python, AI, adapters |
| **Claude Code 2** | CRE & Contracts | `packages/cre-workflows/`, `packages/contracts/` | Architecture, Chainlink, Solidity |
| **Codex 1** | Frontend | `packages/frontend/` | React components, UI |
| **Codex 2** | API & Database | `packages/api/` | Routes, SQLite, middleware |

---

### AGENT 1: Claude Code — Detection Engine ✅ COMPLETED

**Status**: All Phase 1 + Phase 2 tasks completed on March 2, 2026. 96 tests passing.

**Your Directory**: `packages/agents-py/` (DO NOT touch other packages)

#### Completed Tasks

**Task 1.1: ✅ Protocol Adapter Base Class**
```
File: packages/agents-py/aegis/adapters/base.py

Implemented:
- TTLCache with configurable TTL (60s default)
- BaseProtocolAdapter abstract class
- Async methods: get_tvl(), get_token_balances(), get_recent_events()
- Sync wrappers: get_tvl_sync(), etc.
- Models: TokenBalance, ProtocolEvent, ProtocolMetricsSnapshot
```

**Task 1.2: ✅ Aave V3 Adapter**
```
File: packages/agents-py/aegis/adapters/aave_v3.py

Implemented:
- Reads TVL from all reserve aTokens via getATokenTotalSupply()
- Tracks Supply, Withdraw, Borrow, Repay, ReserveDataUpdated events
- get_total_borrows(), get_utilization_rate()
- get_large_withdrawals(threshold_usd)
- Supports Base, Ethereum mainnet
```

**Task 1.3: ✅ Uniswap V3 Adapter**
```
File: packages/agents-py/aegis/adapters/uniswap_v3.py

Implemented:
- Factory mode (multiple pools) or pool mode (single pool)
- Auto-discovers popular pools on Base (WETH/USDC, etc.)
- Tracks Swap, Mint, Burn events
- get_pool_info(), get_large_swaps(threshold_usd)
- Supports Base, Ethereum, Arbitrum
```

**Task 1.4: ✅ Detection Cycle Update**
```
File: packages/agents-py/aegis/coordinator/crew.py

Implemented:
- Added `adapter` parameter to run_detection_cycle()
- Auto-detects adapter when not in simulation mode
- Uses adapter.get_tvl_sync() for real data
- Simulation params take precedence over adapter
```

**Task 1.5: ✅ Adapter Registry**
```
File: packages/agents-py/aegis/adapters/__init__.py

Implemented:
- KNOWN_PROTOCOLS mapping for Base, Ethereum chains
- detect_protocol_type() with on-chain fallback
- AdapterRegistry class with caching
- get_adapter(web3, address, force_type=None)
- reset_registry() for testing
```

**Bonus: ✅ Adapter Tests**
```
File: packages/agents-py/tests/test_adapters.py

21 new tests covering:
- TTLCache (7 tests)
- TokenBalance, ProtocolEvent, ProtocolMetricsSnapshot models
- Adapter creation and configuration
- Registry and factory functions
- Crew integration (adapter param, simulation precedence)
```

#### Testing
All tests pass: `cd packages/agents-py && python -m pytest tests/ -v` → 96 passed

#### Files Created/Modified
- ✅ `aegis/adapters/base.py` (new)
- ✅ `aegis/adapters/aave_v3.py` (new)
- ✅ `aegis/adapters/uniswap_v3.py` (new)
- ✅ `aegis/adapters/__init__.py` (new)
- ✅ `aegis/adapters/history.py` (new — Phase 2)
- ✅ `aegis/sherlock/tracer.py` (new — Phase 2)
- ✅ `aegis/sherlock/__init__.py` (modified — Phase 2)
- ✅ `aegis/coordinator/crew.py` (modified)
- ✅ `tests/test_adapters.py` (new)
- ✅ `tests/test_tracer.py` (new — Phase 2)
- ✅ `tests/test_history.py` (new — Phase 2)

---

### AGENT 1: Claude Code — Phase 2 Tasks (NEW)

**Status**: ✅ Phase 1 + Phase 2 complete. All Agent 1 tasks done (96 tests passing).

**Your Directory**: `packages/agents-py/` (DO NOT touch other packages)

#### Phase 2 Tasks (in order)

**Task 1.6: Real Forensics Engine**
```
File: packages/agents-py/aegis/sherlock/tracer.py

Implement real transaction tracing:
- Connect to archive node (get RPC with debug_traceTransaction support)
- Trace internal calls and fund flows
- Build transaction graph showing money movement
- Identify known attacker addresses (maintain a database)
```

**Task 1.7: Historical TVL Tracking**
```
File: packages/agents-py/aegis/adapters/history.py

Track TVL over time for trend analysis:
- Store TVL snapshots in SQLite (via Agent 4's db layer)
- Calculate rolling averages (1h, 24h, 7d)
- Detect anomalous drops vs historical baseline
- Expose via API: GET /api/v1/protocol/:address/history
```

**Task 1.8: Compound V3 Adapter**
```
File: packages/agents-py/aegis/adapters/compound_v3.py

Implement Compound V3 (Comet) adapter:
- Read TVL from Comet contract
- Track supply/withdraw/absorb events
- get_utilization_rate(), get_liquidation_risk()
- Add to KNOWN_PROTOCOLS mapping
```

**Task 1.9: Event Listener System**
```
File: packages/agents-py/aegis/adapters/listener.py

Replace polling with real-time event listening:
- WebSocket connection to RPC
- Subscribe to Transfer, Swap, Mint, Burn events
- Push alerts on large movements (>$100k)
- Queue for async processing
```

**Task 1.10: AI-Enhanced Analysis Prompts**
```
File: packages/agents-py/aegis/sherlock/prompts.py

Improve forensic analysis:
- Add context about known attack patterns
- Include recent DeFi exploits as examples
- Better vulnerability classification
- Clearer remediation recommendations
```

#### Boundaries
- ✅ You own: `packages/agents-py/`
- ❌ Do NOT touch: `packages/api/`, `packages/frontend/`, `packages/cre-workflows/`, `packages/contracts/`

---

### AGENT 2: Claude Code — CRE & Smart Contracts

**READ THIS IF**: You are assigned to Chainlink CRE workflows and smart contract integration.

**Your Directories**: `packages/cre-workflows/`, `packages/contracts/` (DO NOT touch other packages)

#### Tasks (in order)

**Task 2.1: Complete CRE Threat Detection Workflow**
```
File: packages/cre-workflows/src/workflows/threatDetection/main.ts

Implement full workflow using @chainlink/cre-sdk:
- Trigger: Cron every 30 seconds
- Step 1: HTTP fetch to http://localhost:8000/api/v1/detect
- Step 2: EVM Read - check protocol state
- Step 3: Data Feeds - get ETH/USD price
- Step 4: If CRITICAL → EVM Write to CircuitBreaker.triggerBreaker()
- Step 5: Return signed report
```

**Task 2.2: Add CCIP Cross-Chain Alerting**
```
File: packages/cre-workflows/src/workflows/ccipAlert/main.ts

New workflow triggered by CircuitBreakerTriggered event:
- Send CCIP message to Arbitrum Sepolia
- Message: { threatId, protocol, threatLevel, timestamp }
- Use CCIP Router for Base Sepolia
```

**Task 2.3: Create CircuitBreaker Integration Script**
```
File: packages/contracts/script/IntegrateProtocol.s.sol

Foundry script to:
- Register MockProtocol with CircuitBreaker
- Grant CRE_WORKFLOW_ROLE to workflow address
- Verify registration
```

**Task 2.4: Add VRF Tie-Breaker**
```
File: packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts

When consensus is split (e.g., CRITICAL, HIGH, NONE):
- Request VRF randomness
- Use random number to weight votes
- Return final decision
```

**Task 2.5: Document CRE Setup**
```
File: packages/cre-workflows/README.md

- How to deploy workflows
- Environment variables needed
- Testing with cre workflow simulate
```

#### Deployed Contracts Reference
```
SentinelRegistry:   0xd34FC1ee378F342EFb92C0D334362B9E577b489f
CircuitBreaker:     0xa0eE49660252B353830ADe5de0Ca9385647F85b5
ThreatReport:       0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499
MockProtocol:       0x11887863b89F1bE23A650909135ffaCFab666803
```

#### Execution Status (Updated: 2026-03-02)

**Completed**
- [x] Task 2.1 — `packages/cre-workflows/src/workflows/threatDetection/config.json` — Fixed zero addresses with real deployed contract addresses; threat detection workflow was already fully implemented (323 lines)
- [x] Task 2.2 — `packages/cre-workflows/src/workflows/ccipAlert/main.ts` + `workflow.yaml` — Full CCIP cross-chain alerting: log trigger on CircuitBreakerTriggered, LINK balance check, fee estimation, approve + ccipSend
- [x] Task 2.3 — `packages/contracts/script/IntegrateProtocol.s.sol` — Foundry integration script: registerProtocol, grantRole(CRE_WORKFLOW_ROLE), registerSentinel x3, addUpdater for ReputationTracker; includes ConfigureCircuitBreaker helper
- [x] Task 2.4 — `packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts` + `workflow.yaml` — VRF tie-breaker: requestRandomWords, weighted sentinel selection by reputation scores, deterministic fallback when VRF unavailable
- [x] Task 2.5 — `packages/cre-workflows/README.md` — Full documentation: all 5 workflows, Chainlink services table, setup, env vars, deployment, integration instructions
- [x] Types extended — `packages/cre-workflows/src/types/index.ts` — Added optional CCIP + VRF fields to evmConfigSchema
- [x] ABIs added — `packages/cre-workflows/src/types/abis.ts` — Added ccipRouterAbi, linkTokenAbi, vrfCoordinatorAbi
- [x] TypeScript compilation — `npx tsc --noEmit` passes with zero errors
- [x] Solidity compilation — `forge build` passes for IntegrateProtocol.s.sol

**Remaining**
- [ ] Deploy CRE workflows to Chainlink network (requires CRE CLI access)
- [ ] Create VRF subscription and fund with LINK on Base Sepolia
- [ ] Fund workflow address with LINK for CCIP fees
- [ ] End-to-end integration test with all services running

#### Boundaries
- ✅ You own: `packages/cre-workflows/`, `packages/contracts/`
- ❌ Do NOT touch: `packages/agents-py/`, `packages/api/`, `packages/frontend/`

---

### AGENT 3: Codex — Frontend Dashboard

**READ THIS IF**: You are assigned to build React frontend components.

**Your Directory**: `packages/frontend/` (DO NOT touch other packages)

#### Tech Stack
- React 18 + TypeScript
- Vite
- TailwindCSS
- React Query
- API: http://localhost:3000

#### Tasks (in order)

**Task 3.1: Alert History Component**
```
File: packages/frontend/src/components/alerts/AlertHistory.tsx

- Display list of past alerts in a table
- Columns: Timestamp, Protocol, Threat Level, Action, Consensus %
- Color code: CRITICAL=#ef4444, HIGH=#f97316, MEDIUM=#eab308, NONE=#6b7280
- Fetch from: GET /api/v1/alerts
- Add pagination (20 per page)
```

**Task 3.2: Protocol Registration Form**
```
File: packages/frontend/src/components/protocol/RegisterProtocol.tsx

Form fields:
- Protocol Address (0x...)
- Protocol Name
- Alert Threshold % (default: 10)
- Circuit Breaker Threshold % (default: 20)
Submit to: POST /api/v1/protocols
Show success/error toast
```

**Task 3.3: Live Threat Feed**
```
File: packages/frontend/src/components/dashboard/ThreatFeed.tsx

- Real-time feed of incoming threats
- Auto-refresh every 5 seconds using React Query
- Show: time ago, protocol name, threat level badge, confidence
- Fetch from: GET /api/v1/sentinel/aggregate
```

**Task 3.4: Circuit Breaker Status Card**
```
File: packages/frontend/src/components/protocol/CircuitBreakerCard.tsx

- Shows protocol pause status
- Display: status badge, paused_at, reason, cooldown timer
- Red pulsing animation when paused
- Fetch from: GET /api/v1/protocols/:address/status
```

**Task 3.5: Forensics Report Viewer**
```
File: packages/frontend/src/components/forensics/ReportViewer.tsx

Sections:
- Attack Summary (type, severity, estimated loss)
- Transaction Flow (visual diagram if possible)
- Fund Destinations (table)
- Recommendations (bullet list)
Fetch from: GET /api/v1/forensics/:id
```

**Task 3.6: Add Routing**
```
File: packages/frontend/src/App.tsx

Add React Router with routes:
- / (dashboard with ThreatFeed)
- /alerts (AlertHistory)
- /protocols (list + RegisterProtocol)
- /forensics/:id (ReportViewer)
```

#### Execution Status (Updated: 2026-03-01)

**Completed**
- [x] Task 3.1 — `packages/frontend/src/components/alerts/AlertHistory.tsx`
- [x] Task 3.2 — `packages/frontend/src/components/protocol/RegisterProtocol.tsx`
- [x] Task 3.3 — `packages/frontend/src/components/dashboard/ThreatFeed.tsx`
- [x] Task 3.4 — `packages/frontend/src/components/protocol/CircuitBreakerCard.tsx`
- [x] Task 3.5 — `packages/frontend/src/components/forensics/ReportViewer.tsx`
- [x] Task 3.6 — Routing added in `packages/frontend/src/App.tsx` and `packages/frontend/src/main.tsx`

**Remaining**
- [ ] End-to-end API verification once backend is running on `http://localhost:3000` (frontend currently sees `ECONNREFUSED` when API is down)
- [ ] Confirm final response-shape alignment if Agent 4 adjusts `/api/v1/alerts`, `/api/v1/protocols`, or `/api/v1/protocols/:address/status`

#### Styling Guidelines
```css
/* Use TailwindCSS only */
Background: bg-gray-900
Cards: bg-gray-800 rounded-lg p-4 shadow
Text: text-white, text-gray-400 for secondary
Buttons: bg-blue-600 hover:bg-blue-700 rounded px-4 py-2
```

#### Boundaries
- ✅ You own: `packages/frontend/`
- ❌ Do NOT touch: `packages/agents-py/`, `packages/api/`, `packages/cre-workflows/`, `packages/contracts/`

---

### AGENT 4: Codex — API Routes & Database

**READ THIS IF**: You are assigned to build API routes, database, and notifications.

**Your Directory**: `packages/api/` (DO NOT touch other packages)

#### Tech Stack
- Hono (web framework)
- TypeScript
- better-sqlite3 (SQLite)
- node-telegram-bot-api

#### Tasks (in order)

**Task 4.1: Add SQLite Database** ✅ COMPLETED
```
File: packages/api/src/db/index.ts  (IMPLEMENTED)

SQLite via better-sqlite3 with WAL mode. Three tables: alerts, protocols,
forensic_reports. Typed CRUD helpers exported. Auto-creates data/ directory.
```

**Task 4.2: Alert Routes** ✅ COMPLETED
```
File: packages/api/src/routes/alerts.ts  (IMPLEMENTED)

GET  /api/v1/alerts          - Paginated list (?page=1&limit=20&protocol=0x…)
GET  /api/v1/alerts/:id      - Single alert
POST /api/v1/alerts          - Create alert → auto Telegram on HIGH/CRITICAL
```

**Task 4.3: Protocol Management Routes** ✅ COMPLETED
```
File: packages/api/src/routes/protocols.ts  (IMPLEMENTED)

GET   /api/v1/protocols              - List all (filterable ?active=true)
GET   /api/v1/protocols/:address     - Get protocol details
POST  /api/v1/protocols              - Register (409 on duplicate)
PATCH /api/v1/protocols/:address     - Partial update
GET   /api/v1/protocols/:address/status - Live circuit breaker read
```

**Task 4.4: Telegram Notifications** ✅ COMPLETED
```
File: packages/api/src/services/telegram.ts  (IMPLEMENTED)

Uses native fetch to Telegram Bot API (no heavy SDK dependency).
Graceful no-op when TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID unset.
Formatted Markdown messages with threat-level emojis.
```

**Task 4.5: API Key Authentication** ✅ COMPLETED
```
File: packages/api/src/middleware/auth.ts  (IMPLEMENTED)

- Checks X-API-Key header against API_KEYS env var
- Public routes exempt: /, /api/v1/health, /api/v1/sentinel/aggregate
- Disabled (open access) when API_KEYS env var is empty
```

**Task 4.6: Wire Everything Up** ✅ COMPLETED
```
File: packages/api/src/index.ts  (UPDATED to v1.1.0)

- DB init on startup (getDb())
- Auth middleware before x402
- New routes: /api/v1/alerts, /api/v1/protocols
- CORS updated: PATCH method + X-API-Key header
- Root endpoint lists all 7 route groups
```

#### Environment Variables to Add
```
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
API_KEYS=aegis-dev-key-1,aegis-dev-key-2
DATABASE_PATH=./data/aegis.db
```

#### Boundaries
- ✅ You own: `packages/api/`
- ❌ Do NOT touch: `packages/agents-py/`, `packages/frontend/`, `packages/cre-workflows/`, `packages/contracts/`
- ⚠️ Do NOT modify: `packages/api/src/services/agentProxy.ts` (already complete)

#### Execution Status (Updated: 2026-03-02)

**Completed**
- [x] Task 4.1 — `packages/api/src/db/index.ts` — SQLite WAL-mode, 3 tables, typed CRUD helpers
- [x] Task 4.2 — `packages/api/src/routes/alerts.ts` — Paginated list, by-id, create + Telegram fire
- [x] Task 4.3 — `packages/api/src/routes/protocols.ts` — Full CRUD + live circuit breaker status
- [x] Task 4.4 — `packages/api/src/services/telegram.ts` — Native fetch, Markdown alerts, graceful no-op
- [x] Task 4.5 — `packages/api/src/middleware/auth.ts` — X-API-Key, public route exemptions
- [x] Task 4.6 — `packages/api/src/index.ts` — v1.1.0, DB init, auth, CORS, new routes
- [x] Task 4.7 (polish) — `packages/api/src/routes/ws.ts` — SSE real-time alert streaming, broadcast() on every new alert, 30s heartbeat
- [x] Task 4.8 (polish) — `packages/api/src/middleware/rateLimit.ts` — Sliding-window IP rate limiter, 100 req/min, X-RateLimit-* headers, 429 Retry-After
- [x] Task 4.9 (polish) — `packages/api/src/routes/docs.ts` — OpenAPI 3.1 spec (12 paths), Swagger UI at /api/v1/docs, raw spec at /api/v1/openapi
- [x] Task 4.10 (polish) — `packages/api/src/index.ts` — v1.2.0, rate limit middleware, SSE + docs routes, broadcast on alert POST, /ws + /docs public paths

**Remaining**
- [ ] End-to-end verification with frontend (Agent 3) when both services run together
- [ ] Confirm response-shape alignment with Agent 3’s components for `/api/v1/alerts`, `/api/v1/protocols`, `/api/v1/protocols/:address/status`

---

### Coordination Rules

| Shared Resource | Owner | Rule |
|-----------------|-------|------|
| `packages/agents-py/aegis/models.py` | Agent 1 | Others request changes |
| `packages/api/src/config.ts` | Agent 4 | Others read-only |
| `.env` | Agent 4 | Add vars, notify others |
| `CLAUDE.md` | All agents | Update per Self-Updating Progress Protocol (§24) |

### Communication Protocol

If you need something from another agent's domain:
1. **Don't modify their files**
2. Add a comment in your code: `// TODO: Need Agent X to add Y`
3. Continue with mock/placeholder
4. Coordinate during integration phase

### Parallel Timeline

```
Hour 1:
  Agent 1: [Adapter base + Aave] ████████
  Agent 2: [CRE threatDetection] ████████
  Agent 3: [AlertHistory + ThreatFeed] ████████
  Agent 4: [SQLite + schema] ████████

Hour 2:
  Agent 1: [Uniswap adapter] ████████
  Agent 2: [CCIP alerts] ████████
  Agent 3: [RegisterProtocol + CircuitBreakerCard] ████████
  Agent 4: [alerts + protocols routes] ████████

Hour 3:
  Agent 1: [Integrate in crew.py] ████████
  Agent 2: [VRF tie-breaker] ████████
  Agent 3: [ForensicsViewer + routing] ████████
  Agent 4: [Telegram + auth] ████████

Hour 4:
  ALL: [Integration, testing, merge conflicts]
```

---

## 24. SELF-UPDATING PROGRESS PROTOCOL

> **FOR ALL AGENTS**: After completing your assigned tasks, you MUST update this CLAUDE.md file to reflect what was done. This keeps the document a living source of truth.

### When to Update

Update CLAUDE.md **immediately after finishing a set of tasks**, before ending your session. Do NOT defer this to another agent.

### What to Update

Every agent that completes work must update **all** of the following sections:

| Section | What to change |
|---------|----------------|
| **§20 Completed** | Add `- [x]` entries for each task completed, with file paths and brief descriptions |
| **§20 TODOs** | Check off any TODO items that are now done; add new remaining items if discovered |
| **§5 Repository Structure** | Add any new files/directories you created to the tree |
| **§17 Environment Variables** | Add any new env vars your code introduced |
| **§23 Agent N Execution Status** | Add/update an `#### Execution Status (Updated: YYYY-MM-DD)` block under your agent section with completed/remaining checklists |
| **Version footer** | Bump the patch version and update the description at the bottom of the file |

### Update Format Conventions

```markdown
## In §20 Completed, add entries like:
- [x] **Agent N — Short description** (`path/to/file.ext`) — One-line summary of what was implemented

## In your Agent section, add an Execution Status block like:
#### Execution Status (Updated: 2026-03-01)

**Completed**
- [x] Task N.1 — `path/to/file` — Brief description
- [x] Task N.2 — `path/to/file` — Brief description

**Remaining**
- [ ] Any follow-up items discovered during implementation

## Version footer (last line of file):
*Version: X.Y.Z — Agent N tasks completed; brief change summary*
```

### Rules

1. **Do NOT delete or rewrite other agents' entries** — only append your own.
2. **Be factual** — only mark items `[x]` if the code exists and compiles.
3. **Keep entries concise** — one line per completed item.
4. **Bump the version** — increment the patch number (e.g. 2.3.0 → 2.4.0).
5. **Timestamp your Execution Status** with the current date.

### Why This Matters

This file is the **single source of truth** for every agent and human contributor. If you skip this step:
- Other agents won't know what you built and may duplicate or conflict with your work.
- Integration phases become guesswork.
- The project state becomes unknowable.

---

## QUICK REFERENCE CARD

```
PROJECT: AEGIS Protocol (AI-Enhanced Guardian Intelligence System)
HACKATHON: Chainlink Convergence (Feb 6 - Mar 8, 2026)
SUBMISSION: March 8, 2026
TRACK: Risk & Compliance + AI

CHAINLINK SERVICES (5 = +4 bonus):
  CRE - Workflow orchestration
  Data Feeds - Price verification (ETH/USD)
  Automation - Scheduled 30s detection cycles
  VRF - Fair tie-breaker selection
  CCIP - Cross-chain alerts

DEPLOYED CONTRACTS (Base Sepolia):
  SentinelRegistry:   0xd34FC1ee378F342EFb92C0D334362B9E577b489f
  CircuitBreaker:     0xa0eE49660252B353830ADe5de0Ca9385647F85b5
  ThreatReport:       0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499
  ReputationTracker:  0x7970433B694f7fa6f8D511c7B20110ECd28db100
  MockProtocol:       0x11887863b89F1bE23A650909135ffaCFab666803

KEY COMMANDS:
  bash scripts/run-demo.sh                              # Start all services
  cd packages/contracts && forge test                    # Contract tests (21 passing)
  cd packages/agents-py && python -m pytest tests/ -v   # Agent tests (96 passing)
  npx tsx scripts/simulate-exploit.ts                    # Simulate attack

SERVICES:
  Python Agent API:  http://localhost:8000 (FastAPI docs at /docs)
  TypeScript API:    http://localhost:3000
  Frontend:          http://localhost:5173

TESTNET: Base Sepolia (84532)
```

---

*Last Updated: March 2, 2026*
*Version: 2.9.0 — Agent 2 complete: CCIP alert workflow, VRF tie-breaker workflow, IntegrateProtocol.s.sol, CRE types/ABIs extended, config fixed, README; all 5 CRE workflows + contracts compile clean*
