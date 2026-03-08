# AEGIS Protocol - Customer Discovery Playbook

> Goal: Validate product-market fit and secure 2-3 LOIs before Base Batches application
> Timeline: 3 weeks
> Target: 50 protocols researched, 20 outreach messages sent, 5 discovery calls, 2-3 LOIs

---

## 1. Ideal Customer Profile (ICP)

### Primary Target: Mid-Size Base Ecosystem Protocols

| Attribute | Ideal Range | Why |
|-----------|-------------|-----|
| TVL | $10M - $500M | Large enough to need security, small enough to be agile |
| Protocol Type | Lending, DEX, Yield | Highest exploit risk categories |
| Team Size | 5-20 people | Has budget, lacks dedicated security team |
| Current Security | 1-2 audits, no monitoring | Gap we fill |
| Chain | Base (primary), Ethereum, Arbitrum | Our deployment targets |
| Stage | Post-launch, growing | Past MVP, investing in infrastructure |

### Secondary Characteristics

Must Have:
- Active smart contracts with user funds
- Public team or semi-public (reachable)
- Some security investment (shows they care)
- Active community (Discord/Telegram)

Nice to Have:
- Previous security incident or near-miss
- Insurance coverage (indicates security budget)
- VC-backed (validates budget exists)
- Multi-chain deployment (upsell opportunity)

### Red Flags (Avoid)
- TVL < $1M (no budget)
- TVL > $1B (enterprise sales cycle)
- Anonymous team (unreachable)
- No audit history (too early stage)
- Meme/gambling protocols (regulatory risk)

---

## 2. Customer Segments

### Segment A: Base Native Protocols (Priority 1)

Profile: Built primarily on Base, benefiting from Coinbase ecosystem
Examples: Aerodrome, Moonwell, Seamless, Extra Finance
Pain Points:
- Growing fast, security lagging behind
- Want to attract institutional LPs who require security
- Base ecosystem grants may fund security

Approach: Position as "Base-native security" — we're built on Chainlink CRE, deployed on Base

### Segment B: Multi-Chain Lending Protocols (Priority 2)

Profile: Lending/borrowing with cross-chain deployments
Examples: Morpho, Silo Finance, Radiant Capital
Pain Points:
- Cross-chain = more attack surface
- Oracle manipulation is #1 risk
- Recent Radiant hack ($53M) scared the sector

Approach: Lead with oracle manipulation detection (our Oracle Sentinel)

### Segment C: DEXs and AMMs (Priority 3)

Profile: Decentralized exchanges, liquidity pools
Examples: Uniswap, Balancer, Curve, Velodrome
Pain Points:
- Flash loan attacks
- Liquidity drainage
- MEV exploitation

Approach: Lead with liquidity monitoring and flash loan detection

---

## 3. Buyer Personas

### Persona 1: The Founder/CEO

Role: Final decision maker
Concerns:
- "Will this slow down our development?"
- "Is the cost justified by the risk?"
- "Can I trust this with our protocol?"

Messaging: Focus on ROI, insurance cost reduction, reputation protection

### Persona 2: The Security Lead / Smart Contract Engineer

Role: Technical evaluator, internal champion
Concerns:
- "How does this integrate with our existing setup?"
- "What's the false positive rate?"
- "Can I customize detection rules?"

Messaging: Focus on technical architecture, Chainlink foundation, customization

### Persona 3: The BD/Partnerships Lead

Role: Often first contact, influencer
Concerns:
- "How does this help us win more partnerships?"
- "What security certifications does this enable?"

Messaging: Focus on competitive advantage, trust signals, partnership requirements

---

## 4. Discovery Process

### Phase 1: Research (Week 1)

1. Build Target List
   - 20 Base ecosystem protocols
   - 15 Ethereum mainnet protocols
   - 15 Multi-chain protocols
   - See: `docs/TARGET_PROTOCOLS.md`

2. Enrich Each Profile
   - Founder Twitter handle
   - Discord/Telegram link
   - Recent security events
   - Current security setup (audits, monitoring)
   - Funding status

### Phase 2: Outreach (Week 2)

1. Prioritize by Fit Score
   - Score 1-5 on each ICP criteria
   - Start with highest scorers

2. Multi-Channel Outreach
   - Twitter DM (first touch)
   - Discord message (follow-up)
   - Email if available (formal pitch)
   - See: `docs/OUTREACH_TEMPLATES.md`

3. Track Everything
   - Use Notion/Sheets for pipeline
   - Log every touchpoint
   - Note response sentiment

