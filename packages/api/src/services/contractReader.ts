/**
 * On-chain reads using ethers.js v6.
 */

import { ethers } from "ethers";
import { config } from "../config.js";

let _provider: ethers.JsonRpcProvider | null = null;

function getProvider(): ethers.JsonRpcProvider {
  if (!_provider) {
    _provider = new ethers.JsonRpcProvider(config.rpcUrl);
  }
  return _provider;
}

// ============ CircuitBreaker ============

const CIRCUIT_BREAKER_ABI = [
  "function isPaused(address protocol) view returns (bool)",
  "function getBreakerState(address protocol) view returns (tuple(bool paused, uint8 threatLevel, bytes32 threatId, uint256 pausedAt, uint256 cooldownEnds, string reason))",
];

export async function getCircuitBreakerState(protocol: string) {
  if (!config.circuitBreakerAddress) return null;
  const contract = new ethers.Contract(
    config.circuitBreakerAddress,
    CIRCUIT_BREAKER_ABI,
    getProvider()
  );
  try {
    const state = await contract.getBreakerState(protocol);
    return {
      paused: state.paused,
      threatLevel: Number(state.threatLevel),
      threatId: state.threatId,
      pausedAt: Number(state.pausedAt),
      cooldownEnds: Number(state.cooldownEnds),
      reason: state.reason,
    };
  } catch {
    return null;
  }
}

export async function isProtocolPaused(protocol: string): Promise<boolean> {
  if (!config.circuitBreakerAddress) return false;
  const contract = new ethers.Contract(
    config.circuitBreakerAddress,
    CIRCUIT_BREAKER_ABI,
    getProvider()
  );
  try {
    return await contract.isPaused(protocol);
  } catch {
    return false;
  }
}

// ============ ThreatReport ============

const THREAT_REPORT_ABI = [
  "function getProtocolReports(address protocol, uint256 limit) view returns (bytes32[])",
];

export async function getProtocolReports(protocol: string, limit = 10) {
  if (!config.threatReportAddress) return [];
  const contract = new ethers.Contract(
    config.threatReportAddress,
    THREAT_REPORT_ABI,
    getProvider()
  );
  try {
    return await contract.getProtocolReports(protocol, limit);
  } catch {
    return [];
  }
}

// ============ SentinelRegistry ============

const SENTINEL_REGISTRY_ABI = [
  "function getActiveSentinels() view returns (uint256[])",
  "function isAlive(uint256 tokenId, uint256 maxInactivity) view returns (bool)",
];

export async function getActiveSentinels() {
  if (!config.sentinelRegistryAddress) return [];
  const contract = new ethers.Contract(
    config.sentinelRegistryAddress,
    SENTINEL_REGISTRY_ABI,
    getProvider()
  );
  try {
    const ids = await contract.getActiveSentinels();
    return ids.map((id: bigint) => Number(id));
  } catch {
    return [];
  }
}

// ============ MockProtocol ============

const MOCK_PROTOCOL_ABI = [
  "function getTVL() view returns (uint256)",
  "function paused() view returns (bool)",
];

export async function getProtocolTVL(protocol: string) {
  const contract = new ethers.Contract(
    protocol,
    MOCK_PROTOCOL_ABI,
    getProvider()
  );
  try {
    const tvl = await contract.getTVL();
    return tvl.toString();
  } catch {
    return "0";
  }
}
