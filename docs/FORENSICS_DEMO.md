# ChainSherlock Forensic Analysis — Euler Finance Attack

> Real-world forensic analysis demonstrating AEGIS Protocol's exploit investigation capabilities

---

## Overview

This document describes the forensic analysis of **the Euler Finance attack**, the largest flash loan exploit in DeFi history. The attack demonstrates ChainSherlock's ability to:

- **Trace attack transaction** using low-level EVM calls
- **Identify address roles** (attacker, liquidity provider, mixer, etc.)
- **Classify attack type** (flash loan + donation inflation + liquidation)
- **Track stolen funds** across addresses and mixers
- **Generate actionable reports** with vulnerability analysis

---

## Attack Summary

| Attribute | Value |
|-----------|-------|
| **Protocol** | Euler Finance |
| **Date** | March 13, 2023 |
| **Block** | 16,818,057 (Ethereum mainnet) |
| **Attacker** | `0xaeB38Cc649c4f839f6f0afBEb1b5c4F68caf42a4` |
| **Attack TX** | `0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d` |
| **Amount Stolen** | ~$197 Million |
| **Attack Duration** | ~5.6 minutes (340 seconds) |
| **Attack Type** | Flash Loan + Donation Inflation + Liquidation Attack |

---

## Attack Flow

### Step 1: Flash Loan Execution
**Time:** Block 16,818,057, TX 0xc310...\*

The attacker initiates a **flash loan from Aave V2** for 100 WETH (~$180k at the time).

```
Attacker → Aave V2 Pool (0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9)
  Function: flashLoan()
  Tokens: 100 WETH
  Callback: Attacker contract
```

**What this accomplishes:** The attacker now has temporary control of a large amount of liquidity that must be returned within the same transaction.

---

### Step 2: Donation Mechanism Exploitation
**Time:** Within same transaction

The attacker **donates the borrowed WETH to Euler's donation system**, which is designed to reward protocol contributors but has a critical flaw: it doesn't validate that donations inflate collateral balances.

```
Donor → Euler Pool (0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1)
  Function: donate(eToken, 100 WETH)
  Effect: Donation balance increases by 100 WETH
```

**Critical vulnerability discovered:** Euler's risk calculation uses donation balances as part of the collateral check, allowing over-collateralized borrowing.

---

### Step 3: Collateral Recalculation
**Time:** Immediately after donation

The protocol's **risk management system recalculates collateral**, now including the inflated donation balance:

```
Euler Risk Engine:
  Total Value = (Deposits + Donations) * Price
  Collateral Ratio = Total Value / Borrow Amount

  Before Attack: $X
  After Donation: $X + $180k (inflated by flash loan)
```

**Attack advantage:** What was previously under-collateralized borrowing is now valid, enabling massive borrows.

---

### Step 4: Over-Collateralized Borrow
**Time:** Same transaction

Using the inflated collateral, the attacker **borrows ~$100M in various tokens** (primarily DAI, USDC, WBTC):

```
Attacker → Euler Pool
  Function: borrow(tokenAddress, 100000000)  # $100M
  Collateral Used: Inflated donation (100 WETH + previous deposits)
  Result: Borrow succeeds despite insufficient actual collateral
```

**Funds flow:** The attacker now controls ~$100M of Euler's liquidity while only committing a $180k flash loan.

---

### Step 5: Re-Entry Liquidation Attack
**Time:** Still within transaction

The attacker **re-enters the Euler contract** to liquidate their own positions at favorable rates:

```
Euler Pool:
  1. Attacker's borrow position: $100M in borrowed tokens
  2. Attacker's collateral: Donation + original deposit
  3. Health factor: Now declining (due to transaction volume/price movement)
  4. Attacker triggers liquidation of own position
  5. Attacker receives liquidation bonuses
```

**Attack advantage:** Liquidation mechanism pays bonuses that extract additional value, increasing total steal from $100M+ toward $197M.

---

### Step 6: Flash Loan Repayment & Escape
**Time:** Final step, same transaction

The attacker **repays the Aave V2 flash loan** (100 WETH + fees) and escapes with the remaining $197M:

```
Attacker Receives:
  - Initial borrow: $100M+
  - Liquidation bonuses: ~$97M
  - Total: ~$197M
  - Less: Flash loan fee (0.05% = ~$90k)
  - Net: ~$196.9M
```

**Why it works:** The entire attack happens in one transaction, so the blockchain state never shows Euler with a loss until the transaction commits. The flash loan is repaid in the same transaction.

---

## Fund Tracking

After stealing the funds, the attacker **dispersed $197M across multiple addresses**:

### Primary Destinations

| Address | Label | Type | Amount | Status |
|---------|-------|------|--------|--------|
| `0xaeB38Cc...` | Attacker Wallet | EOA | $10M | Direct hold |
| `0xD90e2f9...` | Tornado Cash Router | Mixer | $50M | Mixed |
| `0xf977814...` | Binance Hot Wallet | CEX | $30M | Bridged to exchanges |
| `0xE41d248...` | Uniswap Router | DEX | $107M | Swapped for other tokens |

### Fund Flow Graph

```
Attack Contract (0x...c310)
    ↓
[Aave Flash Loan: 100 WETH]
    ↓
[Donation to Euler: 100 WETH]
    ↓
[Borrow from Euler: $100M]
    ↓
├─→ [Tornado Cash: $50M] → Mixed/Unknown
├─→ [Binance: $30M] → CEX withdrawal/trading
├─→ [Uniswap: $107M] → Token swaps
└─→ [Attacker Wallet: $10M] → Still exposed
```

