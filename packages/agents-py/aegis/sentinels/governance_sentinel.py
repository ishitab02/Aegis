"""Governance Sentinel - analyzes proposals for malicious intent.

Ported from packages/agents/src/sentinels/GovernanceSentinel/actions/analyzeProposal.ts
"""

import logging

from crewai import Agent
from web3 import Web3

from aegis.models import (
    ActionRecommendation,
    GovernanceProposal,
    SentinelType,
    ThreatAssessment,
    ThreatLevel,
)
from aegis.utils import now_seconds

logger = logging.getLogger(__name__)

# Known suspicious function signatures in governance proposals
SUSPICIOUS_SIGNATURES = [
    "transferOwnership(address)",
    "upgradeTo(address)",
    "upgradeToAndCall(address,bytes)",
    "setAdmin(address)",
    "grantRole(bytes32,address)",
    "pause()",
]

# Pre-compute 4-byte selectors
SUSPICIOUS_SELECTORS = [
    Web3.keccak(text=sig)[:4].hex() for sig in SUSPICIOUS_SIGNATURES
]


def analyze_proposal(proposal: GovernanceProposal) -> ThreatAssessment:
    """Analyze a governance proposal for malicious intent.

    Checks for:
    - Suspicious function calls (transferOwnership, upgradeTo, etc.)
    - Unusually short voting periods (< 100 blocks)
    """
    indicators: list[str] = []
    threat_level = ThreatLevel.NONE
    confidence = 0.7

    # Check for suspicious function calls
    for calldata in proposal.calldatas:
        for i, selector in enumerate(SUSPICIOUS_SELECTORS):
            if calldata.startswith(selector) or selector in calldata[:10]:
                indicators.append(
                    f"Proposal contains suspicious call: {SUSPICIOUS_SIGNATURES[i]}"
                )
                threat_level = ThreatLevel.HIGH
                confidence = 0.85

    # Check if voting period is unusually short
    voting_period = proposal.end_block - proposal.start_block
    if voting_period < 100 and voting_period > 0:
        indicators.append(f"Unusually short voting period: {voting_period} blocks")
        if ThreatLevel.severity(threat_level) < ThreatLevel.severity(ThreatLevel.HIGH):
            threat_level = ThreatLevel.HIGH
        confidence = max(confidence, 0.8)

    recommendation = ActionRecommendation.NONE
    if threat_level == ThreatLevel.CRITICAL:
        recommendation = ActionRecommendation.CIRCUIT_BREAKER
    elif ThreatLevel.severity(threat_level) >= ThreatLevel.severity(ThreatLevel.MEDIUM):
        recommendation = ActionRecommendation.ALERT

    return ThreatAssessment(
        threat_level=threat_level,
        confidence=confidence,
        details=(
            f"Governance proposal {proposal.id} analysis: "
            f"{len(indicators)} indicators found"
        ),
        indicators=indicators,
        recommendation=recommendation,
        timestamp=now_seconds(),
        sentinel_id="governance-sentinel-0",
        sentinel_type=SentinelType.GOVERNANCE,
    )


# ============ CrewAI Agent ============

_governance_sentinel: Agent | None = None


def get_governance_sentinel() -> Agent:
    """Lazy-load the CrewAI agent (requires LLM API key at runtime)."""
    global _governance_sentinel
    if _governance_sentinel is None:
        _governance_sentinel = Agent(
            role="Governance Sentinel",
            goal=(
                "Monitor DeFi protocol governance proposals for malicious actions such as "
                "ownership transfers, unauthorized upgrades, or timelock bypasses."
            ),
            backstory=(
                "You are the AEGIS Governance Sentinel, an AI agent specialized in "
                "detecting malicious governance proposals. You analyze proposal calldata "
                "for suspicious function signatures, check for flash-loan-powered voting, "
                "and flag unusually short voting periods."
            ),
            verbose=False,
            allow_delegation=False,
        )
    return _governance_sentinel
