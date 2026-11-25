import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Target,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Sparkles,
  Info,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Edit3,
  TrendingUp,
  History,
  Clock,
} from "lucide-react";
import { resumesApi } from "@/services/api";
import type { ATSEvaluationResponse, ResumeResponse } from "@/types/api";

export const AtsAnalysisPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const preselectedResumeId = searchParams.get("resume_id") || "";

  const [selectedResumeId, setSelectedResumeId] = useState<string>(preselectedResumeId);

  // Fetch all available resumes for selection
  const { data: resumesData, isLoading: resumesLoading } = useQuery({
    queryKey: ["ats-resumes-list"],
    queryFn: () => resumesApi.list(undefined, undefined, 1, 100),
  });

  const resumes = resumesData?.items || [];
  const currentResumeId = selectedResumeId || (resumes.length > 0 ? resumes[0].id : "");

  // Fetch existing ATS evaluations for the chosen resume
  const {
    data: evaluations,
    isLoading: evalLoading,
    refetch: refetchEvals,
  } = useQuery({
    queryKey: ["ats-evaluations", currentResumeId],
    queryFn: () => resumesApi.listEvaluations(currentResumeId),
    enabled: !!currentResumeId,
  });

  // Run ATS Diagnostic Mutation
  const evaluateMutation = useMutation({
    mutationFn: (resumeId: string) => resumesApi.evaluate(resumeId),
    onSuccess: (newEval) => {
      queryClient.invalidateQueries({ queryKey: ["ats-evaluations", currentResumeId] });
    },
    onError: (err: any) => {
      alert(`ATS evaluation failed: ${err.message}`);
    },
  });

  const latestEvaluation = evaluations && evaluations.length > 0 ? evaluations[0] : null;
  const previousEvaluation = evaluations && evaluations.length > 1 ? evaluations[1] : null;

  const scoreDelta =
    latestEvaluation && previousEvaluation
      ? latestEvaluation.overall_score - previousEvaluation.overall_score
      : null;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-tight text-text-primary flex items-center gap-2.5">
            <Target className="w-6 h-6 text-forma-gold" />
            <span>ATS Diagnostic Engine</span>
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Deterministic evaluation of text parsing, keyword alignment (50%), format compliance (30%), and content quality (20%).
          </p>
        </div>

        {currentResumeId && (
          <div className="flex items-center gap-2">
            <Link
              to={`/builder?resume_id=${currentResumeId}`}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-forma bg-surface-elevated hover:bg-surface-border text-xs text-text-primary font-medium border border-surface-border transition-colors shadow-2xs"
            >
              <Edit3 className="w-3.5 h-3.5 text-forma-emerald" />
              <span>Edit in Builder</span>
            </Link>

            <button
              onClick={() => evaluateMutation.mutate(currentResumeId)}
              disabled={evaluateMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-forma bg-forma-navy hover:bg-forma-deep-navy dark:bg-forma-emerald dark:hover:bg-forma-emerald-hover text-white text-xs font-semibold transition-all shadow-subtle disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${evaluateMutation.isPending ? "animate-spin" : ""}`} />
              <span>{evaluateMutation.isPending ? "Analyzing Keywords..." : "Run ATS Diagnostic"}</span>
            </button>
          </div>
        )}
      </div>

      {/* Target Resume Selector Bar */}
      <div className="bg-surface border border-surface-border rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-primary" />
          <span className="text-xs font-semibold text-text-primary">Target Resume Document:</span>
        </div>

        {resumesLoading ? (
          <div className="text-xs text-text-muted">Loading resumes from database...</div>
        ) : resumes.length === 0 ? (
          <div className="text-xs text-text-muted">No generated resumes found to evaluate.</div>
        ) : (
          <select
            value={currentResumeId}
            onChange={(e) => {
              setSelectedResumeId(e.target.value);
              setSearchParams({ resume_id: e.target.value });
            }}
            className="w-full sm:w-auto bg-surface-elevated border border-surface-border rounded-lg px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-brand-primary font-medium"
          >
            {resumes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.resume_title} (v{r.current_version} · {r.status})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Evaluation Results Card */}
      {!latestEvaluation ? (
        <div className="bg-surface border border-surface-border rounded-xl p-12 text-center space-y-3 shadow-xs">
          <Target className="w-10 h-10 text-text-muted mx-auto" />
          <h3 className="text-sm font-semibold text-text-primary">No ATS Evaluation on File</h3>
          <p className="text-xs text-text-muted max-w-sm mx-auto">
            Click "Run ATS Diagnostic" above to perform deterministic keyword density and compliance scoring against the target job description.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Diagnostic Disclaimer Alert */}
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs">
            <Info className="w-4 h-4 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>Heuristic Notice:</strong> {latestEvaluation.disclaimer ||
                "This evaluation is a local heuristic estimate and does not guarantee employer or vendor ATS outcomes."}
            </p>
          </div>

          {/* Overall Score Card */}
          <div className="bg-surface border border-surface-border rounded-xl p-6 space-y-6 shadow-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
              <div>
                <h3 className="text-base font-bold text-text-primary">ATS Readiness Score</h3>
                <p className="text-xs text-text-muted mt-0.5">
                  Calculated against extracted job description keywords and single-page constraints
                </p>
              </div>

              <div className="flex items-baseline gap-3">
                {scoreDelta !== null && (
                  <span
                    className={`inline-flex items-center gap-1 text-xs font-mono font-bold px-2 py-0.5 rounded ${
                      scoreDelta > 0
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : scoreDelta < 0
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : "bg-surface-elevated text-text-muted"
                    }`}
                  >
                    <TrendingUp className="w-3 h-3" />
                    {scoreDelta > 0 ? `+${scoreDelta}` : scoreDelta} pts
                  </span>
                )}

                <div className="flex items-baseline gap-1.5">
                  <span
                    className={`text-4xl font-extrabold font-mono ${
                      latestEvaluation.overall_score >= 80
                        ? "text-emerald-400"
                        : latestEvaluation.overall_score >= 60
                        ? "text-amber-400"
                        : "text-red-400"
                    }`}
                  >
                    {latestEvaluation.overall_score}
                  </span>
                  <span className="text-text-muted text-xs font-mono">/ 100 Pts</span>
                </div>
              </div>
            </div>

            {/* 3-Pillar Breakdown (Format 30%, Relevance 50%, Quality 20%) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  Relevance (50%)
                </div>
                <div className="text-xl font-bold text-text-primary">
                  {latestEvaluation.relevance_score ?? 0} Pts
                </div>
                <p className="text-[10px] text-text-muted">Keyword & skills overlap</p>
              </div>

              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  Format (30%)
                </div>
                <div className="text-xl font-bold text-text-primary">
                  {latestEvaluation.format_score ?? 0} Pts
                </div>
                <p className="text-[10px] text-text-muted">Section order & typography</p>
              </div>

              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  Quality (20%)
                </div>
                <div className="text-xl font-bold text-text-primary">
                  {latestEvaluation.quality_score ?? 0} Pts
                </div>
                <p className="text-[10px] text-text-muted">Quantified bullet metrics</p>
              </div>
            </div>

            {/* Matched & Missing Keywords */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2">
                <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Matched Keywords ({latestEvaluation.matched_keywords?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {latestEvaluation.matched_keywords?.map((kw) => (
                    <span
                      key={kw}
                      className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2">
                <span className="text-xs font-bold text-text-primary flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  Missing Keywords ({latestEvaluation.missing_keywords?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {latestEvaluation.missing_keywords?.length > 0 ? (
                    latestEvaluation.missing_keywords.map((kw) => (
                      <span
                        key={kw}
                        className="text-[11px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono"
                      >
                        {kw}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-text-muted">No critical missing keywords</span>
                  )}
                </div>
              </div>
            </div>

            {/* Suggestions & Actionable Feedback */}
            {latestEvaluation.suggestions?.length > 0 && (
              <div className="bg-surface-elevated/60 border border-surface-border rounded-lg p-4 space-y-2">
                <span className="text-xs font-bold text-text-primary">Actionable Suggestions</span>
                <ul className="text-xs text-text-secondary space-y-1.5 list-disc list-inside">
                  {latestEvaluation.suggestions.map((s, i) => (
                    <li key={i} className="leading-relaxed">
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Historical Evaluations Log */}
          {evaluations && evaluations.length > 1 && (
            <div className="bg-surface border border-surface-border rounded-xl p-5 space-y-3 shadow-xs">
              <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-brand-primary" />
                Historical Evaluations Log ({evaluations.length})
              </h4>
              <div className="space-y-2">
                {evaluations.map((ev, i) => (
                  <div
                    key={ev.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-surface-elevated border border-surface-border text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-text-muted" />
                      <span className="font-mono text-text-secondary">
                        {new Date(ev.created_at).toLocaleString()}
                      </span>
                      {i === 0 && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-brand-primary/10 text-brand-primary font-bold">
                          Latest
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 font-mono">
                      <span>Rel: {ev.relevance_score}</span>
                      <span>Fmt: {ev.format_score}</span>
                      <span>Qual: {ev.quality_score}</span>
                      <span className="font-bold text-text-primary text-sm">
                        {ev.overall_score} pts
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