### Phase 3: Discovery Calls (Week 3)

1. 15-Minute Structure
   - 2 min: Intro and context
   - 5 min: Pain discovery
   - 3 min: Solution overview
   - 3 min: Pricing test
   - 2 min: Next steps

2. Key Questions to Ask
   - "Have you ever been exploited or had a close call?"
   - "What do you currently spend on security annually?"
   - "How do you monitor for threats today?"
   - "What's your incident response process?"
   - "Would you pay $500/month for automatic circuit breakers?"

3. Validation Goals
   - Confirm pain exists
   - Quantify current spend
   - Test price sensitivity
   - Identify decision maker/process

### Phase 4: LOI Collection

1. Qualification Criteria
   - Confirmed interest after call
   - Budget authority identified
   - Timeline within 6 months
   - Willing to sign non-binding LOI

2. LOI Process
   - Send template within 24 hours of positive call
   - Follow up in 3 days
   - Offer expedited pilot for early signers
   - See: `docs/LOI_TEMPLATE.md`

---

## 5. Objection Handling

### "We already have audits"

Response: "Audits are essential for code quality, but they're point-in-time snapshots. 80% of exploits target logic that passed audits. AEGIS provides continuous monitoring — we catch what audits miss in production."

### "We can't afford it"

Response: "What's your current security budget? Most protocols spend $50-200K on audits annually. AEGIS is $500-2,000/month — roughly 5% of audit costs for continuous protection. One prevented exploit pays for 100 years of AEGIS."

### "We have our own monitoring"

Response: "What's your detection-to-response time? Most teams have hours of lag. AEGIS detects in 30 seconds and can auto-pause — that's the difference between a near-miss and a $10M loss."

### "What if AEGIS has a bug?"

Response: "Our circuit breakers are Chainlink-verified and require 2/3 sentinel consensus. False positives just pause deposits — no fund loss. We're more worried about false negatives, which is why we have triple redundancy."

### "We're too small"

Response: "Actually, you're the perfect size. Big protocols have security teams; small ones have nothing to protect. You're growing — that's exactly when attackers notice. The $50M lending protocol that got hit last month? They thought they were too small too."

---

## 6. Competitive Positioning

| When They Say... | We Say... |
|------------------|-----------|
| "We use Forta" | "Forta detects. AEGIS detects AND acts. When Forta sends an alert, you still need someone to respond. AEGIS triggers circuit breakers automatically." |
| "We use Hypernative" | "Hypernative is great for large enterprises. We're purpose-built for protocols — simpler, cheaper, and deeper DeFi integration." |
| "We use OpenZeppelin Defender" | "Defender is monitoring infrastructure. AEGIS is an AI-powered security system with active response. We complement Defender, not replace it." |

---

## 7. Success Metrics

### Outreach Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| Protocols researched | 50 | Target list |
| Outreach sent | 20 | CRM/Sheets |
| Response rate | 25% (5) | CRM/Sheets |
| Calls booked | 5 | Calendar |
| LOIs signed | 2-3 | DocuSign |

### Call Quality Metrics

| Signal | Positive | Negative |
|--------|----------|----------|
| Pain confirmation | "We worry about this constantly" | "Security isn't a priority" |
| Budget indicator | "We spend $X on audits" | "We don't have budget" |
| Timeline | "We need this now" | "Maybe next year" |
| Decision maker | "I can sign off" | "I need to check with..." |

---

## 8. Tools & Resources

### Research Tools
- DeFiLlama: TVL, fees, chain distribution
- Twitter/X: Founder discovery, sentiment
- DefiSafety: Security ratings
- Crunchbase: Funding data

### Outreach Tools
- Twitter/X: DMs
- Discord: Protocol communities
- LinkedIn: Backup channel
- Email: Formal communication (if available)

### Tracking
- Notion/Sheets: Pipeline tracking
- Google Calendar: Call scheduling
- Loom: Async demos
- DocuSign: LOI signatures

---

## 9. Next Steps

1. Complete Target List → `docs/TARGET_PROTOCOLS.md`
2. Customize Outreach Templates → `docs/OUTREACH_TEMPLATES.md`
3. Prepare LOI Template → `docs/LOI_TEMPLATE.md`
4. Start Outreach → Week of [DATE]
5. Book Discovery Calls → Target: 5 calls
6. Collect LOIs → Target: 2-3 signed

---

*Last Updated: March 8, 2026*
*Status: Ready for execution*
