import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Briefcase,
  PenTool,
  ArrowRight,
  CheckCircle2,
  FileText,
  Plus,
  Download,
  Target,
  Sparkles,
  ChevronRight,
  Layers,
} from "lucide-react";
import {
  profilesApi,
  jobDescriptionsApi,
  resumesApi,
} from "@/services/api";
import { useAuth } from "@/context/AuthContext";
import { useActiveProfile } from "@/context/ActiveProfileContext";

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { activeProfileSlug, setActiveProfileSlug } = useActiveProfile();

  // Fetch Profiles
  const { data: profilesData, isLoading: profilesLoading } = useQuery({
    queryKey: ["dashboard-profiles"],
    queryFn: () => profilesApi.list(1, 10, false),
  });

  // Fetch Job Descriptions
  const { data: jdsData, isLoading: jdsLoading } = useQuery({
    queryKey: ["dashboard-jds"],
    queryFn: () => jobDescriptionsApi.list(undefined, 1, 10),
  });

  // Fetch Resumes
  const { data: resumesData, isLoading: resumesLoading } = useQuery({
    queryKey: ["dashboard-resumes"],
    queryFn: () => resumesApi.list(undefined, undefined, 1, 10),
  });

  const profiles = profilesData?.items || [];
  const jds = jdsData?.items || [];
  const resumes = resumesData?.items || [];

  const userName =
    user?.user_metadata?.full_name ||
    user?.email?.split("@")[0] ||
    "Professional";

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16 font-sans">
      {/* Editorial Welcome Header */}
      <div className="bg-surface rounded-2xl p-6 sm:p-10 border border-surface-border shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="space-y-2 max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#B79A65]/30 bg-[#B79A65]/10 text-[#8F7546] dark:text-[#D4BC8B] text-xs font-semibold tracking-wide">
            <Sparkles className="w-3.5 h-3.5" />
            <span>FormaCV Executive Workspace</span>
          </div>
          <h1 className="font-serif text-2xl sm:text-4xl font-medium tracking-tight text-text-primary">
            {getGreeting()}, <span className="capitalize">{userName}</span>.
          </h1>
          <p className="text-sm text-text-secondary leading-relaxed">
            Craft a career that gets noticed. Tailor your verified accomplishments to target opportunities with deterministic ATS precision.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0 relative z-10 w-full md:w-auto">
          <Link
            to="/builder"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold bg-[#17263C] text-white hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] dark:hover:bg-white shadow-card hover:shadow-elevated transition-all"
          >
            <PenTool className="w-4 h-4" />
            <span>Tailor New Resume</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>
      </div>

      {/* Key Metric Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-surface rounded-xl p-5 border border-surface-border shadow-subtle hover:border-[#B79A65]/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tailored Resumes</span>
            <FileText className="w-4 h-4 text-[#315C4B] dark:text-[#88C4A6]" />
          </div>
          <div className="text-3xl font-serif font-bold text-text-primary">
            {resumesLoading ? "—" : resumesData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted mt-1">
            {resumes.filter((r) => r.status === "approved").length} approved executive manifests
          </p>
        </div>

        <div className="bg-surface rounded-xl p-5 border border-surface-border shadow-subtle hover:border-[#B79A65]/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Candidate Profiles</span>
            <Users className="w-4 h-4 text-[#17263C] dark:text-[#B79A65]" />
          </div>
          <div className="text-3xl font-serif font-bold text-text-primary">
            {profilesLoading ? "—" : profilesData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted mt-1">
            {profiles.filter((p) => !p.is_synthetic).length} personal, {profiles.filter((p) => p.is_synthetic).length} shared demo
          </p>
        </div>

        <div className="bg-surface rounded-xl p-5 border border-surface-border shadow-subtle hover:border-[#B79A65]/40 transition-colors">
          <div className="flex items-center justify-between text-text-muted mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Target JDs Analyzed</span>
            <Briefcase className="w-4 h-4 text-[#B79A65]" />
          </div>
          <div className="text-3xl font-serif font-bold text-text-primary">
            {jdsLoading ? "—" : jdsData?.total ?? 0}
          </div>
          <p className="text-xs text-text-muted mt-1">Structured keyword match matrices</p>
        </div>
      </div>

      {/* Primary Workflow Actions (3 Core Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Workflow 1: Tailor Resume */}
        <Link
          to="/builder"
          className="group bg-surface rounded-xl p-6 border border-surface-border shadow-subtle hover:shadow-card hover:border-[#B79A65]/40 transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-[#17263C] text-white dark:bg-[#F7F5F0] dark:text-[#101B2B] flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <PenTool className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-lg font-semibold text-text-primary mb-1.5 flex items-center justify-between">
              <span>Resume Tailoring</span>
              <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Synthesize a targeted, single-page A4 resume tailored specifically to an active job description.
            </p>
          </div>
          <div className="mt-5 pt-4 border-t border-surface-border text-xs font-semibold text-[#315C4B] dark:text-[#88C4A6]">
            Start Tailoring →
          </div>
        </Link>

        {/* Workflow 2: Profiles */}
        <Link
          to="/profiles"
          className="group bg-surface rounded-xl p-6 border border-surface-border shadow-subtle hover:shadow-card hover:border-[#B79A65]/40 transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-[#315C4B] text-white flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-lg font-semibold text-text-primary mb-1.5 flex items-center justify-between">
              <span>Candidate Profiles</span>
              <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Manage your verified career repository: projects, experiences, skills, education, and credentials.
            </p>
          </div>
          <div className="mt-5 pt-4 border-t border-surface-border text-xs font-semibold text-[#315C4B] dark:text-[#88C4A6]">
            Manage Accomplishments →
          </div>
        </Link>

        {/* Workflow 3: Target JDs */}
        <Link
          to="/job-descriptions"
          className="group bg-surface rounded-xl p-6 border border-surface-border shadow-subtle hover:shadow-card hover:border-[#B79A65]/40 transition-all flex flex-col justify-between"
        >
          <div>
            <div className="w-10 h-10 rounded-lg bg-[#101B2B] text-white flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
              <Briefcase className="w-5 h-5 text-[#B79A65]" />
            </div>
            <h3 className="font-serif text-lg font-semibold text-text-primary mb-1.5 flex items-center justify-between">
              <span>Target Opportunities</span>
              <ChevronRight className="w-4 h-4 text-text-muted group-hover:translate-x-1 transition-transform" />
            </h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Ingest job postings, extract semantic skill markers, and evaluate ATS compatibility before applying.
            </p>
          </div>
          <div className="mt-5 pt-4 border-t border-surface-border text-xs font-semibold text-[#315C4B] dark:text-[#88C4A6]">
            View Opportunities →
          </div>
        </Link>
      </div>

      {/* Recent Tailored Resumes Section */}
      <div className="bg-surface rounded-2xl p-6 sm:p-8 border border-surface-border shadow-card">
        <div className="flex items-center justify-between pb-6 border-b border-surface-border">
          <div>
            <h2 className="font-serif text-xl font-medium text-text-primary">
              Recent Tailored Resumes
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Review, edit, and export your tailored single-page documents
            </p>
          </div>
          <Link
            to="/resumes"
            className="text-xs font-semibold text-[#315C4B] dark:text-[#88C4A6] hover:underline flex items-center gap-1"
          >
            <span>View All Library</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {resumesLoading ? (
          <div className="py-12 text-center text-xs text-text-muted">
            <div className="w-6 h-6 border-2 border-[#17263C] dark:border-[#B79A65] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading recent manifests...
          </div>
        ) : resumes.length === 0 ? (
          /* Premium Empty State */
          <div className="py-12 text-center max-w-md mx-auto">
            <div className="w-12 h-12 rounded-full bg-[#B79A65]/15 text-[#8F7546] dark:text-[#D4BC8B] flex items-center justify-center mx-auto mb-4">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-serif text-lg font-semibold text-text-primary">
              No tailored resumes generated yet
            </h3>
            <p className="text-xs text-text-secondary mt-2 leading-relaxed">
              Select your candidate profile, supply a job description, and FormaCV will synthesize a tailored single-page resume with ATS validation.
            </p>
            <div className="mt-6">
              <Link
                to="/builder"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-[#17263C] text-white hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] shadow-sm transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Your First Resume</span>
              </Link>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-surface-border">
            {resumes.slice(0, 5).map((resume) => (
              <div
                key={resume.id}
                className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-surface-elevated/40 px-2 rounded-lg transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-[#17263C]/10 dark:bg-white/10 text-text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-text-primary">
                      {resume.resume_title || resume.editable_manifest?.target_role || "Tailored Resume"}
                    </div>
                    <div className="text-xs text-text-muted flex items-center gap-2 mt-0.5">
                      <span>{resume.editable_manifest?.personal_info?.full_name || resume.editable_manifest?.target_company || "Candidate"}</span>
                      <span>·</span>
                      <span>v{resume.current_version}</span>
                      <span>·</span>
                      <span className="capitalize">{resume.status}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
                  <Link
                    to={`/builder?resume_id=${resume.id}`}
                    className="px-3 py-1.5 rounded-md text-xs font-medium border border-surface-border bg-surface hover:bg-surface-elevated text-text-primary transition-colors"
                  >
                    Open Editor
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
