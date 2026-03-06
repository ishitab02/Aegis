"""Pre-computed Euler Finance hack analysis for demo purposes.

The Euler Finance exploit occurred on March 13, 2023 (block 16818057).
The attacker drained ~$197M across multiple tokens (DAI, USDC, USDT, WBTC, wstETH, stETH).

This module contains a hardcoded forensic report built from real on-chain data so that
the demo endpoint can return it instantly without needing an archive node.

The attacker later returned the majority of the funds after negotiation.
"""

from __future__ import annotations

from aegis.models import (
    AttackClassification,
    AttackStep,
    AttackType,
    ForensicReport,
    FundDestination,
    FundDestinationType,
    FundTracking,
    ImpactAssessment,
    RecoveryPossibility,
    RootCause,
    ThreatLevel,
)

# ── Euler Hack Constants ─────────────────────────────────────────────
EULER_TX_HASH = "0xc310a0affe2169d1f6feec1c63dbc7f7c62a887fa48795d327d4d2da2d6b111d"
EULER_BLOCK = 16818057
EULER_DATE = "2023-03-13"
EULER_AMOUNT_USD = 197_000_000
EULER_ATTACKER_EOA = "0x9799b475dEc92Bd99bbdD943013325C36157f383"
EULER_ATTACKER_CONTRACT = "0xeBC29199C817Dc47BA12E3F86102564D640539d5"
EULER_PROTOCOL = "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE"  # Euler main
EULER_RETURN_ADDRESS = "0xc66dFA84BC1B93dF194Bd22336D4C71CFB5Cfe9f"

