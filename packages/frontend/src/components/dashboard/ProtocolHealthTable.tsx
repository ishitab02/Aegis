import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQueries } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useAlerts } from "../../hooks/useAlerts";
import { useProtocols } from "../../hooks/useProtocols";
import type { ThreatLevel } from "../../types";
import { ThreatBadge } from "../common/ThreatBadge";
import { StatusDot } from "../common/StatusDot";

const THREAT_RANK: Record<ThreatLevel, number> = {
  NONE: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
};

export function ProtocolHealthTable() {
  const navigate = useNavigate();
  const { data: protocols, isLoading, error } = useProtocols({ refetchInterval: 20_000 });
  const { data: alerts } = useAlerts({ page: 1, limit: 200, refetchInterval: 10_000 });

  const statusQueries = useQueries({
    queries: (protocols ?? []).map((protocol) => ({
      queryKey: ["protocol-status-inline", protocol.address],
      queryFn: () => api.getProtocolStatusByAddress(protocol.address) as Promise<unknown>,
      refetchInterval: 15_000,
    })),
  });

  const statusMap = useMemo(() => {
    const map = new Map<string, boolean>();
    for (const result of statusQueries) {
      const payload = (result.data ?? {}) as Record<string, unknown>;
      const address = String(payload.address ?? "");
      const breaker = (payload.circuitBreaker ?? null) as Record<string, unknown> | null;
      if (address) {
        map.set(address.toLowerCase(), Boolean(breaker?.paused));
      }
    }
    return map;
  }, [statusQueries]);

  const rows = useMemo(() => {
    const grouped = new Map<string, { highest: ThreatLevel; lastSeen: number }>();

    for (const alert of alerts?.items ?? []) {
      const key = alert.protocol.toLowerCase();
      const current = grouped.get(key);

      if (!current) {
        grouped.set(key, { highest: alert.threatLevel, lastSeen: alert.createdAt });
        continue;
      }

      const highest =
        THREAT_RANK[alert.threatLevel] > THREAT_RANK[current.highest]
          ? alert.threatLevel
          : current.highest;
      grouped.set(key, { highest, lastSeen: Math.max(current.lastSeen, alert.createdAt) });
    }

    return (protocols ?? []).map((protocol) => {
      const risk = grouped.get(protocol.address.toLowerCase());
      return {
        ...protocol,
        threat: risk?.highest ?? "NONE",
        lastSeen: risk?.lastSeen ?? protocol.registeredAt,
        paused: statusMap.get(protocol.address.toLowerCase()) ?? false,
      };
    });
  }, [alerts, protocols, statusMap]);

  return (
    <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Protocol Health</h3>
        <span className="text-xs text-[var(--text-muted)]">{rows.length} protocols monitored</span>
      </div>

      {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading protocols...</p>}
      {error && <p className="text-sm text-[#fca5a5]">Failed to load protocol inventory.</p>}

      {!isLoading && !error && rows.length === 0 && (
        <p className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-sm text-[var(--text-muted)]">
          No registered protocols yet.
        </p>
      )}

      {!isLoading && !error && rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-left text-xs uppercase tracking-[0.1em] text-[var(--text-muted)]">
                <th className="px-3 py-2">Protocol</th>
                <th className="px-3 py-2">Thresholds</th>
                <th className="px-3 py-2">Threat</th>
                <th className="px-3 py-2">Circuit</th>
                <th className="px-3 py-2">Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.address}
                  className="cursor-pointer border-b border-[var(--border-subtle)] text-sm transition hover:bg-white/[0.02]"
                  onClick={() => navigate(`/protocols/${row.address}`)}
                >
                  <td className="px-3 py-3">
                    <p className="font-medium text-[var(--text-primary)]">{row.name}</p>
                    <p className="font-mono text-xs text-[var(--text-muted)]">{row.address}</p>
                  </td>
                  <td className="px-3 py-3 text-[var(--text-secondary)]">
                    {row.alertThreshold}% / {row.breakerThreshold}%
                  </td>
                  <td className="px-3 py-3">
                    <ThreatBadge level={row.threat} variant="compact" />
                  </td>
                  <td className="px-3 py-3">
                    <span className="inline-flex items-center gap-2 text-[var(--text-secondary)]">
                      <StatusDot status={row.paused ? "critical" : "low"} animate={row.paused} />
                      {row.paused ? "PAUSED" : "NORMAL"}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-[var(--text-secondary)]">
                    {new Date(row.lastSeen * 1000).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
