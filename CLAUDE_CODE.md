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
| Data Feeds | Real-time price verification for anomaly detection |
| Data Streams | Sub-second monitoring for flash loan attacks |
| Automation | Scheduled health checks, deadline enforcement |
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
| LiquiditySentinel | Monitor TVL, withdrawals, flash loans | ElizaOS Agent + Custom Logic |
| OracleSentinel | Monitor price feeds, detect manipulation | ElizaOS Agent + Chainlink Data Feeds |
| GovernanceSentinel | Monitor proposals, detect malicious governance | ElizaOS Agent + Custom Logic |
| Consensus Coordinator | Aggregate sentinel signals, enforce 2/3 rule | TypeScript Service |
| ChainSherlock | Forensic analysis and reporting | ElizaOS Agent + AI Analysis |
| CRE Workflows | Verifiable execution, on-chain actions | Chainlink CRE (TypeScript) |
| Smart Contracts | State management, circuit breakers | Solidity |
| x402 Gateway | Payment processing | Coinbase x402 SDK |

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

AI Agents:
  - TypeScript 5.x
  - ElizaOS Framework
  - Custom Plugins

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
  - Foundry (forge test)
  - Vitest
  - Hardhat (for some integrations)
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
  - Google Gemini API (primary)
  - Anthropic Claude API (backup)
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
│   ├── cre-workflows/             # Chainlink CRE workflows
│   │   ├── src/
│   │   │   ├── workflows/
│   │   │   │   ├── threatDetection.workflow.ts
│   │   │   │   ├── forensicAnalysis.workflow.ts
│   │   │   │   └── healthCheck.workflow.ts
│   │   │   ├── capabilities/
│   │   │   │   ├── fetchSentinelData.ts
│   │   │   │   ├── analyzeWithAI.ts
│   │   │   │   └── triggerCircuitBreaker.ts
│   │   │   ├── triggers/
│   │   │   │   ├── cronTrigger.ts
│   │   │   │   ├── httpTrigger.ts
│   │   │   │   └── logTrigger.ts
│   │   │   └── types/
│   │   │       └── index.ts
│   │   ├── test/
│   │   │   └── workflows.test.ts
│   │   ├── cre.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── agents/                    # AI Sentinel Agents
│   │   ├── src/
│   │   │   ├── sentinels/
│   │   │   │   ├── LiquiditySentinel/
│   │   │   │   │   ├── index.ts
│   │   │   │   │   ├── character.json
│   │   │   │   │   ├── actions/
│   │   │   │   │   │   ├── monitorTVL.ts
│   │   │   │   │   │   ├── detectFlashLoan.ts
│   │   │   │   │   │   └── analyzeWithdrawals.ts
│   │   │   │   │   └── prompts/
│   │   │   │   │       └── analysis.ts
│   │   │   │   ├── OracleSentinel/
│   │   │   │   │   ├── index.ts
│   │   │   │   │   ├── character.json
│   │   │   │   │   ├── actions/
│   │   │   │   │   │   ├── monitorPriceFeeds.ts
│   │   │   │   │   │   ├── detectDeviation.ts
│   │   │   │   │   │   └── checkStaleness.ts
│   │   │   │   │   └── prompts/
│   │   │   │   │       └── analysis.ts
│   │   │   │   └── GovernanceSentinel/
│   │   │   │       ├── index.ts
│   │   │   │       ├── character.json
│   │   │   │       ├── actions/
│   │   │   │       │   ├── monitorProposals.ts
│   │   │   │       │   ├── analyzeProposal.ts
│   │   │   │       │   └── detectMalicious.ts
│   │   │   │       └── prompts/
│   │   │   │           └── analysis.ts
│   │   │   ├── sherlock/
│   │   │   │   ├── index.ts
│   │   │   │   ├── character.json
│   │   │   │   ├── actions/
│   │   │   │   │   ├── traceTransaction.ts
│   │   │   │   │   ├── classifyVulnerability.ts
│   │   │   │   │   ├── trackFunds.ts
│   │   │   │   │   └── generateReport.ts
│   │   │   │   └── prompts/
│   │   │   │       ├── forensicAnalysis.ts
│   │   │   │       └── reportGeneration.ts
│   │   │   ├── coordinator/
│   │   │   │   ├── index.ts
│   │   │   │   ├── consensus.ts
│   │   │   │   └── aggregator.ts
│   │   │   ├── plugins/
│   │   │   │   ├── chainlink-data-feeds/
│   │   │   │   ├── etherscan-api/
│   │   │   │   └── x402-payments/
│   │   │   └── shared/
│   │   │       ├── types.ts
│   │   │       ├── constants.ts
│   │   │       └── utils.ts
│   │   ├── test/
│   │   │   ├── LiquiditySentinel.test.ts
│   │   │   ├── OracleSentinel.test.ts
│   │   │   └── Consensus.test.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── api/                       # Backend API service
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── sentinel.ts
│   │   │   │   ├── forensics.ts
│   │   │   │   ├── reports.ts
│   │   │   │   └── health.ts
│   │   │   ├── middleware/
│   │   │   │   ├── x402Payment.ts
│   │   │   │   └── auth.ts
│   │   │   ├── services/
│   │   │   │   ├── sentinelService.ts
│   │   │   │   ├── forensicsService.ts
│   │   │   │   └── reportService.ts
│   │   │   └── index.ts
│   │   ├── test/
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── frontend/                  # React dashboard (minimal)
│       ├── src/
│       │   ├── components/
│       │   │   ├── ThreatDashboard.tsx
│       │   │   ├── SentinelStatus.tsx
│       │   │   ├── ForensicsReport.tsx
│       │   │   └── ProtocolHealth.tsx
│       │   ├── hooks/
│       │   │   ├── useSentinels.ts
│       │   │   └── useThreats.ts
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── public/
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── package.json
│
├── scripts/
│   ├── deploy-all.sh              # Deploy everything
│   ├── run-demo.sh                # Run hackathon demo
│   └── simulate-exploit.ts        # Simulate attack for testing
│
├── docs/
│   ├── architecture.md
│   ├── api-reference.md
│   ├── deployment.md
│   └── images/
│       └── architecture-diagram.png
│
├── demo/
│   ├── exploit-scenarios/         # Historical exploit data for demos
│   │   ├── euler-march-2023.json
│   │   ├── mango-markets.json
│   │   └── curve-july-2023.json
│   └── demo-script.md             # Demo walkthrough
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
| TVL drop in 5 min | > 20% | CRITICAL |
| TVL drop in 5 min | > 10% | HIGH |
| Single withdrawal | > 5% of TVL | HIGH |
| Flash loan detected | Any | MEDIUM (context-dependent) |
| Unusual withdraw pattern | Statistical anomaly | MEDIUM |

