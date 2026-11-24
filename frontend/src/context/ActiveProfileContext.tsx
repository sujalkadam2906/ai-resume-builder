import React, { createContext, useContext, useState, useEffect } from "react";

interface ActiveProfileContextType {
  activeProfileSlug: string;
  setActiveProfileSlug: (slug: string) => void;
}

const ActiveProfileContext = createContext<ActiveProfileContextType | undefined>(undefined);

const STORAGE_KEY = "resume_builder_active_profile";

export const ActiveProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeProfileSlug, setActiveProfileSlugState] = useState<string>(() => {
    return localStorage.getItem(STORAGE_KEY) || "sujal";
  });

  const setActiveProfileSlug = (slug: string) => {
    localStorage.setItem(STORAGE_KEY, slug);
    setActiveProfileSlugState(slug);
  };

  return (
    <ActiveProfileContext.Provider value={{ activeProfileSlug, setActiveProfileSlug }}>
      {children}
    </ActiveProfileContext.Provider>
  );
};

export const useActiveProfile = (): ActiveProfileContextType => {
  const context = useContext(ActiveProfileContext);
  if (!context) {
    throw new Error("useActiveProfile must be used within an ActiveProfileProvider");
  }
  return context;
};
