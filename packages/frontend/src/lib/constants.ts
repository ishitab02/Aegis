import type { ThreatLevel } from "../types";

export const THREAT_COLORS: Record<ThreatLevel, string> = {
  NONE: "#10b981",
  LOW: "#6ee7b7",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export const THREAT_BG: Record<ThreatLevel, string> = {
  NONE: "bg-emerald-500/10 border-emerald-500/30",
  LOW: "bg-emerald-400/10 border-emerald-400/30",
  MEDIUM: "bg-amber-500/10 border-amber-500/30",
  HIGH: "bg-orange-500/10 border-orange-500/30",
  CRITICAL: "bg-red-500/10 border-red-500/30",
};

export const THREAT_TEXT: Record<ThreatLevel, string> = {
  NONE: "text-emerald-400",
  LOW: "text-emerald-300",
  MEDIUM: "text-amber-400",
  HIGH: "text-orange-400",
  CRITICAL: "text-red-400",
};

export const SENTINEL_LABELS: Record<string, string> = {
  LIQUIDITY: "Liquidity Sentinel",
  ORACLE: "Oracle Sentinel",
  GOVERNANCE: "Governance Sentinel",
};

export const SENTINEL_ICONS: Record<string, string> = {
  LIQUIDITY: "droplets",
  ORACLE: "eye",
  GOVERNANCE: "shield",
};
