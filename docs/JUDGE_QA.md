# AEGIS Protocol - Judge Q&A

Anticipated questions from Chainlink Convergence Hackathon judges with prepared answers.

---

## Track-Specific Questions

### 1. "Why did you choose the Risk & Compliance track?"

**Answer:**
DeFi's biggest compliance failure is protocol exploits. In 2024, over $3 billion was lost — not to fraud or regulatory violations, but to technical attacks that went undetected for minutes or hours.

AEGIS directly addresses this by providing:
- **Real-time risk monitoring** — continuous, not periodic audits
- **Automated compliance enforcement** — circuit breakers activate automatically
- **Immutable audit trail** — all detections and responses logged on-chain
- **Verifiable execution** — CRE ensures tamper-proof, consensus-verified workflows

We believe security IS compliance in DeFi. A protocol that can be drained in 5 minutes isn't compliant with any reasonable standard.

---

### 2. "How does CRE add value compared to a centralized monitoring service?"

**Answer:**
Three key advantages:

1. **Verifiable Execution**: CRE workflows run with BFT consensus. When AEGIS says "threat detected, circuit breaker triggered," that execution is cryptographically verified — not "trust me, I ran this code."

2. **Decentralized Reliability**: CRE runs on Chainlink's DON (Decentralized Oracle Network). No single server failure can take down monitoring. A centralized service has a single point of failure.

3. **On-Chain Integration**: CRE can directly write to smart contracts. We can trigger the CircuitBreaker in the same verified workflow that detected the threat — no off-chain to on-chain trust boundary.

A centralized service would require protocols to trust our server, our uptime, and our honesty. CRE eliminates that trust assumption.

---

### 3. "What happens if the AI makes a wrong prediction?"

**Answer:**
We have multiple safeguards:

1. **2/3 Consensus**: A single sentinel can't trigger a circuit breaker. Two of three must agree. This reduces false positives from any single malfunctioning agent.

2. **Threat Level Thresholds**: Only HIGH or CRITICAL threats trigger action. MEDIUM alerts are logged but don't pause the protocol.

3. **Configurable Thresholds**: Protocols can adjust sensitivity. A conservative protocol might set TVL drop threshold at 25%; an aggressive one at 10%.

4. **Cooldown Period**: After a circuit breaker triggers, there's a mandatory cooldown before it can be reset. This prevents oscillation but also gives time to verify the threat was real.

5. **Reputation Tracking**: The ReputationTracker contract logs each sentinel's accuracy over time. Sentinels with poor track records get lower weight in weighted consensus.

In the worst case, a false positive pauses a protocol for an hour. That's inconvenient but recoverable. A missed attack drains the protocol permanently.

---

### 4. "How do you prevent false positives?"

**Answer:**
Several mechanisms:

1. **Multi-signal analysis**: We don't just watch one metric. TVL drops + price deviations + governance anomalies must align for consensus.

2. **Context-aware thresholds**: A 10% TVL drop during a market crash is normal. A 10% drop when the market is flat is suspicious. Our sentinels factor in market conditions.

3. **2/3 consensus requirement**: Random noise might trigger one sentinel. It's unlikely to trigger two simultaneously with the same assessment.

4. **Graduated threat levels**: MEDIUM doesn't trigger action, just logging. This creates a "warning zone" before critical response.

5. **Historical baseline**: Our TVL tracking compares against rolling 1h/24h/7d averages, not just the previous reading. This smooths out normal volatility.

---

### 5. "What's the latency from attack start to detection?"

**Answer:**
**30 seconds or less.**

Our CRE workflow runs on a 30-second cron. Within that cycle:
- EVM reads fetch current protocol state (~2 seconds)
- Sentinel analysis runs in parallel (~1 second)
- Consensus determination (~0.1 seconds)
- Circuit breaker transaction submission (~3 seconds)

Total: Under 10 seconds of actual processing, bounded by the 30-second trigger interval.

