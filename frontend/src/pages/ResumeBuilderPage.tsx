import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Cpu,
  Layers,
  CheckCircle2,
  Lock,
  ArrowRight,
  Briefcase,
  Users,
  AlertCircle,
  FileText,
  Save,
  Download,
  Check,
  History,
  Target,
  ChevronLeft,
  Eye,
  Edit3,
  X,
  Info,
} from "lucide-react";
import {
  resumesApi,
  profilesApi,
  jobDescriptionsApi,
  systemApi,
} from "@/services/api";
import { useActiveProfile } from "@/context/ActiveProfileContext";
import { ResumeEditorForm } from "@/components/resume/ResumeEditorForm";
import { ResumePreview } from "@/components/resume/ResumePreview";
import type {
  ResumeResponse,
  ResumeContentManifest,
  JobDescriptionResponse,
  JobDescriptionAnalysisResponse,
  CandidateMatchResponse,
  ProjectMatchScore,
} from "@/types/api";

export const ResumeBuilderPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const { activeProfileSlug, setActiveProfileSlug } = useActiveProfile();

  const resumeIdParam = searchParams.get("resume_id");
  const jdIdParam = searchParams.get("jd_id");

  // Wizard state (when no resume_id is loaded)
  const [wizardStep, setWizardStep] = useState<number>(1);
  const [selectedJdId, setSelectedJdId] = useState<string>(jdIdParam || "");
  const [selectedProjectIds, setSelectedProjectIds] = useState<string[]>([]);
  const [providerOverride, setProviderOverride] = useState<string>("gemini");
  const [resumeTitle, setResumeTitle] = useState<string>("");
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Editor state (when resume_id is loaded)
  const [activeResume, setActiveResume] = useState<ResumeResponse | null>(null);
  const [editorManifest, setEditorManifest] = useState<ResumeContentManifest | null>(null);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [editorError, setEditorError] = useState<string | null>(null);
  const [activeMobileView, setActiveMobileView] = useState<"edit" | "preview">("edit");
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);

  // 1. Fetch Candidate Profiles
  const { data: profilesData } = useQuery({
    queryKey: ["profiles-list"],
    queryFn: () => profilesApi.list(1, 100, false),
  });

  // 2. Fetch Job Descriptions
  const { data: jdsData } = useQuery({
    queryKey: ["job-descriptions-list"],
    queryFn: () => jobDescriptionsApi.list(undefined, 1, 100),
  });

  // 3. Fetch active candidate detail
  const { data: candidateDetail } = useQuery({
    queryKey: ["profile-detail", activeProfileSlug],
    queryFn: () => profilesApi.get(activeProfileSlug),
    enabled: !!activeProfileSlug,
  });

  // 4. Fetch selected JD matching analysis (for Wizard Step 3 & 4)
  const { data: jdMatchData } = useQuery({
    queryKey: ["wizard-jd-match", selectedJdId, activeProfileSlug],
    queryFn: () => jobDescriptionsApi.matchCandidate(selectedJdId, activeProfileSlug),
    enabled: !!selectedJdId && !!activeProfileSlug,
  });

  // 5. Fetch Resume Detail if resume_id is in URL
  const {
    data: fetchedResume,
    isLoading: resumeLoading,
    error: resumeFetchError,
  } = useQuery({
    queryKey: ["resume-detail", resumeIdParam],
    queryFn: () => resumesApi.get(resumeIdParam!),
    enabled: !!resumeIdParam,
  });

  // Sync loaded resume into editor
  useEffect(() => {
    if (fetchedResume) {
      setActiveResume(fetchedResume);
      setEditorManifest(fetchedResume.editable_manifest);
      setResumeTitle(fetchedResume.resume_title);
    }
  }, [fetchedResume]);

  // Sync recommended project IDs when match data loads
  useEffect(() => {
    if (jdMatchData && jdMatchData.recommended_projects?.length > 0) {
      const pids = jdMatchData.recommended_projects.map((p) => p.project_id);
      setSelectedProjectIds(pids.slice(0, 4));
    }
  }, [jdMatchData]);

  // Mutations
  const generateMutation = useMutation({
    mutationFn: () =>
      resumesApi.generate({
        profile_id: activeProfileSlug,
        job_description_id: selectedJdId,
        selected_project_ids: selectedProjectIds.length > 0 ? selectedProjectIds : undefined,
        provider_override: providerOverride,
        resume_title: resumeTitle.trim() || undefined,
      }),
    onSuccess: (newResume) => {
      setGenerationError(null);
      queryClient.invalidateQueries({ queryKey: ["dashboard-resumes"] });
      queryClient.invalidateQueries({ queryKey: ["resumes-library"] });
      setSearchParams({ resume_id: newResume.id });
    },
    onError: (err: any) => {
      setGenerationError(err.message || "Resume generation failed");
    },
  });

  const saveMutation = useMutation({
    mutationFn: (manifestToSave: ResumeContentManifest) =>
      resumesApi.patch(activeResume!.id, {
        resume_title: resumeTitle.trim() || undefined,
        editable_manifest: manifestToSave,
      }),
    onMutate: () => {
      setSaveStatus("saving");
      setEditorError(null);
    },
    onSuccess: (updated) => {
      setActiveResume(updated);
      setEditorManifest(updated.editable_manifest);
      setSaveStatus("saved");
      queryClient.invalidateQueries({ queryKey: ["resume-detail", updated.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-resumes"] });
      queryClient.invalidateQueries({ queryKey: ["resumes-library"] });
      setTimeout(() => setSaveStatus("idle"), 2500);
    },
    onError: (err: any) => {
      setSaveStatus("error");
      setEditorError(err.message || "Failed to save draft edits");
    },
  });

  const approveMutation = useMutation({
    mutationFn: (resumeId: string) => resumesApi.approve(resumeId),
    onSuccess: () => {
      setIsApprovalModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["resume-detail", activeResume!.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-resumes"] });
      queryClient.invalidateQueries({ queryKey: ["resumes-library"] });
      alert("Resume approved! PDF and DOCX exports are now unlocked.");
    },
    onError: (err: any) => {
      alert(`Approval failed: ${err.message}`);
    },
  });

  const isSujal = activeProfileSlug === "sujal";
  const profiles = profilesData?.items || [];
  const jds = jdsData?.items || [];

  const handleDownloadPdf = async () => {
    if (!activeResume) return;
    try {
      setIsDownloadingPdf(true);
      await resumesApi.downloadPdf(activeResume.id, `${activeResume.resume_title || "resume"}.pdf`);
    } catch (err: any) {
      alert(`Failed to download PDF: ${err.message || err}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleDownloadDocx = async () => {
    if (!activeResume) return;
    try {
      setIsDownloadingDocx(true);
      await resumesApi.downloadDocx(activeResume.id, `${activeResume.resume_title || "resume"}.docx`);
    } catch (err: any) {
      alert(`Failed to download DOCX: ${err.message || err}`);
    } finally {
      setIsDownloadingDocx(false);
    }
  };

  // ============================================================================
  // VIEW 1: INTERACTIVE TWO-PANE RESUME EDITOR (When resume_id is active)
  // ============================================================================
  if (resumeIdParam && activeResume && editorManifest) {
    const isApproved = activeResume.status === "approved";

    return (
      <div className="space-y-4 max-w-7xl mx-auto pb-12 h-[calc(100vh-6rem)] flex flex-col">
        {/* Editor Top Navigation & Action Bar */}
        <div className="bg-surface border border-surface-border rounded-xl px-4 py-3 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 shrink-0 shadow-xs">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setSearchParams({});
                setActiveResume(null);
                setEditorManifest(null);
              }}
              className="p-1.5 rounded-lg border border-surface-border text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors"
              title="Return to Wizard / New Draft"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <input
                  type="text"
                  value={resumeTitle}
                  onChange={(e) => setResumeTitle(e.target.value)}
                  onBlur={() => saveMutation.mutate(editorManifest)}
                  className="font-serif font-bold text-base text-text-primary bg-transparent border-b border-dashed border-surface-border hover:border-forma-gold focus:border-forma-gold focus:outline-none max-w-xs sm:max-w-md truncate"
                />
                {isApproved ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" />
                    Approved
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full">
                    Draft (v{activeResume.current_version})
                  </span>
                )}
                <span className="text-[10px] font-mono text-text-muted bg-surface-elevated px-1.5 py-0.5 rounded border border-surface-border">
                  v{activeResume.current_version}
                </span>
              </div>
              <p className="text-[11px] text-text-muted mt-0.5">
                Target: {editorManifest.target_company || "Target Company"} · {editorManifest.target_role || "Role"}
              </p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2 flex-wrap w-full md:w-auto justify-end">
            {/* Mobile View Toggle */}
            <div className="flex md:hidden bg-surface-elevated border border-surface-border rounded-lg p-0.5 text-xs">
              <button
                onClick={() => setActiveMobileView("edit")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  activeMobileView === "edit"
                    ? "bg-surface text-brand-primary font-bold shadow-xs"
                    : "text-text-muted"
                }`}
              >
                <Edit3 className="w-3.5 h-3.5 inline mr-1" />
                Edit
              </button>
              <button
                onClick={() => setActiveMobileView("preview")}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  activeMobileView === "preview"
                    ? "bg-surface text-brand-primary font-bold shadow-xs"
                    : "text-text-muted"
                }`}
              >
                <Eye className="w-3.5 h-3.5 inline mr-1" />
                Preview
              </button>
            </div>

            {/* ATS Audit Link */}
            <Link
              to={`/ats?resume_id=${activeResume.id}`}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-xs text-text-secondary font-medium border border-surface-border transition-colors shadow-2xs"
            >
              <Target className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">ATS Audit</span>
            </Link>

            {/* Human Approval Button */}
            {!isApproved && (
              <button
                onClick={() => setIsApprovalModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors shadow-xs"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Approve Resume</span>
              </button>
            )}

            {/* Export PDF Button (enforced approved) */}
            {isApproved ? (
              <button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold transition-colors shadow-xs disabled:opacity-60"
              >
                <Download className={`w-3.5 h-3.5 ${isDownloadingPdf ? "animate-bounce" : ""}`} />
                <span>{isDownloadingPdf ? "Downloading..." : "Download PDF"}</span>
              </button>
            ) : (
              <button
                disabled
                title="Approval required before PDF compilation"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-muted text-xs font-medium cursor-not-allowed opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download PDF</span>
              </button>
            )}

            {/* Export DOCX Button (enforced approved) */}
            {isApproved ? (
              <button
                onClick={handleDownloadDocx}
                disabled={isDownloadingDocx}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-border text-text-primary text-xs font-semibold border border-surface-border transition-colors shadow-2xs disabled:opacity-60"
              >
                <Download className={`w-3.5 h-3.5 ${isDownloadingDocx ? "animate-bounce" : ""}`} />
                <span>{isDownloadingDocx ? "Downloading..." : "DOCX"}</span>
              </button>
            ) : (
              <button
                disabled
                title="Approval required before DOCX compilation"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-elevated border border-surface-border text-text-muted text-xs font-medium cursor-not-allowed opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>DOCX</span>
              </button>
            )}
          </div>
        </div>

        {/* Two-Pane Workspace Canvas */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-0 overflow-hidden">
          {/* Left Panel: Editable Resume Sections (5 cols on lg) */}
          <div
            className={`lg:col-span-5 h-full overflow-hidden ${
              activeMobileView === "preview" ? "hidden lg:block" : "block"
            }`}
          >
            <ResumeEditorForm
              manifest={editorManifest}
              onChange={(updated) => setEditorManifest(updated)}
              onSave={() => saveMutation.mutate(editorManifest)}
              isSaving={saveMutation.isPending}
              saveStatus={saveStatus}
              errorMessage={editorError}
              isApproved={isApproved}
              currentVersion={activeResume.current_version}
              isSujalProfile={isSujal}
            />
          </div>

          {/* Right Panel: Live A4 Preview Canvas (7 cols on lg) */}
          <div
            className={`lg:col-span-7 h-full overflow-hidden ${
              activeMobileView === "edit" ? "hidden lg:block" : "block"
            }`}
          >
            <ResumePreview
              manifest={editorManifest}
              isApproved={isApproved}
              versionNumber={activeResume.current_version}
            />
          </div>
        </div>

        {/* Human Approval Review Modal */}
        {isApprovalModalOpen && (
          <ApprovalModal
            resumeTitle={resumeTitle}
            versionNumber={activeResume.current_version}
            targetCompany={editorManifest.target_company}
            onClose={() => setIsApprovalModalOpen(false)}
            onApprove={() => approveMutation.mutate(activeResume.id)}
            isLoading={approveMutation.isPending}
          />
        )}
      </div>
    );
  }

  // ============================================================================
  // VIEW 2: GUIDED RESUME CREATION WIZARD (Steps 1 to 5)
  // ============================================================================
  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-16">
      {/* Wizard Header */}
      <div>
        <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-text-primary flex items-center gap-2.5">
          <Sparkles className="w-6 h-6 text-forma-gold" />
          <span>Resume Tailoring Studio</span>
        </h1>
        <p className="text-xs sm:text-sm text-text-secondary mt-1">
          Precision workflow tailoring accomplishments, project evidence, and technical keywords against target job postings.
        </p>
      </div>

      {/* Progress Steps Header */}
      <div className="grid grid-cols-4 gap-2 bg-surface border border-surface-border rounded-xl p-3 text-xs font-semibold">
        {[
          { num: 1, label: "Candidate" },
          { num: 2, label: "Job Description" },
          { num: 3, label: "Evidence & Projects" },
          { num: 4, label: "Engine & Generate" },
        ].map((st) => (
          <button
            key={st.num}
            onClick={() => {
              if (st.num < wizardStep) setWizardStep(st.num);
            }}
            disabled={st.num > wizardStep}
            className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg transition-colors ${
              wizardStep === st.num
                ? "bg-brand-primary/15 text-brand-primary border border-brand-primary/30 font-bold"
                : st.num < wizardStep
                ? "text-emerald-400 hover:bg-surface-elevated cursor-pointer"
                : "text-text-muted opacity-60 cursor-not-allowed"
            }`}
          >
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                st.num < wizardStep
                  ? "bg-emerald-500/20 text-emerald-400"
                  : wizardStep === st.num
                  ? "bg-brand-primary text-white"
                  : "bg-surface-elevated text-text-muted"
              }`}
            >
              {st.num < wizardStep ? <Check className="w-3 h-3" /> : st.num}
            </span>
            <span className="hidden sm:inline">{st.label}</span>
          </button>
        ))}
      </div>

      {/* Generation Error Alert */}
      {generationError && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{generationError}</p>
        </div>
      )}

      {/* WIZARD STEP 1: CANDIDATE PROFILE SELECTION */}
      {wizardStep === 1 && (
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-xs">
          <div>
            <h3 className="text-base font-bold text-text-primary">Step 1: Select Candidate Profile</h3>
            <p className="text-xs text-text-muted mt-0.5">
              Choose the verified profile whose education, skills, and projects will be matched against the job description.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {profiles.map((cand) => {
              const isSelected = cand.slug === activeProfileSlug;
              return (
                <div
                  key={cand.id}
                  onClick={() => setActiveProfileSlug(cand.slug)}
                  className={`cursor-pointer rounded-xl p-5 border transition-all ${
                    isSelected
                      ? "border-brand-primary bg-brand-primary/5 ring-1 ring-brand-primary/30 shadow-xs"
                      : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
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
                        {cand.display_name?.charAt(0) || "P"}
                      </div>
                      <div>
                        <h4 className="font-bold text-text-primary text-sm">{cand.full_name}</h4>
                        <p className="text-xs text-text-muted font-mono">{cand.slug}</p>
                      </div>
                    </div>

                    {cand.is_synthetic ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                        Synthetic Demo
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        Verified
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-text-secondary mt-3">
                    {cand.professional_headline || "Software Engineer"}
                  </p>

                  {cand.slug === "sujal" && (
                    <div className="mt-3 pt-3 border-t border-surface-border flex items-center gap-1.5 text-emerald-400 text-[11px] font-medium">
                      <Lock className="w-3 h-3" />
                      <span>Bearing Fault Diagnosis locked at Slot #2</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex justify-end pt-3 border-t border-surface-border">
            <button
              onClick={() => setWizardStep(2)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold shadow-xs"
            >
              <span>Next: Select Job Description</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* WIZARD STEP 2: JOB DESCRIPTION SELECTION */}
      {wizardStep === 2 && (
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-text-primary">Step 2: Select Target Job Description</h3>
              <p className="text-xs text-text-muted mt-0.5">
                Select the target role posting to extract required keywords and calculate alignment.
              </p>
            </div>
            <Link
              to="/job-descriptions"
              className="text-xs text-brand-primary hover:underline font-medium"
            >
              + Add New Posting
            </Link>
          </div>

          {jds.length === 0 ? (
            <div className="p-8 border border-dashed border-surface-border rounded-xl text-center space-y-3">
              <Briefcase className="w-8 h-8 text-text-muted mx-auto" />
              <p className="text-xs font-medium text-text-primary">No Job Descriptions on Record</p>
              <Link
                to="/job-descriptions"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary text-white text-xs font-medium"
              >
                Create Job Description First
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {jds.map((jd) => {
                const isSelected = jd.id === selectedJdId;
                return (
                  <div
                    key={jd.id}
                    onClick={() => setSelectedJdId(jd.id)}
                    className={`cursor-pointer rounded-xl p-4 border transition-all ${
                      isSelected
                        ? "border-brand-primary bg-brand-primary/5 ring-1 ring-brand-primary/30"
                        : "border-surface-border bg-surface-elevated/40 hover:border-surface-border/90"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-xs sm:text-sm text-text-primary">
                          {jd.job_title || "Target Position"}
                        </h4>
                        <div className="text-xs text-text-muted flex items-center gap-2 mt-0.5">
                          <span className="font-medium text-text-secondary">{jd.company_name}</span>
                          <span>·</span>
                          <span>{jd.extracted_skills?.length || 0} extracted skills</span>
                        </div>
                      </div>

                      {jd.match_percentage !== null && jd.match_percentage !== undefined && (
                        <span className="text-xs font-mono font-bold text-brand-primary bg-brand-primary/10 border border-brand-primary/20 px-2 py-0.5 rounded">
                          {Math.round(jd.match_percentage)}% Match
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex items-center justify-between pt-3 border-t border-surface-border">
            <button
              onClick={() => setWizardStep(1)}
              className="px-3 py-1.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary"
            >
              Back
            </button>
            <button
              onClick={() => setWizardStep(3)}
              disabled={!selectedJdId}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold shadow-xs disabled:opacity-50"
            >
              <span>Next: Review Evidence & Projects</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* WIZARD STEP 3: EVIDENCE & PROJECT SELECTION */}
      {wizardStep === 3 && (
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-xs">
          <div>
            <h3 className="text-base font-bold text-text-primary">Step 3: Review Evidence & Project Selection</h3>
            <p className="text-xs text-text-muted mt-0.5">
              The deterministic engine ranks top candidate projects using the 45/25/20/10 weight matrix while enforcing fixed slot safeguards.
            </p>
          </div>

          {/* Alignment Banner */}
          {jdMatchData && (
            <div className="bg-surface-elevated/70 border border-surface-border rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-brand-primary" />
                  Candidate-to-JD Match Score
                </span>
                <span className="text-sm font-bold font-mono text-brand-primary">
                  {Math.round(jdMatchData.overall_match_percentage)}%
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {jdMatchData.matched_skills?.slice(0, 8).map((sk) => (
                  <span
                    key={sk}
                    className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono"
                  >
                    ✓ {sk}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Project Selection Cards */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-text-primary">
              <span>Selected Projects ({selectedProjectIds.length}/4 max)</span>
              {isSujal && (
                <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                  <Lock className="w-3 h-3" />
                  Slot #2 Bearing Fault Diagnosis Permanently Locked
                </span>
              )}
            </div>

            {candidateDetail?.projects?.map((proj, pIdx) => {
              const isSelected = selectedProjectIds.includes(proj.slug) || selectedProjectIds.includes(proj.id);
              const isBearingFault = proj.slug === "bearing_fault_diagnosis" || proj.is_fixed_project;
              const isLocked = isSujal && isBearingFault;

              return (
                <div
                  key={proj.id}
                  className={`rounded-xl p-4 border transition-all ${
                    isLocked
                      ? "border-emerald-500/40 bg-emerald-500/5"
                      : isSelected
                      ? "border-brand-primary bg-brand-primary/5"
                      : "border-surface-border bg-surface-elevated/40 opacity-75"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={isSelected || isLocked}
                          disabled={isLocked}
                          onChange={(e) => {
                            if (isLocked) return;
                            if (e.target.checked) {
                              if (selectedProjectIds.length >= 4) {
                                alert("Maximum 4 projects allowed for single-page ATS format.");
                                return;
                              }
                              setSelectedProjectIds([...selectedProjectIds, proj.slug]);
                            } else {
                              setSelectedProjectIds(
                                selectedProjectIds.filter((id) => id !== proj.slug && id !== proj.id)
                              );
                            }
                          }}
                          className="rounded border-surface-border text-brand-primary"
                        />
                        <h4 className="font-bold text-xs sm:text-sm text-text-primary">{proj.title}</h4>
                        {isLocked && (
                          <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.2 rounded flex items-center gap-0.5">
                            <Lock className="w-2.5 h-2.5" />
                            Locked Slot #2
                          </span>
                        )}
                      </div>
                      {proj.subtitle && (
                        <p className="text-xs text-text-secondary mt-1">{proj.subtitle}</p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-surface-border">
            <button
              onClick={() => setWizardStep(2)}
              className="px-3 py-1.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary"
            >
              Back
            </button>
            <button
              onClick={() => setWizardStep(4)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold shadow-xs"
            >
              <span>Next: AI Provider & Title</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* WIZARD STEP 4: AI PROVIDER & GENERATION TRIGGER */}
      {wizardStep === 4 && (
        <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-5 shadow-xs">
          <div>
            <h3 className="text-base font-bold text-text-primary">Step 4: AI Provider Cascade & Synthesis</h3>
            <p className="text-xs text-text-muted mt-0.5">
              Select the AI engine tier and document title before synthesizing your tailored single-page resume draft.
            </p>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-text-muted font-medium mb-1">Resume Document Title</label>
              <input
                type="text"
                placeholder={`e.g. ${candidateDetail?.display_name || "Candidate"} - Software Engineer Resume`}
                value={resumeTitle}
                onChange={(e) => setResumeTitle(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>

            <div>
              <label className="block text-text-muted font-medium mb-1">AI Provider Engine Tier</label>
              <select
                value={providerOverride}
                onChange={(e) => setProviderOverride(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              >
                <option value="gemini">Google Gemini (Recommended / Primary)</option>
                <option value="groq">Groq (Llama 3 Ultra-Fast Inference)</option>
                <option value="cerebras">Cerebras (Llama 3.1 8B)</option>
                <option value="mistral">Mistral AI</option>
                <option value="offline">Offline Deterministic Core Engine (Zero API calls)</option>
              </select>
            </div>

            <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2">
              <span className="font-semibold text-text-primary">Generation Pipeline Summary</span>
              <ul className="text-text-muted space-y-1 list-disc list-inside">
                <li>Candidate: {candidateDetail?.full_name} ({activeProfileSlug})</li>
                <li>Target Job ID: {selectedJdId}</li>
                <li>Selected Projects: {selectedProjectIds.length} projects (Slot #2 protected)</li>
                <li>Single-Page Guarantee: Enabled</li>
              </ul>
            </div>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-surface-border">
            <button
              onClick={() => setWizardStep(3)}
              className="px-3 py-1.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary"
            >
              Back
            </button>
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-bold shadow-xs disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{generateMutation.isPending ? "Tailoring Accomplishments..." : "Generate Resume Draft"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ==============================================================================
// APPROVAL MODAL COMPONENT
// ==============================================================================

interface ApprovalModalProps {
  resumeTitle: string;
  versionNumber: number;
  targetCompany: string;
  onClose: () => void;
  onApprove: () => void;
  isLoading: boolean;
}

const ApprovalModal: React.FC<ApprovalModalProps> = ({
  resumeTitle,
  versionNumber,
  targetCompany,
  onClose,
  onApprove,
  isLoading,
}) => {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary flex items-center gap-2">
            <Check className="w-5 h-5 text-emerald-400" />
            Approve Resume Document
          </h3>
          <button onClick={onClose} className="p-1 rounded text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3 text-xs text-text-secondary">
          <p>
            You are approving <strong>{resumeTitle}</strong> (Version #{versionNumber}).
          </p>

          <div className="bg-surface-elevated/70 border border-surface-border rounded-lg p-3 space-y-1.5">
            <div className="font-semibold text-text-primary">What happens next:</div>
            <ul className="list-disc list-inside space-y-1 text-text-muted">
              <li>Locks Version #{versionNumber} as an immutable historical snapshot.</li>
              <li>Enables official ReportLab 1-page PDF download.</li>
              <li>Enables official python-docx DOCX download.</li>
              <li>Future edits will create a new draft (v{versionNumber + 1}) preserving this version.</li>
            </ul>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 pt-3 border-t border-surface-border">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg border border-surface-border text-xs text-text-secondary hover:text-text-primary"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onApprove}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
          >
            <Check className="w-3.5 h-3.5" />
            <span>{isLoading ? "Locking & Approving..." : "Confirm Human Approval"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
