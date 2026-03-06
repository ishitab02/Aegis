# AEGIS ChainSherlock — Euler Finance Forensics Demo

## Exploit Overview

| Field | Value |
|-------|-------|
| **Protocol** | Euler Finance |
| **Date** | March 13, 2023 |
| **Block** | 16818057 (Ethereum Mainnet) |
| **Transaction** | `0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d` |
| **Amount Stolen** | ~$197,000,000 |
| **Attack Type** | Flash Loan + Donation Attack |
| **Attacker EOA** | `0x9799b475dEc92Bd99bbdD943013325C36157f383` |
| **Attack Contract** | `0xeBC29199C817Dc47BA12E3F86102564D640539d5` |
| **Funds Recovered** | ✅ Yes (~98% returned after negotiation) |

---

## Attack Flow (9 Steps)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Aave V2    │     │  Attacker   │     │   Euler     │
│ Flash Loan  │     │  Contract   │     │  Finance    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
  1.   │  30M DAI flash    │                   │
       │──────────────────>│                   │
       │                   │                   │
  2.   │                   │  deposit DAI      │
       │                   │──────────────────>│
       │                   │                   │
  3.   │                   │  receive eDAI     │
       │                   │<──────────────────│
       │                   │                   │
  4.   │                   │  borrow 10× via   │
       │                   │  mint() → dDAI    │
       │                   │──────────────────>│
       │                   │                   │
  5.   │                   │  inflate position │
       │                   │  (repeat 4)       │
       │                   │──────────────────>│
       │                   │                   │
  6.   │                   │ ★ donateToReserves│
       │                   │  (THE BUG — no    │
       │                   │  health check)    │
       │                   │──────────────────>│
       │                   │                   │
  7.   │                   │  self-liquidate   │
       │                   │  sub-acct 0 from  │
       │                   │  sub-acct 1       │
       │                   │──────────────────>│
       │                   │                   │
  8.   │                   │  withdraw DAI     │
       │                   │  (profit!)        │
       │                   │<──────────────────│
       │                   │                   │
  9.   │  repay flash loan │                   │
       │<──────────────────│                   │
       │                   │                   │
       ▼                   ▼                   ▼