# Tokens drained
EULER_STOLEN_TOKENS = {
    "DAI": {"amount": 8_877_507.35, "address": "0x6B175474E89094C44Da98b954EescdeCB5B42d03"},
    "USDC": {"amount": 33_827_832.00, "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"},
    "USDT": {"amount": 18_548_141.00, "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
    "WBTC": {"amount": 849.14, "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"},
    "wstETH": {"amount": 73_821.00, "address": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"},
    "stETH": {"amount": 8_099.30, "address": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"},
}


EULER_ATTACK_FLOW: list[dict[str, str | int]] = [
    {
        "step": 1,
        "action": "Attacker deploys malicious contract at 0xeBC291...",
        "contract": EULER_ATTACKER_CONTRACT,
        "detail": "Contract is designed to exploit the donate-to-reserves + liquidation logic",
    },
    {
        "step": 2,
        "action": "Flash loan 30M DAI from Aave V2",
        "contract": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
        "detail": "Borrows DAI with no collateral via Aave flashLoan()",
    },
    {
        "step": 3,
        "action": "Deposit DAI into Euler via sub-account 0 → receive eDAI",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "deposit() gives the attacker eDAI (Euler deposit tokens)",
    },
    {
        "step": 4,
        "action": "Borrow 10× the deposit via Euler mint() → get dDAI (debt tokens)",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "mint() creates leveraged position: 200M eDAI, 190M dDAI debt",
    },
    {
        "step": 5,
        "action": "Repay part of the debt, then repeat borrow to inflate position",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "Iteratively inflates the eDAI balance while managing debt tokens",
    },
    {
        "step": 6,
        "action": "Donate eDAI to Euler reserves via donateToReserves()",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "KEY BUG: donateToReserves() burns eDAI but doesn't check health factor. "
        "Makes sub-account 0 insolvent (no eDAI, still has dDAI debt)",
    },
    {
        "step": 7,
        "action": "Self-liquidate insolvent sub-account 0 from sub-account 1",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "liquidate() transfers discounted collateral to sub-account 1 and "
        "forgives the debt of sub-account 0. Attacker receives more eDAI than debt owed",
    },
    {
        "step": 8,
        "action": "Withdraw DAI from Euler via sub-account 1",
        "contract": "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE",
        "detail": "withdraw() converts the inflated eDAI into real DAI tokens, draining Euler",
    },
    {
        "step": 9,
        "action": "Repay Aave flash loan (30M DAI + fee)",
        "contract": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
        "detail": "Returns the flash loan. Profit: extracted DAI minus flash loan cost",
    },
]


def get_euler_attack_steps() -> list[AttackStep]:
    """Return the Euler attack flow as AttackStep models."""
    return [
        AttackStep(
            step=s["step"],
            action=str(s["action"]),
            contract=str(s["contract"]),
        )
        for s in EULER_ATTACK_FLOW
    ]


def get_euler_fund_destinations() -> list[FundDestination]:
    """Return known fund destinations from the Euler hack."""
    return [
        FundDestination(
            address=EULER_ATTACKER_EOA,
            amount=str(EULER_AMOUNT_USD),
            type=FundDestinationType.UNKNOWN,
        ),
        FundDestination(
            address="0xc66dFA84BC1B93dF194Bd22336D4C71CFB5Cfe9f",
            amount=str(int(EULER_AMOUNT_USD * 0.98)),
            type=FundDestinationType.UNKNOWN,  # returned to Euler
        ),
        FundDestination(
            address="0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
            amount="1000",
            type=FundDestinationType.MIXER,  # 100 ETH sent through Tornado Cash early
        ),
        FundDestination(
            address="0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
            amount="30000000",
            type=FundDestinationType.UNKNOWN,  # Aave flash loan repaid
        ),
    ]


def get_euler_forensic_report() -> ForensicReport:
    """Return a pre-computed ForensicReport for the Euler Finance hack.

    This is based on publicly available post-mortem data:
    - Euler Labs post-mortem: https://www.euler.finance/blog/euler-finance-attack-post-mortem
    - BlockSec analysis
    - On-chain data from block 16818057
    """
    return ForensicReport(
        report_id="euler-hack-2023-03-13-" + EULER_TX_HASH[:16],
        tx_hash=EULER_TX_HASH,
        protocol=EULER_PROTOCOL,
        attack_classification=AttackClassification(
            primary_type=AttackType.FLASH_LOAN,
            confidence=0.98,
            description=(
                "Flash loan + donation attack on Euler Finance. "
                "The attacker exploited a missing health-check in the donateToReserves() "
                "function. By donating inflated eTokens to reserves, the attacker could "
                "make a sub-account insolvent and then self-liquidate it from another "
                "sub-account, extracting a liquidation bonus on fabricated collateral. "
                "The attack was repeated across 6 tokens (DAI, USDC, USDT, WBTC, wstETH, stETH) "
                "draining approximately $197M."
            ),
        ),
        attack_flow=get_euler_attack_steps(),
        root_cause=RootCause(
            vulnerability=(
                "Missing health-check in donateToReserves(): The function allowed users to "
                "donate their eTokens (deposit tokens) to the protocol reserves without "
                "verifying that the donor's account remained solvent afterwards. This enabled "
                "an attacker to donate away all their eTokens, making their account insolvent "
                "(negative equity) while still holding dTokens (debt). The insolvent account "
                "could then be self-liquidated from another sub-account, granting the liquidator "
                "a discount on the (now nonexistent) collateral, effectively minting tokens "
                "out of thin air."
            ),
            affected_code=(
                "Euler EToken.donateToReserves() at "
                "0xe025E3ca2bE02316033184551D4d3Aa22c1E9eeE — "
                "no checkLiquidity() call after burning the donor's eToken balance"
            ),
            recommendation=(
                "1. Add a post-operation health/solvency check (checkLiquidity()) to "
                "donateToReserves() to prevent intentional self-insolvency.\n"
                "2. Prevent self-liquidation (liquidating your own sub-accounts).\n"
                "3. Consider adding donation limits or governance approval for large donations.\n"
                "4. Implement circuit breakers that pause when TVL drops > 20% in a single block."
            ),
        ),
        impact_assessment=ImpactAssessment(
            funds_at_risk=str(EULER_AMOUNT_USD),
            affected_users="Approximately 200+ depositors across 6 Euler lending markets",
            severity=ThreatLevel.CRITICAL,
        ),
        fund_tracking=FundTracking(
            destinations=get_euler_fund_destinations(),
            recovery_possibility=RecoveryPossibility.HIGH,
        ),
        timestamp=1678752000,  # 2023-03-13T12:00:00Z
    )


# Detailed graph-like summary for the demo endpoint
EULER_TRANSACTION_GRAPH = {
    "root_tx": EULER_TX_HASH,
    "block_number": EULER_BLOCK,
    "date": EULER_DATE,
    "protocol": "Euler Finance",
    "protocol_address": EULER_PROTOCOL,
    "attacker_addresses": [
        {
            "address": EULER_ATTACKER_EOA,
            "label": "Euler Exploiter (primary EOA)",
            "type": "ATTACKER",
        },
        {
            "address": EULER_ATTACKER_CONTRACT,
            "label": "Euler Attack Contract",
            "type": "ATTACKER",
        },
    ],
    "nodes": [
        {"address": EULER_ATTACKER_EOA, "label": "Attacker EOA", "type": "ATTACKER"},
        {"address": EULER_ATTACKER_CONTRACT, "label": "Attack Contract", "type": "ATTACKER"},
        {"address": EULER_PROTOCOL, "label": "Euler Finance", "type": "CONTRACT"},
        {"address": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9", "label": "Aave V2 Pool", "type": "FLASHLOAN_PROVIDER"},
        {"address": "0x27182842E098f60e3D576794A5bFFb0777E025d3", "label": "Euler eUSDC", "type": "CONTRACT"},
        {"address": "0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b", "label": "Tornado Cash", "type": "MIXER"},
        {"address": EULER_RETURN_ADDRESS, "label": "Euler Return Address", "type": "RETURN"},
    ],
    "edges": [
        {
            "from": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
            "to": EULER_ATTACKER_CONTRACT,
            "token": "DAI",
            "amount": "30,000,000",
            "label": "Flash Loan (Step 2)",
        },
        {
            "from": EULER_ATTACKER_CONTRACT,
            "to": EULER_PROTOCOL,
            "token": "DAI",
            "amount": "20,000,000",
            "label": "Deposit (Step 3)",
        },
        {
            "from": EULER_PROTOCOL,
            "to": EULER_ATTACKER_CONTRACT,
            "token": "eDAI",
            "amount": "195,690,000",
            "label": "Mint eTokens (Step 4)",
        },
        {
            "from": EULER_ATTACKER_CONTRACT,
            "to": EULER_PROTOCOL,
            "token": "eDAI",
            "amount": "195,690,000",
            "label": "Donate to Reserves (Step 6) — THE BUG",
        },
        {
            "from": EULER_PROTOCOL,
            "to": EULER_ATTACKER_CONTRACT,
            "token": "DAI",
            "amount": "38,904,507",
            "label": "Self-Liquidation Profit (Step 7-8)",
        },
        {
            "from": EULER_ATTACKER_CONTRACT,
            "to": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
            "token": "DAI",
            "amount": "30,027,000",
            "label": "Repay Flash Loan + Fee (Step 9)",
        },
        {
            "from": EULER_ATTACKER_EOA,
            "to": "0xD90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
            "token": "ETH",
            "amount": "100",
            "label": "Tornado Cash (partial laundering)",
        },
        {
            "from": EULER_ATTACKER_EOA,
            "to": EULER_RETURN_ADDRESS,
            "token": "DAI+ETH",
            "amount": "~$197,000,000",
            "label": "Funds returned after negotiation (March 25-April 4)",
        },
    ],
    "stolen_tokens": EULER_STOLEN_TOKENS,
    "total_stolen_usd": EULER_AMOUNT_USD,
    "fund_recovery": {
        "returned": True,
        "return_date": "2023-04-04",
        "percent_returned": 98.0,
        "notes": (
            "After on-chain messages and negotiation, the attacker returned "
            "approximately $197M between March 25 and April 4, 2023. "
            "The attacker initially sent 100 ETH through Tornado Cash but "
            "ultimately cooperated and returned nearly all stolen funds."
        ),
    },
    "patterns_detected": [
        {
            "type": "FLASH_LOAN",
            "token": "DAI",
            "amount": "30,000,000",
            "provider": "Aave V2",
            "confidence": 0.98,
        },
        {
            "type": "DONATION_ATTACK",
            "detail": "donateToReserves() used to create artificial insolvency",
            "confidence": 0.99,
        },
        {
            "type": "SELF_LIQUIDATION",
            "detail": "Attacker liquidated own sub-account for profit",
            "confidence": 0.97,
        },
    ],
    "risk_indicators": [
        {
            "type": "MIXER_USAGE",
            "destination": "Tornado Cash",
            "severity": "HIGH",
            "detail": "100 ETH sent to Tornado Cash Router before returning funds",
        },
    ],
}
