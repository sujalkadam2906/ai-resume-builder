import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  PenTool,
  Archive,
  Target,
  Settings,
  ShieldCheck,
  Cpu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  apiReady: boolean;
  primaryProvider?: string;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Candidate Profiles", href: "/profiles", icon: Users },
  { name: "Job Descriptions", href: "/job-descriptions", icon: Briefcase },
  { name: "Resume Builder", href: "/builder", icon: PenTool },
  { name: "Resume Library", href: "/resumes", icon: Archive },
  { name: "ATS Diagnostics", href: "/ats", icon: Target },
  { name: "System Settings", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  apiReady,
  primaryProvider,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 lg:hidden"
        />
      )}

      {/* Main Sidebar Panel */}
      <aside
        className={cn(
          "w-64 bg-surface border-r border-surface-border flex flex-col justify-between shrink-0 h-screen sticky top-0 z-50 transition-transform duration-200 ease-in-out",
          // Mobile responsive drawer classes
          "fixed lg:static top-0 left-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div>
          {/* Brand / Logo */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-surface-border">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-primary/10 border border-brand-primary/30 flex items-center justify-center text-brand-primary font-bold shadow-xs">
                <Cpu className="w-4 h-4 text-brand-primary" />
              </div>
              <div>
                <div className="text-sm font-semibold tracking-tight text-text-primary">
                  AI Resume Platform
                </div>
                <div className="text-[11px] text-text-muted flex items-center gap-1">
                  <span>FastAPI + PG16</span>
                  <span className="text-[9px] px-1 py-0.2 rounded bg-surface-elevated text-brand-primary border border-surface-border">
                    v1.0
                  </span>
                </div>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-elevated"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation Items */}
          <div className="p-4 space-y-1">
            <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Core Workflows
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={onCloseMobile}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs sm:text-sm font-medium transition-all group",
                      isActive
                        ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/25 shadow-xs font-semibold"
                        : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated"
                    )
                  }
                >
                  <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-105" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* Footer / Status Card */}
        <div className="p-4 border-t border-surface-border">
          <div className="bg-surface-elevated/70 border border-surface-border rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-secondary font-medium flex items-center gap-1.5 text-[11px]">
                <ShieldCheck className="w-3.5 h-3.5 text-brand-secondary" />
                Backend API
              </span>
              <span
                className={cn(
                  "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium tracking-wide font-mono",
                  apiReady
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                )}
              >
                {apiReady ? "CONNECTED" : "OFFLINE"}
              </span>
            </div>

            <div className="text-[11px] text-text-muted">
              <div className="truncate">
                Primary:{" "}
                <span className="text-text-primary font-medium">
                  {primaryProvider || "Offline Engine"}
                </span>
              </div>
              <div className="text-[10px] text-text-muted/80 mt-0.5">
                PostgreSQL · 124 Records
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
