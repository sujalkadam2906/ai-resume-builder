import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { systemApi } from "@/services/api";

export const AppLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Query readiness probe
  const { data: readinessData } = useQuery({
    queryKey: ["readiness"],
    queryFn: systemApi.getReadiness,
    refetchInterval: 15000,
  });

  // Query AI providers status
  const { data: providersData } = useQuery({
    queryKey: ["providers"],
    queryFn: systemApi.getProvidersStatus,
    refetchInterval: 30000,
  });

  const isApiReady = readinessData?.status === "ready";
  const primaryProvider = providersData?.primary_provider;

  return (
    <div className="flex min-h-screen bg-background text-text-primary selection:bg-brand-primary/20 selection:text-brand-primary">
      <Sidebar
        apiReady={isApiReady}
        primaryProvider={primaryProvider}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header
          isMobileMenuOpen={isMobileMenuOpen}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