For comparison:
- Manual detection: 30-60 minutes (someone notices on Twitter)
- Traditional monitoring: 5-15 minutes (alert fires, human reviews, decides)
- AEGIS: 30 seconds (fully automated)

---

## Technical Questions

### 6. "How do the AI agents actually work?"

**Answer:**
Each sentinel is a Python module with two components:

1. **Threshold-based detection** (no LLM needed): Pure Python functions that check metrics against configurable thresholds. Fast, deterministic, no API calls.

   ```python
   def monitor_tvl(current_tvl, previous_tvl):
       change = (previous_tvl - current_tvl) / previous_tvl
       if change >= 0.20:
           return ThreatAssessment(threat_level="CRITICAL", confidence=0.95)
   ```

2. **AI-enhanced analysis** (LLM for complex cases): CrewAI agents using Anthropic Claude for nuanced analysis — e.g., classifying whether a governance proposal is malicious.

The threshold checks run every cycle. The LLM is invoked only for forensic analysis or ambiguous cases, keeping costs and latency low.

---

### 7. "Why three sentinels? Why not more?"

**Answer:**
Three is the minimum for meaningful consensus:
- Two sentinels: 50/50 ties are possible, no clear majority
- Three sentinels: 2/3 majority is achievable and Byzantine fault-tolerant

We chose specialization over quantity:
- Liquidity Sentinel: Deep expertise in TVL, flash loans, withdrawals
- Oracle Sentinel: Deep expertise in price feeds, manipulation patterns
- Governance Sentinel: Deep expertise in proposal analysis

More sentinels would add complexity without proportional benefit. Each sentinel covers a distinct attack surface. Adding a fourth would either overlap or be too niche.

That said, the architecture supports N sentinels. Protocols could add custom sentinels for their specific risks.

---

### 8. "What DeFi protocols can AEGIS protect?"

**Answer:**
Currently implemented adapters:
- **Aave V3**: TVL, reserves, Supply/Withdraw/Borrow events
- **Uniswap V3**: Pool TVL, liquidity, large swap detection

The adapter pattern makes it easy to add more. Any protocol that exposes:
- A way to read TVL (totalSupply, getTVL, etc.)
- Events for significant actions (deposits, withdrawals, trades)

...can be integrated. We've designed for Compound V3, Curve, and generic ERC-4626 vaults as future additions.

---

### 9. "How does the circuit breaker work technically?"

**Answer:**
The CircuitBreaker.sol contract has a role-based access system:

1. **CRE_WORKFLOW_ROLE**: Only CRE workflows can trigger `triggerBreaker()`
2. **UNPAUSER_ROLE**: Only authorized admins can reset after cooldown

When triggered:
```solidity
function triggerBreaker(address protocol, bytes32 threatId, ThreatLevel level, string reason) {
    protocolStates[protocol].paused = true;
    // Attempt to call protocol.pause() if it exists
    protocol.call(abi.encodeWithSignature("pause()"));
    emit CircuitBreakerTriggered(...);
}
```

The protocol must grant AEGIS permission to call its `pause()` function. This is opt-in — we can't forcibly pause arbitrary contracts.

---

### 10. "How does ChainSherlock do forensic analysis?"

**Answer:**
ChainSherlock uses a multi-step process:

1. **Transaction Tracing**: Calls `debug_traceTransaction` (requires archive node) to get the full call stack
2. **Graph Building**: Constructs a directed graph of internal calls and ETH/token transfers
3. **Address Identification**: Matches addresses against a database of known entities (CEXs, mixers, attackers)
4. **Pattern Detection**: Looks for reentrancy signatures, flash loan patterns, price manipulation sequences
5. **AI Classification**: Uses Claude to synthesize findings into a human-readable report

The output is a `ForensicReport` with attack type, attack flow, affected funds, and recommendations.

---

