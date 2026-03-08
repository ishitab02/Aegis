# AEGIS Protocol - Claude Code Reference

> **AEGIS** = AI-Enhanced Guardian Intelligence System
> **Status**: Transitioning from hackathon project → startup
> **Next Milestone**: Base Batches Application (April 27, 2026)

---

## QUICK REFERENCE

```bash
# Start all services
bash scripts/run-demo.sh

# Run tests
cd packages/contracts && forge test           # 21 passing
cd packages/agents-py && python -m pytest     # 147 passing

# Key URLs
Dashboard:    http://localhost:5173
Python API:   http://localhost:8000
TS API:       http://localhost:3000
Euler Demo:   http://localhost:5173/demo
```

---

## 1. WHAT IS AEGIS?

**One-liner:** "Automatic circuit breakers for DeFi — detect threats in 30 seconds, pause protocols before funds drain."

**The Problem:** DeFi loses $3B/year to exploits. By the time anyone notices, funds are gone.

**The Solution:** 3 AI sentinels monitor protocols 24/7. When 2/3 agree on a threat → circuit breaker triggers automatically. No human delay.

```
┌─────────────────────────────────────────────────────────────┐
│                      AEGIS PROTOCOL                          │
│                                                              │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│   │ LIQUIDITY │   │  ORACLE   │   │GOVERNANCE │            │
│   │ SENTINEL  │   │ SENTINEL  │   │ SENTINEL  │            │
│   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘            │
│         └───────────────┼───────────────┘                   │
│                         ▼                                    │
│              ┌─────────────────────┐                        │
│              │  CONSENSUS (2/3)    │                        │
│              └──────────┬──────────┘                        │
│                         ▼                                    │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│    │  CIRCUIT   │  │   ALERT    │  │ FORENSICS  │          │
│    │  BREAKER   │  │ (Telegram) │  │ (Sherlock) │          │
│    └────────────┘  └────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. REPOSITORY STRUCTURE

```
aegis-protocol/
├── packages/
│   ├── contracts/         # Solidity (Foundry) — CircuitBreaker, SentinelRegistry
│   ├── agents-py/         # Python AI agents (CrewAI + FastAPI)
│   ├── api/               # TypeScript API (Hono)
│   ├── cre-workflows/     # Chainlink CRE workflows
│   └── frontend/          # React dashboard (Vite + Tailwind)
├── scripts/               # Demo and deployment scripts
├── docs/                  # Documentation
└── CLAUDE.md              # This file
```

---

## 3. DEPLOYED CONTRACTS (Base Sepolia)

| Contract | Address |
|----------|---------|
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` |
| SentinelRegistry | `0xd34FC1ee378F342EFb92C0D334362B9E577b489f` |
| ThreatReport | `0x3f01beefA5b7F5931B5545BbCFCF0a72c7131499` |
| TestVault | `0xB85d57374c18902855FA85d6C36080737Fb7509c` |
| VRFConsumer | `0x51bAC1448E5beC0E78B0408473296039A207255e` |

---

## 4. TECH STACK

| Layer | Technology |
|-------|------------|
| Smart Contracts | Solidity 0.8.24, Foundry, OpenZeppelin |
| AI Agents | Python 3.12, CrewAI, Anthropic Claude |
| Backend | FastAPI (Python), Hono (TypeScript) |
| Frontend | React 18, Vite, TailwindCSS |
| Blockchain | Base Sepolia, Chainlink (CRE, Data Feeds, VRF, CCIP) |

---

## 5. ENVIRONMENT VARIABLES

```bash
# Required
DEPLOYER_PRIVATE_KEY=<your-wallet-private-key>
ANTHROPIC_API_KEY=sk-ant-...
BASE_SEPOLIA_RPC=https://sepolia.base.org

# Optional
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

## 6. KEY COMMANDS

```bash
# Development
bash scripts/run-demo.sh              # Start all services
pnpm install                           # Install JS dependencies
cd packages/agents-py && pip install -e ".[dev]"  # Install Python deps

