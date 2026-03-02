import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "../components/common/Toast";
import type { AlertRecord, AlertsPage, ThreatLevel } from "../types";

const ALERT_STREAM_URL = "http://localhost:3000/api/v1/ws";
const MAX_RECONNECT_DELAY_MS = 30000;

type StreamStatus = "connecting" | "connected" | "reconnecting" | "disconnected";

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
  const data = raw.consensus_data;
  if (!data) {
    return null;
  }

  if (typeof data === "string") {
    try {
      return JSON.parse(data) as Record<string, unknown>;
    } catch {
      return null;
    }
  }

  if (typeof data === "object" && !Array.isArray(data)) {
    return data as Record<string, unknown>;
  }

  return null;
}

function normalizeAlert(raw: RawAlert, index: number): AlertRecord {
  const createdAt = toUnixSeconds(raw.created_at ?? raw.timestamp);
  const confidence = typeof raw.confidence === "number"
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

function mergeAlert(existing: AlertsPage, incoming: AlertRecord): AlertsPage {
  if (existing.items.some((item) => item.id === incoming.id)) {
    return existing;
  }

  const nextTotal = existing.total + 1;
  const nextItems = [incoming, ...existing.items].slice(0, existing.limit);

  return {
    ...existing,
    items: nextItems,
    total: nextTotal,
    totalPages: Math.max(1, Math.ceil(nextTotal / existing.limit)),
  };
}

function normalizeThreatLabel(level: ThreatLevel): string {
  if (level === "NONE") {
    return "LOW";
  }
  return level;
}

function getReconnectDelay(attempt: number): number {
  const base = Math.min(MAX_RECONNECT_DELAY_MS, 1000 * 2 ** attempt);
  const jitter = Math.floor(Math.random() * 250);
  return base + jitter;
}

export function useAlertStream() {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();

  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [lastEventAt, setLastEventAt] = useState<number | null>(null);

  const sourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef(0);
  const disconnectedNoticeShownRef = useRef(false);
  const disposedRef = useRef(false);
  const seenIdsRef = useRef<Set<string>>(new Set());

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const upsertAlertCaches = useCallback(
    (raw: RawAlert, alert: AlertRecord) => {
      const alertQueries = queryClient.getQueryCache().findAll({ queryKey: ["alerts"] });

      for (const query of alertQueries) {
        const key = query.queryKey;
        if (!Array.isArray(key) || key[0] !== "alerts") {
          continue;
        }

        const protocolFilter = key[3];
        if (
          typeof protocolFilter === "string" &&
          protocolFilter !== "all" &&
          protocolFilter.toLowerCase() !== alert.protocol.toLowerCase()
        ) {
          continue;
        }

        queryClient.setQueryData<AlertsPage | undefined>(key, (previous) => {
          if (!previous) {
            return previous;
          }
          return mergeAlert(previous, alert);
        });
      }

      queryClient.setQueryData<unknown>(["live-threat-feed-alerts"], (previous: unknown) => {
        if (!previous || typeof previous !== "object") {
          return previous;
        }

        const root = previous as Record<string, unknown>;
        const items = Array.isArray(root.items) ? root.items : [];
        const alreadyExists = items.some((item) => {
          if (!item || typeof item !== "object") {
            return false;
          }
          return String((item as Record<string, unknown>).id ?? "") === alert.id;
        });

        if (alreadyExists) {
          return previous;
        }

        const nextItems = [raw, ...items].slice(0, 20);
        return {
          ...root,
          items: nextItems,
          total:
            typeof root.total === "number" && Number.isFinite(root.total)
              ? root.total + 1
              : nextItems.length,
        };
      });
    },
    [queryClient]
  );

  const connect = useCallback(() => {
    if (disposedRef.current) {
      return;
    }

    clearReconnectTimer();

    setStatus(reconnectAttemptRef.current > 0 ? "reconnecting" : "connecting");

    const source = new EventSource(ALERT_STREAM_URL);
    sourceRef.current = source;

    source.addEventListener("system", (event: Event) => {
      const message = event as MessageEvent<string>;
      if (!message.data) {
        return;
      }

      reconnectAttemptRef.current = 0;
      disconnectedNoticeShownRef.current = false;
      setStatus("connected");
      setLastEventAt(Math.floor(Date.now() / 1000));
    });

    source.addEventListener("alert", (event: Event) => {
      const message = event as MessageEvent<string>;
      if (!message.data) {
        return;
      }

      let parsed: RawAlert;
      try {
        parsed = JSON.parse(message.data) as RawAlert;
      } catch {
        return;
      }

      const parsedId = typeof parsed.id === "string" ? parsed.id : String(parsed.id ?? "");
      if (parsedId && seenIdsRef.current.has(parsedId)) {
        return;
      }

      if (parsedId) {
        seenIdsRef.current.add(parsedId);
        if (seenIdsRef.current.size > 500) {
          const keys = Array.from(seenIdsRef.current);
          const retained = keys.slice(-250);
          seenIdsRef.current = new Set(retained);
        }
      }

      const alert = normalizeAlert(parsed, 0);
      setLastEventAt(Math.floor(Date.now() / 1000));
      upsertAlertCaches(parsed, alert);

      if (alert.threatLevel === "CRITICAL") {
        pushToast({
          variant: "critical",
          title: alert.protocolName,
          message: "CRITICAL threat - Circuit breaker triggered",
        });
        return;
      }

      if (alert.threatLevel === "HIGH") {
        pushToast({
          variant: "warning",
          title: alert.protocolName,
          message: "HIGH threat detected",
        });
        return;
      }

      pushToast({
        variant: "success",
        title: alert.protocolName,
        message: `New ${normalizeThreatLabel(alert.threatLevel)} alert received`,
      });
    });

    source.onerror = () => {
      source.close();

      if (disposedRef.current) {
        return;
      }

      setStatus("reconnecting");

      if (!disconnectedNoticeShownRef.current) {
        disconnectedNoticeShownRef.current = true;
        pushToast({
          variant: "error",
          message: "Failed to connect to API",
        });
      }

      const delay = getReconnectDelay(reconnectAttemptRef.current);
      reconnectAttemptRef.current += 1;

      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, delay);
    };
  }, [clearReconnectTimer, pushToast, upsertAlertCaches]);

  useEffect(() => {
    disposedRef.current = false;
    connect();

    return () => {
      disposedRef.current = true;
      clearReconnectTimer();
      if (sourceRef.current) {
        sourceRef.current.close();
      }
    };
  }, [connect, clearReconnectTimer]);

  return {
    status,
    lastEventAt,
    reconnectAttempts: reconnectAttemptRef.current,
  };
}