```

### Step-by-Step Details

1. **Flash Loan**: Borrow 30M DAI from Aave V2 (no collateral needed)
2. **Deposit**: Send DAI into Euler Finance, receive eDAI (deposit tokens)
3. **Leverage**: Call `mint()` to borrow 10× against deposits, getting dDAI (debt tokens)
4. **Inflate**: Repeat borrow/repay cycle to inflate eDAI balance to ~195M
5. **Repay Partial**: Manage debt to set up the exploit
6. **THE BUG — Donate**: Call `donateToReserves()` to burn all eDAI. This function had **no health check** — it allowed the account to become insolvent (negative equity, still holding dDAI debt)
7. **Self-Liquidate**: Use sub-account 1 to liquidate the now-insolvent sub-account 0. Receive a liquidation bonus on fabricated collateral
8. **Withdraw**: Convert the inflated eDAI from sub-account 1 to real DAI
9. **Repay**: Return 30M DAI + fee to Aave. Keep the ~$8.9M+ profit from this token alone

This was repeated across **6 tokens**: DAI, USDC, USDT, WBTC, wstETH, stETH.

---

## Tokens Drained

| Token | Amount | Approximate USD |
|-------|--------|-----------------|
| DAI | 8,877,507.35 | $8.88M |
| USDC | 33,827,832.00 | $33.83M |
| USDT | 18,548,141.00 | $18.55M |
| WBTC | 849.14 | $21.2M |
| wstETH | 73,821.00 | $116M |
| stETH | 8,099.30 | $13.5M |
| **Total** | | **~$197M** |

---

## Root Cause

### Vulnerability

The `donateToReserves()` function in Euler's EToken contract allowed users to donate their eTokens (deposit tokens) to the protocol reserves **without checking if the donor's account remained solvent afterwards**.

```solidity
// Simplified — the bug was the ABSENCE of a health check
function donateToReserves(uint subAccountId, uint amount) external {
    // Burns eTokens from the user
    // Adds to protocol reserves
    // ❌ MISSING: checkLiquidity(account) — no solvency verification!
}
```

### Why It Was Exploitable

1. An attacker could deposit + borrow to create a leveraged position (lots of eTokens and dTokens)
2. Donate ALL their eTokens to reserves → account becomes insolvent (has debt, no collateral)
3. Self-liquidate the insolvent account from another sub-account → receive liquidation discount
4. The liquidation logic gifts the liquidator collateral from the reserves at a discount, creating value from nothing

### Fix

```solidity
function donateToReserves(uint subAccountId, uint amount) external {
    // Burns eTokens from the user
    // Adds to protocol reserves
    checkLiquidity(account);  // ✅ FIX: verify account is still solvent
}
```

---

## Fund Tracking

### Destinations

| Destination | Amount | Type |
|-------------|--------|------|
| Attacker EOA (`0x9799..`) | ~$197M | Initial recipient |
| Tornado Cash Router | 100 ETH | Mixer (laundering attempt) |
| Euler Return Address (`0xc66d..`) | ~$193M | **Returned** |
| Aave V2 Pool | $30M+ | Flash loan repayment |

### Recovery

After on-chain messages from the Euler team and negotiation:
- **March 18**: Attacker sends 100 ETH through Tornado Cash
- **March 25**: Attacker begins returning funds
- **April 4**: Approximately **98%** of stolen funds returned
- Euler offered a $1M bounty for information leading to the attacker's arrest

---

## AEGIS Detection Patterns

ChainSherlock identified these patterns:

| Pattern | Confidence | Evidence |
|---------|-----------|----------|
| **FLASH_LOAN** | 98% | 30M DAI borrowed and returned in same TX |
| **DONATION_ATTACK** | 99% | `donateToReserves()` call creating insolvency |
| **SELF_LIQUIDATION** | 97% | Attacker liquidated own sub-account |
| **MIXER_USAGE** | HIGH | 100 ETH sent to Tornado Cash |

---

## How to Run the Analysis

### Quick Mode (no RPC needed)
```bash
python scripts/analyze-euler-hack.py --quick
```

### Full Mode (with archive node)
```bash
ALCHEMY_API_KEY=your-key python scripts/analyze-euler-hack.py
```

### JSON Output
```bash
python scripts/analyze-euler-hack.py --json
```

### API Endpoint
```bash
# Start the AEGIS agent API
cd packages/agents-py && uvicorn aegis.api.server:app --port 8000

# Get the Euler demo report
curl http://localhost:8000/api/v1/forensics/demo/euler | jq .
```

---

## API Response Structure

`GET /api/v1/forensics/demo/euler` returns:

```json
{
  "reportId": "euler-hack-2023-03-13-0xc310a0affe21...",
  "status": "COMPLETE",
  "timestamp": 1678752000,
  "exploit": {
    "name": "Euler Finance Hack",
    "date": "2023-03-13",
    "block": 16818057,
    "txHash": "0xc310a0af...",
    "amountStolenUSD": 197000000,
    "attackType": "FLASH_LOAN + DONATION_ATTACK"
  },
  "report": {
    "report_id": "...",
    "attack_classification": {
      "primary_type": "FLASH_LOAN",
      "confidence": 0.98,
      "description": "Flash loan + donation attack..."
    },
    "attack_flow": [...],
    "root_cause": {...},
    "impact_assessment": {
      "funds_at_risk": "197000000",
      "severity": "CRITICAL"
    },
    "fund_tracking": {
      "destinations": [...],
      "recovery_possibility": "HIGH"
    }
  },
  "transactionGraph": {
    "nodes": [...],
    "edges": [...],
    "patterns_detected": [...],
    "risk_indicators": [...]
  }
}
```

---

## References

- [Euler Finance Post-Mortem](https://www.euler.finance/blog/euler-finance-attack-post-mortem)
- [BlockSec Analysis](https://twitter.com/BlockSecTeam/status/1635267386932600832)
- [Etherscan TX](https://etherscan.io/tx/0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d)
- [Rekt News — Euler Finance](https://rekt.news/euler-rekt/)
