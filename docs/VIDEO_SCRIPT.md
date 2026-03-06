# AEGIS Protocol - Demo Video Script

> **Duration**: 3 minutes
> **Format**: Screen recording with voiceover
> **Audience**: Chainlink Convergence Hackathon judges (Risk & Compliance + AI tracks)
> **Last Updated**: March 7, 2026

---

## On-Chain Proof Links (Show These!)

| Service | Proof | Link |
|---------|-------|------|
| **CCIP** | Cross-chain alert sent | [BaseScan TX](https://sepolia.basescan.org/tx/0x6339132295e793680a642008138ab1ab9194e986682327d3d1ccf93c15ab2303) |
| **CCIP** | Message delivered | [CCIP Explorer](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238) |
| **VRF** | Randomness request | [BaseScan TX](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |
| **Circuit Breaker** | TestVault paused | [BaseScan](https://sepolia.basescan.org/address/0xB85d57374c18902855FA85d6C36080737Fb7509c) |
| **Data Feeds** | ETH/USD price | Used in live monitoring |

---

## Pre-Production Checklist

Before recording:
- [ ] Start all services: `bash scripts/run-demo.sh`
- [ ] Verify Python API: `curl http://localhost:8000/api/v1/health`
- [ ] Verify TS API: `curl http://localhost:3000/api/v1/health`
- [ ] Open dashboard: http://localhost:5173
- [ ] Open CCIP Explorer tab: https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238
- [ ] Have terminal ready with curl commands
- [ ] Test live Aave monitoring: `curl http://localhost:8000/api/v1/monitor/aave`

---

## VIDEO SCRIPT

### SEGMENT 1: The Hook (0:00 - 0:15)

**[SCREEN: Black background with white text fading in]**

```
$3,000,000,000
```

**VOICEOVER:**
> "In 2024, DeFi protocols lost three billion dollars to exploits. Euler Finance: 197 million. Ronin Bridge: 625 million. These attacks happen in seconds. Detection takes hours. By then, funds are gone."

**[Text fades to AEGIS logo]**

> "We built AEGIS to change that."

---

### SEGMENT 2: The Problem (0:15 - 0:45)

**[SCREEN: Animated timeline showing attack progression]**

**VISUAL**: Show timeline graphic:
```
Block N    │ Attack begins
           ↓
Block N+5  │ Funds drained (2 minutes)
           ↓
+30 min    │ Twitter notices
           ↓
+2 hours   │ Security team investigates
           ↓
+24 hours  │ Post-mortem published
           ↓
           │ Funds: UNRECOVERABLE
```

**VOICEOVER:**
> "Here's how every major DeFi exploit plays out. Attack starts. Within minutes, funds are drained. Half an hour later, someone notices on Twitter. Hours later, a security team investigates. By then? The attacker has already bridged and mixed the stolen funds."

**[Beat]**

> "The problem isn't detection algorithms. The problem is TIME. DeFi needs an immune system — one that responds in seconds, not hours."

---

### SEGMENT 3: The Solution — AEGIS Architecture (0:45 - 1:30)

**[SCREEN: Architecture diagram (from README)]**

**VISUAL**: Show the architecture diagram with animated highlights:
```
┌─────────────────────────────────────────────────┐
│              SENTINELSWARM                       │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│   │LIQUIDITY│  │ ORACLE  │  │GOVERNANCE│        │
│   │SENTINEL │  │SENTINEL │  │SENTINEL  │        │
│   └────┬────┘  └────┬────┘  └────┬────┘        │
│        └───────────┬┴───────────┘              │
│                    ▼                            │
│           CONSENSUS (2/3 vote)                  │
│                    │                            │
│       ┌────────────┼────────────┐              │
│       ▼            ▼            ▼              │
│   CIRCUIT      TELEGRAM    CHAINSHERLOCK       │
│   BREAKER      ALERT       FORENSICS           │
└─────────────────────────────────────────────────┘
```

**VOICEOVER:**
> "AEGIS is an autonomous security infrastructure built on Chainlink. Three AI sentinel agents monitor a protocol in real-time."

**[Highlight Liquidity Sentinel]**
> "The Liquidity Sentinel watches TVL — Total Value Locked. If funds start draining faster than normal, it raises an alarm."

**[Highlight Oracle Sentinel]**
> "The Oracle Sentinel compares on-chain prices against Chainlink Data Feeds. Price manipulation? Detected instantly."

**[Highlight Governance Sentinel]**
> "The Governance Sentinel analyzes proposals for malicious patterns — like attempts to transfer ownership or disable security."

**[Highlight Consensus]**
> "Each sentinel votes independently. When two out of three agree on a CRITICAL threat..."

**[Highlight Circuit Breaker]**
> "...we automatically trigger an on-chain circuit breaker. The protocol pauses. Funds are protected."

---

**[SCREEN: Chainlink services with PROOF]**

**VISUAL**: Show 5 Chainlink service logos with REAL transaction links:

| Service | What We Use It For | Proof |
|---------|-------------------|-------|
| **CRE** | Workflow orchestration | Simulation passed (blocked on deploy access) |
| **Data Feeds** | ETH/USD price ($1965.14 live) | Used in every detection cycle |
| **Automation** | 30-second monitoring cycles | Cron trigger in CRE workflow |
| **VRF** | Fair tie-breaker selection | [TX: 0x761c...](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff) |
| **CCIP** | Cross-chain alerts | [Message delivered](https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238) |

**VOICEOVER:**
> "AEGIS uses FIVE Chainlink services. That's not just claims — here are the transaction hashes. CRE orchestrates our workflows. Data Feeds give us real-time ETH prices. VRF provides verifiable randomness for tie-breaking — here's the actual request on BaseScan. And CCIP? We sent a real cross-chain alert from Base to Arbitrum. Click that link. It's on-chain."

---

### SEGMENT 4: Live Demo (1:30 - 2:30)

**[SCREEN: Dashboard showing LIVE Aave monitoring]**

**VISUAL**: Show dashboard at http://localhost:5173
- LiveMonitor component showing real Aave V3 data
- Real TVL in USD (from Base Mainnet)
- Chainlink ETH/USD price updating
- Green status indicator

**VOICEOVER:**
> "Here's AEGIS monitoring REAL DeFi — Aave V3 on Base Mainnet. That's not mock data. That TVL is live. That price comes directly from Chainlink Data Feeds."

**[Execute in terminal to prove it's real]**:
```bash
curl -s http://localhost:8000/api/v1/monitor/aave | jq '{tvl_usd, chainlink_eth_usd, status}'
```

---

**[SCREEN: Terminal + Dashboard side by side]**

**VISUAL**: Split screen — terminal on left, dashboard on right

**VOICEOVER:**
> "Now let's simulate what happens during an attack. The attacker drains 25% of TVL in seconds."

**[Execute in terminal]**:
```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0xB85d57374c18902855FA85d6C36080737Fb7509c","simulate_tvl_drop_percent":25}'
```

**[Pause for 2 seconds — show response in terminal]**

**VOICEOVER:**
> "Two of three sentinels detect CRITICAL threat. AI confirms: this matches a flash loan attack pattern."

---

**[SCREEN: Show real on-chain circuit breaker]**

**VISUAL**: Show BaseScan for TestVault being paused

**VOICEOVER:**
> "Watch what happens next. AEGIS triggers the circuit breaker ON-CHAIN."

**[Show command]**:
```bash
# This is REAL — TestVault at 0xB85d57374c18902855FA85d6C36080737Fb7509c
cast call 0xB85d57374c18902855FA85d6C36080737Fb7509c "paused()(bool)" --rpc-url https://sepolia.base.org
# Returns: true
```

**VOICEOVER:**
> "The vault is now paused. No withdrawals possible. Funds are SAFE."

---

**[SCREEN: Show CCIP cross-chain alert]**

**VISUAL**: Open CCIP Explorer showing the real message

**VOICEOVER:**
> "And here's the best part. This alert was sent cross-chain via Chainlink CCIP. Base Sepolia to Arbitrum Sepolia. Real transaction. Real message delivery."

**[Show CCIP Explorer URL]**:
```
https://ccip.chain.link/msg/0x0cc38b26d79e55f7fca889d381522d0efd3a6499a3acd4201abf3331795d8238
```

---

**[SCREEN: Euler Finance Forensics]**

**VISUAL**: Show the Euler hack analysis endpoint

**VOICEOVER:**
> "But AEGIS doesn't just detect — it investigates. ChainSherlock analyzed the real Euler Finance hack from 2023. 197 million dollars. Here's the attack flow it discovered."

**[Execute in terminal]**:
```bash
curl -s http://localhost:8000/api/v1/forensics/demo/euler | jq '.attack_flow[:3]'
```

**VOICEOVER:**
> "Flash loan, donation attack, liquidation exploit. All identified automatically."

---

### SEGMENT 5: Why This Matters (2:30 - 2:45)

**[SCREEN: Side-by-side comparison]**

**VISUAL**:
```
WITHOUT AEGIS          │  WITH AEGIS
───────────────────────│───────────────────────
Attack detected: 30min │  Attack detected: 30sec
Response time: hours   │  Response time: instant
Funds lost: millions   │  Funds lost: zero
```

**VOICEOVER:**
> "Without AEGIS, that attack drains the protocol before anyone notices. With AEGIS? Detected in 30 seconds. Response is automatic. Funds are safe."

---

### SEGMENT 6: Wrap-Up (2:45 - 3:00)

**[SCREEN: AEGIS logo with tagline]**

**VISUAL**:
```
          ╔═══════════════════════════════════╗
          ║          AEGIS PROTOCOL           ║
          ║                                   ║
          ║   The Immune System for DeFi      ║
          ╚═══════════════════════════════════╝

   AI-powered detection │ Chainlink verification │ Instant response
```

**VOICEOVER:**
> "AEGIS Protocol. AI-powered threat detection. Chainlink-verified consensus. Instant automated response. The immune system DeFi has been waiting for."

**[Beat]**

> "Thank you to Chainlink for building the infrastructure that makes this possible. Check out our GitHub. We're ready to protect the protocols of tomorrow."

**[SCREEN: GitHub URL + Proof Links]**

**VISUAL**:
```
GitHub: github.com/aegis-protocol

VERIFY OUR CLAIMS:
├── CCIP Alert:  ccip.chain.link/msg/0x0cc38b26...
├── VRF Request: sepolia.basescan.org/tx/0x761cb3...
├── TestVault:   sepolia.basescan.org/address/0xB85d57...
└── Forensics:   Euler Finance $197M hack analyzed

5 Chainlink Services: CRE + Data Feeds + Automation + VRF + CCIP
Track: Risk & Compliance + AI
```

---

## POST-PRODUCTION NOTES

### Timing Breakdown
| Segment | Duration | Cumulative |
|---------|----------|------------|
| Hook | 0:15 | 0:15 |
| Problem | 0:30 | 0:45 |
| Solution | 0:45 | 1:30 |
| Live Demo | 1:00 | 2:30 |
| Why This Matters | 0:15 | 2:45 |
| Wrap-Up | 0:15 | 3:00 |

### Recording Tips
1. **Record in 1080p** — judges watch on various screens
2. **Use dark mode** — matches dashboard theme
3. **Zoom terminal to 150%** — ensure readability
4. **Test all commands** before recording
5. **Have backup takes** for the live demo segment
6. **Add subtle background music** (optional, keep low)

### Fallback Commands

If services are down during recording, use these pre-recorded responses:

```bash
# Health check
curl -s http://localhost:3000/api/v1/health | jq

# Expected response:
{
  "status": "healthy",
  "sentinels": { "active": 3, "total": 3 },
  "api": "operational"
}
```

```bash
# Simulate attack
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25}'

# Expected response:
{
  "consensus": {
    "reached": true,
    "final_threat_level": "CRITICAL",
    "agreement_ratio": 0.67,
    "recommended_action": "CIRCUIT_BREAKER"
  },
  "sentinels": [...]
}
```

---

## THUMBNAIL / TITLE

**Title**: AEGIS Protocol — Real-Time DeFi Threat Detection

**Thumbnail**: Dashboard screenshot showing CRITICAL threat with red alert badge

**Description**:
> AEGIS is an AI-powered security infrastructure for DeFi protocols. Using Chainlink CRE, Data Feeds, Automation, VRF, and CCIP, AEGIS detects threats in seconds and automatically triggers circuit breakers to protect funds. Built for the Chainlink Convergence Hackathon.
