# AEGIS Protocol - Demo Video Script

> **Duration**: 3 minutes
> **Format**: Screen recording with voiceover
> **Audience**: Chainlink Convergence Hackathon judges (Risk & Compliance + AI tracks)

---

## Pre-Production Checklist

Before recording:
- [ ] Start all services: `bash scripts/run-demo.sh`
- [ ] Verify health: `curl http://localhost:3000/api/v1/health`
- [ ] Open dashboard: http://localhost:5173
- [ ] Clear previous alerts (run `scripts/demo-reset.sh` if available)
- [ ] Have terminal ready with curl commands
- [ ] Test Telegram notifications are working (optional)

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

**[SCREEN: Chainlink services icons]**

**VISUAL**: Show 5 Chainlink service logos with labels:
- CRE (workflow orchestration)
- Data Feeds (price verification)
- Automation (scheduled monitoring)
- VRF (fair tie-breaking)
- CCIP (cross-chain alerts)

**VOICEOVER:**
> "All of this runs on Chainlink's infrastructure. CRE orchestrates detection workflows every 30 seconds. Data Feeds provide price truth. Automation keeps sentinels running 24/7. VRF handles tie-breaker selection. And CCIP propagates alerts across chains."

---

### SEGMENT 4: Live Demo (1:30 - 2:30)

**[SCREEN: Dashboard showing healthy state]**

**VISUAL**: Show dashboard at http://localhost:5173
- All three sentinels green
- Threat level: NONE
- Protocol TVL: 100 ETH

**VOICEOVER:**
> "Here's AEGIS in action. Our dashboard shows a protocol with 100 ETH locked. All three sentinels are healthy. Threat level: none."

---

**[SCREEN: Terminal + Dashboard side by side]**

**VISUAL**: Split screen — terminal on left, dashboard on right

**VOICEOVER:**
> "Let's simulate a reentrancy attack. The attacker is draining funds rapidly."

**[Execute in terminal]**:
```bash
curl -X POST http://localhost:3000/api/v1/sentinel/detect \
  -H "Content-Type: application/json" \
  -d '{"protocol_address":"0x1","simulate_tvl_drop_percent":25,"simulate_price_deviation_percent":6}'
```

**[Pause for 2 seconds — show response in terminal]**

**VOICEOVER:**
> "25% of TVL gone. Oracle showing 6% price deviation."

---

**[SCREEN: Dashboard updates to CRITICAL]**

**VISUAL**:
- Liquidity Sentinel: CRITICAL (red)
- Oracle Sentinel: CRITICAL (red)
- Governance Sentinel: NONE (green)
- Consensus: REACHED
- Recommended Action: CIRCUIT_BREAKER

**VOICEOVER:**
> "Watch the dashboard. Two of three sentinels just went CRITICAL. Consensus reached. Circuit breaker triggered."

---

**[SCREEN: Show Telegram notification (if configured)]**

**VISUAL**: Phone notification or Telegram desktop showing alert

**VOICEOVER:**
> "Protocol operators get an instant Telegram alert. 'CRITICAL threat detected. Circuit breaker activated. Your protocol is now paused.'"

---

**[SCREEN: Forensics output]**

**VISUAL**: Show curl command and JSON response for forensics
```bash
curl http://localhost:3000/api/v1/forensics | jq
```

**VOICEOVER:**
> "Meanwhile, ChainSherlock is already analyzing the attack. Within seconds, we have a forensic report classifying this as a potential reentrancy exploit."

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

**[SCREEN: GitHub URL + team info]**

**VISUAL**:
```
GitHub: github.com/aegis-protocol
Built with: CRE, Data Feeds, Automation, VRF, CCIP
Track: Risk & Compliance
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
