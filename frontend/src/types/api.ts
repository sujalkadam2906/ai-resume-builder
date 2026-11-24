/**
 * TypeScript API interfaces matching FastAPI backend schemas.
 */

// ==============================================================================
// 1. Health & System Schemas
// ==============================================================================

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface ReadinessCheckItem {
  status: "ok" | "error" | "configured" | "active" | string;
  backend?: string;
  path?: string;
  version?: string;
  detail?: string;
}

export interface ReadinessResponse {
  status: "ready" | "degraded";
  timestamp: string;
  checks: {
    storage: ReadinessCheckItem;
    resume_engine: ReadinessCheckItem;
    database: ReadinessCheckItem;
    security_gate: {
      cloudflare_access_required: boolean;
      status: string;
    };
  };
}

export interface SystemInfoResponse {
  app_name: string;
  app_version: string;
  environment: string;
  python_version: string;
  platform: string;
  storage_backend: string;
}

export interface ProviderHealthItem {
  provider: string;
  configured: boolean;
  auth_status: string;
  connectivity: string;
  model_status: string;
  free_tier: boolean;
  priority_rank: number;
  is_enabled: boolean;
  details?: string;
}

export interface ProvidersStatusResponse {
  status: "success" | "error";
  primary_provider: string;
  fallback_sequence: string[];
  providers: ProviderHealthItem[];
  message?: string;
}

// ==============================================================================
// 2. Candidate Profiles & Child Resources Schemas
// ==============================================================================

export interface LinkItem {
  url: string;
  display: string;
}

export interface ProjectLink {
  label: string;
  url: string;
}

