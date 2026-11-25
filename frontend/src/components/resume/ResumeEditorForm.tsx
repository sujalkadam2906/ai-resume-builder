import React, { useState } from "react";
import {
  Save,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Plus,
  Trash2,
  Lock,
  ArrowUp,
  ArrowDown,
  Layers,
  Sparkles,
  Link as LinkIcon,
  ExternalLink,
  HelpCircle,
} from "lucide-react";
import type { ResumeContentManifest, ManifestProject } from "@/types/api";

interface ResumeEditorFormProps {
  manifest: ResumeContentManifest;
  onChange: (updatedManifest: ResumeContentManifest) => void;
  onSave: () => void;
  isSaving: boolean;
  saveStatus: "idle" | "saving" | "saved" | "error";
  errorMessage: string | null;
  isApproved: boolean;
  currentVersion: number;
  isSujalProfile: boolean;
}

const normalizeUrlOnBlur = (val: string, defaultDomain?: string): string => {
  const trimmed = val.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("mailto:")) {
    return trimmed;
  }
  if (!trimmed.includes("/") && !trimmed.includes(".") && defaultDomain) {
    return `https://${defaultDomain}/${trimmed}`;
  }
  return `https://${trimmed}`;
};

export const ResumeEditorForm: React.FC<ResumeEditorFormProps> = ({
  manifest,
  onChange,
  onSave,
  isSaving,
  saveStatus,
  errorMessage,
  isApproved,
  currentVersion,
  isSujalProfile,
}) => {
  const [activeSection, setActiveSection] = useState<
    "header" | "skills" | "projects" | "experience" | "education" | "credentials"
  >("header");

  const updatePersonalInfo = (field: string, value: any) => {
    onChange({
      ...manifest,
      personal_info: {
        ...manifest.personal_info,
        [field]: value,
      },
    });
  };

  const updateHeaderLinks = (service: "linkedin" | "github" | "portfolio", field: "url" | "display", value: string) => {
    onChange({
      ...manifest,
      links: {
        ...manifest.links,
        [service]: {
          url: field === "url" ? value : manifest.links[service]?.url || "",
          display: field === "display" ? value : manifest.links[service]?.display || "",
        },
      },
    });
  };

  // Projects logic
  const updateProject = (index: number, updated: Partial<ManifestProject>) => {
    const newProjects = [...manifest.projects];
    newProjects[index] = { ...newProjects[index], ...updated };
    onChange({
      ...manifest,
      projects: newProjects,
    });
  };

  const getProjectLinkUrl = (proj: ManifestProject, labelType: "Live Demo" | "GitHub"): string => {
    const link = (proj.links || []).find((l) => {
      const lbl = (l.label || "").toLowerCase();
      if (labelType === "Live Demo") {
        return lbl.includes("demo") || lbl.includes("live") || lbl.includes("website") || lbl.includes("app");
      }
      return lbl.includes("github") || lbl.includes("code") || lbl.includes("repo");
    });
    return link?.url || "";
  };

  const updateProjectLink = (projectIndex: number, labelType: "Live Demo" | "GitHub", newUrl: string) => {
    const newProjects = [...manifest.projects];
    const currentProject = { ...newProjects[projectIndex] };
    const currentLinks = [...(currentProject.links || [])];

    const existingIdx = currentLinks.findIndex((l) => {
      const lbl = (l.label || "").toLowerCase();
      if (labelType === "Live Demo") {
        return lbl.includes("demo") || lbl.includes("live") || lbl.includes("website") || lbl.includes("app");
      }
      return lbl.includes("github") || lbl.includes("code") || lbl.includes("repo");
    });

    const trimmed = newUrl.trim();
    if (trimmed) {
      if (existingIdx >= 0) {
        currentLinks[existingIdx] = { label: labelType, url: trimmed };
      } else {
        if (labelType === "Live Demo") {
          currentLinks.unshift({ label: "Live Demo", url: trimmed });
        } else {
          currentLinks.push({ label: "GitHub", url: trimmed });
        }
      }
    } else {
      if (existingIdx >= 0) {
        currentLinks.splice(existingIdx, 1);
      }
    }

    currentProject.links = currentLinks;
    newProjects[projectIndex] = currentProject;
    onChange({ ...manifest, projects: newProjects });
  };

  const updateProjectBullet = (projectIndex: number, bulletIndex: number, text: string) => {
    const newProjects = [...manifest.projects];
    const newBullets = [...newProjects[projectIndex].bullets];
    newBullets[bulletIndex] = text;
    newProjects[projectIndex] = { ...newProjects[projectIndex], bullets: newBullets };
    onChange({
      ...manifest,
      projects: newProjects,
    });
  };

  const addProjectBullet = (projectIndex: number) => {
    const newProjects = [...manifest.projects];
    newProjects[projectIndex] = {
      ...newProjects[projectIndex],
      bullets: [...newProjects[projectIndex].bullets, "Engineered impactful feature resulting in measurable performance gain."],
    };
    onChange({
      ...manifest,
      projects: newProjects,
    });
  };

  const removeProjectBullet = (projectIndex: number, bulletIndex: number) => {
    const newProjects = [...manifest.projects];
    const newBullets = newProjects[projectIndex].bullets.filter((_, idx) => idx !== bulletIndex);
    newProjects[projectIndex] = { ...newProjects[projectIndex], bullets: newBullets };
    onChange({
      ...manifest,
      projects: newProjects,
    });
  };

  // Skills logic
  const updateSkillsForCategory = (category: string, skillsStr: string) => {
    const skillsArray = skillsStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    onChange({
      ...manifest,
      ordered_skills: {
        ...manifest.ordered_skills,
        [category]: skillsArray,
      },
    });
  };

  return (
    <div className="flex flex-col h-full bg-surface border border-surface-border rounded-xl overflow-hidden shadow-xs">
      {/* Top Save Toolbar */}
      <div className="h-14 px-4 bg-surface-elevated/70 border-b border-surface-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-text-primary">Resume Manifest Editor</span>
          {saveStatus === "saving" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-brand-primary">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-ping" />
              Saving changes...
            </span>
          )}
          {saveStatus === "saved" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Saved to PostgreSQL
            </span>
          )}
          {saveStatus === "error" && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-red-400">
              <AlertCircle className="w-3.5 h-3.5" />
              Save failed
            </span>
          )}
        </div>

        <button
          onClick={onSave}
          disabled={isSaving}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-hover text-white text-xs font-semibold transition-colors shadow-xs disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{isSaving ? "Saving..." : "Save Draft"}</span>
        </button>
      </div>

      {/* Approved Modification Warning Alert */}
      {isApproved && (
        <div className="p-3 bg-amber-500/10 border-b border-amber-500/20 text-amber-400 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">
            <strong>Approved Version Safeguard:</strong> This resume is currently approved. Saving changes will automatically increment the version (v{currentVersion} → v{currentVersion + 1}) and reset the status to Draft, requiring human approval again before export.
          </p>
        </div>
      )}

      {/* Error Message Alert */}
      {errorMessage && (
        <div className="p-3 bg-red-500/10 border-b border-red-500/20 text-red-400 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">{errorMessage}</p>
        </div>
      )}

      {/* Section Sub-Tabs */}
      <div className="flex border-b border-surface-border px-3 bg-surface overflow-x-auto text-xs font-medium scrollbar-none shrink-0">
        {[
          { id: "header", label: "Header & Summary" },
          { id: "skills", label: "Skills" },
          { id: "projects", label: `Projects (${manifest.projects?.length || 0}/4)` },
          { id: "experience", label: "Experience" },
          { id: "education", label: "Education" },
          { id: "credentials", label: "Credentials" },
        ].map((sec) => (
          <button
            key={sec.id}
            onClick={() => setActiveSection(sec.id as any)}
            className={`py-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
              activeSection === sec.id
                ? "border-brand-primary text-brand-primary font-semibold"
                : "border-transparent text-text-muted hover:text-text-primary"
            }`}
          >
            {sec.label}
          </button>
        ))}
      </div>

      {/* Scrollable Form Body */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 text-xs">
        {/* SECTION 1: HEADER & SUMMARY */}
        {activeSection === "header" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-text-muted font-medium mb-1">Header Display Name</label>
                <input
                  type="text"
                  value={manifest.personal_info?.display_name || ""}
                  onChange={(e) => updatePersonalInfo("display_name", e.target.value)}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary uppercase"
                />
              </div>

              <div>
                <label className="block text-text-muted font-medium mb-1">Full Legal Name</label>
                <input
                  type="text"
                  value={manifest.personal_info?.full_name || ""}
                  onChange={(e) => updatePersonalInfo("full_name", e.target.value)}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div>
                <label className="block text-text-muted font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={manifest.personal_info?.email || ""}
                  onChange={(e) => updatePersonalInfo("email", e.target.value)}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div>
                <label className="block text-text-muted font-medium mb-1">Phone</label>
                <input
                  type="text"
                  value={manifest.personal_info?.phone || ""}
                  onChange={(e) => updatePersonalInfo("phone", e.target.value)}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-text-muted font-medium mb-1">Location</label>
                <input
                  type="text"
                  value={manifest.personal_info?.location || ""}
                  onChange={(e) => updatePersonalInfo("location", e.target.value)}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-text-muted font-medium mb-1">Professional Headline</label>
                <input
                  type="text"
                  value={manifest.headline || ""}
                  onChange={(e) => onChange({ ...manifest, headline: e.target.value })}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary font-medium"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-text-muted font-medium mb-1">Professional Summary</label>
                <textarea
                  rows={3}
                  value={manifest.summary || ""}
                  onChange={(e) => onChange({ ...manifest, summary: e.target.value })}
                  className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary leading-relaxed"
                />
              </div>
            </div>

            {/* Hyperlinks */}
            <div className="pt-2 border-t border-surface-border space-y-2">
              <span className="font-semibold text-text-primary text-[11px] uppercase tracking-wider">
                Header Hyperlinks
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div>
                  <label className="block text-text-muted text-[11px] mb-0.5">LinkedIn Display</label>
                  <input
                    type="text"
                    value={manifest.links?.linkedin?.display || ""}
                    onChange={(e) => updateHeaderLinks("linkedin", "display", e.target.value)}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-primary"
                  />
                  <input
                    type="url"
                    placeholder="URL (e.g. https://linkedin.com/in/...)"
                    value={manifest.links?.linkedin?.url || ""}
                    onChange={(e) => updateHeaderLinks("linkedin", "url", e.target.value)}
                    onBlur={(e) => updateHeaderLinks("linkedin", "url", normalizeUrlOnBlur(e.target.value, "linkedin.com/in"))}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-muted mt-1 text-[11px]"
                  />
                </div>

                <div>
                  <label className="block text-text-muted text-[11px] mb-0.5">GitHub Display</label>
                  <input
                    type="text"
                    value={manifest.links?.github?.display || ""}
                    onChange={(e) => updateHeaderLinks("github", "display", e.target.value)}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-primary"
                  />
                  <input
                    type="url"
                    placeholder="URL (e.g. https://github.com/...)"
                    value={manifest.links?.github?.url || ""}
                    onChange={(e) => updateHeaderLinks("github", "url", e.target.value)}
                    onBlur={(e) => updateHeaderLinks("github", "url", normalizeUrlOnBlur(e.target.value, "github.com"))}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-muted mt-1 text-[11px]"
                  />
                </div>

                <div>
                  <label className="block text-text-muted text-[11px] mb-0.5">Portfolio Display</label>
                  <input
                    type="text"
                    value={manifest.links?.portfolio?.display || ""}
                    onChange={(e) => updateHeaderLinks("portfolio", "display", e.target.value)}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-primary"
                  />
                  <input
                    type="url"
                    placeholder="URL (e.g. https://...)"
                    value={manifest.links?.portfolio?.url || ""}
                    onChange={(e) => updateHeaderLinks("portfolio", "url", e.target.value)}
                    onBlur={(e) => updateHeaderLinks("portfolio", "url", normalizeUrlOnBlur(e.target.value))}
                    className="w-full bg-surface-elevated border border-surface-border rounded px-2.5 py-1 text-text-muted mt-1 text-[11px]"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SECTION 2: TECHNICAL SKILLS */}
        {activeSection === "skills" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-surface-border">
              <div>
                <h4 className="font-semibold text-text-primary">Technical Skills by Category</h4>
                <p className="text-[11px] text-text-muted">
                  Comma-separated lists of technical skills formatted on the resume
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {manifest.ordered_skills &&
                Object.entries(manifest.ordered_skills).map(([category, skillsList]) => (
                  <div key={category} className="space-y-1">
                    <label className="block text-text-primary font-semibold capitalize text-[11.5px]">
                      {category.replace(/_/g, " ")}
                    </label>
                    <input
                      type="text"
                      value={Array.isArray(skillsList) ? skillsList.join(", ") : skillsList}
                      onChange={(e) => updateSkillsForCategory(category, e.target.value)}
                      className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary"
                    />
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* SECTION 3: PROJECTS */}
        {activeSection === "projects" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-surface-border">
              <div>
                <h4 className="font-semibold text-text-primary">
                  Resume Projects ({manifest.projects?.length || 0} / 4 Max)
                </h4>
                <p className="text-[11px] text-text-muted">
                  Single-page design strictly limits resume to top 4 projects
                </p>
              </div>
              {isSujalProfile && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  <Lock className="w-3 h-3" />
                  Slot #2 Bearing Fault Protected
                </span>
              )}
            </div>

            <div className="space-y-4">
              {manifest.projects?.map((proj, pIdx) => {
                const isFixed = proj.is_fixed || (isSujalProfile && pIdx === 1);
                return (
                  <div
                    key={proj.id || pIdx}
                    className={`bg-surface-elevated/60 border rounded-xl p-4 space-y-3 transition-colors ${
                      isFixed ? "border-emerald-500/40 ring-1 ring-emerald-500/20" : "border-surface-border"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-surface border border-surface-border text-[10px] font-bold flex items-center justify-center text-text-muted">
                          #{pIdx + 1}
                        </span>
                        <input
                          type="text"
                          value={proj.title}
                          onChange={(e) => updateProject(pIdx, { title: e.target.value })}
                          className="font-bold text-text-primary bg-transparent border-b border-dashed border-surface-border focus:border-brand-primary focus:outline-none text-xs"
                        />
                        {isFixed && (
                          <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                            <Lock className="w-2.5 h-2.5" />
                            Pinned Slot
                          </span>
                        )}
                      </div>

                      {/* Project removal safeguard */}
                      {!isFixed && manifest.projects.length > 1 && (
                        <button
                          onClick={() => {
                            if (confirm(`Remove project "${proj.title}" from this resume?`)) {
                              const newProj = manifest.projects.filter((_, idx) => idx !== pIdx);
                              onChange({ ...manifest, projects: newProj });
                            }
                          }}
                          className="p-1 rounded text-text-muted hover:text-red-400 hover:bg-red-500/10"
                          title="Remove project"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    <div>
                      <label className="block text-text-muted text-[11px] mb-0.5">Subtitle / Tech Stack</label>
                      <input
                        type="text"
                        value={proj.subtitle || ""}
                        onChange={(e) => updateProject(pIdx, { subtitle: e.target.value })}
                        className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-secondary focus:outline-none focus:border-brand-primary"
                      />
                    </div>

                    {/* Live Demo and GitHub URLs */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      <div>
                        <label className="block text-text-muted text-[11px] mb-0.5 flex items-center gap-1 font-medium">
                          <ExternalLink className="w-3 h-3 text-text-muted" />
                          <span>Live Demo URL (optional)</span>
                        </label>
                        <input
                          type="url"
                          placeholder="e.g. https://myproject.app"
                          value={getProjectLinkUrl(proj, "Live Demo")}
                          onChange={(e) => updateProjectLink(pIdx, "Live Demo", e.target.value)}
                          onBlur={(e) => updateProjectLink(pIdx, "Live Demo", normalizeUrlOnBlur(e.target.value))}
                          className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-secondary focus:outline-none focus:border-brand-primary text-xs"
                        />
                      </div>
                      <div>
                        <label className="block text-text-muted text-[11px] mb-0.5 flex items-center gap-1 font-medium">
                          <LinkIcon className="w-3 h-3 text-text-muted" />
                          <span>GitHub Repository URL (optional)</span>
                        </label>
                        <input
                          type="url"
                          placeholder="e.g. https://github.com/user/repo"
                          value={getProjectLinkUrl(proj, "GitHub")}
                          onChange={(e) => updateProjectLink(pIdx, "GitHub", e.target.value)}
                          onBlur={(e) => updateProjectLink(pIdx, "GitHub", normalizeUrlOnBlur(e.target.value, "github.com"))}
                          className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-secondary focus:outline-none focus:border-brand-primary text-xs"
                        />
                      </div>
                    </div>

                    {/* Bullets */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-text-muted text-[11px] font-semibold">Accomplishment Bullets</label>
                        <button
                          onClick={() => addProjectBullet(pIdx)}
                          className="inline-flex items-center gap-1 text-[10px] text-brand-primary hover:underline font-medium"
                        >
                          <Plus className="w-3 h-3" />
                          <span>Add Bullet</span>
                        </button>
                      </div>

                      {proj.bullets?.map((bullet, bIdx) => (
                        <div key={bIdx} className="flex items-start gap-1.5">
                          <span className="text-text-muted mt-1 select-none">•</span>
                          <textarea
                            rows={2}
                            value={bullet}
                            onChange={(e) => updateProjectBullet(pIdx, bIdx, e.target.value)}
                            className="flex-1 bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary focus:outline-none focus:border-brand-primary leading-tight text-[11.5px]"
                          />
                          <button
                            onClick={() => removeProjectBullet(pIdx, bIdx)}
                            className="p-1 text-text-muted hover:text-red-400 mt-1"
                            title="Remove bullet"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* SECTION 4: EXPERIENCE / LEADERSHIP */}
        {activeSection === "experience" && (
          <div className="space-y-4">
            <h4 className="font-semibold text-text-primary pb-2 border-b border-surface-border">
              Professional Experience & Leadership
            </h4>

            <div className="space-y-3">
              {manifest.leadership?.map((exp, eIdx) => (
                <div key={exp.id || eIdx} className="bg-surface-elevated/60 border border-surface-border rounded-xl p-4 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-text-muted text-[11px] mb-0.5">Job Role</label>
                      <input
                        type="text"
                        value={exp.role}
                        onChange={(e) => {
                          const newExp = [...manifest.leadership];
                          newExp[eIdx] = { ...newExp[eIdx], role: e.target.value };
                          onChange({ ...manifest, leadership: newExp });
                        }}
                        className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-text-muted text-[11px] mb-0.5">Organization</label>
                      <input
                        type="text"
                        value={exp.organization}
                        onChange={(e) => {
                          const newExp = [...manifest.leadership];
                          newExp[eIdx] = { ...newExp[eIdx], organization: e.target.value };
                          onChange({ ...manifest, leadership: newExp });
                        }}
                        className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-text-muted text-[11px] mb-0.5">Timeframe / Duration</label>
                    <input
                      type="text"
                      value={exp.duration || ""}
                      onChange={(e) => {
                        const newExp = [...manifest.leadership];
                        newExp[eIdx] = { ...newExp[eIdx], duration: e.target.value };
                        onChange({ ...manifest, leadership: newExp });
                      }}
                      className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 5: EDUCATION */}
        {activeSection === "education" && (
          <div className="space-y-4">
            <h4 className="font-semibold text-text-primary pb-2 border-b border-surface-border">
              Education Credentials
            </h4>

            <div className="space-y-3">
              {manifest.education?.map((edu, edIdx) => (
                <div key={edIdx} className="bg-surface-elevated/60 border border-surface-border rounded-xl p-4 space-y-2">
                  <div>
                    <label className="block text-text-muted text-[11px] mb-0.5">Degree Title</label>
                    <input
                      type="text"
                      value={edu.degree}
                      onChange={(e) => {
                        const newEdu = [...manifest.education];
                        newEdu[edIdx] = { ...newEdu[edIdx], degree: e.target.value };
                        onChange({ ...manifest, education: newEdu });
                      }}
                      className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary font-medium"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-text-muted text-[11px] mb-0.5">Institution</label>
                      <input
                        type="text"
                        value={edu.institution}
                        onChange={(e) => {
                          const newEdu = [...manifest.education];
                          newEdu[edIdx] = { ...newEdu[edIdx], institution: e.target.value };
                          onChange({ ...manifest, education: newEdu });
                        }}
                        className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-text-muted text-[11px] mb-0.5">CGPA</label>
                      <input
                        type="text"
                        value={edu.cgpa || ""}
                        onChange={(e) => {
                          const newEdu = [...manifest.education];
                          newEdu[edIdx] = { ...newEdu[edIdx], cgpa: e.target.value };
                          onChange({ ...manifest, education: newEdu });
                        }}
                        className="w-full bg-surface border border-surface-border rounded px-2.5 py-1 text-text-primary"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 6: CREDENTIALS */}
        {activeSection === "credentials" && (
          <div className="space-y-4">
            <h4 className="font-semibold text-text-primary pb-2 border-b border-surface-border">
              Certificates & Achievements
            </h4>

            <div>
              <label className="block text-text-muted font-medium mb-1">
                Certifications (comma-separated)
              </label>
              <textarea
                rows={3}
                value={manifest.certifications?.join(", ") || ""}
                onChange={(e) => {
                  const certs = e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean);
                  onChange({ ...manifest, certifications: certs });
                }}
                className="w-full bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-text-primary leading-relaxed"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
