import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ActiveProfileProvider } from "./context/ActiveProfileContext";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { SignUpPage } from "./pages/SignUpPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
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

const RootRoute: React.FC = () => {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-text-muted">
        <div className="w-8 h-8 border-2 border-[#17263C] dark:border-[#B79A65] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  return session ? <Navigate to="/dashboard" replace /> : <LandingPage />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ActiveProfileProvider>
            <BrowserRouter>
              <Routes>
                {/* Public Marketing & Auth Routes */}
                <Route path="/" element={<RootRoute />} />
                <Route path="/landing" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignUpPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/auth/callback" element={<AuthCallbackPage />} />

                {/* Protected Application Workspace */}
                <Route
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/profiles" element={<ProfilesPage />} />
                  <Route path="/job-descriptions" element={<JobDescriptionsPage />} />
                  <Route path="/builder" element={<ResumeBuilderPage />} />
                  <Route path="/resumes" element={<ResumesPage />} />
                  <Route path="/history" element={<Navigate to="/resumes" replace />} />
                  <Route path="/ats" element={<AtsAnalysisPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
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
