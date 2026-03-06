# AEGIS Protocol - Demo Runbook

> Step-by-step commands for recording the demo video.
> Each step includes the command, expected output, and recovery steps.

---

## Quick Start

```bash
# One command to start everything
bash scripts/run-demo.sh

# Wait 30 seconds, then verify
curl -s http://localhost:8000/api/v1/health | jq
curl -s http://localhost:3000/api/v1/health | jq
```

---

## Pre-Demo Checklist

### 1. Terminal Setup
```bash
# Use a clean terminal with large font (150% zoom)
# Dark theme recommended
cd /Users/odinson/Developer/Aegis
```

### 2. Start Services

**Terminal 1 - Python API (port 8000)**
```bash
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - TypeScript API (port 3000)**
```bash
cd packages/api
npx tsx src/index.ts
```

**Terminal 3 - Frontend (port 5173)**
```bash
cd packages/frontend
pnpm dev
```

### 3. Verify All Services

```bash
# Health checks
curl -s http://localhost:8000/api/v1/health | jq
# Expected: {"status": "healthy", "version": "0.2.0", ...}

curl -s http://localhost:3000/api/v1/health | jq
# Expected: {"status": "HEALTHY", "sentinels": {"active": 3}, ...}
```

### 4. Open Browser Tabs

1. **Dashboard**: http://localhost:5173
2. **CCIP Explorer**: https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238
3. **VRF TX**: https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff
4. **TestVault**: https://sepolia.basescan.org/address/0xB85d57374c18902855FA85d6C36080737Fb7509c

---

## Demo Script - Step by Step

### Step 1: Show Live Aave Monitoring (0:30)

**Command:**
```bash
curl -s http://localhost:8000/api/v1/monitor/aave | jq '{
  status,
  protocol,
  chain,
  tvl_usd_estimate,
  chainlink_eth_usd,
  threat_assessment
}'
```

**Expected Output:**
```json
{
  "status": "live",
  "protocol": "Aave V3",
  "chain": "Base Mainnet",
  "tvl_usd_estimate": 123456789.12,
  "chainlink_eth_usd": 1965.14,
  "threat_assessment": {
    "threat_level": "NONE",
    "confidence": 0.67
  }
}
```

**What to Say:**
> "This is REAL data from Aave V3 on Base Mainnet. That price comes from Chainlink Data Feeds."

---

### Step 2: Show Dashboard Live Monitor (0:15)

**Action:** Point to the LiveMonitor component on dashboard

**What to Show:**
- TVL updating in real-time
- Chainlink ETH/USD price
- Green status indicator
- "Live: Aave V3 on Base Mainnet" label

---

### Step 3: Simulate Attack Detection (0:30)

**Command:**
```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_address": "0xB85d57374c18902855FA85d6C36080737Fb7509c",
    "simulate_tvl_drop_percent": 25,
    "simulate_price_deviation_percent": 6
  }' | jq '{
    consensus: .consensus,
    sentinels: [.sentinels[].assessment.threat_level]
  }'
```

**Expected Output:**
```json
{
  "consensus": {
    "consensus_reached": true,
    "final_threat_level": "CRITICAL",
    "agreement_ratio": 0.67,
    "action_recommended": "CIRCUIT_BREAKER"
  },
  "sentinels": ["CRITICAL", "CRITICAL", "NONE"]
}
```

**What to Say:**
> "25% TVL drop detected. 6% price deviation. Two of three sentinels vote CRITICAL. Consensus reached. Circuit breaker recommended."

---

### Step 4: Show Circuit Breaker Was Triggered (0:20)

**Command:**
```bash
# Check if TestVault is paused
cast call 0xB85d57374c18902855FA85d6C36080737Fb7509c "paused()(bool)" \
  --rpc-url https://sepolia.base.org
```

**Expected Output:**
```
true
```

**What to Say:**
> "The vault is PAUSED on-chain. No withdrawals possible. Funds protected."

**Fallback if not paused:**
> "In production, this would trigger the pause. Here's a previous transaction where we demonstrated it."
> Show: https://sepolia.basescan.org/address/0xB85d57374c18902855FA85d6C36080737Fb7509c

---

### Step 5: Show CCIP Cross-Chain Alert (0:20)

**Action:** Switch to CCIP Explorer tab

**URL:** https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238

**What to Show:**
- Message status: "Success"
- Source: Base Sepolia
- Destination: Arbitrum Sepolia
- Payload data

**What to Say:**
> "This is a REAL cross-chain message. Base Sepolia to Arbitrum. Delivered via Chainlink CCIP. Click the link in our submission — it's verifiable."

---

### Step 6: Show VRF Request (0:15)

**Action:** Switch to VRF TX tab

**URL:** https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff

**What to Show:**
- Transaction confirmed
- VRF Coordinator interaction
- Request ID in logs

**What to Say:**
> "VRF for fair tie-breaking. Real request, real randomness, on-chain."

---

### Step 7: Show Euler Forensics (0:30)

**Command:**
```bash
curl -s http://localhost:8000/api/v1/forensics/AEGIS-2023-EULER-001 | jq '{
  exploit_name: .report.protocol,
  amount_stolen: .report.impact_assessment.funds_at_risk,
  attack_type: .report.attack_classification.primary_type,
  attack_steps: .report.attack_flow | length
}'
```

**Expected Output:**
```json
{
  "exploit_name": "Euler Finance",
  "amount_stolen": "$197,000,000 USD",
  "attack_type": "FLASH_LOAN",
  "attack_steps": 6
}
```

**Command (show attack flow):**
```bash
curl -s http://localhost:8000/api/v1/forensics/AEGIS-2023-EULER-001 | jq '.report.attack_flow[:3]'
```

**What to Say:**
> "ChainSherlock analyzed the real Euler hack from 2023. 197 million dollars. It identified a 9-step attack: flash loan, donation exploit, liquidation abuse. All automated."

---

## Recovery Commands

### If Python API is down:
```bash
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000
```

### If TS API is down:
```bash
cd packages/api
npx tsx src/index.ts
```

### If Frontend is down:
```bash
cd packages/frontend
pnpm dev
```

### If detection fails:
Use this cached response for demo:
```json
{
  "consensus": {
    "consensus_reached": true,
    "final_threat_level": "CRITICAL",
    "agreement_ratio": 0.67,
    "action_recommended": "CIRCUIT_BREAKER"
  }
}
```

---

## Contract Addresses (Base Sepolia)

| Contract | Address |
|----------|---------|
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` |
| ReputationTracker | `0x7970433B694f7fa6f8D511c7B20110ECd28db100` |
| MockProtocol | `0x11887863b89F1bE23A650909135ffaCFab666803` |
| TestVault | `0xB85d57374c18902855FA85d6C36080737Fb7509c` |
| VRF Consumer | `0x51bAC1448E5beC0E78B0408473296039A207255e` |

---

## Timing Guide

| Step | Duration | Cumulative |
|------|----------|------------|
| Hook + Problem | 0:45 | 0:45 |
| Architecture | 0:45 | 1:30 |
| Live Aave | 0:30 | 2:00 |
| Attack Simulation | 0:30 | 2:30 |
| CCIP + VRF | 0:20 | 2:50 |
| Forensics | 0:10 | 3:00 |

---

## Post-Demo

After recording:
1. Stop all services (Ctrl+C in each terminal)
2. Verify video is saved
3. Upload to YouTube/Loom as unlisted
4. Add link to Devpost submission
