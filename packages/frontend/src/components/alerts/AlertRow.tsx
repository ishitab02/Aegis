import { motion, AnimatePresence } from "framer-motion";
import { Boxes, ChevronDown, ExternalLink, Copy, Check } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import { formatRelativeTime } from "../../hooks/useAlerts";
import type { AlertRecord, ThreatLevel } from "../../types";
import { StatusDot } from "../common/StatusDot";
import { ThreatBadge } from "../common/ThreatBadge";
import { Tooltip } from "../common/Tooltip";

function getStatusType(threat: ThreatLevel): "critical" | "high" | "medium" | "low" | "neutral" {
  switch (threat) {
    case "CRITICAL":
      return "critical";
    case "HIGH":
      return "high";
    case "MEDIUM":
      return "medium";
    default:
      return "neutral";
  }
}

function truncateAddress(address: string): string {
  if (address.length <= 12) return address;
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

interface AlertRowProps {
  alert: AlertRecord;
  expanded: boolean;
  onToggle: () => void;
}

export function AlertRow({ alert, expanded, onToggle }: AlertRowProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <tr
        className={clsx(
          "group cursor-pointer border-b border-border-subtle text-sm transition-colors",
          expanded ? "bg-bg-elevated" : "hover:bg-white/[0.02]",
        )}
        onClick={onToggle}
      >
        <td className="w-12 px-4 py-3.5">
          <StatusDot
            status={getStatusType(alert.threatLevel)}
            animate={alert.threatLevel === "CRITICAL"}
            size="md"
          />
        </td>

        <td className="px-4 py-3.5">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-border-subtle bg-bg-surface text-text-muted transition group-hover:border-border-muted">
              <Boxes className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-text-primary">{alert.protocolName}</p>
              <p className="truncate font-mono text-xs text-text-muted">
                {truncateAddress(alert.protocol)}
              </p>
            </div>
          </div>
        </td>

        <td className="px-4 py-3.5">
          <ThreatBadge level={alert.threatLevel} variant="compact" />
        </td>

        <td className="px-4 py-3.5">
          <span
            className={clsx(
              "rounded-md px-2 py-1 text-xs font-medium",
              alert.action === "CIRCUIT_BREAKER" || alert.action === "PAUSE"
                ? "bg-threat-critical-muted/30 text-red-300"
                : alert.action === "ALERT" || alert.action === "INVESTIGATE"
                  ? "bg-threat-medium-muted/30 text-yellow-300"
                  : "bg-border-subtle/50 text-text-secondary",
            )}
          >
            {alert.action.replace(/_/g, " ")}
          </span>
        </td>

        <td className="px-4 py-3.5">
          {typeof alert.consensusPercent === "number" ? (
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-border-subtle">
                <div
                  className={clsx(
                    "h-full rounded-full transition-all",
                    alert.consensusPercent >= 80
                      ? "bg-success"
                      : alert.consensusPercent >= 60
                        ? "bg-threat-medium"
                        : "bg-threat-critical",
                  )}
                  style={{ width: `${Math.min(100, alert.consensusPercent)}%` }}
                />
              </div>
              <span className="text-sm text-text-secondary">
                {alert.consensusPercent.toFixed(0)}%
              </span>
            </div>
          ) : (
            <span className="text-sm text-text-muted">—</span>
          )}
        </td>

        <td className="px-4 py-3.5">
          <Tooltip content={new Date(alert.createdAt * 1000).toLocaleString()}>
            <time className="text-sm text-text-secondary">
              {formatRelativeTime(alert.createdAt)}
            </time>
          </Tooltip>
        </td>

        <td className="w-12 px-4 py-3.5 text-right">
          <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown className="h-4 w-4 text-text-muted" />
          </motion.div>
        </td>
      </tr>

      <AnimatePresence>
        {expanded && (
          <motion.tr
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="border-b border-border-subtle bg-bg-elevated"
          >
            <td colSpan={7} className="px-4 py-4">
              <motion.div
                initial={{ y: -8 }}
                animate={{ y: 0 }}
                className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
              >
                <div>
                  <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-text-muted">
                    Alert ID
                  </p>
                  <div className="flex items-center gap-2">
                    <p className="truncate font-mono text-sm text-text-secondary">{alert.id}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopy(alert.id);
                      }}
                      className="flex-shrink-0 rounded p-1 text-text-muted hover:bg-white/[0.05] hover:text-text-secondary"
                    >
                      {copied ? (
                        <Check className="h-3.5 w-3.5 text-success" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-text-muted">
                    Confidence
                  </p>
                  <p className="text-sm text-text-secondary">
                    {typeof alert.confidence === "number"
                      ? `${alert.confidence.toFixed(1)}%`
                      : "Unavailable"}
                  </p>
                </div>

                <div>
                  <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-text-muted">
                    Protocol Address
                  </p>
                  <div className="flex items-center gap-2">
                    <p className="truncate font-mono text-sm text-text-secondary">
                      {alert.protocol}
                    </p>
                    <a
                      href={`https://basescan.org/address/${alert.protocol}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="flex-shrink-0 rounded p-1 text-text-muted hover:bg-white/[0.05] hover:text-accent"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  </div>
                </div>

                <div>
                  <p className="mb-1.5 text-2xs font-medium uppercase tracking-wider text-text-muted">
                    Recorded At
                  </p>
                  <p className="text-sm text-text-secondary">
                    {new Date(alert.createdAt * 1000).toLocaleString()}
                  </p>
                </div>
              </motion.div>

              {alert.consensusData && (
                <div className="mt-4 rounded-lg border border-border-subtle bg-bg-base p-3">
                  <p className="mb-2 text-2xs font-medium uppercase tracking-wider text-text-muted">
                    Consensus Data
                  </p>
                  <pre className="overflow-x-auto text-xs text-text-secondary">
                    {JSON.stringify(alert.consensusData, null, 2)}
                  </pre>
                </div>
              )}
            </td>
          </motion.tr>
        )}
      </AnimatePresence>
    </>
  );
}
