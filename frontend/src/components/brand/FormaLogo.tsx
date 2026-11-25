import React from "react";
import { cn } from "@/lib/utils";

interface FormaIconProps {
  className?: string;
  size?: number;
  variant?: "navy" | "ivory" | "gold" | "emerald";
}

export const FormaIcon: React.FC<FormaIconProps> = ({
  className,
  size = 32,
  variant = "navy",
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0 transition-transform duration-200", className)}
      aria-label="FormaCV Icon"
    >
      {/* Background Document / Folio Base */}
      <rect
        x="6"
        y="4"
        width="28"
        height="32"
        rx="4"
        className={cn(
          variant === "ivory"
            ? "fill-[#F7F5F0]"
            : "fill-[#101B2B] dark:fill-[#F7F5F0]"
        )}
      />

      {/* Top Folded Corner Cutout / Geometry */}
      <path
        d="M26 4H34V12L26 4Z"
        className={cn(
          variant === "ivory"
            ? "fill-[#E8E4DA]"
            : "fill-[#17263C] dark:fill-[#E8E4DA]"
        )}
      />
      <path
        d="M26 4V10C26 11.1046 26.8954 12 28 12H34"
        className={cn(
          variant === "ivory"
            ? "stroke-[#B79A65]"
            : "stroke-[#B79A65] dark:stroke-[#B79A65]"
        )}
        strokeWidth="1.5"
        strokeLinecap="round"
      />

      {/* Architectural "F" Monogram Bars (Representing Editorial CV Layout) */}
      {/* Primary Top Bar */}
      <path
        d="M12 13H24"
        className={cn(
          variant === "ivory"
            ? "stroke-[#101B2B]"
            : "stroke-[#FFFFFF] dark:stroke-[#101B2B]"
        )}
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* Secondary Mid Bar */}
      <path
        d="M12 20H20"
        className={cn(
          variant === "ivory"
            ? "stroke-[#B79A65]"
            : "stroke-[#B79A65]"
        )}
        strokeWidth="2.2"
        strokeLinecap="round"
      />

      {/* Vertical Spine of 'F' */}
      <path
        d="M12 13V28"
        className={cn(
          variant === "ivory"
            ? "stroke-[#101B2B]"
            : "stroke-[#FFFFFF] dark:stroke-[#101B2B]"
        )}
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* Subtle CV Status Dot / Emerald Seal */}
      <circle
        cx="27"
        cy="26"
        r="2.5"
        className="fill-[#315C4B] dark:fill-[#45826A]"
      />
    </svg>
  );
};

interface FormaLogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  withTagline?: boolean;
  inverted?: boolean;
}

export const FormaLogo: React.FC<FormaLogoProps> = ({
  className,
  size = "md",
  withTagline = false,
  inverted = false,
}) => {
  const iconSize = size === "sm" ? 28 : size === "lg" ? 40 : 32;

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <FormaIcon
        size={iconSize}
        variant={inverted ? "ivory" : "navy"}
      />
      <div className="flex flex-col leading-none">
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "font-serif font-medium tracking-tight",
              size === "sm" ? "text-lg" : size === "lg" ? "text-2xl" : "text-xl",
              inverted
                ? "text-white"
                : "text-[#101B2B] dark:text-[#F7F5F0]"
            )}
          >
            Forma
          </span>
          <span
            className={cn(
              "font-sans font-semibold tracking-wider px-1.5 py-0.5 rounded text-[10px] uppercase border",
              inverted
                ? "bg-white/10 text-white/90 border-white/20"
                : "bg-[#B79A65]/15 text-[#8F7546] dark:text-[#D4BC8B] border-[#B79A65]/30"
            )}
          >
            CV
          </span>
        </div>
        {withTagline && (
          <span
            className={cn(
              "text-[11px] font-sans tracking-normal mt-1",
              inverted
                ? "text-white/60"
                : "text-[#687386] dark:text-[#9DA8B8]"
            )}
          >
            Craft a career that gets noticed.
          </span>
        )}
      </div>
    </div>
  );
};
