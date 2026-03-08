# AEGIS Protocol — Business Model

> **Document Status**: Draft v1.0 | March 2026
> **Purpose**: Define AEGIS Protocol's revenue model, pricing, unit economics, and path to $1M ARR
> **Audience**: Founders, investors, Base Batches reviewers

---

## Executive Summary

AEGIS Protocol is an AI-powered security infrastructure for DeFi that detects threats in 30 seconds and automatically triggers circuit breakers before funds drain. Unlike competitors that only detect threats, AEGIS detects *and* acts — closing the gap between alert and response that costs the industry $3B/year.

**Business Model**: Protocol Subscriptions (SaaS) — monthly recurring revenue tiered by TVL protected and feature access.

**Pricing**: Three tiers — Sentinel (Free), Guardian ($1,500/mo), Fortress ($5,000/mo) — targeting 92%+ gross margins.

**Target**: $1M ARR within 12 months via 22 Guardian + 8 Fortress + 2–3 enterprise custom deals.

**Go-to-Market**: Base ecosystem first (smaller, less competitive, strong Chainlink alignment), then expand to Ethereum mainnet and L2s.

---

## 1. Revenue Model Analysis

Three models were evaluated for fit with AEGIS's product and market:

### Model Comparison

| Dimension | Protocol Subscriptions (SaaS) | Insurance Integration (B2B2C) | Security-as-a-Service (Usage) |
|---|---|---|---|
| **How it works** | Monthly fee per protocol protected, tiered by TVL | Partner with Nexus Mutual / InsurAce; earn fee on premium reduction or underwriting signal | Pay-per-detection-cycle + incident response fees |
| **Revenue predictability** | High — recurring monthly | Medium — depends on insurance partner volume | Low — usage varies with threat landscape |
| **Sales cycle** | 2–4 weeks (founder-led) | 3–6 months (partnership negotiations) | 1–2 weeks (low commitment) |
| **Gross margin** | 90%+ (software delivery) | 60–70% (revenue share with insurer) | 70–80% (variable compute costs) |
| **Scalability** | Linear — each new protocol = incremental MRR | Exponential once partnerships close | Linear but unpredictable |
| **Customer lock-in** | Medium — historical data, custom thresholds | High — integrated into insurance pricing | Low — easy to switch or stop |
| **Time to first revenue** | 3–4 months | 6–12 months | 1–2 months |
| **Best for** | Early-stage traction + long-term growth | Mature product with proven track record | Market validation / entry |

### Pros & Cons Deep Dive

**Protocol Subscriptions (SaaS)**
- Predictable recurring revenue enables planning and hiring
- Simple pricing is easy to explain in a 15-minute call
- Aligns with how protocols already budget for security (annual audits, bug bounties)
- Proven model in B2B security (Datadog, CrowdStrike, Snyk all use subscription)
- *Risk*: Harder to justify cost during quiet periods (no active threats)
- *Mitigation*: Free tier proves value; forensic reports provide ongoing deliverables

**Insurance Integration (B2B2C)**
- Massive TAM — DeFi insurance market projected $25B+ by 2030
- Natural value alignment ("AEGIS saves you money on insurance")
- Creates network effects (more protected protocols = better actuarial data)
- *Risk*: Dependency on insurance partners' timelines and priorities
- *Risk*: Complex revenue attribution (who gets credit for prevented hacks?)
- *Mitigation*: Pursue as Phase 2 after SaaS base is established

**Security-as-a-Service (Usage-Based)**
- Lowest barrier to adoption — protocols pay only for what they use
- Scales naturally with threat volume
- *Risk*: Revenue drops during quiet periods, creating cash flow gaps
- *Risk*: Customers may view as "nice to have" instead of infrastructure
- *Risk*: Difficult to forecast for investors

---

## 2. Recommended Model: Protocol Subscriptions (SaaS)

**Protocol Subscriptions is the right model for AEGIS.** Here's why, evaluated against the three criteria that matter most at this stage:

### Early-Stage Traction (First 10 Customers)

