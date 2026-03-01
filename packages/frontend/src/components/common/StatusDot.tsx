import clsx from "clsx";

type StatusType = "success" | "critical" | "high" | "medium" | "low" | "neutral";

interface StatusDotProps {
  status: StatusType;
  animate?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const STATUS_COLORS: Record<StatusType, { ping: string; dot: string }> = {
  success: {
    ping: "bg-success",
    dot: "bg-success",
  },
  critical: {
    ping: "bg-threat-critical",
    dot: "bg-threat-critical",
  },
  high: {
    ping: "bg-threat-high",
    dot: "bg-threat-high",
  },
  medium: {
    ping: "bg-threat-medium",
    dot: "bg-threat-medium",
  },
  low: {
    ping: "bg-threat-low",
    dot: "bg-threat-low",
  },
  neutral: {
    ping: "bg-text-muted",
    dot: "bg-text-muted",
  },
};

const SIZES = {
  sm: "h-1.5 w-1.5",
  md: "h-2 w-2",
  lg: "h-2.5 w-2.5",
};

export function StatusDot({
  status,
  animate = true,
  size = "md",
  className,
}: StatusDotProps) {
  const colors = STATUS_COLORS[status];
  const sizeClass = SIZES[size];

  return (
    <span className={clsx("relative inline-flex", sizeClass, className)}>
      {animate && (
        <span
          className={clsx(
            "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
            colors.ping
          )}
        />
      )}
      <span
        className={clsx("relative inline-flex rounded-full", sizeClass, colors.dot)}
      />
    </span>
  );
}