**Implementation**:

```typescript
// packages/agents/src/sentinels/LiquiditySentinel/actions/monitorTVL.ts

import { Action, IAgentRuntime } from "@elizaos/core";
import { ethers } from "ethers";

interface TVLSnapshot {
  timestamp: number;
  tvl: bigint;
  blockNumber: number;
}

interface ThreatAssessment {
  threatLevel: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  details: string;
  metrics: {
    currentTVL: string;
    previousTVL: string;
    changePercent: number;
    timeWindowSeconds: number;
  };
}

export const monitorTVL: Action = {
  name: "MONITOR_TVL",
  description: "Monitor Total Value Locked for anomalies",
  
  async handler(
    runtime: IAgentRuntime,
    message: any,
    state: any
  ): Promise<ThreatAssessment> {
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
    
    // Get current TVL
    const currentTVL = await fetchProtocolTVL(
      message.protocolAddress,
      provider
    );
    
    // Get historical snapshots (last 5 minutes)
    const snapshots = await getRecentSnapshots(
      message.protocolAddress,
      300 // 5 minutes
    );
    
    // Calculate change
    const oldestSnapshot = snapshots[0];
    const changePercent = calculateChange(oldestSnapshot.tvl, currentTVL);
    
    // Determine threat level
    let threatLevel: ThreatAssessment["threatLevel"] = "NONE";
    let confidence = 0.9;
    
    if (changePercent < -20) {
      threatLevel = "CRITICAL";
      confidence = 0.95;
    } else if (changePercent < -10) {
      threatLevel = "HIGH";
      confidence = 0.90;
    } else if (changePercent < -5) {
      threatLevel = "MEDIUM";
      confidence = 0.80;
    }
    
    return {
      threatLevel,
      confidence,
      details: `TVL changed by ${changePercent.toFixed(2)}% in last 5 minutes`,
      metrics: {
        currentTVL: currentTVL.toString(),
        previousTVL: oldestSnapshot.tvl.toString(),
        changePercent,
        timeWindowSeconds: 300
      }
    };
  }
};
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
| Rapid price movement | > 10% in 1 block | CRITICAL |

**Implementation**:

```typescript
// packages/agents/src/sentinels/OracleSentinel/actions/monitorPriceFeeds.ts

