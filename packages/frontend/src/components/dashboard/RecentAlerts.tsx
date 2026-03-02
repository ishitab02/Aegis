import { useMemo } from "react";
import { formatRelativeTime, isEscalatedThreat, useAlerts } from "../../hooks/useAlerts";
import { ThreatBadge } from "../common/ThreatBadge";

export function RecentAlerts({
  limit = 5,
  criticalOnly = false,
}: {
  limit?: number;
  criticalOnly?: boolean;
}) {
  const { data, isLoading, error } = useAlerts({ page: 1, limit: 40, refetchInterval: 10_000 });

  const items = useMemo(() => {
    const alerts = data?.items ?? [];
    const filtered = criticalOnly
      ? alerts.filter((item) => isEscalatedThreat(item.threatLevel))
      : alerts;
    return filtered.slice(0, limit);
  }, [criticalOnly, data, limit]);

  return (
    <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Recent Critical Alerts</h3>
        <span className="text-xs text-[var(--text-muted)]">{items.length} items</span>
      </div>

      {isLoading && <p className="text-sm text-[var(--text-muted)]">Loading alerts...</p>}
      {error && <p className="text-sm text-[#fca5a5]">Unable to load alerts.</p>}

      {!isLoading && !error && items.length === 0 && (
        <p className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2 text-sm text-[var(--text-muted)]">
          No critical alerts in this window.
        </p>
      )}

      <ul className="space-y-2">
        {items.map((alert) => (
          <li
            key={alert.id}
            className="rounded-md border border-[var(--border-subtle)] bg-[var(--bg-elevated)] px-3 py-2"
          >
            <div className="mb-1 flex items-center justify-between">
              <ThreatBadge level={alert.threatLevel} variant="compact" />
              <time className="text-xs text-[var(--text-muted)]">
                {formatRelativeTime(alert.createdAt)}
              </time>
            </div>
            <p className="truncate text-sm font-medium text-[var(--text-primary)]">
              {alert.protocolName}
            </p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              Action: {alert.action.replace(/_/g, " ")}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
