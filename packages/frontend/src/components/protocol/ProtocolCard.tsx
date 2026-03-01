import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import type { ProtocolRecord } from "../../types";
import { StatusDot } from "../common/StatusDot";

export function ProtocolCard({
  protocol,
  selected,
  onSelect,
}: {
  protocol: ProtocolRecord;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.01 }}
      className={`w-full rounded-lg border p-4 text-left transition ${
        selected
          ? "border-[var(--accent)] bg-[color:rgba(59,130,246,0.12)]"
          : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-muted)]"
      }`}
      onClick={onSelect}
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">{protocol.name}</p>
          <p className="mt-1 font-mono text-xs text-[var(--text-muted)]">{protocol.address}</p>
        </div>
        <ChevronRight className="h-4 w-4 text-[var(--text-muted)]" />
      </div>

      <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
        <span>Alert {protocol.alertThreshold}%</span>
        <span>Breaker {protocol.breakerThreshold}%</span>
        <span className="inline-flex items-center gap-1.5">
          <StatusDot status={protocol.active ? "low" : "neutral"} />
          {protocol.active ? "Active" : "Disabled"}
        </span>
      </div>
    </motion.button>
  );
}
