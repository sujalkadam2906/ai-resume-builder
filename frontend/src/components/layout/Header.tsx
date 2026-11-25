import React, { useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Menu,
  X,
  Sun,
  Moon,
  Monitor,
  Terminal,
  ChevronDown,
  Check,
  UserCheck,
  Shield,
  Plus,
  Copy,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { useActiveProfile } from "@/context/ActiveProfileContext";
import { profilesApi } from "@/services/api";

interface HeaderProps {
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onToggleMobileMenu,
  isMobileMenuOpen = false,
}) => {
  const location = useLocation();
  const { theme, effectiveTheme, setTheme } = useTheme();
  const { activeProfileSlug, setActiveProfileSlug } = useActiveProfile();
  const { user, signOut } = useAuth();
  const queryClient = useQueryClient();

  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch available candidate profiles
  const { data: profilesData } = useQuery({
    queryKey: ["profiles-list"],
    queryFn: () => profilesApi.list(1, 100, false),
  });

  const cloneMutation = useMutation({
    mutationFn: (slug: string) => profilesApi.clone(slug),
    onSuccess: (newProfile) => {
      queryClient.invalidateQueries({ queryKey: ["profiles-list"] });
      setActiveProfileSlug(newProfile.slug);
      setIsProfileDropdownOpen(false);
    },
    onError: (err: any) => alert(err.message),
  });

  const profiles = profilesData?.items || [];
  const activeProfile =
    profiles.find((p) => p.slug === activeProfileSlug) ||
    profiles.find((p) => !p.is_synthetic) ||
    profiles[0] || {
      id: "demo",
      slug: "demo_candidate",
      full_name: "Demo Candidate",
      display_name: "DEMO CANDIDATE",
      is_synthetic: true,
      is_archived: false,
      created_at: "",
      updated_at: "",
    };

  useEffect(() => {
    if (profiles.length > 0 && !profiles.some((p) => p.slug === activeProfileSlug)) {
      const preferred = profiles.find((p) => !p.is_synthetic) || profiles[0];
      setActiveProfileSlug(preferred.slug);
    }
  }, [profiles, activeProfileSlug, setActiveProfileSlug]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case "/":
        return "Workspace Overview";
      case "/profiles":
        return "Candidate Profiles Management";
      case "/job-descriptions":
        return "Target Job Descriptions";
      case "/builder":
        return "Resume Generation & Editor";
      case "/resumes":
      case "/history":
        return "Tailored Resume Library";
      case "/ats":
        return "ATS Heuristic Diagnostics";
      case "/settings":
        return "System & Provider Settings";
      default:
        return "Workspace";
    }
  };

  return (
    <header className="h-16 bg-surface border-b border-surface-border px-4 sm:px-8 flex items-center justify-between sticky top-0 z-20 backdrop-blur-md bg-opacity-90">
      {/* Left: Mobile hamburger & Page Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="flex items-center gap-2">
          <h1 className="text-sm sm:text-base font-semibold text-text-primary tracking-tight">
            {getPageTitle(location.pathname)}
          </h1>
          <span className="hidden sm:inline text-text-muted text-xs">/</span>
          <span className="hidden sm:inline text-xs text-text-muted font-medium">Personal SaaS</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* CLI Status */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-elevated border border-surface-border text-[11px] text-text-muted">
          <Terminal className="w-3.5 h-3.5 text-brand-primary" />
          <span className="font-mono">CLI Engine Ready</span>
        </div>

        {/* Theme Switcher Toggle */}
        <div className="flex items-center bg-surface-elevated border border-surface-border rounded-lg p-0.5">
          <button
            onClick={() => setTheme("light")}
            title="Light theme"
            className={`p-1.5 rounded-md text-xs transition-colors ${
              theme === "light"
                ? "bg-surface text-brand-primary shadow-xs font-semibold"
                : "text-text-muted hover:text-text-primary"
            }`}
          >
            <Sun className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setTheme("dark")}
            title="Dark theme"
            className={`p-1.5 rounded-md text-xs transition-colors ${
              theme === "dark"
                ? "bg-surface text-brand-primary shadow-xs font-semibold"
                : "text-text-muted hover:text-text-primary"
            }`}
          >
            <Moon className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setTheme("system")}
            title="System theme"
            className={`p-1.5 rounded-md text-xs transition-colors ${
              theme === "system"
                ? "bg-surface text-brand-primary shadow-xs font-semibold"
                : "text-text-muted hover:text-text-primary"
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Active Candidate Profile Switcher Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
            className="flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border border border-surface-border text-xs transition-all shadow-2xs"
          >
            <div className="w-6 h-6 rounded-full bg-brand-primary/15 text-brand-primary flex items-center justify-center font-bold text-xs">
              {activeProfile.display_name?.charAt(0) || activeProfile.full_name?.charAt(0) || "U"}
            </div>
            <div className="text-left hidden sm:block max-w-[120px] md:max-w-[160px]">
              <div className="text-text-primary font-medium text-xs truncate leading-none">
                {activeProfile.display_name || activeProfile.full_name}
              </div>
              <div className="text-[10px] text-text-muted leading-tight mt-0.5">
                {activeProfile.is_synthetic ? "Synthetic Profile" : "Verified Profile"}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-text-muted ml-0.5" />
          </button>

          {/* Dropdown Menu */}
          {isProfileDropdownOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-surface border border-surface-border rounded-xl shadow-xl py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-2 border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted flex items-center justify-between">
                <span>Switch Candidate</span>
                <span className="text-[10px] text-text-muted lowercase">PostgreSQL</span>
              </div>

              <div className="max-h-60 overflow-y-auto p-1 space-y-0.5">
                {profiles.map((p) => {
                  const isSelected = p.slug === activeProfileSlug;
                  return (
                    <button
                      key={p.id}
                      onClick={() => {
                        setActiveProfileSlug(p.slug);
                        setIsProfileDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left text-xs transition-colors ${
                        isSelected
                          ? "bg-brand-primary/10 text-brand-primary font-medium"
                          : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold ${
                            p.is_synthetic
                              ? "bg-purple-500/15 text-purple-400"
                              : "bg-emerald-500/15 text-emerald-400"
                          }`}
                        >
                          {p.display_name?.charAt(0) || "P"}
                        </div>
                        <div className="truncate">
                          <div className="text-text-primary font-medium truncate">{p.full_name}</div>
                          <div className="text-[10px] text-text-muted flex items-center gap-1">
                            <span>{p.slug}</span>
                            {p.is_synthetic ? (
                              <span className="text-[9px] px-1 rounded bg-purple-500/10 text-purple-400 font-mono">Template</span>
                            ) : (
                              <span className="text-[9px] px-1 rounded bg-emerald-500/10 text-emerald-400 font-mono">Personal</span>
                            )}
                          </div>
                        </div>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-brand-primary shrink-0" />}
                    </button>
                  );
                })}
              </div>

              {/* Quick Clone Template Action if active profile is a template */}
              {activeProfile.is_synthetic && (
                <div className="p-1 border-t border-surface-border">
                  <button
                    onClick={() => cloneMutation.mutate(activeProfile.slug)}
                    disabled={cloneMutation.isPending}
                    className="w-full flex items-center justify-center gap-2 px-2.5 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 text-xs font-medium transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>{cloneMutation.isPending ? "Cloning..." : "Clone Template to Workspace"}</span>
                  </button>
                </div>
              )}

              {/* User Account / Logout section */}
              {user && (
                <div className="mt-1 pt-1 border-t border-surface-border px-1">
                  <div className="px-2.5 py-1.5 text-[11px] text-text-muted truncate">
                    Signed in as <span className="font-medium text-text-secondary">{user.email}</span>
                  </div>
                  <button
                    onClick={() => {
                      setIsProfileDropdownOpen(false);
                      signOut();
                    }}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs text-red-500 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
