import clsx from "clsx";

interface LoadingSkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export function LoadingSkeleton({
  className,
  variant = "rectangular",
  width,
  height,
  lines = 1,
}: LoadingSkeletonProps) {
  const baseClasses = "skeleton";

  const variantClasses = {
    text: "h-4 rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height) style.height = typeof height === "number" ? `${height}px` : height;

  if (lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={clsx(
              baseClasses,
              variantClasses.text,
              i === lines - 1 && "w-3/4",
              className,
            )}
            style={{ height: height || 16 }}
          />
        ))}
      </div>
    );
  }

  return <div className={clsx(baseClasses, variantClasses[variant], className)} style={style} />;
}

export function MetricCardSkeleton() {
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <LoadingSkeleton width={80} height={14} />
        <LoadingSkeleton width={40} height={14} />
      </div>
      <LoadingSkeleton width={100} height={32} className="mb-2" />
      <LoadingSkeleton width={60} height={12} />
    </div>
  );
}

export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr className="table-row">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="table-cell">
          <LoadingSkeleton width={i === 0 ? 24 : i === columns - 1 ? 60 : "80%"} height={16} />
        </td>
      ))}
    </tr>
  );
}

export function AlertCardSkeleton() {
  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between">
        <LoadingSkeleton width={80} height={20} />
        <LoadingSkeleton width={50} height={14} />
      </div>
      <LoadingSkeleton lines={2} className="mb-2" />
      <div className="flex gap-4">
        <LoadingSkeleton width={60} height={12} />
        <LoadingSkeleton width={80} height={12} />
      </div>
    </div>
  );
}