import { Action, IAgentRuntime } from "@elizaos/core";
import { ethers } from "ethers";

const CHAINLINK_ETH_USD = "0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1"; // Base Sepolia

interface PriceFeedAssessment {
  threatLevel: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  details: string;
  metrics: {
    protocolPrice: string;
    chainlinkPrice: string;
    deviationPercent: number;
    feedAge: number;
  };
}

export const monitorPriceFeeds: Action = {
  name: "MONITOR_PRICE_FEEDS",
  description: "Monitor price feeds for manipulation or staleness",
  
  async handler(
    runtime: IAgentRuntime,
    message: any,
    state: any
  ): Promise<PriceFeedAssessment> {
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
    
    // Get Chainlink price (source of truth)
    const chainlinkPrice = await getChainlinkPrice(
      CHAINLINK_ETH_USD,
      provider
    );
    
    // Get protocol's internal price
    const protocolPrice = await getProtocolPrice(
      message.protocolAddress,
      message.asset,
      provider
    );
    
    // Calculate deviation
    const deviationPercent = Math.abs(
      ((protocolPrice - chainlinkPrice) / chainlinkPrice) * 100
    );
    
    // Check feed freshness
    const feedAge = await getChainlinkFeedAge(CHAINLINK_ETH_USD, provider);
    
    // Determine threat level
    let threatLevel: PriceFeedAssessment["threatLevel"] = "NONE";
    let confidence = 0.9;
    let details = "";
    
    if (deviationPercent > 5) {
      threatLevel = "CRITICAL";
      confidence = 0.95;
      details = `Price deviation of ${deviationPercent.toFixed(2)}% detected - possible manipulation`;
    } else if (deviationPercent > 2) {
      threatLevel = "HIGH";
      details = `Significant price deviation of ${deviationPercent.toFixed(2)}%`;
    } else if (feedAge > 3600) {
      threatLevel = "HIGH";
      details = `Chainlink feed is ${feedAge}s old - stale data`;
    } else if (feedAge > 1800) {
      threatLevel = "MEDIUM";
      details = `Chainlink feed is ${feedAge}s old`;
    }
    
    return {
      threatLevel,
      confidence,
      details,
      metrics: {
        protocolPrice: protocolPrice.toString(),
        chainlinkPrice: chainlinkPrice.toString(),
        deviationPercent,
        feedAge
      }
    };
  }
};
```

### 6.3 Governance Sentinel

**Purpose**: Monitor governance proposals for malicious actions.

**What It Monitors**:

| Metric | Threat Level |
|--------|--------------|
| Proposal to change admin/owner | HIGH |
| Proposal to upgrade contract | MEDIUM |
| Proposal bypassing timelock | CRITICAL |
| Proposal with suspicious call data | HIGH |
| Flash loan voting detected | CRITICAL |

### 6.4 Consensus Coordinator

**Purpose**: Aggregate sentinel assessments and enforce 2/3 consensus rule.

```typescript
// packages/agents/src/coordinator/consensus.ts

interface SentinelVote {
  sentinelId: string;
  threatLevel: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  timestamp: number;
  signature: string;
}

interface ConsensusResult {
  consensusReached: boolean;
  finalThreatLevel: string;
  agreementRatio: number;
  votes: SentinelVote[];
  actionRecommended: "NONE" | "ALERT" | "CIRCUIT_BREAKER";
}

