# AEGIS Protocol - Judge Cheatsheet

> **One-pager with all verifiable proof links for hackathon judges**

---

## Quick Facts

| Item | Value |
|------|-------|
| **Project** | AEGIS Protocol (AI-Enhanced Guardian Intelligence System) |
| **Track** | Risk & Compliance + AI |
| **Chainlink Services** | 5 (CRE + Data Feeds + Automation + VRF + CCIP) |
| **Network** | Base Sepolia (84532) |
| **Test Coverage** | 147 Python tests passing |

---

## Chainlink Services Used (5 = +4 Bonus Points)

| # | Service | Purpose | Proof |
|---|---------|---------|-------|
| 1 | **CRE** | Workflow orchestration | Simulation passed, blocked on deploy access |
| 2 | **Data Feeds** | ETH/USD price verification | Live in `/api/v1/monitor/aave` |
| 3 | **Automation** | 30-second monitoring cycles | Cron trigger in CRE workflow |
| 4 | **VRF** | Fair tie-breaker selection | [BaseScan TX](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |
| 5 | **CCIP** | Cross-chain alerts | [CCIP Explorer](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238) |

---

## On-Chain Proof Links (Click to Verify)

### CCIP Cross-Chain Alert
- **Source TX**: [0x6339...2303](https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303)
- **Message ID**: [0x0cc3...8238](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238)
- **Route**: Base Sepolia → Arbitrum Sepolia

### VRF Randomness Request
- **Request TX**: [0x761c...45ff](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff)
- **Consumer**: `0x51bAC1448E5beC0E78B0408473296039A207255e`

### Circuit Breaker Demo
- **TestVault**: [0xB85d...509c](https://sepolia.basescan.org/address/0xB85d57374c18902855FA85d6C36080737Fb7509c)
- **CircuitBreaker**: [0xa0eE...85b5](https://sepolia.basescan.org/address/0xa0eE49660252B353830ADe5de0Ca9385647F85b5)

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

## Live Demo Endpoints

| Endpoint | URL | What It Shows |
|----------|-----|---------------|
| Dashboard | http://localhost:5173 | Real-time monitoring UI |
| Health Check | http://localhost:8000/api/v1/health | System status |
| Live Aave | http://localhost:8000/api/v1/monitor/aave | Real Aave V3 TVL (Base Mainnet) |
| Detection | POST http://localhost:8000/api/v1/detect | Simulate attack detection |
| Forensics | http://localhost:8000/api/v1/forensics/demo/euler | Euler hack analysis |

---

## Key Technical Achievements

### 1. Real DeFi Monitoring
- Monitors **actual Aave V3 on Base Mainnet** (not mock data)
- TVL pulled from on-chain reserve data
- Price from Chainlink ETH/USD feed

### 2. AI-Powered Detection
- 3 specialized sentinel agents (Liquidity, Oracle, Governance)
- CrewAI + Claude for contextual threat analysis
- 2/3 consensus required for circuit breaker

### 3. Automated Response
- Circuit breaker triggers on CRITICAL consensus
- Pauses vault withdrawals in <30 seconds
- Cross-chain alert propagation via CCIP

### 4. Forensic Analysis
- ChainSherlock analyzes real exploits (Euler Finance demo)
- Transaction graph tracing
- Attack classification and fund tracking

---

## Verification Commands

```bash
# Check TestVault is paused
cast call 0xB85d57374c18902855FA85d6C36080737Fb7509c "paused()(bool)" --rpc-url https://sepolia.base.org

# Get live Aave TVL
curl -s http://localhost:8000/api/v1/monitor/aave | jq '.tvl_usd_estimate'

# Run detection simulation
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0xB85d57374c18902855FA85d6C36080737Fb7509c","simulate_tvl_drop_percent":25}'
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                      AEGIS PROTOCOL                          │
├─────────────────────────────────────────────────────────────┤
│  Protected Protocols: Aave V3, Uniswap V3, Compound V3      │
│                            ↓                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  SENTINELSWARM (3 AI Agents)                        │    │
│  │  Liquidity │ Oracle │ Governance                    │    │
│  │       ↓         ↓         ↓                         │    │
│  │  CONSENSUS COORDINATOR (2/3 majority)               │    │
│  └─────────────────────────────────────────────────────┘    │
│                            ↓ if CRITICAL                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  RESPONSE: Circuit Breaker │ CCIP Alert │ Forensics │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  CHAINLINK: CRE │ Data Feeds │ Automation │ VRF │ CCIP      │
└──────────────────────────────────────────────────────────────┘
```

---

## Links

| Resource | URL |
|----------|-----|
| **GitHub** | https://github.com/aegis-protocol |
| **Demo Video** | [YouTube/Loom link here] |
| **Devpost** | [Devpost submission link] |

---

*Generated for Chainlink Convergence Hackathon 2026*
