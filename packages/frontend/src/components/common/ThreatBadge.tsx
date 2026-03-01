import clsx from "clsx";
import type { ThreatLevel } from "../../types";

interface ThreatBadgeProps {
  level: ThreatLevel;
  variant?: "default" | "compact" | "inline";
  showDot?: boolean;
  className?: string;
}

const STYLES: Record<ThreatLevel, {
  border: string;
  bg: string;
  text: string;
  dot: string;
  pulse?: boolean;
}> = {
  CRITICAL: {
    border: "border-l-threat-critical",
    bg: "bg-threat-critical-muted/50",
    text: "text-red-300",
    dot: "bg-threat-critical",
    pulse: true,
  },
  HIGH: {
    border: "border-l-threat-high",
    bg: "bg-threat-high-muted/50",
    text: "text-orange-300",
    dot: "bg-threat-high",
  },
  MEDIUM: {
    border: "border-l-threat-medium",
    bg: "bg-threat-medium-muted/50",
    text: "text-yellow-300",
    dot: "bg-threat-medium",
  },
  LOW: {
    border: "border-l-border-subtle",
    bg: "bg-threat-low-muted/50",
    text: "text-text-secondary",
    dot: "bg-threat-low",
  },
  NONE: {
    border: "border-l-border-subtle",
    bg: "bg-threat-low-muted/50",
    text: "text-text-secondary",
    dot: "bg-text-muted",
  },
};

export function ThreatBadge({
  level,
  variant = "default",
  showDot = true,
  className
}: ThreatBadgeProps) {
  const style = STYLES[level] ?? STYLES.NONE;
  const displayLabel = level === "NONE" ? "LOW" : level;

  if (variant === "inline") {
    return (
      <span
        className={clsx(
          "inline-flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide",
          style.text,
          className
        )}
      >
        {showDot && (
          <span className="relative flex h-1.5 w-1.5">
            {style.pulse && (
              <span className={clsx("absolute h-full w-full animate-ping rounded-full opacity-75", style.dot)} />
            )}
            <span className={clsx("relative h-1.5 w-1.5 rounded-full", style.dot)} />
          </span>
        )}
        {displayLabel}
      </span>
    );
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-md border-l-4 text-xs font-medium uppercase tracking-[0.06em]",
        variant === "compact" ? "px-2 py-0.5" : "px-3 py-1.5",
        style.border,
        style.bg,
        style.text,
        style.pulse && "animate-pulse-slow",
        className
      )}
    >
      {showDot && (
        <span className="relative flex h-1.5 w-1.5">
          {style.pulse && (
            <span className={clsx("absolute h-full w-full animate-ping rounded-full opacity-75", style.dot)} />
          )}
          <span className={clsx("relative h-1.5 w-1.5 rounded-full", style.dot)} />
        </span>
      )}
      {displayLabel}
    </span>
  );
}

export function getThreatColor(level: ThreatLevel): string {
  switch (level) {
    case "CRITICAL": return "#ef4444";
    case "HIGH": return "#f97316";
    case "MEDIUM": return "#eab308";
    case "LOW":
    case "NONE":
    default: return "#71717a";
  }
}

export function getThreatBgClass(level: ThreatLevel): string {
  switch (level) {
    case "CRITICAL": return "bg-threat-critical-muted/30";
    case "HIGH": return "bg-threat-high-muted/30";
    case "MEDIUM": return "bg-threat-medium-muted/30";
    case "LOW":
    case "NONE":
    default: return "bg-threat-low-muted/30";
  }
}
