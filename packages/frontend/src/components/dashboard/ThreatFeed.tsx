import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Pause, Play, RefreshCw, Filter } from "lucide-react";
import clsx from "clsx";
import { api } from "../../lib/api";
import type { ThreatLevel } from "../../types";
import { ThreatBadge, getThreatBgClass } from "../common/ThreatBadge";
import { formatRelativeTime } from "../../hooks/useAlerts";
import { LoadingSkeleton, AlertCardSkeleton } from "../common/LoadingSkeleton";

type FeedItem = {
  id: string;
  protocolName: string;
  threatLevel: ThreatLevel;
  details: string;
  confidence: number | null;
  action: string;
  timestamp: number;
};

const LEVEL_FILTERS: Array<ThreatLevel | "ALL"> = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Failed to load threat feed.";
  }

  if (error.message.toLowerCase().includes("timed out")) {
    return "Threat feed request timed out. Please retry.";
  }

  return error.message || "Failed to load threat feed.";
}

function normalizeThreat(level: unknown): ThreatLevel {
  if (typeof level !== "string") return "NONE";
  const upper = level.toUpperCase();
  if (upper === "LOW" || upper === "MEDIUM" || upper === "HIGH" || upper === "CRITICAL") {
    return upper;
  }
  return "NONE";
}

function normalizeTimestamp(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1_000_000_000_000 ? Math.floor(value / 1000) : value;
  }
  if (typeof value === "string") {
    const numeric = Number(value);
    if (!Number.isNaN(numeric)) {
      return numeric > 1_000_000_000_000 ? Math.floor(numeric / 1000) : numeric;
    }
  }
  return Math.floor(Date.now() / 1000);
}

function normalizeConfidence(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value <= 1 ? value * 100 : value;
}

function extractFeedItems(payload: unknown): FeedItem[] {
  const root = ((payload as Record<string, unknown>) ?? {}) as Record<string, unknown>;
  const assessments = Array.isArray(root.assessments) ? root.assessments : [];
  const fallbackProtocol =
    (typeof root.protocol_name === "string" && root.protocol_name) ||
    (typeof root.protocol === "string" && root.protocol) ||
    "Unknown Protocol";
  const fallbackAction =
    (typeof (root.consensus as Record<string, unknown> | undefined)?.action_recommended ===
      "string" &&
      String((root.consensus as Record<string, unknown>).action_recommended)) ||
    "MONITOR";

  return assessments
    .map((entry, index) => {
      const assessment = ((entry ?? {}) as Record<string, unknown>) ?? {};
      const timestamp = normalizeTimestamp(assessment.timestamp ?? root.timestamp);

      return {
        id:
          (typeof assessment.id === "string" && assessment.id) ||
          (typeof assessment.sentinel_id === "string" &&
            `${assessment.sentinel_id}-${timestamp}`) ||
          `feed-${timestamp}-${index}`,
        protocolName:
          (typeof assessment.protocol_name === "string" && assessment.protocol_name) ||
          (typeof assessment.protocol === "string" && assessment.protocol) ||
          fallbackProtocol,
        threatLevel: normalizeThreat(assessment.threat_level),
        details:
          (typeof assessment.details === "string" && assessment.details) ||
          "Sentinel reported anomalous protocol behavior.",
        confidence: normalizeConfidence(assessment.confidence),
        action:
          (typeof assessment.action === "string" && assessment.action) ||
          (typeof assessment.recommendation === "string" && assessment.recommendation) ||
          fallbackAction,
        timestamp,
      };
    })
    .sort((a, b) => b.timestamp - a.timestamp);
}

