import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { ProtocolRecord, ProtocolStatusResponse } from "../types";

function toUnixSeconds(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1_000_000_000_000 ? Math.floor(value / 1000) : value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed > 1_000_000_000_000 ? Math.floor(parsed / 1000) : parsed;
    }
  }
  return Math.floor(Date.now() / 1000);
}

function normalizeProtocols(payload: unknown): ProtocolRecord[] {
  if (!payload) {
    return [];
  }

  const list = Array.isArray(payload)
    ? payload
    : (((payload as Record<string, unknown>).protocols as unknown[]) ?? []);

  return list
    .map((entry) => (entry ?? {}) as Record<string, unknown>)
    .filter((entry) => typeof entry.address === "string")
    .map((entry) => ({
      address: String(entry.address),
      name: String(entry.name ?? "Unnamed Protocol"),
      alertThreshold: Number(entry.alert_threshold ?? 10),
      breakerThreshold: Number(entry.breaker_threshold ?? 20),
      active: Number(entry.active ?? 1) === 1,
      registeredAt: toUnixSeconds(entry.registered_at),
    }));
}

function normalizeProtocolStatus(payload: unknown): ProtocolStatusResponse {
  const root = ((payload as Record<string, unknown>) ?? {}) as Record<string, unknown>;
  const circuit = ((root.circuitBreaker as Record<string, unknown> | null) ?? null) as Record<
    string,
    unknown
  > | null;
  const protocol = ((root.protocol as Record<string, unknown> | null) ?? null) as Record<
    string,
    unknown
  > | null;

  return {
    address: String(root.address ?? ""),
    registered: Boolean(root.registered),
    protocol: protocol
      ? {
          address: String(protocol.address ?? ""),
          name: String(protocol.name ?? "Unknown Protocol"),
          alertThreshold: Number(protocol.alert_threshold ?? 10),
          breakerThreshold: Number(protocol.breaker_threshold ?? 20),
          active: Number(protocol.active ?? 1) === 1,
          registeredAt: toUnixSeconds(protocol.registered_at),
        }
      : null,
    circuitBreaker: circuit
      ? {
          paused: Boolean(circuit.paused),
          threatLevel: Number(circuit.threatLevel ?? 0),
          threatId: typeof circuit.threatId === "string" ? circuit.threatId : undefined,
          pausedAt: toUnixSeconds(circuit.pausedAt ?? 0),
          cooldownEnds: toUnixSeconds(circuit.cooldownEnds ?? 0),
          reason: String(circuit.reason ?? "No reason provided"),
        }
      : null,
    timestamp: toUnixSeconds(root.timestamp),
  };
}

export function useProtocols(options?: { activeOnly?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: ["protocols", options?.activeOnly ? "active" : "all"],
    queryFn: async () => {
      const response = await api.getProtocols(options?.activeOnly ?? false);
      return normalizeProtocols(response);
    },
    refetchInterval: options?.refetchInterval ?? 20_000,
  });
}

export function useProtocolStatus(address: string, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: ["protocol-status", address],
    queryFn: async () => {
      const response = await api.getProtocolStatusByAddress(address);
      return normalizeProtocolStatus(response);
    },
    enabled: Boolean(address),
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}
