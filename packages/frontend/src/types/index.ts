export type ThreatLevel = "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AlertAction =
  | "NONE"
  | "ALERT"
  | "INVESTIGATE"
  | "CIRCUIT_BREAKER"
  | "PAUSE"
  | "UNPAUSE"
  | string;

export interface HealthResponse {
  status: "HEALTHY" | "DEGRADED" | "UNHEALTHY" | string;
  services?: {
    agentApi?: { status?: string };
    onChain?: { activeSentinels?: number };
  };
  timestamp?: number;
}

export interface AlertRecord {
  id: string;
  protocol: string;
  protocolName: string;
  threatLevel: ThreatLevel;
  action: AlertAction;
  confidence: number | null;
  consensusPercent: number | null;
  createdAt: number;
  consensusData: Record<string, unknown> | null;
}

export interface AlertsPage {
  items: AlertRecord[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface ProtocolRecord {
  address: string;
  name: string;
  alertThreshold: number;
  breakerThreshold: number;
  active: boolean;
  registeredAt: number;
}

export interface ProtocolsResponse {
  protocols: ProtocolRecord[];
}

export interface CircuitBreakerState {
  paused: boolean;
  threatLevel: number;
  threatId?: string;
  pausedAt: number;
  cooldownEnds: number;
  reason: string;
}

export interface ProtocolStatusResponse {
  address: string;
  registered: boolean;
  protocol: ProtocolRecord | null;
  circuitBreaker: CircuitBreakerState | null;
  timestamp: number;
}

export interface SentinelAssessment {
  sentinel_id?: string;
  threat_level?: string;
  confidence?: number;
  details?: string;
  protocol?: string;
  protocol_name?: string;
  action?: string;
  timestamp?: number | string;
}

export interface SentinelAggregateResponse {
  assessments?: SentinelAssessment[];
  consensus?: {
    final_threat_level?: string;
    action_recommended?: string;
    agreement_ratio?: number;
  };
  protocol?: string;
  protocol_name?: string;
  timestamp?: number | string;
}

export interface ForensicsListItem {
  id: string;
  protocol?: string;
  tx_hash?: string;
  created_at?: number;
  report?: unknown;
}

export interface ForensicsSummary {
  reportId: string;
  protocol: string;
  address: string;
  severity: ThreatLevel;
  attackType: string;
  estimatedLoss: string;
  summaryText: string;
  timestamp: number;
  flow: Array<{ id: string; label: string; address?: string; action?: string }>;
  destinations: Array<{
    address: string;
    amount: string;
    status: "TRACED" | "UNTRACED";
    chain?: string;
  }>;
  technicalDetails: {
    vulnerability: string;
    affectedFunctions: string[];
    codeSnippet: string;
  };
  recommendations: Array<{
    text: string;
    priority: "HIGH" | "MEDIUM" | "LOW";
  }>;
}

export type ActionRecommendation = "NONE" | "ALERT" | "INVESTIGATE" | "CIRCUIT_BREAKER";

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
