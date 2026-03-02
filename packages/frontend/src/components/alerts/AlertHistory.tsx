import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, RefreshCw, Download } from "lucide-react";
import clsx from "clsx";
import { useAlerts } from "../../hooks/useAlerts";
import { TableRowSkeleton } from "../common/LoadingSkeleton";
import { AlertRow } from "./AlertRow";

interface AlertHistoryProps {
  title?: string;
  subtitle?: string;
  protocol?: string;
  pageSize?: number;
  className?: string;
}

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Failed to load alerts.";
  }

  if (error.message.toLowerCase().includes("timed out")) {
    return "Alert request timed out. Please retry.";
  }

  return error.message || "Failed to load alerts.";
}

export function AlertHistory({
  title = "Alert History",
  subtitle = "Complete timeline of detected threats and actions taken",
  protocol,
  pageSize = 15,
  className,
}: AlertHistoryProps) {
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data, isLoading, error, isFetching, refetch } = useAlerts({
    page,
    limit: pageSize,
    protocol,
    refetchInterval: 15_000,
  });

  const tableRows = useMemo(() => data?.items ?? [], [data]);
  const totalPages = data?.totalPages ?? 1;
  const currentPage = data?.page ?? 1;
  const total = data?.total ?? tableRows.length;
  const errorMessage = getErrorMessage(error);

  const startIndex = (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, total);

  return (
    <section
      className={clsx(
        "overflow-hidden rounded-lg border border-border-subtle bg-bg-surface",
        className
      )}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle px-5 py-4">
        <div>
          <h3 className="text-base font-semibold text-text-primary">{title}</h3>
          <p className="text-sm text-text-muted">{subtitle}</p>
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
            className="btn-secondary gap-1.5"
            onClick={() => {
              // Export functionality placeholder
              const csv = tableRows.map(row =>
                [row.id, row.protocolName, row.threatLevel, row.action, new Date(row.createdAt * 1000).toISOString()].join(",")
              ).join("\n");
              const blob = new Blob([`ID,Protocol,Threat,Action,Time\n${csv}`], { type: "text/csv" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `aegis-alerts-${Date.now()}.csv`;
              a.click();
            }}
          >
            <Download className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="table-header">
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Protocol</th>
                <th className="px-4 py-3 text-left">Threat</th>
                <th className="px-4 py-3 text-left">Action</th>
                <th className="px-4 py-3 text-left">Consensus</th>
                <th className="px-4 py-3 text-left">Time</th>
                <th className="px-4 py-3 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((i) => (
                <TableRowSkeleton key={i} columns={7} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="p-5">
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
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="table-header sticky top-0 z-10 border-b border-border-subtle">
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Protocol</th>
                  <th className="px-4 py-3 text-left">Threat</th>
                  <th className="px-4 py-3 text-left">Action</th>
                  <th className="px-4 py-3 text-left">Consensus</th>
                  <th className="px-4 py-3 text-left">Time</th>
                  <th className="px-4 py-3 w-12"></th>
                </tr>
              </thead>
              <tbody>
                {tableRows.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-12 text-center">
                      <p className="text-sm text-text-secondary">No alerts detected yet.</p>
                      <p className="mt-1 text-xs text-text-disabled">
                        This table will populate when sentinels publish new alerts.
                      </p>
                    </td>
                  </tr>
                ) : (
                  tableRows.map((alert) => (
                    <AlertRow
                      key={alert.id}
                      alert={alert}
                      expanded={expandedId === alert.id}
                      onToggle={() => setExpandedId((id) => (id === alert.id ? null : alert.id))}
                    />
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {tableRows.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border-subtle px-5 py-3">
              <p className="text-sm text-text-secondary">
                Showing <span className="font-medium text-text-primary">{startIndex}</span> to{" "}
                <span className="font-medium text-text-primary">{endIndex}</span> of{" "}
                <span className="font-medium text-text-primary">{total}</span> alerts
              </p>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  className="btn-secondary gap-1 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span className="hidden sm:inline">Previous</span>
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        type="button"
                        onClick={() => setPage(pageNum)}
                        className={clsx(
                          "flex h-8 w-8 items-center justify-center rounded-lg text-sm font-medium transition",
                          pageNum === currentPage
                            ? "bg-accent text-white"
                            : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
                        )}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages}
                  className="btn-secondary gap-1 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <span className="hidden sm:inline">Next</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
