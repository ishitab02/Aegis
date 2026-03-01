"""Pydantic models for the AEGIS Protocol agent system.

Ported from packages/agents/src/shared/types.ts
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ============ Enums ============


class ThreatLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @staticmethod
    def severity(level: "ThreatLevel") -> int:
        """Return numeric severity for ordering comparisons."""
        return _THREAT_SEVERITY[level]


_THREAT_SEVERITY: dict["ThreatLevel", int] = {
    ThreatLevel.NONE: 0,
    ThreatLevel.LOW: 1,
    ThreatLevel.MEDIUM: 2,
    ThreatLevel.HIGH: 3,
    ThreatLevel.CRITICAL: 4,
}


class SentinelType(str, Enum):
    LIQUIDITY = "LIQUIDITY"
    ORACLE = "ORACLE"
    GOVERNANCE = "GOVERNANCE"
    SHERLOCK = "SHERLOCK"


class ActionRecommendation(str, Enum):
    NONE = "NONE"
    ALERT = "ALERT"
    INVESTIGATE = "INVESTIGATE"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"


class AttackType(str, Enum):
    REENTRANCY = "REENTRANCY"
    PRICE_MANIPULATION = "PRICE_MANIPULATION"
    FLASH_LOAN = "FLASH_LOAN"
    ORACLE_MANIPULATION = "ORACLE_MANIPULATION"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    LOGIC_ERROR = "LOGIC_ERROR"
    OTHER = "OTHER"


class RecoveryPossibility(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class FundDestinationType(str, Enum):
    CEX = "CEX"
    DEX = "DEX"
    MIXER = "MIXER"
    BRIDGE = "BRIDGE"
    UNKNOWN = "UNKNOWN"


# ============ Sentinel Types ============


class ThreatAssessment(BaseModel):
    threat_level: ThreatLevel
    confidence: float = Field(ge=0.0, le=1.0)
    details: str
    indicators: list[str] = Field(default_factory=list)
    recommendation: ActionRecommendation
    timestamp: int
    sentinel_id: str
    sentinel_type: SentinelType


class SentinelVote(BaseModel):
    sentinel_id: str
    threat_level: ThreatLevel
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: int
    signature: str = ""


class ConsensusResult(BaseModel):
    consensus_reached: bool
    final_threat_level: ThreatLevel
    agreement_ratio: float
    votes: list[SentinelVote]
    action_recommended: ActionRecommendation


# ============ Forensics Types ============


class InternalCall(BaseModel):
    from_address: str = Field(alias="from", serialization_alias="from")
    to: str
    value: str
    input: str
    output: str
    type: Literal["CALL", "DELEGATECALL", "STATICCALL", "CREATE", "CREATE2"]
    depth: int

    model_config = {"populate_by_name": True}


class TokenTransfer(BaseModel):
    token: str
    from_address: str = Field(alias="from", serialization_alias="from")
    to: str
    amount: str
    symbol: Optional[str] = None

    model_config = {"populate_by_name": True}


class TransactionTrace(BaseModel):
    tx_hash: str
    from_address: str = Field(alias="from", serialization_alias="from")
    to: str
    value: str
    gas_used: int
    internal_calls: list[InternalCall] = Field(default_factory=list)
    token_transfers: list[TokenTransfer] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class AttackStep(BaseModel):
    step: int
    action: str
    contract: str


class FundDestination(BaseModel):
    address: str
    amount: str
    type: FundDestinationType


class AttackClassification(BaseModel):
    primary_type: AttackType
    confidence: float = Field(ge=0.0, le=1.0)
    description: str


class RootCause(BaseModel):
    vulnerability: str
    affected_code: str
    recommendation: str


class ImpactAssessment(BaseModel):
    funds_at_risk: str
    affected_users: str
    severity: ThreatLevel


class FundTracking(BaseModel):
    destinations: list[FundDestination] = Field(default_factory=list)
    recovery_possibility: RecoveryPossibility


class ForensicReport(BaseModel):
    report_id: str
    tx_hash: str
    protocol: str
    attack_classification: AttackClassification
    attack_flow: list[AttackStep] = Field(default_factory=list)
    root_cause: RootCause
    impact_assessment: ImpactAssessment
    fund_tracking: FundTracking
    timestamp: int


# ============ Protocol Types ============


class ProtocolMetrics(BaseModel):
    address: str
    name: str
    tvl: int
    tvl_5min_ago: int
    tvl_change_percent: float
    large_withdrawals: int
    flash_loan_count: int


class PriceFeedData(BaseModel):
    price: float
    updated_at: int
    decimals: int
    feed_address: str


# ============ API Types ============


class SentinelStatus(BaseModel):
    active: int
    total: int


class HealthStatus(BaseModel):
    status: Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]
    sentinels: SentinelStatus
    last_check: int


class DetectionRequest(BaseModel):
    protocol_address: str
    protocol_name: str = "MockProtocol"


class DetectionResponse(BaseModel):
    consensus: ConsensusResult
    assessments: list[ThreatAssessment]
    timestamp: int


class ForensicsRequest(BaseModel):
    tx_hash: str
    protocol: str
    description: str = ""


class GovernanceProposal(BaseModel):
    id: str
    proposer: str
    description: str
    targets: list[str] = Field(default_factory=list)
    calldatas: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    for_votes: int = 0
    against_votes: int = 0
    start_block: int = 0
    end_block: int = 0
