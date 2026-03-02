"""Demo endpoints for video recording and presentations.

Provides endpoints that simulate real-world exploit scenarios step-by-step,
designed for recording demo videos and live presentations.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from aegis.models import (
    ActionRecommendation,
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
from aegis.utils import now_seconds

# Import the forensics report store to add demo reports
from aegis.api.routes.forensics import _reports as forensics_reports

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ Data Models ============


class SentinelAssessment(BaseModel):
    """Simplified assessment model for demos."""

    sentinel_id: int
    sentinel_type: str
    threat_level: ThreatLevel
    confidence: float = Field(ge=0.0, le=1.0)
    details: str
    indicators: list[str] = Field(default_factory=list)
    recommended_action: ActionRecommendation


class ConsensusResult(BaseModel):
    """Simplified consensus result model for demos."""

    consensus_reached: bool
    final_threat_level: ThreatLevel
    agreement_ratio: float
    participating_sentinels: int
    vote_breakdown: dict[str, int] = Field(default_factory=dict)
    recommended_action: ActionRecommendation
    report_id: str
    timestamp: int


class DemoStep(BaseModel):
    """A single step in the demo scenario."""

    step_number: int
    timestamp_offset_seconds: float
    title: str
    description: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    sentinel_assessments: list[SentinelAssessment] = Field(default_factory=list)
    consensus: ConsensusResult | None = None
    action_taken: str = ""
    is_critical: bool = False


class DemoScenario(BaseModel):
    """Complete demo scenario with all steps."""

    scenario_id: str
    scenario_name: str
    description: str
    protocol_name: str
    protocol_address: str
    attack_type: AttackType
    total_steps: int
    estimated_duration_seconds: int
    steps: list[DemoStep] = Field(default_factory=list)
    created_at: int
    status: str = "ready"  # ready, running, completed


class DemoRunResponse(BaseModel):
    """Response from running a demo scenario."""

    scenario_id: str
    current_step: int
    total_steps: int
    step_data: DemoStep
    is_final_step: bool
    next_step_available: bool


# ============ Demo State ============

# Store active demo runs
_active_demos: dict[str, dict] = {}


# ============ Demo Forensic Reports ============


def create_euler_forensic_report() -> ForensicReport:
    """Create a sample forensic report for the Euler exploit."""
    return ForensicReport(
        report_id="AEGIS-2023-EULER-001",
        tx_hash="0x71a26e7f09f6e7d0c18fdcde31e3a31cd9b9b5c5c5a5a5a5a5a5a5a5a5a5a5a5",
        protocol="Euler Finance",
        attack_classification=AttackClassification(
            primary_type=AttackType.FLASH_LOAN,
            confidence=0.95,
            description="Donation-based inflate-and-liquidate attack using flash loans",
        ),
        attack_flow=[
            AttackStep(step=1, action="Flash loan 30M DAI from Aave", contract="0xAavePool"),
            AttackStep(step=2, action="Deposit to Euler, mint eTokens", contract="0xEulerPool"),
            AttackStep(step=3, action="Donate to eToken pool to inflate exchange rate", contract="0xEulerPool"),
            AttackStep(step=4, action="Self-liquidate position at inflated rate", contract="0xEulerPool"),
            AttackStep(step=5, action="Extract profit via withdrawal", contract="0xEulerPool"),
            AttackStep(step=6, action="Repay flash loan", contract="0xAavePool"),
        ],
        root_cause=RootCause(
            vulnerability="Exchange rate manipulation via direct donations to eToken reserves",
            affected_code="eToken.donateToReserves() allows inflating exchange rate without checks",
            recommendation="Add donation limits and exchange rate deviation circuit breakers",
        ),
        impact_assessment=ImpactAssessment(
            funds_at_risk="$197,000,000 USD",
            affected_users="~11,000 depositors",
            severity=ThreatLevel.CRITICAL,
        ),
        fund_tracking=FundTracking(
            destinations=[
                FundDestination(
                    address="0x9799b475dEc92Bd99bbdD943013325C36157f383",
                    amount="$20,000,000",
                    type=FundDestinationType.MIXER,
                ),
                FundDestination(
                    address="0x1234567890123456789012345678901234567890",
                    amount="$17,500,000",
                    type=FundDestinationType.BRIDGE,
                ),
                FundDestination(
                    address="0xBinanceDeposit",
                    amount="$12,500,000",
                    type=FundDestinationType.CEX,
                ),
            ],
            recovery_possibility=RecoveryPossibility.LOW,
        ),
        timestamp=now_seconds(),
    )


# ============ Predefined Scenarios ============


def create_euler_scenario() -> DemoScenario:
    """Create the Euler Finance exploit replay scenario.

    Based on the March 2023 Euler Finance hack ($197M).
    Simulates the attack flow with realistic timing and metrics.
    """
    protocol_address = "0x27182842E098f60e3D576794A5bFFb0777E025d3"  # Euler Pool

    # Step 1: Normal state
    step_1 = DemoStep(
        step_number=1,
        timestamp_offset_seconds=0,
        title="Normal Operation",
        description="Euler Finance operating normally. TVL: $200M, all sentinels green.",
        metrics={
            "tvl_usd": 200_000_000,
            "tvl_eth": 80_000,
            "utilization_rate": 0.65,
            "eth_price_usd": 2500.00,
            "active_borrows_usd": 130_000_000,
        },
        sentinel_assessments=[
            SentinelAssessment(
                sentinel_id=1,
                sentinel_type="LIQUIDITY",
                threat_level=ThreatLevel.NONE,
                confidence=0.95,
                details="TVL stable at $200M. No anomalies detected.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
            SentinelAssessment(
                sentinel_id=2,
                sentinel_type="ORACLE",
                threat_level=ThreatLevel.NONE,
                confidence=0.98,
                details="All price feeds current. ETH/USD: $2,500.00",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
            SentinelAssessment(
                sentinel_id=3,
                sentinel_type="GOVERNANCE",
                threat_level=ThreatLevel.NONE,
                confidence=0.90,
                details="No pending proposals. Governance stable.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
        ],
        consensus=ConsensusResult(
            consensus_reached=True,
            final_threat_level=ThreatLevel.NONE,
            agreement_ratio=1.0,
            participating_sentinels=3,
            vote_breakdown={"NONE": 3},
            recommended_action=ActionRecommendation.NONE,
            report_id="demo-euler-001",
            timestamp=now_seconds(),
        ),
        action_taken="Monitoring continues normally",
        is_critical=False,
    )

    # Step 2: Flash loan detected
    step_2 = DemoStep(
        step_number=2,
        timestamp_offset_seconds=30,
        title="Flash Loan Initiated",
        description="ALERT: Large flash loan detected from Aave. Amount: 30M DAI",
        metrics={
            "tvl_usd": 200_000_000,
            "flash_loan_amount_usd": 30_000_000,
            "flash_loan_source": "Aave V3",
            "eth_price_usd": 2500.00,
            "tx_hash": "0x71a26...pending",
        },
        sentinel_assessments=[
            SentinelAssessment(
                sentinel_id=1,
                sentinel_type="LIQUIDITY",
                threat_level=ThreatLevel.MEDIUM,
                confidence=0.75,
                details="Flash loan of $30M DAI detected. Monitoring for impact.",
                indicators=["Flash loan initiated", "Large capital movement"],
                recommended_action=ActionRecommendation.ALERT,
            ),
            SentinelAssessment(
                sentinel_id=2,
                sentinel_type="ORACLE",
                threat_level=ThreatLevel.NONE,
                confidence=0.95,
                details="Price feeds stable. Monitoring for manipulation.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
            SentinelAssessment(
                sentinel_id=3,
                sentinel_type="GOVERNANCE",
                threat_level=ThreatLevel.NONE,
                confidence=0.90,
                details="No governance anomalies.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
        ],
        consensus=ConsensusResult(
            consensus_reached=False,
            final_threat_level=ThreatLevel.MEDIUM,
            agreement_ratio=0.33,
            participating_sentinels=3,
            vote_breakdown={"NONE": 2, "MEDIUM": 1},
            recommended_action=ActionRecommendation.ALERT,
            report_id="demo-euler-002",
            timestamp=now_seconds() + 30,
        ),
        action_taken="Alert sent to monitoring dashboard",
        is_critical=False,
    )

    # Step 3: Donation attack begins
    step_3 = DemoStep(
        step_number=3,
        timestamp_offset_seconds=45,
        title="Donation Attack Detected",
        description="CRITICAL: Unusual donation to eToken detected. Potential exploit pattern.",
        metrics={
            "tvl_usd": 200_000_000,
            "donation_amount_usd": 15_000_000,
            "affected_token": "eDAI",
            "donation_pattern": "Inflate-and-Liquidate",
            "eth_price_usd": 2500.00,
        },
        sentinel_assessments=[
            SentinelAssessment(
                sentinel_id=1,
                sentinel_type="LIQUIDITY",
                threat_level=ThreatLevel.HIGH,
                confidence=0.85,
                details="Abnormal donation pattern detected. $15M donation to eToken without borrow.",
                indicators=[
                    "Large donation without borrow",
                    "Potential inflation attack",
                    "Self-liquidation pattern",
                ],
                recommended_action=ActionRecommendation.ALERT,
            ),
            SentinelAssessment(
                sentinel_id=2,
                sentinel_type="ORACLE",
                threat_level=ThreatLevel.MEDIUM,
                confidence=0.80,
                details="Exchange rate manipulation detected. eToken value inflated.",
                indicators=["Exchange rate spike", "Unusual token valuation"],
                recommended_action=ActionRecommendation.ALERT,
            ),
            SentinelAssessment(
                sentinel_id=3,
                sentinel_type="GOVERNANCE",
                threat_level=ThreatLevel.NONE,
                confidence=0.85,
                details="No governance involvement detected.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
        ],
        consensus=ConsensusResult(
            consensus_reached=True,
            final_threat_level=ThreatLevel.HIGH,
            agreement_ratio=0.67,
            participating_sentinels=3,
            vote_breakdown={"HIGH": 1, "MEDIUM": 1, "NONE": 1},
            recommended_action=ActionRecommendation.ALERT,
            report_id="demo-euler-003",
            timestamp=now_seconds() + 45,
        ),
        action_taken="HIGH alert triggered. Team notified.",
        is_critical=False,
    )

    # Step 4: TVL drop begins
    step_4 = DemoStep(
        step_number=4,
        timestamp_offset_seconds=60,
        title="TVL Drop Detected",
        description="CRITICAL: TVL dropping rapidly! 15% decrease in 30 seconds.",
        metrics={
            "tvl_usd": 170_000_000,
            "tvl_drop_percent": 15.0,
            "tvl_drop_timeframe_seconds": 30,
            "withdrawal_rate_usd_per_second": 1_000_000,
            "eth_price_usd": 2500.00,
        },
        sentinel_assessments=[
            SentinelAssessment(
                sentinel_id=1,
                sentinel_type="LIQUIDITY",
                threat_level=ThreatLevel.CRITICAL,
                confidence=0.92,
                details="CRITICAL: TVL dropped 15% in 30 seconds. Active exploit detected!",
                indicators=[
                    "15% TVL drop",
                    "Rapid withdrawal pattern",
                    "Self-liquidation execution",
                    "Profit extraction underway",
                ],
                recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            ),
            SentinelAssessment(
                sentinel_id=2,
                sentinel_type="ORACLE",
                threat_level=ThreatLevel.HIGH,
                confidence=0.88,
                details="Severe price deviation detected. Oracle manipulation confirmed.",
                indicators=["8% price deviation from Chainlink", "Manipulated exchange rate"],
                recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            ),
            SentinelAssessment(
                sentinel_id=3,
                sentinel_type="GOVERNANCE",
                threat_level=ThreatLevel.NONE,
                confidence=0.80,
                details="No governance attack vector identified.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
        ],
        consensus=ConsensusResult(
            consensus_reached=True,
            final_threat_level=ThreatLevel.CRITICAL,
            agreement_ratio=0.67,
            participating_sentinels=3,
            vote_breakdown={"CRITICAL": 1, "HIGH": 1, "NONE": 1},
            recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            report_id="demo-euler-004",
            timestamp=now_seconds() + 60,
        ),
        action_taken="CIRCUIT BREAKER ACTIVATED",
        is_critical=True,
    )

    # Step 5: Circuit breaker triggered
    step_5 = DemoStep(
        step_number=5,
        timestamp_offset_seconds=65,
        title="Circuit Breaker Activated",
        description="Protocol paused by AEGIS. Further exploitation prevented.",
        metrics={
            "tvl_usd": 150_000_000,
            "tvl_protected_usd": 150_000_000,
            "tvl_lost_usd": 50_000_000,
            "circuit_breaker_latency_ms": 5200,
            "protocol_status": "PAUSED",
        },
        sentinel_assessments=[
            SentinelAssessment(
                sentinel_id=1,
                sentinel_type="LIQUIDITY",
                threat_level=ThreatLevel.CRITICAL,
                confidence=0.98,
                details="Circuit breaker activated. Protocol paused. $150M protected.",
                indicators=["Protocol paused", "Withdrawals halted", "Deposits blocked"],
                recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            ),
            SentinelAssessment(
                sentinel_id=2,
                sentinel_type="ORACLE",
                threat_level=ThreatLevel.CRITICAL,
                confidence=0.95,
                details="All oracle feeds frozen. Manipulation contained.",
                indicators=["Feeds frozen", "Manipulation stopped"],
                recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            ),
            SentinelAssessment(
                sentinel_id=3,
                sentinel_type="GOVERNANCE",
                threat_level=ThreatLevel.NONE,
                confidence=0.85,
                details="Governance unchanged. Emergency response active.",
                indicators=[],
                recommended_action=ActionRecommendation.NONE,
            ),
        ],
        consensus=ConsensusResult(
            consensus_reached=True,
            final_threat_level=ThreatLevel.CRITICAL,
            agreement_ratio=0.67,
            participating_sentinels=3,
            vote_breakdown={"CRITICAL": 2, "NONE": 1},
            recommended_action=ActionRecommendation.CIRCUIT_BREAKER,
            report_id="demo-euler-005",
            timestamp=now_seconds() + 65,
        ),
        action_taken="Protocol paused. ChainSherlock forensics initiated.",
        is_critical=True,
    )

    # Step 6: Forensics begins
    step_6 = DemoStep(
        step_number=6,
        timestamp_offset_seconds=70,
        title="ChainSherlock Forensics Started",
        description="AI forensics engine analyzing attack transaction graph.",
        metrics={
            "transactions_analyzed": 15,
            "addresses_identified": 8,
            "known_addresses_found": 3,
            "attack_pattern": "Donation-Based Inflate & Liquidate",
            "analysis_progress_percent": 35,
        },
        sentinel_assessments=[],
        consensus=None,
        action_taken="Forensic analysis in progress...",
        is_critical=False,
    )

    # Step 7: Attacker identified
    step_7 = DemoStep(
        step_number=7,
        timestamp_offset_seconds=90,
        title="Attacker Address Identified",
        description="ChainSherlock identified attacker EOA and traced fund movements.",
        metrics={
            "attacker_address": "0x9799b475dEc92Bd99bbdD943013325C36157f383",
            "attacker_label": "Euler Exploiter",
            "funds_traced_usd": 50_000_000,
            "destination_1": "Tornado Cash (40%)",
            "destination_2": "Cross-chain bridge (35%)",
            "destination_3": "CEX deposit (25%)",
            "analysis_progress_percent": 100,
        },
        sentinel_assessments=[],
        consensus=None,
        action_taken="Forensic report generated. Fund tracking active.",
        is_critical=False,
    )

    # Step 8: Report generated
    step_8 = DemoStep(
        step_number=8,
        timestamp_offset_seconds=120,
        title="Forensic Report Complete",
        description="Full forensic report ready. Attack classification: Donation-Based Exploit",
        metrics={
            "report_id": "AEGIS-2023-EULER-001",
            "attack_type": "DONATION_EXPLOIT",
            "attack_classification": "Inflate-and-Liquidate via eToken donation",
            "severity": "CRITICAL",
            "total_loss_usd": 50_000_000,
            "total_protected_usd": 150_000_000,
            "detection_time_seconds": 60,
            "mitigation_time_seconds": 65,
            "recommendations": [
                "Add donation amount limits",
                "Implement exchange rate circuit breakers",
                "Add self-liquidation cooldown",
            ],
        },
        sentinel_assessments=[],
        consensus=None,
        action_taken="Report published. CCIP alert sent to all chains.",
        is_critical=False,
    )

    # Step 9: Summary
    step_9 = DemoStep(
        step_number=9,
        timestamp_offset_seconds=150,
        title="Incident Summary",
        description="AEGIS prevented $150M in additional losses. Total incident response: 2.5 minutes.",
        metrics={
            "incident_duration_seconds": 150,
            "detection_latency_seconds": 60,
            "mitigation_latency_seconds": 5,
            "total_loss_usd": 50_000_000,
            "total_protected_usd": 150_000_000,
            "loss_prevention_percent": 75.0,
            "sentinels_activated": 3,
            "consensus_votes": "2/3 CRITICAL",
            "chainlink_services_used": ["Data Feeds", "Automation", "CCIP"],
        },
        sentinel_assessments=[],
        consensus=None,
        action_taken="Incident closed. Post-mortem available.",
        is_critical=False,
    )

    return DemoScenario(
        scenario_id="euler-replay-2023",
        scenario_name="Euler Finance Exploit Replay",
        description=(
            "Replay of the March 2023 Euler Finance exploit ($197M). "
            "Demonstrates how AEGIS would have detected and mitigated the attack "
            "within 65 seconds, potentially saving $150M."
        ),
        protocol_name="Euler Finance",
        protocol_address=protocol_address,
        attack_type=AttackType.FLASH_LOAN,
        total_steps=9,
        estimated_duration_seconds=150,
        steps=[step_1, step_2, step_3, step_4, step_5, step_6, step_7, step_8, step_9],
        created_at=now_seconds(),
        status="ready",
    )


# ============ Endpoints ============


@router.get("/scenarios", response_model=list[dict])
async def list_scenarios():
    """List all available demo scenarios."""
    return [
        {
            "scenario_id": "euler-replay-2023",
            "name": "Euler Finance Exploit Replay",
            "attack_type": "FLASH_LOAN",
            "duration_seconds": 150,
            "steps": 9,
            "description": "Replay of the March 2023 Euler Finance hack ($197M)",
        },
    ]


@router.post("/euler-replay", response_model=DemoScenario)
async def start_euler_replay():
    """Initialize the Euler Finance exploit replay demo.

    Returns the full scenario with all steps. Use /euler-replay/{step} to
    get individual steps for animation/timing purposes.
    Also creates a sample forensic report for the Forensics page.
    """
    scenario = create_euler_scenario()
    _active_demos[scenario.scenario_id] = {
        "scenario": scenario,
        "started_at": now_seconds(),
        "current_step": 0,
    }

    # Create sample forensic report for the demo
    forensic_report = create_euler_forensic_report()
    forensics_reports[forensic_report.report_id] = forensic_report
    logger.info("Created demo forensic report: %s", forensic_report.report_id)

    logger.info("Started Euler replay demo: %s", scenario.scenario_id)
    return scenario


@router.get("/euler-replay/step/{step_number}", response_model=DemoRunResponse)
async def get_euler_replay_step(step_number: int):
    """Get a specific step from the Euler replay demo.

    Args:
        step_number: Step number (1-9)

    Returns:
        The step data with context about position in the scenario
    """
    scenario = create_euler_scenario()

    if step_number < 1 or step_number > scenario.total_steps:
        step_number = max(1, min(step_number, scenario.total_steps))

    step_data = scenario.steps[step_number - 1]

    return DemoRunResponse(
        scenario_id=scenario.scenario_id,
        current_step=step_number,
        total_steps=scenario.total_steps,
        step_data=step_data,
        is_final_step=(step_number == scenario.total_steps),
        next_step_available=(step_number < scenario.total_steps),
    )


@router.post("/euler-replay/reset")
async def reset_euler_replay():
    """Reset the Euler replay demo state."""
    if "euler-replay-2023" in _active_demos:
        del _active_demos["euler-replay-2023"]
    return {"status": "reset", "message": "Euler replay demo reset"}


@router.get("/active", response_model=list[str])
async def list_active_demos():
    """List all currently active demo runs."""
    return list(_active_demos.keys())
