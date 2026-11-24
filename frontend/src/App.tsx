import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { ActiveProfileProvider } from "./context/ActiveProfileContext";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProfilesPage } from "./pages/ProfilesPage";
import { JobDescriptionsPage } from "./pages/JobDescriptionsPage";
import { ResumeBuilderPage } from "./pages/ResumeBuilderPage";
import { ResumesPage } from "./pages/ResumesPage";
import { AtsAnalysisPage } from "./pages/AtsAnalysisPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ActiveProfileProvider>
            <BrowserRouter>
              <Routes>
                {/* Public Auth Route */}
                <Route path="/login" element={<LoginPage />} />

                {/* Protected Application Routes */}
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<DashboardPage />} />
                  <Route path="profiles" element={<ProfilesPage />} />
                  <Route path="job-descriptions" element={<JobDescriptionsPage />} />
                  <Route path="builder" element={<ResumeBuilderPage />} />
                  <Route path="resumes" element={<ResumesPage />} />
                  <Route path="history" element={<Navigate to="/resumes" replace />} />
                  <Route path="ats" element={<AtsAnalysisPage />} />
                  <Route path="settings" element={<SettingsPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </ActiveProfileProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
