import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Briefcase,
  Plus,
  Trash2,
  Cpu,
  Target,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Layers,
  Search,
  ArrowRight,
  Info,
  X,
  FileText,
  Clock,
  Building,
} from "lucide-react";
import { jobDescriptionsApi, profilesApi } from "@/services/api";
import { useActiveProfile } from "@/context/ActiveProfileContext";
import type {
  JobDescriptionResponse,
  JobDescriptionAnalysisResponse,
  CandidateMatchResponse,
  JobDescriptionCreate,
} from "@/types/api";

export const JobDescriptionsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { activeProfileSlug } = useActiveProfile();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedJdId, setSelectedJdId] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // 1. Fetch Job Descriptions
  const {
    data: jdsData,
    isLoading: jdsLoading,
  } = useQuery({
    queryKey: ["job-descriptions-list"],
    queryFn: () => jobDescriptionsApi.list(undefined, 1, 100),
  });

  const jds = jdsData?.items || [];
  const filteredJds = jds.filter((jd) => {
    const q = searchQuery.toLowerCase();
    return (
      (jd.job_title && jd.job_title.toLowerCase().includes(q)) ||
      (jd.company_name && jd.company_name.toLowerCase().includes(q)) ||
      jd.raw_text.toLowerCase().includes(q)
    );
  });

  // Default selection to first JD if none selected
  const activeJd =
    jds.find((j) => j.id === selectedJdId) || (filteredJds.length > 0 ? filteredJds[0] : null);

  // 2. Fetch Analysis for the active JD
  const {
    data: analysisData,
    isLoading: analysisLoading,
    refetch: refetchAnalysis,
  } = useQuery({
    queryKey: ["jd-analysis", activeJd?.id],
    queryFn: () => jobDescriptionsApi.getAnalysis(activeJd!.id),
    enabled: !!activeJd,
    retry: false,
  });

  // 3. Fetch Candidate Matching for active JD & active candidate
  const {
    data: matchData,
    isLoading: matchLoading,
    refetch: refetchMatch,
  } = useQuery({
    queryKey: ["jd-match", activeJd?.id, activeProfileSlug],
    queryFn: () => jobDescriptionsApi.matchCandidate(activeJd!.id, activeProfileSlug),
    enabled: !!activeJd && !!activeProfileSlug,
    retry: false,
  });

  // Mutations
  const analyzeMutation = useMutation({
    mutationFn: (jdId: string) => jobDescriptionsApi.analyze(jdId, activeProfileSlug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jd-analysis", activeJd?.id] });
      queryClient.invalidateQueries({ queryKey: ["jd-match", activeJd?.id, activeProfileSlug] });
      queryClient.invalidateQueries({ queryKey: ["job-descriptions-list"] });
    },
    onError: (err: any) => {
      alert(`Analysis failed: ${err.message}`);
    },
  });

  const deleteJdMutation = useMutation({
    mutationFn: (jdId: string) => jobDescriptionsApi.delete(jdId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-descriptions-list"] });
      setSelectedJdId(null);
    },
    onError: (err: any) => {
      alert(`Delete failed: ${err.message}`);
    },
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-text-primary flex items-center gap-2.5">
            <Briefcase className="w-6 h-6 text-forma-emerald" />
            <span>Target Job Descriptions</span>
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Ingest target postings, extract structured requirement matrices, and calculate explainable project rankings.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-forma bg-forma-navy hover:bg-forma-deep-navy dark:bg-forma-emerald dark:hover:bg-forma-emerald-hover text-white text-xs font-semibold transition-all shadow-subtle hover:shadow-card"
        >
          <Plus className="w-4 h-4" />
          <span>Add Job Description</span>
        </button>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Job Description Sidebar / List (4 cols) */}
        <div className="lg:col-span-4 bg-surface border border-surface-border rounded-xl p-4 space-y-3">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search postings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted flex items-center justify-between pt-1">
            <span>Saved Postings</span>
            <span className="font-mono">{filteredJds.length}</span>
          </div>

          {jdsLoading ? (
            <div className="space-y-2">
              <div className="h-16 bg-surface-elevated rounded-lg animate-pulse" />
              <div className="h-16 bg-surface-elevated rounded-lg animate-pulse" />
            </div>
          ) : filteredJds.length === 0 ? (
            <div className="border border-dashed border-surface-border rounded-lg p-6 text-center space-y-2">
              <Briefcase className="w-6 h-6 text-text-muted mx-auto" />
              <p className="text-xs text-text-muted">No job descriptions found.</p>
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="text-xs text-brand-primary hover:underline font-medium"
              >
                Create your first posting
              </button>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredJds.map((jd) => {
                const isSelected = activeJd?.id === jd.id;
                return (
                  <button
                    key={jd.id}
                    onClick={() => setSelectedJdId(jd.id)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? "bg-brand-primary/10 border-brand-primary/40 shadow-xs"
                        : "bg-surface-elevated/60 hover:bg-surface-elevated border-surface-border"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-text-primary truncate">
                          {jd.job_title || "Software Engineer"}
                        </div>
                        <div className="text-[11px] text-text-muted flex items-center gap-1.5 mt-0.5">
                          <Building className="w-3 h-3 text-text-secondary" />
                          <span className="truncate">{jd.company_name || "Company"}</span>
                        </div>
                      </div>
                      {jd.match_percentage !== null && jd.match_percentage !== undefined && (
                        <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-brand-primary/10 text-brand-primary shrink-0 border border-brand-primary/20">
                          {Math.round(jd.match_percentage)}%
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-text-muted pt-2 border-t border-surface-border/50 mt-2">
                      <span>{jd.extracted_skills?.length || 0} skills extracted</span>
                      <span>{new Date(jd.created_at).toLocaleDateString()}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Detailed Workspace & Analysis (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {!activeJd ? (
            <div className="bg-surface border border-surface-border rounded-xl p-12 text-center space-y-3">
              <Briefcase className="w-10 h-10 text-text-muted mx-auto" />
              <h3 className="text-sm font-semibold text-text-primary">No Job Description Selected</h3>
              <p className="text-xs text-text-muted max-w-sm mx-auto">
                Select a saved posting from the sidebar or click "Add Job Description" to paste a new posting.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Active JD Summary Card */}
              <div className="bg-surface border border-surface-border rounded-xl p-5 sm:p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base sm:text-lg font-bold text-text-primary">
                        {activeJd.job_title || "Target Position"}
                      </h3>
                      {activeJd.source_url && (
                        <a
                          href={activeJd.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-text-muted hover:text-brand-primary p-1"
                          title="Open original job posting"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>
                    <div className="text-xs text-text-secondary flex items-center gap-2">
                      <span className="font-semibold text-text-primary">
                        {activeJd.company_name || "Company Unspecified"}
                      </span>
                      <span>·</span>
                      <span className="text-text-muted">
                        Added {new Date(activeJd.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => analyzeMutation.mutate(activeJd.id)}
                      disabled={analyzeMutation.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-medium border border-surface-border transition-colors"
                    >
                      <Cpu className="w-3.5 h-3.5 text-brand-primary" />
                      <span>{analyzeMutation.isPending ? "Analyzing..." : "Analyze Requirements"}</span>
                    </button>

                    <Link
                      to={`/builder?jd_id=${activeJd.id}&profile_id=${activeProfileSlug}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Tailor Resume</span>
                    </Link>

                    <button
                      onClick={() => {
                        if (confirm(`Delete this job description?`)) {
                          deleteJdMutation.mutate(activeJd.id);
                        }
                      }}
                      className="p-1.5 rounded-lg text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      title="Delete Posting"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Candidate Match Score Bar */}
                {matchData && (
                  <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-brand-primary" />
                        <span className="text-xs font-semibold text-text-primary">
                          Candidate Alignment Score
                        </span>
                        <span className="text-[10px] text-text-muted font-mono">
                          ({matchData.candidate_slug})
                        </span>
                      </div>
                      <span className="text-sm font-bold text-brand-primary font-mono">
                        {Math.round(matchData.overall_match_percentage)}% Match
                      </span>
                    </div>

                    <div className="w-full bg-surface border border-surface-border h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-brand-primary h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(0, matchData.overall_match_percentage))}%` }}
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-[11px] text-center pt-1 border-t border-surface-border/50">
                      <div>
                        <span className="text-emerald-400 font-bold">
                          {matchData.matched_skills?.length || 0}
                        </span>
                        <span className="text-text-muted ml-1">Matched</span>
                      </div>
                      <div>
                        <span className="text-amber-400 font-bold">
                          {matchData.missing_skills?.length || 0}
                        </span>
                        <span className="text-text-muted ml-1">Missing</span>
                      </div>
                      <div>
                        <span className="text-text-muted font-bold">
                          {matchData.unsupported_skills?.length || 0}
                        </span>
                        <span className="text-text-muted ml-1">Unsupported</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Raw Posting Text Preview Accordion / Box */}
                <details className="text-xs group">
                  <summary className="font-semibold text-text-muted hover:text-text-primary cursor-pointer select-none flex items-center justify-between py-1">
                    <span>Inspect Raw Job Description Posting ({activeJd.raw_text.length} chars)</span>
                    <span className="text-[10px] text-brand-primary">Toggle Text</span>
                  </summary>
                  <pre className="mt-2 p-3 rounded-lg bg-surface-elevated border border-surface-border text-text-secondary whitespace-pre-wrap font-sans text-[11px] leading-relaxed max-h-48 overflow-y-auto">
                    {activeJd.raw_text}
                  </pre>
                </details>
              </div>

              {/* Requirement Analysis Section */}
              {analysisData && (
                <div className="bg-surface border border-surface-border rounded-xl p-5 sm:p-6 space-y-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-brand-primary" />
                        Structured Requirement Matrix
                      </h4>
                      <p className="text-xs text-text-muted mt-0.5">
                        Extracted competencies, tech stack, and key responsibilities
                      </p>
                    </div>
                    {analysisData.is_ai_extracted && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                        AI Extracted
                      </span>
                    )}
                  </div>

                  {/* AI Disclaimer Box */}
                  <div className="flex items-start gap-2.5 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
                    <Info className="w-4 h-4 shrink-0 mt-0.5" />
                    <p className="leading-relaxed text-[11px]">
                      {analysisData.confidence_note ||
                        "Analysis extracted for human review. Verify before treating as definitive fact."}
                    </p>
                  </div>

                  {/* Required & Preferred Skills */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-2">
                      <span className="text-xs font-bold text-text-primary">Required Skills</span>
                      <div className="flex flex-wrap gap-1.5">
                        {analysisData.required_skills?.map((sk) => (
                          <span
                            key={sk}
                            className="text-[11px] px-2 py-0.5 rounded bg-surface border border-surface-border text-text-primary font-medium"
                          >
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-2">
                      <span className="text-xs font-bold text-text-primary">Preferred Skills</span>
                      <div className="flex flex-wrap gap-1.5">
                        {analysisData.preferred_skills?.length > 0 ? (
                          analysisData.preferred_skills.map((sk) => (
                            <span
                              key={sk}
                              className="text-[11px] px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary"
                            >
                              {sk}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-text-muted">None explicitly separated</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Responsibilities */}
                  {analysisData.responsibilities?.length > 0 && (
                    <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3.5 space-y-2">
                      <span className="text-xs font-bold text-text-primary">Key Responsibilities</span>
                      <ul className="text-xs text-text-secondary space-y-1 list-disc list-inside">
                        {analysisData.responsibilities.map((r, i) => (
                          <li key={i} className="leading-relaxed">
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Candidate Project Selection & Explainability Section */}
              {matchData && matchData.recommended_projects?.length > 0 && (
                <div className="bg-surface border border-surface-border rounded-xl p-5 sm:p-6 space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
                      <Layers className="w-4 h-4 text-emerald-400" />
                      Algorithmic Project Recommendation (45/25/20/10 Breakdown)
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Top projects evaluated for relevance: Skills 45%, Responsibilities 25%, Tech Stack 20%, Domain 10%
                    </p>
                  </div>

                  <div className="space-y-3">
                    {matchData.recommended_projects.map((proj, idx) => (
                      <div
                        key={proj.project_id}
                        className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2.5 hover:border-surface-border/90 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-brand-primary/10 text-brand-primary text-[10px] font-bold flex items-center justify-center">
                              #{idx + 1}
                            </span>
                            <h5 className="text-xs font-bold text-text-primary">{proj.title}</h5>
                            {proj.is_fixed && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                                <Lock className="w-3 h-3" />
                                Pinned Safeguard (#{proj.fixed_position || 2})
                              </span>
                            )}
                          </div>

                          <div className="text-xs font-mono font-bold text-brand-primary">
                            {Math.round(proj.overall_score)}% Score
                          </div>
                        </div>

                        {proj.subtitle && (
                          <p className="text-xs text-text-secondary">{proj.subtitle}</p>
                        )}

                        {/* 4-part Score Breakdown Chips */}
                        <div className="flex flex-wrap gap-2 text-[10px] font-mono pt-1">
                          <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary">
                            Skills (45%):{" "}
                            <strong className="text-text-primary">
                              {Math.round(proj.score_breakdown?.required_skills ?? 0)}%
                            </strong>
                          </span>
                          <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary">
                            Resp (25%):{" "}
                            <strong className="text-text-primary">
                              {Math.round(proj.score_breakdown?.responsibilities ?? 0)}%
                            </strong>
                          </span>
                          <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary">
                            Stack (20%):{" "}
                            <strong className="text-text-primary">
                              {Math.round(proj.score_breakdown?.tech_stack ?? 0)}%
                            </strong>
                          </span>
                          <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary">
                            Domain (10%):{" "}
                            <strong className="text-text-primary">
                              {Math.round(proj.score_breakdown?.domain ?? 0)}%
                            </strong>
                          </span>
                        </div>

                        {/* Ranking Explanation */}
                        {proj.ranking_explanation && (
                          <p className="text-[11px] text-text-muted leading-relaxed bg-surface/50 p-2.5 rounded border border-surface-border/50">
                            {proj.ranking_explanation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* MODAL: Add Job Description */}
      {isAddModalOpen && (
        <AddJobDescriptionModal
          activeProfileSlug={activeProfileSlug}
          onClose={() => setIsAddModalOpen(false)}
          onSuccess={(newJd) => {
            queryClient.invalidateQueries({ queryKey: ["job-descriptions-list"] });
            setSelectedJdId(newJd.id);
            setIsAddModalOpen(false);
          }}
        />
      )}
    </div>
  );
};

// ==============================================================================
// ADD JOB DESCRIPTION MODAL
// ==============================================================================

interface AddJobDescriptionModalProps {
  activeProfileSlug: string;
  onClose: () => void;
  onSuccess: (jd: JobDescriptionResponse) => void;
}

const AddJobDescriptionModal: React.FC<AddJobDescriptionModalProps> = ({
  activeProfileSlug,
  onClose,
  onSuccess,
}) => {
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [rawText, setRawText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rawText.trim().length < 20) {
      setError("Job description text must be at least 20 characters long.");
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      const created = await jobDescriptionsApi.create({
        job_title: jobTitle.trim() || undefined,
        company_name: companyName.trim() || undefined,
        source_url: sourceUrl.trim() || undefined,
        raw_text: rawText.trim(),
        profile_id: activeProfileSlug,
      });

      // Automatically trigger initial analysis
      try {
        await jobDescriptionsApi.analyze(created.id, activeProfileSlug);
      } catch {
        // non-blocking
      }

      onSuccess(created);
    } catch (err: any) {
      setError(err.message || "Failed to persist job description");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Target Job Description</h3>
          <button onClick={onClose} className="p-1 rounded text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-2.5 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-text-muted font-medium mb-1">Job Title</label>
              <input
                placeholder="e.g. Backend Software Engineer"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
            <div>
              <label className="block text-text-muted font-medium mb-1">Company Name</label>
              <input
                placeholder="e.g. Razorpay"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Source URL (optional)</label>
            <input
              type="url"
              placeholder="https://boards.greenhouse.io/..."
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">
              Raw Job Description Text * (min 20 characters)
            </label>
            <textarea
              required
              rows={8}
              placeholder="Paste the full job posting requirements and description here..."
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary font-mono text-[11px] leading-relaxed"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-surface-border">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg border border-surface-border text-text-secondary hover:text-text-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white font-medium shadow-xs disabled:opacity-50"
            >
              {isLoading ? "Saving & Analyzing..." : "Save Job Description"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