export async function reachConsensus(
  votes: SentinelVote[]
): Promise<ConsensusResult> {
  // Require at least 2 votes
  if (votes.length < 2) {
    return {
      consensusReached: false,
      finalThreatLevel: "UNKNOWN",
      agreementRatio: 0,
      votes,
      actionRecommended: "NONE"
    };
  }
  
  // Count votes by threat level
  const threatCounts = new Map<string, number>();
  for (const vote of votes) {
    const count = threatCounts.get(vote.threatLevel) || 0;
    threatCounts.set(vote.threatLevel, count + 1);
  }
  
  // Find majority
  let maxCount = 0;
  let majorityThreat = "NONE";
  for (const [threat, count] of threatCounts) {
    if (count > maxCount) {
      maxCount = count;
      majorityThreat = threat;
    }
  }
  
  const agreementRatio = maxCount / votes.length;
  const consensusReached = agreementRatio >= 0.67; // 2/3 rule
  
  // Determine action
  let actionRecommended: ConsensusResult["actionRecommended"] = "NONE";
  if (consensusReached) {
    if (majorityThreat === "CRITICAL") {
      actionRecommended = "CIRCUIT_BREAKER";
    } else if (majorityThreat === "HIGH" || majorityThreat === "MEDIUM") {
      actionRecommended = "ALERT";
    }
  }
  
  return {
    consensusReached,
    finalThreatLevel: majorityThreat,
    agreementRatio,
    votes,
    actionRecommended
  };
}
```

### 6.5 ChainSherlock

**Purpose**: Real-time forensic analysis when threats are detected.

**Capabilities**:

1. **Transaction Graph Analysis**: Trace the full call stack of attack transactions
2. **Vulnerability Classification**: Identify the type of exploit (reentrancy, price manipulation, etc.)
3. **Fund Tracking**: Follow where stolen funds move
4. **Report Generation**: Create actionable, structured reports

```typescript
// packages/agents/src/sherlock/actions/traceTransaction.ts

interface TransactionTrace {
  txHash: string;
  from: string;
  to: string;
  value: string;
  gasUsed: number;
  internalCalls: InternalCall[];
  tokenTransfers: TokenTransfer[];
  logs: Log[];
}

interface InternalCall {
  from: string;
  to: string;
  value: string;
  input: string;
  output: string;
  type: "CALL" | "DELEGATECALL" | "STATICCALL" | "CREATE" | "CREATE2";
  depth: number;
}

export async function traceTransaction(
  txHash: string,
  provider: ethers.Provider
): Promise<TransactionTrace> {
  // Use debug_traceTransaction if available
  const trace = await provider.send("debug_traceTransaction", [
    txHash,
    { tracer: "callTracer" }
  ]);
  
  // Parse internal calls
  const internalCalls = parseInternalCalls(trace);
  
  // Extract token transfers from logs
  const receipt = await provider.getTransactionReceipt(txHash);
  const tokenTransfers = extractTokenTransfers(receipt.logs);
  
  return {
    txHash,
    from: trace.from,
    to: trace.to,
    value: trace.value,
    gasUsed: parseInt(trace.gasUsed, 16),
    internalCalls,
    tokenTransfers,
    logs: receipt.logs
  };
}
```

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

## 11. AI AGENT SPECIFICATION

### 11.1 Agent Characters

Each sentinel has a character.json defining its personality:

```json
// packages/agents/src/sentinels/LiquiditySentinel/character.json
{
  "name": "AEGIS Liquidity Sentinel",
  "description": "Specialized AI agent monitoring DeFi protocol liquidity for anomalies",
  "personality": [
    "vigilant",
    "precise",
    "cautious"
  ],
  "expertise": [
    "DeFi liquidity analysis",
    "Flash loan detection",
    "TVL monitoring",
    "Withdrawal pattern analysis"
  ],
  "responseStyle": {
    "format": "structured",
    "includesConfidence": true,
    "includesEvidence": true
  }
}
```

### 11.2 AI Prompts

**Threat Analysis Prompt**:

```typescript
// packages/agents/src/sentinels/LiquiditySentinel/prompts/analysis.ts

export const LIQUIDITY_ANALYSIS_PROMPT = `
You are the AEGIS Liquidity Sentinel, an AI security agent monitoring DeFi protocols.

Analyze the following protocol metrics and determine if there is an anomaly indicating a potential exploit.

PROTOCOL DATA:
- Protocol: {{protocolName}}
- Current TVL: {{currentTVL}}
- TVL 5 minutes ago: {{previousTVL}}
- TVL change: {{changePercent}}%
- Recent large withdrawals: {{largeWithdrawals}}
- Flash loans in last 10 blocks: {{flashLoanCount}}
- Unusual addresses involved: {{unusualAddresses}}

HISTORICAL CONTEXT:
- Average daily TVL change: {{avgDailyChange}}%
- Maximum normal withdrawal: {{maxNormalWithdrawal}}
- Previous incidents: {{previousIncidents}}

CHAINLINK REFERENCE DATA:
- ETH/USD: {{ethPrice}}
- Data Feed last update: {{feedAge}} seconds ago

Based on this data, provide your assessment in the following JSON format:
{
  "threatLevel": "NONE|LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "indicators": ["List of specific anomalies detected"],
  "recommendation": "NONE|ALERT|INVESTIGATE|CIRCUIT_BREAKER"
}

Be conservative - only flag HIGH or CRITICAL if there are clear indicators of an exploit in progress.
False positives are costly but missed exploits are catastrophic.
`;
```

**Forensic Analysis Prompt**:

```typescript
// packages/agents/src/sherlock/prompts/forensicAnalysis.ts

