import React from "react";
import { History, FileText, Download } from "lucide-react";

export const HistoryPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Resume Generation Archive
        </h2>
        <p className="text-sm text-text-secondary">
          Browse historical tailored applications, inspect previous version snapshots, and download PDF or DOCX documents.
        </p>
      </div>

      <div className="bg-surface border border-surface-border rounded-xl p-8 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-surface-elevated mx-auto flex items-center justify-center text-text-muted">
          <History className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-text-primary">No Web Application Records</h3>
          <p className="text-xs text-text-secondary max-w-md mx-auto">
            Historical applications generated via the terminal CLI reside safely in your local <code className="text-brand-primary bg-surface-elevated px-1.5 py-0.5 rounded text-[11px]">output/</code> directory. Web history tracking will be active in Milestone 4.
          </p>
        </div>
      </div>
    </div>
  );
};
