import { ArrowRight } from "lucide-react";

export function AttackFlowDiagram({
  nodes,
}: {
  nodes: Array<{ id: string; label: string; address?: string; action?: string }>;
}) {
  if (nodes.length === 0) {
    return <p className="text-sm text-[var(--text-muted)]">No attack flow data available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <div className="flex min-w-max items-center gap-2 pb-2">
        {nodes.map((node, index) => (
          <div key={node.id} className="contents">
            <article className="w-56 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)] p-3">
              <p className="text-sm font-medium text-[var(--text-primary)]">{node.label}</p>
              {node.address && (
                <p className="mt-1 break-all font-mono text-xs text-[var(--text-muted)]">
                  {node.address}
                </p>
              )}
              {node.action && (
                <p className="mt-2 text-xs text-[var(--text-secondary)]">Action: {node.action}</p>
              )}
            </article>
            {index < nodes.length - 1 && (
              <ArrowRight className="h-4 w-4 text-[var(--text-muted)]" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
