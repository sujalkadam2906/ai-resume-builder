import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Settings,
  Shield,
  Server,
  HardDrive,
  Cpu,
  Sun,
  Moon,
  Monitor,
  CheckCircle2,
  Database,
  Lock,
  Sparkles,
} from "lucide-react";
import { systemApi, profilesApi } from "@/services/api";
import { useTheme } from "@/context/ThemeContext";
import { useActiveProfile } from "@/context/ActiveProfileContext";

export const SettingsPage: React.FC = () => {
  const { theme, effectiveTheme, setTheme } = useTheme();
  const { activeProfileSlug } = useActiveProfile();

  const { data: systemInfo } = useQuery({
    queryKey: ["systemInfo"],
    queryFn: systemApi.getSystemInfo,
  });

  const { data: readiness } = useQuery({
    queryKey: ["readiness"],
    queryFn: systemApi.getReadiness,
  });

  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: systemApi.getProvidersStatus,
  });

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16 font-sans">
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-[#B79A65] mb-1">
          Preferences & Runtime
        </div>
        <h2 className="font-serif text-2xl sm:text-3xl font-medium tracking-tight text-text-primary">
          Platform Settings
        </h2>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Configure application visual style, inspect infrastructure parameters, and review security boundaries.
        </p>
      </div>

      {/* Theme Preferences Card */}
      <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4 shadow-subtle">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div>
            <h3 className="font-serif text-base font-semibold text-text-primary">Theme Appearance</h3>
            <p className="text-xs text-text-muted mt-0.5">
              Select your preferred visual style. System mode matches your operating system theme.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-elevated text-text-muted border border-surface-border">
            Active: {effectiveTheme.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <button
            onClick={() => setTheme("light")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "light"
                ? "border-[#17263C] bg-[#17263C]/5 dark:border-[#B79A65] ring-1 ring-[#17263C] dark:ring-[#B79A65] shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Sun className={`w-5 h-5 ${theme === "light" ? "text-[#17263C]" : "text-text-muted"}`} />
              {theme === "light" && <CheckCircle2 className="w-4 h-4 text-[#315C4B]" />}
            </div>
            <div>
              <div className="font-semibold text-xs text-text-primary">Warm Ivory</div>
              <div className="text-[10px] text-text-muted">Editorial daytime palette</div>
            </div>
          </button>

          <button
            onClick={() => setTheme("dark")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "dark"
                ? "border-[#B79A65] bg-[#B79A65]/10 ring-1 ring-[#B79A65] shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Moon className={`w-5 h-5 ${theme === "dark" ? "text-[#B79A65]" : "text-text-muted"}`} />
              {theme === "dark" && <CheckCircle2 className="w-4 h-4 text-[#B79A65]" />}
            </div>
            <div>
              <div className="font-semibold text-xs text-text-primary">Deep Navy</div>
              <div className="text-[10px] text-text-muted">Executive midnight palette</div>
            </div>
          </button>

          <button
            onClick={() => setTheme("system")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "system"
                ? "border-[#17263C] dark:border-[#B79A65] bg-surface-elevated ring-1 ring-[#17263C] dark:ring-[#B79A65] shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Monitor className={`w-5 h-5 ${theme === "system" ? "text-text-primary" : "text-text-muted"}`} />
              {theme === "system" && <CheckCircle2 className="w-4 h-4 text-[#315C4B]" />}
            </div>
            <div>
              <div className="font-semibold text-xs text-text-primary">System Match</div>
              <div className="text-[10px] text-text-muted">Follows OS environment</div>
            </div>
          </button>
        </div>
      </div>

      {/* Backend Runtime Environment Card */}
      <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-subtle">
        <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
          <Server className="w-4 h-4 text-[#B79A65]" />
          <h3 className="font-serif text-base font-semibold text-text-primary">
            Infrastructure & Runtime Architecture
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-1">
            <span className="text-text-muted">Platform Service</span>
            <div className="text-text-primary font-medium">FormaCV Engine API</div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-1">
            <span className="text-text-muted">Python Version</span>
            <div className="text-text-primary font-medium">{systemInfo?.python_version || "Python 3.13"}</div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-1">
            <span className="text-text-muted">Typesetting Backend</span>
            <div className="text-text-primary font-medium">ReportLab Strict A4 + python-docx</div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-1">
            <span className="text-text-muted">Security Model</span>
            <div className="text-text-primary font-medium">Supabase JWT + Row-Level Security</div>
          </div>
        </div>

        {/* Security Parameters */}
        <div className="pt-2">
          <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
            <Shield className="w-4 h-4 text-[#315C4B] dark:text-[#88C4A6]" />
            <h4 className="font-semibold text-text-primary text-xs">Tenant Isolation & Privacy</h4>
          </div>

          <div className="text-xs text-text-secondary space-y-2 pt-2">
            <p className="leading-relaxed">
              Every resume manifest, target job description, and candidate profile is strictly isolated to the authenticated user. Row-level security on PostgreSQL guarantees zero cross-tenant data leakage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