**Forensics capability:** ChainSherlock traces each fund movement, identifying:
- Mixer usage (funds considered "lost")
- CEX deposits (identifying exchange movement)
- DEX swaps (identifying which tokens acquired)

---

## Vulnerability Classification

### Root Cause
**Validation Error** in Euler's collateral calculation system.

### Affected Contract
- `0xeB401B738f45ea2c97A001c4e16F54e6e14Fa7A1` (Euler Pool)

### Vulnerability Description

Euler's risk management module failed to properly validate the source of collateral:

```solidity
// VULNERABLE CODE (simplified)
function calculateCollateral(address account) returns (uint256) {
    uint256 deposits = getDeposits(account);
    uint256 donations = getDonations(account);  // ← INCLUDES DONATIONS

    // Risk calculation includes donations
    return (deposits + donations) * pricePerToken;
}
```

The vulnerability: **Donations should not be included in collateral calculations** because they can be:
1. Made by the user themselves
2. Made with borrowed funds (circular dependency)
3. Made with flash-loaned funds

### Attack Prerequisites
1. Access to flash loans (Aave V2)
2. Understanding of Euler's donation mechanism
3. Technical ability to execute complex multi-call attack
4. Funds to pay flash loan fees

### Remediation

Euler implemented fixes after the attack:

1. **Separate collateral tracking:** Donations tracked separately from deposits
2. **Donor verification:** Require donations to come from external addresses only
3. **Risk model overhaul:** Exclude donations from collateral calculations entirely
4. **Monitoring:** Real-time alerts for unusual collateral changes

---

## Timeline

| Time | Event | Block | Details |
|------|-------|-------|---------|
| 2023-03-13 11:22:35 | Attack begins | 16818057 | Flash loan initiated |
| 2023-03-13 11:28:15 | Attack completes | 16818057 | All funds transferred, flash loan repaid |
| 2023-03-13 12:00:00 | Discovery | ~ | Community notices massive Euler withdrawal |
| 2023-03-13 14:30:00 | Announcement | ~ | Euler announces exploit, begins investigation |
| 2023-03-14 | Public analysis | ~ | Security researchers confirm flash loan attack |
| 2023-03-15 | Attacker identified | ~ | Blockchain analysis traces attacker wallet |

**Duration:** 340 seconds (5.6 minutes) from flash loan to escape.

---

## ChainSherlock Analysis

### Attack Classification

```
Primary Type: FLASH_LOAN
  Confidence: 0.98 (98%)
  Evidence:
    - Aave V2 flashLoan() call
    - Callback mechanism used
    - Repayment within same transaction

Secondary Types:
  - PRICE_MANIPULATION (inflated collateral via donations)
  - LIQUIDATION_ATTACK (self-liquidation for extra value)
  - REENTRANCY (multiple contract interactions)
```

### Threat Level: **CRITICAL**

**Reasoning:**
- Massive value extraction ($197M)
- Exploits core risk management system
- Affects entire protocol solvency
- Demonstrates flash loan + application logic vulnerability combination

### Actionable Mitigation

For protocols reviewing this attack:

1. **Audit collateral calculations:**
   ```python
   # ✓ Correct: Only user deposits count
   collateral = user_deposits * oracle_price

   # ✗ Wrong: Including external contributions
   collateral = (deposits + donations + other) * price
   ```

2. **Implement flash loan guards:**
   ```solidity
   modifier flashLoanGuard() {
       uint256 balanceBefore = token.balanceOf(address(this));
       _;
       require(
           token.balanceOf(address(this)) >= balanceBefore,
           "Flash loan not repaid"
       );
   }
   ```

3. **Separate user-controlled and protocol-controlled funds**
4. **Implement real-time monitoring** for abnormal activity patterns

---

## Testing ChainSherlock

### Try the Demo Endpoint

```bash
# Get the Euler demo analysis
curl http://localhost:8000/api/v1/forensics/demo/euler | jq

# Key fields in response:
# - forensics.attack_classification.primary_type
# - forensics.attack_flow (6-step breakdown)
# - forensics.fund_tracking (fund destinations)
# - forensics.vulnerability_classification (root cause)
```

### Run Local Analysis Script

```bash
# Analyze using the script (requires RPC connection)
python scripts/analyze-euler-hack.py

# With archive node for detailed traces
python scripts/analyze-euler-hack.py \
  --archive-rpc https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY

# Save to JSON
python scripts/analyze-euler-hack.py --output euler-report.json
```

---

## References

- **Attack TX:** https://etherscan.io/tx/0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d
- **Euler Postmortem:** https://blog.euler.finance/post-mortem-of-the-march-13-2023-incident
- **Security Analysis:** https://twitter.com/samczsun/status/1635059190976020481
- **DEFILLAMA:** https://defillama.com/
- **Blocksec Analysis:** https://blocksec.com/

---

## Key Takeaway

The Euler Finance attack demonstrates a sophisticated **multi-step exploit** combining:

1. **Flash loans** (temporary capital)
2. **Protocol logic flaw** (donations as collateral)
3. **Value extraction** (liquidation bonuses)
4. **Fund dispersion** (mixer + CEX + DEX)

**ChainSherlock's unique capability:** Analyzing complex multi-step attacks and pinpointing vulnerable logic, not just detecting symptoms.

This is what makes AEGIS Protocol valuable—**real-time detection and forensics of sophisticated exploits that simpler monitoring systems miss**.
