import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users,
  Briefcase,
  GraduationCap,
  Award,
  Code2,
  BookOpen,
  Plus,
  Trash2,
  Edit2,
  Lock,
  CheckCircle2,
  AlertCircle,
  Archive,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Shield,
  Save,
  X,
} from "lucide-react";
import { profilesApi } from "@/services/api";
import { useActiveProfile } from "@/context/ActiveProfileContext";
import type {
  CandidateProfileDetail,
  ProjectResponse,
  SkillResponse,
  EducationResponse,
  ExperienceResponse,
  CertificationResponse,
  AchievementResponse,
  ProfessionalDevelopmentResponse,
  ProjectCreate,
  SkillCreate,
  EducationCreate,
  ExperienceCreate,
  CertificationCreate,
  AchievementCreate,
  CandidateProfileCreate,
} from "@/types/api";

type ActiveTab =
  | "overview"
  | "projects"
  | "skills"
  | "experience"
  | "education"
  | "credentials";

export const ProfilesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { activeProfileSlug, setActiveProfileSlug } = useActiveProfile();
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");

  // Dialog States
  const [isNewProfileModalOpen, setIsNewProfileModalOpen] = useState(false);
  const [isAddProjectModalOpen, setIsAddProjectModalOpen] = useState(false);
  const [isAddSkillModalOpen, setIsAddSkillModalOpen] = useState(false);
  const [isAddExperienceModalOpen, setIsAddExperienceModalOpen] = useState(false);
  const [isAddEducationModalOpen, setIsAddEducationModalOpen] = useState(false);
  const [isAddCertModalOpen, setIsAddCertModalOpen] = useState(false);
  const [isAddAchievementModalOpen, setIsAddAchievementModalOpen] = useState(false);

  // Form error message
  const [formError, setFormError] = useState<string | null>(null);

  // 1. Fetch all candidate profiles
  const {
    data: profilesData,
    isLoading: profilesLoading,
  } = useQuery({
    queryKey: ["profiles-list"],
    queryFn: () => profilesApi.list(1, 100, true),
  });

  const profiles = profilesData?.items || [];
  const selectedSlug = profiles.some((p) => p.slug === activeProfileSlug)
    ? activeProfileSlug
    : profiles[0]?.slug || "sujal";

  // 2. Fetch full detail of the selected candidate
  const {
    data: profileDetail,
    isLoading: detailLoading,
    error: detailError,
  } = useQuery({
    queryKey: ["profile-detail", selectedSlug],
    queryFn: () => profilesApi.get(selectedSlug),
    enabled: !!selectedSlug,
  });

  // Overview edit state
  const [overviewForm, setOverviewForm] = useState<{
    full_name: string;
    display_name: string;
    email: string;
    phone: string;
    location: string;
    professional_headline: string;
    professional_summary: string;
  }>({
    full_name: "",
    display_name: "",
    email: "",
    phone: "",
    location: "",
    professional_headline: "",
    professional_summary: "",
  });

  // Sync overview form when detail loads
  React.useEffect(() => {
    if (profileDetail) {
      setOverviewForm({
        full_name: profileDetail.full_name || "",
        display_name: profileDetail.display_name || "",
        email: profileDetail.email || "",
        phone: profileDetail.phone || "",
        location: profileDetail.location || "",
        professional_headline: profileDetail.professional_headline || "",
        professional_summary: profileDetail.professional_summary || "",
      });
    }
  }, [profileDetail]);

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<typeof overviewForm>) =>
      profilesApi.patch(selectedSlug, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
      queryClient.invalidateQueries({ queryKey: ["profiles-list"] });
      alert("Candidate profile updated successfully.");
    },
    onError: (err: any) => {
      alert(`Error updating profile: ${err.message}`);
    },
  });

  const toggleArchiveMutation = useMutation({
    mutationFn: () => {
      if (profileDetail?.is_archived) {
        return profilesApi.restore(selectedSlug);
      } else {
        return profilesApi.archive(selectedSlug);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
      queryClient.invalidateQueries({ queryKey: ["profiles-list"] });
    },
    onError: (err: any) => {
      alert(`Archive action failed: ${err.message}`);
    },
  });

  const createProfileMutation = useMutation({
    mutationFn: (data: CandidateProfileCreate) => profilesApi.create(data),
    onSuccess: (newProf) => {
      queryClient.invalidateQueries({ queryKey: ["profiles-list"] });
      setActiveProfileSlug(newProf.slug);
      setIsNewProfileModalOpen(false);
      setFormError(null);
    },
    onError: (err: any) => {
      setFormError(err.message || "Failed to create candidate profile");
    },
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (projectSlug: string) =>
      profilesApi.deleteProject(profileDetail!.id, projectSlug),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => {
      alert(`Cannot delete project: ${err.message}`);
    },
  });

  const deleteSkillMutation = useMutation({
    mutationFn: (skillId: string) =>
      profilesApi.deleteSkill(profileDetail!.id, skillId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => alert(err.message),
  });

  const deleteEducationMutation = useMutation({
    mutationFn: (eduId: string) =>
      profilesApi.deleteEducation(profileDetail!.id, eduId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => alert(err.message),
  });

  const deleteExperienceMutation = useMutation({
    mutationFn: (expId: string) =>
      profilesApi.deleteExperience(profileDetail!.id, expId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => alert(err.message),
  });

  const deleteCertMutation = useMutation({
    mutationFn: (certId: string) =>
      profilesApi.deleteCertification(profileDetail!.id, certId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => alert(err.message),
  });

  const deleteAchievementMutation = useMutation({
    mutationFn: (achId: string) =>
      profilesApi.deleteAchievement(profileDetail!.id, achId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
    },
    onError: (err: any) => alert(err.message),
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-text-primary flex items-center gap-2">
            <Users className="w-5 h-5 text-brand-primary" />
            Candidate Profiles Management
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary">
            Maintain independent candidate entities, verified skills, and project repositories in PostgreSQL.
          </p>
        </div>

        <button
          onClick={() => {
            setFormError(null);
            setIsNewProfileModalOpen(true);
          }}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Candidate Profile</span>
        </button>
      </div>

      {/* Profile Selector Chips */}
      <div className="flex flex-wrap items-center gap-2 border-b border-surface-border pb-3">
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider mr-1">
          Profiles:
        </span>
        {profiles.map((p) => {
          const isSelected = p.slug === selectedSlug;
          return (
            <button
              key={p.id}
              onClick={() => setActiveProfileSlug(p.slug)}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isSelected
                  ? "bg-brand-primary text-white shadow-xs font-semibold"
                  : "bg-surface hover:bg-surface-elevated text-text-secondary border border-surface-border"
              }`}
            >
              <span>{p.full_name}</span>
              {p.is_synthetic ? (
                <span
                  className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                    isSelected ? "bg-white/20 text-white" : "bg-purple-500/10 text-purple-400"
                  }`}
                >
                  Demo
                </span>
              ) : (
                <span
                  className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                    isSelected ? "bg-white/20 text-white" : "bg-emerald-500/10 text-emerald-400"
                  }`}
                >
                  Verified
                </span>
              )}
              {p.is_archived && (
                <span className="text-[9px] px-1 py-0.2 rounded bg-red-500/20 text-red-300 font-mono">
                  Archived
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Main Profile Workspace Card */}
      {detailLoading ? (
        <div className="bg-surface border border-surface-border rounded-xl p-8 text-center text-xs text-text-muted">
          Loading candidate profile from database...
        </div>
      ) : !profileDetail ? (
        <div className="bg-surface border border-surface-border rounded-xl p-8 text-center text-xs text-text-muted">
          Profile not found or archived.
        </div>
      ) : (
        <div className="bg-surface border border-surface-border rounded-xl shadow-xs overflow-hidden">
          {/* Candidate Banner Header */}
          <div className="p-6 border-b border-surface-border bg-gradient-to-r from-surface to-surface-elevated flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shadow-xs ${
                  profileDetail.is_synthetic
                    ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                    : "bg-brand-primary/20 text-brand-primary border border-brand-primary/30"
                }`}
              >
                {profileDetail.display_name?.charAt(0) || "P"}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base sm:text-lg font-bold text-text-primary">
                    {profileDetail.full_name}
                  </h3>
                  {profileDetail.is_synthetic ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                      Synthetic Profile
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Verified Profile
                    </span>
                  )}
                  {profileDetail.is_archived && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                      Archived
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-muted mt-0.5 font-mono">
                  Slug: {profileDetail.slug} · ID: {profileDetail.id}
                </p>
              </div>
            </div>

            {/* Archive / Restore Button */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => toggleArchiveMutation.mutate()}
                disabled={toggleArchiveMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-surface-border bg-surface-elevated hover:bg-surface-border text-xs text-text-secondary font-medium transition-colors"
              >
                <Archive className="w-3.5 h-3.5" />
                <span>{profileDetail.is_archived ? "Restore Profile" : "Archive Profile"}</span>
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-surface-border px-4 sm:px-6 overflow-x-auto text-xs font-medium scrollbar-none">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "overview"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Overview & Demographics</span>
            </button>
            <button
              onClick={() => setActiveTab("projects")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "projects"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <Briefcase className="w-3.5 h-3.5" />
              <span>Projects ({profileDetail.projects?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("skills")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "skills"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Skills ({profileDetail.skills?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("experience")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "experience"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Experience ({profileDetail.experiences?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("education")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "education"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Education ({profileDetail.educations?.length || 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("credentials")}
              className={`py-3 px-3 border-b-2 transition-colors flex items-center gap-1.5 shrink-0 ${
                activeTab === "credentials"
                  ? "border-brand-primary text-brand-primary font-semibold"
                  : "border-transparent text-text-muted hover:text-text-primary"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Certificates & Awards</span>
            </button>
          </div>

          {/* Tab Content Panel */}
          <div className="p-6">
            {/* 1. OVERVIEW & DEMOGRAPHICS */}
            {activeTab === "overview" && (
              <div className="space-y-6 max-w-3xl">
                <div className="flex items-center justify-between pb-3 border-b border-surface-border">
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      Contact & Professional Information
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Information rendered at the top of generated resumes
                    </p>
                  </div>
                  <button
                    onClick={() => updateProfileMutation.mutate(overviewForm)}
                    disabled={updateProfileMutation.isPending || profileDetail.is_archived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Changes</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="block text-text-muted font-medium mb-1">Full Legal Name</label>
                    <input
                      type="text"
                      value={overviewForm.full_name}
                      onChange={(e) => setOverviewForm({ ...overviewForm, full_name: e.target.value })}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-text-muted font-medium mb-1">Resume Header Name</label>
                    <input
                      type="text"
                      value={overviewForm.display_name}
                      onChange={(e) => setOverviewForm({ ...overviewForm, display_name: e.target.value })}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-text-muted font-medium mb-1">Email Address</label>
                    <input
                      type="email"
                      value={overviewForm.email}
                      onChange={(e) => setOverviewForm({ ...overviewForm, email: e.target.value })}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-text-muted font-medium mb-1">Phone Number</label>
                    <input
                      type="text"
                      value={overviewForm.phone}
                      onChange={(e) => setOverviewForm({ ...overviewForm, phone: e.target.value })}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-text-muted font-medium mb-1">Location</label>
                    <input
                      type="text"
                      value={overviewForm.location}
                      onChange={(e) => setOverviewForm({ ...overviewForm, location: e.target.value })}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-text-muted font-medium mb-1">
                      Professional Headline
                    </label>
                    <input
                      type="text"
                      value={overviewForm.professional_headline}
                      onChange={(e) =>
                        setOverviewForm({ ...overviewForm, professional_headline: e.target.value })
                      }
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-text-muted font-medium mb-1">
                      Professional Summary
                    </label>
                    <textarea
                      rows={3}
                      value={overviewForm.professional_summary}
                      onChange={(e) =>
                        setOverviewForm({ ...overviewForm, professional_summary: e.target.value })
                      }
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary text-xs leading-relaxed"
                    />
                  </div>
                </div>

                {/* Candidate Configuration Rules Card */}
                <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2">
                  <span className="text-xs font-semibold text-text-primary">Configuration Rules</span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-text-secondary">
                    <div className="flex justify-between">
                      <span className="text-text-muted">Open to Relocate:</span>
                      <span className="text-text-primary">{profileDetail.open_to_relocate ? "Yes" : "No"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Immediate Joiner:</span>
                      <span className="text-text-primary">{profileDetail.immediate_joiner ? "Yes" : "No"}</span>
                    </div>
                    {profileDetail.slug === "sujal" && (
                      <div className="col-span-2 flex items-center gap-1.5 text-emerald-400 font-medium pt-1">
                        <Lock className="w-3.5 h-3.5" />
                        <span>Fixed Position Safeguard: Bearing Fault Diagnosis locked at Position #2</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 2. PROJECTS */}
            {activeTab === "projects" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      Verified Projects Repository
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Projects ranked and selected by the recommendation engine (max 4 per tailored resume)
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAddProjectModalOpen(true)}
                    disabled={profileDetail.is_archived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Project</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {profileDetail.projects?.map((proj) => (
                    <div
                      key={proj.id}
                      className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-3 hover:border-surface-border/90 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h5 className="text-sm font-bold text-text-primary">{proj.title}</h5>
                            {proj.is_fixed_project && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                                <Lock className="w-3 h-3" />
                                Pinned Slot #{proj.fixed_position || 2} Safeguard
                              </span>
                            )}
                          </div>
                          {proj.subtitle && (
                            <p className="text-xs text-text-secondary mt-0.5">{proj.subtitle}</p>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              if (proj.is_fixed_project) {
                                alert("Protected Project: Bearing Fault Diagnosis is pinned at position #2 and cannot be deleted.");
                                return;
                              }
                              if (confirm(`Delete project "${proj.title}"?`)) {
                                deleteProjectMutation.mutate(proj.slug);
                              }
                            }}
                            disabled={proj.is_fixed_project || profileDetail.is_archived}
                            className={`p-1.5 rounded text-xs transition-colors ${
                              proj.is_fixed_project
                                ? "text-text-muted cursor-not-allowed opacity-40"
                                : "text-text-muted hover:text-red-400 hover:bg-red-500/10"
                            }`}
                            title={proj.is_fixed_project ? "Protected Project" : "Delete Project"}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Project Skills */}
                      {proj.skills?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {proj.skills.map((sk) => (
                            <span
                              key={sk}
                              className="text-[11px] px-2 py-0.5 rounded bg-surface border border-surface-border text-text-secondary font-mono"
                            >
                              {sk}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Bullets */}
                      {proj.bullets?.length > 0 && (
                        <ul className="text-xs text-text-secondary space-y-1 list-disc list-inside">
                          {proj.bullets.map((b, idx) => (
                            <li key={idx} className="leading-relaxed">
                              {b}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. SKILLS */}
            {activeTab === "skills" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      Technical Skills & Competencies
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Categorized technical skills matched deterministically against job description keywords
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAddSkillModalOpen(true)}
                    disabled={profileDetail.is_archived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Skill</span>
                  </button>
                </div>

                {/* Group skills by category */}
                {(() => {
                  const grouped: Record<string, SkillResponse[]> = {};
                  (profileDetail.skills || []).forEach((sk) => {
                    const cat = sk.category || "General";
                    if (!grouped[cat]) grouped[cat] = [];
                    grouped[cat].push(sk);
                  });

                  const categories = Object.keys(grouped);
                  if (categories.length === 0) {
                    return (
                      <div className="text-center py-8 text-xs text-text-muted">
                        No technical skills recorded yet.
                      </div>
                    );
                  }

                  return (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {categories.map((cat) => (
                        <div
                          key={cat}
                          className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-3"
                        >
                          <div className="flex items-center justify-between border-b border-surface-border/60 pb-2">
                            <span className="text-xs font-bold text-text-primary capitalize">
                              {cat.replace(/_/g, " ")}
                            </span>
                            <span className="text-[10px] text-text-muted font-mono">
                              {grouped[cat].length} skills
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-1.5">
                            {grouped[cat].map((sk) => (
                              <span
                                key={sk.id}
                                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-surface border border-surface-border text-text-secondary hover:text-text-primary group"
                              >
                                <span>{sk.skill_name}</span>
                                <button
                                  onClick={() => deleteSkillMutation.mutate(sk.id)}
                                  disabled={profileDetail.is_archived}
                                  className="text-text-muted hover:text-red-400 transition-colors opacity-60 group-hover:opacity-100"
                                >
                                  <X className="w-3 h-3" />
                                </button>
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* 4. EXPERIENCE */}
            {activeTab === "experience" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      Professional Experience & Internships
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Career roles and verified impact metrics
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAddExperienceModalOpen(true)}
                    disabled={profileDetail.is_archived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Experience</span>
                  </button>
                </div>

                <div className="space-y-3">
                  {profileDetail.experiences?.map((exp) => (
                    <div
                      key={exp.id}
                      className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h5 className="text-sm font-bold text-text-primary">{exp.role}</h5>
                          <div className="text-xs text-text-muted flex items-center gap-2 mt-0.5">
                            <span className="text-text-secondary font-medium">{exp.organization}</span>
                            <span>·</span>
                            <span>{exp.duration}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            if (confirm(`Delete experience record?`)) {
                              deleteExperienceMutation.mutate(exp.id);
                            }
                          }}
                          disabled={profileDetail.is_archived}
                          className="p-1.5 rounded text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {exp.bullets?.length > 0 && (
                        <ul className="text-xs text-text-secondary space-y-1 list-disc list-inside pt-1">
                          {exp.bullets.map((b, idx) => (
                            <li key={idx} className="leading-relaxed">
                              {b}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. EDUCATION */}
            {activeTab === "education" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      Education Credentials
                    </h4>
                    <p className="text-xs text-text-muted mt-0.5">
                      Degrees, institutions, graduation dates and GPA
                    </p>
                  </div>
                  <button
                    onClick={() => setIsAddEducationModalOpen(true)}
                    disabled={profileDetail.is_archived}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-medium transition-colors shadow-xs disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Education</span>
                  </button>
                </div>

                <div className="space-y-3">
                  {profileDetail.educations?.map((edu) => (
                    <div
                      key={edu.id}
                      className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 flex items-center justify-between"
                    >
                      <div className="space-y-1">
                        <h5 className="text-sm font-bold text-text-primary">{edu.degree}</h5>
                        <div className="text-xs text-text-secondary">
                          <span>{edu.institution}</span>
                          {edu.duration && <span className="text-text-muted"> · {edu.duration}</span>}
                          {edu.cgpa && (
                            <span className="text-emerald-400 font-medium ml-2">CGPA: {edu.cgpa}</span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`Delete education record?`)) {
                            deleteEducationMutation.mutate(edu.id);
                          }
                        }}
                        disabled={profileDetail.is_archived}
                        className="p-1.5 rounded text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 6. CREDENTIALS & AWARDS */}
            {activeTab === "credentials" && (
              <div className="space-y-6">
                {/* Certifications Section */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-text-primary">Certifications</h4>
                    <button
                      onClick={() => setIsAddCertModalOpen(true)}
                      disabled={profileDetail.is_archived}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-medium border border-surface-border"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add Certificate</span>
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {profileDetail.certifications?.map((c) => (
                      <div
                        key={c.id}
                        className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-semibold text-text-primary">{c.name}</div>
                          <div className="text-text-muted text-[11px]">
                            {c.issuer} {c.issue_date ? `· ${c.issue_date}` : ""}
                          </div>
                        </div>
                        <button
                          onClick={() => deleteCertMutation.mutate(c.id)}
                          disabled={profileDetail.is_archived}
                          className="text-text-muted hover:text-red-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Achievements Section */}
                <div className="space-y-3 pt-4 border-t border-surface-border">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-text-primary">Achievements & Honors</h4>
                    <button
                      onClick={() => setIsAddAchievementModalOpen(true)}
                      disabled={profileDetail.is_archived}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-medium border border-surface-border"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add Achievement</span>
                    </button>
                  </div>
                  <div className="space-y-2">
                    {profileDetail.achievements?.map((a) => (
                      <div
                        key={a.id}
                        className="bg-surface-elevated/60 border border-surface-border rounded-lg p-3 flex items-start justify-between text-xs"
                      >
                        <div className="space-y-1">
                          <div className="font-semibold text-text-primary">{a.title}</div>
                          {a.description && <p className="text-text-muted">{a.description}</p>}
                        </div>
                        <button
                          onClick={() => deleteAchievementMutation.mutate(a.id)}
                          disabled={profileDetail.is_archived}
                          className="text-text-muted hover:text-red-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: New Candidate Profile */}
      {isNewProfileModalOpen && (
        <NewProfileModal
          onClose={() => setIsNewProfileModalOpen(false)}
          onSubmit={(data) => createProfileMutation.mutate(data)}
          isLoading={createProfileMutation.isPending}
          errorMessage={formError}
        />
      )}

      {/* MODAL: Add Project */}
      {isAddProjectModalOpen && profileDetail && (
        <AddProjectModal
          profileId={profileDetail.id}
          onClose={() => setIsAddProjectModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddProjectModalOpen(false);
          }}
        />
      )}

      {/* MODAL: Add Skill */}
      {isAddSkillModalOpen && profileDetail && (
        <AddSkillModal
          profileId={profileDetail.id}
          onClose={() => setIsAddSkillModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddSkillModalOpen(false);
          }}
        />
      )}

      {/* MODAL: Add Experience */}
      {isAddExperienceModalOpen && profileDetail && (
        <AddExperienceModal
          profileId={profileDetail.id}
          onClose={() => setIsAddExperienceModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddExperienceModalOpen(false);
          }}
        />
      )}

      {/* MODAL: Add Education */}
      {isAddEducationModalOpen && profileDetail && (
        <AddEducationModal
          profileId={profileDetail.id}
          onClose={() => setIsAddEducationModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddEducationModalOpen(false);
          }}
        />
      )}

      {/* MODAL: Add Certificate */}
      {isAddCertModalOpen && profileDetail && (
        <AddCertModal
          profileId={profileDetail.id}
          onClose={() => setIsAddCertModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddCertModalOpen(false);
          }}
        />
      )}

      {/* MODAL: Add Achievement */}
      {isAddAchievementModalOpen && profileDetail && (
        <AddAchievementModal
          profileId={profileDetail.id}
          onClose={() => setIsAddAchievementModalOpen(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["profile-detail", selectedSlug] });
            setIsAddAchievementModalOpen(false);
          }}
        />
      )}
    </div>
  );
};

// ==============================================================================
// MODAL COMPONENTS
// ==============================================================================

interface NewProfileModalProps {
  onClose: () => void;
  onSubmit: (data: CandidateProfileCreate) => void;
  isLoading: boolean;
  errorMessage: string | null;
}

const NewProfileModal: React.FC<NewProfileModalProps> = ({
  onClose,
  onSubmit,
  isLoading,
  errorMessage,
}) => {
  const [slug, setSlug] = useState("");
  const [fullName, setFullName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [headline, setHeadline] = useState("");
  const [isSynthetic, setIsSynthetic] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      slug: slug.trim().toLowerCase(),
      full_name: fullName.trim(),
      display_name: displayName.trim() || fullName.trim().toUpperCase(),
      email: email.trim() || undefined,
      phone: phone.trim() || undefined,
      location: location.trim() || undefined,
      professional_headline: headline.trim() || undefined,
      is_synthetic: isSynthetic,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Create Candidate Profile</h3>
          <button onClick={onClose} className="p-1 rounded text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        {errorMessage && (
          <div className="p-2.5 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div>
            <label className="block text-text-muted font-medium mb-1">
              Profile Slug (unique ID, e.g. "john_doe") *
            </label>
            <input
              required
              pattern="^[a-z0-9_-]+$"
              placeholder="e.g. sujal_kadam"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary font-mono"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Full Legal Name *</label>
            <input
              required
              placeholder="e.g. Sujal Sunil Kadam"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Display Name (Header)</label>
            <input
              placeholder="e.g. SUJAL KADAM"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-text-muted font-medium mb-1">Email</label>
              <input
                type="email"
                placeholder="candidate@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
            <div>
              <label className="block text-text-muted font-medium mb-1">Phone</label>
              <input
                placeholder="+91 9876543210"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Location</label>
            <input
              placeholder="e.g. Pune, Maharashtra, India"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Headline</label>
            <input
              placeholder="e.g. Full Stack Developer | Java & Python"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="syntheticCheck"
              checked={isSynthetic}
              onChange={(e) => setIsSynthetic(e.target.checked)}
              className="rounded border-surface-border bg-surface-elevated text-brand-primary"
            />
            <label htmlFor="syntheticCheck" className="text-text-secondary cursor-pointer">
              Mark as synthetic demonstration fixture (Demo candidate)
            </label>
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
              {isLoading ? "Creating..." : "Create Profile"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD PROJECT MODAL
// ==============================================================================

interface AddProjectModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddProjectModal: React.FC<AddProjectModalProps> = ({ profileId, onClose, onSuccess }) => {
  const [slug, setSlug] = useState("");
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [skillsStr, setSkillsStr] = useState("");
  const [bulletsStr, setBulletsStr] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const skills = skillsStr
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const bullets = bulletsStr
        .split("\n")
        .map((b) => b.trim())
        .filter(Boolean);

      await profilesApi.createProject(profileId, {
        slug: slug.trim().toLowerCase().replace(/\s+/g, "_"),
        title: title.trim(),
        subtitle: subtitle.trim() || undefined,
        skills,
        bullets,
        verification_status: "verified",
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Verified Project</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Project Slug *</label>
            <input
              required
              placeholder="e.g. cloud_sentinel_guard"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary font-mono"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Project Title *</label>
            <input
              required
              placeholder="e.g. CloudSentinel Distributed Security"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Subtitle / Tech Stack Headline</label>
            <input
              placeholder="e.g. FastAPI · Python · Redis · AWS"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Technologies (comma-separated)</label>
            <input
              placeholder="Python, FastAPI, Docker, PostgreSQL"
              value={skillsStr}
              onChange={(e) => setSkillsStr(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Impact Bullets (one per line)</label>
            <textarea
              rows={3}
              placeholder="Engineered high-throughput service&#10;Decreased query latency by 35%"
              value={bulletsStr}
              onChange={(e) => setBulletsStr(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary leading-relaxed"
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
              {isLoading ? "Saving..." : "Add Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD SKILL MODAL
// ==============================================================================

interface AddSkillModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddSkillModal: React.FC<AddSkillModalProps> = ({ profileId, onClose, onSuccess }) => {
  const [category, setCategory] = useState("languages");
  const [skillName, setSkillName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await profilesApi.createSkill(profileId, {
        category,
        skill_name: skillName.trim(),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to add skill");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Technical Skill</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            >
              <option value="languages">Languages</option>
              <option value="backend_and_java">Backend & Java</option>
              <option value="databases_and_sql">Databases & SQL</option>
              <option value="cloud_devops_and_deployment">Cloud, DevOps & Deployment</option>
              <option value="frontend">Frontend</option>
              <option value="core_cs_and_ml">Core CS & Machine Learning</option>
              <option value="testing_and_tools">Testing & Tools</option>
            </select>
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Skill Title *</label>
            <input
              required
              placeholder="e.g. PostgreSQL"
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
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
              {isLoading ? "Saving..." : "Add Skill"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD EXPERIENCE MODAL
// ==============================================================================

interface AddExperienceModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddExperienceModal: React.FC<AddExperienceModalProps> = ({
  profileId,
  onClose,
  onSuccess,
}) => {
  const [role, setRole] = useState("");
  const [organization, setOrganization] = useState("");
  const [duration, setDuration] = useState("");
  const [bulletsStr, setBulletsStr] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const bullets = bulletsStr
        .split("\n")
        .map((b) => b.trim())
        .filter(Boolean);
      await profilesApi.createExperience(profileId, {
        role: role.trim(),
        organization: organization.trim(),
        duration: duration.trim() || undefined,
        bullets,
        source: "verified_both",
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to add experience");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Professional Experience</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Job Title / Role *</label>
            <input
              required
              placeholder="e.g. Software Engineer Intern"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Organization / Company *</label>
            <input
              required
              placeholder="e.g. Infosys Ltd."
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Duration / Timeframe</label>
            <input
              placeholder="e.g. Jan 2024 - Jun 2024"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Impact Bullets (one per line)</label>
            <textarea
              rows={3}
              placeholder="Developed microservice components&#10;Decreased payload size by 20%"
              value={bulletsStr}
              onChange={(e) => setBulletsStr(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary leading-relaxed"
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
              {isLoading ? "Saving..." : "Add Experience"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD EDUCATION MODAL
// ==============================================================================

interface AddEducationModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddEducationModal: React.FC<AddEducationModalProps> = ({
  profileId,
  onClose,
  onSuccess,
}) => {
  const [degree, setDegree] = useState("");
  const [institution, setInstitution] = useState("");
  const [duration, setDuration] = useState("");
  const [cgpa, setCgpa] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await profilesApi.createEducation(profileId, {
        degree: degree.trim(),
        institution: institution.trim(),
        duration: duration.trim() || undefined,
        cgpa: cgpa.trim() || undefined,
        source: "verified_both",
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to add education record");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Education Record</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Degree Title *</label>
            <input
              required
              placeholder="e.g. B.Tech Computer Engineering"
              value={degree}
              onChange={(e) => setDegree(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Institution *</label>
            <input
              required
              placeholder="e.g. Pune Institute of Computer Technology"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-text-muted font-medium mb-1">Duration</label>
              <input
                placeholder="2021 - 2025"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
            <div>
              <label className="block text-text-muted font-medium mb-1">CGPA / Score</label>
              <input
                placeholder="8.50/10"
                value={cgpa}
                onChange={(e) => setCgpa(e.target.value)}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
              />
            </div>
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
              {isLoading ? "Saving..." : "Add Education"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD CERTIFICATE MODAL
// ==============================================================================

interface AddCertModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddCertModal: React.FC<AddCertModalProps> = ({ profileId, onClose, onSuccess }) => {
  const [name, setName] = useState("");
  const [issuer, setIssuer] = useState("");
  const [issueDate, setIssueDate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await profilesApi.createCertification(profileId, {
        name: name.trim(),
        issuer: issuer.trim() || undefined,
        issue_date: issueDate.trim() || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to add certificate");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Certification</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Credential Name *</label>
            <input
              required
              placeholder="e.g. AWS Certified Developer"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Issuer</label>
            <input
              placeholder="e.g. Amazon Web Services"
              value={issuer}
              onChange={(e) => setIssuer(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Issue Year</label>
            <input
              placeholder="e.g. 2024"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
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
              {isLoading ? "Saving..." : "Add Certification"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ==============================================================================
// ADD ACHIEVEMENT MODAL
// ==============================================================================

interface AddAchievementModalProps {
  profileId: string;
  onClose: () => void;
  onSuccess: () => void;
}

const AddAchievementModal: React.FC<AddAchievementModalProps> = ({
  profileId,
  onClose,
  onSuccess,
}) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await profilesApi.createAchievement(profileId, {
        title: title.trim(),
        description: description.trim() || undefined,
        source: "verified_both",
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to add achievement");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-surface border border-surface-border rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-surface-border">
          <h3 className="text-base font-bold text-text-primary">Add Achievement</h3>
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
          <div>
            <label className="block text-text-muted font-medium mb-1">Achievement Title *</label>
            <input
              required
              placeholder="e.g. 1st Place National Hackathon"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="block text-text-muted font-medium mb-1">Description / Context</label>
            <textarea
              rows={2}
              placeholder="Brief summary of the honor"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary"
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
              {isLoading ? "Saving..." : "Add Achievement"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
