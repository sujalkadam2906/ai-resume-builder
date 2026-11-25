import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { AlertCircle, CheckCircle2 } from "lucide-react";

export const AuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Parse hash params from URL
        const hash = window.location.hash.substring(1);
        const searchParams = new URLSearchParams(window.location.search);
        const hashParams = new URLSearchParams(hash);

        const error = hashParams.get("error") || searchParams.get("error");
        const errorDescription =
          hashParams.get("error_description") || searchParams.get("error_description");

        if (error || errorDescription) {
          setErrorMsg(errorDescription || error || "Authentication verification failed.");
          return;
        }

        const type = hashParams.get("type") || searchParams.get("type");

        // Refresh or obtain session
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          setErrorMsg(sessionError.message);
          return;
        }

        if (type === "recovery") {
          navigate("/reset-password", { replace: true });
        } else if (session) {
          navigate("/", { replace: true });
        } else {
          // If no active session, redirect to login
          navigate("/login", { replace: true });
        }
      } catch (err: any) {
        setErrorMsg(err.message || "An error occurred during authentication callback.");
      }
    };

    handleAuthCallback();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-900 dark:text-slate-100 transition-colors">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        {errorMsg ? (
          <div className="bg-white dark:bg-slate-900 py-8 px-6 shadow-xl sm:rounded-2xl border border-red-200 dark:border-red-900/60">
            <div className="mx-auto w-12 h-12 bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center mb-4">
              <AlertCircle className="w-7 h-7" />
            </div>
            <h3 className="text-xl font-bold text-red-700 dark:text-red-400">Authentication Error</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{errorMsg}</p>
            <div className="mt-6">
              <button
                onClick={() => navigate("/login", { replace: true })}
                className="w-full py-2.5 px-4 rounded-lg bg-primary-600 hover:bg-primary-700 text-white font-medium text-sm transition-colors"
              >
                Back to Sign In
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
              Verifying credentials and completing sign in...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
