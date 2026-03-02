import { useMemo, useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, CheckCheck, Menu, Shield, X } from "lucide-react";
import { Link } from "react-router-dom";
import { useAlerts, formatRelativeTime, isEscalatedThreat } from "../../hooks/useAlerts";
import { ThreatBadge } from "../common/ThreatBadge";
import { ConnectButton } from "../wallet/ConnectButton";

interface HeaderProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export function Header({ sidebarOpen, onToggleSidebar }: HeaderProps) {
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [readAlertIds, setReadAlertIds] = useState<Set<string>>(new Set());
  const notificationRef = useRef<HTMLDivElement>(null);

  const { data: alerts } = useAlerts({ page: 1, limit: 10, refetchInterval: 10_000 });

  const recentEscalated = useMemo(
    () => (alerts?.items ?? []).filter((item) => isEscalatedThreat(item.threatLevel)).slice(0, 5),
    [alerts]
  );

  const unreadCount = useMemo(
    () => recentEscalated.filter((alert) => !readAlertIds.has(alert.id)).length,
    [recentEscalated, readAlertIds]
  );

  function markAllAsRead() {
    setReadAlertIds((current) => {
      const next = new Set(current);
      for (const alert of recentEscalated) {
        next.add(alert.id);
      }
      return next;
    });
  }

  // Close notifications on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-40 h-16 border-b border-border-subtle bg-bg-base/90 backdrop-blur-md">
      <div className="flex h-full items-center justify-between px-4 lg:px-6">
        {/* Left section */}
        <div className="flex items-center gap-4">
          {/* Mobile menu toggle */}
          <button
            type="button"
            onClick={onToggleSidebar}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-subtle bg-bg-surface text-text-secondary transition hover:bg-bg-elevated hover:text-text-primary lg:hidden"
            aria-label="Toggle menu"
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>

          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-subtle bg-gradient-to-br from-bg-surface to-bg-elevated">
              <Shield className="h-5 w-5 text-accent" />
            </span>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold tracking-[0.1em] text-text-primary">AEGIS</p>
              <p className="text-2xs text-text-muted">Security Command Center</p>
            </div>
          </Link>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative" ref={notificationRef}>
            <button
              type="button"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-border-subtle bg-bg-surface text-text-secondary transition hover:border-border-muted hover:bg-bg-elevated hover:text-text-primary"
              aria-label="Notifications"
            >
              <Bell className="h-[18px] w-[18px]" />
              {unreadCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-threat-critical px-1 text-2xs font-semibold text-white">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>

            <AnimatePresence>
              {notificationsOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -4, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-border-subtle bg-bg-overlay p-1 shadow-dropdown"
                >
                  <div className="flex items-center justify-between px-3 py-2.5">
                    <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
                    <div className="flex items-center gap-2">
                      {unreadCount > 0 && (
                        <span className="rounded-full bg-threat-critical-muted/50 px-2 py-0.5 text-2xs font-medium text-red-300">
                          {unreadCount} new
                        </span>
                      )}
                      {recentEscalated.length > 0 && unreadCount > 0 && (
                        <button
                          type="button"
                          onClick={markAllAsRead}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-2xs font-medium text-text-secondary transition hover:bg-white/[0.05] hover:text-text-primary"
                        >
                          <CheckCheck className="h-3.5 w-3.5" />
                          Mark as read
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="max-h-80 overflow-y-auto">
                    {recentEscalated.length === 0 ? (
                      <div className="px-3 py-8 text-center">
                        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-bg-surface">
                          <Bell className="h-5 w-5 text-text-muted" />
                        </div>
                        <p className="text-sm text-text-secondary">No critical alerts</p>
                        <p className="text-xs text-text-muted">All systems operating normally</p>
                      </div>
                    ) : (
                      <div className="space-y-1 p-1">
                        {recentEscalated.map((alert) => (
                          <Link
                            key={alert.id}
                            to={`/alerts?id=${alert.id}`}
                            onClick={() => {
                              setReadAlertIds((current) => new Set(current).add(alert.id));
                              setNotificationsOpen(false);
                            }}
                            className="block rounded-lg p-3 transition hover:bg-white/[0.03]"
                          >
                            <div className="mb-2 flex items-center justify-between">
                              <ThreatBadge level={alert.threatLevel} variant="compact" />
                              <time className="text-2xs text-text-muted">
                                {formatRelativeTime(alert.createdAt)}
                              </time>
                            </div>
                            <p className="mb-1 truncate text-sm font-medium text-text-primary">
                              {alert.protocolName}
                            </p>
                            <p className="text-xs text-text-secondary">
                              Action: {alert.action.replace(/_/g, " ")}
                            </p>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>

                  {recentEscalated.length > 0 && (
                    <div className="border-t border-border-subtle p-2">
                      <Link
                        to="/alerts"
                        onClick={() => setNotificationsOpen(false)}
                        className="block rounded-lg px-3 py-2 text-center text-xs font-medium text-accent transition hover:bg-white/[0.03]"
                      >
                        View all alerts
                      </Link>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Wallet */}
          <ConnectButton />
        </div>
      </div>
    </header>
  );
}
