import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowDown, ArrowUp, Minus, type LucideIcon } from "lucide-react";
import clsx from "clsx";

type TrendDirection = "up" | "down" | "neutral";
type IndicatorStatus = "success" | "warning" | "critical" | "neutral";

interface MetricCardProps {
  label: string;
  value: string | number;
  previousValue?: number;
  change?: string;
  subvalue?: string;
  trend?: TrendDirection;
  indicator?: IndicatorStatus;
  icon?: LucideIcon;
  animate?: boolean;
  className?: string;
}

const TREND_STYLES: Record<TrendDirection, { icon: typeof ArrowUp; classes: string }> = {
  up: { icon: ArrowUp, classes: "text-success bg-success-muted/30" },
  down: { icon: ArrowDown, classes: "text-threat-critical bg-threat-critical-muted/30" },
  neutral: { icon: Minus, classes: "text-text-muted bg-border-subtle/30" },
};

const INDICATOR_STYLES: Record<IndicatorStatus, { dot: string; glow?: string }> = {
  success: { dot: "bg-success", glow: "shadow-[0_0_8px_rgba(34,197,94,0.4)]" },
  warning: { dot: "bg-threat-medium" },
  critical: { dot: "bg-threat-critical", glow: "shadow-[0_0_8px_rgba(239,68,68,0.4)]" },
  neutral: { dot: "bg-text-muted" },
};

function AnimatedNumber({ value, duration = 500 }: { value: number; duration?: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const startTime = Date.now();
    const startValue = displayValue;
    const diff = value - startValue;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(startValue + diff * easeOut));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value, duration]);

  return <>{displayValue.toLocaleString()}</>;
}

export function MetricCard({
  label,
  value,
  change,
  subvalue,
  trend = "neutral",
  indicator,
  icon: Icon,
  animate = true,
  className,
}: MetricCardProps) {
  const trendStyle = TREND_STYLES[trend];
  const TrendIcon = trendStyle.icon;
  const indicatorStyle = indicator ? INDICATOR_STYLES[indicator] : null;

  const numericValue = typeof value === "number" ? value : parseFloat(value);
  const isNumeric = !isNaN(numericValue) && animate;

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={clsx(
        "group relative rounded-xl border border-border-subtle bg-bg-surface p-5 transition-all duration-200 hover:border-border-muted",
        className
      )}
    >
      {/* Header row */}
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {Icon && (
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-bg-elevated text-text-muted transition group-hover:text-text-secondary">
              <Icon className="h-4 w-4" />
            </span>
          )}
          <span className="text-sm font-medium text-text-secondary">{label}</span>
        </div>

        {change && (
          <span
            className={clsx(
              "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
              trendStyle.classes
            )}
          >
            <TrendIcon className="h-3 w-3" />
            {change}
          </span>
        )}

        {indicatorStyle && (
          <span className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span
                className={clsx(
                  "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
                  indicatorStyle.dot
                )}
              />
              <span
                className={clsx(
                  "relative inline-flex h-2 w-2 rounded-full",
                  indicatorStyle.dot,
                  indicatorStyle.glow
                )}
              />
            </span>
          </span>
        )}
      </div>

      {/* Value */}
      <p className="text-3xl font-bold tracking-tight text-text-primary">
        {isNumeric ? <AnimatedNumber value={numericValue} /> : value}
      </p>

      {/* Subvalue */}
      {subvalue && (
        <p className="mt-2 text-sm text-text-muted">{subvalue}</p>
      )}
    </motion.article>
  );
}

// Compact variant for inline metrics
export function MetricInline({
  label,
  value,
  trend,
}: {
  label: string;
  value: string;
  trend?: TrendDirection;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-bg-surface px-3 py-2">
      <span className="text-xs text-text-muted">{label}</span>
      <span className={clsx(
        "text-sm font-semibold",
        trend === "up" ? "text-success" :
        trend === "down" ? "text-threat-critical" :
        "text-text-primary"
      )}>
        {value}
      </span>
    </div>
  );
}
