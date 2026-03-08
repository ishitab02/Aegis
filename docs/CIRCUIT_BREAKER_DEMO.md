# Circuit Breaker E2E Demo

TestVault | `$TEST_VAULT_ADDRESS` | [BaseScan](https://sepolia.basescan.org/address/$TEST_VAULT_ADDRESS)
| CircuitBreaker | `0xa0eE49660252B353830ADe5de0Ca9385647F85b5` | [BaseScan](https://sepolia.basescan.org/address/0xa0eE49660252B353830ADe5de0Ca9385647F85b5) |

```bash
export DEPLOYER_PRIVATE_KEY=<your-key>
export BASE_SEPOLIA_RPC=https://sepolia.base.org
pnpm install
cd packages/contracts && forge build
```

## Quick Start

```bash

cd packages/contracts
forge script script/DeployTestVault.s.sol:DeployTestVault \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast

export TEST_VAULT_ADDRESS=<deployed-address>
npx tsx scripts/demo-circuit-breaker.ts
```

```bash
cd packages/contracts
forge script script/DeployTestVault.s.sol:DeployTestVault \
  --rpc-url https://sepolia.base.org \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --broadcast --verify
```

### Run the Demo

```bash
npx tsx scripts/demo-circuit-breaker.ts
```

```bash
# Check vault is paused
cast call $TEST_VAULT_ADDRESS "isPaused()" --rpc-url https://sepolia.base.org
# Returns: true

# Check TVL is preserved
cast call $TEST_VAULT_ADDRESS "getTVL()" --rpc-url https://sepolia.base.org

# Attempt withdrawal
cast send $TEST_VAULT_ADDRESS "withdraw(uint256)" 1000000000000000 \
  --private-key $DEPLOYER_PRIVATE_KEY \
  --rpc-url https://sepolia.base.org
# Reverts with: EnforcedPause()
```

## Demo Flow Diagram (AI generated)

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

## Architecture (AI GEN)

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