- **Simple pitch**: "Pay $X/month, we protect your protocol 24/7." No complex integration discussions.
- **Fast close**: 2–4 week sales cycle with founder-led sales. No partnership negotiations needed.
- **Free tier funnel**: DeFi teams can try AEGIS risk-free, see real alerts, then upgrade when they trust the system.
- **Proof of value**: Monthly forensic reports and threat dashboards give tangible deliverables even when no attacks occur.

### Scalability (100+ Protocols)

- **Unit economics improve with scale**: Infrastructure cost per protocol decreases as monitoring overhead is shared across customers.
- **Self-serve potential**: Free → Guardian upgrade can be automated with Stripe/crypto payments. No sales call required.
- **Multi-chain expansion**: Same product, new market — Arbitrum, Optimism, Polygon each represent a new customer pool with identical pricing.
- **Platform effects**: Historical threat data across 100+ protocols makes detection smarter, creating a compounding advantage.

### Defensibility (Competitive Moat)

- **Data moat**: Every protocol monitored generates threat intelligence that improves all sentinels. Competitors starting later will have less training data.
- **Switching costs**: Custom thresholds, historical baselines, and protocol-specific tuning accumulate over time. Switching means losing months of calibration.
- **Chainlink-native verification**: On-chain consensus via Chainlink CRE/VRF is auditable and trustless — a unique trust advantage competitors can't easily replicate.
- **Ecosystem integration**: Deep integration with Base, Chainlink services, and protocol governance systems creates multi-layered lock-in.

### Phase 2 Expansion: Insurance Integration

After establishing a SaaS base with 20+ paying customers (est. Month 8–10), AEGIS will pursue insurance partnerships:
- Partner with Nexus Mutual / InsurAce to offer premium discounts for AEGIS-protected protocols
- Revenue share model: AEGIS earns 10–15% of premium savings
- This creates a second revenue stream without cannibalizing subscriptions
- AEGIS-verified security status becomes an on-chain attestation that insurers can programmatically consume

---

## 3. Pricing Structure

### Infrastructure Cost Basis

Pricing is grounded in real infrastructure costs measured from the AEGIS codebase and deployment:

| Cost Component | Per Protocol / Month | Notes |
|---|---|---|
| Anthropic Claude API | $9–54 | ~$0.30–1.80/day; 30–40% of detection cycles trigger AI analysis |
| Base L2 Gas | $15–60 | ~$0.50–2.00/day; on-chain threat reports, circuit breaker calls |
| Chainlink VRF | $0–45 | ~$0–1.50/day; only triggered on sentinel ties (~5–10% of cycles) |
| Chainlink Automation/CRE | $5–15 | Cron-based monitoring orchestration |
| Compute (Railway/Fly) | $5–10 | Shared across protocols; per-protocol share |
| Support & Ops Overhead | $20 | Monitoring, maintenance, on-call |
| **Total Cost to Serve** | **$54–204** | **Midpoint: ~$120/month** |

### Three-Tier Pricing

| Feature | **Sentinel** (Free) | **Guardian** ($1,500/mo) | **Fortress** ($5,000/mo) |
|---|---|---|---|
| **Price** | $0 | $1,500/month | $5,000/month |
| **Annual Price** | — | $14,400/year (20% off) | $48,000/year (20% off) |
| **Protocols Monitored** | 1 | Up to 3 | Unlimited |
| **Detection Cycle** | 5 minutes | 30 seconds | 30 seconds |
| **Auto Circuit Breaker** | — | Included | Included |
| **CCIP Cross-Chain Alerts** | — | — | Included |
| **AI Forensic Reports** | — | Monthly summary | Real-time + dedicated analyst |
| **Custom Thresholds** | Default only | Basic tuning | Full customization |
| **Alert Channels** | Dashboard only | Telegram, Discord, Email | All + PagerDuty, Slack, Webhook |
| **Historical Data Retention** | 7 days | 90 days | Unlimited |
| **SLA** | Best effort | 99% uptime | 99.9% uptime |
| **Support** | Community | Email (24h response) | Priority (1h response) + dedicated Slack |
| **On-Chain Verification** | — | Included | Included + audit trail |
| **Max TVL Protected** | $5M | $50M | $500M (custom above) |
| **Target Customer** | Indie devs, new protocols | Small-mid protocols on Base | Top 50 DeFi, multi-chain protocols |

