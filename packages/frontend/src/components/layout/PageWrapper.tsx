import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { isEscalatedThreat, useAlerts } from "../../hooks/useAlerts";

interface PageWrapperProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function PageWrapper({ children, title, subtitle, actions }: PageWrapperProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const { data: alerts } = useAlerts({ page: 1, limit: 50, refetchInterval: 10_000 });

  const alertCount = useMemo(
    () => (alerts?.items ?? []).filter((item) => isEscalatedThreat(item.threatLevel)).length,
    [alerts]
  );

  return (
    <div className="min-h-screen bg-bg-base text-text-primary">
      <Header
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((open) => !open)}
      />
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        alertCount={alertCount}
      />

      <main className="min-h-[calc(100vh-4rem)] px-4 pb-8 pt-20 sm:px-6 lg:ml-64 lg:px-8">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="mx-auto max-w-7xl"
        >
          {/* Page header */}
          {(title || actions) && (
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                {title && (
                  <h1 className="text-xl font-semibold text-text-primary sm:text-2xl">
                    {title}
                  </h1>
                )}
                {subtitle && (
                  <p className="mt-1 text-sm text-text-muted">{subtitle}</p>
                )}
              </div>
              {actions && <div className="flex items-center gap-3">{actions}</div>}
            </div>
          )}

          {children}
        </motion.div>
      </main>
    </div>
  );
}

// Simple page container without layout (for use in nested routes)
export function PageContainer({
  children,
  title,
  subtitle,
  actions,
}: PageWrapperProps) {
  return (
    <div className="mx-auto max-w-7xl">
      {(title || actions) && (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            {title && (
              <h1 className="text-xl font-semibold text-text-primary sm:text-2xl">
                {title}
              </h1>
            )}
            {subtitle && (
              <p className="mt-1 text-sm text-text-muted">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-3">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
