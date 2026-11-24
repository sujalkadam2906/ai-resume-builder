import React, { useState } from "react";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  ExternalLink,
  Mail,
  Phone,
  MapPin,
  Linkedin,
  Github,
  Globe,
  Lock,
  Layers,
  Sparkles,
} from "lucide-react";
import type { ResumeContentManifest } from "@/types/api";

interface ResumePreviewProps {
  manifest: ResumeContentManifest;
  scale?: number;
  onScaleChange?: (newScale: number) => void;
  isApproved?: boolean;
  versionNumber?: number;
}

export const ResumePreview: React.FC<ResumePreviewProps> = ({
  manifest,
  scale: controlledScale,
  onScaleChange,
  isApproved = false,
  versionNumber = 1,
}) => {
  const [internalScale, setInternalScale] = useState<number>(0.95);
  const scale = controlledScale !== undefined ? controlledScale : internalScale;

  const handleZoom = (delta: number) => {
    const next = Math.max(0.6, Math.min(1.4, Number((scale + delta).toFixed(2))));
    if (onScaleChange) onScaleChange(next);
    else setInternalScale(next);
  };

  const handleFit = () => {
    if (onScaleChange) onScaleChange(0.95);
    else setInternalScale(0.95);
  };

  const { personal_info, links, headline, summary, ordered_skills, projects, leadership, education, certifications, achievements } = manifest;

  return (
    <div className="flex flex-col h-full bg-surface-elevated/40 border border-surface-border rounded-xl overflow-hidden shadow-xs">
      {/* Canvas Toolbar */}
      <div className="h-11 px-4 bg-surface border-b border-surface-border flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Live A4 Document Preview
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-elevated text-text-muted border border-surface-border">
            v{versionNumber} · {isApproved ? "Approved" : "Draft"}
          </span>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1.5 bg-surface-elevated border border-surface-border rounded-lg p-0.5 text-xs">
          <button
            onClick={() => handleZoom(-0.1)}
            disabled={scale <= 0.6}
            className="p-1 rounded text-text-muted hover:text-text-primary disabled:opacity-40"
            title="Zoom out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="px-1.5 font-mono text-[11px] text-text-secondary min-w-[42px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={() => handleZoom(0.1)}
            disabled={scale >= 1.4}
            className="p-1 rounded text-text-muted hover:text-text-primary disabled:opacity-40"
            title="Zoom in"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleFit}
            className="p-1 rounded text-text-muted hover:text-text-primary text-[10px] px-1 font-medium"
            title="Fit view"
          >
            Fit
          </button>
        </div>
      </div>

      {/* Scrollable Canvas Viewport */}
      <div className="flex-1 overflow-auto p-4 sm:p-8 flex justify-center items-start bg-neutral-900/30">
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "top center",
            width: "794px", // Standard A4 width in px at 96 DPI
            minHeight: "1123px", // Standard A4 height in px at 96 DPI
          }}
          className="bg-white text-slate-900 shadow-2xl rounded-xs p-10 sm:p-12 transition-transform duration-100 ease-out font-sans flex flex-col justify-between shrink-0 select-text"
        >
          {/* A4 Resume Body */}
          <div className="space-y-4 text-[12px] leading-normal">
            {/* Header: Candidate Name & Target Headline */}
            <div className="text-center pb-2 border-b border-slate-300">
              <h1 className="text-2xl font-bold tracking-tight text-slate-950 uppercase font-serif">
                {personal_info?.display_name || personal_info?.full_name || "CANDIDATE NAME"}
              </h1>
              {headline && (
                <p className="text-[12px] font-semibold text-slate-700 tracking-wide mt-0.5">
                  {headline}
                </p>
              )}

              {/* Contact Meta Line */}
              <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-600 mt-2 font-medium">
                {personal_info?.location && <span>{personal_info.location}</span>}
                {personal_info?.phone && (
                  <>
                    <span>•</span>
                    <span>{personal_info.phone}</span>
                  </>
                )}
                {personal_info?.email && (
                  <>
                    <span>•</span>
                    <a href={`mailto:${personal_info.email}`} className="text-blue-700 hover:underline">
                      {personal_info.email}
                    </a>
                  </>
                )}
                {links?.linkedin?.url && (
                  <>
                    <span>•</span>
                    <a
                      href={links.linkedin.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-700 hover:underline inline-flex items-center gap-0.5"
                    >
                      {links.linkedin.display || "LinkedIn"}
                    </a>
                  </>
                )}
                {links?.github?.url && (
                  <>
                    <span>•</span>
                    <a
                      href={links.github.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-700 hover:underline inline-flex items-center gap-0.5"
                    >
                      {links.github.display || "GitHub"}
                    </a>
                  </>
                )}
                {links?.portfolio?.url && (
                  <>
                    <span>•</span>
                    <a
                      href={links.portfolio.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-700 hover:underline inline-flex items-center gap-0.5"
                    >
                      {links.portfolio.display || "Portfolio"}
                    </a>
                  </>
                )}
              </div>
            </div>

            {/* Professional Summary */}
            {summary && (
              <div className="pt-0.5">
                <p className="text-[11.5px] text-slate-700 leading-relaxed text-justify">
                  {summary}
                </p>
              </div>
            )}

            {/* Technical Skills Section */}
            {ordered_skills && Object.keys(ordered_skills).length > 0 && (
              <div className="space-y-1 pt-1">
                <div className="flex items-center border-b border-slate-300 pb-0.5">
                  <h2 className="text-[12px] font-bold tracking-wider uppercase text-slate-900 font-serif">
                    Technical Skills
                  </h2>
                </div>
                <div className="space-y-0.5 text-[11px] pt-0.5">
                  {Object.entries(ordered_skills).map(([category, skillsList]) => (
                    <div key={category} className="flex">
                      <span className="font-bold text-slate-800 w-36 shrink-0 capitalize">
                        {category.replace(/_/g, " ")}:
                      </span>
                      <span className="text-slate-700 leading-tight">
                        {Array.isArray(skillsList) ? skillsList.join(", ") : skillsList}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Projects Section */}
            {projects && projects.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="flex items-center border-b border-slate-300 pb-0.5">
                  <h2 className="text-[12px] font-bold tracking-wider uppercase text-slate-900 font-serif">
                    Projects
                  </h2>
                </div>
                <div className="space-y-2.5">
                  {projects.map((proj, idx) => (
                    <div key={proj.id || idx} className="space-y-1">
                      <div className="flex items-baseline justify-between text-[11.5px]">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-bold text-slate-900">{proj.title}</span>
                          {proj.subtitle && (
                            <span className="text-slate-600 font-medium">| {proj.subtitle}</span>
                          )}
                          {proj.is_fixed && (
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold">
                              Locked Slot #{idx + 1}
                            </span>
                          )}
                        </div>

                        {/* Project Links */}
                        {proj.links && proj.links.length > 0 && (
                          <div className="flex items-center gap-2 text-[10.5px]">
                            {proj.links.map((link, lIdx) => (
                              <a
                                key={lIdx}
                                href={link.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-blue-700 hover:underline font-medium"
                              >
                                {link.label || "Link"}
                              </a>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Project Bullets */}
                      {proj.bullets && proj.bullets.length > 0 && (
                        <ul className="list-disc list-outside ml-4 space-y-0.5 text-[11px] text-slate-700">
                          {proj.bullets.map((bullet, bIdx) => (
                            <li key={bIdx} className="leading-tight pl-0.5">
                              {bullet}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Professional Experience / Leadership Section */}
            {leadership && leadership.length > 0 && (
              <div className="space-y-2 pt-1">
                <div className="flex items-center border-b border-slate-300 pb-0.5">
                  <h2 className="text-[12px] font-bold tracking-wider uppercase text-slate-900 font-serif">
                    Experience & Leadership
                  </h2>
                </div>
                <div className="space-y-2">
                  {leadership.map((exp, idx) => (
                    <div key={exp.id || idx} className="space-y-0.5 text-[11.5px]">
                      <div className="flex items-baseline justify-between">
                        <div>
                          <span className="font-bold text-slate-900">{exp.role}</span>
                          <span className="text-slate-700">, {exp.organization}</span>
                        </div>
                        <span className="text-[10.5px] text-slate-600 font-medium">
                          {exp.duration}
                        </span>
                      </div>

                      {exp.bullets && exp.bullets.length > 0 && (
                        <ul className="list-disc list-outside ml-4 space-y-0.5 text-[11px] text-slate-700 pt-0.5">
                          {exp.bullets.map((b, bIdx) => (
                            <li key={bIdx} className="leading-tight pl-0.5">
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

            {/* Education Section */}
            {education && education.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <div className="flex items-center border-b border-slate-300 pb-0.5">
                  <h2 className="text-[12px] font-bold tracking-wider uppercase text-slate-900 font-serif">
                    Education
                  </h2>
                </div>
                <div className="space-y-1 text-[11px]">
                  {education.map((edu, idx) => (
                    <div key={idx} className="flex items-baseline justify-between">
                      <div>
                        <span className="font-bold text-slate-900">{edu.degree}</span>
                        <span className="text-slate-700"> — {edu.institution}</span>
                        {edu.cgpa && (
                          <span className="text-slate-800 font-semibold ml-2">
                            (CGPA: {edu.cgpa})
                          </span>
                        )}
                      </div>
                      <span className="text-slate-600 font-medium text-[10.5px]">
                        {edu.duration}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Certifications & Achievements Section */}
            {((certifications && certifications.length > 0) ||
              (achievements && achievements.length > 0)) && (
              <div className="space-y-1 pt-1">
                <div className="flex items-center border-b border-slate-300 pb-0.5">
                  <h2 className="text-[12px] font-bold tracking-wider uppercase text-slate-900 font-serif">
                    Certifications & Achievements
                  </h2>
                </div>
                <div className="text-[11px] text-slate-700 space-y-0.5">
                  {certifications && certifications.length > 0 && (
                    <div>
                      <span className="font-bold text-slate-800">Certifications: </span>
                      <span>{certifications.join(" • ")}</span>
                    </div>
                  )}
                  {achievements && achievements.length > 0 && (
                    <div className="space-y-0.5 pt-0.5">
                      {achievements.map((ach, idx) => (
                        <div key={ach.id || idx}>
                          <span className="font-bold text-slate-800">• {ach.title}</span>
                          {ach.description && (
                            <span className="text-slate-600"> — {ach.description}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Guaranteed Single-Page A4 Footer Marker */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-between text-[9.5px] text-slate-600 font-mono select-none">
            <span>Compiled via Python Core Engine · ReportLab A4 Precision</span>
            <span>Single-Page Guaranteed</span>
          </div>
        </div>
      </div>
    </div>
  );
};