### Tier Rationale

**Sentinel (Free)** — *The funnel*
- Purpose: Prove AEGIS works. Let teams see real threat assessments on their own protocol.
- Limitation: 5-minute detection cycle means it's monitoring, not protection. No auto-response.
- Conversion lever: "You just got a HIGH alert. With Guardian, we would have paused your protocol automatically."

**Guardian ($1,500/mo)** — *The core product*
- Covers 80% of DeFi protocols (TVL under $50M)
- 30-second detection + auto circuit breaker = the full value proposition
- Price point validated against security audit costs ($10–50K one-time) and bug bounty budgets ($5–20K/month)
- 3-protocol limit incentivizes upgrade for multi-product teams

**Fortress ($5,000/mo)** — *The enterprise play*
- Unlimited protocols for complex DeFi ecosystems (Aave, Compound, Uniswap have multiple deployments across chains)
- CCIP cross-chain alerts protect multi-chain deployments simultaneously
- Custom thresholds eliminate false positives for high-TVL protocols with unique patterns
- SLA guarantee required for protocols managing >$50M in user funds
- Enterprise custom pricing for TVL >$500M (est. $8,000–15,000/mo)

### Payment Methods

- **Primary**: USDC on Base (on-chain, automated via smart contract)
- **Secondary**: Wire transfer / Stripe for traditional billing
- **Future**: Protocol-native token payments at a negotiated rate

---

## 4. Unit Economics

### Cost to Serve: One Protocol (Guardian Tier)

| Component | Monthly Cost | Calculation |
|---|---|---|
| AI Analysis (Anthropic Claude) | $30 | ~1,000 AI-triggered detections/month × $0.03 avg |
| On-Chain Gas (Base) | $30 | ~50 tx/day × $0.02 avg gas × 30 days |
| Chainlink VRF | $15 | ~15 tie-breakers/month × $1.00 avg |
| Chainlink Services (CRE/Automation) | $15 | Shared orchestration costs |
| Compute Infrastructure | $10 | Railway/Fly shared allocation |
| Support & Maintenance | $20 | Engineering time allocation (fractional) |
| **Total COGS** | **$120** | |

### Margin Analysis

| Metric | Guardian ($1,500/mo) | Fortress ($5,000/mo) |
|---|---|---|
| Revenue per customer | $1,500 | $5,000 |
| COGS per customer | $120 | $300 (multi-protocol, higher AI usage) |
| **Gross Profit** | **$1,380** | **$4,700** |
| **Gross Margin** | **92%** | **94%** |
| Target benchmark | >70% ✓ | >70% ✓ |

### Customer Acquisition Cost (CAC)

| Channel | Cost | Conversions/Mo | CAC |
|---|---|---|---|
| Founder-led sales (conferences, DeFi events) | $3,000/mo | 1–2 | $1,500–3,000 |
| Content marketing (Twitter threads, blog posts) | $500/mo | 0.5 | $1,000 |
| Referral program (1 month free for referrer) | $1,500/referral | 0.5 | $1,500 |
| **Blended CAC** | | | **~$3,000** |

### Lifetime Value (LTV)

| Metric | Guardian | Fortress |
|---|---|---|
| Monthly revenue | $1,500 | $5,000 |
| Average lifespan | 18 months | 24 months |
| **LTV** | **$27,000** | **$120,000** |
| **LTV:CAC Ratio** | **9:1** | **40:1** |
| Benchmark (healthy SaaS) | >3:1 ✓ | >3:1 ✓ |

### Payback Period

| Tier | CAC | Monthly Revenue | **Payback** |
|---|---|---|---|
| Guardian | $3,000 | $1,500 | **2 months** |
| Fortress | $3,000 | $5,000 | **< 1 month** |
| Benchmark (healthy SaaS) | | | < 12 months ✓ |

