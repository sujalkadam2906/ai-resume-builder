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
  X,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { FormaLogo } from "@/components/brand/FormaLogo";

interface SidebarProps {
  apiReady: boolean;
  primaryProvider?: string;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const navItems = [
  { name: "Workspace", href: "/dashboard", icon: LayoutDashboard },
  { name: "Candidate Profiles", href: "/profiles", icon: Users },
  { name: "Job Descriptions", href: "/job-descriptions", icon: Briefcase },
  { name: "Resume Builder", href: "/builder", icon: PenTool },
  { name: "Resume Library", href: "/resumes", icon: Archive },
  { name: "ATS Diagnostics", href: "/ats", icon: Target },
  { name: "Settings", href: "/settings", icon: Settings },
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
          "w-64 bg-surface border-r border-surface-border flex flex-col justify-between shrink-0 h-screen sticky top-0 z-50 transition-transform duration-200 ease-in-out font-sans",
          "fixed lg:static top-0 left-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div>
          {/* Brand Header */}
          <div className="h-20 flex items-center justify-between px-6 border-b border-surface-border">
            <NavLink to="/" className="flex items-center">
              <FormaLogo size="md" />
            </NavLink>

            {/* Mobile close button */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-elevated"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items */}
          <div className="p-4 space-y-1">
            <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-[#B79A65]">
              Editorial Suite
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
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all",
                      isActive
                        ? "bg-[#17263C] text-white dark:bg-[#F7F5F0] dark:text-[#101B2B] font-semibold shadow-xs"
                        : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated"
                    )
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* System & Architecture Status Footer */}
        <div className="p-4 border-t border-surface-border bg-surface-elevated/40">
          <div className="rounded-xl border border-surface-border p-3.5 bg-surface text-left">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                Engine Status
              </span>
              <span className="flex items-center gap-1.5 text-[11px] font-semibold text-[#315C4B] dark:text-[#45826A]">
                <span className="w-2 h-2 rounded-full bg-[#315C4B] dark:bg-[#45826A] animate-pulse" />
                {apiReady ? "Active" : "Connecting"}
              </span>
            </div>

            <div className="mt-2 text-[11px] text-text-secondary flex items-center justify-between">
              <span className="text-text-muted">A4 Engine:</span>
              <span className="font-mono text-text-primary font-medium">ReportLab Strict</span>
            </div>

            {primaryProvider && (
              <div className="mt-1 text-[11px] text-text-secondary flex items-center justify-between">
                <span className="text-text-muted">AI Provider:</span>
                <span className="font-mono text-text-primary capitalize text-[10px] bg-background px-1.5 py-0.5 rounded border border-surface-border">
                  {primaryProvider}
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
