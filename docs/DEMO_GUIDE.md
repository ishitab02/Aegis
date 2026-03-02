# AEGIS Protocol - Demo Guide

Step-by-step instructions for running the AEGIS demo for judges or local testing.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Verify Services](#verify-services)
4. [Demo Scenario 1: Normal Monitoring](#demo-scenario-1-normal-monitoring)
5. [Demo Scenario 2: TVL Drop Attack](#demo-scenario-2-tvl-drop-attack)
6. [Demo Scenario 3: Oracle Manipulation](#demo-scenario-3-oracle-manipulation)
7. [Demo Scenario 4: Governance Attack](#demo-scenario-4-governance-attack)
8. [Demo Scenario 5: Combined Attack](#demo-scenario-5-combined-attack)
9. [Demo Scenario 6: Forensic Analysis](#demo-scenario-6-forensic-analysis)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Check Command |
|----------|---------|---------------|
| Node.js | >= 20 | `node --version` |
| pnpm | >= 9 | `pnpm --version` |
| Python | >= 3.11 | `python3 --version` |
| Foundry | latest | `forge --version` |

### Environment Variables

Ensure `.env` is configured with:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (for full functionality)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Pre-configured (deployed contracts on Base Sepolia)
SENTINEL_REGISTRY_ADDRESS=0xd34FC1ee378F342EFb92C0D334362B9E577b489f
CIRCUIT_BREAKER_ADDRESS=0xa0eE49660252B353830ADe5de0Ca9385647F85b5
MOCK_PROTOCOL_ADDRESS=0x11887863b89F1bE23A650909135ffaCFab666803
```

---

## Quick Start

### Option A: One Command (Recommended)

```bash
bash scripts/run-demo.sh
```

This starts all three services and opens the dashboard.

### Option B: Manual Start (Three Terminals)

**Terminal 1 — Python Agent API (port 8000)**
```bash
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — TypeScript API (port 3000)**
```bash
cd packages/api
npx tsx src/index.ts
```

**Terminal 3 — Frontend Dashboard (port 5173)**
```bash
cd packages/frontend
pnpm dev
```

### Open Dashboard

Navigate to: **http://localhost:5173**

---

## Verify Services

Run these checks to ensure everything is working:

### Health Checks

```bash
# Python Agent API
curl -s http://localhost:8000/api/v1/health | jq

# Expected:
# {
#   "status": "healthy",
#   "sentinels": { "active": 3, "total": 3 }
# }

# TypeScript API
curl -s http://localhost:3000/api/v1/health | jq

# Expected:
# {
#   "status": "healthy",
#   "services": {
#     "agents": "operational",
#     "database": "operational"
#   }
# }
```

### Sentinel Status

```bash
curl -s http://localhost:3000/api/v1/sentinel/aggregate | jq
```

You should see all three sentinels with status information.

---

## Demo Scenario 1: Normal Monitoring

**Goal**: Show the system in a healthy state with no threats.

### Steps

1. Open the dashboard at http://localhost:5173
2. Observe the three sentinel cards — all should show "NONE" threat level
3. Click "Run Scan" or wait for auto-refresh (5 seconds)

### Expected Result

```
┌─────────────────────────────────────────────────┐
│  LIQUIDITY SENTINEL     │ Status: NONE (green) │
│  ORACLE SENTINEL        │ Status: NONE (green) │
│  GOVERNANCE SENTINEL    │ Status: NONE (green) │
├─────────────────────────────────────────────────┤
│  CONSENSUS: Not reached (no threat detected)   │
└─────────────────────────────────────────────────┘
```

### CLI Alternative

```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x11887863b89F1bE23A650909135ffaCFab666803"}'
```

---

## Demo Scenario 2: TVL Drop Attack

**Goal**: Simulate rapid fund drainage triggering the Liquidity Sentinel.

### Attack Explanation

An attacker is draining funds from the protocol (e.g., reentrancy exploit). TVL drops by 25% in one detection cycle.

### Steps

1. Open dashboard and terminal side-by-side
2. Run the simulation:

```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0x1",
    "simulate_tvl_drop_percent": 25
  }'
```

3. Watch the dashboard update

### Expected Result

```json
{
  "sentinels": [
    {
      "type": "LIQUIDITY",
      "assessment": {
        "threat_level": "CRITICAL",
        "confidence": 0.95,
        "details": "TVL dropped by 25.0%, exceeding critical threshold of 20%"
      }
    },
    {
      "type": "ORACLE",
      "assessment": { "threat_level": "NONE" }
    },
    {
      "type": "GOVERNANCE",
      "assessment": { "threat_level": "NONE" }
    }
  ],
  "consensus": {
    "reached": false,
    "final_threat_level": "NONE",
    "agreement_ratio": 0.33
  }
}
```

**Note**: With only 1 sentinel flagging CRITICAL, consensus is NOT reached (requires 2/3).

---

## Demo Scenario 3: Oracle Manipulation

**Goal**: Simulate price feed manipulation triggering the Oracle Sentinel.

### Attack Explanation

An attacker is manipulating the on-chain price (e.g., via flash loan to skew a DEX pool). Protocol's internal price deviates 8% from Chainlink.

### Steps

```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0x1",
    "simulate_price_deviation_percent": 8
  }'
```

### Expected Result

```json
{
  "sentinels": [
    {
      "type": "LIQUIDITY",
      "assessment": { "threat_level": "NONE" }
    },
    {
      "type": "ORACLE",
      "assessment": {
        "threat_level": "CRITICAL",
        "confidence": 0.95,
        "details": "Price deviation of 8.0% exceeds critical threshold of 5%"
      }
    },
    {
      "type": "GOVERNANCE",
      "assessment": { "threat_level": "NONE" }
    }
  ],
  "consensus": {
    "reached": false,
    "final_threat_level": "NONE",
    "agreement_ratio": 0.33
  }
}
```

---

## Demo Scenario 4: Governance Attack

**Goal**: Simulate a malicious governance proposal triggering the Governance Sentinel.

### Attack Explanation

An attacker submits a proposal with a suspiciously short voting period, attempting to push through a malicious change before community notices.

### Steps

```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0x1",
    "simulate_short_voting_period": true
  }'
```

### Expected Result

```json
{
  "sentinels": [
    {
      "type": "LIQUIDITY",
      "assessment": { "threat_level": "NONE" }
    },
    {
      "type": "ORACLE",
      "assessment": { "threat_level": "NONE" }
    },
    {
      "type": "GOVERNANCE",
      "assessment": {
        "threat_level": "HIGH",
        "confidence": 0.85,
        "details": "Voting period of 50 blocks is below minimum threshold of 100"
      }
    }
  ],
  "consensus": {
    "reached": false,
    "agreement_ratio": 0.33
  }
}
```

---

## Demo Scenario 5: Combined Attack (Circuit Breaker Triggered!)

**Goal**: Simulate a coordinated attack that triggers consensus and the circuit breaker.

### Attack Explanation

Sophisticated attack combining:
- Rapid TVL drainage (25% drop) — reentrancy/flash loan
- Oracle manipulation (6% deviation) — DEX price manipulation

When 2/3 sentinels agree on HIGH/CRITICAL, the circuit breaker fires.

### Steps

```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0x1",
    "simulate_tvl_drop_percent": 25,
    "simulate_price_deviation_percent": 6
  }'
```

### Expected Result

```json
{
  "sentinels": [
    {
      "type": "LIQUIDITY",
      "assessment": {
        "threat_level": "CRITICAL",
        "confidence": 0.95
      }
    },
    {
      "type": "ORACLE",
      "assessment": {
        "threat_level": "CRITICAL",
        "confidence": 0.95
      }
    },
    {
      "type": "GOVERNANCE",
      "assessment": { "threat_level": "NONE" }
    }
  ],
  "consensus": {
    "reached": true,
    "final_threat_level": "CRITICAL",
    "agreement_ratio": 0.67,
    "recommended_action": "CIRCUIT_BREAKER"
  }
}
```

**Dashboard**: Should show red CRITICAL status with "Circuit Breaker Triggered" message.

**Telegram**: If configured, you'll receive an alert.

---

## Demo Scenario 6: Forensic Analysis

**Goal**: Show ChainSherlock analyzing a suspicious transaction.

### Steps

1. First, list existing forensic reports:

```bash
curl -s http://localhost:3000/api/v1/forensics | jq
```

2. Request a new forensic analysis:

```bash
curl -X POST http://localhost:3000/api/v1/forensics \
  -H "Content-Type: application/json" \
  -d '{
    "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "protocol_address": "0x11887863b89F1bE23A650909135ffaCFab666803"
  }' | jq
```

### Expected Result

```json
{
  "report_id": "FR-1709...",
  "status": "COMPLETE",
  "attack_classification": {
    "type": "REENTRANCY",
    "confidence": 0.85
  },
  "attack_flow": [
    "Attacker deploys malicious contract",
    "Initiates withdrawal",
    "Callback triggers recursive withdrawals",
    "Funds drained before state update"
  ],
  "recommendations": [
    "Implement checks-effects-interactions pattern",
    "Add reentrancy guard",
    "Use pull payment pattern"
  ]
}
```

---

## Troubleshooting

### Service Won't Start

**Python API (port 8000)**
```bash
# Check if port is in use
lsof -ti:8000 | xargs kill -9

# Verify Python environment
cd packages/agents-py
source venv/bin/activate
pip install -r requirements.txt
```

**TypeScript API (port 3000)**
```bash
# Check if port is in use
lsof -ti:3000 | xargs kill -9

# Reinstall dependencies
cd packages/api
pnpm install
```

### "Connection Refused" Errors

Ensure services started in this order:
1. Python API first (port 8000)
2. TypeScript API second (port 3000) — depends on Python API
3. Frontend last (port 5173)

Wait 5 seconds between each service start.

### Dashboard Shows "Error Loading Data"

```bash
# Check if TS API can reach Python API
curl http://localhost:3000/api/v1/sentinel/aggregate

# If error, check Python API directly
curl http://localhost:8000/api/v1/sentinel/aggregate
```

### Consensus Never Reached

Remember: Consensus requires **2 of 3** sentinels to agree on HIGH or CRITICAL.

To trigger consensus, combine multiple simulation parameters:
```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25,"simulate_price_deviation_percent":6}'
```

### Telegram Notifications Not Working

1. Verify environment variables:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

2. Test the bot manually:
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": \"Test from AEGIS\"}"
```

### Reset Demo State

To clear all alerts and start fresh:
```bash
# Remove SQLite database
rm -f packages/api/data/aegis.db

# Restart TypeScript API
cd packages/api && npx tsx src/index.ts
```

---

## Demo Timing Guide

For video recording or live demos, here's the recommended pacing:

| Demo | Duration | Key Moment |
|------|----------|------------|
| Show healthy dashboard | 15 sec | All green |
| TVL attack (single sentinel) | 20 sec | One red, no consensus |
| Combined attack (consensus!) | 30 sec | Two red, circuit breaker |
| Show Telegram alert | 10 sec | Phone notification |
| Forensic report | 25 sec | Attack classification |

**Total**: ~2 minutes of demo content (leaves room for explanation)

---

## Quick Reference Commands

```bash
# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:3000/api/v1/health

# Normal scan (no simulation)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1"}'

# TVL attack (CRITICAL)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25}'

# Oracle attack (CRITICAL)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_price_deviation_percent":8}'

# Combined attack (triggers circuit breaker)
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25,"simulate_price_deviation_percent":6}'

# List alerts
curl http://localhost:3000/api/v1/alerts

# List forensic reports
curl http://localhost:3000/api/v1/forensics
```
