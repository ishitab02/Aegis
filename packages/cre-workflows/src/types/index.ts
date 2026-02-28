import { z } from "zod";

// ============ Config Schema ============

const evmConfigSchema = z.object({
  chainSelectorName: z.string().min(1),
  circuitBreakerAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/u),
  threatReportAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/u),
  sentinelRegistryAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/u),
  mockProtocolAddress: z.string().regex(/^0x[a-fA-F0-9]{40}$/u),
  gasLimit: z.string().regex(/^\d+$/),
  chainlinkFeeds: z.object({
    ethUsd: z.string().regex(/^0x[a-fA-F0-9]{40}$/u),
  }),
});

export const configSchema = z.object({
  schedule: z.string(),
  agentApiUrl: z.string().url(),
  evms: z.array(evmConfigSchema).min(1),
});

export type Config = z.infer<typeof configSchema>;

// ============ Agent API Response Types ============

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

export type DetectionResponse = {
  consensus: ConsensusResult;
  assessments: ThreatAssessment[];
  timestamp: number;
};

export type HealthResponse = {
  status: "HEALTHY" | "DEGRADED" | "UNHEALTHY";
  sentinels: { active: number; total: number };
  last_check: number;
};

// ============ Threat Level Mapping (Solidity enum uint8) ============

export const THREAT_LEVEL_UINT8: Record<ThreatLevel, number> = {
  NONE: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
};