### Break-Even Analysis

| Expense | Monthly |
|---|---|
| Engineering team (2 FTE) | $25,000 |
| Infrastructure (all customers) | $2,000 |
| Marketing & sales | $3,000 |
| Legal, admin, misc | $2,000 |
| **Total Monthly Burn** | **$32,000** |
| **Break-even MRR** | **$32,000** |
| **Break-even customers** | ~8 Guardian + 3 Fortress (or equivalent mix) |
| **Expected break-even** | **Month 7–8** |

---

## 5. 12-Month Revenue Projection

### Month-by-Month Forecast

| Month | Phase | New Guardian | New Fortress | Total Guardian | Total Fortress | MRR | ARR Run Rate |
|---|---|---|---|---|---|---|---|
| 1 | Beta | — | — | 0 | 0 | $0 | $0 |
| 2 | Beta | — | — | 0 | 0 | $0 | $0 |
| 3 | Beta | — | — | 0 | 0 | $0 | $0 |
| 4 | Launch | +3 | — | 3 | 0 | $4,500 | $54,000 |
| 5 | Launch | +2 | +1 | 5 | 1 | $12,500 | $150,000 |
| 6 | Launch | +2 | +1 | 7 | 2 | $20,500 | $246,000 |
| 7 | Growth | +2 | +1 | 9 | 3 | $28,500 | $342,000 |
| 8 | Growth | +3 | +1 | 12 | 4 | $38,000 | $456,000 |
| 9 | Growth | +3 | +1 | 15 | 5 | $47,500 | $570,000 |
| 10 | Scale | +3 | +1 | 18 | 6 | $57,000 | $684,000 |
| 11 | Scale | +2 | +1 | 20 | 7 | $65,000 | $780,000 |
| 12 | Scale | +2 | +1 | 22 | 8 | $73,000 | $876,000 |

**Plus enterprise custom deals (Month 10–12):** 2–3 protocols at $8,000–15,000/mo = +$16,000–45,000 MRR

**Month 12 Target: $89,000–$118,000 MRR = $1.07M–$1.42M ARR**

### Phase Narrative

**Months 1–3: Beta (MRR: $0)**
- Deploy Sentinel (free tier) on Base mainnet
- Onboard 10–15 Base ecosystem protocols manually
- Goal: Generate 3+ case studies showing threats detected
- Build relationships with protocol founders
- Validate alert accuracy and false positive rate (<5% target)
- Publish weekly "Base Security Report" for ecosystem visibility

**Months 4–6: Launch (MRR: $4,500 → $20,500)**
- Launch Guardian tier with auto circuit breaker
- Convert top 3 beta users first (warm leads, proven value)
- Announce at ETH Denver / Base ecosystem events
- Target: 7 Guardian + 2 Fortress customers by end of Month 6
- First Fortress customer likely from beta (largest TVL protocol)
- Publish first "AEGIS Prevented a $X Attack" case study

**Months 7–9: Growth (MRR: $28,500 → $47,500)**
- Expand adapter support (Morpho, Aerodrome, other Base-native protocols)
- Launch referral program (1 month free for successful referral)
- Hire first sales/BD person (part-time or contractor)
- Target: 15 Guardian + 5 Fortress by end of Month 9
- Begin conversations with Ethereum mainnet protocols

**Months 10–12: Scale (MRR: $57,000 → $73,000+)**
- Deploy on Ethereum mainnet and Arbitrum
- Close 2–3 enterprise custom deals ($8K–15K/mo each)
- Launch insurance integration partnership (Nexus Mutual)
- Target: 22 Guardian + 8 Fortress + 2–3 Enterprise by Month 12
- Approach $1M ARR milestone

### Key Milestones

