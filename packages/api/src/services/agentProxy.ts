import { config } from "../config.js";

const AGENT_BASE = config.agentApiUrl;

async function agentFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = `${AGENT_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  return res;
}

export interface DetectionParams {
  protocol_address: string;
  protocol_name?: string;
  simulate_tvl_drop_percent?: number;
  simulate_price_deviation_percent?: number;
  simulate_short_voting_period?: boolean;
  live_mode?: boolean;
}

export async function runDetection(params: DetectionParams) {
  const res = await agentFetch("/api/v1/detect", {
    method: "POST",
    body: JSON.stringify(params),
  });
  return res.json();
}

export async function getSentinelAggregate() {
  const res = await agentFetch("/api/v1/sentinel/aggregate");
  return res.json();
}

export async function getSentinelById(id: string) {
  const res = await agentFetch(`/api/v1/sentinel/${id}`);
  if (!res.ok) return null;
  return res.json();
}

export async function runForensics(txHash: string, protocol: string, description = "") {
  const res = await agentFetch("/api/v1/forensics", {
    method: "POST",
    body: JSON.stringify({ tx_hash: txHash, protocol, description }),
  });
  return res.json();
}

export async function getForensicReport(id: string) {
  const res = await agentFetch(`/api/v1/forensics/${id}`);
  if (!res.ok) return null;
  return res.json();
}

export async function listForensicReports() {
  const res = await agentFetch("/api/v1/forensics");
  return res.json();
}

export async function getAgentHealth() {
  try {
    const res = await agentFetch("/api/v1/health");
    return res.json();
  } catch {
    return { status: "UNHEALTHY", error: "Agent API unreachable" };
  }
}

export async function getDemoScenarios() {
  const res = await agentFetch("/api/v1/demo/scenarios");
  return res.json();
}

export async function startEulerReplay() {
  const res = await agentFetch("/api/v1/demo/euler-replay", {
    method: "POST",
  });
  return res.json();
}

export async function getEulerReplayStep(stepNumber: number) {
  const res = await agentFetch(`/api/v1/demo/euler-replay/step/${stepNumber}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getLiveAaveMonitor() {
  const res = await agentFetch("/api/v1/monitor/aave");
  return res.json();
}

export async function getLiveProtocolMonitor(address: string) {
  const res = await agentFetch(`/api/v1/monitor/${address}`);
  return res.json();
}
