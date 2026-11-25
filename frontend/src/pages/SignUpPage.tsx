import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/context/AuthContext";
import { Lock, Mail, User, ArrowRight, AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";

export const SignUpPage: React.FC = () => {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const isPublicSignupEnabled = import.meta.env.VITE_ALLOW_PUBLIC_SIGNUP !== "false";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!loading && session) {
    return <Navigate to="/" replace />;
  }

  if (!isPublicSignupEnabled) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-900 dark:text-slate-100 transition-colors">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white dark:bg-slate-900 py-8 px-6 shadow-xl sm:rounded-2xl border border-slate-200 dark:border-slate-800 text-center space-y-4">
            <div className="mx-auto w-12 h-12 bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Invite-Only Access</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
              Public registration is currently disabled. Please sign in with an authorized account or contact the administrator for access.
            </p>
            <div className="pt-2">
              <Link
                to="/login"
                className="w-full inline-flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 transition-colors"
              >
                Return to Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !trimmedEmail.includes("@")) {
      setErrorMessage("Please enter a valid email address.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      const { data, error } = await supabase.auth.signUp({
        email: trimmedEmail,
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        if (
          error.message.toLowerCase().includes("already registered") ||
          error.message.toLowerCase().includes("already exists")
        ) {
          setErrorMessage("An account with this email already exists. Please sign in or use password recovery.");
        } else if (error.message.toLowerCase().includes("signups not allowed")) {
          setErrorMessage("Public registrations are currently being enabled on Supabase. Please enable 'Allow new users to sign up' in the Supabase Dashboard (Authentication -> Providers -> Email).");
        } else {
          setErrorMessage(error.message);
        }
      } else if (data.session) {
        // Direct login without email confirmation
        navigate("/", { replace: true });
      } else {
        // Email verification required
        setIsSuccess(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during registration.");
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
        <h2 className="text-3xl font-extrabold tracking-tight">Create your account</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Build and customize AI-tailored resumes for your career
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10 border border-slate-200 dark:border-slate-800">
          {isSuccess ? (
            <div className="text-center space-y-4">
              <div className="mx-auto w-12 h-12 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold">Check your email</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                We've sent a verification link to <span className="font-semibold text-slate-900 dark:text-slate-200">{email}</span>. Please click the link to confirm your account and sign in.
              </p>
              <div className="pt-4">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 transition-colors"
                >
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700 dark:text-red-300 font-medium">
                    {errorMessage}
                  </div>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label
                    htmlFor="fullName"
                    className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                  >
                    Full Name
                  </label>
                  <div className="mt-1 relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <User className="h-5 h-5" />
                    </div>
                    <input
                      id="fullName"
                      name="fullName"
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                      placeholder="Jane Doe"
                    />
                  </div>
                </div>

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
                      placeholder="jane@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                  >
                    Password
                  </label>
                  <div className="mt-1 relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <Lock className="h-5 h-5" />
                    </div>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                      placeholder="••••••••••••"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-sm font-semibold text-slate-700 dark:text-slate-300"
                  >
                    Confirm Password
                  </label>
                  <div className="mt-1 relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <Lock className="h-5 h-5" />
                    </div>
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent sm:text-sm"
                      placeholder="••••••••••••"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 transition-colors"
                  >
                    {isSubmitting ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        Create Account
                        <ArrowRight className="ml-2 w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-4 text-center">
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Already have an account?{" "}
                  <Link
                    to="/login"
                    className="font-semibold text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    Sign In
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
