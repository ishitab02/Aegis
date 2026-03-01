import { parseAbi } from "viem";

export const circuitBreakerAbi = parseAbi([
  "function triggerBreaker(address protocol, bytes32 threatId, uint8 threatLevel, string reason) external",
  "function resetBreaker(address protocol) external",
  "function isPaused(address protocol) external view returns (bool)",
  "function recordAlert(address protocol, bytes32 threatId, uint8 threatLevel) external",
  "event CircuitBreakerTriggered(address indexed protocol, bytes32 indexed threatId, uint8 threatLevel, string reason)",
]);

export const threatReportAbi = parseAbi([
  "function submitReport(address protocol, uint8 threatLevel, bytes32 consensusHash, string ipfsHash, bool actionTaken, (uint256 sentinelId, uint8 threatLevel, uint256 confidence, bytes signature)[] votes) external returns (bytes32 reportId)",
  "function getProtocolReports(address protocol, uint256 limit) external view returns (bytes32[])",
]);

export const sentinelRegistryAbi = parseAbi([
  "function getActiveSentinels() external view returns (uint256[])",
  "function isAlive(uint256 tokenId, uint256 maxInactivity) external view returns (bool)",
  "function heartbeat(uint256 tokenId) external",
]);

export const mockProtocolAbi = parseAbi([
  "function getTVL() external view returns (uint256)",
  "function paused() external view returns (bool)",
]);

export const chainlinkAggregatorAbi = parseAbi([
  "function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)",
  "function decimals() external view returns (uint8)",
]);
