import { useMemo } from "react";
import { motion } from "framer-motion";
import { useAlerts } from "../../hooks/useAlerts";
import { LoadingSkeleton } from "../common/LoadingSkeleton";

const BUCKETS = 12;
const WINDOW_SECONDS = 2 * 60 * 60;

function formatHourLabel(unixSeconds: number): string {
  const date = new Date(unixSeconds * 1000);
  return `${String(date.getHours()).padStart(2, "0")}:00`;
}

export function ThreatActivityChart() {
  const { data, isLoading, error } = useAlerts({ page: 1, limit: 200, refetchInterval: 15_000 });

  const chart = useMemo(() => {
    const now = Math.floor(Date.now() / 1000);
    const start = now - BUCKETS * WINDOW_SECONDS;
    const buckets = Array.from({ length: BUCKETS }, () => 0);

    for (const alert of data?.items ?? []) {
      if (alert.createdAt < start) {
        continue;
      }
      const offset = Math.floor((alert.createdAt - start) / WINDOW_SECONDS);
      const index = Math.min(BUCKETS - 1, Math.max(0, offset));
      buckets[index] += 1;
    }

    const labels = buckets.map((_, index) => formatHourLabel(start + index * WINDOW_SECONDS));
    const maxValue = Math.max(1, ...buckets);

    return { buckets, labels, maxValue };
  }, [data]);

  const width = 680;
  const height = 260;
  const padding = 28;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = chart.buckets.map((value, index) => {
    const x = padding + (index / Math.max(1, BUCKETS - 1)) * chartWidth;
    const y = height - padding - (value / chart.maxValue) * chartHeight;
    return { x, y, value };
  });

  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const areaPath = `${linePath} L ${padding + chartWidth} ${height - padding} L ${padding} ${height - padding} Z`;

  return (
    <section className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">Threat Activity</h3>
          <p className="text-sm text-[var(--text-secondary)]">
            Last 24 hours, sampled every 2 hours
          </p>
        </div>
        <span className="text-xs text-[var(--text-muted)]">
          Total: {chart.buckets.reduce((sum, value) => sum + value, 0)}
        </span>
      </div>

      {isLoading && <LoadingSkeleton lines={6} />}
      {error && (
        <p className="rounded-lg border border-[#7f1d1d] bg-[#7f1d1d]/30 px-3 py-2 text-sm text-[#fca5a5]">
          Unable to load threat activity timeline.
        </p>
      )}

      {!isLoading && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="overflow-x-auto"
        >
          <svg viewBox={`0 0 ${width} ${height}`} className="min-w-[620px]">
            <defs>
              <linearGradient id="threatArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgba(239, 68, 68, 0.28)" />
                <stop offset="100%" stopColor="rgba(239, 68, 68, 0)" />
              </linearGradient>
            </defs>

            {Array.from({ length: 5 }).map((_, index) => {
              const y = padding + (chartHeight / 4) * index;
              return (
                <line
                  key={`grid-${index}`}
                  x1={padding}
                  y1={y}
                  x2={padding + chartWidth}
                  y2={y}
                  stroke="rgba(63,63,70,0.35)"
                  strokeDasharray="3 5"
                />
              );
            })}

            <path d={areaPath} fill="url(#threatArea)" />
            <path d={linePath} fill="none" stroke="rgba(239,68,68,0.85)" strokeWidth="2.5" />

            {points.map((point, index) => (
              <circle
                key={`point-${index}`}
                cx={point.x}
                cy={point.y}
                r={3.5}
                fill="rgba(239,68,68,0.92)"
              />
            ))}
          </svg>

          <div className="mt-2 grid grid-cols-6 gap-2 sm:grid-cols-12">
            {chart.labels.map((label, index) => (
              <span key={`label-${index}`} className="text-center text-xs text-[var(--text-muted)]">
                {label}
              </span>
            ))}
          </div>
        </motion.div>
      )}
    </section>
  );
}
