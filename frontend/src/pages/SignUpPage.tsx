import React, { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/context/AuthContext";
import { Lock, Mail, User, ArrowRight, AlertCircle, CheckCircle2, Eye, EyeOff } from "lucide-react";
import { FormaLogo } from "@/components/brand/FormaLogo";

export const SignUpPage: React.FC = () => {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const isPublicSignupEnabled = import.meta.env.VITE_ALLOW_PUBLIC_SIGNUP !== "false";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  if (!loading && session) {
    return <Navigate to="/dashboard" replace />;
  }

  if (!isPublicSignupEnabled) {
    return (
      <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-text-primary transition-colors font-sans">
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
          <Link to="/" className="inline-block mb-6">
            <FormaLogo size="lg" withTagline={true} />
          </Link>
          <div className="bg-surface py-8 px-6 shadow-card sm:rounded-xl border border-surface-border text-center space-y-4">
            <h2 className="font-serif text-2xl font-bold tracking-tight text-text-primary">
              Private Access Phase
            </h2>
            <p className="text-sm text-text-secondary leading-relaxed">
              Public registration is currently restricted. Please sign in with authorized credentials or check back soon.
            </p>
            <div className="pt-3">
              <Link
                to="/login"
                className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-[#17263C] hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] transition-all"
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
          setErrorMessage("Public registrations are currently being enabled in Supabase Auth. Please enable user registrations in the Supabase Dashboard under Authentication -> Providers -> Email -> Enable Signups.");
        } else {
          setErrorMessage(error.message);
        }
      } else if (data.session) {
        navigate("/dashboard", { replace: true });
      } else {
        setIsSuccess(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during registration.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-text-primary transition-colors font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-block mb-6 hover:opacity-90 transition-opacity">
          <FormaLogo size="lg" withTagline={true} />
        </Link>
        <h2 className="font-serif text-3xl font-medium tracking-tight text-text-primary">
          Create your account
        </h2>
        <p className="mt-2 text-sm text-text-secondary">
          Craft executive, tailored resumes engineered for interview conversion
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-surface py-8 px-6 shadow-card sm:rounded-xl sm:px-10 border border-surface-border">
          {isSuccess ? (
            <div className="text-center space-y-4 py-4">
              <div className="mx-auto w-12 h-12 bg-[#E8F0EB] dark:bg-[#315C4B]/30 text-[#315C4B] dark:text-[#88C4A6] rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="font-serif text-2xl font-bold text-text-primary">Check your email</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                We've sent a verification link to <span className="font-semibold text-text-primary">{email}</span>. Click the link in the email to activate your account and begin tailoring.
              </p>
              <div className="pt-4">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-[#17263C] hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] transition-all"
                >
                  Proceed to Sign In
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Link>
              </div>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
                  <div className="text-xs text-red-700 dark:text-red-300 font-medium leading-relaxed">
                    {errorMessage}
                  </div>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label
                    htmlFor="fullName"
                    className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1.5"
                  >
                    Full Name
                  </label>
                  <div className="relative rounded-lg shadow-2xs">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                      <User className="h-4 w-4" />
                    </div>
                    <input
                      id="fullName"
                      name="fullName"
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="block w-full pl-10 pr-3.5 py-2.5 border border-surface-border rounded-lg bg-background text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-[#17263C] dark:focus:ring-[#B79A65] transition-all"
                      placeholder="Jane Doe"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="email"
                    className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1.5"
                  >
                    Email Address
                  </label>
                  <div className="relative rounded-lg shadow-2xs">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                      <Mail className="h-4 w-4" />
                    </div>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="block w-full pl-10 pr-3.5 py-2.5 border border-surface-border rounded-lg bg-background text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-[#17263C] dark:focus:ring-[#B79A65] transition-all"
                      placeholder="jane@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1.5"
                  >
                    Password (8+ characters)
                  </label>
                  <div className="relative rounded-lg shadow-2xs">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="block w-full pl-10 pr-10 py-2.5 border border-surface-border rounded-lg bg-background text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-[#17263C] dark:focus:ring-[#B79A65] transition-all"
                      placeholder="••••••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-text-primary"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-xs font-semibold uppercase tracking-wider text-text-secondary mb-1.5"
                  >
                    Confirm Password
                  </label>
                  <div className="relative rounded-lg shadow-2xs">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-muted">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="block w-full pl-10 pr-3.5 py-2.5 border border-surface-border rounded-lg bg-background text-text-primary placeholder-text-muted text-sm focus:outline-none focus:ring-2 focus:ring-[#17263C] dark:focus:ring-[#B79A65] transition-all"
                      placeholder="••••••••••••"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full flex justify-center items-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-[#17263C] hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] dark:hover:bg-white shadow-card hover:shadow-elevated disabled:opacity-50 transition-all cursor-pointer"
                  >
                    {isSubmitting ? (
                      <div className="w-5 h-5 border-2 border-white/60 dark:border-black/60 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        Create Account
                        <ArrowRight className="ml-2 w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-8 border-t border-surface-border pt-6 text-center">
                <p className="text-sm text-text-secondary">
                  Already have an account?{" "}
                  <Link
                    to="/login"
                    className="font-semibold text-[#315C4B] dark:text-[#88C4A6] hover:underline"
                  >
                    Sign in instead
                  </Link>
                </p>
              </div>
            </>
          )}
        </div>

        {/* Back to Home Link */}
        <div className="text-center mt-6">
          <Link to="/" className="text-xs text-text-muted hover:text-text-primary transition-colors">
            ← Back to FormaCV Home
          </Link>
        </div>
      </div>
    </div>
  );
};