export const FORENSIC_ANALYSIS_PROMPT = `
You are ChainSherlock, an AI forensic analyst for blockchain exploits.

Analyze the following transaction trace and identify the attack vector.

TRANSACTION DATA:
- Hash: {{txHash}}
- From: {{from}}
- To: {{to}}
- Value: {{value}}
- Block: {{blockNumber}}

INTERNAL CALLS:
{{internalCalls}}

TOKEN TRANSFERS:
{{tokenTransfers}}

AFFECTED PROTOCOL:
- Name: {{protocolName}}
- Contract: {{protocolAddress}}
- Type: {{protocolType}}

Provide your forensic analysis in the following JSON format:
{
  "attackClassification": {
    "primaryType": "REENTRANCY|PRICE_MANIPULATION|FLASH_LOAN|ORACLE_MANIPULATION|ACCESS_CONTROL|LOGIC_ERROR|OTHER",
    "confidence": 0.0-1.0,
    "description": "Detailed description of the attack"
  },
  "attackFlow": [
    {"step": 1, "action": "Description", "contract": "0x..."},
    ...
  ],
  "rootCause": {
    "vulnerability": "Description of the vulnerability",
    "affectedCode": "Function or code section",
    "recommendation": "How to fix"
  },
  "impactAssessment": {
    "fundsAtRisk": "Amount in USD",
    "affectedUsers": "Estimated count",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL"
  },
  "fundTracking": {
    "destinations": [
      {"address": "0x...", "amount": "...", "type": "CEX|DEX|MIXER|BRIDGE|UNKNOWN"}
    ],
    "recoveryPossibility": "HIGH|MEDIUM|LOW|NONE"
  }
}
`;
```

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

### 15.2 Agent Tests

```bash
# Run agent tests
cd packages/agents
pnpm test

# Run with coverage
pnpm test:coverage

# Run specific sentinel tests
pnpm test -- --grep "LiquiditySentinel"
```

**Key Test Cases**:
- Individual sentinel detection logic
- Consensus mechanism
- AI prompt responses (mocked)
- Integration with mock protocols

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
# Install dependencies
pnpm install

# Install CRE CLI
curl -sSL https://cre.chain.link/install.sh | bash

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Copy environment file
cp .env.example .env
# Fill in all required values
```

### 16.2 Deploy Contracts

```bash
cd packages/contracts

# Deploy to Base Sepolia
forge script script/Deploy.s.sol:DeployAegis \
  --rpc-url $BASE_SEPOLIA_RPC \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast \
  --verify

# Note deployed addresses
# Update .env with contract addresses
```

### 16.3 Deploy CRE Workflows

```bash
cd packages/cre-workflows

# Login to CRE
cre auth login

# Deploy threat detection workflow
cre workflow deploy threatDetection --network base-sepolia

# Deploy forensics workflow
cre workflow deploy forensicAnalysis --network base-sepolia

# Note workflow IDs
```

### 16.4 Start Agents

```bash
cd packages/agents

# Start all sentinels
pnpm start

# Or start individually
pnpm start:liquidity
pnpm start:oracle
pnpm start:governance
pnpm start:sherlock
```

### 16.5 Start API

```bash
cd packages/api

# Start API server
pnpm start

# Server runs on http://localhost:3000
```

### 16.6 Verification Checklist

- [ ] Contracts deployed and verified on explorer
- [ ] CRE workflows deployed and triggered successfully
- [ ] All sentinels reporting heartbeats
- [ ] x402 payments working (test with small amount)
- [ ] CCIP test message sent successfully
- [ ] Data Feeds returning correct prices
- [ ] Frontend connected and displaying data

---

## 17. ENVIRONMENT VARIABLES