export interface EducationResponse {
  id: string;
  profile_id: string;
  degree: string;
  institution: string;
  duration?: string | null;
  start_year?: number | null;
  end_year?: number | null;
  cgpa?: string | null;
  score?: string | null;
  scale?: string | null;
  source: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface EducationCreate {
  degree: string;
  institution: string;
  duration?: string | null;
  start_year?: number | null;
  end_year?: number | null;
  cgpa?: string | null;
  score?: string | null;
  scale?: string | null;
  source?: string;
  display_order?: number;
}

export interface EducationUpdate {
  degree?: string;
  institution?: string;
  duration?: string | null;
  start_year?: number | null;
  end_year?: number | null;
  cgpa?: string | null;
  score?: string | null;
  scale?: string | null;
  source?: string;
  display_order?: number;
}

export interface ExperienceResponse {
  id: string;
  profile_id: string;
  role: string;
  organization: string;
  duration?: string | null;
  metrics?: string | null;
  description?: string | null;
  bullets: string[];
  source: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ExperienceCreate {
  role: string;
  organization: string;
  duration?: string | null;
  metrics?: string | null;
  description?: string | null;
  bullets?: string[];
  source?: string;
  display_order?: number;
}

export interface ExperienceUpdate {
  role?: string;
  organization?: string;
  duration?: string | null;
  metrics?: string | null;
  description?: string | null;
  bullets?: string[];
  source?: string;
  display_order?: number;
}

export interface SkillResponse {
  id: string;
  profile_id: string;
  category: string;
  skill_name: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface SkillCreate {
  category: string;
  skill_name: string;
  display_order?: number;
}

export interface SkillUpdate {
  category?: string;
  skill_name?: string;
  display_order?: number;
}

export interface BulkSkillUpdate {
  skills_by_category: Record<string, string[]>;
}

export interface ProjectResponse {
  id: string;
  profile_id: string;
  slug: string;
  title: string;
  subtitle?: string | null;
  notice?: string | null;
  is_fixed_project: boolean;
  fixed_position?: number | null;
  display_order: number;
  categories: string[];
  skills: string[];
  links: ProjectLink[];
  bullets: string[];
  metrics: string[];
  evidence_source?: string | null;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  slug: string;
  title: string;
  subtitle?: string | null;
  notice?: string | null;
  is_fixed_project?: boolean;
  fixed_position?: number | null;
  display_order?: number;
  categories?: string[];
  skills?: string[];
  links?: ProjectLink[];
  bullets?: string[];
  metrics?: string[];
  evidence_source?: string | null;
  verification_status?: string;
}

export interface ProjectUpdate {
  slug?: string;
  title?: string;
  subtitle?: string | null;
  notice?: string | null;
  is_fixed_project?: boolean;
  fixed_position?: number | null;
  display_order?: number;
  categories?: string[];
  skills?: string[];
  links?: ProjectLink[];
  bullets?: string[];
  metrics?: string[];
  evidence_source?: string | null;
  verification_status?: string;
}

export interface CertificationResponse {
  id: string;
  profile_id: string;
  name: string;
  issuer?: string | null;
  issue_date?: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface CertificationCreate {
  name: string;
  issuer?: string | null;
  issue_date?: string | null;
  display_order?: number;
}

export interface CertificationUpdate {
  name?: string;
  issuer?: string | null;
  issue_date?: string | null;
  display_order?: number;
}

export interface AchievementResponse {
  id: string;
  profile_id: string;
  title: string;
  description?: string | null;
  bullets: string[];
  source: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface AchievementCreate {
  title: string;
  description?: string | null;
  bullets?: string[];
  source?: string;
  display_order?: number;
}

export interface AchievementUpdate {
  title?: string;
  description?: string | null;
  bullets?: string[];
  source?: string;
  display_order?: number;
}

export interface ProfessionalDevelopmentResponse {
  id: string;
  profile_id: string;
  title: string;
  organization: string;
  date?: string | null;
  bullets: string[];
  source?: string | null;
  conflict_note?: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProfessionalDevelopmentCreate {
  title: string;
  organization: string;
  date?: string | null;
  bullets?: string[];
  source?: string | null;
  conflict_note?: string | null;
  display_order?: number;
}

export interface ProfessionalDevelopmentUpdate {
  title?: string;
  organization?: string;
  date?: string | null;
  bullets?: string[];
  source?: string | null;
  conflict_note?: string | null;
  display_order?: number;
}

export interface CandidateProfileSummary {
  id: string;
  slug: string;
  full_name: string;
  display_name: string;
  professional_headline?: string | null;
  location?: string | null;
  is_synthetic: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateProfileDetail extends CandidateProfileSummary {
  email?: string | null;
  phone?: string | null;
  open_to_relocate: boolean;
  immediate_joiner: boolean;
  professional_summary?: string | null;
  headlines: Record<string, any>;
  summaries: Record<string, any>;
  links: Record<string, any>;
  config_rules: Record<string, any>;
  educations: EducationResponse[];
  experiences: ExperienceResponse[];
  skills: SkillResponse[];
  projects: ProjectResponse[];
  certifications: CertificationResponse[];
  achievements: AchievementResponse[];
  professional_developments: ProfessionalDevelopmentResponse[];
}

export interface CandidateProfileCreate {
  slug: string;
  full_name: string;
  display_name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  open_to_relocate?: boolean;
  immediate_joiner?: boolean;
  professional_headline?: string | null;
  professional_summary?: string | null;
  headlines?: Record<string, any>;
  summaries?: Record<string, any>;
  links?: Record<string, any>;
  config_rules?: Record<string, any>;
  is_synthetic?: boolean;
}

export interface CandidateProfileUpdate {
  full_name?: string;
  display_name?: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  open_to_relocate?: boolean;
  immediate_joiner?: boolean;
  professional_headline?: string | null;
  professional_summary?: string | null;
  headlines?: Record<string, any>;
  summaries?: Record<string, any>;
  links?: Record<string, any>;
  config_rules?: Record<string, any>;
  is_synthetic?: boolean;
}

export interface ProfilePaginationResponse {
  items: CandidateProfileSummary[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==============================================================================
// 3. Job Descriptions & Candidate Matching Schemas
// ==============================================================================

export interface JobDescriptionResponse {
  id: string;
  profile_id?: string | null;
  job_title?: string | null;
  company_name?: string | null;
  raw_text: string;
  source_url?: string | null;
  extracted_skills: string[];
  match_percentage?: number | null;
  created_at: string;
  updated_at: string;
}

export interface JobDescriptionCreate {
  profile_id?: string | null;
  job_title?: string | null;
  company_name?: string | null;
  raw_text: string;
  source_url?: string | null;
}

export interface JobDescriptionUpdate {
  job_title?: string | null;
  company_name?: string | null;
  raw_text?: string | null;
  source_url?: string | null;
}

export interface JobDescriptionPaginationResponse {
  items: JobDescriptionResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface JobDescriptionAnalysisResponse {
  id: string;
  job_title?: string | null;
  company_name?: string | null;
  required_skills: string[];
  preferred_skills: string[];
  technical_stack: Record<string, string[]>;
  responsibilities: string[];
  experience_requirements?: string | null;
  education_requirements?: string | null;
  domain?: string | null;
  important_keywords: string[];
  match_percentage?: number | null;
  is_ai_extracted: boolean;
  confidence_note: string;
}

export interface ProjectMatchScore {
  project_id: string;
  title: string;
  subtitle: string;
  is_fixed: boolean;
  fixed_position?: number | null;
  overall_score: number;
  score_breakdown: {
    required_skills?: number;
    responsibilities?: number;
    tech_stack?: number;
    domain?: number;
    [key: string]: number | undefined;
  };
  ranking_explanation: string;
}

export interface CandidateMatchResponse {
  candidate_id: string;
  candidate_slug: string;
  job_description_id: string;
  overall_match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  unsupported_skills: string[];
  recommended_projects: ProjectMatchScore[];
  project_selection_warnings?: string | null;
}

// ==============================================================================
// 4. Resume Generation, Versioning & ATS Evaluation Schemas
// ==============================================================================

export interface ResumeGenerateRequest {
  profile_id: string;
  job_description_id: string;
  selected_project_ids?: string[];
  selected_skills?: string[];
  provider_override?: string;
  resume_title?: string;
}

export interface ResumeUpdateRequest {
  resume_title?: string;
  editable_manifest?: ResumeContentManifest | Record<string, any>;
}

export interface ManifestLinkItem {
  url: string;
  display: string;
}

export interface ManifestLinksProfile {
  linkedin?: ManifestLinkItem;
  github?: ManifestLinkItem;
  portfolio?: ManifestLinkItem;
  [key: string]: ManifestLinkItem | undefined;
}

export interface ManifestPersonalInfo {
  full_name: string;
  display_name: string;
  phone: string;
  email: string;
  location: string;
  open_to_relocate?: boolean;
  immediate_joiner?: boolean;
}

export interface ManifestProject {
  id: string;
  title: string;
  subtitle: string;
  is_fixed?: boolean;
  bullets: string[];
  links?: Array<{ label: string; url: string }>;
}

export interface ManifestExperienceItem {
  id: string;
  role: string;
  organization: string;
  duration?: string | null;
  metrics?: string | null;
  description?: string;
  bullets: string[];
  source?: string;
}

export interface ManifestEducationItem {
  degree: string;
  institution: string;
  duration: string;
  start_year?: number;
  end_year?: number;
  cgpa?: string;
  score?: string;
  scale?: string;
  source?: string;
}

export interface ManifestAchievementItem {
  id: string;
  title: string;
  description?: string;
  bullets: string[];
  source?: string;
}

export interface ManifestProfessionalDevelopmentItem {
  id: string;
  title: string;
  organization: string;
  date: string;
  bullets: string[];
  source?: string;
  conflict_note?: string | null;
}

export interface ResumeContentManifest {
  target_company: string;
  target_role: string;
  model_used: string;
  personal_info: ManifestPersonalInfo;
  links: ManifestLinksProfile;
  headline: string;
  summary: string;
  ordered_skills: Record<string, string[]>;
  projects: ManifestProject[];
  leadership: ManifestExperienceItem[];
  professional_development?: ManifestProfessionalDevelopmentItem[];
  education: ManifestEducationItem[];
  achievements?: ManifestAchievementItem[];
  research_publications?: Array<{ title: string; venue: string; year: number; doi?: string; doi_url?: string }>;
  certifications?: string[];
  tailoring_notes?: string[];
  created_at?: string | null;
}

export interface ResumeResponse {
  id: string;
  profile_id: string;
  job_description_id?: string | null;
  resume_title: string;
  status: "draft" | "approved";
  current_version: number;
  editable_manifest: ResumeContentManifest;
  created_at: string;
  updated_at: string;
}

export interface ResumePaginationResponse {
  items: ResumeResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ResumeApprovalResponse {
  id: string;
  status: "approved";
  approved_version: number;
  message: string;
}

export interface ResumeVersionResponse {
  id: string;
  resume_id: string;
  version_number: number;
  manifest_snapshot: Record<string, any>;
  pdf_storage_key?: string | null;
  docx_storage_key?: string | null;
  preview_storage_key?: string | null;
  ats_score?: number | null;
  ats_analysis: Record<string, any>;
  created_at: string;
}

export interface ATSEvaluationResponse {
  id: string;
  resume_id: string;
  overall_score: number;
  format_score?: number | null;
  relevance_score?: number | null;
  quality_score?: number | null;
  score_breakdown: Record<string, any>;
  matched_keywords: string[];
  missing_keywords: string[];
  critical_issues: string[];
  warnings: string[];
  suggestions: string[];
  disclaimer: string;
  created_at: string;
}
