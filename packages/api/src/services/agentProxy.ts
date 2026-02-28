/**
 * HTTP proxy to the Python FastAPI agent service (port 8000).
 */

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

// ---- Detection ----

export async function runDetection(
  protocolAddress: string,
  protocolName = "MockProtocol"
) {
  const res = await agentFetch("/api/v1/detect", {
    method: "POST",
    body: JSON.stringify({
      protocol_address: protocolAddress,
      protocol_name: protocolName,
    }),
  });
  return res.json();
}

// ---- Sentinel ----

export async function getSentinelAggregate() {
  const res = await agentFetch("/api/v1/sentinel/aggregate");
  return res.json();
}

export async function getSentinelById(id: string) {
  const res = await agentFetch(`/api/v1/sentinel/${id}`);
  if (!res.ok) return null;
  return res.json();
}

// ---- Forensics ----

export async function runForensics(
  txHash: string,
  protocol: string,
  description = ""
) {
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

// ---- Health ----

export async function getAgentHealth() {
  try {
    const res = await agentFetch("/api/v1/health");
    return res.json();
  } catch {
    return { status: "UNHEALTHY", error: "Agent API unreachable" };
  }
}