/** Convert /alerts response items into feed items. */
function extractAlertFeedItems(payload: unknown): FeedItem[] {
  const root = ((payload as Record<string, unknown>) ?? {}) as Record<string, unknown>;
  const items = Array.isArray(root.items) ? root.items : Array.isArray(root) ? root : [];

  return items.map((entry: unknown, index: number) => {
    const alert = ((entry ?? {}) as Record<string, unknown>) ?? {};
    const timestamp = normalizeTimestamp(alert.created_at ?? alert.timestamp);

    return {
      id: (typeof alert.id === "string" && alert.id) || `alert-${timestamp}-${index}`,
      protocolName:
        (typeof alert.protocol_name === "string" && alert.protocol_name) ||
        (typeof alert.protocol === "string" && alert.protocol) ||
        "Unknown Protocol",
      threatLevel: normalizeThreat(alert.threat_level),
      details:
        (typeof alert.details === "string" && alert.details) ||
        `${normalizeThreat(alert.threat_level)} threat detected — ${(typeof alert.action === "string" && alert.action) || "ALERT"}`,
      confidence: normalizeConfidence(alert.confidence),
      action: (typeof alert.action === "string" && alert.action) || "ALERT",
      timestamp,
    };
  });
}

interface ThreatFeedProps {
  compact?: boolean;
  className?: string;
}

