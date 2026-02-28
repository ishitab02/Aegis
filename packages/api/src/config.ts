import "dotenv/config";

export const config = {
  port: parseInt(process.env.API_PORT ?? "3000", 10),
  agentApiUrl: process.env.AGENT_API_URL ?? "http://localhost:8000",

  // Contract addresses (from deployment)
  circuitBreakerAddress: process.env.CIRCUIT_BREAKER_ADDRESS ?? "",
  threatReportAddress: process.env.THREAT_REPORT_ADDRESS ?? "",
  sentinelRegistryAddress: process.env.SENTINEL_REGISTRY_ADDRESS ?? "",
  reputationTrackerAddress: process.env.REPUTATION_TRACKER_ADDRESS ?? "",
  protocolToMonitor: process.env.PROTOCOL_TO_MONITOR ?? "",

  // RPC
  rpcUrl: process.env.BASE_SEPOLIA_RPC ?? "https://sepolia.base.org",

  // x402
  x402FacilitatorUrl:
    process.env.X402_FACILITATOR_URL ?? "https://x402.org/facilitator",
  payeeAddress: process.env.PAYEE_ADDRESS ?? "",
} as const;