| Milestone | Target Month | Metric |
|---|---|---|
| First paid customer | Month 4 | 1 Guardian subscriber |
| $10K MRR | Month 5 | Product-market fit signal |
| Break-even | Month 7–8 | MRR covers monthly burn |
| 20 paying customers | Month 9 | Scale readiness |
| $50K MRR | Month 9–10 | Series Seed trigger |
| $1M ARR | Month 12 | Fundraise milestone |

---

## 6. Competitive Landscape

### Head-to-Head Comparison

| Dimension | **AEGIS** | **Forta Network** | **Hypernative** | **OZ Defender** |
|---|---|---|---|---|
| **Funding** | Pre-seed | $23M raised | $16M raised | Part of OpenZeppelin |
| **Detection** | AI sentinels (30s) | Bot network (varies) | ML models (real-time) | Rule-based monitoring |
| **Response** | Auto circuit breaker | Alert only | Alert + some automation | Manual response |
| **Verification** | On-chain (Chainlink CRE/VRF) | Decentralized bots | Centralized | Centralized |
| **Cross-chain** | CCIP native | Multi-chain bots | Multi-chain support | Multi-chain support |
| **Forensics** | AI-powered analysis | Community-built | Basic | None |
| **Pricing** | $0–5,000/mo | Per-bot subscription | Enterprise (undisclosed) | Free tier + enterprise |
| **Base Focus** | Primary ecosystem | General | General | General |

### AEGIS Differentiators (Ranked by Impact)

1. **Detection → Action (not just detection)**
   - Forta tells you there's a fire. AEGIS triggers the sprinklers.
   - Only solution with automatic on-chain circuit breaker response.
   - This is the #1 differentiator. Build all messaging around it.

2. **30-Second End-to-End**
   - Detection → consensus → action in 30 seconds.
   - Industry standard: 30+ minutes for detection alone.
   - By the time competitors alert, AEGIS has already paused the protocol.

3. **Chainlink-Native Verification**
   - Consensus verified on-chain via Chainlink CRE.
   - VRF tie-breaker is provably fair.
   - No "trust us" — the math is on-chain.

4. **Multi-Signal Consensus (3 Sentinels)**
   - Liquidity + Oracle + Governance = comprehensive coverage.
   - 2/3 majority eliminates single-point-of-failure false positives.
   - Each sentinel specializes in a different attack vector.

5. **AI Forensics (Post-Incident)**
   - ChainSherlock provides immediate attack classification and fund tracing.
   - Competitors stop at "something happened."
   - AEGIS tells you *what* happened, *how*, and *where the funds went*.

### Competitive Positioning Matrix

```
                    Detection Only ←————————→ Detection + Response
                         │                        │
  Centralized    ┌───────┤                        │
                 │ Forta  │                        │
                 │Network │                        │
                 └───────┤                        │
                         │      ┌──────────┐      │
                 ┌───────┤      │Hypernative│      │
                 │  OZ    │      └──────────┘      │
                 │Defender│                        │
                 └───────┤                   ┌────┤
                         │                   │AEGIS│
  Decentralized/         │                   │    │
  Verifiable             │                   └────┤
                         │                        │
```

AEGIS occupies the unique position of **verifiable + automated response** — a quadrant no competitor currently fills.

---

## 7. Key Assumptions & Risks

### Assumptions

| Assumption | Basis | Risk if Wrong |
|---|---|---|
| Protocols will pay $1,500+/mo for security | Security audits cost $10–50K one-time; bug bounties cost $5–20K/mo | Validated by competitor pricing (Forta, Hypernative both charge) |
| 30% of free tier converts to paid | Industry SaaS benchmark: 2–5% for PLG, 20–40% for sales-led | Conservative; DeFi security has higher urgency than typical SaaS |
| Average customer retains 18 months (Guardian) | B2B security SaaS benchmark: 18–24 months | Lower than enterprise benchmark, accounting for DeFi protocol lifecycle |
| 2–3 new Guardian customers per month (Growth phase) | Based on 200+ protocols on Base with >$1M TVL | Requires consistent outreach; hire BD by Month 7 |
| Infrastructure costs stay within $120/month per protocol | Based on current Anthropic API pricing and Base gas costs | AI costs trending down; Base gas is stable and low |

### Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **False positive triggers circuit breaker** | Critical | Medium | 2/3 consensus minimizes risk; configurable thresholds; manual override always available |
| **No major exploits during beta = hard to prove value** | High | Medium | Simulate historical attacks (Euler demo); publish security reports; show near-misses |
| **Competitor with more funding copies our approach** | High | Low | First-mover on Base; Chainlink partnership moat; data advantage compounds |
| **Anthropic API costs increase significantly** | Medium | Low | Model-agnostic architecture; can switch to open-source models (Llama, Mixtral) |
| **Regulatory uncertainty around automated protocol pausing** | Medium | Low | Circuit breaker is opt-in by protocol governance; AEGIS doesn't have unilateral control |
| **Chainlink CRE pricing changes** | Medium | Medium | Diversify execution layer; maintain direct RPC fallback |

---

## 8. Next Steps

### Immediate (Weeks 1–2)
- [ ] Validate pricing with 5 discovery calls with Base protocol teams
- [ ] Confirm infrastructure costs on Base mainnet (vs. testnet estimates)
- [ ] Build simple pricing page for website
- [ ] Draft LOI template for early adopters

### Short-Term (Weeks 3–4)
- [ ] Secure 2–3 signed LOIs (non-binding intent to use AEGIS at stated price)
- [ ] Submit Base Batches application (April 27, 2026 deadline)
- [ ] Publish "State of DeFi Security on Base" report (lead gen content)
- [ ] Set up USDC payment smart contract for on-chain subscriptions

### Medium-Term (Months 2–3)
- [ ] Deploy Sentinel (free tier) on Base mainnet
- [ ] Onboard first 10 beta protocols
- [ ] Establish monitoring dashboard for beta users
- [ ] Begin weekly "Base Security Report" publication

---

## Appendix A: Market Sizing

### Total Addressable Market (TAM)

| Segment | # Protocols | Avg Revenue/Protocol/Year | Market Size |
|---|---|---|---|
| Top 50 DeFi (>$100M TVL) | 50 | $60,000 (Fortress) | $3.0M |
| Mid-tier DeFi ($10M–100M TVL) | 500 | $18,000 (Guardian) | $9.0M |
| Long-tail DeFi ($1M–10M TVL) | 2,000 | $18,000 (Guardian) | $36.0M |
| **Total DeFi Security TAM** | **2,550** | | **$48.0M** |

### Serviceable Addressable Market (SAM) — Base + Ethereum

| Segment | # Protocols | Market Size |
|---|---|---|
| Base ecosystem | 200+ | $5.4M |
| Ethereum mainnet (top 200) | 200 | $7.2M |
| **SAM** | **400** | **$12.6M** |

### Serviceable Obtainable Market (SOM) — Year 1

| Segment | # Customers | Revenue |
|---|---|---|
| Guardian tier | 22 | $396K |
| Fortress tier | 8 | $480K |
| Enterprise custom | 2–3 | $192K–360K |
| **SOM (Year 1)** | **32–33** | **$1.07M–$1.24M** |

---

## Appendix B: Sensitivity Analysis

### Revenue Scenarios (Month 12 ARR)

| Scenario | Guardian Customers | Fortress Customers | Enterprise | ARR |
|---|---|---|---|---|
| **Bear** | 12 | 4 | 0 | $456K |
| **Base** | 22 | 8 | 2 | $1.07M |
| **Bull** | 30 | 12 | 5 | $1.30M+ |

### Key Levers

- **Conversion rate**: Each +5% free-to-paid conversion = ~$13.5K additional MRR
- **ARPU uplift**: Each $500 Guardian price increase = +$11K MRR at 22 customers
- **Churn reduction**: Each extra month of retention = +$1.2M cumulative LTV across customer base
- **Enterprise wins**: Each enterprise deal at $10K/mo = +$120K ARR

---

*Last Updated: March 8, 2026*
*Authors: AEGIS Protocol Founding Team*
*Next Review: After 5 discovery calls + Base Batches application submission*
