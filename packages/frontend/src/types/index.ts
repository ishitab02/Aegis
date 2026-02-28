export type ThreatLevel = "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ActionRecommendation =
  | "NONE"
  | "ALERT"
  | "INVESTIGATE"
  | "CIRCUIT_BREAKER";

export type SentinelVote = {
  sentinel_id: string;
  threat_level: ThreatLevel;
  confidence: number;
  timestamp: number;
};

export type ConsensusResult = {
  consensus_reached: boolean;
  final_threat_level: ThreatLevel;
  agreement_ratio: number;
  votes: SentinelVote[];
  action_recommended: ActionRecommendation;
};

export type ThreatAssessment = {
  threat_level: ThreatLevel;
  confidence: number;
  details: string;
  indicators: string[];
  recommendation: ActionRecommendation;
  timestamp: number;
  sentinel_id: string;
  sentinel_type: string;
};

export type AggregateResponse = {
  assessments: ThreatAssessment[];
  consensus: ConsensusResult;
  timestamp: number;
};

export type HealthResponse = {
  status: "HEALTHY" | "DEGRADED" | "UNHEALTHY";
  services: {
    agentApi: { status: string };
    onChain: { activeSentinels: number };
  };
  timestamp: number;
};

export type ProtocolStatus = {
  address: string;
  paused: boolean;
  tvl: string;
  circuitBreaker: {
    paused: boolean;
    threatLevel: number;
    reason: string;
    cooldownEnds: number;
  } | null;
  timestamp: number;
};
