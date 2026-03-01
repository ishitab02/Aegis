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

---

## 1. PROJECT OVERVIEW

### What is AEGIS Protocol?

AEGIS Protocol is an autonomous, AI-powered security infrastructure for DeFi protocols. It combines two integrated systems:

1. **SentinelSwarm**: A network of specialized AI agents that continuously monitor DeFi protocols for anomalies and threats, capable of triggering circuit breakers when consensus is reached.

2. **ChainSherlock**: An AI forensics engine that, when triggered by threat detection, traces attack paths, identifies vulnerabilities, and generates actionable reports in real-time.

### The One-Liner

> "AEGIS is the immune system for DeFi - AI agents that detect threats in seconds and investigate exploits in minutes, not hours."

### Hackathon Context

- **Event**: Chainlink Convergence Hackathon (Feb 6 - Mar 1, 2026)
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
  - pytest - Python agents (25 tests passing)
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
│   │   │       │   ├── config.json
│   │   │       │   └── workflow.yaml
│   │   │       ├── forensicAnalysis/
│   │   │       │   ├── main.ts    # Log trigger: CircuitBreakerTriggered → forensics
│   │   │       │   └── workflow.yaml
│   │   │       └── healthCheck/
│   │   │           ├── main.ts    # 5min cron: API health + sentinel liveness
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
│   │   │   ├── sentinels/
│   │   │   │   ├── liquidity_sentinel.py   # monitor_tvl() + CrewAI Agent
│   │   │   │   ├── oracle_sentinel.py      # monitor_price_feeds() + CrewAI Agent
│   │   │   │   └── governance_sentinel.py  # analyze_proposal() + CrewAI Agent
│   │   │   ├── sherlock/
│   │   │   │   ├── chain_sherlock.py       # trace_transaction() + CrewAI Agent
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
│   │       └── test_api.py               # 7 tests (FastAPI endpoints)
│   │
│   ├── api/                       # [IMPLEMENTED] TypeScript API (Hono, port 3000)
│   │   ├── src/
│   │   │   ├── index.ts           # Hono server entry point
│   │   │   ├── config.ts          # Env vars, contract addresses
│   │   │   ├── routes/
│   │   │   │   ├── sentinel.ts    # GET /aggregate, /:id, POST /detect
│   │   │   │   ├── forensics.ts   # POST /, GET /, GET /:id
│   │   │   │   ├── reports.ts     # GET /protocol (on-chain reads)
│   │   │   │   └── health.ts      # GET / (aggregated health)
│   │   │   ├── middleware/
│   │   │   │   ├── x402Payment.ts # HTTP 402 payment gate
│   │   │   │   └── cors.ts
│   │   │   └── services/
│   │   │       ├── agentProxy.ts  # HTTP client to Python FastAPI
│   │   │       └── contractReader.ts  # ethers.js v6 on-chain reads
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

25 tests passing (`cd packages/agents-py && python -m pytest tests/ -v`):
- **test_consensus.py** (7): insufficient votes, 2/3 critical, unanimous, split, high alert, 2-sentinel, weighted
- **test_sentinels.py** (11): TVL drops (initial/critical/high/medium/none), oracle deviations (critical/high/stale/none), governance (clean/short)
- **test_api.py** (7): root, health, sentinel aggregate, sentinel by ID, sentinel 404, forensics list, forensics 404

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
- [x] All sentinels operational (25 tests passing)
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

python -m pytest tests/ -v                          # Run tests (25 passing)
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
- [x] Python agents package (`packages/agents-py/`) — CrewAI + FastAPI + web3.py + Pydantic v2 — 25 tests passing
- [x] 3 sentinel detection functions (liquidity, oracle, governance) with exact threshold parity to TS
- [x] Consensus algorithms (reach_consensus + weighted_consensus) with 2/3 majority rule
- [x] ChainSherlock forensic tracing (trace_transaction + analyze_trace)
- [x] FastAPI server with 6 endpoints (detect, sentinel, forensics, health)
- [x] CRE workflows (3 workflows: threatDetection, forensicAnalysis, healthCheck) using @chainlink/cre-sdk
- [x] TypeScript API (`packages/api/`) — Hono + ethers.js + x402 middleware — proxies to Python agents
- [x] Frontend dashboard (`packages/frontend/`) — React + Vite + Tailwind + React Query — 5s polling
- [x] Demo scripts (run-demo.sh, simulate-exploit.ts, reentrancy-demo.json)

### TODOs

- [x] Deploy contracts to Base Sepolia (5 contracts deployed, addresses in .env)
- [x] Install npm dependencies for api, frontend, cre-workflows (`pnpm install`)
- [ ] Implement CCIP cross-chain alerting (show code, explain to judges)
- [ ] Add VRF tie-breaker selection (show code, explain to judges)
- [ ] Deploy CRE workflows to Chainlink network
- [ ] Record demo video

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

## QUICK REFERENCE CARD

```
PROJECT: AEGIS Protocol (AI-Enhanced Guardian Intelligence System)
HACKATHON: Chainlink Convergence (Feb 6 - Mar 1, 2026)
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
  cd packages/agents-py && python -m pytest tests/ -v   # Agent tests (25 passing)
  npx tsx scripts/simulate-exploit.ts                    # Simulate attack

SERVICES:
  Python Agent API:  http://localhost:8000 (FastAPI docs at /docs)
  TypeScript API:    http://localhost:3000
  Frontend:          http://localhost:5173

TESTNET: Base Sepolia (84532)
```

---

*Last Updated: February 28, 2026*
*Version: 2.0.0 — All phases complete, contracts deployed*