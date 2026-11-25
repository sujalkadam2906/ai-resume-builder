import React, { useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "@/lib/supabase";
import { Mail, ArrowRight, AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react";
import { FormaLogo } from "@/components/brand/FormaLogo";

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/auth/callback`,
      });

      if (error) {
        setErrorMessage(error.message);
      } else {
        setIsSuccess(true);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred.");
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
          Reset your password
        </h2>
        <p className="mt-2 text-sm text-text-secondary">
          Enter your registered email address and we'll send a secure recovery link
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-surface py-8 px-6 shadow-card sm:rounded-xl sm:px-10 border border-surface-border">
          {isSuccess ? (
            <div className="text-center space-y-4 py-4">
              <div className="mx-auto w-12 h-12 bg-[#E8F0EB] dark:bg-[#315C4B]/30 text-[#315C4B] dark:text-[#88C4A6] rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="font-serif text-2xl font-bold text-text-primary">Recovery email sent</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                If an account exists with <span className="font-semibold text-text-primary">{email}</span>, you will receive an email with instructions to reset your password.
              </p>
              <div className="pt-4">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center items-center py-2.5 px-4 rounded-lg text-sm font-semibold text-white bg-[#17263C] hover:bg-[#101B2B] dark:bg-[#F7F5F0] dark:text-[#101B2B] transition-all"
                >
                  <ArrowLeft className="mr-2 w-4 h-4" />
                  Back to Sign In
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

              <form className="space-y-5" onSubmit={handleSubmit}>
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
                      placeholder="name@company.com"
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
                        Send Recovery Link
                        <ArrowRight className="ml-2 w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-8 border-t border-surface-border pt-6 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center text-xs font-semibold text-[#315C4B] dark:text-[#88C4A6] hover:underline"
                >
                  <ArrowLeft className="mr-1.5 w-3.5 h-3.5" />
                  Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