### 11. "Why Python for AI agents and TypeScript for API?"

**Answer:**
Best tool for each job:

**Python (agents-py)**:
- CrewAI and most AI/ML libraries are Python-native
- web3.py is mature and well-documented
- Easier to iterate on AI logic

**TypeScript (api, cre-workflows)**:
- CRE SDK is TypeScript
- ethers.js v6 is the gold standard for EVM interaction
- Hono is fast and lightweight for the gateway API
- Frontend is React/Vite

The Python FastAPI server exposes HTTP endpoints that the TypeScript gateway proxies. Clean separation of concerns.

---

## Business & Impact Questions

### 12. "How would real protocols integrate this?"

**Answer:**
Three-step integration:

1. **Register Protocol**: Call `CircuitBreaker.registerProtocol(protocolAddress)`
2. **Grant Pause Permission**: The protocol grants `PAUSER_ROLE` to the CircuitBreaker contract
3. **Configure Thresholds**: Set TVL drop %, price deviation %, etc. via the AEGIS dashboard

For production, we'd add:
- Web portal for self-service registration
- x402 payment integration for subscriptions
- SDK for protocols to embed AEGIS status in their UI

---

### 13. "What's the business model?"

**Answer:**
Three revenue streams:

1. **Protocol Subscriptions**: $100-1000/month depending on TVL, for continuous monitoring
2. **Forensic Reports**: $1-10 per report via x402 micropayments — pay-per-use forensics
3. **Insurance Integration**: Partner with DeFi insurance protocols. AEGIS-protected protocols get reduced premiums; we get a cut.

The x402 payment layer is already integrated in the codebase. Protocols would pay in USDC on Base.

---

### 14. "Who are your competitors?"

**Answer:**
Existing solutions:
- **OpenZeppelin Defender**: Monitoring + automation, but no AI analysis, no consensus
- **Forta**: Alert bots, but reactive (alerts after detection), no circuit breakers
- **Chainalysis/Elliptic**: Focus on AML/compliance, not real-time exploit detection
- **Trail of Bits/Consensys Diligence**: Audits, but point-in-time, not continuous

AEGIS differentiators:
- **Autonomous response**: We trigger circuit breakers, not just alerts
- **AI consensus**: Multiple specialized agents, not single-model detection
- **Chainlink verification**: CRE ensures tamper-proof execution
- **Integrated forensics**: Detection + investigation in one system

---

### 15. "What's your team's background?"

**Answer:**
[Customize based on actual team]

- Deep experience in DeFi security research
- Previous work on smart contract auditing
- Background in AI/ML systems
- Familiar with Chainlink ecosystem

---

## Chainlink-Specific Questions

### 16. "Why did you choose these 5 Chainlink services specifically?"

**Answer:**
Each service solves a specific problem:

| Service | Problem Solved |
|---------|----------------|
| **CRE** | Need verifiable, tamper-proof workflow execution |
| **Data Feeds** | Need source of truth for price comparison |
| **Automation** | Need 24/7 scheduled monitoring without manual triggers |
| **VRF** | Need provably fair tie-breaking when sentinels disagree |
| **CCIP** | Need to propagate alerts across chains (Base → Ethereum → Arbitrum) |

We didn't add services for the sake of the bonus. Each one is architecturally necessary.

---

### 17. "How do you use VRF in the consensus mechanism?"

**Answer:**
VRF handles edge cases where sentinels are split 1-1-1 (three different threat levels).

Instead of defaulting to "no action" (dangerous) or "most severe" (false positive risk), we use VRF to randomly select one sentinel's vote as the tie-breaker — weighted by their reputation score.

This ensures:
- **Fairness**: No hardcoded preference
- **Unpredictability**: Attackers can't game the tie-breaker
- **Accountability**: Selected sentinel's reputation is on the line

Code: `packages/cre-workflows/src/workflows/vrfTieBreaker/main.ts`

