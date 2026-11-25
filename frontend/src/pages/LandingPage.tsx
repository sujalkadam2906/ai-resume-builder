import React from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Target,
  Sparkles,
  ShieldCheck,
  Download,
  Sliders,
  Layers,
  ChevronRight,
} from "lucide-react";
import { FormaLogo } from "@/components/brand/FormaLogo";
import { useAuth } from "@/context/AuthContext";

export const LandingPage: React.FC = () => {
  const { session } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans transition-colors">
      {/* Top Brand Navigation */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <FormaLogo size="md" withTagline={false} />
          </Link>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-text-secondary">
            <a href="#method" className="hover:text-text-primary transition-colors">
              The Method
            </a>
            <a href="#features" className="hover:text-text-primary transition-colors">
              Features
            </a>
            <a href="#ats-engine" className="hover:text-text-primary transition-colors">
              ATS Diagnostics
            </a>
            <a href="#workflow" className="hover:text-text-primary transition-colors">
              Workflow
            </a>
          </nav>

          <div className="flex items-center gap-4">
            {session ? (
              <button
                onClick={() => navigate("/dashboard")}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium bg-[#17263C] text-white hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] dark:hover:bg-white shadow-sm transition-all"
              >
                Go to Workspace
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-semibold text-text-secondary hover:text-text-primary px-3 py-2 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/signup"
                  className="inline-flex items-center gap-2 px-4.5 py-2 rounded-lg text-sm font-semibold bg-[#17263C] text-[#F7F5F0] hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] dark:hover:bg-white shadow-sm hover:shadow-md transition-all"
                >
                  Create My Resume
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        {/* Subtle Gold / Editorial Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-[#B79A65]/40 bg-[#B79A65]/10 text-[#8F7546] dark:text-[#D4BC8B] text-xs font-semibold uppercase tracking-wider mb-8 animate-fade-in">
          <Sparkles className="w-3.5 h-3.5" />
          <span>The Editorial Resume Synthesis Platform</span>
        </div>

        {/* Editorial Headline */}
        <h1 className="font-serif text-4xl sm:text-6xl lg:text-7xl font-medium tracking-tight text-text-primary max-w-4xl mx-auto leading-[1.12]">
          Craft a career that{" "}
          <span className="italic font-normal text-[#315C4B] dark:text-[#45826A]">
            gets noticed.
          </span>
        </h1>

        {/* Tagline & Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto font-normal leading-relaxed">
          FormaCV matches your verified accomplishments to target job descriptions with mathematical precision. Engineered for professionals who refuse to submit generic templates.
        </p>

        {/* Action CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to={session ? "/builder" : "/signup"}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-lg text-base font-semibold bg-[#17263C] text-white hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] dark:hover:bg-white shadow-card hover:shadow-elevated transition-all"
          >
            Create My Resume
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to={session ? "/dashboard" : "/login"}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-lg text-base font-medium border border-surface-border bg-surface hover:bg-surface-elevated text-text-primary transition-all"
          >
            Explore Interactive Demo
          </Link>
        </div>

        {/* Trust Points */}
        <div className="mt-14 pt-8 border-t border-surface-border/60 max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-[#315C4B] dark:text-[#45826A] shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-semibold text-text-primary">Zero Hallucinations</div>
              <div className="text-xs text-text-muted mt-0.5">Synthesizes only from your verified project record.</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-[#315C4B] dark:text-[#45826A] shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-semibold text-text-primary">Strict 1-Page A4 Parity</div>
              <div className="text-xs text-text-muted mt-0.5">ReportLab PDF & DOCX with millimetre typographical precision.</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-[#315C4B] dark:text-[#45826A] shrink-0 mt-0.5" />
            <div>
              <div className="text-sm font-semibold text-text-primary">Private Multi-Tenant Isolation</div>
              <div className="text-xs text-text-muted mt-0.5">Row-level security ensures your data is strictly yours.</div>
            </div>
          </div>
        </div>
      </section>

      {/* Visual Workflow & Interactive Document Showcase */}
      <section id="method" className="py-16 md:py-24 bg-surface border-y border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-[#B79A65]">
              Deterministic Architecture
            </h2>
            <p className="font-serif text-3xl sm:text-4xl font-medium mt-3 text-text-primary">
              Not another generic prompt. An engineered pipeline.
            </p>
            <p className="mt-4 text-base text-text-secondary leading-relaxed">
              Every tailored resume is generated through a rigorous multi-tier matching matrix, scoring target keywords against your proven professional history.
            </p>
          </div>

          {/* Interactive Document Preview Mockup */}
          <div className="relative mx-auto max-w-5xl rounded-2xl border border-surface-border bg-background shadow-elevated p-4 sm:p-8">
            <div className="flex items-center justify-between pb-6 border-b border-surface-border">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-amber-400" />
                <div className="w-3 h-3 rounded-full bg-emerald-400" />
                <span className="text-xs text-text-muted font-mono ml-2">
                  FormaCV Document Engine v1.0 — A4 Strict Single-Page
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F0EB] dark:bg-[#315C4B]/30 text-[#315C4B] dark:text-[#88C4A6] border border-[#315C4B]/20">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  ATS Readiness: 94 / 100
                </span>
                <span className="text-xs px-2.5 py-1 rounded bg-surface-elevated text-text-muted border border-surface-border font-mono">
                  1 Page Exact
                </span>
              </div>
            </div>

            {/* Document Body Preview */}
            <div className="mt-8 bg-surface rounded-xl p-6 sm:p-10 border border-surface-border shadow-subtle max-w-3xl mx-auto text-left">
              <div className="border-b border-surface-border pb-5">
                <div className="flex items-baseline justify-between">
                  <h3 className="font-serif text-2xl font-bold text-text-primary tracking-tight">
                    Alex Mercer
                  </h3>
                  <div className="text-xs text-text-muted">Senior AI & Platform Engineer</div>
                </div>
                <div className="mt-2 text-xs text-text-secondary flex flex-wrap gap-4">
                  <span>alex.mercer@example.com</span>
                  <span>linkedin.com/in/alex-mercer</span>
                  <span>San Francisco, CA</span>
                </div>
              </div>

              {/* Tailored Profile Summary */}
              <div className="mt-5">
                <div className="text-xs font-bold uppercase tracking-wider text-[#315C4B] dark:text-[#88C4A6] mb-1.5">
                  Targeted Executive Summary
                </div>
                <p className="text-xs leading-relaxed text-text-secondary">
                  Specialized Platform Engineer with 6+ years designing distributed backend services and high-throughput LLM pipelines. Proven record reducing latency by 42% on Tier-1 architectures while ensuring 99.99% uptime.
                </p>
              </div>

              {/* Tailored Verified Projects */}
              <div className="mt-5">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-[#315C4B] dark:text-[#88C4A6]">
                    Relevance-Ranked Projects (45% Core Match)
                  </div>
                  <span className="text-[10px] text-text-muted font-mono">Match Score: 98%</span>
                </div>
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-background border border-surface-border">
                    <div className="flex justify-between items-baseline text-xs font-semibold text-text-primary">
                      <span>Enterprise Semantic Retrieval Gateway</span>
                      <span className="text-text-muted font-normal text-[11px]">Python, FastAPI, PGVector</span>
                    </div>
                    <p className="text-[11px] text-text-secondary mt-1">
                      Architected resilient multi-tenant RAG search handling 2.5M daily queries with sub-80ms p95 latency.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-background border border-surface-border">
                    <div className="flex justify-between items-baseline text-xs font-semibold text-text-primary">
                      <span>Automated Compliance & ATS Pipeline</span>
                      <span className="text-text-muted font-normal text-[11px]">ReportLab, PostgreSQL, Docker</span>
                    </div>
                    <p className="text-[11px] text-text-secondary mt-1">
                      Engineered strict single-page typesetting engine adhering to executive ATS parsing guidelines.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section id="features" className="py-20 md:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-[#B79A65]">
            Engineered Capabilities
          </h2>
          <p className="font-serif text-3xl sm:text-4xl font-medium mt-3 text-text-primary">
            Every feature designed for interview conversion.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#17263C] text-white flex items-center justify-center mb-5">
              <Sliders className="w-5 h-5 text-[#B79A65]" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              JD Keyword Ingestion
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Paste any target job description. FormaCV extracts core technical requirements, domain tools, and methodology markers automatically.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#315C4B] text-white flex items-center justify-center mb-5">
              <Target className="w-5 h-5 text-emerald-200" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              ATS Scoring Matrix
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              A 100-point diagnostic scoring system evaluating formatting robustness, keyword alignment, and typographical compliance.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#101B2B] text-white flex items-center justify-center mb-5">
              <Download className="w-5 h-5 text-[#B79A65]" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              Dual PDF & DOCX Export
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Download native ReportLab PDFs engineered to strictly occupy exactly one page, plus editable Word documents for manual recruiter submissions.
            </p>
          </div>

          {/* Card 4 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#17263C] text-white flex items-center justify-center mb-5">
              <Layers className="w-5 h-5 text-amber-200" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              Candidate Master Profiles
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Maintain your complete career history in one comprehensive master record. FormaCV filters the most relevant points for each specific job.
            </p>
          </div>

          {/* Card 5 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#315C4B] text-white flex items-center justify-center mb-5">
              <ShieldCheck className="w-5 h-5 text-emerald-200" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              Multi-Tenant Privacy
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Cryptographically verified Supabase JWTs and PostgreSQL row-level security isolate your career data. No cross-tenant visibility.
            </p>
          </div>

          {/* Card 6 */}
          <div className="bg-surface p-8 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-all">
            <div className="w-10 h-10 rounded-lg bg-[#101B2B] text-white flex items-center justify-center mb-5">
              <FileText className="w-5 h-5 text-[#B79A65]" />
            </div>
            <h3 className="font-serif text-xl font-semibold text-text-primary mb-2">
              Version History & Snapshots
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              Every generated resume is saved with its source job description, timestamp, and ATS breakdown so you can reference exactly what you submitted.
            </p>
          </div>
        </div>
      </section>

      {/* 4-Step Workflow Section */}
      <section id="workflow" className="py-20 bg-surface border-t border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-[#B79A65]">
              Step-by-Step Experience
            </h2>
            <p className="font-serif text-3xl sm:text-4xl font-medium mt-3 text-text-primary">
              From job description to tailored resume in minutes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="p-6 rounded-xl bg-background border border-surface-border relative">
              <div className="text-3xl font-serif font-bold text-[#B79A65]/40 mb-3">01</div>
              <h4 className="font-serif font-semibold text-base text-text-primary mb-1">Enter Master Data</h4>
              <p className="text-xs text-text-secondary leading-relaxed">
                Add your verified projects, roles, certifications, and skills to your profile.
              </p>
            </div>
            <div className="p-6 rounded-xl bg-background border border-surface-border relative">
              <div className="text-3xl font-serif font-bold text-[#B79A65]/40 mb-3">02</div>
              <h4 className="font-serif font-semibold text-base text-text-primary mb-1">Paste Job Opportunity</h4>
              <p className="text-xs text-text-secondary leading-relaxed">
                Supply the job posting. FormaCV pinpoints core expectations and keywords.
              </p>
            </div>
            <div className="p-6 rounded-xl bg-background border border-surface-border relative">
              <div className="text-3xl font-serif font-bold text-[#B79A65]/40 mb-3">03</div>
              <h4 className="font-serif font-semibold text-base text-text-primary mb-1">Synthesize & Refine</h4>
              <p className="text-xs text-text-secondary leading-relaxed">
                Review tailored bullet points, adjust emphasis, and verify ATS score.
              </p>
            </div>
            <div className="p-6 rounded-xl bg-background border border-surface-border relative">
              <div className="text-3xl font-serif font-bold text-[#B79A65]/40 mb-3">04</div>
              <h4 className="font-serif font-semibold text-base text-text-primary mb-1">Export Executive Formats</h4>
              <p className="text-xs text-text-secondary leading-relaxed">
                Download verified A4 1-page PDF and editable DOCX files instantly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="py-20 md:py-28 bg-[#101B2B] text-white text-center px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="max-w-3xl mx-auto relative z-10">
          <h2 className="font-serif text-3xl sm:text-5xl font-medium tracking-tight leading-tight">
            Craft a career that gets noticed.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-white/70 max-w-xl mx-auto">
            Join professionals who tailor every application with precision and confidence.
          </p>
          <div className="mt-8">
            <Link
              to={session ? "/builder" : "/signup"}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg text-base font-semibold bg-[#F7F5F0] text-[#101B2B] hover:bg-white shadow-elevated transition-all"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Editorial Footer */}
      <footer className="bg-background border-t border-surface-border py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex flex-col items-center md:items-start gap-1">
            <FormaLogo size="sm" withTagline={true} />
          </div>

          <div className="text-xs text-text-muted text-center md:text-right">
            <div>© {new Date().getFullYear()} FormaCV. All rights reserved.</div>
            <div className="mt-1">Architectural typesetting & ATS compliance engine.</div>
          </div>
        </div>
      </footer>
    </div>
  );
};
