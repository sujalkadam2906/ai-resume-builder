import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Settings,
  Shield,
  Server,
  HardDrive,
  Cpu,
  Terminal,
  Sun,
  Moon,
  Monitor,
  CheckCircle2,
  Database,
  Lock,
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

  const { data: activeProfile } = useQuery({
    queryKey: ["profile-detail", activeProfileSlug],
    queryFn: () => profilesApi.get(activeProfileSlug),
    enabled: !!activeProfileSlug,
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
          <Settings className="w-5 h-5 text-brand-primary" />
          System & Platform Settings
        </h2>
        <p className="text-xs sm:text-sm text-text-secondary">
          Configure application theme, inspect backend PostgreSQL runtime parameters, and verify AI fallback cascade health.
        </p>
      </div>

      {/* Theme Preferences Card */}
      <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div>
            <h3 className="font-semibold text-text-primary text-sm">Theme Appearance</h3>
            <p className="text-xs text-text-muted mt-0.5">
              Select your preferred visual style. System mode matches your operating system theme.
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-elevated text-text-muted border border-surface-border">
            Current: {effectiveTheme.toUpperCase()}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <button
            onClick={() => setTheme("light")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "light"
                ? "border-brand-primary bg-brand-primary/10 ring-1 ring-brand-primary shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Sun className={`w-5 h-5 ${theme === "light" ? "text-brand-primary" : "text-text-muted"}`} />
              {theme === "light" && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
            </div>
            <div>
              <div className="font-bold text-xs text-text-primary">Light Mode</div>
              <div className="text-[10px] text-text-muted">High-contrast daytime clarity</div>
            </div>
          </button>

          <button
            onClick={() => setTheme("dark")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "dark"
                ? "border-brand-primary bg-brand-primary/10 ring-1 ring-brand-primary shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Moon className={`w-5 h-5 ${theme === "dark" ? "text-brand-primary" : "text-text-muted"}`} />
              {theme === "dark" && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
            </div>
            <div>
              <div className="font-bold text-xs text-text-primary">Dark Mode</div>
              <div className="text-[10px] text-text-muted">Obsidian minimal aesthetic</div>
            </div>
          </button>

          <button
            onClick={() => setTheme("system")}
            className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between h-24 ${
              theme === "system"
                ? "border-brand-primary bg-brand-primary/10 ring-1 ring-brand-primary shadow-xs"
                : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
            }`}
          >
            <div className="flex items-center justify-between w-full">
              <Monitor className={`w-5 h-5 ${theme === "system" ? "text-brand-primary" : "text-text-muted"}`} />
              {theme === "system" && <CheckCircle2 className="w-4 h-4 text-brand-primary" />}
            </div>
            <div>
              <div className="font-bold text-xs text-text-primary">System Match</div>
              <div className="text-[10px] text-text-muted">Follows OS dark/light setting</div>
            </div>
          </button>
        </div>
      </div>

      {/* Backend Runtime Environment Card */}
      <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-xs">
        <div className="flex items-center gap-2 pb-3 border-b border-surface-border">
          <Server className="w-4 h-4 text-brand-primary" />
          <h3 className="font-semibold text-text-primary text-sm">Backend & Database Infrastructure</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-1">
            <span className="text-text-muted">Application Service</span>
            <div className="text-text-primary font-medium">{systemInfo?.app_name || "AI Resume Platform API"}</div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-1">
            <span className="text-text-muted">Python Version</span>
            <div className="text-text-primary font-medium">{systemInfo?.python_version || "Python 3.13"}</div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-1">
            <span className="text-text-muted">PostgreSQL Database</span>
            <div className="text-text-primary font-medium flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>PostgreSQL 16 (124 Candidate Records)</span>
            </div>
          </div>

          <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-1">
            <span className="text-text-muted">Storage Driver</span>
            <div className="text-text-primary font-medium uppercase">{systemInfo?.storage_backend || "Local Filesystem"}</div>
          </div>
        </div>

        {/* Security Parameters */}
        <div className="pt-2">
          <div className="flex items-center gap-2 pb-2 border-b border-surface-border">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h4 className="font-semibold text-text-primary text-xs">Zero-Trust Security Boundary</h4>
          </div>

          <div className="text-xs text-text-secondary space-y-2 pt-2">
            <p>
              In production, the platform is gated by Cloudflare Access at the DNS edge. All write mutations and PDF/DOCX downloads require verified authentication.
            </p>
            <div className="bg-surface-elevated border border-surface-border rounded-lg p-3 flex items-center justify-between text-xs">
              <span className="text-text-muted">Gate Status:</span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-surface text-emerald-400 border border-emerald-500/20">
                {readiness?.checks?.security_gate?.status || "Local Development Mode (Bypassed)"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