---

### 18. "How does CCIP fit into your architecture?"

**Answer:**
Many DeFi protocols deploy on multiple chains (Aave on Ethereum, Arbitrum, Base, etc.).

When AEGIS detects a threat on one chain, CCIP propagates the alert to all other chains. This enables:
- **Coordinated pause**: All deployments pause, not just the attacked one
- **Cross-chain forensics**: Track funds that bridge to other chains
- **Unified alerting**: Operators get one alert for all chains

Example: Attack on Base → CCIP message to Ethereum → Ethereum deployment pauses preemptively.

Code: `packages/cre-workflows/src/workflows/ccipAlert/main.ts`

---

### 19. "What are the limitations of your current implementation?"

**Answer:**
Honest limitations:

1. **Simulation mode**: Current demo uses simulated threat parameters. Real-world use needs live protocol connections (adapters are built, just need mainnet RPCs).

2. **CRE deployment**: Workflows are coded and tested but not yet deployed to Chainlink's production DON.

3. **Limited adapters**: Only Aave V3 and Uniswap V3 adapters are complete. Other protocols need custom adapters.

4. **Archive node dependency**: Deep forensic tracing requires archive node access, which is expensive.

5. **Protocol opt-in**: We can only pause protocols that explicitly grant us permission. We can't protect protocols that don't integrate.

---

### 20. "What would you build next with more time?"

**Answer:**
Priority order:

1. **Production CRE deployment**: Get workflows running on Chainlink mainnet
2. **More protocol adapters**: Compound, Curve, Yearn, MakerDAO
3. **ML-based detection**: Train models on historical exploit data for predictive (not just reactive) detection
4. **Protocol onboarding portal**: Self-service registration with x402 payments
5. **Insurance integration**: Partner with Nexus Mutual, InsurAce for premium discounts
6. **Cross-chain dashboard**: Unified view of all protected protocols across all chains
7. **DAO governance**: Decentralize AEGIS itself — sentinel operators stake and govern upgrades

---

## Rapid-Fire Questions

### "Can it stop a flash loan attack?"
Yes. The Oracle Sentinel detects price manipulation that often accompanies flash loan attacks. If the price deviates > 5% from Chainlink, we flag CRITICAL.

### "What if the attacker attacks AEGIS itself?"
AEGIS doesn't hold funds. The worst case is a DoS that delays detection. The protocol's own contracts still hold the funds — pausing them protects assets.

### "Is the circuit breaker a centralization risk?"
The circuit breaker is a smart contract with role-based access. CRE workflows (verified execution) trigger it, not a single admin key. The protocol can revoke AEGIS's permission at any time.

### "How do you handle MEV?"
We submit circuit breaker transactions with high priority gas. For production, we'd integrate with Flashbots Protect to prevent frontrunning.

### "What's your test coverage?"
- Smart contracts: 21 tests (Foundry)
- Python agents: 96 tests (pytest)
- All passing

### "Is this open source?"
Yes, MIT licensed. Anyone can run their own AEGIS instance or contribute adapters.

---

## Final Talking Points

If you only have 30 seconds with a judge:

> "AEGIS is the immune system for DeFi. Three AI sentinels monitor protocols 24/7 using Chainlink Data Feeds. When two of three agree on a critical threat, we automatically trigger an on-chain circuit breaker — verified by Chainlink CRE — and pause the protocol in 30 seconds. Not 30 minutes. Not 3 hours. 30 seconds. That's the difference between 'funds protected' and '$200 million gone.'"

If they ask for the technical hook:

> "We use CRE for verifiable workflow execution, Data Feeds for price truth, Automation for scheduled monitoring, VRF for fair tie-breaking, and CCIP for cross-chain alerts. Five Chainlink services, working together, to build something that wasn't possible before."

If they ask about impact:

> "In 2024, DeFi lost $3 billion. With AEGIS, that number could be close to zero."