export function ThreatFeed({ compact = false, className }: ThreatFeedProps) {
  const [paused, setPaused] = useState(false);
  const [filter, setFilter] = useState<ThreatLevel | "ALL">("ALL");
  const [visibleCount, setVisibleCount] = useState(compact ? 5 : 10);
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());
  const previousIds = useRef<string[]>([]);

  const { data, isLoading, error, isFetching, refetch } = useQuery({
    queryKey: ["live-threat-feed"],
    queryFn: () => api.getSentinelAggregate() as Promise<unknown>,
    refetchInterval: paused ? false : 5_000,
  });
  const errorMessage = getErrorMessage(error);

  // Also fetch recent alerts for historical feed items
  const { data: alertsData } = useQuery({
    queryKey: ["live-threat-feed-alerts"],
    queryFn: () => api.getAlerts(1, 10) as Promise<unknown>,
    refetchInterval: paused ? false : 15_000,
  });

  const items = useMemo(() => {
    const liveItems = extractFeedItems(data);
    const historyItems = extractAlertFeedItems(alertsData);
    // Merge: live first, then history — deduplicate by timestamp+protocol
    const seen = new Set(liveItems.map((i) => `${i.timestamp}-${i.protocolName}`));
    const merged = [...liveItems];
    for (const item of historyItems) {
      const key = `${item.timestamp}-${item.protocolName}`;
      if (!seen.has(key)) {
        seen.add(key);
        merged.push(item);
      }
    }
    return merged.sort((a, b) => b.timestamp - a.timestamp);
  }, [data, alertsData]);
  const filteredItems = useMemo(
    () =>
      items
        .filter((item) => (filter === "ALL" ? true : item.threatLevel === filter))
        .slice(0, visibleCount),
    [filter, items, visibleCount],
  );

  // Track new items for highlight effect
  useEffect(() => {
    const prev = new Set(previousIds.current);
    const fresh = items.filter((item) => !prev.has(item.id)).map((item) => item.id);
    previousIds.current = items.map((item) => item.id);

    if (fresh.length === 0) return;

    setHighlightedIds(new Set(fresh));
    const timer = setTimeout(() => setHighlightedIds(new Set()), 2500);
    return () => clearTimeout(timer);
  }, [items]);

  return (
    <section
      className={clsx(
        "overflow-hidden rounded-lg border border-border-subtle bg-bg-surface",
        className,
      )}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary">Live Threat Feed</h3>
          <p className="text-sm text-text-muted">Real-time sentinel consensus</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn-ghost p-2"
            aria-label="Refresh"
          >
            <RefreshCw className={clsx("h-4 w-4", isFetching && "animate-spin")} />
          </button>
          <button
            type="button"
            onClick={() => setPaused((s) => !s)}
            className={clsx(
              "btn-secondary gap-1.5",
              paused && "border-threat-medium/50 text-threat-medium",
            )}
          >
            {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{paused ? "Resume" : "Pause"}</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 overflow-x-auto border-b border-border-subtle px-5 py-3 scrollbar-hide">
        <Filter className="h-3.5 w-3.5 flex-shrink-0 text-text-muted" />
        {LEVEL_FILTERS.map((level) => (
          <button
            key={level}
            type="button"
            onClick={() => setFilter(level)}
            className={clsx(
              "flex-shrink-0 rounded-full border px-3 py-1 text-xs font-medium transition-all",
              filter === level
                ? "border-accent bg-accent/10 text-accent"
                : "border-border-subtle text-text-secondary hover:border-border-muted hover:text-text-primary",
            )}
          >
            {level === "ALL" ? "All" : level}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <AlertCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/20 px-4 py-3">
            <p className="text-sm text-red-300">{errorMessage}</p>
            <button
              type="button"
              onClick={() => refetch()}
              className="mt-2 rounded border border-red-500/50 px-2 py-1 text-xs text-red-200 transition hover:bg-red-500/20"
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <>
            <AnimatePresence mode="popLayout">
              {filteredItems.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-lg border border-border-subtle bg-bg-elevated px-4 py-8 text-center"
                >
                  <p className="text-sm text-text-secondary">
                    {items.length === 0
                      ? "No threat activity yet."
                      : "No threats match the selected filter."}
                  </p>
                  <p className="mt-1 text-xs text-text-disabled">
                    {items.length === 0
                      ? "Live alerts will appear here as new assessments arrive."
                      : "Try a different severity filter."}
                  </p>
                </motion.div>
              ) : (
                <ul className="space-y-2">
                  {filteredItems.map((item, index) => (
                    <motion.li
                      key={item.id}
                      layout
                      initial={{ opacity: 0, y: -12 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ delay: index * 0.03, duration: 0.2 }}
                      className={clsx(
                        "relative rounded-lg border border-border-subtle p-4 transition-all",
                        getThreatBgClass(item.threatLevel),
                        highlightedIds.has(item.id) && "ring-1 ring-accent/50",
                      )}
                    >
                      {/* Left border indicator */}
                      <div
                        className={clsx(
                          "absolute left-0 top-0 h-full w-1 rounded-l-lg",
                          item.threatLevel === "CRITICAL" && "bg-threat-critical",
                          item.threatLevel === "HIGH" && "bg-threat-high",
                          item.threatLevel === "MEDIUM" && "bg-threat-medium",
                          (item.threatLevel === "LOW" || item.threatLevel === "NONE") &&
                            "bg-border-subtle",
                        )}
                      />

                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="mb-2 flex items-center gap-2">
                            <ThreatBadge level={item.threatLevel} variant="compact" />
                            <span className="truncate text-sm font-medium text-text-primary">
                              {item.protocolName}
                            </span>
                          </div>
                          <p className="mb-2 text-sm text-text-secondary line-clamp-2">
                            {item.details}
                          </p>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted">
                            <span>
                              Confidence:{" "}
                              {item.confidence !== null ? `${item.confidence.toFixed(0)}%` : "N/A"}
                            </span>
                            <span className="hidden sm:inline">•</span>
                            <span className="hidden sm:inline">
                              Action: {item.action.replace(/_/g, " ")}
                            </span>
                          </div>
                        </div>
                        <time
                          className="flex-shrink-0 text-xs text-text-muted"
                          title={new Date(item.timestamp * 1000).toLocaleString()}
                        >
                          {formatRelativeTime(item.timestamp)}
                        </time>
                      </div>
                    </motion.li>
                  ))}
                </ul>
              )}
            </AnimatePresence>

            {/* Load more */}
            {!compact && items.length > visibleCount && (
              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => setVisibleCount((c) => c + 8)}
                  className="btn-ghost text-xs"
                >
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border-subtle px-5 py-3">
        <p className="text-xs text-text-muted">
          {paused ? (
            <span className="text-threat-medium">Feed paused</span>
          ) : isFetching ? (
            "Refreshing..."
          ) : (
            "Auto-refresh every 5s"
          )}
        </p>
      </div>
    </section>
  );
}
