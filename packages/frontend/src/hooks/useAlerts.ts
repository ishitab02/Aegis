import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { AlertRecord, AlertsPage, ThreatLevel } from "../types";

type RawAlert = Record<string, unknown>;

function normalizeThreat(level: unknown): ThreatLevel {
  if (typeof level !== "string") {
    return "NONE";
  }

  const upper = level.toUpperCase();
  if (upper === "LOW" || upper === "MEDIUM" || upper === "HIGH" || upper === "CRITICAL") {
    return upper;
  }

  return "NONE";
}

function toUnixSeconds(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1_000_000_000_000 ? Math.floor(value / 1000) : value;
  }

  if (typeof value === "string") {
    const numeric = Number(value);
    if (!Number.isNaN(numeric)) {
      return numeric > 1_000_000_000_000 ? Math.floor(numeric / 1000) : numeric;
    }

    const parsed = Date.parse(value);
    if (!Number.isNaN(parsed)) {
      return Math.floor(parsed / 1000);
    }
  }

  return Math.floor(Date.now() / 1000);
}

function normalizeConsensusPercent(raw: RawAlert): number | null {
  const direct = raw.consensus_percent ?? raw.consensus ?? raw.agreement_ratio ?? raw.confidence;
  if (typeof direct === "number" && Number.isFinite(direct)) {
    return direct <= 1 ? direct * 100 : direct;
  }

  const data = raw.consensus_data;
  if (!data) {
    return null;
  }

  if (typeof data === "string") {
    try {
      const parsed = JSON.parse(data) as Record<string, unknown>;
      const value = parsed.consensus_percent ?? parsed.agreement_ratio;
      if (typeof value === "number" && Number.isFinite(value)) {
        return value <= 1 ? value * 100 : value;
      }
    } catch {
      return null;
    }
  }

  if (typeof data === "object" && !Array.isArray(data)) {
    const nested = data as Record<string, unknown>;
    const value = nested.consensus_percent ?? nested.agreement_ratio;
    if (typeof value === "number" && Number.isFinite(value)) {
      return value <= 1 ? value * 100 : value;
    }
  }

  return null;
}

function normalizeConsensusData(raw: RawAlert): Record<string, unknown> | null {
  const { consensus_data: consensusData } = raw;

  if (!consensusData) {
    return null;
  }

  if (typeof consensusData === "string") {
    try {
      const parsed = JSON.parse(consensusData) as Record<string, unknown>;
      return parsed;
    } catch {
      return null;
    }
  }

  if (typeof consensusData === "object" && !Array.isArray(consensusData)) {
    return consensusData as Record<string, unknown>;
  }

  return null;
}

function normalizeAlert(raw: RawAlert, index: number): AlertRecord {
  const createdAt = toUnixSeconds(raw.created_at ?? raw.timestamp);
  const confidence =
    typeof raw.confidence === "number"
      ? raw.confidence <= 1
        ? raw.confidence * 100
        : raw.confidence
      : null;

  return {
    id: String(raw.id ?? `alert-${createdAt}-${index}`),
    protocol: String(raw.protocol ?? "unknown"),
    protocolName:
      (typeof raw.protocol_name === "string" && raw.protocol_name) ||
      (typeof raw.protocol === "string" && raw.protocol) ||
      "Unknown Protocol",
    threatLevel: normalizeThreat(raw.threat_level),
    action: String(raw.action ?? "NONE"),
    confidence,
    consensusPercent: normalizeConsensusPercent(raw),
    createdAt,
    consensusData: normalizeConsensusData(raw),
  };
}

function normalizeAlertsResponse(payload: unknown): AlertsPage {
  if (!payload) {
    return { items: [], total: 0, page: 1, limit: 20, totalPages: 1 };
  }

  if (Array.isArray(payload)) {
    const items = payload.map((entry, index) => normalizeAlert((entry ?? {}) as RawAlert, index));
    return {
      items,
      total: items.length,
      page: 1,
      limit: items.length || 20,
      totalPages: 1,
    };
  }

  const root = payload as Record<string, unknown>;
  const list = (root.items ?? root.alerts ?? root.data ?? []) as unknown[];
  const page = Math.max(
    1,
    Number(root.page ?? (root.pagination as Record<string, unknown> | undefined)?.page ?? 1),
  );
  const limit = Math.max(
    1,
    Number(root.limit ?? (root.pagination as Record<string, unknown> | undefined)?.limit ?? 20),
  );
  const total = Math.max(
    0,
    Number(
      root.total ?? (root.pagination as Record<string, unknown> | undefined)?.total ?? list.length,
    ),
  );

  const items = list.map((entry, index) => normalizeAlert((entry ?? {}) as RawAlert, index));

  return {
    items,
    total,
    page,
    limit,
    totalPages: Math.max(1, Math.ceil(total / limit)),
  };
}

export function useAlerts(options?: {
  page?: number;
  limit?: number;
  protocol?: string;
  refetchInterval?: number;
}) {
  const page = options?.page ?? 1;
  const limit = options?.limit ?? 20;

  return useQuery({
    queryKey: ["alerts", page, limit, options?.protocol ?? "all"],
    queryFn: async () => {
      const response = await api.getAlerts(page, limit, options?.protocol);
      return normalizeAlertsResponse(response);
    },
    refetchInterval: options?.refetchInterval,
    placeholderData: (previous) => previous,
  });
}

export function isEscalatedThreat(level: ThreatLevel): boolean {
  return level === "CRITICAL" || level === "HIGH";
}

export function formatRelativeTime(unixSeconds: number): string {
  const diff = Math.max(0, Math.floor(Date.now() / 1000) - unixSeconds);

  if (diff < 60) {
    return `${diff}s ago`;
  }

  if (diff < 3600) {
    return `${Math.floor(diff / 60)}m ago`;
  }

  if (diff < 86400) {
    return `${Math.floor(diff / 3600)}h ago`;
  }

  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatThreatLabel(level: ThreatLevel): string {
  if (level === "NONE") {
    return "LOW";
  }
  return level;
}
