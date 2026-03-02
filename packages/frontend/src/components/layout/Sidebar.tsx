import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Boxes, LayoutDashboard, Search, Settings, ShieldAlert, X } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

const navItems = [
  { icon: LayoutDashboard, label: "Overview", path: "/" },
  { icon: ShieldAlert, label: "Alerts", path: "/alerts", hasBadge: true },
  { icon: Boxes, label: "Protocols", path: "/protocols" },
  { icon: Search, label: "Forensics", path: "/forensics" },
  { icon: Activity, label: "Live Feed", path: "/feed" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  alertCount?: number;
}

export function Sidebar({ open, onClose, alertCount = 0 }: SidebarProps) {
  const location = useLocation();

  const NavContent = ({ isMobile = false }: { isMobile?: boolean }) => (
    <nav className="flex flex-col gap-1 px-3 py-4">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive =
          location.pathname === item.path ||
          (item.path !== "/" && location.pathname.startsWith(item.path));
        const badge = item.hasBadge ? alertCount : 0;

        return (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={isMobile ? onClose : undefined}
            className={clsx(
              "group relative flex items-center justify-between overflow-hidden rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150",
              isActive
                ? "bg-white/[0.06] text-text-primary"
                : "text-text-secondary hover:bg-white/[0.03] hover:text-text-primary",
            )}
          >
            {isActive && (
              <span className="absolute bottom-1.5 left-0 top-1.5 w-1 rounded-r-full bg-accent" />
            )}

            <span className="flex items-center gap-3">
              <Icon
                className={clsx(
                  "h-[18px] w-[18px] transition-colors",
                  isActive
                    ? "text-text-primary"
                    : "text-text-muted group-hover:text-text-secondary",
                )}
              />
              <span>{item.label}</span>
            </span>

            {badge > 0 && (
              <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-threat-critical-muted px-1.5 text-2xs font-semibold text-red-300">
                {badge > 99 ? "99+" : badge}
              </span>
            )}
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="fixed bottom-0 left-0 top-16 z-30 hidden w-64 border-r border-border-subtle bg-bg-surface/95 backdrop-blur-sm lg:block">
        <NavContent />

        {/* Bottom section with status */}
        <div className="absolute bottom-0 left-0 right-0 border-t border-border-subtle p-4">
          <div className="flex items-center gap-3 rounded-lg bg-success-muted/30 px-3 py-2.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </span>
            <div className="flex-1">
              <p className="text-xs font-medium text-success">System Operational</p>
              <p className="text-2xs text-text-muted">All sentinels active</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={onClose}
            />

            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
              className="fixed bottom-0 left-0 top-0 z-50 w-72 border-r border-border-subtle bg-bg-surface lg:hidden"
            >
              {/* Mobile header */}
              <div className="flex h-16 items-center justify-between border-b border-border-subtle px-4">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-subtle bg-bg-elevated">
                    <ShieldAlert className="h-5 w-5 text-accent" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold tracking-wide text-text-primary">AEGIS</p>
                    <p className="text-2xs text-text-muted">Security Command</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-lg p-2 text-text-muted transition hover:bg-bg-elevated hover:text-text-primary"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <NavContent isMobile />

              {/* Mobile bottom status */}
              <div className="absolute bottom-0 left-0 right-0 border-t border-border-subtle p-4">
                <div className="flex items-center gap-3 rounded-lg bg-success-muted/30 px-3 py-2.5">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                  </span>
                  <p className="text-xs font-medium text-success">System Operational</p>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
