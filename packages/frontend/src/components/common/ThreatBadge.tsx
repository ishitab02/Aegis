import type { ThreatLevel } from "../../types";
import { THREAT_BG, THREAT_TEXT } from "../../lib/constants";

export function ThreatBadge({ level }: { level: ThreatLevel }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${THREAT_BG[level]} ${THREAT_TEXT[level]}`}
    >
      {level === "CRITICAL" && (
        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse mr-1.5" />
      )}
      {level}
    </span>
  );
}