# Testing
cd packages/contracts && forge test    # Contract tests
cd packages/agents-py && python -m pytest tests/ -v  # Agent tests

# Demo
open http://localhost:5173/demo        # Euler hack replay
```

---

## 7. WHAT'S BEEN BUILT

| Component | Status | Tests |
|-----------|--------|-------|
| 3 AI Sentinels (Liquidity, Oracle, Governance) | ✅ Complete | 147 passing |
| Consensus Algorithm (2/3 majority) | ✅ Complete | ✅ |
| CircuitBreaker Contract | ✅ Deployed | 21 passing |
| CRE Workflows (5 total) | ✅ Simulation passed | ✅ |
| CCIP Cross-chain Alerts | ✅ TX confirmed | ✅ |
| VRF Tie-breaker | ✅ TX confirmed | ✅ |
| Euler Hack Demo | ✅ 9-step replay | ✅ |
| React Dashboard | ✅ Complete | - |
| Protocol Adapters (Aave, Uniswap, Compound, Curve) | ✅ Complete | ✅ |

---

## 8. WHAT'S MISSING (STARTUP GAPS)

| Gap | Status | Priority |
|-----|--------|----------|
| Business Model | ❌ Undefined | **CRITICAL** |
| Pricing Page | ❌ Missing | **CRITICAL** |
| First Customer/LOI | ❌ None | **CRITICAL** |
| Competitive Positioning | ❌ Generic | HIGH |
| Go-to-Market Strategy | ❌ Missing | HIGH |
| Team Page | ❌ Missing | HIGH |
| Pitch Deck | ❌ Missing | MEDIUM |
| Landing Page | ❌ Missing | MEDIUM |

---

# STARTUP DEVELOPMENT — 3 AGENT PROMPTS

> **Goal**: Transform AEGIS from hackathon project to fundable startup
> **Timeline**: 3 weeks before Base Batches application (April 27, 2026)
> **Each agent works independently on their assigned task**

---

## AGENT 1: BUSINESS MODEL ARCHITECT

### Mission
Design AEGIS's revenue model, pricing structure, and unit economics.

### Prompt for Agent 1

```
You are a startup business strategist helping AEGIS Protocol define its business model.

**Context:**
AEGIS is an AI-powered security system for DeFi protocols that:
- Monitors protocols 24/7 with 3 AI sentinels
- Detects threats in 30 seconds (vs. 30+ minutes industry standard)
- Automatically triggers circuit breakers to pause protocols
- Provides forensic analysis after incidents

**Your Task:**
Create a comprehensive business model for AEGIS. Deliver:

1. **Revenue Model Options Analysis**
   Compare these 3 models with pros/cons:
   - Protocol Subscriptions (SaaS model)
   - Insurance Integration (B2B2C with Nexus Mutual, etc.)
   - Security-as-a-Service (pay-per-protocol-protected)

2. **Recommended Model**
   Pick ONE model and justify why it's best for:
   - Early-stage traction (first 10 customers)
   - Scalability (100+ protocols)
   - Defensibility (competitive moat)

