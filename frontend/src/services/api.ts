import { supabase } from "@/lib/supabase";
import type {
  HealthResponse,
  ReadinessResponse,
  SystemInfoResponse,
  ProvidersStatusResponse,
  CandidateProfileSummary,
  CandidateProfileDetail,
  CandidateProfileCreate,
  CandidateProfileUpdate,
  ProfilePaginationResponse,
  EducationResponse,
  EducationCreate,
  EducationUpdate,
  ExperienceResponse,
  ExperienceCreate,
  ExperienceUpdate,
  SkillResponse,
  SkillCreate,
  SkillUpdate,
  BulkSkillUpdate,
  ProjectResponse,
  ProjectCreate,
  ProjectUpdate,
  CertificationResponse,
  CertificationCreate,
  CertificationUpdate,
  AchievementResponse,
  AchievementCreate,
  AchievementUpdate,
  ProfessionalDevelopmentResponse,
  ProfessionalDevelopmentCreate,
  ProfessionalDevelopmentUpdate,
  JobDescriptionResponse,
  JobDescriptionCreate,
  JobDescriptionUpdate,
  JobDescriptionPaginationResponse,
  JobDescriptionAnalysisResponse,
  CandidateMatchResponse,
  ResumeGenerateRequest,
  ResumeUpdateRequest,
  ResumeResponse,
  ResumePaginationResponse,
  ResumeApprovalResponse,
  ResumeVersionResponse,
  ATSEvaluationResponse,
} from "@/types/api";

