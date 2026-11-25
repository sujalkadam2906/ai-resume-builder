import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  Download,
  FileText,
  CheckCircle2,
  Clock,
  ExternalLink,
  Sparkles,
  Layers,
  History,
  X,
  AlertCircle,
  Check,
  Search,
  Filter,
  Target,
  Edit3,
} from "lucide-react";
import { resumesApi, profilesApi } from "@/services/api";
import { useActiveProfile } from "@/context/ActiveProfileContext";
import type { ResumeResponse, ResumeVersionResponse } from "@/types/api";

export const ResumesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { activeProfileSlug } = useActiveProfile();

  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [candidateFilter, setCandidateFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedResumeForHistory, setSelectedResumeForHistory] = useState<ResumeResponse | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownloadPdf = async (res: ResumeResponse) => {
    try {
      setDownloadingId(`${res.id}-pdf`);
      await resumesApi.downloadPdf(res.id, `${res.resume_title || "resume"}.pdf`);
    } catch (err: any) {
      alert(`Download failed: ${err.message || err}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDownloadDocx = async (res: ResumeResponse) => {
    try {
      setDownloadingId(`${res.id}-docx`);
      await resumesApi.downloadDocx(res.id, `${res.resume_title || "resume"}.docx`);
    } catch (err: any) {
      alert(`Download failed: ${err.message || err}`);
    } finally {
      setDownloadingId(null);
    }
  };

  // Fetch Profiles for candidate filtering
  const { data: profilesData } = useQuery({
    queryKey: ["profiles-list"],
    queryFn: () => profilesApi.list(1, 100, false),
  });

  // Fetch Resumes
  const {
    data: resumesData,
    isLoading: resumesLoading,
  } = useQuery({
    queryKey: ["resumes-library", statusFilter, candidateFilter],
    queryFn: () =>
      resumesApi.list(
        candidateFilter === "all" ? undefined : candidateFilter,
        statusFilter === "all" ? undefined : statusFilter,
        1,
        100
      ),
  });

  // Approve Mutation
  const approveMutation = useMutation({
    mutationFn: (resumeId: string) => resumesApi.approve(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes-library"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-resumes"] });
      alert("Resume approved and locked for export!");
    },
    onError: (err: any) => {
      alert(`Approval failed: ${err.message}`);
    },
  });

  const resumes = resumesData?.items || [];
  const profiles = profilesData?.items || [];

  const filteredResumes = resumes.filter((r) => {
    const q = searchQuery.toLowerCase();
    const matchesTitle = r.resume_title.toLowerCase().includes(q);
    const manifest = r.editable_manifest || {};
    const matchesCompany = (manifest.target_company || "").toLowerCase().includes(q);
    const matchesRole = (manifest.target_role || "").toLowerCase().includes(q);
    return matchesTitle || matchesCompany || matchesRole;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-text-primary flex items-center gap-2.5">
            <Archive className="w-6 h-6 text-forma-emerald" />
            <span>Tailored Resume Archive</span>
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Manage tailored applications, inspect version snapshots, and download certified one-page PDF/DOCX files.
          </p>
        </div>

        <Link
          to="/builder"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-forma bg-forma-navy hover:bg-forma-deep-navy dark:bg-forma-emerald dark:hover:bg-forma-emerald-hover text-white text-xs font-semibold transition-all shadow-subtle hover:shadow-card"
        >
          <Sparkles className="w-4 h-4" />
          <span>New Resume Draft</span>
        </Link>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-surface border border-surface-border rounded-xl p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-xs">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search resumes by title, role or company..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-elevated border border-surface-border rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-primary"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Status Filter */}
          <div className="flex items-center bg-surface-elevated border border-surface-border rounded-lg p-0.5 text-xs">
            {["all", "approved", "draft"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium capitalize transition-all ${
                  statusFilter === st
                    ? "bg-surface text-brand-primary font-bold shadow-xs"
                    : "text-text-muted hover:text-text-primary"
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Candidate Filter */}
          <select
            value={candidateFilter}
            onChange={(e) => setCandidateFilter(e.target.value)}
            className="bg-surface-elevated border border-surface-border rounded-lg px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-primary"
          >
            <option value="all">All Candidates</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.slug}>
                {p.full_name} ({p.slug})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Resume Grid / List */}
      {resumesLoading ? (
        <div className="space-y-3">
          <div className="h-20 bg-surface border border-surface-border rounded-xl animate-pulse" />
          <div className="h-20 bg-surface border border-surface-border rounded-xl animate-pulse" />
        </div>
      ) : filteredResumes.length === 0 ? (
        <div className="bg-surface border border-surface-border rounded-xl p-12 text-center space-y-3 shadow-xs">
          <FileText className="w-10 h-10 text-text-muted mx-auto" />
          <h3 className="text-sm font-semibold text-text-primary">No Resumes Found</h3>
          <p className="text-xs text-text-muted max-w-sm mx-auto">
            {searchQuery || statusFilter !== "all" || candidateFilter !== "all"
              ? "No resumes matched the active search and filter criteria."
              : "Generate a tailored draft from a target job description to build your archive."}
          </p>
          <Link
            to="/builder"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Open Resume Wizard</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filteredResumes.map((res) => {
            const isApproved = res.status === "approved";
            const manifest = res.editable_manifest || {};
            const candidate = profiles.find((p) => p.id === res.profile_id);

            return (
              <div
                key={res.id}
                className="bg-surface border border-surface-border rounded-xl p-4 sm:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:border-surface-border/90 transition-colors shadow-xs"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h4 className="text-sm font-bold text-text-primary truncate">
                      {res.resume_title}
                    </h4>
                    {isApproved ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        Approved
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <Clock className="w-3 h-3" />
                        Draft (v{res.current_version})
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-elevated text-text-muted border border-surface-border">
                      Version {res.current_version}
                    </span>
                    {candidate && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-brand-primary/10 text-brand-primary font-medium border border-brand-primary/20">
                        {candidate.display_name || candidate.full_name}
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-text-muted flex items-center gap-2 flex-wrap">
                    {manifest.target_company && (
                      <>
                        <span className="text-text-secondary font-medium">{manifest.target_company}</span>
                        <span>·</span>
                      </>
                    )}
                    {manifest.target_role && (
                      <>
                        <span>{manifest.target_role}</span>
                        <span>·</span>
                      </>
                    )}
                    <span>Updated {new Date(res.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Actions & Export Downloads */}
                <div className="flex items-center gap-2 flex-wrap shrink-0">
                  {/* Edit / Open in Editor Button */}
                  <Link
                    to={`/builder?resume_id=${res.id}`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-medium border border-surface-border transition-colors shadow-2xs"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-brand-primary" />
                    <span>{isApproved ? "View / Edit" : "Continue Editing"}</span>
                  </Link>

                  {/* Version History Button */}
                  <button
                    onClick={() => setSelectedResumeForHistory(res)}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-secondary font-medium border border-surface-border transition-colors"
                    title="Inspect historical version snapshots"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">History</span>
                  </button>

                  {/* ATS Diagnostic Link */}
                  <Link
                    to={`/ats?resume_id=${res.id}`}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-secondary font-medium border border-surface-border transition-colors"
                    title="Audit ATS scoring"
                  >
                    <Target className="w-3.5 h-3.5 text-amber-400" />
                    <span className="hidden sm:inline">ATS</span>
                  </Link>

                  {/* Approve Action (if draft) */}
                  {!isApproved && (
                    <button
                      onClick={() => {
                        if (confirm(`Approve "${res.resume_title}" (v${res.current_version}) for final export?`)) {
                          approveMutation.mutate(res.id);
                        }
                      }}
                      disabled={approveMutation.isPending}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors shadow-xs"
                      title="Promote draft to approved status"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Approve</span>
                    </button>
                  )}

                  {/* PDF Download */}
                  {isApproved ? (
                    <button
                      onClick={() => handleDownloadPdf(res)}
                      disabled={downloadingId === `${res.id}-pdf`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold transition-colors shadow-xs disabled:opacity-60"
                    >
                      <Download className={`w-3.5 h-3.5 ${downloadingId === `${res.id}-pdf` ? "animate-bounce" : ""}`} />
                      <span>{downloadingId === `${res.id}-pdf` ? "PDF..." : "PDF"}</span>
                    </button>
                  ) : (
                    <button
                      disabled
                      title="Human approval required before PDF compilation"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-muted text-xs font-medium cursor-not-allowed opacity-50"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>PDF</span>
                    </button>
                  )}

                  {/* DOCX Download */}
                  {isApproved ? (
                    <button
                      onClick={() => handleDownloadDocx(res)}
                      disabled={downloadingId === `${res.id}-docx`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-semibold border border-surface-border transition-colors shadow-2xs disabled:opacity-60"
                    >
                      <Download className={`w-3.5 h-3.5 ${downloadingId === `${res.id}-docx` ? "animate-bounce" : ""}`} />
                      <span>{downloadingId === `${res.id}-docx` ? "DOCX..." : "DOCX"}</span>
                    </button>
                  ) : (
                    <button
                      disabled
                      title="Human approval required before DOCX compilation"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-muted text-xs font-medium cursor-not-allowed opacity-50"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>DOCX</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL: Version History Snapshot Inspector */}
      {selectedResumeForHistory && (
        <VersionHistoryModal
          resume={selectedResumeForHistory}
          onClose={() => setSelectedResumeForHistory(null)}
        />
      )}
    </div>
  );
};

// ==============================================================================
// VERSION HISTORY MODAL
// ==============================================================================

interface VersionHistoryModalProps {
  resume: ResumeResponse;
  onClose: () => void;
}

const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({ resume, onClose }) => {
  const { data: versions, isLoading } = useQuery({
    queryKey: ["resume-versions", resume.id],
    queryFn: () => resumesApi.listVersions(resume.id),
  });

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <div>
            <h3 className="text-base font-bold text-text-primary">Immutable Version History</h3>
            <p className="text-xs text-text-muted">{resume.resume_title}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading ? (
          <div className="py-6 text-center text-xs text-text-muted">Loading version snapshots...</div>
        ) : !versions || versions.length === 0 ? (
          <div className="py-6 text-center text-xs text-text-muted">
            No historical version snapshots created yet.
          </div>
        ) : (
          <div className="space-y-2.5 max-h-80 overflow-y-auto">
            {versions.map((ver) => (
              <div
                key={ver.id}
                className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 space-y-1.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text-primary font-mono">
                    Snapshot Version #{ver.version_number}
                  </span>
                  <span className="text-text-muted font-mono text-[10px]">
                    {new Date(ver.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-[11px] text-text-muted">
                  Storage Key: <code className="font-mono">{ver.pdf_storage_key || "Draft snapshot"}</code>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-surface-border">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
