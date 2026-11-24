import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Briefcase,
  Cpu,
  Target,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Plus,
  Lock,
  Layers,
  Sparkles,
  ExternalLink,
  Download,
} from "lucide-react";
import {
  profilesApi,
  jobDescriptionsApi,
  resumesApi,
  systemApi,
} from "@/services/api";
import { useActiveProfile } from "@/context/ActiveProfileContext";

export const DashboardPage: React.FC = () => {
  const { activeProfileSlug, setActiveProfileSlug } = useActiveProfile();

  // 1. Fetch Profiles
  const {
    data: profilesData,
    isLoading: profilesLoading,
    error: profilesError,
  } = useQuery({
    queryKey: ["dashboard-profiles"],
    queryFn: () => profilesApi.list(1, 10, true),
  });

  // 2. Fetch Job Descriptions
  const {
    data: jdsData,
    isLoading: jdsLoading,
  } = useQuery({
    queryKey: ["dashboard-jds"],
    queryFn: () => jobDescriptionsApi.list(undefined, 1, 5),
  });

  // 3. Fetch Resumes
  const {
    data: resumesData,
    isLoading: resumesLoading,
  } = useQuery({
    queryKey: ["dashboard-resumes"],
    queryFn: () => resumesApi.list(undefined, undefined, 1, 5),
  });

  // 4. Fetch AI Providers Status
  const {
    data: providersData,
    isLoading: providersLoading,
  } = useQuery({
    queryKey: ["dashboard-providers"],
    queryFn: () => systemApi.getProvidersStatus(),
  });

  const profiles = profilesData?.items || [];
  const jds = jdsData?.items || [];
  const resumes = resumesData?.items || [];
  const approvedResumesCount = resumes.filter((r) => r.status === "approved").length;

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* Welcome & Quick Action Banner */}
      <div className="bg-gradient-to-r from-surface to-surface-elevated border border-surface-border rounded-xl p-6 sm:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-sm">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-brand-primary text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
            PostgreSQL 16 Connected · Real Database Active
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
            Candidate Resume Generation & ATS Platform
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary max-w-2xl leading-relaxed">
            Multi-profile management, deterministic job description analysis, explainable 45/25/20/10 project selection, and one-page ATS resume compilation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <Link
            to="/job-descriptions"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-surface-elevated hover:bg-surface-border border border-surface-border text-text-primary text-xs font-medium transition-colors shadow-2xs"
          >
            <Briefcase className="w-3.5 h-3.5 text-brand-primary" />
            <span>Add Job Description</span>
          </Link>
          <Link
            to="/builder"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Tailor Resume</span>
          </Link>
        </div>
      </div>

      {/* Live Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Profiles */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-2 hover:border-brand-primary/30 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Candidate Profiles</span>
            <Users className="w-4 h-4 text-brand-primary" />
          </div>
          <div className="text-2xl font-bold text-text-primary">
            {profilesLoading ? "..." : profilesData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted">
            {profiles.length > 0
              ? `${profiles.filter((p) => !p.is_synthetic).length} Verified, ${profiles.filter((p) => p.is_synthetic).length} Synthetic`
              : "PostgreSQL Database"}
          </p>
        </div>

        {/* Metric 2: Job Descriptions */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-2 hover:border-brand-primary/30 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Job Descriptions</span>
            <Briefcase className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-text-primary">
            {jdsLoading ? "..." : jdsData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted">Extracted requirement matrices</p>
        </div>

        {/* Metric 3: Resumes Generated */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-2 hover:border-brand-primary/30 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">Resumes & Versions</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-text-primary">
            {resumesLoading ? "..." : resumesData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted">
            {resumes.length > 0
              ? `${approvedResumesCount} Approved, ${resumes.length - approvedResumesCount} Drafts`
              : "Draft & Approved Manifests"}
          </p>
        </div>

        {/* Metric 4: AI Engine Cascade */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-2 hover:border-brand-primary/30 transition-colors">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-xs font-semibold uppercase tracking-wider">AI Fallback Engine</span>
            <Cpu className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-text-primary">
            {providersLoading ? "..." : `${providersData?.providers.length ?? 6} Tiers`}
          </div>
          <p className="text-xs text-text-muted truncate">
            Primary: {providersData?.primary_provider || "Offline Engine"}
          </p>
        </div>
      </div>

      {/* Candidate Profiles Overview Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-primary" />
              Candidate Profiles
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Profiles stored in PostgreSQL with complete verified credentials, skills, and projects
            </p>
          </div>
          <Link
            to="/profiles"
            className="text-xs text-brand-primary hover:text-brand-hover font-medium flex items-center gap-1"
          >
            <span>Manage All Profiles</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {profilesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-surface border border-surface-border rounded-xl p-6 h-40 animate-pulse" />
            <div className="bg-surface border border-surface-border rounded-xl p-6 h-40 animate-pulse" />
          </div>
        ) : profilesError ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center text-xs text-red-400">
            Failed to load candidate profiles from PostgreSQL API.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map((cand) => {
              const isSelected = cand.slug === activeProfileSlug;
              return (
                <div
                  key={cand.id}
                  className={`bg-surface border rounded-xl p-5 space-y-4 transition-all ${
                    isSelected
                      ? "border-brand-primary/50 shadow-xs ring-1 ring-brand-primary/20"
                      : "border-surface-border hover:border-surface-border/80"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                          cand.is_synthetic
                            ? "bg-purple-500/15 text-purple-400"
                            : "bg-emerald-500/15 text-emerald-400"
                        }`}
                      >
                        {cand.display_name?.charAt(0) || "U"}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-text-primary text-sm">
                            {cand.full_name}
                          </h4>
                          {isSelected && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-primary/10 text-brand-primary font-medium border border-brand-primary/20">
                              Active Context
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-text-muted font-mono">{cand.slug}</p>
                      </div>
                    </div>

                    {cand.is_synthetic ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        <Cpu className="w-3 h-3" />
                        Demo Candidate
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified Candidate
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-text-secondary space-y-1.5 border-t border-surface-border pt-3">
                    <div className="flex justify-between">
                      <span className="text-text-muted">Headline:</span>
                      <span className="text-text-primary font-medium truncate max-w-[240px]">
                        {cand.professional_headline || "Software Development Engineer"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Location:</span>
                      <span className="text-text-primary">{cand.location || "Pune, India"}</span>
                    </div>
                    {cand.slug === "sujal" && (
                      <div className="flex justify-between items-center text-emerald-400 font-medium">
                        <span className="text-text-muted">Pinned Rule:</span>
                        <span className="flex items-center gap-1 text-[11px]">
                          <Lock className="w-3 h-3 text-emerald-400" />
                          Bearing Fault Diagnosis (#2) Protected
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-surface-border">
                    <button
                      onClick={() => setActiveProfileSlug(cand.slug)}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors ${
                        isSelected
                          ? "bg-brand-primary text-white border-brand-primary"
                          : "bg-surface-elevated text-text-secondary hover:text-text-primary border-surface-border"
                      }`}
                    >
                      {isSelected ? "Active Profile" : "Select as Active"}
                    </button>
                    <Link
                      to="/profiles"
                      className="text-xs text-text-muted hover:text-brand-primary flex items-center gap-1"
                    >
                      <span>Edit Profile</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Grid: Recent Job Descriptions & Recent Resumes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Recent Target Job Descriptions */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-emerald-400" />
                Recent Target Job Descriptions
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Ingested job postings with extracted requirement matrices
              </p>
            </div>
            <Link
              to="/job-descriptions"
              className="text-xs text-brand-primary hover:text-brand-hover font-medium flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {jdsLoading ? (
            <div className="space-y-2">
              <div className="h-14 bg-surface-elevated rounded-lg animate-pulse" />
              <div className="h-14 bg-surface-elevated rounded-lg animate-pulse" />
            </div>
          ) : jds.length === 0 ? (
            <div className="border border-dashed border-surface-border rounded-lg p-6 text-center space-y-2">
              <Briefcase className="w-6 h-6 text-text-muted mx-auto" />
              <p className="text-xs font-medium text-text-primary">No Job Descriptions Added Yet</p>
              <p className="text-[11px] text-text-muted max-w-xs mx-auto">
                Paste target job descriptions to extract skill requirements and calculate candidate match scores.
              </p>
              <Link
                to="/job-descriptions"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border border border-surface-border text-xs text-text-primary font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Job Description</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {jds.map((jd) => (
                <div
                  key={jd.id}
                  className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 flex items-center justify-between hover:border-brand-primary/30 transition-colors"
                >
                  <div className="space-y-1 min-w-0 pr-2">
                    <div className="text-xs font-semibold text-text-primary truncate">
                      {jd.job_title || "Software Engineer"}
                    </div>
                    <div className="text-[11px] text-text-muted flex items-center gap-2">
                      <span className="text-text-secondary font-medium">{jd.company_name || "Company"}</span>
                      <span>·</span>
                      <span>{jd.extracted_skills?.length || 0} skills</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {jd.match_percentage !== null && jd.match_percentage !== undefined && (
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
                        {Math.round(jd.match_percentage)}% Match
                      </span>
                    )}
                    <Link
                      to="/job-descriptions"
                      className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-surface"
                      title="Inspect analysis"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Recent Tailored Resumes */}
        <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-primary" />
                Tailored Resumes
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Saved resume drafts and approved single-page versions
              </p>
            </div>
            <Link
              to="/resumes"
              className="text-xs text-brand-primary hover:text-brand-hover font-medium flex items-center gap-1"
            >
              <span>View Library</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {resumesLoading ? (
            <div className="space-y-2">
              <div className="h-14 bg-surface-elevated rounded-lg animate-pulse" />
              <div className="h-14 bg-surface-elevated rounded-lg animate-pulse" />
            </div>
          ) : resumes.length === 0 ? (
            <div className="border border-dashed border-surface-border rounded-lg p-6 text-center space-y-2">
              <FileText className="w-6 h-6 text-text-muted mx-auto" />
              <p className="text-xs font-medium text-text-primary">No Web Resumes Generated Yet</p>
              <p className="text-[11px] text-text-muted max-w-xs mx-auto">
                Generate your first tailored resume using the candidate profile and target job description.
              </p>
              <Link
                to="/builder"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Open Resume Builder</span>
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {resumes.map((res) => (
                <div
                  key={res.id}
                  className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 flex items-center justify-between hover:border-brand-primary/30 transition-colors"
                >
                  <div className="space-y-1 min-w-0 pr-2">
                    <div className="text-xs font-semibold text-text-primary truncate">
                      {res.resume_title}
                    </div>
                    <div className="text-[11px] text-text-muted flex items-center gap-2">
                      <span className="font-mono">v{res.current_version}</span>
                      <span>·</span>
                      <span
                        className={`font-medium ${
                          res.status === "approved" ? "text-emerald-400" : "text-amber-400"
                        }`}
                      >
                        {res.status === "approved" ? "Approved" : "Draft"}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {res.status === "approved" ? (
                      <a
                        href={resumesApi.getExportPdfUrl(res.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-2 py-1 rounded bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 text-xs font-medium border border-brand-primary/20"
                      >
                        <Download className="w-3 h-3" />
                        <span>PDF</span>
                      </a>
                    ) : (
                      <Link
                        to="/builder"
                        className="text-xs text-brand-primary hover:text-brand-hover font-medium flex items-center gap-1"
                      >
                        <span>Edit</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Multi-Provider AI Fallback Cascade Status */}
      <div className="bg-surface border border-surface-border rounded-xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-text-primary flex items-center gap-2">
              <Cpu className="w-4 h-4 text-brand-primary" />
              Multi-Provider AI Fallback Cascade
            </h3>
            <p className="text-xs text-text-muted mt-0.5">
              Live provider health and failover priority chain managed by the Python core engine
            </p>
          </div>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-surface-elevated border border-surface-border text-text-muted self-start sm:self-auto">
            Priority-Ranked Fallback
          </span>
        </div>

        {providersLoading ? (
          <div className="text-center py-6 text-xs text-text-muted">
            Checking AI provider connectivity...
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {providersData?.providers.map((p) => (
              <div
                key={p.provider}
                className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-2 hover:border-surface-border/90 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-xs text-text-primary flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded bg-surface border border-surface-border text-[10px] flex items-center justify-center font-bold text-text-muted">
                      #{p.priority_rank}
                    </span>
                    {p.provider}
                  </span>
                  {p.configured ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      Ready
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium text-text-muted">
                      <AlertCircle className="w-3 h-3" />
                      Fallback
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between text-[10px] text-text-muted border-t border-surface-border/50 pt-2">
                  <span>Auth: {p.auth_status}</span>
                  <span className="font-mono">{p.free_tier ? "Free Tier" : "Pay-Per-Token"}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