3. **Pricing Structure**
   Create 3 tiers with specific prices:
   - Free tier (what's included, limitations)
   - Pro tier (target: small-mid protocols)
   - Enterprise tier (target: top 50 DeFi protocols)

4. **Unit Economics**
   Calculate:
   - Cost to serve one protocol (infra, AI API calls, monitoring)
   - Target gross margin (should be 70%+)
   - Customer lifetime value assumptions
   - Payback period target

5. **Revenue Projections**
   Create 12-month projection:
   - Month 1-3: Beta (free)
   - Month 4-6: Launch pricing
   - Month 7-12: Scale
   - Target ARR by month 12

**Competitors to Reference:**
- Forta Network ($23M raised, decentralized detection)
- Hypernative ($16M raised, real-time prevention)
- OpenZeppelin Defender (part of OZ ecosystem)

**Output Format:**
Create a document at docs/BUSINESS_MODEL.md with all sections above.
Also create a simple pricing table component for the website.

**Constraints:**
- Must work for Base ecosystem (target Base protocols first)
- Must be sustainable without grants long-term
- Must have clear path to $1M ARR
```

---

## AGENT 2: CUSTOMER DISCOVERY STRATEGIST

### Mission
Identify target customers, create outreach strategy, and draft materials to get LOIs.

### Prompt for Agent 2

```
You are a customer discovery specialist helping AEGIS Protocol find its first paying customers.

**Context:**
AEGIS is an AI-powered security system for DeFi protocols. We need to validate:
- Who will pay for this?
- How much will they pay?
- What's their buying process?

**Your Task:**
Create a complete customer discovery playbook. Deliver:

1. **Ideal Customer Profile (ICP)**
   Define the perfect first customer:
   - Protocol size (TVL range)
   - Protocol type (DEX, lending, yield, bridge)
   - Team size and structure
   - Current security setup
   - Budget indicators

2. **Target List: 50 Protocols**
   Research and list 50 potential customers:
   - 20 Base ecosystem protocols (priority)
   - 15 Ethereum mainnet protocols
   - 15 Multi-chain protocols

   For each, include:
   - Protocol name
   - TVL
   - Twitter handle of founder/security lead
   - Discord/Telegram link
   - Current security (audited? insurance?)

3. **Outreach Templates**
   Create 3 cold outreach templates:
   - Twitter DM (short, <280 chars)
   - Email (longer, value-focused)
   - Discord message (community appropriate)

4. **Discovery Call Script**
   15-minute call structure:
   - Opening (2 min)
   - Pain discovery questions (5 min)
   - Brief demo mention (3 min)
   - Pricing test (3 min)
   - Next steps (2 min)

   Include specific questions to validate:
   - "Have you ever been exploited or had a close call?"
   - "What do you currently spend on security?"
   - "Would you pay $X/month for automatic circuit breakers?"

5. **LOI Template**
   Create a simple Letter of Intent template:
   - Non-binding
   - States intent to use AEGIS when launched
   - Includes expected price range
   - Can be signed digitally

6. **Outreach Tracker**
   Create spreadsheet structure to track:
   - Protocol name
   - Contact
   - Outreach date
   - Response
   - Call scheduled?
   - Interest level (1-5)
   - Notes

**Success Metrics:**
- 50 protocols identified
- 20 outreach messages sent
- 5 discovery calls completed
- 2-3 LOIs signed

**Output Format:**
Create these files:
- docs/CUSTOMER_DISCOVERY.md (strategy doc)
- docs/TARGET_PROTOCOLS.md (the 50 protocols list)
- docs/OUTREACH_TEMPLATES.md (all templates)
- docs/LOI_TEMPLATE.md (Letter of Intent)

**Research Sources:**
- DeFiLlama (TVL data)
- Twitter (founder accounts)
- Base ecosystem page
- DefiSafety (security ratings)
```

---

## AGENT 3: POSITIONING & PITCH STRATEGIST

### Mission
Craft AEGIS's competitive positioning, messaging, and pitch materials.

### Prompt for Agent 3

```
You are a startup positioning expert helping AEGIS Protocol stand out in the DeFi security market.

**Context:**
AEGIS competes in a crowded security space:
- Forta Network: "Decentralized threat detection" ($23M raised)
- Hypernative: "Real-time threat prevention" ($16M raised)
- OpenZeppelin Defender: "Security operations platform"
- Chainalysis: "Blockchain forensics" ($8.6B valuation)

AEGIS's current (weak) positioning: "AI-powered DeFi security"
This is too generic. We need something sharper.

**Your Task:**
Create compelling positioning and pitch materials. Deliver:

1. **Competitive Analysis**
   Deep dive on top 4 competitors:
   - What they do well
   - What they don't do
   - Their pricing (if public)
   - Their customers
   - Their weaknesses we can exploit

2. **Positioning Statement**
   Using the format:
   "For [target customer] who [need], AEGIS is the [category] that [key benefit] unlike [competitors] because [unique differentiator]."

   Create 3 options, recommend one.

3. **Key Messaging**
   - Tagline (5 words or less)
   - One-liner (one sentence)
   - Elevator pitch (30 seconds)
   - Full pitch (2 minutes)

4. **Unique Differentiators**
   What makes AEGIS different? Rank by importance:
   - Automatic circuit breakers (detection → action)
   - Chainlink-native (verifiable, decentralized)
   - AI forensics (not just detection)
   - Multi-signal consensus (3 sentinels)
   - 30-second detection time

5. **Pitch Deck Outline**
   12-slide structure:
   1. Title
   2. Problem
   3. Solution
   4. How it works
   5. Demo/Product
   6. Market size
   7. Business model
   8. Traction
   9. Competition
   10. Team
   11. Roadmap
   12. Ask

   Include bullet points for each slide.

6. **Landing Page Copy**
   Write copy for a simple landing page:
   - Hero section (headline + subhead + CTA)
   - Problem section
   - Solution section
   - How it works (3 steps)
   - Social proof placeholder
   - Pricing teaser
   - Final CTA

7. **Base Batches Application Answers**
   Draft answers for likely application questions:
   - "What are you building?"
   - "What problem does it solve?"
   - "Who are your customers?"
   - "What's your business model?"
   - "Why are you the team to build this?"
   - "What's your traction so far?"
   - "Why Base?"

**Output Format:**
Create these files:
- docs/COMPETITIVE_ANALYSIS.md
- docs/POSITIONING.md (statement + messaging)
- docs/PITCH_DECK_OUTLINE.md
- docs/LANDING_PAGE_COPY.md
- docs/BASE_BATCHES_APPLICATION.md

**Key Insight to Emphasize:**
AEGIS doesn't just DETECT threats like competitors — it ACTS on them.
Forta tells you there's a fire. AEGIS triggers the sprinklers.
This is the key differentiator. Build all messaging around it.
```

---

## EXECUTION INSTRUCTIONS

### For Claude Code Users

Run each agent's prompt in a separate Claude Code session:

```bash
# Session 1: Business Model
claude "Read CLAUDE.md section 'AGENT 1: BUSINESS MODEL ARCHITECT' and execute the prompt"

# Session 2: Customer Discovery
claude "Read CLAUDE.md section 'AGENT 2: CUSTOMER DISCOVERY STRATEGIST' and execute the prompt"

# Session 3: Positioning
claude "Read CLAUDE.md section 'AGENT 3: POSITIONING & PITCH STRATEGIST' and execute the prompt"
```

### Expected Output Files

After all 3 agents complete:

```
docs/
├── BUSINESS_MODEL.md           # Agent 1
├── CUSTOMER_DISCOVERY.md       # Agent 2
├── TARGET_PROTOCOLS.md         # Agent 2
├── OUTREACH_TEMPLATES.md       # Agent 2
├── LOI_TEMPLATE.md             # Agent 2
├── COMPETITIVE_ANALYSIS.md     # Agent 3
├── POSITIONING.md              # Agent 3
├── PITCH_DECK_OUTLINE.md       # Agent 3
├── LANDING_PAGE_COPY.md        # Agent 3
└── BASE_BATCHES_APPLICATION.md # Agent 3
```

### Timeline

| Week | Agent | Deliverable |
|------|-------|-------------|
| Week 1 | Agent 1 | Business model + pricing |
| Week 2 | Agent 2 | Customer list + outreach |
| Week 3 | Agent 3 | Positioning + pitch deck |
| Week 4 | Human | Send outreach, get LOIs |

---

## APPENDIX: TECHNICAL COMMANDS

### Start Services
```bash
# All at once
bash scripts/run-demo.sh

# Individually
cd packages/agents-py && uvicorn aegis.api.server:app --port 8000
cd packages/api && npx tsx src/index.ts
cd packages/frontend && pnpm dev
```

### Deploy Contracts
```bash
cd packages/contracts
forge script script/Deploy.s.sol:DeployAegis \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast
```

### Run Tests
```bash
# Contracts
cd packages/contracts && forge test -vvv

# Python agents
cd packages/agents-py && python -m pytest tests/ -v
```

---

*Last Updated: March 8, 2026*
*Status: Preparing for Base Batches application*