const BACKEND_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const API_BASE = `${BACKEND_BASE}/api/v1`;

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const headers = new Headers(options.headers || {});

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Attach Supabase access token if session exists
  try {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  } catch (err) {
    // Session retrieval error - proceed without token (e.g. public endpoints or local dev bypass)
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMessage = `HTTP ${res.status}: ${res.statusText}`;
    let errData: any = null;
    try {
      errData = await res.json();
      if (errData && errData.detail) {
        errMessage = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      // not json
    }
    throw new ApiError(res.status, errMessage, errData);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json() as Promise<T>;
}

// ==============================================================================
// 1. System & Health API
// ==============================================================================

export const systemApi = {
  getHealth: () => request<HealthResponse>("/health"),
  getReadiness: () => request<ReadinessResponse>("/health/ready"),
  getSystemInfo: () => request<SystemInfoResponse>("/system/info"),
  getProvidersStatus: () => request<ProvidersStatusResponse>("/system/providers"),
};

// ==============================================================================
// 2. Candidate Profiles API
// ==============================================================================

export const profilesApi = {
  list: (page = 1, size = 20, includeArchived = false) =>
    request<ProfilePaginationResponse>(
      `/profiles?page=${page}&size=${size}&include_archived=${includeArchived}`
    ),

  get: (profileIdOrSlug: string) =>
    request<CandidateProfileDetail>(`/profiles/${profileIdOrSlug}`),

  create: (data: CandidateProfileCreate) =>
    request<CandidateProfileDetail>("/profiles", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  patch: (profileIdOrSlug: string, data: CandidateProfileUpdate) =>
    request<CandidateProfileDetail>(`/profiles/${profileIdOrSlug}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  archive: (profileIdOrSlug: string) =>
    request<{ status: string; id: string; slug: string; is_archived: boolean }>(
      `/profiles/${profileIdOrSlug}/archive`,
      { method: "POST" }
    ),

  restore: (profileIdOrSlug: string) =>
    request<{ status: string; id: string; slug: string; is_archived: boolean }>(
      `/profiles/${profileIdOrSlug}/restore`,
      { method: "POST" }
    ),

  // Child: Education
  listEducation: (profileId: string) =>
    request<EducationResponse[]>(`/profiles/${profileId}/education`),
  createEducation: (profileId: string, data: EducationCreate) =>
    request<EducationResponse>(`/profiles/${profileId}/education`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateEducation: (profileId: string, educationId: string, data: EducationUpdate) =>
    request<EducationResponse>(`/profiles/${profileId}/education/${educationId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteEducation: (profileId: string, educationId: string) =>
    request<void>(`/profiles/${profileId}/education/${educationId}`, {
      method: "DELETE",
    }),

  // Child: Experience
  listExperience: (profileId: string) =>
    request<ExperienceResponse[]>(`/profiles/${profileId}/experience`),
  createExperience: (profileId: string, data: ExperienceCreate) =>
    request<ExperienceResponse>(`/profiles/${profileId}/experience`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateExperience: (profileId: string, experienceId: string, data: ExperienceUpdate) =>
    request<ExperienceResponse>(`/profiles/${profileId}/experience/${experienceId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteExperience: (profileId: string, experienceId: string) =>
    request<void>(`/profiles/${profileId}/experience/${experienceId}`, {
      method: "DELETE",
    }),

  // Child: Skills
  listSkills: (profileId: string) =>
    request<SkillResponse[]>(`/profiles/${profileId}/skills`),
  createSkill: (profileId: string, data: SkillCreate) =>
    request<SkillResponse>(`/profiles/${profileId}/skills`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateSkill: (profileId: string, skillId: string, data: SkillUpdate) =>
    request<SkillResponse>(`/profiles/${profileId}/skills/${skillId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteSkill: (profileId: string, skillId: string) =>
    request<void>(`/profiles/${profileId}/skills/${skillId}`, {
      method: "DELETE",
    }),
  bulkUpdateSkills: (profileId: string, data: BulkSkillUpdate) =>
    request<SkillResponse[]>(`/profiles/${profileId}/skills/bulk`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Child: Projects
  listProjects: (profileId: string) =>
    request<ProjectResponse[]>(`/profiles/${profileId}/projects`),
  getProject: (profileId: string, projectIdentifier: string) =>
    request<ProjectResponse>(`/profiles/${profileId}/projects/${projectIdentifier}`),
  createProject: (profileId: string, data: ProjectCreate) =>
    request<ProjectResponse>(`/profiles/${profileId}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateProject: (profileId: string, projectIdentifier: string, data: ProjectUpdate) =>
    request<ProjectResponse>(`/profiles/${profileId}/projects/${projectIdentifier}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteProject: (profileId: string, projectIdentifier: string) =>
    request<void>(`/profiles/${profileId}/projects/${projectIdentifier}`, {
      method: "DELETE",
    }),

  // Child: Certifications
  listCertifications: (profileId: string) =>
    request<CertificationResponse[]>(`/profiles/${profileId}/certifications`),
  createCertification: (profileId: string, data: CertificationCreate) =>
    request<CertificationResponse>(`/profiles/${profileId}/certifications`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCertification: (profileId: string, certId: string, data: CertificationUpdate) =>
    request<CertificationResponse>(`/profiles/${profileId}/certifications/${certId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteCertification: (profileId: string, certId: string) =>
    request<void>(`/profiles/${profileId}/certifications/${certId}`, {
      method: "DELETE",
    }),

  // Child: Achievements
  listAchievements: (profileId: string) =>
    request<AchievementResponse[]>(`/profiles/${profileId}/achievements`),
  createAchievement: (profileId: string, data: AchievementCreate) =>
    request<AchievementResponse>(`/profiles/${profileId}/achievements`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateAchievement: (profileId: string, achId: string, data: AchievementUpdate) =>
    request<AchievementResponse>(`/profiles/${profileId}/achievements/${achId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteAchievement: (profileId: string, achId: string) =>
    request<void>(`/profiles/${profileId}/achievements/${achId}`, {
      method: "DELETE",
    }),

  // Child: Professional Development
  listProfessionalDevelopment: (profileId: string) =>
    request<ProfessionalDevelopmentResponse[]>(`/profiles/${profileId}/professional-development`),
  createProfessionalDevelopment: (profileId: string, data: ProfessionalDevelopmentCreate) =>
    request<ProfessionalDevelopmentResponse>(`/profiles/${profileId}/professional-development`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateProfessionalDevelopment: (profileId: string, pdId: string, data: ProfessionalDevelopmentUpdate) =>
    request<ProfessionalDevelopmentResponse>(`/profiles/${profileId}/professional-development/${pdId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteProfessionalDevelopment: (profileId: string, pdId: string) =>
    request<void>(`/profiles/${profileId}/professional-development/${pdId}`, {
      method: "DELETE",
    }),
};

// ==============================================================================
// 3. Job Descriptions API
// ==============================================================================

export const jobDescriptionsApi = {
  list: (profileId?: string, page = 1, size = 20) => {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (profileId) params.set("profile_id", profileId);
    return request<JobDescriptionPaginationResponse>(`/job-descriptions?${params.toString()}`);
  },

  get: (jdId: string) =>
    request<JobDescriptionResponse>(`/job-descriptions/${jdId}`),

  create: (data: JobDescriptionCreate) =>
    request<JobDescriptionResponse>("/job-descriptions", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  patch: (jdId: string, data: JobDescriptionUpdate) =>
    request<JobDescriptionResponse>(`/job-descriptions/${jdId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (jdId: string) =>
    request<void>(`/job-descriptions/${jdId}`, {
      method: "DELETE",
    }),

  analyze: (jdId: string, profileId?: string) => {
    const params = profileId ? `?profile_id=${encodeURIComponent(profileId)}` : "";
    return request<JobDescriptionAnalysisResponse>(`/job-descriptions/${jdId}/analyze${params}`, {
      method: "POST",
    });
  },

  getAnalysis: (jdId: string) =>
    request<JobDescriptionAnalysisResponse>(`/job-descriptions/${jdId}/analysis`),

  matchCandidate: (jdId: string, profileId: string) =>
    request<CandidateMatchResponse>(`/job-descriptions/${jdId}/match?profile_id=${encodeURIComponent(profileId)}`),
};

// ==============================================================================
// 4. Resumes & ATS API
// ==============================================================================

export const resumesApi = {
  list: (profileId?: string, status?: string, page = 1, size = 20) => {
    const params = new URLSearchParams({ page: String(page), size: String(size) });
    if (profileId) params.set("profile_id", profileId);
    if (status) params.set("status", status);
    return request<ResumePaginationResponse>(`/resumes?${params.toString()}`);
  },

  get: (resumeId: string) =>
    request<ResumeResponse>(`/resumes/${resumeId}`),

  generate: (data: ResumeGenerateRequest) =>
    request<ResumeResponse>("/resumes/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  patch: (resumeId: string, data: ResumeUpdateRequest) =>
    request<ResumeResponse>(`/resumes/${resumeId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  approve: (resumeId: string) =>
    request<ResumeApprovalResponse>(`/resumes/${resumeId}/approve`, {
      method: "POST",
    }),

  listVersions: (resumeId: string) =>
    request<ResumeVersionResponse[]>(`/resumes/${resumeId}/versions`),

  getVersion: (resumeId: string, versionNumber: number) =>
    request<ResumeVersionResponse>(`/resumes/${resumeId}/versions/${versionNumber}`),

  evaluate: (resumeId: string) =>
    request<ATSEvaluationResponse>(`/resumes/${resumeId}/evaluate`, {
      method: "POST",
    }),

  listEvaluations: (resumeId: string) =>
    request<ATSEvaluationResponse[]>(`/resumes/${resumeId}/evaluations`),

  getExportPdfUrl: (resumeId: string) => `${API_BASE}/resumes/${resumeId}/export/pdf`,
  getExportDocxUrl: (resumeId: string) => `${API_BASE}/resumes/${resumeId}/export/docx`,
};

// For backward compatibility
export const apiService = systemApi;
