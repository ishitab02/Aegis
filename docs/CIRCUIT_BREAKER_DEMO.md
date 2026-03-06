# Circuit Breaker E2E Demo

> Shows the full AEGIS detection → consensus → circuit breaker → fund protection flow.

## Overview

This demo deploys a **TestVault** (a simple ETH vault) and demonstrates AEGIS detecting a simulated attack, triggering the circuit breaker, and **blocking withdrawals** to protect funds.

## Contracts

| Contract | Address | Explorer |
|----------|---------|----------|
| TestVault | `$TEST_VAULT_ADDRESS` | [BaseScan](https://sepolia.basescan.org/address/$TEST_VAULT_ADDRESS) |
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | [BaseScan](https://sepolia.basescan.org/address/0xa0eE49660252B353830ADe5de0Ca9385647F85b5) |

## Prerequisites

```bash
# 1. Environment variables
export DEPLOYER_PRIVATE_KEY=<your-key>
export BASE_SEPOLIA_RPC=https://sepolia.base.org

# 2. ETH on Base Sepolia (for gas)
# Get from faucet: https://www.alchemy.com/faucets/base-sepolia

# 3. Dependencies installed
pnpm install
cd packages/contracts && forge build
```

## Quick Start

```bash
# One-command deploy + demo:
cd packages/contracts
forge script script/DeployTestVault.s.sol:DeployTestVault \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast

# Copy the TestVault address from output, then:
export TEST_VAULT_ADDRESS=<deployed-address>
npx tsx scripts/demo-circuit-breaker.ts
```

## Step-by-Step Demo

### 1. Deploy TestVault

```bash
cd packages/contracts
forge script script/DeployTestVault.s.sol:DeployTestVault \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast --verify
```

This deploys the TestVault, registers it with the CircuitBreaker, grants the deployer the `CRE_WORKFLOW_ROLE`, and seeds it with 0.01 ETH.

### 2. (Optional) Register Separately

If you need to register later or with a different setup:

```bash
export TEST_VAULT_ADDRESS=<address-from-step-1>
npx tsx scripts/register-test-vault.ts
```

### 3. Start AEGIS Agent API (Optional)

The demo works without the agent API (falls back to direct on-chain trigger), but for the full AI detection flow:

```bash
cd packages/agents-py
source venv/bin/activate
uvicorn aegis.api.server:app --host 0.0.0.0 --port 8000
```

### 4. Run the Demo

```bash
npx tsx scripts/demo-circuit-breaker.ts
```

Or without the agent API:

```bash
npx tsx scripts/demo-circuit-breaker.ts --skip-api
```

### 5. Verify on Chain

```bash
# Check vault is paused
cast call $TEST_VAULT_ADDRESS "isPaused()" --rpc-url https://sepolia.base.org
# Returns: true

# Check TVL is preserved (funds NOT drained)
cast call $TEST_VAULT_ADDRESS "getTVL()" --rpc-url https://sepolia.base.org

# Attempt withdrawal (should revert)
cast send $TEST_VAULT_ADDRESS "withdraw(uint256)" 1000000000000000 \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --rpc-url https://sepolia.base.org
# Reverts with: EnforcedPause()
```

## Demo Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    AEGIS DEMO FLOW                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Show vault state                               │
│    TVL: 0.01 ETH │ Paused: false                       │
│                                                         │
│  Step 2: Normal deposit (0.001 ETH)                     │
│    ✓ Deposit succeeds → TVL: 0.011 ETH                 │
│                                                         │
│  Step 3: AEGIS detection cycle                          │
│    → 3 sentinels analyze (25% TVL drop simulated)       │
│    → Liquidity: CRITICAL (95% confidence)               │
│    → Oracle: CRITICAL (90% confidence)                  │
│    → Governance: NONE                                   │
│    → Consensus: CRITICAL (2/3 majority)                 │
│    → Action: CIRCUIT_BREAKER                            │
│                                                         │
│  Step 4: Trigger circuit breaker                        │
│    → CircuitBreaker.triggerBreaker(vault, CRITICAL)     │
│    → CircuitBreaker calls vault.pause()                 │
│    → Vault is now PAUSED                                │
│                                                         │
│  Step 5: Withdrawal BLOCKED                             │
│    ✗ vault.withdraw() → EnforcedPause                  │
│    ✓ Funds are safe!                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## What the Contracts Do

### TestVault.sol
- Simple ETH vault (deposit/withdraw)
- Inherits OpenZeppelin `Pausable`
- Accepts `pause()` calls from CircuitBreaker or owner
- When paused: `deposit()`, `withdraw()`, and `receive()` all revert

### CircuitBreaker.sol
- Role-based access: `CRE_WORKFLOW_ROLE` can trigger breakers
- `triggerBreaker()` records threat and calls `vault.pause()`
- Cooldown period (1 hour) before reset is allowed
- Auto-pause after 3 consecutive HIGH alerts

## Architecture (for judges)

```
CRE Workflow (30s cron)
    │
    ├── HTTP → Python Agent API → 3 AI Sentinels
    │                              ├── Liquidity Sentinel
    │                              ├── Oracle Sentinel
    │                              └── Governance Sentinel
    │
    ├── Consensus (2/3 majority) → CRITICAL
    │
    ├── EVM Write → CircuitBreaker.triggerBreaker()
    │                     │
    │                     └── vault.pause()
    │
    └── Withdrawal blocked: EnforcedPause ✓
```

## Video Recording Notes

1. **Start with dashboard** showing green/healthy state
2. **Show the deposit** working normally (terminal + BaseScan)
3. **Run detection** — show the 3 sentinels voting CRITICAL
4. **Trigger circuit breaker** — show the on-chain transaction
5. **Attempt withdrawal** — show `EnforcedPause` error (the "money shot")
6. **Explain** that this happened in seconds, not hours

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Not registered" | Run `register-test-vault.ts` |
| "AccessControl: missing role" | Deployer needs CRE_WORKFLOW_ROLE — use `register-test-vault.ts` |
| "Already paused" | Vault was paused from a previous run. Wait for cooldown + reset, or redeploy |
| Agent API 502 | Start the Python agent: `uvicorn aegis.api.server:app --port 8000` |
| Insufficient funds | Get Base Sepolia ETH from faucet |