```bash
# .env.example

# ============ Network ============
BASE_SEPOLIA_RPC=https://sepolia.base.org
ETHEREUM_SEPOLIA_RPC=https://rpc.sepolia.org
ARBITRUM_SEPOLIA_RPC=https://sepolia-rollup.arbitrum.io/rpc

# ============ Accounts ============
DEPLOYER_PRIVATE_KEY=0x...
SENTINEL_OPERATOR_PRIVATE_KEY=0x...

# ============ Deployed Contracts ============
SENTINEL_REGISTRY_ADDRESS=0x...
CIRCUIT_BREAKER_ADDRESS=0x...
THREAT_REPORT_ADDRESS=0x...
REPUTATION_TRACKER_ADDRESS=0x...

# ============ Chainlink ============
CRE_API_KEY=...
CRE_WORKFLOW_ID=...
CHAINLINK_ETH_USD_FEED=0x4aDC67696bA383F43DD60A9e78F2C97Fbbfc7cb1
CHAINLINK_VRF_COORDINATOR=0x...
CHAINLINK_LINK_TOKEN=0xE4aB69C077896252FAFBD49EFD26B5D171A32410

# ============ x402 ============
X402_FACILITATOR_URL=https://x402.org/facilitator
AEGIS_PAYMENT_RECEIVER=0x...

# ============ AI ============
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...

# ============ External APIs ============
ETHERSCAN_API_KEY=...
BASESCAN_API_KEY=...

# ============ IPFS ============
PINATA_API_KEY=...
PINATA_SECRET_KEY=...

# ============ Monitoring ============
PROTOCOL_TO_MONITOR=0x...  # Address of protocol being protected
```

---

## 18. COMMON TASKS & COMMANDS

### Development Commands

```bash
# Start development environment
pnpm dev

# Build all packages
pnpm build

# Run linting
pnpm lint

# Format code
pnpm format

# Clean build artifacts
pnpm clean
```

### Contract Commands

```bash
# Compile contracts
forge build

# Run tests
forge test

# Deploy to testnet
forge script script/Deploy.s.sol --broadcast

# Verify contract
forge verify-contract <address> <contract> --chain base-sepolia
```

### CRE Commands

```bash
# Initialize new workflow
cre init <name>

# Simulate workflow
cre workflow simulate <name>

# Deploy workflow
cre workflow deploy <name> --network base-sepolia

# Check workflow status
cre workflow status <workflow-id>

# View logs
cre workflow logs <workflow-id>
```

### Agent Commands

```bash
# Start specific agent
pnpm start:liquidity
pnpm start:oracle
pnpm start:governance
pnpm start:sherlock

# Run agent tests
pnpm test

# Check agent health
curl http://localhost:3001/health
```

### Demo Commands

```bash
# Run full demo
./scripts/run-demo.sh

# Simulate specific exploit
npx ts-node scripts/simulate-exploit.ts euler

# Generate demo report
npx ts-node scripts/generate-demo-report.ts
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

3. **ElizaOS Plugin Conflicts**: Some ElizaOS plugins may conflict. If issues arise, disable unused plugins in character.json.

4. **Data Streams Access**: Data Streams requires separate approval. Fall back to Data Feeds if not available.

### TODOs

- [ ] Implement CCIP cross-chain alerting
- [ ] Add VRF tie-breaker selection
- [ ] Build frontend dashboard
- [ ] Add more exploit scenarios for demos
- [ ] Implement subscription management
- [ ] Add Telegram/Discord alert notifications
- [ ] Optimize gas usage in contracts
- [ ] Add multi-language support for reports

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

### ElizaOS

- GitHub: https://github.com/elizaOS/eliza
- Docs: https://docs.elizaos.ai

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
PRIZE: $100K+ total, $20K for Risk track

CHAINLINK SERVICES (5 = +4 bonus):
✓ CRE - Workflow orchestration
✓ Data Feeds - Price verification
✓ Data Streams - Real-time monitoring
✓ Automation - Scheduled checks
✓ VRF - Fair tie-breaker
✓ CCIP - Cross-chain alerts

KEY COMMANDS:
  pnpm install          # Install all deps
  pnpm dev              # Start dev environment
  forge test            # Run contract tests
  cre workflow simulate # Test CRE workflow
  ./scripts/run-demo.sh # Run full demo

KEY FILES:
  packages/contracts/src/core/CircuitBreaker.sol
  packages/cre-workflows/src/workflows/threatDetection.workflow.ts
  packages/agents/src/sentinels/LiquiditySentinel/index.ts
  packages/api/src/middleware/x402Payment.ts

TESTNET: Base Sepolia (84532)
DEPLOYER: Check .env for addresses
```

---

*Last Updated: January 2026*
*Version: 1.0.0*