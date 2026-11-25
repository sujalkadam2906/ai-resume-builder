import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/context/AuthContext";
import { Lock, Mail, ArrowRight, AlertCircle, ShieldCheck } from "lucide-react";

export const LoginPage: React.FC = () => {
  const { session, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!loading && session) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) {
        if (error.message.toLowerCase().includes("email not confirmed")) {
          setErrorMessage("Please check your email and click the confirmation link before signing in.");
        } else {
          setErrorMessage(error.message);
        }
      } else {
        navigate("/", { replace: true });
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during sign in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-900 dark:text-slate-100 transition-colors">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center text-white shadow-lg mb-4">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h2 className="text-3xl font-extrabold tracking-tight">AI Resume Builder</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Sign in with your authorized credentials to access your dashboard
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10 border border-slate-200 dark:border-slate-800">
          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-700 dark:text-red-300 font-medium">
                {errorMessage}
              </div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
              >
                Email Address
              </label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-5 h-5" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                  placeholder="admin@example.com"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                >
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-primary-600 dark:text-primary-400 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-5 h-5" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Sign In
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {import.meta.env.VITE_ALLOW_PUBLIC_SIGNUP !== "false" && (
            <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-4 text-center">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="font-semibold text-primary-600 dark:text-primary-400 hover:underline"
                >
                  Sign Up
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
